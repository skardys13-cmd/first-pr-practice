import { chromium } from "playwright";
import path from "path";
const file = "file://" + path.resolve("dist/operations-capacity-model.html");
const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
const page = await browser.newPage({ viewport: { width: 1340, height: 1000 } });
const errs = [];
page.on("pageerror", e => errs.push("PAGEERROR: " + e.message));
page.on("console", m => { if (m.type() === "error") errs.push("CONSOLE: " + m.text()); });
await page.goto(file, { waitUntil: "networkidle" });
await page.waitForTimeout(700);

const probe = async () => page.evaluate(() => {
  const bad = [];
  document.querySelectorAll(".panel:not([hidden])").forEach(p => {
    const t = p.innerText;
    ["NaN", "Infinity", "undefined", "[object Object]"].forEach(k => { if (t.includes(k)) bad.push(k + " in #" + p.id); });
  });
  return { bad, wide: document.documentElement.scrollWidth > window.innerWidth + 2 };
});

const panels = ["start", "case1", "case2", "case3", "case4", "assump", "build", "present"];
for (const p of panels) {
  await page.click(`#casenav button[data-panel="${p}"]`);
  await page.waitForTimeout(220);
  const r = await probe();
  if (r.bad.length) errs.push(`panel ${p}: ${r.bad.join(", ")}`);
  if (r.wide) errs.push(`panel ${p}: body scrolls sideways`);
  await page.screenshot({ path: `shot-${p}.png`, fullPage: true });
}

// exercise every slider through its full range on every panel
await page.click('#casenav button[data-panel="case2"]');
await page.evaluate(() => { const b = document.querySelector("#sb-panel"); if (b.hidden) document.querySelector("#sb-toggle").click(); });
const keys = await page.$$eval("#sliders input[type=range]", els => els.map(e => e.dataset.key));
for (const k of keys) {
  for (const frac of [0, 0.25, 0.5, 0.75, 1]) {
    await page.evaluate(([key, f]) => {
      const el = document.querySelector(`#sl-${key}`);
      el.value = String(+el.min + f * (+el.max - +el.min));
      el.dispatchEvent(new Event("input", { bubbles: true }));
    }, [k, frac]);
  }
  const r = await probe();
  if (r.bad.length) errs.push(`slider ${k}: ${r.bad.join(", ")}`);
}
await page.click("#sb-reset");

// zero out operations headcount -> must fail visibly
await page.evaluate(() => {
  const el = document.querySelector("#sl-extraOpsFte");
  el.value = el.min; el.dispatchEvent(new Event("input", { bubbles: true }));
});
await page.waitForTimeout(150);
const failsVisibly = await page.evaluate(() => /the model stopped/i.test(document.body.innerText));
await page.screenshot({ path: "shot-failed.png" });
await page.click("#sb-reset");
await page.waitForTimeout(200);
const recovered = await page.evaluate(() => {
  const p = document.querySelector("#p-case2");
  return !p.hidden && !!document.querySelector("#c2-tiles") && p.innerText.includes("Utilisation today");
});

// toggles
await page.click("#t-xray"); await page.waitForTimeout(120);
const xrayWorks = await page.evaluate(() => document.body.classList.contains("xray") && getComputedStyle(document.querySelector('.fig[data-tag="PLACEHOLDER"]')).textDecorationLine.includes("underline"));
await page.click("#t-xray");
await page.click("#t-anon"); await page.waitForTimeout(150);
await page.click("#t-anon");
await page.click("#t-theme"); await page.waitForTimeout(200);
await page.click('#casenav button[data-panel="case3"]'); await page.waitForTimeout(250);
await page.screenshot({ path: "shot-dark.png" });
const darkOk = await page.evaluate(() => {
  const bg = getComputedStyle(document.body).backgroundColor;
  const c = getComputedStyle(document.querySelector("h2")).color;
  return { bg, c };
});
await page.click("#t-theme"); await page.click("#t-theme");

// compare mode
await page.click('#casenav button[data-panel="case2"]');
await page.click("#cmp-toggle");
await page.click('[data-preset="seat"]'); await page.waitForTimeout(250);
const cmpOk = await page.evaluate(() => !document.querySelector("#cmp-strip").hidden && document.querySelector("#cmp-strip").innerText.includes("Compare"));
await page.screenshot({ path: "shot-compare.png" });

console.log(JSON.stringify({ errors: errs, failsVisibly, recovered, xrayWorks, darkOk, cmpOk }, null, 1));
await browser.close();
