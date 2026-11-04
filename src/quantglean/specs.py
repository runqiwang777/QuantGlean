"""Declarative specifications and content-addressed freezing.

Only data is loaded from YAML; specifications never execute expressions or imports.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import yaml


class ValidationError(ValueError):
    """A specification, dataset, or experiment violates an explicit contract."""


def _json_values(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_values(item) for item in value]
    return value


def load_spec(path: str | Path) -> dict:
    """Read a JSON or safe YAML mapping, without executing source-supplied code."""
    source = Path(path)
    content = source.read_text(encoding="utf-8-sig")
    try:
        result = json.loads(content) if source.suffix.lower() == ".json" else yaml.safe_load(content)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ValidationError(f"Cannot parse specification: {exc}") from exc
    if not isinstance(result, dict):
        raise ValidationError("Specification must be a mapping")
    return _json_values(result)


def canonical_hash(spec: dict) -> str:
    """Hash every JSON field except the hash itself, including the frozen status."""
    payload = deepcopy(spec)
    payload.pop("spec_hash", None)
    try:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValidationError("Specification must contain finite JSON-compatible values") from exc
    return hashlib.sha256(encoded).hexdigest()


def _number(value: Any, *, integer: bool = False) -> bool:
    return (isinstance(value, int) if integer else isinstance(value, (int, float))) and not isinstance(value, bool) and math.isfinite(value)


def _sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value.lower())


def validate_spec(spec: dict) -> list[str]:
    """Return actionable errors; accepting a schema never implies runner support."""
    if not isinstance(spec, dict):
        return ["Specification must be a mapping"]
    errors: list[str] = []
    for field in ("id", "analysis_type"):
        if not isinstance(spec.get(field), str) or not spec[field].strip():
            errors.append(f"{field} must be a nonempty string")
    if spec.get("spec_version") != 1:
        errors.append("spec_version must be 1")
    if spec.get("status") not in ("draft", "spec_ready"):
        errors.append("status must be draft or spec_ready")
    if spec.get("artifact_type") not in ("factor", "model", "infra"):
        errors.append("artifact_type must be factor, model, or infra")
    level = spec.get("reproduction_level")
    if level == "result_reproduction":
        errors.append("result_reproduction is unavailable: this MVP cannot reproduce the original historical result")
    elif level not in ("pipeline_demo", "method_reimplementation", "inspired_extension"):
        errors.append("reproduction_level must be pipeline_demo, method_reimplementation, or inspired_extension")
    objects: dict[str, dict] = {}
    for field in ("source", "implementation", "data", "validation", "execution"):
        obj = spec.get(field)
        if not isinstance(obj, dict):
            errors.append(f"{field} must be a mapping")
            obj = {}
        objects[field] = obj
    source = objects["source"]
    for field in ("case", "url"):
        if not isinstance(source.get(field), str) or not source[field].strip():
            errors.append(f"source.{field} must be a nonempty string")
    if not _sha(source.get("sha256")):
        errors.append("source.sha256 must pin the report with a SHA256 fingerprint")
    evidence = source.get("evidence_ids")
    if not isinstance(evidence, list) or not evidence or any(not isinstance(x, str) or not x for x in evidence):
        errors.append("source.evidence_ids must be a nonempty list of evidence identifiers")
    implementation = objects["implementation"]
    if not isinstance(implementation.get("entrypoint"), str) or not implementation.get("entrypoint"):
        errors.append("implementation.entrypoint must name an explicit runner")
    # Other artifact types may be specified now; each future runner owns its schema.
    if spec.get("artifact_type") == "factor" and spec.get("analysis_type") == "time_series":
        lookbacks = implementation.get("lookbacks")
        if not isinstance(lookbacks, list) or not lookbacks or any(not _number(x, integer=True) or x < 1 for x in lookbacks):
            errors.append("implementation.lookbacks must be positive integer periods")
        elif len(set(lookbacks)) != len(lookbacks):
            errors.append("implementation.lookbacks must not contain duplicates")
        for field, minimum in (("baseline_lookback", 1), ("volatility_lookback", 2), ("execution_lag_periods", 1)):
            value = implementation.get(field)
            if not _number(value, integer=True) or value < minimum:
                errors.append(f"implementation.{field} must be an integer >= {minimum}")
        for field in ("min_volatility", "target_volatility", "max_gross_leverage"):
            value = implementation.get(field)
            if not _number(value) or value <= 0:
                errors.append(f"implementation.{field} must be positive and finite")
        if implementation.get("rebalance") != "monthly":
            errors.append("implementation.rebalance must be monthly")
        costs = implementation.get("costs")
        if not isinstance(costs, dict):
            errors.append("implementation.costs must explicitly declare all cost components")
            costs = {}
        for field in ("commission_bps", "spread_bps", "impact_bps", "financing_bps_annual", "roll_bps_per_period"):
            if not _number(costs.get(field)) or costs[field] < 0:
                errors.append(f"implementation.costs.{field} must be finite and nonnegative")
    if spec.get("analysis_type") in ("cross_sectional", "predictive"):
        errors.extend(_panel_errors(spec, objects))
    if spec.get("artifact_type") == "infra" and spec.get("analysis_type") == "point_in_time":
        errors.extend(_infra_errors(objects))
    choices = implementation.get("undocumented_choices")
    if not isinstance(choices, list) or not choices or any(not isinstance(x, str) or not x.strip() for x in choices):
        errors.append("implementation.undocumented_choices must list the reference implementation's own conventions")
    data = objects["data"]
    if data.get("manifest") is not None and (not isinstance(data["manifest"], str) or not data["manifest"].strip()):
        errors.append("data.manifest must be a local path or null")
    if data.get("sha256") is not None and not _sha(data["sha256"]):
        errors.append("data.sha256 must be a SHA256 fingerprint or null")
    if data.get("manifest_sha256") is not None and not _sha(data["manifest_sha256"]):
        errors.append("data.manifest_sha256 must be a SHA256 fingerprint or null")
    validation = objects["validation"]
    reference = spec.get("artifact_type") == "factor" and spec.get("analysis_type") == "time_series"
    parsed_dates = []
    for field in ("evaluation_start", "evaluation_end"):
        if not reference and field not in validation:
            continue
        value = validation.get(field)
        try:
            parsed_dates.append(date.fromisoformat(value))
        except (TypeError, ValueError):
            errors.append(f"validation.{field} must be an ISO calendar date")
    if len(parsed_dates) == 2 and parsed_dates[0] > parsed_dates[1]:
        errors.append("validation.evaluation_start must precede evaluation_end")
    if not isinstance(validation.get("metric"), str) or not validation.get("metric"):
        errors.append("validation.metric must be a nonempty string")
    if reference:
        if validation.get("metric") != "net_sharpe_difference":
            errors.append("validation.metric must be net_sharpe_difference")
        if validation.get("annualization") != 12:
            errors.append("validation.annualization must be 12 for monthly observations")
        for field, minimum, maximum in (("bootstrap_samples", 100, 100000), ("bootstrap_block_periods", 1, 1200)):
            if not _number(validation.get(field), integer=True) or not minimum <= validation[field] <= maximum:
                errors.append(f"validation.{field} must be an integer in [{minimum}, {maximum}]")
        confidence = validation.get("confidence")
        if not _number(confidence) or not 0 < confidence < 1:
            errors.append("validation.confidence must lie strictly between 0 and 1")
    seed = objects["execution"].get("seed")
    if not _number(seed, integer=True) or not 0 <= seed < 2**32:
        errors.append("execution.seed must be an integer in [0, 2**32)")
    missing = spec.get("missing_information")
    if not isinstance(missing, list):
        errors.append("missing_information must be an explicit list")
    elif missing:
        errors.append("missing_information is unresolved: " + "; ".join(str(x) for x in missing))
    try:
        actual = canonical_hash(spec)
        if spec.get("status") == "spec_ready" and spec.get("spec_hash") != actual:
            errors.append("spec_hash does not match the frozen specification; freeze again after edits")
    except ValidationError as exc:
        errors.append(str(exc))
    return errors


def freeze_spec(spec: dict) -> dict:
    """Validate and return a frozen copy; mutating it invalidates its fingerprint."""
    frozen = deepcopy(spec)
    # A changed frozen input must be deliberately frozen again, not rejected for its old hash.
    frozen["status"] = "draft"
    frozen.pop("spec_hash", None)
    errors = validate_spec(frozen)
    if errors:
        raise ValidationError("; ".join(errors))
    frozen["status"] = "spec_ready"
    frozen["spec_hash"] = canonical_hash(frozen)
    return frozen


def _panel_errors(spec: dict, objects: dict) -> list[str]:
    errors = []
    impl, validation = objects["implementation"], objects["validation"]
    model = spec.get("analysis_type") == "predictive"
    if spec.get("artifact_type") != ("model" if model else "factor"):
        errors.append("Panel analysis_type does not match artifact_type")
    expected_entry = "qg_model_001_reference" if model else "qg_cs_001_reference"
    if impl.get("entrypoint") != expected_entry:
        errors.append("Unsupported panel entrypoint")
    expected = {"lookback_periods": 12, "skip_periods": 1, "baseline_lookback_periods": 6,
                "execution_lag_periods": 1, "rebalance": "monthly"}
    for key, value in expected.items():
        if impl.get(key) != value:
            errors.append(f"implementation.{key} must be {value!r} for this reviewed reference")
    if not _number(impl.get("quantiles"), integer=True) or not 3 <= impl["quantiles"] <= 10:
        errors.append("implementation.quantiles must be an integer in [3, 10]")
    if not _number(impl.get("gross_leverage")) or not 0 < impl["gross_leverage"] <= 2:
        errors.append("implementation.gross_leverage must be in (0, 2]")
    costs = impl.get("costs", {})
    if not isinstance(costs, dict):
        costs = {}
    for key in ("commission_bps", "spread_bps", "impact_bps", "financing_bps_annual",
                "roll_bps_per_period", "short_borrow_bps_annual"):
        if not _number(costs.get(key)) or costs[key] < 0:
            errors.append(f"implementation.costs.{key} must be finite and nonnegative")
    fields = ["evaluation_start", "evaluation_end"]
    if model:
        fields = ["train_start", "train_end", "valid_start", "valid_end"] + fields
        if impl.get("backend") not in ("numpy", "qlib"):
            errors.append("implementation.backend must be numpy or qlib")
        if not _number(impl.get("ridge_alpha")) or impl["ridge_alpha"] <= 0:
            errors.append("implementation.ridge_alpha must be positive")
        if impl.get("features") != ["momentum_12_1", "reversal_1", "volatility_12"]:
            errors.append("implementation.features must match the three reviewed causal features")
        if impl.get("label_horizon_periods") != 1:
            errors.append("Only a one-month forward label is implemented")
        if not _number(validation.get("gap_periods"), integer=True) or validation["gap_periods"] < 1:
            errors.append("validation.gap_periods must be >= 1")
    parsed = {}
    for key in fields:
        try:
            value = date.fromisoformat(validation.get(key))
            import calendar
            if value.day != calendar.monthrange(value.year, value.month)[1]:
                raise ValueError("month-end required")
            parsed[key] = value
        except (ValueError, TypeError):
            errors.append(f"validation.{key} must be an ISO month-end")
    if len(parsed) == len(fields):
        ordered = [parsed[key] for key in fields]
        if any(a > b for a,b in zip(ordered, ordered[1:])):
            errors.append("Train, validation and evaluation bounds must be chronological and non-overlapping")
        if model and _number(validation.get("gap_periods"), integer=True):
            def month(value): return value.year * 12 + value.month
            for end, start in (("train_end", "valid_start"), ("valid_end", "evaluation_start")):
                if month(parsed[start]) - month(parsed[end]) <= validation["gap_periods"]:
                    errors.append("Each split requires the declared number of complete gap months")
    metric = "mse_improvement" if model else "rank_ic_improvement"
    if validation.get("metric") != metric:
        errors.append(f"validation.metric must be {metric}")
    if validation.get("annualization") != 12:
        errors.append("validation.annualization must be 12")
    for key, low, high in (("bootstrap_samples", 100, 100000), ("bootstrap_block_periods", 1, 1200)):
        if not _number(validation.get(key), integer=True) or not low <= validation[key] <= high:
            errors.append(f"validation.{key} must be an integer in [{low}, {high}]")
    if not _number(validation.get("confidence")) or not 0 < validation["confidence"] < 1:
        errors.append("validation.confidence must be strictly between zero and one")
    return errors


def _infra_errors(objects):
    errors = []
    impl, validation = objects["implementation"], objects["validation"]
    expected = {"entrypoint": "qg_infra_001_reference", "event_selection": "latest_known_before_cutoff",
                "revision_selection": "latest_available_then_revision", "withdrawal_policy": "missing_without_fallback",
                "availability_boundary": "inclusive"}
    for key, value in expected.items():
        if impl.get(key) != value:
            errors.append(f"implementation.{key} must be {value!r}")
    config = impl.get("benchmark", {})
    if not isinstance(config, dict):
        return errors + ["implementation.benchmark must be a mapping"]
    counts = config.get("query_counts")
    if (not isinstance(counts, list) or not counts or len(counts) > 5
            or any(not _number(v, integer=True) or not 1 <= v <= 5000 for v in counts)):
        errors.append("benchmark.query_counts must contain 1..5 integer workloads in [1,5000]")
    elif counts != sorted(set(counts)):
        errors.append("benchmark.query_counts must be strictly increasing")
    if not _number(config.get("repetitions"), integer=True) or not 2 <= config["repetitions"] <= 10:
        errors.append("benchmark.repetitions must be in [2,10]")
    if config.get("memory_measurement") != "tracemalloc_python_peak":
        errors.append("Only separate Python allocation peaks are implemented")
    if validation.get("metric") != "snapshot_equivalence":
        errors.append("validation.metric must be snapshot_equivalence")
    return errors
