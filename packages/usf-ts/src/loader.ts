import { promises as fs } from "node:fs";
import path from "node:path";

import { getAdapter, type ProviderName } from "./adapters/index.js";
import { parse } from "./parser.js";
import { buildPrompt, type CompiledPrompt } from "./prompt.js";
import type { Vault } from "./obsidian.js";

export interface InputSpec {
  name: string;
  type?: "string" | "number" | "boolean";
  required?: boolean;
  default?: unknown;
  description?: string;
}

export class Skill {
  constructor(
    public readonly frontmatter: Record<string, unknown>,
    public readonly sections: Record<string, string>,
    public readonly inputsSpec: InputSpec[],
    public readonly sourcePath?: string,
  ) {}

  get name(): string {
    return String(this.frontmatter["name"] ?? "");
  }

  get description(): string {
    return String(this.frontmatter["description"] ?? "");
  }

  async buildPrompt(
    inputs: Record<string, unknown> = {},
    vault?: Vault,
  ): Promise<CompiledPrompt> {
    return buildPrompt(this, inputs, vault);
  }

  async render(
    provider: ProviderName,
    inputs: Record<string, unknown> = {},
    vault?: Vault,
  ): Promise<Record<string, unknown>> {
    const compiled = await this.buildPrompt(inputs, vault);
    return getAdapter(provider).render(compiled);
  }
}

export async function load(filePath: string): Promise<Skill> {
  const text = await fs.readFile(filePath, "utf-8");
  const parsed = parse(text);
  const inputsSpec = parseInputs(parsed.frontmatter["inputs"]);
  return new Skill(parsed.frontmatter, parsed.sections, inputsSpec, filePath);
}

export async function loadDir(dirPath: string): Promise<Skill[]> {
  const abs = path.resolve(dirPath);
  const entries = await fs.readdir(abs, { withFileTypes: true });
  const skills: Skill[] = [];
  for (const e of entries) {
    if (!e.isFile() || !e.name.endsWith(".md")) continue;
    const full = path.join(abs, e.name);
    try {
      const skill = await load(full);
      if (skill.frontmatter["usf"] === false) continue;
      if (!skill.frontmatter["name"] || !skill.frontmatter["description"]) continue;
      skills.push(skill);
    } catch {
      continue;
    }
  }
  skills.sort((a, b) => a.name.localeCompare(b.name));
  return skills;
}

function parseInputs(raw: unknown): InputSpec[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((r) => ({
    name: String((r as any).name),
    type: (r as any).type ?? "string",
    required: Boolean((r as any).required),
    default: (r as any).default,
    description: (r as any).description,
  }));
}
