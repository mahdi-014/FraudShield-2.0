import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.mock.spec.ts',
  timeout: 30000,
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'retain-on-failure',
    launchOptions: process.env.PLAYWRIGHT_BROWSER_EXECUTABLE
      ? { executablePath: process.env.PLAYWRIGHT_BROWSER_EXECUTABLE } : {},
  },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 4173 --strictPort',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: false,
  },
});
