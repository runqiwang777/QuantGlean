"""Publish a permitted synthetic infra result and saved temporal walkthrough."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import pandas as pd
from quantglean.infra import load_revision_dataset

ROOT=Path(__file__).resolve().parents[1]
def export(run: Path):
    manifest=json.loads((run/"run_manifest.json").read_text(encoding="utf-8"))
    spec=json.loads((run/"frozen_spec.json").read_text(encoding="utf-8"))
    source=json.loads((run/"data_manifest.json").read_text(encoding="utf-8"))
    if not (manifest["status"]=="completed" and manifest["conclusion"]=="untested_synthetic"
            and manifest["reproduction_level"]=="pipeline_demo" and source["source"]["kind"]=="synthetic"
            and source["rights"]["redistribution_permitted"] is True and manifest["code"]["dirty"] is False
            and spec["implementation"]["entrypoint"]=="qg_infra_001_reference"):
        raise ValueError("Publish only a committed, completed, permitted synthetic infra run")
    for name,expected in manifest["artifacts"].items():
        if Path(name).name!=name or hashlib.sha256((run/name).read_bytes()).hexdigest()!=expected:
            raise ValueError("Artifact mismatch: "+name)
    case=ROOT/"examples/reproduction/qg_infra_001"
    dataset,original=load_revision_dataset(case/"data_manifest.json")
    if dataset.sha256!=manifest["data_sha256"] or hashlib.sha256((case/"data_manifest.json").read_bytes()).hexdigest()!=spec["data"]["manifest_sha256"]:
        raise ValueError("The public fixture no longer matches this run")
    metrics=json.loads((run/"metrics.json").read_text(encoding="utf-8"))
    snapshots=pd.read_csv(run/"snapshots.csv").set_index("query_id")
    scenarios=[]
    for i,kind in enumerate(("initial","revision","withdrawal")):
        for when in ("before","equal"):
            query=dataset.queries.set_index("query_id").loc[f"EDGE_{i}_{when}"]
            snapshot=snapshots.loc[f"EDGE_{i}_{when}"]
            chosen=dataset.events[(dataset.events.instrument==query.instrument)&(dataset.events.field==query.field)&
                                  (dataset.events.event_time==query.event_cutoff)]
            timeline=[]
            for record in chosen.itertuples(index=False):
                timeline.append({"event_time":record.event_time.isoformat(),"published_at":record.published_at.isoformat(),
                                 "available_at":record.available_at.isoformat(),"revision":int(record.revision),
                                 "value":None if record.withdrawn else float(record.value),"withdrawn":bool(record.withdrawn),
                                 "known":bool(record.available_at<=query.decision_at),
                                 "selected":bool(pd.notna(snapshot.revision) and record.revision==snapshot.revision)})
            scenarios.append({"scenario":kind+"_"+when,"query_id":f"EDGE_{i}_{when}","instrument":query.instrument,
                              "field":query.field,"decision_at":query.decision_at.isoformat(),"event_cutoff":query.event_cutoff.isoformat(),
                              "status":snapshot.status,"value":None if pd.isna(snapshot.value) else float(snapshot.value),
                              "revision":None if pd.isna(snapshot.revision) else int(snapshot.revision),"timeline":timeline})
    summary={"id":spec["id"],"run_id":manifest["run_id"],"level":manifest["reproduction_level"],"conclusion":manifest["conclusion"],
             "correctness":metrics["correctness"],"availability_audit":metrics["availability_audit"],
             "benchmark":metrics["benchmark"],"scenarios":scenarios,
             "provenance":{"code":manifest["code"],"spec_hash":manifest["spec_hash"],"data_sha256":manifest["data_sha256"],
                           "data_manifest_sha256":manifest["data_manifest_sha256"],"metrics_sha256":manifest["artifacts"]["metrics.json"]}}
    target=case/"sample-run"
    if target.exists(): raise FileExistsError("Review and replace the existing public sample explicitly")
    shutil.copytree(run,target)
    (ROOT/"site/reproduction/infra-summary.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    print(target)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("run_directory",type=Path)
    export(parser.parse_args().run_directory)
