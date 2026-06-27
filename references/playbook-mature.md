# Archetype playbook — Mature / declining / high-payout

How to value a business whose **growth is behind it** and whose worth lives in the
**cash it returns**, not the cash it reinvests. The default FCFF engine
(`scripts/dcf_valuation.py`) is the *right* engine here — but it is run inverted:
low or negative growth, a high-but-fading margin, almost no reinvestment, and a
terminal that decays rather than compounds. No single outside school owns this
ground; the discipline that does is **capital allocation and cash return**, drawn
from the quality-investing canon and from Buffett *only* on the narrow point that a
buyback creates value solely **below** intrinsic value.

> Uniform skeleton (shared by every archetype playbook): identify → why the default
> frame breaks → the right drivers → engine mapping → input-estimation deltas → bear
> checklist → master lens → self-check → traps. Method-first; numbers date, structure doesn't.

## 1. Identify (and the mis-classification trap)
Use this archetype when **the core business is flat-to-shrinking, the margin is
high but no longer expanding, reinvestment needs are minimal, and the firm throws
off more cash than it can sensibly redeploy** — so the cash goes out as dividends
and buybacks. The canonical cases: legacy packaged goods, wireline and incumbent
telecom, tobacco, mature industrials, late-cycle software with a declining seat
count, integrated names in structural runoff. The thesis is a *cash-return* story:
*how much does the runoff produce, how fast does it melt, and is the payout funded?*

**The trap that wrecks valuations — three lookalikes:**
- A **genuinely mature cash cow** has a structurally flat or declining top line,
  stable-to-eroding margins, and no credible reinvestment runway. Value it here.
- A **temporarily-stalled compounder** *looks* flat — a demand air-pocket, a product
  transition, a cyclical trough — but retains pricing power, a reinvestment runway,
  and a return on incremental capital well above its cost. Model that with the
  *young/growth* frame; pinning a 0% terminal on a paused compounder under-values it.
- A **value trap** is cheap because the decline is faster, more permanent, and more
  margin-destructive than the multiple admits — secular obsolescence, not a plateau.
  It is *not* this archetype run optimistically; it is the same engine with an
  honest (steeper) decline rate and a margin that breaks, not erodes.

The decisive test: *is the decline a plateau (a long, gentle fade with intact
margins) or a cliff (accelerating volume loss that takes pricing with it)?* The
first is investable at a discount; the second is the trap. Decline rate and margin
durability — not cheapness — sort the three.

## 2. Why the default four-driver FCFF frame breaks at the edges
The four drivers still apply — this *is* a discounted-FCFF valuation — but each is
pushed to the edge of its usual range, and the failure mode is the mirror image of
the growth case:
- **Growth is the wrong protagonist.** The instinctive error is to pencil in a
  "modest" positive growth rate because flat feels too pessimistic. A declining
  business compounded at +2% forever is a fiction; the honest path is *negative,
  then flattening*. Over-optimistic terminal growth is where these valuations die.
- **The terminal value is a *fading* annuity, not a growth perpetuity.** With
  `g ≈ 0` and a modest ROC, the terminal block shrinks relative to the explicit
  years. Value migrates **forward** into near-term cash, the inverse of the young
  archetype where 70–90% of value sits in the terminal.
- **Reinvestment turns negative.** Because revenue *falls*, `Δrevenue` is negative,
  so engine reinvestment `(Rev_t − Rev_{t−1}) / sales_to_capital` is **negative** —
  a working-capital *release*. A shrinking firm liquidates receivables and inventory
  and under-spends maintenance capex; that release **lifts** near-term FCFF above
  after-tax EBIT. Missing this understates the cash cow precisely where its value is.
- **Risk is low but not zero.** Cost of capital is low (stable cash flows, debt
  capacity), but the binding risk is *governance*, not operations: cash held by
  management with a shrinking core is cash at risk of being spent badly.

So the spine of the story is **PV of the cash returned over a melting revenue base**:
a large, front-loaded explicit block plus a small, decaying terminal. State that
sentence as the thesis — not a dividend yield, not a P/E.

## 3. The right drivers
| Driver | What it is | Where it sits in this archetype |
|---|---|---|
| **Revenue growth** | the melt rate | **negative then flattening** (e.g. −3% → 0%); the "melting ice cube" is the single most important input |
| **Operating margin** | profitability | **high but slowly eroding** (e.g. 30% → 28%) as scale and pricing fade; a *break* in margin, not a drift, signals the value trap |
| **Sales-to-capital** | reinvestment efficiency | **high** (2–3+); the firm barely reinvests, so growth capex is light and a shrinking base *releases* working capital → near-term FCFF > after-tax EBIT |
| **Cost of capital** | the hurdle | **low** (stable, predictable cash flows; real debt capacity), gliding modestly toward the mature-market average |
| **Terminal growth** | perpetual growth | **≈ 0** (often 0%); a declining business does not earn a positive growth perpetuity — assuming one is the cardinal sin |
| **Terminal ROC** | quality of the steady state | **modest, above the cost of capital** (e.g. 9% vs 7.5%) — a small, durable excess return, not a compounding machine |
| **Payout (div + buyback)** | how cash leaves | the residual of light reinvestment; high *because* growth is scarce — its **funding** (FCF, not debt) is the live question |

