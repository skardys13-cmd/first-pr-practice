/* ===========================================================================
   OPERATIONS CAPACITY & ECONOMICS ENGINE
   Pure functions. No DOM, no globals, no hard-coded firm numbers.
   Every number this file produces comes from inputs.json via the `I` argument.
   =========================================================================== */

export const TIER_IDS = ["T1", "T2", "T3", "T4"];

/* --- 1. TIERED (MARGINAL) FEE ------------------------------------------- */
/* Each band charges its own rate on the PORTION of assets inside that band.
   A flat rate on total assets is a different and wrong model. The unit test
   in verify.mjs pins the "just above a breakpoint" case, which is where a
   flat-rate model silently substitutes itself for a tiered one.            */
export function tieredFee(aum, bands) {
  if (!(aum > 0)) return 0;
  let fee = 0;
  for (const b of bands) {
    const top = (b.to === null || b.to === undefined) ? Infinity : b.to;
    const inBand = Math.min(aum, top) - b.from;
    if (inBand > 0) fee += inBand * b.rate;
    if (aum <= top) break;
  }
  return fee;
}

/* Returns the band-by-band working, for showing the arithmetic on screen. */
export function tieredFeeWorking(aum, bands) {
  const rows = [];
  let fee = 0;
  for (const b of bands) {
    const top = (b.to === null || b.to === undefined) ? Infinity : b.to;
    const inBand = Math.max(0, Math.min(aum, top) - b.from);
    if (inBand > 0) {
      const amt = inBand * b.rate;
      fee += amt;
      rows.push({ from: b.from, to: top, rate: b.rate, assets: inBand, fee: amt });
    }
    if (aum <= top) break;
  }
  return { rows, fee, effectiveRate: aum > 0 ? fee / aum : 0 };
}

/* --- 2. SCENARIO DEFAULTS ------------------------------------------------ */
export function defaultScenario(I) {
  const c = I.constants;
  return {
    growth: c.growth_rate_households.v,
    feeRealisation: c.fee_realisation.v,
    efficiency: 1.0,
    benefitsLoad: c.benefits_load.v,
    productiveHours: c.productive_hours_year.v,
    switchingUplift: c.switching_uplift.v,
    firmOverheadPerHousehold: c.firm_overhead_per_household.v,
    consultantPresent: true,
    response: "absorb",          // absorb | backfill | internal
    extraOpsFte: 0,
    blendedOpsHourlyOverride: null,
    horizonYears: 6,
    seatOpsAllocation: 0.85,     // R4's ops share if they take the operations seat
    advisorHourBasis: c.advisor_hour_basis.v,     // R4's ops share if they take the operations seat
  };
}

export const PRESETS = {
  today:      { label: "Today",                        consultantPresent: true,  response: "absorb"   },
  gone:       { label: "She's gone, nothing changes",  consultantPresent: false, response: "absorb"   },
  seat:       { label: "She's gone, I own operations", consultantPresent: false, response: "internal" },
};

/* --- 3. EFFECTIVE ROSTER ------------------------------------------------- */
/* Applies the scenario to the roster: removes the consultant, adds a backfill,
   or promotes the paraplanner into the operations seat.                     */
