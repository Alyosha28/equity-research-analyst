<p align="center">
  <h1 align="center">Story → Numbers → Value</h1>
  <p align="center"><em>A Damodaran-method fundamental equity valuation engine</em></p>
</p>

---

**Story → Numbers → Value** is a disciplined, reproducible fundamental valuation
toolkit that values companies the way a thoughtful investor does: a **narrative,
disciplined by numbers, expressed as a value, and turned into a decision.** It
does not chase price targets or give trading tips — it estimates *intrinsic
value*, quantifies the *uncertainty*, and compares value to price.

Distilled from Aswath Damodaran's public valuations and the complementary lenses
used by sell-side, buy-side, and independent analysts, it ships a **runnable
Python engine** so every number is auditable and every valuation is reproducible.

---

## What's Inside

| Component | Purpose |
|-----------|---------|
| **Valuation Engine** (`scripts/`) | 10 Python programs — DCF, Monte Carlo, reverse DCF, breakeven, SOTP, comps, financials, charts, linting, data fetching |
| **Methodology** (`references/`) | The six-layer Damodaran framework + input estimation + valuation lenses + analyst playbook |
| **Archetype Playbooks** | Per-company-type guides — growth, banks/insurers, cyclicals/commodities, pre-profit/young, mature/declining, holding companies |
| **Templates** (`templates/`) | Worked examples — NVIDIA ($240 intrinsic, Jun 2023), Tencent SOTP, Freeport-McMoRan, plus blank assumption sheets |
| **Tests** (`tests/`) | Reproducibility guard, output schema validation, report linter, archetype coverage |
| **Style Guide** | Investor-facing prose discipline — no second-person, no emoji, long-form argument, MoS buy-band, numbers ledger |

## Modular Architecture — Self-Iterating Pipeline

The skill is decomposed into **14 sub-skills** orchestrated through a self-iterating
pipeline with four quality gates. Each sub-skill is independently testable and
optimizable — improve one without breaking the rest.

### The pipeline (Mode A — Full Valuation)

```
┌─────────────────────────────────────────────────────────────┐
│              /equity-research-analyst (orchestrator)         │
│                                                             │
│  STEP 1  /classify-archetype    → archetype, engine, playbook│
│  STEP 2  /analyze-industry      → industry lifecycle, leaders│
│  STEP 3  /analyze-company       → business model, 10yr fin. │
│  STEP 4  /analyze-theme         → TAM × share, competitive   │
│              ┌─── GATE A: Sanity check ───┐                  │
│  STEP 5  /build-assumptions     → story→numbers, .json file  │
│              ┌─── GATE B: Input sanity ───┐                  │
│  STEP 6  /run-valuation          → DCF, MC, breakeven, rev.  │
│  STEP 7  /durability-check       → ROIC-WACC, CAP, RONIC     │
│  STEP 8  /triangulate            → 7-lens cross-check        │
│              ┌─── GATE C: Triangulation ──┐                  │
│  STEP 9  /write-report           → investor-facing prose      │
│  STEP 10 /self-audit             → lint + adversarial review  │
│              ┌─── GATE D: Publish gate ───┐                  │
│              │ CRITICAL → feedback route  │                  │
│              │ to failing sub-skill       │                  │
│              └────────────────────────────┘                  │
│  STEP 11 /generate-pdf           → typographic PDF deliverable│
└─────────────────────────────────────────────────────────────┘
```

### Self-iteration mechanism

When a quality gate fails, the orchestrator routes targeted feedback to the
specific sub-skill that produced the problematic output, then re-runs downstream
steps. This creates a **closed optimization loop**:

```
gate fails → identify root sub-skill → targeted fix → re-run cascade → re-gate
```

Each sub-skill can be invoked independently for debugging and optimization:

### All sub-skills

