import { promises as fs } from "node:fs";
import path from "node:path";

import { parse, type ParsedSkill } from "./parser.js";

const WIKILINK_RE = /\[\[([^\[\]#|]+)(?:#([^\[\]|]+))?(?:\|[^\[\]]+)?\]\]/g;

export type WikilinkMode = "truncate" | "summary" | "full";

export interface WikilinkStats {
  resolved: number;
  truncated: number;
  skipped: number;
  totalTokens: number;
}

export class Vault {
  constructor(
    public readonly root: string,
    public readonly notes: Map<string, string>,
  ) {}

  async getNoteText(name: string): Promise<string | null> {
    const p = this.notes.get(name);
    if (!p) return null;
    return fs.readFile(p, "utf-8");
  }
}

export async function loadVault(root: string): Promise<Vault> {
  const abs = path.resolve(root);
  const notes = new Map<string, string>();
  await walk(abs, notes);
  return new Vault(abs, notes);
}

async function walk(dir: string, notes: Map<string, string>): Promise<void> {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    if (e.name.startsWith(".")) continue;
    const full = path.join(dir, e.name);
    if (e.isDirectory()) {
      await walk(full, notes);
    } else if (e.isFile() && e.name.endsWith(".md")) {
      const stem = e.name.replace(/\.md$/, "");
      notes.set(stem, full);
    }
  }
}

export function approxTokens(text: string): number {
  return Math.max(1, Math.floor(text.length / 4));
}

export async function resolveWikilinks(
  vault: Vault,
  text: string,
  opts: { mode?: WikilinkMode; perLinkTokenLimit?: number } = {},
  visited: Set<string> = new Set(),
): Promise<{ text: string; stats: WikilinkStats }> {
  const mode = opts.mode ?? "truncate";
  const limit = opts.perLinkTokenLimit ?? 1000;
  if (!["truncate", "summary", "full"].includes(mode)) {
    throw new Error(`invalid wikilink mode: ${mode}`);
  }
  const stats: WikilinkStats = { resolved: 0, truncated: 0, skipped: 0, totalTokens: 0 };

  // Because JS regex .replace can't await, collect matches and build output sequentially.
  const matches: { start: number; end: number; content: string }[] = [];
  for (const m of text.matchAll(WIKILINK_RE)) {
    const name = m[1].trim();
    const section = m[2]?.trim();
    if (visited.has(name)) {
      stats.skipped += 1;
      matches.push({ start: m.index!, end: m.index! + m[0].length, content: `[[${name}]]` });
      continue;
    }
    const raw = await vault.getNoteText(name);
    if (raw == null) {
      stats.skipped += 1;
      matches.push({ start: m.index!, end: m.index! + m[0].length, content: `[[${name}]]` });
      continue;
    }
    const parsed = parse(raw);
    const body = section ? extractSection(parsed, section) : noteBody(parsed);
    let content = applyMode(parsed.frontmatter, body, mode, limit, stats);
    if (content.includes("[[")) {
      const child = new Set(visited);
      child.add(name);
      const resolved = await resolveWikilinks(vault, content, opts, child);
      content = resolved.text;
      stats.resolved += resolved.stats.resolved;
      stats.truncated += resolved.stats.truncated;
      stats.skipped += resolved.stats.skipped;
      stats.totalTokens += resolved.stats.totalTokens;
    }
    stats.resolved += 1;
    stats.totalTokens += approxTokens(content);
    matches.push({ start: m.index!, end: m.index! + m[0].length, content });
  }
  let out = "";
  let cursor = 0;
  for (const m of matches) {
    out += text.slice(cursor, m.start) + m.content;
    cursor = m.end;
  }
  out += text.slice(cursor);
  return { text: out, stats };
}

function noteBody(parsed: ParsedSkill): string {
  if (Object.keys(parsed.sections).length === 0) {
    return parsed.raw.split(/^---\s*$/m).slice(-1)[0].trim();
  }
  return Object.entries(parsed.sections)
    .map(([name, body]) => `# ${name}\n${body}`)
    .join("\n\n");
}

function extractSection(parsed: ParsedSkill, section: string): string {
  for (const [name, body] of Object.entries(parsed.sections)) {
    if (name.toLowerCase() === section.toLowerCase()) return body;
  }
  return noteBody(parsed);
}

function applyMode(
  frontmatter: Record<string, unknown>,
  body: string,
  mode: WikilinkMode,
  limit: number,
  stats: WikilinkStats,
): string {
  if (mode === "full") return body;
  if (mode === "summary") {
    const s = frontmatter["summary"];
    if (typeof s === "string" && s.trim()) return s.trim();
  }
  const chars = limit * 4;
  if (body.length > chars) {
    stats.truncated += 1;
    return body.slice(0, chars).replace(/\s+$/, "") + "\n\n…[truncated]";
  }
  return body;
}
