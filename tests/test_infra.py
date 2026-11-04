"""Known-answer temporal cases, future invariance, integrity and benchmark accounting."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from quantglean.infra import (EVENT_COLUMNS, QUERY_COLUMNS, RevisionDataset, validate_events, validate_queries,
                             snapshot_reference, snapshot_indexed, mismatch_count, load_revision_dataset, run_infra)
from quantglean.specs import load_spec, freeze_spec
from quantglean.runs import execute
from quantglean.catalog import verify_run, compare_runs, list_runs
from quantglean.cli import main

CASE=Path(__file__).resolve().parents[1]/"examples/reproduction/qg_infra_001"
def events():
    rows = [
        ["A","eps","2020-01-01Z","2020-01-03Z","2020-01-04Z",0,10.,False],
        ["A","eps","2020-01-01Z","2020-01-30Z","2020-02-01Z",1,11.,False],
        ["A","eps","2020-01-01Z","2020-02-28Z","2020-03-01Z",2,12.,False],
        ["A","eps","2020-02-01Z","2020-02-02Z","2020-02-03Z",0,20.,False],
        ["A","eps","2020-02-01Z","2020-03-03Z","2020-03-04Z",1,np.nan,True],
    ]
    rows = [[value.replace("Z","T00:00:00Z") if isinstance(value,str) and value.endswith("Z") else value for value in row] for row in rows]
    return validate_events(pd.DataFrame(rows, columns=EVENT_COLUMNS))
def queries():
    return validate_queries(pd.DataFrame([
        ["pre","A","eps","2020-01-03T00:00:00Z","2020-01-01T00:00:00Z"],
        ["equal","A","eps","2020-01-04T00:00:00Z","2020-01-01T00:00:00Z"],
        ["rev","A","eps","2020-02-01T00:00:00Z","2020-01-31T00:00:00Z"],
        ["late","A","eps","2020-03-02T00:00:00Z","2020-03-02T00:00:00Z"],
        ["withdrawn","A","eps","2020-03-04T00:00:00Z","2020-03-04T00:00:00Z"],
        ["old_cutoff","A","eps","2020-03-04T00:00:00Z","2020-01-01T00:00:00Z"],
        ["unknown","B","eps","2020-03-04T00:00:00Z","2020-03-04T00:00:00Z"],
    ],columns=QUERY_COLUMNS))

@pytest.mark.parametrize("engine",[snapshot_reference,snapshot_indexed])
def test_known_answers_delay_boundary_revision_and_withdrawal(engine):
    output=engine(events(),queries()).set_index("query_id")
    assert output.loc["pre","status"]=="unavailable", "Publication alone is not pipeline availability"
    assert output.loc["equal","value"]==10.
    assert output.loc["rev","value"]==11.
    assert output.loc["late","value"]==20., "A later release of an older event must not replace a newer known event"
    assert output.loc["withdrawn","status"]=="withdrawn"
    assert pd.isna(output.loc["withdrawn","value"]), "Do not fall back after withdrawal"
    assert output.loc["old_cutoff","value"]==12.
    assert output.loc["unknown","status"]=="unavailable"

def test_future_revisions_and_new_events_do_not_change_past_answers():
    source=events()
    appended=source.iloc[[0]].copy()
    appended["revision"]=3
    appended["published_at"]=pd.Timestamp("2021-01-01",tz="UTC")
    appended["available_at"]=pd.Timestamp("2021-01-02",tz="UTC")
    appended["value"]=999.
    changed=validate_events(pd.concat([source,appended],ignore_index=True))
    for engine in (snapshot_reference,snapshot_indexed):
        assert mismatch_count(engine(source,queries()),engine(changed,queries()))==0

def test_input_and_query_order_do_not_change_semantics():
    a=snapshot_indexed(events(),queries())
    b=snapshot_indexed(events().sample(frac=1,random_state=3),queries().iloc[::-1])
    pd.testing.assert_frame_equal(a.sort_values("query_id").reset_index(drop=True),
                                  b.sort_values("query_id").reset_index(drop=True))

@pytest.mark.parametrize("error",["duplicate","revision_backwards","naive_time","invalid_clocks","value","withdrawn_value"])
def test_bad_event_contracts_are_rejected(error):
    data=events().copy()
    if error=="duplicate": data=pd.concat([data,data.iloc[[0]]])
    elif error=="revision_backwards": data.loc[(data.event_time==pd.Timestamp("2020-01-01",tz="UTC")) & (data.revision==1),"revision"]=5
    elif error=="naive_time": data["published_at"]=data.published_at.dt.tz_localize(None)
    elif error=="invalid_clocks": data.loc[0,"available_at"]=pd.Timestamp("2019-01-01",tz="UTC")
    elif error=="value": data.loc[0,"value"]=np.inf
    elif error=="withdrawn_value": data.loc[data.withdrawn,"value"]=123.
    with pytest.raises(ValueError): validate_events(data)

def test_bad_query_cutoff_and_duplicate_ids_are_rejected():
    data=queries().copy();data.loc[0,"event_cutoff"]=pd.Timestamp("2030-01-01",tz="UTC")
    with pytest.raises(ValueError): validate_queries(data)
    with pytest.raises(ValueError): validate_queries(pd.concat([queries(),queries().iloc[[0]]]))

def small_spec():
    spec=load_spec(CASE/"experiment.yaml")
    spec["implementation"]["benchmark"]["query_counts"]=[3,7]
    spec["implementation"]["benchmark"]["repetitions"]=2
    return freeze_spec(spec)

def test_small_benchmark_checks_equivalence_not_fixed_speed():
    spec=small_spec()
    data=RevisionDataset(events(),queries(),spec["data"]["sha256"],"synthetic")
    result=run_infra(spec,data)
    assert result["metrics"]["correctness"]["mismatches"]==0
    assert result["metrics"]["conclusion"]=="untested_synthetic"
    assert len(result["benchmark_samples"])==2*2*2
    assert (result["benchmark_samples"].elapsed_ms>=0).all()
    assert (result["benchmark"].indexed_python_peak_bytes>0).all()
    assert result["metrics"]["availability_audit"]["unsafe_final_version_queries"]>0
    json.dumps(result["metrics"],allow_nan=False)

def test_bundle_hash_and_manifest_rights_are_enforced(tmp_path):
    manifest=json.loads((CASE/"data_manifest.json").read_text())
    for name in ("events","queries"):
        (tmp_path/(name+".csv")).write_bytes((CASE/(name+".csv")).read_bytes())
    manifest["files"]["events"]["sha256"]="0"*64
    path=tmp_path/"manifest.json";path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="SHA256"): load_revision_dataset(path)
    manifest=json.loads((CASE/"data_manifest.json").read_text())
    manifest["rights"]["use_permitted"]=False
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="permitted"): load_revision_dataset(path)

def test_run_package_catalog_and_corruption_detection(tmp_path):
    spec=small_spec()
    path=tmp_path/"spec.json";path.write_text(json.dumps(spec))
    root,record=execute(path,CASE/"data_manifest.json",tmp_path/"runs")
    assert record["status"]=="completed",record.get("error")
    assert (root/"snapshots.csv").exists()
    assert not (root/"returns.csv").exists()
    assert verify_run(root)["valid"]
    assert list_runs(tmp_path/"runs")[0]["experiment_id"]=="QG-INFRA-001"
    assert main(["verify",str(root)])==0
    before=(root/"report.md").read_bytes()
    assert main(["report",str(root),"--quantstats"])==1
    assert (root/"report.md").read_bytes()==before
    assert verify_run(root)["valid"]
    same=compare_runs(root,root,"correctness.mismatches")
    assert same["comparable"] and same["second_minus_first"]==0
    (root/"snapshots.csv").write_text("corrupted")
    assert not verify_run(root)["valid"]
    assert main(["verify",str(root)])==1

def test_verifier_rejects_path_traversal(tmp_path):
    (tmp_path/"run_manifest.json").write_text(json.dumps({"artifacts":{"../outside":"0"*64}}))
    result=verify_run(tmp_path)
    assert not result["valid"] and any("Unsafe" in error for error in result["errors"])

def test_corrupt_catalog_entry_does_not_hide_other_attempts(tmp_path):
    child=tmp_path/"bad";child.mkdir();(child/"run_manifest.json").write_text("{")
    records=list_runs(tmp_path)
    assert records[0]["status"]=="unreadable"

def test_compare_rejects_incompatible_protocols(tmp_path):
    from quantglean.runs import dump
    spec=small_spec();root=tmp_path/"one";root.mkdir()
    dump(root/"frozen_spec.json",spec);dump(root/"metrics.json",{"correctness":{"mismatches":0}})
    record={"run_id":"one","status":"completed","spec_hash":spec["spec_hash"],"data_sha256":spec["data"]["sha256"],
            "code":{"source_sha256":{"a":"one"}},"environment":{}}
    record["artifacts"]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
    dump(root/"run_manifest.json",record)
    other=tmp_path/"two";other.mkdir()
    import shutil
    for p in root.iterdir():shutil.copyfile(p,other/p.name)
    changed=deepcopy(record);changed["data_sha256"]="different";dump(other/"run_manifest.json",changed)
    result=compare_runs(root,other,"correctness.mismatches")
    assert not result["comparable"] and result["second_minus_first"] is None


def test_same_availability_timestamp_chooses_highest_known_revision():
    data=events()
    mask=(data.event_time==pd.Timestamp("2020-01-01",tz="UTC")) & (data.revision==1)
    data.loc[mask,"published_at"]=pd.Timestamp("2020-01-04",tz="UTC")
    data.loc[mask,"available_at"]=pd.Timestamp("2020-01-04",tz="UTC")
    data=validate_events(data)
    for engine in (snapshot_reference,snapshot_indexed):
        assert engine(data,queries()).set_index("query_id").loc["equal","value"]==11.

def test_synthetic_infra_cannot_claim_historical_validation():
    spec=load_spec(CASE/"experiment.yaml");spec["reproduction_level"]="method_reimplementation"
    spec=freeze_spec(spec)
    data=RevisionDataset(events(),queries(),spec["data"]["sha256"],"synthetic")
    with pytest.raises(ValueError,match="Synthetic"):
        run_infra(spec,data)

def test_wrong_artifact_type_cannot_execute_infra():
    spec=load_spec(CASE/"experiment.yaml")
    spec.update(artifact_type="model",analysis_type="other")
    spec=freeze_spec(spec)
    with pytest.raises(ValueError,match="reviewed"):
        run_infra(spec,RevisionDataset(events(),queries(),spec["data"]["sha256"],"synthetic"))


def test_large_reference_workload_stops_before_quadratic_scan():
    source,_=load_revision_dataset(CASE/"data_manifest.json")
    large=pd.concat([source.queries]*40,ignore_index=True)
    large["query_id"]=[f"Q_{i}" for i in range(len(large))]
    with pytest.raises(ValueError,match="budget"):
        run_infra(small_spec(),RevisionDataset(source.events,large,source.sha256,"synthetic"))
