import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";

import { load, type Skill } from "./loader.js";
import { REQUIRED_SECTIONS } from "./parser.js";
import { findVariables } from "./template.js";

let cachedSchema: Record<string, unknown> | null = null;
let cachedValidator: ReturnType<Ajv2020["compile"]> | null = null;

async function findSchemaPath(): Promise<string> {
  const candidates: string[] = [];
  try {
    const here = path.dirname(fileURLToPath(import.meta.url));
    let dir = here;
    for (let i = 0; i < 8; i++) {
      candidates.push(path.join(dir, "schema", "skill.schema.json"));
      const parent = path.dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  } catch {
    // ignore — fall back to CWD walk
  }
  let cwd = process.cwd();
  for (let i = 0; i < 8; i++) {
    candidates.push(path.join(cwd, "schema", "skill.schema.json"));
    const parent = path.dirname(cwd);
    if (parent === cwd) break;
    cwd = parent;
  }
  for (const candidate of candidates) {
    try {
      await fs.access(candidate);
      return candidate;
    } catch {
      // keep looking
    }
  }
  throw new Error(
    `could not locate schema/skill.schema.json (searched from module dir and cwd)`,
  );
}

async function getValidator() {
  if (cachedValidator && cachedSchema) return cachedValidator;
  const schemaPath = await findSchemaPath();
  const text = await fs.readFile(schemaPath, "utf-8");
  cachedSchema = JSON.parse(text);
  const ajv = new Ajv2020({ allErrors: true, strict: false });
  cachedValidator = ajv.compile(cachedSchema as object);
  return cachedValidator;
}

export async function validateSkill(skill: Skill): Promise<string[]> {
  const errors: string[] = [];
  const validator = await getValidator();
  if (!validator(skill.frontmatter)) {
    for (const err of validator.errors ?? []) {
      errors.push(`frontmatter: ${err.message} (at ${err.instancePath || "/"})`);
    }
  }
  for (const s of REQUIRED_SECTIONS) {
    if (!(s in skill.sections)) {
      errors.push(`missing required section: # ${s}`);
    }
  }
  const declared = new Set(skill.inputsSpec.map((i) => i.name));
  const used = new Set<string>();
  for (const body of Object.values(skill.sections)) {
    for (const v of findVariables(body)) used.add(v);
  }
  const undeclared = [...used].filter((v) => !declared.has(v));
  const unused = [...declared].filter((v) => !used.has(v));
  if (undeclared.length) {
    errors.push(`template uses undeclared input(s): ${JSON.stringify(undeclared.sort())}`);
  }
  if (unused.length) {
    errors.push(`inputs declared but never referenced: ${JSON.stringify(unused.sort())}`);
  }
  return errors;
}

export async function validatePath(target: string): Promise<Record<string, string[]>> {
  const results: Record<string, string[]> = {};
  const stat = await fs.stat(target);
  const files = stat.isFile()
    ? [target]
    : (await fs.readdir(target))
        .filter((n) => n.endsWith(".md"))
        .sort()
        .map((n) => path.join(target, n));
  for (const file of files) {
    let skill: Skill;
    try {
      skill = await load(file);
    } catch (exc) {
      const msg = (exc as Error).message;
      if (msg.includes("utf") || msg.includes("encode")) continue;
      results[file] = [`parse error: ${msg}`];
      continue;
    }
    if (skill.frontmatter["usf"] === false) continue;
    if (!skill.frontmatter["name"] || !skill.frontmatter["description"]) continue;
    const errs = await validateSkill(skill);
    if (errs.length) results[file] = errs;
  }
  return results;
}
