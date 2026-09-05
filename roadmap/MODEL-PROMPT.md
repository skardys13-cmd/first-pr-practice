# Build me an RIA operations & economics model

Paste this whole file as the first message of a new Claude Code session.

---

## 1. Who this is for

I am Seth. I am a **paraplanner about two months into my first seat at a six-person
RIA**. My boss is **Kristian**. I work on a **Mac** (no Windows, no Power BI Desktop).
I am studying for the **Series 65** independently.

Three things drive everything below:

1. **Our operations consultant leaves in about 100 days.** I am learning her work,
   documenting it, and taking it over in stages during 2–4 protected work hours a week.
2. **I want the operations manager seat**, not an advisor seat. Long term I want to be a
   COO. There is an internal decision point around **December** on whether an operations
   role at this firm becomes real.
3. **I have to show Kristian something.** This model is that something. It has to be
   correct, honest about what it does not know, and useful to him rather than
   impressive at him.

I am 60 days in. I am not the person who tells a firm owner what his numbers are. I am
the person who builds a tool, states his assumptions out loud, and asks to be corrected.
**Everything you build must be shaped by that.**

---

## 2. What to build — two deliverables

### A. An interactive Artifact page (the thing I present from)
A single published HTML artifact: scenario sliders, live charts, four "cases" I can walk
Kristian through. Numbers move, charts move with them, and every figure carries its
provenance. This is the conversation.

### B. A working Excel file (the thing that survives the meeting)
A real `.xlsx` with live formulas — not values pasted in — that Kristian can open, change
and keep. Same engine, same numbers as the page. Multi-tab, documented, with the
assumption ledger as a real sheet.

Build **A first**, get it right, then generate **B** from the same numbers so they can
never disagree.

---

## 3. Hard rules — these are not negotiable

- **No client data leaves approved firm systems.** No names, account numbers, balances,
  statements, or screenshots of live records — not in this model, not in a chat, not in
  a file on my laptop. The model works on **counts, tiers, ranges and averages** only.
- **Compliance ownership stays with the firm's designated CCO / qualified person.**
  Nothing here is a compliance opinion.
- **Never write a password, credential or vendor login into any document.**
- If a number would identify a specific household, it is at the wrong grain — aggregate
  it into a tier until it does not.
- The published page must not name the firm, its custodian, its vendors, or any person.
  Use roles ("Advisor 1", "the custodian") throughout. **The version I show Kristian
  internally can carry real labels; the artifact must not.** Build a single
  `ANONYMISE` toggle that swaps a labels table, defaulting to anonymous.

---

## 4. The assumption ledger — build this FIRST

This is the spine of the whole thing and the reason it will be taken seriously.

I can only see some of the firm's numbers. I can observe AUM, household counts, who does
what, and I can time my own processes. I cannot see the expense lines. So **every single
input in this model carries a provenance tag**, and it is visible everywhere the number
appears:

| Tag | Means | Colour convention |
|---|---|---|
| `MEASURED` | I timed it or counted it myself | strongest |
| `OBSERVED` | I can see it in a firm system or was told it directly | strong |
| `ESTIMATED` | My own judgement, stated as a range | muted, italic |
| `BENCHMARK` | From a published industry source, cited with source and year | muted, with citation |
| `PLACEHOLDER` | Not yet filled in — the model runs but this number is fake | **loud warning colour** |

Requirements:

- Every input cell/field stores a tag alongside the value.
- Every headline output shows **what share of its inputs are measured vs estimated**.
  A big number built on three estimates must say so on its face.
- There is an **Assumptions tab** listing every input: name, value, tag, source, who
  could confirm it, and the date it was last checked.
- There is a **"Show me the estimates"** toggle that highlights, on every screen, every
  figure that is not `MEASURED` or `OBSERVED`.
- Any output whose inputs are more than 50% `ESTIMATED` renders with a visible caveat
  strip. Do not let me walk into Kristian's office with a confident number I invented.

