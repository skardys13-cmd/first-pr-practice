/* ==========================================================================
   OPERATIONS CAPACITY MODEL - page layer
   The engine above is byte-identical to the one the verification harness runs.
   ========================================================================== */
const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => [...(r || document).querySelectorAll(s)];

/* ---------------------------------------------------------------- FORMAT */
const nf = (n, d = 0) => (Number.isFinite(n) ? n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }) : "—");
const usd = (n, d = 0) => (Number.isFinite(n) ? (n < 0 ? "−$" : "$") + nf(Math.abs(n), d) : "—");
const usdK = n => !Number.isFinite(n) ? "—" : Math.abs(n) >= 1e6 ? (n < 0 ? "−$" : "$") + (Math.abs(n) / 1e6).toFixed(Math.abs(n) >= 1e7 ? 0 : 1) + "m"
  : Math.abs(n) >= 10000 ? (n < 0 ? "−$" : "$") + nf(Math.abs(n) / 1000, 0) + "k" : usd(n);
const pct = (n, d = 1) => Number.isFinite(n) ? (n * 100).toFixed(d) + "%" : "—";
const ratio = n => Number.isFinite(n) ? n.toFixed(2) + "×" : "—";
const hrs = (n, d = 1) => Number.isFinite(n) ? nf(n, d) + " h" : "—";
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const longDate = iso => { if (!iso) return "—"; const d = new Date(iso + "T00:00:00Z"); return MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear(); };
const shortDate = iso => { if (!iso) return "—"; const d = new Date(iso + "T00:00:00Z"); return MONTHS[d.getUTCMonth()].slice(0, 3) + " " + d.getUTCFullYear(); };
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/* ---------------------------------------------------------------- STATE */
const TAGS = ["MEASURED", "OBSERVED", "BENCHMARK", "ESTIMATED", "PLACEHOLDER"];
let state = defaultScenario(INPUTS);
let anonymised = true, xray = false, cmpBase = null, activePanel = "start";
let ledgerFilter = "ALL";

/* label lookup - the single ANONYMISE switch */
const L = key => {
  const row = INPUTS.labels[key];
  if (!row) return key;
  return anonymised ? row.anon : row.real;
};

