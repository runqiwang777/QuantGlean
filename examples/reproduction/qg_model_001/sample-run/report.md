# QuantGlean reproduction report

- Run: 20261103T150823Z-2d976ada
- Status: completed
- Level: pipeline_demo
- Conclusion: untested_synthetic
- Spec SHA256: 1eeb94b52444e5fe9443fdb0d1212fc41768b678b522ebee7e04a31bf45a09b2
- Dataset SHA256: 8e0a87d2cd65b101c3e4f18b1a6c092435863560723e4bf8e45b5bb01e5bdfcd
- Started (UTC): 2026-11-03T15:08:23.694490+00:00
- Code: {'commit': 'fbbd41439f1716e5c77b031a50880d0905b78e09', 'dirty': False, 'source_sha256': {'quantglean/__init__.py': 'ae832ea0b449dfebcedd43125082c64da94cda8bfea92a6b5761f76ac019a7f6', 'quantglean/__main__.py': '935a1c1166b0c1ea35a82256345000bf2c73ded718d77773bc27a71ecce28f7d', 'quantglean/cli.py': 'c050acb691648509afb909565db2f2d2801371aa5547f76acca4dfc4dc31cd16', 'quantglean/cross_sectional.py': '2b1c6a3a0eb3e32c74bebf10e9a3579c5b19ffaa2122e6094e40a1a3eccf7366', 'quantglean/data.py': '92aab2808f511e1684931cf51501d19f9abfa909e3933bc7a5828c93bf445ff0', 'quantglean/engine.py': 'b42e59bf15b3f1e589e5aeb4d7aeaa36f7a090f44723fb173c419665f77b7051', 'quantglean/models.py': '4c7e1465646fb2feb9891700857c978c5121d87b9678087050296917ee43d9f8', 'quantglean/qlib_adapter.py': '20c6eeb86e79dcd3b9c65d3c50af534187fffd9f2075f73a2b140018c525fbae', 'quantglean/reporting.py': '061d91d7f1535b25e0af61eaa2b5fbcfc99f072e9f9b3c70a22c5db5df6210f1', 'quantglean/runs.py': '86b3313376196d72cada60216805ee8099f048ef112d0e0c86dc8ec83cb6dbba', 'quantglean/specs.py': 'b58081eeae7eec5d8fe1d25bbaf922f62552d2f9da6be5e76acae5652282befc'}}

Monthly constant-notional excess-return research accounting. Not a trade/fill simulator. Synthetic data tests the pipeline only. This implementation does not reproduce the original paper's historical results. QuantStats period statistics are not executed-trade statistics.

## Research source and protocol

Source record: https://github.com/runqiwang777/QuantGlean/blob/main/examples/reproduction/qg_model_001/SOURCE.md
Source SHA256: 904cfe0aec53f2f94c4677ba950d909276f16bea61540dc5486bb2508dd4c36a
Evidence IDs: D1, D2
Evaluation: 2018-02-28 to 2024-12-31

## Measured net excess-return results

| Variant | Net Sharpe | Annual vol | Max drawdown | Mean turnover |
| --- | ---: | ---: | ---: | ---: |
| candidate | -0.213733 | 0.050506 | -0.148049 | 0.572880 |
| baseline | -0.072138 | 0.039492 | -0.077100 | 0.603985 |

Primary comparison: test mean monthly MSE improvement over fixed training-mean predictor = -4.805568335884653e-07
Interval: [-1.0254695693582475e-05, 1.8945983339773116e-05]
Conclusion: untested_synthetic

Full metrics below include twice-cost stress with unchanged positions.

## Cross-sectional signal diagnostics

IC/RankIC compare each decision's scores with that holding month's subsequently observed returns.
Quintile returns in quantiles.csv are gross long-only bucket returns.

```json
{
  "candidate": {
    "mean_ic": -0.009275367685838868,
    "mean_rank_ic": -0.004670384323672392,
    "defined_rank_ic_months": 83,
    "mean_eligible_instruments": 17.40963855421687,
    "mean_feature_coverage": 1.0,
    "mean_eligible_fraction": 0.8704819277108438
  },
  "baseline": {
    "mean_ic": 0.02622509046674468,
    "mean_rank_ic": 0.03420026856652617,
    "defined_rank_ic_months": 83,
    "mean_eligible_instruments": 17.40963855421687,
    "mean_feature_coverage": 1.0,
    "mean_eligible_fraction": 0.8704819277108438
  }
}
```

## Forecast evaluation

Primary metric: baseline training-mean MSE minus candidate MSE, averaged equally across months.
Positive values indicate lower forecast error; this is distinct from the portfolio comparison.
Portfolio baseline: 12-1 momentum long-short; distinct from the forecast training-mean baseline

