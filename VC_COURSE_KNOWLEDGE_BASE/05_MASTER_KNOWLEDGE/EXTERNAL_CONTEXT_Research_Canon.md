# EXTERNAL CONTEXT — Research Canon & Gap-Filling Layer

> # ⚠ THIS FILE IS NOT COURSE MATERIAL
>
> Everything here is `EXTERNAL CONTEXT` under `MASTER_INSTRUCTIONS.md` §3. **None
> of it came from Todd Ortberg or FIN/ENTRP 4350/4310.** It must never be cited
> as something the course taught, and must never be merged into
> `Concept_Library.md`, `Formula_Library.md`, `Case_Library.md`, or
> `Professor_Ortberg_Heuristics.md`.
>
> **Why the separation is non-negotiable:** the entire value of this project in
> an interview is that Seth can say "in my venture capital coursework we analyzed
> X" and have it be *true*. A claim that silently blends outside reading into
> course material is a claim he cannot defend when someone asks a follow-up.
> Keep the layers apart and both stay usable.

**Version:** v0.1 — first research pass, 2026-08-12
**Purpose:** fill the gaps the course material genuinely leaves open, and build
depth beyond what a single semester could cover.

---

## 1. WHERE THE REAL GAPS ARE

Established by auditing the 11 fully-extracted decks. These are ranked by how
much they matter for Seth's stated VC/CVC target.

| # | Gap | Status in course material | Priority |
|---|---|---|---|
| **1** | **New Venture Financing (4310) as a whole** | One deck (`SRC-P-006`, Corporate VC) out of 14. Seed-stage financing, bootstrapping, friends & family, angel rounds, burn/runway, unit economics, financial forecasting, and pitching are **almost entirely absent**. | **Critical** |
| **2** | **Fund economics from the LP side** | Course covers 2-and-20, carry, and hurdle rates well from the GP view. Fund construction, reserve strategy, recycling, J-curve, DPI/TVPI/RVPI, and how LPs actually diligence a GP are **not covered**. | **High** |
| **3** | **Portfolio construction math** | The power law is implied (`SRC-P-010`: ~75% of VC deals don't return capital) but never formalized into ownership targets, check sizing, or shots-on-goal. | **High** |
| **4** | **Early-stage metrics** | CAC, LTV, payback, cohort retention, net revenue retention, magic number. Rule of 40 appears (`SRC-P-007/009`) but the underlying SaaS metric stack does not. | **High** |
| **5** | **Sourcing and founder evaluation** | `SRC-P-011` covers PE sourcing excellently. **VC** sourcing and how VCs actually judge founders is thin. | **Medium** |
| **6** | **Decks 2, 3, 4** | Unretrieved — connector size ceiling, not missing content. Content unknown; may cover some of the above. | **Blocking unknown** |

**Rule for this file:** fill gaps with the best available evidence, cite it, and
never let it drift into the course layer.

---

## 2. THE ACADEMIC CANON

These are the papers that actually underpin what practitioners assert. Where the
course states something as a rule of thumb, the paper is usually the reason.

### Returns and performance measurement

- **Kaplan, S. & Schoar, A. (2005), "Private Equity Performance: Returns,
  Persistence, and Capital Flows," *Journal of Finance*.** The foundational
  performance-persistence study. Establishes that, unlike public managers, PE/VC
  GP performance *persists* across funds — which is the empirical justification
  for the entire top-quartile-manager-selection industry.
  **Connects to:** `SRC-P-001`'s "top quartile firms" claim and `SRC-P-012`'s
  "K-shaped recovery" — this is the paper underneath both.

- **Korteweg, A. & Nagel, S. (2016), "Risk-Adjusting the Returns to Venture
  Capital," *Journal of Finance*.** Shows that naive VC return figures overstate
  performance once systematic risk is properly priced. Directly relevant to any
  claim that "VC returns beat the S&P."
  **Connects to:** `SRC-P-001`'s CAGR comparison and `SRC-P-013`'s alpha material.
  *(Also: NBER WP 19347.)*

- **Korteweg, A. & Sorensen, M. (2010), "Risk and Return Characteristics of
  Venture Capital-Backed Entrepreneurial Companies," *Review of Financial
  Studies*.** Company-level rather than fund-level risk/return.

- **Gompers, P. & Lerner, J. (1997), "Risk and Reward in Private Equity
  Investments: The Challenge of Performance Assessment."** Why measuring private
  returns is genuinely hard — stale marks, selection bias, IRR manipulability.
  **This is the paper to know when someone asks why you distrust a reported IRR.**

### The power law

The distribution of VC outcomes is extremely right-skewed: a high density of
total losses and a heavy right tail where a small number of outliers drive
aggregate fund performance. This breaks the Gaussian assumptions in classical
portfolio theory, with direct consequences for portfolio construction,
diversification, and performance evaluation.

**Connects to:** `SRC-P-010`'s "~75% of VC deals do NOT return the investment"
and `SRC-P-007`'s Sevin Rosen Fund I (one $25M fund holding both Compaq and
Lotus, returning ~$191M gross). **The course gives the anecdote; this literature
gives the structure.**

