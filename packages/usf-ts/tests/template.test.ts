import { describe, it, expect } from "vitest";
import { render, findVariables, TemplateError } from "../src/template.js";

describe("template.render", () => {
  it("renders plain variable", () => {
    expect(render("Hello {{name}}", { name: "Ada" })).toBe("Hello Ada");
  });

  it("uses default when value missing", () => {
    expect(render('X={{v | default("fallback")}}', {})).toBe("X=fallback");
  });

  it("skips default when value present", () => {
    expect(render('X={{v | default("fallback")}}', { v: "real" })).toBe("X=real");
  });

  it("uses default on empty string", () => {
    expect(render('X={{v | default("fb")}}', { v: "" })).toBe("X=fb");
  });

  it("throws on missing required var", () => {
    expect(() => render("{{name}}", {})).toThrow(TemplateError);
  });

  it("escapes literal double braces", () => {
    expect(render("code {{{{literal}}}}", {})).toBe("code {{literal}}");
  });

  it("replaces multiple occurrences", () => {
    expect(render("{{x}} / {{x}}", { x: "Y" })).toBe("Y / Y");
  });

  it("rejects invalid identifier", () => {
    expect(() => render("{{1bad}}", { "1bad": "x" })).toThrow(TemplateError);
  });
});

describe("findVariables", () => {
  it("returns all referenced names", () => {
    const vars = findVariables('{{a}} and {{b | default("x")}}');
    expect([...vars].sort()).toEqual(["a", "b"]);
  });

  it("skips escaped sequences", () => {
    const vars = findVariables("{{{{literal}}}} {{real}}");
    expect([...vars]).toEqual(["real"]);
  });
});
