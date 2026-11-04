"""Original point-in-time revision queries and correctness-first local benchmarks."""
from __future__ import annotations
from bisect import bisect_right, insort
from dataclasses import dataclass
import gc
import hashlib
import json
import math
from pathlib import Path, PureWindowsPath
import statistics
import time
import tracemalloc

import numpy as np
import pandas as pd
from .specs import ValidationError, load_spec, validate_spec

EVENT_COLUMNS = ["instrument", "field", "event_time", "published_at", "available_at", "revision", "value", "withdrawn"]
QUERY_COLUMNS = ["query_id", "instrument", "field", "decision_at", "event_cutoff"]

@dataclass
class RevisionDataset:
    events: pd.DataFrame
    queries: pd.DataFrame
    sha256: str
    source_kind: str

def bundle_hash(files: dict) -> str:
    payload = {name: entry["sha256"] for name, entry in files.items()}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def _timestamps(frame, names):
    for name in names:
        try:
            if not frame[name].map(lambda v: pd.notna(v) and pd.Timestamp(v).tzinfo is not None).all():
                raise ValueError("Explicit timezone required")
            frame[name] = pd.to_datetime(frame[name], utc=True, format="mixed", errors="raise")
            if frame[name].isna().any():
                raise ValueError("NaT is not an available timestamp")
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValidationError(f"{name} requires explicit timezone-aware timestamps") from exc

def validate_events(frame: pd.DataFrame) -> pd.DataFrame:
    if not set(EVENT_COLUMNS).issubset(frame.columns) or frame.empty or len(frame) > 200000:
        raise ValidationError("Events require the revision-log columns and 1..200000 rows")
    out = frame[EVENT_COLUMNS].copy()
    for name in ("instrument", "field"):
        if not out[name].map(lambda v: isinstance(v, str) and bool(v.strip())).all():
            raise ValidationError(f"{name} must contain nonempty identifiers")
    _timestamps(out, ["event_time", "published_at", "available_at"])
    if ((out.published_at < out.event_time) | (out.available_at < out.published_at)).any():
        raise ValidationError("Historical observations require event_time <= published_at <= available_at")
    revision = pd.to_numeric(out.revision, errors="raise")
    if (not np.isfinite(revision).all() or (revision < 0).any() or (revision > 1000000).any()
            or (revision % 1 != 0).any() or out.revision.map(lambda x: isinstance(x, (bool, np.bool_))).any()):
        raise ValidationError("revision must be a finite nonnegative integer")
    out["revision"] = revision.astype("int64")
    if not out.withdrawn.map(lambda x: isinstance(x, (bool, np.bool_))).all():
        raise ValidationError("withdrawn must contain explicit booleans")
    out["value"] = pd.to_numeric(out.value, errors="raise")
    if out.loc[~out.withdrawn, "value"].isna().any() or not np.isfinite(out.loc[~out.withdrawn, "value"]).all():
        raise ValidationError("Non-withdrawn observations require finite values")
    if out.loc[out.withdrawn, "value"].notna().any():
        raise ValidationError("A withdrawal must carry an empty value")
    identity = ["instrument", "field", "event_time"]
    if out.duplicated(identity + ["revision"]).any():
        raise ValidationError("Duplicate event/revision identities are ambiguous")
    ordered = out.sort_values(identity + ["available_at", "revision"], kind="stable")
    if (ordered.groupby(identity).revision.diff().dropna() <= 0).any():
        raise ValidationError("Revision numbers cannot go backwards in availability order")
    return ordered.reset_index(drop=True)

def validate_queries(frame: pd.DataFrame) -> pd.DataFrame:
    if not set(QUERY_COLUMNS).issubset(frame.columns) or frame.empty or len(frame) > 50000:
        raise ValidationError("Queries require explicit identities/cutoffs and 1..50000 rows")
    out = frame[QUERY_COLUMNS].copy()
    for name in ("query_id", "instrument", "field"):
        if not out[name].map(lambda v: isinstance(v, str) and bool(v.strip())).all():
            raise ValidationError(f"{name} must contain nonempty identifiers")
    if out.query_id.duplicated().any():
        raise ValidationError("query_id must be unique")
    _timestamps(out, ["decision_at", "event_cutoff"])
    if (out.event_cutoff > out.decision_at).any():
        raise ValidationError("event_cutoff cannot be later than the decision")
    return out.reset_index(drop=True)

