# SRC-P-013 — Deal Transaction Tools, the VC Method, and M&A Analysis

**Source:** `13.pptx` (Drive `10nD-7RQe_d7O3asSFAxca8ZO2KWZtuzH`)
**Course:** FIN/ENTRP 4350: Venture Capital, M&A, Private Equity · **Spring 2026**
**Instructor:** Todd Ortberg · **Extraction:** FULL (2026-08-12)

> **Fills the M&A gap.** Contains the **Venture Capital Method of valuation**,
> the complete **accretion/dilution model**, the full **M&A analysis toolkit**,
> deal structures, goodwill, board governance, and M&A success-rate data.
> Alongside `SRC-P-005`, this is the most interview-critical deck in the set.

---

## Part 1 — IRR and MOIC

### IRR — `SOURCE FACT`
```
IRR = ((FV / PV) ^ (1/n)) − 1
Example: fund invests $100M, in three years returns $300M
       = (($300M / $100M) ^ (1/3)) − 1 = 43.69%
```

### MOIC — `SOURCE FACT`
```
Times Money / Multiple on Invested Capital (MOIC) = Exit / Invested
Example: MOIC = $300M exit / $100M = 3x
```

### The two hurdle tables — `PROFESSOR / COURSE VIEW`

**VENTURE CAPITAL — good funds: 40% IRR**
| Outcome | ≈ IRR |
|---|---|
| 2x your money in **2** years | ~40% |
| 3x your money in **3** years | ~40% |
| 4x your money in **4** years | ~40% |
| 5x your money in **5** years | ~40% |

**PRIVATE EQUITY — good funds: 20% IRR**
| Outcome | ≈ IRR |
|---|---|
| 2x your money in **4** years | ~20% |
| 3x your money in **6** years | ~20% |
| 4x your money in **8** years | ~20% |
| 5x your money in **10** years | ~20% |

