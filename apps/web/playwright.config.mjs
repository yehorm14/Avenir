import { defineConfig } from "@playwright/test";

const baseURL = "http://127.0.0.1:4275";

export default defineConfig({
  testDir: "./browser",
  workers: 1,
  use: { baseURL },
  webServer: {
    command: "node ../../scripts/run-app.mjs --production",
    url: `${baseURL}/health`,
    env: {
      AVENIR_PORT: "4275",
      LLM_BASE_URL: "",
      LLM_API_KEY: "",
      LLM_MODEL: "",
      ANTHROPIC_API_KEY: "",
      OPENAI_API_KEY: "",
    },
  },
});
