/**
 * Example: build the OpenAI chat-completions payload for the code-reviewer skill.
 *
 * Run with:
 *   cd packages/usf-ts && npm run build && cd ../..
 *   npx tsx examples/node/openai_example.ts
 *
 * This script stays offline — it prints the payload. To actually call OpenAI,
 * pass `payload` to the official `openai` SDK (or fetch).
 */
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load, getAdapter } from "../../packages/usf-ts/src/index.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const skillPath = path.resolve(here, "../../skills/code-reviewer.md");

async function main() {
  const skill = await load(skillPath);
  const compiled = await skill.buildPrompt({
    code: "function divide(a, b) { return a / b; }",
    language: "javascript",
  });
  const payload = getAdapter("openai").render(compiled);
  console.log(JSON.stringify(payload, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
