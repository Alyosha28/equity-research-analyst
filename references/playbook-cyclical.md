# Archetype playbook — Cyclical / commodity (price-takers)

How to value a business whose earnings are a **derivative of a commodity price it does
not set**: miners, steel, oil & gas E&P, chemicals, pulp & paper, memory chips,
shipping, refiners. The FCFF engine is *right* here — the same `scripts/dcf_valuation.py`
the default archetypes use — but it is lethal if fed **current** margins and **spot**
revenue. The whole discipline is to feed it **through-cycle normalized** inputs. Embeds
the school that owns cycle placement: **Ray Dalio on the economic machine and the
business / debt cycle** (operational, not as a portfolio theory).

> Uniform skeleton (shared by every archetype playbook): identify → why the default
> frame breaks → the right drivers → engine mapping → input-estimation deltas → bear
> checklist → master lens → self-check → traps. Method-first; numbers date, structure doesn't.

## 1. Identify (and the mis-classification trap)
Use this archetype when the firm is a **price-taker on a traded commodity**: its
realized price is set by a global/regional clearing market, not by the company, and its
margin therefore swings with that price across a multi-year cycle. Tells: revenue ≈
volume × an exchange-quoted price; gross margin oscillates 2–4× peak-to-trough; the
product is fungible (one producer's copper cathode ≈ another's).

**The trap that wrecks valuations:** *cyclical demand is not the same as commodity
price-taking.* Many quality compounders have demand that rises and falls with the cycle
yet keep **pricing power** through it — they set price, pass through input costs, and
defend a stable margin. A copper miner takes the LME price; an industrial that sells
copper-bearing equipment under a brand, with switching costs and a service annuity, has
a moat and a *durable* margin. Mis-label the second as the first and you normalize away
real excess returns; mis-label the first as the second and you capitalize a peak that
the next cycle erases. Test: *if the commodity price halved, does the firm's unit margin
collapse (→ this playbook) or hold because it controls price (→ default FCFF, with a
genuine moat and terminal excess return)?* A refiner is a price-taker on the crack
spread; a branded consumer staple that uses the same feedstock is not.

## 2. Why the default frame breaks for cyclicals
The four-driver FCFF model is structurally fine; the **inputs analysts reach for** are
the killer. Two specific errors recur:
- **Current-margin extrapolation.** The model glides from `base_operating_margin` to
  `target_operating_margin`. If you set those to *today's* margin, you bake the current
  point of the cycle into perpetuity. At a peak that means valuing 30%+ margins forever
  for a business that averages 20%; at a trough it means writing off a viable producer
  on a 10% margin it will not stay at. Either way the terminal value — which dominates —
  inherits the wrong number. **The single biggest mistake in commodity valuation is
  valuing at the current margin instead of the through-cycle margin.**
- **Spot-price revenue paths.** Building the revenue line off the *spot* commodity price
  (or, worse, off a forward curve that the model treats as a forecast) couples every
  forecast year to a number that is itself the most mean-reverting series in finance.
  Spot is noise; the cycle is the signal. A revenue path anchored to spot will be peak-
  heavy at the top and capitulatory at the bottom — exactly backwards for a mean-
  reverting asset.

So the default DCF stays, but every driver is re-expressed in **normalized, mid-cycle**
terms, and the burden of the work moves *upstream* into estimating the cycle average.

## 3. The right drivers
Same four FCFF drivers as the default engine, each **fed with a normalized input** and
read through the cycle rather than the quarter:

| Driver | Default reading | Cyclical (normalized) reading |
|---|---|---|
| **Revenue growth** | TAM × share, declining | **Volume/capacity growth × a price deck**, not spot. Real-price *drift* (toward marginal cost), not a price *forecast* |
| **Operating margin** | base → target glide | **Through-cycle (mid-cycle) margin** as both base and target — the average across a full peak-to-trough, not today's print |
| **Reinvestment (sales-to-capital)** | revenue per $ capital | Capital-heavy: low sales-to-capital; **split maintenance vs growth capex** — sustaining the resource base is not growth |
| **Risk (cost of capital)** | riskfree + β·ERP | **Higher β and CoC** — operating + commodity leverage makes equity volatile; price-takers earn no premium for taking price |
| **Terminal ROC** | durable excess if moat | **Mid-cycle ROC ≈ cost of capital** — a commodity rarely sustains excess returns; a thin, defensible spread at most |

The thesis sentence is not a multiple; it is: *the normalized mid-cycle earnings power,
discounted at a cost of capital that respects the volatility, is worth $X — and the
price is embedding [peak / trough / mid] economics.*

## 4. Engine mapping → `dcf_valuation.py` (normalized inputs)
Reuse the FCFF engine unchanged; the discipline is entirely in the JSON. Set the
operating-margin pair to the **through-cycle** margin so the glide converges on the
*average*, not the peak, and build the revenue path from **price-deck × volume**, not
spot:

