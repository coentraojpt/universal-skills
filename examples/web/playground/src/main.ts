import matter from "gray-matter";
import { parse, buildPrompt, getAdapter, Skill, type InputSpec } from "@universal-skills/core";

type SkillRecord = {
  name: string;
  description: string;
  raw: string;
  inputsSpec: InputSpec[];
};

// Skills are bundled statically via Vite's glob import — works in-browser without fs.
const modules = import.meta.glob("../../../../skills/*.md", { as: "raw", eager: true });

function buildSkillRecords(): SkillRecord[] {
  const records: SkillRecord[] = [];
  for (const [p, raw] of Object.entries(modules)) {
    const fm = matter(raw as string);
    const data = fm.data as Record<string, unknown>;
    if (!data.name || !data.description) continue;
    if (data.usf === false) continue;
    const inputs = Array.isArray(data.inputs) ? (data.inputs as InputSpec[]) : [];
    records.push({
      name: String(data.name),
      description: String(data.description),
      raw: raw as string,
      inputsSpec: inputs,
    });
  }
  return records.sort((a, b) => a.name.localeCompare(b.name));
}

async function render(record: SkillRecord, inputs: Record<string, unknown>, provider: string) {
  const parsed = parse(record.raw);
  const skill = new Skill(parsed.frontmatter, parsed.sections, record.inputsSpec);
  const compiled = await buildPrompt(skill, inputs);
  const payload = getAdapter(provider).render(compiled);
  return { compiled, payload };
}

function renderInputs(record: SkillRecord, container: HTMLElement) {
  container.innerHTML = "";
  for (const spec of record.inputsSpec) {
    const label = document.createElement("label");
    label.textContent = spec.name + (spec.required ? " *" : "");
    const textarea = document.createElement("textarea");
    textarea.id = `input-${spec.name}`;
    textarea.placeholder = spec.description ?? "";
    if (spec.default !== undefined) textarea.value = String(spec.default);
    container.appendChild(label);
    container.appendChild(textarea);
  }
}

async function main() {
  const records = buildSkillRecords();
  const skillSelect = document.getElementById("skill") as HTMLSelectElement;
  const providerSelect = document.getElementById("provider") as HTMLSelectElement;
  const inputsDiv = document.getElementById("inputs") as HTMLDivElement;
  const promptPre = document.getElementById("prompt") as HTMLPreElement;
  const payloadPre = document.getElementById("payload") as HTMLPreElement;
  const btn = document.getElementById("render") as HTMLButtonElement;

  for (const r of records) {
    const opt = document.createElement("option");
    opt.value = r.name;
    opt.textContent = `${r.name} — ${r.description.slice(0, 60)}`;
    skillSelect.appendChild(opt);
  }

  const find = (name: string) => records.find((r) => r.name === name)!;
  renderInputs(find(skillSelect.value), inputsDiv);
  skillSelect.addEventListener("change", () => renderInputs(find(skillSelect.value), inputsDiv));

  btn.addEventListener("click", async () => {
    const r = find(skillSelect.value);
    const inputs: Record<string, string> = {};
    for (const spec of r.inputsSpec) {
      const el = document.getElementById(`input-${spec.name}`) as HTMLTextAreaElement;
      if (el && el.value) inputs[spec.name] = el.value;
    }
    try {
      const { compiled, payload } = await render(r, inputs, providerSelect.value);
      promptPre.textContent = `[system]\n${compiled.system}\n\n[user]\n${compiled.user}`;
      payloadPre.textContent = JSON.stringify(payload, null, 2);
    } catch (e: any) {
      promptPre.textContent = `Error: ${e.message}`;
      payloadPre.textContent = "";
    }
  });

  // Render something on load
  btn.click();
}

main();
