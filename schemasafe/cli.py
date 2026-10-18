import argparse
import glob
import json
import os
import sys

from .scanner import scan

ORDER = {"low": 0, "medium": 1, "high": 2}


def _collect(paths):
    files, seen = [], set()
    for path in paths:
        if os.path.isdir(path):
            found = sorted(glob.glob(os.path.join(path, "**", "*.sql"), recursive=True))
        else:
            found = [path]
        for f in found:
            key = os.path.abspath(f)
            if key not in seen:
                seen.add(key)
                files.append(f)
    return files


def main(argv=None):
    p = argparse.ArgumentParser(prog="schemasafe", description="Flag risky PostgreSQL migration statements.")
    p.add_argument("paths", nargs="+", help="SQL files or directories")
    p.add_argument("--min-severity", choices=list(ORDER), default="low")
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args(argv)

    files = _collect(args.paths)
    if not files:
        print("schemasafe: no .sql files found", file=sys.stderr)
        return 2

    threshold = ORDER[args.min_severity]
    findings = []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                text = fh.read()
        except (OSError, UnicodeError) as exc:
            print(f"schemasafe: {f}: {exc}", file=sys.stderr)
            return 2
        for line, rule, sev, msg in scan(text):
            if ORDER.get(sev, ORDER["high"]) >= threshold:
                findings.append({"file": f, "line": line, "rule": rule, "severity": sev, "message": msg})

    if args.format == "json":
        print(json.dumps(findings, indent=2))
    elif findings:
        for x in findings:
            print(f"{x['file']}:{x['line']} [{x['severity'].upper()}] {x['rule']}: {x['message']}")
    else:
        print("No risky statements found.")
    return 1 if findings else 0
