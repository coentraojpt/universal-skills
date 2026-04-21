# Obsidian integration

USF treats a skills directory as a valid Obsidian vault. This lets you:

- Author skills inside Obsidian, with the same tooling you already use
  for notes.
- Reference vault notes as **memory** from inside a skill via
  `[[wikilink]]`.
- Run skills without leaving the editor (via the companion plugin).
- Keep API keys out of your notes (they live in Obsidian's plugin data
  storage, never in plaintext markdown).

## Vault layout

```
skills/                       <- point Obsidian at this folder
├── code-reviewer.md          <- runnable skill (has name + description + sections)
├── api-designer.md           <- runnable
├── ...
└── _memory/                  <- referenceable notes, not listed as skills
    ├── coding-style.md       <- frontmatter: usf: false
    └── company-glossary.md   <- frontmatter: usf: false
```

The underscore prefix is convention, not magic. USF decides whether a
note is "runnable" based purely on frontmatter:

- Has **both** `name` and `description` → treated as a runnable skill.
- Has `usf: false` → always skipped for skill listing (memory only).
- Anything else → silently ignored.

## Memory via wikilinks

Inside any skill section, you can reference other vault notes:

```markdown
# Context
Apply the standards from [[coding-style]] and glossary in [[company-glossary]].
```

When the skill is loaded through `load_vault()` (Python) or `loadVault()`
(TypeScript), the wikilinks are resolved into inline text before the
prompt is built. Three modes control how:

| Mode | Behaviour |
| --- | --- |
| **`truncate`** (default) | Include each note's body up to `wikilink_token_limit` (default 1000 tokens ≈ 4000 chars). Truncated notes get `…[truncated]` and a stderr warning. |
| **`summary`** | If the linked note's frontmatter has `summary: "..."`, inject only that. Otherwise fall back to truncate. |
| **`full`** | Include the entire note. Opt-in — you probably only want this for tests or for very small memory notes. |

Configure per-skill in frontmatter:

```yaml
wikilink_mode: summary
wikilink_token_limit: 500
```

## Why the token limit matters

A single `[[company-playbook]]` reference into an 8000-token note silently
tripling every request is the most common way self-hosted memory systems
blow up. USF defaults to `truncate` with a conservative limit so you
get a loud warning before a budget surprise:

```
[warn] wikilinks truncated in section 'Context': 1 link(s) -> 1000 tokens each
```

If you see that in CI or at the CLI, either raise the limit intentionally
or add a `summary:` to the linked note.

## The Obsidian plugin

The companion plugin (`packages/obsidian-plugin`) adds two commands:

- **USF: Run skill** — picks a skill, prompts for inputs, runs it against
  the configured provider, pastes the output into the current note.
- **USF: Validate current note** — checks the active markdown file against
  the USF schema and reports errors in a notice.

API keys are stored via Obsidian's plugin data storage (`saveData` /
`loadData`). They never enter a markdown file. When you sync your vault
via Obsidian Sync or git, keys stay on-device.

See `packages/obsidian-plugin/README.md` for install and dev instructions.
