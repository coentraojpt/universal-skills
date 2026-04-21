const ESC_OPEN = "\x00USF_ESC_OPEN\x00";
const ESC_CLOSE = "\x00USF_ESC_CLOSE\x00";

const TAG_RE = /\{\{\s*([\s\S]*?)\s*\}\}/g;
const DEFAULT_RE = /^([a-zA-Z_][a-zA-Z0-9_]*)\s*\|\s*default\(\s*(?:"(.*?)"|'(.*?)')\s*\)$/;
const NAME_RE = /^[a-zA-Z_][a-zA-Z0-9_]*$/;

export class TemplateError extends Error {}

export function render(template: string, inputs: Record<string, unknown>): string {
  const pre = template.replaceAll("{{{{", ESC_OPEN).replaceAll("}}}}", ESC_CLOSE);
  const replaced = pre.replace(TAG_RE, (_match, group: string) => {
    const expr = group.trim();
    const dm = expr.match(DEFAULT_RE);
    if (dm) {
      const name = dm[1];
      const fallback = dm[2] ?? dm[3] ?? "";
      const val = inputs[name];
      if (val === undefined || val === null || val === "") return fallback;
      return String(val);
    }
    if (!NAME_RE.test(expr)) {
      throw new TemplateError(`invalid template expression: {{ ${expr} }}`);
    }
    if (!(expr in inputs)) {
      throw new TemplateError(`missing variable: ${expr}`);
    }
    return String(inputs[expr]);
  });
  return replaced.replaceAll(ESC_OPEN, "{{").replaceAll(ESC_CLOSE, "}}");
}

export function findVariables(template: string): Set<string> {
  const pre = template.replaceAll("{{{{", ESC_OPEN).replaceAll("}}}}", ESC_CLOSE);
  const names = new Set<string>();
  for (const m of pre.matchAll(TAG_RE)) {
    const expr = m[1].trim();
    const dm = expr.match(DEFAULT_RE);
    if (dm) names.add(dm[1]);
    else if (NAME_RE.test(expr)) names.add(expr);
  }
  return names;
}
