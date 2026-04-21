"""Google Gemini adapter (generateContent-style payload)."""
from __future__ import annotations

from ..prompt import CompiledPrompt

DEFAULT_MODEL = "gemini-1.5-pro"


def render(compiled: CompiledPrompt, *, model: str | None = None) -> dict:
    fm = compiled.frontmatter
    chosen_model = model or (fm.get("model_hints") or {}).get("gemini") or DEFAULT_MODEL
    gen_config: dict = {}
    if "recommended_temperature" in fm:
        gen_config["temperature"] = fm["recommended_temperature"]
    if "max_tokens" in fm:
        gen_config["maxOutputTokens"] = fm["max_tokens"]
    payload: dict = {
        "model": chosen_model,
        "system_instruction": {"parts": [{"text": compiled.system}]},
        "contents": [{"role": "user", "parts": [{"text": compiled.user}]}],
    }
    if gen_config:
        payload["generationConfig"] = gen_config
    return payload
