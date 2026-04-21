/**
 * Inspect a skill's compiled prompt and payloads for every provider.
 *
 * Run with:
 *   npx tsx examples/node/load_any_skill.ts code-reviewer
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load, getAdapter, availableProviders } from "../../packages/usf-ts/src/index.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "../..");

async function main() {
  const name = process.argv[2] ?? "code-reviewer";
  const skill = await load(path.join(repo, "skills", `${name}.md`));
  const fixtures = JSON.parse(
    await fs.readFile(path.join(repo, "tests/fixtures/canonical_inputs.json"), "utf-8"),
  ) as Record<string, Record<string, unknown>>;
  const compiled = await skill.buildPrompt(fixtures[name] ?? {});

  console.log(`=== Skill: ${skill.name} ===`);
  console.log("[system]");
  console.log(compiled.system);
  console.log("\n[user]");
  console.log(compiled.user);

  for (const provider of availableProviders()) {
    const payload = getAdapter(provider).render(compiled);
    console.log(`\n--- ${provider} payload ---`);
    console.log(JSON.stringify(payload, null, 2).slice(0, 500));
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
