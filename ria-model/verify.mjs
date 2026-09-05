/* Verification harness. Run: node ria-model/verify.mjs
   Section B deliberately recomputes the hours from raw JSON with its own loops
   rather than calling the engine, so a bug in the engine cannot hide here. */
import fs from "fs";
import { fileURLToPath } from "url";
import path from "path";
import * as E from "./engine.mjs";

const dir = path.dirname(fileURLToPath(import.meta.url));
const I = JSON.parse(fs.readFileSync(path.join(dir, "inputs.json"), "utf8"));

let pass = 0, fail = 0;
const money = n => "$" + n.toLocaleString(undefined, { maximumFractionDigits: 2 });
function ok(name, cond, detail = "") {
  if (cond) { pass++; console.log(`  PASS  ${name}${detail ? "  " + detail : ""}`); }
  else { fail++; console.log(`  FAIL  ${name}  ${detail}`); }
}
function near(a, b, tol = 0.005) { return Math.abs(a - b) <= tol; }
function hdr(t) { console.log("\n" + t + "\n" + "-".repeat(t.length)); }

/* ========== A. TIERED FEE, HAND-WORKED ================================== */
hdr("A. Tiered fee maths - three households, hand-worked");
const bands = I.fee_schedule.bands;

/* Hand working, done on paper first, then pinned here as literals.
   Schedule: 1.00% to 500k | 0.85% 500k-1m | 0.70% 1m-3m | 0.50% 3m-5m | 0.35% over 5m */

// (1) BELOW the first breakpoint: 145,000 x 1.00% = 1,450.00
const h1 = E.tieredFee(145000, bands);
ok("H1 $145,000 (below first breakpoint) = $1,450.00", near(h1, 1450), `got ${money(h1)}`);

// (2) JUST ABOVE a breakpoint - the flat-rate detector.
//     500,000 x 1.00% =  5,000.00
//      20,000 x 0.85% =    170.00
//                        --------
//                        5,170.00
const h2 = E.tieredFee(520000, bands);
ok("H2 $520,000 (just above the $500k breakpoint) = $5,170.00", near(h2, 5170), `got ${money(h2)}`);
const flatTrap = 520000 * 0.0085;
ok("H2 is NOT the flat-rate answer ($4,420.00)", !near(h2, flatTrap),
   `tiered ${money(h2)} vs flat-rate ${money(flatTrap)} - a $${(h2 - flatTrap).toFixed(2)} difference`);

// (3) WELL ABOVE:
//     500,000 x 1.00% =  5,000.00
//     500,000 x 0.85% =  4,250.00
//   2,000,000 x 0.70% = 14,000.00
//   2,000,000 x 0.50% = 10,000.00
//     100,000 x 0.35% =    350.00
//                        ---------
//                       33,600.00   (effective rate 0.6588%)
const h3 = E.tieredFee(5100000, bands);
ok("H3 $5,100,000 (well above) = $33,600.00", near(h3, 33600), `got ${money(h3)}`);
ok("H3 effective rate = 0.659%", near(h3 / 5100000, 0.0065882, 1e-6),
   `got ${((h3 / 5100000) * 100).toFixed(4)}%`);

// Monotonic and continuous at every breakpoint (no jumps => genuinely marginal)
let mono = true, cont = true;
let prev = -1;
for (let a = 0; a <= 6000000; a += 5000) { const f = E.tieredFee(a, bands); if (f < prev - 1e-9) mono = false; prev = f; }
for (const b of bands) { if (b.to == null) continue;
  const below = E.tieredFee(b.to - 0.01, bands), above = E.tieredFee(b.to + 0.01, bands);
  if (Math.abs(above - below) > 0.01) cont = false; }
ok("Fee is monotonically increasing in AUM", mono);
ok("Fee is continuous at every breakpoint (no cliff => marginal, not flat)", cont);

