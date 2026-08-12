# VC / PE / M&A / New Venture Financing — Course Knowledge Base

A permanent, source-traceable knowledge system built from two Iowa State
University courses taught by **Todd Ortberg**, Professor of Practice, Ivy College
of Business:

1. **FIN/ENTRP 4350** — Private Markets: Venture Capital, Private Equity and
   Mergers & Acquisitions
2. **FIN/ENTRP 4310** — New Venture Finance

> **Note:** the project brief originally named the instructor "Gudmundur 'Good'
> Ortberg." Every deck that carries a name says **Todd Ortberg**
> (`ortberg@iastate.edu`). Corrected throughout. See
> `05_MASTER_KNOWLEDGE/Master_Course_Notes.md` §1.

The goal was never to summarize old slide decks. It was to recover everything
useful from both courses and turn it into a professional knowledge system that
supports a move toward venture capital.

---

## STATUS: complete and usable

**13 of 14 decks fully extracted**, with structured notes, master knowledge
libraries, six frameworks, career material, and a study system. **52 files.**

| | |
|---|---|
| Decks extracted | **13 of 14** (`SRC-P-004` never retrieved) |
| Structured deck notes | 13 |
| Databases | 44 companies/deals · 22 investors · 12 people |
| Frameworks | 6 |
| Study material | Cheat sheet · flashcards · 57 questions · 16 worked calcs · 10 cases |

---

## Start here

| If you want to… | Read |
|---|---|
| **Prepare for an interview tomorrow** | [`09_STUDY/VC_Cheat_Sheet.md`](09_STUDY/VC_Cheat_Sheet.md) then [`08_CAREER/Interview_Prep.md`](08_CAREER/Interview_Prep.md) |
| **Learn the material** | [`10_FINAL/Complete_Course_Knowledge_Base.md`](10_FINAL/Complete_Course_Knowledge_Base.md) — the master index with a reading order |
| **Evaluate a company** | [`10_FINAL/Seth_VC_Playbook.md`](10_FINAL/Seth_VC_Playbook.md) |
| **Know what to build next** | [`08_CAREER/Portfolio_Project_Plan.md`](08_CAREER/Portfolio_Project_Plan.md) |
| **Pick up the project cold** | [`00_PROJECT_CONTROL/MASTER_INSTRUCTIONS.md`](00_PROJECT_CONTROL/MASTER_INSTRUCTIONS.md), then `EXTRACTION_STATUS.md`, then `NEXT_SESSION_HANDOFF.md` |

## Layout

```
00_PROJECT_CONTROL/   methodology, manifest, log, status, handoff, tools/
01_PRESENTATION_EXTRACTIONS/   raw verbatim deck extractions
02_PRESENTATION_NOTES/         13 interpreted structured notes  ← the detail
03_SOURCE_DOCUMENTS/           ORIGINALS — read only
05_MASTER_KNOWLEDGE/           course notes, concepts, formulas, heuristics,
                               cases, glossary + the EXTERNAL CONTEXT files
06_DATABASES/                  companies/deals, investors, people, source index
07_FRAMEWORKS/                 investment, financing, deal lifecycle, fund
                               economics, due diligence, investment memo
08_CAREER/                     translation, gap analysis, resume, LinkedIn,
                               interview prep, portfolio projects
09_STUDY/                      cheat sheet, flashcards, questions, calcs, cases
10_FINAL/                      master index + Seth's VC Playbook
```

## The rule that governs everything

**Source-First.** Course material is the primary source. Course terminology,
framing, examples — and even its internal inconsistencies — are preserved rather
than "corrected." Anything from outside is confined to files named
`EXTERNAL_CONTEXT_*` and labelled `EXTERNAL CONTEXT` or `CLAUDE INFERENCE`.
Every major claim carries a source ID. Nothing is invented — missing information
is marked `[NOT PROVIDED]`, `[UNCLEAR]`, or `[VISUAL NOT CAPTURED]`.

**Why this matters practically:** the value of this knowledge base in an
interview is that *"in my venture capital coursework we analyzed X"* is
verifiably true. Blending outside reading into the course layer would leave a
claim that collapses under one follow-up question.

## Known limits

- **`SRC-P-004`** was never retrieved
- Many slides are graphics-only and marked `[VISUAL NOT CAPTURED]`. Largest
  losses: the cap tables in `SRC-P-005`, the carry waterfall in `SRC-P-007`,
  current round benchmarks in `SRC-P-003`
- **4310 New Venture Finance is one deck deep.** Burn rate, runway and unit
  economics are not in the course — filled in
  `05_MASTER_KNOWLEDGE/EXTERNAL_CONTEXT_Gap_Fill.md`
- The course is strong on deal structure and returns, **thin on qualitative
  founder evaluation**

## Extraction tool

```bash
python3 00_PROJECT_CONTROL/tools/extract_source.py --all --export-images
```
Handles `.pptx/.pdf/.docx/.xlsx/.csv/.md/.txt`, converts legacy Office via
LibreOffice, reads originals read-only. **Requires:**
`pip install python-pptx pdfplumber openpyxl python-docx`

> **Retrieval note:** Google Drive's text indexer silently skips files above
> ~17 MB — it returns empty content rather than an error. Three decks failed that
> way. **Exporting to PDF bypasses it entirely.**
