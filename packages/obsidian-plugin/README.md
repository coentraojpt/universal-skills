# Universal Skills — Obsidian plugin

Run and validate [Universal LLM Skills Framework](https://github.com/coentraojpt/universal-skills)
(USF) skills directly from your Obsidian vault.

## What it does

- **USF: Run skill** — opens a picker of every USF skill in your vault, prompts for declared
  inputs, calls the provider (OpenAI / Anthropic / Gemini / Ollama), and pastes the
  output into the current note.
- **USF: Validate current note** — checks the active markdown file against the USF spec
  (required frontmatter + required sections) and reports problems in a notice.
- Resolves `[[wikilinks]]` inside skill bodies so you can pull vault notes into prompts
  as reusable memory. Three modes: `truncate` (default), `summary`, `full`.
- Status bar shows the count of USF skills detected in the current vault.

## Install (dev mode)

1. Build: `npm install && npm run build` in this directory.
2. Copy `manifest.json`, `main.js` into `<your-vault>/.obsidian/plugins/universal-skills/`.
3. In Obsidian → Settings → Community plugins → enable **Universal Skills (USF)**.
4. Open settings and paste your API keys. Keys are stored via Obsidian's plugin data
   storage — **never in your notes in plaintext**.

## What counts as a USF skill?

A markdown file whose frontmatter has `name` and `description` and whose body contains
the required `# Role`, `# Task`, `# Context`, `# Constraints`, `# Output Format`
sections. Notes with `usf: false` are always ignored (safe for memory/reference notes
that use `[[wikilinks]]` to skills but are not themselves runnable).

## Roadmap

- Submit to the community plugin store.
- Live preview of the compiled prompt before sending.
- Streaming output.
