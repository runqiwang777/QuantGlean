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
