import matter from "gray-matter";

export const REQUIRED_SECTIONS = [
  "Role",
  "Task",
  "Context",
  "Constraints",
  "Output Format",
] as const;

export interface ParsedSkill {
  frontmatter: Record<string, unknown>;
  sections: Record<string, string>;
  raw: string;
}

export function parse(text: string): ParsedSkill {
  const parsed = matter(text);
  const frontmatter = (parsed.data ?? {}) as Record<string, unknown>;
  const sections = splitSections(parsed.content);
  return { frontmatter, sections, raw: text };
}

function splitSections(body: string): Record<string, string> {
  const lines = body.split(/\r?\n/);
  const sections: Record<string, string> = {};
  let current: string | null = null;
  let buf: string[] = [];
  const flush = () => {
    if (current !== null) sections[current] = buf.join("\n").replace(/^\n+|\n+$/g, "");
  };
  for (const line of lines) {
    const m = line.match(/^#\s+(.+?)\s*$/);
    if (m) {
      flush();
      current = m[1].trim();
      buf = [];
    } else if (current !== null) {
      buf.push(line);
    }
  }
  flush();
  return sections;
}

export function missingRequiredSections(sections: Record<string, string>): string[] {
  return REQUIRED_SECTIONS.filter((s) => !(s in sections));
}
