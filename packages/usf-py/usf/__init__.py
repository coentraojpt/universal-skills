"""Universal Skills Framework — load, compile, and render LLM skills."""
from __future__ import annotations

from .loader import Skill, InputSpec, load, load_dir
from .prompt import CompiledPrompt, build_prompt
from .validate import validate_skill, ValidationError
from .obsidian import Vault, load_vault, resolve_wikilinks

__version__ = "0.1.4"

__all__ = [
    "Skill",
    "InputSpec",
    "CompiledPrompt",
    "Vault",
    "ValidationError",
    "load",
    "load_dir",
    "load_vault",
    "build_prompt",
    "resolve_wikilinks",
    "validate_skill",
]
