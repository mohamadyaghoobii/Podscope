import { defineConfig, devices } from "@playwright/test";

const WEB_PORT = process.env.WEB_PORT || "3000";
const API_PORT = process.env.API_PORT || "8000";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    trace: "on-first-retry"
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `python -m uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT}`,
      cwd: "../api",
      url: `http://localhost:${API_PORT}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000
    },
    {
      command: `npm run start -- -p ${WEB_PORT}`,
      url: `http://localhost:${WEB_PORT}`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: { NEXT_PUBLIC_API_BASE_URL: `http://localhost:${API_PORT}` }
    }
  ]
});
