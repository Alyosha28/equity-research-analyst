---
name: equity-research-analyst/classify-archetype
description: >
  Classify a company into its business-model archetype AND corporate life-cycle phase.
  Produces the combined classification that determines engine, playbook, narrative
  emphasis, and driver sensitivity for every downstream step. First step of Mode A.
license: MIT
---

# Classify Archetype & Life-Cycle Phase

**Pipeline position:** STEP 1 of Mode A. Runs first — its output determines the
engine, playbook, driver set, and narrative emphasis for every downstream step.

## Input
- Company name / ticker
- Brief description of business (if available)
- Sector/industry
- Revenue (approximate, trailing 12-month)
- Operating margin (approximate, or whether the company is profitable)
- Revenue growth rate (approximate, trailing)
- Age of the company (years since founding / IPO)

## What you produce

A **dual classification** verdict with rationale:

```
Archetype: [one of 6 business-model types]
Life-Cycle Phase: [one of 6 phases]
Engine: [which Python script]
Playbook: [which reference playbook(s)]
Narrative Emphasis: [what the story is about, per the life-cycle phase]
Confidence: HIGH / MEDIUM / CHECK
If CHECK: what additional info would resolve ambiguity
```

---

## Part A: Business-model archetype (6 types)

The archetype answers "what kind of business is this?" — it determines the
valuation engine and the structural approach to the drivers.

| Archetype | Defining trait | Engine | Playbook |
|-----------|---------------|--------|----------|
| **Default** (growth/mature operating co) | Earns operating margin on goods/services | `dcf_valuation.py` | methodology-damodaran.md |
| **Financials** | Balance sheet IS the product; earns spread/underwriting | `financial_valuation.py` | playbook-financials.md |
| **Cyclical** | Commodity/cyclical price-taker; margins cycle with macro | `dcf_valuation.py` (normalized) | playbook-cyclical.md |
| **Young** | Currently lossmaking / pre-scale; high failure risk | `dcf_valuation.py` + failure branch | playbook-young.md |
| **Mature/Declining** | Flat-to-declining, returning cash, low reinvestment | `dcf_valuation.py` (low/neg growth) | playbook-mature.md |
| **Holding-co** | Operating co + large investment portfolio | `sotp.py` | holding-company-sotp.md |

### Archetype classification algorithm

Ask in order — the first "yes" is the answer:

1. **Does the company earn primarily a spread or underwriting result on its own balance sheet?**
   - YES → **Financials**. (Banks, insurers, specialty lenders, BDCs, mortgage REITs.)
   - TRAP: card networks, exchanges, rating agencies, asset managers, pure-fee fintechs
     are NOT financials — they earn fees on others' money. Use Default.

2. **Is the company currently unprofitable / pre-revenue / pre-scale, with a material chance of failure?**
   - YES → **Young**. (Biotech pre-approval, early SaaS burning cash, pre-revenue deep tech.)

3. **Is the company's revenue dominated by a commodity whose price it cannot control?**
   - YES → **Cyclical**. (Miners, oil & gas producers, chemical commodity, steel, shipping.)

4. **Is the company flat-to-declining, paying out most earnings, with minimal reinvestment?**
   - YES → **Mature/Declining**. (Tobacco, legacy media, declining retail.)

5. **Does the company hold a large, separable investment portfolio alongside an operating business?**
   - YES → **Holding-co**. (Tencent, SoftBank, Berkshire, conglomerates.)

6. **None of the above** → **Default**. (NVIDIA, Apple, Starbucks, most companies.)

---

## Part B: Corporate life-cycle phase (6 phases)

The life-cycle phase answers "how old is this business?" — it determines the
narrative emphasis, the shape of the driver paths, and the sensitivity structure.
Based on Damodaran's *The Corporate Life Cycle* (2024). Full detail in
`references/methodology-lifecycle.md`.

| Phase | Revenue profile | Growth rate | Margin profile | Narrative emphasis | Valuation priority |
|-------|----------------|-------------|----------------|-------------------|-------------------|
| **Start-Up** | Zero or near-zero | N/A (no base) | Deeply negative (idea stage) | Can this idea become a business? | TAM × probability of success; cash runway |
| **Young Growth** | Small, scaling fast | High from tiny base | Negative; investing ahead of revenue | Will the business model work at scale? | Revenue path; margin glide to positive; failure branch |
| **High Growth** | Large and growing fast | 30%+ | Turning positive; operating leverage | How big can this get? | TAM × share; growth deceleration; margin expansion |
| **Mature Growth** | Large, decelerating | 5–30% | Positive, expanding toward target | How long can moat defend above-average returns? | CAP; margin durability; competitive threats |
| **Mature Stable** | Large, market-paced | 0–5% | Stable at or near peak; strong FCF | How will value be preserved? | Terminal value; capital allocation; payout |
| **Decline** | Shrinking | Negative | Compressing; fixed-cost deleverage | How fast does it shrink and what's the floor? | Liquidation value; pace of decline; debt paydown |

