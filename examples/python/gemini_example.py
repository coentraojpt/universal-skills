"""Run the api-designer skill against Google Gemini.

Prereq:
    pip install -e packages/usf-py[gemini]
    export GEMINI_API_KEY=...

Run:
    python examples/python/gemini_example.py
"""
from __future__ import annotations

from pathlib import Path

from usf import load

SKILL = Path(__file__).resolve().parents[2] / "skills" / "api-designer.md"


def main() -> None:
    skill = load(SKILL)
    output = skill.run(
        "gemini",
        {
            "feature": "A notification service that fans out events to email, SMS, and push.",
            "style": "REST",
        },
    )
    print(output)


if __name__ == "__main__":
    main()
