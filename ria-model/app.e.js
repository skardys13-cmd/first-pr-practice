
/* ---------------------------------------------------------------- PRESENT */
function renderPresent(model) {
  const cap = model.capacity, c1 = model.case1, c4 = model.case4, t1 = model.tiers[0];
  $("#present-body").innerHTML = `
    <div class="card"><div class="card-head"><div><div class="card-title">The opening sentence</div>
      <div class="card-sub">One sentence. It has to ask him to correct my assumptions, not to admire my work.</div></div></div>
      <div class="card-body stack gap-16">
        <div class="script"><b>Say this</b>
          "I've built a model of how much operations work we carry and when we run out of room for it. Most of the
          numbers in it are my guesses, and they're all labelled as guesses — what I'd really like is half an hour
          of you telling me which ones are wrong."</div>
        <div class="prose" style="max-width:none">
          <p>The whole posture is in that sentence. I am sixty days in. I am not the person who tells him what his
          numbers are. I am the person who built a tool, labelled every assumption, and asked to be corrected.
          If he spends the meeting correcting me, the meeting has worked.</p>
          <p><b>Do not open with the seat.</b> Do not open with an insight. Open by handing him the controls.</p>
        </div>
      </div></div>

    <div class="card"><div class="card-head"><div><div class="card-title">The order to walk them in</div>
      <div class="card-sub">Departure first. It is the problem he already has, and it is the only one with a date on it.</div></div></div>
      <div class="card-body"><ol class="steps">
        <li><div class="step-body"><div class="step-title">Case 1 — what happens in ${nf(c1.daysAway, 0)} days</div>
          <p class="prose" style="font-size:.87rem;margin:0">Start here because he is already worried about it and
          because it needs no persuading. Lead with the gap, not the total: the catalogue accounts for
          ${nf(c1.catalogued, 0)} of her roughly ${nf(c1.contracted, 0)} hours, and the honest headline is that
          <b>I do not yet know what the other ${nf(c1.unmapped, 0)} hours are</b>. Admitting that first buys credit
          for everything after it.</p></div></li>
        <li><div class="step-body"><div class="step-title">Case 2 — where capacity breaks</div>
          <p class="prose" style="font-size:.87rem;margin:0">Now the departure has a context: it is not a one-off
          problem, it is an early arrival of a problem that was coming anyway${cap.breakDate ? `, around ${longDate(cap.breakDate)}` : ""}.
          Show the tornado chart here — it is the chart that says which of my guesses the answer actually depends
          on, and it is the fastest way to demonstrate that I know what I do not know.</p></div></li>
        <li><div class="step-body"><div class="step-title">Case 3 — what each tier costs to serve</div>
          <p class="prose" style="font-size:.87rem;margin:0">Third, and carefully. Frame it before showing it:
          "this one I'm least sure about, because the biggest number in it is one I can't see." Then ask for the
          overhead figure and rerun it in front of him. Present three options flat. <b>Do not recommend one.</b></p></div></li>
        <li><div class="step-body"><div class="step-title">Case 4 — the seat</div>
          <p class="prose" style="font-size:.87rem;margin:0">Last. By now he has spent forty minutes correcting a
          model that says operations is the constraint; the seat is the obvious next question rather than my ask.
          Lead with the displaced-hours problem, not the break-even — being the one who found the hole in my own
          proposal is worth more than the ratio is.</p></div></li>
      </ol></div></div>

    <div class="card"><div class="card-head"><div><div class="card-title">The three questions to ask him</div>
      <div class="card-sub">Phrased so the answers improve the model rather than just fill silence.</div></div></div>
      <div class="card-body grid2">
        <div class="q"><div class="qq">"What's our non-payroll cost per household — rent, tech, E&amp;O, all of it?"</div>
          <div class="qw">It is the largest single layer in case 3 and it is currently a number I made up. It also
          quietly tells me whether he thinks in per-household economics at all, which changes how I present
          everything else.</div></div>
        <div class="q"><div class="qq">"When she goes, what do you already expect to drop?"</div>
          <div class="qw">If he names something, that is a real input and it goes in the model. If he says nothing
          drops, then the ${nf(c1.options[0].hoursShort, 0)} hours with no owner in case 1 is the whole
          conversation, and I have not had to assert it myself.</div></div>
        <div class="q"><div class="qq">"Which of these numbers looks most wrong to you?"</div>
          <div class="qw">Invites correction rather than defence, and whatever he names is the assumption to work
          on next. Ask it while the sliders are on screen so the answer can go straight in.</div></div>
        <div class="q" style="border-style:dashed"><div class="qq">A fourth, only if it is going well</div>
          <div class="qw">"Is an operations role here something you're actually considering, or am I building
          towards something that isn't going to exist?" Direct, but it is the December question and a straight
          answer is worth more than a good meeting.</div></div>
      </div></div>

    <div class="card"><div class="card-head"><div><div class="card-title">What to do when he disagrees with a number</div></div></div>
      <div class="card-body stack gap-12">
        <div class="prose" style="max-width:none">
          <p><b>Change it in front of him. Immediately, without defending the old value.</b> Open the controls,
          move the slider to his number, and let him watch the chart move. That is the entire reason this is
          interactive rather than a deck.</p>
          <p>Then say what it did: "at your number the capacity date moves from X to Y" — or, better,
          "at your number it barely moves, so it turns out that assumption wasn't carrying much." Both of those
          are good outcomes. A model that survives being corrected is a tool. One that has to be defended is a
          presentation, and it is the last one of mine he will sit through.</p>
          <p>If he disagrees with something I actually timed, that is different and worth holding: "that one I
          timed — three runs, median was 40 minutes. Happy to time it again, but that's where the number came
          from." Say it once, without pushing. That is what the MEASURED tag is for.</p>
        </div>
        <div class="dont"><b style="font-family:var(--sans);font-size:.9rem">The one thing not to say</b>
          <div class="prose" style="max-width:none;margin-top:7px">
            <p><b>Do not present cost-to-serve as a finding about specific clients.</b> Never "these clients lose
            us money." The model works in tiers precisely so that sentence is not available. The tier is a
            question about a service model; the household is somebody's family, and the person who says the
            second sentence in a six-person firm does not get asked into the next conversation.</p>
            <p><b>And do not lead with the seat.</b> It is the last thing in the meeting, framed as protection
            rather than generation. An operations seat protects advisor capacity and prevents service failures.
            Claiming it generates revenue invites the one challenge I cannot win from this chair.</p>
          </div></div>
      </div></div>

    <div class="card"><div class="card-head"><div><div class="card-title">The leave-behind</div>
      <div class="card-sub">One page, printed, on the desk when I go. The workbook goes with it.</div></div></div>
      <div class="card-body stack gap-12">
        <p class="prose" style="font-size:.88rem">Everything on the summary is drawn live from whatever the sliders
        are set to when it prints — so if he corrects three numbers in the meeting, the page he keeps has his
        numbers on it, not mine. Print it at the end, not before.</p>
        <button class="btn noprint" id="print-btn2">Print the one-page summary</button>
      </div></div>`;
  const b = $("#print-btn2"); if (b) b.onclick = doPrint;
}