/* ========== B. INDEPENDENT RECOMPUTATION OF HOURS ======================= */
hdr("B. Operations hours - recomputed independently from raw JSON");
const s = E.defaultScenario(I);
const m = E.computeModel(I, {});

// --- own loops, no engine calls ---
const bookBy = Object.fromEntries(I.book.map(b => [b.tier, b]));
let recurMin = 0, onboardMin = 0, firmMin = 0;
const totalH = I.book.reduce((a, b) => a + b.households, 0);
const newTotal = totalH * s.growth;
for (const t of I.tasks) {
  if (t.work_type !== "operations") continue;
  const base = t.minutes * t.occurrences * s.efficiency;
  if (t.basis === "firm") { firmMin += base; continue; }
  for (const tier of t.tiers) {
    const bk = bookBy[tier];
    if (t.basis === "household") recurMin += bk.households * base;
    else if (t.basis === "account") recurMin += bk.households * bk.accounts_per_household * base;
    else if (t.basis === "new_household") onboardMin += (newTotal * bk.new_mix) * base;
  }
}
const up = 1 + s.switchingUplift;
const indepRequired = (recurMin + onboardMin + firmMin) / 60 * up;
ok("Total operations hours required matches independent recomputation",
   near(indepRequired, m.capacity.required.total, 0.01),
   `independent ${indepRequired.toFixed(2)}h vs engine ${m.capacity.required.total.toFixed(2)}h`);

let availIndep = 0;
for (const r of I.roster) if (r.is_operations) availIndep += r.fte * r.ops_allocation * s.productiveHours;
ok("Operations hours available matches independent recomputation",
   near(availIndep, m.capacity.available, 0.01),
   `independent ${availIndep.toFixed(2)}h vs engine ${m.capacity.available.toFixed(2)}h`);
ok("Utilisation = required / available",
   near(indepRequired / availIndep, m.capacity.utilisation, 1e-9),
   `${(m.capacity.utilisation * 100).toFixed(2)}%`);

// Revenue, recomputed independently
let revIndep = 0;
for (const b of I.book) revIndep += b.households * E.tieredFee(b.avg_aum, bands) * s.feeRealisation;
ok("Total revenue matches independent recomputation", near(revIndep, m.revenue.total, 0.01),
   `${money(Math.round(revIndep))}`);

/* ========== C. CAPACITY CROSSOVER, HAND-WORKED ========================== */
hdr("C. Capacity crossover - hand-worked at 15% growth");
/* Required hours are affine in household count at a fixed tier mix:
       required(H) = fixed + H x perHousehold
   fixed          = firm-level hours only (do not scale with the book)
   perHousehold   = marginal hours of one more household at today's mix,
                    including the onboarding work growth brings with it.     */
const fixedHand = firmMin / 60 * up;
const unitMix = {}; for (const b of I.book) unitMix[b.tier] = b.households / totalH;
let perHhMin = 0;
for (const t of I.tasks) {
  if (t.work_type !== "operations" || t.basis === "firm") continue;
  const base = t.minutes * t.occurrences * s.efficiency;
  for (const tier of t.tiers) {
    const bk = bookBy[tier];
    if (t.basis === "household") perHhMin += unitMix[tier] * base;
    else if (t.basis === "account") perHhMin += unitMix[tier] * bk.accounts_per_household * base;
    else if (t.basis === "new_household") perHhMin += (s.growth * bk.new_mix) * base;
  }
}
const perHhHand = perHhMin / 60 * up;
const breakHand = (availIndep - fixedHand) / perHhHand;
ok("Fixed (firm-level) hours match", near(fixedHand, m.capacity.fixedHours, 0.01), `${fixedHand.toFixed(2)}h`);
ok("Marginal hours per household match", near(perHhHand, m.capacity.perHouseholdHours, 1e-6), `${perHhHand.toFixed(4)}h/household`);
ok("Break at fixed mix matches closed form", near(breakHand, m.capacity.breakHouseholdsExact, 0.01),
   `${breakHand.toFixed(1)} households`);
