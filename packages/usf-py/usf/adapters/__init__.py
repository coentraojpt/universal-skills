"""Provider adapters — each turns a CompiledPrompt into a provider-specific payload."""
from __future__ import annotations

from . import anthropic, gemini, ollama, openai

_ADAPTERS = {
    "openai": openai,
    "anthropic": anthropic,
    "claude": anthropic,  # alias
    "gemini": gemini,
    "google": gemini,  # alias
    "ollama": ollama,
    "local": ollama,  # alias
}


def get_adapter(provider: str):
    key = provider.lower()
    if key not in _ADAPTERS:
        raise ValueError(
            f"unknown provider: {provider}. Supported: {sorted(set(_ADAPTERS.values()), key=lambda m: m.__name__)}"
        )
    return _ADAPTERS[key]


def available_providers() -> list[str]:
    return ["openai", "anthropic", "gemini", "ollama"]
