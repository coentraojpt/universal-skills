import { defineConfig } from "vite";
import path from "node:path";

export default defineConfig({
  server: { port: 5173 },
  build: { target: "es2022" },
  resolve: {
    alias: {
      "@universal-skills/core": path.resolve(__dirname, "../../../packages/usf-ts/src/index.ts"),
    },
  },
});
