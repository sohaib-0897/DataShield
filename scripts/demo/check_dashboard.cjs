// Read-only browser tour of the disposable showcase session. No decisions/policy writes.
const fs = require('fs');
const path = require('path');
const {chromium, expect} = require('../../frontend/node_modules/@playwright/test');
const root = path.resolve(__dirname, '../..');
const name = process.argv[2] || 'showcase';
if (!/^[a-zA-Z0-9_-]+$/.test(name)) throw new Error('Invalid demo session name');
const folder = path.join(root, '.local/demo', name);
const config = JSON.parse(fs.readFileSync(path.join(folder, 'config.json'), 'utf8'));
let browser;
(async () => {
  browser = await chromium.launch({
    executablePath: process.env.DATASHIELD_DEMO_CHROME || '/opt/google/chrome/chrome',
    headless: true,
  });
  const page = await browser.newPage({viewport: {width: 1440, height: 900}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => {
    if (response.url().includes('/api/v1/') && response.status() >= 400)
      errors.push(`${response.status()} ${new URL(response.url()).pathname}`);
  });
  await page.goto('http://localhost:3101/login', {waitUntil: 'networkidle'});
  await page.getByLabel('Username').fill('demo.admin');
  await page.getByLabel('Password').fill(config.DATASHIELD_DEMO_ADMIN_PASSWORD);
  await page.getByRole('button', {name: 'Sign in'}).click();
  await expect(page.getByRole('heading', {name: 'Security overview'})).toBeVisible();
  await page.screenshot({path: path.join(folder, 'dashboard.png'), fullPage: true});
  await page.getByRole('link', {name: 'Alerts', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Alerts', exact: true})).toBeVisible();
  await page.getByRole('link', {name: 'Investigate'}).first().click();
  await expect(page.getByRole('heading', {name: 'Alert investigation'})).toBeVisible();
  await expect(page.getByText('Evidence and sensitive detections', {exact: true})).toBeVisible();
  await expect(page.getByText('HEURISTIC').first()).toBeVisible();
  for (const [link, heading] of [['Reports', 'Reports'], ['System status', 'System status'],
                                ['User activity', 'User activity'], ['Policies', 'Policy settings'],
                                ['Audit log', 'Audit log']]) {
    await page.getByRole('link', {name: link, exact: true}).click();
    await expect(page.getByRole('heading', {name: heading, exact: true})).toBeVisible();
    if (link === 'System status') {
      await expect(page.getByText('HEURISTIC', {exact: true})).toBeVisible();
      await expect(page.getByText(/patterns-v1/)).toBeVisible();
    }
    if (link === 'User activity') {
      await page.getByRole('button', {name: /synthetic\.employee/}).click();
      await expect(page.getByText('Latest risk', {exact: true})).toBeVisible();
      await page.getByRole('button', {name: /synthetic\.demo\.monitor/}).click();
      await expect(page.getByText(/FILE_MOVE/).first()).toBeVisible();
      await expect(page.getByText('INSUFFICIENT_HISTORY', {exact: true}).first()).toBeVisible();
      await page.screenshot({path: path.join(folder, 'monitor-timeline.png'), fullPage: true});
    }
  }
  if (errors.length) throw new Error('Browser/API errors: ' + errors.join('; '));
  const result = {browser_login: true, overview: true, alert_investigation: true,
    reports: true, system_status: true, user_activity: true, native_file_move_timeline: true, policies: true, audit: true,
    browser_errors: 0, policy_or_decision_writes: 0};
  fs.writeFileSync(path.join(folder, 'browser-verification.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
})().catch(error => {console.error(error.message); process.exitCode = 1;})
  .finally(async () => {if (browser) await browser.close();});
