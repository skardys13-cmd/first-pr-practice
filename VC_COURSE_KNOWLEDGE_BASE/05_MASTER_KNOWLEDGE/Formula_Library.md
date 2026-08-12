# Formula & Model Library

**Version:** v1.0 — rebuilt 2026-08-12 from all 13 fully-extracted decks.
**Every formula below appears in the course material.** Nothing is added from
outside; where the course omits a standard formula, that is noted rather than
filled in.

---

## RETURNS

### IRR — Internal Rate of Return
```
IRR = ((FV / PV) ^ (1/n)) − 1
```
**Course definition** (`SRC-P-001`): *"basically the % return to the investor."*

**Worked example** (`SRC-P-013`): fund invests $100M, returns $300M in 3 years.
`(($300M/$100M)^(1/3)) − 1 = **43.69%**`

**Second worked example — Ziply Fiber** (`SRC-P-008`):
`IRR = (3.65/1.35)^(1/4) − 1 = (2.703^0.25) − 1 = 1.2823 − 1 = **28.23%**`

### MOIC — Multiple on Invested Capital ("Times Money")
```
MOIC = Exit proceeds ÷ Capital invested
```
**Course definition** (`SRC-P-001`): *"basically how many times did the money grow."*
**Example** (`SRC-P-013`): $300M exit ÷ $100M = **3x**

### ⭐ The rule-of-thumb tables — `PROFESSOR / COURSE VIEW`

**VENTURE CAPITAL — good funds target 40% IRR** (`SRC-P-013`, `SRC-P-001`)
| Outcome | ≈ IRR |
|---|---|
| 2x in 2 years | ~40% |
| 3x in 3 years | ~40% |
| 4x in 4 years | ~40% |
| **5x in 5 years** | **~40%** — *"This is what I would model when looking at a deal"* |

**PRIVATE EQUITY — good funds target 20% IRR** (`SRC-P-013`)
| Outcome | ≈ IRR |
|---|---|
| 2x in 4 years | ~20% |
| 3x in 6 years | ~20% |
| 4x in 8 years | ~20% |
| 5x in 10 years | ~20% |

**The shorthand** (`SRC-P-009`): **"2x4"** = 2x in 4 years ≈ 20% IRR = the PE
planning hurdle. **"4x4"** = 4x in 4 years ≈ 40% IRR = the VC planning hurdle.

> **The single most portable idea in the course: VC needs the same multiple in
> half the time PE does.**

### Fund survival threshold (`SRC-P-001`)
> "A VC FIRM — TO BE IN THE TOP HALF … needs at least **20%+ IRR on the entire
> fund**. NO SUFFICIENT RETURNS? — NO MORE FUNDS."

### Benchmarks to beat
| Benchmark | Value | Source |
|---|---|---|
| US stock market CAGR | **9.7%** | `SRC-P-001` |
| S&P 500, 100-year total return CAGR (1926–2026) | **10.42%** | `SRC-P-013` |
| S&P 500, 10-year | 15.62% | `SRC-P-013` |
| S&P 500, since 2000 | 7.91% | `SRC-P-013` |
| **Median PE return, last 10 years** | **13.5%** | `SRC-P-008` |
| PE industry average MOIC | 2.3x (top quartile 3.0x) | `SRC-P-010` |
| Private credit / PE / VC over 10 years | ~10% / ~15% / ~11.5% median | `SRC-P-010` |

---

## VALUATION — VENTURE

### Pre-money, money, post-money (`SRC-P-007`, `SRC-P-003`)
```
PRE + MONEY = POST
MONEY ÷ POST = OWNERSHIP BOUGHT = DILUTION TO FOUNDERS
POST = INVESTMENT ÷ OWNERSHIP %          ← solving backwards
```

**Worked example A** (`SRC-P-003`): $1M invested at **$4M pre** → **$5M post**;
investor owns 20%.

