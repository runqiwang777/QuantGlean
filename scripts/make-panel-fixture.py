"""Original fictional panel and two frozen-protocol experiment drafts; no market downloads."""
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
SOURCE_HASH = "c7ed8899d0074238675c4267bdaf6d02887c562a4894c6da223aa1562f38c77a"
SOURCE_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html"
def encoded(obj):
    return (json.dumps(obj, indent=2) + "\n").encode("utf-8")

def build_fixture(base: Path | None = None):
    base = base or ROOT / "examples" / "reproduction"
    rng = random.Random(20261104)
    buf = io.StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["date","instrument","return","available_at","eligible","eligibility_available_at"])
    latent = [rng.gauss(0, .006) for _ in range(20)]
    for t in range(240):
        year, month = 2005 + t // 12, t % 12 + 1
        date = f"{year:04}-{month:02}-{monthrange(year,month)[1]:02}"
        start = f"{year:04}-{month:02}-01T00:00:00Z"
        common = rng.gauss(0, .014)
        for j in range(20):
            latent[j] = .75 * latent[j] + rng.gauss(0, .004)
            value = .003 + latent[j] + .004 * math.sin((t+j*3)/17) + common + rng.gauss(0,.035)
            # Eligibility is a deterministic, preannounced schedule, independent of future returns.
            eligible = (t + 3*j) % 23 not in (0,1,2)
            writer.writerow([date,f"SYN_{j:02}",f"{value:.12f}",date+"T23:59:59Z",eligible,start])
    data = buf.getvalue().encode("utf-8")
    manifest = {"schema_version":1,"data_path":"synthetic.csv","sha256":hashlib.sha256(data).hexdigest(),
                "source":{"kind":"synthetic","description":"Original QuantGlean fictional generator; seed 20261104"},
                "rights":{"use_permitted":True,"redistribution_permitted":True,"description":"Original synthetic fixture released under MIT"},
                "frequency":"monthly","returns_kind":"simple_excess",
                "universe":{"eligibility":"Preannounced Boolean schedule, timestamped at start of each holding month; 20 fixed fictional histories",
                            "survivorship":"Fictional complete panel; no observed security or historical constituent claim"},
                "adjustments":"None. Generated excess returns; no prices, securities, corporate actions or delisting data."}
    for case, model in [("qg_cs_001",False),("qg_model_001",True)]:
        target=base/case
        target.mkdir(parents=True,exist_ok=True)
        (target/"synthetic.csv").write_bytes(data)
        (target/"data_manifest.json").write_bytes(encoded(manifest))
        source_text = (
            "# QG-MODEL-001 analyst research design\n\n"
            "This original note proposes a fixed-split ridge experiment. It is not an external paper result.\n\n"
            "## D1 — causal features\n\n"
            "At holding month t, momentum compounds simple excess returns t-12 through t-2; reversal is minus t-1 return; "
            "volatility is the annualized sample standard deviation over t-12 through t-1.\n\n"
            "## D2 — model and validation\n\n"
            "Fit feature means/scales and one ridge model only on eligible training rows. Alpha is fixed at 1. "
            "Compare validation/test MSE with the constant training-mean predictor. "
            "Portfolio diagnostics rank the prediction and separately compare with fixed 12-1 momentum. "
            "There is no tuning, refit on validation, or untouched real-world holdout claim.\n\n"
            "## References and differences\n\n"
            "Momentum convention context: " + SOURCE_URL + "\n"
            "Optional Qlib model API: https://qlib.readthedocs.io/en/latest/start/integration.html\n"
            "The equal-fraction synthetic portfolios are not the French size/value-weighted momentum factor.\n"
        ) if model else (
            "# QG-CS-001 source and analyst choices\n\n"
            "Primary source: Kenneth R. French, Monthly Momentum Factor construction notes.\n"
            "URL: " + SOURCE_URL + "\n"
            "Inspected 2026-11-03; source HTML SHA256: " + SOURCE_HASH + "\n\n"
            "## E1 — formation window\n\n"
            "The source describes a momentum sort using prior months 2 through 12, omitting the immediately preceding month.\n\n"
            "## E2 — original construction boundary\n\n"
            "Its momentum factor combines size-conditioned value-weighted portfolios and specific historical stock eligibility. "
            "QuantGlean instead tests equal-fraction quintiles on original fictional excess returns. "
            "The fixed 6-1 comparator, costs, universe, evaluation and bootstrap are analyst-defined choices.\n\n"
            "We link the source; no source page, market return file or chart is redistributed.\n"
        )
        source_bytes = source_text.encode("utf-8")
        (target/"SOURCE.md").write_bytes(source_bytes)
        source = {"case":case,"url":("https://github.com/runqiwang777/QuantGlean/blob/main/examples/reproduction/"+case+"/SOURCE.md") if model else SOURCE_URL,
                  "sha256":hashlib.sha256(source_bytes).hexdigest() if model else SOURCE_HASH,
                  "evidence_ids":["D1","D2"] if model else ["E1","E2"]}
        implementation = {"entrypoint":"qg_model_001_reference" if model else "qg_cs_001_reference",
                          "lookback_periods":12,"skip_periods":1,"baseline_lookback_periods":6,
                          "execution_lag_periods":1,"rebalance":"monthly","quantiles":5,"gross_leverage":1.,
                          "costs":{"commission_bps":1,"spread_bps":2,"impact_bps":1,
                                   "financing_bps_annual":100,"roll_bps_per_period":0,"short_borrow_bps_annual":100},
                          "undocumented_choices":[
                              "Original synthetic excess-return panel and preannounced eligibility replace any historical market universe.",
                              "12-1 compounds t-12 through t-2; fixed 6-1 baseline compounds t-6 through t-2.",
                              "Equal-fraction quintiles split boundary ties symmetrically; 50% long top and 50% short bottom, no volatility matching.",
                              "Monthly constant-notional targets; L1 target turnover, flat initial holdings; no intramonth drift/fill simulation.",
                              "Costs are illustrative: commission/spread/impact 1/2/1bp, 100bp annual short borrow, zero roll for this fictional non-futures panel.",
                              "Frozen calendar evaluation and paired moving-block bootstrap are analyst protocol choices."
                          ]}
        validation = {"evaluation_start":"2018-02-28","evaluation_end":"2024-12-31",
                      "metric":"mse_improvement" if model else "rank_ic_improvement","annualization":12,
                      "bootstrap_samples":300,"bootstrap_block_periods":6,"confidence":.95}
        if model:
            implementation.update(backend="numpy",ridge_alpha=1.,features=["momentum_12_1","reversal_1","volatility_12"],label_horizon_periods=1)
            implementation["undocumented_choices"] += [
                "Training-only feature means and population scales; one fixed-alpha ridge fit, no model selection or validation refit.",
                "Forecast baseline is training mean; portfolio baseline is 12-1 momentum. These compare different outcomes."
            ]
            validation.update(train_start="2007-01-31",train_end="2014-12-31",
                              valid_start="2015-02-28",valid_end="2017-12-31",gap_periods=1)
        spec={"id":"QG-MODEL-001" if model else "QG-CS-001","spec_version":1,"status":"draft",
              "artifact_type":"model" if model else "factor","analysis_type":"predictive" if model else "cross_sectional",
              "reproduction_level":"pipeline_demo","source":source,"implementation":implementation,
              "data":{"manifest":"data_manifest.json","sha256":manifest["sha256"],
                      "manifest_sha256":hashlib.sha256(encoded(manifest)).hexdigest()},
              "validation":validation,"execution":{"seed":11},"missing_information":[]}
        (target/"experiment.yaml").write_bytes(encoded(spec))
    print(base)

if __name__=="__main__":
    build_fixture()
