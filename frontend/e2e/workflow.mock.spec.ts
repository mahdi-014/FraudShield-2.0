// Real browser UI regression tests with explicit API fixtures, not live DB E2E.
import { test, expect, type Page } from '@playwright/test';

const token = 'browser-test-analyst-token-32characters';
function caseFixture(id: string) {
  return {
    id, transaction_id: 'tx-' + id, status: 'open', resolution: null as string | null,
    created_at: '2026-10-02T00:00:00Z', updated_at: '2026-10-02T00:00:00Z',
    transaction: {
      id: 'tx-' + id, client_transaction_id: 'DEMO-' + id,
      service_actor: 'checkout_service', model_score: 0.80569,
      recommended_action: 'hold', status: 'held_for_review', version: 1,
      model_version: 'fixture-v1', policy_version: 'fixture-v1', schema_version: 'fixture-v1',
      features: { TransactionAmt: 46.725 }, model_factors: [],
      policy_reasons: ['Fixture risk policy'], created_at: '2026-10-02T00:00:00Z',
    },
  };
}

async function setup(page: Page) {
  const state = {
    cases: [caseFixture('case-one'), caseFixture('case-two')],
    expired: false, outage: false, conflict: false, actionCount: 0,
  };
  await page.route('**/health/ready', route => route.fulfill({ json: {
    status: 'ready', database: 'connected', mode: 'historical_dataset_replay',
  }}));
  await page.route('**/v1/**', async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    if (state.expired) return route.fulfill({ status: 401, json: { detail: 'Expired test credential' }});
    if (path === '/v1/auth/me') return route.fulfill({ json: { identity: 'analyst_test', role: 'analyst' }});
    if (state.outage) return route.fulfill({ status: 503, json: { detail: 'Database service is unavailable.' }});
    if (path === '/v1/cases') {
      let items = state.cases;
      const status = url.searchParams.get('status');
      if (status) items = items.filter(item => item.status === status);
      return route.fulfill({ json: { items, total: items.length, limit: 10, offset: 0 }});
    }
    const action = path.match(/^\/v1\/cases\/([^/]+)\/actions$/);
    if (action) {
      state.actionCount++;
      const item = state.cases.find(item => item.id === action[1])!;
      if (state.conflict) {
        item.transaction.version = 2;
        return route.fulfill({ status: 409, json: { detail: 'Version conflict' }});
      }
      const body = route.request().postDataJSON();
      expect(body.expected_version).toBe(item.transaction.version);
      item.status = 'resolved'; item.resolution = body.action === 'release' ? 'released' : 'rejected';
      item.transaction.status = body.action === 'release' ? 'completed' : 'rejected';
      item.transaction.version++;
      return route.fulfill({ json: { case: item, transaction: item.transaction, message: 'Resolved' }});
    }
    const detail = path.match(/^\/v1\/cases\/([^/]+)$/);
    if (detail) return route.fulfill({ json: state.cases.find(item => item.id === detail[1]) });
    if (path.endsWith('/audit')) return route.fulfill({ json: { audit_events: [{
      id: 'event-' + path, event_type: 'ANALYST_ACTION', actor: 'analyst_test',
      actor_role: 'analyst', action: 'release', resulting_status: 'completed',
      reason: 'Simulated browser fixture ' + path, created_at: '2026-10-02T00:00:00Z',
    }] }});
    return route.fulfill({ status: 404, json: { detail: 'Fixture not found' }});
  });
  return state;
}

async function login(page: Page) {
  await page.goto('/');
  await page.locator('#btn-prompt-signin').click();
  await page.locator('#analyst-token-input').fill(token);
  await page.locator('#btn-analyst-signin').click();
  await expect(page.getByText('Client Ref: DEMO-case-one', { exact: true })).toBeVisible();
}

for (const action of ['release', 'reject'] as const) {
  test(`${action}, terminal controls, audit timezone and logout`, async ({ page }) => {
    const state = await setup(page);
    await login(page);
    await page.locator('#btn-case-' + action).click();
    await page.locator('#action-reason-input').fill('Simulated analyst decision');
    await page.locator('#btn-confirm-action').click();
    await expect(page.getByText(action === 'release' ? 'Terminal State: Released' : 'Terminal State: Rejected')).toBeVisible();
    await expect(page.locator('#btn-case-release')).toHaveCount(0);
    expect(state.actionCount).toBe(1);
    await page.getByRole('button', { name: 'Audit Trail', exact: true }).click();
    await expect(page.getByText('Audit History (1 Events)')).toBeVisible();
    await expect(page.getByText(/02 Oct 2026, 06:00:00 \(Asia\/Dhaka\)/).last()).toBeVisible();
    expect(await page.evaluate(() => [localStorage.length, sessionStorage.length])).toEqual([0, 0]);
    await page.getByRole('button', { name: 'Sign Out' }).click();
    await expect(page.getByText('Analyst Sign In Required')).toBeVisible();
    await expect(page.getByText('Client Ref: DEMO-case-one', { exact: true })).toHaveCount(0);
  });
}

