
/* ======================================================== SECTION RENDERERS */
function tile(label, value, sub, opts = {}) {
  return `<div class="tile${opts.alert ? " alert" : ""}">
    <div class="t-label">${esc(label)}</div>
    <div class="t-value">${value}</div>
    ${sub ? `<div class="t-sub">${sub}</div>` : ""}
    ${opts.ids ? provMeter(opts.ids, opts.model, { hours: opts.hours }) : ""}</div>`;
}
function verdict(text) {
  return `<div class="verdict"><span class="v-tag">The sentence this ends on</span>
    <div class="v-text">${text}</div></div>`;
}
const M = () => computeModel(INPUTS, state);

/* ---------------------------------------------------------------- START */
function renderStart(model) {
  const cap = model.capacity;
  $("#start-tiles").innerHTML =
    tile("The book", `${nf(model.book.totalHouseholds, 0)}`, `households · ${usdK(model.book.aumTotal)} AUM`, { ids: DEPS.revenue_total, model }) +
    tile("Revenue at the schedule", usdK(model.revenue.total), `${usd(model.revenue.perHousehold)} per household`, { ids: DEPS.revenue_total, model }) +
    tile("Operations utilisation", pct(cap.utilisation), `${nf(cap.required.total, 0)} h needed · ${nf(cap.available, 0)} h available`, { ids: DEPS.utilisation, model, hours: true, alert: cap.utilisation > 1 }) +
    tile("Capacity runs out", cap.breakDate ? longDate(cap.breakDate) : "not inside " + model.scenario.horizonYears + " years",
      cap.breakDate ? `at about ${nf(cap.breakHouseholds, 0)} households` : "at this growth rate", { ids: DEPS.capacity_break, model, hours: true, alert: cap.breakMonth !== null && cap.breakMonth < 24 });

  $("#start-integrity").innerHTML = caveatHTML([...new Set([...DEPS.utilisation, ...DEPS.cost_to_serve])]) ||
    `<div class="caveat soft"><span class="cv-tag">Note</span><span>Provenance is clean.</span></div>`;

  const cases = [
    ["01", "What happens in 100 days", `${nf(model.case1.catalogued, 0)} catalogued hours a year need a home, plus ${nf(model.case1.unmapped, 0)} the model cannot see yet.`],
    ["02", "Where capacity breaks", cap.breakDate ? `Around ${longDate(cap.breakDate)}, at about ${nf(cap.breakHouseholds, 0)} households.` : `Not inside the ${model.scenario.horizonYears}-year horizon at this growth rate.`],
    ["03", "What each tier costs to serve", model.underwaterLoaded.length ? `${model.underwaterLoaded.join(", ")} costs more to serve, fully loaded, than it produces.` : `No tier is underwater on the numbers as filed.`],
    ["04", "The operations seat", `Costs ${usd(model.case4.seatCostLoaded)} loaded. It has to protect that much to pay for itself.`],
  ];
  $("#start-cases").innerHTML = cases.map(([n, t, s]) =>
    `<div><div style="display:flex;gap:9px;align-items:baseline"><span class="oc-num">${n}</span>
      <b style="font-size:.9rem">${esc(t)}</b></div>
      <div style="font-size:.82rem;color:var(--muted);padding-left:26px">${esc(s)}</div></div>`).join("");

  const blind = [
    ["The expense lines", "I cannot see rent, technology, E&O, custodial platform fees or professional fees. Firm overhead per household is a placeholder, and it is the number that decides whether the bottom tier looks profitable."],
    ["What the consultant actually does", `Her catalogued work comes to ${nf(model.case1.catalogued, 0)} hours against roughly ${nf(model.case1.contracted, 0)} contracted. The ${nf(model.case1.unmapped, 0)}-hour gap is work I have not documented yet, not work that does not exist.`],
    ["Real task timings", `All ${INPUTS.tasks.length} rows in the task catalogue are placeholders. Every hour figure in this model rests on them.`],
    ["Fee realisation", "I have assumed every household pays the published schedule. Discounts, family aggregation and flat-fee exceptions are not in here."],
  ];
  $("#start-blind").innerHTML = blind.map(([t, s]) =>
    `<div><b style="font-size:.88rem">${esc(t)}</b><div style="font-size:.82rem;color:var(--muted)">${esc(s)}</div></div>`).join("");
}

