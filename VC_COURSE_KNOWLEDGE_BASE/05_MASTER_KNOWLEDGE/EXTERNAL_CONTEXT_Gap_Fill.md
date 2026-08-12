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

## ⭐ GAP 6 — HOW VCs ACTUALLY DECIDE
### The single best evidence on the dimension the course underweights.

**Gompers, Gornall, Kaplan & Strebulaev, "How Do Venture Capitalists Make
Decisions?"** — *Journal of Financial Economics*, January 2020 (NBER WP 22587).
**A survey of 885 institutional venture capitalists at 681 firms.** It is the
largest systematic account of what VCs actually do, covering pre-investment
screening, deal structuring, and post-investment monitoring, using the framework
from Kaplan & Strömberg (2001).

### The three findings that matter for you

**1. Team beats business — in selection *and* in attribution.**
> In selecting investments, VCs see **the management team as somewhat more
> important than business-related characteristics** such as product or
> technology — though with meaningful variation across stage and industry.
> And VCs **attribute ultimate success or failure more to the team than to the
> business.**

**This is precisely the axis the course underweights.** `SRC-P-006`'s pitch
template makes Leadership Team required, and `SRC-P-012` lists management
evaluation in diligence — but the course spends its depth on structure, terms and
returns. **The evidence says practitioners weight the opposite way.**

**2. Deal *selection* is rated the most important source of value.**
> Of deal sourcing, deal selection, and post-investment value-add, **VCs rate
> selection as the most important of the three.**

This sits interestingly against two course claims. `SRC-P-011` argues
**sourcing** channel drives returns (proprietary beats auctions) — that is a PE
claim, and both can hold. And `SRC-P-007`'s *"do VCs add value beyond money? ~it's
about 50/50"* aligns well: practitioners themselves rank post-investment
value-add **below** selection.

**3. It quantifies the qualitative.** The paper is the credible source to cite
when asked how VCs evaluate founders — rather than repeating platitudes.

### How to use this in an interview
Asked *"what makes a good founder?"* or *"how would you evaluate a team?"*, the
strongest available answer combines both layers:

> "The course gave me the diligence frame — track record, industry expertise,
> cultural fit, and verifying credentials, which was a real failure case we
> studied. But the broader evidence goes further: the Gompers, Gornall, Kaplan
> and Strebulaev survey of 885 VCs found they rate the management team as **more
> important than product or technology in selection**, and they attribute
> outcomes more to the team than the business. They also rate **selection** as
> the biggest driver of value — above sourcing and above their own
> post-investment help."

That answer is honest about which part is coursework and which is reading, cites
a real study, and demonstrates you know where your training was thin.

**Sources:** [NBER WP 22587 (full PDF)](https://www.nber.org/system/files/working_papers/w22587/w22587.pdf) ·
[Journal of Financial Economics](https://www.sciencedirect.com/science/article/abs/pii/S0304405X19301680) ·
[Stanford GSB](https://www.gsb.stanford.edu/faculty-research/publications/how-do-venture-capitalists-make-decisions) ·
[Harvard Law corpgov summary](https://corpgov.law.harvard.edu/2019/08/20/how-do-venture-capitalists-make-decisions)

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

## ⭐ GAP 8 — WHY HEADLINE VALUATIONS ARE WRONG
### The best single thing you can raise unprompted in a VC interview.

**Gornall & Strebulaev, "Squaring Venture Capital Valuations with Reality"** —
*Journal of Financial Economics*, January 2020 (NBER WP 23895). They valued
**135 U.S. unicorns** using the actual financial terms in legal filings.

### The findings
| Finding | Value |
|---|---|
| Reported post-money valuations vs fair value | **48% too high on average** |
| Companies more than 100% overvalued | **14 of 135** |
| **Common shares overvalued by** | **56%** |
| **Unicorns that lose unicorn status once adjusted** | **65 of 135 — nearly half** |
| VCs who themselves think unicorns are overvalued | **91%** |

### Why — and this is the part that connects to the course
> **Reported valuations assume every share is as valuable as the most recently
> issued preferred share.** They are not.

Recent investors routinely hold protections that earlier shareholders and common
holders do not:
- **IPO return guarantees** — 15% of the sample
- **Vetoes over down-IPOs** — 24%
- **Seniority over all other investors** — 30%

**Common shares have none of these — hence 56% overvalued.**

### ⭐ Why this is the strongest thing you own
`SRC-P-003` teaches **`POST = INVESTMENT ÷ OWNERSHIP%`** — a $500k SAFE at a
$10M cap "means" a $10M company. `SRC-P-005` teaches that **preferences cumulate
by round** and that a $38M offer against $40M raised leaves common with roughly
nothing.

**This paper is those two lessons combined and measured at scale.** The headline
valuation the course teaches you to compute is *mechanically correct and
economically misleading*, because it prices the whole company off the most
protected share class in the stack.

The course gets you to the edge of this insight — the $38M trap is the same idea —
but never generalizes it. This does, with numbers.

### How to say it
> "One thing my coursework set up that I followed further: we learned that
> post-money is just investment divided by ownership, and separately that
> liquidation preferences cumulate by round — we worked a case where a company
> raised $40M, got a $38M offer, and the common was worth almost nothing.
>
> Gornall and Strebulaev did that at scale. They valued 135 unicorns off their
> actual legal terms and found **reported post-money valuations average 48% above
> fair value**, because the headline price assumes every share is worth as much as
> the newest, most-protected preferred. **Common is 56% overvalued, and about half
> the unicorns stop being unicorns once you adjust.**
>
> So when I see a headline valuation, my first question is what's in the
> preference stack."

**That answer demonstrates you can distinguish a reported number from an economic
one — which is most of the job.**

**Sources:** [NBER WP 23895 (full PDF)](https://www.nber.org/system/files/working_papers/w23895/w23895.pdf) ·
[Journal of Financial Economics](https://www.sciencedirect.com/science/article/abs/pii/S0304405X19301692) ·
[Stanford GSB](https://www.gsb.stanford.edu/faculty-research/publications/squaring-venture-capital-valuations-reality) ·
[Poets&Quants summary](https://poetsandquants.com/2020/02/24/stanfords-strebulaev-tech-unicorns-valuations-are-fairy-tales/)

---

## PRIORITY ORDER FOR SETH

1. **Post-money vs pre-money SAFEs** — the only item here that is a live
   *correction* to course material. Learn it first
2. **Unit economics** — CAC payback, NRR, burn multiple. Highest frequency in
   real conversations
3. **Burn and runway** — basic literacy, and it completes the staging argument
4. **Option pool shuffle** — a sharp, specific thing to know
5. **Gompers et al on VC decision-making** — closes the founder-evaluation gap ✅ *done*
6. **Gornall & Strebulaev on unicorn valuations** — the best unprompted point you
   have ✅ *done*
7. **Portfolio construction** — matters once talking to funds, not before
