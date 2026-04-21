import {
  App,
  Editor,
  MarkdownFileInfo,
  MarkdownView,
  Modal,
  Notice,
  Plugin,
  PluginSettingTab,
  Setting,
  TFile,
} from "obsidian";
import matter from "gray-matter";

// We vendor a tiny subset of USF logic here to avoid pulling node-only APIs
// (fs, url) into the plugin bundle. The runtime mirrors packages/usf-ts.

const SYSTEM_SECTIONS = ["Role", "Context", "Constraints", "Guardrails"] as const;
const USER_SECTIONS = ["Task", "Output Format", "Examples"] as const;
const REQUIRED_SECTIONS = ["Role", "Task", "Context", "Constraints", "Output Format"] as const;

interface InputSpec {
  name: string;
  type?: string;
  required?: boolean;
  default?: unknown;
  description?: string;
}

interface SkillDoc {
  file: TFile;
  frontmatter: Record<string, unknown>;
  sections: Record<string, string>;
  inputsSpec: InputSpec[];
}

interface USFSettings {
  openaiKey: string;
  anthropicKey: string;
  geminiKey: string;
  defaultProvider: "openai" | "anthropic" | "gemini" | "ollama";
  wikilinkMode: "truncate" | "summary" | "full";
  wikilinkTokenLimit: number;
}

const DEFAULT_SETTINGS: USFSettings = {
  openaiKey: "",
  anthropicKey: "",
  geminiKey: "",
  defaultProvider: "anthropic",
  wikilinkMode: "truncate",
  wikilinkTokenLimit: 1000,
};

function splitSections(body: string): Record<string, string> {
  const sections: Record<string, string> = {};
  let current: string | null = null;
  let buf: string[] = [];
  const flush = () => {
    if (current !== null) sections[current] = buf.join("\n").replace(/^\n+|\n+$/g, "");
  };
  for (const line of body.split(/\r?\n/)) {
    const m = line.match(/^#\s+(.+?)\s*$/);
    if (m) {
      flush();
      current = m[1].trim();
      buf = [];
    } else if (current !== null) {
      buf.push(line);
    }
  }
  flush();
  return sections;
}

function parseInputs(raw: unknown): InputSpec[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((r: any) => ({
    name: String(r.name),
    type: r.type ?? "string",
    required: Boolean(r.required),
    default: r.default,
    description: r.description,
  }));
}

const TAG_RE = /\{\{\s*([\s\S]*?)\s*\}\}/g;
const DEFAULT_RE = /^([a-zA-Z_][a-zA-Z0-9_]*)\s*\|\s*default\(\s*(?:"(.*?)"|'(.*?)')\s*\)$/;
const NAME_RE = /^[a-zA-Z_][a-zA-Z0-9_]*$/;
const ESC_OPEN = "\x00OPEN\x00";
const ESC_CLOSE = "\x00CLOSE\x00";

function renderTemplate(template: string, inputs: Record<string, unknown>): string {
  const pre = template.replaceAll("{{{{", ESC_OPEN).replaceAll("}}}}", ESC_CLOSE);
  const out = pre.replace(TAG_RE, (_m, grp: string) => {
    const expr = grp.trim();
    const dm = expr.match(DEFAULT_RE);
    if (dm) {
      const v = inputs[dm[1]];
      if (v === undefined || v === null || v === "") return dm[2] ?? dm[3] ?? "";
      return String(v);
    }
    if (!NAME_RE.test(expr)) throw new Error(`invalid template expression: {{ ${expr} }}`);
    if (!(expr in inputs)) throw new Error(`missing variable: ${expr}`);
    return String(inputs[expr]);
  });
  return out.replaceAll(ESC_OPEN, "{{").replaceAll(ESC_CLOSE, "}}");
}

const WIKILINK_RE = /\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]/g;

