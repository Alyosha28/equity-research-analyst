# Report Quality Gate - 55-Point Checklist

Every Mode A research report must pass this gate before publication. The checklist
is derived from the XPEV report (the "gold standard" baseline) and covers four
dimensions: structural completeness, Damodaran framework discipline, multi-lens
triangulation, and narrative falsifiability.

**How to use this gate:**

- **Type-A items** (labeled `[A]`) are machine-checkable by `report_lint.py`.
  The linter must exit with zero FAIL before the report proceeds to PDF.
- **Type-B items** (labeled `[B]`) require judgment. They are scored by the
  adversarial review agent (self-audit's 7-dimension critique or the per-step
  reviewer). Each receives PASS / REVISE / BLOCK.
- **Checklist items** (labeled `[✓]`) are structural presence checks. The
  `self-audit` sub-skill verifies these by reading the report.
- **Publishing contract**: Before scoring, apply
  `references/publishing-contract.md`. Its language lock, source-tier ledger,
  cyclical normalization, and PDF checks are part of this gate.

---

## A. Structural Completeness (26 items)

### A1–A5 Industry Layer

| # | Item | Type | Criterion |
|---|------|------|-----------|
| A1 | Investment thesis upfront | [✓] | Thesis paragraph exists before first section break, with rating + value + price + one-sentence judgment |
| A2 | Industry lifecycle | [✓] | Lifecycle phase stated (early/growth/mature/declining) with quantitative evidence (penetration rate, growth deceleration) |
| A3 | Industry profit cycle | [✓] | Historical profit margin trajectory + compression/expansion drivers listed |
| A4 | Leader rotation table | [✓] | Multi-year Top-N ranking table + rotation pattern commentary linked to moat implications |
| A5 | Industry valuation history | [✓] | Historical EV/Revenue or EV/EBITDA multiples for the sector, with current comps positioning |

### A6–A10 Company Layer

| # | Item | Type | Criterion |
|---|------|------|-----------|
| A6 | Business model + revenue decomposition | [✓] | Revenue split by segment with margin/contribution characteristics per segment |
| A7 | Moat decomposition (component-level) | [✓] | >=4 moat components, each with: type, strength (1-5), erosion threat, monitorable indicator |
| A8 | 10-year financial trajectory | [✓] | >=7 years of revenue/profit/FCF data with inflection-point narrative |
| A9 | Near-death experience narrative | [✓] | At least one crisis/drawdown event described with recovery story (Damodaran: "great companies have near-death drawdowns") |
| A10 | Capital allocation grade | [✓] | Explicit capital allocation assessment (R&D intensity, SBC dilution, M&A, buybacks) |

### A11–A14 Theme Layer

| # | Item | Type | Criterion |
|---|------|------|-----------|
| A11 | Core win/loss drivers | [✓] | <=3 decisive drivers identified, each falsifiable |
| A12 | Value chain positioning | [✓] | Company's position in the value chain stated, with profit-pool commentary |
| A13 | TAM x share build (top-down + bottom-up) | [✓] | Dual-path revenue construction with reconciliation |
| A14 | Big Market Delusion check | [B] | Sum of all players' implied shares <= 100% of TAM. If >100%, must be explicitly acknowledged |

### A15–A22 Valuation Layer

| # | Item | Type | Criterion |
|---|------|------|-----------|
| A15 | Four-driver assumption tables | [✓] | Each driver (growth, margin, reinvestment, risk) has its own table with basis column |
| A16 | DCF result with PV decomposition | [A] | Intrinsic value, price, P/V ratio, explicit-period PV, terminal PV all stated |
| A17 | Monte Carlo distribution | [A] | Trial count, P5/P25/P50/P75/P95, price-in-distribution percentile reported |
| A18 | Reverse DCF | [✓] | Per-driver price-implied vs. base gap table |
| A19 | Breakeven grid | [✓] | Terminal-revenue x margin grid with conclusion ("no combination justifies price") |
| A20 | Morningstar/consensus comparison | [✓] | Third-party fair value stated + deviation sources decomposed dimension-by-dimension |
| A21 | Scenario analysis (probability-weighted) | [✓] | >=3 scenarios with explicit probabilities and probability-weighted value |
| A22 | Rating + rating rationale | [A] | Rating stated + rationale with price-implied assumptions decomposed into observable conditions |

### A23–A26 Completeness & Disclosure

| # | Item | Type | Criterion |
|---|------|------|-----------|
| A23 | Limitations / self-falsification | [✓] | Explicit "what would prove this wrong" section with most sensitive assumptions |
| A24 | Key risks + disclaimer | [A] | Risk list + not-investment-advice disclaimer present |
| A25 | Numbers ledger (Appendix A) | [A] | Table: every material number has source + date |
| A26 | Disclosures & Certifications (Appendix B) | [A] | B.1-B.8 all present: Reg AC, rating distribution, rating meanings, FINRA 2241 (>=3 items), methodology (>=2 methods), risk factors (>=3), information cutoff date, CSRC/SAC supplement (China names) |
| A27 | Report language lock | [A] | Output language matches `report_lang`; Chinese reports contain no English broker-template labels (`THESIS`, `INTRINSIC`, `DOWNSIDE`, `MoS BUY-BAND`, `Figure N:`, standalone `HOLD`/`REDUCE`) outside tickers, legal names, formulas, source titles, or quotes |

---

