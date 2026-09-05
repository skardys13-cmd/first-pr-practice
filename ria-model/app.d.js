
/* ---------------------------------------------------------------- LEDGER */
function atomValue(a) {
  if (a.id.startsWith("book.T")) {
    const b = INPUTS.book.find(x => "book." + x.tier === a.id);
    return `${nf(b.households, 0)} households · ${usdK(b.avg_aum)} avg · ${nf(b.accounts_per_household, 1)} accts`;
  }
  if (a.id === "book.new_mix") return INPUTS.book.map(b => `${b.tier} ${pct(b.new_mix, 0)}`).join(" · ");
  if (a.id === "fee.schedule") return INPUTS.fee_schedule.bands.map(b =>
    `${pct(b.rate, 2)} to ${b.to === null ? "∞" : usdK(b.to)}`).join(" · ");
  if (a.taskId) { const t = INPUTS.tasks.find(x => x.id === a.taskId);
    return `${nf(t.minutes, 0)} min × ${nf(t.occurrences, 2)}/yr · ${t.basis.replace(/_/g, " ")} · ${L(t.owner)}`; }
  switch (a.unit) {
    case "usd": return usd(a.value);
    case "pct": return pct(a.value, a.value < 0.1 ? 1 : 0);
    case "hours": return nf(a.value, 0) + " h";
    case "fte": return nf(a.value, 2) + " FTE";
    case "days": return nf(a.value, 0) + " days";
    case "count": return nf(a.value, 0);
    case "choice": return String(a.value).replace(/_/g, " ");
    default: return a.value === null ? "—" : String(a.value);
  }
}
function renderAssumptions(model) {
  const r = rollup(ATOMS.map(a => a.id));
  const solidPct = r.solid;
  $("#a-summary").innerHTML = `<div class="tiles">
    ${tile("Inputs in the model", nf(r.total, 0), "every one carries a tag", {})}
    ${tile("Measured or observed", pct(solidPct, 0), `${r.counts.MEASURED + r.counts.OBSERVED} of ${r.total}`, {})}
    ${tile("Still placeholders", nf(r.counts.PLACEHOLDER, 0), "numbers I made up so the model would run", { alert: r.counts.PLACEHOLDER > 0 })}
    ${tile("Timed by me", nf(r.counts.MEASURED, 0), "the strongest evidence in the model", { alert: r.counts.MEASURED === 0 })}
  </div>
  <div style="margin-top:14px">${provMeter(ATOMS.map(a => a.id), model)}</div>`;

  $("#a-filters").innerHTML = ["ALL", ...TAGS].map(t =>
    `<button class="btn btn-sm" data-filter="${t}" aria-pressed="${ledgerFilter === t}">${t === "ALL" ? "All" : t[0] + t.slice(1).toLowerCase()}${t === "ALL" ? "" : ` <span class="num">${rollup(ATOMS.map(a => a.id)).counts[t]}</span>`}</button>`).join("");

  const rows = ATOMS.filter(a => ledgerFilter === "ALL" || a.tag === ledgerFilter);
  $("#a-count").innerHTML = `${rows.length} of ${ATOMS.length} inputs shown. Every row: what it is, what it is set to, where it came from, who could confirm it, and when it was last checked.`;
  $("#a-table").innerHTML = `<div class="tscroll" style="max-height:640px;overflow-y:auto">
    <table class="data sticky-head" style="min-width:940px"><thead><tr>
      <th>Ref</th><th>Input</th><th>Value</th><th>Tag</th><th>Where it came from</th><th>Who could confirm it</th><th>Last checked</th>
    </tr></thead><tbody>
    ${rows.map(a => `<tr id="atom-${esc(a.id)}" data-soft="${["ESTIMATED", "PLACEHOLDER", "BENCHMARK"].includes(a.tag) ? 1 : 0}">
      <td class="num" style="color:var(--muted);font-size:.72rem">${a.ref}</td>
      <td style="min-width:190px"><b style="color:var(--ink);font-weight:500">${esc(a.name)}</b>
        <div style="font-size:.7rem;color:var(--muted)">${esc(a.group)}</div></td>
      <td class="num" style="font-size:.75rem">${esc(atomValue(a))}</td>
      <td><span class="tag tag-${a.tag}">${a.tag}</span></td>
      <td style="min-width:250px;font-size:.76rem">${esc(a.src)}</td>
      <td style="min-width:170px;font-size:.76rem">${esc(a.who)}</td>
      <td class="num" style="font-size:.72rem;${a.checked === "never" ? "color:var(--warn);font-weight:600" : ""}">${esc(a.checked)}</td>
    </tr>`).join("")}</tbody></table></div>`;

  const ranked = INPUTS.tasks.map(t => ({ t, h: model.taskHoursById[t.id] || 0 }))
    .filter(x => x.t.work_type === "operations").sort((a, b) => b.h - a.h);
  const totalH = ranked.reduce((a, x) => a + x.h, 0);
  let cum = 0;
  const top = ranked.slice(0, 10).map((x, i) => { cum += x.h;
    return [`${i + 1}. ${esc(x.t.task)}`, esc(L(x.t.owner)), nf(x.h, 0), pct(x.h / totalH, 1), pct(cum / totalH, 0)]; });
  $("#a-priority").innerHTML = `<div class="tscroll"><table class="data" style="min-width:0">
    <thead><tr><th>Task</th><th>Currently owned by</th><th class="n">Hours / yr</th><th class="n">Share</th><th class="n">Cumulative</th></tr></thead>
    <tbody>${top.map(r => `<tr>${r.map((c, i) => `<td class="${i > 1 ? "n" : ""}">${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
    <p style="font-size:.79rem;color:var(--muted);margin-top:9px">These ten rows are
    <b>${pct(cum / totalH, 0)}</b> of all catalogued operations hours. Timing them turns most of this model from
    guesswork into evidence. The remaining ${ranked.length - 10} rows are worth timing eventually and not worth
    delaying the conversation for.</p>`;

  $("#a-tagkey").innerHTML = `<div class="grid2">${TAGS.map(t => `
    <div style="display:flex;gap:11px;align-items:flex-start">
      <span class="tag tag-${t}">${t}</span>
      <span style="font-size:.83rem;color:var(--ink-2)">${esc(INPUTS.tag_meta[t].desc)}</span></div>`).join("")}</div>
    <p style="font-size:.8rem;color:var(--muted);margin-top:14px">The tag travels with the number everywhere it
    appears. Turn on <b>Show me the estimates</b> at the top of the page and every figure that is not measured or
    observed lights up, on every screen.</p>`;
}

/* ---------------------------------------------------------------- BUILD */
const WORKFLOW = [
  { phase: "Tonight, on my own", note: "Nothing here needs anybody else's time. All of it is readable out of systems I already have access to." },
  { n: 1, title: "Household counts and average AUM, by tier",
    need: "How many households sit in each of the four AUM bands, and the average balance in each band.",
    from: "The portfolio system's household report. Group by household, sort by total value, then count into the four bands. Export the summary only — never the household list.",
    goes: "Book tab, one row per tier. Workbook: <span class='num'>Book!C5:E8</span>.",
    formula: "Total AUM is a formula, not a typed number: <span class='num'>= households × average AUM</span>.",
    check: "Total AUM across the four tiers should land within a few percent of the AUM figure the firm quotes. If it is 20% out, the household grouping is wrong — usually because related accounts are not grouped into one household.",
    tag: "OBSERVED" },
  { n: 2, title: "Accounts per household, by tier",
    need: "The average number of custodial accounts each household holds, per tier.",
    from: "Export the account list, count accounts, divide by households in that tier. This is the number I currently have as an estimate and it takes ten minutes to make real.",
    goes: "Book tab, accounts per household column.",
    formula: "Drives every per-account task row: <span class='num'>minutes × occurrences × accounts per household</span>.",
    check: "Should rise across the tiers. If the top tier is not the highest, either the grouping is wrong or there are dormant accounts inflating a lower tier.",
    tag: "MEASURED" },
  { n: 3, title: "The fee schedule, as bands",
    need: "Every breakpoint and the rate that applies inside each band.",
    from: "The ADV Part 2A, or the client agreement. Copy the bands exactly — do not simplify to an average rate.",
    goes: "FeeSchedule tab, one row per band.",
    formula: "Each band charges its own rate on the portion of assets inside it. The workbook uses SUMPRODUCT over the band table, not a lookup of one rate.",
    check: "Hand-work a household just above a breakpoint. A household at $520,000 on a 1.00% / 0.85% schedule pays <b>$5,170</b>, not $4,420. If the model gives $4,420 it is a flat-rate model wearing a tiered schedule, and every revenue number in it is wrong.",
    tag: "OBSERVED" },
  { n: 4, title: "My own week",
    need: "What share of my hours is operations work rather than planning, research and meeting support.",
    from: "Me. Keep a two-week log in 30-minute blocks. Not a guess — a log.",
    goes: "Roster tab, operations allocation for my row.",
    formula: "Feeds operations hours available: <span class='num'>FTE × allocation × productive hours</span>.",
    check: "If it comes out above 60% I should ask whether I am already doing the operations job. That is useful information for case 4 either way.",
    tag: "MEASURED" },
  { phase: "The next two weeks — timing", note: "This is the strongest evidence I will have. It is also the only evidence in this model that nobody can dispute, because I will have done it myself." },
  { n: 5, title: "Time the ten tasks that carry the model",
    need: "Median minutes per occurrence for the ten task rows that make up most of the catalogued hours. The Assumptions tab ranks them.",
    from: "A stopwatch and my own calendar. Three runs each, not one.",
    goes: "Tasks tab, minutes column, and change the tag from PLACEHOLDER to MEASURED as each one lands.",
    formula: "Everything. Every hour figure in this model is built on this column.",
    check: "A timing that is faster than my instinct is a timing I did wrong. See the note below on timing honestly.",
    tag: "MEASURED", coach: "timing" },
  { phase: "One conversation with the consultant", note: "Batched deliberately into a single conversation. She is leaving; her time is the scarcest input in this whole exercise, and asking her the same kind of question four times over four weeks is how goodwill gets spent." },
  { n: 6, title: "Her task list", needs_person: true,
    need: "Everything she does that is not already in my catalogue — especially the quarterly and annual work that does not happen while I am watching.",
    from: "Her, directly. This needs to be framed as documentation, not measurement. See the script below.",
    goes: "Tasks tab, new rows, owner set to her role, tagged OBSERVED until timed.",
    formula: "New rows enter the catalogue and the coverage check on the Capacity tab closes.",
    check: "The coverage check is the test. Her catalogued hours currently account for only part of her contracted hours; the gap should shrink markedly after this conversation. If it does not, I have not asked well enough.",
    tag: "OBSERVED", coach: "asking" },
  { n: 7, title: "Her contracted hours", needs_person: true,
    need: "How many hours a week or month she is actually engaged for.",
    from: "Her, or the principal — whoever finds it less awkward. It is in the engagement letter.",
    goes: "Roster tab, FTE for her row: <span class='num'>= weekly hours × 48 / productive hours</span>.",
    formula: "Sets how much capacity leaves the firm on her last day.",
    check: "Compare with the catalogued hours for her rows. A large gap means the catalogue is still incomplete — go back to step 6.",
    tag: "OBSERVED" },
  { n: 8, title: "Her own timings, for her own tasks", needs_person: true,
    need: "Her estimate of minutes per occurrence on the rows only she does.",
    from: "The same conversation. Ask for ranges, not points: 'somewhere between 20 minutes and an hour' is a more honest input than '35 minutes'.",
    goes: "Tasks tab, tagged OBSERVED (her figure) rather than MEASURED (mine).",
    formula: "Same as any other task row.",
    check: "Put her ranges in at both ends and see whether the capacity date moves by more than a quarter. If it does, that row is worth timing properly before it leaves with her.",
    tag: "OBSERVED" },
  { phase: "One conversation with the principal", note: "Also batched. These are the numbers I genuinely cannot see, and asking for them one at a time over a month makes me look like I am fishing rather than building." },
  { n: 9, title: "Compensation, as bands not points", needs_person: true,
    need: "A loaded cost band for each seat. Bands are fine — the model does not need anybody's exact salary.",
    from: "The principal. Offer the band framing first; it is easier to say yes to.",
    goes: "Roster tab, compensation column.",
    formula: "<span class='num'>loaded hourly = comp × (1 + benefits load) / (FTE × productive hours)</span>.",
    check: "Run the model at both ends of every band. If the answer to any of the four cases flips between the ends, say so out loud rather than picking a midpoint.",
    tag: "OBSERVED" },
  { n: 10, title: "Non-payroll firm overhead per household", needs_person: true,
    need: "Rent, technology, custodial platform fees, E&O, compliance vendors, professional fees, marketing — divided by household count.",
    from: "The principal, or whoever prepares the P&L. A single annual total is enough; I do not need the breakdown.",
    goes: "Assumptions tab, firm overhead per household.",
    formula: "<span class='num'>= total non-payroll overhead / total households</span>.",
    check: "This number decides on its own whether the bottom tier looks profitable. Until it is real, case 3 is a structure, not a finding — and I should say exactly that when I show it.",
    tag: "OBSERVED" },
  { n: 11, title: "The real growth rate", needs_person: true,
    need: "New households opened in each of the last three years.",
    from: "A CRM report, or the principal. A count, not a feeling — including mine.",
    goes: "Assumptions tab, household growth rate.",
    formula: "<span class='num'>= (households now / households three years ago) ^ (1/3) − 1</span>.",
    check: "If the three years disagree wildly, use the range and show the capacity date at both ends rather than averaging them into a single false number.",
    tag: "OBSERVED" },
  { n: 12, title: "Fee realisation", needs_person: true,
    need: "Actual fees billed last quarter against what the schedule implies.",
    from: "The billing run. I may be able to get this myself once I am closer to the billing cycle.",
    goes: "Assumptions tab, fee realisation.",
    formula: "<span class='num'>= fees actually billed / fees the schedule implies</span>.",
    check: "Almost certainly below 100% — discounts, family aggregation, flat-fee exceptions. If it comes out above 100% the schedule in the model is wrong.",
    tag: "OBSERVED" },
  { n: 13, title: "Service incidents worth counting", needs_person: true,
    need: "Actual service failures in the last two years, and roughly what each cost.",
    from: "The principal, or the compliance file.",
    goes: "Assumptions tab, service failures avoided and cost per event.",
    formula: "Feeds case 4 only.",
    check: "Leave this at zero unless somebody can name real incidents. A padded number here is the fastest way to lose the room, and the case is strong enough without it.",
    tag: "OBSERVED" },
];

function renderBuild() {
  const phases = [];
  let cur = null;
  for (const s of WORKFLOW) {
    if (s.phase) { cur = { phase: s.phase, note: s.note, steps: [] }; phases.push(cur); }
    else cur.steps.push(s);
  }
  const coachTiming = `<div class="card"><div class="card-head"><div>
      <div class="card-title">How to time a process honestly</div>
      <div class="card-sub">The timings are the only evidence in this model that is mine. If I flatter them, everything built on them is worthless — and worse, it is confidently worthless.</div></div></div>
    <div class="card-body prose" style="max-width:none">
      <p><b>Three runs, never one.</b> The first run of anything is the slowest and the one I am most tempted to
      throw away. Keep it. Three runs of the same task on three different days.</p>
      <p><b>Record the median, not the best.</b> The fastest run is the one where nothing went wrong, and nothing
      going wrong is not the normal case. The median of three is the number that goes in the model.</p>
      <p><b>Include the interruptions.</b> If the phone goes while I am opening an account, that time counts. The
      model is trying to predict how much of a real week this work consumes, not how fast the task could be done
      in a room with the door shut. Stop the clock only when I stop working on the firm's behalf entirely.</p>
      <p><b>Time the whole loop, not the keystrokes.</b> An account opening is not the twelve minutes in the
      custodian portal. It is the prep, the portal, the follow-up on the thing that bounced, and the note in the
      CRM. Time from picking it up to genuinely putting it down.</p>
      <p><b>Write down what made a run unusual.</b> "45 minutes, but the client's trust document was wrong" is a
      more useful record than "45 minutes", because when the median looks strange in three weeks I will know why.</p>
      <p style="color:var(--warn)"><b>The failure mode to watch for in myself:</b> timing the runs where I look
      efficient. A timing I flatter myself with is worse than no timing at all, because no timing is honestly
      labelled PLACEHOLDER and a flattering one gets labelled MEASURED.</p>
    </div></div>`;

  const coachAsking = `<div class="card"><div class="card-head"><div>
      <div class="card-title">How to ask the consultant for her task list</div>
      <div class="card-sub">This is the conversation I am most likely to get wrong. She is leaving. Any question about what she does can land as an audit, and once it lands that way I will not get a second run at it.</div></div></div>
    <div class="card-body stack gap-16">
      <div class="prose" style="max-width:none">
        <p>Three things make the difference: <b>ask for the handover, not the inventory</b>; <b>make it clear the
        work is going to be harder without her, not easier</b>; and <b>ask her to correct me rather than to
        inform me</b> — bring a draft she can mark up, so she is editing my document instead of writing hers.</p>
      </div>
      <div class="script"><b>The opening — in person, not over email</b>
        "I've been trying to write down everything operations covers so that when you go, we don't discover
        something important in February that nobody knew existed. I've had a go at the list myself, but I know
        it's got holes in it — particularly the quarterly and annual things I haven't been here long enough to
        see. Could I show you what I've got and have you tell me what I've missed?"</div>
      <div class="script"><b>Handing over the draft</b>
        "Don't worry about the numbers on it — those are all my guesses at the minute. What I really want is the
        rows that aren't there at all. The things that only happen in January, or only when something goes wrong."</div>
      <div class="script"><b>Asking for her timings, without it sounding like a stopwatch</b>
        "For the ones only you do — could you give me a rough range rather than a number? If you tell me the
        billing run is somewhere between three and six hours depending on how many exceptions there are, that's
        far more useful to me than a single figure, and it's honest about the thing that actually varies."</div>
      <div class="script"><b>If it starts to feel like measurement</b>
        "To be clear about why I'm asking — this isn't about your hours. It's that I'm probably picking a lot of
        this up, and I'd rather find out now what I don't know than in the middle of a quarter end."</div>
      <div class="prose" style="max-width:none">
        <p><b>What not to do:</b> do not send her a spreadsheet with empty minute columns and ask her to fill it
        in. That is an audit form, whatever the covering note says. Do not ask what she does with her time. Do not
        mention utilisation, capacity or cost anywhere in this conversation — those are my words for my model, and
        none of them belong in a handover.</p>
        <p><b>What to do afterwards:</b> send her the updated list and ask if it looks right. People correct a
        document far more readily than they compose one, and it makes plain that the point was the handover.</p>
      </div>
    </div></div>`;

  $("#build-body").innerHTML = `
    <div class="caveat soft"><span class="cv-tag">Order matters</span><span>Sequenced so everything I can get on
      my own comes first, and everything needing somebody else is batched into two conversations rather than
      fifteen interruptions. Steps needing another person are marked.</span></div>
    ${phases.map((p, pi) => `
      <div class="stack gap-12">
        <div>
          <span class="eyebrow">Phase ${pi + 1}</span>
          <h3 style="margin-top:4px">${esc(p.phase)}</h3>
          <p class="prose" style="margin-top:6px;font-size:.88rem">${esc(p.note)}</p>
        </div>
        <div class="card"><div class="card-body"><ol class="steps">
        ${p.steps.map(s => `<li><div class="step-body">
          <div class="step-title">${esc(s.title)} ${s.needs_person ? `<span class="needs">needs someone else</span>` : ""}</div>
          <dl class="stepgrid">
            <dt>The number</dt><dd>${esc(s.need)}</dd>
            <dt>Where from</dt><dd>${esc(s.from)}</dd>
            <dt>Where it goes</dt><dd>${s.goes}</dd>
            <dt>Formula on it</dt><dd>${s.formula}</dd>
            <dt>Sanity check</dt><dd>${s.check}</dd>
            <dt>Tag it</dt><dd><span class="tag tag-${s.tag}">${s.tag}</span></dd>
          </dl>
          ${s.coach === "timing" ? `<p style="font-size:.8rem;color:var(--muted);margin:0">See <b>How to time a process honestly</b> below before starting this one.</p>` : ""}
          ${s.coach === "asking" ? `<p style="font-size:.8rem;color:var(--muted);margin:0">The exact wording is drafted below under <b>How to ask the consultant for her task list</b>.</p>` : ""}
        </div></li>`).join("")}
        </ol></div></div>
      </div>`).join("")}
    ${coachTiming}
    ${coachAsking}`;
}
