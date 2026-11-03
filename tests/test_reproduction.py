"""Regression checks for temporal integrity, accounting and truthful run states."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from quantglean.specs import load_spec, validate_spec, freeze_spec
from quantglean.data import load_dataset
from quantglean.engine import run_reference
from quantglean.runs import execute
from quantglean.cli import main

CASE = Path(__file__).resolve().parents[1] / "examples" / "reproduction" / "qg_tf_001"

@pytest.fixture
def spec():
    return freeze_spec(load_spec(CASE / "experiment.yaml"))

@pytest.fixture
def frame():
    return load_dataset(CASE / "data_manifest.json")[0]

def write_dataset(tmp_path, frame, **changes):
    path = tmp_path / "data.csv"
    frame.to_csv(path, index=False)
    manifest = json.loads((CASE / "data_manifest.json").read_text())
    manifest.update(data_path="data.csv", sha256=hashlib.sha256(path.read_bytes()).hexdigest(), **changes)
    target = tmp_path / "manifest.json"
    target.write_text(json.dumps(manifest), encoding="utf-8")
    return target

def test_freeze_is_stable_and_detects_mutation(spec):
    original = deepcopy(spec)
    frozen = freeze_spec(spec)
    assert spec == original
    assert freeze_spec(spec) == frozen
    assert not validate_spec(frozen)
    frozen["implementation"]["costs"]["spread_bps"] = 99
    assert validate_spec(frozen), "A changed frozen rule must not reuse its old fingerprint"

@pytest.mark.parametrize("level", ["method_reimplementation", "inspired_extension"])
def test_synthetic_cannot_claim_historical_test(spec, tmp_path, level):
    spec["reproduction_level"] = level
    frozen = freeze_spec(spec)
    path = tmp_path / "spec.json"; path.write_text(json.dumps(frozen))
    root, manifest = execute(path, CASE / "data_manifest.json", tmp_path / "runs")
    assert manifest["status"] == "failed"
    assert manifest["conclusion"] == "untested"
    assert not (root / "metrics.json").exists()

def test_original_result_level_is_unavailable(spec):
    spec["reproduction_level"] = "result_reproduction"
    assert validate_spec(spec)

def test_data_hash_is_enforced(tmp_path):
    manifest = json.loads((CASE / "data_manifest.json").read_text())
    (tmp_path / "data.csv").write_bytes((CASE / "synthetic.csv").read_bytes())
    manifest["data_path"] = "data.csv"
    manifest["sha256"] = "0" * 64
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        load_dataset(path)

@pytest.mark.parametrize("bad", ["duplicate", "gap", "nan", "loss", "future", "rights"])
def test_invalid_data_is_not_silently_repaired(frame, tmp_path, bad):
    f = frame.copy(); overrides = {}
    if bad == "duplicate":
        f = pd.concat([f, f.iloc[[0]]])
    elif bad == "gap":
        f = f.iloc[1:]
    elif bad == "nan":
        f.loc[f.index[0], "return"] = np.nan
    elif bad == "loss":
        f.loc[f.index[0], "return"] = -1
    elif bad == "future":
        f.loc[f.index[0], "available_at"] = pd.Timestamp("2030-01-01", tz="UTC")
    elif bad == "rights":
        overrides["rights"] = {"use_permitted": False, "redistribution_permitted": False, "description": "not licensed"}
    path = write_dataset(tmp_path, f, **overrides)
    with pytest.raises(ValueError):
        load_dataset(path)

def normalized(df, before=None):
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], utc=True)
    if before is not None:
        out = out[out["date"] < pd.Timestamp(before, tz="UTC")]
    return out.sort_values(["variant", "date", "instrument"]).reset_index(drop=True)

def test_future_perturbation_preserves_past_and_current_positions(spec, frame):
    original = run_reference(spec, frame)
    changed = frame.copy()
    dates = pd.to_datetime(changed["date"], utc=True)
    changed.loc[dates >= pd.Timestamp("2020-01-31", tz="UTC"), "return"] *= -3
    rerun = run_reference(spec, changed)
    pd.testing.assert_frame_equal(normalized(original["signals"], "2020-01-31"), normalized(rerun["signals"], "2020-01-31"))
    # Return observed during January cannot determine January's holding.
    pd.testing.assert_frame_equal(normalized(original["positions"], "2020-02-01"), normalized(rerun["positions"], "2020-02-01"))

def test_signs_follow_known_compounded_excess_returns(spec, frame):
    result = run_reference(spec, frame)
    signals = result["signals"]
    sample = signals[signals["variant"] == "single_1"].copy()
    raw = frame.copy()
    raw["date"] = pd.to_datetime(raw["date"], utc=True)
    sample["date"] = pd.to_datetime(sample["date"], utc=True)
    merged = sample.merge(raw[["date", "instrument", "return"]], on=["date", "instrument"])
    assert len(merged) > 100
    np.testing.assert_allclose(merged["value"], np.sign(merged["return"]))

def test_accounting_matches_positions_and_itemized_costs(spec, frame):
    result = run_reference(spec, frame)
    returns = result["returns"].copy()
    positions = result["positions"].copy()
    raw = frame.copy()
    for f in (returns, positions, raw):
        f["date"] = pd.to_datetime(f["date"], utc=True)
    contributions = positions.merge(raw[["date", "instrument", "return"]], on=["date", "instrument"])
    expected = contributions.assign(gross=contributions.weight * contributions["return"]).groupby(["variant", "date"])["gross"].sum()
    actual = returns.set_index(["variant", "date"])
    np.testing.assert_allclose(actual["gross_return"], expected.reindex(actual.index), atol=1e-12)
    cost_columns = ["commission_cost", "spread_cost", "impact_cost", "financing_cost", "roll_cost"]
    assert (actual[cost_columns] >= 0).all().all()
    np.testing.assert_allclose(actual.net_return, actual.gross_return - actual[cost_columns].sum(axis=1), atol=1e-12)
    np.testing.assert_allclose(actual.commission_cost, actual.turnover * spec["implementation"]["costs"]["commission_bps"] / 10000, atol=1e-12)
    np.testing.assert_allclose(actual.spread_cost, actual.turnover * spec["implementation"]["costs"]["spread_bps"] / 10000, atol=1e-12)
    assert (actual.gross_leverage <= spec["implementation"]["max_gross_leverage"] + 1e-12).all()
    assert (actual.groupby(level="variant").head(1).turnover > 0).all(), "Initial entry must be charged"

def test_identical_inputs_give_identical_results(spec, frame):
    a, b = run_reference(spec, frame), run_reference(spec, frame)
    pd.testing.assert_frame_equal(a["returns"], b["returns"])
    assert a["metrics"] == b["metrics"]
    json.dumps(a["metrics"], allow_nan=False)

def test_blocked_run_records_no_placeholder_performance(spec, tmp_path):
    path = tmp_path / "spec.json"; path.write_text(json.dumps(freeze_spec(spec)))
    root, manifest = execute(path, tmp_path / "missing.json", tmp_path / "runs")
    assert manifest["status"] == "blocked_missing_data"
    assert not (root / "metrics.json").exists()
    assert "blocked_missing_data" in (root / "report.md").read_text()
    assert main(["run", str(path), "--data-manifest", str(tmp_path / "missing.json"), "--output", str(tmp_path / "runs")]) == 2

def test_complete_run_artifacts_and_parquet_roundtrip(spec, tmp_path):
    pytest.importorskip("pyarrow")
    path = tmp_path / "spec.json"; path.write_text(json.dumps(freeze_spec(spec)))
    root, manifest = execute(path, CASE / "data_manifest.json", tmp_path / "runs", parquet=True)
    assert manifest["status"] == "completed", manifest.get("error")
    assert manifest["conclusion"] == "untested_synthetic"
    for name, digest in manifest["artifacts"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    csv = pd.read_csv(root / "returns.csv")
    parquet = pd.read_parquet(root / "returns.parquet")
    assert len(csv) == len(parquet) > 100
    np.testing.assert_allclose(csv.net_return, parquet.net_return, atol=1e-15)
    second, _ = execute(path, CASE / "data_manifest.json", tmp_path / "runs")
    assert second != root

def test_cli_freeze_refuses_overwrite(spec, tmp_path):
    output = tmp_path / "frozen.json"
    assert main(["freeze", str(CASE / "experiment.yaml"), "--output", str(output)]) == 0
    before = output.read_bytes()
    assert main(["freeze", str(CASE / "experiment.yaml"), "--output", str(output)]) == 1
    assert output.read_bytes() == before


def test_known_constant_return_accounting(spec, frame, tmp_path):
    known = frame[frame.instrument == "SYN_A"].copy()
    known["return"] = .01
    manifest_path = write_dataset(tmp_path, known)
    loaded, manifest = load_dataset(manifest_path)
    spec["data"]["sha256"] = manifest["sha256"]
    result = run_reference(freeze_spec(spec), loaded)
    rows = result["returns"][result["returns"].variant == "candidate"]
    np.testing.assert_allclose(rows.gross_return, .02, atol=1e-12)
    # Weight=2 at leverage cap. Entry L1 turnover=2, afterwards no target changes.
    np.testing.assert_allclose(rows.iloc[0].net_return, .02 - .0008 - .01 / 12 - .0002, atol=1e-12)
    np.testing.assert_allclose(rows.iloc[1:].net_return, .02 - .01 / 12 - .0002, atol=1e-12)

def test_zero_signal_statistics_are_undefined_not_nan(spec, frame, tmp_path):
    zero = frame.copy(); zero["return"] = 0.
    loaded, manifest = load_dataset(write_dataset(tmp_path, zero))
    spec["data"]["sha256"] = manifest["sha256"]
    result = run_reference(freeze_spec(spec), loaded)
    assert (result["positions"].weight == 0).all()
    assert (result["returns"].net_return == 0).all()
    assert result["metrics"]["variants"]["candidate"]["sharpe"] is None
    assert result["metrics"]["comparison"]["conclusion"] == "untested_synthetic"
    json.dumps(result["metrics"], allow_nan=False)

def test_changed_provenance_requires_a_new_frozen_spec(spec, tmp_path):
    manifest = json.loads((CASE / "data_manifest.json").read_text())
    (tmp_path / "data.csv").write_bytes((CASE / "synthetic.csv").read_bytes())
    manifest["data_path"] = "data.csv"
    manifest["rights"]["description"] += " changed declaration"
    mp = tmp_path / "manifest.json"; mp.write_text(json.dumps(manifest))
    sp = tmp_path / "spec.json"; sp.write_text(json.dumps(spec))
    root, record = execute(sp, mp, tmp_path / "runs")
    assert record["status"] == "failed"
    assert "manifest_sha256" in record["error"]
    assert not (root / "returns.csv").exists()

def test_arbitrary_entrypoint_is_not_executed(spec, frame):
    spec["implementation"]["entrypoint"] = "os.system"
    with pytest.raises(ValueError, match="entrypoint"):
        run_reference(freeze_spec(spec), frame)

def test_infra_scaffold_uses_infra_metric_and_cannot_run(spec, frame):
    spec.update(artifact_type="infra", analysis_type="data_quality")
    spec["validation"] = {"metric": "row_equivalence_and_latency"}
    frozen = freeze_spec(spec)
    assert not validate_spec(frozen)
    with pytest.raises(ValueError, match="Unsupported runner"):
        run_reference(frozen, frame)

def test_yaml_object_tags_never_execute(tmp_path):
    path = tmp_path / "malicious.yaml"
    path.write_text("!!python/object/apply:os.system ['echo forbidden']")
    with pytest.raises(ValueError):
        load_spec(path)
