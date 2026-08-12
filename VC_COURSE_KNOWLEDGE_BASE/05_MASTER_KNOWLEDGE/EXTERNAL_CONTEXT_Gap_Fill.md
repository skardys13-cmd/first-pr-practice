# EXTERNAL CONTEXT — Gap Fill: What the Course Did Not Teach

> # ⚠ NOT COURSE MATERIAL
>
> Nothing in this file came from Todd Ortberg, FIN/ENTRP 4350, or 4310. It fills
> gaps identified by auditing all 13 decks. **Never cite any of it as coursework.**
> Where it *corrects or updates* something the course taught, that is flagged
> explicitly — the course's position is preserved, not overwritten.

**Version:** v1.0 — researched 2026-08-12

---

## ⭐ GAP 1 — PRE-MONEY vs POST-MONEY SAFEs
### **This is the one that could actually embarrass you in an interview.**

**What the course teaches** (`SRC-P-005`, `SRC-P-003`): a SAFE is a warrant, not
debt, buying preferred at the next round's price at a ~15% discount, with an
indefinite term and no valuation required. **All correct — but incomplete.**

**What it omits:** SAFEs come in two forms, and **the distinction determines who
absorbs dilution.**

### The 2018 change
Y Combinator **replaced the pre-money SAFE with the post-money SAFE in 2018** and
pulled the pre-money form from its site. The post-money SAFE is now the market
standard. **The course's treatment predates or ignores this.**

### Why YC changed it
Startups raise from many angels over time, each SAFE carrying its own cap or
discount. As they stack, **ownership becomes impossible to calculate before a
priced round closes**, because inconsistent terms interact unpredictably.

### The post-money SAFE fixes that — with arithmetic you can do in your head
> A **$500k SAFE at a $10M post-money cap = exactly 5%** of the company.
> Add **$1M at a $16M post-money cap = 6.25% more**. Total sold: **11.25%.**

### ⚠ The trade-off founders miss
**Post-money SAFEs lock each investor's ownership percentage until the priced
round.** When the company issues *additional* SAFEs, **that dilution falls on the
founders**, not on earlier SAFE holders.

Under a **pre-money** SAFE, dilution is **shared** — each new investor dilutes the
founder *and* the earlier SAFE investors.

**The illustrative difference: a founder gives up ~30% under post-money SAFEs
where pre-money SAFEs would have cost ~25%.**

### Why this matters for you
The course's central dilution lesson (`SRC-P-005`) is that **staging rounds
preserves founder value**. The post-money SAFE is the *same lesson at the seed
stage* — and it cuts the other way: **stacking post-money SAFEs concentrates all
the dilution on the founder.** If asked "what's the risk of raising on SAFEs?",
this is the answer, and it's a genuinely current one.