**Worked example B** (`SRC-P-003`): *"I will buy a 5% stake for $200,000"* →
`$200,000 ÷ 0.05 = **$4,000,000 post-money**`; founders retain 95%.

**Worked example C** (`SRC-P-007`, "typical Shark Tank like Seed Round"):
$250,000 for 50% → `$250,000 ÷ 0.50 = $500,000 post` → **$250,000 pre**.

### ⭐ THE VENTURE CAPITAL METHOD (`SRC-P-013`)
**The course's answer to "how do you value an early-stage company?"**
```
Required post-money = (Exit revenue × Exit multiple) ÷ Required MOIC
```
**Worked example:** NewCo could reach **$100M revenue** and exit in **4 years**.
The sector trades at **3x revenue** (*"like Calix does"*) → **$300M exit**.
Need **40% IRR** over 4 years → need **4x**. So `$300M ÷ 4 = **$75M post-money**
…or less.`

> *"This is how I decide what post money I can support at the current time."*

**Why it matters:** valuation is derived **backwards from the return you need**,
not forwards from intrinsic worth.

### What is NOT used (`SRC-P-007`) — `SOURCE FACT`
> **"Valuation Metrics like Discounted Cash Flow are NOT used, there is often no
> cash flow!"** — **"Market averages by Round are the most common valuation
> method."** Tracked by the **NVCA** and **PitchBook**.

---

## VALUATION — PE / M&A

### Market Capitalization (`SRC-P-007`, `SRC-P-013`)
```
Market Cap = Share Price × Total Shares Outstanding
```
**Worked (CALX):** 63.78M shares × $41.07 = **$2.619B**

### Enterprise Value — two variants, both the course's own
```
(SRC-P-008)  EV = Market Cap + Net Debt + Minority Interest − Cash
(SRC-P-009/013) EV = Market Cap + Total Debt − Cash
```
**Worked (CALIX, `SRC-P-013`):** $2.619B + $0.01472B − $0.2435B = **EV $2.390B**

> *"EV is capital-structure-neutral. It is the PE firm's true cost of ownership."*
> **"EV in, EV out."**

**And in diligence (`SRC-P-012`):** **`EV + WC = TOTAL NEEDED TO BUY AND RUN`**

### EBITDA (`SRC-P-013`)
```
EBITDA = Net Income + Interest + Taxes + Depreciation + Amortization
Adjusted EBITDA = EBITDA + goodwill impairment + one-time costs
                  + management fees + non-recurring items
```
> *"PE firms always negotiate 'Adjusted' EBITDA… Creates the basis for purchase
> price. **Adjustments are often heavily contested.**"* (`SRC-P-008`)

### Trading multiples (`SRC-P-008`)
| Multiple | Typical | Use |
|---|---|---|
| **EV / EBITDA** | **8x – 14x** | The primary PE metric |
| EV / Revenue | 1x – 5x+ | When EBITDA is negative or depressed |
| EV / EBIT | 10x – 18x | Penalizes capex-heavy businesses |
| P / E | 12x – 25x | Rarely used for PE deal pricing |
| EV / (EBITDA − CapEx) | 10x – 16x | Capex-intensive sectors |

**Benchmark multiples paid** (`SRC-P-013`): **PE ~11x EV/EBITDA · Corporate M&A
~9x.** LBOs today typically bought at **11x EBITDA** (`SRC-P-010`).

### Revenue multiple screen (`SRC-P-011`, `SRC-P-012`)
```
Revenue multiple = Market Cap ÷ Revenue (TTM)
```
**Worked (Allbirds):** $37.37M ÷ $160M = **0.24x** vs market average **0.55x**
→ *"Opportunity to double market cap if valued as 'normal'."*
Against Birkenstock: $7.4B = **3.4x revenue = 118x EBITDA**.

