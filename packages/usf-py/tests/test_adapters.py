from pathlib import Path

from usf.adapters import available_providers, get_adapter
from usf.loader import load

REPO = Path(__file__).resolve().parents[3]


def _skill():
    return load(REPO / "skills" / "code-reviewer.md")


def test_openai_payload_shape():
    payload = _skill().render("openai", {"code": "x = 1"})
    assert payload["model"] == "gpt-4o"
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"
    assert "x = 1" in payload["messages"][1]["content"]
    assert payload["temperature"] == 0.1


def test_anthropic_payload_shape():
    payload = _skill().render("anthropic", {"code": "x = 1"})
    assert payload["model"].startswith("claude-")
    assert isinstance(payload["system"], str) and len(payload["system"]) > 0
    assert payload["messages"][0]["role"] == "user"
    assert payload["max_tokens"] == 2048


def test_gemini_payload_shape():
    payload = _skill().render("gemini", {"code": "x = 1"})
    assert payload["model"].startswith("gemini-")
    assert payload["system_instruction"]["parts"][0]["text"]
    assert payload["contents"][0]["role"] == "user"


def test_ollama_payload_shape():
    payload = _skill().render("ollama", {"code": "x = 1"})
    assert "system" in payload and "prompt" in payload
    assert payload["stream"] is False


def test_available_providers():
    assert set(available_providers()) == {"openai", "anthropic", "gemini", "ollama"}


def test_alias_claude_resolves_to_anthropic():
    a = get_adapter("claude")
    b = get_adapter("anthropic")
    assert a is b


def test_unknown_provider_raises():
    import pytest
    with pytest.raises(ValueError):
        get_adapter("bogus")