```json
{
  "valid": {
    "mse": 0.0014662651379725668,
    "baseline_train_mean_mse": 0.0014514224871899723,
    "mse_improvement": -1.484265078259455e-05,
    "months": 35,
    "rows": 610,
    "mean_rank_ic": 0.015177650007371377
  },
  "test": {
    "mse": 0.0014933340086872844,
    "baseline_train_mean_mse": 0.0014928534518536959,
    "mse_improvement": -4.805568335884653e-07,
    "months": 83,
    "rows": 1445,
    "mean_rank_ic": -0.004670384323672392
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
      "annualized_excess_geometric_growth": -0.011986622509558835,
      "annualized_volatility": 0.05050554311824512,
      "sharpe": -0.21373274170014106,
      "gross_sharpe": -0.060258432841997805,
      "gross_annualized_volatility": 0.05053011234139711,
      "gross_annualized_excess_geometric_growth": -0.004295055807223957,
      "max_drawdown": -0.1480490247852141,
      "average_turnover": 0.5728797543113632,
      "average_gross_leverage": 1.0,
      "maximum_gross_leverage": 1.0000000000000002,
      "positive_compounded_wealth": true,
      "cost_sums": {
        "commission_cost": 0.004754901960784313,
        "spread_cost": 0.009509803921568626,
        "impact_cost": 0.004754901960784313,
        "financing_cost": 5.551115123125783e-19,
        "roll_cost": 0.0,
        "short_borrow_cost": 0.03458333333333334,
        "total": 0.05360294117647059
      }
    },
    "baseline": {
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
    }
  },
  "cost_stress_2x": {
    "method": "double all declared costs with unchanged weights",
    "variants": {
      "candidate": {
        "observations": 83,
        "annualized_excess_geometric_growth": -0.01962387971087163,
        "annualized_volatility": 0.05048486603615251,
        "sharpe": -0.36732812184015573,
        "gross_sharpe": -0.060258432841997805,
        "gross_annualized_volatility": 0.05053011234139711,
        "gross_annualized_excess_geometric_growth": -0.004295055807223957,
        "max_drawdown": -0.1684959935482665,
        "average_turnover": 0.5728797543113632,
        "average_gross_leverage": 1.0,
        "maximum_gross_leverage": 1.0000000000000002,
        "positive_compounded_wealth": true,
        "cost_sums": {
          "commission_cost": 0.009509803921568626,
          "spread_cost": 0.019019607843137252,
          "impact_cost": 0.009509803921568626,
          "financing_cost": 1.1102230246251566e-18,
          "roll_cost": 0.0,
          "short_borrow_cost": 0.06916666666666668,
          "total": 0.10720588235294118
        }
      },
      "baseline": {
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
      }
    }
  },
  "factor_diagnostics": {
    "candidate": {
      "mean_ic": -0.009275367685838868,
      "mean_rank_ic": -0.004670384323672392,
      "defined_rank_ic_months": 83,
      "mean_eligible_instruments": 17.40963855421687,
      "mean_feature_coverage": 1.0,
      "mean_eligible_fraction": 0.8704819277108438
    },
    "baseline": {
      "mean_ic": 0.02622509046674468,
      "mean_rank_ic": 0.03420026856652617,
      "defined_rank_ic_months": 83,
      "mean_eligible_instruments": 17.40963855421687,
      "mean_feature_coverage": 1.0,
      "mean_eligible_fraction": 0.8704819277108438
    }
  },
  "reproduction_level": "pipeline_demo",
  "conclusion": "untested_synthetic",
  "comparison": {
    "metric": "mse_improvement",
    "difference": -4.805568335884653e-07,
    "ci_lower": -1.0254695693582475e-05,
    "ci_upper": 1.8945983339773116e-05,
    "confidence": 0.95,
    "observations": 83,
    "defined_observations": 83,
    "bootstrap_samples": 300,
    "bootstrap_block_periods": 6,
    "method": "paired monthly non-circular moving blocks; undefined months retain calendar positions",
    "conclusion": "untested_synthetic",
    "diagnostic_direction": "inconclusive"
  },
  "prediction_metrics": {
    "valid": {
      "mse": 0.0014662651379725668,
      "baseline_train_mean_mse": 0.0014514224871899723,
      "mse_improvement": -1.484265078259455e-05,
      "months": 35,
      "rows": 610,
      "mean_rank_ic": 0.015177650007371377
    },
    "test": {
      "mse": 0.0014933340086872844,
      "baseline_train_mean_mse": 0.0014928534518536959,
      "mse_improvement": -4.805568335884653e-07,
      "months": 83,
      "rows": 1445,
      "mean_rank_ic": -0.004670384323672392
    }
  },
  "primary_test": "test mean monthly MSE improvement over fixed training-mean predictor",
  "portfolio_baseline": "12-1 momentum long-short; distinct from the forecast training-mean baseline",
  "evaluation_start": "2018-02-28",
  "evaluation_end": "2024-12-31",
  "interpretation": "Prediction quality and portfolio performance are separate. Synthetic scenario only."
}
```

## Audit trail

See frozen_spec.json, data_manifest.json (when available), checks.json, implementation_differences.md, and artifact SHA256 values in run_manifest.json.
The manifest records the actual environment and command; inspect code.dirty before treating a commit as exact code provenance.