## B. Damodaran Framework Discipline (12 items)

| # | Item | Type | Criterion |
|---|------|------|-----------|
| B1 | 10-year explicit forecast period | [A] | Growth/margin table extends to Y10, growth converges monotonically toward terminal rate |
| B2 | Terminal growth bounds | [A] | CRITICAL. Upper: g_terminal <= adjusted risk-free rate. Lower: g >= rf - 1.5pp (configurable `tg_lower_bound_buffer`). Machine-checkable: extract g, rf, compare both bounds. |
| B3 | Cost-of-capital glide | [A] | Initial WACC != terminal WACC, with stated glide interval (e.g., Y5→Y10) |
| B4 | Explicit failure probability (Young/High Growth) | [A] | Failure probability % + distress value stated. Required for Young Growth archetype. |
| B5 | Sales-to-capital reinvestment discipline | [B] | S2C ratio explicitly stated with industry range. No "free growth" — reinvestment mechanically linked to revenue change. |
| B6 | Terminal value % of operating value stated | [A] | Terminal-pct explicitly reported and interpreted (not hidden). |
| B7 | R&D capitalization adjustment | [✓] | If report mentions R&D capitalization: (a) amortization life + basis, (b) adjusted operating margin, (c) explanation of how terminal_roc reflects adjusted invested capital |
| B8 | SBC treated as real expense, in fully diluted shares | [✓] | SBC acknowledged; share count reflects full dilution |
| B9 | Bottom-up revenue (TAM x share) | [B] | Revenue derived bottom-up, not top-down extrapolation |
| B10 | Data dates on macro parameters | [✓] | ERP, risk-free rate, CRP, beta all have source dates (typically from Damodaran monthly update) |
| B11 | S2C industry context | [A] | If report mentions sales-to-capital: industry name + industry median (any numeric source) present. Missing → WARN. |
| B12 | WACC stacking explained | [A] | If report mentions failure_probability > 0: WACC decomposition table present + premium/failure-probability mutual-exclusivity narrative. Missing → WARN. |

---

## C. Multi-Lens Triangulation (5 items)

| # | Item | Type | Criterion |
|---|------|------|-----------|
| C1 | Intrinsic DCF | [A] | DCF valuation present with explicit FCFF rows |
| C2 | Reverse DCF | [✓] | Reverse DCF present (what does the price imply?) |
| C3 | Monte Carlo | [A] | Distribution simulation with >=10,000 trials |
| C4 | Comps / relative valuation cross-check | [✓] | At least one relative-valuation lens (EV/Sales, EV/EBITDA, P/E comps, or football field) |
| C5 | Lenses interpreted, not averaged | [B] | Multiple lens results presented side-by-side with convergence/divergence interpretation. Not mechanically averaged. |

---

## D. Narrative Quality & Falsifiability (11 items)

| # | Item | Type | Criterion |
|---|------|------|-----------|
| D1 | Story → numbers → value chain intact | [B] | Every key number traces back to a narrative; every narrative claim lands in a number. |
| D2 | Price-implied assumptions decomposed | [B] | Reverse-DCF assumptions broken into separately observable sub-conditions |
| D3 | Rating logic clear (not just a conclusion) | [B] | Rating has explicit logical chain from assumptions to conclusion |
| D4 | "What would change my mind" | [✓] | Explicit list of events that would flip the rating |
| D5 | Revisit trigger with date | [✓] | Explicit revisit-by date (e.g., "Q2 2026 earnings, Aug 18 2026") |
| D6 | Margin-of-safety buy-band | [A] | Three accumulation/fair/rich zones with explicit price boundaries |
| D7 | Valid-as-of date stamp | [A] | Explicit effective date on the valuation |
| D8 | Bear case as rigorous as bull case | [B] | Bear scenario has comparable depth and evidence weight to bull |
| D9 | Self-falsification | [B] | Report actively presents conditions that would prove it wrong |
| D10 | Bias disclosure | [✓] | Position/interest disclosure present |
| D11 | Institutional register (no "you", no emoji) | [A] | Zero second-person pronouns, zero emoji, zero banned AI-tell callouts |

---

## Scoring

- **PASS**: Zero CRITICAL failures, zero Type-A FAIL, all Type-B items >= PASS.
- **PASS-WITH-NOTES**: Zero CRITICAL, zero Type-A FAIL, some Type-B REVISE that are documented in limitations.
- **REVISE**: One or more Type-A FAIL or Type-B REVISE that must be fixed before publication.
- **BLOCK**: CRITICAL failure (B2 terminal growth > risk-free, B4 missing for Young, A14 Big Market >100% unacknowledged).

## Quick Pre-Publish Check

Before running the full 52-point gate, run these three quick checks:

```bash
# 1. Mechanical lint (Type-A gates)
python scripts/report_lint.py output/TICKER_research_report.md
# Must exit 0 with zero FAIL lines.

# 2. Chart coverage
python scripts/select_charts.py TICKER --data-dir data/ --json | python -c "
import sys, json; d = json.load(sys.stdin)
missing = set(d['required']) - set(d['data_ready'])
if missing: print(f'BLOCK: {len(missing)} required charts missing data: {missing}')
"
# Must print nothing (no missing required charts).

# 3. PDF render with visual verify
python src/common/build_report.py TICKER
# Must exit 0, PDF size < 5MB, preview PNGs show no logo overlap.
```
