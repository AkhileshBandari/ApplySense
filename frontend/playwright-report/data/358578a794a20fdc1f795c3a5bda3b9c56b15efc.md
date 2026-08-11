# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auto_apply.spec.ts >> Auto Apply Control Center >> renders recent runs widget
- Location: tests\auto_apply.spec.ts:226:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=Recent Auto Apply Runs')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('text=Recent Auto Apply Runs')

```

```yaml
- complementary:
  - text: A ApplySense.AI
  - navigation:
    - button "Dashboard":
      - img
      - text: Dashboard
    - button "Smart Job Feed":
      - img
      - text: Smart Job Feed
    - button "Applications":
      - img
      - text: Applications
    - button "Profile":
      - img
      - text: Profile
    - button "Resumes":
      - img
      - text: Resumes
    - button "Career Growth":
      - img
      - text: Career Growth
    - button "Evidence & Intelligence":
      - img
      - text: Evidence & Intelligence
    - button "AI Career Coach":
      - img
      - text: AI Career Coach
    - button "Career Brand":
      - img
      - text: Career Brand
    - button "Interview Intelligence":
      - img
      - text: Interview Intelligence
    - button "Action Planner":
      - img
      - text: Action Planner
    - button "Execution Plan":
      - img
      - text: Execution Plan
    - button "OS Dashboard":
      - img
      - text: OS Dashboard
    - button "Ops Dashboard":
      - img
      - text: Ops Dashboard
    - button "Career Outcomes":
      - img
      - text: Career Outcomes
  - button "Logout":
    - img
    - text: Logout
- main:
  - img
  - heading "Action Required" [level=2]:
    - img
    - text: Action Required
  - paragraph: The Auto Apply engine encountered security checks (e.g. CAPTCHAs, OTPs) that require your manual input.
  - text: CAPTCHA REQUIRED
  - img
  - text: 8/11/2026, 3:04:31 PM
  - paragraph: Frontend Developer @ Web Inc
  - link "Complete Manually":
    - /url: http://example.com/job
    - text: Complete Manually
    - img
  - heading "Auto Apply Engine" [level=2]:
    - img
    - text: Auto Apply Engine
  - paragraph: Control your automated application settings
  - button "Enable Auto Apply":
    - img
    - text: Enable Auto Apply
  - text: Daily Limit
  - spinbutton: "5"
  - paragraph: "Used today: 1 / 5"
  - text: Weekly Limit
  - spinbutton: "20"
  - paragraph: "Used this week: 3 / 20"
  - button "Save Limits":
    - img
    - text: Save Limits
  - text: Time Range
  - combobox:
    - option "Last 7 Days"
    - option "Last 30 Days" [selected]
    - option "Last 90 Days"
    - option "Last 6 Months"
    - option "Last 1 Year"
    - option "All Time"
  - text: Source
  - combobox:
    - option "All Sources" [selected]
    - option "LinkedIn"
    - option "Indeed"
    - option "Naukri"
  - text: Provider
  - combobox:
    - option "All Providers" [selected]
    - option "Greenhouse"
    - option "Lever"
    - option "Ashby"
    - option "Workday"
  - text: Network Error
  - button "Add New Application":
    - img
    - text: Add New Application
  - button "View Calendar":
    - img
    - text: View Calendar
  - button "View Offers":
    - img
    - text: View Offers
  - button "Refresh Data":
    - img
    - text: Refresh Data
