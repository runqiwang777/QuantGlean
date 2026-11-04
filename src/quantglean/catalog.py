"""Read-only local run inventory, integrity checks and guarded metric comparison."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from .specs import canonical_hash

def read_manifest(root):
    record = json.loads((Path(root) / "run_manifest.json").read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("Run manifest must be a mapping")
    return record

def list_runs(directory):
    records = []
    for root in sorted(Path(directory).iterdir()):
        if root.is_dir() and (root / "run_manifest.json").is_file():
            try:
                record = read_manifest(root)
                spec_path = root / "frozen_spec.json"
                spec = json.loads(spec_path.read_text(encoding="utf-8")) if spec_path.is_file() else {}
                records.append({"directory": str(root), "run_id": record.get("run_id"), "experiment_id": spec.get("id"),
                                "status": record.get("status"), "conclusion": record.get("conclusion"),
                                "started_at": record.get("started_at"), "spec_hash": record.get("spec_hash"),
                                "code_commit": record.get("code", {}).get("commit")})
            except (ValueError, OSError) as exc:
                records.append({"directory": str(root), "status": "unreadable", "error": str(exc)})
    return records

def verify_run(directory):
    root = Path(directory).resolve()
    manifest = read_manifest(root)
    errors = []
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        return {"valid": False, "errors": ["No finalized artifact inventory"], "checked_files": 0}
    required = {"frozen_spec.json", "report.md", "report.html"}
    if manifest.get("status") == "completed":
        required |= {"metrics.json", "checks.json", "data_manifest.json", "implementation_differences.md", "run.log"}
    for name in sorted(required - set(artifacts)):
        errors.append("Required artifact absent from inventory: " + name)
    checked = 0
    for name, expected in artifacts.items():
        path = root / name
        if Path(name).name != name or "\\" in name or path.is_symlink() or path.resolve().parent != root:
            errors.append("Unsafe artifact name: " + name); continue
        if not path.is_file():
            errors.append("Missing artifact: " + name); continue
        checked += 1
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append("Checksum mismatch: " + name)
    spec_file = root / "frozen_spec.json"
    if spec_file.is_file() and not spec_file.is_symlink():
        try:
            spec = json.loads(spec_file.read_text(encoding="utf-8"))
            if not isinstance(spec, dict):
                raise ValueError("Frozen specification must be a mapping")
            actual = canonical_hash(spec)
            if spec.get("spec_hash") != actual or manifest.get("spec_hash") != actual:
                errors.append("Frozen specification fingerprint mismatch")
            if manifest.get("status") == "completed" and spec.get("data", {}).get("sha256") != manifest.get("data_sha256"):
                errors.append("Dataset fingerprint binding mismatch")
        except (ValueError, TypeError) as exc:
            errors.append("Invalid frozen specification: " + str(exc))
    else:
        errors.append("Frozen specification is unavailable")
    return {"valid": not errors, "errors": errors, "checked_files": checked,
            "scope": "Internal consistency/corruption check, not a signature, authorship proof or data-license audit"}

def compare_runs(first, second, metric):
    roots = [Path(first), Path(second)]
    manifests = [read_manifest(root) for root in roots]
    reasons = []
    for root in roots:
        verification = verify_run(root)
        if not verification["valid"]:
            reasons.append(str(root) + ": integrity verification failed")
    specs = [json.loads((root / "frozen_spec.json").read_text(encoding="utf-8")) for root in roots]
    for field in ("id", "artifact_type", "analysis_type", "reproduction_level", "validation"):
        if specs[0].get(field) != specs[1].get(field):
            reasons.append("Different " + field)
    if any(record.get("status") != "completed" for record in manifests):
        reasons.append("Both runs must be completed")
    if specs[0].get("data", {}).get("manifest_sha256") != specs[1].get("data", {}).get("manifest_sha256"):
        reasons.append("Different data manifests")
    if specs[0].get("artifact_type") == "infra" and specs[0].get("implementation", {}).get("benchmark") != specs[1].get("implementation", {}).get("benchmark"):
        reasons.append("Different benchmark protocols")
    if manifests[0].get("data_sha256") != manifests[1].get("data_sha256"):
        reasons.append("Different datasets")
    if manifests[0].get("code", {}).get("source_sha256") != manifests[1].get("code", {}).get("source_sha256"):
        reasons.append("Different implementation source hashes")
    if manifests[0].get("environment") != manifests[1].get("environment"):
        reasons.append("Different recorded environments")
    values = []
    for root in roots:
        value = json.loads((root / "metrics.json").read_text(encoding="utf-8"))
        for key in metric.split("."):
            if isinstance(value, dict) and key in value:
                value = value[key]
            elif isinstance(value, list) and key.isdecimal() and int(key) < len(value):
                value = value[int(key)]
            else:
                raise ValueError("Metric path is unavailable: " + metric)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("Metric must be a defined finite number")
        values.append(value)
    return {"comparable": not reasons, "reasons": reasons, "metric": metric, "values": values,
            "second_minus_first": values[1] - values[0] if not reasons else None,
            "interpretation": "A recorded scalar difference, not a hypothesis test or an automatic improvement claim"}