The value is **PV(near-term FCFF on a melting base) + PV(a small fading terminal)**,
with the payout judged on whether it is funded and whether buybacks are struck
below intrinsic value. Make *that* the thesis, not the headline yield.

## 4. Engine mapping → `dcf_valuation.py`
Same two-stage FCFF model as every non-financial archetype; the inputs encode
decline:
- `revenue_growth`: a **flat-to-negative** path, e.g.
  `[-0.03, -0.03, -0.02, -0.02, -0.01, -0.01, 0.0, 0.0, 0.0, 0.0]` — declining, then
  flattening. Do **not** let it turn positive without a story that contradicts the
  "mature" classification.
- `base_operating_margin` → `target_operating_margin`: a high base gliding *down*
  (30% → 28%) via `margin_convergence_year`; the engine glides the margin linearly.
- `sales_to_capital`: **high** (2.5+) so growth capex is minimal. Because the
  revenue path *declines*, the engine's `reinvestment = Δrevenue / sales_to_capital`
  is **negative** in the shrinking years — a working-capital release that *adds* to
  FCFF. This is correct and intended: it is why a melting business still gushes cash.
- `terminal_growth`: **0.0** (or a whisker above). `terminal_roc` modest but above
  `cost_of_capital_terminal` (9% vs 7.5%) so the terminal reinvestment rate
  `g/ROC` is near zero and terminal FCFF ≈ after-tax terminal EBIT.
- `cost_of_capital_initial/terminal`: **low** (8% → 7.5%), reflecting stable cash
  flows; `cash`/`debt` carry a heavier debt load against those flows.

```bash
cd scripts
python dcf_valuation.py ../templates/mature.example.json          # value/share, terminal share
python dcf_valuation.py ../templates/mature.example.json --json   # for charts.py / programmatic use
```

The worked template reproduces **value/share ≈ $64.61 vs a ~$58 price** — modestly
undervalued — with the **terminal value ≈ 47% of operating value**. That 47% is the
tell: in a growth name the terminal is 70–90%; here near-term cash *dominates*
(PV of explicit FCFF ≈ $71.2B vs PV of terminal ≈ $62.1B). The near-term block is
large precisely because the declining base releases working capital and the margin
is still high — the value is the cash collected *soon*, while a fading terminal
contributes under half. If a mature-company model shows an 80%-terminal split, the
inputs have smuggled in growth that the "mature" label denies.

## 5. Input-estimation deltas (what changes here)
- **Estimate the decline rate, then defend it.** This is the highest-leverage input
  and the easiest to fudge. Anchor it to *volume* trends (units, subscribers, cases
  shipped), not revenue dollars, which price increases can mask. Split the question:
  is the top line falling on **volume** (structural) or holding on **price**
  (a clock running out as elasticity bites)? Pricing power that backfills volume
  decline is finite — model it fading.
- **Separate maintenance from growth capex.** A mature firm's reported capex is
  mostly **maintenance** (sustaining the existing base), not growth. Maintenance
  capex is a true cash cost and must stay in FCFF; only the (small) growth capex
  scales with revenue. The engine's light reinvestment assumes this split — verify
  it against depreciation: maintenance capex roughly tracks D&A for a steady-state
  base, and capex chronically *below* D&A is a firm quietly harvesting its assets.
- **Margin erosion vs margin break.** A gentle 1–3 point glide is normal as scale
  and mix fade. A *break* — fixed-cost deleverage as volume falls, a price war,
  input-cost pass-through failing — is the value-trap signature and belongs in the
  bear case, not the base case.
- **Durability *and funding* of the payout.** Compute the payout (dividends +
  buybacks) as a fraction of **FCF**, not of EPS. A payout ratio under ~1.0× of FCF
  is self-funding and durable; a payout *exceeding* FCF is being financed by debt or
  balance-sheet drawdown and will be cut — model the cut, not the promise.
- **Debt capacity against stable cash flows.** Mature cash flows support more
  leverage, so the balance sheet legitimately carries more debt — but that debt has
  to be *serviced and refinanced*. Map the maturity wall against the (declining)
  cash flows; rising rates plus a melting top line is how a "safe" payer is forced
  to choose between the dividend and the refinancing.

## 6. Bear checklist + leading indicators (Munger: invert + incentives)
The central agency problem here is structural: **management runs a shrinking core
while sitting on a growing cash pile.** Invert the incentive. The empire-builder's
instinct is to *not* return the cash — to "buy growth" through a transformational
acquisition or a value-destroying diversification, because a bigger, growing empire
flatters compensation and ego where a managed decline does not. The bear case is
therefore as much about *what management does with the cash* as about the business:
1. **Decline accelerates** → unit/subscriber/volume trend turning steeper, not
   gentler; pricing power exhausted. *The melt outruns the model.*
2. **Margin breaks** → fixed-cost deleverage as volume falls; the high margin was
   load-bearing and it gives way. Watch gross margin and incremental margins.
