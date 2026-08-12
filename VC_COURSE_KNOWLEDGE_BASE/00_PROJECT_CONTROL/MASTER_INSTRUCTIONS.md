# MASTER INSTRUCTIONS — VC / PE / M&A / New Venture Financing Knowledge Extraction

**Owner:** Seth Kardys (skardys13@gmail.com)
**Status of this file:** Authoritative. Read this completely before doing any work on the project.
**Version:** 1.0 — established 2026-08-12

---

## 0. IF YOU ARE A NEW SESSION, READ IN THIS ORDER

1. `00_PROJECT_CONTROL/MASTER_INSTRUCTIONS.md` (this file)
2. `00_PROJECT_CONTROL/EXTRACTION_STATUS.md`
3. `00_PROJECT_CONTROL/NEXT_SESSION_HANDOFF.md`
4. `00_PROJECT_CONTROL/FILE_MANIFEST.md`
5. `00_PROJECT_CONTROL/PROCESS_LOG.md`

Then open **only** the master knowledge files needed for the next task.
Resume from the `NEXT ACTION` line in the handoff. **Do not restart the project.
Do not redo completed sources. Do not re-read every raw source.**

---

## 1. WHAT THIS PROJECT IS

Seth graduated from Iowa State University with a Finance degree. In his final
semester he took two courses taught by **Gudmundur "Good" Ortberg**:

- **Course 1 — Venture Capital, Private Equity, and Mergers & Acquisitions**
- **Course 2 — New Venture Financing**

This project takes the slide decks and other course documents from those two
courses and turns them into a permanent, organized, searchable professional
knowledge system.

**This project is NOT** "summarize my old college PowerPoints."

**It IS:** recover everything useful from two finance/venture courses and
transform it into a permanent professional knowledge system that supports a
career move toward venture capital.

### The six-stage order of operations

```
1. PRESERVE    capture what the course actually taught
2. ORGANIZE    turn scattered decks into structured information
3. CONNECT     link concepts, companies, deals, formulas, cases
4. SYNTHESIZE  build frameworks and higher-level understanding
5. MASTER      convert into study material and investment judgment
6. APPLY       translate into portfolio projects, interviews, resume, career
```

Do not jump to stage 5 or 6 before stages 1–4 are substantially done on the
material that exists.

### Priority order when things conflict

```
Accuracy → Completeness → Source Traceability → Organization
        → Understanding → Practical Application → Career Value
```

---

## 2. CAREER CONTEXT (drives the "APPLY" stage)

- Started at **Retirement Income Strategies (RIS)** around late July 2026.
- Plans roughly **1–1.5 years** there to build professional, client-facing,
  communication, leadership, and relationship-management experience.
- Target destinations: **Venture Capital, Corporate VC, startup investing,
  growth investing, private markets, startup finance, corporate development**,
  possibly a startup operating role as a stepping stone, possibly
  entrepreneurship.
- Has considered relocating to the **Tampa, Florida** area.

The project serves two purposes simultaneously:

- **Purpose A — Preserve the education.** A permanent organized knowledge base.
- **Purpose B — Help the career.** Surface the knowledge, frameworks,
  terminology, examples, and analytical skills that support breaking into VC or
  an adjacent field.

---

## 3. THE SOURCE-FIRST RULE (most-violated rule — read twice)

**The course materials are the primary source.**

Never silently replace what Professor Ortberg taught with generic internet
knowledge or model priors.

Preserve: terminology, definitions, frameworks, opinions, examples,
explanations, analogies, company examples, investment examples, deal examples,
warnings, heuristics, formulas, practical advice, career advice, case examples,
slide notes, charts, diagrams, tables, and financial examples.

If something sounds unusual or non-standard, **preserve it rather than
"correcting" it.** You may separately flag it as potentially outdated,
incomplete, or debatable — but the flag goes in its own labeled block.

### Mandatory labeling taxonomy

Every non-trivial claim in a derived file carries one of these labels:

