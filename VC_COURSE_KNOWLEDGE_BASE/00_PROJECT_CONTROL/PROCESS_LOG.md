# PROCESS LOG

Append-only. One entry per working session. Never rewrite history — correct
forward with a new entry.

---

## Session 1 — 2026-08-12

**Source IDs processed:** none (none available)

### Actions completed

1. Read the full master brief and established the project methodology.
2. Searched for source material in every reachable location:
   - repo `/home/user/first-pr-practice` — only an unrelated `wordcount.py` practice project
   - `/mnt/attach` (session attachments) — empty
   - `/mnt/user-data` — empty
   - filesystem-wide sweep for `.pptx/.ppt/.pdf/.docx/.xlsx/.key` — nothing course-related
   - Google Drive, five separate queries (`Ortberg`; titles containing "Venture";
     titles containing "Private Equity"/"Cap Table"/"Finance"; all Slides +
     PowerPoint MIME types; full-text `term sheet`/`pre-money`/`liquidation
     preference`) — **no course material.** The only near-misses were Series 65
     exam-prep files and one unrelated ISU marketing deck.
3. Created the directory structure from `MASTER_INSTRUCTIONS.md` §5.
4. Wrote `MASTER_INSTRUCTIONS.md` — the complete methodology in self-contained
   form, so the project survives loss of the chat thread.
5. Created `FILE_MANIFEST.md`, `EXTRACTION_STATUS.md`, `NEXT_SESSION_HANDOFF.md`,
   and this log.
6. Created the four database CSVs with headers and a documented schema.
7. Created master-knowledge and framework stubs, each explicitly marked as
   awaiting source material.
8. Built `00_PROJECT_CONTROL/tools/extract_source.py`.
9. Verified the toolchain rather than assuming it:
   - Confirmed `python-pptx`, `pdfplumber`, `openpyxl`, `python-docx` all import
     (required repairing a broken `cffi`/`cryptography` binding first).
   - Confirmed LibreOffice is present for legacy `.ppt`/`.doc`/`.xls` conversion.
   - Confirmed `tesseract` is **absent** → no OCR for scanned PDFs.
   - Built synthetic .pptx/.docx/.xlsx fixtures resembling course material and
     ran the harness end-to-end. It correctly recovered slide text, bullet
     nesting, speaker notes, a cap-table table, chart series values
     (`MOIC: [3.2, 2.1]`), Word headings and tables, and spreadsheet **formulas**
     (`=B1+B2`, `=B2/B3`) alongside values.
   - Deleted all fixtures and their outputs afterward.

### Outputs created

`MASTER_INSTRUCTIONS.md` · `FILE_MANIFEST.md` · `EXTRACTION_STATUS.md` ·
`NEXT_SESSION_HANDOFF.md` · `PROCESS_LOG.md` · `tools/extract_source.py` ·
4 database CSVs · master-knowledge and framework stubs · `README.md` ·
`03_SOURCE_DOCUMENTS/README_HOW_TO_ADD_SOURCES.md`

### Issues encountered

- **Blocking:** no course material available anywhere in the environment. The
  brief said "I will provide the slide presentations"; they had not been
  delivered when this session ran.
- `pdfplumber` initially failed on a broken system `cryptography` binding
  (`ModuleNotFoundError: _cffi_backend`); fixed by upgrading `cffi`.
- No OCR engine available for scanned PDFs.

### Judgment calls

- **Did not populate any knowledge file from general VC knowledge.** Filling
  the Concept Library, Formula Library, Ortberg Heuristics, frameworks, or
  interview material from model priors would have produced something that
  *looks* like progress while silently violating the Source-First Rule and
  corrupting the source of truth for later interview prep. Empty stubs with
  explicit "awaiting source" markers are the honest state.
- **Built the extraction harness anyway.** It is the one piece of real work that
  does not depend on the sources existing, and it removes the slowest step from
  the first real processing session.

### Remaining tasks

Everything downstream of ingestion. See `NEXT_SESSION_HANDOFF.md` → NEXT ACTION.