async function resolveWikilinks(
  app: App,
  text: string,
  settings: USFSettings,
  visited = new Set<string>(),
): Promise<string> {
  const mode = settings.wikilinkMode;
  const limit = settings.wikilinkTokenLimit;
  const parts: string[] = [];
  let lastIdx = 0;
  const matches = [...text.matchAll(WIKILINK_RE)];
  for (const m of matches) {
    parts.push(text.slice(lastIdx, m.index!));
    lastIdx = m.index! + m[0].length;
    const target = m[1].trim();
    if (visited.has(target)) {
      parts.push(`[circular: ${target}]`);
      continue;
    }
    const file = app.metadataCache.getFirstLinkpathDest(target, "");
    if (!file) {
      parts.push(m[0]);
      continue;
    }
    visited.add(target);
    const raw = await app.vault.cachedRead(file);
    const fm = matter(raw);
    if ((fm.data as any)?.usf === false) {
      // intentional skip via opt-out
    }
    let content: string;
    if (mode === "summary" && (fm.data as any)?.summary) {
      content = String((fm.data as any).summary);
    } else if (mode === "full") {
      content = fm.content.trim();
    } else {
      const charLimit = limit * 4;
      content = fm.content.trim();
      if (content.length > charLimit) content = content.slice(0, charLimit) + "\n…[truncated]";
    }
    const resolved = await resolveWikilinks(app, content, settings, visited);
    parts.push(resolved);
    visited.delete(target);
  }
  parts.push(text.slice(lastIdx));
  return parts.join("");
}

async function buildPrompt(
  app: App,
  skill: SkillDoc,
  inputs: Record<string, unknown>,
  settings: USFSettings,
): Promise<{ system: string; user: string }> {
  const merged = { ...inputs };
  const missing: string[] = [];
  for (const spec of skill.inputsSpec) {
    const present = spec.name in merged && merged[spec.name] !== null && merged[spec.name] !== "";
    if (present) continue;
    if (spec.default !== undefined) merged[spec.name] = spec.default;
    else if (spec.required) missing.push(spec.name);
  }
  if (missing.length) throw new Error(`Missing required input(s): ${missing.join(", ")}`);

  const sections: Record<string, string> = {};
  for (const [name, body] of Object.entries(skill.sections)) {
    const resolved = body.includes("[[") ? await resolveWikilinks(app, body, settings) : body;
    sections[name] = renderTemplate(resolved, merged);
  }
  const sys = SYSTEM_SECTIONS.filter((s) => s in sections).map((s) => `# ${s}\n${sections[s]}`).join("\n\n").trim();
  const usr = USER_SECTIONS.filter((s) => s in sections).map((s) => `# ${s}\n${sections[s]}`).join("\n\n").trim();
  return { system: sys, user: usr };
}

async function loadSkillsFromVault(app: App): Promise<SkillDoc[]> {
  const skills: SkillDoc[] = [];
  for (const file of app.vault.getMarkdownFiles()) {
    const raw = await app.vault.cachedRead(file);
    const fm = matter(raw);
    const data = fm.data as Record<string, unknown>;
    if (data.usf === false) continue;
    if (!data.name || !data.description) continue;
    const sections = splitSections(fm.content);
    const missing = REQUIRED_SECTIONS.filter((s) => !(s in sections));
    if (missing.length) continue;
    skills.push({
      file,
      frontmatter: data,
      sections,
      inputsSpec: parseInputs(data.inputs),
    });
  }
  return skills.sort((a, b) => String(a.frontmatter.name).localeCompare(String(b.frontmatter.name)));
}