**The elegant symmetry:** VC needs the same multiple in *half the time*. This is
the cleanest single statement of the difference between VC and PE return
expectations in the entire course. *(The PE table's heading says "Rules of Thumb
for 40% IRR" — a slide typo; the body clearly gives 20%. Preserved as written.)*

---

## Part 2 — THE VENTURE CAPITAL METHOD OF VALUATION

`SOURCE FACT` — one of the most important frameworks in the course:

> "The Venture Capital Method of Valuation looks at **what I need the company to
> be to get my return desired in terms of xMOIC**.
>
> Example: ……I want 40% IRR....I think we can exit in 4 years….that means I need
> to invest so that the value at exit will be 4x my investment. **This is how I
> decide what post money I can support at the current time.**"

### The worked deal — `SOURCE FACT`

> "NewCo is pitching me (a VC) [on] a Series X deal.
>
> **1.** They have revenue and some traction, so I take a look, and estimate they
> could get to **$100M in revenue** ….and hence an exit as IPO or M&A…**in 4
> years**.
>
> **2.** The business they are in…. trades at **3x revenue** (like Calix does), so
> an exit at $100M revenue × 3x revenue valuation = **$300M exit value**.
>
> **3.** Since I know I need 40%, I know I need that exit value to be **4x what I
> invested in**, given a 4 year duration.
>
> **4.** So….the **$300M exit in the future / $75M investment valuation now = 4x**.
>
> **5.** Therefore, **$75M investment valuation is the Post Money I want on the
> current round X…or less.**"

**Why this matters enormously:** it inverts the valuation question. Rather than
asking "what is this company worth today?", the VC asks "what can I pay today
such that a realistic exit delivers my required multiple?" Valuation is derived
*backwards from the required return*.

This is the direct answer to the interview question **"how do you value an
early-stage company?"** — and it reconciles with `SRC-P-007`'s statement that
**DCF is not used** in venture. The VC Method replaces it.

```
Required post-money = (Exit revenue × Exit multiple) ÷ Required MOIC
```

---

## Part 3 — Company Valuation Tools (worked on Calix)

### Market Capitalization — `SOURCE FACT`
```
CALX: Shares Outstanding 63.78M (from Yahoo Finance)
    × Current Price $41.07
    = $2.619B
```

### Enterprise Value — `SOURCE FACT`
```
CALIX:  Market Cap        $2.619B
      + Total Debt        $0.01472B
      − Cash              $0.2435B
      = EV                $2.390B
```
> "**EV: THIS is the most commonly used assessment for PE of what it takes to buy
> the company.**"

### EBITDA and Adjusted EBITDA — `SOURCE FACT`
```
EBITDA = Net Income plus "Add backs" of Interest, Taxes, Depreciation and Amortization
```
**Adjusted EBITDA — used when goodwill impairment exists:**
- "Goodwill impairment reduces reported earnings, but….because it is a **non-cash
  expense**, it is typically excluded from adjusted financial metrics."
- "**Impact on Standard EBITDA?** Technically, a goodwill impairment charge is an
  operating expense that reduces net income. **Since it is neither interest,
  taxes, depreciation, nor amortization, it is sometimes left in standard EBITDA
  calculations, which would lower the result.**"
- "**Impact on Adjusted EBITDA:** In professional practice, analysts and firms
  almost always **also add back goodwill impairment** to calculate 'Adjusted
  EBITDA'."

### Trading multiples — `SOURCE FACT`
> "**EV/EBITDA is the most common PE and M&A tool.** EV represents the total cost
> to buy the company. EBITDA removes the non-cash items from Net Income to be a
> better measure of what the business is generating for earnings.
>
> Revenue multiples are also used, **especially when no EBITDA**…..
>
> EBITDA is used everywhere, **from valuation multiples to debt covenants. It is
> the de facto metric in many instances, for better or for worse.**"

### The two benchmark multiples — `SOURCE FACT`
| Buyer | Typical EV/EBITDA |
|---|---|
| **Private Equity** | **~11x** |
| **Corporate M&A** | **~9x** |

**A strategic buyer normally pays *less* than a PE firm on this metric** — worth
noting against `SRC-P-010`'s Adobe/Marketo example, where the strategic paid a
huge premium. Both are the course's own; the difference is competitive dynamics.

---

## Part 4 — Investor Evaluation Tools

### Benchmarks — the S&P 500 — `SOURCE FACT`
"A benchmark is a reference index used to measure investment performance… Used to
evaluate portfolio performance vs market, **fund manager skill**, and strategic
asset allocation assumptions."

**Historical Total Return CAGR (through April 2026):**
| Period | CAGR |
|---|---|
| **Long-Term Average (100 Years, 1926–2026, dividends reinvested)** | **10.42%** |
| 10-Year | **15.62%** |
| 5-Year | **13.72%** |
| **21st Century (since 2000)** | **7.91%** |

*(Note `SRC-P-001` gives 9.7% as the US stock market CAGR. Both preserved.)*

### Hurdle Rate — `SOURCE FACT`
"Minimum required return for an investment. This can be, and sometimes is, used
for determining **when a fund pays carried interest**. So an LP may set a hurdle
rate for [the] fund….that may be **payback of fund and fees….and is [so] in
Venture Capital**. But in some PE funds, that threshold is a hurdle rate."

```
IRR > hurdle rate → invest
IRR < hurdle rate → reject
```

**Important distinction:** in VC, carry typically starts after **fund and fees
are repaid**; in PE, after a **stated hurdle rate**.

### Beta — `SOURCE FACT`
β = 1 → moves with benchmark · β > 1 → more volatile · β < 1 → more defensive

### Alpha — `SOURCE FACT`
"**Alpha (α): excess return** — return above what beta predicts. Positive α =
manager skill. Negative α = underperformance."

| Alpha | Meaning |
|---|---|
| **Positive** | "outperformed its benchmark after adjusting for risk. If the market is up 10%, but the stock is up 13%, its Alpha is +3%. **GOOD INVESTOR**" |
| **Zero** | "performed exactly as its risk profile predicted. Most 'passive' index funds aim for zero Alpha minus a small expense ratio: **INVESTOR NO BETTER THAN BUYING SP500 INDEX FUND**" |
| **Negative** | "underperformed relative to its risk… **INVESTOR DESTROYS VALUE, WOULD HAVE [BEEN] BETTER OFF NOT USING THEM AND INVESTING IN INDEX FUND**" |

Example given: "Investors Alpha is **−3.3**…..less return [than] if just invested
in an index fund." And: **"Funds are 'seeking alpha'……"**

### WACC in M&A and PE — `SOURCE FACT`
"WACC = blended cost of equity and debt. Used as **discount rate in valuation
(DCF models)**. Essentially it is a **Hurdle Rate** for evaluating investment
returns required… given its risk."

**In M&A:** compare acquisition IRR vs WACC; use WACC as the DCF discount rate;
**if IRR > WACC → value creation**.
**In PE:** "Often replaced by hurdle rate (target IRR). Still used for valuation
baselines like DCF and exit pricing assumptions. **BUT…..the IRR desired in a
fund is likely >>> WACC….so often not the 'Hurdle Rate' desired. WACC would be
lower than the desired fund hurdle rate (e.g. 20% in Private Equity).**"

---

## Part 5 — THE M&A ANALYSIS TOOLKIT

`SOURCE FACT` — **"Multiple methods are used together — no single test is
sufficient"**

| Method | Question it answers |
|---|---|
| **Accretion / Dilution** | "Does the deal increase or decrease acquirer EPS? **The most common first test.**" |
| **DCF Valuation** | "What is the intrinsic value of the target?" |
| **Comparable Companies** | "What multiples do similar public companies trade at?" |
| **Precedent Transactions** | "What multiples have been paid in similar past deals?" |
| **LBO Analysis** | "What can a financial buyer (PE firm) pay and still achieve target returns?" |
| **Contribution Analysis** | "What % of combined revenues, earnings, and assets does each company contribute?" |

---

## Part 6 — ACCRETION / DILUTION — the complete model

### The concept — `SOURCE FACT`
```
EPS = (Net Income − Dividends) / Shares Outstanding
```
- **Accretive:** Combined EPS **>** Acquirer's standalone EPS. "The deal ADDS to
  earnings per share. Acquirer shareholders are better off." Happens when the
  target has **high earnings yield** or there are **significant cost synergies**.
  "Accretive deals often use cash or low-interest debt."
- **Dilutive:** Combined EPS **<** Acquirer's standalone EPS. "Acquirer
  shareholders are worse off — the acquisition price is too high relative to the
  earnings being added." Happens when **target's earnings yield < buyer's cost**,
  **synergies insufficient to offset premium**, **high debt financing costs**, or
  **large share issuance**.

**Evaluating a target for an accretive acquisition:** stronger profit margins and
revenue growth · no excessive debt burden · complementary products or services ·
potential for scalability and synergies.

### STEP 1 — Standalone inputs — `SOURCE FACT`

| Item | Acquirer (Co. A) | Target (Co. B) |
|---|---|---|
| Share Price | $50.00 | $30.00 |
| Shares Outstanding | 200M | 100M |
| Market Capitalization | $10,000M | $3,000M |
| Net Income (NTM) | $600M | $150M |
| **EPS (NTM)** | **$3.00** | **$1.50** |
| P/E Multiple | 16.7x | 20.0x |
| **Earnings Yield** | **6.0%** | **5.0%** |

*(Earnings yield = EPS ÷ Price, the inverse of P/E. NTM = next twelve months.)*

### STEP 2 — Deal assumptions — `SOURCE FACT`

| Assumption | Value | Explanation |
|---|---|---|
| Purchase Price per Share | **$36.00** | **20% premium** over $30 |
| Total Equity Purchase Price | $3,600M | $36 × 100M shares |
| Financing: Cash (50%) | $1,800M | Borrowed at **5% pre-tax** |
| Financing: Stock (50%) | $1,800M | Issues 36M new shares at $50 — **DILUTIVE** |
| After-Tax Interest Cost | **$63M** | $1,800M × 5% × (1 − 30% tax) — **DILUTIVE** |
| Annual Cost Synergies | **$50M** | After-tax, phased in Year 1 — **ACCRETIVE** |
| Pro-Forma Shares Outstanding | **236M** | 200M + 36M |

> "**Key: The interest cost on debt and shares issued both 'cost' the acquirer —
> they reduce or dilute EPS.**"

### STEP 3 — Pro-forma EPS — `SOURCE FACT`

```
  Acquirer Net Income (standalone)          $600M
  Target Net Income (standalone)            $150M
− After-Tax Interest on New Debt           ($63M)
+ Cost Synergies (after-tax)               +$50M
= Pro-Forma Combined Net Income             $737M
÷ Pro-Forma Shares Outstanding              236M
= Pro-Forma EPS                             $3.12
  Standalone Acquirer EPS                   $3.00
  ────────────────────────────────────────────────
  ACCRETION                        +$0.12 (+4.0%)
```

### Sensitivity — `SOURCE FACT`

| Scenario | EPS accretion / (dilution) |
|---|---|
| No synergies, 0% premium | **+3.2%** |
| No synergies, 20% premium | **−1.8%** |
| No synergies, 40% premium | **−5.9%** |
| $25M synergies, 20% premium | +1.2% |
| $50M synergies, 20% premium | **+4.0%** |
| $100M synergies, 20% premium | **+9.6%** |

> "**KEY INSIGHT: Synergies are the primary lever.** A 20% premium deal can swing
> from dilutive to highly accretive with sufficient synergy realization."

### Break-even synergy analysis — `SOURCE FACT`

**"What level of synergies is required to make the deal EPS-neutral?"**

| Premium paid | Required synergies ($M) |
|---|---|
| 10% | **0** |
| 15% | 18 |
| 20% | 38 |
| 25% | 60 |
| 30% | 85 |
| 35% | 112 |
| 40% | 141 |
| 45% | 173 |
| 50% | **207** |

**How to use it** — `SOURCE FACT`:
> "1. Determine the premium you plan to pay. 2. Read off the break-even synergy
> level. 3. **Ask: Is this synergy target achievable and credible?**
> 4. **If no — the deal may be value-destructive.**"

**This is a genuinely practical tool** — it converts a negotiation over price
into a testable operating question.

### Real examples — `SOURCE FACT`

**Accretive / successful:**
- **Facebook / Instagram (2012)** — "Instagram had high user growth but no
  revenue. Facebook monetized through advertising. Acquisition increased
  engagement and revenue per user."
- **Amazon / Whole Foods (2017)** — "Boosted brick-and-mortar presence…
  operational synergies with logistics networks. Enhanced Amazon Prime's
  subscription value."
- **Microsoft / LinkedIn (2016)** — "Integrated LinkedIn into Office 365 and AI
  tools. Increased advertising and B2B revenue."

**Dilutive / failed:**
- **eBay / Skype (2005)** — "No clear synergy, later sold at a loss."
- **Microsoft / Nokia** — "**Do you see many phones with Windows on them?.....
  18,000 laid off from Nokia when it didn't work….**"

> "**SUCCESSFUL INTEGRATION: Transitional Support Agreements are KEY**"

---

## Part 7 — Comps, Precedents, and DCF

### Comparable Companies — `SOURCE FACT`
"Find **5–10** similar public companies. Calculate key trading multiples:"

| Multiple | Typical range |
|---|---|
| EV / Revenue | 1x – 5x |
| EV / EBITDA | 6x – 14x |
| Price / Earnings | 12x – 25x |
| Price / Book | 1x – 4x |

"Apply **median** multiples to target's financials to estimate value range.
**Limitation: No control premium. Reflects minority share value.**"

### Precedent Transactions — `SOURCE FACT`
"Find **10–20** similar past M&A deals. Same key multiples, but:
- **Include a control premium (typically +20–40%)**
- More relevant for pricing a deal
- Reflect actual prices paid, not just public trading

**Typically shows HIGHER values than comps.** Limitation: old deals may not
reflect current market. No two deals are identical."

### DCF — `SOURCE FACT`, four steps
1. **Project Free Cash Flows** — "Forecast FCF for **5–10 years** based on
   revenue growth, margins, capex, and working capital changes."
2. **Estimate Terminal Value** — "Use **Gordon Growth Model or Exit Multiple**…
   **Often 60–80% of total DCF value.**"
3. **Select Discount Rate (WACC)** — "**Typically 8–12% for stable companies.**
   Higher risk = higher WACC = lower value."
4. **Discount All Cash Flows** — `PV = FCF_t ÷ (1 + WACC)^t`, summed, plus PV of
   terminal value.

> ⚠ "**DCF is highly sensitive to WACC and terminal growth rate assumptions —
> small changes can swing valuation by 30–50%**"

**Note the contrast with venture** (`SRC-P-007`): DCF is a real M&A/PE tool for
companies with cash flows, and explicitly *not* used for early-stage venture.

---

## Part 8 — Deal Structures

`SOURCE FACT`:

| Structure | Characteristics |
|---|---|
| **Cash Deal** | "Buyer pays 100% cash. **Seller receives certainty. Buyer bears all risk.**" |
| **All Stock Deal** | "Seller shares in combined upside/downside….**because they become stockholders too….and ride the stock.** In an all-cash deal this is not the case." Plus: "**Less dilutive to EPS if buyer stock trades at a high multiple** — so when your stock is high, it's a good time to theoretically buy, because that's less new shares to be issued…..so less dilution of EPS." |
| **Combination** | "Balances seller preference for certainty vs. buyer desire to preserve cash." |
| **Earnout** | "Part of price is contingent on future performance. Common in tech/pharma. **Bridges valuation gaps.** Creates post-close disputes — **30–40% of earnouts are litigated. 'Sue-Outs'…..**" |

> "All else equal, an **all-cash deal will show higher EPS than an all-stock
> deal** because it avoids share dilution. Note……the true outcome depends on the
> relative cost of capital and if you borrowed and added expenses."

**Public deals usually end up with a premium of ~30%.**

### Earnout example — Dell buys BakBone / Alvarri — `SOURCE FACT`

Another **first-hand case** (the instructor was CEO of Alvarri — `SRC-P-001`):
- Upfront payment
- **Asset purchase of the software technology**
- Integrated into Dell's corporate backup product line
- **5 years of revenue sharing** of that product line
- **Quarterly payments based on Dell revenue**
- **"Company stayed as a Shell with a board to collect payments and distribute"**

**Excellent, concrete illustration of how an earnout actually operates** — the
selling entity persists purely as a distribution vehicle.

---

## Part 9 — Goodwill

`SOURCE FACT`:
> "**Goodwill = the premium you pay above the fair value of identifiable net
> assets in an acquisition.** It's what you pay for things you can't separately
> identify or book — **brand, customer relationships, network effects, management
> quality**, etc."

**Purchase price allocation (PPA) at closing:**
```
Step 1: Start with purchase price — total consideration (cash, stock, debt assumed)
Step 2: Subtract identifiable net assets at fair value
        (assets — inventory, PP&E, identifiable intangibles like patents/customer
         lists — minus liabilities)

Goodwill = Purchase Price − Fair Value of Net Identifiable Assets
```
**Example:** "Purchase price $1,000 − Fair value of net assets $700 → **Goodwill
= $300**." A "$300 'plug' on [the] balance sheet as [an] intangible asset — **it
does not get amortized.**"

**Income statement treatment** — `SOURCE FACT`:
- "**No regular expense.** Goodwill does NOT show up on [the] income statement
  each year… **In normal operations: Goodwill has zero impact on EPS.**"
- "Then the business underperforms, and the company has to write down $100M of
  the $300M…. **Then Goodwill does hit [the] income statement if impaired.**"
- "The 'write down' of goodwill is a **non-cash expense** (in GAAP, excluded in
  non-GAAP). **It reduces net income and EPS, sometimes dramatically.** Seen as a
  One Time Event...**maybe**…."

