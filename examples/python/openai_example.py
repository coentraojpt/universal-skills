"""Run the code-reviewer skill against OpenAI.

Prereq:
    pip install -e packages/usf-py[openai]
    export OPENAI_API_KEY=sk-...

Run:
    python examples/python/openai_example.py
"""
from __future__ import annotations

from pathlib import Path

from usf import load

SKILL = Path(__file__).resolve().parents[2] / "skills" / "code-reviewer.md"


def main() -> None:
    skill = load(SKILL)
    output = skill.run(
        "openai",
        {
            "code": "def divide(a, b):\n    return a / b",
            "language": "python",
        },
    )
    print(output)


if __name__ == "__main__":
    main()
