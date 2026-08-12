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

## CURRENT STATE

**BLOCKED — awaiting source material.**

The project scaffold, methodology, tracking system, database schemas, and a
tested extraction pipeline are all in place. **Zero course files have been
delivered**, so no course knowledge exists in this repository yet.

Locations checked on 2026-08-12, all empty of course material:

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

1. **No source material delivered.** Everything downstream is blocked on this.
2. Course order for the decks is unknown until filenames/content are seen; the
   manifest's `Order` column stays empty until then.
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
