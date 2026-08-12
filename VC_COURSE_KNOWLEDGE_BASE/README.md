# VC / PE / M&A / New Venture Financing — Course Knowledge Base

A permanent, source-traceable knowledge system built from two Iowa State
University courses taught by **Gudmundur "Good" Ortberg**:

1. **Venture Capital, Private Equity, and Mergers & Acquisitions**
2. **New Venture Financing**

The goal is not to summarize old slide decks. It is to recover everything useful
from both courses and turn it into a professional knowledge system that supports
a move toward venture capital — preserving what was taught, organizing it,
connecting it across sources, and only then translating it into study material,
portfolio work, and career material.

---

## ⚠ CURRENT STATE: awaiting source material

The scaffold, methodology, tracking system, database schemas, and a **tested**
extraction pipeline are in place. **No course files have been delivered**, so
every knowledge file is deliberately empty.

That emptiness is the honest state, not an oversight. Filling the Concept
Library, Formula Library, or "Ortberg Rules" from general VC knowledge would
produce something that looks like progress while quietly replacing what the
professor actually taught — and would poison the well for interview prep later,
where an untraceable claim is a liability.

**To unblock:** see
[`03_SOURCE_DOCUMENTS/README_HOW_TO_ADD_SOURCES.md`](03_SOURCE_DOCUMENTS/README_HOW_TO_ADD_SOURCES.md).

---

## Start here

| If you are… | Read |
|---|---|
| Adding course files | [`03_SOURCE_DOCUMENTS/README_HOW_TO_ADD_SOURCES.md`](03_SOURCE_DOCUMENTS/README_HOW_TO_ADD_SOURCES.md) |
| A new session picking this up | [`00_PROJECT_CONTROL/MASTER_INSTRUCTIONS.md`](00_PROJECT_CONTROL/MASTER_INSTRUCTIONS.md), then `EXTRACTION_STATUS.md`, then `NEXT_SESSION_HANDOFF.md` |
| Checking progress | [`00_PROJECT_CONTROL/EXTRACTION_STATUS.md`](00_PROJECT_CONTROL/EXTRACTION_STATUS.md) |

## Layout

```
00_PROJECT_CONTROL/   methodology, manifest, log, status, handoff, tools/
01_PRESENTATION_EXTRACTIONS/   raw verbatim deck extractions
02_PRESENTATION_NOTES/         interpreted structured notes
03_SOURCE_DOCUMENTS/           ORIGINALS — read only
04_DOCUMENT_NOTES/             non-deck sources
05_MASTER_KNOWLEDGE/           course notes, concepts, formulas, heuristics, cases, glossary
06_DATABASES/                  companies/deals, investors/firms, people, source index
07_FRAMEWORKS/                 investment, financing, deal lifecycle, fund economics, DD, memo
08_CAREER/                     translation, gap analysis, resume, LinkedIn, interview, projects
09_STUDY/                      cheat sheet, flashcards, questions, calc practice, cases
10_FINAL/                      consolidated knowledge base, personal VC playbook
```

## Pipeline

```
source file → raw extraction → structured notes → master files + databases
            → frameworks → study material → career material
```

Master files serve as working memory. Later sessions read those rather than
re-reading raw extractions — that is what keeps a 30+ file project affordable
across many sessions.

## The rule that governs everything

**Source-First.** Course material is the primary source. Course terminology,
framing, examples, and even oddities are preserved rather than "corrected."
Anything not from the course is labeled `EXTERNAL CONTEXT` or `CLAUDE INFERENCE`
and kept visibly separate. Every major claim carries its source ID and slide or
page number. Nothing is invented — missing information is marked
`[NOT PROVIDED]` or `[UNCLEAR]`.

## Extraction tool

```bash
python3 00_PROJECT_CONTROL/tools/extract_source.py --all --export-images
python3 00_PROJECT_CONTROL/tools/extract_source.py --file "03_SOURCE_DOCUMENTS/X.pptx" --id SRC-P-004
```

Verified to recover slide text with bullet nesting, speaker notes, tables, chart
series values, Word headings and tables, and spreadsheet **formulas** as well as
values. Handles legacy `.ppt`/`.doc`/`.xls` via LibreOffice. Reads originals in
binary read-only mode and writes only to derived directories.

**Requires:** `pip install python-pptx pdfplumber openpyxl python-docx`
