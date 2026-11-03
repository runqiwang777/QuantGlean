# QG-MODEL-001 — fixed-split ridge forecasting

**pipeline_demo / untested_synthetic**

Three causal features, one training-only ridge fit, fixed alpha, chronological train/validation/test segments
and complete one-month gaps. Forecast MSE is compared with the training mean; portfolio outcomes separately
compare ranked model predictions with the 12-1 momentum rule.

- [Original research design](SOURCE.md)
- [Experiment](experiment.yaml) · [Data manifest](data_manifest.json)
- [Saved actual run](sample-run/report.md)
- [Optional Qlib backend and protocol](../../../docs/panel-experiments.md)

Inputs are original fictional data. Parameters are plain JSON; no arbitrary generated code is executed.