| Label | Meaning |
|---|---|
| `SOURCE FACT` | Directly supported by course material. Cite source ID + slide/page. |
| `PROFESSOR / COURSE VIEW` | A principle, opinion, heuristic, or framework the material represents. |
| `CLAUDE INFERENCE` | A reasonable conclusion drawn across multiple materials. Must say which. |
| `EXTERNAL CONTEXT` | Information from outside the course. Must be visibly separated. |

**Never present an inference as something Professor Ortberg explicitly taught.**
**Never fabricate quotations.** If exact wording or attribution is uncertain,
mark it as uncertain.

### Uncertainty markers — use them, don't guess

`[UNCLEAR]` · `[NOT PROVIDED]` · `[TEXT NOT LEGIBLE]` · `[INTERPRETATION UNCERTAIN]`

Preserving uncertainty beats introducing false information. Never invent a
missing number, company name, date, or attribution.

### Outdated material

Some examples will concern older companies, markets, or transactions. **Do not
update the numbers.** Preserve what was taught. Where genuinely useful,
distinguish `COURSE DATA` from `CURRENT DATA` in separate blocks. Only research
outside data when it is specifically useful or requested.

---

## 4. ORIGINALS ARE READ-ONLY

Never modify, overwrite, reformat, rename in place, or delete any original
course file: PowerPoints, PDFs, assignments, notes, spreadsheets, cases,
readings. Everything in `03_SOURCE_DOCUMENTS/` is immutable.

All work product goes into derived directories.

---

## 5. DIRECTORY STRUCTURE

```
VC_COURSE_KNOWLEDGE_BASE/
  00_PROJECT_CONTROL/        MASTER_INSTRUCTIONS.md, PROCESS_LOG.md,
                             FILE_MANIFEST.md, EXTRACTION_STATUS.md,
                             NEXT_SESSION_HANDOFF.md, tools/
  01_PRESENTATION_EXTRACTIONS/  raw machine extractions of decks (+ _extracted_images/)
  02_PRESENTATION_NOTES/     structured interpreted notes per deck
  03_SOURCE_DOCUMENTS/       ORIGINAL MATERIALS — READ ONLY
  04_DOCUMENT_NOTES/         raw extractions + notes for non-deck sources
  05_MASTER_KNOWLEDGE/       Master_Course_Notes, Concept_Library,
                             Professor_Ortberg_Heuristics, Formula_Library,
                             Case_Library, VC_PE_MA_GLOSSARY
  06_DATABASES/              Companies_and_Deals, Investors_and_Firms,
                             People, Source_Index (CSV)
  07_FRAMEWORKS/             VC_Investment_Framework, Startup_Financing_Framework,
                             Deal_Lifecycle, Fund_Economics_Framework,
                             Due_Diligence_Framework, Investment_Memo_Template
  08_CAREER/                 VC_Career_Translation, Career_Gap_Analysis,
                             Resume_Material, LinkedIn_Material, Interview_Prep,
                             Portfolio_Project_Plan
  09_STUDY/                  VC_Cheat_Sheet, Flashcards, Technical_Questions,
                             Calculation_Practice, Practice_Cases
  10_FINAL/                  Complete_Course_Knowledge_Base, Seth_VC_Playbook
```

Change this structure only for a strong practical reason, and log the reason.

---

## 6. SOURCE ID SCHEME

Every source file gets a stable ID, assigned in `FILE_MANIFEST.md`.
**Never rely on filenames alone** — they are inconsistent and can be renamed.

| Prefix | Meaning |
|---|---|
| `SRC-P-###` | Presentation / slide deck |
| `SRC-C-###` | Case study |
| `SRC-A-###` | Assignment |
| `SRC-S-###` | Spreadsheet / model |
| `SRC-R-###` | Reading / article / handout |
| `SRC-N-###` | Class notes |
| `SRC-D-###` | Other document (generic) |

Numbering for presentations should follow **reconstructed course order**, not
alphabetical filename order. The extraction tool assigns provisional IDs; the
manifest holds the final, authoritative ID.

Once an ID is published into a derived file, **it never changes.**

---

## 7. THE PROCESSING PIPELINE (token discipline)