/* ---------------------------------------------- THE ASSUMPTION LEDGER */
/* Every input in the model becomes one atom with a workpaper reference code. */
const ATOMS = [];
const ATOM_BY_ID = {};
/* Rebuilt whenever ANONYMISE flips: atom ids are stable, only the labels move. */
function buildLedger() {
  ATOMS.length = 0;
  for (const k of Object.keys(ATOM_BY_ID)) delete ATOM_BY_ID[k];
  const push = a => { ATOMS.push(a); ATOM_BY_ID[a.id] = a; return a; };
  let n;
  n = 0;
  for (const [k, c] of Object.entries(INPUTS.constants))
    push({ id: "const." + k, ref: "C-" + (++n), group: "Constants", name: c.name,
      value: c.v, unit: c.unit, tag: c.tag, src: c.src, who: c.who, checked: c.checked });
  n = 0;
  for (const r of INPUTS.roster) {
    push({ id: "roster." + r.role_id + ".comp", ref: "R-" + (++n), group: "Roster",
      name: L(r.role_id) + " — annual compensation", value: r.comp, unit: "usd",
      tag: r.comp_tag, src: r.comp_src, who: r.who, checked: r.comp_tag === "PLACEHOLDER" ? "never" : INPUTS.meta.as_of });
    push({ id: "roster." + r.role_id + ".fte", ref: "R-" + (++n), group: "Roster",
      name: L(r.role_id) + " — FTE", value: r.fte, unit: "fte", tag: r.fte_tag,
      src: r.fte_tag === "OBSERVED" ? "Headcount I can see." : "My estimate of the hours actually worked here.",
      who: "The principal holds the contract or the offer letter.", checked: INPUTS.meta.as_of });
    if (r.is_operations)
      push({ id: "roster." + r.role_id + ".ops_allocation", ref: "R-" + (++n), group: "Roster",
        name: L(r.role_id) + " — share of time on operations", value: r.ops_allocation, unit: "pct",
        tag: "ESTIMATED", src: "My estimate of how much of this person's week is operations work rather than planning, bookkeeping or reception.",
        who: "The person themselves, from a two-week time log. This is the cheapest input in the model to upgrade.",
        checked: INPUTS.meta.as_of });
  }
  n = 0;
  for (const b of INPUTS.book)
    push({ id: "book." + b.tier, ref: "B-" + (++n), group: "Book",
      name: b.tier + " " + b.label + " — households, average AUM, accounts per household",
      value: b.households, unit: "households", tag: b.tag, src: b.src, who: b.who, checked: INPUTS.meta.as_of });
  push({ id: "book.new_mix", ref: "B-" + (++n), group: "Book",
    name: "How new households distribute across the tiers", value: null, unit: "mix",
    tag: INPUTS.book_meta.new_mix_tag, src: INPUTS.book_meta.new_mix_src, who: INPUTS.book_meta.new_mix_who,
    checked: INPUTS.meta.as_of });
  push({ id: "fee.schedule", ref: "F-1", group: "Fee schedule",
    name: "Tiered fee schedule (" + INPUTS.fee_schedule.bands.length + " bands)", value: null, unit: "schedule",
    tag: INPUTS.fee_schedule.tag, src: INPUTS.fee_schedule.src, who: INPUTS.fee_schedule.who, checked: INPUTS.meta.as_of });
  n = 0;
  for (const t of INPUTS.tasks)
    push({ id: "task." + t.id, ref: "T-" + (++n), group: "Task catalogue",
      name: t.task + (t.tiers.length && t.tiers.length < 4 ? " (" + t.tiers.join(", ") + ")" : ""),
      value: t.minutes, unit: "minutes", tag: t.tag, taskId: t.id,
      src: "Seeded from the shape of real RIA operations work. The minutes are not measured — " + t.minutes + " min × " + t.occurrences + "/yr is a placeholder.",
      who: "Me, with a stopwatch. Three runs, median, interruptions included.", checked: "never" });
}
buildLedger();

const opsTaskAtoms = INPUTS.tasks.filter(t => t.work_type === "operations").map(t => "task." + t.id);
const allTaskAtoms = INPUTS.tasks.map(t => "task." + t.id);
const bookAtoms = INPUTS.book.map(b => "book." + b.tier);
const opsRoleIds = INPUTS.roster.filter(r => r.is_operations).map(r => r.role_id);
const advisorRoleIds = INPUTS.roster.filter(r => r.is_advisor).map(r => r.role_id);
const opsRosterAtoms = opsRoleIds.flatMap(r => ["roster." + r + ".fte", "roster." + r + ".ops_allocation"]);
const opsCompAtoms = opsRoleIds.map(r => "roster." + r + ".comp");
const advisorCompAtoms = advisorRoleIds.map(r => "roster." + r + ".comp");

/* Which inputs each headline output actually depends on. */
const DEPS = {
  revenue_total: ["fee.schedule", ...bookAtoms, "const.fee_realisation"],
  utilisation: [...opsTaskAtoms, ...opsRosterAtoms, ...bookAtoms, "book.new_mix",
    "const.productive_hours_year", "const.switching_uplift", "const.growth_rate_households"],
  hours_required: [...opsTaskAtoms, ...bookAtoms, "book.new_mix",
    "const.switching_uplift", "const.growth_rate_households"],
  capacity_break: [...opsTaskAtoms, ...opsRosterAtoms, ...bookAtoms, "book.new_mix",
    "const.productive_hours_year", "const.switching_uplift", "const.growth_rate_households"],
  cost_to_serve: [...opsTaskAtoms, ...opsCompAtoms, ...bookAtoms, "const.benefits_load",
    "const.productive_hours_year", "const.switching_uplift", "const.firm_overhead_per_household",
    ...advisorCompAtoms, "fee.schedule", "const.fee_realisation"],
  consultant_hours: [...INPUTS.tasks.filter(t => t.owner === "R7").map(t => "task." + t.id),
    ...bookAtoms, "const.switching_uplift", "roster.R7.fte", "const.productive_hours_year"],
  seat: ["const.ops_seat_comp", "roster.R4.comp", "const.benefits_load",
    ...INPUTS.tasks.filter(t => t.owner === "R7" || advisorRoleIds.includes(t.owner)).map(t => "task." + t.id),
    ...advisorCompAtoms, "const.productive_hours_year", "const.switching_uplift",
    "const.service_failures_avoided", "const.service_failure_cost_per_event"],
};

