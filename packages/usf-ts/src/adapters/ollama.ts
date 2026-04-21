import type { CompiledPrompt } from "../prompt.js";

const DEFAULT_MODEL = "llama3.1:8b";

export function render(compiled: CompiledPrompt, opts: { model?: string } = {}): Record<string, unknown> {
  const fm = compiled.frontmatter;
  const hints = (fm["model_hints"] as Record<string, string> | undefined) ?? {};
  const model = opts.model ?? hints.ollama ?? DEFAULT_MODEL;
  const options: Record<string, unknown> = {};
  if ("recommended_temperature" in fm) options.temperature = fm["recommended_temperature"];
  if ("max_tokens" in fm) options.num_predict = fm["max_tokens"];
  const payload: Record<string, unknown> = {
    model,
    system: compiled.system,
    prompt: compiled.user,
    stream: false,
  };
  if (Object.keys(options).length) payload.options = options;
  return payload;
}