### Still to read — flagged, not yet done
- **Gompers, Gornall, Kaplan & Strebulaev, "How Do Venture Capitalists Make
  Decisions?"** — the large-scale survey of actual VC practice (deal sourcing,
  selection criteria, valuation methods, post-investment involvement). **This is
  the single highest-value paper for gap #5 and should be the next thing read
  in full.** The searches above surfaced returns literature rather than this
  paper; it needs a direct retrieval.
- Gornall & Strebulaev on **unicorn valuation** — demonstrates that headline
  post-money valuations systematically overstate true company value because they
  ignore preference stacks. **Directly extends `SRC-P-005`'s liquidation
  preference material and is a genuinely impressive thing to raise in an
  interview.**
- Ewens & Farre-Mensa on the changing supply of late-stage private capital.
- Metrick & Yasuda, *Venture Capital and the Finance of Innovation* — the
  standard graduate textbook; the rigorous treatment of fund economics that
  fills gap #2.

---

## 3. THE PRACTITIONER CANON

### Tier 1 — read completely

- **Brad Feld & Jason Mendelson, *Venture Deals: Be Smarter Than Your Lawyer and
  Venture Capitalist*.** The definitive term-sheet book: economics vs control,
  liquidation preferences, participation, anti-dilution, protective provisions,
  drag-along, option pools.
  **Relationship to the course:** this is the deepest single overlap with
  `SRC-P-005`, and the right way to extend it. The course teaches the mechanics;
  Feld teaches which terms actually matter and which are noise. **The
  distinction between *economics* terms and *control* terms is the organizing
  idea the course material does not explicitly name.**

- **Scott Kupor, *Secrets of Sand Hill Road*.** Written by a16z's managing
  partner. Explains the LP/GP relationship, why VCs behave as they do, and the
  internal mechanics of firm decision-making.
  **Fills gap #2 directly** — this is the best accessible source on the fund-side
  economics the course covers only from the GP fee perspective.

- **Sebastian Mallaby, *The Power Law: Venture Capital and the Making of the New
  Future*.** History of the industry with unusual access to Sequoia, Kleiner
  Perkins, Accel, Benchmark, and a16z.
  **Fills gap #3 conceptually** and supplies the historical narrative that makes
  the Compaq/Sevin Rosen case (`SRC-P-007`) part of a larger pattern.

### Tier 2
- **Jeff Bussgang, *Mastering the VC Game*** — the founder-side view of raising.
- **Metrick & Yasuda** (above) — the quantitative counterpart to Feld.

### On using these honestly
Reading a book is **not** coursework and must never be described as such. The
legitimate framing on a resume or in an interview is a **skill or a view**, not a
credential: "I've built on the coursework by working through *Venture Deals* and
*Secrets of Sand Hill Road*" is true and creditable. "I studied VC deal terms" is
also true. Implying the course covered something it didn't is the failure mode
this entire file exists to prevent.

---

## 4. THE 4310 GAP — what a New Venture Financing course covers

`CLAUDE INFERENCE` — reconstructed from the standard scope of such a course, to
be **replaced** with real material if Seth locates the 4310 decks.

The financing lifecycle the missing course would have covered:

