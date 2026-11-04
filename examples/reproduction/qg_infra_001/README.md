# QG-INFRA-001 — point-in-time revision queries

**pipeline_demo / untested_synthetic**

An original infra component that distinguishes event time, publication and actual pipeline availability.
It compares a simple correct baseline with a batch indexed implementation, then measures fixed workloads
only after all query snapshots agree.

- [Original design and conventions](SOURCE.md)
- [Experiment](experiment.yaml) · [Two-file input manifest](data_manifest.json)
- [Actual saved run](sample-run/report.md)
- [Data contract, benchmark limits and run tools](../../../docs/infra.md)
- [Interactive saved-query walkthrough](https://runqiwang777.github.io/QuantGlean/infra.html?lang=en)

All revisions and queries are fictional. Timings are environment-specific and are not investment returns.
