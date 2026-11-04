# From a research note to a reproducible experiment

QuantGlean 0.2 adds a local Python workflow alongside the independently usable reading skill.
The first executable case is QG-TF-001: a monthly time-series trend reference implementation.
Version 0.3 also runs cross-sectional momentum and a fixed-split ridge model; see the [panel/model guide](panel-experiments.md). Version 0.4 adds the [point-in-time infra runner and local run tools](infra.md).

## Install and run

Python 3.10+; from the repository root:

```sh
python -m venv .venv
# Activate .venv using your shell, then:
python -m pip install -e ".[dev,parquet,reports]"
python scripts/make-synthetic-fixture.py
qg validate examples/reproduction/qg_tf_001/experiment.yaml
qg freeze examples/reproduction/qg_tf_001/experiment.yaml --output local-work/frozen-demo.json
qg run local-work/frozen-demo.json --data-manifest ../examples/reproduction/qg_tf_001/data_manifest.json --output local-work/runs --parquet
qg report local-work/runs/<run-id> --quantstats
python -m pytest -q
```

The data-manifest argument is resolved relative to the frozen specification, including explicit CLI overrides. Use an absolute manifest path for a custom location.
Choose a fresh frozen-spec filename for a new experiment. Every run has a unique directory.
The checked-in sample uses only original synthetic data. No paid data, reports, or financial API credentials are needed.

On Windows, keep the clone, virtual environment, temporary directory, pip cache and Matplotlib cache on the drive you choose.
For this project's maintainer all project assets remain under D:/Github/QuantGlean.
The optional reports extra installs QuantStats and its dependencies; the core reference runner does not require it.

## Commands and states

- `qg validate SPEC`: inspect machine-readable errors.
- `qg freeze SPEC --output FILE`: validate, set spec_ready, hash canonical JSON, refuse overwriting a file.
- `qg scaffold SPEC --output NEW_DIRECTORY`: create an original task brief; does not execute report-supplied code.
- `qg run SPEC --data-manifest FILE --output DIRECTORY [--parquet]`: execute a reviewed reference runner.
- `qg report RUN_DIRECTORY [--quantstats]`: render recorded artifacts; optional local-return-series adapter.

A run ends in completed, failed, or blocked_missing_data. Missing data creates an audit record and a nonzero exit status without performance.
Completion is independent of the research conclusion. Synthetic results always say untested_synthetic.
Levels: pipeline_demo, method_reimplementation, inspired_extension. result_reproduction is deliberately rejected in this release.
A user-supplied historical dataset does not automatically qualify as an exact paper reproduction.

## Frozen specification

See [the complete example](../examples/reproduction/qg_tf_001/experiment.yaml).
Required concepts include source/evidence references, formula choices, data fingerprint, costs, fixed baseline, evaluation bounds, primary metric, bootstrap design and seed.
This page describes factor/time_series and the built-in monthly trend reference; additional reviewed panel/model runners are documented separately. It does not import arbitrary entrypoints.

Signals are signs of compounded 1/3/12-month simple excess returns.
Candidate horizons share an equal-risk construction; the fixed baseline is 12 months, with 1/3-month diagnostic ablations.
Risk estimates use historical monthly covariance, a volatility floor, target volatility and a gross leverage cap.
Positions are lagged at least one period.
Accounting is constant-notional monthly research accounting: each month resets to the lagged target weight vector; no intramonth drift is simulated.
Absolute changes in successive target weights determine charged turnover. This omits wealth-normalized weight drift and is not an executable futures ledger.
Commission, spread, impact, financing and roll charges are separate explicit parameters. Demo values are illustrative, not calibrated market estimates.
All returns are excess returns; risk-free return is not subtracted a second time. Geometric growth is excess-series growth, not total account CAGR.

The primary comparison is the candidate minus baseline net Sharpe, with paired moving-block bootstrap.
Its conditional interval is an exploratory uncertainty estimate; it does not correct repeated trials or establish a prospective holdout.
There is no fitting or automatic parameter search in this runner.
Historical experiments must protect their chosen test period externally, disclose prior access and record each attempted spec.
Changing horizons after inspecting the result creates a new exploratory trial, not an untouched test.

## Local data contract

See [the synthetic manifest](../examples/reproduction/qg_tf_001/data_manifest.json).
CSV or optional Parquet is read from a local path; remote URLs are rejected.
Long-form columns are `date,instrument,return,available_at`.
`date` is month-end. `return` is a finite simple excess return greater than -1.
Every instrument must have the same complete consecutive monthly calendar.
No forward fill, silent drop, new listing interpolation, or survivorship correction is applied.
An unbalanced historical universe must be prepared under an explicitly documented eligibility rule before using this limited runner.

`available_at` is the UTC time the period observation was actually available.
It must be no later than the next month boundary; positions then use observations at least one month old.
This is an explicit optimistic boundary execution convention, not proof that any real market offered a tradable price at that instant.
Datasets published later cannot be made valid by relabeling timestamps. Use another runner with a suitable decision calendar.

Pin the dataset SHA256 in both manifest and frozen spec. Also pin the complete manifest bytes as data.manifest_sha256, so provenance, permissions and eligibility changes require a new frozen spec.
Declare source kind (synthetic or user_supplied), provenance, frequency, return definition,
historical universe eligibility and data-use rights.
`use_permitted` must be true for local execution.
`redistribution_permitted` is a separate declaration and never inferred from public accessibility.
These declarations and hashes support auditing; software cannot independently prove a data license or timestamp.
Keep restricted data and derived artifacts private when the source terms require it.

## Run package

Always: run_manifest.json, frozen_spec.json, report.md/html, run.log when executed.
On success: data_manifest.json, signals.csv, positions.csv, returns.csv, metrics.json, checks.json,
implementation_differences.md; `--parquet` adds matching Parquet outputs.
Optional: quantstats.html, generated from local net excess-return series and the baseline.
The manifest records seed, actual dependency versions, code commit/dirty flag, per-source hashes and artifact hashes.
When code is dirty, source hashes identify the implementation; a commit alone is insufficient.
The manifest excludes its own hash to avoid a circular checksum.
No run directory is reused. Reporting only refreshes the presentation and artifact hashes.

## Scope and next milestones

The AQR source motivates the question; this implementation is independently written from the stated specification.
It uses neither the original 137-year dataset nor its full contract/execution conventions.
The four-language [website](https://runqiwang777.github.io/QuantGlean/) displays an actual saved synthetic run, with downloadable records.
GitHub Pages is static: it does not execute Python or accept uploaded private reports.

Available in 0.3: decision-time-eligible cross-sectional factor and fixed-split ridge examples, with an optional Qlib backend. Next: audited historical data, richer coverage contracts, measured infra benchmarks and experiment tracking;
finally an optional budgeted RD-Agent adapter after the evidence/verification layer is stable.
No upstream source is vendored. See [rights and dependency notes](../THIRD_PARTY_NOTICES.md).
