import { resolveWikilinks, type Vault, type WikilinkStats } from "./obsidian.js";
import { render as renderTemplate } from "./template.js";
import type { Skill } from "./loader.js";

export const SYSTEM_SECTIONS = ["Role", "Context", "Constraints", "Guardrails"] as const;
export const USER_SECTIONS = ["Task", "Output Format", "Examples"] as const;

export interface CompiledPrompt {
  system: string;
  user: string;
  metadata: Record<string, unknown>;
  frontmatter: Record<string, unknown>;
}

export async function buildPrompt(
  skill: Skill,
  inputs: Record<string, unknown> = {},
  vault?: Vault,
): Promise<CompiledPrompt> {
  const mergedInputs = { ...inputs };
  applyDefaultsAndValidate(skill, mergedInputs);

  const sections: Record<string, string> = { ...skill.sections };
  let wikilinkStats: WikilinkStats | undefined;

  if (vault) {
    const mode = (skill.frontmatter["wikilink_mode"] as "truncate" | "summary" | "full") ?? "truncate";
    const limit = Number(skill.frontmatter["wikilink_token_limit"] ?? 1000);
    for (const [name, body] of Object.entries(sections)) {
      if (!body.includes("[[")) continue;
      const { text, stats } = await resolveWikilinks(vault, body, {
        mode,
        perLinkTokenLimit: limit,
      });
      sections[name] = text;
      if (!wikilinkStats) wikilinkStats = { ...stats };
      else {
        wikilinkStats.resolved += stats.resolved;
        wikilinkStats.truncated += stats.truncated;
        wikilinkStats.skipped += stats.skipped;
        wikilinkStats.totalTokens += stats.totalTokens;
      }
      if (stats.truncated) {
        console.warn(
          `[warn] wikilinks truncated in section '${name}': ${stats.truncated} link(s) -> ${limit} tokens each`,
        );
      }
    }
  }

  for (const [name, body] of Object.entries(sections)) {
    sections[name] = renderTemplate(body, mergedInputs);
  }

  const systemParts = SYSTEM_SECTIONS.filter((s) => s in sections).map(
    (s) => `# ${s}\n${sections[s]}`,
  );
  const userParts = USER_SECTIONS.filter((s) => s in sections).map(
    (s) => `# ${s}\n${sections[s]}`,
  );

  const metadata: Record<string, unknown> = { skill: skill.frontmatter["name"] };
  if (wikilinkStats) metadata.wikilink_stats = wikilinkStats;

  return {
    system: systemParts.join("\n\n").trim(),
    user: userParts.join("\n\n").trim(),
    metadata,
    frontmatter: { ...skill.frontmatter },
  };
}

function applyDefaultsAndValidate(skill: Skill, inputs: Record<string, unknown>): void {
  const missing: string[] = [];
  for (const spec of skill.inputsSpec) {
    const present = spec.name in inputs && inputs[spec.name] !== null && inputs[spec.name] !== "";
    if (present) continue;
    if (spec.default !== undefined) {
      inputs[spec.name] = spec.default;
    } else if (spec.required) {
      missing.push(spec.name);
    }
  }
  if (missing.length) {
    throw new Error(
      `Missing required input(s) for skill '${skill.frontmatter["name"]}': ${missing.join(", ")}`,
    );
  }
}
