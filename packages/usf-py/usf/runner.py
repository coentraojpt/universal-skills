"""Call real provider SDKs — lazy imports so only installed SDKs need be present."""
from __future__ import annotations

import json
import os
import urllib.request

from .loader import Skill


def run(skill: Skill, provider: str, inputs: dict, *, vault=None, model: str | None = None,
        stream: bool = False) -> str:
    payload = skill.render(provider, inputs, vault)
    if model:
        payload["model"] = model
    provider = provider.lower()
    if provider in ("openai",):
        return _run_openai(payload, stream=stream)
    if provider in ("anthropic", "claude"):
        return _run_anthropic(payload, stream=stream)
    if provider in ("gemini", "google"):
        return _run_gemini(payload)
    if provider in ("ollama", "local"):
        return _run_ollama(payload)
    raise ValueError(f"unsupported provider: {provider}")


def _run_openai(payload: dict, *, stream: bool) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai not installed. pip install 'universal-skills[openai]'") from exc
    client = OpenAI()
    if stream:
        chunks = []
        with client.chat.completions.stream(**payload) as s:
            for event in s:
                if event.type == "content.delta":
                    print(event.delta, end="", flush=True)
                    chunks.append(event.delta)
            print()
        return "".join(chunks)
    resp = client.chat.completions.create(**payload)
    return resp.choices[0].message.content or ""


def _run_anthropic(payload: dict, *, stream: bool) -> str:
    try:
        import anthropic as sdk
    except ImportError as exc:
        raise RuntimeError("anthropic not installed. pip install 'universal-skills[anthropic]'") from exc
    client = sdk.Anthropic()
    if stream:
        chunks = []
        with client.messages.stream(**payload) as s:
            for text in s.text_stream:
                print(text, end="", flush=True)
                chunks.append(text)
            print()
        return "".join(chunks)
    resp = client.messages.create(**payload)
    return resp.content[0].text if resp.content else ""


def _run_gemini(payload: dict) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("google-genai not installed. pip install 'universal-skills[gemini]'") from exc
    client = genai.Client()
    model = payload["model"]
    system_text = payload["system_instruction"]["parts"][0]["text"]
    user_text = payload["contents"][0]["parts"][0]["text"]
    cfg_raw = payload.get("generationConfig", {})
    cfg = types.GenerateContentConfig(
        system_instruction=system_text,
        temperature=cfg_raw.get("temperature"),
        max_output_tokens=cfg_raw.get("maxOutputTokens"),
    )
    resp = client.models.generate_content(model=model, contents=user_text, config=cfg)
    return resp.text or ""


def _run_ollama(payload: dict) -> str:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    req = urllib.request.Request(
        f"{host}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("response", "")
