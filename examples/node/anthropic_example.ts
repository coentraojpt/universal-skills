/**
 * Build the Anthropic Messages API payload for the refactorer skill.
 *
 * Run with:
 *   npx tsx examples/node/anthropic_example.ts
 */
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load, getAdapter } from "../../packages/usf-ts/src/index.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const skillPath = path.resolve(here, "../../skills/refactorer.md");

async function main() {
  const skill = await load(skillPath);
  const compiled = await skill.buildPrompt({
    code: "function p(l) { const r = []; for (let i=0; i<l.length; i++) if (l[i] % 2 === 0) r.push(l[i]*2); return r; }",
    language: "javascript",
    priorities: "readability,simplicity",
  });
  const payload = getAdapter("anthropic").render(compiled);
  console.log(JSON.stringify(payload, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