**This ledger is the single most important feature. If you cut anything, do not cut this.**

---

## 5. Model architecture

Three layers, cleanly separated. Inputs never contain formulas; outputs never contain
hard-coded numbers.

### Layer 1 — INPUTS

**5.1 Firm roster** (I will fill this in; build the table)
```
role_id | role label | FTE | is_advisor | is_operations | annual comp (or range) | comp tag
```
Six people. Include the departing consultant as a row with an `end_date`.

**5.2 Client book, by tier** — never per household
```
tier | label            | households | total AUM | avg AUM | tag
T1   | under $250k      |            |           |         |
T2   | $250k – $1m      |            |           |         |
T3   | $1m – $3m        |            |           |         |
T4   | over $3m         |            |           |         |
```

**5.3 Fee schedule** — as a real tiered table, never a blended guess
```
from_amount | to_amount | rate
```
**Tiered means each band is charged at its own rate.** A flat rate applied to total
assets is a different and wrong model. Build it as a lookup table so breakpoints can be
changed. Test it against a hand calculation on three households: one below the first
breakpoint, one just above, one well above. If the "just above" case is wrong, you have
built a flat-rate model by accident — this is the single most common error in these
models.

**5.4 Operations task catalogue** — the heart of it
```
task | trigger (per household / per account / per year / ad hoc)
     | minutes per occurrence | occurrences per year | applies to tier(s)
     | owner role_id | tag
```
Seed it with the real shape of RIA operations work: account opening, ACAT/transfers,
money movement and distributions, RMDs, billing cycle, quarterly/annual reporting,
performance reporting, CRM hygiene, meeting prep, meeting follow-up, annual review
scheduling, beneficiary and account maintenance, death claims, trade errors, custodian
reconciliation, compliance calendar items, vendor management, onboarding/offboarding.

Mark every seeded row `PLACEHOLDER` until I replace it with a timed figure. **I will time
these myself — that is the `MEASURED` column, and it is my strongest evidence in the
whole model.**

**5.5 Cost and capacity constants**
```
benefits_load          default 25%   BENCHMARK  (state the source)
productive_hours_year  default 1700  ESTIMATED  (2080 less PTO, holidays, admin)
loaded_hourly(role)    = comp × (1 + benefits_load) / productive_hours_year
growth_rate_households default 15%   ESTIMATED
```

### Layer 2 — ENGINE

```
revenue_household(tier)  = tiered_fee(avg_AUM(tier))
revenue_total            = Σ households(tier) × revenue_household(tier)

ops_minutes(tier)        = Σ over tasks applying to tier:
                             minutes × occurrences_per_year
ops_hours_required       = Σ households(tier) × ops_minutes(tier) / 60
ops_hours_available      = Σ FTE(operations roles) × productive_hours_year
utilisation              = ops_hours_required / ops_hours_available

cost_to_serve(tier)      = ops_minutes(tier)/60 × loaded_hourly(blended ops)
margin(tier)             = revenue_household(tier) − cost_to_serve(tier)

revenue_per_advisor      = revenue_total / count(is_advisor)
revenue_per_employee     = revenue_total / total FTE
revenue_per_household    = revenue_total / total households

capacity_break_households = solve: ops_hours_required(H) = ops_hours_available
capacity_break_date       = today + time to reach that H at growth_rate
```

Show the capacity break as **both a household count and a date.** A date makes a firm act;
a count does not.

### Layer 3 — OUTPUTS

Four cases, each a view on the page and a tab in Excel. Each one ends on a **single
sentence with a number in it.**

---

## 6. The four cases

### Case 1 — "What happens in 100 days" (the consultant's departure)
The most urgent and the hardest to argue with. Build it first.

- Her rows in the task catalogue → hours per year she currently absorbs.
- What happens to `utilisation` when her hours move to the remaining team.
- Three redistribution scenarios, side by side, each costed:
  1. Absorb across the existing team (show the utilisation number this produces)
  2. Backfill with a hire (show the cost, and the break-even)
  3. **I take it on** (show the cost, the hours, and what I would have to stop doing)
