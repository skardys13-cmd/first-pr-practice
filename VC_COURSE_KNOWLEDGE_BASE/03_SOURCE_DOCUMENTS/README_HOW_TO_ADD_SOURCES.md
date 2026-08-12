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

## Three ways to deliver

**1. Google Drive (recommended for a large batch).** The Drive connector is
live and working in this session. Put everything into a single Drive folder —
e.g. `VC Course Materials` — and say so. Files can be pulled directly from
there, subfolders and all. Best option for ~30+ files.

**2. Commit them into this folder.** Drop the files here and push. Fine if the
files are already on a machine with the repo checked out. Note that GitHub
rejects individual files over 100 MB; large decks may need Drive instead.

**3. Attach to a session.** Works for a handful of files at a time; awkward for
a full course archive.

Mixing methods is fine. So is delivering in batches — the manifest and process
log track exactly what has been processed, so a later batch resumes cleanly
instead of restarting.

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
