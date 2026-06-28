# Archetype playbook — Default compounder (durable moat, FCFF-valued)

How to value a mature company with an **enduring competitive advantage** — a moat that
protects returns above the cost of capital for the long run: branded consumer staples,
software platforms with switching costs, data-network businesses, regulated utilities
with allowed returns, industrial franchises with installed-base lock-in, healthcare
compounders with IP portfolios. The `scripts/dcf_valuation.py` engine was built for this
case; the discipline is not in adapting the model but in **estimating the four drivers
honestly** and **defending the terminal excess return that the model rewards so heavily**.
Embeds the school that owns intrinsic valuation: **Aswath Damodaran on the story-to-
numbers discipline, the 3P framework, and the terminal-value-as-going-concern logic.**

> Uniform skeleton (shared by every archetype playbook): identify → why the default
> frame works → the right drivers → engine mapping → input-estimation deltas → bear
> checklist → master lens → self-check → traps. Method-first; numbers date, structure doesn't.

## 1. Identify (and the mis-classification trap)

Use this archetype when the firm earns **returns on invested capital (ROIC) sustainably
above its cost of capital (CoC)**, supported by one or more identifiable moat sources:
brand pricing power, high customer switching costs, network effects, scale-cost
advantages, regulatory protection, or intangible-asset portfolios (patents, licenses,
data). Tells: gross margins are **high and stable** across a cycle (60%+ for software,
40%+ for branded goods); ROIC has exceeded CoC by 500+ bps for most of the last decade;
the company can raise prices without unit-volume collapse; market share is **durable**
rather than won by periodic price wars; and the reinvestment rate (capex + working
capital as a fraction of after-tax operating income) is moderate — the moat means growth
does not require consuming every dollar earned.

**The trap that wrecks valuations:** *mistaking a cyclical-at-peak for a default
compounder.* The cyclical's margins look fat at the top, its ROIC prints attractively, and
its management tells a growth story that sounds like a moat narrative — exactly the
profile this archetype's engine extrapolates. Feed peak-cycle numbers into a default FCFF
with terminal ROC > CoC and you value a commodity producer at 2× its through-cycle worth;
the next downturn erases the premium. Test: *does the margin oscillate 2–4× across a
cycle, driven by an input price the firm does not set? If yes, this is NOT a default
compounder — route to `playbook-cyclical.md`.* A profitable copper miner at $5/lb is not
Coca-Cola; a memory-chip maker at the top of the DRAM cycle is not Microsoft. The
discipline question: *can the firm defend this ROIC if the industry's revenue compresses
20%?* If the answer is no, the "moat" is not a moat — it is cycle timing.

A secondary trap: *mistaking a growth story for a compounder.* High revenue growth with
sub-CoC returns is not compounder economics — it is capital-consumption dressed as
momentum. Check ROIC first; growth amplifies value only when ROIC > CoC. If ROIC < CoC,
growth destroys value and the default frame does not apply (route to the growth or
turnaround playbook).

## 2. Why the default frame works (the FCFF model is designed for this case)

The FCFF engine models a firm as a going concern that converts revenue growth into free
cash flow through an operating margin, reinvests a fraction of after-tax operating income
to sustain that growth, and then earns a terminal return on capital that reflects its
competitive position. That structure **directly maps to the economics of a durable-moat
compounder:**

- **Revenue growth** — the firm grows with its addressable market (TAM) and/or takes
  share, both of which are forecastable when the moat is understood. Growth is not a
  mystery; it is TAM expansion plus a defendable share claim.
- **Operating margin** — a moat produces a **stable, predictable margin** that glides
  toward a long-run target rather than oscillating with input prices. The margin path can
  improve (operating leverage, mix shift, pricing) or compress (competition, regulation),
  but it does not swing 2× year-to-year.
- **Reinvestment (sales-to-capital)** — the moat means growth is capital-efficient. A
  dollar of after-tax operating income funds more than a dollar of revenue growth because
  the moat reduces the competitive scramble for each incremental sale. Sales-to-capital
  ratios of 1.5–3.0 are typical for compounders vs 0.5–1.0 for capital-heavy
  price-takers.