| Sub-skill | Role | Mode |
|-----------|------|------|
| `/classify-archetype` | Classify company → pick engine + playbook | A |
| `/analyze-industry` | Industry lifecycle, profit cycles, leader rotation | A |
| `/analyze-company` | Business model, moat, 10yr trajectory, drawdowns | A |
| `/analyze-theme` | Thematic driver, TAM × share, competitive map | A |
| `/build-assumptions` | Story → numbers, accounting adj, write .json | A |
| `/run-valuation` | Execute Python engine suite | A |
| `/durability-check` | ROIC-WACC, CAP, RONIC fade, moat decomposition | A |
| `/triangulate` | 7-lens cross-check, dispute locus | A |
| `/write-report` | Produce investor-facing long-form prose | A |
| `/self-audit` | Lint + adversarial self-critique → gate | A/C |
| `/generate-pdf` | Render report to typographic PDF | A/B/C |
| `/critique-report` | Audit third-party research (Mode B) | B |
| `/refresh-valuation` | Currency sweep, driver delta, update memo (Mode C) | C |
| `/fetch-data` | Fetch financials, build skeleton (shared) | All |

## Philosophy

> *"A valuation is a story disciplined by numbers. A story without numbers is a
> fairy tale; numbers without a story are a spreadsheet nobody believes."*
> — Aswath Damodaran

Every valuation traces to a narrative, and every narrative is stress-tested
with a distribution, not a point estimate. The engine enforces a handful of
non-negotiable disciplines:

- **Story → numbers → value.** Never a spreadsheet without a narrative, never a narrative without numbers.
- **Quantify uncertainty; don't hide behind it.** Monte Carlo over the key drivers. Output a distribution.
- **Robustness over precision.** A conclusion that flips on a 2% tweak isn't one.
- **Separate investing from trading.** Value closes the price–value gap; momentum is a different game.
- **Be honest about bias.** Disclose priors, data dates, and the numbers ledger.

## Quick Start

```bash
# Clone
git clone https://github.com/Alyosha28/equity-research-analyst.git
cd equity-research-analyst

# Reproduce the NVIDIA valuation (Damodaran, June 2023)
cd scripts
python dcf_valuation.py ../templates/assumptions.example.json
# → intrinsic value ≈ $236/share

# Run the Monte Carlo
python monte_carlo.py ../templates/assumptions.example.json --price 409 --trials 20000
# → price at ~94th percentile, P(undervalued) ≈ 5%

# What does the price imply?
python reverse_dcf.py ../templates/assumptions.example.json --price 409 --solve-for terminal_revenue
# → $409 price implies ~$489B year-10 revenue (83% above base case)

# Generate charts for your report
python monte_carlo.py ../templates/assumptions.example.json --price 409 --json > mc.json
python charts.py --kind montecarlo --in mc.json --out figs/

# Value your own company
cp ../templates/assumptions.example.json ../my_company.json
# Edit my_company.json with your estimates
python dcf_valuation.py ../my_company.json
```

No dependencies beyond Python 3.10+ and the standard library for the core
engine. Optional: `matplotlib` for chart generation.

## The Engine

All scripts consume a JSON assumptions sheet. Money is in **$ millions**, rates
are **decimals** (0.40 = 40%), shares in **millions**. Every valuation script
accepts `--json` for machine-readable output, composable with `charts.py`.

| Script | Lens | Output |
|--------|------|--------|
| `dcf_valuation.py` | Intrinsic DCF | value/share, FCFF schedule, terminal-value share |
| `monte_carlo.py` | Uncertainty | value distribution, percentiles, **margin-of-safety buy-band**, price percentile |
| `breakeven.py` | "What has to be true" | 2-variable table (revenue × margin) |
| `reverse_dcf.py` | Expectations investing | growth / margin / CoC the price implies |
| `sotp.py` | Sum-of-the-parts | core DCF + portfolio + net cash → per share |
| `comps.py` | Relative valuation | peer-median multiples → implied value |
| `financial_valuation.py` | Banks & insurers | excess-return `(ROE − Ke) × BV` + DDM cross-check |
| `charts.py` | Visualization | Monte Carlo histogram, football field, breakeven heatmap, tornado → PNG/SVG |
| `report_lint.py` | Quality gate | flags AI-answer tells: second-person, emoji, missing MoS/ledger/disclaimer |
| `fetch_financials.py` | Data pre-fill | yfinance/EDGAR → assumptions skeleton *(third-party tier — confirm before use)* |

