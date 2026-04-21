# Anti-patterns

Patterns to spot and avoid when writing USF skills.

## 1. The mega-skill

A single skill that reviews code, generates docs, writes tests, and ships
it to prod. Models handle one clear objective far better than four tangled
ones. Split into composable skills and orchestrate them — USF is the unit,
not the pipeline.

## 2. "Helpful assistant" roles

```yaml
# Role
You are a helpful AI assistant.
```
This does nothing. Specificity is free. "You are a senior site reliability
engineer who has debugged production outages for a decade" pulls different
patterns out of the model than "helpful assistant."

## 3. Frontmatter lies

```yaml
description: Returns a JSON object with severity, category, and fix.
```
…and the Output Format section says "respond in markdown with bullets."
Pick one. Validators can't catch lies between frontmatter and body, but
reviewers and models both notice.

## 4. Secret inputs

```markdown
# Task
Review this code against our house style.
```
No `[[wikilink]]`, no input, no context. The skill assumes the model
knows your house style — it doesn't. Either inject the style via a
wikilink to a memory note, pass it as an input, or rename the skill to
something that doesn't promise that context.

## 5. `temperature: 0` as a safety blanket

Temperature zero is right for debugging, code review, SQL — places where
you want one determined answer. It is wrong for brainstorming, writing,
naming, design. Zero isn't "safe," it's "narrow." Pick with intent.

## 6. Dumping raw wikilinks into the prompt

```markdown
# Context
See [[company-playbook]] for everything.
```
If `company-playbook.md` is 8000 tokens, every request now pays for 8000
tokens of context. USF's default `truncate` mode with a 1000-token limit
saves you — but the real fix is to write a focused summary in frontmatter
(`summary: "..."`) and use `wikilink_mode: summary`.

## 7. Outputs without schemas

```markdown
# Output Format
Provide your feedback.
```
"Provide your feedback" → you will get different structure from every
provider, every request. Show the literal format. Headings, bullets, JSON
with named fields. The boringer, the better.

## 8. Required inputs that should be defaults

```yaml
inputs:
  - name: language
    required: true
```
Can you infer the language from the code itself? Most of the time yes.
Make it `required: false, default: auto` and let the Task section say
"if language is `auto`, infer it from the code fence."

## 9. Version `1.0.0` forever

`version:` is there so you can iterate. Bump it when you change the prompt.
Semver applies: behaviour-changing edits are a minor/major bump,
typo fixes are a patch. Consumers can pin if they depend on specific
wording.

## 10. Writing prose where schemas belong

```markdown
# Output Format
Please respond with the severity, a short summary, and a list of fixes,
all as a JSON object.
```
Show the JSON shape with placeholders. The model will follow a literal
template far more reliably than it will follow a description of one.