function rollup(ids) {
  const counts = Object.fromEntries(TAGS.map(t => [t, 0]));
  const seen = new Set();
  for (const id of ids) { if (seen.has(id)) continue; seen.add(id);
    const a = ATOM_BY_ID[id]; if (a) counts[a.tag]++; }
  const total = [...seen].filter(id => ATOM_BY_ID[id]).length || 1;
  const shares = Object.fromEntries(TAGS.map(t => [t, counts[t] / total]));
  return { counts, shares, total,
    solid: shares.MEASURED + shares.OBSERVED,
    worstTag: TAGS.slice().reverse().find(t => counts[t] > 0) || "OBSERVED" };
}
/* Hours-weighted view: which tags the HOURS in a figure come from. Tells you
   where a stopwatch buys the most, which a headcount of inputs does not.  */
function hoursRollup(model, ids) {
  const counts = Object.fromEntries(TAGS.map(t => [t, 0]));
  let total = 0;
  for (const id of new Set(ids)) {
    const a = ATOM_BY_ID[id];
    if (!a || !a.taskId) continue;
    const h = model.taskHoursById[a.taskId] || 0;
    counts[a.tag] += h; total += h;
  }
  if (total <= 0) return null;
  return { counts, total, shares: Object.fromEntries(TAGS.map(t => [t, counts[t] / total])) };
}
function caveatFor(ids) {
  const r = rollup(ids);
  if (r.counts.PLACEHOLDER > 0) return { level: "hard", r,
    text: `${r.counts.PLACEHOLDER} of the ${r.total} inputs behind this figure are placeholders — numbers I made up so the model would run. This is not yet a finding. It is a structure waiting for real values.` };
  if (r.shares.ESTIMATED > 0.5) return { level: "soft", r,
    text: `${pct(r.shares.ESTIMATED, 0)} of the inputs behind this figure are my own estimates rather than measured or observed values. Treat the shape as informative and the level as provisional.` };
  return null;
}
function caveatHTML(ids) {
  const c = caveatFor(ids); if (!c) return "";
  return `<div class="caveat${c.level === "soft" ? " soft" : ""}"><span class="cv-tag">${c.level === "hard" ? "Placeholders" : "Mostly estimated"}</span><span>${esc(c.text)}</span></div>`;
}
function provMeter(ids, model, opts = {}) {
  const r = rollup(ids);
  const segs = TAGS.filter(t => r.counts[t] > 0)
    .map(t => `<div class="pm-seg pm-${t}" style="width:${(r.shares[t] * 100).toFixed(2)}%" title="${t}: ${r.counts[t]} of ${r.total}"></div>`).join("");
  const legend = TAGS.filter(t => r.counts[t] > 0)
    .map(t => `<span><i class="pm-dot pm-${t}"></i>${r.counts[t]} ${t.toLowerCase()}</span>`).join("");
  let hoursLine = "";
  if (opts.hours && model) {
    const hr = hoursRollup(model, opts.ids || ids);
    if (hr) {
      const untimed = hr.shares.PLACEHOLDER + hr.shares.ESTIMATED;
      hoursLine = `<span style="color:var(--muted)">${pct(untimed, 0)} of the hours in this number come from untimed rows</span>`;
    }
  }
  return `<div class="provmeter"><div class="pm-track">${segs}</div>
    <div class="pm-legend">${legend}${hoursLine ? `<span>·</span>${hoursLine}` : ""}</div></div>`;
}
/* A figure with its provenance attached. */
function fig(text, tag, refId) {
  const a = refId ? ATOM_BY_ID[refId] : null;
  return `<span class="fig" data-tag="${tag}">${text}</span>${a ? `<a class="ref" href="#" data-goto="${esc(refId)}" title="${esc(a.name)} — ${a.tag}">[${a.ref}]</a>` : ""}`;
}
/* A computed figure: tagged with the weakest input behind it. */
function outFig(text, ids) { return `<span class="fig" data-tag="${rollup(ids).worstTag}">${text}</span>`; }

