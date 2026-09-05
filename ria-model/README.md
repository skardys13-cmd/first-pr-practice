# Operations capacity & economics model

A model of how much operations work an RIA carries, who carries it, what it costs, and when it
runs out of room. Built as a working tool for a conversation with a firm principal — not as a
firm document, and not as a compliance opinion.

**The point of it is the provenance ledger.** Every input carries a tag saying whether it was
measured, observed, taken from a benchmark, estimated, or invented so the model would run. Every
headline output shows what share of its inputs are which, and anything resting on a placeholder
says so on its face.

## Two deliverables, one engine

| File | What it is |
|---|---|
| `dist/operations-capacity-model.html` | The interactive page: scenario sliders, live charts, four cases |
| `dist/RIA_Operations_Model.xlsx` | The workbook: 13 tabs, live formulas, native charts, named ranges |

Both are generated from `inputs.json` by the same engine, so they cannot disagree — and
`verify_parity.py` proves it by evaluating the workbook's formulas independently and comparing
every figure against the page's engine.

## Layout

```
inputs.json        canonical inputs + provenance tags. The single source of truth.
engine.mjs         the engine. Pure functions, no DOM, no hard-coded firm numbers.
page.head.html     page: tokens, type, components
page.body.html     page: structure
app.a..e.js        page: provenance system, charts, renderers, controls
build.mjs          inlines inputs.json + engine.mjs into dist/*.html
make_xlsx.py       generates the workbook from inputs.json
verify.mjs         engine: hand-checks, independent recomputation, slider sweeps
verify_page.mjs    published page: privacy, anonymisation, integrity
verify_parity.py   workbook ↔ page: every figure, all four cases
smoke.mjs          headless browser: panels, sliders, toggles, failure mode
dump.mjs           engine values as JSON, for the parity check
```

## Rebuild

```bash
node build.mjs                  # page  -> dist/operations-capacity-model.html
python3 make_xlsx.py            # workbook -> dist/RIA_Operations_Model.xlsx
node verify.mjs                 # 29 checks
node verify_page.mjs            # 14 checks
node dump.mjs && python3 verify_parity.py   # 105 checks
node smoke.mjs                  # browser
```

## Verification status

148 automated checks, all passing:

- Tiered fee maths hand-worked at three household sizes, including one just above a breakpoint
  (the case where a flat-rate model silently substitutes itself for a tiered one).
- Operations hours and revenue recomputed by a second, independent code path.
- Capacity crossover hand-worked in closed form and reconciled with the projection.
- 105 scenario combinations swept for `NaN`, `Infinity` and negative counts.
- Zero operations headcount makes the model refuse to run rather than produce a number.
- Workbook and page produce identical figures for all four cases.
- No client-identifying data, no credentials, and no person, firm or vendor name anywhere.

`recalc.py` (LibreOffice) could not be used — LibreOffice cannot load any file in this sandbox,
including a three-cell test workbook. The workbook's formulas are instead evaluated by the
`formulas` package, which found and forced the fix of three real `#VALUE!` errors
(`SUMPRODUCT` across mismatched range orientations). It now evaluates 3,054 cells with zero
errors, and `fullCalcOnLoad` is set so Excel and Numbers compute everything on open.

## Rules this model runs under

- No client data. Counts, tiers, ranges and averages only; the smallest unit anywhere is a tier.
- Nothing here is a compliance opinion. Compliance ownership stays with the firm's designated person.
- No credential, password or vendor login appears in any file.
- The published page names no person, firm, custodian or vendor. `ANONYMISE` defaults to on and the
  labels table ships with its "real" column identical to its anonymous one.
