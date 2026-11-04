"""Original event/revision log, delayed ingestion and fixed query workloads."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from quantglean.infra import bundle_hash

ROOT = Path(__file__).resolve().parents[1]
def encoded(value):
    return (json.dumps(value, indent=2) + "\n").encode("utf-8")
def csv_bytes(columns, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    return stream.getvalue().encode()
def iso(value):
    return value.isoformat().replace("+00:00", "Z")

def build_fixture(target: Path | None = None):
    from quantglean.infra import EVENT_COLUMNS, QUERY_COLUMNS
    target = target or ROOT / "examples/reproduction/qg_infra_001"
    target.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20261104)
    events = []
    for month in range(36):
        year, number = 2020 + month // 12, month % 12 + 1
        event = datetime(year, number, 1, tzinfo=timezone.utc)
        for symbol in range(8):
            for field in ("earnings", "quality_score"):
                base = 10 + symbol + rng.gauss(0, 2)
                first_release = event + timedelta(days=2 + (month + symbol) % 8, hours=9)
                for revision, delay in enumerate((0, 20, 70)):
                    published = first_release + timedelta(days=delay)
                    available = published + timedelta(days=(month + symbol) % 4, hours=1)
                    withdrawn = revision == 2 and (month + symbol) % 17 == 0
                    events.append({"instrument":f"SYN_{symbol:02}","field":field,"event_time":iso(event),
                                   "published_at":iso(published),"available_at":iso(available),"revision":revision,
                                   "value":"" if withdrawn else f"{base + revision * .25:.8f}","withdrawn":withdrawn})
    queries = []
    origin = datetime(2019,12,20,tzinfo=timezone.utc)
    for i in range(480):
        decision = origin + timedelta(days=rng.randrange(1170), hours=rng.randrange(24))
        cutoff = decision - timedelta(days=rng.randrange(95))
        queries.append({"query_id":f"Q{i:04}","instrument":"UNKNOWN" if i % 37 == 0 else f"SYN_{rng.randrange(8):02}",
                        "field":rng.choice(["earnings","quality_score"]),"decision_at":iso(decision),"event_cutoff":iso(cutoff)})
    selected = [events[0], events[1], next(row for row in events if row["withdrawn"])]
    for i, row in enumerate(selected):
        available = datetime.fromisoformat(row["available_at"].replace("Z","+00:00"))
        for offset in (-1, 0):
            queries.append({"query_id":f"EDGE_{i}_{'before' if offset else 'equal'}",
                            "instrument":row["instrument"],"field":row["field"],
                            "decision_at":iso(available + timedelta(microseconds=offset)),
                            "event_cutoff":row["event_time"]})
    source = (
        "# QG-INFRA-001 original research design\n\n"
        "## I1 — three clocks\n\n"
        "The event time describes a historical observation; publication time is when its source released it; "
        "available_at is when this pipeline could actually use it. Query by actual availability, never by a final revised table.\n\n"
        "## I2 — selection and withdrawal\n\n"
        "Among event times no later than event_cutoff, select the newest one with any version known at decision_at. "
        "Within that event select its latest available revision. Boundaries are inclusive. A known withdrawal returns "
        "missing with status withdrawn and does not fall back to an older event. No forecast/future-event semantics are implied.\n\n"
        "## I3 — correctness before performance\n\n"
        "Compare the batch availability sweep with a simple independent filter-and-sort baseline on every query. "
        "Time repeated predeclared workloads including index construction, excluding validation and file I/O. "
        "Measure Python allocation peaks separately from timing; these are not total process RSS. "
        "No speed threshold or investment-return target is an acceptance condition.\n"
    ).encode()
    (target / "SOURCE.md").write_bytes(source)
    files = {}
    for name, columns, rows in (("events", EVENT_COLUMNS, events), ("queries", QUERY_COLUMNS, queries)):
        body = csv_bytes(columns, rows)
        filename = name + ".csv"; (target / filename).write_bytes(body)
        files[name] = {"path":filename,"sha256":hashlib.sha256(body).hexdigest()}
    manifest = {"schema_version":2,"kind":"event_revisions","files":files,"sha256":bundle_hash(files),
                "availability_basis":"actual_pipeline_availability",
                "source":{"kind":"synthetic","description":"Original fictional revision log and query generator; seed 20261104"},
                "rights":{"use_permitted":True,"redistribution_permitted":True,
                          "description":"Original synthetic events and queries, released under the repository MIT license"}}
    (target / "data_manifest.json").write_bytes(encoded(manifest))
    spec = {"id":"QG-INFRA-001","spec_version":1,"status":"draft","artifact_type":"infra","analysis_type":"point_in_time",
            "reproduction_level":"pipeline_demo",
            "source":{"case":"qg_infra_001","url":"https://github.com/runqiwang777/QuantGlean/blob/main/examples/reproduction/qg_infra_001/SOURCE.md",
                      "sha256":hashlib.sha256(source).hexdigest(),"evidence_ids":["I1","I2","I3"]},
            "implementation":{"entrypoint":"qg_infra_001_reference","event_selection":"latest_known_before_cutoff",
                              "revision_selection":"latest_available_then_revision","withdrawal_policy":"missing_without_fallback",
                              "availability_boundary":"inclusive",
                              "benchmark":{"query_counts":[40,160,400],"repetitions":3,"memory_measurement":"tracemalloc_python_peak"},
                              "undocumented_choices":["Original synthetic observations, revisions, withdrawals and predeclared queries only.",
                                "Actual pipeline availability can lag publication; inclusive UTC boundaries; no fallback after withdrawal.",
                                "Batch sweep uses sorted lists of known event times; worst-case insertion is linear in known event count.",
                                "Timing includes per-call index build and full output construction; excludes input parsing and validation.",
                                "Allocation peaks are measured in separate tracemalloc runs; not process RSS or persisted index size.",
                                "Three fixed query workloads, alternating engine order, three repeats; no minimum speedup target."]},
            "data":{"manifest":"data_manifest.json","sha256":manifest["sha256"],"manifest_sha256":hashlib.sha256(encoded(manifest)).hexdigest()},
            "validation":{"metric":"snapshot_equivalence"},"execution":{"seed":17},"missing_information":[]}
    (target / "experiment.yaml").write_bytes(encoded(spec))
    print(target)

if __name__ == "__main__":
    build_fixture()
