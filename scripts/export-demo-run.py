"""Publish only an explicitly permitted synthetic run, never arbitrary local data."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def export(run_dir: Path) -> None:
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    dataset = json.loads((run_dir / "data_manifest.json").read_text(encoding="utf-8"))
    spec = json.loads((run_dir / "frozen_spec.json").read_text(encoding="utf-8"))
    if not (manifest["status"] == "completed" and manifest["reproduction_level"] == "pipeline_demo"
            and manifest["conclusion"] == "untested_synthetic" and dataset["source"]["kind"] == "synthetic"
            and dataset["rights"]["redistribution_permitted"] is True):
        raise ValueError("Only completed, permitted synthetic pipeline_demo runs can be exported by this script")
    for name, expected in manifest["artifacts"].items():
        if Path(name).name != name or hashlib.sha256((run_dir / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Artifact mismatch: " + name)
    target = ROOT / "examples" / "reproduction" / "qg_tf_001" / "sample-run"
    if target.exists():
        raise FileExistsError("Public sample already exists; review and replace it explicitly")
    shutil.copytree(run_dir, target)
    frame = pd.read_csv(run_dir / "returns.csv")
    variants = []
    for name in ("candidate", "baseline", "single_1", "single_3"):
        f = frame[frame.variant == name]
        series = f.net_return
        std = float(series.std(ddof=1))
        wealth = np.r_[1., np.cumprod(1 + series.to_numpy())]
        drawdown = wealth / np.maximum.accumulate(wealth) - 1
        variants.append({"name": name, "net_sharpe": float(series.mean() / std * np.sqrt(12)) if std > 0 else None,
                         "annualized_volatility": std * np.sqrt(12), "max_drawdown": float(drawdown.min()),
                         "mean_turnover": float(f.turnover.mean())})
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    comparison = metrics["comparison"]
    summary = {"run_id": manifest["run_id"], "evaluation_start": spec["validation"]["evaluation_start"],
               "evaluation_end": spec["validation"]["evaluation_end"], "variants": variants,
               "comparison": {"difference": comparison["difference"], "lower": comparison["ci_lower"], "upper": comparison["ci_upper"]},
               "provenance": {"code": manifest["code"], "spec_hash": manifest["spec_hash"],
                              "data_sha256": manifest["data_sha256"], "metrics_sha256": manifest["artifacts"]["metrics.json"],
                              "reproduction_level": manifest["reproduction_level"], "conclusion": manifest["conclusion"]}}
    out = ROOT / "site" / "reproduction"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(target)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    export(parser.parse_args().run_directory)
