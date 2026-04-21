#!/usr/bin/env tsx
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load, getAdapter } from "../packages/usf-ts/src/index.js";

const PROVIDERS = ["openai", "anthropic", "gemini", "ollama"] as const;

function stableStringify(value: unknown): string {
  const seen = new WeakSet<object>();
  const normalize = (v: unknown): unknown => {
    if (v === null || typeof v !== "object") return v;
    if (seen.has(v as object)) throw new Error("cycle in payload");
    seen.add(v as object);
    if (Array.isArray(v)) return v.map(normalize);
    const out: Record<string, unknown> = {};
    for (const k of Object.keys(v as Record<string, unknown>).sort()) {
      out[k] = normalize((v as Record<string, unknown>)[k]);
    }
    return out;
  };
  return JSON.stringify(normalize(value), null, 2) + "\n";
}

async function main() {
  const args = process.argv.slice(2);
  let out = "build/ts";
  let skillsDir = "skills";
  let fixturesPath = "tests/fixtures/canonical_inputs.json";
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--out") out = args[++i];
    else if (args[i] === "--skills") skillsDir = args[++i];
    else if (args[i] === "--fixtures") fixturesPath = args[++i];
  }
  const here = path.dirname(fileURLToPath(import.meta.url));
  const repo = path.resolve(here, "..");
  const outDir = path.resolve(repo, out);
  await fs.mkdir(outDir, { recursive: true });

  const fixtures = JSON.parse(await fs.readFile(path.resolve(repo, fixturesPath), "utf-8")) as Record<
    string,
    Record<string, unknown>
  >;
  const skillsPath = path.resolve(repo, skillsDir);
  const entries = (await fs.readdir(skillsPath)).filter((n) => n.endsWith(".md")).sort();

  for (const entry of entries) {
    const full = path.join(skillsPath, entry);
    let skill;
    try {
      skill = await load(full);
    } catch {
      continue;
    }
    const name = skill.name;
    if (!name || !(name in fixtures)) continue;
    const compiled = await skill.buildPrompt(fixtures[name]);
    for (const provider of PROVIDERS) {
      const payload = getAdapter(provider).render(compiled);
      const target = path.join(outDir, `${name}__${provider}.json`);
      await fs.writeFile(target, stableStringify(payload), "utf-8");
    }
  }
  console.log(`rendered to ${outDir}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
