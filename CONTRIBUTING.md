# Contributing to USF

Thanks for being here. USF is small on purpose — contributions that keep
it small are the most welcome.

## What we're looking for

- **New skills** that pull their weight: niche, concrete, well-tested.
  Generic "AI assistant" skills don't make the cut.
- **Adapter improvements** (streaming, tool use, provider-specific
  options) that keep the `CompiledPrompt` → payload mapping honest.
- **Docs fixes** — typos, clarifications, real-world examples.
- **Validator rules** that catch real mistakes people make.

We are *not* looking for orchestration features, chain abstractions, or
provider features that would force USF to pick a lowest-common-denominator
design. Those belong in the layer above USF.

## Local setup

```bash
# Python side
python -m venv .venv && source .venv/bin/activate
pip install -e packages/usf-py[dev]
pytest packages/usf-py/tests/

# TypeScript side
cd packages/usf-ts && npm install && npm test && npm run build

# Full parity check
python scripts/render_all.py --out build/py
npx --prefix packages/usf-ts tsx scripts/render_all.ts --out build/ts
diff -r build/py build/ts       # must exit 0
```

## Before you open a PR

- [ ] `pytest packages/usf-py/tests/` is green.
- [ ] `npm --prefix packages/usf-ts test` is green.
- [ ] `skill validate skills/` returns 0.
- [ ] If you changed parser / template / prompt / adapters on **one side**,
      you changed them on **both** sides. The parity test in CI will reject
      you otherwise.
- [ ] New skills live in `skills/`, have `version: 0.1.0` to start, and
      declare all inputs used in their body.
- [ ] You added or updated tests that would have caught the bug you fixed
      or the feature you added.

## Style

- Python: 4-space indent, `from __future__ import annotations` at the top
  of new files, no runtime dependencies beyond what `pyproject.toml`
  already lists without opening an issue first.
- TypeScript: ESM-only, 2-space indent, `strict: true`, no runtime
  dependencies beyond `ajv` and `gray-matter` without an issue.
- Skills: lowercase-kebab names, descriptions under 200 chars when
  possible, `version:` bumped per semver on every behavioural change.
- Docs: short sentences, no marketing language. "Portable, testable,
  versioned" is the frame; everything ties back to it.

## Design decisions already made

Don't spend cycles re-litigating these in a PR — open an issue first:

- **Template engine is custom, not Jinja/Nunjucks.** Parity with TS is
  the reason.
- **USF is a superset of Claude Skills, not 1:1 compatible.** The export
  path is one-way by design.
- **No orchestration.** USF defines the unit.
- **Approximate tokenization (len/4).** Upgrade to tiktoken is a v0.2
  roadmap item, not a v0.1 dependency.

## Reporting bugs

Include:

1. The skill file (or a minimal reproduction).
2. The inputs.
3. The command or code path that triggered the bug.
4. Expected vs actual output.

Bugs that can be reproduced with a skill file in `skills/` or a test in
`tests/` get fixed fastest.

## License

By contributing, you agree your changes are licensed under the MIT license
in [LICENSE](LICENSE).