### The Four Value Drivers

Every valuation reduces to four inputs, all built from the story:

1. **Revenue growth** — segment TAM × market share, declining toward the risk-free rate
2. **Target operating margin** — R&D-adjusted, with a convergence path
3. **Reinvestment efficiency** — sales-to-capital ratio (revenue produced per dollar invested)
4. **Cost of capital** — starting at the sector rate, gliding to mature-market levels

## Company Archetypes

Most companies fit the default FCFF frame. Five types do **not** — each has its
own engine and playbook:

| Archetype | Engine | Key Idea | Example |
|-----------|--------|----------|---------|
| **Growth / Mature** (default) | `dcf_valuation.py` | FCFF, four-driver spine | NVIDIA, most operating cos |
| **Financials** (banks, insurers) | `financial_valuation.py` | Excess-return on equity `(ROE − Ke) × BV` | Large banks, P&C insurers |
| **Cyclicals / Commodities** | `dcf_valuation.py` | FCFF on **normalized** mid-cycle inputs + price deck | Freeport-McMoRan, oil producers |
| **Pre-profit / Young** | `dcf_valuation.py` | FCFF + **failure branch** + margin path | Biotech, early SaaS |
| **Mature / Declining** | `dcf_valuation.py` | FCFF, low/neg growth, near-term cash dominates | Tobacco, legacy media |
| **Holding Companies** | `sotp.py` | Core DCF + portfolio mark-to-market + net cash | Tencent, SoftBank, conglomerates |

## Worked Example — NVIDIA (June 2023)

A faithful reconstruction of Damodaran's public NVDA valuation at ~$409/share:

```
Intrinsic value ≈ $236–240/share
Price at ~94th percentile of value distribution
P(undervalued) ≈ 5%
Rating: REDUCE
```

The engine reproduces the number, the distribution, and the decision. See
`templates/report.example.md` for the full research report.

## Triangulation — Seven Lenses

No single lens is enough. The framework triangulates across seven perspectives
and instructs: **tell me where they agree vs. disagree — the dispute locus is
where the real diligence belongs.**

| Lens | What it answers | Engine script |
|------|-----------------|---------------|
| 1. Intrinsic DCF | What is the company worth? | `dcf_valuation.py` |
| 2. Monte Carlo | How wide is the uncertainty? | `monte_carlo.py` |
| 3. Breakeven | What has to be true for this price? | `breakeven.py` |
| 4. Reverse DCF | What does the price already price in? | `reverse_dcf.py` |
| 5. Comps | What do peers imply? | `comps.py` |
| 6. SOTP | What are the pieces worth separately? | `sotp.py` |
| 7. Bear / Skeptic | How does this break? | *structured checklist* |

## Report Quality Gate

Every report must survive its own author's audit before publication:

```bash
python report_lint.py ../path/report.md          # quick check
python report_lint.py ../path/report.md --strict  # fresh report — zero tolerance
```

The linter catches: second-person address ("you"), emoji, banned callout
patterns, missing margin-of-safety band, missing numbers ledger, missing
disclaimer, and AI-answer sentence patterns. Additionally, self-apply the
seven-dimension Mode B critique rubric from `references/report-critique-rubric.md`.

## Project Structure

