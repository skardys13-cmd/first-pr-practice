# HOW TO ADD SOURCE MATERIAL

**Everything in this folder is READ-ONLY once added.** Nothing in the project
ever modifies, renames, reformats, or deletes an original course file. All work
product is written to derived folders (`01_`, `02_`, `04_`–`10_`).

---

## What to add

Everything from both courses. More is better than less — the methodology
deduplicates, so overlap costs almost nothing while a missing file is invisible.

- Slide decks (`.pptx`, `.ppt`) — **the primary material**
- PDFs, Word documents, class notes
- Cases, assignments, exams, handouts, readings, articles
- Spreadsheets and financial models (`.xlsx`) — the **formulas** are the teaching
  content and are extracted along with the values
- **The syllabus or course schedule, if one exists** — process this first; it
  settles the deck ordering for both courses in one shot

Assignments and graded work matter more than they look. They show what Seth was
actually asked to *produce*, which is the strongest evidence available for
honest resume and interview claims.

## Delivery method: PASTED TEXT (chosen 2026-08-12)

Seth pastes lecture content directly into the conversation, one lecture at a
time, as he needs it. There is no bulk file upload.

**Handling procedure for pasted lectures — follow this every time:**

1. Save the paste **verbatim** to `03_SOURCE_DOCUMENTS/<SRC-ID>_<short-name>.md`.
   Do not clean it up, reflow it, fix typos, or reorder it on the way in. The
   saved file becomes the immutable original for that lecture, and it is the
   only copy that will ever exist — there is no underlying `.pptx` to go back to.
2. Register it in `FILE_MANIFEST.md` with a final `SRC-P-###` ID.
3. Run the extractor on it (see below), then write structured notes.
4. Roll entities/numbers/formulas/concepts up into `05_MASTER_KNOWLEDGE/` and
   `06_DATABASES/`, cross-reference against earlier lectures, update the log and
   status, and commit.

**What to ask Seth to include with each paste**, since it cannot be recovered
from the text later:

- Which course — VC/PE/M&A, or New Venture Financing
- The lecture title and number, or roughly where it fell in the semester
- Whether the paste is the complete lecture or a portion

If those are missing, mark them `[NOT PROVIDED]` in the manifest rather than
guessing, and ask when convenient — do not stall the extraction over it.

**Known limitation of the paste route.** Copying from a deck loses what was not
text: chart data, table layout, diagrams, images, and speaker notes. When a
lecture clearly referenced a visual that did not survive the paste, record
`[VISUAL NOT CAPTURED]` at that point in the notes rather than inventing what
it showed. If a specific chart or table matters, ask for it separately.

## Also supported, if files ever do become available

- **Commit them into this folder** and push (GitHub rejects files over 100 MB).
- **Attach to a session** — fine for a handful of files.
- **Google Drive** — the connector works; a single folder of materials can be
  pulled directly.

Mixing methods is fine, and so is delivering in batches — the manifest and
process log track exactly what has been processed, so later batches resume
cleanly instead of restarting.

## Naming

Original filenames are preserved exactly as they are. **Do not rename anything
to be helpful** — the manifest assigns a stable `SRC-` ID to each file, and
messy original names are useful evidence for reconstructing course order.

If the two courses' materials are already separated, keep that separation as
subfolders; it is a useful signal. If they are mixed, that is fine too — course
attribution is worked out from the content.

## Then run

```bash
python3 VC_COURSE_KNOWLEDGE_BASE/00_PROJECT_CONTROL/tools/extract_source.py \
        --all --export-images
```

This performs mechanical, verbatim extraction only — it never summarizes.
Interpretation happens afterward, by reading the extractions.

## Known limitations to be aware of

| Situation | Behavior |
|---|---|
| Scanned-image PDF | No OCR available in this environment → pages come out `[NO TEXT EXTRACTED]`. Will be flagged as unresolved, never guessed at. |
| Chart pasted in as a picture | Not machine-readable. Exported via `--export-images` and read visually instead. |
| Legacy `.ppt` / `.doc` / `.xls` | Auto-converted through LibreOffice into a scratch directory. The original is never touched. |
| Spreadsheet never opened in Excel | Cached values may be blank; formulas still extract correctly. |
| Pasted text (`.md` / `.txt`) | Preserved verbatim. Slide/section markers (`Slide 4`, `Lecture 2`, …) are auto-detected and indexed so citations stay addressable; if none are found, citations fall back to line numbers. |
