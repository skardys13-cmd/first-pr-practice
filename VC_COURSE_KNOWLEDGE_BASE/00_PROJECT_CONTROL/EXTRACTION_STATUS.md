# EXTRACTION STATUS

**Last updated:** 2026-08-12
**Master knowledge version:** v0.3 (7 decks fully extracted)

---

## PROJECT STATUS

```
Presentations discovered:     14   (Google Drive)
Presentations FULLY done:      7   (SRC-P-001, 005, 006, 007, 008, 009, 010)
Partial only (snippets):       4   (SRC-P-011, 012, 013, 014)
Unresolved (zero content):     3   (SRC-P-002, 003, 004)

Other documents discovered:    0
Other documents processed:     0
Other documents remaining:     0
```

## DELIVERY METHOD — SUPERSEDED, NOW GOOGLE DRIVE

Original plan was pasted text. **Superseded 2026-08-12:** Seth put 14 decks in a
Drive folder, "Lecture notes venture capital". The paste path still works and
remains supported for anything not in Drive.

## CURRENT STATE

**UNBLOCKED — Drive read access granted 2026-08-12. Extraction in progress.**

Six decks fully extracted with structured notes. Five remain (partial snippets
only). Three return zero content and are permanently unresolvable by this route.

### SRC-P-002 / 003 / 004 — CONFIRMED UNRESOLVABLE

Re-tested **with full access granted**: all three return an empty
`fileContent`. This is **not** a permissions problem — those decks contain no
extractable text at all. At 65-92 MB each they are almost certainly slides built
as images, or embedded video/recorded lectures.

They cannot be recovered through the connector. Options, in order of practicality:
1. Ask Seth what those three decks are (they may be recorded lectures rather
   than slide content).
2. Export them to PDF and re-upload — only helps if the text is real text.
3. Screenshot key slides for visual reading.

Binary download remains off the table: base64 of a 92 MB file is millions of
tokens.

## PRIOR BLOCK (resolved)

All 14 decks are identified with their Drive file IDs (see `FILE_MANIFEST.md`).
Neither retrieval route is currently open:

| Route | Status |
|---|---|
| Connector text extraction (`read_file_content`) | **Permission not granted.** Three attempts, all "MCP tool call requires approval". This is the intended route and remains the blocker. |
| Connector search snippets (`search_files`) | **WORKS — currently the only content channel.** Returns ~5,000 chars per file. Delivered 11 of 14 decks. Set `excludeContentSnippets: false`; the response overflows the tool limit and lands on disk, so parse it there. |
| Connector binary download (`download_file_content`) | **Not viable regardless of permission.** Returns base64 into the model's context; a 92 MB deck is millions of tokens. Never use this for these files. |
| Direct HTTPS download in the shell | No Drive credentials in the environment. Would work only if the folder were link-shared. |

Disk is not a constraint — 30 GB free against ~340 MB of decks.

### Unblocking

Approve the Drive connector's file-read permission (choose the always-allow
option so all 14 decks process without re-prompting per file). Then proceed to
the NEXT ACTION in `NEXT_SESSION_HANDOFF.md`.

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

1. **Drive read permission not granted.** Everything downstream waits on this.
2. **Course attribution unknown.** The folder is named for venture capital, but
   Seth took two courses. Some of these 14 decks may belong to New Venture
   Financing. Determine per deck from content — do not assume the folder name
   settles it, and do not assume all 14 are one course.
3. **Deck order unverified.** Filenames are bare numbers `1.pptx`–`14.pptx`.
   That probably reflects lecture order, but it is an assumption; confirm from
   content and re-sort the manifest if wrong.
4. **Decks 2, 3, 4 are 65–92 MB** — heavy embedded media. Their text extraction
   will likely understate what the lecture actually covered. Flag visuals as
   `[VISUAL NOT CAPTURED]` rather than guessing.
5. No syllabus in the folder. One would settle ordering and course attribution
   in a single step — worth asking for.
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
