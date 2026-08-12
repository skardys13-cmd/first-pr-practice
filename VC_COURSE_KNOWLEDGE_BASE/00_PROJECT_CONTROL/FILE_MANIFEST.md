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

Filenames are bare numbers `1.pptx`–`14.pptx`. Provisional IDs below follow that
numbering on the assumption it reflects lecture order — **unverified**, since no
deck content has been read yet. Topic, course attribution, and final ordering
stay `[NOT PROVIDED]` until the content is inspected; do not fill them from the
filename alone.

| ID | Filename | Type | Course | Order | Topic | Extracted? | Notes Created? | Cross-Referenced? | Status |
|---|---|---|---|---|---|---|---|---|---|
| SRC-P-001 | 1.pptx | Deck | C? | 1? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-002 | 2.pptx | Deck | C? | 2? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-003 | 3.pptx | Deck | C? | 3? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-004 | 4.pptx | Deck | C? | 4? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-005 | 5.pptx | Deck | C? | 5? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-006 | 6.pptx | Deck | C? | 6? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-007 | 7.pptx | Deck | C? | 7? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-008 | 8.pptx | Deck | C? | 8? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-009 | 9.pptx | Deck | C? | 9? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-010 | 10.pptx | Deck | C? | 10? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-011 | 11.pptx | Deck | C? | 11? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-012 | 12.pptx | Deck | C? | 12? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-013 | 13.pptx | Deck | C? | 13? | [NOT PROVIDED] | No | No | No | Located, not retrieved |
| SRC-P-014 | 14.pptx | Deck | C? | 14? | [NOT PROVIDED] | No | No | No | Located, not retrieved |

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
