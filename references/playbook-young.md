# Archetype playbook — Young / pre-profit high-growth

How to value a business that has **no past worth extrapolating and a future that is
almost entirely terminal**. The FCFF engine still applies — this archetype *reuses*
the default `scripts/dcf_valuation.py` — but it leans on two features the mature case
ignores: the **failure branch** (`failure_probability`, `failure_value_per_share`) and
the **base→target margin glide** out of negative territory. The one school that owns
this ground is **Damodaran's "dark side of valuation"**: value the company as an
*expected value across survival and failure*, not as a multiple of a number it does
not yet have.

> Uniform skeleton (shared by every archetype playbook): identify → why the default
> frame breaks → the right drivers → engine mapping → input-estimation deltas → bear
> checklist → master lens → self-check → traps. Method-first; numbers date, structure doesn't.

## 1. Identify (and the mis-classification trap)
Use this archetype when the company is **early in its life, scaling fast, and not yet
profitable** — losses are by design (customer acquisition, capacity ahead of demand,
R&D ahead of revenue), the share count is still inflating, and the investment case is a
claim about a future the financials have not reached: high-growth SaaS pre-breakeven, a
platform burning to buy a market, a clinical-stage or pre-revenue hardware story, a
recently-listed disruptor.

**The trap that wrecks valuations** is mis-reading *why* the earnings are negative.
Three companies can show the same current loss and need three completely different
treatments:
- A **genuine young/pre-scale** company — losses shrink as revenue scales over an
  operating base that is *widening*; unit economics improve with volume; there is a
  credible, datable path to a positive margin. → *this playbook.*
- A **mature company having a bad year** — it has a long history of positive margins
  and a loss driven by a cyclical trough, a one-off charge, or a temporary shock. The
  anchor is its own *normalized* earnings power, not a hockey-stick. → default FCFF on
  a normalized margin, or the cyclical/turnaround handling — **not** this playbook.
- A **permanently-unprofitable broken model** — it has scaled and the losses did *not*
  compress; incremental units do not move the contribution margin toward positive. The
  "path to margin" never crosses. → there may be no going-concern value to anchor; the
  honest output is closer to the failure branch alone.

Test: *do the unit economics improve with scale, and is there a dated path to a
positive margin (→ this playbook), or is the loss either temporary on a profitable base
(→ mature/cyclical) or structural after scale (→ broken model)?* Youth is a stage, not
a synonym for "lossmaking".

## 2. Why the default four-driver FCFF frame breaks
The four drivers still apply, but the **two anchors a mature valuation leans on are
missing**, and that changes where the value comes from:
- **There is no meaningful current earnings or margin to anchor on.** The mature case
  starts from a normalized EBIT margin and adjusts it. Here the current margin is
  *negative* and *uninformative* — it reflects deliberate front-loaded spend, not
  steady-state economics. Anchoring on trailing margin (or worse, a trailing P/E) is
  meaningless when the denominator is a loss.
- **Current losses are not the signal; the *path* is.** The whole case is a claim about
  *when and how* losses turn — the slope from a negative base margin to a positive
  target, and the year it converges. Value is dominated by years that have not happened.
- **The value is almost entirely in a distant, uncertain terminal.** Because near-term
  FCFF is *negative* (after-tax operating income is negative while reinvestment is still
  consuming cash to fund growth), the explicit-period PV is **negative**, and the
  terminal value carries *more than 100%* of operating value. In the worked template the
  PV of explicit FCFF is **−$584M** and PV(terminal) is **$8,033M** — so terminal is
  **108% of operating value**. This is not an engine error; it is the diagnostic
  **signature** of a young company. A mature company's terminal is typically 50–70% of
  value; when it punches *through* 100%, the model is telling you the business has not
  yet earned a dollar of the value you are ascribing to it. Read the number as a risk
  gauge, not a glitch — the higher above 100%, the more the thesis rides on survival and
  the further out the payoff sits.

So value the company as an **expected value**: a probability-weighted blend of a
going-concern DCF (which itself is terminal-heavy) and a distress outcome — *not* a
single forward multiple applied to a far-future earnings number.

## 3. The right drivers
| Driver | What it is | Decomposes into |
|---|---|---|
| **Path to target margin** | *the crux of the case* | base (negative) margin → target margin, and the **year it converges**; the slope is the operating-leverage story |
| **Revenue scaling toward a TAM** | the size of the prize | TAM growth × a defensible, *rising-then-settling* market share; growth high early, declining toward the riskfree rate |
| **Survival probability** | the gate on everything | 1 − failure probability; bond-rating / cash-runway based — value only accrues to the firm if it lives to collect it |
| **Reinvestment to fund growth** | what the burn buys | ΔRevenue ÷ sales-to-capital; early years it *exceeds* operating cash, which is why FCFF is negative |
| **Cost of capital (fading)** | the hurdle, today elevated | high in the growth phase (small, single-product, cash-burning, illiquid), gliding down as the company de-risks and matures |
| **Terminal economics** | where the value lives | terminal growth ≤ riskfree, terminal ROC > g; this is 100%+ of value, so stress it hardest |

