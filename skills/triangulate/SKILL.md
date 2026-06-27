---
name: equity-research-analyst/triangulate
description: >
  Cross-check all seven valuation lenses, identify where they agree vs disagree
  (the dispute locus), and produce the triangulation verdict. The disagreement
  pattern is where the real investment insight lives. Step 8 of Mode A.
license: MIT
---

# Triangulate

**Pipeline position:** STEP 8 of Mode A. Runs after valuation (step 6) and durability
check (step 7). Synthesizes all lenses into a single coherent judgment.

## Input
- Valuation results (step 6): DCF value, Monte Carlo distribution, breakeven,
  reverse DCF, comps
- Durability assessment (step 7): CAP, moat, RONIC fade
- Company analysis (step 3)
- Theme analysis (step 4): TAM, competitive landscape

## The seven lenses

| # | Lens | Question | Source |
|---|------|----------|--------|
| 1 | Intrinsic DCF | What is it worth? | `dcf_valuation.py` |
| 2 | Monte Carlo | How wide is the uncertainty? | `monte_carlo.py` |
| 3 | Breakeven | What must be true for this price? | `breakeven.py` |
| 4 | Reverse DCF | What does the price already price in? | `reverse_dcf.py` |
| 5 | Comps | What do peers imply? | `comps.py` |
| 6 | SOTP (if holding-co) | What are the pieces worth separately? | `sotp.py` |
| 7 | Bear / Skeptic | How does this break? | structured checklist |

## What you produce

A **triangulation verdict** — not an average of the lenses, but an interpretation
of their pattern.

### Step 1: Lay the lenses side by side

```
Lens 1 (DCF):         value = $X/share
Lens 2 (Monte Carlo): median = $Y, price at Nth percentile
Lens 3 (Breakeven):   to justify price → Y10 rev = $A B AND margin = B%
Lens 4 (Reverse DCF): price implies Y10 rev = $C B (+D% vs base)
Lens 5 (Comps):       peers imply $E–$F/share
Lens 7 (Bear):        [top 3 break mechanisms with triggers]
```

### Step 2: Identify the dispute locus

| Pattern | Interpretation | Action |
|---------|---------------|--------|
| DCF ≈ comps ≈ price | Market and fundamentals agree | Little edge unless your story differs |
| DCF < price, reverse-DCF implies heroic numbers | Priced for near-best case | **Overvalued** signal |
| DCF > price, comps also low | Possible undervaluation | Investigate why market disagrees |
| DCF > price but comps high | Your DCF may be the optimist | Pressure-test your own inputs |
| Wide Monte Carlo, price in top decile | Even if bull path exists, odds are poor | Size accordingly |

### Step 3: Write the triangulation verdict

A prose statement (~300–500 words) that:
1. States where the lenses agree and disagree
2. Identifies the **dispute locus** — is the real bet on near-term execution or
   terminal durability?
3. Names the **variant perception** — the one thing you must out-predict the market on
4. Recommends where to **concentrate diligence**

### Output format

```markdown
## Triangulation: [TICKER]

### Lens summary
| Lens | Value/Share | vs Price | Signal |
|------|-------------|----------|--------|
| DCF  | $X          | -Y%      | SELL   |
| MC median | $Z   | Nth %ile | WEAK   |
| Comps     | $A–B | -C%      | SELL   |
| Reverse   | $D implied | +E%    | RICH   |

### Agreement/disagreement pattern
[Prose: where they cluster and where they diverge]

### Dispute locus
"The fight is about [near-term revenue / terminal margin / CAP length / market share],
not [everything else]. The market believes X; our evidence says Y."

### Variant perception
"To be right on this call, I must be right that [specific, falsifiable claim]."

### Diligence concentration
"The highest-ROI diligence is on [specific question], because it moves the value
by Z% and the evidence is contestable."
```

## Integration with the self-iterating loop

If the triangulation reveals a **fatal contradiction** (e.g., DCF value < 0 while
comps are rich, or reverse-DCF implies >100% TAM share), this triggers GATE C:
- Route back to `/build-assumptions` with the specific contradiction as feedback
- Or route back to `/analyze-theme` if the TAM share assumption is the root cause

This is a KEY LOOP POINT — the triangulation is often where bad assumptions are
first exposed.

## Rules
- **Never average the lenses.** Each answers a different question.
- **The dispute locus IS the insight.** "Everyone agrees on year 1; the fight is
  about years 5–10" → concentrate diligence on terminal assumptions.
- **Be specific about what you must out-predict.** "I think growth will be higher"
  is not a variant perception. "I think AI chip TAM will be $200B not $300B because
  hyperscaler capex is already at 50% of operating cash flow" is.

## Self-check
- [ ] All seven lenses are populated (or marked N/A with reason)
- [ ] Dispute locus is specific — names the dimension (near-term vs terminal) and
      the driver (revenue/margin/CAP)
- [ ] Variant perception is falsifiable
- [ ] Diligence concentration is actionable
- [ ] No averaging of lenses into one number
