# Claude Agent Skills — compatibility

USF is a **superset** of Anthropic's [Claude Agent Skills][skills] format.
Any USF skill can be exported to a Claude `SKILL.md`; not every Claude
Skill round-trips back to USF, because Claude Skills have no typed inputs,
no structured sections, and no cross-provider adapters.

> USF skills can be **exported** to the Claude Agent Skills format via
> `skill export --format claude`. The exported `SKILL.md` runs as a
> standalone skill in Claude Code.

[skills]: https://docs.claude.com/en/docs/claude-code/skills

## Format comparison

| Field / feature | Claude Skills | USF |
| --- | --- | --- |
| `name` (≤64 chars, kebab-case) | Required | Required |
| `description` (≤1024 chars) | Required | Required |
| Body | Free markdown | 5 required H1 sections + optional `# Guardrails`, `# Examples` |
| `version` | — | `version: X.Y.Z` (semver) |
| `author` | — | string |
| `tags` | — | array |
| Inputs | Implicit (model reads the body) | Declared with types, defaults, required flag |
| Template variables | — | `{{var}}`, `{{var \| default("x")}}` |
| Provider | Claude only | OpenAI / Anthropic / Gemini / Ollama via adapters |
| Wikilinks / memory | Not built-in | `[[note]]` with `truncate`/`summary`/`full` modes |
| Model hints | — | `model_hints: { openai: ..., anthropic: ..., gemini: ..., ollama: ... }` |

## Exporting

```bash
skill export code-reviewer --format claude --out ~/.claude/skills/
```

What this produces:

1. A `SKILL.md` with `name` and `description` copied verbatim.
2. The body flattened: the five USF sections concatenated with their H1
   headings preserved, so Claude Code can still read them.
3. All USF-only frontmatter keys (`version`, `inputs`, `tags`,
   `model_hints`, `wikilink_*`, `recommended_temperature`, `max_tokens`)
   **dropped** from the exported frontmatter — they are invalid in the
   Claude format.
4. Inputs become plain `{{var}}` placeholders in the body. Claude Code
   will ask the user for each input when the skill runs.

## Why not 1:1?

A Claude Skill is a description + free-form instructions. USF adds three
things Claude Skills can't express:

1. **Declared interface.** `inputs:` gives you validation, defaults, and
   a stable contract. A Claude Skill's body just says "give me the code"
   and trusts the model to ask for it.
2. **Structured shape.** The five required sections make diffs and PR
   reviews legible. Claude's body can be anything, including a mess.
3. **Provider choice.** A Claude Skill runs on Claude. A USF skill runs
   on whatever adapter you point it at, with the same output contract.

If you live entirely inside Claude Code, the structure is optional. If you
serve a skill across a fleet of providers or let downstream callers
depend on its output format, the structure is how you keep the skill
honest as it ages.

## Round-tripping

You can import a Claude Skill into USF manually: keep its frontmatter,
split its body into the five required sections, and declare its inputs.
There is no automatic `skill import --format claude` in this release —
it is on the roadmap once we have enough real-world Claude Skills to
base the heuristics on.