```
Raw source file
   ↓  (tools/extract_source.py — mechanical, verbatim)
Raw extraction            01_PRESENTATION_EXTRACTIONS/ or 04_DOCUMENT_NOTES/
   ↓  (Claude reads + interprets)
Structured notes          02_PRESENTATION_NOTES/ or 04_DOCUMENT_NOTES/
   ↓  (entities, numbers, formulas, concepts)
Master files + databases  05_MASTER_KNOWLEDGE/, 06_DATABASES/
   ↓  (cross-source synthesis)
Frameworks                07_FRAMEWORKS/
   ↓
Career + study + final    08_CAREER/, 09_STUDY/, 10_FINAL/
```

**Use the master files as working memory.** Do not re-read completed raw
extractions to answer a later question — read the master files, and return to a
raw source only to verify a specific fact. This is what keeps the project
affordable across many sessions.

---

## 8. PRESENTATION PROCESSING PROCEDURE

For each deck:

1. **Register** in `FILE_MANIFEST.md` (ID, filename, type, course, topic).
2. **Inspect** — course, topic, apparent position in sequence, slide count,
   relationship to other materials.
3. **Extract** — run the tool; then read the raw extraction. Examine text,
   tables, charts, diagrams, screenshots, footnotes, financial examples, and
   speaker notes. Any exported image flagged `[IMAGE NOT YET INTERPRETED]`
   must be viewed before the notes are considered done.
4. **Structured notes** → `02_PRESENTATION_NOTES/`, using the section template
   in §9.
5. **Entities** — companies, investors/firms, founders, executives, other people.
6. **Transactions** — investments, rounds, acquisitions, mergers, exits, IPOs.
7. **Quantitative** — valuations, multiples, ownership, dilution, metrics,
   returns, investment amounts, fund sizes, financing terms.
8. **Concepts** — definitions, frameworks, methodologies, analytical processes.
9. **Formulas** — update `Formula_Library.md`.
10. **Heuristics** — update `Professor_Ortberg_Heuristics.md`.
11. **Career relevance** — record professional applications.
12. **Cross-reference** — connect to previously processed materials.
13. **Master update** — update the relevant `05_MASTER_KNOWLEDGE/` and
    `06_DATABASES/` files.
14. **Log** — append to `PROCESS_LOG.md`.
15. **Status** — update `EXTRACTION_STATUS.md`.
16. **Continue** to the next source. **Do not ask permission between sources.**

### Non-presentation documents

Same spine, but **identify what the document actually is first** and treat it
accordingly:

- A **case** → analyze with the case template (§11).
- A **spreadsheet** → analyze as a model (§10).
- An **assignment** → it reveals what analytical skills the professor expected
  students to demonstrate. That is career-translation evidence.
- A **reading/article** → outside context for something in the slides.

---

## 9. STRUCTURED NOTE TEMPLATE (per source)

Include each section **when applicable** — omit rather than pad.

```
Presentation Overview        what it primarily teaches
Major Concepts               concepts and definitions
Frameworks                   any framework/process/methodology/checklist/decision tree
Companies Mentioned          company · industry · why mentioned · lesson · financing context
Investors / Funds Mentioned  VC, PE, angels, institutions, corporates, accelerators, banks, acquirers
People Mentioned             founders, investors, executives, bankers, entrepreneurs — and why they matter
Deals / Transactions         acquisitions, mergers, rounds, PE deals, exits, IPOs, recaps, restructurings
Numbers                      valuations, amounts, ownership, multiples, revenue, margins, growth,
                             dilution, returns, fund sizes, cap-table figures, terms, exits, IRR, MOIC
Formulas / Calculations      every useful formula or quantitative process
Professor Frameworks         rules, principles, warnings, practical teachings
Cases / Real-World Examples  preserved because they become interview material
Career Insights              anything about breaking into VC, evaluating companies/founders/deals
Key Takeaways                the most important lessons
```

### Slide-by-slide extraction

For important decks, keep enough granularity that nothing is lost to
summarization:

```
Slide N — <title>
  Topic:
  Important Content:
  Companies/Firms Mentioned:
  Numbers:
  Interpretation:
```

Use judgment — a decorative title slide does not need a paragraph. The goal is
**information preservation, not verbosity.**

### Preserve examples, not just definitions

Wrong: "Post-money valuation is the valuation after an investment."