export function effectiveRoster(I, s) {
  const rows = I.roster.map(r => ({ ...r }));
  const out = [];
  for (const r of rows) {
    if (r.role_id === "R7") {
      if (!s.consultantPresent) continue;         // she has left
      out.push(r);
      continue;
    }
    if (r.role_id === "R4" && s.response === "internal" && !s.consultantPresent) {
      out.push({ ...r,
        ops_allocation: s.seatOpsAllocation,
        comp: I.constants.ops_seat_comp.v,
        seat_holder: true });
      continue;
    }
    out.push(r);
  }
  if (!s.consultantPresent && s.response === "backfill") {
    const orig = I.roster.find(r => r.role_id === "R7");
    out.push({ role_id: "R8", fte: orig.fte, fte_tag: "ESTIMATED",
      is_advisor: false, is_operations: true, ops_allocation: 1.0,
      comp: I.constants.backfill_consultant_cost.v, comp_tag: "PLACEHOLDER",
      is_contractor: true, end_date: null, backfill: true });
  }
  /* Negative headcount removes operations time, largest contributor first, so
     "what if we lose the service associate too" is a scenario the model can be
     asked - including the degenerate case of no operations capacity at all.  */
  if (s.extraOpsFte < 0) {
    let remove = -s.extraOpsFte;
    const ops = out.filter(r => r.is_operations && r.fte > 0)
      .sort((a, b) => (b.fte * b.ops_allocation) - (a.fte * a.ops_allocation));
    for (const r of ops) {
      if (remove <= 1e-9) break;
      const has = r.fte * r.ops_allocation;
      const take = Math.min(has, remove);
      r.ops_allocation = Math.max(0, (has - take) / r.fte);
      remove -= take;
    }
  }
  if (s.extraOpsFte > 0) {
    out.push({ role_id: "R9", fte: s.extraOpsFte, fte_tag: "ESTIMATED",
      is_advisor: false, is_operations: true, ops_allocation: 1.0,
      comp: I.constants.ops_seat_comp.v * s.extraOpsFte, comp_tag: "PLACEHOLDER",
      is_contractor: false, end_date: null, extra: true });
  }
  return out;
}

/* Loaded hourly cost for one role. Contractors carry no benefits load.
   Divides by the role's OWN hours (fte x productive hours), not by a full
   year, so a fractional role is not costed as if it were full time.        */
export function loadedHourly(role, s) {
  const hours = role.fte * s.productiveHours;
  if (!(hours > 0)) return 0;
  const load = role.is_contractor ? 0 : s.benefitsLoad;
  return (role.comp * (1 + load)) / hours;
}
export function loadedCost(role, s) {
  return role.comp * (1 + (role.is_contractor ? 0 : s.benefitsLoad));
}
/* Hours a role actually gives to operations. */
export function opsHoursOf(role, s) {
  return role.is_operations ? role.fte * role.ops_allocation * s.productiveHours : 0;
}

/* --- 4. TASK MINUTES ----------------------------------------------------- */
/* Per-household RECURRING operations minutes for one tier (household + account
   basis). Onboarding is deliberately excluded here - it is a one-off per new
   household, reported separately, never smeared across the existing book.   */
function minutesFor(I, s, tier, { basis, workType, ownerFilter }) {
  const bk = I.book.find(b => b.tier === tier);
  let mins = 0;
  for (const t of I.tasks) {
    if (t.work_type !== workType) continue;
    if (!basis.includes(t.basis)) continue;
    if (t.basis !== "firm" && !t.tiers.includes(tier)) continue;
    if (ownerFilter && !ownerFilter(t.owner)) continue;
    let m = t.minutes * s.efficiency * t.occurrences;
    if (t.basis === "account") m *= bk.accounts_per_household;
    mins += m;
  }
  return mins;
}
function firmMinutes(I, s, { workType = "operations", ownerFilter } = {}) {
  let mins = 0;
  for (const t of I.tasks) {
    if (t.work_type !== workType || t.basis !== "firm") continue;
    if (ownerFilter && !ownerFilter(t.owner)) continue;
    mins += t.minutes * s.efficiency * t.occurrences;
  }
  return mins;
}

export function tierMinutes(I, s, tier, ownerFilter) {
  return {
    recurringOps: minutesFor(I, s, tier, { basis: ["household", "account"], workType: "operations", ownerFilter }),
    onboardingOps: minutesFor(I, s, tier, { basis: ["new_household"], workType: "operations", ownerFilter }),
    advisory: minutesFor(I, s, tier, { basis: ["household", "account"], workType: "advisory", ownerFilter }),
  };
}

/* --- 5. OPERATIONS HOURS REQUIRED --------------------------------------- */
/* households: {T1:n,...}. newHouseholds: total new this year (split by new_mix).
   The switching uplift applies to operations work only - a timed task measures
   the task, not the day.                                                    */
