**English** | [简体中文](./README_CN.md)

<p align="center">
  <h1 align="center">AnalystCollective</h1>
  <p align="center"><em>Story → Numbers → Value &nbsp;·&nbsp; A Damodaran-method fundamental equity valuation engine</em></p>
</p>

---

**AnalystCollective** is not a black-box stock recommender. It is a **transparent,
AI agent-driven valuation engine** — you see not just what a company is "worth",
but how the story unfolds under every assumption, and what the gap between price
and value actually means.

Built on Aswath Damodaran's six-layer valuation framework, it turns methodology
into runnable Python code, orchestrated through **17 independent AI sub-agents**
in a self-iterating pipeline with adversarial review at every step. Every number
is auditable. Every report is reproducible.

---

## What's New (June 2026)

The `generate-pdf` sub-skill received a robustness overhaul based on real-world
testing with Chinese-language reports on Windows (non-ASCII working directories):

| Feature | Before | After |
|---------|--------|-------|
| **Company logo** | `position: fixed` CSS (overlapped title text on every page) | Engine-native: `headerTemplate` (Chromium) / `running()` (WeasyPrint). Top margin auto-grows with logo size — no overlap ever. |
| **Image paths** | `file://` / relative paths (blank images in non-ASCII dirs like `D:\\研报生成`) | Every image base64-embedded as a `data:` URI — path-independent, engine-neutral. |
| **Chart sizing** | No height bound (9×5.2″ chart filled the page) | `max-height: 8.5cm; object-fit: contain` ceiling on all chart images. |
| **Visual verification** | File-size checks only (layout bugs invisible) | `render_pdf_previews()` renders PDF→PNG for actual inspection. `--verify-visual` flag. |
| **Engine detection** | Crashed on Windows when WeasyPrint raised `OSError` (missing Pango) | Catches broad `Exception` → gracefully falls back to Playwright. |
| **Logo size** | Hard-coded 0.95cm | Configurable `--logo-height` (cm). Top margin auto-computes: `max(2.5, height + 1.4)`. |

See [`skills/generate-pdf/PDF_FIXES.md`](skills/generate-pdf/PDF_FIXES.md) for the full
post-mortem and [`skills/generate-pdf/SKILL.md`](skills/generate-pdf/SKILL.md) for the updated spec.

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

## Modular Architecture — Agent Team + Adversarial Review

The skill is decomposed into **14 sub-skills** orchestrated through a pipeline with
two powerful mechanisms:

### Mechanism 1 — Default Agent Team (Parallelism)

Where sub-skills are independent, the orchestrator **automatically spawns parallel
agents** — no manual instruction needed. This cuts wall-clock time significantly:

```
WAVE 1 (parallel)  → /analyze-industry ∥ /analyze-theme
WAVE 2             → /analyze-company
WAVE 3             → /build-assumptions
WAVE 4             → /run-valuation
WAVE 5 (parallel)  → /durability-check ∥ /triangulate
WAVE 6             → /write-report
WAVE 7             → /self-audit
WAVE 8             → /generate-pdf
```

### Mechanism 2 — Adversarial Review at Every Step

After **EVERY** sub-skill completes, an adversarial review agent critiques the
output before the pipeline can proceed. The reviewer's stance is **skeptical,

### Mechanism 3 — Loop Protocol (Type-A/B Gates + Cross-Model Verdict)

Every gate is classified Type-A (machine-checkable) or Type-B (requires taste).
**Type-B gates route to a different model family (Codex xhigh)** — Claude drives
the loop but a different model signs off on quality. A convergence terminator
caps iterations at 3, escalating to risk annotation instead of silent pass.
Full protocol: [`references/loop-protocol.md`](references/loop-protocol.md).

| Gate Type | Examples | Reviewer | Rule |
|-----------|----------|----------|------|
| **Type-A** | `report_lint.py`, JSON validity, engine sanity, terminal growth ≤ riskfree | Same-model / script | Self-judgment OK |
| **Type-B** | 7-dim audit, report voice/depth, adversarial reviews | **Cross-model (Codex xhigh)** | Cannot self-acquit |

> *"A loop can DRIVE; it cannot ACQUIT."* — Claude orchestrates; a different model
> family verifies. 5 Claude reviewers agreeing = shared bias, not correctness.

