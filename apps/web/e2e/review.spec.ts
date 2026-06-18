import { Page, expect, test } from "@playwright/test";

function sample(page: Page, name: string) {
  return page.locator(".sample-chip", { hasText: name });
}

function runReview(page: Page) {
  return page.locator(".header-run").click();
}

test.describe("Podscope review workspace", () => {
  test("loads the homepage", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Review" })).toBeVisible();
    await expect(page.locator(".header-run")).toBeVisible();
  });

  test("risky sample produces a failing score and findings", async ({ page }) => {
    await page.goto("/");
    await sample(page, "Risky web stack").click();
    await runReview(page);

    await expect(page.locator(".score-value")).toBeVisible();
    await expect(page.locator(".status-chip")).toContainText(/Blocked/);

    const score = Number(await page.locator(".score-value").innerText());
    expect(score).toBeLessThan(60);

    await expect(page.locator(".finding-card").first()).toBeVisible();
    await expect(page.locator(".severity-cell.sev-critical strong")).not.toHaveText("0");
  });

  test("shows a suggested fix and severity filter works", async ({ page }) => {
    await page.goto("/");
    await sample(page, "Risky web stack").click();
    await runReview(page);
    await expect(page.locator(".finding-card").first()).toBeVisible();

    await page.locator(".severity-cell.sev-critical").click();
    await expect(page.locator(".clear-filter")).toBeVisible();

    await page.locator(".finding-card .finding-head").first().click();
    await expect(page.locator(".finding-fix pre").first()).toBeVisible();
  });

  test("hardened sample scores better than risky", async ({ page }) => {
    await page.goto("/");
    await sample(page, "Risky web stack").click();
    await runReview(page);
    await expect(page.locator(".score-value")).toBeVisible();
    const risky = Number(await page.locator(".score-value").innerText());

    await sample(page, "Hardened web stack").click();
    await runReview(page);
    await expect(page.locator(".status-chip")).toContainText(/Deployable/);
    const hardened = Number(await page.locator(".score-value").innerText());

    expect(hardened).toBeGreaterThan(risky);
  });

  test("assistant tab generates a deterministic summary", async ({ page }) => {
    await page.goto("/");
    await sample(page, "Risky web stack").click();
    await runReview(page);
    await expect(page.locator(".score-value")).toBeVisible();

    await page.getByRole("button", { name: /^Assistant/ }).click();
    await page.getByRole("button", { name: /^Generate$/ }).click();
    await expect(page.locator(".ai-headline")).toContainText(/Podscope score/);
  });
});