export function opsHoursRequired(I, s, households, newTotal, ownerFilter) {
  let recurring = 0, onboarding = 0;
  for (const tier of TIER_IDS) {
    const bk = I.book.find(b => b.tier === tier);
    const m = tierMinutes(I, s, tier, ownerFilter);
    recurring += (households[tier] || 0) * m.recurringOps;
    onboarding += (newTotal * bk.new_mix) * m.onboardingOps;
  }
  const firm = firmMinutes(I, s, { ownerFilter });
  const up = 1 + s.switchingUplift;
  return {
    recurring: recurring / 60 * up,
    onboarding: onboarding / 60 * up,
    firm: firm / 60 * up,
    total: (recurring + onboarding + firm) / 60 * up,
  };
}

/* --- 6. THE FULL MODEL --------------------------------------------------- */
export function computeModel(I, scenario) {
  const s = { ...defaultScenario(I), ...scenario };
  const bands = I.fee_schedule.bands;
  const roster = effectiveRoster(I, s);

  /* -- guardrails: the model must fail loudly, never quietly ------------- */
  const errors = [];
  if (!(s.productiveHours > 0)) errors.push("Productive hours per year is zero or negative. Every hourly rate and every capacity figure divides by it.");
  const opsRoles = roster.filter(r => r.is_operations);
  const opsHoursAvailable = opsRoles.reduce((a, r) => a + opsHoursOf(r, s), 0);
  if (!(opsHoursAvailable > 0)) errors.push("There is no operations capacity at all: every operations role is removed or allocated zero time. Utilisation, cost to serve and the capacity date cannot be computed - there is nobody to do the work.");
  const advisors = roster.filter(r => r.is_advisor);
  if (advisors.length === 0) errors.push("There are no advisor roles, so revenue per advisor cannot be computed.");

  const households0 = {};
  for (const b of I.book) households0[b.tier] = b.households;
  const totalHouseholds0 = TIER_IDS.reduce((a, t) => a + households0[t], 0);
  if (!(totalHouseholds0 > 0)) errors.push("Household count is zero. There is no book to model.");

  if (errors.length) return { failed: true, errors, scenario: s };

  /* -- rates ------------------------------------------------------------- */
  const blendedOpsHourlyAuto = opsRoles.reduce((a, r) => a + opsHoursOf(r, s) * loadedHourly(r, s), 0) / opsHoursAvailable;
  const blendedOpsHourly = (s.blendedOpsHourlyOverride != null && s.blendedOpsHourlyOverride > 0)
    ? s.blendedOpsHourlyOverride : blendedOpsHourlyAuto;
  const advisorHoursTotal = advisors.reduce((a, r) => a + r.fte * s.productiveHours, 0);
  const advisorLoadedHourly = advisorHoursTotal > 0
    ? advisors.reduce((a, r) => a + loadedCost(r, s), 0) / advisorHoursTotal : 0;

  /* -- revenue ----------------------------------------------------------- */
  const tiers = I.book.map(b => {
    const gross = tieredFee(b.avg_aum, bands);
    const net = gross * s.feeRealisation;
    return { tier: b.tier, label: b.label, households: b.households, avgAum: b.avg_aum,
      accountsPerHousehold: b.accounts_per_household, newMix: b.new_mix,
      totalAum: b.households * b.avg_aum,
      feeGross: gross, revenuePerHousehold: net,
      effectiveRate: b.avg_aum > 0 ? net / b.avg_aum : 0,
      revenueTier: net * b.households };
  });
  const revenueTotal = tiers.reduce((a, t) => a + t.revenueTier, 0);
  const aumTotal = tiers.reduce((a, t) => a + t.totalAum, 0);
  const totalFte = roster.reduce((a, r) => a + r.fte, 0);

  /* -- capacity today ---------------------------------------------------- */
  const newTotal0 = totalHouseholds0 * s.growth;
  const req0 = opsHoursRequired(I, s, households0, newTotal0);
  const utilisation = req0.total / opsHoursAvailable;

  /* Where the operations work currently sits, by owner. */
  const roleIds = [...new Set(I.tasks.map(t => t.owner))];
  const hoursByOwner = {};
  for (const rid of roleIds) {
    hoursByOwner[rid] = opsHoursRequired(I, s, households0, newTotal0, o => o === rid).total;
  }
  const advisorIds = new Set(I.roster.filter(r => r.is_advisor).map(r => r.role_id));
  const opsOnAdvisors = Object.entries(hoursByOwner)
    .filter(([rid]) => advisorIds.has(rid))
    .reduce((a, [, h]) => a + h, 0);

  /* Coverage check: catalogued hours per role vs the hours that role has.
     A large gap means the catalogue is incomplete, not that the role is idle. */
  const coverage = roster.filter(r => r.is_operations).map(r => {
    const have = opsHoursOf(r, s);
    const catalogued = hoursByOwner[r.role_id] || 0;
    return { role_id: r.role_id, available: have, catalogued,
      gap: have - catalogued, pct: have > 0 ? catalogued / have : 0 };
  });

  /* -- projection & capacity break --------------------------------------- */
  const months = s.horizonYears * 12;
  const gm = s.growth > -1 ? Math.pow(1 + s.growth, 1 / 12) - 1 : 0;
  const proj = [];
  let hh = { ...households0 };
  let breakMonth = null, breakHouseholds = null;
  const asOf = new Date(I.meta.as_of + "T00:00:00Z");

  for (let m = 0; m <= months; m++) {
    const totalH = TIER_IDS.reduce((a, t) => a + hh[t], 0);
    const newAnnual = totalH * s.growth;
    const r = opsHoursRequired(I, s, hh, newAnnual);
    const d = new Date(asOf); d.setUTCMonth(d.getUTCMonth() + m);
    proj.push({ month: m, date: d.toISOString().slice(0, 10), households: totalH,
      required: r.total, available: opsHoursAvailable, utilisation: r.total / opsHoursAvailable });
    if (breakMonth === null && r.total >= opsHoursAvailable) {
      breakMonth = m; breakHouseholds = totalH;
    }
    const added = totalH * gm;
    for (const t of TIER_IDS) hh[t] += added * (I.book.find(b => b.tier === t).new_mix);
  }

  /* Sub-month interpolation, so the household count and the date describe the
     SAME crossing rather than two nearby ones.                              */
  let breakDateExact = null, breakHouseholdsInterp = null, breakMonthFrac = null;
  if (breakMonth !== null) {
    if (breakMonth === 0) {
      breakMonthFrac = 0; breakHouseholdsInterp = proj[0].households; breakDateExact = proj[0].date;
    } else {
      const a = proj[breakMonth - 1], b = proj[breakMonth];
      const span = (b.required - a.required);
      const f = span > 0 ? (opsHoursAvailable - a.required) / span : 0;
      breakMonthFrac = (breakMonth - 1) + f;
      breakHouseholdsInterp = a.households + f * (b.households - a.households);
      const d = new Date(asOf);
      d.setUTCDate(d.getUTCDate() + Math.round(breakMonthFrac * 30.4375));
      breakDateExact = d.toISOString().slice(0, 10);
    }
  }

  /* Households at which capacity breaks, holding today's mix (the count the
     firm can act on). Solved directly rather than read off the projection.  */
  const perHhAtMix = (() => {
    const unit = {}; for (const t of TIER_IDS) unit[t] = households0[t] / totalHouseholds0;
    const r1 = opsHoursRequired(I, s, unit, 1 * s.growth);
    return r1.total - opsHoursRequired(I, s, { T1: 0, T2: 0, T3: 0, T4: 0 }, 0).total;
  })();
  const fixedHours = opsHoursRequired(I, s, { T1: 0, T2: 0, T3: 0, T4: 0 }, 0).total;
  const breakHouseholdsExact = perHhAtMix > 0
    ? (opsHoursAvailable - fixedHours) / perHhAtMix : null;

  const capacity = {
    required: req0, available: opsHoursAvailable, utilisation,
    hoursByOwner, opsOnAdvisors, coverage, projection: proj,
    breakMonth, breakMonthFrac,
    breakHouseholds: breakHouseholdsInterp,
    breakHouseholdsStepped: breakHouseholds,
    breakHouseholdsExact,
    breakDate: breakDateExact,
    breakDateStepped: breakMonth === null ? null : proj[breakMonth].date,
    alreadyOver: utilisation >= 1,
    noBreak: breakMonth === null,
    horizonMonths: months,
    fixedHours, perHouseholdHours: perHhAtMix,
  };

  /* -- cost to serve, layer by layer ------------------------------------- */
  const firmOpsHours = req0.firm;
  const allocFirmPerHh = (firmOpsHours * blendedOpsHourly) / totalHouseholds0;
  const up = 1 + s.switchingUplift;

  const tierEcon = tiers.map(t => {
    const m = tierMinutes(I, s, t.tier);
    const directHours = m.recurringOps / 60 * up;
    const onboardHours = m.onboardingOps / 60 * up;
    const advisoryHours = m.advisory / 60;
    const directOps = directHours * blendedOpsHourly;
    const advisory = advisoryHours * advisorLoadedHourly;
    const firmOh = s.firmOverheadPerHousehold;
    const totalLoaded = directOps + allocFirmPerHh + advisory + firmOh;
    return { ...t, directHours, onboardHours, advisoryHours,
      onboardingCost: onboardHours * blendedOpsHourly,
      costLayers: { directOps, allocFirm: allocFirmPerHh, advisory, firmOverhead: firmOh },
      costDirect: directOps,
      costOpsFull: directOps + allocFirmPerHh,
      costTotalLoaded: totalLoaded,
      marginDirect: t.revenuePerHousehold - directOps,
      marginLoaded: t.revenuePerHousehold - totalLoaded };
  });
  const underwaterDirect = tierEcon.filter(t => t.marginDirect < 0).map(t => t.tier);
  const underwaterLoaded = tierEcon.filter(t => t.marginLoaded < 0).map(t => t.tier);

  /* -- CASE 1: the consultant's departure --------------------------------- */
  const consultant = I.roster.find(r => r.role_id === "R7");
  const consultantCatalogued = opsHoursRequired(I, s, households0, newTotal0, o => o === "R7").total;
  const consultantContracted = consultant.fte * s.productiveHours;
  const consultantUnmapped = Math.max(0, consultantContracted - consultantCatalogued);

  function utilUnder(opts) {
    const sc = { ...s, ...opts };
    const rs = effectiveRoster(I, sc);
    const avail = rs.filter(r => r.is_operations).reduce((a, r) => a + opsHoursOf(r, sc), 0);
    const req = opsHoursRequired(I, sc, households0, newTotal0).total;
    return { available: avail, required: req, utilisation: avail > 0 ? req / avail : Infinity, roster: rs };
  }
  const base = utilUnder({ consultantPresent: true, response: "absorb" });
  const optAbsorb = utilUnder({ consultantPresent: false, response: "absorb" });
  const optBackfill = utilUnder({ consultantPresent: false, response: "backfill" });
  const optInternal = utilUnder({ consultantPresent: false, response: "internal" });

  const r4 = I.roster.find(r => r.role_id === "R4");
  const seatCompDelta = I.constants.ops_seat_comp.v - r4.comp;
  const seatCostLoaded = seatCompDelta * (1 + s.benefitsLoad);
  const displacedParaplanningHours = (s.seatOpsAllocation - r4.ops_allocation) * r4.fte * s.productiveHours;

  const case1 = {
    departureDate: consultant.end_date,
    daysAway: I.constants.consultant_departure_days.v,
    catalogued: consultantCatalogued,
    contracted: consultantContracted,
    unmapped: consultantUnmapped,
    baseUtilisation: base.utilisation,
    options: [
      { key: "absorb", label: "Absorb across the existing team",
        annualCost: 0, costNote: "No new spend. The hours land on the people already here.",
        available: optAbsorb.available, utilisation: optAbsorb.utilisation,
        hoursShort: Math.max(0, optAbsorb.required - optAbsorb.available) },
      { key: "backfill", label: "Backfill with a like-for-like hire",
        annualCost: I.constants.backfill_consultant_cost.v,
        costNote: "Replaces her hours at the same cost. Break-even is immediate by construction - the question is whether the hours come back.",
        available: optBackfill.available, utilisation: optBackfill.utilisation,
        hoursShort: Math.max(0, optBackfill.required - optBackfill.available) },
      { key: "internal", label: "I take it on",
        annualCost: seatCostLoaded,
        costNote: `Compensation delta only, loaded. Displaces ${Math.round(displacedParaplanningHours)} hours a year of paraplanning work that has to go somewhere.`,
        available: optInternal.available, utilisation: optInternal.utilisation,
        hoursShort: Math.max(0, optInternal.required - optInternal.available),
        displacedHours: displacedParaplanningHours },
    ],
  };

  /* -- CASE 4: the operations seat ---------------------------------------- */
  const postDepartureBlended = (() => {
    const sc = { ...s, consultantPresent: false, response: "internal" };
    const rs = effectiveRoster(I, sc).filter(r => r.is_operations);
    const h = rs.reduce((a, r) => a + opsHoursOf(r, sc), 0);
    return h > 0 ? rs.reduce((a, r) => a + opsHoursOf(r, sc) * loadedHourly(r, sc), 0) / h : 0;
  })();
  const protectConsultant = consultantCatalogued * postDepartureBlended;
  const protectAdvisor = opsOnAdvisors * (s.advisorHourBasis === "revenue_capacity"
    ? (revenueTotal / advisorHoursTotal) : advisorLoadedHourly);
  const protectFailures = I.constants.service_failures_avoided.v * I.constants.service_failure_cost_per_event.v;
  const protectTotal = protectConsultant + protectAdvisor + protectFailures;

  const case4 = {
    seatCompDelta, seatCostLoaded, displacedParaplanningHours,
    advisorLoadedHourly, revenuePerAdvisorHour: advisorHoursTotal > 0 ? revenueTotal / advisorHoursTotal : 0,
    protect: [
      { key: "consultant", label: "Operations hours she leaves behind, covered in-house",
        hours: consultantCatalogued, rate: postDepartureBlended, value: protectConsultant },
      { key: "advisor", label: "Operations work currently sitting on advisors, moved off",
        hours: opsOnAdvisors, rate: advisorLoadedHourly, value: protectAdvisor },
      { key: "failures", label: "Service failures avoided",
        hours: null, rate: I.constants.service_failure_cost_per_event.v, value: protectFailures,
        note: "Deliberately zero. I have no incident list, so I am counting nothing." },
    ],
    protectTotal,
    breakEvenRatio: seatCostLoaded > 0 ? protectTotal / seatCostLoaded : Infinity,
    surplus: protectTotal - seatCostLoaded,
    monthsOfHeadroom: (() => {
      const withSeat = utilUnder({ consultantPresent: false, response: "internal" });
      if (withSeat.available <= 0) return null;
      let h = { ...households0 }, m = 0;
      while (m < 600) {
        const totalH = TIER_IDS.reduce((a, t) => a + h[t], 0);
        const r = opsHoursRequired(I, s, h, totalH * s.growth).total;
        if (r >= withSeat.available) break;
        const added = totalH * gm;
        for (const t of TIER_IDS) h[t] += added * (I.book.find(b => b.tier === t).new_mix);
        m++;
      }
      return m >= 600 ? null : m;
    })(),
  };

  const taskHoursById = taskHours(I, s, households0, newTotal0);

  return {
    failed: false, scenario: s, roster, taskHoursById,
    rates: { blendedOpsHourly, blendedOpsHourlyAuto, advisorLoadedHourly,
      loadedHourlyByRole: Object.fromEntries(roster.map(r => [r.role_id, loadedHourly(r, s)])) },
    book: { households: households0, totalHouseholds: totalHouseholds0, aumTotal, newTotal: newTotal0 },
    revenue: { total: revenueTotal,
      perHousehold: revenueTotal / totalHouseholds0,
      perAdvisor: revenueTotal / advisors.length,
      perEmployee: revenueTotal / totalFte,
      totalFte, advisorCount: advisors.length },
    tiers: tierEcon, underwaterDirect, underwaterLoaded,
    allocFirmPerHh, capacity, case1, case4,
  };
}

