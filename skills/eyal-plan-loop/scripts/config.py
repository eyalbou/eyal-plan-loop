#!/usr/bin/env python3
"""Local Eyal Plan Loop prefs. Stdlib only. Path: ~/.cursor/eyal-plan-loop.json"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

CONFIG = Path.home() / ".cursor" / "eyal-plan-loop.json"


def load() -> dict:
    if not CONFIG.is_file():
        return {}
    try:
        value = json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def save(value: dict) -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    value["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tmp = CONFIG.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, CONFIG)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("path")
    sub.add_parser("get")
    p_set = sub.add_parser("set-reviewer")
    p_set.add_argument("reviewer_id")
    p_set.add_argument("--host", default="")
    p_add = sub.add_parser("add-claude-model")
    p_add.add_argument("model_id")
    p_add.add_argument("label", nargs="?", default="")
    args = parser.parse_args(argv)
    if args.cmd == "path":
        print(CONFIG)
        return 0
    if args.cmd == "get":
        print(json.dumps(load(), indent=2))
        return 0
    data = load()
    if args.cmd == "set-reviewer":
        data["reviewer_id"] = args.reviewer_id
        if args.host:
            data["host"] = args.host
        save(data)
        print(json.dumps(load(), indent=2))
        return 0
    models = list(data.get("claude_code_models") or [])
    entry = {"id": args.model_id, "label": args.label or args.model_id}
    models = [m for m in models if isinstance(m, dict) and m.get("id") != args.model_id]
    models.insert(0, entry)
    data["claude_code_models"] = models[:20]
    save(data)
    print(json.dumps(load(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
