# QuantGlean reproduction report

- Run: 20261103T150823Z-e0349e56
- Status: completed
- Level: pipeline_demo
- Conclusion: untested_synthetic
- Spec SHA256: 41e856db4c3630dc9b9cda9fc889034c1d96e84075e32d0ae058dec2bc0029d5
- Dataset SHA256: 8e0a87d2cd65b101c3e4f18b1a6c092435863560723e4bf8e45b5bb01e5bdfcd
- Started (UTC): 2026-11-03T15:08:23.694490+00:00
- Code: {'commit': 'fbbd41439f1716e5c77b031a50880d0905b78e09', 'dirty': False, 'source_sha256': {'quantglean/__init__.py': 'ae832ea0b449dfebcedd43125082c64da94cda8bfea92a6b5761f76ac019a7f6', 'quantglean/__main__.py': '935a1c1166b0c1ea35a82256345000bf2c73ded718d77773bc27a71ecce28f7d', 'quantglean/cli.py': 'c050acb691648509afb909565db2f2d2801371aa5547f76acca4dfc4dc31cd16', 'quantglean/cross_sectional.py': '2b1c6a3a0eb3e32c74bebf10e9a3579c5b19ffaa2122e6094e40a1a3eccf7366', 'quantglean/data.py': '92aab2808f511e1684931cf51501d19f9abfa909e3933bc7a5828c93bf445ff0', 'quantglean/engine.py': 'b42e59bf15b3f1e589e5aeb4d7aeaa36f7a090f44723fb173c419665f77b7051', 'quantglean/models.py': '4c7e1465646fb2feb9891700857c978c5121d87b9678087050296917ee43d9f8', 'quantglean/qlib_adapter.py': '20c6eeb86e79dcd3b9c65d3c50af534187fffd9f2075f73a2b140018c525fbae', 'quantglean/reporting.py': '061d91d7f1535b25e0af61eaa2b5fbcfc99f072e9f9b3c70a22c5db5df6210f1', 'quantglean/runs.py': '86b3313376196d72cada60216805ee8099f048ef112d0e0c86dc8ec83cb6dbba', 'quantglean/specs.py': 'b58081eeae7eec5d8fe1d25bbaf922f62552d2f9da6be5e76acae5652282befc'}}

Monthly constant-notional excess-return research accounting. Not a trade/fill simulator. Synthetic data tests the pipeline only. This implementation does not reproduce the original paper's historical results. QuantStats period statistics are not executed-trade statistics.

## Research source and protocol

Source record: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html
Source SHA256: c7ed8899d0074238675c4267bdaf6d02887c562a4894c6da223aa1562f38c77a
Evidence IDs: E1, E2
Evaluation: 2018-02-28 to 2024-12-31

## Measured net excess-return results

| Variant | Net Sharpe | Annual vol | Max drawdown | Mean turnover |
| --- | ---: | ---: | ---: | ---: |
| candidate | -0.072138 | 0.039492 | -0.077100 | 0.603985 |
| baseline | 0.028284 | 0.039860 | -0.094037 | 0.799236 |

Primary comparison: mean monthly RankIC improvement over fixed 6-1 momentum = 0.016082907481318468
Interval: [-0.018336154214380743, 0.06437499222897783]
Conclusion: untested_synthetic

Full metrics below include twice-cost stress with unchanged positions.

## Cross-sectional signal diagnostics

IC/RankIC compare each decision's scores with that holding month's subsequently observed returns.
Quintile returns in quantiles.csv are gross long-only bucket returns.

```json
{
  "candidate": {
    "mean_ic": 0.02622509046674468,
    "mean_rank_ic": 0.03420026856652617,
    "defined_rank_ic_months": 83,
    "mean_eligible_instruments": 17.40963855421687,
    "mean_feature_coverage": 1.0,
    "mean_eligible_fraction": 0.8704819277108438
  },
  "baseline": {
    "mean_ic": 0.01517382847002896,
    "mean_rank_ic": 0.018117361085207704,
    "defined_rank_ic_months": 83,
    "mean_eligible_instruments": 17.40963855421687,
    "mean_feature_coverage": 1.0,
    "mean_eligible_fraction": 0.8704819277108438
  }
}
```

## Recorded metrics

Undefined statistics are null. Sharpe uses excess returns and annualization 12.
Intervals are exploratory paired moving-block bootstrap estimates; they do not establish causality or remove selection bias.