/* --- 7. SENSITIVITY (the tornado) --------------------------------------- */
/* Each lever is moved to a low and a high value that I would actually defend,
   and we record what the answer becomes. The output is months-to-capacity-break,
   because that is the number the firm would act on.                          */
export function sensitivity(I, scenario, metric = "breakMonth") {
  const s = { ...defaultScenario(I), ...scenario };
  const levers = [
    { key: "switchingUplift",  label: "Switching and interruption uplift", low: 0.10, high: 0.40, fmt: "pct" },
    { key: "growth",           label: "Household growth rate",             low: 0.08, high: 0.25, fmt: "pct" },
    { key: "efficiency",       label: "Minutes per task (process change)", low: 0.85, high: 1.15, fmt: "pct" },
    { key: "productiveHours",  label: "Productive hours per person",       low: 1500, high: 1850, fmt: "num" },
  ];
  const readOut = m => {
    if (m.failed) return null;
    if (metric === "breakMonth") return m.capacity.breakMonth === null ? m.capacity.horizonMonths + 1 : m.capacity.breakMonth;
    if (metric === "utilisation") return m.capacity.utilisation;
    return null;
  };
  const baseM = computeModel(I, s);
  const baseV = readOut(baseM);
  const rows = levers.map(l => {
    const lo = readOut(computeModel(I, { ...s, [l.key]: l.low }));
    const hi = readOut(computeModel(I, { ...s, [l.key]: l.high }));
    return { ...l, baseValue: s[l.key], lowOut: lo, highOut: hi,
      swing: Math.abs((hi ?? 0) - (lo ?? 0)) };
  });
  /* Ops allocation is a roster field, not a scenario field, so it is swung
     through the productive-hours-equivalent instead: +/- 0.5 operations FTE. */
  const loFte = readOut(computeModel(I, { ...s, extraOpsFte: 0 }));
  const hiFte = readOut(computeModel(I, { ...s, extraOpsFte: 0.5 }));
  rows.push({ key: "extraOpsFte", label: "Half an extra operations FTE", low: 0, high: 0.5,
    baseValue: s.extraOpsFte, lowOut: loFte, highOut: hiFte, swing: Math.abs((hiFte ?? 0) - (loFte ?? 0)), fmt: "num" });

  rows.sort((a, b) => b.swing - a.swing);
  return { baseValue: baseV, rows, metric };
}

/* --- 8. HOURS BY TASK (drives the ledger's "time these first" ordering) --- */
export function taskHours(I, s, households, newTotal) {
  const out = {};
  const up = 1 + s.switchingUplift;
  for (const t of I.tasks) {
    const base = t.minutes * s.efficiency * t.occurrences;
    let mins = 0;
    if (t.basis === "firm") mins = base;
    else for (const tier of t.tiers) {
      const bk = I.book.find(b => b.tier === tier);
      if (t.basis === "household") mins += (households[tier] || 0) * base;
      else if (t.basis === "account") mins += (households[tier] || 0) * bk.accounts_per_household * base;
      else if (t.basis === "new_household") mins += (newTotal * bk.new_mix) * base;
    }
    out[t.id] = mins / 60 * (t.work_type === "operations" ? up : 1);
  }
  return out;
}