/* ---------------------------------------------------------------- TOOLTIP */
const tipEl = () => $("#tip");
document.addEventListener("pointerover", e => {
  const t = e.target.closest("[data-tip]"); if (!t) return;
  const el = tipEl(); el.innerHTML = t.getAttribute("data-tip"); el.style.opacity = "1"; moveTip(e);
});
document.addEventListener("pointermove", e => { if (tipEl().style.opacity === "1") moveTip(e); });
document.addEventListener("pointerout", e => {
  if (e.target.closest("[data-tip]") && !e.relatedTarget?.closest?.("[data-tip]")) tipEl().style.opacity = "0";
});
function moveTip(e) {
  const el = tipEl(), r = el.getBoundingClientRect();
  let x = e.clientX + 14, y = e.clientY + 16;
  if (x + r.width > innerWidth - 8) x = e.clientX - r.width - 12;
  if (y + r.height > innerHeight - 8) y = e.clientY - r.height - 12;
  el.style.left = Math.max(8, x) + "px"; el.style.top = Math.max(8, y) + "px";
}
const tipRows = (title, rows) => esc(`<div class="tt-h">${title}</div>` +
  rows.map(([k, v]) => `<div class="tt-r"><span class="tt-n">${k}</span><span>${v}</span></div>`).join(""));

/* ---------------------------------------------------------------- CHARTS */
const SERIES = ["--s1", "--s2", "--s3", "--s4", "--s5"];
const sc = i => `var(${SERIES[i % SERIES.length]})`;