def load_revision_dataset(path: str | Path) -> tuple[RevisionDataset, dict]:
    manifest_path = Path(path).resolve()
    manifest = load_spec(manifest_path)
    if manifest.get("schema_version") != 2 or manifest.get("kind") != "event_revisions":
        raise ValidationError("Infra requires schema_version=2, kind=event_revisions")
    source, rights = manifest.get("source", {}), manifest.get("rights", {})
    if source.get("kind") not in ("synthetic", "user_supplied") or not source.get("description"):
        raise ValidationError("Declare the source kind and provenance description")
    if not all(type(rights.get(k)) is bool for k in ("use_permitted", "redistribution_permitted")):
        raise ValidationError("Declare separate Boolean use and redistribution rights")
    if not rights["use_permitted"] or not isinstance(rights.get("description"), str) or not rights["description"].strip():
        raise ValidationError("Explicit permitted use and rights description are required")
    if manifest.get("availability_basis") != "actual_pipeline_availability":
        raise ValidationError("available_at must mean actual pipeline availability, not assumed publication time")
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != {"events", "queries"}:
        raise ValidationError("The manifest must pin exactly events and queries")
    frames = {}
    for name, info in files.items():
        filename = info.get("path") if isinstance(info, dict) else None
        if (not isinstance(filename, str) or not filename or "://" in filename
                or PureWindowsPath(filename).drive or Path(filename).is_absolute() or filename.startswith(("//", "\\"))):
            raise ValidationError("Input files must be local relative paths")
        target = (manifest_path.parent / filename).resolve()
        if not target.is_file():
            raise ValidationError(f"Missing {name} input")
        if hashlib.sha256(target.read_bytes()).hexdigest() != info.get("sha256"):
            raise ValidationError(f"{name} SHA256 mismatch")
        if target.suffix.lower() == ".csv":
            frames[name] = pd.read_csv(target)
        elif target.suffix.lower() in (".parquet", ".pq"):
            frames[name] = pd.read_parquet(target)
        else:
            raise ValidationError("Revision inputs must be CSV or Parquet")
    fingerprint = bundle_hash(files)
    if manifest.get("sha256") != fingerprint:
        raise ValidationError("Revision bundle fingerprint mismatch")
    dataset = RevisionDataset(validate_events(frames["events"]), validate_queries(frames["queries"]),
                              fingerprint, source["kind"])
    return dataset, manifest

def _row(query, record):
    result = {name: getattr(query, name) for name in QUERY_COLUMNS}
    result.update(status="unavailable", selected_event_time=pd.NaT, published_at=pd.NaT,
                  available_at=pd.NaT, revision=None, value=None)
    if record is not None:
        result.update(status="withdrawn" if record.withdrawn else "available",
                      selected_event_time=record.event_time, published_at=record.published_at,
                      available_at=record.available_at, revision=int(record.revision),
                      value=None if record.withdrawn else float(record.value))
    return result

def snapshot_reference(events: pd.DataFrame, queries: pd.DataFrame) -> pd.DataFrame:
    """Correct simple baseline: filter both clocks, then choose event and known revision."""
    rows = []
    for query in queries.itertuples(index=False):
        eligible = events[(events.instrument == query.instrument) & (events.field == query.field) &
                          (events.event_time <= query.event_cutoff) & (events.available_at <= query.decision_at)]
        selected = eligible.sort_values(["event_time", "available_at", "revision"], kind="stable")
        record = next(selected.tail(1).itertuples(index=False), None)
        rows.append(_row(query, record))
    return pd.DataFrame(rows)