/* ---------------------------------------------------------------- PRINT */
function renderPrint(model) {
  const cap = model.capacity, c1 = model.case1, c4 = model.case4, t1 = model.tiers[0];
  const r = rollup(ATOMS.map(a => a.id));
  $("#printsheet").innerHTML = `
    <h2 style="margin-bottom:4px">Operations capacity &amp; economics — summary</h2>
    <p style="font-size:.8rem;color:var(--muted);margin-bottom:12px">Working model, ${esc(INPUTS.meta.as_of)}.
      ${r.counts.PLACEHOLDER} of ${r.total} inputs are still placeholders. Nothing here is a compliance opinion,
      and no client data is used anywhere in it.</p>
    <table class="data" style="min-width:0"><tbody>
      <tr><td><b>The book</b></td><td class="n">${nf(model.book.totalHouseholds, 0)} households · ${usdK(model.book.aumTotal)} AUM · ${usdK(model.revenue.total)} revenue at the schedule</td></tr>
      <tr><td><b>Operations today</b></td><td class="n">${nf(cap.required.total, 0)} h required · ${nf(cap.available, 0)} h available · <b>${pct(cap.utilisation)} utilised</b></td></tr>
      <tr><td><b>1 · In ${nf(c1.daysAway, 0)} days</b></td><td class="n">${nf(c1.catalogued, 0)} catalogued hours need a home, plus ~${nf(c1.unmapped, 0)} not yet documented. Absorbing them: <b>${pct(c1.options[0].utilisation)}</b> utilisation, ${nf(c1.options[0].hoursShort, 0)} h unowned. Backfill ${usd(c1.options[1].annualCost)}/yr. Internal seat ${usd(c1.options[2].annualCost)}/yr.</td></tr>
      <tr><td><b>2 · Capacity</b></td><td class="n">${cap.breakDate ? `Breaks at ~${nf(cap.breakHouseholds, 0)} households, around <b>${longDate(cap.breakDate)}</b>, at ${pct(model.scenario.growth, 0)} growth.` : `No break inside ${model.scenario.horizonYears} years at ${pct(model.scenario.growth, 0)} growth.`}</td></tr>
      <tr><td><b>3 · Tier economics</b></td><td class="n">${t1.tier} costs ~${usd(t1.costTotalLoaded)} loaded to serve, produces ${usd(t1.revenuePerHousehold)}. Driven by a placeholder overhead figure of ${usd(model.scenario.firmOverheadPerHousehold)}/household. Three options: raise the minimum, serve differently, accept as pipeline cost.</td></tr>
      <tr><td><b>4 · The seat</b></td><td class="n">Costs ${usd(c4.seatCostLoaded)} loaded. Protects ${usd(c4.protectTotal)} on these numbers (${nf(c4.protect[1].hours, 0)} advisor hours + ${nf(c4.protect[0].hours, 0)} consultant hours). Displaces ${nf(c4.displacedParaplanningHours, 0)} h of paraplanning that must go somewhere.</td></tr>
    </tbody></table>
    <p style="font-size:.78rem;margin-top:14px"><b>What I need from you:</b> the non-payroll overhead per household,
      compensation bands for the roster, the real three-year new-household count, and whether an operations role is
      genuinely on the table. Everything else I can get myself.</p>`;
}
function doPrint() { $("#printsheet").style.display = "block"; window.print();
  setTimeout(() => { $("#printsheet").style.display = "none"; }, 400); }