**Impairment triggers** — annually required by the SEC: worse performance of the
acquired business/assets · worse outlook · higher discount rates if debt
applicable · "anything else that reduces the estimated value of the acquired
business below its carrying value."

### "Gaming Goodwill" — `PROFESSOR / COURSE VIEW`
> "**Academic research strongly suggests companies time impairments
> strategically, and down markets provide ideal cover.** The notion is that a
> company and its management will not be punished proportionately more for the
> big hit to already-depressed earnings. **This 'clearing of the decks' makes it
> easier to generate higher profits in later years.**"

---

## Part 10 — Boards and Governance

### Board functions — `SOURCE FACT`
"Boards steer the overall corporate direction: setting general goals and policies
on resources (**dividends, debt, capital raise**); **choosing executives
(especially the CEO)**; ensuring major decisions are essential, ethical, and
prudent. The board **should represent both the management and shareholders
interests.** Boards include external and internal members. The insider member is
usually a C-level executive. Outside directors are not involved in day-to-day
workings. Usually the CEO is the chairman."

### Fiduciary duties — `SOURCE FACT`
- **Duty of care** — act in the best interest of the company
- **Duty of loyalty** — avoid conflicts of interest
- **Duty of good faith** — make informed decisions
- **Duty of oversight** — monitor management and risks