3. **Payout is unfunded** → dividends + buybacks running *above* FCF; the dividend
   is now financed by debt or asset sales. A payout cut is the eventual tell.
4. **Debt maturity wall** → near-term maturities large versus declining cash flow;
   refinancing at higher rates competes directly with the distribution.
5. **Empire-building M&A (the Munger incentive flag)** → a "transformational"
   acquisition or a diversification into an unrelated, higher-growth field, paid for
   with the cash that should have been returned. Invert: management is *rewarded*
   for size and growth, *not* for shrinking gracefully and handing cash back — so
   the default expectation is value-destroying redeployment. A deal announced at a
   premium to "pivot to growth" is the classic incentive-caused misjudgment.
6. **Buybacks struck *above* intrinsic value** → repurchasing at any price to shrink
   the share count destroys value per share; it is the agency problem wearing the
   costume of shareholder return.

Leading indicators to track, each cracking before the thesis: payout-vs-FCF
coverage, the debt-maturity schedule, the volume-decline slope, and any
transformational-acquisition announcement.

## 7. Master lens — capital allocation / cash return (operational moves)
No single guru owns this archetype cleanly. The discipline is **capital
allocation**, and the one Buffett principle that applies — narrowly — is that a
buyback is value-accretive **only below intrinsic value**. Operational moves:
- **Value the runoff honestly.** Treat the business as a melting annuity: estimate
  the decline rate, let the margin erode, and take the PV of the cash it actually
  produces. Do not dress a declining base in a growth perpetuity to make the
  terminal carry the valuation — the value lives in the near-term cash.
- **Judge buybacks by price versus value, not by share-count reduction.** A buyback
  below intrinsic value transfers wealth to continuing holders; *above* value it
  destroys it. The right question is never "is the company returning cash?" but "is
  it retiring shares at a discount to what they are worth?" Management that buys back
  indiscriminately at any price is allocating capital badly, full stop.
- **Stress the "melting ice cube" decline rate.** The conclusion must survive a
  steeper decline. Re-run with a faster melt and an earlier margin break; if a
  modest change in the decline rate flips under/overvalued, the thesis rests on the
  one number that is hardest to know. Robustness over precision.
- **Weigh breakup / liquidation value as a floor.** A mature firm is often worth
  more in parts — divestible segments, owned real estate, brands, a securities
  portfolio. Estimate the sum-of-the-parts or orderly-liquidation value as a *floor*
  under the going-concern DCF; when the market price sits below that floor, the
  downside is bounded by assets, not by the melt. (For a true conglomerate, hand the
  parts to the SOTP lens.)

## 8. Self-check gate (before publishing a mature/declining report)
- [ ] The **decline rate is explicit and defended** from volume trends, not assumed
      flat or smuggled positive — the melt is the load-bearing input.
- [ ] The **dividend and buyback are funded from FCF**, not from debt or
      balance-sheet drawdown; payout-vs-FCF coverage is stated.
- [ ] **Terminal growth is not over-optimistic** — `g ≈ 0` for a declining base; the
      terminal is a *fading* annuity and its share of value is modest (here ~47%),
      not the 70–90% of a growth name.
- [ ] **Buybacks are judged against intrinsic value** (accretive only below it), not
      praised for shrinking the share count at any price.
- [ ] A **breakup / liquidation floor** is estimated and compared to price, bounding
      the downside.
- [ ] Maintenance capex is **kept in FCFF**; the negative-reinvestment (working-
      capital release) is real, not an artifact.
- [ ] A **margin-of-safety band** is given by stressing the decline rate and the
      margin break — the conclusion holds across the band, not just at the point.

## 9. Common traps
- **Assuming perpetual modest growth for a declining business.** Penciling +2%
  terminal because flat "feels harsh" inflates the terminal value and the whole
  valuation. The honest path is negative-then-flat, `g ≈ 0`.
- **Ignoring the melting ice cube.** Treating a flat year as permanent and missing
  that the base shrinks each year; the decline rate compounds against the holder.
- **Trusting an unfunded payout.** Reading a fat dividend yield as safe without
  checking it against FCF; a distribution financed by debt is a cut waiting to
  happen, and the yield is a mirage.
- **Rewarding "growth" M&A that destroys value.** Crediting a transformational
  acquisition as a re-rating catalyst when the incentive-driven base case is
  value-destroying redeployment of cash that should have been returned.
- **Buying back above intrinsic value.** Counting any buyback as shareholder-
  friendly; repurchases struck above value reduce value per share.
- **Missing the value trap.** Mistaking a cliff for a plateau — calling a structurally
  obsolescing business "cheap" when the decline is accelerating and the margin is
  about to break. Cheapness is not a thesis; an honest decline rate is.

> Worked template: `templates/mature.example.json` → `dcf_valuation.py`
> (≈ $64.61/share vs ~$58 price, terminal ≈ 47% of value — near-term cash dominates).
> Classifier & other archetypes: `SKILL.md` (Mode A step 2). Voice & numbers ledger:
> `references/report-voice.md`.
