# The Currency Layer — keeping a valuation investment-relevant

An intrinsic value is a point-in-time estimate built on a story. The moment the
story changes — a new quarter, a regulatory ruling, a competitor's launch — the
estimate can go stale. A report that is rigorous but stale is useless for an
immediate investment decision. This layer makes a valuation **current**: it dates
the analysis, surfaces what has changed and what is coming, and states the few
things to watch that would flip the call.

> **Precedent.** Damodaran's NVIDIA intrinsic value moved from ~$240 (Jun 2023) to
> ~$87 (Sep 2024) to ~$78 (Feb 2025, after DeepSeek "changed the story"). The
> discipline is not to be right once — it is to **re-value when the story moves**
> and to say plainly what moved it. A valuation is a living document.

## What "currency" requires (every Mode A report carries this)

1. **A valid-as-of / revisit-by stamp.** State the data-as-of date and the next
   hard catalyst (usually the next earnings date) by which the call should be
   revisited. A rating without a freshness window is a trap.
2. **A dated "recent developments" sweep.** The latest 1–2 quarters of facts that
   bear on the drivers — not generic news. Each item dated and source-tiered
   (see the data-confidence tiers in `../SKILL.md` Guardrails).
3. **A driver delta.** For each of the four drivers (growth / margin /
   reinvestment / risk), state whether the most recent data point CONFIRMS,
   STRENGTHENS, or BREAKS the assumption in the model — and by how much.
4. **A catalyst calendar.** Dated upcoming events, the driver each one hits, and
   the expected direction. This is what makes the report actionable *now*.
5. **Monitoring triggers.** The two or three specific, observable metrics whose
   crossing a stated threshold would change the rating — tied to the bear-case
   leading indicators (`analyst-playbook.md` Lens 6).

## How to run the sweep (tools)

The valuation engine still runs on a dated `assumptions.json` — that does not
change. The currency layer is a **research pass layered on top**, run with:

- **`deep-research` skill** — for a multi-source, fact-checked sweep of the last
  1–2 quarters (earnings, guidance, regulation, competitive moves, analyst
  revisions). Preferred when the developments are material or contested.
- **`WebSearch` / `WebFetch`** — for a quick, targeted refresh of a single fact
  (latest quarter revenue, a specific ruling, current price/multiple).

Always **date every fetched fact** and tier its source. Recency itself is a
data-quality dimension: a number from last week and a number from two years ago
are not the same input even if they are the same metric.

## The sweep checklist (what to look for)

| Dimension | What to pull (dated) | Feeds |
|---|---|---|
| **Latest results** | Most recent quarter vs the model's path: revenue, segment growth, margin, FCF | Driver delta (growth, margin) |
| **Guidance** | Management's forward guidance, capex plans, buyback/dividend changes | Driver delta + catalyst calendar |
| **Regulation / legal** | New rulings, fines, license changes, export controls | Risk (cost of capital, failure prob) |
| **Competitive moves** | Rivals' launches, share shifts, pricing, customer in-sourcing | Growth, margin, CAP / moat durability |
| **Theme / demand signal** | The driver-specific real-world signal (e.g. hyperscaler capex, TAM revisions) | Growth |
| **Capital actions** | Buybacks executed, insider activity, M&A, divestitures | Per-share value, capital-allocation read |
| **Price & multiple move** | How price / implied multiple moved since the as-of date | Reverse-DCF: has what's-priced-in changed? |
| **Analyst revisions** | Consensus target / estimate revisions and *why* | Sanity check, not an anchor |

## The driver-delta discipline

For each new data point, do not just report it — **re-anchor the assumption**:

- *Confirms* — the data point is within the model's path; no change. Say so.
- *Strengthens / weakens* — the data point moves a driver but not the rating;
  note the revised input and the value sensitivity.
- *Breaks* — the data point invalidates an assumption (e.g. a margin guide far
  below the model's target); **re-run the engine** with the corrected input and
  state the new value. This is the NVDA $240→$87 move: don't defend the old
  number, update it.

## Writing the currency layer into the report (register-compliant)

In the report body this appears as a dated prose section, **not** a news dump:
develop what changed and what it means in paragraphs, with at most one compact
exhibit (the catalyst calendar). Lead each development with its date. Keep the
investor-facing voice — no "you", no "since you asked". See
`output-templates.md` for the section placement and `report-voice.md` for register.

## Mode C — Refresh an existing valuation (lightweight)

When asked to *update* a prior report rather than build one from scratch:

1. Run the sweep checklist above for the period since the prior report's as-of date.
2. Compute the driver delta. If nothing **breaks**, the prior value stands —
   publish a short "update memo" (Template C in `output-templates.md`) confirming
   the call, refreshing the catalyst calendar, and re-stamping valid-as-of.
3. If a driver **breaks**, re-run the affected engine inputs, state the new value
   and the changed rating, and explain — in one paragraph — exactly what moved.
4. Always show the price/multiple move since last time and re-test "what's priced
   in" with `reverse_dcf.py` — the gap that mattered may have closed or widened.

> A refresh is cheap and should be frequent; a full rebuild is expensive and rare.
> Most of the investment relevance comes from disciplined refreshes that keep the
> driver delta and catalyst calendar honest between rebuilds.

## Integration
- Bear-case leading indicators (monitoring triggers): [`analyst-playbook.md`](analyst-playbook.md)
- Data recency / source tiers: `../SKILL.md` Guardrails
- Section placement & refresh memo: [`output-templates.md`](output-templates.md)
- Register (dated, investor-facing prose): [`report-voice.md`](report-voice.md)