test('audit authorization expiry purges session', async ({ page }) => {
  const state = await setup(page); await login(page); state.expired = true;
  await page.getByRole('button', { name: 'Audit Trail', exact: true }).click();
  await expect(page.getByText('Analyst Sign In Required')).toBeVisible();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByText('Client Ref: DEMO-case-one', { exact: true })).toHaveCount(0);
});

test('database outage shows retry state', async ({ page }) => {
  const state = await setup(page); await login(page); state.outage = true;
  await page.getByTitle('Refresh queue').click();
  await expect(page.getByText('Failed to Load Review Queue')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Retry Request' })).toBeVisible();
});

test('stale version conflict refreshes without a second decision', async ({ page }) => {
  const state = await setup(page); await login(page); state.conflict = true;
  await page.locator('#btn-case-release').click();
  await page.locator('#action-reason-input').fill('Simulated analyst decision');
  await page.locator('#btn-confirm-action').click();
  await expect(page.getByText('Tx Version: 2')).toBeVisible();
  expect(state.actionCount).toBe(1);
});

test('late queue response cannot replace a newer filtered result', async ({ page }) => {
  await setup(page); await login(page);
  const stale = caseFixture('stale-case'); stale.status = 'resolved';
  await page.route('**/v1/cases?**', async route => {
    if (new URL(route.request().url()).searchParams.get('status') === 'resolved') {
      await new Promise(resolve => setTimeout(resolve, 400));
      return route.fulfill({ json: { items: [stale], total: 1 }});
    }
    return route.fallback();
  });
  const status = page.locator('select').first();
  const slow = page.waitForRequest(request => request.url().includes('status=resolved'));
  await status.selectOption('resolved'); await slow;
  await status.selectOption('open');
  await expect(page.getByText('Client Ref: DEMO-case-one', { exact: true })).toBeVisible();
  await page.waitForResponse(response => response.url().includes('status=resolved'));
  await expect(page.getByText('Client Ref: DEMO-stale-case', { exact: true })).toHaveCount(0);
});

test('switching cases cancels an old audit and never shows its evidence', async ({ page }) => {
  await setup(page); await login(page);
  let started!: () => void;
  const start = new Promise<void>(resolve => { started = resolve; });
  let finish!: () => void;
  const done = new Promise<void>(resolve => { finish = resolve; });
  await page.route('**/v1/transactions/tx-case-one/audit', async route => {
    started();
    await new Promise(resolve => setTimeout(resolve, 400));
    try {
      await route.fulfill({ json: { audit_events: [{ id: 'old',
        reason: 'OLD_CASE_PRIVATE_EVIDENCE', event_type: 'OLD_CASE',
        created_at: '2026-10-02T00:00:00Z', actor_role: 'analyst',
      }] }});
    } finally { finish(); }
  });
  await page.getByRole('button', { name: 'Audit Trail', exact: true }).click();
  await start;
  await page.getByRole('button', { name: /Ref: DEMO-case-two/ }).click();
  await page.getByRole('button', { name: 'Audit Trail', exact: true }).click();
  await expect(page.getByText(/Simulated browser fixture .*tx-case-two\/audit/)).toBeVisible();
  await done;
  await expect(page.getByText('OLD_CASE_PRIVATE_EVIDENCE')).toHaveCount(0);
});

test('service token is rejected by the analyst console', async ({ page }) => {
  await setup(page);
  await page.route('**/v1/auth/me', route => route.fulfill({ json: {
    identity: 'checkout_test', role: 'service',
  }}));
  await page.goto('/'); await page.locator('#btn-prompt-signin').click();
  await page.locator('#analyst-token-input').fill('browser-service-test-token-32characters');
  await page.locator('#btn-analyst-signin').click();
  await expect(page.getByText(/only 'analyst' credentials can access this console/)).toBeVisible();
  await expect(page.getByText('Analyst Case Queue', { exact: true })).toHaveCount(0);
});
