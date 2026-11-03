# QuantGlean reproduction report

- Run: 20261103T115029Z-72c32e7e
- Status: completed
- Level: pipeline_demo
- Conclusion: untested_synthetic
- Spec SHA256: f2dd249d5d98d459382dfbb9726e1aad4ee6cf01d318a6c8501298a33fc7b031
- Dataset SHA256: c92b38cdc0180258b1b32dc05eb4dc6385867a95569e4000705774bf520344e9
- Started (UTC): 2026-11-03T11:50:29.428092+00:00
- Code: {'commit': 'abb00055a7cd041aeae02fffdaf402aeb941b6e9', 'dirty': False, 'source_sha256': {'quantglean/__init__.py': '76d0319c60d765d2523052d098b89580daa64a4539b49b8b3a27f04f4e50cdab', 'quantglean/__main__.py': '935a1c1166b0c1ea35a82256345000bf2c73ded718d77773bc27a71ecce28f7d', 'quantglean/cli.py': '7d3644b3b21519f6d867fe1f6e72bc45c6fabbe9f492f671009faf31d30ac4cd', 'quantglean/data.py': 'f59a16988abc1d2265827f911edc46b6cf57b66b70109d4984cb9d3a182f586d', 'quantglean/engine.py': '6425e2ae0b9e8125186c397e525c3389e0d7d3b14dadcc235d8cf9de34e096c9', 'quantglean/reporting.py': 'ceedb2d907608b39322b43c743f64764077cf267dcdf3cbef4cf431dc8897435', 'quantglean/runs.py': 'fd77ac2dff375c8f2762d9f5344827dff3342d53b8c22b78c1485099170729b8', 'quantglean/specs.py': '4d5957ced9bb43c19fa6910b32d0f96c173c8814d8296faf03bfa6e7d5fe77a7'}}

Monthly constant-notional excess-return research accounting. Not a trade/fill simulator. Synthetic data tests the pipeline only. This implementation does not reproduce the original paper's historical results. QuantStats period statistics are not executed-trade statistics.

## Research source and protocol

Source record: https://github.com/runqiwang777/QuantGlean/blob/main/examples/aqr-century-trend-following/SOURCE.md
Report SHA256: 666f19c81a6932809fa69bb4f8746e531bb71912be7f554ce233eef73eb21d7c
Evidence IDs: E2, E3, E6
Evaluation: 2014-01-31 to 2023-12-31

## Measured net excess-return results

| Variant | Net Sharpe | Annual vol | Max drawdown | Mean turnover |
| --- | ---: | ---: | ---: | ---: |
| candidate | 0.483260 | 0.107643 | -0.305302 | 1.476738 |
| baseline | 0.490626 | 0.098526 | -0.255249 | 0.537837 |
| single_1 | 0.474913 | 0.090460 | -0.163488 | 1.871066 |
| single_3 | 0.300378 | 0.097107 | -0.246998 | 1.013128 |

Primary comparison (candidate minus fixed baseline): -0.007365707859156578
Interval: [-0.4677392321900822, 0.47504787667440995]
Conclusion: untested_synthetic

Full metrics below include twice-cost stress with unchanged positions.

## Recorded metrics

Undefined statistics are null. Sharpe uses excess returns and annualization 12.
Intervals are exploratory paired moving-block bootstrap estimates; they do not establish causality or remove selection bias.

