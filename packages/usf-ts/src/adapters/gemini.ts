import type { CompiledPrompt } from "../prompt.js";

const DEFAULT_MODEL = "gemini-1.5-pro";

export function render(compiled: CompiledPrompt, opts: { model?: string } = {}): Record<string, unknown> {
  const fm = compiled.frontmatter;
  const hints = (fm["model_hints"] as Record<string, string> | undefined) ?? {};
  const model = opts.model ?? hints.gemini ?? DEFAULT_MODEL;
  const genConfig: Record<string, unknown> = {};
  if ("recommended_temperature" in fm) genConfig.temperature = fm["recommended_temperature"];
  if ("max_tokens" in fm) genConfig.maxOutputTokens = fm["max_tokens"];
  const payload: Record<string, unknown> = {
    model,
    system_instruction: { parts: [{ text: compiled.system }] },
    contents: [{ role: "user", parts: [{ text: compiled.user }] }],
  };
  if (Object.keys(genConfig).length) payload.generationConfig = genConfig;
  return payload;
}