/* ---------------------------------------------------------------- CONTROLS */
const SLIDERS = [
  { key: "growth", label: "Household growth rate", min: 0, max: 0.30, step: 0.01, fmt: v => pct(v, 0), ref: "const.growth_rate_households" },
  { key: "efficiency", label: "Minutes per task", min: 0.60, max: 1.20, step: 0.01, fmt: v => pct(v, 0) + " of filed", note: "A 10% process improvement is 90%." },
  { key: "switchingUplift", label: "Switching and interruption uplift", min: 0, max: 0.50, step: 0.01, fmt: v => pct(v, 0), ref: "const.switching_uplift" },
  { key: "feeRealisation", label: "Fee realisation against schedule", min: 0.70, max: 1.10, step: 0.01, fmt: v => pct(v, 0), ref: "const.fee_realisation" },
  { key: "productiveHours", label: "Productive hours per person", min: 1200, max: 2000, step: 25, fmt: v => nf(v, 0) + " h", ref: "const.productive_hours_year" },
  { key: "benefitsLoad", label: "Benefits and payroll load", min: 0, max: 0.50, step: 0.01, fmt: v => pct(v, 0), ref: "const.benefits_load" },
  { key: "firmOverheadPerHousehold", label: "Firm overhead per household", min: 0, max: 5000, step: 100, fmt: v => usd(v), ref: "const.firm_overhead_per_household" },
  { key: "extraOpsFte", label: "Operations headcount change", min: -2.5, max: 2, step: 0.1,
    fmt: v => v > 0 ? "+" + nf(v, 1) + " FTE" : v < 0 ? "−" + nf(-v, 1) + " FTE" : "no change",
    note: "On top of whatever the scenario sets. Negative removes operations time, largest contributor first — take it far enough and the model refuses to run." },
  { key: "blendedOpsHourlyOverride", label: "Blended operations hourly rate", min: 0, max: 150, step: 1, fmt: v => v > 0 ? usd(v) + " / h" : "auto from roster", note: "Zero uses the roster." },
  { key: "seatOpsAllocation", label: "My operations share, if I take the seat", min: 0.35, max: 1, step: 0.05, fmt: v => pct(v, 0), note: "Case 4. The rest of my week stays paraplanning." },
];
const BASE = defaultScenario(INPUTS);

