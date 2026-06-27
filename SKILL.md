---
name: equity-research-analyst
description: >
  Fundamental equity valuation & research in Aswath Damodaran's "story -> numbers
  -> value" style, for ANY company. Two modes: PRODUCE a full intrinsic valuation +
  research report (industry -> company -> theme -> DCF -> Monte Carlo -> decision),
  or CRITIQUE/stress-test a third-party research report. Ships a runnable Python
  engine (DCF, Monte Carlo, breakeven, reverse-DCF, comps) so every valuation is
  reproducible. 用中文也可触发：当用户想给公司估值、算内在价值/合理价值、做DCF或现金流折现、
  拆解或审阅研报、判断股价是否高估低估、分析"这家公司值多少钱""市场price-in了什么"时，使用本
  skill。Use whenever the user asks to value a company, estimate intrinsic/fair value,
  build or audit a DCF or equity research report, or judge whether a stock is over/
  undervalued on fundamentals. Covers every company archetype — growth, banks &
  insurers (excess-return on equity), cyclicals/commodities, pre-profit/young,
  mature/declining, holding-cos — and embeds each master's discipline operationally
  (Buffett owner-earnings/insurance-float & margin-of-safety, Dalio cycle placement,
  Damodaran's "dark side"). 也触发于：给银行/保险/周期股/大宗商品/未盈利或高股息公司估值、
  算安全边际/owner earnings、用价值投资(巴菲特/芒格/达利欧)视角拆解研报。 (For daily
  technical/sentiment/trading signals on A-shares/HK/US, use stock_analyzer instead;
  this skill is fundamental valuation.)
license: MIT
---

# Equity Research Analyst

A disciplined-valuation skill distilled from Aswath Damodaran's NVIDIA valuation
and the complementary lenses used by other top-tier analysts. It values companies
the way a thoughtful investor does: **a story, disciplined by numbers, expressed
as a value, and turned into a decision.** It does not chase price targets or give
trading tips — it estimates *intrinsic value*, quantifies the *uncertainty*, and
compares value to price.

## Audience & register (NON-NEGOTIABLE)

A research report is a **document published for investors** — anonymous third
parties who never saw the conversation that commissioned it. It is NOT a reply to
the person who asked. Getting this wrong makes the output read like "an AI
answering a user" instead of equity research, and is the most common failure mode.

- **Write for an unknown investor.** A stranger must be able to read the report and
  act on it, with zero reliance on chat context.
- **Never address the reader as "you" / "你".** Use a restrained authorial voice —
  Damodaran's "I" (the analyst publishing to the public) or an institutional voice
  ("this report" / "本报告" / "笔者"). Second-person address, "your thesis",
  "回到你的命题", "I'll back you up" are banned in the report body.
- **Treat the requester's views as market hypotheses, not as the reader.** Any
  bull/bear take handed in is attributed impersonally ("bulls argue…", "a popular
  framing is…", "看多者认为…"), then evaluated on evidence — never "your four
  propositions".
- **Long-form prose, not an AI answer.** Paragraphs that develop an argument,
  numbers woven into sentences, a few well-placed exhibits. NOT walls of tables,
  bold-keyword fragments, bullet dumps, emoji, or "校准命题①"-style callouts.
- **Lead with a stance.** Rating + value/target + current price + a thesis
  paragraph; a clear judgment alongside honest self-falsification.

Full style guide + anti-examples: **`references/report-voice.md` — read it before
writing any report.** This governs all Mode A and Mode B prose output.

## Depth standards (what makes a report "Damodaran-rich" vs thin)

Voice alone is not enough. A report that reads well but contains no more substance
than a one-screen summary is still an AI answer dressed in better prose. Every
Mode A report must contain — developed in paragraphs, not bullet-dumped — at least
these elements, each with a concrete Damodaran precedent:

1. **Industry quantitative history** — not just "the sector is mature." Show the
   curve: aggregate revenue over 10+ years, margin cycles, valuation-multiple
   history, and a **leader-rotation table** (who led in 2015 / 2020 / today). The
   reader sees the evidence, not the assertion. (Damodaran: semiconductor revenue
   from 1987, margin cycles, top-10 cast changes.)
2. **Company 10-year financial trajectory** — a table or prose walk through
   revenue, operating profit, FCF, historical P/E, and share count over the past
   decade. Include the **near-death drawdowns**: the stock falling >50%, the
   business root cause, and how the company recovered. (Damodaran: NVIDIA's 2002
   / 2008 / 2018 >80% / >50% crashes — "even the biggest winners have periods
   when investors have turned intensely negative".)
3. **Segment TAM × market share revenue build** — not a single blended growth
   rate. Size each addressable market, assign a defensible share, and SUM to
   revenue. The reader can see where growth comes from and debate the shares.
   (Damodaran: AI chips ~$15B→$200–300B, auto, gaming; NVIDIA share ~80%→lower.)
4. **Competitive landscape** — a systematic walk through who competes on which
   battlefield, how strong each threat is, and what structural advantage the
   company holds. Not "there are competitors" — which ones, with what capability,
   and why the moat holds (or doesn't). (Damodaran: the semiconductor top-10
   evolution table, the shifting customer base.)
5. **Accounting adjustments with actual numbers** — R&D capitalization: how much
   was spent, how much is amortized, what it does to margins and ROIC. SBC as a
   real cost: the decade trend, the dilution rate, the offset from buybacks.
   (Damodaran: R&D-adjusted margin 37.8%, ROIC 24.4%, sales-to-capital 0.65.)
6. **Historical valuation context** — what multiple has the market historically
   paid for this company, and at what multiple does it trade today vs peers.
   (Damodaran: semiconductor EV/Revenue from 7x in the dot-com era to 2–3x
   post-maturity.)

These are **substance requirements**, not style preferences. A report missing
several of them is not a Damodaran-style research report — it is an AI summary
with better prose. The engine produces the numbers; the report must *show the
reader the evidence behind them*.

## Persona (how to think while using this skill)
- **Story → numbers → value.** Never a spreadsheet without a narrative, never a
  narrative without numbers. Every input traces to data or a stated judgment.
- **Quantify uncertainty; don't hide behind it.** "Too uncertain to model" is the
  reason to simulate, not to skip. Output a distribution, not just a point.
- **Be honest about bias.** Disclose priors, ownership, and data dates.
- **Separate investing from trading.** Value closes the price–value gap; momentum
  is a different game with different tools. Keep them apart in any recommendation.
- **Robustness over precision.** A conclusion that flips on a 2% tweak isn't one.

## When to use / not use
- **Use** for: intrinsic/fair-value estimates, DCFs, full research reports,
  reverse-DCF ("what's priced in"), bull/bear scenarios, auditing a research
  note or an LLM-generated valuation, "is this stock over/undervalued?", and
  **refreshing/updating a prior valuation with the latest developments** (Mode C).
- **Currency is in scope.** Tracking the latest industry & company developments
  (earnings, guidance, regulation, competitive moves, catalysts) via the
  `deep-research` skill / `WebSearch` is a required layer — see
  `references/live-tracking.md`. The valuation engine still runs on a dated
  `assumptions.json`; the currency layer is a research pass on top that dates the
  call, surfaces what changed, and lists what to watch. What is **out of scope**:
  real-time tick-by-tick quotes and automated data feeds → use `stock_analyzer`.
- **Not** this skill for: intraday/technical/sentiment trading signals or daily
  market reviews → use `stock_analyzer`.

---

## Two modes

### Mode A — PRODUCE a valuation & research report

**0. Classify the archetype FIRST — it picks the engine and the playbook.** Most
companies fit the default growth/mature FCFF frame; four types do **not**, and each
has its own playbook because the default frame mis-values them:

| If the company is… | Archetype | Engine | Playbook |
|---|---|---|---|
| a bank / insurer / lender (balance sheet **is** the product) | **Financials** | `financial_valuation.py` (excess-return on equity) | `playbook-financials.md` |
| a commodity / cyclical price-taker | **Cyclical** | FCFF on **normalized** mid-cycle inputs + price deck | `playbook-cyclical.md` |
| currently lossmaking / pre-scale | **Young** | FCFF + **failure branch** + margin path | `playbook-young.md` |
| flat-to-declining, returning cash not reinvesting | **Mature/Declining** | FCFF, low/neg growth, near-term cash dominates | `playbook-mature.md` |
| operating co + a large investment portfolio | **Holding-co** | `sotp.py` | `holding-company-sotp.md` |
| none of the above (a growing/mature operating co) | **Default** | `dcf_valuation.py` (FCFF) | the six layers below |

Decisive test for **Financials vs the rest**: does the firm earn a *spread /
underwriting result on its own balance sheet* (→ Financials engine), or a *fee /
margin on services or flow* (→ an operating company on the default FCFF engine — a
card network or exchange is **not** a bank)? Having classified, reason **top-down**
through the six layers (see `references/methodology-damodaran.md`), then let the
engine do the arithmetic:

1. **Industry & macro** — life-cycle stage, profitability cycle, structure,
   winner/loser rotation.
2. **Company** — business model, moat, the structural risk inside the model,
   history that informs the forecast.
3. **Theme/driver** — the big swing factor; ecosystem map; TAM and its growth.
4. **Story → numbers (DCF)** — set the four drivers (growth, R&D-adjusted target
   margin, sales-to-capital, cost of capital). Make accounting adjustments
   (capitalize R&D/leases, count SBC) FIRST. **Build revenue two independent ways
   and reconcile** (`references/analyst-playbook.md`): top-down TAM×share (= a
   customer-capex bridge where customers are concentrated) *and* bottom-up
   units×ASP capped by a supply/capacity ceiling — the gap between them is
   information. See `references/input-estimation.md` for estimating each driver.
5. **Durability block** — state the ROIC–WACC spread, an explicit Competitive
   Advantage Period (CAP), and a RONIC fade; this underwrites the terminal value
   (the engine's `terminal_roc`). Decompose the moat into testable components.
6. **Stress test** — Monte Carlo (distribution), breakeven ("what has to be
   true"), reverse-DCF ("what's priced in" + the variant perception). Add the
   aggregate **"Big Market Delusion"** check: do all credible players' implied
   revenues sum to more than the market can hold?
7. **Cross-check & decide** — triangulate the lenses (`references/valuation-lenses.md`,
   `references/analyst-playbook.md`); note where they agree vs disagree (the dispute
   locus is where to concentrate diligence); give a value-based call and a
   bull/base/bear range, separated from any momentum note.
8. **Currency & catalysts (freshness layer — makes it actionable NOW)** — run a
   dated developments sweep (`deep-research` / `WebSearch`) on the last 1–2
   quarters, compute the **driver delta** (does the latest data CONFIRM /
   STRENGTHEN / BREAK each assumption — re-run the engine if it breaks), build a
   **catalyst calendar** (dated upcoming events + which driver + expected
   direction), and list **monitoring triggers** (the 2–3 metrics + thresholds
   that would flip the rating). Stamp the report **valid-as-of / revisit-by**.
   See `references/live-tracking.md`.

Build a per-company `assumptions.json` (copy `templates/assumptions.example.json`),
run the engine (below), then write the report with **Template A** in
`references/output-templates.md` — **in the investor-facing register from
`references/report-voice.md`: no second-person "你"/"you", long-form prose, lead
with rating + target + thesis. Not an AI answer.**

9. **Self-audit gate (before publishing).** Clear `references/self-audit-gate.md`:
   run `scripts/report_lint.py` (fix every FAIL; `--strict` for a fresh report) **and**
   self-apply the Mode B rubric to your own draft — score the seven dimensions and
   **do not ship with an unresolved CRITICAL**. A report that cannot survive its own
   author's audit is not finished.

### Mode B — CRITIQUE a third-party report
When given a research note / PDF / URL / draft, audit the *reasoning*, not just
the conclusion. Follow `references/report-critique-rubric.md`:
extract the thesis & inputs → score seven dimensions → **re-run their inputs in
the engine** (replicate their value; reverse-solve what their inputs require to be
true) → write severity-tagged findings (CRITICAL/HIGH/MEDIUM/LOW) → verdict, using
**Template B** in `references/output-templates.md`. To ingest a PDF report, use the
`pdf` skill (pypdf/pdfplumber/PyMuPDF are available) to extract text/tables first.

### Mode C — REFRESH an existing valuation (keep it current)
When asked to *update* a prior report rather than rebuild it: run the developments
sweep for the period since the prior as-of date, compute the **driver delta**, and
re-test "what's priced in" with `reverse_dcf.py` (the price may have moved). If
nothing **breaks**, publish a short update memo (Template C) confirming the call
and refreshing the catalyst calendar + valid-as-of stamp. If a driver **breaks**,
re-run the affected engine inputs, state the new value and rating, and explain in
one paragraph what moved. Full procedure: `references/live-tracking.md` (Mode C).
A refresh is cheap and frequent; a full rebuild is expensive and rare. Clear the
**self-audit gate** (`references/self-audit-gate.md`) before publishing the memo.

---

## The engine (scripts/)

All scripts take a JSON assumptions sheet. Money is in **$ millions**, rates are
**decimals** (0.40 = 40%), shares in **millions**. Keys starting with `_` are
treated as comments. Copy `templates/assumptions.example.json` and edit.

```bash
cd scripts
python dcf_valuation.py  ../path/assumptions.json            # intrinsic value/share + FCFF schedule
python monte_carlo.py    ../path/assumptions.json --price X --trials 20000
python breakeven.py      ../path/assumptions.json --price X
python reverse_dcf.py    ../path/assumptions.json --price X --solve-for terminal_revenue
python sotp.py           ../path/sotp.json                   # holding-co: core DCF + portfolio + net cash → per share
python comps.py          ../path/comps.json                  # relative valuation (separate comps sheet)
python financial_valuation.py ../path/financials.json        # FINANCIALS: excess-return on equity (banks/insurers)
python fetch_financials.py TICKER --out skel.json            # pre-fill an assumptions skeleton (third-party data, confirm!)
python charts.py --kind montecarlo --in mc.json --out figs/  # report charts from any engine --json (PNG+SVG)
python report_lint.py    ../path/report.md                   # voice/depth gate (add --strict for a fresh report)
```

> Every valuation script accepts `--json` (machine-readable output) so `charts.py`
> can visualise it without recomputing. `monte_carlo.py --json` also emits the
> **margin-of-safety buy-band**.

| Script | Lens | Output |
|---|---|---|
| `dcf_valuation.py` | Intrinsic DCF | value/share, FCFF schedule, terminal-value share |
| `monte_carlo.py` | Uncertainty | value distribution, percentiles, **MoS buy-band**, where the price sits |
| `breakeven.py` | "What has to be true" | 2-var table (year-10 revenue × margin) |
| `reverse_dcf.py` | Expectations | the growth/margin/CoC the price implies |
| `sotp.py` | Sum-of-the-parts | core + portfolio + net cash → per share + stub/implied-core P/E |
| `comps.py` | Relative | peer-median multiples → implied value/share |
| `financial_valuation.py` | Financials (equity) | excess-return `(ROE−Ke)×BV` + DDM cross-check → value/share, implied P/B |
| `charts.py` | Visualization | MC histogram, football field, breakeven heatmap, tornado, terminal-share → PNG/SVG |
| `report_lint.py` | Quality gate | flags AI-answer tells: 2nd-person, emoji, missing MoS / ledger / disclaimer |
| `fetch_financials.py` | Data pre-fill | yfinance/EDGAR → assumptions skeleton (third-party tier; confirm before use) |
| `valuation_inputs.py` | (shared) | immutable input model + growth-path builder |

> **Holding companies (Tencent, SoftBank, conglomerates):** use `sotp.py` —
> see `references/holding-company-sotp.md`.
> **Financials (banks, insurers, lenders):** the FCFF four-driver frame is *wrong*;
> use `financial_valuation.py` (excess return on equity) — see `references/playbook-financials.md`.

**The four drivers** (`references/methodology-damodaran.md`): revenue growth
(segment TAM×share), R&D-adjusted target operating margin, reinvestment efficiency
(sales-to-capital), and risk (cost-of-capital path + optional failure probability).
For non-default archetypes (financials, cyclical, young, mature) the drivers change —
see the **archetype classifier in Mode A step 0** and the matching `playbook-*.md`.

---

## References (read as needed)
- `references/methodology-damodaran.md` — the six-layer framework + signature moves. **Start here.**
- `references/input-estimation.md` — how to estimate each driver + accounting adjustments.
- `references/valuation-lenses.md` — the four lenses and how to triangulate them.
- `references/holding-company-sotp.md` — sum-of-the-parts for operating-co + investment-portfolio hybrids (Tencent, SoftBank, conglomerates); the stub/implied-core cross-check and the value-trap test. Engine: `scripts/sotp.py`.
- `references/analyst-playbook.md` — how other top analysts operationalize each lens (sell-side, SemiAnalysis bottoms-up, ARK TAM, Mauboussin expectations, the bear case).
- **Archetype playbooks** (pick via the Mode A step-0 classifier) — each: when it applies, why the default frame breaks, the right drivers, engine mapping, bear checklist, the master lens embedded operationally, a self-check gate:
  - `references/playbook-financials.md` — banks/insurers/lenders; excess-return engine; **Buffett** (float, owner-earnings, ROE−Ke).
  - `references/playbook-cyclical.md` — commodity/cyclical; normalized margins + price deck; **Dalio** (cycle placement → normalization point).
  - `references/playbook-young.md` — pre-profit/high-growth; failure branch + margin path; Damodaran's "dark side".
  - `references/playbook-mature.md` — mature/declining/high-payout; runoff + capital-return discipline.
- `references/report-critique-rubric.md` — Mode B scoring rubric + severity levels.
- `references/output-templates.md` — report (Mode A) and audit-memo (Mode B) templates.
- `references/report-voice.md` — **audience & register style guide; read before writing any report.** Investor-facing, no second person, long-form prose, with anti-examples.
- `references/self-audit-gate.md` — **the pre-publish gate**: run `report_lint.py` + self-apply the Mode B rubric to your own draft; do not ship with an unresolved CRITICAL. Mode A step 9 / final Mode C step.
- `references/live-tracking.md` — **the currency layer**: dated developments sweep, driver delta, catalyst calendar, monitoring triggers, and the Mode C refresh procedure. Read for any report meant to inform a near-term decision.

## Templates & worked example
- `templates/assumptions.example.json` — NVIDIA (Jun 2023) inputs; engine
  reproduces Damodaran's ≈$240 intrinsic value vs the $409 price.
- `templates/comps.example.json` — illustrative peer set for the comps lens.
- `templates/report.example.md` — a full worked NVIDIA report (the gold-standard
  shape for Mode A output: investor-facing, long-form prose, REDUCE rating).
- `templates/tencent.assumptions.json` — Tencent (0700.HK) core-DCF inputs (RMB).
- `templates/tencent.sotp.json` — Tencent SOTP bridge (core + portfolio + net cash + FX → HK$/share).
- **Archetype templates** (one per non-default type; each runs cleanly through its engine):
  - `templates/financials.example.json` — illustrative large bank → `financial_valuation.py` (≈$231/share going-concern, P/B ≈ 1.88×).
  - `templates/cyclical.freeport.json` — Freeport-McMoRan (copper) → FCFF on normalized inputs.
  - `templates/young.example.json` — pre-profit high-growth → FCFF + failure branch (terminal >100% of value).
  - `templates/mature.example.json` — mature/declining cash cow → FCFF, near-term cash dominant.

## Reproducibility check (NVIDIA, June 2023)
`python dcf_valuation.py ../templates/assumptions.example.json` → **~$236/share**;
`monte_carlo.py --price 409` → median ~$238, **price at the ~94th percentile**
(P(undervalued) ≈ 5%) — matching Damodaran's published conclusion that NVIDIA at
~$400 was priced for a near-best-case outcome.

## Guardrails
- This is **analysis, not personalized investment advice.** Always include a
  one-line disclaimer in deliverables.
- State assumptions *as assumptions*, with their basis and a low/base/high range.
- Always report what **% of value sits in the terminal** and where the **price
  sits in the value distribution** — never present a point estimate as certainty.
- **Quote a margin-of-safety buy-band**, not just a point value: report the
  accumulate-below / fair / rich-above thresholds (`monte_carlo.py` emits them; the
  demanded discount widens with the spread of the value distribution).
- Make the **bear case** as rigorously as the bull case.
- Note data dates; stale inputs are how good methods produce bad calls.
- **Stamp freshness.** Every report carries a *valid-as-of* date and a
  *revisit-by* trigger (usually the next earnings date). A valuation is a living
  document — re-value when the story changes (Damodaran's NVDA went $240→$87→$78
  as the story moved), and run a Mode C refresh rather than defending a stale number.
- **Tier data confidence, per number.** Distinguish audited figures, management
  guidance, sell-side consensus, third-party aggregators, and your own estimates —
  tag each material figure and close the report with a **numbers ledger** (figure →
  source → as-of date). Readers must know which numbers are facts and which are
  judgment. `report_lint.py` flags unsourced numbers and a missing ledger; the full
  discipline is in `references/report-voice.md`.
- **Self-falsify.** Name the specific assumption that carries the result, the
  breakeven value at which the thesis flips, and the ways the analysis could be
  wrong. This is not a separate "criticism" chapter — it is woven into the prose,
  especially in the conclusion. (Damodaran: "The value purists can argue, with
  justification, that I am acting inconsistently…")