```
Founder savings / bootstrapping / revenue
    → Friends & family
    → Grants and non-dilutive capital       ← SRC-P-006 touches this ($1M grant, Parkiva)
    → Angels / angel syndicates
    → Accelerators (YC, Techstars)
    → Pre-seed / Seed (SAFEs, convertible notes)   ← SRC-P-005 covers instruments
    → Series A (first priced institutional round)  ← SRC-P-005/007 cover mechanics
    → Series B/C/growth
    → Exit                                          ← SRC-P-001/007 cover well
```

**What the surviving decks already cover well:** the instruments (`SRC-P-005`),
priced-round mechanics and dilution (`SRC-P-005`), the pitch deck
(`SRC-P-006`), CVC (`SRC-P-006`), and exits (`SRC-P-001`, `SRC-P-007`).

**What is genuinely missing and needs external filling:**
1. **Burn rate, runway, and the fundraising cycle** — how long a round should
   last, when to start raising, why 18–24 months of runway is the standard target
2. **Unit economics** — CAC, LTV, LTV/CAC ratios, CAC payback period, contribution
   margin, cohort retention, net revenue retention
3. **Startup financial forecasting** — bottom-up vs top-down models, driver-based
   forecasting, hiring plans as the dominant cost line
4. **Angel investing and syndicates** — how angels differ from institutional VC in
   diligence, check size, and expectations
5. **Accelerators** — standard terms, the YC SAFE, demo day dynamics
6. **Founder equity** — splits, vesting cliffs, the option pool shuffle
   (`SRC-P-005` covers vesting but not the pool-shuffle negotiation)

**Note the tension worth preserving:** `SRC-P-007` states that **DCF is not used**
in venture because there are no cash flows, and `SRC-P-013` gives the **Venture
Capital Method** as the replacement. Most outside sources treat forecasting as
central to early-stage finance. These are reconcilable — the forecast drives
*operating* decisions and the ask; the VC Method drives *pricing* — but the
course's position is the sharper one and should be preserved as taught.

---

## 5. RESEARCH LOG

| Date | Query | Outcome |
|---|---|---|
| 2026-08-12 | VC returns / power law academic literature | Located Kaplan-Schoar, Korteweg-Nagel, Korteweg-Sorensen, Gompers-Lerner. Recorded above. |
| 2026-08-12 | Practitioner book canon | Confirmed Feld, Kupor, Mallaby as the consensus core; Bussgang secondary. |

### Next research actions, in priority order
1. **Retrieve Gompers/Gornall/Kaplan/Strebulaev, "How Do Venture Capitalists Make
   Decisions?" in full** — highest value for founder evaluation and sourcing.
2. **Gornall & Strebulaev on unicorn valuations** — extends the liquidation
   preference material with a genuinely non-obvious result.
3. **NVCA / PitchBook current benchmarks** — the course names both as the
   standard source for round-by-round comparables (`SRC-P-007`); pull actual
   current medians so the coursework examples can be marked
   `COURSE DATA` vs `CURRENT DATA` per §45.
4. **SaaS metrics canon** (Bessemer's cloud benchmarks, a16z metrics posts) for
   gap #4.
5. **Fund construction math** — ownership targets, reserve ratios, portfolio size.

## Sources consulted

- [Risk-Adjusting the Returns to Venture Capital (Korteweg & Nagel), Journal of Finance](https://onlinelibrary.wiley.com/doi/10.1111/jofi.12390)
- [NBER Working Paper 19347 — Risk-Adjusting the Returns to Venture Capital](https://www.nber.org/system/files/working_papers/w19347/w19347.pdf)
- [Venture Investment Returns — Springer](https://link.springer.com/rwe/10.1007/978-3-030-38738-9_56-2)
- [Commonfund — Venture Capital and the Power Law of Returns](https://www.commonfund.org/cf-private-equity/is-venture-capital-going-back-to-the-future-reemergence-of-the-power-law-of-returns)
- [Venture Deals — Feld & Mendelson](https://www.amazon.com/Venture-Deals-Smarter-Lawyer-Capitalist/dp/1119594820)
- [Secrets of Sand Hill Road — a16z](https://a16z.com/books/secrets-of-sand-hill-road/)
- [The Power Law — Mallaby](https://www.goodreads.com/book/show/58009109-the-power-law)