console.log(`        hand working:  (${availIndep.toFixed(1)}h available - ${fixedHand.toFixed(1)}h fixed) / ${perHhHand.toFixed(4)}h per household = ${breakHand.toFixed(1)} households`);

/* Years to reach that count at 15%: ln(H_break / H_now) / ln(1.15) */
const yrsHand = Math.log(breakHand / totalH) / Math.log(1 + s.growth);
console.log(`        ln(${breakHand.toFixed(1)}/${totalH}) / ln(1.15) = ${yrsHand.toFixed(3)} years = ${(yrsHand * 12).toFixed(1)} months`);
ok("Closed-form crossing is later than the projection's (mix shift toward larger tiers pulls it in)",
   yrsHand * 12 > m.capacity.breakMonthFrac,
   `closed form ${(yrsHand * 12).toFixed(1)}mo vs projection ${m.capacity.breakMonthFrac.toFixed(1)}mo - the projection sends ${(I.book.find(b=>b.tier==="T3").new_mix*100).toFixed(0)}% of new households into T3, which costs more hours each`);
ok("Chart crossing month equals the reported break month",
   m.capacity.projection[m.capacity.breakMonth].required >= m.capacity.available &&
   m.capacity.projection[m.capacity.breakMonth - 1].required < m.capacity.available,
   `month ${m.capacity.breakMonth}, ${m.capacity.breakDate}`);

