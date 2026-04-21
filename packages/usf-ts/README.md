# @universal-skills/core

TypeScript / JavaScript implementation of the Universal Skills Framework.

```
npm install @universal-skills/core
```

```ts
import { load } from "@universal-skills/core";

const skill = await load("skills/code-reviewer.md");
const payload = skill.render("openai", { code: "console.log(1)" });
```

Full docs at the [repo root](https://github.com/coentraojpt/universal-skills).
