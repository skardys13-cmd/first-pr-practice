# Ops Ladder

A single-file, self-contained 364-task career system: month one at an RIA →
Florida → the operations ladder → $130-150k.

Calibrated for ~6-8 hours a week, weighted to the operations-leadership path, and
built on a Mac toolchain (Tableau Public, DuckDB, Looker Studio) since Power BI
Desktop is Windows-only.

The compensation model is anchored on a known step: Associate Advisor at around
$65k, three to six months out, gated on the Series 65. Targets are $80k+ on the
move, $100k at year two, $130-150k at years four to six.

- `index.html` — the whole application. No build step, no dependencies. Open it in a
  browser, or publish it as a Claude Artifact.

Progress is stored in the browser (`localStorage`) and, when published as an Artifact
with the `db` capability, synced across devices. Use **Export backup** on the left rail
to keep a copy of your data.

## How it works

There are 364 tasks in a fixed order and **none of them has a date**. The Tonight tab
pulls the next few off the top of the queue and fills whatever session length you pick
(30 minutes to a long session). Finish one and the list regenerates. Skip a week or a
month and the same work is still there, in the same order — nothing goes overdue.

Each task has quarter buttons (log how far you got — partial minutes count toward
banked hours and the task stays pinned to the front of the queue), **Done**, and
**Not this one** (drops it a few places down the queue).

The dashboard reports a rate measured from what you have actually been doing and
projects a finishing date from it. Gaps do not create a backlog; they move that date.

The only dated things are on the Milestones tab: the Series 65 exam, the Florida move,
and the compensation targets. The tracker does not schedule study or quiz you — the
exam sits there as a date and a plan for the week you pass.

Contents: 364 tasks across 52 blocks and 4 phases, a 40-process SOP index, three skill
ladders, a Tampa Bay target board with outreach scripts, a compensation model, a
Florida move plan, 17 reusable prompts, 8 automation recipes, a risk register, and six
charts.