- **Risk (cost of capital)** — predictable earnings produce lower equity betas, narrower
  default spreads, and a cost of capital that **declines as the firm matures**. The
  terminal CoC is below the initial CoC — the firm gets cheaper to finance as its moat
  proves durable.
- **Terminal excess return** — this is the engine's most important lever and the one that
  most separates compounders from price-takers. A durable moat justifies `terminal_roc >
  cost_of_capital_terminal` — the firm earns excess returns in perpetuity because the
  moat is structural, not cyclical. That spread is value: every 100 bps of terminal
  excess return adds 15–25% to the intrinsic value per share, depending on reinvestment.

The model is not the risk; **sloppy inputs masquerading as precision** are. The whole
task is to estimate the four drivers from the competitive position outward, not from the
recent quarter backward.

## 3. The right drivers

Same four FCFF drivers, each read through the moat rather than the cycle:

| Driver | Default reading | Moat-compounder reading |
|---|---|---|
| **Revenue growth** | TAM × share, declining | **TAM growth × defendable share × pricing power.** Growth starts at a TAM-expansion rate (mid-to-high single digits for most addressable markets) and **declines toward terminal growth** (risk-free rate, 2–3% nominal) as the firm saturates its market. Revenue growth = volume growth + price growth; the moat's pricing power means real price growth > 0, so nominal revenue growth in terminal > inflation. |
| **Operating margin** | base → target glide | **Base (current, normalized) → target (long-run steady-state), adjusted for R&D, SBC, and one-time items.** The glide is 3–7 years; moat quality determines both the target level and the confidence in reaching it. A wide-moat firm's target margin should reflect its **unit-economic maturity**, not a peak quarter. Target margin is the margin at which the firm earns its terminal ROC — back-solve it through the reinvestment rate. |
| **Reinvestment (sales-to-capital)** | revenue per $ invested capital | **Revenue generated per dollar of incremental invested capital (capex + working capital + R&D capitalization).** Compounders are capital-light: 1.5–3.0×. Separate growth reinvestment from maintenance; the moat means maintenance is low. R&D is capex, not opex — capitalize it (§5) or the sales-to-capital ratio is overstated (looks more efficient than it is because the capital base is understated). |
| **Risk (cost of capital)** | riskfree + β·ERP | **Declining CoC path.** Initial CoC (8–10%) reflects current operating risk, industry beta, and any country-risk premium. Terminal CoC (7–8%) reflects the mature, moat-protected steady state. The decline is 50–100 bps over the high-growth period, modeled as a linear glide. Equity risk premium is 4.5–5.5% for developed markets; add a country-risk premium (Damodaran's CRP table) for EM exposure. |
| **Terminal ROC** | durable excess if moat | **Terminal ROC > terminal CoC by a defendable spread.** The moat is the warrant for the spread. Typical spreads: 200–500 bps for wide moats (Visa, Microsoft, Coca-Cola); 100–200 bps for narrow moats; 0 bps for no-moat firms (see cyclical playbook). The spread must be **explainable in one sentence** that names the moat source: "switching costs make customer lifetime value >> acquisition cost," not "the company is great." |

The thesis sentence is not a multiple; it is: *the moat — [name it: switching costs /
brand / network effects / scale-cost / regulatory / IP] — supports returns above the cost
of capital for the long run, and the current price embeds [optimism / realism /
pessimism] about the durability of that moat.*

## 4. Engine mapping → `dcf_valuation.py`

The FCFF engine accepts exactly the four drivers plus terminal assumptions. Feed it
**adjusted** numbers (R&D capitalized, leases capitalized, SBC expensed — see §5). The
discipline is in the JSON:

```bash
cd scripts
python dcf_valuation.py ../templates/default.microsoft.json          # value/share, terminal share
python dcf_valuation.py ../templates/default.microsoft.json --json    # for charts.py / programmatic use
```

Mapping for a compounder name (see `templates/default.microsoft.json`):
- `base_operating_margin` → trailing operating margin **after R&D capitalization and SBC
  adjustment**, not the GAAP print. Microsoft's GAAP margin is ~44%; adjusted margin may
  be higher or lower depending on R&D treatment. `target_operating_margin` → long-run
  steady-state margin the firm converges to over the glide period. The target should be
  **below** the base if the base includes a cyclical tailwind, or **above** if the base
  reflects a reinvestment-heavy period.
- `revenue_growth` → starts at a TAM-plus-share-take rate (e.g., 12% for a company
  expanding cloud TAM at 15% with 80% share retention) and declines over the high-growth
  period to terminal growth (2–3% nominal). The path is a staircase, not a hockey stick;
  every inflection needs a business driver (product launch, geographic expansion, pricing
  change).
- `sales_to_capital` → **1.5–3.0× for compounders.** Microsoft's is ~2.0×: each dollar
  of reinvested capital (capex + R&D + working capital) generates ~$2 of incremental
  revenue. Set this number by averaging the firm's own historical marginal sales-to-capital
  over 5+ years, or by benchmarking against comparable moat-width peers. Do not plug the
  industry average — a wide-moat firm should be above it.
- `terminal_roc` → **above `cost_of_capital_terminal`.** Microsoft: 20% ROC terminal vs
  8.0% terminal CoC — a 1200 bps spread. That is wide. It requires the analyst to state
  **why** Microsoft earns 20% in perpetuity: the enterprise-software switching-cost moat,
  the Azure network effect, the Office/Windows installed base. If you cannot defend the
  spread in two sentences, narrow it. A spread of 300–500 bps is aggressive; 500+ bps is
  extraordinary and demands extraordinary evidence.
- `cost_of_capital_initial` → 9–10% for a typical compounder (beta 1.0–1.2, ERP 5%,
  risk-free 4–4.5%). `cost_of_capital_terminal` → 7.5–8.5% (beta declines toward 1.0 as
  the firm matures, default risk recedes). The decline is the market's vote of confidence
  in the moat.
- `terminal_growth` → the nominal risk-free rate (3–3.5% for USD, adjusted for the
  firm's currency mix). Do not exceed the risk-free rate — terminal growth above the
  economy's growth rate implies the firm becomes the economy, which is impossible unless the
  economy itself is the TAM and the firm already owns it (and even then, it is the
  asymptote). A terminal growth rate of 2.5% is aggressive; 3.0% is the practical ceiling
  for a US-dollar compounder.

Worked anchor: those inputs for a wide-moat software platform reproduce value/share
reflecting a terminal value of ~55–65% of operating value — the compounder's natural
range. If terminal value exceeds 75%, the near-term assumptions are too thin and the
valuation is a terminal-value punt, not a forecast. If terminal value is below 45%, the
near-term growth is doing the lifting and the terminal assumption may be too conservative
or the growth period too long.

**Reverse-DCF cross-check (mandatory).** Run `reverse_dcf.py` on the same name and ask
the compounder-specific question: *what revenue growth and margin does the current price
imply, and are those numbers consistent with a plausible TAM trajectory?* If the market
price implies 15% revenue growth in perpetuity when the TAM grows at 6%, the price is
betting on a share gain that must eventually hit a ceiling. If it implies a margin 500
bps above any peer, the price is betting on a moat width the industry has never seen. The
reverse DCF converts "overvalued / undervalued" into a concrete "the price embeds X,
while the TAM and competitive position support Y."

## 5. Input-estimation deltas (adjusting before you value)

The GAAP income statement is a starting point, not the truth. Four adjustments are
mandatory for compounder valuation, and skipping any of them systematically misprices the
firm:

### 5.1 R&D capitalization

R&D is an investment in future revenue, not a period expense. Treating it as opex
understates both current operating income and invested capital, and overstates the
sales-to-capital ratio (makes the firm look more capital-efficient than it is).

**Method:**
1. Determine an amortizable life for R&D (typically 3–5 years for software, 5–10 for
   pharma — match the product development cycle).
2. Collect R&D expense for the last N years (N = amortizable life).
3. Capitalize each year's R&D and amortize it straight-line over the life. The net R&D
   asset is the unamortized portion; the R&D adjustment to operating income = current
   year R&D expense − current year amortization of past R&D.
4. Add the net R&D asset to invested capital; adjust operating income upward by the net
   R&D capitalization (R&D expense − amortization).

The adjustment is material for any firm where R&D exceeds 5% of revenue — which is nearly
every compounder in technology, healthcare, and specialty industrials.

### 5.2 Operating leases

Operating leases are debt-like obligations. Capitalize them or the capital base is
understated, and the firm looks artificially asset-light.

**Method:**
1. Collect future minimum lease payments (from the lease footnote) for the next 5+ years
   and the "thereafter" lump sum.
2. Discount them at the firm's pre-tax cost of debt (typically 3–5% for investment-grade).
3. The PV of lease commitments is lease debt — add it to invested capital. Adjust operating
   income by adding back the imputed interest portion of the lease payment (the depreciation
   is already embedded in the lease expense reversal).

Since ASC 842 / IFRS 16, most leases already appear on the balance sheet as right-of-use
assets and lease liabilities. Verify that they are there; if they are, the adjustment is
redundant. If valuing a pre-2019 historical period or a jurisdiction with weaker
standards, apply the full capitalization.

### 5.3 Stock-based compensation (SBC)

SBC is compensation expense — real, dilutive, and cash-cost-equivalent over the long run.
Treating it as a non-cash add-back overstates operating income and free cash flow.

**Method:**
- **Option 1 (conservative, preferred):** Treat SBC as an operating expense, do not add it
  back in the FCFF calculation. This reduces operating margin and free cash flow; it is
  the right treatment if you believe SBC is a recurring cost of talent.
- **Option 2 (adjusted):** Add back SBC to FCFF but increase the diluted share count to
  reflect the full overhang of outstanding options, RSUs, and warrants. The dilution
  reduces value per share; the add-back increases FCFF. The two effects partially offset,
  but the net is almost always negative (dilution > FCFF boost) for heavy SBC issuers.
- **Option 3 (Damodaran's preferred):** Forecast future SBC as a fraction of revenue
  (based on historical grant rates), treat it as an operating expense in the projection,
  and adjust the share count for expected dilution. This is the most forward-looking
  treatment and the one the engine supports directly.

**Which option?** Option 1 for most cases — simple, conservative, and hard to game.
Option 3 for firms where SBC is a material (5%+ of revenue) and variable cost that
warrants explicit modeling.

### 5.4 One-time charges and non-recurring items

Restructuring charges, asset impairments, litigation settlements, and gains/losses on
asset sales are not operating items. Remove them from the base year's operating income
before setting `base_operating_margin`.

**Method:**
1. Average the last 3–5 years of one-time items to compute a run-rate adjustment. Most
   firms have a "one-time" charge every year — that is a recurring cost under a different
   name.
2. If the charge is genuinely one-time (a specific lawsuit settlement, a one-off
   restructuring), remove it entirely.
3. If charges recur (annual restructuring, periodic impairments), treat the average as a
   normal cost of doing business.

The rule: if management calls it "one-time" in three of the last five years, it is not
one-time — it is an unrecognized operating cost. Expense it.

### 5.5 Cross-holdings and minority interests

If the firm owns stakes in other public/private companies (common in tech and
conglomerates), those are non-operating assets. Value them separately and add to the
operating value:

**Method:**
1. Public stakes → mark to market, apply a liquidity discount (10–20%).
2. Private stakes → use the latest funding round or a comparable-company multiple, apply
   an illiquidity discount (20–30%).
3. Add the after-tax value to the DCF-derived operating value per share. Do not bury
   cross-holdings in the revenue or margin assumptions.

## 6. Bear checklist + leading indicators (Munger: invert; always invert)

A compounder's story of durable excess returns is a claim the market is right to
skeptically cross-examine. Five vectors, each with the leading indicator that turns first:

1. **Moat erosion (the central one) — ROIC trend, Munger.** The moat is a structural
   claim; ROIC is its observable signature. Track **ROIC over rolling 5-year windows**,
   adjusted for R&D and goodwill. A declining trend (ROIC falling toward CoC) means the
   moat is narrowing — competition is arriving, switching costs are eroding, or pricing
   power is slipping — and it is happening *before* revenue growth or margin shows it.
   Watch: gross margin compression precedes operating margin compression; customer
   retention/churn rates precede revenue deceleration. *Invert: what would make this
   moat irrelevant in 10 years? Technology substitution? Regulatory change? A new
   business model that makes the installed base a liability?*

2. **Disruption — revenue-TAM decoupling.** The firm's revenue growth should track its
   addressable TAM. When revenue growth detaches from TAM growth downward (the firm grows
   at 3% while its TAM grows at 8%), it is losing share — the moat is not defending the
   franchise. When it detaches upward (20% firm growth in an 8% TAM), it is gaining share
   but may be doing so unsustainably (pricing below cost, over-investing). Track:
   **market share trajectory** as the ratio of firm revenue growth to TAM growth. A
   compounder should hold or gain share gradually; a share spike is as concerning as a
   share leak.

3. **Management capital allocation — return on incremental invested capital (ROIIC).**
   The moat only compounds value if management reinvests at above-CoC returns. ROIIC
   measures the return on each dollar of new investment: (Δ NOPAT) / (Δ Invested Capital).
   If ROIIC < CoC, growth is destroying value — and because management is paid on growth
   (revenue, EPS), not on ROIIC, the incentive is to keep investing past the point of
   value creation. Watch: **serial M&A at ROIC < CoC**, buybacks at prices above intrinsic
   value, capacity additions into a softening market. The capital-allocation record is the
   single best predictor of whether the moat's value accrues to shareholders or gets
   reinvested into value-destroying endeavors.

4. **Valuation — multiple compression from re-rating.** A compounder can deliver healthy
   earnings growth and still lose shareholders money if the entry multiple compresses.
   EV/EBIT multiples for wide-moat compounders typically range 15–25×; an entry at 30×
   requires perfection, and a re-rating to 20× over 5 years subtracts 6–7% annualized from
   total return even if earnings grow nicely. Watch: **implied cost of equity from the
   reverse DCF** — when the market price implies a cost of equity below 7%, the multiple
   is demanding a bull case as the base case.

5. **Macro and regulatory — the exogenous risks to the moat.** Compounders are *less*
   exposed to macro cycles than price-takers, but they are *more* exposed to regulatory
   and antitrust risk — the very moat that produces excess returns invites political
   scrutiny. Watch: **antitrust filings, regulatory proposals targeting the moat source**
   (app-store rules for platforms, patent cliffs for pharma, tariff exposure for branded
   goods with global supply chains), and **interest-rate sensitivity of the terminal
   value** — a 100 bps rise in the risk-free rate alone can reduce intrinsic value 12–20%
   for a long-duration compounder because the terminal value is such a large fraction of
   operating value.

Each bear vector must be assigned a **probability and a value impact.** A bear checklist
without numbers is storytelling, not analysis.

## 7. Master lens — Aswath Damodaran (the story-numbers-value discipline)

Damodaran is **the** school for intrinsic valuation. His framework is the spine this
playbook hangs on, and using it means running the full discipline, not quoting the man:

### (a) Story → Numbers → Value (the spine)

Every valuation is three layers: a **story** about the company's competitive position
and how it will evolve; **numbers** that translate the story into drivers (growth,
margin, reinvestment, risk); and a **value** that the numbers produce when discounted.
The analysis fails when any layer detaches from the one above it — a story with no
numbers is narrative; numbers with no story are spreadsheet exercises; a value with no
story or numbers is a multiple pulled from a peer group.

**Operational form for this playbook:**
1. Write the story in one paragraph: *"Company X has a [moat type] that allows it to
   [pricing/reinvestment/share] advantage, growing with its TAM at [X%] while defending
   margins of [Y%], producing returns of [Z%] on capital."*
2. Map each sentence to a driver. "Growing with its TAM at X%" → `revenue_growth` path.
   "Defending margins of Y%" → `base_operating_margin` / `target_operating_margin`. "Returns
   of Z% on capital" → `terminal_roc`.
3. Run the numbers. If the value that comes out conflicts with the story (e.g., a "wide
   moat" story producing a value per share below the market price because margins are
   declining), *one of the three is wrong* — adjust the story, the numbers, or the market
   thesis. Never smooth the disconnect.

### (b) The 3P framework: Philosophy, Process, People

- **Philosophy:** You must believe that markets make mistakes (or there is no point to
  valuation) and that those mistakes correct over time (or there is no profit in being
  right). A value investor's philosophy is that price converges to intrinsic value —
  eventually, not mechanically, with a catalyst or without one, over a horizon of 2–5
  years. If you lack this conviction, you are trading, not valuing.
- **Process:** The process is the DCF — not because a DCF is "accurate" (it is not) but
  because it forces you to be explicit about every assumption. A DCF is a disciplined
  conversation, not a calculation. Change one input and the value changes; the question
  is whether the change is plausible given the story. The spreadsheet that embarrasses
  you with its output is the one that is working.
- **People:** Management matters more for compounders than for any other archetype
  because the moat's durability depends on decisions made over decades. Assess: does
  management understand the moat's source? Do they invest to defend it? Does their
  capital allocation record (ROIIC, buyback timing, M&A discipline) suggest they are
  stewards of the moat or exploiters of it for personal enrichment? Proxy: insider
  ownership, compensation structure (ROIC-linked vs revenue-linked), and the CEO's
  letters — read five years of them for consistency of moat narrative vs opportunistic
  pivots.

### (c) "What has to be true" — the breakeven analysis

For every compounder, there is a set of assumptions that makes the current price the
intrinsic value. Find that set. If the current price implies 10% revenue growth and 35%
margins in perpetuity, ask: *do I believe the TAM grows at 10% for decades and no
competitor enters to compress that 35% margin?* If the answer is "that requires a
suspension of competitive economics," the stock is overvalued. If the reverse DCF shows
the price embeds declining growth and margin compression, the stock is undervalued even
under conservative assumptions. The breakeven is the sanity check; it converts "I think
this is cheap" into "the market is pricing X, and I believe Y instead."

### (d) Stay in the lane

This is intrinsic valuation of a single company. Use Damodaran's framework, his data
(ERP tables, country-risk premiums, industry betas, tax-rate compilations), and his
discipline. Do **not** import macro forecasting, top-down allocation, or technical
analysis — those answer a different question than "what is this company worth to a
long-horizon buyer of the whole business." If the question is "should I buy this stock
now?", the intrinsic value is one input among many; if the question is "what is this
company worth?", it is the answer.

## 8. Self-check gate (before publishing a default-compounder report)

- [ ] **R&D capitalized** — the net R&D asset is on the balance sheet; operating income
      reflects the R&D adjustment; invested capital includes the capitalized R&D asset.
- [ ] **Operating leases capitalized** — lease debt is added to invested capital; operating
      income is adjusted for the imputed interest (or ASC 842 compliance verified).
- [ ] **SBC expensed or dilution-adjusted** — one of the three treatments (§5.3) is applied
      consistently; SBC is not silently added back to FCFF without a dilution offset.
- [ ] **One-time charges normalized** — recurring "one-time" items are treated as operating
      costs; genuinely non-recurring items are removed from the base margin.
- [ ] **Moat named and defended** — the moat source is identified (brand / switching costs /
      network effects / scale-cost / regulatory / IP) and the claim is supported by
      ROIC history, market-share stability, and gross margin trend.
- [ ] **Terminal ROC > terminal CoC** — the spread is stated explicitly (e.g., "300 bps:
      12% ROC over 9% CoC") and defended in one sentence that names the moat mechanism.
- [ ] **Terminal growth ≤ risk-free rate** — the terminal growth rate does not exceed the
      nominal risk-free rate for the firm's primary-currency economy. The assumption is
      stated as a percent.
- [ ] **Terminal value % of operating value stated** — "terminal value represents X% of
      operating value." If > 75%, the near-term forecast is too short or too thin.
- [ ] **Margin-of-safety band** — a range is given around the base-case value, driven by
      plausible variation in the two most sensitive drivers (typically terminal ROC spread
      and revenue growth). Use `monte_carlo.py` or a simple scenario table (bear / base /
      bull) with explicit driver values. "About $150/share" without a band is a point
      estimate masquerading as precision.
- [ ] **Bear case is as rigorous as the bull case** — the bear scenario has explicit
      drivers (ROIC declining, share loss, margin compression, multiple contraction) and
      produces a specific value per share. If the bear case is "the stock might go down,"
      it is not a bear case — it is anxiety.
- [ ] **Reverse DCF run and reported** — the reverse DCF output is reported as: "At the
      current price, the market is pricing in revenue growth of X% and margins of Y%. The
      TAM grows at Z%, so the implied growth requires market share of W% — which is
      [plausible / aggressive / impossible]."
- [ ] **Damodaran data used** — ERP, country-risk premium, and beta are sourced from
      Damodaran's published tables (updated annually at `pages.stern.nyu.edu/~adamodar`),
      not invented or Googled from a random source.
- [ ] **Numbers ledger complete** — every driver assumption is recorded in the numbers
      ledger (`references/number-ledger.md` or the valuation JSON), dated, and sourced so
      that the next analyst can reproduce and challenge the valuation.

## 9. Common traps

- **Peak margins as "normalized"** — running a margin that the firm achieved once in a
  demand spike as the `target_operating_margin`. A compounder's target margin is the
  margin at which its moat produces a defendable ROC; if the target margin requires a
  demand environment that occurs once a decade, the "moat" is actually cycle luck. Test:
  *could this margin be sustained in a mild recession?* If no, it is not normalized.
- **TAM religion** — constructing a revenue path by taking a Gartner/IDC TAM forecast
  and multiplying by an assumed market share, without asking whether the TAM itself is
  sensibly forecastable (most are not, beyond 3–5 years) or whether the revenue path
  implies a market-share trajectory that violates competitive bounds (share > 100% of a
  sub-market, or share growing at a rate that requires competitors to cede without
  fighting). TAM is a directional anchor; revenue growth is a business forecast rooted in
  unit economics, not a TAM × share arithmetic exercise.
- **Terminal value denial** — "the terminal value is X% of the total, so I'll shorten the
  high-growth period to reduce it." This is gaming the model. The terminal value is large
  because the firm is a going concern; that is the right answer. The correct response to a
  large terminal value is not to shorten the growth period but to ensure the terminal
  assumptions (ROC, growth rate, CoC) are conservative and defended. A shortened growth
  period with an unchanged terminal assumption produces the same terminal value in fewer
  years — worse, not better.
- **False precision** — producing a valuation of "$143.27 per share" from inputs that have
  ±30% uncertainty bands each. The value is a midpoint of a distribution; report it as a
  range. The margin-of-safety band is not a concession to uncertainty — it *is* the answer.
  "The stock is worth $130–170, with a base case of $150, vs a current price of $120" is
  a complete valuation. "$143.27" is cosplay.
- **Story drift** — starting with a moat narrative, running the numbers, getting an
  uncomfortable value, and then quietly adjusting the story ("well, maybe the growth rate
  is actually 14% not 10%"). The story must drive the numbers; when the numbers are tweaked
  first and the story rewritten to match, the analyst is pricing, not valuing. The test:
  *can the story you told before running the numbers survive the numbers it produced?* If
  the numbers said intrinsic value is 30% below the market price and you find yourself
  re-telling the story to close the gap, you are selling, not analyzing.
- **Discount-rate gaming** — responding to a low intrinsic value by lowering the cost of
  capital. The CoC is an estimate of the firm's risk; lowering it because the output is
  inconvenient is the most common — and most invisible — form of valuation bias. Lock the
  CoC inputs (risk-free rate from the 10-year Treasury, ERP from Damodaran's latest survey,
  beta from a 2–5 year regression against a broad index) before running the DCF; change
  them only if the firm's risk profile has structurally changed, not if the valuation is
  not what you hoped.

> Worked template: `templates/default.microsoft.json` → `dcf_valuation.py` (the FCFF
> engine, fed adjusted moat-compounder inputs). Classifier & other archetypes: `SKILL.md`
> (Mode A step 2). Voice & numbers ledger: `references/report-voice.md`.
> The master lens source is Aswath Damodaran's published work — his blog (Musings on
> Markets), his books (*The Little Book of Valuation*, *Narrative and Numbers*,
> *Investment Valuation*), and his annual data updates at `pages.stern.nyu.edu/~adamodar`.
