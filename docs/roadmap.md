# Alpha reproduction roadmap

The reading Skill remains the entry point. QuantGlean owns the evidence, experiment specifications,
validation and result records. Mature computation engines are optional adapters.

| Stage | Scope | Current status |
| --- | --- | --- |
| 1 | Frozen specs, local data contract, QG-TF-001 time-series reference, cost accounting, reports, synthetic tests | Implemented in 0.2; historical method results await a permitted audited dataset |
| 2 | Point-in-time cross-sectional factor and fixed-split model example; optional Qlib adapter | Planned |
| 3 | Data-availability infra component, correctness/performance benchmark, optional MLflow/DVC tracking | Planned |
| 4 | Optional Linux/WSL RD-Agent adapter with budget, attempt records and protected final test | Planned |

## Gates before expanding

- Preserve source/evidence links through each implementation and run.
- Keep pipeline demos distinct from historical method tests and exact original-result reproduction.
- Use a metric appropriate to the task: time-series portfolio statistics, cross-sectional diagnostics, model prediction quality, or infra correctness/latency/memory.
- Freeze the baseline and primary protocol before evaluation. Record failed and exploratory attempts.
- Do not fit preprocessing or select parameters on the final test. Handle overlapping labels when supervised models are added.
- Bring your own data with documented provenance, historical universe and use/publication rights.
- Review each new dependency's actual license and compatibility before integration; process separation is not license clearance.
- Publish only permitted original artifacts. GitHub Pages displays static results and does not run research jobs.

The first runner deliberately handles a complete fixed monthly panel and a small reviewed strategy family.
Dynamic universes, contract-level futures execution, arbitrary generated code and exact original-result matching require separate validated implementations.
