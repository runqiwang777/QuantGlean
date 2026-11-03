"""Temporal, statistical and accounting checks for cross-sectional/model experiments."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from quantglean.data import load_dataset
from quantglean.specs import load_spec, freeze_spec, validate_spec
from quantglean.cross_sectional import (run_factor, feature_table, quantile_weights, validate_eligibility)
from quantglean.models import run_model, fit_model

BASE = Path(__file__).resolve().parents[1] / "examples/reproduction"

@pytest.fixture(scope="module")
def cases():
    result = {}
    for key, folder, runner in [("factor", "qg_cs_001", run_factor), ("model", "qg_model_001", run_model)]:
        case = BASE / folder
        spec = freeze_spec(load_spec(case / "experiment.yaml"))
        frame, _ = load_dataset(case / "data_manifest.json")
        result[key] = (spec, frame, runner(spec, frame))
    return result

def test_tied_boundary_allocation_has_no_symbol_bias():
    scores = pd.Series([1.,1.,1.,2.,2.,2.,3.], index=list("ABCDEFG"))
    weights = quantile_weights(scores, 5)
    np.testing.assert_allclose(weights.sum(axis=0), 1)
    np.testing.assert_allclose(weights.loc["A"], weights.loc["C"])
    reordered = quantile_weights(scores.iloc[::-1], 5)
    pd.testing.assert_frame_equal(weights.sort_index(), reordered.sort_index())
    equal = quantile_weights(pd.Series(0., index=list("ABCDEFG")), 5)
    np.testing.assert_allclose(equal[5] - equal[1], 0, atol=1e-15)

def test_factor_window_excludes_two_latest_holding_month_returns(cases):
    _, frame, _ = cases["factor"]
    table = feature_table(frame)
    date, symbol = pd.Timestamp("2018-02-28", tz="UTC"), "SYN_04"
    rows = frame[frame.instrument == symbol].set_index("date")
    i = rows.index.get_loc(date)
    expected = np.prod(1 + rows["return"].iloc[i-12:i-1]) - 1
    actual = table[(table.date == date) & (table.instrument == symbol)].momentum_12_1.iloc[0]
    assert actual == pytest.approx(expected, abs=1e-13)
    changed = frame.copy()
    changed.loc[(changed.instrument == symbol) & (changed.date.isin(rows.index[i-1:i+1])), "return"] = .5
    after = feature_table(changed)
    assert after[(after.date == date) & (after.instrument == symbol)].momentum_12_1.iloc[0] == pytest.approx(actual)

@pytest.mark.parametrize("kind,runner", [("factor", run_factor), ("model", run_model)])
def test_future_returns_cannot_change_past_scores_or_current_holdings(cases, kind, runner):
    spec, frame, original = cases[kind]
    changed = frame.copy()
    date = pd.Timestamp("2021-01-31", tz="UTC")
    changed.loc[changed.date >= date, "return"] *= -2
    rerun = runner(spec, changed)
    for artifact, value in [("signals", "value"), ("positions", "weight")]:
        a, b = original[artifact], rerun[artifact]
        a, b = a[a.date <= date], b[b.date <= date]
        np.testing.assert_allclose(a[value], b[value], atol=1e-12)
    if kind == "model":
        assert original["model"] == rerun["model"]
        a, b = original["predictions"], rerun["predictions"]
        np.testing.assert_allclose(a[a.date <= date].prediction, b[b.date <= date].prediction, atol=1e-12)

def test_train_only_scaler_and_model_ignore_validation_and_test_labels(cases):
    spec, frame, original = cases["model"]
    changed = frame.copy()
    changed.loc[changed.date > pd.Timestamp(spec["validation"]["train_end"], tz="UTC"), "return"] += .04
    rerun = run_model(spec, changed)
    assert original["model"] == rerun["model"]
    train = original["features"]
    train = train[(train.date >= pd.Timestamp(spec["validation"]["train_start"], tz="UTC")) &
                  (train.date <= pd.Timestamp(spec["validation"]["train_end"], tz="UTC")) & train.eligible]
    np.testing.assert_allclose(original["model"]["feature_mean"],
                               train[["momentum_12_1", "reversal_1", "volatility_12"]].mean().to_numpy(), atol=1e-14)

def test_time_gaps_and_one_month_labels_are_enforced(cases):
    spec = deepcopy(cases["model"][0])
    spec["validation"]["valid_start"] = spec["validation"]["train_end"]
    with pytest.raises(ValueError, match="gap"):
        freeze_spec(spec)
    spec = deepcopy(cases["model"][0])
    spec["implementation"]["label_horizon_periods"] = 2
    with pytest.raises(ValueError, match="one-month"):
        freeze_spec(spec)

@pytest.mark.parametrize("kind", ["factor", "model"])
def test_ineligible_positions_are_zero_and_costs_reconcile(cases, kind):
    spec, frame, result = cases[kind]
    held = result["positions"].merge(frame[["date", "instrument", "eligible", "return"]], on=["date", "instrument"])
    assert (held.loc[~held.eligible, "weight"] == 0).all()
    actual = result["returns"].set_index(["variant", "date"])
    gross = held.assign(pnl=held.weight * held["return"]).groupby(["variant", "date"]).pnl.sum()
    np.testing.assert_allclose(actual.gross_return, gross.reindex(actual.index), atol=1e-12)
    costs = ["commission_cost","spread_cost","impact_cost","financing_cost","roll_cost","short_borrow_cost"]
    np.testing.assert_allclose(actual.net_return, actual.gross_return - actual[costs].sum(axis=1), atol=1e-12)
    short = held.assign(exposure=-held.weight.clip(upper=0)).groupby(["variant", "date"]).exposure.sum()
    np.testing.assert_allclose(actual.short_borrow_cost,
                               short.reindex(actual.index) * spec["implementation"]["costs"]["short_borrow_bps_annual"] / 10000 / 12)
    assert (actual.gross_leverage <= spec["implementation"]["gross_leverage"] + 1e-12).all()
    for variant, rows in result["returns"].groupby("variant"):
        recorded = result["metrics"]["variants"][variant]["cost_sums"]["total"]
        assert recorded == pytest.approx(rows[costs].sum().sum())
        stress = result["metrics"]["cost_stress_2x"]["variants"][variant]["cost_sums"]["total"]
        assert stress == pytest.approx(2 * recorded)

def test_eligibility_must_be_known_at_decision(cases):
    frame = cases["factor"][1].copy()
    frame.loc[0, "eligibility_available_at"] = frame.loc[0, "date"]
    with pytest.raises(ValueError, match="unavailable"):
        validate_eligibility(frame)

def test_model_uses_two_explicit_baselines(cases):
    result = cases["model"][2]
    prediction = result["predictions"]
    assert prediction.train_mean.nunique() == 1
    for segment in ("valid", "test"):
        rows = prediction[prediction.segment == segment]
        monthly = rows.assign(error=(rows.prediction - rows["return"])**2).groupby("date").error.mean().mean()
        assert result["metrics"]["prediction_metrics"][segment]["mse"] == pytest.approx(monthly)
    assert "momentum" in result["metrics"]["portfolio_baseline"]
    assert result["metrics"]["comparison"]["metric"] == "mse_improvement"

def test_synthetic_conclusions_and_serialization(cases):
    for _,_,result in cases.values():
        assert result["metrics"]["conclusion"] == "untested_synthetic"
        assert result["metrics"]["comparison"]["conclusion"] == "untested_synthetic"
        json.dumps(result["metrics"], allow_nan=False)
        assert not result["checks"]["original_historical_results_reproduced"]

def test_qlib_matches_native_fit_on_same_train_only_features(cases):
    pytest.importorskip("qlib")
    spec, _, result = cases["model"]
    table = result["features"]
    v = spec["validation"]
    train = table[(table.date >= pd.Timestamp(v["train_start"], tz="UTC")) &
                  (table.date <= pd.Timestamp(v["train_end"], tz="UTC")) & table.eligible].copy()
    inference = table[(table.date >= pd.Timestamp(v["valid_start"], tz="UTC")) & table.eligible].copy()
    native, native_model = fit_model(train, inference, spec["implementation"])
    implementation = deepcopy(spec["implementation"]); implementation["backend"] = "qlib"
    qlib, qlib_model = fit_model(train, inference, implementation)
    np.testing.assert_allclose(qlib, native, atol=1e-10, rtol=1e-10)
    np.testing.assert_allclose(qlib_model["coefficients"], native_model["coefficients"], atol=1e-10, rtol=1e-10)

def test_qlib_does_not_read_inference_labels(cases):
    pytest.importorskip("qlib")
    spec, _, result = cases["model"]
    table = result["features"]
    v = spec["validation"]
    train = table[(table.date >= pd.Timestamp(v["train_start"], tz="UTC")) &
                  (table.date <= pd.Timestamp(v["train_end"], tz="UTC")) & table.eligible]
    infer = table[(table.date >= pd.Timestamp(v["valid_start"], tz="UTC")) & table.eligible].copy()
    impl = deepcopy(spec["implementation"]); impl["backend"] = "qlib"
    first, _ = fit_model(train, infer, impl)
    infer["return"] = 999.
    second, _ = fit_model(train, infer, impl)
    np.testing.assert_allclose(first, second, atol=1e-12)


@pytest.mark.parametrize("case,artifact", [("qg_cs_001","factor_values.csv"),("qg_model_001","model.json")])
def test_cli_run_package_contains_typed_artifacts(tmp_path, case, artifact):
    import hashlib
    from quantglean.runs import execute
    spec = freeze_spec(load_spec(BASE / case / "experiment.yaml"))
    sp = tmp_path / "spec.json"; sp.write_text(json.dumps(spec))
    root, manifest = execute(sp, BASE / case / "data_manifest.json", tmp_path / "runs")
    assert manifest["status"] == "completed", manifest.get("error")
    assert manifest["data_summary"]["months"] == 240
    assert (root / artifact).is_file()
    for name, expected in manifest["artifacts"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected

def test_missing_and_unknown_eligibility_are_rejected(cases):
    frame = cases["factor"][1].copy()
    frame.loc[0,"eligibility_available_at"] = pd.NaT
    with pytest.raises(ValueError):
        validate_eligibility(frame)
    with pytest.raises(ValueError):
        validate_eligibility(frame.drop(columns=["eligible"]))
