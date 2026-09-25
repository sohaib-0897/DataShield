const { test, expect } = require('@playwright/test');

test('demo admin can investigate an alert, record a decision, and review reports and model status', async ({ page }) => {
  const password = process.env.DATASHIELD_DEMO_ADMIN_PASSWORD;
  test.skip(!password, 'Set DATASHIELD_DEMO_ADMIN_PASSWORD after running scripts/demo/seed_demo.py');

  await page.goto('/login');
  await page.getByLabel('Username').fill('demo.admin');
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page.getByRole('heading', { name: 'Security overview' })).toBeVisible();
  await page.getByRole('link', { name: 'Alerts', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Alerts', exact: true })).toBeVisible();
  const investigate = page.getByRole('link', { name: 'Investigate' }).first();
  await expect(investigate).toBeVisible();
  await investigate.click();

  await expect(page.getByRole('heading', { name: 'Alert investigation' })).toBeVisible();
  await expect(page.getByText('Identity', { exact: true })).toBeVisible();
  await expect(page.getByText('Risk assessment', { exact: true })).toBeVisible();
  await expect(page.getByText('Analysis sources', { exact: true })).toBeVisible();
  await expect(page.getByText('Evidence and sensitive detections', { exact: true })).toBeVisible();
  await expect(page.getByText('Supporting event timeline', { exact: true })).toBeVisible();
  await expect(page.getByText(/synthetic\.employee/)).toBeVisible();
  await expect(page.getByText('Endpoint: synthetic-workstation')).toBeVisible();
  await expect(page.getByText('Hostname: synthetic-workstation')).toBeVisible();
  await expect(page.getByText(/Channel: upload|Channel: usb/i)).toBeVisible();
  await expect(page.getByText(/Risk assessment/)).toBeVisible();
  await expect(page.getByText(/HEURISTIC/).first()).toBeVisible();
  await expect(page.getByText(/sensitive/).first()).toBeVisible();

  await page.getByLabel('Decision notes').fill('Synthetic FYP demo review');
  page.once('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'BLOCK' }).click();
  await expect(page.getByText('BLOCKED', { exact: true }).first()).toBeVisible();

  await page.getByRole('link', { name: 'Audit log' }).click();
  await expect(page.getByRole('heading', { name: 'Audit log' })).toBeVisible();
  await expect(page.getByText('ALERT_DECISION').first()).toBeVisible();

  await page.getByRole('link', { name: 'Reports' }).click();
  await expect(page.getByRole('heading', { name: 'Reports' })).toBeVisible();
  await expect(page.getByText('Alerts over time')).toBeVisible();
  await expect(page.getByText('Event volume')).toBeVisible();
  await expect(page.getByText('Analyst decisions')).toBeVisible();

  await page.getByRole('link', { name: 'System status' }).click();
  await expect(page.getByRole('heading', { name: 'System status' })).toBeVisible();
  await expect(page.getByText('Release: 0.9.0-pre-cert')).toBeVisible();
  await expect(page.getByText('HEURISTIC', { exact: true })).toBeVisible();
  await expect(page.getByText('Not available', { exact: true })).toBeVisible();
  await expect(page.getByText(/patterns-v1/)).toBeVisible();

  await page.getByRole('link', { name: 'User activity' }).click();
  await expect(page.getByRole('heading', { name: 'User activity' })).toBeVisible();
  await page.getByRole('button', { name: /synthetic\.employee/ }).click();
  await expect(page.getByText('Latest risk', { exact: true })).toBeVisible();
  await expect(page.getByText('Channels used', { exact: true })).toBeVisible();
  await expect(page.getByText('Recent alerts', { exact: true })).toBeVisible();

  await page.getByRole('link', { name: 'Policies' }).click();
  await expect(page.getByRole('heading', { name: 'Policy settings' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Save policy' })).toBeVisible();
});
