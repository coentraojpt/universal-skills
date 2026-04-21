"""Run the commit-message-writer skill against a local Ollama model.

Prereq:
    Run Ollama locally: https://ollama.com
    pip install -e packages/usf-py
    (optional) export OLLAMA_HOST=http://localhost:11434

Run:
    python examples/python/ollama_example.py
"""
from __future__ import annotations

from pathlib import Path

from usf import load

SKILL = Path(__file__).resolve().parents[2] / "skills" / "commit-message-writer.md"
DIFF = """diff --git a/src/auth.ts b/src/auth.ts
@@
-function verify(token) {
+function verify(token, opts = {}) {
   if (!token) return false;
+  if (opts.allowExpired && isExpired(token)) return true;
   return validate(token);
 }
"""


def main() -> None:
    skill = load(SKILL)
    output = skill.run("ollama", {"diff": DIFF, "scope": "auth"})
    print(output)


if __name__ == "__main__":
    main()