/* ---------------------------------------------------------------- CASE 1 */
function renderCase1(model) {
  const c = model.case1, cap = model.capacity;
  $("#c1-tiles").innerHTML =
    tile("She leaves in", `${nf(c.daysAway, 0)} days`, longDate(c.departureDate), {}) +
    tile("Hours the catalogue has captured", nf(c.catalogued, 0) + " h", "per year, from her rows in the task catalogue", { ids: DEPS.consultant_hours, model, hours: true }) +
    tile("Hours it has not", nf(c.unmapped, 0) + " h", `against roughly ${nf(c.contracted, 0)} h contracted`, { alert: true }) +
    tile("If nothing changes", pct(c.options[0].utilisation), `${nf(c.options[0].hoursShort, 0)} h a year with no owner`, { alert: c.options[0].utilisation > 1 });

  $("#c1-gap").innerHTML = `<div class="caveat"><span class="cv-tag">Read this first</span><span>
    The catalogue accounts for ${nf(c.catalogued, 0)} of her roughly ${nf(c.contracted, 0)} contracted hours a year. The
    ${nf(c.unmapped, 0)}-hour difference is almost certainly real work I have not written down yet, not slack.
    <b>Everything below understates the problem by that amount.</b> Closing that gap is the single most
    valuable thing I can do in the ${nf(c.daysAway, 0)} days remaining, and it needs her help to do it.</span></div>`;

  $("#c1-chart").innerHTML = chartDeparture(model);

  $("#c1-options").innerHTML = c.options.map((o, i) => `
    <div class="optioncard${o.utilisation > 1 ? " flag" : ""}">
      <h4><span class="oc-num">0${i + 1}</span>${esc(o.label)}</h4>
      <div>
        <div class="kv"><span class="k">Annual cost</span><span class="v">${o.annualCost > 0 ? outFig(usd(o.annualCost), DEPS.seat) : "none"}</span></div>
        <div class="kv"><span class="k">Operations utilisation after</span><span class="v" style="${o.utilisation > 1 ? "color:var(--warn)" : ""}">${pct(o.utilisation)}</span></div>
        <div class="kv"><span class="k">Hours left with no owner</span><span class="v" style="${o.hoursShort > 0 ? "color:var(--warn)" : ""}">${nf(o.hoursShort, 0)} h</span></div>
        ${o.displacedHours ? `<div class="kv"><span class="k">Paraplanning work displaced</span><span class="v">${nf(o.displacedHours, 0)} h</span></div>` : ""}
      </div>
      <p style="font-size:.8rem;color:var(--muted);margin:0">${esc(o.costNote)}</p>
    </div>`).join("");

  $("#c1-verdict").innerHTML = verdict(
    `When she leaves, <b>${nf(c.catalogued, 0)} catalogued hours a year</b> need a home &mdash; and ${nf(c.unmapped, 0)} more
     that this model cannot see yet. Absorbing them puts operations at <b>${pct(c.options[0].utilisation)}</b> and leaves
     ${nf(c.options[0].hoursShort, 0)} hours with nobody on them. Backfilling costs ${usd(c.options[1].annualCost)} a year.
     Moving me into the seat costs ${usd(c.options[2].annualCost)} and displaces ${nf(c.options[2].displacedHours, 0)} hours
     of the planning work I do now.`) + caveatHTML(DEPS.consultant_hours);
}

