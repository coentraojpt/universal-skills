#!/usr/bin/env python3
"""Render every skill × every provider to deterministic JSON files.

Used by the Py↔TS parity test in CI.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from usf import adapters, load

PROVIDERS = ["openai", "anthropic", "gemini", "ollama"]


def _normalize(value):
    """Match JS JSON behavior: whole-number floats collapse to ints."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Output directory for payload JSON files.")
    parser.add_argument("--skills", default="skills", help="Skills directory.")
    parser.add_argument(
        "--fixtures",
        default="tests/fixtures/canonical_inputs.json",
        help="JSON file with canonical inputs per skill name.",
    )
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fixtures = json.loads(Path(args.fixtures).read_text(encoding="utf-8"))
    skills_dir = Path(args.skills)

    for md in sorted(skills_dir.glob("*.md")):
        try:
            skill = load(md)
        except (UnicodeDecodeError, ValueError):
            continue
        name = skill.name
        if not name or name not in fixtures:
            continue
        inputs = fixtures[name]
        compiled = skill.build_prompt(inputs)
        for provider in PROVIDERS:
            payload = _normalize(adapters.get_adapter(provider).render(compiled))
            target = out / f"{name}__{provider}.json"
            # Force LF so golden diff is stable across platforms.
            body = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            target.write_bytes(body.encode("utf-8"))
    print(f"rendered to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