```json
{
  "reproduction_level": "pipeline_demo",
  "conclusion": "untested_synthetic",
  "evaluation_start": "2014-01-31",
  "evaluation_end": "2023-12-31",
  "annualization": 12,
  "variants": {
    "candidate": {
      "observations": 120,
      "annualized_excess_geometric_growth": 0.047253399806897294,
      "annualized_volatility": 0.10764268754683987,
      "sharpe": 0.48325979748647063,
      "gross_sharpe": 0.6478563973498337,
      "gross_annualized_volatility": 0.10757731305524561,
      "gross_annualized_excess_geometric_growth": 0.06586019861177538,
      "max_drawdown": -0.3053016413274854,
      "average_turnover": 1.4767379176413655,
      "average_gross_leverage": 1.8381183109895403,
      "maximum_gross_leverage": 2.0000000000000004,
      "positive_compounded_wealth": true,
      "cost_sums": {
        "commission_cost": 0.017720855011696388,
        "spread_cost": 0.035441710023392775,
        "impact_cost": 0.017720855011696388,
        "financing_cost": 0.08381183109895403,
        "roll_cost": 0.022057419731874486,
        "total": 0.1767526708776141
      }
    },
    "baseline": {
      "observations": 120,
      "annualized_excess_geometric_growth": 0.044419061314517054,
      "annualized_volatility": 0.09852583909741705,
      "sharpe": 0.4906255053456272,
      "gross_sharpe": 0.6360517919292881,
      "gross_annualized_volatility": 0.09857038325322952,
      "gross_annualized_excess_geometric_growth": 0.05945941965154527,
      "max_drawdown": -0.25524918870378865,
      "average_turnover": 0.5378366574124936,
      "average_gross_leverage": 1.9441931559840324,
      "maximum_gross_leverage": 2.0000000000000004,
      "positive_compounded_wealth": true,
      "cost_sums": {
        "commission_cost": 0.006454039888949924,
        "spread_cost": 0.012908079777899848,
        "impact_cost": 0.006454039888949924,
        "financing_cost": 0.09441931559840323,
        "roll_cost": 0.023330317871808393,
        "total": 0.1435657930260113
      }
    },
    "single_1": {
      "observations": 120,
      "annualized_excess_geometric_growth": 0.039629062923110595,
      "annualized_volatility": 0.09045977157492469,
      "sharpe": 0.4749128354112448,
      "gross_sharpe": 0.7016182303942725,
      "gross_annualized_volatility": 0.09059438393517656,
      "gross_annualized_excess_geometric_growth": 0.06117497228513309,
      "max_drawdown": -0.1634884204136272,
      "average_turnover": 1.8710659612798688,
      "average_gross_leverage": 1.930450724715492,
      "maximum_gross_leverage": 2.0000000000000004,
      "positive_compounded_wealth": true,
      "cost_sums": {
        "commission_cost": 0.022452791535358424,
        "spread_cost": 0.04490558307071685,
        "impact_cost": 0.022452791535358424,
        "financing_cost": 0.0930450724715492,
        "roll_cost": 0.023165408696585905,
        "total": 0.20602164730956882
      }
    },
    "single_3": {
      "observations": 120,
      "annualized_excess_geometric_growth": 0.02474952203671665,
      "annualized_volatility": 0.09710703871547488,
      "sharpe": 0.30037832721963853,
      "gross_sharpe": 0.4711288993596102,
      "gross_annualized_volatility": 0.09700008110428654,
      "gross_annualized_excess_geometric_growth": 0.04180100490455812,
      "max_drawdown": -0.24699790421596157,
      "average_turnover": 1.0131283521158148,
      "average_gross_leverage": 1.9346138846154028,
      "maximum_gross_leverage": 2.0000000000000004,
      "positive_compounded_wealth": true,
      "cost_sums": {
        "commission_cost": 0.012157540225389778,
        "spread_cost": 0.024315080450779555,
        "impact_cost": 0.012157540225389778,
        "financing_cost": 0.0934613884615403,
        "roll_cost": 0.023215366615384838,
        "total": 0.16530691597848424
      }
    }
  },
  "comparison": {
    "metric": "net_sharpe_difference",
    "difference": -0.007365707859156578,
    "ci_lower": -0.4677392321900822,
    "ci_upper": 0.47504787667440995,
    "confidence": 0.95,
    "bootstrap_samples": 200,
    "bootstrap_valid_samples": 200,
    "bootstrap_block_periods": 6,
    "bootstrap_method": "paired moving blocks, sampled with replacement, truncated to evaluation length",
    "conclusion": "untested_synthetic",
    "diagnostic_direction": "inconclusive"
  },
  "cost_stress_2x": {
    "method": "twice every declared cost component; fixed original signals, positions and gross returns",
    "variants": {
      "candidate": {
        "observations": 120,
        "annualized_excess_geometric_growth": 0.028943630285268248,
        "annualized_volatility": 0.10771800226203736,
        "sharpe": 0.3188335800498558,
        "gross_sharpe": 0.6478563973498337,
        "gross_annualized_volatility": 0.10757731305524561,
        "gross_annualized_excess_geometric_growth": 0.06586019861177538,
        "max_drawdown": -0.3391929651920481,
        "average_turnover": 1.4767379176413655,
        "average_gross_leverage": 1.8381183109895403,
        "maximum_gross_leverage": 2.0000000000000004,
        "positive_compounded_wealth": true,
        "cost_sums": {
          "commission_cost": 0.035441710023392775,
          "spread_cost": 0.07088342004678555,
          "impact_cost": 0.035441710023392775,
          "financing_cost": 0.16762366219790806,
          "roll_cost": 0.04411483946374897,
          "total": 0.3535053417552282
        }
      },
      "baseline": {
        "observations": 120,
        "annualized_excess_geometric_growth": 0.02957383822266059,
        "annualized_volatility": 0.09848952879424899,
        "sharpe": 0.3450388148892778,
        "gross_sharpe": 0.6360517919292881,
        "gross_annualized_volatility": 0.09857038325322952,
        "gross_annualized_excess_geometric_growth": 0.05945941965154527,
        "max_drawdown": -0.2839928673870834,
        "average_turnover": 0.5378366574124936,
        "average_gross_leverage": 1.9441931559840324,
        "maximum_gross_leverage": 2.0000000000000004,
        "positive_compounded_wealth": true,
        "cost_sums": {
          "commission_cost": 0.012908079777899848,
          "spread_cost": 0.025816159555799696,
          "impact_cost": 0.012908079777899848,
          "financing_cost": 0.18883863119680647,
          "roll_cost": 0.046660635743616785,
          "total": 0.2871315860520226
        }
      },
      "single_1": {
        "observations": 120,
        "annualized_excess_geometric_growth": 0.01848346479262398,
        "annualized_volatility": 0.09034004810413307,
        "sharpe": 0.24749092288031704,
        "gross_sharpe": 0.7016182303942725,
        "gross_annualized_volatility": 0.09059438393517656,
        "gross_annualized_excess_geometric_growth": 0.06117497228513309,
        "max_drawdown": -0.19000080921954055,
        "average_turnover": 1.8710659612798688,
        "average_gross_leverage": 1.930450724715492,
        "maximum_gross_leverage": 2.0000000000000004,
        "positive_compounded_wealth": true,
        "cost_sums": {
          "commission_cost": 0.04490558307071685,
          "spread_cost": 0.0898111661414337,
          "impact_cost": 0.04490558307071685,
          "financing_cost": 0.1860901449430984,
          "roll_cost": 0.04633081739317181,
          "total": 0.41204329461913763
        }
      },
      "single_3": {
        "observations": 120,
        "annualized_excess_geometric_growth": 0.007952762634062176,
        "annualized_volatility": 0.09722830987605521,
        "sharpe": 0.1299843458028786,
        "gross_sharpe": 0.4711288993596102,
        "gross_annualized_volatility": 0.09700008110428654,
        "gross_annualized_excess_geometric_growth": 0.04180100490455812,
        "max_drawdown": -0.2825543498986107,
        "average_turnover": 1.0131283521158148,
        "average_gross_leverage": 1.9346138846154028,
        "maximum_gross_leverage": 2.0000000000000004,
        "positive_compounded_wealth": true,
        "cost_sums": {
          "commission_cost": 0.024315080450779555,
          "spread_cost": 0.04863016090155911,
          "impact_cost": 0.024315080450779555,
          "financing_cost": 0.1869227769230806,
          "roll_cost": 0.046430733230769676,
          "total": 0.3306138319569685
        }
      }
    }
  },
  "interpretation": "Synthetic results test the software pipeline only; bootstrap direction is not research evidence."
}
```

## Audit trail

See frozen_spec.json, data_manifest.json (when available), checks.json, implementation_differences.md, and artifact SHA256 values in run_manifest.json.
The manifest records the actual environment and command; inspect code.dirty before treating a commit as exact code provenance.
