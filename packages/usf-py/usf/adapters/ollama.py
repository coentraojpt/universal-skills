"""Ollama local-LLM adapter (/api/generate style)."""
from __future__ import annotations

from ..prompt import CompiledPrompt

DEFAULT_MODEL = "llama3.1:8b"


def render(compiled: CompiledPrompt, *, model: str | None = None) -> dict:
    fm = compiled.frontmatter
    chosen_model = model or (fm.get("model_hints") or {}).get("ollama") or DEFAULT_MODEL
    options: dict = {}
    if "recommended_temperature" in fm:
        options["temperature"] = fm["recommended_temperature"]
    if "max_tokens" in fm:
        options["num_predict"] = fm["max_tokens"]
    payload: dict = {
        "model": chosen_model,
        "system": compiled.system,
        "prompt": compiled.user,
        "stream": False,
    }
    if options:
        payload["options"] = options
    return payload