async function callProvider(
  provider: string,
  system: string,
  user: string,
  fm: Record<string, unknown>,
  settings: USFSettings,
): Promise<string> {
  const hints = (fm.model_hints as Record<string, string>) ?? {};
  const temperature = fm.recommended_temperature as number | undefined;
  const maxTokens = Number(fm.max_tokens ?? 2048);

  if (provider === "openai") {
    if (!settings.openaiKey) throw new Error("OpenAI key not set in USF settings.");
    const model = hints.openai ?? "gpt-4o";
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${settings.openaiKey}` },
      body: JSON.stringify({
        model,
        messages: [
          { role: "system", content: system },
          { role: "user", content: user },
        ],
        ...(temperature !== undefined ? { temperature } : {}),
        max_tokens: maxTokens,
      }),
    });
    if (!res.ok) throw new Error(`OpenAI error: ${res.status} ${await res.text()}`);
    const j = await res.json();
    return j.choices?.[0]?.message?.content ?? "";
  }
  if (provider === "anthropic") {
    if (!settings.anthropicKey) throw new Error("Anthropic key not set in USF settings.");
    const model = hints.anthropic ?? "claude-sonnet-4-6";
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": settings.anthropicKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model,
        system,
        messages: [{ role: "user", content: user }],
        max_tokens: maxTokens,
        ...(temperature !== undefined ? { temperature } : {}),
      }),
    });
    if (!res.ok) throw new Error(`Anthropic error: ${res.status} ${await res.text()}`);
    const j = await res.json();
    return j.content?.[0]?.text ?? "";
  }
  if (provider === "gemini") {
    if (!settings.geminiKey) throw new Error("Gemini key not set in USF settings.");
    const model = hints.gemini ?? "gemini-1.5-pro";
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${settings.geminiKey}`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_instruction: { parts: [{ text: system }] },
        contents: [{ role: "user", parts: [{ text: user }] }],
        generationConfig: {
          ...(temperature !== undefined ? { temperature } : {}),
          maxOutputTokens: maxTokens,
        },
      }),
    });
    if (!res.ok) throw new Error(`Gemini error: ${res.status} ${await res.text()}`);
    const j = await res.json();
    return j.candidates?.[0]?.content?.parts?.[0]?.text ?? "";
  }
  if (provider === "ollama") {
    const host = (fm.ollama_host as string) ?? "http://localhost:11434";
    const model = hints.ollama ?? "llama3.1:8b";
    const res = await fetch(`${host}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        system,
        prompt: user,
        stream: false,
        options: {
          ...(temperature !== undefined ? { temperature } : {}),
          num_predict: maxTokens,
        },
      }),
    });
    if (!res.ok) throw new Error(`Ollama error: ${res.status} ${await res.text()}`);
    const j = await res.json();
    return j.response ?? "";
  }
  throw new Error(`unknown provider: ${provider}`);
}

class SkillPickerModal extends Modal {
  constructor(
    app: App,
    private skills: SkillDoc[],
    private onPick: (skill: SkillDoc) => void,
  ) {
    super(app);
  }
  onOpen() {
    this.titleEl.setText("Run USF skill");
    const container = this.contentEl.createDiv();
    for (const skill of this.skills) {
      const btn = container.createEl("button", { text: String(skill.frontmatter.name) });
      btn.style.display = "block";
      btn.style.margin = "4px 0";
      btn.style.width = "100%";
      btn.style.textAlign = "left";
      btn.onclick = () => {
        this.close();
        this.onPick(skill);
      };
      const desc = container.createEl("div", { text: String(skill.frontmatter.description ?? "") });
      desc.style.fontSize = "0.8em";
      desc.style.opacity = "0.7";
      desc.style.marginBottom = "8px";
    }
  }
  onClose() {
    this.contentEl.empty();
  }
}

class InputsModal extends Modal {
  private values: Record<string, string> = {};
  constructor(
    app: App,
    private skill: SkillDoc,
    private onSubmit: (inputs: Record<string, string>, provider: string) => void,
    private defaultProvider: string,
  ) {
    super(app);
  }
  onOpen() {
    this.titleEl.setText(`Inputs for ${String(this.skill.frontmatter.name)}`);
    for (const spec of this.skill.inputsSpec) {
      new Setting(this.contentEl)
        .setName(spec.name + (spec.required ? " *" : ""))
        .setDesc(spec.description ?? "")
        .addTextArea((t) => {
          t.setPlaceholder(spec.default !== undefined ? String(spec.default) : "");
          t.onChange((v) => (this.values[spec.name] = v));
        });
    }
    let provider = this.defaultProvider;
    new Setting(this.contentEl)
      .setName("Provider")
      .addDropdown((dd) => {
        dd.addOption("openai", "openai");
        dd.addOption("anthropic", "anthropic");
        dd.addOption("gemini", "gemini");
        dd.addOption("ollama", "ollama");
        dd.setValue(provider);
        dd.onChange((v) => (provider = v));
      });
    new Setting(this.contentEl).addButton((b) =>
      b.setButtonText("Run").setCta().onClick(() => {
        this.close();
        this.onSubmit(this.values, provider);
      }),
    );
  }
  onClose() {
    this.contentEl.empty();
  }
}

export default class USFPlugin extends Plugin {
  settings!: USFSettings;

  async onload() {
    await this.loadSettings();

    this.addCommand({
      id: "usf-run-skill",
      name: "USF: Run skill",
      editorCallback: async (editor: Editor, _view: MarkdownView | MarkdownFileInfo) => {
        const skills = await loadSkillsFromVault(this.app);
        if (!skills.length) {
          new Notice("No USF skills found in this vault.");
          return;
        }
        new SkillPickerModal(this.app, skills, (skill) => {
          new InputsModal(
            this.app,
            skill,
            async (inputs, provider) => {
              try {
                new Notice(`Running ${String(skill.frontmatter.name)} via ${provider}…`);
                const { system, user } = await buildPrompt(this.app, skill, inputs, this.settings);
                const out = await callProvider(provider, system, user, skill.frontmatter, this.settings);
                editor.replaceSelection("\n\n" + out + "\n");
                new Notice("USF: done.");
              } catch (e: any) {
                new Notice(`USF error: ${e.message}`);
              }
            },
            this.settings.defaultProvider,
          ).open();
        }).open();
      },
    });

    this.addCommand({
      id: "usf-validate-note",
      name: "USF: Validate current note",
      editorCallback: async (_editor: Editor, view: MarkdownView | MarkdownFileInfo) => {
        const file = view.file;
        if (!file) return;
        const raw = await this.app.vault.cachedRead(file);
        const fm = matter(raw);
        const data = fm.data as Record<string, unknown>;
        const errs: string[] = [];
        if (!data.name) errs.push("frontmatter missing 'name'");
        if (!data.description) errs.push("frontmatter missing 'description'");
        const sections = splitSections(fm.content);
        for (const s of REQUIRED_SECTIONS) {
          if (!(s in sections)) errs.push(`missing required section: # ${s}`);
        }
        if (!errs.length) new Notice("USF: valid skill.");
        else new Notice("USF: " + errs.join("\n"));
      },
    });

    this.addSettingTab(new USFSettingTab(this.app, this));

    loadSkillsFromVault(this.app).then((skills) => {
      this.addStatusBarItem().setText(`USF: ${skills.length} skills`);
    });
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
}

