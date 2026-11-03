"""Original monthly panel experiments. Eligibility is known at the holding-month boundary."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from .data import validate_panel
from .engine import _summary
from .specs import ValidationError, validate_spec

FEATURES = ["momentum_12_1", "reversal_1", "volatility_12"]
COST_NAMES = ["commission_cost", "spread_cost", "impact_cost", "financing_cost", "roll_cost"]

def validate_eligibility(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if not {"eligible", "eligibility_available_at"}.issubset(out.columns):
        raise ValidationError("Panel experiments require eligible and eligibility_available_at")
    if out[["eligible", "eligibility_available_at"]].isna().any().any():
        raise ValidationError("Eligibility cannot be missing")
    if not out.eligible.map(lambda x: isinstance(x, (bool, np.bool_))).all():
        raise ValidationError("eligible must contain explicit booleans")
    try:
        out["eligibility_available_at"] = pd.to_datetime(out.eligibility_available_at, utc=True, format="mixed")
    except (ValueError, TypeError) as exc:
        raise ValidationError("Invalid eligibility_available_at") from exc
    if out["eligibility_available_at"].isna().any():
        raise ValidationError("Eligibility availability cannot be NaT")
    decisions = out.date.dt.tz_localize(None).dt.to_period("M").dt.start_time.dt.tz_localize("UTC")
    if (out.eligibility_available_at > decisions).any():
        raise ValidationError("Eligibility snapshot was unavailable at the holding-month decision")
    return out

def context(spec: dict, frame: pd.DataFrame) -> pd.DataFrame:
    errors = validate_spec(spec)
    if errors:
        raise ValidationError("; ".join(errors))
    if spec["status"] != "spec_ready":
        raise ValidationError("A frozen spec_ready specification is required")
    level, kind = spec["reproduction_level"], frame.attrs.get("source_kind")
    if (level == "pipeline_demo" and kind != "synthetic") or (level != "pipeline_demo" and kind != "user_supplied"):
        raise ValidationError("Source kind and reproduction level do not match")
    if spec["data"].get("sha256") != frame.attrs.get("data_sha256"):
        raise ValidationError("Frozen data fingerprint does not match the validated frame")
    return validate_eligibility(validate_panel(frame))

def feature_table(frame: pd.DataFrame) -> pd.DataFrame:
    wide = frame.pivot(index="date", columns="instrument", values="return").sort_index()
    def compound(x, length):
        return np.expm1(np.log1p(x).rolling(length, min_periods=length).sum())
    fields = {
        # Holding month t: t-12 through t-2, deliberately excludes t-1 and t.
        "momentum_12_1": compound(wide.shift(2), 11),
        "momentum_6_1": compound(wide.shift(2), 5),
        "reversal_1": -wide.shift(1),
        "volatility_12": wide.shift(1).rolling(12, min_periods=12).std(ddof=1) * math.sqrt(12),
    }
    result = frame[["date", "instrument", "return", "available_at", "eligible", "eligibility_available_at"]].copy()
    for name, data in fields.items():
        result = result.merge(data.stack(future_stack=True).rename(name).reset_index(), on=["date", "instrument"], validate="one_to_one")
    previous_availability = frame[["date", "instrument"]].copy()
    previous_availability["feature_available_at"] = frame.groupby("instrument")["available_at"].shift(1)
    result = result.merge(previous_availability, on=["date", "instrument"], validate="one_to_one")
    result["decision_at"] = result.date.dt.tz_localize(None).dt.to_period("M").dt.start_time.dt.tz_localize("UTC")
    return result

def select_period(table: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    first, last = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    dates = pd.DatetimeIndex(table.date.drop_duplicates()).sort_values()
    if first not in dates or last not in dates:
        raise ValidationError("Split/evaluation bounds must be observed UTC month-end dates")
    result = table[(table.date >= first) & (table.date <= last)].copy()
    if len(result.date.unique()) < 12:
        raise ValidationError("Each measured evaluation segment requires at least 12 months")
    return result

def require_features(table: pd.DataFrame, columns: list[str], quantiles: int) -> None:
    eligible = table[table.eligible]
    if eligible[columns].isna().any().any() or not np.isfinite(eligible[columns].to_numpy()).all():
        raise ValidationError("An eligible observation lacks fully warmed finite features; no silent dropping")
    if eligible.feature_available_at.isna().any() or (eligible.feature_available_at > eligible.decision_at).any():
        raise ValidationError("Feature information was unavailable at the decision")
    counts = eligible.groupby("date").size()
    if len(counts) != table.date.nunique() or (counts < quantiles).any():
        raise ValidationError("Each decision requires at least quantiles eligible instruments")

def quantile_weights(scores: pd.Series, quantiles: int) -> pd.DataFrame:
    """Fractional boundary allocation treats tied symbols equally in every bucket."""
    n = len(scores)
    if n < quantiles or not np.isfinite(scores.to_numpy()).all():
        raise ValidationError("Insufficient finite cross-section for quantiles")
    _, inverse, counts = np.unique(scores.to_numpy(), return_inverse=True, return_counts=True)
    ends = np.cumsum(counts)
    starts = ends - counts
    width = n / quantiles
    boundaries = np.arange(quantiles) * width
    overlap = np.maximum(0., np.minimum(ends[:, None], boundaries + width) -
                         np.maximum(starts[:, None], boundaries))
    allocation = overlap / counts[:, None] / width
    return pd.DataFrame(allocation[inverse], index=scores.index, columns=range(1, quantiles + 1))

def correlation(x: pd.Series, y: pd.Series, rank=False) -> float | None:
    if len(x) < 3:
        return None
    if rank:
        x, y = x.rank(method="average"), y.rank(method="average")
    if x.std(ddof=0) <= 1e-15 or y.std(ddof=0) <= 1e-15:
        return None
    value = float(x.corr(y))
    return value if math.isfinite(value) else None

def portfolios(table: pd.DataFrame, score_columns: dict[str, str], implementation: dict) -> dict:
    q, gross = implementation["quantiles"], implementation["gross_leverage"]
    costs = implementation["costs"]
    signals, positions, returns, diagnostics, quantile_returns = [], [], [], [], []
    instruments = sorted(table.instrument.unique())
    for variant, column in score_columns.items():
        previous = pd.Series(0., index=instruments)
        for date, rows in table.groupby("date", sort=True):
            use = rows[rows.eligible].set_index("instrument")
            scores = use[column]
            bins = quantile_weights(scores, q)
            held = pd.Series(0., index=instruments)
            held.loc[use.index] = gross / 2 * (bins[q] - bins[1])
            turnover = float((held - previous).abs().sum())
            exposure = float(held.abs().sum())
            components = {
                "commission_cost": turnover * costs["commission_bps"] / 10000,
                "spread_cost": turnover * costs["spread_bps"] / 10000,
                "impact_cost": turnover * costs["impact_bps"] / 10000,
                "financing_cost": max(exposure - 1, 0) * costs["financing_bps_annual"] / 10000 / 12,
                "roll_cost": exposure * costs["roll_bps_per_period"] / 10000,
                "short_borrow_cost": float(-held.clip(upper=0).sum()) * costs["short_borrow_bps_annual"] / 10000 / 12,
            }
            pnl = float(held @ rows.set_index("instrument")["return"].reindex(instruments))
            returns.append({"variant": variant, "date": date, "gross_return": pnl, **components,
                            "net_return": pnl - sum(components.values()), "gross_leverage": exposure,
                            "turnover": turnover})
            diagnostics.append({"variant": variant, "date": date, "n_eligible": len(use), "n_total": len(rows),
                                "coverage": 1., "eligible_fraction": len(use) / len(rows), "ic": correlation(scores, use["return"]),
                                "rank_ic": correlation(scores, use["return"], rank=True)})
            for bucket in bins.columns:
                quantile_returns.append({"variant": variant, "date": date, "quantile": bucket,
                                         "gross_return": float(bins[bucket] @ use["return"])})
            signals.extend({"variant": variant, "date": date, "instrument": symbol,
                            "value": float(value)} for symbol, value in scores.items())
            positions.extend({"variant": variant, "date": date, "instrument": symbol,
                              "weight": float(value)} for symbol, value in held.items())
            previous = held
    return {"signals": pd.DataFrame(signals), "positions": pd.DataFrame(positions), "returns": pd.DataFrame(returns),
            "diagnostics": pd.DataFrame(diagnostics), "quantiles": pd.DataFrame(quantile_returns)}

def mean_interval(differences: np.ndarray, validation: dict, seed: int, synthetic: bool) -> dict:
    values = np.asarray(differences, dtype=float)
    defined = np.isfinite(values)
    result = {"metric": validation["metric"], "difference": float(values[defined].mean()) if defined.any() else None,
              "ci_lower": None, "ci_upper": None, "confidence": validation["confidence"],
              "observations": len(values), "defined_observations": int(defined.sum()),
              "bootstrap_samples": validation["bootstrap_samples"],
              "bootstrap_block_periods": validation["bootstrap_block_periods"],
              "method": "paired monthly non-circular moving blocks; undefined months retain calendar positions",
              "conclusion": "inconclusive"}
    block = validation["bootstrap_block_periods"]
    if len(values) < 2 * block or defined.sum() < 12:
        result["reason"] = "Insufficient paired monthly observations"
    else:
        rng = np.random.default_rng(seed)
        samples = []
        for _ in range(validation["bootstrap_samples"]):
            starts = rng.integers(0, len(values) - block + 1, math.ceil(len(values) / block))
            indices = np.concatenate([np.arange(i, i + block) for i in starts])[:len(values)]
            draw = values[indices]
            if np.isfinite(draw).sum() >= 12:
                samples.append(float(draw[np.isfinite(draw)].mean()))
        if len(samples) >= validation["bootstrap_samples"] // 2:
            alpha = (1 - validation["confidence"]) / 2
            lower, upper = np.quantile(samples, [alpha, 1 - alpha])
            result.update(ci_lower=float(lower), ci_upper=float(upper),
                          conclusion="supported" if lower > 0 else "rejected" if upper <= 0 else "inconclusive")
    if synthetic:
        result["diagnostic_direction"] = result["conclusion"]
        result["conclusion"] = "untested_synthetic"
    return result

def summaries(result: dict) -> dict:
    diagnostics = result["diagnostics"]
    def nullable_mean(series):
        values = series.dropna()
        return float(values.mean()) if len(values) else None
    return {
        "variants": {name: _summary(rows) for name, rows in result["returns"].groupby("variant", sort=False)},
        "cost_stress_2x": {"method": "double all declared costs with unchanged weights",
                          "variants": {name: _summary(rows, multiplier=2) for name, rows in result["returns"].groupby("variant", sort=False)}},
        "factor_diagnostics": {name: {"mean_ic": nullable_mean(rows.ic), "mean_rank_ic": nullable_mean(rows.rank_ic),
                                     "defined_rank_ic_months": int(rows.rank_ic.notna().sum()),
                                     "mean_eligible_instruments": float(rows.n_eligible.mean()),
                                     "mean_feature_coverage": float(rows.coverage.mean()), "mean_eligible_fraction": float(rows.eligible_fraction.mean())}
                               for name, rows in diagnostics.groupby("variant", sort=False)},
    }

def run_factor(spec: dict, frame: pd.DataFrame) -> dict:
    panel = context(spec, frame)
    if (spec["artifact_type"], spec["analysis_type"], spec["implementation"]["entrypoint"]) != (
            "factor", "cross_sectional", "qg_cs_001_reference"):
        raise ValidationError("Unsupported cross-sectional reference specification")
    table = feature_table(panel)
    validation, impl = spec["validation"], spec["implementation"]
    selected = select_period(table, validation["evaluation_start"], validation["evaluation_end"])
    require_features(selected, ["momentum_12_1", "momentum_6_1"], impl["quantiles"])
    result = portfolios(selected, {"candidate": "momentum_12_1", "baseline": "momentum_6_1"}, impl)
    paired = result["diagnostics"].pivot(index="date", columns="variant", values="rank_ic").sort_index()
    comparison = mean_interval((paired.candidate - paired.baseline).to_numpy(), validation, spec["execution"]["seed"],
                               spec["reproduction_level"] == "pipeline_demo")
    result["metrics"] = {**summaries(result), "reproduction_level": spec["reproduction_level"],
                         "conclusion": comparison["conclusion"], "comparison": comparison,
                         "evaluation_start": validation["evaluation_start"], "evaluation_end": validation["evaluation_end"],
                         "primary_test": "mean monthly RankIC improvement over fixed 6-1 momentum",
                         "quantile_returns": "long-only equal-fraction buckets, gross before costs",
                         "interpretation": "Synthetic software scenario only; not a French momentum factor replication."}
    result["checks"] = {"conclusion": comparison["conclusion"], "eligibility_known_at_decision": True,
                        "features_use_completed_past_months": True, "initial_position": "flat, entry charged",
                        "tie_rule": "fractional quantile boundary allocation; equal scores treated equally",
                        "accounting": "monthly constant-notional; turnover is L1 target change; no wealth drift/fills",
                        "short_borrow_cost": "separate from gross-over-one financing; charged on absolute short exposure",
                        "original_historical_results_reproduced": False}
    result["factor_values"] = selected
    return result