### Comps vs precedents (`SRC-P-013`)
| Method | Sample | Control premium |
|---|---|---|
| Comparable Companies | 5–10 public companies, apply **median** | **None** — minority value |
| Precedent Transactions | 10–20 past deals | **+20–40%** — reads higher |

### DCF (`SRC-P-013`) — used in M&A, *not* venture
1. Project FCF **5–10 years**
2. Terminal value (Gordon Growth or exit multiple) — **often 60–80% of total value**
3. Discount rate = **WACC, typically 8–12%** for stable companies
4. `PV = FCF_t ÷ (1 + WACC)^t`, summed + PV of terminal value

> ⚠ *"Highly sensitive to WACC and terminal growth — small changes can swing
> valuation by **30–50%**."*

---

## COST OF CAPITAL

### CAPM — cost of equity (`SRC-P-009`)
```
Cost of Equity = Risk-Free Rate + (Beta × Market Risk Premium)
              = 4% + (1.25 × 8.0%) = 14%
```
Inputs used: 10-yr government bond **4.019%**, beta **1.25**, ERP **~6–10%**
(*"~4% public-market ERP + ~2–5% illiquidity/PE premium"*).

### WACC (`SRC-P-009`)
```
WACC = (E/V × Cost of Equity) + (D/V × Cost of Debt × (1 − tax rate))
```
**Worked:** $300M company, $100M equity / $200M debt, cost of debt 9.6%, tax 30%
`(0.33 × 14%) + (0.66 × 9.6% × 0.70) = (0.33×14%) + (0.66×6.72%) = **9.15%**`
**All-equity (CALX, no debt):** WACC = cost of equity = **14%**

> **The arithmetic reason LBOs exist: 14% → 9.15% by adding tax-deductible debt.**
> *"Cost of Debt for a PE Buyout Deal is ~9.6%."*

---

## LEVERAGE & LBO

### The capital stack (`SRC-P-009`)
| Layer | Share |
|---|---|
| Senior Secured Bank Debt | ~50% |
| Senior Unsecured Notes | ~20% |
| Junk Bonds (Sub. Debt) | ~25% |
| **PE Equity** | **~5%** |

**Typical split** (`SRC-P-008`): **1/3 equity, 2/3 debt** (range 50–90% debt).
**2024 average leverage: 4.5x–4.7x Debt/EBITDA** (`SRC-P-009`); today's average
debt/equity ~2x (`SRC-P-010`).

### Leverage and coverage ratios (`SRC-P-008`)
| Metric | Threshold |
|---|---|
| **Total Debt / EBITDA** | Entry **4x–7x**; PE targets **5–6x**; lender cap ~6–7x |
| Senior Debt / EBITDA | 3x – 4.5x |
| Net Debt / EBITDA | Covenant tested, e.g. breach above 6.5x |
| **EBITDA / Interest** | Minimum **2.0x–3.0x**; below 2x is distress |
| (EBITDA − CapEx) / Interest (FCCR) | 1.1x – 1.25x |
| MOIC target | 2.5x – 3.5x+ over 5 years |
| **IRR hurdle** | **20%+ gross** |

### ⭐ The zero-growth LBO (`SRC-P-008`) — the clearest leverage illustration
```
ENTRY:  $100M purchase — $80M debt (7yr) + $15M PE + $5M management
EXIT (year 7): sold at the SAME $100M. No growth. No multiple expansion.
        Debt repaid entirely from company cash flow → $80M becomes $0
        $20M of equity now owns 100% = $100M

        PE:         $15M → $75M = 3.75x
        Management:  $5M → $25M = 4.00x
```
> *"Who pays the debt? **The company that is acquired does.**"*
> *"**LEVERAGE AMPLIFIES…WHETHER GOOD OR BAD.**"*

---

## INCOME STATEMENT

### Gross margin (`SRC-P-008`)
```
Gross Margin = Revenue − COGS
```
**Worked:** sell a watch for $100, bought for $60 → $40 = **40% margin**

