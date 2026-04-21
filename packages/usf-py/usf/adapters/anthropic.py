"""Anthropic Messages API adapter."""
from __future__ import annotations

from ..prompt import CompiledPrompt

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 2048


def render(compiled: CompiledPrompt, *, model: str | None = None) -> dict:
    fm = compiled.frontmatter
    chosen_model = model or (fm.get("model_hints") or {}).get("anthropic") or DEFAULT_MODEL
    payload: dict = {
        "model": chosen_model,
        "system": compiled.system,
        "messages": [{"role": "user", "content": compiled.user}],
        "max_tokens": int(fm.get("max_tokens", DEFAULT_MAX_TOKENS)),
    }
    if "recommended_temperature" in fm:
        payload["temperature"] = fm["recommended_temperature"]
    return payload
