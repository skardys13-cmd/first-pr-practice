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

**Located 2026-08-12** in Google Drive folder **"Lecture notes venture capital"**
(`1QCGZPUtT9kyNmPMSDj8noUqY8FsZHz8p`, owner skardys13@gmail.com, created
2026-08-12). 14 PowerPoint decks, ~340 MB total.

Filenames are bare numbers `1.pptx`–`14.pptx`. IDs follow that numbering as a
stable label only — **it does not encode lecture order** (see below). Course,
term, and topic below are taken from each deck's own title slide.

| ID | Filename | Type | Course | Term | Topic | Extracted? | Notes? | X-Ref? | Status |
|---|---|---|---|---|---|---|---|---|---|
| SRC-P-001 | 1.pptx | Deck | C1 (4350) | Spring 2025 | Course intro, syllabus, objectives; instructor background and full investment/board record | Partial | Yes | Yes | Partial — full deck not retrieved |
| SRC-P-002 | 2.pptx (via PDF) | Deck | C1 (4350) | Spring 2026 | Financing the early side of private markets: the 8-method ladder, VC fund structure, cost to reach an IPO | Yes | Yes | Yes | Complete |
| SRC-P-003 | 3.pptx (via PDF) | Deck | C1 (4350) | Spring 2026 | VC vs PE; priced vs unpriced rounds; worked valuation examples; 30 Iowa IPOs | Yes | Yes | Yes | Complete |
| SRC-P-004 | 4.pptx | Deck | [UNCLEAR] | [UNCLEAR] | [NOT PROVIDED] | No | No | No | **Unresolved — deprioritized. Retrieve by exporting to PDF (Drive indexer skips files >~17MB)** |
| SRC-P-005 | 5.pptx | Deck | C1 (4350) | Fall 2025 | VC: term sheets, liquidation preferences, preferred vs common, convertible notes, SAFEs, protective provisions, anti-dilution, vesting | Partial | Yes | Yes | Partial |
| SRC-P-006 | 6.pptx | Deck | **C2 (4310)** | Fall 2024 | Corporate VC vs Fund VC; CVC landscape (50+ named corporate arms); investor pitch deck template | Partial | Yes | Yes | Partial |
| SRC-P-007 | 7.pptx | Deck | C1 (4350) | Spring 2026 | *Silicon Cowboys* / Compaq case wrap-up; founder ownership at IPO; fund economics and carry distribution (Sevin Rosen Fund I) | Partial | Yes | Yes | Partial |
| SRC-P-008 | 8.pptx | Deck | C1 (4350) | [UNCLEAR] | AI, reviewing public financials, Private Equity I; remaining-term class plan | Partial | Yes | Yes | Partial |
| SRC-P-009 | 9.pptx | Deck | C1 (4350) | [UNCLEAR] | Private Equity II, leveraged buyouts, *Barbarians at the Gate* | Partial | Yes | Yes | Partial |
| SRC-P-010 | 10.pptx | Deck | C1 (4350) | [UNCLEAR] | Course recap of private funds; PE case study; leverage/debt "stack"; private capital vs bank debt post-2008 | Partial | Yes | Yes | Partial |
| SRC-P-011 | 11.pptx | Deck | C1 (4350) | Spring 2026 | PE criticism: post-buyout bankruptcies, overleverage; *Bad Company* (2025) | Partial | Yes | Yes | Partial |
| SRC-P-012 | 12.pptx | Deck | C1 (4350) | Spring 2026 | PE deal selection / "bottom feeding"; Allbirds revenue-multiple example | Partial | Yes | Yes | Partial |
| SRC-P-013 | 13.pptx | Deck | C1 (4350) | Spring 2026 | Deal transaction tools: IRR, MOIC, rule-of-thumb return heuristics | Partial | Yes | Yes | Partial |
| SRC-P-014 | 14.pptx | Deck | C1 (4350) | Spring 2026 | Hedge funds, real estate funds, crypto, commodities, REITs; alternatives as an asset class | Partial | Yes | Yes | Partial |

