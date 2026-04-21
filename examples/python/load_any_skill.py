"""Load a skill, build the prompt, and inspect the payload for every provider.

Runs entirely offline — no API keys required.

Run:
    python examples/python/load_any_skill.py code-reviewer
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from usf import adapters, load

REPO = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO / "skills"
FIXTURES = json.loads(
    (REPO / "tests" / "fixtures" / "canonical_inputs.json").read_text(encoding="utf-8")
)


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "code-reviewer"
    skill = load(SKILLS_DIR / f"{name}.md")
    inputs = FIXTURES.get(name, {})
    compiled = skill.build_prompt(inputs)
    print(f"=== Skill: {skill.name} ===")
    print(f"[system]\n{compiled.system}\n")
    print(f"[user]\n{compiled.user}\n")
    for provider in adapters.available_providers():
        payload = adapters.get_adapter(provider).render(compiled)
        print(f"--- {provider} payload ---")
        print(json.dumps(payload, indent=2, ensure_ascii=False)[:500])
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
