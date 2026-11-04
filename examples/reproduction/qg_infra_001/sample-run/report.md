# QuantGlean reproduction report

- Run: 20261104T001126Z-b79ba343
- Status: completed
- Level: pipeline_demo
- Conclusion: untested_synthetic
- Spec SHA256: df7f6c32721f329d506de1a36fa4cf904dcf5cf2c428ff417efb5c0d761ff79f
- Dataset SHA256: 873d3a9f74b34787a438cfc33506333adf98652ab748a4454779aa5eeaf5a51c
- Started (UTC): 2026-11-04T00:11:26.240703+00:00
- Code: {'commit': '6233fc75d18e1d2a7858e3b381d40836b012b697', 'dirty': False, 'source_sha256': {'quantglean/__init__.py': '06b6ba21998412885a2afb8c410bede8bd2ed69b8c4bcbf41bf35585b1c515f1', 'quantglean/__main__.py': '935a1c1166b0c1ea35a82256345000bf2c73ded718d77773bc27a71ecce28f7d', 'quantglean/catalog.py': 'f8f0ae03943297a96402da0a2cc36c95108fc85562630f26a2930459db4da711', 'quantglean/cli.py': 'e4c6c06dd06a360775ef2a53224e1b0ce9d5ec84ecc1658e07f988689b49ed5d', 'quantglean/cross_sectional.py': '2b1c6a3a0eb3e32c74bebf10e9a3579c5b19ffaa2122e6094e40a1a3eccf7366', 'quantglean/data.py': '92aab2808f511e1684931cf51501d19f9abfa909e3933bc7a5828c93bf445ff0', 'quantglean/engine.py': 'b42e59bf15b3f1e589e5aeb4d7aeaa36f7a090f44723fb173c419665f77b7051', 'quantglean/infra.py': '2c13e4ff2b4e735953fc6adb36a343896c7f5a4fb919d8dd4ee76df61e8a8b12', 'quantglean/models.py': '4c7e1465646fb2feb9891700857c978c5121d87b9678087050296917ee43d9f8', 'quantglean/qlib_adapter.py': '20c6eeb86e79dcd3b9c65d3c50af534187fffd9f2075f73a2b140018c525fbae', 'quantglean/reporting.py': 'cf85925cd2b2a11d5660a325772e3af62946656fe32b61a0c63bda02bb0649b1', 'quantglean/runs.py': '3ba443e3a64973cf575452bb2b1991be9f08a7e24c940bdce272d79761c55bb8', 'quantglean/specs.py': 'fa15104326bad951ba1a7ee2a99a5b13b7d03c69c3ab0422d054a801d2526426'}}

Point-in-time data-query correctness and local performance benchmark. Synthetic fixture only; timings vary by environment and are not investment returns.

## Research source and protocol

Source record: https://github.com/runqiwang777/QuantGlean/blob/main/examples/reproduction/qg_infra_001/SOURCE.md
Source SHA256: e4809344539c5408a64c2e10b3fe19cd7c71b85f58e0d78400a6c6c5da6483c2
Evidence IDs: I1, I2, I3
Validation: snapshot_equivalence

## Correctness and availability

```json
{
  "correctness": {
    "queries": 486,
    "events": 1728,
    "mismatches": 0,
    "matched_queries": 447,
    "unavailable_queries": 39,
    "withdrawn_queries": 15
  },
  "availability_audit": {
    "unsafe_final_version_queries": 300,
    "different_value_or_status_queries": 300
  }
}
```

## Measured performance

| Queries | Reference median ms | Indexed median ms | Ratio | Reference Python peak bytes | Indexed Python peak bytes |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 40 | 60.7146 | 34.7524 | 1.7470620734107571 | 294454 | 1244753 |
| 160 | 240.3926 | 38.1167 | 6.3067526832070975 | 592183 | 1269770 |
| 400 | 609.2641 | 39.7076 | 15.34376542525864 | 921611 | 1530527 |

validated in-memory input through complete output; includes per-call index construction; excludes file I/O/validation
separate tracemalloc Python allocation peaks; excludes existing input frames; not process RSS
This dataset/environment only. Timings vary, ratios are not guaranteed and are not investment returns.

## Recorded metrics

Undefined statistics are null.
Measured timings are descriptive, not inferential speed guarantees.

```json
{
  "artifact_type": "infra",
  "reproduction_level": "pipeline_demo",
  "conclusion": "untested_synthetic",
  "correctness": {
    "queries": 486,
    "events": 1728,
    "mismatches": 0,
    "matched_queries": 447,
    "unavailable_queries": 39,
    "withdrawn_queries": 15
  },
  "availability_audit": {
    "unsafe_final_version_queries": 300,
    "different_value_or_status_queries": 300
  },
  "benchmark": {
    "profiles": [
      {
        "queries": 40,
        "events": 1728,
        "reference_median_ms": 60.7146,
        "indexed_median_ms": 34.7524,
        "speed_ratio": 1.7470620734107571,
        "reference_python_peak_bytes": 294454,
        "indexed_python_peak_bytes": 1244753,
        "mismatches": 0,
        "query_sample_sha256": "9a971782ffab9eaf73f2746d9c57beba3ba783d3fb5e4e3742561e803e876baa"
      },
      {
        "queries": 160,
        "events": 1728,
        "reference_median_ms": 240.3926,
        "indexed_median_ms": 38.1167,
        "speed_ratio": 6.3067526832070975,
        "reference_python_peak_bytes": 592183,
        "indexed_python_peak_bytes": 1269770,
        "mismatches": 0,
        "query_sample_sha256": "495ab81267eaedadd88b6b49cbeb3b261cd588e22a3a6db14e0824bf1132b026"
      },
      {
        "queries": 400,
        "events": 1728,
        "reference_median_ms": 609.2641,
        "indexed_median_ms": 39.7076,
        "speed_ratio": 15.34376542525864,
        "reference_python_peak_bytes": 921611,
        "indexed_python_peak_bytes": 1530527,
        "mismatches": 0,
        "query_sample_sha256": "1cc43921bc7ab8d5623628bf72c4c8053715ee2f87159c801191245a6db06629"
      }
    ],
    "repetitions": 3,
    "timing_scope": "validated in-memory input through complete output; includes per-call index construction; excludes file I/O/validation",
    "memory_scope": "separate tracemalloc Python allocation peaks; excludes existing input frames; not process RSS",
    "caution": "This dataset/environment only. Timings vary, ratios are not guaranteed and are not investment returns."
  }
}
```

## Audit trail

See frozen_spec.json, data_manifest.json (when available), checks.json, implementation_differences.md, and artifact SHA256 values in run_manifest.json.
The manifest records the actual environment and command; inspect code.dirty before treating a commit as exact code provenance.