```bash
cd scripts
python dcf_valuation.py ../templates/cyclical.freeport.json          # value/share, terminal share
python dcf_valuation.py ../templates/cyclical.freeport.json --json    # for charts.py / programmatic use
```

Mapping for a commodity name (see `templates/cyclical.freeport.json`):
- `base_operating_margin` / `target_operating_margin` → **both anchored to the mid-cycle
  margin** (Freeport: 22% now → 25% mid-cycle target; a copper miner swings ~10–35%, so
  the point is to value the ~25% average, not the 35% peak). `margin_convergence_year`
  pulls a depressed or elevated *current* margin back to the normalized one early.
- `revenue_growth` → **volume growth + a normalized real-price drift** that declines to
  terminal. Freeport's path runs 6% → 2.5% off a ~$25B base: copper volume plus a modest
  through-cycle price drift, *not* a spot extrapolation.
- `sales_to_capital` low (Freeport 0.55) — mining/heavy industry consumes capital.
- `terminal_roc` ≈ `cost_of_capital_terminal` (Freeport: 10% ROC over an 8.5% terminal
  CoC — a thin durable spread, the most a price-taker should claim).
- `cost_of_capital_initial` elevated (Freeport 10%) for commodity + operating leverage.

Worked anchor: those inputs reproduce **value/share ≈ $31.77 vs the ~$42 price — about
24% downside on normalized earnings — with terminal value ≈ 63% of operating value.**
The gap is the cycle: at $42 the market is paying for economics nearer the peak than the
mid-cycle average the DCF assumes.

**Reverse-DCF cross-check (the key one here).** Run `reverse_dcf.py` on the same name and
ask the cyclical-specific question: *what margin / price does the current price imply, and
is that a peak or a trough number?* If solving the market price back through the engine
requires a margin at or above the historical peak (or a commodity price above the prior
cycle high), the market is capitalizing the top of the cycle; if it implies a margin below
the trough, the market is pricing distress. That single check reframes "expensive/cheap"
as "which point of the cycle is priced in" — the only framing that means anything for a
mean-reverting asset.

## 5. Input-estimation deltas (normalizing across the cycle)
- **Normalize the margin across a full cycle.** Take at least one complete peak-to-trough
  (often 7–10+ years; commodity cycles are long) and use the **average** operating margin,
  not the trailing one. Where history is short or distorted, normalize bottom-up: mid-
  cycle price − the firm's unit cash cost − D&A. Feed that single number into *both*
  `base_operating_margin` and `target_operating_margin`. If the current margin is far from
  it, set `base` to current and let `margin_convergence_year` glide to the normalized
  `target` within a year or two — do **not** leave the peak/trough margin running to
  terminal.
- **Build a price deck, not a spot print.** The defensible long-run anchor is the
  **marginal cost of production** — the all-in incentive price of the highest-cost
  producer needed to clear forecast demand (the top of the **cost curve**). Over a cycle,
  price oscillates around that marginal cost: it cannot stay far below for long (high-cost
  supply shuts in) or far above (new capacity arrives). Use that marginal-cost level as the
  through-cycle deck, with a modest real drift, rather than today's quote or the futures
  strip. State the deck as an explicit number ($/lb, $/bbl, $/ton) so it can be argued with.
- **Inventory and working-capital swings.** Commodity producers see large inventory and
  receivable swings across the cycle; a trough builds working capital that a recovery
  releases. Normalize working-capital intensity to mid-cycle rather than letting a single
  year's swing distort sales-to-capital or near-term FCFF.
- **Maintenance vs growth capex.** Heavy industry must spend just to hold output (sustaining
  capex, reserve replacement, stay-in-business spend). Only capex *beyond* maintenance is
  growth. Confusing the two understates required reinvestment and overstates free cash —
  set `sales_to_capital` so that maintenance is implicitly covered and growth capex earns
  the volume in the revenue path.

## 6. Bear checklist + leading indicators (Munger: invert; watch incentives)
Each vector paired with the leading indicator that **turns first**:
1. **The capital cycle (the central one) — incentive flag, Munger.** Management is
   *rewarded* for growth and is flush with cash exactly at the **peak**, so the industry
   approves capacity at the top, that capacity arrives into the next downturn, and the
   added supply caps the recovery. Invert: *what does the return look like if everyone
   builds at once?* — and watch **industry-wide capacity additions / capex announcements**.
   When the whole sector is sanctioning new mines/plants, the cycle is late. This is the
   classic capital-cycle misjudgment; the incentive (grow-at-the-top) causes it.
2. **Inventory & spot price** → rising inventories and a rolling-over spot price lead the
   margin down before reported earnings show it.
