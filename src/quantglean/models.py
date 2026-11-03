"""Fixed-split ridge forecasting with train-only transforms and honest baselines."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .cross_sectional import (FEATURES, context, feature_table, select_period, require_features,
                              portfolios, summaries, mean_interval, correlation)
from .specs import ValidationError

def fit_model(train: pd.DataFrame, inference: pd.DataFrame, implementation: dict) -> tuple[np.ndarray, dict]:
    if train.available_at.max() > inference.decision_at.min():
        raise ValidationError("Training labels were unavailable at the frozen model fit time")
    x = train[FEATURES].to_numpy(dtype=float)
    y = train["return"].to_numpy(dtype=float)
    mean, scale = x.mean(axis=0), x.std(axis=0, ddof=0)
    scale[scale <= 1e-15] = 1.
    standardized = (x - mean) / scale
    future = (inference[FEATURES].to_numpy(dtype=float) - mean) / scale
    alpha, backend = implementation["ridge_alpha"], implementation["backend"]
    if backend == "numpy":
        intercept = float(y.mean())
        coef = np.linalg.solve(standardized.T @ standardized + alpha * np.eye(len(FEATURES)),
                               standardized.T @ (y - intercept))
        predictions = future @ coef + intercept
        version = np.__version__
    elif backend == "qlib":
        from .qlib_adapter import fit_predict
        tx = pd.DataFrame(standardized, index=pd.MultiIndex.from_frame(train[["date", "instrument"]]), columns=FEATURES)
        px = pd.DataFrame(future, index=pd.MultiIndex.from_frame(inference[["date", "instrument"]]), columns=FEATURES)
        predictions, coef, intercept, version = fit_predict(tx, pd.Series(y, index=tx.index), px, alpha)
    else:
        raise ValidationError("Only numpy and optional qlib backends are reviewed")
    if not np.isfinite(predictions).all():
        raise ValidationError("Nonfinite model prediction")
    model = {"backend": backend, "backend_version": version, "features": FEATURES, "ridge_alpha": alpha,
             "feature_mean": mean.tolist(), "feature_scale": scale.tolist(), "coefficients": coef.tolist(),
             "intercept": intercept, "baseline_train_mean": float(y.mean()), "train_rows": len(train),
             "train_label_available_at": str(train.available_at.max()),
             "train_start": str(train.date.min().date()), "train_end": str(train.date.max().date()),
             "fit_at": str(inference.decision_at.min()), "selection": "fixed alpha; validation never fitted or selected"}
    return predictions, model

def run_model(spec: dict, frame: pd.DataFrame) -> dict:
    panel = context(spec, frame)
    if (spec["artifact_type"], spec["analysis_type"], spec["implementation"]["entrypoint"]) != (
            "model", "predictive", "qg_model_001_reference"):
        raise ValidationError("Unsupported prediction reference specification")
    validation, impl = spec["validation"], spec["implementation"]
    table = feature_table(panel)
    train_all = select_period(table, validation["train_start"], validation["train_end"])
    valid = select_period(table, validation["valid_start"], validation["valid_end"])
    test = select_period(table, validation["evaluation_start"], validation["evaluation_end"])
    for segment in (train_all, valid, test):
        require_features(segment, FEATURES, impl["quantiles"])
    train = train_all[train_all.eligible].sort_values(["date", "instrument"]).copy()
    valid["segment"], test["segment"] = "valid", "test"
    inference = pd.concat([valid, test]).sort_values(["date", "instrument"])
    usable = inference[inference.eligible].copy()
    predictions, model = fit_model(train, usable, impl)
    usable["prediction"] = predictions
    usable["train_mean"] = model["baseline_train_mean"]
    inference = inference.merge(usable[["date", "instrument", "prediction", "train_mean"]],
                                on=["date", "instrument"], how="left", validate="one_to_one")
    prediction_metrics = {}
    errors = []
    for segment, rows in usable.groupby("segment", sort=False):
        monthly = []
        for date, group in rows.groupby("date", sort=True):
            mse = float(np.mean((group.prediction - group["return"])**2))
            base_mse = float(np.mean((group.train_mean - group["return"])**2))
            item = {"date": date, "segment": segment, "mse": mse, "baseline_mse": base_mse,
                    "mse_improvement": base_mse - mse, "n": len(group),
                    "ic": correlation(group.prediction, group["return"]),
                    "rank_ic": correlation(group.prediction, group["return"], rank=True)}
            monthly.append(item); errors.append(item)
        m = pd.DataFrame(monthly)
        prediction_metrics[segment] = {"mse": float(m.mse.mean()), "baseline_train_mean_mse": float(m.baseline_mse.mean()),
                                       "mse_improvement": float(m.mse_improvement.mean()), "months": len(m),
                                       "rows": len(rows), "mean_rank_ic": None if m.rank_ic.isna().all() else float(m.rank_ic.mean())}
    monthly_errors = pd.DataFrame(errors)
    comparison = mean_interval(monthly_errors[monthly_errors.segment == "test"].mse_improvement.to_numpy(),
                               validation, spec["execution"]["seed"], spec["reproduction_level"] == "pipeline_demo")
    evaluation = inference[inference.segment == "test"].copy()
    result = portfolios(evaluation, {"candidate": "prediction", "baseline": "momentum_12_1"}, impl)
    result["metrics"] = {**summaries(result), "reproduction_level": spec["reproduction_level"],
                         "conclusion": comparison["conclusion"], "comparison": comparison,
                         "prediction_metrics": prediction_metrics,
                         "primary_test": "test mean monthly MSE improvement over fixed training-mean predictor",
                         "portfolio_baseline": "12-1 momentum long-short; distinct from the forecast training-mean baseline",
                         "evaluation_start": validation["evaluation_start"], "evaluation_end": validation["evaluation_end"],
                         "interpretation": "Prediction quality and portfolio performance are separate. Synthetic scenario only."}
    result["checks"] = {"conclusion": comparison["conclusion"], "train_only_scaling": True,
                        "single_fit_no_validation_or_test_labels": True, "label_horizon_periods": 1,
                        "gap_periods": validation["gap_periods"], "eligibility_known_at_decision": True,
                        "split_convention": "holding/label months; complete gap months between train/valid/test",
                        "fit_at": model["fit_at"], "initial_position": "flat at test start; entry charged",
                        "accounting": "monthly constant-notional; no wealth drift/fills",
                        "short_borrow_cost": "separate from gross-over-one financing; charged on absolute short exposure",
                        "original_historical_results_reproduced": False}
    result["predictions"] = usable[["date", "decision_at", "instrument", "segment", "prediction", "train_mean", "return"]]
    result["features"] = table
    result["prediction_diagnostics"] = monthly_errors
    result["model"] = model
    return result