### Approval thresholds — `SOURCE FACT`
- **Standard:** majority (over 50%) of shares. "Some companies may require a
  majority of **votes cast** rather than of **outstanding shares**."
- **Supermajority:** "Some companies and states (like **Delaware**) may require
  a supermajority (e.g. **66.7% or 75%**) for major corporate changes."
- **"Board Approval Required: Even if shareholders approve a deal, the Board of
  Directors must typically approve it first."**
- Divestitures/asset sales: "If a company is selling a major portion of its
  assets, shareholder approval may be required, usually with a majority vote."

### Shareholder activism — `SOURCE FACT`
> "**PE Deals can come from Public companies pushed/forced by ACTIVIST
> SHAREHOLDERS into action… M&A&D can result.**
>
> **M&A [is the] most common action pushed by activists.**
>
> Can come from simple communication with the management team [to] aggressive
> tactics such as **proxy battles and shareholder resolutions**."

Plus the aside: "if you own ONE share of Warren Buffett's Berkshire Hathaway
….you can attend their annual meeting……"

---

## Part 11 — THE SOBERING REALITY OF M&A

### Top 10 M&A mistakes — `SOURCE FACT`
"What experienced practitioners wish they had known"
1. **Overpaying due to auction pressure**
2. **Assuming synergies without rigorous analysis**
3. Neglecting cultural due diligence
4. Underestimating integration complexity
5. Losing key talent post-close
6. **Underestimating dis-synergies**
7. Letting integration drift after 100 days
8. Inadequate communication to employees
9. Pursuing deals for growth at any cost
10. **Not having a clear thesis before approaching [the] target**

