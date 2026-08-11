import { test, expect } from '@playwright/test';

test.describe('Auto Apply Control Center', () => {
  
  test.beforeEach(async ({ page }) => {
    page.on('request', request => console.log('>>', request.method(), request.url()));
    page.on('response', response => console.log('<<', response.status(), response.url()));
    page.on('console', msg => console.log('LOG:', msg.text()));

    // Mock local storage auth state so we don't redirect to /login
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

    // Handle OPTIONS requests for all API endpoints
    await page.route('**/api/**', async (route) => {
      if (route.request().method() === 'OPTIONS') {
        await route.fulfill({ status: 200, headers: corsHeaders });
      } else {
        await route.continue();
      }
    });

    // Mock auth/me so AuthContext thinks we're logged in
    await page.route('**/api/auth/me/', async (route) => {
      if (route.request().method() === 'OPTIONS') { await route.fallback(); return; } // Handled by fallback
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: corsHeaders,
        body: JSON.stringify({ id: 1, email: 'test@example.com', role: 'user' }),
      });
    });

    // Mock the APIs for dashboard analytics
    await page.route('**/api/applications/analytics/', async (route) => {
      if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: corsHeaders,
        body: JSON.stringify({
          total_applications: 10,
          status_breakdown: { Saved: 2, Interview: 1, Offer: 0 },
          average_match_score: 85
        })
      });
    });

    await page.route('**/api/jobs/recommendations/', async (route) => {
      if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: corsHeaders,
        body: JSON.stringify([])
      });
    });

    // Mock the initial config
    await page.route('**/api/automation/auto-apply/config/', async (route) => {
      if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: corsHeaders,
        body: JSON.stringify({
          auto_apply_enabled: false,
          daily_limit: 5,
          weekly_limit: 20,
          daily_count: 1,
          weekly_count: 3
        })
      });
    });

    // Mock the runs list
    await page.route('**/api/automation/auto-apply/runs/', async (route) => {
      if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: corsHeaders,
        body: JSON.stringify([
          {
            id: 1,
            status: 'SUCCESS',
            job_title: 'Software Engineer',
            job_company: 'Tech Corp',
            created_at: new Date().toISOString()
          },
          {
            id: 2,
            status: 'USER_ACTION_REQUIRED',
            job_title: 'Frontend Developer',
            job_company: 'Web Inc',
            failure_reason: 'CAPTCHA detected',
            created_at: new Date().toISOString()
          }
        ])
      });
    });

    // Mock the action required list
    await page.route('**/api/automation/auto-apply/action-required/', async (route) => {
      if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: corsHeaders,
        body: JSON.stringify([
          {
            id: 1,
            action_type: 'CAPTCHA_REQUIRED',
            job_title: 'Frontend Developer',
            job_company: 'Web Inc',
            job_url: 'http://example.com/job',
            created_at: new Date().toISOString()
          }
        ])
      });
    });

    // Mock the health automation
    await page.route('**/api/health/automation/', async (route) => {
      if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: corsHeaders,
        body: JSON.stringify({ status: 'ok', workers: 2 })
      });
    });

    // Navigate to dashboard
    await page.goto('http://localhost:3000/dashboard');
  });

  test('renders the Auto Apply Control Center and limits', async ({ page }) => {
    await expect(page.locator('h2:has-text("Auto Apply Engine")').first()).toBeVisible();
    await expect(page.locator('button:has-text("Enable Auto Apply")').first()).toBeVisible();
    
    // Verify limits are displayed
    await expect(page.locator('input[type="number"]').first()).toHaveValue('5'); // daily limit
    await expect(page.locator('input[type="number"]').nth(1)).toHaveValue('20'); // weekly limit
    
    await expect(page.locator('text=Used today: 1 / 5')).toBeVisible();
  });

  test('toggles the auto apply status', async ({ page }) => {
    // Wait for the button to appear first, using the beforeEach config (disabled)
    const enableButton = page.locator('button:has-text("Enable Auto Apply")').first();
    await expect(enableButton).toBeVisible();

    let enableCalled = false;
    await page.route('**/api/automation/auto-apply/enable/', async (route) => {
      if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
      enableCalled = true;
      await route.fulfill({ status: 200, headers: { 'Access-Control-Allow-Origin': '*' }, body: '{"status": "Auto Apply Enabled"}' });
    });

    // After enabling, config mock should return true
    await page.route('**/api/automation/auto-apply/config/', async (route) => {
      if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({
          auto_apply_enabled: true,
          daily_limit: 5,
          weekly_limit: 20,
          daily_count: 1,
          weekly_count: 3
        })
      });
    });

    await enableButton.click();
    expect(enableCalled).toBe(true);

    // It should now say "Pause Auto Apply"
    await expect(page.locator('button:has-text("Pause Auto Apply")').first()).toBeVisible();
  });

  test('saves new limits', async ({ page }) => {
    // Wait for the button to appear first, using the beforeEach config
    const saveButton = page.locator('button:has-text("Save Limits")').first();
    const dailyInput = page.locator('input[type="number"]').first();
    await expect(saveButton).toBeVisible();

    let updateCalled = false;
    let savedLimits = { daily_limit: 0, weekly_limit: 0 };
    
    await page.route('**/api/automation/auto-apply/config/', async (route) => {
      if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
      if (route.request().method() === 'PUT') {
        updateCalled = true;
        savedLimits = JSON.parse(route.request().postData() || '{}');
        await route.fulfill({ status: 200, headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(savedLimits) });
      } else {
        await route.fallback();
      }
    });

    // Change daily limit to 10
    await dailyInput.fill('10');
    
    await saveButton.click();
    
    expect(updateCalled).toBe(true);
    expect(savedLimits.daily_limit).toBe(10);
    expect(savedLimits.weekly_limit).toBe(20);
  });

  test('renders recent runs widget', async ({ page }) => {
    await expect(page.locator('text=Recent Auto Apply Runs')).toBeVisible();
    await expect(page.locator('text=Software Engineer')).toBeVisible();
    await expect(page.locator('text=Tech Corp')).toBeVisible();
    await expect(page.locator('text=CAPTCHA detected')).toBeVisible();
  });

  test('renders user action required widget', async ({ page }) => {
    await expect(page.locator('h2:has-text("Action Required")')).toBeVisible();
    await expect(page.locator('text=CAPTCHA REQUIRED')).toBeVisible();
    
    const manualBtn = page.locator('a:has-text("Complete Manually")');
    await expect(manualBtn).toBeVisible();
    await expect(manualBtn).toHaveAttribute('href', 'http://example.com/job');
  });

});
