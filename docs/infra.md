# Point-in-time data infrastructure and local run tools

QuantGlean 0.4 adds a reviewed infra runner, QG-INFRA-001. It measures data-query
correctness and local performance. It does not measure financial alpha.
The implementation, source design, events, queries and public walkthrough are original QuantGlean work.

## Quick start

```sh
python scripts/make-infra-fixture.py
qg freeze examples/reproduction/qg_infra_001/experiment.yaml --output local-work/frozen-infra.json
qg run local-work/frozen-infra.json --data-manifest ../examples/reproduction/qg_infra_001/data_manifest.json --output local-work/runs --parquet
qg verify local-work/runs/<run-id>
qg runs local-work/runs
qg compare local-work/runs/<first-id> local-work/runs/<second-id> --metric benchmark.profiles.2.indexed_median_ms
```

The core dependencies are unchanged. Parquet remains optional.
Use a fresh frozen filename after editing a protocol; manifest overrides resolve relative to the frozen spec.
The [saved example](../examples/reproduction/qg_infra_001/README.md) and
[four-language walkthrough](https://runqiwang777.github.io/QuantGlean/infra.html?lang=en) show an actual run.

## Three clocks and one explicit query

| Field | Meaning |
| --- | --- |
| event_time | Time of the historical observation/measurement |
| published_at | Time this revision was released by its source |
| available_at | Time this pipeline could actually use this revision |
| revision | Unique, increasing revision number within instrument/field/event |
| withdrawn | Explicit withdrawal; its value must be empty |
| decision_at | Information cutoff for the query |
| event_cutoff | Latest allowed observation time, no later than decision_at |

All timestamps must include a timezone and are normalized to UTC.
The historical-observation contract requires event_time ≤ published_at ≤ available_at.
This contract does not represent future-dated forecasts.

For each instrument/field query:

1. Retain records with event_time ≤ event_cutoff and available_at ≤ decision_at.
2. Select the latest event_time in that known set.
3. Select its latest available revision; a simultaneous release selects the highest revision number.
4. If it is withdrawn, return missing with status withdrawn. Do not silently fall back to an older event.
5. If no version is known, return missing with status unavailable.

A later publication revising an older period does not replace a more recent known event.
Publication alone is insufficient when ingestion happened later.
Future records and revisions must not change prior query answers.
The input may arrive out of event-time order; duplicate revisions and backwards revision sequences are rejected.

The application cannot prove timestamp truth or recover missing historical vintages.
Never label a final revised table as point-in-time data merely by adding old dates.

## Input bundle

The schema_version=2 manifest pins exactly two local CSV/Parquet files:

- events: instrument, field, event_time, published_at, available_at, revision, value, withdrawn.
- queries: query_id, instrument, field, decision_at, event_cutoff.

It records source provenance, separate use/redistribution declarations and
availability_basis=actual_pipeline_availability.
The bundle SHA256 hashes canonical JSON mapping the file roles to their byte SHA256 values.
The frozen spec also pins the complete manifest bytes. Paths are local and relative to the manifest.

The public fixture has 1,728 revisions and 486 queries, including known boundary cases,
delayed ingestion, changing revisions, withdrawals and missing keys.
It contains no observed market or personal data. A separate unsafe-final-version diagnostic
shows how many queries would select an unavailable version if availability were ignored.

## Correctness-first benchmark

Two independently written implementations are compared on every supplied query:

- reference: simple per-query filtering and sorting.
- indexed: batch sweep ordered by availability, maintaining the latest known revision for each event and a sorted list of known event times.

Queries are restored to their original order. The indexed implementation includes per-call group/index construction.
Sorted-list insertion is linear in the number of known events in the worst case; this is a transparent in-memory reference,
not a persistent database, online service or claim of production-scale complexity.

Only exact output equivalence permits timing results. The frozen workloads use seeded query samples,
alternating engine order and repeated measurements. Raw samples and the sample fingerprints are saved.
There is no minimum speed ratio or timing threshold in the tests. The reference runner rejects estimated baseline workloads above 50 million row/query comparisons before scanning; split larger research logs into audited batches or use another reviewed engine.

Timing uses perf_counter_ns and reports median milliseconds. It includes index construction and output assembly,
and excludes file reads, validation and warmup.
Memory is measured in separate tracemalloc sessions and reports peak traced allocations during the call.
Existing input frames are outside that tracing window. These measurements are **not total process RSS**,
persistent storage size, or directly comparable to other languages' resident-memory figures.
See the official [timing](https://docs.python.org/3/library/time.html#time.perf_counter_ns)
and [allocation tracing](https://docs.python.org/3/library/tracemalloc.html) references.

Correct snapshots and scalar statistics should reproduce from the same inputs and code.
Timings and allocation peaks can vary across runs, environments, library versions and background load.
A ratio below one is a valid result. No speed improvement is guaranteed.

## Result package

In addition to the common run/spec/data manifests, checks, implementation differences and report:

- snapshots.csv: indexed answers with status, chosen event, publication/availability and revision.
- reference_snapshots.csv: the correct baseline answers.
- availability_audit.csv: comparison with deliberately unsafe final-version selection.
- benchmark.csv: per-workload medians, ratios, allocation peaks and correctness counts.
- benchmark_samples.csv: raw repeated timings and query-sample fingerprints.
- Matching Parquet files when requested.

No return series or placeholder investment metrics are generated for infra runs.
The report and website label synthetic checks pipeline_demo / untested_synthetic.
Real permitted data can check equivalence for its supplied queries, not prove universal correctness or data rights.

## Local inventory, verification and comparison

qg runs reads immediate run directories and includes completed, failed, blocked, running and unreadable attempts.
It does not silently delete failed experiments or promote a running attempt to completed.

qg verify checks the declared artifact byte hashes, frozen-spec fingerprint and completed-run dataset binding.
It rejects unsafe artifact paths and symlinks. It detects corruption and internal inconsistencies;
it is not a digital signature, authorship certificate or license audit. A deliberately forged manifest and all hashes
require external provenance/signatures to detect. Original restricted input data is not copied into a run package;
replay needs the original permitted input files/manifest.

qg compare accepts a dot-separated finite numeric metric path (including list indices).
It withholds a delta when integrity, experiment identity, task, level, validation protocol, data/manifest,
implementation-source hashes or recorded environment differ. Infra benchmark settings must also match.
A scalar delta is descriptive, not an automatic hypothesis test or investment improvement claim.

The registry is file-based and read-only. MLflow/DVC services and RD-Agent automation remain optional future integrations.
This infra API is independent of the existing factor/model runners; converting event snapshots into a model's feature matrix
still requires an explicit, audited mapping. It does not fill missing delisting or constituent histories.
