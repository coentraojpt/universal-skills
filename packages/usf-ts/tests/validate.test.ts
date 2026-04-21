import { describe, it, expect } from "vitest";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load } from "../src/loader.js";
import { validateSkill, validatePath } from "../src/validate.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "../../..");
const SKILLS_DIR = path.join(REPO, "skills");

describe("validateSkill", () => {
  it("passes on real code-reviewer skill", async () => {
    const skill = await load(path.join(SKILLS_DIR, "code-reviewer.md"));
    const errs = await validateSkill(skill);
    expect(errs).toEqual([]);
  });
});

describe("validatePath", () => {
  it("returns empty object for valid skills dir", async () => {
    const results = await validatePath(SKILLS_DIR);
    expect(Object.keys(results)).toEqual([]);
  });
});
