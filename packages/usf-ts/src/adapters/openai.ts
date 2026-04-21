import type { CompiledPrompt } from "../prompt.js";

const DEFAULT_MODEL = "gpt-4o";

export function render(compiled: CompiledPrompt, opts: { model?: string } = {}): Record<string, unknown> {
  const fm = compiled.frontmatter;
  const hints = (fm["model_hints"] as Record<string, string> | undefined) ?? {};
  const model = opts.model ?? hints.openai ?? DEFAULT_MODEL;
  const payload: Record<string, unknown> = {
    model,
    messages: [
      { role: "system", content: compiled.system },
      { role: "user", content: compiled.user },
    ],
  };
  if ("recommended_temperature" in fm) payload.temperature = fm["recommended_temperature"];
  if ("max_tokens" in fm) payload.max_tokens = fm["max_tokens"];
  return payload;
}
