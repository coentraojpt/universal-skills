---
name: my-advanced-skill
description: One-line description (≤1024 chars) — shown in listings and used by Claude Agent Skills.
version: 0.1.0
author: your-handle
tags: [category, subcategory]
recommended_temperature: 0.3
max_tokens: 2048
model_hints:
  openai: gpt-4o
  anthropic: claude-sonnet-4-6
  gemini: gemini-1.5-pro
  ollama: llama3.1:8b
inputs:
  - name: target
    type: string
    required: true
    description: The primary subject of the task.
  - name: tone
    type: string
    required: false
    default: neutral
    description: Desired tone (neutral, formal, casual).
wikilink_mode: truncate
wikilink_token_limit: 1000
---

# Role
[Detailed persona. Include domain, seniority, and perspective.]

# Task
[Primary objective. Start with an action verb. Reference inputs with {{{{var}}}}.]

Target: {{target}}
Tone: {{tone | default("neutral")}}

# Context
[Relevant background. Reference shared memory via [[wikilink]] when appropriate.]

# Constraints
- DO [explicit positive rule].
- DO NOT [explicit negative rule].

# Output Format
[Strict schema — JSON, Markdown layout, or specific headings.]

# Guardrails
[What to do when inputs are missing, ambiguous, or the task cannot be completed.]

# Examples
[Optional few-shot input/output pairs.]
