import type { CompiledPrompt } from "../prompt.js";
import * as anthropic from "./anthropic.js";
import * as gemini from "./gemini.js";
import * as ollama from "./ollama.js";
import * as openai from "./openai.js";

export type ProviderName = "openai" | "anthropic" | "claude" | "gemini" | "google" | "ollama" | "local";

export interface Adapter {
  render(compiled: CompiledPrompt, opts?: { model?: string }): Record<string, unknown>;
}

const ADAPTERS: Record<string, Adapter> = {
  openai,
  anthropic,
  claude: anthropic,
  gemini,
  google: gemini,
  ollama,
  local: ollama,
};

export function getAdapter(provider: string): Adapter {
  const key = provider.toLowerCase();
  const adapter = ADAPTERS[key];
  if (!adapter) {
    throw new Error(`unknown provider: ${provider}. Supported: openai, anthropic, gemini, ollama`);
  }
  return adapter;
}

export function availableProviders(): string[] {
  return ["openai", "anthropic", "gemini", "ollama"];
}