### Success rates — `SOURCE FACT`

| Outcome | Share of deals |
|---|---|
| **Destroy Value** | **47%** |
| Break Even | 26% |
| Create Modest Value | 19% |
| **Create Significant Value** | **8%** |

Key findings: **~47% destroy shareholder value** · **~73% fail to beat the S&P
500 benchmark** · **~50% of all synergy targets are missed** · **~30% of acquired
companies are divested within 5 years.**
*Sources cited: McKinsey Global Institute, Harvard Business Review, KPMG M&A Survey.*

### Why deals fail — `SOURCE FACT`
| Factor | % citing as primary |
|---|---|
| **Poor Integration Execution** | **61%** |
| **Overpaying / Excessive Premium** | **57%** |
| Overestimated Synergies | 45% |
| Cultural Mismatch | 39% |
| Flawed Strategy | 31% |
| Insufficient Due Diligence | 22% |

### Who wins — acquirer vs target — `SOURCE FACT`

| Window | Acquirer abnormal return | Target abnormal return |
|---|---|---|
| Announcement Day | **−1.0%** | **+22.0%** |
| 1 Month Post-Deal | −2.5% | +24.5% |
| 1 Year Post-Close | −4.2% | +23.1% |
| 3 Years Post-Close | **−7.3%** | **+20.4%** |

