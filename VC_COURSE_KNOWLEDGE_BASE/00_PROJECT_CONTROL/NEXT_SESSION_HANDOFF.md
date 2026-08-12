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

## DELIVERY METHOD — SETTLED

**Seth pastes lectures into the conversation, one at a time, as needed.** There
is no bulk upload and no underlying deck files. Each paste is saved verbatim
into `03_SOURCE_DOCUMENTS/` and becomes the immutable original for that lecture.

Full handling procedure: `03_SOURCE_DOCUMENTS/README_HOW_TO_ADD_SOURCES.md`.

Implications to keep in mind:

- **The saved paste is the only copy.** There is no source deck to re-check a
  detail against, so capture generously on the first pass.
- Visuals do not survive a paste. Mark `[VISUAL NOT CAPTURED]` where a lecture
  clearly referenced a chart/table/diagram that is not in the text. Never invent
  what it showed.
- Course order arrives incrementally and possibly out of sequence. Keep the
  manifest's `Order` column provisional and re-sort as the picture fills in.

## OPEN QUESTIONS FOR SETH

1. Ask **with each paste**: which course, lecture title/number or rough position
   in the semester, and whether it is the complete lecture. Mark `[NOT PROVIDED]`
   rather than guessing; do not stall extraction waiting on an answer.
2. Is there a syllabus or schedule he could paste **first**? It would settle
   ordering for both courses in one shot and is the map for everything else.
3. Any graded assignments or exams with his own work? Those are the strongest
   career-translation evidence — they show what he actually produced, not just
   what he was shown.

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

**Blocked on one thing: Drive read permission.** Once granted, work
`SRC-P-001` → `SRC-P-014` in order, one deck per cycle:

```
1. read_file_content(fileId)          # Drive file IDs are in FILE_MANIFEST.md
2. Save the returned text VERBATIM to
   03_SOURCE_DOCUMENTS/SRC-P-###_<n>.md          <- immutable original
3. python3 00_PROJECT_CONTROL/tools/extract_source.py \
          --file "03_SOURCE_DOCUMENTS/SRC-P-###_<n>.md" --id SRC-P-###
```

Determine each deck's **course** and **topic** from its content and correct the
manifest — the folder name is not proof all 14 are the VC/PE/M&A course.

Then:

3. Register it in `FILE_MANIFEST.md` with its final source ID.
4. Read the raw extraction and write structured notes into
   `02_PRESENTATION_NOTES/` using the §9 template.
5. Roll entities, numbers, formulas, concepts, and heuristics up into
   `05_MASTER_KNOWLEDGE/` and `06_DATABASES/` as you go — not batched at the end.
6. Cross-reference the new lecture against everything already processed.
7. Update `PROCESS_LOG.md` and `EXTRACTION_STATUS.md`.
8. Commit and push. Then wait for the next paste — do not ask whether to continue.

If several lectures arrive at once, process them all in sequence autonomously.

---

## IMPORTANT

- Read `MASTER_INSTRUCTIONS.md` before continuing.
- Do not restart completed work.
- Do not modify original course materials.
- Do not populate knowledge files from general VC knowledge — **only** from
  Professor Ortberg's material. An empty file is correct; an invented one is not.
- Work on branch `claude/vc-pe-ma-course-extraction-ray2bh`. Commit and push at
  the end of every working session.
