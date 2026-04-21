"""Tiny {{var}} templating engine — kept minimal for Py↔TS parity.

Syntax:
  {{name}}                      -> inputs["name"]
  {{name | default("fallback")}} -> inputs.get("name", "fallback")
  {{{{literal}}}}                -> literal {{literal}} (escape)

Intentionally does NOT support loops, conditionals, or filters beyond `default`.
If you need those, your skill is doing too much — split it.
"""
from __future__ import annotations

import re

_ESCAPE_OPEN = "\x00USF_ESC_OPEN\x00"
_ESCAPE_CLOSE = "\x00USF_ESC_CLOSE\x00"

_TAG_RE = re.compile(r"\{\{\s*(.*?)\s*\}\}", re.DOTALL)
_DEFAULT_RE = re.compile(
    r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*\|\s*default\(\s*(?:\"(.*?)\"|'(.*?)')\s*\)$"
)
_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class TemplateError(ValueError):
    pass


def render(template: str, inputs: dict) -> str:
    """Replace {{var}} and {{var | default("x")}} in template with values from inputs."""
    pre = template.replace("{{{{", _ESCAPE_OPEN).replace("}}}}", _ESCAPE_CLOSE)

    def replace(m: re.Match) -> str:
        expr = m.group(1).strip()
        # default filter
        dm = _DEFAULT_RE.match(expr)
        if dm:
            name = dm.group(1)
            fallback = dm.group(2) if dm.group(2) is not None else dm.group(3)
            val = inputs.get(name)
            if val is None or val == "":
                return str(fallback)
            return str(val)
        # plain variable
        if not _NAME_RE.match(expr):
            raise TemplateError(f"invalid template expression: {{{{ {expr} }}}}")
        if expr not in inputs:
            raise TemplateError(f"missing variable: {expr}")
        return str(inputs[expr])

    result = _TAG_RE.sub(replace, pre)
    return result.replace(_ESCAPE_OPEN, "{{").replace(_ESCAPE_CLOSE, "}}")


def find_variables(template: str) -> set[str]:
    """Return the set of variable names referenced in template (ignoring defaults)."""
    pre = template.replace("{{{{", _ESCAPE_OPEN).replace("}}}}", _ESCAPE_CLOSE)
    names: set[str] = set()
    for m in _TAG_RE.finditer(pre):
        expr = m.group(1).strip()
        dm = _DEFAULT_RE.match(expr)
        if dm:
            names.add(dm.group(1))
        elif _NAME_RE.match(expr):
            names.add(expr)
    return names