```json
{
  "variants": {
    "candidate": {
      "observations": 83,
      "annualized_excess_geometric_growth": -0.0036131750567967077,
      "annualized_volatility": 0.03949201273338352,
      "sharpe": -0.07213812699959586,
      "gross_sharpe": 0.12790183184195097,
      "gross_annualized_volatility": 0.03948533037147233,
      "gross_annualized_excess_geometric_growth": 0.0042890884100411164,
      "max_drawdown": -0.07709987847904409,
      "average_turnover": 0.6039845657138359,
      "average_gross_leverage": 1.0,
      "maximum_gross_leverage": 1.0000000000000002,
      "positive_compounded_wealth": true,
      "cost_sums": {
        "commission_cost": 0.005013071895424835,
        "spread_cost": 0.01002614379084967,
        "impact_cost": 0.005013071895424835,
        "financing_cost": 7.401486830834377e-19,
        "roll_cost": 0.0,
        "short_borrow_cost": 0.03458333333333334,
        "total": 0.05463562091503269
      }
    },
    "baseline": {
      "observations": 83,
      "annualized_excess_geometric_growth": 0.0003420946293558389,
      "annualized_volatility": 0.03985964952437895,
      "sharpe": 0.02828431711589391,
      "gross_sharpe": 0.2497827579729918,
      "gross_annualized_volatility": 0.03988960894540878,
      "gross_annualized_excess_geometric_growth": 0.009216452934283123,
      "max_drawdown": -0.0940372607872405,
      "average_turnover": 0.7992361603275848,
      "average_gross_leverage": 1.0,
      "maximum_gross_leverage": 1.0000000000000002,
      "positive_compounded_wealth": true,
      "cost_sums": {
        "commission_cost": 0.006633660130718955,
        "spread_cost": 0.01326732026143791,
        "impact_cost": 0.006633660130718955,
        "financing_cost": 9.251858538542971e-19,
        "roll_cost": 0.0,
        "short_borrow_cost": 0.03458333333333334,
        "total": 0.06111797385620916
      }
    }
  },
  "cost_stress_2x": {
    "method": "double all declared costs with unchanged weights",
    "variants": {
      "candidate": {
        "observations": 83,
        "annualized_excess_geometric_growth": -0.011458498378042838,
        "annualized_volatility": 0.0395011372559456,
        "sharpe": -0.27209357735236167,
        "gross_sharpe": 0.12790183184195097,
        "gross_annualized_volatility": 0.03948533037147233,
        "gross_annualized_excess_geometric_growth": 0.0042890884100411164,
        "max_drawdown": -0.11322756032399084,
        "average_turnover": 0.6039845657138359,
        "average_gross_leverage": 1.0,
        "maximum_gross_leverage": 1.0000000000000002,
        "positive_compounded_wealth": true,
        "cost_sums": {
          "commission_cost": 0.01002614379084967,
          "spread_cost": 0.02005228758169934,
          "impact_cost": 0.01002614379084967,
          "financing_cost": 1.4802973661668755e-18,
          "roll_cost": 0.0,
          "short_borrow_cost": 0.06916666666666668,
          "total": 0.10927124183006538
        }
      },
      "baseline": {
        "observations": 83,
        "annualized_excess_geometric_growth": -0.00846080218591828,
        "annualized_volatility": 0.03983282853852776,
        "sharpe": -0.19353209112027092,
        "gross_sharpe": 0.2497827579729918,
        "gross_annualized_volatility": 0.03988960894540878,
        "gross_annualized_excess_geometric_growth": 0.009216452934283123,
        "max_drawdown": -0.11090462985577032,
        "average_turnover": 0.7992361603275848,
        "average_gross_leverage": 1.0,
        "maximum_gross_leverage": 1.0000000000000002,
        "positive_compounded_wealth": true,
        "cost_sums": {
          "commission_cost": 0.01326732026143791,
          "spread_cost": 0.02653464052287582,
          "impact_cost": 0.01326732026143791,
          "financing_cost": 1.8503717077085942e-18,
          "roll_cost": 0.0,
          "short_borrow_cost": 0.06916666666666668,
          "total": 0.12223594771241832
        }
      }
    }
  },
  "factor_diagnostics": {
    "candidate": {
      "mean_ic": 0.02622509046674468,
      "mean_rank_ic": 0.03420026856652617,
      "defined_rank_ic_months": 83,
      "mean_eligible_instruments": 17.40963855421687,
      "mean_feature_coverage": 1.0,
      "mean_eligible_fraction": 0.8704819277108438
    },
    "baseline": {
      "mean_ic": 0.01517382847002896,
      "mean_rank_ic": 0.018117361085207704,
      "defined_rank_ic_months": 83,
      "mean_eligible_instruments": 17.40963855421687,
      "mean_feature_coverage": 1.0,
      "mean_eligible_fraction": 0.8704819277108438
    }
  },
  "reproduction_level": "pipeline_demo",
  "conclusion": "untested_synthetic",
  "comparison": {
    "metric": "rank_ic_improvement",
    "difference": 0.016082907481318468,
    "ci_lower": -0.018336154214380743,
    "ci_upper": 0.06437499222897783,
    "confidence": 0.95,
    "observations": 83,
    "defined_observations": 83,
    "bootstrap_samples": 300,
    "bootstrap_block_periods": 6,
    "method": "paired monthly non-circular moving blocks; undefined months retain calendar positions",
    "conclusion": "untested_synthetic",
    "diagnostic_direction": "inconclusive"
  },
  "evaluation_start": "2018-02-28",
  "evaluation_end": "2024-12-31",
  "primary_test": "mean monthly RankIC improvement over fixed 6-1 momentum",
  "quantile_returns": "long-only equal-fraction buckets, gross before costs",
  "interpretation": "Synthetic software scenario only; not a French momentum factor replication."
}
```

## Audit trail

See frozen_spec.json, data_manifest.json (when available), checks.json, implementation_differences.md, and artifact SHA256 values in run_manifest.json.
The manifest records the actual environment and command; inspect code.dirty before treating a commit as exact code provenance.
