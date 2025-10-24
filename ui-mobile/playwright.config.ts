import { defineConfig } from '@playwright/test';
export default defineConfig({
  retries: 2,
  use: { trace: 'retain-on-failure', video: 'retain-on-failure', screenshot: 'only-on-failure' },
  outputDir: 'test-artifacts'
});