Make the thesis the sentence: *PV of a probability-weighted path to a target margin over
a scaling revenue base, gated by survival* — not "trades at N× 2030 earnings".

## 4. Engine mapping → `dcf_valuation.py` (reuses the default FCFF engine)
No separate script. The default two-stage FCFF engine handles youth through three input
moves the mature case leaves idle:
1. **Negative base margin gliding to a positive target.** Set `base_operating_margin`
   **negative** and `target_operating_margin` positive, with a realistic
   `margin_convergence_year`. The engine's `_linear_to_target` walks the margin up year
   by year — in the template, −15% → +20% reaching target at **year 7** (so years 1–4
   are still negative-to-breakeven, and FCFF stays negative until the cross). The
   convergence year *is* the operating-leverage thesis; do not bury it.
2. **Effective tax ramps from zero to marginal.** Set `effective_tax_rate = 0` while
   lossmaking (no tax shield is modeled, no fictitious tax on losses), with
   `tax_convergence_year` near the margin cross so the effective rate ramps to the
   marginal `tax_rate` exactly as real profits — and cash taxes — arrive. (NOL carry-
   forwards realistically delay cash tax further; if material, push the convergence out.)
3. **The failure branch — the move that makes this archetype honest.** Set
   `failure_probability` and `failure_value_per_share` so the engine returns
   `vps = (1−p)·going_concern + p·distress`. In the template p = 0.25 with a ~$2/share
   distress value: the going-concern DCF alone is far higher, but probability-weighting a
   one-in-four wipeout drags value/share to **$16.34**. Without this branch you would be
   valuing only the worlds in which the company *succeeds* — survivorship bias baked into
   the spreadsheet.

```bash
cd scripts
python dcf_valuation.py ../templates/young.example.json          # value/share, terminal %, the negative-FCFF table
python dcf_valuation.py ../templates/young.example.json --json   # for charts.py / programmatic use
```
This prints the signature directly: early FCFF rows **negative**, PV of explicit FCFF
**−$584M**, terminal **108% of operating value**, value/share **$16.34** (going-concern
before the failure weighting is higher; the printed per-share is already failure-adjusted).

**Monte Carlo matters MOST here.** Uncertainty is not a footnote — it is the asset. A
point estimate of $16.34 hides that the inputs carrying the result (the margin
convergence year, terminal margin, TAM/share, and the failure probability itself) each
have wide, fat-tailed ranges. Run `scripts/monte_carlo.py` and **report the
distribution, not the point** — the percentile band is the deliverable, and the price's
percentile in that band is the decision. A young company quoted as a single number is
mis-stated by construction.

## 5. Input-estimation deltas (what changes vs the mature case)
- **Size the TAM, then defend a share — do not assume either.** Build revenue bottom-up
  (TAM × share), sizing the addressable market and assigning a share path that *rises*
  as the company wins, then *settles* as the market matures and competition arrives.
  "Captures 30% of a $X00B market" is a hypothesis to be probability-weighted (see §7),
  not a given. The discipline is forcing the story to confront the size of the prize.
- **Estimate the path to margin from unit economics or comparable maturation.** The
  convergence year is the highest-leverage single input. Ground it: decompose
  contribution margin from real unit economics (does gross margin × scale cover fixed
  opex at the modeled revenue?), or anchor on how *comparable* companies matured —
  how many years from this revenue scale to the target margin, for businesses with
  similar cost structure. A target margin must be reachable from today's cost base by an
  identifiable mechanism (operating leverage, mix shift, pricing power), not asserted.
- **Set the failure probability the way Damodaran does** — from a **synthetic bond
  rating / cash-runway** read, not a gut number. Map the company's interest coverage,
  leverage, and liquidity to an implied rating, take the empirical cumulative default
  rate for that rating over the horizon, and use it as `failure_probability`. A pre-
  profit, cash-burning firm often maps to deep-junk default odds — be willing to write
  20–40% rather than a comfortable single digit.
- **Cash runway vs burn is the survival clock.** Compute months of runway = cash ÷
  monthly burn, and test it against the modeled year of breakeven. If runway ends
  *before* FCFF turns positive, the company *must* raise — which means either dilution
  (model it; see §6) or a higher failure probability. The going-concern DCF silently
  assumes the firm survives to the margin cross; runway is what tells you whether that
  assumption is funded.
- **Elevated, fading cost of capital.** Start the cost of capital high — small,
  single-product, illiquid, cash-burning firms carry more risk than the mature-market
  average — and glide it down (`coc_glide_start_year`/`end_year`) as the company de-risks:
  scale, diversification, positive cash flow, and access to cheaper capital all compress
  the hurdle. The template runs 12% → 9%.

## 6. Bear checklist + leading indicators (Munger: invert + watch incentives)
**Invert: ask what kills it, then watch the metric that cracks first.** And weigh the
incentive: *founders and VCs are paid to project hockey-sticks* — the people supplying
your growth assumptions profit from your believing them. The base rate for young-company
projections is optimism; discount accordingly.
1. **Cash burn outruns runway** → months of runway vs the modeled breakeven year; the
   *trend* in monthly burn. Runway shrinking faster than losses narrow is the tell.
