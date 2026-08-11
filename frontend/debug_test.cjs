const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
  page.on('pageerror', err => console.log('BROWSER ERROR:', err));
  
  page.on('request', request => console.log('>>', request.method(), request.url()));
  page.on('response', response => console.log('<<', response.status(), response.url()));

  await page.addInitScript(() => {
    localStorage.setItem('applysense_auth', JSON.stringify({
      access_token: 'test-token',
      refresh_token: 'test-token',
      user: { email: 'test@example.com' }
    }));
  });

  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
  };

  await page.route('**/api/**', async (route) => {
    if (route.request().method() === 'OPTIONS') {
      await route.fulfill({ status: 200, headers: corsHeaders });
    } else {
      await route.continue();
    }
  });

  await page.route('**/api/auth/me/', async (route) => {
    if (route.request().method() === 'OPTIONS') return;
    await route.fulfill({
      status: 200, contentType: 'application/json', headers: corsHeaders,
      body: JSON.stringify({ id: 1, email: 'test@example.com', role: 'user' }),
    });
  });

  await page.route('**/api/applications/analytics/', async (route) => {
    if (route.request().method() === 'OPTIONS') return;
    await route.fulfill({
      status: 200, contentType: 'application/json', headers: corsHeaders,
      body: JSON.stringify({ total_applications: 10, status_breakdown: {}, average_match_score: 85 })
    });
  });

  await page.route('**/api/jobs/recommendations/', async (route) => {
    if (route.request().method() === 'OPTIONS') return;
    await route.fulfill({ status: 200, contentType: 'application/json', headers: corsHeaders, body: '[]' });
  });

  await page.route('**/api/automation/auto-apply/config/', async (route) => {
    if (route.request().method() === 'OPTIONS') return;
    await route.fulfill({
      status: 200, contentType: 'application/json', headers: corsHeaders,
      body: JSON.stringify({ auto_apply_enabled: false, daily_limit: 5, weekly_limit: 20, daily_count: 1, weekly_count: 3 })
    });
  });

  await page.route('**/api/automation/auto-apply/runs/', async (route) => {
    if (route.request().method() === 'OPTIONS') return;
    await route.fulfill({ status: 200, contentType: 'application/json', headers: corsHeaders, body: '[]' });
  });

  await page.route('**/api/automation/auto-apply/action-required/', async (route) => {
    if (route.request().method() === 'OPTIONS') return;
    await route.fulfill({ status: 200, contentType: 'application/json', headers: corsHeaders, body: '[]' });
  });

  await page.goto('http://localhost:3000/dashboard');
  await page.waitForTimeout(2000);
  console.log(await page.content());
  await browser.close();
})();
