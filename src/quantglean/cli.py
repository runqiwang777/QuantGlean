"""Local-only CLI: no arbitrary entrypoint execution or automatic downloads."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from .specs import freeze_spec, load_spec, validate_spec
from .runs import dump, execute, finalize
from .reporting import quantstats_report, write_report

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="qg", description="QuantGlean local research experiments")
    sub = parser.add_subparsers(dest="action", required=True)
    validate = sub.add_parser("validate"); validate.add_argument("spec")
    freeze = sub.add_parser("freeze"); freeze.add_argument("spec"); freeze.add_argument("--output", required=True)
    scaffold = sub.add_parser("scaffold"); scaffold.add_argument("spec"); scaffold.add_argument("--output", required=True)
    run = sub.add_parser("run"); run.add_argument("spec"); run.add_argument("--data-manifest")
    run.add_argument("--output", required=True); run.add_argument("--parquet", action="store_true")
    report = sub.add_parser("report"); report.add_argument("run_directory"); report.add_argument("--quantstats", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "validate":
            errors = validate_spec(load_spec(args.spec))
            print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
            return 1 if errors else 0
        if args.action == "freeze":
            target = Path(args.output)
            if target.exists():
                raise ValueError("Output already exists; choose a new spec version path")
            frozen = freeze_spec(load_spec(args.spec))
            target.parent.mkdir(parents=True, exist_ok=True)
            dump(target, frozen)  # JSON is also valid YAML.
            print(frozen["spec_hash"])
        elif args.action == "scaffold":
            spec = load_spec(args.spec)
            errors = validate_spec(spec)
            if errors:
                raise ValueError("; ".join(errors))
            root = Path(args.output)
            root.mkdir(parents=True, exist_ok=False)
            dump(root / "experiment.json", spec)
            (root / "IMPLEMENTATION.md").write_text(
                "# Implementation task\n\n"
                f"Artifact type: {spec['artifact_type']}\n\n"
                "Specify formula, point-in-time data, fixed baseline, split, costs, evidence and tests.\n"
                "Reviewed runners: time-series trend, cross-sectional momentum, fixed-split ridge.\n"
                "Other model families and infra execution remain design scaffolds.\n",
                encoding="utf-8")
            print(root)
        elif args.action == "run":
            root, manifest = execute(args.spec, args.data_manifest, args.output, parquet=args.parquet,
                                     command=["qg", *(argv if argv is not None else sys.argv[1:])])
            print(json.dumps({"run_directory": str(root), "status": manifest["status"],
                              "conclusion": manifest["conclusion"], "error": manifest.get("error")}, indent=2))
            return 0 if manifest["status"] == "completed" else 2
        elif args.action == "report":
            root = Path(args.run_directory)
            print(write_report(root))
            if args.quantstats:
                print(quantstats_report(root))
            manifest = json.loads((root / "run_manifest.json").read_text(encoding="utf-8"))
            finalize(root, manifest)
        return 0
    except (ValueError, TypeError, OSError, KeyError, ImportError) as exc:
        print(f"qg: {exc}", file=sys.stderr)
        return 1