/* ---------------------------------------------------------------- CASE 2 */
function renderCase2(model) {
  const cap = model.capacity;
  $("#c2-tiles").innerHTML =
    tile("Utilisation today", pct(cap.utilisation), `${nf(cap.required.total, 0)} h required of ${nf(cap.available, 0)} h`, { ids: DEPS.utilisation, model, hours: true, alert: cap.utilisation > 1 }) +
    tile("Capacity breaks at", cap.breakHouseholds ? nf(cap.breakHouseholds, 0) : "—", cap.breakHouseholds ? `households, from ${nf(model.book.totalHouseholds, 0)} today` : "no break in horizon", { ids: DEPS.capacity_break, model }) +
    tile("Which is around", cap.breakDate ? longDate(cap.breakDate) : "beyond the horizon", cap.breakMonth !== null ? `${nf(cap.breakMonthFrac, 0)} months away` : `at ${pct(model.scenario.growth, 0)} growth`, { ids: DEPS.capacity_break, model, alert: cap.breakMonth !== null && cap.breakMonth < 24 }) +
    tile("Fixed vs variable", `${nf(cap.perHouseholdHours, 1)} h`, `per additional household · ${nf(cap.fixedHours, 0)} h fixed firm-level`, { ids: DEPS.hours_required, model, hours: true });

  $("#c2-chart").innerHTML = chartCapacity(model);

  const rates = [0.10, 0.15, 0.20];
  $("#c2-sens").innerHTML = `<div class="tscroll"><table class="data" style="min-width:0">
    <thead><tr><th>Growth rate</th><th class="n">Households at the break</th><th class="n">Date</th><th class="n">Months away</th></tr></thead>
    <tbody>${rates.map(g => {
      const m2 = computeModel(INPUTS, { ...state, growth: g });
      const on = Math.abs(g - model.scenario.growth) < 1e-9;
      return `<tr${on ? ' style="background:var(--accent-soft)"' : ""}><td>${pct(g, 0)}${on ? " <span class=\"pill ok\">as filed</span>" : ""}</td>
        <td class="n">${m2.capacity.breakHouseholds ? nf(m2.capacity.breakHouseholds, 0) : "—"}</td>
        <td class="n">${m2.capacity.breakDate ? longDate(m2.capacity.breakDate) : "beyond horizon"}</td>
        <td class="n">${m2.capacity.breakMonth !== null ? nf(m2.capacity.breakMonthFrac, 0) : "—"}</td></tr>`;
    }).join("")}</tbody></table></div>
    <p style="font-size:.78rem;color:var(--muted);margin-top:9px">Growth is the only thing changing between these
    rows. The household count at the break moves as well as the date, because faster growth means more onboarding
    work arriving alongside the larger book.</p>`;

  $("#c2-coverage").innerHTML = `<div class="tscroll"><table class="data" style="min-width:0">
    <thead><tr><th>Role</th><th class="n">Hours available</th><th class="n">Catalogued</th><th class="n">Accounted for</th></tr></thead>
    <tbody>${cap.coverage.map(c => `<tr data-soft="${c.pct < 0.8 ? 1 : 0}">
      <td>${esc(L(c.role_id))}</td><td class="n">${nf(c.available, 0)}</td><td class="n">${nf(c.catalogued, 0)}</td>
      <td class="n"><span class="pill ${c.pct >= 0.8 ? "ok" : "bad"}">${pct(c.pct, 0)}</span></td></tr>`).join("")}</tbody></table></div>
    <p style="font-size:.78rem;color:var(--muted);margin-top:9px">Anything well under 100% means I have not yet
    written down what that person does. It is a gap in my catalogue, not spare time on their calendar &mdash; and
    every one of those gaps makes the capacity date above <b>later than it really is</b>.</p>`;

  $("#c2-tornado").innerHTML = chartTornado(model);

  $("#c2-verdict").innerHTML = verdict(cap.breakDate
    ? `At ${pct(model.scenario.growth, 0)} growth, operations runs out of capacity at <b>${nf(cap.breakHouseholds, 0)} households</b>,
       around <b>${longDate(cap.breakDate)}</b> &mdash; ${nf(cap.breakMonthFrac, 0)} months from now.`
    : `At ${pct(model.scenario.growth, 0)} growth, operations does not run out of capacity inside the
       ${model.scenario.horizonYears}-year horizon. Utilisation settles at ${pct(cap.projection[cap.projection.length - 1].utilisation)}.`)
    + caveatHTML(DEPS.capacity_break);
}