/* ========== D. SLIDER SWEEP ============================================= */
hdr("D. Slider sweep - every control across its full range");
const sweeps = {
  growth: [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
  feeRealisation: [0.70, 0.85, 1.0, 1.10],
  efficiency: [0.60, 0.8, 1.0, 1.2],
  benefitsLoad: [0, 0.1, 0.25, 0.5],
  productiveHours: [1200, 1500, 1700, 2000],
  switchingUplift: [0, 0.15, 0.25, 0.40],
  firmOverheadPerHousehold: [0, 900, 1800, 4000],
  extraOpsFte: [0, 0.5, 1, 2],
};
const bad = [];
function scan(obj, p, sc) {
  for (const [k, v] of Object.entries(obj)) {
    const key = p ? `${p}.${k}` : k;
    if (typeof v === "number") {
      if (!Number.isFinite(v)) bad.push(`${sc} -> ${key} = ${v}`);
    } else if (Array.isArray(v)) v.forEach((x, i) => (x && typeof x === "object") && scan(x, `${key}[${i}]`, sc));
    else if (v && typeof v === "object") scan(v, key, sc);
  }
}
let combos = 0;
for (const [lever, vals] of Object.entries(sweeps)) {
  for (const v of vals) {
    for (const preset of ["today", "gone", "seat"]) {
      const pr = E.PRESETS[preset];
      const sc = { [lever]: v, consultantPresent: pr.consultantPresent, response: pr.response };
      const r = E.computeModel(I, sc);
      combos++;
      if (r.failed) continue;
      scan(r, "", `${lever}=${v}/${preset}`);
      if (r.book.totalHouseholds < 0) bad.push(`${lever}=${v} -> negative households`);
      if (r.capacity.available < 0) bad.push(`${lever}=${v} -> negative available hours`);
      for (const t of r.tiers) if (t.costTotalLoaded < 0) bad.push(`${lever}=${v} -> negative cost to serve ${t.tier}`);
    }
  }
}
ok(`No NaN / Infinity / negative counts across ${combos} scenario combinations`, bad.length === 0, bad.slice(0, 6).join(" | "));

/* Extremes together */
const extreme = E.computeModel(I, { growth: 0.30, efficiency: 1.2, switchingUplift: 0.40,
  productiveHours: 1200, benefitsLoad: 0.5, feeRealisation: 0.7, consultantPresent: false, response: "absorb" });
ok("Worst-case corner still computes", !extreme.failed && Number.isFinite(extreme.capacity.utilisation),
   `utilisation ${(extreme.capacity.utilisation * 100).toFixed(1)}%, break ${extreme.capacity.breakDate ?? "already past"}`);
const zeroGrowth = E.computeModel(I, { growth: 0 });
ok("Zero growth does not break capacity inside the horizon (and says so)",
   zeroGrowth.capacity.breakMonth === null && zeroGrowth.capacity.breakDate === null,
   "breakDate reported as null, not a fabricated date");

/* ========== E. FAIL-VISIBLY TESTS ====================================== */
hdr("E. The model must fail visibly, never quietly");
const noOps = JSON.parse(JSON.stringify(I));
for (const r of noOps.roster) if (r.is_operations) r.ops_allocation = 0;
const rNoOps = E.computeModel(noOps, {});
ok("Zero operations headcount returns failed:true with an explanation",
   rNoOps.failed === true && rNoOps.errors.length > 0, rNoOps.errors?.[0]?.slice(0, 78) + "...");
const noHours = E.computeModel(I, { productiveHours: 0 });
ok("Zero productive hours returns failed:true", noHours.failed === true, noHours.errors?.[0]?.slice(0, 60) + "...");
const noBook = JSON.parse(JSON.stringify(I));
for (const b of noBook.book) b.households = 0;
ok("Empty book returns failed:true", E.computeModel(noBook, {}).failed === true);

/* ========== F. PRIVACY ================================================= */
hdr("F. Privacy - no client-identifying data anywhere in the inputs");
const raw = fs.readFileSync(path.join(dir, "inputs.json"), "utf8");
const banned = [/\b\d{3}-\d{2}-\d{4}\b/, /\baccount\s*(?:no|number|#)\s*[:=]?\s*\d/i,
  /\b\d{8,}\b/, /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/];
const hits = banned.filter(re => re.test(raw));
ok("No SSNs, account numbers, long identifiers or email addresses in inputs.json", hits.length === 0, hits.join(" "));
ok("Every book row is a tier aggregate, never a household", I.book.every(b => b.households >= 1));
const labelsAnon = Object.entries(I.labels).filter(([k]) => k !== "_note")
  .every(([, v]) => v.anon === v.real);
ok("Shipped labels table carries nothing identifying (anon === real as published)", labelsAnon);

/* ========== G. LEDGER COMPLETENESS ===================================== */
hdr("G. Assumption ledger completeness");
const validTags = Object.keys(I.tag_meta);
const untagged = [];
for (const [k, c] of Object.entries(I.constants)) if (!validTags.includes(c.tag)) untagged.push("constant " + k);
for (const r of I.roster) { if (!validTags.includes(r.comp_tag)) untagged.push("roster " + r.role_id + " comp"); if (!validTags.includes(r.fte_tag)) untagged.push("roster " + r.role_id + " fte"); }
for (const b of I.book) if (!validTags.includes(b.tag)) untagged.push("book " + b.tier);
for (const t of I.tasks) if (!validTags.includes(t.tag)) untagged.push("task " + t.id);
if (!validTags.includes(I.fee_schedule.tag)) untagged.push("fee schedule");
ok("Every input carries a valid provenance tag", untagged.length === 0, untagged.slice(0, 5).join(", "));
const noSrc = Object.entries(I.constants).filter(([, c]) => !c.src || !c.who).map(([k]) => k);
ok("Every constant names a source and who could confirm it", noSrc.length === 0, noSrc.join(", "));
ok("Every seeded task row is PLACEHOLDER until timed", I.tasks.every(t => t.tag === "PLACEHOLDER"),
   `${I.tasks.length} rows`);
ok("Benchmark inputs cite a source", Object.values(I.constants)
   .filter(c => c.tag === "BENCHMARK").every(c => /\d{4}|Bureau|Study|Survey|Benchmark/i.test(c.src)));

console.log(`\n${"=".repeat(64)}\n  ${pass} passed, ${fail} failed\n${"=".repeat(64)}`);
process.exit(fail ? 1 : 0);