```
equity-research-analyst/
├── SKILL.md              # Main orchestrator (routes Mode A/B/C)
├── skills/               # 14 sub-skills (the pipeline)
│   ├── classify-archetype/SKILL.md
│   ├── analyze-industry/SKILL.md
│   ├── analyze-company/SKILL.md
│   ├── analyze-theme/SKILL.md
│   ├── build-assumptions/SKILL.md
│   ├── run-valuation/SKILL.md
│   ├── durability-check/SKILL.md
│   ├── triangulate/SKILL.md
│   ├── write-report/SKILL.md
│   ├── self-audit/SKILL.md
│   ├── generate-pdf/SKILL.md
│   ├── critique-report/SKILL.md
│   ├── refresh-valuation/SKILL.md
│   └── fetch-data/SKILL.md
├── scripts/              # Python valuation engine (10 programs)
│   ├── dcf_valuation.py
│   ├── monte_carlo.py
│   ├── breakeven.py
│   ├── reverse_dcf.py
│   ├── sotp.py
│   ├── comps.py
│   ├── financial_valuation.py
│   ├── charts.py
│   ├── report_lint.py
│   ├── fetch_financials.py
│   └── valuation_inputs.py
├── references/           # Methodology & playbooks
│   ├── methodology-damodaran.md
│   ├── input-estimation.md
│   ├── valuation-lenses.md
│   ├── analyst-playbook.md
│   ├── playbook-financials.md
│   ├── playbook-cyclical.md
│   ├── playbook-young.md
│   ├── playbook-mature.md
│   ├── holding-company-sotp.md
│   ├── report-critique-rubric.md
│   ├── report-voice.md
│   ├── self-audit-gate.md
│   ├── live-tracking.md
│   └── output-templates.md
├── templates/            # Worked examples & assumption sheets
│   ├── assumptions.example.json      (NVIDIA, Jun 2023)
│   ├── report.example.md             (full NVIDIA report)
│   ├── tencent.assumptions.json      (Tencent core DCF)
│   ├── tencent.sotp.json             (Tencent SOTP bridge)
│   ├── financials.example.json       (large bank)
│   ├── cyclical.freeport.json        (Freeport-McMoRan)
│   ├── young.example.json            (pre-profit)
│   ├── mature.example.json           (mature/declining)
│   ├── comps.example.json
│   └── freeport.figs/                (example chart outputs)
├── tests/                # Unit tests & reproducibility guard
├── evals/                # Evaluation config
├── docs/                 # Development & optimization docs
├── SKILL.md              # Full skill definition (Claude Code)
├── LICENSE               # MIT
└── README.md
```

## Guardrails

- This is **analysis, not personalized investment advice.** Always include a disclosure.
- State assumptions *as assumptions*, with basis and low/base/high ranges.
- Always report what **% of value sits in the terminal** and where the **price sits in the value distribution.**
- Quote a **margin-of-safety buy-band** (accumulate-below / fair / rich-above), not just a point.
- Make the **bear case** as rigorously as the bull case.
- **Self-falsify.** Name the specific assumption that carries the result and the breakeven at which the thesis flips.
- Note data dates. Stale inputs are how good methods produce bad calls.
- **Tier data confidence.** Distinguish audited figures, management guidance, sell-side consensus, third-party aggregators, and own estimates.

## Credits

Built on the public valuation methodology of **Aswath Damodaran** (NYU Stern),
whose blog *Musings on Markets* and open-source spreadsheets have taught a
generation of investors how to value companies. This project adapts his
six-layer framework into a reproducible, scriptable form.

Also incorporates techniques from:
- Mauboussin & Rappaport — *Expectations Investing* (reverse DCF, implied forecast period)
- SemiAnalysis — bottoms-up supply-chain modelling (capacity ceiling → units × ASP)
- Sell-side consensus methodology — segment build → EPS → multiple decomposition
- Buffett / Munger — owner-earnings, margin-of-safety, moat-durability discipline
- Dalio — cycle placement for cyclicals/commodities

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, ship it in production. Attribution appreciated.

---

<p align="center">
  <sub>Not investment advice. All valuations are sensitive to assumptions — the cost of capital most of all.</sub>
</p>
