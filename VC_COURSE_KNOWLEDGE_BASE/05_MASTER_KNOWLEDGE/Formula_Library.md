# Formula & Model Library

> **Evidence base: PARTIAL.** Built from the first ~5,000 characters of 11 of 14
> decks (see `Master_Course_Notes.md`). Entries are real and sourced, but the
> set is incomplete. Citations are `SRC-P-###, partial extract` — slide numbers
> are not recoverable from snippet-form text.

---

## IRR (Internal Rate of Return)

**Formula** — as written on the slide:

```
IRR = ((FV / PV) ^ (1/n)) - 1
```

**Variables** — `FV` future/exit value, `PV` invested capital, `n` years held.

**Meaning** — the annualized compound rate that grows the investment into the
exit value. The course presents it as a *deal transaction tool* for PE and M&A.

**Course example** — `SOURCE FACT`:
> A fund invests $100M, and in three years returns are $300M.
> `IRR = (($300M / $100M) ^ (1/3)) - 1 = 43.69%`

**When it is used** — evaluating PE and M&A transactions; the time-sensitive
counterpart to MOIC.

**Source** — `SRC-P-013`, partial extract.

---

## Rule of thumb: multiple-to-IRR shortcuts

`PROFESSOR / COURSE VIEW` — presented on the slide as "RECALL RULE OF THUMB":

| Outcome | Approx. IRR |
|---|---|
| 2x your money in 2 years | ~40% |
| 3x your money in 3 years | ~40% |
| 4x your money in 4 years | ~40% |

**Why it is worth memorizing** — it lets you convert between "times money" and
an annualized return in your head, in a meeting, without a spreadsheet. The
three cases are deliberately chosen to land on roughly the same number.

`CLAUDE INFERENCE` — the underlying arithmetic: 2^(1/2)-1 = 41.4%,
3^(1/3)-1 = 44.2%, 4^(1/4)-1 = 41.4%. All ~40%, so the heuristic holds.

**Source** — `SRC-P-013`, partial extract.

---

## MOIC / Times Money (Multiple on Invested Capital)

**Formula** — the slide introduces it as *"Times Money or Multiple on Invested
Capital (MOIC) ="* but the definition falls past the ~5,000-character
truncation point. `[TEXT NOT RETRIEVED]`

**Standard relationship** — `EXTERNAL CONTEXT`, clearly separated:
`MOIC = Total value returned / Total capital invested`. **Verify against the
full deck before using this in any career-facing document** — the course's own
phrasing has not been recovered.

**Source** — `SRC-P-013`, partial extract (truncated).

---

## Market capitalization

**Formula** — `SOURCE FACT`:

```
Market Cap = Price of Shares x Total Number of Shares in existence
```

**Course example** — Compaq's IPO: ~$500M market cap on $111M revenue, which
the deck converts to **~5x revenue** as a public-company valuation multiple.

**Source** — `SRC-P-007`, partial extract.

---

## Revenue-multiple valuation

**Method** — `SOURCE FACT`, from the Allbirds screen:

```
Revenue multiple = Market Cap / Revenue (TTM)
```

**Course example**:

| Input | Value |
|---|---|
| Market cap | $37.37M |
| Revenue (TTM) | $160M |
| Implied multiple | $37M / $160M = **0.24x revenue** |
| Sector average | **0.55x** |

**The investment logic the slide draws from it** — *"Opportunity to double
market cap if valued as 'normal' in market space, based on this metric."* This
is the course's worked illustration of PE deal selection by relative
undervaluation.

**Source** — `SRC-P-012`, partial extract.

---

## VC fund economics — the GP's two income streams

`SOURCE FACT` (`SRC-P-007`) — stated directly:

> "VC (GP's) big upside is carried interest of 20% of the fund amount above
> payback of original capital and fees."
> "So….the VC (The General Partner; GP) GETS: 2% of fund- Annual Fees.
> 20% of the 'Carry'"

**The worked case — Sevin Rosen Fund I:**

| Item | Value |
|---|---|
| Fund size | $25M |
| Notable holdings | Compaq **and** Lotus |
| Gross proceeds from Fund I companies | ~$191M (estimated) |
| Implied gross multiple | `CLAUDE INFERENCE` ~7.6x |

The slide then walks how "the $191M exit and pay gets distributed" — the
distribution waterfall itself is past the truncation point. `[TEXT NOT RETRIEVED]`

**Source** — `SRC-P-007`, partial extract.