**The average public company P&L:** `38% GM − 30% OpEx = 8% Net Income`
($100 revenue, $62 COGS)

```
Revenue − Cost of Revenue = Gross Profit
Gross Profit − Operating Expenses = Operating Income
```
**OpEx buckets:** S&M · G&A · R&D — *or* SG&A · R&D

### EPS and accretion/dilution (`SRC-P-013`)
```
EPS = (Net Income − Dividends) ÷ Shares Outstanding

Pro-Forma EPS = (NI_acquirer + NI_target − after-tax interest + synergies)
                ÷ (existing shares + new shares issued)
```
**⭐ The full worked model:**
```
  Acquirer NI                    $600M
  Target NI                      $150M
− After-tax interest on new debt ($63M)   ← $1,800M × 5% × (1−30%)
+ Cost synergies (after-tax)      +$50M
= Pro-forma combined NI           $737M
÷ Pro-forma shares                 236M   ← 200M + 36M issued at $50
= Pro-forma EPS                    $3.12
  Standalone acquirer EPS          $3.00
  ACCRETION                +$0.12 (+4.0%)
```

**Break-even synergies required by premium paid:**
| Premium | 10% | 15% | 20% | 25% | 30% | 35% | 40% | 45% | 50% |
|---|---|---|---|---|---|---|---|---|---|
| Synergies ($M) | 0 | 18 | 38 | 60 | 85 | 112 | 141 | 173 | 207 |

> *"Determine the premium you plan to pay → read off the break-even synergy level
> → **ask: is this synergy target achievable and credible?** If no — the deal may
> be value-destructive."*

### Goodwill (`SRC-P-013`)
```
Goodwill = Purchase Price − Fair Value of Net Identifiable Assets
```
**Worked:** $1,000 price − $700 net assets = **$300 goodwill**. Not amortized;
zero EPS impact until impaired, then a non-cash write-down hits net income.

---

## OPERATING METRICS

### Rule of 40 (`SRC-P-007`, `SRC-P-009`)
```
Revenue growth rate (%) + profit margin (%) ≥ 40%
```
Use **Free Cash Flow or EBITDA** for margin, *not* GAAP net income.

**Worked** (`SRC-P-009`): 3-yr CAGR 130%, revenue run-rate ~$25B with ~$5B losses
(−20%) → **130% − 20% = 110%**
| Tier | Score |
|---|---|
| Strong SaaS | 40–60% |
| Elite growth | 70–80% |
| Hyper-growth (rare) | 90%+ |

### Fees and spreads
| Item | Rate | Source |
|---|---|---|
| VC/PE management fee | **2%** of committed capital | `SRC-P-001`, `SRC-P-008` |
| **Hedge fund fee** | **2% of NAV, marked to market quarterly** | `SRC-P-014` |
| Carried interest | **20%** above return of capital/hurdle | throughout |
| **GP commitment** | **1% of fund must be the VCs' own money** | `SRC-P-002` |
| Investment banker M&A fee | **~7% of deal value** | `SRC-P-001` |
| IPO underwriter spread | **5–7%** | `SRC-P-007` |
| Greenshoe | up to **15%** more shares | `SRC-P-007` |
| PE deal-manager fee | **1% of total deal size, debt included** | `SRC-P-010` |
| RE fund | 1–2% fee, 15–20% carry after preferred return | `SRC-P-014` |

---

## Formulas the course NAMES but does not derive
Recorded so nothing is mistakenly attributed:
- **Contribution Analysis** (`SRC-P-013`) — named in the M&A toolkit, not worked
- **Gordon Growth Model** (`SRC-P-013`) — named as a terminal value method only
- **Alpha** (`SRC-P-013`) — defined conceptually (excess return over beta
  prediction) with examples, but no regression formula given
- **CAC, LTV, payback, retention** — **not covered anywhere.** See
  `EXTERNAL_CONTEXT_Research_Canon.md` gap #4.
