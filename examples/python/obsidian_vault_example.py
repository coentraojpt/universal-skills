"""Use an Obsidian vault as the skills registry, with [[wikilinks]] as memory.

The `skills/` folder of this repo doubles as a valid Obsidian vault: notes in
`skills/_memory/` use `usf: false` in their frontmatter so they are discoverable
via `[[coding-style]]` but never listed as runnable skills themselves.

Run:
    python examples/python/obsidian_vault_example.py
"""
from __future__ import annotations

from pathlib import Path

from usf import load_vault

VAULT = Path(__file__).resolve().parents[2] / "skills"


def main() -> None:
    vault = load_vault(VAULT)
    print(f"vault: {VAULT}")
    print(f"runnable skills: {len(vault.skills)}")
    for s in vault.skills:
        print(f"  - {s.name}: {s.description}")
    print(f"referenceable memory notes: {len(vault.memory)}")
    for key in sorted(vault.memory):
        print(f"  - [[{key}]]")

    skill = next(s for s in vault.skills if s.name == "code-reviewer")
    compiled = skill.build_prompt(
        {"code": "print('hi')", "language": "python"}, vault=vault,
    )
    print("\n[wikilink stats]", compiled.metadata.get("wikilink_stats"))


if __name__ == "__main__":
    main()
