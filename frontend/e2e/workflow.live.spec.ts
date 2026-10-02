// Live browser + backend + model + PostgreSQL verification. No API fixtures.
import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

test('live analyst release/reject, persistence and audit workflow', async ({ page, request }) => {
  const api = process.env.FRAUDSHIELD_URL;
  const service = process.env.FRAUDSHIELD_SERVICE_KEY;
  const analyst = process.env.FRAUDSHIELD_ANALYST_KEY;
  if (!api || !service || !analyst) throw new Error('Run scripts/verify_m31.py --browser to provision the isolated workflow');
  const sample = JSON.parse(fs.readFileSync(path.resolve('../artifacts/sample_fraud.json'), 'utf8'));
  for (const action of ['release', 'reject'] as const) {
    const reference = 'browser-' + crypto.randomUUID();
    const submit = await request.post(api + '/v1/transactions', {
      headers: { Authorization: `Bearer ${service}`, 'Idempotency-Key': reference },
      data: { client_transaction_id: reference, features: sample.features },
    });
    expect(submit.status()).toBe(201);
    const tx = await submit.json();
    expect(tx.model_score).toBeCloseTo(0.8057, 4);
    expect(tx.status).toBe('held_for_review');
    await page.goto('/');
    await page.locator('#btn-prompt-signin').click();
    await page.locator('#analyst-token-input').fill(analyst);
    await page.locator('#btn-analyst-signin').click();
    await expect(page.getByText('Client Ref: ' + reference, { exact: true })).toBeVisible();
    await page.locator('#btn-case-' + action).click();
    const reason = 'Simulated live browser analyst decision: ' + action;
    await page.locator('#action-reason-input').fill(reason);
    await page.locator('#btn-confirm-action').click();
    await expect(page.getByText(action === 'release' ? 'Terminal State: Released' : 'Terminal State: Rejected')).toBeVisible();
    await page.getByRole('button', { name: 'Audit Trail', exact: true }).click();
    await expect(page.getByText(reason, { exact: true })).toBeVisible();
    await expect(page.getByText('Audit History (2 Events)')).toBeVisible();
    const persisted = await request.get(api + '/v1/transactions/' + tx.id, {
      headers: { Authorization: `Bearer ${analyst}` },
    });
    expect((await persisted.json()).status).toBe(action === 'release' ? 'completed' : 'rejected');
    await page.getByRole('button', { name: 'Sign Out' }).click();
    await expect(page.getByText('Analyst Sign In Required')).toBeVisible();
  }
});
