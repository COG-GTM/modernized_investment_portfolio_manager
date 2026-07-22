import { test, expect } from '@playwright/test';

const VALID_ACCOUNT = '1234567890';
const EXPECTED_HOLDINGS = ['AAPL', 'MSFT', 'GOOGL', 'TSLA'];

test.describe('Portfolio Inquiry', () => {
  test('happy path: valid account shows portfolio summary with holdings', async ({ page }) => {
    await page.goto('/portfolio-inquiry');
    await expect(page.getByRole('heading', { name: 'Portfolio Inquiry' })).toBeVisible();

    await page.getByLabel('Account Number').fill(VALID_ACCOUNT);
    await page.getByRole('button', { name: 'View Portfolio' }).click();

    await expect(page.getByRole('heading', { name: 'Portfolio Details' })).toBeVisible();
    await expect(page.getByText(`Account: ${VALID_ACCOUNT}`)).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Holdings' })).toBeVisible();

    for (const symbol of EXPECTED_HOLDINGS) {
      await expect(page.getByText(symbol, { exact: true })).toBeVisible();
    }
  });

  test('validation error: invalid account shows error and no holdings', async ({ page }) => {
    await page.goto('/portfolio-inquiry');

    const input = page.getByLabel('Account Number');
    await input.fill('12345');

    await expect(page.getByRole('alert')).toHaveText('Account number must be exactly 10 digits');
    await expect(page.getByRole('button', { name: 'View Portfolio' })).toBeDisabled();
    await expect(page.getByRole('heading', { name: 'Holdings' })).not.toBeVisible();

    await input.fill('12345abcde');
    await expect(page.getByRole('alert')).toHaveText('Account number must contain only numeric characters');
    await expect(page.getByRole('button', { name: 'View Portfolio' })).toBeDisabled();
    await expect(page.getByRole('heading', { name: 'Holdings' })).not.toBeVisible();
  });

  test('transaction history: navigate from a valid inquiry', async ({ page }) => {
    await page.goto('/portfolio-inquiry');
    await page.getByLabel('Account Number').fill(VALID_ACCOUNT);
    await page.getByRole('button', { name: 'View Portfolio' }).click();
    await expect(page.getByRole('heading', { name: 'Portfolio Details' })).toBeVisible();

    await page.getByRole('button', { name: 'View Transaction History' }).click();

    await expect(page).toHaveURL(new RegExp(`/transaction-history\\?account=${VALID_ACCOUNT}`));
    await expect(page.getByRole('heading', { name: 'Transaction History' })).toBeVisible();
    await expect(page.getByText(`Transactions for Account ${VALID_ACCOUNT}`)).toBeVisible();
  });
});