function renderSliders() {
  const respHTML = `<div class="slider" style="grid-column:1/-1">
    <label><span>Operations headcount</span></label>
    <div class="sb-group">
      <label style="font-size:.78rem;display:flex;gap:6px;align-items:center;font-weight:400;margin:0">
        <input type="checkbox" id="c-consultant" ${state.consultantPresent ? "checked" : ""}> Consultant still on the roster</label>
      <div class="segmented" role="group" aria-label="Response to her departure">
        ${[["absorb", "Absorb"], ["backfill", "Backfill"], ["internal", "I take the seat"]].map(([k, l]) =>
          `<button data-resp="${k}" aria-pressed="${state.response === k}" ${state.consultantPresent ? "disabled style=opacity:.45" : ""}>${l}</button>`).join("")}
      </div>
    </div>
    <span class="hint">${state.consultantPresent ? "The response only applies once she is off the roster." : "How her work is covered."}</span></div>`;

  $("#sliders").innerHTML = respHTML + SLIDERS.map(s => {
    const v = state[s.key] ?? 0;
    const dirty = Math.abs(v - (BASE[s.key] ?? 0)) > 1e-9;
    const a = s.ref ? ATOM_BY_ID[s.ref] : null;
    return `<div class="slider${dirty ? " dirty" : ""}">
      <label for="sl-${s.key}"><span>${esc(s.label)}${a ? ` <span class="tag tag-${a.tag}" style="font-size:.52rem">${a.tag}</span>` : ""}</span>
        <output id="out-${s.key}">${s.fmt(v)}</output></label>
      <input type="range" id="sl-${s.key}" min="${s.min}" max="${s.max}" step="${s.step}" value="${v}" data-key="${s.key}">
      <span class="hint">${esc(s.note || (a ? "Filed value " + s.fmt(BASE[s.key]) + ". " + a.who : ""))}</span></div>`;
  }).join("");

  $$("#sliders input[type=range]").forEach(el => {
    el.addEventListener("input", () => {
      const k = el.dataset.key, s = SLIDERS.find(x => x.key === k);
      state[k] = k === "blendedOpsHourlyOverride" && +el.value === 0 ? null : +el.value;
      $("#out-" + k).textContent = s.fmt(+el.value);
      el.closest(".slider").classList.toggle("dirty", Math.abs(+el.value - (BASE[k] ?? 0)) > 1e-9);
      syncPresetButtons(); renderAll(false);
    });
  });
  const cc = $("#c-consultant");
  if (cc) cc.onchange = () => { state.consultantPresent = cc.checked; syncPresetButtons(); renderSliders(); renderAll(); };
  $$("#sliders [data-resp]").forEach(b => b.onclick = () => {
    if (state.consultantPresent) return;
    state.response = b.dataset.resp; syncPresetButtons(); renderSliders(); renderAll();
  });
}
function syncPresetButtons() {
  $$("[data-preset]").forEach(b => {
    const p = PRESETS[b.dataset.preset];
    b.setAttribute("aria-pressed", String(state.consultantPresent === p.consultantPresent && state.response === p.response));
  });
}
function renderReadout(model) {
  if (model.failed) {
    $("#sb-readout").innerHTML = `<b style="color:var(--warn)">Model cannot run</b>`;
    return;
  }
  const cap = model.capacity;
  $("#sb-readout").innerHTML = `
    <span>Utilisation <b style="${cap.utilisation > 1 ? "color:var(--warn)" : ""}">${pct(cap.utilisation)}</b></span>
    <span>Capacity <b>${cap.breakDate ? longDate(cap.breakDate) : "beyond " + model.scenario.horizonYears + " yrs"}</b></span>
    <span>Revenue <b>${usdK(model.revenue.total)}</b></span>`;
}
function renderCompare(model) {
  const strip = $("#cmp-strip");
  if (!cmpBase) { strip.hidden = true; return; }
  strip.hidden = false;
  const a = computeModel(INPUTS, cmpBase.state), b = model;
  const rowsFor = m => m.failed ? null : ({
    "Operations utilisation": [pct(m.capacity.utilisation), m.capacity.utilisation],
    "Hours required per year": [nf(m.capacity.required.total, 0), m.capacity.required.total],
    "Hours available per year": [nf(m.capacity.available, 0), m.capacity.available],
    "Capacity runs out": [m.capacity.breakDate ? longDate(m.capacity.breakDate) : "beyond horizon", m.capacity.breakMonthFrac ?? 999],
    "Revenue at the schedule": [usdK(m.revenue.total), m.revenue.total],
    "Bottom tier margin, loaded": [usd(m.tiers[0].marginLoaded), m.tiers[0].marginLoaded],
  });
  const A = rowsFor(a), B = rowsFor(b);
  if (!A || !B) { strip.innerHTML = `<div class="caveat"><span class="cv-tag">Compare</span><span>One of the two scenarios cannot run.</span></div>`; return; }
  const keys = Object.keys(A);
  strip.innerHTML = `<div class="card" style="margin-bottom:22px"><div class="card-head">
      <div><div class="card-title">Compare</div><div class="card-sub">A is pinned. Move any control and B moves with it. The deltas are the argument.</div></div>
      <button class="btn btn-sm" id="cmp-clear">Clear</button></div>
    <div class="card-body"><div class="tscroll"><table class="data" style="min-width:0">
      <thead><tr><th>Measure</th><th class="n">A · ${esc(cmpBase.label)}</th><th class="n">B · now</th><th class="n">Change</th></tr></thead>
      <tbody>${keys.map(k => {
        const d = B[k][1] - A[k][1];
        const same = Math.abs(d) < 1e-9;
        const dir = k === "Capacity runs out" ? (d > 0 ? "later" : "sooner") : (d > 0 ? "up" : "down");
        return `<tr><td>${esc(k)}</td><td class="n">${A[k][0]}</td><td class="n"><b>${B[k][0]}</b></td>
          <td class="n" style="color:${same ? "var(--muted)" : "var(--ink)"}">${same ? "no change" :
            (k === "Capacity runs out" ? `${nf(Math.abs(d), 0)} months ${dir}` : `${d > 0 ? "+" : "−"}${
              k.includes("Revenue") || k.includes("margin") ? usdK(Math.abs(d)) :
              k.includes("utilisation") ? pct(Math.abs(d)) : nf(Math.abs(d), 0)}`)}</td></tr>`;
      }).join("")}</tbody></table></div></div></div>`;
  $("#cmp-clear").onclick = () => { cmpBase = null; $("#cmp-toggle").setAttribute("aria-pressed", "false"); $("#cmp-state").textContent = ""; renderAll(); };
}

