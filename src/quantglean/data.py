"""Strict local data manifests. No downloads, implicit filling, or universe inference."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path, PureWindowsPath

import numpy as np
import pandas as pd
import yaml

from .specs import ValidationError


def load_dataset(manifest_path: str | Path) -> tuple[pd.DataFrame, dict]:
    """Validate a local monthly excess-return panel and its declared provenance."""
    manifest_file = Path(manifest_path).resolve()
    content = manifest_file.read_text(encoding="utf-8-sig")
    try:
        manifest = json.loads(content) if manifest_file.suffix.lower() == ".json" else yaml.safe_load(content)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ValidationError(f"Cannot parse data manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValidationError("Data manifest must be a mapping")
    if manifest.get("schema_version") != 1:
        raise ValidationError("Data manifest schema_version must be 1")
    source, rights, universe = (manifest.get(field) for field in ("source", "rights", "universe"))
    if not isinstance(source, dict) or source.get("kind") not in ("synthetic", "user_supplied"):
        raise ValidationError("source.kind must be synthetic or user_supplied")
    if not isinstance(source.get("description"), str) or not source["description"].strip():
        raise ValidationError("source.description must describe the generator or data provenance")
    if not isinstance(rights, dict) or any(type(rights.get(field)) is not bool for field in ("use_permitted", "redistribution_permitted")):
        raise ValidationError("rights must explicitly declare boolean use_permitted and redistribution_permitted")
    if rights["use_permitted"] is not True:
        raise ValidationError("Data use must be explicitly permitted")
    if not isinstance(rights.get("description"), str) or not rights["description"].strip():
        raise ValidationError("rights.description must explain the permission or license")
    if not isinstance(universe, dict) or any(not isinstance(universe.get(field), str) or not universe[field].strip() for field in ("eligibility", "survivorship")):
        raise ValidationError("universe must declare eligibility and survivorship assumptions")
    if not isinstance(manifest.get("adjustments"), str) or not manifest["adjustments"].strip():
        raise ValidationError("adjustments must describe data transformations, including none")
    if manifest.get("frequency") != "monthly":
        raise ValidationError("Only explicit monthly frequency is supported")
    if manifest.get("returns_kind") != "simple_excess":
        raise ValidationError("returns_kind must be simple_excess; prices and total/log returns need an explicit external conversion")
    data_name = manifest.get("data_path")
    if not isinstance(data_name, str) or not data_name.strip():
        raise ValidationError("data_path must be a local path relative to the manifest")
    if "://" in data_name or Path(data_name).is_absolute() or PureWindowsPath(data_name).is_absolute() or PureWindowsPath(data_name).drive or data_name.startswith(("\\\\", "//")):
        raise ValidationError("data_path must be local and relative to the manifest; URLs and network paths are unsupported")
    data_file = (manifest_file.parent / data_name).resolve()
    if not data_file.is_file():
        raise ValidationError(f"Dataset file is unavailable: {data_file}")
    fingerprint = hashlib.sha256(data_file.read_bytes()).hexdigest()
    if manifest.get("sha256") != fingerprint:
        raise ValidationError("Dataset SHA256 mismatch: manifest must pin the actual file bytes")
    if data_file.suffix.lower() == ".csv":
        frame = pd.read_csv(data_file)
    elif data_file.suffix.lower() in {".parquet", ".pq"}:
        frame = pd.read_parquet(data_file)
    else:
        raise ValidationError("Dataset must be a CSV or Parquet file")
    frame = validate_panel(frame)
    frame.attrs.update(source_kind=source["kind"], data_sha256=fingerprint,
                       universe=deepcopy(universe), frequency="monthly", returns_kind="simple_excess")
    enriched = deepcopy(manifest)
    # The exact original manifest is retained; its own fingerprint is recorded by the run package.
    return frame, enriched


def validate_panel(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a validated copy, keeping every observation and rejecting gaps."""
    required = {"date", "instrument", "return", "available_at"}
    if not required.issubset(frame.columns):
        raise ValidationError("Dataset requires columns date, instrument, return, available_at")
    if frame.empty:
        raise ValidationError("Dataset is empty")
    result = frame.copy()
    if result[list(required)].isna().any().any():
        raise ValidationError("Dataset contains missing required values")
    try:
        result["date"] = pd.to_datetime(result["date"], utc=True, errors="raise", format="mixed")
        result["available_at"] = pd.to_datetime(result["available_at"], utc=True, errors="raise", format="mixed")
        result["return"] = pd.to_numeric(result["return"], errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"Invalid timestamp or return: {exc}") from exc
    if result[["date", "available_at", "return"]].isna().any().any():
        raise ValidationError("Dataset contains missing timestamps or returns")
    if not np.isfinite(result["return"].to_numpy(dtype=float)).all() or (result["return"] <= -1).any():
        raise ValidationError("Returns must be finite simple excess returns strictly greater than -1")
    if not result["instrument"].map(lambda x: isinstance(x, str) and bool(x.strip())).all():
        raise ValidationError("instrument must contain nonempty string identifiers")
    if not result["date"].is_monotonic_increasing:
        raise ValidationError("Dataset rows must be chronological by date; sort explicitly before fingerprinting")
    month_ends = result["date"].dt.tz_localize(None).dt.to_period("M").dt.to_timestamp("M").dt.tz_localize("UTC")
    if not result["date"].equals(month_ends.rename("date")):
        raise ValidationError("date must be the UTC calendar month-end at midnight")
    if result.duplicated(["date", "instrument"]).any():
        raise ValidationError("Duplicate date/instrument observations are not allowed")
    decisions = month_ends + pd.offsets.MonthBegin(1)
    if (result["available_at"] < month_ends).any():
        raise ValidationError("available_at precedes the completed monthly return date")
    if (result["available_at"] > decisions).any():
        raise ValidationError("available_at is after the next-month decision; this would introduce look-ahead")
    all_dates = pd.DatetimeIndex(result["date"].drop_duplicates())
    expected = pd.date_range(all_dates[0], all_dates[-1], freq=pd.offsets.MonthEnd(), tz="UTC")
    if not all_dates.equals(expected):
        raise ValidationError("Monthly history has gaps; no silent filling is allowed")
    for instrument, rows in result.groupby("instrument", sort=False):
        if not pd.DatetimeIndex(rows["date"]).equals(all_dates):
            raise ValidationError(f"Instrument {instrument} lacks the complete shared monthly grid; declare an eligible fixed panel explicitly")
    result = result.sort_values(["date", "instrument"], kind="stable").reset_index(drop=True)
    return result