> "**Acquirers Lose on Average −4% to −7% over 3 years. Targets Gain on Average
> +20% to +25% [at] announcement.**"
> *Source: academic meta-analysis of 2,000+ transactions.*

**This is the course's most important M&A conclusion**: target shareholders
capture nearly all the value, and acquirers destroy value on average. It reframes
every accretion/dilution model that precedes it — the model may say +4.0%, but
the base rate says be skeptical.

---

## Key Takeaways

1. **The VC Method:** required post-money = (exit revenue × exit multiple) ÷
   required MOIC. Valuation derived backwards from the return you need.
2. **VC needs the same multiple in half the time as PE** — 40% vs 20% IRR
   hurdles, expressed as matched rule-of-thumb tables.
3. **PE pays ~11x EV/EBITDA; corporate M&A ~9x.**
4. **Accretion/dilution is the first M&A test** — and synergies are the primary
   lever; the break-even synergy table turns price into a testable claim.
5. **Comps understate (no control premium); precedents include +20–40% control
   premium and read higher.**
6. **DCF terminal value is 60–80% of the answer**, and the output swings 30–50%
   on assumptions.
7. **30–40% of earnouts are litigated** — "sue-outs."
8. **Goodwill only hits earnings when impaired** — and impairments are timed
   strategically.
9. **47% of M&A destroys value; ~73% fail to beat the S&P; acquirers lose 4–7%
   over three years while targets gain 20–25%.**

## Cross-References

- `SRC-P-007` — DCF *not* used in venture; the VC Method is what replaces it
- `SRC-P-008` — EV, EBITDA, adjusted EBITDA, LBO analysis
- `SRC-P-001` — Calix, used here as the live valuation example
- `SRC-P-011` — Alvarri/Dell appears there as a portfolio exit; here as an earnout structure

## Open Items

- `[VISUAL NOT CAPTURED]`: the IRR/MOIC formula graphics; sensitivity and
  break-even charts (values recovered from data labels, axis labels inferred);
  "Typical Structure of a Company" org chart; the Apple/WACC deal-structure slide.