/* ---------------------------------------------------------------- CASE 3 */
function renderCase3(model) {
  const oh = ATOM_BY_ID["const.firm_overhead_per_household"];
  $("#c3-warning").innerHTML = `<div class="caveat"><span class="cv-tag">Before reading this</span><span>
    The largest single layer in the cost stack below is non-payroll firm overhead, set at
    ${fig(usd(model.scenario.firmOverheadPerHousehold), "PLACEHOLDER", "const.firm_overhead_per_household")} per household.
    <b>I invented that number.</b> I cannot see the expense lines. It decides on its own whether the bottom tier
    looks profitable, so the honest version of this screen is: tell me the real figure and I will rerun it in
    front of you. Move the overhead slider to nothing and ${model.tiers.filter(t => t.revenuePerHousehold - (t.costTotalLoaded - model.scenario.firmOverheadPerHousehold) < 0).length === 0 ? "every tier is above water" : "the picture changes"}.</span></div>`;

  $("#c3-chart").innerHTML = chartTiers(model);

  $("#c3-table").innerHTML = `<div class="tscroll"><table class="data">
    <thead><tr><th>Tier</th><th class="n">Households</th><th class="n">Avg AUM</th><th class="n">Revenue</th>
      <th class="n">Ops hours</th><th class="n">Direct ops</th><th class="n">Firm ops share</th>
      <th class="n">Advisor time</th><th class="n">Firm overhead</th><th class="n">Loaded total</th><th class="n">Margin</th></tr></thead>
    <tbody>${model.tiers.map(t => `<tr>
      <td><b>${t.tier}</b> ${esc(t.label)}</td>
      <td class="n">${nf(t.households, 0)}</td><td class="n">${usdK(t.avgAum)}</td>
      <td class="n">${usd(t.revenuePerHousehold)}</td>
      <td class="n">${nf(t.directHours, 1)}</td>
      <td class="n">${usd(t.costLayers.directOps)}</td><td class="n">${usd(t.costLayers.allocFirm)}</td>
      <td class="n">${usd(t.costLayers.advisory)}</td><td class="n">${usd(t.costLayers.firmOverhead)}</td>
      <td class="n">${usd(t.costTotalLoaded)}</td>
      <td class="n ${t.marginLoaded < 0 ? "neg" : ""}">${usd(t.marginLoaded)}</td></tr>`).join("")}
      <tr class="total"><td>Whole book</td><td class="n">${nf(model.book.totalHouseholds, 0)}</td>
        <td class="n">${usdK(model.book.aumTotal / model.book.totalHouseholds)}</td>
        <td class="n">${usd(model.revenue.perHousehold)}</td>
        <td class="n">${nf(model.tiers.reduce((a, t) => a + t.directHours * t.households, 0) / model.book.totalHouseholds, 1)}</td>
        <td class="n" colspan="5"></td>
        <td class="n">${usd(model.tiers.reduce((a, t) => a + t.costTotalLoaded * t.households, 0) / model.book.totalHouseholds)}</td>
        <td class="n">${usd(model.tiers.reduce((a, t) => a + t.marginLoaded * t.households, 0) / model.book.totalHouseholds)}</td></tr>
    </tbody></table></div>
    <p style="font-size:.78rem;color:var(--muted);margin-top:9px">Onboarding is deliberately not in these figures.
    A new ${model.tiers[2].tier} household costs about ${usd(model.tiers[2].onboardingCost)} of operations time to bring on,
    once. Smearing that across the existing book would overstate what a settled household costs.</p>`;

  const t1 = model.tiers[0];
  const opts = [
    ["Raise the minimum", `Stop taking households below a threshold. Protects capacity and margin. Costs the firm its pipeline: a ${t1.tier} household today is sometimes a ${model.tiers[2].tier} household in ten years, and referrals come from families, not balances.`],
    ["Serve that tier differently", `Keep them, change the service model: fewer scheduled meetings, group or digital review, a defined service tier. Cuts the ${nf(t1.directHours, 1)} operations hours a ${t1.tier} household takes now. Costs consistency, and someone has to tell them.`],
    ["Accept it as a pipeline cost", `Decide the ${usd(Math.abs(t1.marginLoaded))} a year is what the firm pays for relationships, referrals and the next generation. Perfectly defensible &mdash; but it should be a decision somebody made, not an accident of never having counted.`],
  ];
  $("#c3-options").innerHTML = opts.map(([t, s], i) =>
    `<div class="optioncard"><h4><span class="oc-num">0${i + 1}</span>${esc(t)}</h4>
      <p style="font-size:.83rem;color:var(--ink-2);margin:0">${s}</p></div>`).join("");

  $("#c3-verdict").innerHTML = verdict(
    `The bottom tier costs roughly <b>${usd(t1.costTotalLoaded)}</b> a year to serve on a fully loaded basis and produces
     <b>${usd(t1.revenuePerHousehold)}</b>. That is a decision, not a finding, and there are three versions of it above.
     ${t1.marginDirect >= 0 ? `On direct operations cost alone it is still ${usd(t1.marginDirect)} ahead &mdash; the gap is created by overhead and advisor time, not by the operations team.` : ""}`)
    + caveatHTML(DEPS.cost_to_serve);
}

