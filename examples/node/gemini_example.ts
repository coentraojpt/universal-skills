/**
 * Build a Gemini generateContent payload for the api-designer skill.
 *
 * Run with:
 *   npx tsx examples/node/gemini_example.ts
 */
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load, getAdapter } from "../../packages/usf-ts/src/index.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const skillPath = path.resolve(here, "../../skills/api-designer.md");

async function main() {
  const skill = await load(skillPath);
  const compiled = await skill.buildPrompt({
    feature: "A notification service that fans out events to email, SMS, and push.",
    style: "REST",
  });
  const payload = getAdapter("gemini").render(compiled);
  console.log(JSON.stringify(payload, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
