"""Run the refactorer skill against Anthropic Claude.

Prereq:
    pip install -e packages/usf-py[anthropic]
    export ANTHROPIC_API_KEY=sk-ant-...

Run:
    python examples/python/claude_example.py
"""
from __future__ import annotations

from pathlib import Path

from usf import load

SKILL = Path(__file__).resolve().parents[2] / "skills" / "refactorer.md"
MESSY = """def p(l):
  r = []
  for i in range(len(l)):
    if l[i] % 2 == 0:
      r.append(l[i] * 2)
  return r
"""


def main() -> None:
    skill = load(SKILL)
    output = skill.run(
        "anthropic",
        {"code": MESSY, "language": "python", "priorities": "readability,simplicity"},
    )
    print(output)


if __name__ == "__main__":
    main()