/* ---------------------------------------------------------------- RENDER */
function renderAll(full = true) {
  const model = M();
  renderReadout(model);
  const fb = $("#failbanner");
  if (model.failed) {
    /* Fail visibly: hide every panel rather than render a number that looks
       fine and means nothing. The panels are intact and come straight back. */
    fb.hidden = false;
    fb.innerHTML = `<div class="caveat" style="margin-top:20px"><span class="cv-tag">The model stopped</span>
      <span><b>This is deliberate.</b> At these settings the model cannot produce an honest number, so it
      produces none.<br><br>${model.errors.map(x => "• " + esc(x)).join("<br>")}<br><br>
      Move the controls back, or press Reset, and everything returns.</span></div>`;
    $$(".panel").forEach(p => { p.hidden = true; });
    $("#cmp-strip").hidden = true;
    return;
  }
  fb.hidden = true;
  $$(".panel").forEach(p => { p.hidden = p.id !== "p-" + activePanel; });
  renderCompare(model);
  const r = { start: renderStart, case1: renderCase1, case2: renderCase2, case3: renderCase3,
    case4: renderCase4, assump: renderAssumptions, build: () => renderBuild(), present: renderPresent }[activePanel];
  if (r) r(model);
  renderPrint(model);
  const meta = rollup(ATOMS.map(a => a.id));
  $("#m-asof").textContent = INPUTS.meta.as_of;
  $("#m-schema").textContent = INPUTS.meta.schema_version;
  $("#m-inputcount").textContent = meta.total;
  $("#m-measured").textContent = meta.counts.MEASURED + " of " + meta.total;
}

