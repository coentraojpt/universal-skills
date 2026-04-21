import { describe, it, expect } from "vitest";
import { parse, missingRequiredSections } from "../src/parser.js";

const SAMPLE = `---
name: sample
description: A test skill.
---

# Role
You are helpful.

# Task
Do the thing.

# Context
Context text.

# Constraints
Be careful.

# Output Format
JSON.
`;

describe("parser.parse", () => {
  it("reads frontmatter", () => {
    const p = parse(SAMPLE);
    expect(p.frontmatter.name).toBe("sample");
    expect(p.frontmatter.description).toBe("A test skill.");
  });

  it("splits H1 sections", () => {
    const p = parse(SAMPLE);
    expect(Object.keys(p.sections).sort()).toEqual([
      "Constraints",
      "Context",
      "Output Format",
      "Role",
      "Task",
    ]);
    expect(p.sections.Role).toBe("You are helpful.");
  });

  it("preserves body text in section", () => {
    const p = parse(SAMPLE);
    expect(p.sections.Task).toBe("Do the thing.");
  });
});

describe("missingRequiredSections", () => {
  it("returns empty when all present", () => {
    const p = parse(SAMPLE);
    expect(missingRequiredSections(p.sections)).toEqual([]);
  });

  it("lists missing", () => {
    expect(missingRequiredSections({ Role: "x" })).toEqual([
      "Task",
      "Context",
      "Constraints",
      "Output Format",
    ]);
  });
});