```

# Test source

```ts
  127 |             job_url: 'http://example.com/job',
  128 |             created_at: new Date().toISOString()
  129 |           }
  130 |         ])
  131 |       });
  132 |     });
  133 | 
  134 |     // Mock the health automation
  135 |     await page.route('**/api/health/automation/', async (route) => {
  136 |       if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
  137 |       await route.fulfill({
  138 |         status: 200,
  139 |         contentType: 'application/json',
  140 |         headers: corsHeaders,
  141 |         body: JSON.stringify({ status: 'ok', workers: 2 })
  142 |       });
  143 |     });
  144 | 
  145 |     // Navigate to dashboard
  146 |     await page.goto('http://localhost:3000/dashboard');
  147 |   });
  148 | 
  149 |   test('renders the Auto Apply Control Center and limits', async ({ page }) => {
  150 |     await expect(page.locator('h2:has-text("Auto Apply Engine")').first()).toBeVisible();
  151 |     await expect(page.locator('button:has-text("Enable Auto Apply")').first()).toBeVisible();
  152 |     
  153 |     // Verify limits are displayed
  154 |     await expect(page.locator('input[type="number"]').first()).toHaveValue('5'); // daily limit
  155 |     await expect(page.locator('input[type="number"]').nth(1)).toHaveValue('20'); // weekly limit
  156 |     
  157 |     await expect(page.locator('text=Used today: 1 / 5')).toBeVisible();
  158 |   });
  159 | 
  160 |   test('toggles the auto apply status', async ({ page }) => {
  161 |     // Wait for the button to appear first, using the beforeEach config (disabled)
  162 |     const enableButton = page.locator('button:has-text("Enable Auto Apply")').first();
  163 |     await expect(enableButton).toBeVisible();
  164 | 
  165 |     let enableCalled = false;
  166 |     await page.route('**/api/automation/auto-apply/enable/', async (route) => {
  167 |       if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
  168 |       enableCalled = true;
  169 |       await route.fulfill({ status: 200, headers: { 'Access-Control-Allow-Origin': '*' }, body: '{"status": "Auto Apply Enabled"}' });
  170 |     });
  171 | 
  172 |     // After enabling, config mock should return true
  173 |     await page.route('**/api/automation/auto-apply/config/', async (route) => {
  174 |       if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
  175 |       await route.fulfill({
  176 |         status: 200,
  177 |         contentType: 'application/json',
  178 |         headers: { 'Access-Control-Allow-Origin': '*' },
  179 |         body: JSON.stringify({
  180 |           auto_apply_enabled: true,
  181 |           daily_limit: 5,
  182 |           weekly_limit: 20,
  183 |           daily_count: 1,
  184 |           weekly_count: 3
  185 |         })
  186 |       });
  187 |     });
  188 | 
  189 |     await enableButton.click();
  190 |     expect(enableCalled).toBe(true);
  191 | 
  192 |     // It should now say "Pause Auto Apply"
  193 |     await expect(page.locator('button:has-text("Pause Auto Apply")').first()).toBeVisible();
  194 |   });
  195 | 
  196 |   test('saves new limits', async ({ page }) => {
  197 |     // Wait for the button to appear first, using the beforeEach config
  198 |     const saveButton = page.locator('button:has-text("Save Limits")').first();
  199 |     const dailyInput = page.locator('input[type="number"]').first();
  200 |     await expect(saveButton).toBeVisible();
  201 | 
  202 |     let updateCalled = false;
  203 |     let savedLimits = { daily_limit: 0, weekly_limit: 0 };
  204 |     
  205 |     await page.route('**/api/automation/auto-apply/config/', async (route) => {
  206 |       if (route.request().method() === 'OPTIONS') { await route.fallback(); return; }
  207 |       if (route.request().method() === 'PUT') {
  208 |         updateCalled = true;
  209 |         savedLimits = JSON.parse(route.request().postData() || '{}');
  210 |         await route.fulfill({ status: 200, headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(savedLimits) });
  211 |       } else {
  212 |         await route.fallback();
  213 |       }
  214 |     });
  215 | 
  216 |     // Change daily limit to 10
  217 |     await dailyInput.fill('10');
  218 |     
  219 |     await saveButton.click();
  220 |     
  221 |     expect(updateCalled).toBe(true);
  222 |     expect(savedLimits.daily_limit).toBe(10);
  223 |     expect(savedLimits.weekly_limit).toBe(20);
  224 |   });
  225 | 
  226 |   test('renders recent runs widget', async ({ page }) => {
> 227 |     await expect(page.locator('text=Recent Auto Apply Runs')).toBeVisible();
      |                                                               ^ Error: expect(locator).toBeVisible() failed
  228 |     await expect(page.locator('text=Software Engineer')).toBeVisible();
  229 |     await expect(page.locator('text=Tech Corp')).toBeVisible();
  230 |     await expect(page.locator('text=CAPTCHA detected')).toBeVisible();
  231 |   });
  232 | 
  233 |   test('renders user action required widget', async ({ page }) => {
  234 |     await expect(page.locator('h2:has-text("Action Required")')).toBeVisible();
  235 |     await expect(page.locator('text=CAPTCHA REQUIRED')).toBeVisible();
  236 |     
  237 |     const manualBtn = page.locator('a:has-text("Complete Manually")');
  238 |     await expect(manualBtn).toBeVisible();
  239 |     await expect(manualBtn).toHaveAttribute('href', 'http://example.com/job');
  240 |   });
  241 | 
  242 | });
  243 | 
```