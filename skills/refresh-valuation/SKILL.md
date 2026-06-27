---
name: equity-research-analyst/refresh-valuation
description: >
  Mode C: Keep a valuation current. Sweep developments since last as-of date,
  compute the driver delta (CONFIRMS/STRENGTHENS/BREAKS), re-run engine if a driver
  broke, and publish a dated update memo. Lightweight, frequent, high-ROI.
license: MIT
---

# Refresh Valuation (Mode C)

**Pipeline position:** Standalone — Mode C. Invoked when the user wants to update
a prior valuation with the latest developments.

## Philosophy

A valuation is a living document. Damodaran's NVIDIA went $240 → $87 → $78 as the
story moved. The discipline is not to be right once — it's to **re-value when the
story moves** and to say plainly what moved it. A refresh is cheap and frequent;
a full rebuild is expensive and rare.

## Input
- Prior report (Markdown or PDF)
- Prior `assumptions.json` (or reconstruct from the report)
- Current date, current stock price

## Pipeline

### Step 1 — Sweep developments since [prior as-of date]

Run a targeted research sweep using `WebSearch` or the `deep-research` skill for
the period since the prior report's valid-as-of date:

| Dimension | What to pull (dated) | Feeds |
|-----------|---------------------|-------|
| Latest results | Most recent quarter: revenue, segment, margin, FCF | Driver delta |
| Guidance | Management's forward guidance, capex, buyback/dividend | Driver delta + catalysts |
| Regulation/legal | New rulings, fines, export controls | Risk driver |
| Competitive moves | Rivals' launches, share shifts, pricing, in-sourcing | Growth, margin, CAP |
| Theme/demand | Hyperscaler capex, TAM revisions, demand signals | Growth |
| Capital actions | Buybacks, insider, M&A, divestitures | Per-share value |
| Price/multiple move | Price change vs prior as-of date | Reverse-DCF re-test |
| Analyst revisions | Consensus changes and *why* | Sanity check |

Date every fetched fact and tier its source.

### Step 2 — Compute the driver delta

For each new data point, **re-anchor the assumption**:

| Verdict | Meaning | Action |
|---------|---------|--------|
| **CONFIRMS** | Data is within the model's path | No change; note it |
| **STRENGTHENS** | Data moves a driver in a favorable direction | Note revised input + sensitivity |
| **WEAKENS** | Data moves a driver unfavorably but doesn't break the thesis | Note revised input + sensitivity |
| **BREAKS** | Data invalidates a core assumption | **Re-run the engine** with corrected input |

### Step 3 — If nothing broke: short update memo

```
Header: Company (ticker) · prior call & date · call CONFIRMED ·
        price then → now · new valid-as-of / revisit-by

1. What changed — dated developments in prose, each tagged CONFIRMS/STRENGTHENS
2. Price-implied re-test — re-run reverse_dcf.py at current price; has the gap
   widened or closed?
3. Refreshed catalyst calendar + monitoring triggers
4. Re-stamped valid-as-of / revisit-by
```

### Step 4 — If a driver broke: re-run + revised value

```
Header: Company (ticker) · prior call & date · call REVISED (X → Y) ·
        price then → now · new valid-as-of

1. What broke — state the specific assumption, the new evidence, the corrected
   input, and the new value. One paragraph. (The NVDA $240→$87 discipline.)
2. Re-run the engine with corrected input
3. New value, new rating, new MoS band
4. Price-implied re-test at current price
5. Refreshed catalyst calendar + monitoring triggers
6. Self-audit (lightweight) before publishing
```

### Step 5 — Self-audit (lightweight)

Run `report_lint.py` on the memo. Quick check against the report voice:
- No second person
- Dated
- Driver delta explicit
- valid-as-of / revisit-by stamped

## Output format (Template C)

```markdown
# [TICKER] — Valuation Update
**Prior call:** [rating] · [value] · [date]
**Updated call:** [rating] · [value] · [date]
**Price:** $X → $Y ([+/-Z%])
**Valid as of:** [date] · **Revisit by:** [next catalyst]

## Developments since [prior date]
[Dated prose, each tagged CONFIRMS / STRENGTHENS / WEAKENS / BREAKS]

## Driver delta
| Driver | Prior | Now | Δ | Verdict |
|--------|-------|-----|---|---------|
| Revenue growth | X% | Y% | Zpp | CONFIRMS |
| Op margin | X% | Y% | Zpp | STRENGTHENS |
| S-to-C | X | Y | Z | CONFIRMS |
| CoC | X% | Y% | Zpp | CONFIRMS |

## [If broke:] Revised valuation
- Corrected input: [what changed]
- New intrinsic value: $X/share (was $Y)
- New rating: [Z]
- New MoS buy-band: $A – $B

## Price-implied re-test
- Reverse DCF at current price $Y: implies [driver] = [value]
- Gap vs base: [same / wider / narrower] → [interpretation]

## Catalyst calendar
| Date | Event | Driver | Expected direction |
|------|-------|--------|-------------------|
| ...  |       |        |                    |

## Monitoring triggers
- [Metric 1] crosses [threshold] → [action]
- [Metric 2] crosses [threshold] → [action]

*Analysis, not investment advice. Data as of [date].*
```

## Integration
- Full procedure: `references/live-tracking.md`
- Currency layer methodology is the same document
- Template C in `references/output-templates.md`
- If the refresh reveals a structural story change → recommend a full Mode A rebuild

## Self-check
- [ ] Every development is dated and source-tiered
- [ ] Driver delta is explicit — CONFIRMS/STRENGTHENS/WEAKENS/BREAKS for each driver
- [ ] Reverse DCF re-run at current price
- [ ] Catalyst calendar updated
- [ ] valid-as-of / revisit-by re-stamped
- [ ] If a driver broke: engine re-run, new value stated, explanation in one paragraph