- Output sentence: *"When she leaves, N hours a year need a home. Here are the three
  places they can go and what each costs."*

### Case 2 — "Where capacity breaks"
- `ops_hours_required` vs `ops_hours_available` projected forward at the growth rate.
- The crossover point: household count **and** date.
- Sensitivity: what the date becomes at 10% / 15% / 20% growth.
- Output sentence: *"At current growth, operations runs out of capacity at N households,
  around [month year]."*

### Case 3 — "What each client tier costs to serve"
- Revenue per household vs cost to serve per household, tier by tier.
- Identify the tier where cost exceeds revenue.
- **Handle this carefully.** Present it as a question, not a verdict. The three responses
  are: raise the minimum, serve that tier differently, or accept it as a pipeline cost.
  Lay out all three neutrally. Do not recommend one.
- Output sentence: *"The bottom tier costs roughly $X to serve and produces $Y. That is a
  decision, and here are the three versions of it."*

### Case 4 — "The operations seat" (my ask)
- Cost of the seat: my comp delta, loaded.
- What it protects: advisor hours returned × what an advisor hour is worth; service
  failures avoided; the consultant's hours covered.
- Break-even: what the seat has to protect to pay for itself.
- **Frame it as protection, not generation.** An operations hire protects advisor capacity
  and prevents service failure. Claiming it directly generates revenue will get challenged
  and I will lose the room.
- Output sentence: *"The seat costs $X loaded. It has to protect $Y to pay for itself.
  Here is where that $Y comes from."*

---

## 7. Scenario controls

Live sliders/inputs on the page, wired to a scenario switch in Excel. Every chart and
every headline number responds immediately.

- Household growth rate (0–30%)
- Average fee realisation (to test the fee schedule)
- Operations headcount (with and without the consultant, with and without a new seat)
- Minutes per task — a global efficiency multiplier (what a 10% process improvement does)
- Benefits load
- Productive hours per year
- Blended ops hourly rate

Plus three **preset scenarios** as one-click buttons:
- **Today** — as things are
- **She's gone, nothing changes** — the do-nothing case
- **She's gone, I own operations** — my proposal

Add a **compare mode** that shows any two scenarios side by side with the deltas called
out. The deltas are the argument.

---

## 8. Charts

Read the `dataviz` skill before writing any chart code. Requirements:

- Every chart responds to the scenario controls **live**. No static images.
- **Capacity chart** — required vs available operations hours over time, with the
  crossover point marked and labelled with its date. This is the money chart.
- **Tier economics chart** — revenue per household vs cost to serve, by tier, with the
  crossing point visible.
- **Departure waterfall** — her hours, and where they land under each scenario.
- **Break-even chart** for the seat.
- **Sensitivity tornado** — which assumptions move the answer most. This is the chart
  that makes an owner trust the model, because it admits what it does not know.
- Colourblind-safe categorical palette; validate it. Never encode meaning in colour alone —
  pair every colour signal with a label, shape or text marker.
- Light and dark theme, using tokens on bare `:root` with the dark overrides guarded.
- Wide content scrolls inside its own container; the page body never scrolls sideways.
- Every axis labelled with its unit. Every estimated series visually distinguished from
  measured ones.

---

## 9. The Excel file

Generate it with real formulas using the `xlsx` skill. Structure:

1. **README** — what this is, who built it, what is measured vs estimated, how to change
   the fee schedule, and the date.
2. **Assumptions** — the full ledger. Every input, tagged, sourced, dated.
3. **Roster** — input.
4. **Book** — tiers, households, AUM. Input.
5. **FeeSchedule** — the tiered table. Input.
6. **Tasks** — the operations task catalogue. Input.
7. **Engine** — all calculations. No hard-coded numbers anywhere on this sheet.
8. **Case1_Departure**, **Case2_Capacity**, **Case3_CostToServe**, **Case4_Seat**.
9. **Dashboard** — the summary Kristian looks at first, with native Excel charts.