**Sources:** [Carta](https://carta.com/learn/startups/fundraising/convertible-securities/pre-money-vs-post-money-safes/) ·
[YC — New Standard Deal](https://www.ycombinator.com/blog/new-standard-deal) ·
[Avisen Legal — the dilution math founders miss](https://www.avisenlegal.com/pre-money-vs-post-money-safes-the-dilution-math-founders-miss/) ·
[Pillar Legal — risks for founders](https://www.pillarlegalpc.com/wp-content/uploads/2024/07/Y-Combinators-Post-Money-SAFE-Risks-for-Founders-Final-2023-11-7-clean-V2.pdf)

---

## ⭐ GAP 2 — UNIT ECONOMICS
### The course teaches Rule of 40 and nothing beneath it.

`SRC-P-007` and `SRC-P-009` cover the **Rule of 40** (`growth% + margin% ≥ 40%`,
using FCF/EBITDA). That is an **IPO-readiness screen**. The metrics that actually
get discussed in early-stage diligence are absent entirely.

### The four metrics to know

**1. CAC Payback Period** — months of gross profit to recover customer
acquisition cost.
| Benchmark | Value |
|---|---|
| Median SaaS | **~16 months** (2025); some datasets report ~20, up from 12–14 |
| Good B2B SaaS | **under 18 months** |
| Top-tier | **under 12 months** |
| Top quartile | under 6 months |

**By deal size** (Benchmarkit 2025): sub-$5K ACV **9 months** · $10–25K ACV
**12 months** · $25–50K ACV **14 months** · $250K+ ACV **24 months**.
*Bigger deals take longer to pay back — that is normal, not a red flag.*

**2. Net Revenue Retention (NRR)** — revenue from existing customers year over
year, including expansion, net of churn and contraction.
| Segment | Median NRR |
|---|---|
| Enterprise (ACV > $100K) | **118%** |
| Mid-market ($25–100K ACV) | **108%** |
| Bootstrapped ($3–20M ARR) | **103%** |
| Best-in-class public SaaS | **120–125%** |

**Why it matters:** NRR above 100% means the business grows without acquiring a
single new customer. It is the closest thing to a single-number quality score.

**3. Burn Multiple** — net burn ÷ net new ARR. How much cash is consumed per
dollar of new recurring revenue.
| Level | Reading |
|---|---|
| **Median Series A** | **1.6x** |
| Above 2.0x | **"significant investor scrutiny"** |
| Under 1.5x | Competitive for top-tier investors |
| Under 1.0x | **Exceptional** |
| At $25–50M ARR | Target ~1.4x |
| At $100M+ ARR | Target ≤1.0x |

**4. Magic Number** — net new ARR ÷ prior-period S&M spend. Sales efficiency.
Median rose **0.94 (2024) → 1.37 (2025)**; 75th percentile **1.27 (2022) → 2.14
(2025)**.
⚠ **Conflicting guidance in the sources:** some define "healthy" as **0.70–0.89**
while the medians above exceed that. `[INTERPRETATION UNCERTAIN]` — the
thresholds are likely stage- and definition-dependent. **Cite the median trend,
not a hard "good" threshold.**

**Sources:** [Aleph — CAC payback 2026](https://www.getaleph.com/answers/cac-payback-period-saas-2026) ·
[Optifai — 939 companies](https://optif.ai/learn/questions/cac-payback-period-benchmark/) ·
[SaaS Capital — bootstrapped benchmarks](https://www.saas-capital.com/blog-posts/benchmarking-metrics-for-bootstrapped-saas-companies/) ·
[Digital Applied — NRR benchmarks](https://www.digitalapplied.com/blog/net-revenue-retention-benchmarks-2026-saas-expansion-data) ·
[Runway — burn multiple benchmarks](https://runway.com/blog/burn-multiple-benchmarks-for-2026-what-good-looks-like-at-seed-to-scale) ·
[CFO Advisors — Series A burn multiple](https://cfoadvisors.com/blog/2026-burn-multiple-benchmarks-series-a-saas) ·
[Data-Mania — magic number and NRR by stage](https://www.data-mania.com/blog/b2b-saas-revenue-efficiency-benchmarks-2026-magic-number-rule-of-40-nrr-by-stage/)

### How this connects to what the course *did* teach
`SRC-P-008`'s three cash needs — operating losses, **working capital**, capex —
are the *balance sheet* view of the same problem the burn multiple measures from
the P&L side. And `SRC-P-008`'s **"margin covers up a lot of sins"** is why CAC
payback is computed on **gross profit**, not revenue.

---

## GAP 3 — BURN AND RUNWAY
`EXTERNAL CONTEXT` — standard practice, not sourced to a specific study.

```
Net burn      = cash out − cash in, per month
Runway        = cash on hand ÷ net monthly burn
Default alive = would the company reach profitability on current cash
                and growth without raising again?
```

**The operating conventions:**
- Raise enough for **18–24 months** of runway. Below ~6 months, negotiating
  leverage collapses
- **Start raising with 9–12 months left** — a round takes 3–6 months
- **Gross burn** (total spend) vs **net burn** (spend minus revenue) — investors
  ask for net

**The connection to the course:** `SRC-P-005`'s staging result depends entirely
on surviving to the higher valuation. **Runway is what buys the option to stage.**
That link is the single most useful thing to say about burn in an interview, and
the course implies it without ever stating it.

---

## GAP 4 — THE OPTION POOL SHUFFLE
`EXTERNAL CONTEXT` — a standard negotiation the course omits entirely.

`SRC-P-005` covers the ESOP as a cap table line item. It does not cover **who pays
for it.**

**The mechanic:** investors typically require an option pool be created or topped
up **before** the round, **inside the pre-money valuation.** That means the pool
dilutes **existing shareholders only** — the founders — not the incoming investor.

**The effect:** a "$12M pre-money" with a 15% pool carved out pre-money is
economically closer to a **$10.2M** pre-money for the founders. The headline
valuation overstates what they actually got.

**The negotiation:** argue the pool should be sized to the *actual hiring plan*
for the next 12–18 months rather than a round number, or that it sit **post-money**
so both sides share it.

**Why it belongs next to the course material:** this is the same insight as
`SRC-P-005`'s dilution exercise — **the headline valuation is not the economics** —
applied to a term the course never mentions.

---

## GAP 5 — PORTFOLIO CONSTRUCTION
`EXTERNAL CONTEXT` — the math behind the power law the course teaches by anecdote.

The course states **~75% of VC deals don't return capital** (`SRC-P-010`) and
shows NVIDIA at $42M against a 24-year loss (`SRC-P-002`). It never formalizes
what that implies for building a portfolio.

**The logic:**
- If one deal must return the whole fund, **ownership at exit matters more than
  entry price**. A 2% stake in a $1B outcome returns $20M — immaterial to a $150M
  fund. Hence **target ownership** (commonly 10–20% at entry for a lead)
- **Reserves:** funds typically hold **40–60% of the fund** for follow-ons to
  defend ownership through later rounds
- **Shots on goal:** portfolio size is set so that the expected number of outliers
  is at least one — which is why seed funds hold 30+ positions and later-stage
  funds fewer
- **The fund-returner test:** for each investment, ask *"can this alone return the
  fund?"* If no, the ownership or the outcome assumption is wrong

**Connects directly to** `Fund_Economics_Framework.md`'s median $150M fund and the
10-year clock.

---

## GAP 6 — HOW VCs ACTUALLY DECIDE
`EXTERNAL CONTEXT` — the qualitative side the course is thinnest on.

The definitive source is **Gompers, Gornall, Kaplan & Strebulaev, "How Do Venture
Capitalists Make Decisions?"** — a large-scale survey of practicing VCs covering
sourcing, selection, valuation methods and post-investment involvement.
**Flagged in `EXTERNAL_CONTEXT_Research_Canon.md` as the highest-value paper still
to read in full.** Its headline finding — consistently reported — is that VCs rank
**the team above the market or the product** in selection, which is precisely the
dimension the course underweights.

**The practical gap to close:** the course gives you the tools to price and
structure a deal but almost nothing on judging the people. If an interviewer asks
*"what makes a good founder?"*, you currently have `SRC-P-012`'s diligence items
(track record, industry expertise, cultural fit) and the Coral Ventures
credential-verification failure — and little else. **Read the paper.**

---

## GAP 7 — SECTOR-SPECIFIC METRICS OUTSIDE SaaS
`EXTERNAL CONTEXT` — flagged, not researched.

The course's examples skew heavily to fiber/broadband/telecom and enterprise
software, because that was the instructor's career. Marketplaces (GMV, take rate,
liquidity), consumer (DAU/MAU, cohort retention curves), fintech (interchange,
loss rates), and hardware (BOM, gross margin ramp) all have different metric
stacks. **If you develop the Iowa insurance/private-credit thesis, the relevant
metric stack is insurance and credit, not SaaS** — that is a separate research
task.

---

## PRIORITY ORDER FOR SETH

1. **Post-money vs pre-money SAFEs** — the only item here that is a live
   *correction* to course material. Learn it first
2. **Unit economics** — CAC payback, NRR, burn multiple. Highest frequency in
   real conversations
3. **Burn and runway** — basic literacy, and it completes the staging argument
4. **Option pool shuffle** — a sharp, specific thing to know
5. **Gompers et al on VC decision-making** — closes the founder-evaluation gap
6. **Portfolio construction** — matters once talking to funds, not before
