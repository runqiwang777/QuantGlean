"""Export reviewed, permitted synthetic panel runs; refuse arbitrary destinations."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
CASES = {"cs": ("qg_cs_001", "qg_cs_001_reference"), "model": ("qg_model_001", "qg_model_001_reference")}
def export(run: Path, case: str):
    folder, entry = CASES[case]
    manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    spec = json.loads((run / "frozen_spec.json").read_text(encoding="utf-8"))
    data = json.loads((run / "data_manifest.json").read_text(encoding="utf-8"))
    if not (manifest["status"] == "completed" and manifest["conclusion"] == "untested_synthetic"
            and manifest["reproduction_level"] == "pipeline_demo" and data["source"]["kind"] == "synthetic"
            and data["rights"]["redistribution_permitted"] is True and spec["implementation"]["entrypoint"] == entry):
        raise ValueError("Only the declared, completed and permitted synthetic reference can be published")
    if manifest["code"]["dirty"] is not False:
        raise ValueError("Commit implementation before publishing its reference run")
    for name, expected in manifest["artifacts"].items():
        if Path(name).name != name or hashlib.sha256((run / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Artifact mismatch: " + name)
    target = ROOT / "examples" / "reproduction" / folder / "sample-run"
    if target.exists():
        raise FileExistsError("Review and replace an existing public sample explicitly")
    metrics = json.loads((run / "metrics.json").read_text(encoding="utf-8"))
    summary = {"case": case, "id": spec["id"], "run_id": manifest["run_id"],
               "input_months": manifest["data_summary"]["months"], "input_instruments": manifest["data_summary"]["instruments"],
               "evaluation_start": spec["validation"]["evaluation_start"], "evaluation_end": spec["validation"]["evaluation_end"],
               "variants": [{"name": name, "net_sharpe": row["sharpe"], "annualized_volatility": row["annualized_volatility"],
                             "max_drawdown": row["max_drawdown"], "mean_turnover": row["average_turnover"]}
                            for name, row in metrics["variants"].items()],
               "comparison": {"metric": metrics["comparison"]["metric"], "confidence": metrics["comparison"]["confidence"], "difference": metrics["comparison"]["difference"],
                              "lower": metrics["comparison"]["ci_lower"], "upper": metrics["comparison"]["ci_upper"]},
               "factor_diagnostics": metrics["factor_diagnostics"], "prediction_metrics": metrics.get("prediction_metrics"),
               "provenance": {"code": manifest["code"], "spec_hash": manifest["spec_hash"], "data_sha256": manifest["data_sha256"],
                              "metrics_sha256": manifest["artifacts"]["metrics.json"], "reproduction_level": manifest["reproduction_level"],
                              "conclusion": manifest["conclusion"]}}
    shutil.copytree(run, target)
    out = ROOT / "site/reproduction" / (case + "-summary.json")
    out.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(target)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--case", required=True, choices=CASES)
    args = parser.parse_args()
    export(args.run_directory, args.case)
