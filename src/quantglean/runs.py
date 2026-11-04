"""Append-only run packages with content hashes and explicit failure records."""
from __future__ import annotations
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .data import load_dataset
from .engine import run_reference
from .reporting import write_report
from .specs import load_spec, validate_spec

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def code_state() -> dict:
    root = Path(__file__).resolve().parents[2]
    try:
        def git(*args):
            return subprocess.check_output(["git", "-c", "safe.directory=*", *args],
                                           cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
        commit, dirty = git("rev-parse", "HEAD"), bool(git("status", "--porcelain"))
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    sources = {"quantglean/" + p.name: digest(p) for p in sorted(Path(__file__).resolve().parent.glob("*.py"))}
    return {"commit": commit, "dirty": dirty, "source_sha256": sources}

def environment() -> dict:
    packages = {}
    for name in ("quantglean", "numpy", "pandas", "PyYAML", "pyarrow", "quantstats", "pyqlib", "scikit-learn"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {"python": sys.version, "platform": platform.platform(), "packages": packages}

def finalize(root: Path, manifest: dict) -> None:
    manifest.setdefault("finished_at", datetime.now(timezone.utc).isoformat())
    manifest["report_generated_at"] = datetime.now(timezone.utc).isoformat()
    # Report needs the manifest; regenerate and hash every artifact after it is written.
    dump(root / "run_manifest.json", manifest)
    write_report(root)
    manifest["artifacts"] = {p.name: digest(p) for p in sorted(root.iterdir())
                             if p.is_file() and p.name != "run_manifest.json"}
    dump(root / "run_manifest.json", manifest)

def execute(spec_path, manifest_path, output, *, parquet=False, command=None) -> tuple[Path, dict]:
    base = Path(output)
    base.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = base / run_id
    root.mkdir()  # Never overwrite an earlier attempt.
    manifest = {"run_id": run_id, "status": "running", "conclusion": "untested",
                "started_at": datetime.now(timezone.utc).isoformat(), "command": command or sys.argv,
                "code": code_state(), "environment": environment(), "artifacts": {}}
    dump(root / "run_manifest.json", manifest)
    try:
        spec = load_spec(spec_path)
        dump(root / "frozen_spec.json", spec)
        manifest.update(spec_hash=spec.get("spec_hash"), reproduction_level=spec.get("reproduction_level"),
                        seed=spec.get("execution", {}).get("seed"), experiment_id=spec.get("id"),
                        artifact_type=spec.get("artifact_type"), analysis_type=spec.get("analysis_type"))
        errors = validate_spec(spec)
        if errors:
            raise ValueError("; ".join(errors))
        if spec.get("status") != "spec_ready":
            raise ValueError("Run requires a frozen spec_ready specification; use qg freeze first")
        chosen = manifest_path or spec.get("data", {}).get("manifest")
        if not chosen:
            manifest.update(status="blocked_missing_data", error="No data manifest supplied; provide --data-manifest.")
            finalize(root, manifest)
            return root, manifest
        data_path = Path(chosen)
        if not data_path.is_absolute():
            data_path = Path(spec_path).resolve().parent / data_path
        if not data_path.is_file():
            manifest.update(status="blocked_missing_data", error="Data manifest unavailable; no performance computed.")
            finalize(root, manifest)
            return root, manifest
        if spec.get("data", {}).get("manifest_sha256") != digest(data_path):
            raise ValueError("Frozen data.manifest_sha256 must match the full data manifest, including provenance and rights")
        entry = spec["implementation"]["entrypoint"]
        if entry == "qg_infra_001_reference":
            from .infra import load_revision_dataset
            frame, dataset = load_revision_dataset(data_path)
            manifest["data_summary"] = {"events": len(frame.events), "queries": len(frame.queries),
                                        "instruments": int(frame.events.instrument.nunique()),
                                        "fields": int(frame.events.field.nunique())}
        else:
            frame, dataset = load_dataset(data_path)
            manifest["data_summary"] = {"observations": len(frame), "months": int(frame.date.nunique()),
                                        "instruments": int(frame.instrument.nunique())}
        dump(root / "data_manifest.json", dataset)
        manifest["data_sha256"] = dataset.get("sha256")
        manifest["data_manifest_sha256"] = digest(data_path)
        # A frozen spec must pin its dataset for any actual experiment.
        pinned = spec.get("data", {}).get("sha256")
        if pinned != dataset.get("sha256"):
            raise ValueError("Frozen spec data.sha256 must match the validated dataset fingerprint")
        synthetic = dataset.get("source", {}).get("kind") == "synthetic"
        if synthetic and spec["reproduction_level"] != "pipeline_demo":
            raise ValueError("Synthetic data is only allowed with reproduction_level=pipeline_demo")
        if not synthetic and spec["reproduction_level"] == "pipeline_demo":
            raise ValueError("pipeline_demo requires the declared synthetic data source")
        differences = spec.get("implementation", {}).get("undocumented_choices", [])
        if not synthetic and not differences:
            raise ValueError("Historical experiments must declare implementation.undocumented_choices")
        entry = spec["implementation"]["entrypoint"]
        if entry == "qg_infra_001_reference":
            from .infra import run_infra
            result = run_infra(spec, frame)
        elif entry == "qg_cs_001_reference":
            from .cross_sectional import run_factor
            result = run_factor(spec, frame)
        elif entry == "qg_model_001_reference":
            from .models import run_model
            result = run_model(spec, frame)
        else:
            result = run_reference(spec, frame)
        for name in ("signals", "positions", "returns", "diagnostics", "quantiles",
                     "factor_values", "features", "predictions", "prediction_diagnostics", "snapshots",
                     "reference_snapshots", "availability_audit", "benchmark", "benchmark_samples"):
            if name not in result:
                continue
            result[name].to_csv(root / (name + ".csv"), index=False, float_format="%.17g")
            if parquet:
                result[name].to_parquet(root / (name + ".parquet"), index=False)
        if "model" in result:
            dump(root / "model.json", result["model"])
        dump(root / "metrics.json", result["metrics"])
        dump(root / "checks.json", result["checks"])
        text = "# Implementation differences\n\n" + "\n".join("- " + str(x) for x in differences)
        text += ("\n\nReference: see experiment ID, source/evidence and implementation choices in the frozen spec.\n"
                 "Synthetic assets or a user-defined modern universe differ from any original historical sample.\n"
                 "Monthly return accounting does not model individual futures contracts, fills, margin, or intramonth trading.\n")
        if entry == "qg_infra_001_reference":
            text = "# Implementation differences\n\n" + "\n".join("- " + str(x) for x in differences)
            text += "\n\nOriginal in-memory data-query benchmark; no investment-return or external historical-data claim.\n"
        (root / "implementation_differences.md").write_text(text, encoding="utf-8")
        (root / "run.log").write_text("Validated frozen specification and dataset; reference runner completed.\n", encoding="utf-8")
        conclusion = result["metrics"].get("conclusion", result["checks"].get("conclusion", "inconclusive"))
        manifest.update(status="completed", conclusion="untested_synthetic" if synthetic else conclusion)
    except Exception as exc:
        manifest.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        (root / "run.log").write_text(manifest["error"] + "\n", encoding="utf-8")
    finalize(root, manifest)
    return root, manifest