2. **The funding window shuts** → financing climate and the company's own access (down-
   rounds, pulled raises, rising cost of new money). A model that *assumes* the next
   round closes is one capital-market freeze from the failure branch.
3. **Unit economics never cross** → contribution margin and payback period *by cohort*.
   If newer cohorts are not more profitable than older ones, the "path to margin" is a
   line on a chart with no engine under it — the broken-model case in disguise.
4. **Customer / revenue concentration** → revenue share of the top handful of customers;
   net revenue retention. One whale leaving can erase a year of "growth".
5. **Key-person risk** → dependence on a founder/visionary; depth of the bench. Young
   companies are often one person's conviction; price the discontinuity.
6. **Dilution (incentive flag, Munger)** → fully-diluted share count *trend*, SBC as a
   % of revenue, and the terms of each raise. Management is rewarded on growth and is
   *incentivized to spend (and issue equity) to chase it*; your per-share value bleeds out
   through a share count that keeps climbing even as the business "succeeds". Invert and
   ask what your stake is worth after the dilution required to fund the plan.

## 7. Master lens — Damodaran's "dark side of valuation" (operational moves)
This archetype has no second outside guru; the authority is Damodaran's framework for
exactly the hard case — young, declining, distressed, and otherwise un-anchorable firms.
Do **not** import Buffett's "circle of competence pass" or Dalio's regime overlay here —
the discipline is to value the un-valuable, not to refuse it. Operational moves:
- **Value as expected value across survival and failure.** A going-concern DCF answers
  "what is it worth *if it makes it*?"; the value is that, *times survival*, plus distress
  *times failure*. The failure branch is not a haircut bolted on at the end — it is half
  of the definition of value for a company that might not exist in five years.
- **The 3P discipline — possible / plausible / probable.** Any input can be argued
  *possible*. Demand that the numbers you actually use are *probable*: a TAM share that
  competitors and capacity make defensible, a margin reachable by an identified mechanism,
  a growth rate that decays toward the riskfree rate rather than compounding forever.
  "Possible" is where hockey-sticks live; "probable" is where value lives.
- **Narrative discipline — a probability-weighted story, not a hockey-stick.** Write the
  story, then weight it. The honest output is "in the world where it captures the market
  it is worth A, where it muddles B, where it fails ~$2 — weighted, $16.34", not "it is
  the next [winner], so $A". Refusing to estimate does not remove the uncertainty; it
  just lets an arbitrary premium fill the vacuum.
- **Widen Monte Carlo variance on the drivers that carry the result.** Don't simulate
  every input with the same timid spread. Put the *wide* distributions on the few that
  move value most — terminal margin, the margin-convergence year, TAM/share, and the
  failure probability — and let the simulation show how fat the tails really are. The
  conclusion should survive the simulation, not just the point estimate.

## 8. Self-check gate (before publishing a young-company report)
- [ ] Is the **path to margin explicit and dated** — base margin, target margin, and the
      convergence year stated, with a mechanism (not just a slope)?
- [ ] Is a **survival / failure probability stated and weighted** into the per-share
      value (failure branch on, not p = 0), and grounded in rating/runway?
- [ ] Is **terminal > 100% of value explained** as the young-company signature (negative
      explicit FCFF), not left looking like an error or quietly capped?
- [ ] Is the **Monte Carlo distribution reported** — a percentile band and the price's
      percentile — rather than a single point estimate?
- [ ] Is **TAM × share probability-weighted**, not assumed — the share path defended, and
      the "what if it's half that" case priced?
- [ ] Is the **margin of safety band** stated, sized to the (large) uncertainty — and is
      **dilution / cash runway** reflected in the per-share number?

## 9. Common traps
- **Linear (or compounding) revenue forever.** Extrapolating the current growth rate
  past the point any market can absorb; growth must decay toward the riskfree rate, and
  share toward a ceiling competition enforces.
- **Ignoring failure and dilution.** Valuing only the worlds where it works (failure
  branch off) and on today's share count (no dilution) — double survivorship bias that
  systematically overvalues the young company.
- **Valuing on a multiple of far-future earnings.** "20× 2032 EPS, discounted back"
  smuggles in a terminal assumption while hiding the survival question and the path that
  has to be true to reach those earnings at all. Run the FCFF with the failure branch
  instead.
- **Mistaking narrative for probability.** A vivid, *possible* story is not a *probable*
  number. The hockey-stick is the default failure mode of this archetype — every input
  argued at its optimistic edge, none weighted. Discipline the story with the
  distribution.

> Worked template: `templates/young.example.json` → `dcf_valuation.py` (value/share
> ≈ $16.34, terminal ≈ 108% of value, explicit FCFF negative). Classifier & other
> archetypes: `SKILL.md` (Mode A step 2). Methodology backbone: `references/methodology-damodaran.md`.