### Life-cycle phase classification algorithm

Ask in order — the first clear match is the answer:

1. **Does the company have meaningful revenue (>$10M)?**
   - No → **Start-Up**. Pre-revenue, idea stage, clinical-stage biotech with no
     approved product, pre-revenue deep tech. Most of the value is in the story.
   - Yes → proceed to Q2.

2. **Is the company profitable (positive operating margin, trailing 12-month)?**
   - No → **Young Growth**. Losses are by design (investing ahead of demand).
     Unit economics should show a credible path to positive margins.
     - CAVEAT: If the company has scaled and losses did NOT compress, it may be a
       broken model, not a Young Growth company. Flag for special handling.
   - Yes → proceed to Q3.

3. **What is the annual revenue growth rate (trailing)?**
   - 30%+ → **High Growth**. Company is scaling aggressively; reinvesting heavily;
     margins expanding with operating leverage.
   - 5–30% → **Mature Growth**. Growth is decelerating; the company is shifting
     from offense to defense; competitors are entering its market.
   - 0–5% → **Mature Stable**. Growth has converged to the economy's rate.
     Company generates more cash than it can profitably reinvest.
   - Negative → **Decline**. The market is shrinking.

4. **Refine with qualitative signals:**
   - High Growth vs. Mature Growth: Are competitors entering aggressively? Is the
     company still gaining market share or defending? Has management started
     talking about "capital return"?
   - Mature Growth vs. Mature Stable: Has the company initiated a dividend for
     the first time? (This is a strong signal of Mature Stable acceptance.)
     Is growth converging to GDP?
   - Mature Stable vs. Decline: Is the revenue decline cyclical (→ still Mature
     Stable with a cyclical dip) or structural (→ Decline)? Look at the market,
     not just the company. A structural decline means the market itself is
     shrinking — not just a bad year.

### Special cases

- **Multi-segment companies:** Classify the dominant segment (by revenue or value)
  for the primary phase. Note if other segments are in different phases — this
  has implications for sum-of-the-parts valuation.
- **Cyclical companies:** A cyclical in an up-cycle may look like High Growth; in
  a down-cycle, like Decline. Use **through-cycle** revenue and margins for phase
  classification, not the current cycle point. The archetype is "Cyclical"; the
  phase should reflect the underlying structural position of the industry (e.g.,
  a diversified miner with 30-year reserves is structurally Mature Growth, even
  if revenue is temporarily booming or slumping).
- **Financials:** Banks cannot be Start-Ups (regulatory capital requirements).
  Neobanks and early fintechs map to Young Growth. Large-cap banks map to Mature
  Stable. The phase framework adapts to financials — use ROE decomposition instead
  of operating margins for the margin assessment.

---

## Combined output format

```json
{
  "archetype": "default",
  "lifecycle_phase": "high_growth",
  "engine": "scripts/dcf_valuation.py",
  "playbooks": [
    "references/methodology-damodaran.md",
    "references/methodology-lifecycle.md",
    "references/analyst-playbook.md"
  ],
  "narrative_emphasis": "How big can this get? TAM x share; growth deceleration; margin expansion. Big Market Delusion check is essential.",
  "rationale_archetype": "Company earns operating margins on goods/services -- standard FCFF frame.",
  "rationale_phase": "Revenue growth >30% with positive and expanding margins. Company is scaling aggressively in a large addressable market.",
  "confidence_archetype": "HIGH",
  "confidence_phase": "HIGH",
  "traps_avoided": [],
  "downstream_consequences": {
    "drivers": ["revenue_growth", "target_margin", "sales_to_capital", "cost_of_capital"],
    "driver_emphasis": "Revenue growth is the most sensitive driver; margin expansion path is the second. Terminal assumptions are less dominant than for mature phases.",
    "cost_of_capital_structure": "Initial at sector average, gliding to mature market average over the 10-year horizon. Failure probability low (<5%).",
    "terminal_structure": "Going-concern terminal value at stable growth <= riskfree. Terminal value ~60-80% of operating value.",
    "special_checks": ["Big Market Delusion cross-check", "Growth deceleration credibility", "Competitive entry timeline"],
    "monte_carlo_emphasis": "Widen revenue growth and margin distributions -- these drive the value range for High Growth companies."
  }
}
```