def snapshot_indexed(events: pd.DataFrame, queries: pd.DataFrame) -> pd.DataFrame:
    """Batch sweep by availability with per-key sorted known event times.

    Sorted-list insertion costs O(E) in the worst case per new event. This small
    in-memory reference is not a general database or an online streaming service.
    """
    groups = {key: list(group.sort_values(["available_at", "revision", "event_time"], kind="stable").itertuples(index=False))
              for key, group in events.groupby(["instrument", "field"], sort=False)}
    answers = {}
    for key, group in queries.groupby(["instrument", "field"], sort=False):
        records = groups.get(key, [])
        active, known, cursor = [], {}, 0
        for query in group.sort_values(["decision_at", "query_id"], kind="stable").itertuples(index=False):
            while cursor < len(records) and records[cursor].available_at <= query.decision_at:
                record = records[cursor]
                if record.event_time not in known:
                    insort(active, record.event_time)
                known[record.event_time] = record
                cursor += 1
            position = bisect_right(active, query.event_cutoff) - 1
            record = known[active[position]] if position >= 0 else None
            answers[query.query_id] = _row(query, record)
    return pd.DataFrame([answers[query_id] for query_id in queries.query_id])

def mismatch_count(first: pd.DataFrame, second: pd.DataFrame) -> int:
    if list(first.columns) != list(second.columns) or len(first) != len(second):
        raise ValidationError("Snapshot schemas/row counts differ")
    a, b = first.reset_index(drop=True), second.reset_index(drop=True)
    return int((~(a.eq(b) | (a.isna() & b.isna())).all(axis=1)).sum())

def _measure(function, events, queries):
    gc.collect()
    started = time.perf_counter_ns()
    result = function(events, queries)
    return (time.perf_counter_ns() - started) / 1e6, result

def benchmark(events, queries, config, seed):
    if tracemalloc.is_tracing():
        raise ValidationError("Benchmark requires ownership of a fresh tracemalloc session")
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(queries))
    profiles, samples = [], []
    functions = {"reference": snapshot_reference, "indexed": snapshot_indexed}
    for count in config["query_counts"]:
        if count > len(queries):
            raise ValidationError("Benchmark query count exceeds the provided query set")
        subset = queries.iloc[order[:count]].reset_index(drop=True)
        sample_hash = hashlib.sha256("\n".join(subset.query_id).encode()).hexdigest()
        for function in functions.values():
            function(events, subset.head(min(5, count)))
        measurements = {name: [] for name in functions}
        for repetition in range(config["repetitions"]):
            outputs = {}
            engines = list(functions) if repetition % 2 == 0 else list(reversed(functions))
            for name in engines:
                duration, outputs[name] = _measure(functions[name], events, subset)
                measurements[name].append(duration)
                samples.append({"queries": count, "engine": name, "repetition": repetition,
                                "elapsed_ms": duration, "query_sample_sha256": sample_hash})
            if mismatch_count(outputs["reference"], outputs["indexed"]):
                raise ValidationError("Correctness gate failed during timing; no speed claim is allowed")
        peaks = {}
        for name, function in functions.items():
            gc.collect()
            tracemalloc.start()
            try:
                output = function(events, subset)
                _, peak = tracemalloc.get_traced_memory()
                peaks[name] = int(peak)
                del output
            finally:
                tracemalloc.stop()
        reference, indexed = (statistics.median(measurements[name]) for name in ("reference", "indexed"))
        profiles.append({"queries": count, "events": len(events), "reference_median_ms": reference,
                         "indexed_median_ms": indexed, "speed_ratio": reference / indexed if indexed > 0 else None,
                         "reference_python_peak_bytes": peaks["reference"], "indexed_python_peak_bytes": peaks["indexed"],
                         "mismatches": 0, "query_sample_sha256": sample_hash})
    return pd.DataFrame(profiles), pd.DataFrame(samples)

