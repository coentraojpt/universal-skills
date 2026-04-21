# Compatibility tips

Four providers, one skill file. Here is how to write skills that behave
similarly across all of them.

## Token budgets are not interchangeable

| Provider | Counts | Notes |
| --- | --- | --- |
| OpenAI | Tokens (cl100k / o200k depending on model) | `max_tokens` limits the **completion** only. |
| Anthropic | Tokens | `max_tokens` is **required**. USF defaults to 2048 if you don't set it. |
| Gemini | Characters → tokens (~4 chars = 1 token) | Uses `maxOutputTokens`. |
| Ollama | Tokens (model-dependent) | Uses `num_predict`. Context windows vary wildly by model. |

If you set `max_tokens: 500` in the frontmatter, every adapter will
respect it — but the *cost* of getting to 500 tokens depends on the
provider and model. Budget at write time, not at read time.

## Temperature semantics drift

- OpenAI and Anthropic: 0.0 is deterministic-ish, 1.0 is creative.
- Gemini: same scale, but the "safe default" is lower — set
  `recommended_temperature` explicitly if you want Gemini output to look
  like the others.
- Ollama: passes through to the model. Some open models interpret 0.0 as
  "greedy decode" and repeat themselves — usually `0.1` is safer than `0.0`.

## System prompts

All four adapters put your `# Role` / `# Context` / `# Constraints` /
`# Guardrails` in the provider's system slot:

- **OpenAI**: `messages[0]` with `role: system`.
- **Anthropic**: top-level `system` field.
- **Gemini**: `system_instruction.parts[0].text`.
- **Ollama**: top-level `system` field (requires a recent Ollama build
  and a model that was trained with system prompts — Llama 3.1 and later
  handle it; older models may need you to concatenate system+user yourself).

## Model hints

```yaml
model_hints:
  openai: gpt-4o
  anthropic: claude-sonnet-4-6
  gemini: gemini-1.5-pro
  ollama: llama3.1:8b
```

These are the defaults the adapters use when `--model` isn't passed. Pin
them if your skill depends on a specific model's behaviour (e.g. long
context, tool use). Override on the command line when testing.

## Format sensitivity

- **OpenAI** follows structured Output Format sections well, but prefers
  native JSON when you need JSON. Consider using OpenAI's `response_format`
  in your own code if strict JSON matters.
- **Anthropic** tends to add small conversational preambles ("Here's the
  review:"). If that matters, add a constraint: "Return **only** the
  output format — no preamble, no trailing commentary."
- **Gemini** occasionally wraps code blocks in extra fences. Specify the
  fence language in your Output Format template.
- **Ollama** local models vary widely. Always test your skill against the
  specific model you'll deploy on — USF makes it cheap, but it doesn't
  remove the need to verify.

## Streaming

This release ships non-streaming adapters only. Streaming (SSE / chunked
responses) is on the roadmap; for now, `skill run --stream` falls back to
the non-streaming API and emits the full response at the end.
