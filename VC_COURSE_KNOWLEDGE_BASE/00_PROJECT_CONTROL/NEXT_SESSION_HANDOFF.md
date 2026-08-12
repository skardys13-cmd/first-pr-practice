# NEXT SESSION HANDOFF

**PROJECT:** VC / PE / M&A / New Venture Financing Course Knowledge Extraction
**HANDOFF WRITTEN:** 2026-08-12 (end of Session 1)

---

## LAST COMPLETED SOURCE

None. No source material has been delivered.

## CURRENT SOURCE

None.

## NEXT SOURCE

The first deck delivered into `03_SOURCE_DOCUMENTS/`.

---

## COMPLETED SO FAR

Session 1 established the machinery, not the knowledge:

- Full directory structure per `MASTER_INSTRUCTIONS.md` §5
- `MASTER_INSTRUCTIONS.md` — the complete methodology, self-contained, so the
  project can continue without the original chat thread
- `FILE_MANIFEST.md`, `PROCESS_LOG.md`, `EXTRACTION_STATUS.md`, this handoff
- Four database CSVs with headers and documented schemas
- Master-knowledge and framework stubs, each explicitly marked as awaiting
  source material
- `00_PROJECT_CONTROL/tools/extract_source.py` — extraction harness, **built and
  verified** against .pptx (text, bullet levels, speaker notes, tables, chart
  series), .docx (headings, tables), and .xlsx (values **and** formulas)

## CURRENT OUTPUT FILES

Everything under `VC_COURSE_KNOWLEDGE_BASE/`. Nothing outside it was touched.

## MASTER KNOWLEDGE STATUS

**v0.0 — empty by design.** No concepts, formulas, heuristics, cases, or
glossary entries exist, because no course material exists. This is correct, not
an oversight. See `EXTRACTION_STATUS.md` → "DELIBERATELY NOT DONE".

## DATABASE STATUS

All four CSVs contain headers only, zero rows.

## OPEN QUESTIONS FOR SETH

1. **How will the ~30+ files be delivered?** Recommended: a single Google Drive
   folder (the Drive connector is live and working in this session). Also fine:
   committing them into `03_SOURCE_DOCUMENTS/`, or attaching them to a session.
2. Are both courses' materials mixed together, or already separated by course?
3. Is there a syllabus or schedule? That would settle deck ordering immediately
   and is worth processing **first** — it is the map for everything else.
4. Any graded assignments/exams with his own work on them? Those are the
   strongest career-translation evidence (they show what he actually produced,
   not just what he was shown).

## KNOWN EXTRACTION ISSUES

- No OCR available (`tesseract` not installed) — scanned-image PDFs will yield
  `[NO TEXT EXTRACTED]` per page. Flag and report; do not guess at content.
- Chart extraction reads the plotted series data. Charts pasted in as **images**
  cannot be read this way — export them with `--export-images` and read them
  visually before finalizing notes.
- Spreadsheet cached values can be blank if a workbook was never opened in
  Excel; the formulas still extract correctly.

---

## NEXT ACTION (exact)

```bash
# 1. Confirm sources have landed
ls -la VC_COURSE_KNOWLEDGE_BASE/03_SOURCE_DOCUMENTS/

# 2. Mechanically extract everything (originals are never modified)
python3 VC_COURSE_KNOWLEDGE_BASE/00_PROJECT_CONTROL/tools/extract_source.py \
        --all --export-images
```

Then:

3. Register every file in `FILE_MANIFEST.md` with a **final** source ID.
   Presentation numbering follows reconstructed **course order**, not filename
   order. Process any syllabus first to establish that order.
4. Read the raw extractions and write structured notes into
   `02_PRESENTATION_NOTES/` using the §9 template.
5. Roll entities, numbers, formulas, concepts, and heuristics up into
   `05_MASTER_KNOWLEDGE/` and `06_DATABASES/` as you go — not in a batch at the end.
6. Cross-reference each new source against what is already processed.
7. Update `PROCESS_LOG.md` and `EXTRACTION_STATUS.md` after each source.
8. Continue autonomously through all sources. Do not ask permission between files.

---

## IMPORTANT

- Read `MASTER_INSTRUCTIONS.md` before continuing.
- Do not restart completed work.
- Do not modify original course materials.
- Do not populate knowledge files from general VC knowledge — **only** from
  Professor Ortberg's material. An empty file is correct; an invented one is not.
- Work on branch `claude/vc-pe-ma-course-extraction-ray2bh`. Commit and push at
  the end of every working session.
