# The Four Valuation Lenses (and how to triangulate them)

Damodaran's intrinsic DCF is one lens. Top-tier equity research reads a company
through **several** lenses and treats disagreement between them as *information*,
not noise. This skill uses four. Run the intrinsic DCF first (it forces an
explicit story), then cross-check with the others.

> Do **not** average the lenses into one number. Each answers a different
> question; the *pattern* of agreement/disagreement is the insight.

---

## Lens 1 — Intrinsic DCF ("what is it worth?")
- **Question:** What are the future cash flows worth today, given a defensible story?
- **Method:** Story → four drivers → FCFF → discounted value. See
  `methodology-damodaran.md`. Engine: `dcf_valuation.py`.
- **Strength:** Forces an explicit, falsifiable story; immune to market mood.
- **Blind spot:** Garbage-in-garbage-out; terminal value often dominates (be
  honest about what % of value is post-horizon).
- **Use when:** Always — it is the anchor.

## Lens 2 — Reverse DCF / expectations investing ("what's priced in?")
- **Question:** What must the market believe to justify today's price?
- **Method:** Hold all drivers at base case except one; solve for the value of
  that driver that makes intrinsic value = price. Then judge plausibility. Engine:
  `reverse_dcf.py`.
- **Strength:** Sidesteps the "is my forecast right?" trap; turns the question
  into "are *these* expectations achievable?" — often far easier to falsify.
- **Blind spot:** Single-variable solves can hide that the price needs *several*
  things to break right at once (use the breakeven table for the joint view).
- **Use when:** The stock looks expensive/cheap and you want to test whether the
  market's implied expectations are sane. (NVDA: price implied ~$489B year-10
  revenue or ~65% margins — both beyond the optimistic story.)

## Lens 3 — Relative valuation / comps ("what's the market paying for peers?")
- **Question:** Cheap or dear *relative to* similar businesses right now?
- **Method:** Peer-median multiples (EV/Sales, EV/EBITDA, P/E, PEG) applied to the
  target's metrics. Engine: `comps.py`.
- **Strength:** Fast, market-grounded, good for sanity checks and for sectors
  where DCF inputs are unstable.
- **Blind spot:** Inherits the market's mood — if the whole peer set is bubbly,
  comps call a bubble "fair". Trailing multiples punish hyper-growth names that a
  DCF rewards (use **forward** metrics for high-growth companies). Peer choice is
  a judgment call that can be gamed.
- **Use when:** Cross-checking the DCF and gauging sentiment. Big DCF-vs-comps
  gaps are a flag to investigate, not average away.

## Lens 4 — Scenario / thematic ("what are the distinct futures?")
- **Question:** What are the few coherent worlds the company could live in, and
  how likely is each?
- **Method:** Build 2–4 internally-consistent scenarios (e.g., *AI dominance* /
  *base* / *competition compresses margins*), each a full set of drivers; value
  each; probability-weight. The Monte Carlo (`monte_carlo.py`) is the continuous
  version — a distribution instead of discrete scenarios.
- **Strength:** Captures structural uncertainty and path-dependence that a single
  DCF flattens; communicates the bull/bear cases honestly.
- **Blind spot:** Scenario probabilities are subjective; easy to anchor on a
  preferred outcome. Discipline: make the bear case as rigorously as the bull.
- **Use when:** The future is genuinely forked (platform shifts, regulation,
  binary outcomes).

---

## Triangulation: reading the lenses together

After running all four, lay the outputs side by side and interpret the pattern:

| Pattern | Interpretation |
|---|---|
| DCF ≈ comps ≈ price | Market and fundamentals agree; little edge unless your story differs. |
| DCF < price, reverse-DCF implies heroic numbers | Priced for a near-best case → **overvalued** unless you believe the heroics. (NVDA June 2023.) |
| DCF > price, comps also low, no broken thesis | Possible **undervaluation** — investigate why the market disagrees (what does it see that you don't?). |
| DCF > price but comps high & sector bubbly | Your DCF may be the optimist; pressure-test your own inputs. |
| Wide Monte Carlo, price in the top decile | Even if a bull path exists, the *odds* are poor — size accordingly. |

**The triangulation question is always the same:** *where is the market's view
different from mine, and who has the better-grounded reason?* If you can't
articulate why the market is wrong, you probably don't have an edge.

See `analyst-playbook.md` for how specific top analysts operationalize each lens
(sell-side EPS×multiple, SemiAnalysis supply-chain build, ARK TAM scenarios,
Mauboussin expectations, the bear case).
