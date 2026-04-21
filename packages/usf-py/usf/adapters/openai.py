"""OpenAI Chat Completions adapter."""
from __future__ import annotations

from ..prompt import CompiledPrompt

DEFAULT_MODEL = "gpt-4o"


def render(compiled: CompiledPrompt, *, model: str | None = None) -> dict:
    fm = compiled.frontmatter
    chosen_model = model or (fm.get("model_hints") or {}).get("openai") or DEFAULT_MODEL
    payload: dict = {
        "model": chosen_model,
        "messages": [
            {"role": "system", "content": compiled.system},
            {"role": "user", "content": compiled.user},
        ],
    }
    if "recommended_temperature" in fm:
        payload["temperature"] = fm["recommended_temperature"]
    if "max_tokens" in fm:
        payload["max_tokens"] = fm["max_tokens"]
    return payload
