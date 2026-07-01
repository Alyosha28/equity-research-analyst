---
name: equity-research-analyst
description: >
  Fundamental equity valuation and investor-facing research in Aswath
  Damodaran's story to numbers to value style. Use for producing full equity
  research reports, critiquing third-party reports, refreshing valuations, and
  analyzing listed companies, industries, themes, valuation assumptions,
  cyclical/commodity businesses, SOTP cases, and PDF-ready research packages.
license: MIT
---

# Equity Research Analyst

This is the orchestrator for the `equity-research-analyst` skill family. It runs
three modes:

- **Mode A - Produce:** build a complete equity research report from company,
  industry, theme, assumptions, valuation, charts, self-audit, and PDF.
- **Mode B - Critique:** audit a third-party report, rerun key inputs, and write
  severity-tagged findings.
- **Mode C - Refresh:** update a prior valuation for new data, market price, and
  driver changes.

Use the sub-skills listed below rather than duplicating their work. Read only the
references needed for the active mode.

## Required Shared Contract

Before writing, rendering, or publishing any report, read
`references/publishing-contract.md`. It defines the shared contract for:

- report language and locale propagation across writing, charts, PDF, and lint;
- broker-template label translation for Chinese reports;
- source confidence tiers and numbers ledger requirements;
- cyclical valuation normalization;
- pre-publish mechanical gates.

This contract is inherited by `write-report`, `generate-charts`, `generate-pdf`,
and `self-audit`.

## Sub-Skill Map

| Step | Sub-skill | Purpose |
|---|---|---|
| 0 | `fetch-damodaran-data` | Fetch current ERP, CRP, betas, WACC, and risk-free inputs |
| 1 | `classify-archetype` | Classify business archetype and life-cycle phase |
| 2 | `analyze-industry` | Industry cycle, structure, margin history, leader rotation |
| 3 | `analyze-theme` | Theme, TAM, value chain, competitive map |
| 4 | `analyze-company` | Business model, moat, 10-year financials, drawdowns |
| 5 | `build-assumptions` | Convert story into low/base/high model inputs |
| 6 | `run-valuation` | Run DCF, Monte Carlo, reverse DCF, breakeven, comps, SOTP |
| 7 | `durability-check` | ROIC-WACC spread, CAP, RONIC fade, moat decomposition |
| 8 | `triangulate` | Cross-check valuation lenses and identify the dispute locus |
| 9 | `generate-charts` | Render story-driven charts from valuation JSON |
| 10 | `write-report` | Write the investor-facing report |
| 11 | `self-audit` | Run mechanical lint plus adversarial quality gate |
| 12 | `generate-pdf` | Render the final PDF and visual previews |

Shared utilities:

- `research`: single point for web research, source annotation, and fact checks.
- `fetch-data`: build financial-data skeletons from filings/APIs.

Rule: analysis sub-skills send research briefs to `research`; do not fork
uncoordinated web searches inside every step.

## Mode A - Produce Pipeline

### Phase 0 - Market Data and Classification

1. Run `fetch-damodaran-data`.
   - Use current Damodaran ERP, CRP, betas, WACC, and risk-free data.
   - If offline, use cache only within the age limits in the sub-skill and carry
     `STALE_DATA` or `UNCACHED_FALLBACK` into the report limitations.
2. Run `classify-archetype`.
   - Lock both business-model archetype and Damodaran life-cycle phase.
   - If the firm is cyclical/commodity-like, read
     `references/playbook-cyclical.md` and `references/publishing-contract.md`.

### Phase 1 - Research

Run independent research streams in parallel when the runtime supports it:

- `analyze-industry`: 10+ year cycles, margin history, structure, leader rotation.
- `analyze-theme`: TAM, value chain, demand driver, competitor map.

Then run `analyze-company` using the industry context.

Consistency check: industry structure, company moat, and theme TAM/share path must
not contradict one another. If they do, route the fix to the originating step.

### Phase 2 - Assumptions and Engine

Run `build-assumptions`, then `run-valuation`.

Required engine outputs:

- intrinsic DCF value and terminal value share;
- Monte Carlo distribution and current-price percentile;
- reverse DCF / price-implied assumptions;
- breakeven grid;
- margin-of-safety buy band;
- applicable relative valuation or SOTP cross-check.

For cyclicals, do not capitalize a peak or trough:

- normalize margins through a full cycle;
- build revenue from volume/capacity and a defended price deck;
- keep terminal ROC close to cost of capital for price-takers;
- frame reverse DCF as peak/mid/trough economics already priced.

### Phase 3 - Durability, Triangulation, Charts

Run these as independent workstreams when supported:

- `durability-check`: ROIC-WACC spread, CAP, RONIC fade, moat threats.
- `triangulate`: interpret the valuation lenses; do not average them.
- `generate-charts`: run `scripts/select_charts.py` first, then render charts
  whose input data is ready.

Chart contract: report markdown must reference charts as
`![](figs/<TICKER>_<kind>)` with no extension. The PDF renderer resolves SVG
first and PNG second.

### Phase 4 - Report, Audit, PDF

1. Run `write-report`.
   - Use the report language chosen in `references/publishing-contract.md`.
   - Write for anonymous investors, not as a chat reply.
   - Lead with rating, value/target, current price, and thesis.
2. Run `self-audit`.
   - `scripts/report_lint.py REPORT --strict` must pass for fresh reports.
   - Type-B reasoning gates require adversarial review or an explicit
     unverified-gate disclosure if independent review is unavailable.
3. Run `generate-pdf`.
   - Use `python src/common/build_report.py TICKER` when the project wrapper
     exists.
   - Render visual previews and inspect them for CJK fonts, chart embedding,
     first-page rating box, page numbers, and logo/header overlap.

Final package:

- `TICKER_report.md`
- `TICKER_research_report.pdf`
- `TICKER_assumptions.json`
- `figs/` with SVG and PNG charts
- any valuation JSON needed to reproduce the output

## Mode B - Critique Pipeline

Use `critique-report`.

1. Extract thesis, key assumptions, valuation methods, and rating.
2. Re-run or approximate the key valuation inputs.
3. Score the report against `references/report-critique-rubric.md`.
4. Lead with findings by severity.
5. State what evidence or assumption change would alter the verdict.

Optional: render the audit memo via `generate-pdf`.

## Mode C - Refresh Pipeline

Use `refresh-valuation`.

1. Sweep developments since the last valid-as-of date.
2. Mark each driver as CONFIRMS, STRENGTHENS, WEAKENS, or BREAKS.
3. Re-run affected valuation components.
4. Produce either a short update memo or a revised report.
5. Run the same language, source-tier, and lint gates before publishing.

## Review and Iteration Rules

- Type-A gates are machine-checkable: scripts, JSON validity, math bounds,
  chart existence, and PDF build exit codes.
- Type-B gates require judgment: voice, thesis quality, valuation interpretation,
  chart usefulness, and publishability.
- A loop can drive revision but cannot acquit itself. If cross-model or human
  review is unavailable, record the gap instead of silently passing.
- Cap same-error revisions at three attempts; then publish only with explicit
  risk annotation or stop and ask for better input.

## Guardrails

- This is analysis, not personalized investment advice.
- Every material number needs a source tier and as-of date.
- Always report terminal value share, price percentile, MoS buy band, and
  valid-as-of / revisit-by dates.
- Make the bear case as rigorous as the bull case.
- Every Mode A report must include the Disclosures and Certifications appendix
  from `references/output-templates.md`; China-listed names also need the China
  supplement.
