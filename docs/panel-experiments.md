# Cross-sectional factors and predictive models

QuantGlean 0.3 adds two reviewed local runners and an optional Qlib training backend.
The reading Skill still works independently. All public results use original fictional data.

## Two runnable cases

| Case | Question | Primary comparison | Additional outputs |
| --- | --- | --- | --- |
| QG-CS-001 | Does a 12-1 momentum sort improve signal quality over a fixed 6-1 sort? | Mean monthly RankIC difference, paired monthly block interval | factor_values, diagnostics, quintile gross returns, positions, itemized costs |
| QG-MODEL-001 | Does one fixed ridge model forecast better than the training mean? | Monthly mean MSE improvement on the test segment | train-only transforms, model.json, validation/test predictions and errors |

Sources: [factor provenance](../examples/reproduction/qg_cs_001/SOURCE.md) and
[original model design](../examples/reproduction/qg_model_001/SOURCE.md).
The French momentum notes motivate the skip-month convention. Our synthetic excess-return,
equal-fraction quintile experiment does not implement its size-conditioned value-weighted historical factor.

## Quick start

From the repository root, after installing the core workflow:

```sh
python scripts/make-panel-fixture.py
qg freeze examples/reproduction/qg_cs_001/experiment.yaml --output local-work/frozen-cs.json
qg run local-work/frozen-cs.json --data-manifest ../examples/reproduction/qg_cs_001/data_manifest.json --output local-work/runs --parquet
qg freeze examples/reproduction/qg_model_001/experiment.yaml --output local-work/frozen-model.json
qg run local-work/frozen-model.json --data-manifest ../examples/reproduction/qg_model_001/data_manifest.json --output local-work/runs --parquet
```

Use a new frozen filename for each changed protocol. Manifest paths are resolved relative to the frozen specification.
The 20 fictional instruments have 240 months of complete returns and a preannounced changing eligibility schedule.
No financial downloads, credentials or source-report redistribution are required.

## Information timing and eligibility

Rows describe the **holding/label month t**. Features may use completed past months only.
Decision time is t's first calendar-day UTC boundary; the optimistic boundary-execution limitation from
[the core guide](reproduction.md) still applies.

- 12-1 momentum: compound excess returns t-12 through t-2 (11 months).
- 6-1 comparator: compound t-6 through t-2 (5 months).
- Reversal: minus the t-1 excess return.
- Volatility: sample standard deviation of t-12 through t-1, annualized by sqrt(12).

The panel CSV adds `eligible` (explicit Boolean) and `eligibility_available_at`.
That snapshot must be known by the holding-month decision. Future constituents cannot decide today's weights.
Ineligible instruments receive zero holdings; exits contribute to turnover and costs.

This release still requires a complete rectangular return history for the declared coverage universe.
It supports changing eligibility inside that coverage, not arbitrary IPO, missing-price or delisting histories.
Do not turn real delistings into filled zero returns or silently remove them. An appropriate dynamic-coverage data contract is future work.

## Portfolio and diagnostic conventions

Fractional quantile boundary allocation treats equal scores symmetrically, independent of symbol ordering.
Each diagnostic quantile is a fully invested long-only gross bucket.
The long-short portfolio allocates half the declared gross budget to the highest bucket and half to the lowest.
When ties overlap both tails, netted gross exposure can be smaller; a constant score produces no trade.

Returns use monthly constant-notional targets and L1 target turnover, including entry from flat.
No intramonth fills, wealth-normalized drift, contract ledger, sector neutralization or volatility matching is modeled.
Both strategies use the same gross budget; realized risk may differ. IC is Pearson cross-sectional correlation;
RankIC is Pearson correlation of average ranks. Undefined correlations are null, not zero.

Commission, spread, linear impact, financing above unit gross, roll and **short borrow** are separate cost columns.
The synthetic non-futures fixture explicitly sets roll to zero; the other costs are illustrative, not calibrated estimates.
Shortability, borrow availability, recalls and dynamic spreads are not simulated.
A two-times-cost diagnostic doubles every component with unchanged weights.
Financial returns and prediction improvements do not by themselves establish causal or investable alpha.

## Model chronology

The frozen reference uses:

- Train holding months: January 2007–December 2014.
- Gap: January 2015.
- Validation: February 2015–December 2017.
- Gap: January 2018.
- Test: February 2018–December 2024.

The one-month target is the holding month's simple excess return.
Feature means/population scales, response mean and ridge coefficients are fitted **once on eligible training rows**.
Alpha=1 is fixed; no validation tuning, validation refit, rolling retraining or test selection is performed.
Constant training columns use scale=1.
The complete gaps exceed this runner's single-month label horizon; multi-month overlapping targets are rejected.

Prediction metrics average per-month cross-sectional MSE equally over months.
The prediction baseline is the constant training mean.
The **portfolio** baseline is the fixed 12-1 momentum long-short rule; these baselines evaluate different outcomes.
Validation is diagnostic only; the predeclared primary interval uses test monthly MSE improvement.
Synthetic timestamps do not establish an untouched real-world holdout. Record every experiment and prior data access.

`model.json` contains train-only means/scales, coefficients, intercept, backend/version and fit timing.
It is plain JSON, not an executable/pickle model. Predictions are saved separately from model parameters.

## Optional Qlib backend

```sh
python -m pip install -e ".[qlib]"
```

Copy the model draft to a new path, set `implementation.backend: qlib`, then freeze and run that new spec.
The adapter is pinned to **pyqlib 0.9.7**. It uses public `StaticDataLoader`, `DataHandlerLP`, `DatasetH`
and `LinearModel.fit/predict` interfaces with in-memory, train-only-scaled inputs.
Inference labels are never supplied to Qlib. Its ridge estimator uses the same alpha and intercept convention.
No Qlib market provider, data download, expression execution, model pickle load or tracking service is started.

Qlib's own dependency set is substantially larger than the default core; install it only for that backend.
Dependencies retain their licenses. We authored the adapter; no upstream source is vendored.
Backend parity and inference-label independence have dedicated optional tests.
Qlib currently powers this fixed ridge experiment, not a general Alpha158/LightGBM or live trading integration.

## Public runs and remaining work

The [four-language lab](https://runqiwang777.github.io/QuantGlean/reproduction.html?lang=en&case=cs)
shows saved runs and links their reports, specs and metrics.
All synthetic conclusions stay `untested_synthetic`, including the bootstrap comparison.
A successful run verifies this declared workflow, not a paper's historical performance.

Next gates: permitted audited historical data, dynamic-coverage/delisting contracts, additional model families,
the point-in-time [infra benchmark and local run tools](infra.md) are available in 0.4; external experiment tracking remains optional future work.
