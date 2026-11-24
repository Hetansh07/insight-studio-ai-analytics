import { expect, test } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

test('loads the dashboard and authenticates in demo mode', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Login to Continue' })).toBeVisible();
  await page.locator('#emailInput').selectOption('user@example.com');
  await page.getByRole('button', { name: 'Continue' }).click();

  await expect(page.getByText('Logged in as user@example.com')).toBeVisible();
  await expect(page.locator('data-quality-dashboard')).toHaveCount(1);
  await expect(page.locator('vanna-chat')).toHaveCount(1);
});

test('health endpoint and dataset API are reachable from the browser context', async ({
  request,
}) => {
  const health = await request.get('/health');
  expect(health.ok()).toBeTruthy();
  expect((await health.json()).status).toBe('healthy');

  const datasets = await request.get('/api/data-quality/datasets');
  expect(datasets.ok()).toBeTruthy();
  expect(Array.isArray((await datasets.json()).datasets)).toBeTruthy();
});

test('runs the data-quality workflow through the dashboard', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Login to Continue' })).toBeVisible();
  await page.locator('#emailInput').selectOption('user@example.com');
  await page.getByRole('button', { name: 'Continue' }).click();

  const dashboard = page.locator('data-quality-dashboard');
  const fileInput = dashboard.locator('#dataset-upload');
  await fileInput.setInputFiles({
    name: 'browser-sales.csv',
    mimeType: 'text/csv',
    buffer: fs.readFileSync(path.resolve(__dirname, '../../../examples/demo_sales.csv')),
  });
  await expect(dashboard.getByText(/Uploaded browser-sales.csv as dataset_/)).toBeVisible();
  const datasetId = await dashboard.locator('input[aria-label="Dataset table"]').inputValue();
  await expect(dashboard.getByText(/Profiled/)).toBeVisible();
  await dashboard.getByRole('button', { name: 'Preview dataset' }).click();
  await expect(dashboard.getByRole('heading', { name: 'Data Preview' })).toBeVisible();
  await expect(dashboard.getByText(/missing cells/)).toBeVisible();
  await dashboard.getByRole('button', { name: 'Data Cleaning' }).click();
  await expect(dashboard.getByRole('heading', { name: 'Cleaning recommendations' })).toBeVisible();

  const recommendation = dashboard.locator('input[type="checkbox"]').first();
  await expect(recommendation).toBeVisible();
  await recommendation.check();
  await dashboard.getByRole('button', { name: 'Preview cleaning' }).click();
  await expect(dashboard.getByText(/Preview:/)).toBeVisible();

  page.once('dialog', dialog => dialog.accept());
  await dashboard.getByRole('button', { name: 'Approve and create version' }).click();
  await expect(dashboard.locator('select[aria-label="Dataset version"] option')).toHaveCount(2);

  const versionSelect = dashboard.locator('select[aria-label="Dataset version"]');
  await versionSelect.selectOption({ index: 0 });
  await expect(versionSelect).toHaveValue(datasetId);

  await dashboard.getByRole('button', { name: 'Version History' }).click();
  const rollback = dashboard.getByRole('button', { name: 'Rollback' }).first();
  if (await rollback.count()) {
    page.once('dialog', dialog => dialog.accept());
    const rollbackResponse = page.waitForResponse(response =>
      response.url().endsWith('/api/data-quality/rollback') && response.request().method() === 'POST',
    );
    await rollback.click();
    expect((await rollbackResponse).ok()).toBeTruthy();
  }

  await expect(page.locator('vanna-chat')).toHaveCount(1);
});

test('shows a dashboard error when a data-quality request fails', async ({ page }) => {
  await page.route('**/api/data-quality/profile/Customer', async route => {
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Data quality is temporarily unavailable' }),
    });
  });

  await page.goto('/');
  await page.getByRole('heading', { name: 'Login to Continue' }).waitFor();
  await page.locator('#emailInput').selectOption('user@example.com');
  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page.getByRole('alert')).toContainText('Data quality is temporarily unavailable');
});

test('opens and closes the floating AI assistant without losing the dashboard', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('heading', { name: 'Login to Continue' }).waitFor();
  await page.locator('#emailInput').selectOption('user@example.com');
  await page.getByRole('button', { name: 'Continue' }).click();

  await expect(page.getByRole('button', { name: 'Ask AI about your data' })).toBeVisible();
  await page.getByRole('button', { name: 'Ask AI about your data' }).click();
  const popup = page.getByRole('dialog', { name: 'AI Data Assistant' });
  await expect(popup).toBeVisible();
  await expect(page.locator('vanna-chat')).toHaveCount(1);
  await expect(page.locator('vanna-chat').getByText('Welcome to Insight Studio')).toBeVisible();
  await expect(
    page.locator('vanna-chat').getByPlaceholder('Ask anything about your data...'),
  ).toBeVisible();
  const popupBox = await popup.boundingBox();
  expect(popupBox).not.toBeNull();
  expect(popupBox!.height).toBeLessThanOrEqual(650);
  const viewportHeight = await page.evaluate(() => window.innerHeight);
  expect(popupBox!.y + popupBox!.height).toBeLessThanOrEqual(viewportHeight);
  await page.getByRole('button', { name: 'Minimize chat' }).click();
  await expect(page.getByRole('button', { name: 'Ask AI about your data' })).toBeVisible();
  await expect(page.locator('data-quality-dashboard')).toBeVisible();
});

test('keeps the compact workspace usable on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/');
  await page.getByRole('heading', { name: 'Login to Continue' }).waitFor();
  await page.locator('#emailInput').selectOption('user@example.com');
  await page.getByRole('button', { name: 'Continue' }).click();

  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.getByRole('button', { name: 'Ask AI about your data' }).click();
  const popup = page.getByRole('dialog', { name: 'AI Data Assistant' });
  await expect(popup).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
});

test('builds an interactive chart from the selected dataset', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('heading', { name: 'Login to Continue' }).waitFor();
  await page.locator('#emailInput').selectOption('user@example.com');
  await page.getByRole('button', { name: 'Continue' }).click();

  const dashboard = page.locator('data-quality-dashboard');
  await dashboard.getByRole('button', { name: 'AI Analytics' }).click();
  await expect(dashboard.getByText('Build an interactive visualization')).toBeVisible();
  await expect(dashboard.getByLabel('Chart type')).toBeVisible();
  await expect(dashboard.getByLabel('X-axis')).toBeVisible();
  await expect(dashboard.getByLabel('Y-axis')).toBeVisible();
  await dashboard.getByRole('button', { name: 'Generate Chart' }).click();
  await expect(dashboard.locator('plotly-chart')).toBeVisible();
  await expect(dashboard.getByText(/plotted rows using/)).toBeVisible();
});
