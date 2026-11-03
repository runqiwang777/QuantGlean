"""Reports from recorded artifacts; never infer a successful reproduction."""
from __future__ import annotations
import html
import json
from pathlib import Path

DISCLAIMER = (
    "Monthly constant-notional excess-return research accounting. "
    "Not a trade/fill simulator. Synthetic data tests the pipeline only. "
    "This implementation does not reproduce the original paper's historical results. QuantStats period statistics are not executed-trade statistics."
)

def write_report(run_dir: str | Path) -> Path:
    root = Path(run_dir)
    manifest = json.loads((root / "run_manifest.json").read_text(encoding="utf-8"))
    metrics_path = root / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    lines = [
        "# QuantGlean reproduction report", "",
        f"- Run: {manifest['run_id']}",
        f"- Status: {manifest['status']}",
        f"- Level: {manifest.get('reproduction_level', 'unknown')}",
        f"- Conclusion: {manifest.get('conclusion', 'untested')}",
        f"- Spec SHA256: {manifest.get('spec_hash')}",
        f"- Dataset SHA256: {manifest.get('data_sha256')}",
        f"- Started (UTC): {manifest['started_at']}",
        f"- Code: {manifest.get('code', {})}", "", DISCLAIMER, "",
    ]
    spec_path = root / "frozen_spec.json"
    if spec_path.exists():
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        source = spec.get("source", {})
        lines += ["## Research source and protocol", "",
                  "Source record: " + str(source.get("url", "unavailable")),
                  "Report SHA256: " + str(source.get("sha256")),
                  "Evidence IDs: " + ", ".join(source.get("evidence_ids", [])),
                  "Evaluation: " + str(spec.get("validation", {}).get("evaluation_start")) + " to "
                  + str(spec.get("validation", {}).get("evaluation_end")), ""]
    if metrics.get("variants"):
        lines += ["## Measured net excess-return results", "",
                  "| Variant | Net Sharpe | Annual vol | Max drawdown | Mean turnover |",
                  "| --- | ---: | ---: | ---: | ---: |"]
        def number(value):
            return "undefined" if value is None else f"{value:.6f}"
        for variant, row in metrics["variants"].items():
            lines.append("| " + variant + " | " + " | ".join(number(row.get(key)) for key in
                         ("sharpe", "annualized_volatility", "max_drawdown", "average_turnover")) + " |")
        comparison = metrics.get("comparison", {})
        lines += ["", "Primary comparison (candidate minus fixed baseline): " + str(comparison.get("difference")),
                  "Interval: [" + str(comparison.get("ci_lower")) + ", " + str(comparison.get("ci_upper")) + "]",
                  "Conclusion: " + str(manifest.get("conclusion")), "",
                  "Full metrics below include twice-cost stress with unchanged positions.", ""]
    if manifest.get("error"):
        lines += ["## Failure / missing information", "", manifest["error"], ""]
    if metrics:
        lines += ["## Recorded metrics", "", "Undefined statistics are null. Sharpe uses excess returns and annualization 12.",
                  "Intervals are exploratory paired moving-block bootstrap estimates; they do not establish causality or remove selection bias.", "",
                  "```json", json.dumps(metrics, indent=2, ensure_ascii=False, allow_nan=False), "```", ""]
    lines += ["## Audit trail", "", "See frozen_spec.json, data_manifest.json (when available), checks.json, "
              "implementation_differences.md, and artifact SHA256 values in run_manifest.json.",
              "The manifest records the actual environment and command; inspect code.dirty before treating a commit as exact code provenance.", ""]
    md = "\n".join(lines)
    (root / "report.md").write_text(md, encoding="utf-8")
    # Escape all report content. No source-supplied HTML or executable scripts.
    body = ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>QuantGlean experiment report</title>'
            '<style>body{max-width:1000px;margin:3rem auto;padding:0 1rem;font:16px/1.6 system-ui;'
            'color:#153d36;background:#fafbf9}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>'
            '<main><pre>' + html.escape(md) + '</pre></main></html>')
    (root / "report.html").write_text(body, encoding="utf-8")
    return root / "report.html"

def quantstats_report(run_dir: str | Path) -> Path:
    """Optional public API adapter. All inputs are local return series, no tickers."""
    import pandas as pd
    import quantstats as qs
    root = Path(run_dir)
    manifest = json.loads((root / "run_manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "completed":
        raise ValueError("QuantStats requires a completed run")
    frame = pd.read_csv(root / "returns.csv")
    # QuantStats internally aligns against naive calendar dates.
    frame["date"] = pd.to_datetime(frame["date"], utc=True).dt.tz_localize(None)
    wide = frame.pivot(index="date", columns="variant", values="net_return").sort_index()
    if len(wide) < 24:
        raise ValueError("QuantStats report requires at least 24 monthly evaluation observations")
    target = root / "quantstats.html"
    qs.reports.html(wide["candidate"], benchmark=wide["baseline"], output=str(target),
                    title="QuantGlean | " + manifest["reproduction_level"] + " | net EXCESS returns",
                    periods_per_year=12, compounded=True, rf=0,
                    download_filename="quantstats.html")
    # Preserve QuantStats' generated notices and link back to the provenance report.
    content = target.read_text(encoding="utf-8")
    banner = ('<aside style="padding:20px;background:#fff1cc;color:#152e2a">'
              '<strong>QuantGlean: ' + html.escape(manifest["reproduction_level"]) + '</strong> — '
              + html.escape(DISCLAIMER) + ' <a href="report.html">Provenance and conclusion</a></aside>')
    import re
    content, n = re.subn(r"(<body[^>]*>)", lambda m: m.group(1) + banner, content, count=1, flags=re.I)
    if not n:
        content = banner + content
    target.write_text(content, encoding="utf-8")
    # The generated HTML includes an upstream template; retain its distribution license.
    import importlib.metadata
    distribution = importlib.metadata.distribution("quantstats")
    for item in distribution.files or []:
        if item.name.upper().split(".")[0] in {"LICENSE", "NOTICE"}:
            license_name = "quantstats-" + item.name
            (root / license_name).write_bytes(distribution.locate_file(item).read_bytes())
    (root / "quantstats-ATTRIBUTION.md").write_text(
        "# QuantStats report component\n\nGenerated using QuantStats " + distribution.version +
        " by Ran Aroussi and contributors. Apache-2.0.\n"
        "Source: https://github.com/ranaroussi/quantstats\n"
        "QuantGlean changes: provenance warning banner and local monthly excess-return input.\n",
        encoding="utf-8")
    return target
