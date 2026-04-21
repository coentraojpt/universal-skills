# Launch playbook

Pre-flight checklist and posting templates for the first public release.

## Pre-launch checklist

- [ ] `pytest packages/usf-py/tests/` green.
- [ ] `npm --prefix packages/usf-ts test` green.
- [ ] `skill validate skills/` returns 0.
- [ ] Py↔TS parity `diff -r build/py build/ts` returns 0.
- [ ] `assets/demo.gif` exists, ≤5 MB, shows `skill run` with real output.
- [ ] README renders correctly on GitHub (check preview).
- [ ] GitHub Actions green on the main branch.
- [ ] LICENSE, CODE_OF_CONDUCT, CONTRIBUTING all present.
- [ ] 10 people who will upvote in the first 30 min know the launch
      window (timezone, URL to like).
- [ ] A first comment already drafted (so you can post it ~1 min after
      submission to seed the thread).

## Where to post

Order matters. Each platform has different attention windows.

1. **Hacker News** — single best shot. Post Tuesday–Thursday, 08:00–10:00
   ET. One chance per URL. Title below.
2. **Reddit** — post shortly after HN:
   - r/LocalLLaMA (biggest audience for multi-provider positioning)
   - r/programming (general dev)
   - r/ObsidianMD (plugin angle)
   - r/ClaudeAI, r/OpenAI (niche but engaged)
3. **X / Twitter** — thread with the GIF and the tagline.
4. **LinkedIn** — next day, longer-form post with the "why".
5. **Dev.to / Hashnode** — write-up that can live on its own.

## Title candidates

### Hacker News
- Show HN: Universal LLM Skills Framework — portable, testable, versioned prompts
- Show HN: Markdown + YAML skills that run on OpenAI, Claude, Gemini, and Ollama
- Show HN: A standard for LLM "skills" that exports to Claude Agent Skills

### Reddit
- r/LocalLLaMA: "Run the same skill file on Ollama, OpenAI, Claude, and Gemini"
- r/programming: "We're tracking every other kind of code — why not our prompts?"
- r/ObsidianMD: "Run LLM skills from your Obsidian vault with `[[wikilinks]]` as memory"

## Seed comment (HN, first ~30 seconds)

> Author here. Happy to answer questions.
>
> The short pitch: prompts keep showing up as string literals scattered
> across codebases with no owner, no test, no version. USF defines a
> portable unit (markdown + YAML), ships it across four providers, and
> verifies Python and TypeScript implementations produce byte-identical
> output in CI.
>
> It's intentionally a superset of Claude Agent Skills — anything here
> exports to SKILL.md with one command. Not trying to replace
> orchestration frameworks; trying to define the unit they should be
> made of.

## What to watch for

- **Will show up in comments**: "Isn't this just LangChain templates?"
  Answer: LangChain templates are Python objects. USF is a file format
  that's portable across languages and providers, with an export path
  to Claude Agent Skills. Different layer.
- **Will show up in comments**: "Why not just use <other YAML
  prompt library>?" Answer: name three, compare the feature matrix,
  emphasize the Py↔TS parity test and the Obsidian memory integration.
- **Will show up in comments**: "Templates over LLMs are an anti-pattern,
  just use DSPy / BAML / ..." Answer: DSPy and BAML solve different
  problems (optimization, type-safe function calls). USF is the unit,
  not the optimizer or the runtime.

## After the launch

- Issue template set up so first-time contributors have a clear entry.
- "Good first issue" tag on 5–10 small tasks (new skill, new adapter
  option, docs cleanup).
- Thank every external contributor by name in the release notes.

## Not this launch

- PyPI / npm publishing. Do it after the first round of feedback lands
  to avoid having to ship a v0.1.1 in 48 hours.
- Obsidian community plugin store submission. Ship via BRAT first.
- `skill test <name>` with expectations. That's the 0.2 story.
