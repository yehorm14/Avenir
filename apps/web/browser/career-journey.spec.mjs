import { expect, test } from "@playwright/test";

test.use({ viewport: { width: 390, height: 844 } });

test("a keyboard user can inspect evidence, save a plan and try the warned example", async ({
  page,
}) => {
  await page.goto("/");
  const hero = page.getByRole("region", { name: "Sample evidence comparison" });
  await expect(hero).toContainText("Employment trend vs typical, per year");
  await expect(hero).toContainText("ONS ASHE · 2022");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(
    390,
  );

  const compare = page.getByRole("button", { name: /Try a sample comparison/ });
  for (let step = 0; step < 20; step += 1) {
    if (await compare.evaluate((element) => element === document.activeElement))
      break;
    await page.keyboard.press("Tab");
  }
  await expect(compare).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("button", { name: "Compare careers" }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Evidence", exact: true }).click();
  await page.getByRole("button", { name: "Build my plan" }).first().click();
  await page.goto("/#/discover");

  const resume = page.getByRole("button", { name: /Review my plan/ });
  const exampleRequest = page.getByRole("button", {
    name: /Read about Amira.s example profile/,
  });
  await exampleRequest.press("Enter");
  const card = page.getByRole("article", { name: "Amira, 17, S6 in Glasgow" });
  await expect(card).toBeFocused();
  await expect(card).toContainText("This replaces your current career choices");
  await resume.click();
  await expect(page.getByRole("heading", { name: "My plan" })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /Software develop/ }),
  ).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download plan" }).click();
  expect((await download).suggestedFilename()).toMatch(/\.html$/);

  await page.goto("/#/discover");
  await page
    .getByRole("button", { name: /Use Amira.s example profile/ })
    .click();
  const guide = page.getByRole("complementary", { name: "Example profile" });
  await expect(guide).toContainText("Example profile: Amira");
  await guide.getByRole("button", { name: "Compare the evidence" }).click();
  await expect(
    guide.getByRole("button", { name: "Compare the evidence" }),
  ).toHaveAttribute("aria-current", "step");
  await guide.getByRole("button", { name: "Your plan" }).click();
  await expect(page.getByRole("heading", { name: "My plan" })).toBeVisible();
  await guide.getByRole("button", { name: "Start a fresh session" }).click();
  await expect(guide).toHaveCount(0);
  await resume.click();
  await expect(
    page.getByRole("heading", { name: "A little discovery comes first." }),
  ).toBeVisible();
});

test("a failed example request raises one alert and allows a retry", async ({
  page,
}) => {
  await page.route(
    "**/api/discovery",
    (route) =>
      route.fulfill({
        status: 503,
        json: { detail: "The example is temporarily unavailable." },
      }),
    { times: 1 },
  );
  await page.goto("/");
  const start = page.getByRole("button", {
    name: /Use Amira.s example profile/,
  });
  await start.click();
  await expect(page.getByRole("alert")).toHaveCount(1);
  await expect(page.getByRole("alert")).toHaveText(
    "The example is temporarily unavailable.",
  );
  await expect(start).toBeEnabled();
  await start.click();
  await expect(
    page.getByRole("complementary", { name: "Example profile" }),
  ).toContainText("Example profile: Amira");
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("missing role data keeps the market available at 320 px", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.route("**/api/bootstrap", async (route) => {
    const response = await route.fetch();
    const result = await response.json();
    result.data.careers = result.data.careers.filter(
      (career) => career.soc !== "2134",
    );
    await route.fulfill({ response, json: result });
  });
  await page.goto("/");
  const hero = page.getByRole("region", { name: "Sample evidence comparison" });
  await expect(hero.getByRole("status")).toContainText(
    "The sample figures are not available right now.",
  );
  await expect(hero.getByRole("table")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(
    320,
  );
  await hero.getByRole("button", { name: "Analyse the job market" }).click();
  await expect(
    page.getByRole("heading", { name: "Jobs", exact: true }).first(),
  ).toBeVisible();
});
