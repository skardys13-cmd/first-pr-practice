# FILE MANIFEST

Authoritative registry of every source file. **Filenames are not trusted** —
the Source ID assigned here is the stable identifier used in every derived file.

**Rule:** once an ID appears in a derived file, it never changes.

## ID scheme

| Prefix | Meaning |
|---|---|
| `SRC-P-###` | Presentation / slide deck |
| `SRC-C-###` | Case study |
| `SRC-A-###` | Assignment |
| `SRC-S-###` | Spreadsheet / model |
| `SRC-R-###` | Reading / article / handout |
| `SRC-N-###` | Class notes |
| `SRC-D-###` | Other document |

`SRC-P` numbering follows **reconstructed course order**, not filename order.
The extraction tool assigns provisional IDs; this table holds the final ones.

## Course codes

| Code | Course |
|---|---|
| `C1` | Venture Capital, Private Equity, and Mergers & Acquisitions |
| `C2` | New Venture Financing |
| `C?` | Course not yet determined |

---

## REGISTERED SOURCES

*No source files have been delivered. Table is empty by design, not by omission.*

| ID | Filename | Type | Course | Order | Topic | Extracted? | Notes Created? | Cross-Referenced? | Status |
|---|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — | Awaiting source material |

### Column meanings

- **Order** — position within its course (from syllabus, dates, or content
  sequence). Leave blank while genuinely unknown; do not guess.
- **Extracted?** — raw machine extraction exists in `01_` or `04_`.
- **Notes Created?** — interpreted structured notes exist in `02_` or `04_`.
- **Cross-Referenced?** — connected to other sources and rolled up into
  `05_MASTER_KNOWLEDGE/` and `06_DATABASES/`.
- **Status** — `Complete`, `In progress`, `Unresolved — <specific reason>`.

A source is only `Complete` after passing the quality-control check below.

---

## QUALITY CONTROL CHECK

Before marking a source complete, confirm all of the following:

- [ ] Major concepts captured
- [ ] Slides genuinely inspected — not just plain text scraped (charts, tables,
      diagrams, images reviewed)
- [ ] Company examples captured
- [ ] Investors / firms captured
- [ ] People captured
- [ ] Deals and transactions captured
- [ ] Meaningful numbers captured
- [ ] Formulas captured
- [ ] Frameworks captured
- [ ] Practical lessons captured
- [ ] Career insights captured
- [ ] Cross-referenced against related material
- [ ] Source traceability preserved (source ID + slide/page on every major claim)

If any box fails, the source goes back to `In progress`.