Right: the definition **plus** the actual course example — the initial
valuation, the investment, the resulting valuation, the ownership percentage,
and the resulting dilution. The examples are often more useful in interviews
than the definitions.

---

## 10. SPREADSHEET PROCESSING

Do not treat a model like a document. Inspect sheets, formulas, assumptions,
inputs, outputs, methodology, statements, cap tables, ownership calcs, returns,
sensitivities, and charts. Then write up:

1. Purpose 2. Inputs 3. Calculations 4. Outputs 5. Financial logic
6. Course concept demonstrated 7. Practical application

The extraction tool captures both cached values and underlying formulas — the
**formulas are the teaching content.** Never overwrite the original workbook.

---

## 11. CASE PROCESSING TEMPLATE

```
Situation · Company · Decision · Financial Information · Strategic Considerations
· Investment / Deal Considerations · Risks · Course Concepts · Outcome (if given)
· Lessons · Interview Use
```

---

## 12. CROSS-REFERENCING (do not treat sources as isolated universes)

Materials overlap. A deck may introduce a company, another deck may explain its
financing, a case may hold the transaction detail, an assignment may require
its analysis, and a spreadsheet may hold the valuation. **Connect them.**

```
COMPANY X
  Sources: SRC-P-004 (slide 11), SRC-P-007 (slides 3–6), SRC-C-002, SRC-A-003
  Consolidated: what those sources collectively teach
```

### Duplicate management

When the same concept recurs: preserve genuinely new information, merge
overlapping explanations, record every source that covered it, prefer the most
complete explanation, **preserve contradictions rather than silently picking a
winner**, and append new examples to the existing entry. Do not fill the
knowledge base with repeated explanations.

---

## 13. SOURCE TRACEABILITY

Every major piece of extracted knowledge must be traceable:

```
Post-Money Valuation
  Definition: ...
  Sources: SRC-P-004 Slide 11 · SRC-P-009 Slide 6 · SRC-A-002
```

Preserve the specific slide/page number whenever possible. This matters most
later, when building interview material — a claim you cannot trace is a claim
you cannot safely make in an interview.

---

## 14. DERIVED KNOWLEDGE ASSETS

Build these **from the material**, never from a generic template:

- **Master Course Map** — the real structure of both courses (provisional
  category lists in the original brief are hypotheses, not answers).
- **Concept Library** — per concept: definition · how the course explains it ·
  formula · course example · where it appeared · practical VC application ·
  related concepts. *Only include a concept if the material supports it.*
- **Company / Deal Database**, **Investor / Firm Database**, **People Database**
  — CSVs in `06_DATABASES/`. Use `Not provided` for missing values; never invent.
- **Formula / Model Library** — per formula: formula · variables · meaning ·
  course example · when used · source. *Only claim it was taught if it appears.*
- **Good Ortberg Rules / Heuristics** — memorable principles reasonably
  attributable to the course. Do not fabricate quotes. Do not attribute a
  generic slide statement to him personally unless the material supports it.
- **Frameworks** — VC investment, startup financing lifecycle, deal lifecycle,
  fund economics, due diligence, investment memo template.
- **Glossary** — `VC_PE_MA_GLOSSARY.md`, term · definition · course explanation
  · example · related terms · source.
- **Timeline** — only if the material actually supports one.

### Concept relationships matter more than isolated definitions

Build chains wherever the course supports them, e.g.:

```
valuation → ownership → dilution → exit value → investor return
fund size → check size → required ownership → portfolio construction → required exits
burn rate → runway → fundraising timing → dilution → negotiating leverage
```

### Two-layer summaries

For each major topic produce both:

- **ACADEMIC UNDERSTANDING** — what the course teaches.
- **PRACTICAL INVESTOR UNDERSTANDING** — what actually needs to be remembered
  when evaluating a company or discussing the concept professionally.

### Knowledge levels

Tag important material: **L1 MUST KNOW** (instant recall) · **L2 SHOULD KNOW** ·
**L3 ADVANCED** · **L4 REFERENCE**.

### Turn knowledge into judgment

For major concepts, work through: Why does this matter? When does it matter?
What can go wrong? What would an investor look for? What would a founder care
about? What changes the decision? What creates upside/downside? What would make
me pass? What further information would I request?