/* ---------------------------------------------------------------- CASE 4 */
function renderCase4(model) {
  const c4 = model.case4;
  $("#c4-tiles").innerHTML =
    tile("The seat costs", usd(c4.seatCostLoaded), `${usd(c4.seatCompDelta)} compensation delta, loaded at ${pct(model.scenario.benefitsLoad, 0)}`, { ids: ["const.ops_seat_comp", "roster.R4.comp", "const.benefits_load"], model }) +
    tile("It has to protect", usd(c4.seatCostLoaded), "to pay for itself", {}) +
    tile("On these numbers it protects", usd(c4.protectTotal), `${ratio(c4.breakEvenRatio)} the cost of the seat`, { ids: DEPS.seat, model, hours: true }) +
    tile("Capacity headroom it buys", c4.monthsOfHeadroom !== null ? nf(c4.monthsOfHeadroom, 0) + " months" : "beyond horizon",
      "before the capacity date returns", { ids: DEPS.capacity_break, model });

  $("#c4-chart").innerHTML = chartSeat(model);

  $("#c4-table").innerHTML = `<div class="tscroll"><table class="data" style="min-width:0">
    <thead><tr><th>What it protects</th><th class="n">Hours</th><th class="n">Valued at</th><th class="n">Per year</th></tr></thead>
    <tbody>${c4.protect.map(p => `<tr><td>${esc(p.label)}${p.note ? `<div style="font-size:.74rem;color:var(--muted)">${esc(p.note)}</div>` : ""}</td>
      <td class="n">${p.hours !== null ? nf(p.hours, 0) : "—"}</td>
      <td class="n">${p.rate ? usd(p.rate, 2) : "—"}</td>
      <td class="n">${usd(p.value)}</td></tr>`).join("")}
      <tr class="total"><td>Total protected</td><td class="n"></td><td class="n"></td><td class="n">${usd(c4.protectTotal)}</td></tr>
      <tr><td>Cost of the seat, loaded</td><td class="n"></td><td class="n"></td><td class="n">${usd(c4.seatCostLoaded)}</td></tr>
      <tr class="total"><td>Surplus</td><td class="n"></td><td class="n"></td>
        <td class="n ${c4.surplus < 0 ? "neg" : ""}">${usd(c4.surplus)}</td></tr>
    </tbody></table></div>
    <p style="font-size:.78rem;color:var(--muted);margin-top:9px">Advisor hours are valued at
    <b>${usd(c4.advisorLoadedHourly, 2)}</b>, what they cost the firm &mdash; not at
    ${usd(c4.revenuePerAdvisorHour, 2)}, what an advisor hour earns. The larger number is the one that gets
    challenged, because it assumes the returned hour would have been sold. I have used the smaller one on purpose.</p>`;

  const displaced = c4.displacedParaplanningHours;
  const backfillCost = INPUTS.constants.paraplanning_backfill_comp
    ? INPUTS.constants.paraplanning_backfill_comp.v * (1 + model.scenario.benefitsLoad) * (displaced / model.scenario.productiveHours) : null;
  $("#c4-displace").innerHTML = `
    <p class="prose" style="font-size:.87rem;margin-bottom:12px">Moving me into the seat takes my operations share
    from ${pct(INPUTS.roster.find(r => r.role_id === "R4").ops_allocation, 0)} to ${pct(model.scenario.seatOpsAllocation, 0)}.
    That frees <b>${nf(displaced, 0)} hours a year</b> of operations capacity &mdash; and it displaces the same
    ${nf(displaced, 0)} hours of paraplanning work. That work does not disappear. There are three places it can go,
    and one of them cancels the whole proposal.</p>
    <div class="stack gap-8">
      <div class="kv"><span class="k">Advisors absorb it (at ${usd(c4.advisorLoadedHourly, 0)}/h)</span>
        <span class="v" style="color:var(--warn)">${usd(displaced * c4.advisorLoadedHourly)} a year</span></div>
      <div class="kv"><span class="k">A junior hire absorbs it</span><span class="v">${backfillCost ? usd(backfillCost) : "needs a number"}</span></div>
      <div class="kv"><span class="k">The firm decides some of it stops</span><span class="v">free, but somebody has to choose</span></div>
    </div>
    <div class="caveat" style="margin-top:12px"><span class="cv-tag">Say this out loud</span><span>
      If advisors absorb the displaced planning work, this proposal <b>costs</b> the firm
      ${usd(displaced * c4.advisorLoadedHourly - c4.protectTotal + c4.seatCostLoaded)} rather than saving anything.
      The seat only works if the paraplanning either stops or gets cheaper hands. That is the question to put to him,
      and it is better that I raise it than that he finds it.</span></div>`;

  $("#c4-verdict").innerHTML = verdict(
    `The seat costs <b>${usd(c4.seatCostLoaded)}</b> loaded. It has to protect <b>${usd(c4.seatCostLoaded)}</b> to pay for
     itself. On these numbers it protects ${usd(c4.protectTotal)} &mdash; ${nf(c4.protect[1].hours, 0)} advisor hours moved off
     operations work and ${nf(c4.protect[0].hours, 0)} of the consultant's hours covered in-house &mdash; but only if the
     ${nf(displaced, 0)} hours of planning work it displaces are not simply handed back to the advisors.`)
    + caveatHTML(DEPS.seat);
}
