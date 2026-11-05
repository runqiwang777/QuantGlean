#!/usr/bin/env python3
"""Score model-generated regional Mom CSVs against Ken French's official factor files.

The eight official ZIPs stay local. Invalid month/region coverage receives no
numeric accuracy score; filtering duplicate rows after seeing answers is forbidden.
"""
from __future__ import annotations

import csv
import json
import math
import re
import runpy
import sys
from collections import Counter
from pathlib import Path

REGIONS = ["North_America", "Europe", "Japan", "Asia_Pacific_ex_Japan"]
DATE = re.compile(r"^(\d{4})-?(\d{2})(?:-\d{2})?$")


def score(source_dir: Path, arms_dir: Path) -> dict:
    base = runpy.run_path(str(Path(__file__).with_name("audit-french-momentum.py")))
    expected = {}
    for region in REGIONS:
        _, factor_name = base["PAIR_NAMES"][region]
        lines, _ = base["source_lines"](source_dir / factor_name)
        official = base["monthly"](lines, factor=True)
        expected.update({(region, date): value[0] for date, value in official.items()})
    out = {"official_observations": len(expected), "official_scope": "current-vintage published regional factor returns", "arms": {}}
    for arm in ("sol", "luna", "luna_qg", "luna_qg_v2"):
        file = arms_dir / arm / "factor.csv"
        rows = []
        malformed = 0
        total_rows = 0
        with file.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["region", "date", "wml_percentage_points"]:
                raise ValueError(f"Wrong CSV header for {arm}: {reader.fieldnames}")
            for row in reader:
                total_rows += 1
                match = DATE.fullmatch(row["date"])
                if not match:
                    malformed += 1
                    continue
                date = "".join(match.groups())
                value = float(row["wml_percentage_points"])
                if not math.isfinite(value):
                    raise ValueError(f"Nonfinite output from {arm}")
                rows.append(((row["region"], date), value))
        counts = Counter(key for key, _ in rows)
        missing = set(expected) - set(counts)
        unexpected = set(counts) - set(expected)
        duplicates = sum(n - 1 for n in counts.values() if n > 1)
        item = {
            "rows": total_rows,
            "malformed_rows": malformed,
            "distinct_region_months": len(counts),
            "duplicate_rows": duplicates,
            "missing_region_months": len(missing),
            "unexpected_region_months": len(unexpected),
            "valid_complete_series": not (duplicates or missing or unexpected or malformed),
        }
        if item["valid_complete_series"]:
            errors = [value - expected[key] for key, value in rows]
            item["mae_percentage_points"] = sum(abs(e) for e in errors) / len(errors)
            item["max_absolute_error_percentage_points"] = max(abs(e) for e in errors)
        else:
            item["numeric_score"] = "withheld: monthly series is not one row per expected region/month"
        out["arms"][arm] = item
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/score-french-momentum-arms.py OFFICIAL_ZIP_DIR ARMS_DIR")
    print(json.dumps(score(Path(sys.argv[1]), Path(sys.argv[2])), ensure_ascii=False, indent=2))
