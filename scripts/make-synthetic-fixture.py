"""Original deterministic fictional data; no market data or report content."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
import random
from calendar import monthrange
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "examples" / "reproduction" / "qg_tf_001"

def build_fixture(target: Path = TARGET) -> None:
    target.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20261103)
    buf = io.StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["date", "instrument", "return", "available_at"])
    for t in range(180):
        year, month = 2009 + t // 12, t % 12 + 1
        date = f"{year:04}-{month:02}-{monthrange(year, month)[1]:02}"
        common = rng.gauss(0, .012)
        for j, symbol in enumerate(["SYN_A", "SYN_B", "SYN_C", "SYN_D"]):
            regime = .009 * math.sin((t + j * 8) / 13)
            value = regime + .006 * math.sin(t * .7 + j) + common * .4 + rng.gauss(0, .024 + j * .003)
            writer.writerow([date, symbol, f"{value:.12f}", date + "T23:59:59Z"])
    data = buf.getvalue().encode("utf-8")
    (target / "synthetic.csv").write_bytes(data)
    fingerprint = hashlib.sha256(data).hexdigest()
    manifest = {
        "schema_version": 1, "data_path": "synthetic.csv", "sha256": fingerprint,
        "source": {"kind": "synthetic", "description": "Original deterministic QuantGlean generator; seed 20261103; fictional returns only"},
        "rights": {"use_permitted": True, "redistribution_permitted": True,
                   "description": "Original fictional fixture released under the repository MIT license"},
        "frequency": "monthly", "returns_kind": "simple_excess",
        "universe": {"eligibility": "SYN_A/B/C/D fixed at inception; no real securities",
                     "survivorship": "Not applicable to fictional instruments"},
        "adjustments": "None; generated simple excess returns, not prices or futures contracts",
    }
    spec = {
        "id": "QG-TF-001", "spec_version": 1, "status": "draft",
        "artifact_type": "factor", "analysis_type": "time_series", "reproduction_level": "pipeline_demo",
        "source": {"case": "aqr-century-trend-following",
                   "url": "https://github.com/runqiwang777/QuantGlean/blob/main/examples/aqr-century-trend-following/SOURCE.md",
                   "sha256": "666f19c81a6932809fa69bb4f8746e531bb71912be7f554ce233eef73eb21d7c",
                   "evidence_ids": ["E2", "E3", "E6"]},
        "implementation": {
            "entrypoint": "qg_tf_001_reference", "lookbacks": [1, 3, 12], "baseline_lookback": 12,
            "volatility_lookback": 36, "min_volatility": .01, "target_volatility": .1,
            "max_gross_leverage": 2, "execution_lag_periods": 1, "rebalance": "monthly",
            "costs": {"commission_bps": 1, "spread_bps": 2, "impact_bps": 1,
                      "financing_bps_annual": 100, "roll_bps_per_period": 1},
            "undocumented_choices": [
                "Original synthetic monthly excess returns replace the original 67-market long-history sample.",
                "36-month sample covariance, annual volatility floor 1%, target volatility 10%, gross leverage capped at 2.",
                "Average equal-risk horizon weights then covariance scale; lag one monthly period.",
                "Reset constant-notional target exposures monthly; no intramonth execution or wealth-normalized drift.",
                "Illustrative costs are explicit but not calibrated: commission 1bp, spread 2bp, impact 1bp per unit turnover; annual financing 100bp above unit gross; roll 1bp per unit exposure/month.",
                "Fixed evaluation period and paired 6-month block bootstrap are analyst choices, not source-paper reproductions.",
            ],
        },
        "data": {"manifest": "data_manifest.json", "sha256": fingerprint,
                 "manifest_sha256": hashlib.sha256((json.dumps(manifest, indent=2) + "\n").encode("utf-8")).hexdigest()},
        "validation": {"evaluation_start": "2014-01-31", "evaluation_end": "2023-12-31",
                       "metric": "net_sharpe_difference", "annualization": 12, "bootstrap_samples": 200,
                       "bootstrap_block_periods": 6, "confidence": .95},
        "execution": {"seed": 7}, "missing_information": [],
    }
    for name, obj in [("data_manifest.json", manifest), ("experiment.yaml", spec)]:
        # JSON subset of YAML: deterministic, readable, safe_load compatible.
        (target / name).write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8", newline="\n")

if __name__ == "__main__":
    build_fixture()
    print(TARGET)
