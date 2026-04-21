import type { CompiledPrompt } from "../prompt.js";

const DEFAULT_MODEL = "claude-sonnet-4-6";
const DEFAULT_MAX_TOKENS = 2048;

export function render(compiled: CompiledPrompt, opts: { model?: string } = {}): Record<string, unknown> {
  const fm = compiled.frontmatter;
  const hints = (fm["model_hints"] as Record<string, string> | undefined) ?? {};
  const model = opts.model ?? hints.anthropic ?? DEFAULT_MODEL;
  const payload: Record<string, unknown> = {
    model,
    system: compiled.system,
    messages: [{ role: "user", content: compiled.user }],
    max_tokens: Number(fm["max_tokens"] ?? DEFAULT_MAX_TOKENS),
  };
  if ("recommended_temperature" in fm) payload.temperature = fm["recommended_temperature"];
  return payload;
}
