# Publishing Contract

Read this before writing, charting, auditing, or rendering a report. It is the
shared contract between `write-report`, `generate-charts`, `generate-pdf`, and
`self-audit`.

## 1. Report Language Lock

Choose `report_lang` before the first draft:

1. The user's requested output language wins.
2. If the user writes in Chinese and asks for a report, default to `zh-CN`.
3. If sources are mostly English but the requested output is Chinese, keep the
   report in Chinese and translate broker-template labels.
4. Ask only when the request language and expected audience language materially
   conflict.

Propagate the same language into:

- report markdown;
- chart manifest (`lang`);
- chart titles, axes, legends, and source notes;
- PDF renderer (`--lang` or project wrapper auto-detection);
- lint and self-audit checks.

For Chinese reports, English may appear only in tickers, company legal names,
proper nouns, source titles, quoted source snippets, formulas, and unavoidable
regulatory terms. Broker-template labels must be translated.

Chinese label mapping:

| English template label | Chinese report label |
|---|---|
| Rating | 评级 |
| Intrinsic value / Fair value | 内在价值 / 合理价值 |
| Current price / Price | 当前价格 / 股价 |
| Upside / Downside | 上行空间 / 下行空间 |
| Thesis | 核心结论 |
| MoS buy-band | 安全边际区间 |
| Figure | 图表 |
| Analyst Certification | 分析师认证 |
| Meaning of Ratings | 评级定义 |
| Conflicts of Interest | 利益冲突披露 |
| Price Target Methodology | 目标价方法论 |

Chinese rating vocabulary:

| English | Chinese |
|---|---|
| Buy / Overweight / Outperform | 买入 / 增持 / 跑赢 |
| Hold / Neutral / Equal-weight | 持有 / 中性 / 同步大市 |
| Sell / Reduce / Underweight | 卖出 / 减持 / 低配 |

Hard-stop examples in Chinese reports: `THESIS`, `INTRINSIC`, `DOWNSIDE`,
`MoS BUY-BAND`, `Figure N:`, and standalone English ratings such as `HOLD` or
`REDUCE`.

## 2. Source Confidence Tiers

Every load-bearing figure needs a tier and as-of date in the numbers ledger.

| Tier | Use for |
|---|---|
| T0 - audited/official | annual reports, exchange filings, regulatory data |
| T1 - company primary | interim reports, presentations, management guidance |
| T2 - recognized third party | Wind/Bloomberg/FactSet/industry bodies/broker consensus |
| T3 - derived estimate | analyst calculation from stated inputs |
| T4 - fallback/proxy | stale cache, comparable proxy, uncached fallback |

Rules:

- Never present T4 data as current fact.
- If Damodaran or market data is stale, disclose age and fallback class.
- Put the source tier in the ledger even when inline prose omits it for style.

## 3. Cyclical Valuation Discipline

For commodity, panel, memory, shipping, chemical, metal, and other price-taking
cyclicals:

- value mid-cycle economics, not the latest margin;
- normalize across at least one full peak-to-trough cycle when data permits;
- use a defended price deck tied to marginal cost or capacity-clearing price;
- separate maintenance capex from growth capex;
- test balance-sheet survival at trough conditions;
- set terminal ROC close to terminal cost of capital unless the company has
  non-commodity pricing power;
- run reverse DCF as "what cycle point is priced in" rather than only
  "expensive/cheap".

Minimum cyclicals output:

- cycle position (early/mid/late; business/debt-cycle context where relevant);
- current margin vs normalized margin vs peak/trough band;
- base price deck and unit;
- cost-curve or capacity position;
- price-implied margin or price deck from reverse DCF;
- wide margin-of-safety band around normalized value.

## 4. Chart and Figure Contract

Markdown chart references use:

```markdown
![](figs/<TICKER>_<kind>)
```

No file extension. No ticker subdirectory. The renderer tries SVG first, then
PNG.

For Chinese reports:

- chart titles, axes, legends, annotations, and captions must be Chinese;
- use CJK-capable fonts and fail fast if none are available;
- figure prefixes must render as `图表 N：`, not `Figure N:`;
- units should be localized where natural (`亿元`, `%`, `倍`).

## 5. Pre-Publish Gates

Fresh reports must pass:

```bash
python scripts/report_lint.py output/TICKER_research_report.md --strict
python src/common/build_report.py TICKER
```

After PDF generation, inspect preview PNGs or rendered PDF pages. Confirm:

- first-page rating box language matches `report_lang`;
- all charts are embedded and legible;
- no CJK tofu or missing glyph boxes;
- no logo/header overlap;
- page numbers, disclosure appendix, and disclaimer exist;
- no forbidden English template labels remain in a Chinese report.

If a Type-B gate cannot be independently reviewed, record it as unverified and
carry the limitation into the final note. Do not silently self-acquit.
