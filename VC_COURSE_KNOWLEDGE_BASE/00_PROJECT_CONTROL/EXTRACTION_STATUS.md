# EXTRACTION STATUS

**Last updated:** 2026-08-12
**Master knowledge version:** v0.0 (no course knowledge yet — scaffold only)

---

## PROJECT STATUS

```
Presentations discovered:      0
Presentations processed:       0
Presentations remaining:       0   (none delivered yet)

Other documents discovered:    0
Other documents processed:     0
Other documents remaining:     0   (none delivered yet)
```

## DELIVERY METHOD

**Pasted text.** Seth pastes lectures into the conversation one at a time, as
needed — there is no bulk file upload and no underlying deck files. Each paste
is saved verbatim into `03_SOURCE_DOCUMENTS/` and becomes the immutable original
for that lecture. The extractor accepts `.md`/`.txt` and auto-indexes any
slide/section markers so citations stay addressable.

Consequence: the saved paste is the **only** copy of that lecture — there is no
source deck to re-check against — and visuals (charts, tables, diagrams, speaker
notes) do not survive a copy-paste. Capture generously on the first pass and
mark `[VISUAL NOT CAPTURED]` rather than inferring what a missing exhibit showed.

## CURRENT STATE

**Ready and waiting for the first lecture paste.**

The project scaffold, methodology, tracking system, database schemas, and a
tested extraction pipeline are all in place. **No lecture content has been
pasted yet**, so no course knowledge exists in this repository.

Locations checked on 2026-08-12 before the paste workflow was settled, all empty
of course material:

| Location | Result |
|---|---|
| `/home/user/first-pr-practice` (repo) | Only the unrelated `wordcount.py` practice project |
| `/mnt/attach` (session attachments) | Empty |
| `/mnt/user-data` | Empty |
| Filesystem-wide sweep for `.pptx/.ppt/.pdf/.docx/.xlsx` | No course files |
| Google Drive — `fullText contains 'Ortberg'` | 0 results |
| Google Drive — titles containing "Venture" | 0 results |
| Google Drive — all Slides/PowerPoint files | 3 files, none from either course |
| Google Drive — `'term sheet' / 'pre-money' / 'liquidation preference'` | 2 hits, both Series 65 exam prep, not course material |

## LAST COMPLETED

Session 1 — project scaffold, `MASTER_INSTRUCTIONS.md`, tracking files, database
schemas, and `tools/extract_source.py` (built and verified against .pptx, .docx,
and .xlsx fixtures).

## NEXT

Ingest course files once delivered. See `NEXT_SESSION_HANDOFF.md`.

## OPEN ISSUES

1. **No lecture content pasted yet.** Everything downstream waits on this.
2. Course order arrives incrementally and possibly out of sequence, since
   lectures are pasted as needed rather than in bulk. Keep the manifest's
   `Order` column provisional and re-sort as the picture fills in. A pasted
   syllabus would resolve it in one step.
3. Scanned-image PDFs would need OCR — `tesseract` is **not** installed in this
   environment. Flag any such file as unresolved and note it here.
4. `.ppt`/`.doc`/`.xls` legacy files convert via LibreOffice (installed) — path
   is coded but not yet exercised on a real file.
5. Speaker notes are extracted where present, but many decks have none. Do not
   treat absence of notes as absence of content.

## DELIBERATELY NOT DONE

Per the Source-First Rule (`MASTER_INSTRUCTIONS.md` §3), the following were
**left empty rather than filled from general knowledge**: Concept Library,
Formula Library, Ortberg Heuristics, Case Library, Glossary, all databases, all
frameworks, all career/resume/interview material, and the playbook.

Populating those from model priors instead of Professor Ortberg's material would
defeat the entire purpose of the project and would silently corrupt the source
of truth for later interview preparation.
