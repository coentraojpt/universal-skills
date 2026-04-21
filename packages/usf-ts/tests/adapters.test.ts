import { describe, it, expect } from "vitest";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load } from "../src/loader.js";
import { getAdapter, availableProviders } from "../src/adapters/index.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "../../..");
const SKILLS_DIR = path.join(REPO, "skills");

async function compileSample() {
  const skill = await load(path.join(SKILLS_DIR, "code-reviewer.md"));
  return skill.buildPrompt({ code: "print('hi')", language: "python" });
}

describe("adapters", () => {
  it("lists 4 providers", () => {
    expect(availableProviders()).toEqual(["openai", "anthropic", "gemini", "ollama"]);
  });

  it("openai builds chat payload", async () => {
    const compiled = await compileSample();
    const payload = getAdapter("openai").render(compiled) as any;
    expect(payload.messages[0].role).toBe("system");
    expect(payload.messages[1].role).toBe("user");
    expect(payload.model).toContain("gpt");
  });

  it("anthropic builds system+messages payload", async () => {
    const compiled = await compileSample();
    const payload = getAdapter("anthropic").render(compiled) as any;
    expect(payload.system).toBeTruthy();
    expect(payload.messages[0].role).toBe("user");
    expect(payload.max_tokens).toBeTypeOf("number");
  });

  it("gemini builds system_instruction + contents", async () => {
    const compiled = await compileSample();
    const payload = getAdapter("gemini").render(compiled) as any;
    expect(payload.system_instruction.parts[0].text).toBeTruthy();
    expect(payload.contents[0].role).toBe("user");
  });

  it("ollama builds system + prompt", async () => {
    const compiled = await compileSample();
    const payload = getAdapter("ollama").render(compiled) as any;
    expect(payload.system).toBeTruthy();
    expect(payload.prompt).toContain("print('hi')");
    expect(payload.stream).toBe(false);
  });

  it("claude alias maps to anthropic", async () => {
    const compiled = await compileSample();
    const a = getAdapter("claude").render(compiled);
    const b = getAdapter("anthropic").render(compiled);
    expect(a).toEqual(b);
  });

  it("rejects unknown provider", () => {
    expect(() => getAdapter("bogus")).toThrow(/unknown provider/);
  });
});
