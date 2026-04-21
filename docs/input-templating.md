# Input templating

USF skills declare their inputs up front and interpolate them with a
tiny `{{var}}` engine. The engine is ~40 lines in both Python and
TypeScript — that is on purpose, because their outputs must match
byte-for-byte. Every prompt you build goes through the same engine.

## Declaring inputs

```yaml
inputs:
  - name: code
    type: string
    required: true
    description: Code to review.
  - name: language
    type: string
    required: false
    default: auto
```

- **`name`** — valid identifier (`[a-zA-Z_][a-zA-Z0-9_]*`), must be used
  in the body.
- **`type`** — `string`, `number`, or `boolean`. Current engine coerces
  with `String(value)`, so this is documentation until a future validator
  tightens it.
- **`required`** — if `true` and no value is provided and no default
  exists, the skill refuses to build with a clear error.
- **`default`** — used when the input is missing, `null`, or an empty
  string. Also applied before the `{{var | default("...")}}` template
  default, so the template default is only a safety net.
- **`description`** — shown in `skill show` output and the Obsidian
  plugin's input modal.

## The template engine

Three constructs, nothing else:

```text
{{name}}                          -- substitute the value of `name`; error if missing
{{name | default("fallback")}}    -- substitute, or "fallback" if empty/missing
{{{{literal}}}}                   -- renders as {{literal}}
```

Single and double quotes are both accepted for the default value:
`{{v | default('x')}}` works too. Whitespace around `|` is optional.

### Why this limited

The template engine has to be bit-identical between Python and TypeScript
for the parity test to work. Jinja2 and Nunjucks have drifted on edge
cases (whitespace control, filter chaining, undefined handling), and
USF does not want to adopt either's opinion. Forty lines you can hold
in your head beat a thousand lines you have to diff.

## Validator cross-checks

`skill validate` enforces:

1. Every `{{var}}` in the body (including inside defaults) is declared
   in `inputs:`.
2. Every input declared in `inputs:` is referenced at least once in
   the body.

If either rule fails, the skill is rejected with a specific message:

```
template uses undeclared input(s): ["language"]
inputs declared but never referenced: ["snippet"]
```

This catches dead inputs and typos the same way TypeScript catches unused
variables — before you ship.

## Running with inputs

```bash
# Inline
skill run code-reviewer --input code="print('hi')" --input language=python

# From a file (prefix with @)
skill run code-reviewer --input code=@app.py --input language=python

# From a JSON map
skill run code-reviewer --json inputs.json
```

All three routes funnel into the same `build_prompt(inputs)` call, so the
result is identical.

## Missing-input error

```
Error: Missing required input(s) for skill 'code-reviewer': code
```

Required inputs with no default never silently become empty strings.
If you want the skill to run without `code`, make it `required: false`
and set a default — it is one line of YAML and it keeps the contract
visible.
