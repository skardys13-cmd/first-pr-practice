
/* ---- CHART 3: where her hours land -------------------------------------- */
function chartDeparture(model) {
  const c1 = model.case1;
  const W = 760, rowH = 62, P = { t: 30, r: 20, b: 40, l: 150 };
  const H = P.t + rowH * 3 + P.b;
  const iw = W - P.l - P.r;
  const totalHours = c1.catalogued + c1.unmapped;
  const xMax = totalHours * 1.04;
  const x = v => P.l + (v / xMax) * iw;

  /* Under "absorb", her hours land on whoever has slack. Spare capacity is
     measured at the team level - available hours after she goes, less the work
     that is not hers - because a per-role "gap" is unmapped work, not free time. */
  const afterAvail = c1.options[0].available;
  const workNotHers = model.capacity.required.total - c1.catalogued;
  const canAbsorb = Math.max(0, Math.min(c1.catalogued, afterAvail - workNotHers));
  const overflow = Math.max(0, c1.catalogued - canAbsorb);

  const scenarios = [
    { name: "Absorb across the team", segs: [
        ...(canAbsorb > 0.5 ? [{ label: "Spare capacity on the remaining team", hours: canAbsorb, c: sc(2) }] : []),
        ...(overflow > 0.5 ? [{ label: "Nobody — work with no owner", hours: overflow, c: "var(--warn)" }] : [])],
      util: c1.options[0].utilisation, cost: c1.options[0].annualCost },
    { name: "Backfill like-for-like", segs: [{ label: "Replacement engagement", hours: c1.catalogued, c: sc(2) }],
      util: c1.options[1].utilisation, cost: c1.options[1].annualCost },
    { name: "I take it on", segs: [{ label: "The operations seat", hours: c1.catalogued, c: sc(0) }],
      util: c1.options[2].utilisation, cost: c1.options[2].annualCost },
  ];

  let body = "";
  scenarios.forEach((s, i) => {
    const yTop = P.t + rowH * i + 8, bh = 22;
    let acc = 0;
    body += `<text x="${P.l - 12}" y="${yTop + 15}" text-anchor="end" font-size="11.5" font-weight="600" fill="var(--ink)">${esc(s.name)}</text>`;
    for (const g of s.segs) {
      const x0 = x(acc), w = Math.max(1, x(acc + g.hours) - x(acc) - 2);
      body += `<rect x="${x0.toFixed(1)}" y="${yTop}" width="${w.toFixed(1)}" height="${bh}" fill="${g.c}" rx="1"
        data-tip="${tipRows(s.name, [[g.label, nf(g.hours, 0) + " h/yr"]])}"/>`;
      acc += g.hours;
    }
    // unmapped extension - outlined, never filled: it is not yet known work
    const ux0 = x(c1.catalogued), uw = Math.max(1, x(totalHours) - ux0 - 2);
    body += `<rect x="${ux0.toFixed(1)}" y="${yTop}" width="${uw.toFixed(1)}" height="${bh}" fill="none"
      stroke="var(--rule-strong)" stroke-width="1.5" stroke-dasharray="4 3" rx="1"
      data-tip="${tipRows("Not yet in the model", [["Unmapped hours", nf(c1.unmapped, 0) + " h/yr"], ["Her contracted hours", nf(c1.contracted, 0) + " h/yr"]])}"/>`;
    body += `<text x="${P.l}" y="${yTop + bh + 16}" font-size="10.5" fill="var(--muted)">operations then runs at </text>
      <text x="${P.l + 108}" y="${yTop + bh + 16}" font-size="10.5" font-weight="700" fill="${s.util > 1 ? "var(--warn)" : "var(--ink)"}">${pct(s.util)}</text>
      <text x="${P.l + 152}" y="${yTop + bh + 16}" font-size="10.5" fill="var(--muted)">· ${s.cost > 0 ? usd(s.cost) + " a year" : "no new spend"}</text>`;
  });

  const svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Where the consultant's hours land under each of three responses">
    <text x="${P.l}" y="18" font-size="10.5" fill="var(--muted)">0 h</text>
    <text x="${x(c1.catalogued).toFixed(1)}" y="18" text-anchor="middle" font-size="10.5" fill="var(--ink-2)" font-weight="600">${nf(c1.catalogued, 0)} h catalogued</text>
    <text x="${x(totalHours).toFixed(1)}" y="18" text-anchor="end" font-size="10.5" fill="var(--muted)">${nf(totalHours, 0)} h contracted</text>
    <line x1="${P.l}" y1="24" x2="${x(totalHours).toFixed(1)}" y2="24" stroke="var(--grid)"/>
    <line x1="${x(c1.catalogued).toFixed(1)}" y1="24" x2="${x(c1.catalogued).toFixed(1)}" y2="${P.t + rowH * 3 - 8}" stroke="var(--rule-2)" stroke-width="1"/>
    ${body}
    <text x="${P.l}" y="${H - 12}" font-size="10.5" fill="var(--muted)">Hours per year. The dashed extension is work she does that this model cannot see yet.</text>
  </svg>`;

  const rows = scenarios.map((s, i) => [s.name, nf(c1.catalogued, 0),
    s.segs.map(g => esc(g.label) + " " + nf(g.hours, 0) + "h").join("; "),
    pct(s.util), s.cost > 0 ? usd(s.cost) : "—"]);
  return `<div class="chart-scroll">${svg}</div>` +
    legendHTML([...new Map(scenarios.flatMap(s => s.segs).map(g => [g.label, g])).values()]
      .map(g => ({ label: g.label, color: g.c }))
      .concat([{ label: "Unmapped — not yet in the model", color: "var(--rule-strong)" }])) +
    tableView(["Response", "Hours to rehome", "Where they land", "Resulting utilisation", "Annual cost"], rows);
}

/* ---- CHART 4: does the seat pay for itself ------------------------------ */
function chartSeat(model) {
  const c4 = model.case4;
  const W = 760, H = 210, P = { t: 34, r: 20, b: 46, l: 150 };
  const iw = W - P.l - P.r;
  const items = c4.protect.filter(p => p.value > 0);
  const total = c4.protectTotal;
  const xMax = Math.max(total, c4.seatCostLoaded) * 1.15;
  const x = v => P.l + (v / xMax) * iw;
  const bh = 30;

  let stack = "", acc = 0;
  items.forEach((p, i) => {
    const x0 = x(acc), w = Math.max(1, x(acc + p.value) - x0 - 2);
    stack += `<rect x="${x0.toFixed(1)}" y="${P.t + 44}" width="${w.toFixed(1)}" height="${bh}" fill="${sc(i)}" rx="1"
      data-tip="${tipRows(p.label, [["Value protected", usd(p.value)], ...(p.hours ? [["Hours", nf(p.hours, 0) + " h/yr"], ["Valued at", usd(p.rate, 2) + "/h"]] : [])])}"/>`;
    acc += p.value;
  });

  const costW = Math.max(2, x(c4.seatCostLoaded) - P.l - 2);
  const svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Cost of the operations seat against what it protects">
    <text x="${P.l - 12}" y="${P.t + 20}" text-anchor="end" font-size="11.5" font-weight="600" fill="var(--ink)">Cost of the seat</text>
    <rect x="${P.l}" y="${P.t + 4}" width="${costW.toFixed(1)}" height="${bh}" fill="var(--rule-strong)" rx="1"
      data-tip="${tipRows("Cost of the seat", [["Compensation delta", usd(c4.seatCompDelta)], ["Loaded", usd(c4.seatCostLoaded)]])}"/>
    <text x="${(P.l + costW + 9).toFixed(1)}" y="${P.t + 24}" font-size="11.5" font-weight="600" fill="var(--ink)">${usd(c4.seatCostLoaded)}</text>
    <text x="${P.l - 12}" y="${P.t + 64}" text-anchor="end" font-size="11.5" font-weight="600" fill="var(--ink)">What it protects</text>
    ${stack}
    <text x="${(x(total) + 9).toFixed(1)}" y="${P.t + 64}" font-size="11.5" font-weight="600" fill="var(--ink)">${usd(total)}</text>
    <line x1="${x(c4.seatCostLoaded).toFixed(1)}" y1="${P.t - 4}" x2="${x(c4.seatCostLoaded).toFixed(1)}" y2="${P.t + 88}" stroke="var(--warn)" stroke-width="1.5" stroke-dasharray="3 3"/>
    <text x="${x(c4.seatCostLoaded).toFixed(1)}" y="${P.t - 10}" text-anchor="middle" font-size="10" font-weight="600" fill="var(--warn)">break-even</text>
    <text x="${P.l}" y="${H - 14}" font-size="10.5" fill="var(--muted)">Everything right of the dashed line is surplus: ${usd(c4.surplus)} a year, or ${ratio(c4.breakEvenRatio)} the cost of the seat.</text>
  </svg>`;
  return `<div class="chart-scroll">${svg}</div>` +
    legendHTML([{ label: "Cost of the seat (loaded)", color: "var(--rule-strong)" },
      ...items.map((p, i) => ({ label: p.label, color: sc(i) }))]) +
    tableView(["Component", "Hours", "Valued at", "Value"],
      [...items.map(p => [p.label, p.hours ? nf(p.hours, 0) + " h" : "—", p.rate ? usd(p.rate, 2) : "—", usd(p.value)]),
       ["<b>Total protected</b>", "", "", "<b>" + usd(total) + "</b>"],
       ["Cost of the seat", "", "", usd(c4.seatCostLoaded)]]);
}

