# Writing good skills

A skill is a small file. It lives in git. It is read by humans in a PR and by
four different LLMs in production. Write it for both audiences.

## Checklist

- [ ] **Frontmatter has `name` (kebab-case, ≤64 chars) and `description` (≤1024 chars).**
  Both are required and both are what Claude Agent Skills will see if you
  export. Make the description do real work — it is how a router or a user
  decides whether to run this skill at all.
- [ ] **All five required sections are present.** `# Role` / `# Task` /
  `# Context` / `# Constraints` / `# Output Format`. Missing any of these
  makes the skill invalid.
- [ ] **Every `{{variable}}` in the body is declared in `inputs:`.** The
  validator enforces this both ways — undeclared variables error out, and
  declared-but-unused inputs also error out.
- [ ] **Required inputs are actually required.** If the skill can run with
  a sensible default, set `required: false` and `default: ...`. If it can't,
  set `required: true` so the user gets a clear error instead of a skill
  that silently hallucinates.
- [ ] **Temperature matches the task.** Low (0.0–0.2) for debugging, code
  review, SQL optimization, security. Medium (0.2–0.5) for writing, design.
  Never ship a skill with default temperature if you haven't thought about it.
- [ ] **`max_tokens` is realistic.** Too low truncates. Too high wastes money.
  Set it to roughly 1.5× the size of your Output Format example.

## The five sections

### Role
One sentence that puts the model in the right frame. Concrete, specific,
named. "You are a senior SRE and master debugger" beats "You are a
helpful assistant." Roles are free — spend them.

### Task
The smallest imperative that describes the input → output transformation.
Inline `{{variable}}` references the user will fill in. Keep this section
boring; the *how* belongs in Constraints.

### Context
What the model needs to know that isn't in the task itself. Relevant
standards, assumed environment, pointer notes via `[[wikilinks]]`.

### Constraints
Hard rules. Use `DO` / `DO NOT` bullets. The goal is reproducibility — a
reader in six months should see what boundaries the skill runs in.

### Output Format
The single most important section. Show the exact shape. Use a literal
markdown template, a JSON schema snippet, or numbered headings. The more
explicit the format, the less variance between providers.

## Common patterns

### Defaults that aren't lies
```yaml
inputs:
  - name: language
    type: string
    required: false
    default: auto
```
Then in the body: `` ```{{language}} `` — when the user doesn't know the
language, the fence is still valid.

### Memory via wikilinks
```markdown
# Context
Apply the standards from [[coding-style]].
```
This pulls in `_memory/coding-style.md` when the skill is loaded through
an Obsidian vault. Notes tagged `usf: false` are referenceable but never
listed as runnable skills — use this for glossaries, style guides, policies.

### Conditional sections via defaults
```markdown
# Task
Debug this error:
```
{{error}}
```

Relevant code (may be empty):
```{{language}}
{{code}}
```
```
An empty `code` default keeps the markdown valid even without that input.

## Anti-patterns (see [anti-patterns.md](anti-patterns.md))

- 500-line mega-skills that do six things.
- Frontmatter promises the body doesn't keep (e.g. "JSON output" but the
  Output Format is prose).
- Inputs that are actually parameters pretending to be queries.
- `temperature: 0` on a creative writing skill because "zero = safe".