---

## 15. CAREER TRANSLATION RULES

- Claim a skill **only if the coursework supports it**, and record the evidence.
- Distinguish **"Analyzed…"** from **"Invested…"**. Seth was a student, not a
  professional investor. Never imply he professionally executed investments.
- LinkedIn/resume material should read as legitimate **academic preparation**
  for the target career — not fabricated professional VC experience.
- Gap analysis must be honest: coursework alone does not qualify someone for a
  VC role. Name the real gaps (transaction experience, sourcing, networking,
  modeling reps, operating experience, sector depth, memo writing, portfolio
  work, IC exposure, founder relationships).
- Connect RIS experience only where the connection is genuine (client
  communication, relationship management, financial analysis, presenting
  financial information, professional judgment, business development). **Do not
  force weak connections.**

Target narrative:

```
Finance education → VC/PE/M&A + venture financing coursework
→ professional client-facing finance experience (RIS)
→ independent VC skill development + portfolio work
→ transition toward VC or an adjacent stepping-stone role
```

---

## 16. DO NOT FINALIZE TOO EARLY

Keep these **provisional** until the material is substantially processed:
the VC investment framework, Ortberg's major rules, Seth's strongest course
skills, resume bullets, career gaps, interview stories, and the personal VC
playbook. Maintain working versions; refine as evidence accumulates. Mark
version numbers (`v0.3`, `v0.4`) so a reader knows maturity.

---

## 17. WHAT NOT TO DO

- Produce shallow summaries or merely rewrite slide bullets
- Ignore examples, charts, tables, diagrams, footnotes, or company examples
- Fabricate missing content or quotations
- Pretend Seth professionally executed investments
- Erase course-specific viewpoints
- Silently replace course knowledge with internet knowledge
- Process files without tracking them
- Repeatedly ask "should I continue?"
- Make Seth manually organize every file
- Dump everything into one enormous unstructured document
- Lose source traceability
- Restart the methodology between conversations
- Waste context re-reading completed sources
- Modify original source files

---

## 18. AUTONOMY

Once files are available: organize working copies, create folders, classify
decks, extract, analyze, cross-reference, consolidate, update databases and
knowledge files, detect duplicates, identify missing pieces, build frameworks,
and maintain tracking files — **without asking permission for each step.**

Continue autonomously until blocked by an actual technical limitation, a
missing source, or a usage/context constraint. If one file cannot be processed,
state the specific limitation, flag that source as unresolved in the manifest,
and **keep going with the others.**

---

## 19. END-OF-SESSION REQUIREMENT (non-negotiable)

Before any session ends — especially if stopped by context or usage limits —
ensure these are current:

1. `MASTER_INSTRUCTIONS.md`
2. `FILE_MANIFEST.md`
3. `PROCESS_LOG.md`
4. `EXTRACTION_STATUS.md`
5. `Master_Course_Notes.md`
6. `NEXT_SESSION_HANDOFF.md`

The **files**, not the chat, are the state of the project. Commit and push them.

---

## 20. FINAL DELIVERABLES (28)

Complete Course Knowledge Base · VC Master Notes · New Venture Financing Master
Notes · VC/PE/M&A Master Notes · Company & Deal Database · Investor & Firm
Database · People Database · Formula & Modeling Library · Good Ortberg Rules &
Heuristics · Case Study Library · VC Investment Framework · Startup Financing
Framework · Deal Lifecycle Framework · Fund Economics Framework · Due-Diligence
Framework · Investment Memo Template · VC Career Translation · Career Gap
Analysis · VC Resume Material · LinkedIn Material · VC Interview Preparation ·
VC Technical Interview Questions · VC Cheat Sheet · VC Flashcards · Calculation
Practice · Practice Investment Cases · Portfolio Project Plan · Seth's Venture
Capital Playbook

The end goal is not knowing what was on the slides. It is being able to
understand venture capital, analyze startups, understand venture financing and
private-market transactions, discuss investments intelligently, perform the
relevant calculations, evaluate deals, build investment work products, prepare
for VC interviews, and use this education as part of a realistic path into
venture capital.