def run_infra(spec: dict, dataset: RevisionDataset) -> dict:
    errors = validate_spec(spec)
    if errors:
        raise ValidationError("; ".join(errors))
    if spec["status"] != "spec_ready" or (spec["artifact_type"], spec["analysis_type"], spec["implementation"]["entrypoint"]) != ("infra", "point_in_time", "qg_infra_001_reference"):
        raise ValidationError("Infra requires the frozen reviewed reference")
    if spec["data"].get("sha256") != dataset.sha256:
        raise ValidationError("Frozen input bundle fingerprint mismatch")
    synthetic = dataset.source_kind == "synthetic"
    if (spec["reproduction_level"] == "pipeline_demo") != synthetic:
        raise ValidationError("Synthetic logs cannot be upgraded to historical validation")
    events, queries = validate_events(dataset.events), validate_queries(dataset.queries)
    config = spec["implementation"]["benchmark"]
    reference_queries = 2 * len(queries) + (config["repetitions"] + 1) * sum(config["query_counts"]) + 5 * len(config["query_counts"])
    if len(events) * reference_queries > 50000000:
        raise ValidationError("Workload exceeds this reference runner's 50-million row/query comparison budget; split it into smaller audited batches")
    reference, indexed = snapshot_reference(events, queries), snapshot_indexed(events, queries)
    mismatches = mismatch_count(reference, indexed)
    if mismatches:
        raise ValidationError(f"Snapshot equivalence failed for {mismatches} queries")
    # Deliberately unsafe diagnostic: use final revisions while ignoring availability.
    unsafe_queries = queries.copy()
    unsafe_queries["decision_at"] = max(events.available_at.max(), queries.decision_at.max())
    final_view = snapshot_reference(events, unsafe_queries)
    audit = queries[["query_id", "decision_at", "event_cutoff"]].copy()
    audit["asof_status"], audit["asof_revision"] = indexed.status, indexed.revision
    audit["final_status"], audit["final_revision"] = final_view.status, final_view.revision
    audit["unavailable_version_selected"] = (final_view.available_at > queries.decision_at).fillna(False)
    audit["value_or_status_differs"] = ~((indexed.value.eq(final_view.value) | (indexed.value.isna() & final_view.value.isna())) &
                                        indexed.status.eq(final_view.status))
    profiles, timing = benchmark(events, queries, spec["implementation"]["benchmark"], spec["execution"]["seed"])
    conclusion = "untested_synthetic" if synthetic else "supported_within_declared_fixture"
    metrics = {"artifact_type": "infra", "reproduction_level": spec["reproduction_level"], "conclusion": conclusion,
               "correctness": {"queries": len(queries), "events": len(events), "mismatches": mismatches,
                               "matched_queries": int((indexed.status != "unavailable").sum()),
                               "unavailable_queries": int((indexed.status == "unavailable").sum()),
                               "withdrawn_queries": int((indexed.status == "withdrawn").sum())},
               "availability_audit": {"unsafe_final_version_queries": int(audit.unavailable_version_selected.sum()),
                                      "different_value_or_status_queries": int(audit.value_or_status_differs.sum())},
               "benchmark": {"profiles": profiles.to_dict("records"), "repetitions": spec["implementation"]["benchmark"]["repetitions"],
                             "timing_scope": "validated in-memory input through complete output; includes per-call index construction; excludes file I/O/validation",
                             "memory_scope": "separate tracemalloc Python allocation peaks; excludes existing input frames; not process RSS",
                             "caution": "This dataset/environment only. Timings vary, ratios are not guaranteed and are not investment returns."}}
    checks = {"conclusion": conclusion, "snapshot_equivalence": mismatches == 0, "availability_boundary": "inclusive",
              "selection": "latest known event <= event_cutoff, then latest available revision",
              "withdrawal_policy": "missing without fallback to an older event",
              "clocks": "event_time <= published_at <= actual available_at <= decision_at for selected records",
              "financial_alpha_tested": False, "benchmark_correctness_gate": True}
    return {"snapshots": indexed, "reference_snapshots": reference, "availability_audit": audit,
            "benchmark": profiles, "benchmark_samples": timing, "metrics": metrics, "checks": checks}