Rules:
- Input cells one fill colour, formula cells another, clearly keyed on the README.
- Named ranges for every constant. No magic numbers inside formulas.
- Scenario switch driven by a single cell that the case tabs read.
- Data validation on tag columns so provenance cannot be left blank.
- Every sheet has a header row that freezes.
- Number formats: currency with no decimals, percentages to one decimal, hours to one.
- It must open cleanly and recalculate on a Mac in both Excel and Numbers.

---

## 10. The workflow — walk me through this step by step

I want a **numbered, click-by-click build workflow**, delivered as its own section of the
finished page (a "How this was built" tab) *and* as a checklist I work through with you in
this session. For every single step:

- **What number I need**, in plain words
- **Where it comes from** — which system, which report, which screen, or which person
- **Exactly how to ask** if it comes from a person, including the actual sentence to say
- **Where it goes** — which field on the page, which cell in the workbook
- **What formula, if any, sits on it**
- **How to sanity-check it** before moving on — what a wrong value would look like
- **What tag it gets**

Sequence the workflow so I can start tonight with things I can get on my own, and so the
things that need Kristian or the consultant are batched into as few conversations as
possible. Explicitly mark which steps need someone else, and draft those asks for me.

Two specific pieces of coaching I want written into the workflow:

- **How to time a process honestly.** Three runs, not one. Include the interruptions.
  Record the median, not the best. A timing I flatter myself with is worse than no timing.
- **How to ask the consultant for her task list** without it sounding like I am measuring
  her on her way out the door. This matters. Draft the exact wording.

---

## 11. How to present it to Kristian

Write me a short section — this goes in the page, and I want to rehearse it:

- **The opening sentence.** One sentence on what the model is and what I want from him.
  It should ask him to correct my assumptions, not admire my work.
- **The order to walk the four cases in**, and why. (My instinct: the departure first,
  because it is the problem he already has.)
- **The three questions I should ask him**, phrased so the answers improve the model.
- **The one thing not to say.** Specifically: do not present cost-to-serve as a finding
  about specific clients, and do not lead with the seat I want. The seat is the last
  slide, not the first.
- **What to do when he disagrees with a number.** The correct answer is to change it in
  front of him and show what it does to the chart. That is the entire point of building it
  interactive — a model that updates while he watches is a tool; one that does not is a
  presentation.
- A one-page printable summary I can leave behind.

---

## 12. Build order

1. Assumption ledger and provenance system.
2. Input layer with realistic `PLACEHOLDER` values so the thing runs end to end from day one.
3. Engine, with the tiered fee calculation tested against three hand-worked households.
4. Case 1 (departure), then 2, 3, 4.
5. Scenario controls and compare mode.
6. Charts.
7. The build workflow and the presentation section.
8. Excel generation from the same numbers.
9. Verification pass.

## 13. Verification — do this before telling me it is done

- Tiered fee maths hand-checked at three household sizes, including one just above a
  breakpoint. Show me the working.
- Capacity crossover recomputed by hand at one growth rate and matched to the chart.
- Every headline figure on the page traced back to its inputs and their tags.
- Change every slider through its full range and confirm nothing renders `NaN`,
  `Infinity`, a negative household count, or a divide-by-zero.
- Set operations headcount to zero and confirm the model fails visibly rather than
  silently producing a number.
- Confirm the Excel file and the page produce identical figures for all four cases.
- Confirm no client-identifying data exists anywhere in either deliverable.
- Confirm the anonymise toggle actually removes every real label.

## 14. Ask me before you build

Ask me for: the roster and roughly what each person does, my best current figures for
households and AUM by tier, the fee schedule, and which operations tasks I have already
timed. Ask in one batch, not one at a time. Where I do not know something, put in a
`PLACEHOLDER`, tell me who at the firm would know, and keep building.