class USFSettingTab extends PluginSettingTab {
  constructor(app: App, private plugin: USFPlugin) {
    super(app, plugin);
  }
  display(): void {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("h2", { text: "Universal Skills (USF)" });
    containerEl.createEl("p", {
      text:
        "API keys are stored via Obsidian's plugin data (never written as plaintext in your notes).",
    });

    new Setting(containerEl)
      .setName("OpenAI API key")
      .addText((t) =>
        t.setValue(this.plugin.settings.openaiKey).onChange(async (v) => {
          this.plugin.settings.openaiKey = v;
          await this.plugin.saveSettings();
        }),
      );

    new Setting(containerEl)
      .setName("Anthropic API key")
      .addText((t) =>
        t.setValue(this.plugin.settings.anthropicKey).onChange(async (v) => {
          this.plugin.settings.anthropicKey = v;
          await this.plugin.saveSettings();
        }),
      );

    new Setting(containerEl)
      .setName("Google Gemini API key")
      .addText((t) =>
        t.setValue(this.plugin.settings.geminiKey).onChange(async (v) => {
          this.plugin.settings.geminiKey = v;
          await this.plugin.saveSettings();
        }),
      );

    new Setting(containerEl)
      .setName("Default provider")
      .addDropdown((dd) => {
        dd.addOption("openai", "openai");
        dd.addOption("anthropic", "anthropic");
        dd.addOption("gemini", "gemini");
        dd.addOption("ollama", "ollama");
        dd.setValue(this.plugin.settings.defaultProvider);
        dd.onChange(async (v: any) => {
          this.plugin.settings.defaultProvider = v;
          await this.plugin.saveSettings();
        });
      });

    new Setting(containerEl)
      .setName("Wikilink mode")
      .setDesc("How [[note]] references in skills are expanded.")
      .addDropdown((dd) => {
        dd.addOption("truncate", "truncate");
        dd.addOption("summary", "summary");
        dd.addOption("full", "full");
        dd.setValue(this.plugin.settings.wikilinkMode);
        dd.onChange(async (v: any) => {
          this.plugin.settings.wikilinkMode = v;
          await this.plugin.saveSettings();
        });
      });

    new Setting(containerEl)
      .setName("Wikilink token limit")
      .setDesc("Approx. tokens per resolved [[link]] (used when mode=truncate).")
      .addText((t) =>
        t.setValue(String(this.plugin.settings.wikilinkTokenLimit)).onChange(async (v) => {
          const n = Number(v);
          if (!Number.isNaN(n) && n > 0) {
            this.plugin.settings.wikilinkTokenLimit = n;
            await this.plugin.saveSettings();
          }
        }),
      );
  }
}
