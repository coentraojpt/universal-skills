---
usf: false
name: usf-format
description: Referência completa do formato USF para criar e atualizar skills.
---

# USF Skill Format

A skill USF é um ficheiro markdown com frontmatter YAML. Cada skill vive em `skills/<name>.md`.

## Estrutura do ficheiro

```
---
name: <kebab-case-sem-espacos>
description: <uma frase clara do que a skill faz>
version: 1.0.0
tags: [tag1, tag2]
recommended_temperature: 0.2
max_tokens: 2048
model_hints:
  openai: gpt-4o
  anthropic: claude-sonnet-4-6
  gemini: gemini-1.5-pro
  ollama: llama3.1:8b
inputs:
  - name: <nome-do-input>
    type: string
    required: true
    description: <descrição do que este input representa>
  - name: <input-opcional>
    type: string
    required: false
    default: <valor-default>
    description: <descrição>
---

# Role
<Quem é o LLM — persona, expertise, tom>

# Task
<O que fazer exatamente. Usar {{variavel}} para interpolar inputs.>

# Context
<Pressupostos, notas de domínio, referências. Usar [[nome-da-nota]] para injetar memória do vault.>

# Constraints
- DO <fazer X>
- DO NOT <fazer Y>

# Output Format
<Estrutura exata da resposta — headers, listas, formato, língua>
```

## Regras

- `name` em kebab-case, igual ao nome do ficheiro sem `.md`
- As 5 secções (Role, Task, Context, Constraints, Output Format) são obrigatórias
- Inputs usados no body com `{{nome}}` devem estar declarados no frontmatter
- `[[nota]]` resolve para o conteúdo de `_memory/nota.md` em runtime
- `recommended_temperature`: 0.0–0.3 para tarefas exactas, 0.4–0.8 para criativas

## Exemplo mínimo

```markdown
---
name: resumo
description: Resume um texto longo em bullet points.
version: 1.0.0
tags: [writing]
recommended_temperature: 0.3
inputs:
  - name: texto
    type: string
    required: true
    description: O texto a resumir.
---

# Role
És um editor técnico sénior especializado em síntese de informação.

# Task
Resume o seguinte texto em bullet points concisos:

{{texto}}

# Context
Prioriza factos, decisões e acções concretas. Ignora frases de preenchimento.

# Constraints
- DO manter cada bullet com menos de 20 palavras.
- DO NOT incluir opiniões ou interpretações que não estejam no texto original.

# Output Format
- Bullet 1
- Bullet 2
- ...

Máximo 10 bullets.
```