/* ---- CHART 5: sensitivity tornado --------------------------------------- */
function chartTornado(model) {
  const sens = sensitivity(INPUTS, state, "breakMonth");
  const rows = sens.rows.filter(r => r.lowOut !== null && r.highOut !== null);
  const W = 760, rowH = 34, P = { t: 36, r: 132, b: 40, l: 210 };
  const H = P.t + rowH * rows.length + P.b;
  const iw = W - P.l - P.r;
  const all = rows.flatMap(r => [r.lowOut, r.highOut]).concat([sens.baseValue]);
  const lo = Math.min(...all), hi = Math.max(...all);
  const pad = Math.max(1, (hi - lo) * 0.08);
  const x = v => P.l + ((v - (lo - pad)) / ((hi + pad) - (lo - pad))) * iw;
  const fmtLever = (r, v) => r.fmt === "pct" ? pct(v, 0) : nf(v, v < 10 ? 1 : 0);
  const outLabel = m => m > model.capacity.horizonMonths ? "no break in " + model.scenario.horizonYears + " yrs"
    : m <= 0 ? "already past" : nf(m, 0) + " mo";

  let body = "";
  rows.forEach((r, i) => {
    const yc = P.t + rowH * i + rowH / 2;
    const a = Math.min(r.lowOut, r.highOut), b = Math.max(r.lowOut, r.highOut);
    const xb = x(sens.baseValue);
    const worseW = Math.max(0, xb - x(a)), betterW = Math.max(0, x(b) - xb);
    body += `<text x="${P.l - 14}" y="${yc + 4}" text-anchor="end" font-size="11.5" fill="var(--ink)">${esc(r.label)}</text>`;
    if (worseW > 0.5) body += `<rect x="${x(a).toFixed(1)}" y="${yc - 9}" width="${worseW.toFixed(1)}" height="18" fill="var(--div-neg)" rx="2"
      data-tip="${tipRows(r.label + " → " + fmtLever(r, r.lowOut === a ? r.low : r.high), [["Capacity breaks in", outLabel(a)], ["vs base", outLabel(sens.baseValue)]])}"/>`;
    if (betterW > 0.5) body += `<rect x="${xb.toFixed(1)}" y="${yc - 9}" width="${betterW.toFixed(1)}" height="18" fill="var(--div-pos)" rx="2"
      data-tip="${tipRows(r.label + " → " + fmtLever(r, r.highOut === b ? r.high : r.low), [["Capacity breaks in", outLabel(b)], ["vs base", outLabel(sens.baseValue)]])}"/>`;
    body += `<text x="${(x(a) - 7).toFixed(1)}" y="${yc + 4}" text-anchor="end" font-size="10" fill="var(--muted)">${fmtLever(r, r.lowOut === a ? r.low : r.high)}</text>
      <text x="${(x(b) + 7).toFixed(1)}" y="${yc + 4}" text-anchor="start" font-size="10" fill="var(--muted)">${fmtLever(r, r.highOut === b ? r.high : r.low)}</text>`;
  });

  const xb = x(sens.baseValue);
  const svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Which assumptions move the capacity date most">
    <line x1="${xb.toFixed(1)}" y1="${P.t - 12}" x2="${xb.toFixed(1)}" y2="${P.t + rowH * rows.length + 4}" stroke="var(--rule-strong)" stroke-width="1.5"/>
    <text x="${xb.toFixed(1)}" y="${P.t - 18}" text-anchor="middle" font-size="10.5" font-weight="600" fill="var(--ink-2)">as filed: ${outLabel(sens.baseValue)}</text>
    ${body}
    <text x="${P.l}" y="${H - 14}" font-size="10.5" fill="var(--muted)">Months until operations capacity is exhausted, measured from the line marked as filed.</text>
  </svg>`;
  return `<div class="chart-scroll">${svg}</div>` +
    legendHTML([{ label: "Breaks sooner than filed", color: "var(--div-neg)" },
                { label: "Breaks later than filed", color: "var(--div-pos)" }]) +
    tableView(["Assumption", "Low value", "Breaks in", "High value", "Breaks in", "Swing (months)"],
      rows.map(r => [r.label, fmtLever(r, r.low), outLabel(r.lowOut), fmtLever(r, r.high), outLabel(r.highOut), nf(r.swing, 0)]));
}
