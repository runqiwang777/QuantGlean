"""Self-authored monthly time-series reference experiment.

This is constant-notional excess-return research accounting, not a futures,
order-fill, margin, or intramonth execution simulator. Numerical conventions are
extensions to the cited research and must be declared in the frozen spec.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .data import validate_panel
from .specs import ValidationError, validate_spec

_COSTS = ("commission_cost", "spread_cost", "impact_cost", "financing_cost", "roll_cost")


def _sharpe(values: np.ndarray, annualization: int = 12) -> float | None:
    deviation = float(np.std(values, ddof=1)) if len(values) >= 2 else 0.0
    if not math.isfinite(deviation) or deviation <= 1e-15:
        return None
    return float(np.mean(values) / deviation * math.sqrt(annualization))


def _summary(rows: pd.DataFrame, multiplier: float = 1.0) -> dict:
    gross = rows["gross_return"].to_numpy(dtype=float)
    cost_columns = list(_COSTS) + (["short_borrow_cost"] if "short_borrow_cost" in rows else [])
    costs = rows[cost_columns].sum(axis=1).to_numpy(dtype=float) * multiplier
    values = gross - costs
    positive_wealth = bool(np.all(values > -1))
    growth = float(np.expm1(np.log1p(values).mean() * 12)) if positive_wealth else None
    if positive_wealth:
        # Include starting capital so an immediate loss counts toward drawdown.
        wealth = np.concatenate(([1.0], np.cumprod(1 + values)))
        drawdown = float(np.min(wealth / np.maximum.accumulate(wealth) - 1))
    else:
        drawdown = None
    vol = float(np.std(values, ddof=1) * math.sqrt(12)) if len(values) >= 2 else None
    result = {
        "observations": int(len(values)),
        "annualized_excess_geometric_growth": growth,
        "annualized_volatility": vol,
        "sharpe": _sharpe(values),
        "gross_sharpe": _sharpe(gross),
        "gross_annualized_volatility": float(np.std(gross, ddof=1) * math.sqrt(12)) if len(gross) >= 2 else None,
        "gross_annualized_excess_geometric_growth": float(np.expm1(np.log1p(gross).mean() * 12)) if np.all(gross > -1) else None,
        "max_drawdown": drawdown,
        "average_turnover": float(rows["turnover"].mean()),
        "average_gross_leverage": float(rows["gross_leverage"].mean()),
        "maximum_gross_leverage": float(rows["gross_leverage"].max()),
        "positive_compounded_wealth": positive_wealth,
        "cost_sums": {name: float(rows[name].sum() * multiplier) for name in cost_columns},
    }
    result["cost_sums"]["total"] = float(costs.sum())
    return result


def _comparison(candidate: np.ndarray, baseline: np.ndarray, validation: dict, seed: int) -> dict:
    candidate_sharpe, baseline_sharpe = _sharpe(candidate), _sharpe(baseline)
    result = {
        "metric": "net_sharpe_difference",
        "difference": None,
        "ci_lower": None,
        "ci_upper": None,
        "confidence": validation["confidence"],
        "bootstrap_samples": validation["bootstrap_samples"],
        "bootstrap_valid_samples": 0,
        "bootstrap_block_periods": validation["bootstrap_block_periods"],
        "bootstrap_method": "paired moving blocks, sampled with replacement, truncated to evaluation length",
        "conclusion": "inconclusive",
    }
    if candidate_sharpe is None or baseline_sharpe is None:
        result["reason"] = "Sharpe is undefined for at least one evaluation series"
        return result
    result["difference"] = candidate_sharpe - baseline_sharpe
    n = len(candidate)
    block = validation["bootstrap_block_periods"]
    generator = np.random.default_rng(seed)
    differences = []
    for _ in range(validation["bootstrap_samples"]):
        starts = generator.integers(0, n - block + 1, size=math.ceil(n / block))
        # The same monthly indices preserve the strategy pair's contemporaneous dependence.
        indices = np.concatenate([np.arange(start, start + block) for start in starts])[:n]
        first, second = _sharpe(candidate[indices]), _sharpe(baseline[indices])
        if first is not None and second is not None:
            differences.append(first - second)
    result["bootstrap_valid_samples"] = len(differences)
    if len(differences) < max(30, validation["bootstrap_samples"] // 2):
        result["reason"] = "Too few defined paired bootstrap statistics"
        return result
    alpha = (1 - validation["confidence"]) / 2
    lower, upper = np.quantile(differences, [alpha, 1 - alpha])
    result.update(ci_lower=float(lower), ci_upper=float(upper))
    if lower > 0:
        result["conclusion"] = "supported"
    elif upper <= 0:
        result["conclusion"] = "rejected"
    return result


def _weights(direction: np.ndarray, covariance: np.ndarray, floor: float,
             target: float, cap: float) -> np.ndarray:
    """Inverse-volatility instrument budgets, covariance-scaled then gross-capped."""
    covariance = np.array(covariance, dtype=float, copy=True)
    diagonal = np.diag(covariance).copy()
    # Add only the variance needed to enforce the declared per-instrument floor.
    covariance += np.diag(np.maximum(floor**2 - diagonal, 0))
    volatility = np.sqrt(np.maximum(np.diag(covariance), floor**2))
    raw = direction / volatility / len(direction)
    variance = float(raw @ covariance @ raw)
    if variance <= 1e-24 or not np.any(raw):
        return np.zeros_like(raw)
    result = raw * target / math.sqrt(variance)
    gross = float(np.abs(result).sum())
    if gross > cap:
        result *= cap / gross
    return result


def run_reference(spec: dict, frame: pd.DataFrame) -> dict:
    """Run one frozen, fully declared factor/time_series monthly specification."""
    errors = validate_spec(spec)
    if errors:
        raise ValidationError("; ".join(errors))
    if spec.get("status") != "spec_ready":
        raise ValidationError("Reference runner requires a frozen spec_ready specification")
    if spec["artifact_type"] != "factor" or spec["analysis_type"] != "time_series":
        raise ValidationError("Unsupported runner: this MVP executes factor/time_series only; model and infra remain declarative scaffolds")
    implementation = spec["implementation"]
    if implementation["entrypoint"] != "qg_tf_001_reference":
        raise ValidationError("Unsupported implementation.entrypoint; only qg_tf_001_reference is implemented")
    level = spec["reproduction_level"]
    source_kind = frame.attrs.get("source_kind")
    if level == "pipeline_demo" and source_kind != "synthetic":
        raise ValidationError("pipeline_demo requires a validated synthetic source")
    if level != "pipeline_demo" and source_kind != "user_supplied":
        raise ValidationError("Historical method experiments require validated user_supplied provenance; synthetic data cannot be upgraded")
    expected_hash = spec.get("data", {}).get("sha256")
    if expected_hash is None or expected_hash != frame.attrs.get("data_sha256"):
        raise ValidationError("Frozen data.sha256 must match the validated panel fingerprint")
    data = validate_panel(frame)
    wide = data.pivot(index="date", columns="instrument", values="return").sort_index()
    dates, instruments = wide.index, list(wide.columns)
    values = wide.to_numpy(dtype=float)
    validation = spec["validation"]
    lag = implementation["execution_lag_periods"]
    lookbacks = implementation["lookbacks"]
    baseline_lookback = implementation["baseline_lookback"]
    # Keep the one- and three-month diagnostics even if candidate horizons change.
    horizons = sorted(set(lookbacks + [baseline_lookback, 1, 3]))
    vol_window = implementation["volatility_lookback"]
    minimum_history = max(horizons) + vol_window + lag
    if len(wide) < minimum_history:
        raise ValidationError(f"Insufficient history: need at least {minimum_history} monthly observations for lookback, risk and execution lag coverage")
    first_signal = max(max(horizons), vol_window) - 1
    first_position = first_signal + lag
    evaluation_start = pd.Timestamp(validation["evaluation_start"], tz="UTC")
    evaluation_end = pd.Timestamp(validation["evaluation_end"], tz="UTC")
    if evaluation_start < dates[first_position]:
        raise ValidationError(f"Evaluation starts before fully warmed lagged positions are available ({dates[first_position].date()})")
    if evaluation_start < dates[0] or evaluation_end > dates[-1]:
        raise ValidationError("Evaluation dates must lie within the available panel history")
    selected = np.flatnonzero((dates >= evaluation_start) & (dates <= evaluation_end))
    if len(selected) < max(12, 2 * validation["bootstrap_block_periods"]):
        raise ValidationError("Evaluation needs at least 12 months and two bootstrap blocks")
    if validation["bootstrap_block_periods"] > len(selected):
        raise ValidationError("bootstrap_block_periods exceeds the evaluation sample")
    desired: dict[str, np.ndarray] = {
        name: np.full(values.shape, np.nan)
        for name in ("candidate", "baseline", "single_1", "single_3")
    }
    signals = []
    for i in range(first_signal, len(values)):
        direction = {
            horizon: np.sign(np.expm1(np.log1p(values[i - horizon + 1:i + 1]).sum(axis=0)))
            for horizon in horizons
        }
        directions = {
            "candidate": np.mean([direction[h] for h in lookbacks], axis=0),
            "baseline": direction[baseline_lookback],
            "single_1": direction[1],
            "single_3": direction[3],
        }
        history = values[i - vol_window + 1:i + 1]
        # np.cov returns a scalar for one instrument; keep a square matrix.
        covariance = np.atleast_2d(np.cov(history, rowvar=False, ddof=1)) * 12
        for variant, vector in directions.items():
            desired[variant][i] = _weights(vector, covariance, implementation["min_volatility"],
                                           implementation["target_volatility"],
                                           implementation["max_gross_leverage"])
            signals.extend({"variant": variant, "date": dates[i], "instrument": instrument,
                            "value": float(vector[j])} for j, instrument in enumerate(instruments))
    position_rows, return_rows = [], []
    costs = implementation["costs"]
    cap = implementation["max_gross_leverage"]
    for variant, history in desired.items():
        # Warmup estimates the signal; evaluation opens from flat and pays its entry.
        previous = np.zeros(len(instruments), dtype=float)
        for i in selected:
            held = history[i - lag].copy()
            if not np.isfinite(held).all():
                raise ValidationError("Evaluation contains an uninitialized lagged position")
            gross_leverage = float(np.abs(held).sum())
            turnover = float(np.abs(held - previous).sum())
            components = {
                "commission_cost": turnover * costs["commission_bps"] / 10000,
                "spread_cost": turnover * costs["spread_bps"] / 10000,
                "impact_cost": turnover * costs["impact_bps"] / 10000,
                "financing_cost": max(gross_leverage - 1, 0) * costs["financing_bps_annual"] / 10000 / 12,
                "roll_cost": gross_leverage * costs["roll_bps_per_period"] / 10000,
            }
            gross_return = float(held @ values[i])
            return_rows.append({
                "variant": variant, "date": dates[i], "gross_return": gross_return,
                **components, "net_return": gross_return - sum(components.values()),
                "gross_leverage": gross_leverage, "turnover": turnover,
            })
            position_rows.extend({"variant": variant, "date": dates[i], "instrument": instrument,
                                  "weight": float(held[j])} for j, instrument in enumerate(instruments))
            previous = held
    signals_frame = pd.DataFrame(signals)
    positions_frame = pd.DataFrame(position_rows)
    returns_frame = pd.DataFrame(return_rows)
    for name, artifact in (("signals", signals_frame), ("positions", positions_frame), ("returns", returns_frame)):
        if not np.isfinite(artifact.select_dtypes(include="number").to_numpy()).all():
            raise ValidationError(f"Nonfinite value in {name}")
    observed_cap = float(returns_frame["gross_leverage"].max())
    if observed_cap > cap + 1e-10:
        raise ValidationError("Gross leverage exceeds the declared cap")
    groups = {name: rows for name, rows in returns_frame.groupby("variant", sort=False)}
    compared = _comparison(groups["candidate"]["net_return"].to_numpy(),
                           groups["baseline"]["net_return"].to_numpy(),
                           validation, spec["execution"]["seed"])
    conclusion = "untested_synthetic" if level == "pipeline_demo" else compared["conclusion"]
    if level == "pipeline_demo":
        compared["diagnostic_direction"] = compared["conclusion"]
        compared["conclusion"] = "untested_synthetic"
    # This diagnostic holds the exact same signals and weights; there is no retuning.
    stress = {name: _summary(rows, multiplier=2.0) for name, rows in groups.items()}
    metrics = {
        "reproduction_level": level,
        "conclusion": conclusion,
        "evaluation_start": str(dates[selected[0]].date()),
        "evaluation_end": str(dates[selected[-1]].date()),
        "annualization": 12,
        "variants": {name: _summary(rows) for name, rows in groups.items()},
        "comparison": compared,
        "cost_stress_2x": {
            "method": "twice every declared cost component; fixed original signals, positions and gross returns",
            "variants": stress,
        },
        "interpretation": (
            "Synthetic results test the software pipeline only; bootstrap direction is not research evidence."
            if level == "pipeline_demo" else
            "Exploratory paired-block comparison for this declared dataset; not the original paper's historical result."
        ),
    }
    checks = {
        "conclusion": conclusion,
        "source_kind": source_kind,
        "minimum_history_periods": minimum_history,
        "available_history_periods": len(wide),
        "warmup_signal_periods": first_signal + 1,
        "evaluation_observations": len(selected),
        "execution_lag_periods": lag,
        "information_boundary": "Signal and covariance through signal month only; weights applied after the declared monthly lag",
        "availability_boundary": "available_at may equal next-month decision; this assumes processing at that boundary without additional latency",
        "initial_position": "flat at evaluation start; first position pays all declared entry costs",
        "portfolio_convention": "inverse-volatility instrument budgets, average horizon direction, covariance risk scaling, gross cap",
        "accounting": "monthly constant-notional simple excess returns; no price/fill/margin or intramonth simulation",
        "turnover_convention": "L1 change in constant-notional monthly weights including initial entry",
        "cost_convention": "linear turnover costs; financing on gross exposure above 1 divided by 12; roll on gross exposure",
        "all_artifacts_finite": True,
        "gross_leverage_cap_respected": True,
        "maximum_observed_gross_leverage": observed_cap,
        "original_historical_results_reproduced": False,
    }
    return {"signals": signals_frame, "positions": positions_frame,
            "returns": returns_frame, "metrics": metrics, "checks": checks}