3. **Cost-curve position** → where the firm sits on the industry cost curve sets who
   survives the trough; a high-cost producer bleeds first. Falling toward the firm's own
   cash cost is the warning line.
4. **Demand proxy** → the end-market driver (construction/credit, auto, electrification,
   industrial production) tied to the price deck — a credit-driven slowdown in the demand
   proxy precedes price weakness.
5. **Balance-sheet survival** → net debt / through-cycle EBITDA: a commodity firm dies at
   the trough from leverage, not from a bad average. Can it fund maintenance capex and
   service debt at the **trough** price, not the mid-cycle one?

## 7. Master lens — Ray Dalio (the economic machine; operational, not quotes)
Dalio is **not a single-stock valuer**, and this lens does not pretend otherwise. His
contribution here is narrow and specific: **placing the cycle so the normalization point
is honest.** Keep it to that; do not drift into macro portfolio construction.
- **(a) Cycle placement → the normalization point.** Locate where the asset sits in the
  **short-term business cycle** (the 5–10 year demand swing) *and* the **long-term debt
  cycle** (the multi-decade build-up and deleveraging of credit). Late in a credit
  expansion, demand and prices run hot and "normal" looks high; in a deleveraging, they
  run cold and "normal" looks low. The placement is what tells the analyst whether today's
  margin is above or below mid-cycle — i.e. it *sets the normalization point* that drivers
  3 and the price deck feed. This is the whole reason Dalio is the master lens for this
  archetype: he disciplines the single most important cyclical input.
- **(b) The price deck as the expression of through-cycle demand.** Demand for a commodity
  is downstream of **credit and capex** in the economic machine — construction, autos, and
  capacity-building are credit-financed. The through-cycle price deck (§5) is the way that
  credit/capex-driven demand enters the valuation: anchor it to where demand sits over a
  full debt-and-business cycle, not to the current quarter's spot.
- **(c) "What's already discounted" ≈ the reverse-DCF.** Dalio insists the question is not
  what *will* happen but what the price *already embeds*. That is exactly the §4 reverse-DCF
  cross-check: solve the price back through the engine and read whether it is pricing peak
  or trough economics. Use the reverse-DCF as the operational form of "what's discounted in".
- **(d) Stay in the lane.** This is single-stock intrinsic valuation. Use cycle placement
  and the normalization point; do **not** import risk-parity, macro allocation, or
  all-weather portfolio theory — they answer a different question than "what is this
  company worth."

## 8. Self-check gate (before publishing a cyclical report)
- [ ] Margins are **normalized through-cycle**, not the current (peak or trough) print —
      both `base` and `target` reflect the mid-cycle average.
- [ ] A **price deck** is stated as an explicit number and defended against the commodity's
      long-run **marginal cost** — not lifted from spot or the forward strip.
- [ ] The **cycle position is named** (early / mid / late; where in the debt cycle) and the
      normalization point follows from it.
- [ ] **Terminal ROC ≈ cost of capital** — no perpetual excess return assumed for a
      price-taker (a thin durable spread at most).
- [ ] **Maintenance vs growth capex** separated; sustaining spend is not counted as growth.
- [ ] The **reverse-DCF** is run and reported as a **peak/trough framing** ("the price
      implies a margin of X%, which is the [peak / mid / trough]").
- [ ] A **margin-of-safety band** is given around the normalized value (cyclicals deserve a
      wide band — see `monte_carlo.py` over margin and the price deck).
- [ ] The final report follows `references/publishing-contract.md`: it states the
      cycle position, current vs normalized vs peak/trough margin, price deck,
      cost-curve/capacity position, and reverse-DCF implied cycle point in the
      report language.

## 9. Common traps
- **Peak-margin extrapolation** — running the current top-of-cycle margin to terminal, so
  the dominant terminal value capitalizes a number the next cycle erases.
- **Spot-price revenue** — anchoring the revenue path to the spot commodity price (or
  treating the futures curve as a forecast) instead of a through-cycle price deck.
- **Ignoring the capital cycle** — missing that the whole industry adds capacity at the top;
  valuing one firm's growth while the sector's combined supply is about to cap the price.
- **Treating a commodity as a compounder** — assigning a durable moat and a perpetual excess
  return (terminal ROC ≫ CoC) to a price-taker that has neither. The mirror error is also a
  trap: normalizing away a genuine pricing-power business as if it were a price-taker.
- **Trough capitulation** — writing off a low-cost, well-financed producer on trough
  economics, the symmetric error to peak extrapolation and just as costly.

> Worked template: `templates/cyclical.freeport.json` → `dcf_valuation.py` (the same FCFF
> engine, fed normalized inputs). Classifier & other archetypes: `SKILL.md` (Mode A step 2).
> Voice & numbers ledger: `references/report-voice.md`.