After **EVERY** sub-skill completes, an adversarial review agent critiques the
output before the pipeline can proceed. The reviewer's stance is **skeptical,
not friendly** — it must find at least one weakness or prove the output is
genuinely flawless. Each sub-skill gets **1–2 revision rounds**:

```
sub-skill → output → adversarial review → REVISE?
    ↑                                        │
    └── fix + re-submit (round 2) ───────────┘
                                                 ↓
                                            REVISE again?
                                                 │
                                    ┌────────────┴────────────┐
                                    ↓                         ↓
                                  PASS                    ESCALATE
                              (next step)           (flag with risk note)
```

Each sub-skill has a specific review criteria section in its SKILL.md —
the reviewer checks against a concrete checklist, not vague impressions.

### All sub-skills

| Sub-skill | Role | Key review check |
|-----------|------|-----------------|
| `/classify-archetype` | Pick engine + playbook | Financials trap avoided? Edge cases considered? |
| `/analyze-industry` | Lifecycle, cycles, leaders | 10+ yr data? Leader rotation table real? |
| `/analyze-company` | Model, moat, 10yr, drawdowns | Moat decomposed? Drawdowns documented? SBC quantified? |
| `/analyze-theme` | TAM × share, competition | Two revenue paths? TAM sourced? Big Market Delusion? |
| `/build-assumptions` | Story→numbers, .json | Accounting computed? Drivers justified? Engine sanity? |
| `/run-valuation` | DCF, MC, breakeven, reverse | All scripts run? Terminal % stated? MoS band? |
| `/durability-check` | ROIC-WACC, CAP, RONIC | ROIC adjusted? Each moat has threat? CAP justified? |
| `/triangulate` | 7-lens cross-check | No averaging? Dispute locus specific? Variant falsifiable? |
| `/write-report` | Investor-facing prose | No "you"? All 6 depth elements? Numbers ledger? |
| `/self-audit` | Lint + self-critique | Lint passes? No dodged CRITICALs? Honest scoring? |
| `/generate-pdf` | Typographic PDF | Charts embedded? Logo in margin (not overlapping text)? CJK fonts? Rating box? All images base64-embedded? Visual previews verified? |
| `/critique-report` | Mode B: audit others | Evidence-backed? Re-run present? Verdict matches? |
| `/refresh-valuation` | Mode C: keep current | Dated sweep? Driver delta explicit? Reverse re-test? |
| `/fetch-data` | Shared: data skeleton | Sources annotated? Tiers correct? Warnings present? |

Each sub-skill is independently invocable and optimizable — change one review
criteria, improve one prompt, and the pipeline benefits without touching the rest.

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

# Build a professional PDF (auto-detects engine, embeds images as base64)
cd ../skills/generate-pdf/scripts
python render_pdf.py ../../templates/report.example.md --out report.pdf \
    --cjk --lang zh --chart-index ../../figs/chart-index.json

# With a company logo (auto-sized, never overlaps text)
python render_pdf.py ../../report.md --out report.pdf \
    --logo company_logo.jpg --logo-height 1.4 --verify-visual

# Value your own company
cp ../templates/assumptions.example.json ../my_company.json
# Edit my_company.json with your estimates
python dcf_valuation.py ../my_company.json
```

No dependencies beyond Python 3.10+ and the standard library for the core
engine. Optional: `matplotlib` for chart generation.

## The Engine

All scripts consume a JSON assumptions sheet. Money is in **$ millions** (or the
reporting currency), rates are **decimals** (0.40 = 40%), shares in **millions**.
Every valuation script accepts `--json` for machine-readable output, composable
with `charts.py`.

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
| `render_pdf.py` | PDF rendering | MD+charts+CSS → professional PDF. Auto-detect engine (WeasyPrint/Playwright). Logo via headerTemplate/running element. Base64 image embedding. Visual previews. |
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
├── scripts/              # Python valuation engine (11 programs)
│   ├── dcf_valuation.py
│   ├── monte_carlo.py
│   ├── breakeven.py
│   ├── reverse_dcf.py
│   ├── sotp.py
│   ├── comps.py
│   ├── financial_valuation.py
│   ├── charts.py
│   ├── render_pdf.py       # MD→PDF with logo, base64, visual verify
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
