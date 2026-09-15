#!/usr/bin/env python3
"""Validate Eyal Plan Loop review JSON and hash plans. Stdlib only."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REQUIRED = ("verdict", "summary", "findings", "coverage", "limitations")
FINDING_KEYS = ("id", "severity", "path", "evidence", "fix")
VERDICTS = ("APPROVED", "REVISE", "BLOCKED")
SEVERITIES = ("high", "medium", "low")


class Fail(Exception):
    pass


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Fail(f"Invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise Fail("Review JSON must be an object.")
    return value


def validate_review(value: dict) -> None:
    if set(value) != set(REQUIRED):
        raise Fail("Review must contain exactly verdict, summary, findings, coverage, limitations.")
    if value["verdict"] not in VERDICTS:
        raise Fail("Invalid verdict.")
    if not isinstance(value["summary"], str) or not value["summary"].strip():
        raise Fail("Missing summary.")
    for key in ("coverage", "limitations"):
        items = value[key]
        if not isinstance(items, list) or any(not isinstance(x, str) or not x.strip() for x in items):
            raise Fail(f"Invalid {key} list.")
    if value["verdict"] != "BLOCKED" and not value["coverage"]:
        raise Fail("A completed review must identify what was inspected.")
    findings = value["findings"]
    if not isinstance(findings, list):
        raise Fail("Invalid findings list.")
    ids: set[str] = set()
    for finding in findings:
        if not isinstance(finding, dict) or set(finding) != set(FINDING_KEYS):
            raise Fail("Invalid finding fields.")
        if any(not isinstance(v, str) or not v.strip() for v in finding.values()):
            raise Fail("Every finding needs id, severity, path, evidence and fix.")
        if finding["id"] in ids or finding["severity"] not in SEVERITIES:
            raise Fail("Finding IDs must be unique; severity must be high, medium or low.")
        ids.add(finding["id"])
    material = any(f["severity"] in ("high", "medium") for f in findings)
    if value["verdict"] == "APPROVED" and material:
        raise Fail("APPROVED cannot contain unresolved high/medium findings.")
    if value["verdict"] == "REVISE" and not findings:
        raise Fail("REVISE must include at least one finding.")
    if value["verdict"] == "BLOCKED" and not value["limitations"]:
        raise Fail("BLOCKED must explain the limitation.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_hash = sub.add_parser("hash", help="Print SHA256 of a plan file.")
    p_hash.add_argument("plan", type=Path)
    p_review = sub.add_parser("review", help="Validate a review JSON file.")
    p_review.add_argument("json_path", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.cmd == "hash":
            path = args.plan.expanduser().resolve(strict=True)
            print(digest_file(path))
            return 0
        path = args.json_path.expanduser().resolve(strict=True)
        validate_review(load_json(path))
        print("OK")
        return 0
    except (Fail, OSError) as exc:
        print(f"eyal-plan-loop: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