### Course codes — CORRECTED from source material

| Code | Course | Evidence |
|---|---|---|
| `C1` | **FIN/ENTRP 4350** — Private Markets: Venture Capital, Private Equity and Mergers & Acquisitions | Title slides, SRC-P-001 / 013 |
| `C2` | **FIN/ENTRP 4310** — New Venture Finance | Title slide, SRC-P-006 |

**13 of the 14 decks are 4350.** Only `SRC-P-006` is 4310. The folder name
("Lecture notes venture capital") is therefore not a reliable course label, and
the New Venture Finance course is represented by a single deck here.

**Retrieval note:** `SRC-P-002/003/004` initially returned empty content through
the Drive connector. This was **not** an image-only problem — Google's text
indexer silently skips files above ~17 MB. Decks 2 and 3 were recovered as PDF
exports, which bypasses the ceiling entirely.

### Ordering — filename numbering does NOT equal lecture order

The decks span **at least four different offerings**: Fall 2024, Spring 2025,
Fall 2025, Spring 2026. They are not one sequence. Within Spring 2026 the class
plans allow partial ordering (SRC-P-013 IRR/MOIC → SRC-P-011/012 PE →
SRC-P-014 hedge/RE/crypto, which the plan lists last at 5/6). Treat the `Order`
concept as *per-offering*, not across the folder.

Office number is a weak term fingerprint: 3123 Gerdin (SRC-P-001, 014),
3132 Gerdin (SRC-P-008/009/010), 3233 Gerdin (SRC-P-005/006/007/011/012/013).
Recorded as observation, not conclusion.


### Drive file IDs (for retrieval)

| ID | Drive file ID | Size |
|---|---|---|
| SRC-P-001 | `1691I57sYS70jqBGTjgAv_tRp6Gua1T0e` | 12.6 MB |
| SRC-P-002 | `1ATckjwpbH8GshYak09j8yIn27qr-8O99` | 65.2 MB |
| SRC-P-003 | `1nvQKmotLltIu48RUvNM4wEjeFaLxGeW9` | 66.7 MB |
| SRC-P-004 | `1EoWuwgzH3P5s-P9an12y4T5WarAf-p5l` | 91.7 MB |
| SRC-P-005 | `1McT6Btil8f3JEhHQDRA8afn1zhMWmnbd` | 7.9 MB |
| SRC-P-006 | `14G8VSM9xZy3TkEsOqgBxwhFKhpAHVbTp` | 15.1 MB |
| SRC-P-007 | `1_uNZZkSSq4sG1U95wmGkyW8rT4zB_C7a` | 8.2 MB |
| SRC-P-008 | `14jdpQzCn2gxvo-vf0Q2ccnToFIkYrBlK` | 16.9 MB |
| SRC-P-009 | `11EKNaGbem_6WJQeeIEXklIgqYCU7EsXu` | 6.9 MB |
| SRC-P-010 | `1Gft4ajzJxh-cul9Mwb4hyIQKTaKhc2CH` | 5.9 MB |
| SRC-P-011 | `1KUjgMaFQI-1JtFCRdtfqyKDWFJacPN-s` | 7.5 MB |
| SRC-P-012 | `1X-9XB9YhnzYFRQ-bmg8upwuFTVZOiJ0s` | 10.1 MB |
| SRC-P-013 | `10nD-7RQe_d7O3asSFAxca8ZO2KWZtuzH` | 8.8 MB |
| SRC-P-014 | `12x-4hvJUZpqJCPipUkvMjx_CxXEIGaiW` | 16.2 MB |

The large decks (2, 3, 4 — 65–92 MB) almost certainly carry embedded media.
Expect their text-to-filesize ratio to be low and their visual content to matter
more than average.

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