---

## Edge cases and cross-dimension traps

- **Diversified financials** with large asset management arms: classify by dominant
  earnings driver. >50% from spread/underwriting → Financials. >50% from fees → Default.
- **Commodity-like tech** (DRAM): if pricing power is cyclical → Cyclical archetype.
  Phase depends on structural industry position, not current cycle point.
- **Platform companies** (Uber, Airbnb): Default — they earn take-rates, not spreads.
  Phase: most are High Growth or Mature Growth.
- **Young Growth vs. Start-Up:** The key test is revenue. Revenue >$10M → Young Growth.
  Revenue <$10M (or pre-revenue) → Start-Up. A clinical-stage biotech with no approved
  drug is a Start-Up even if it is 10 years old — phase is about business maturity,
  not chronological age.
- **Mature/Declining archetype vs. Decline phase:** The Mature/Declining archetype
  (flat-to-declining, paying out) describes the business model; the Decline phase
  (negative growth, shrinking market) describes the aging stage. A Mature Stable
  company in a stable market uses the Default archetype with Mature Stable phase. A
  company in structural decline uses BOTH the Mature/Declining archetype AND the
  Decline phase.
- **Holding-co + life-cycle phase:** Classify the phase of the dominant operating
  subsidiary. If the holding company has diverse subsidiaries in different phases,
  note this — it affects the SOTP discount rate and terminal assumptions per segment.

---

## Adversarial Review Gate

After this sub-skill produces output, an adversarial review agent critiques it
(1–2 rounds max) against these criteria:

### Review criteria
- [ ] **Archetype correctness:** Does the archetype match the defining trait? Test:
  re-apply the classification algorithm — would a second analyst reach the same
  conclusion?
- [ ] **Life-cycle phase correctness:** Does the revenue/growth/margin profile
  match the assigned phase? Re-apply the phase algorithm.
- [ ] **Archetype-phase consistency:** Do the archetype and phase cohere? E.g.,
  a "Start-Up Financials" is impossible (banks can't be start-ups). A "High Growth
  Mature/Declining" is contradictory.
- [ ] **Financials trap check:** If NOT financials, was the spread-vs-fee test
  explicitly applied and passed?
- [ ] **Decisiveness:** Both classification dimensions are single, decisive picks
  — not "maybe X or Y".
- [ ] **Downstream mapping:** Engine, playbook(s), narrative emphasis, driver
  emphasis, and special checks are all explicitly stated.
- [ ] **Edge cases:** Commodity-tech, platform, diversified-financial, multi-segment,
  and cyclical-phase cases considered.

### Common failure modes (reviewer hunts for these)
- Card network / exchange / asset manager misclassified as Financials (→ BLOCK)
- Commodity-chemical company NOT classified as Cyclical (→ REVISE)
- Holding-co with >30% of value in stakes NOT classified as Holding-co (→ REVISE)
- Pre-revenue biotech NOT classified as Young (→ REVISE with failure branch)
- High Growth phase assigned to a company with <10% revenue growth (→ REVISE)
- Mature Stable phase assigned to a company with 40%+ growth (→ REVISE)
- Contradictory archetype-phase combination (e.g., Financials + Start-Up) (→ REVISE)
- Life-cycle phase omitted entirely (only archetype given) (→ REVISE)

### Verdict thresholds
- **PASS:** Both archetype and phase correct, consistent, mapped to downstream steps,
  traps documented. Minor notes OK.
- **REVISE:** Ambiguous classification on either dimension, missing downstream mapping,
  inconsistent archetype-phase pairing, or edge case not considered. Give specific fix
  directive.
- **BLOCK:** Wrong archetype (fatal — all downstream steps depend on this), or
  contradictory classification.

### Self-check (run before submitting to review)
- [ ] The "trap" test for financials is explicitly applied
- [ ] Both archetype and life-cycle phase are stated
- [ ] Archetype and phase are consistent with each other
- [ ] Revenue range, margin status, and growth rate support the phase
- [ ] Each classification dimension is decisive, not "maybe X or Y"
- [ ] Downstream consequences (engine + playbooks + driver emphasis + narrative) are stated
- [ ] Phase-specific special checks (Big Market Delusion for High Growth, liquidation
  floor for Decline, etc.) are identified
