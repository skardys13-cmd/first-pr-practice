# Calculation Practice — worked solutions

All problems drawn from course examples. Do them cold, then check.

---
### 1. IRR and MOIC
$100M invested, $300M returned in 3 years.
```
MOIC = 300/100 = 3.0x
IRR  = (300/100)^(1/3) − 1 = 3^0.333 − 1 = 1.4369 − 1 = 43.69%
```

### 2. The hurdle tables — recall cold
40% IRR ≈ **2x/2yr, 3x/3yr, 4x/4yr, 5x/5yr** · 20% IRR ≈ **2x/4yr, 3x/6yr,
4x/8yr, 5x/10yr**. Shorthand: **"4x4" = VC, "2x4" = PE.**

### 3. Post-money from a stake
$200,000 for 5%: `200,000 / 0.05 = $4,000,000 post` → pre = 4,000,000 − 200,000 =
**$3.8M**. *(The deck states $4M as post; founders keep 95%.)*

### 4. Pre + Money = Post
$1M at $4M pre → **$5M post**; investor owns `1/5 = **20%**`.

### 5. The VC Method
$100M revenue × 3x = **$300M exit**. Need 40% over 4 years → **4x**.
`300 / 4 = **$75M maximum post-money**`.

### 6. Market cap and EV (CALX)
```
Market cap = 63.78M × $41.07 = $2.619B
EV = 2.619 + 0.01472 − 0.2435 = $2.390B
```

### 7. CAPM and WACC
```
Cost of equity = 4% + (1.25 × 8%) = 14%
WACC = (100/300 × 14%) + (200/300 × 9.6% × 0.70)
     = (0.333 × 14%) + (0.667 × 6.72%) = 4.67% + 4.48% = 9.15%
All-equity WACC = 14%
```
**The point:** leverage plus tax deductibility cuts the cost of capital by ~5pts.

### 8. The zero-growth LBO
```
Entry $100M: $80M debt + $15M sponsor + $5M management
Year 7, sold at $100M, debt fully repaid from cash flow
Equity now owns 100% = $100M, split 75/25 by contribution
Sponsor:    $15M → $75M = 3.75x
Management:  $5M → $25M = 4.00x
```

### 9. Income statement
Revenue $100, COGS $62 → **GM $38 = 38%**. Less 30% OpEx → **8% net income**.
Watch example: $100 − $60 = **$40 = 40% margin**.

### 10. Rule of 40
`130% growth + (−20% margin) = **110%**` — vs strong SaaS 40–60%, elite 70–80%.

### 11. Goodwill
`$1,000 − $700 = **$300**`, booked as a non-amortized intangible.

### 12. Accretion/dilution — full model
```
New shares = $1,800M / $50 = 36M → pro-forma shares = 236M
After-tax interest = $1,800M × 5% × (1 − 0.30) = $63M

Pro-forma NI = 600 + 150 − 63 + 50 = $737M
Pro-forma EPS = 737 / 236 = $3.12
Standalone EPS = $3.00
Accretion = +$0.12 = **+4.0% ACCRETIVE**
```
**Sensitivity to know:** no synergies at a 20% premium = **−1.8% (dilutive)**;
$100M synergies at 20% = **+9.6%**.

### 13. Break-even synergies
| Premium | 10% | 20% | 30% | 40% | 50% |
|---|---|---|---|---|---|
| Required ($M) | 0 | 38 | 85 | 141 | 207 |

### 14. Ziply
`MOIC = 3.65/1.35 = 2.70x` · `IRR = 2.70^0.25 − 1 = **28.23%**`
*(The deck also states 2.87x and 28.7% using slightly different figures — the
inconsistency is preserved in `SRC-P-008` notes.)*

### 15. The dilution exercise — reproduce the result
$40M raised two ways:
```
Staged:   $18M at $12M pre (A), then $22M at $100M pre (B)
          → founders $16.9M each · investors $381M on $40M ≈ 9x
One shot: all $40M at $12M pre
          → founders $12.4M each · investors $466M on $40M ≈ 12x
Difference to founders: ~40%
```

### 16. Revenue multiple screen
`$37.37M / $160M = **0.24x**` vs market average **0.55x**.
Re-rating to 0.55x implies roughly **doubling** the market cap.
Birkenstock: `$7.4B → 3.4x revenue → 118x EBITDA`.