/* ---------------------------------------------------------------- EVENTS */
function showPanel(name) {
  activePanel = name;
  $$(".panel").forEach(p => { p.hidden = p.id !== "p-" + name; });
  $$("#casenav button").forEach(b => b.setAttribute("aria-selected", String(b.dataset.panel === name)));
  renderAll();
  window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
}
$$("#casenav button").forEach(b => b.onclick = () => showPanel(b.dataset.panel));
$$("[data-preset]").forEach(b => b.onclick = () => {
  const p = PRESETS[b.dataset.preset];
  state.consultantPresent = p.consultantPresent; state.response = p.response;
  syncPresetButtons(); renderSliders(); renderAll();
});
$("#sb-toggle").onclick = () => {
  const open = $("#sb-panel").hidden;
  $("#sb-panel").hidden = !open;
  $("#sb-toggle").setAttribute("aria-expanded", String(open));
};
$("#sb-reset").onclick = () => { state = defaultScenario(INPUTS); syncPresetButtons(); renderSliders(); renderAll(); };
$("#cmp-toggle").onclick = () => {
  if (cmpBase) { cmpBase = null; $("#cmp-toggle").setAttribute("aria-pressed", "false"); $("#cmp-state").textContent = ""; }
  else {
    const preset = Object.entries(PRESETS).find(([, p]) => p.consultantPresent === state.consultantPresent && p.response === state.response);
    cmpBase = { state: JSON.parse(JSON.stringify(state)), label: preset ? preset[1].label : "pinned" };
    $("#cmp-toggle").setAttribute("aria-pressed", "true");
    $("#cmp-state").textContent = "A pinned — now change something";
  }
  renderAll();
};
$("#t-xray").onclick = () => { xray = !xray; document.body.classList.toggle("xray", xray);
  $("#t-xray").setAttribute("aria-pressed", String(xray)); };
$("#t-anon").onclick = () => { anonymised = !anonymised;
  $("#t-anon").setAttribute("aria-pressed", String(anonymised));
  $("#t-anon").textContent = anonymised ? "Anonymised" : "Real labels";
  buildLedger(); renderAll();
};
$("#t-theme").onclick = () => {
  const cur = document.documentElement.getAttribute("data-theme");
  const next = cur === "dark" ? "light" : cur === "light" ? null : "dark";
  if (next) document.documentElement.setAttribute("data-theme", next);
  else document.documentElement.removeAttribute("data-theme");
  $("#t-theme").textContent = next ? next[0].toUpperCase() + next.slice(1) : "Theme";
};
$("#t-print").onclick = doPrint;
document.addEventListener("click", e => {
  const f = e.target.closest("[data-filter]");
  if (f) { ledgerFilter = f.dataset.filter; renderAll(); return; }
  const g = e.target.closest("[data-goto]");
  if (g) { e.preventDefault(); ledgerFilter = "ALL"; showPanel("assump");
    requestAnimationFrame(() => {
      const row = document.getElementById("atom-" + g.dataset.goto);
      if (row) { row.scrollIntoView({ block: "center", behavior: "smooth" });
        row.style.transition = "background .2s"; row.style.background = "var(--accent-soft)";
        setTimeout(() => { row.style.background = ""; }, 1600); }
    });
  }
});

/* ---------------------------------------------------------------- INIT */
/* Closed at rest: open, the control panel takes half the viewport and pushes
   the numbers off screen. The presets and the readout stay visible either way. */
$("#sb-panel").hidden = true;
$("#sb-toggle").setAttribute("aria-expanded", String(!$("#sb-panel").hidden));
renderSliders();
showPanel("start");
