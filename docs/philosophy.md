# Philosophy

> **USF turns prompts into portable, testable, versioned units.**

Everything in this repo exists to prove that one line. If a feature doesn't
help a skill be portable, testable, or versioned, it is feature creep.

## The problem

LLM prompts are the fastest-growing source of production logic in modern
codebases — and the worst tracked. They live as string literals scattered
across Python, TypeScript, and shell scripts. They have no owner, no test,
no diff, no version. Swap providers and you rewrite them. Change the model
and you can't tell what regressed.

Frameworks that try to fix this (LangChain, CrewAI, DSPy) solve different
problems: orchestration, agentic loops, optimizer-in-the-loop prompting.
None of them define a durable, portable unit for *what the skill is*.

## The unit

A USF skill is a single markdown file with YAML frontmatter:

- **`name`** and **`description`** — the only fields Claude Agent Skills
  require, so any USF skill exports cleanly to `SKILL.md`.
- **Required sections** (`# Role`, `# Task`, `# Context`, `# Constraints`,
  `# Output Format`) — a predictable shape that survives provider swaps.
- **Declared `inputs:`** — an explicit interface, so a skill is a function,
  not a template you hope works.
- **`{{var}}` templates** in the body — the minimal engine needed to keep
  Python and TypeScript implementations bit-identical.
- **`version:`** — it lives in git, diffs in PRs, ages with your codebase.

## The three promises

| Promise | Proof in this repo |
| --- | --- |
| **Portable** | 4 adapters (OpenAI, Anthropic, Gemini, Ollama) + `skill export --format claude` |
| **Testable** | `skill validate`, `skill diff`, Py↔TS parity test in CI |
| **Versioned** | `version:` in frontmatter, skills live in git, change like code |

## What USF is *not*

- **Not an orchestration framework.** No chains, no tools, no agents. USF
  defines the unit that agentic frameworks should be made of.
- **Not a model abstraction layer.** Each adapter produces the native payload
  for that provider — no lowest-common-denominator abstraction over tool use
  or streaming.
- **Not "1:1 compatible" with Claude Agent Skills.** USF is a **superset**:
  Claude Skills are runnable by Claude Code as-is; USF adds structured
  sections, typed inputs, and multi-provider adapters. You can always
  `skill export --format claude` to get back to the baseline.

## Design guarantees

1. **Deterministic prompt building.** Same skill + same inputs = same output
   bytes. This is the contract the Py↔TS parity test enforces.
2. **Provider-agnostic compiled form.** `CompiledPrompt` has three fields:
   `system`, `user`, `metadata`. Adapters only pack — they never think.
3. **No silent context explosion.** Obsidian `[[wikilinks]]` are always
   bounded (default 1000 tokens per link) with a warning when truncated.
4. **No invisible defaults.** Missing required inputs raise a clear error;
   no silently-empty strings in your prompt.
