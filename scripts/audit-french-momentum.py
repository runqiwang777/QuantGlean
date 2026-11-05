#!/usr/bin/env python3
"""Audit current Ken French regional Mom factors from the corresponding six portfolio files.

Input ZIPs are official downloads kept outside Git. This script emits aggregate
checks only; it neither extracts nor republishes monthly source returns.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

PAIR_NAMES = {
    "North_America": (
        "North_America_6_Portfolios_ME_Prior_12_2_CSV.zip",
        "North_America_Mom_Factor_CSV.zip",
    ),
    "Europe": ("Europe_6_Portfolios_ME_Prior_12_2_CSV.zip", "Europe_Mom_Factor_CSV.zip"),
    "Japan": ("Japan_6_Portfolios_ME_Prior_12_2_CSV.zip", "Japan_Mom_Factor_CSV.zip"),
    "Asia_Pacific_ex_Japan": (
        "Asia_Pacific_ex_Japan_6_Portfolios_ME_Prior_12_2_CSV.zip",
        "Asia_Pacific_ex_Japan_MOM_Factor_CSV.zip",
    ),
}
DATE = re.compile(r"^\d{6}$")


def source_lines(path: Path) -> tuple[list[str], str]:
    raw = path.read_bytes()
    with zipfile.ZipFile(path) as archive:
        entries = archive.namelist()
        if len(entries) != 1 or not entries[0].lower().endswith(".csv"):
            raise ValueError(f"Unexpected ZIP inventory: {path.name}")
        lines = archive.read(entries[0]).decode("latin1").splitlines()
    return lines, hashlib.sha256(raw).hexdigest()


def monthly(lines: list[str], factor: bool) -> dict[str, list[float]]:
    marker = ",WML" if factor else "Average Value Weighted Returns -- Monthly"
    try:
        pos = next(i for i, line in enumerate(lines) if marker in line)
    except StopIteration as exc:
        raise ValueError(f"Monthly section missing: {marker}") from exc
    if not factor:
        pos += 1  # six-column header precedes the monthly data
    out = {}
    for line in lines[pos + 1 :]:
        row = next(csv.reader([line]))
        date = row[0].strip() if row else ""
        if not DATE.fullmatch(date):
            if out:
                break
            continue
        expected = 2 if factor else 7
        if len(row) != expected:
            raise ValueError(f"Expected {expected} columns at {date}, found {len(row)}")
        values = [float(value.strip()) for value in row[1:]]
        if any(value <= -99 for value in values):
            raise ValueError(f"Missing-value sentinel in {date}")
        if date in out:
            raise ValueError(f"Duplicate month {date}")
        out[date] = values
    if not out:
        raise ValueError("No monthly data")
    return out


def audit(directory: Path) -> dict:
    result = {}
    for region, (portfolio_name, factor_name) in PAIR_NAMES.items():
        plines, phash = source_lines(directory / portfolio_name)
        flines, fhash = source_lines(directory / factor_name)
        p = monthly(plines, factor=False)
        f = monthly(flines, factor=True)
        dates = sorted(set(p) & set(f))
        if not dates:
            raise ValueError(f"No aligned months: {region}")
        # Columns: Small Low/Neutral/High, Big Low/Neutral/High; percentage points.
        errors = [0.5 * (p[d][2] + p[d][5] - p[d][0] - p[d][3]) - f[d][0] for d in dates]
        result[region] = {
            "source_sha256": {portfolio_name: phash, factor_name: fhash},
            "aligned_months": len(dates),
            "first_month": dates[0],
            "last_month": dates[-1],
            "max_absolute_error_percentage_points": max(abs(e) for e in errors),
            "mean_absolute_error_percentage_points": sum(abs(e) for e in errors) / len(errors),
            "months_within_0_011_percentage_points": sum(abs(e) <= 0.011 for e in errors),
            "formula": "0.5*(Small High + Big High - Small Low - Big Low)",
        }
    return {
        "source": "Kenneth R. French Data Library, regional monthly size-and-momentum portfolios and Mom factors",
        "scope": "Published portfolio aggregation only; not the paper's original security-level reconstruction",
        "regions": result,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/audit-french-momentum.py DIRECTORY_WITH_8_OFFICIAL_ZIPS")
    print(json.dumps(audit(Path(sys.argv[1])), ensure_ascii=False, indent=2))
