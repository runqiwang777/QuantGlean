#!/usr/bin/env python3
"""Summarize AQR's original TSMOM workbook without copying its rows to disk.

Requires openpyxl: python -m pip install openpyxl
The workbook stays at the user-supplied path. Output contains metadata/statistics only.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

try:
    import openpyxl
except ImportError as exc:
    raise SystemExit("Install the optional reader first: python -m pip install openpyxl") from exc


def summarize(path: Path) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = book["TSMOM factors"]
    rows = list(sheet.iter_rows(values_only=True))
    header_index = next(i for i, row in enumerate(rows) if row and row[0] == "DATE")
    headers = rows[header_index]
    data = [r for r in rows[header_index + 1 :] if isinstance(r[0], datetime)]
    if len(data) != 300 or data[0][0].strftime("%Y-%m") != "1985-01" or data[-1][0].strftime("%Y-%m") != "2009-12":
        raise ValueError("Unexpected sample: expected 300 monthly rows from 1985-01 through 2009-12")
    result = {}
    for col, name in enumerate(headers[1:6], 1):
        values = [float(row[col]) for row in data if isinstance(row[col], (int, float))]
        if len(values) != 300 or min(values) <= -1:
            raise ValueError(f"Unexpected or incomplete return series: {name}")
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        result[name] = {
            "observations": len(values),
            "annualized_arithmetic_mean": mean * 12,
            "annualized_sample_volatility": std * math.sqrt(12),
            "annualized_sharpe_arithmetic": mean / std * math.sqrt(12),
            "annualized_geometric_return": math.prod(1 + x for x in values) ** (12 / len(values)) - 1,
        }
    return {
        "source": "AQR Capital Management, LLC — Time Series Momentum: Original Paper Data",
        "sha256": digest,
        "start": data[0][0].strftime("%Y-%m-%d"),
        "end": data[-1][0].strftime("%Y-%m-%d"),
        "monthly_rows": len(data),
        "statistics": result,
        "note": "Descriptive calculations on published portfolio returns; not a raw-data strategy reconstruction.",
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/summarize-aqr-tsmom.py path/to/original-paper-data.xlsx")
    print(json.dumps(summarize(Path(sys.argv[1])), indent=2))
