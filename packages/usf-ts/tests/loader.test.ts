import { describe, it, expect } from "vitest";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load, loadDir } from "../src/loader.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "../../..");
const SKILLS_DIR = path.join(REPO, "skills");

describe("loader.load", () => {
  it("loads code-reviewer skill", async () => {
    const skill = await load(path.join(SKILLS_DIR, "code-reviewer.md"));
    expect(skill.name).toBe("code-reviewer");
    expect(skill.inputsSpec.some((i) => i.name === "code")).toBe(true);
  });

  it("builds prompt with inputs", async () => {
    const skill = await load(path.join(SKILLS_DIR, "code-reviewer.md"));
    const compiled = await skill.buildPrompt({ code: "print('hi')", language: "python" });
    expect(compiled.system).toContain("Role");
    expect(compiled.user).toContain("print('hi')");
  });

  it("throws when required input missing", async () => {
    const skill = await load(path.join(SKILLS_DIR, "code-reviewer.md"));
    await expect(skill.buildPrompt({})).rejects.toThrow(/Missing required input/);
  });
});

describe("loader.loadDir", () => {
  it("loads all 9 skills", async () => {
    const skills = await loadDir(SKILLS_DIR);
    expect(skills.length).toBe(9);
    expect(skills.map((s) => s.name).sort()).toEqual([
      "api-designer",
      "code-reviewer",
      "commit-message-writer",
      "debug-assistant",
      "refactorer",
      "security-auditor",
      "sql-optimizer",
      "startup-validator",
      "technical-writer",
    ]);
  });
});