function niceTicks(max, count = 5) {
  if (!(max > 0)) return [0, 1];
  const raw = max / count, mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw) || 10 * mag;
  const out = []; for (let v = 0; v <= max * 1.0001 + step * .5; v += step) out.push(v);
  return out;
}
function legendHTML(items) {
  return `<div class="legend">` + items.map(i =>
    `<span class="lg"><i class="sw${i.line ? " line" : ""}" style="background:${i.color}"></i>${esc(i.label)}</span>`).join("") + `</div>`;
}
function tableView(headers, rows, label = "Show the numbers") {
  return `<details class="tableview"><summary>${esc(label)}</summary><div class="tscroll">
    <table class="data"><thead><tr>${headers.map((h, i) => `<th class="${i ? "n" : ""}">${esc(h)}</th>`).join("")}</tr></thead>
    <tbody>${rows.map(r => `<tr>${r.map((c, i) => `<td class="${i ? "n" : ""}">${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div></details>`;
}

/* ---- CHART 1: capacity over time ---------------------------------------- */
function chartCapacity(model) {
  const W = 760, H = 340, P = { t: 22, r: 96, b: 44, l: 62 };
  const proj = model.capacity.projection;
  const iw = W - P.l - P.r, ih = H - P.t - P.b;
  const maxY = Math.max(...proj.map(p => p.required), model.capacity.available) * 1.12;
  const ticks = niceTicks(maxY);
  const yMax = ticks[ticks.length - 1];
  const x = m => P.l + (m / model.capacity.horizonMonths) * iw;
  const y = v => P.t + ih - (v / yMax) * ih;

  const line = proj.map((p, i) => `${i ? "L" : "M"}${x(p.month).toFixed(1)},${y(p.required).toFixed(1)}`).join("");
  const area = `M${x(0).toFixed(1)},${y(0).toFixed(1)}` + proj.map(p => `L${x(p.month).toFixed(1)},${y(p.required).toFixed(1)}`).join("") + `L${x(proj[proj.length - 1].month).toFixed(1)},${y(0).toFixed(1)}Z`;
  const availY = y(model.capacity.available);

  let grid = ticks.map(t => `<line x1="${P.l}" y1="${y(t).toFixed(1)}" x2="${P.l + iw}" y2="${y(t).toFixed(1)}" stroke="var(--grid)" stroke-width="1"/>
    <text x="${P.l - 9}" y="${(y(t) + 4).toFixed(1)}" text-anchor="end" font-size="11" fill="var(--muted)">${nf(t)}</text>`).join("");
  let xt = "";
  for (let m = 0; m <= model.capacity.horizonMonths; m += 12) {
    xt += `<line x1="${x(m).toFixed(1)}" y1="${P.t + ih}" x2="${x(m).toFixed(1)}" y2="${P.t + ih + 5}" stroke="var(--axis)"/>
      <text x="${x(m).toFixed(1)}" y="${P.t + ih + 19}" text-anchor="middle" font-size="11" fill="var(--muted)">${shortDate(proj[m].date)}</text>`;
  }

  let cross = "";
  if (model.capacity.breakMonth !== null) {
    const cx = x(model.capacity.breakMonthFrac), cy = availY;
    cross = `<line x1="${cx.toFixed(1)}" y1="${P.t}" x2="${cx.toFixed(1)}" y2="${P.t + ih}" stroke="var(--warn)" stroke-width="1"/>
      <circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="6" fill="var(--warn)" stroke="var(--surface)" stroke-width="2"/>
      <rect x="${(cx - 52).toFixed(1)}" y="${(P.t + 2).toFixed(1)}" width="104" height="34" rx="3" fill="var(--surface)" stroke="var(--warn)" stroke-width="1"/>
      <text x="${cx.toFixed(1)}" y="${(P.t + 15).toFixed(1)}" text-anchor="middle" font-size="11" font-weight="600" fill="var(--ink)">${esc(longDate(model.capacity.breakDate))}</text>
      <text x="${cx.toFixed(1)}" y="${(P.t + 29).toFixed(1)}" text-anchor="middle" font-size="10.5" fill="var(--muted)">${nf(model.capacity.breakHouseholds, 0)} households</text>`;
  }

  const hits = proj.map(p => `<rect x="${(x(p.month) - iw / model.capacity.horizonMonths / 2).toFixed(1)}" y="${P.t}" width="${(iw / model.capacity.horizonMonths).toFixed(2)}" height="${ih}" fill="transparent"
    data-tip="${tipRows(longDate(p.date), [["Households", nf(p.households, 0)], ["Hours required", nf(p.required, 0)], ["Hours available", nf(p.available, 0)], ["Utilisation", pct(p.utilisation)]])}"/>`).join("");

  const last = proj[proj.length - 1];
  const svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Operations hours required against hours available, projected forward">
    ${grid}${xt}
    <line x1="${P.l}" y1="${P.t + ih}" x2="${P.l + iw}" y2="${P.t + ih}" stroke="var(--axis)"/>
    <path d="${area}" fill="${sc(0)}" opacity=".10"/>
    <line x1="${P.l}" y1="${availY.toFixed(1)}" x2="${P.l + iw}" y2="${availY.toFixed(1)}" stroke="${sc(1)}" stroke-width="2" stroke-linecap="round"/>
    <path d="${line}" fill="none" stroke="${sc(0)}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    ${cross}
    <circle cx="${x(last.month).toFixed(1)}" cy="${y(last.required).toFixed(1)}" r="4.5" fill="${sc(0)}" stroke="var(--surface)" stroke-width="2"/>
    <text x="${P.l + iw + 9}" y="${(y(last.required) + 4).toFixed(1)}" font-size="11.5" font-weight="600" fill="var(--ink)">${nf(last.required, 0)} h</text>
    <text x="${P.l + iw + 9}" y="${(availY + 4).toFixed(1)}" font-size="11.5" font-weight="600" fill="var(--ink)">${nf(model.capacity.available, 0)} h</text>
    <text x="${P.l + iw + 9}" y="${(availY + 17).toFixed(1)}" font-size="10" fill="var(--muted)">available</text>
    <text x="12" y="${(P.t + ih / 2).toFixed(1)}" font-size="11" fill="var(--muted)" transform="rotate(-90 12 ${(P.t + ih / 2).toFixed(1)})" text-anchor="middle">Operations hours per year</text>
    ${hits}
  </svg>`;

  const rows = proj.filter(p => p.month % 12 === 0).map(p =>
    [longDate(p.date), nf(p.households, 0), nf(p.required, 0), nf(p.available, 0), pct(p.utilisation)]);
  return `<div class="chart-scroll">${svg}</div>` +
    legendHTML([{ label: "Hours required by the task catalogue", color: sc(0), line: 1 },
                { label: "Hours the operations team has", color: sc(1), line: 1 }]) +
    tableView(["Date", "Households", "Required (h)", "Available (h)", "Utilisation"], rows);
}

/* ---- CHART 2: tier economics -------------------------------------------- */
function chartTiers(model) {
  const W = 760, H = 360, P = { t: 34, r: 18, b: 62, l: 66 };
  const iw = W - P.l - P.r, ih = H - P.t - P.b;
  const layers = [
    { key: "directOps", label: "Direct operations time", c: sc(1) },
    { key: "allocFirm", label: "Share of firm-level operations", c: sc(2) },
    { key: "advisory", label: "Advisor time", c: sc(3) },
    { key: "firmOverhead", label: "Non-payroll firm overhead", c: sc(4) },
  ];
  const maxV = Math.max(...model.tiers.map(t => Math.max(t.revenuePerHousehold, t.costTotalLoaded))) * 1.16;
  const ticks = niceTicks(maxV); const yMax = ticks[ticks.length - 1];
  const y = v => P.t + ih - (v / yMax) * ih;
  const band = iw / model.tiers.length;
  const bw = Math.min(24, band * 0.24), gap2 = 2;

  let grid = ticks.map(t => `<line x1="${P.l}" y1="${y(t).toFixed(1)}" x2="${P.l + iw}" y2="${y(t).toFixed(1)}" stroke="var(--grid)"/>
    <text x="${P.l - 9}" y="${(y(t) + 4).toFixed(1)}" text-anchor="end" font-size="11" fill="var(--muted)">${usdK(t)}</text>`).join("");

  let bars = "", labels = "", divider = "";
  model.tiers.forEach((t, i) => {
    const cx = P.l + band * i + band / 2;
    const xr = cx - bw - 4, xcst = cx + 4;
    // revenue bar (rounded top, square base)
    const hR = Math.max(1.5, (t.revenuePerHousehold / yMax) * ih);
    bars += roundedTopRect(xr, y(t.revenuePerHousehold), bw, hR, 4, sc(0),
      tipRows(t.tier + " · " + t.label,
        [["Revenue per household", usd(t.revenuePerHousehold)], ["Average AUM", usd(t.avgAum)], ["Effective fee rate", pct(t.effectiveRate, 3)]]));
    // cost stack
    let acc = 0;
    layers.forEach((ly, li) => {
      const v = t.costLayers[ly.key]; if (v <= 0) return;
      const y0 = y(acc + v), y1 = y(acc);
      const h = Math.max(0.8, y1 - y0 - (li === 0 ? 0 : gap2));
      const top = li === layers.length - 1;
      bars += (top ? roundedTopRect(xcst, y0, bw, h, 4, ly.c, tipRows(t.tier + " · " + ly.label, [["Cost per household", usd(v)], ["Share of loaded cost", t.costTotalLoaded > 0 ? pct(v / t.costTotalLoaded) : "—"]]))
        : `<rect x="${xcst.toFixed(1)}" y="${y0.toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}" fill="${ly.c}" data-tip="${tipRows(t.tier + " · " + ly.label, [["Cost per household", usd(v)], ["Share of loaded cost", t.costTotalLoaded > 0 ? pct(v / t.costTotalLoaded) : "—"]])}"/>`);
      acc += v;
    });
    labels += `<text x="${xr + bw / 2}" y="${(y(t.revenuePerHousehold) - 7).toFixed(1)}" text-anchor="middle" font-size="10.5" font-weight="600" fill="var(--ink)">${usdK(t.revenuePerHousehold)}</text>
      <text x="${xcst + bw / 2}" y="${(y(t.costTotalLoaded) - 7).toFixed(1)}" text-anchor="middle" font-size="10.5" font-weight="600" fill="${t.marginLoaded < 0 ? "var(--warn)" : "var(--ink)"}">${usdK(t.costTotalLoaded)}</text>
      <text x="${cx}" y="${P.t + ih + 18}" text-anchor="middle" font-size="11.5" font-weight="600" fill="var(--ink)">${t.tier}</text>
      <text x="${cx}" y="${P.t + ih + 32}" text-anchor="middle" font-size="10.5" fill="var(--muted)">${esc(t.label)}</text>
      <text x="${cx}" y="${P.t + ih + 47}" text-anchor="middle" font-size="10.5" font-weight="${t.marginLoaded < 0 ? 600 : 400}" fill="${t.marginLoaded < 0 ? "var(--warn)" : "var(--muted)"}">${t.marginLoaded < 0 ? "cost exceeds revenue" : usdK(t.marginLoaded) + " margin"}</text>`;
  });

  // the crossing: boundary between the last underwater tier and the first that is not
  const firstOk = model.tiers.findIndex(t => t.marginLoaded >= 0);
  if (firstOk > 0) {
    const dx = P.l + band * firstOk;
    divider = `<line x1="${dx}" y1="${P.t - 12}" x2="${dx}" y2="${P.t + ih}" stroke="var(--warn)" stroke-width="1" stroke-dasharray="2 3"/>
      <text x="${dx - 7}" y="${P.t - 16}" text-anchor="end" font-size="10" fill="var(--warn)" font-weight="600">cost &gt; revenue</text>
      <text x="${dx + 7}" y="${P.t - 16}" text-anchor="start" font-size="10" fill="var(--muted)">revenue &gt; cost</text>`;
  }

  const svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Revenue per household against fully loaded cost to serve, by tier">
    ${grid}<line x1="${P.l}" y1="${P.t + ih}" x2="${P.l + iw}" y2="${P.t + ih}" stroke="var(--axis)"/>
    ${divider}${bars}${labels}
    <text x="12" y="${(P.t + ih / 2).toFixed(1)}" font-size="11" fill="var(--muted)" transform="rotate(-90 12 ${(P.t + ih / 2).toFixed(1)})" text-anchor="middle">Dollars per household per year</text>
  </svg>`;

  const rows = model.tiers.map(t => [t.tier + " " + t.label, usd(t.revenuePerHousehold),
    usd(t.costLayers.directOps), usd(t.costLayers.allocFirm), usd(t.costLayers.advisory),
    usd(t.costLayers.firmOverhead), usd(t.costTotalLoaded),
    `<span class="${t.marginLoaded < 0 ? "neg" : ""}">${usd(t.marginLoaded)}</span>`]);
  return `<div class="chart-scroll">${svg}</div>` +
    legendHTML([{ label: "Revenue per household", color: sc(0) }, ...layers.map(l => ({ label: l.label, color: l.c }))]) +
    tableView(["Tier", "Revenue", "Direct ops", "Firm ops share", "Advisor time", "Firm overhead", "Total loaded", "Margin"], rows);
}
function roundedTopRect(x, y, w, h, r, fill, tip) {
  r = Math.min(r, h, w / 2);
  const d = `M${x.toFixed(1)},${(y + h).toFixed(1)} L${x.toFixed(1)},${(y + r).toFixed(1)} Q${x.toFixed(1)},${y.toFixed(1)} ${(x + r).toFixed(1)},${y.toFixed(1)} L${(x + w - r).toFixed(1)},${y.toFixed(1)} Q${(x + w).toFixed(1)},${y.toFixed(1)} ${(x + w).toFixed(1)},${(y + r).toFixed(1)} L${(x + w).toFixed(1)},${(y + h).toFixed(1)} Z`;
  return `<path d="${d}" fill="${fill}"${tip ? ` data-tip="${tip}"` : ""}/>`;
}
