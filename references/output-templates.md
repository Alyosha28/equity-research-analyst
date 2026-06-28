# Output Templates

Two deliverables: a **research report** (Mode A) and an **audit memo** (Mode B).
Both are written for investors, in the register defined in
[`report-voice.md`](report-voice.md) — **read it first.** The outlines below are
*section maps for long-form prose*, not bullet skeletons to fill: each heading
names the argument that section must develop in paragraphs. Lead with a stance;
weave numbers into sentences; keep exhibits sparse.

---

## Template A — Equity research report (Mode A)

A header block, then ~3,500–5,000 words of prose across these sections. Use a
restrained authorial/institutional voice; never address the reader as "you"/"你".

**Header (a compact block, not the whole report):** Company (ticker) · Rating ·
Target/intrinsic value · Current price · Date. Then a 3–5 sentence **investment
thesis** stated impersonally — the gap between value and price and the single
reason it exists.

**Opening.** The core thesis as a hook, in the author's voice — what the prevailing
market debate gets wrong and what actually decides the call. (Damodaran opens with
a framing, not a table.)

**Industry & macro.** Life-cycle stage, profitability cycle, structure, how winners
rotate — prose that sets the field the company plays on.

**The company.** Business model and how it actually makes money; the moat and its
durability; the structural risk baked into the model; the history that informs the
forecast (growth, margins, drawdowns).

**The driver / theme.** The big swing factor; where the company sits in the value
chain; the size and growth of the prize.

**Story → numbers (intrinsic DCF).** Translate the narrative into the four drivers
— each justified in a sentence or two with its basis and a low/base/high — then the
value and the % of value sitting in the terminal. Engine: `dcf_valuation.py`.

**Sum-of-the-parts** (holding-co hybrids only). Core operating value + investment
portfolio (with haircuts) + net cash → per share; plus the stub / implied-core
multiple. Engine: `sotp.py`; method: [`holding-company-sotp.md`](holding-company-sotp.md).

**What the market is pricing.** Reverse-DCF and breakeven — the growth/margin/CoC
the price implies, and whether those expectations are plausible. The crux of any
over/undervaluation claim.

**Scenarios.** Two to four internally-consistent futures (bull/base/bear), each a
full driver set, with value ranges. Prefer discrete scenarios to a smooth
simulation when the dominant risk is a structural break.

**Evaluation of the prevailing market narratives.** Take the bull/bear views
circulating on the name (attributed impersonally) and adjudicate each on the
evidence assembled above.

**Recent developments & catalysts (as of DATE).** A dated prose section (see
[`live-tracking.md`](live-tracking.md)): what changed in the last 1–2 quarters and
whether each datum CONFIRMS / STRENGTHENS / BREAKS a driver; then a compact
**catalyst calendar** (dated upcoming events · driver hit · expected direction);
then the **monitoring triggers** (the 2–3 metrics + thresholds that would flip the
rating). This is the layer that makes the report actionable now, not six months ago.

**Conclusion & rating rationale.** The judgment, stated plainly, and why the rating
and target follow from the analysis. Separate the value call from any momentum note.
Stamp the call **valid-as-of [date] · revisit-by [next catalyst]**.

**Report limitations / what could prove this wrong.** The assumptions that carry
the result, the biases, the data vintage — honest self-falsification.

**Key risks & disclaimer.** The monitorable risks, and a one-line not-advice
disclaimer with data dates.

**Disclosures & Certifications appendix (MANDATORY for every Mode A report).** This
appendix is NOT optional — a report without it fails the self-audit gate and cannot be
published under a regulated entity's name. The appendix must contain these minimum
sections, detailed below in [Appendix B: Disclosures & Certifications](#appendix-b-disclosures--certifications):

1. **Analyst Certification** (SEC Regulation AC / 17 CFR 242.501 compliant)
2. **Rating Distribution table** (FINRA Rule 2241(c) compliant)
3. **Meaning of Ratings** (definitions for each rating category)
4. **Conflicts of Interest disclosure** (FINRA Rule 2241(c)(4) compliant, items A through I)
5. **Price Target Methodology** (at least two methods, triangulation approach, valuation horizon)
6. **Risk Factors** (specific, monitorable risks to the thesis)
7. **For China-listed names:** CSRC/SAC independence statement per the 2024 SAC 指引 (《证券公司提供投资价值研究报告行为指引》) and the 2025 SAC 《发布证券研究报告执业规范》修订版.

> Appendix A (optional): the assumptions table (the JSON), sources & dates, accounting
> adjustments made.

---

## Appendix B: Disclosures & Certifications (full template)

This is the mandatory disclosure appendix for every Mode A equity research report.
The text below is **boilerplate with fill-in fields** denoted `[like this]`. The
write-report agent MUST replace every bracket-bounded field with actual data from the
analysis. Fields where the answer is "no" or "none" should state that plainly — never
omit a required disclosure line.

### B.1 Analyst Certification (Reg AC)

> I, `[Analyst Name]`, hereby certify that all of the views expressed in this
> research report accurately reflect my personal views about the subject company or
> companies and its or their securities. I also certify that no part of my
> compensation was, is, or will be, directly or indirectly, related to the specific
> recommendations or views expressed in this report.
>
> Unless otherwise stated, the individual(s) listed as the author(s) of this report
> are analysts in `[Firm Name]`'s `[Global Investment Research / Research]` division.

*Regulatory basis: SEC Regulation AC (17 CFR 242.501). If any part of the analyst's
compensation was, is, or will be related to the specific recommendations or views,
option (ii) of Rule 501(a)(2) must be used instead — disclose the source, amount, and
purpose of such compensation, and state that it could influence the recommendations.*

### B.2 Rating Distribution

As of `[Quarter-End Date, e.g., March 31, 2026]`, `[Firm Name]`'s equity research
coverage universe comprised `[N]` companies. The distribution of investment ratings
across the coverage universe is as follows:

| Rating | % of Total Coverage | % Investment Banking Clients |
|--------|-------------------|----------------------------|
| Buy / Overweight / Outperform | `[XX]`% | `[XX]`% |
| Hold / Neutral / Equal-Weight | `[XX]`% | `[XX]`% |
| Sell / Underweight / Underperform | `[XX]`% | `[XX]`% |

*"Investment Banking Clients" refers to companies for which `[Firm Name]` has provided
investment banking services (underwriting, M&A advisory, or similar) in the preceding
12 months.*

For independent / unaffiliated research (no banking business), replace the "% IB
Clients" column with: *"The firm conducts no investment banking business and has no
investment banking clients."* — the distribution table itself must still be shown.

### B.3 Meaning of Ratings

| Rating | Definition |
|--------|-----------|
| **Buy / Overweight / Outperform** | The analyst expects the total return (price appreciation plus dividend yield, if any) of the subject security to exceed the return of the coverage universe median, or a specified benchmark, over a **12-month** investment horizon. |
| **Hold / Neutral / Equal-Weight** | The analyst expects the total return of the subject security to be in line with the return of the coverage universe median, or a specified benchmark, over a **12-month** investment horizon. |
| **Sell / Underweight / Underperform** | The analyst expects the total return of the subject security to be below the return of the coverage universe median, or a specified benchmark, over a **12-month** investment horizon. |

*Ratings are relative to the coverage universe median unless an absolute benchmark is
specified. A rating is not a recommendation to buy, sell, or hold any security.
Ratings may be suspended or discontinued at any time.*

### B.4 Conflicts of Interest Disclosure

In accordance with FINRA Rule 2241(c)(4) and SEC Regulation AC, the following
disclosures are made with respect to `[Company Name]` (`[TICKER]`) as of
`[Report Date]`:

| Disclosure Item (FINRA 2241(c)(4)) | Status |
|-------------------------------------|--------|
| (A) The research analyst or a member of the analyst's household has a financial interest in the debt or equity securities of the subject company (including any option, right, warrant, future, or long or short position). | `[Yes / No]`. `[If Yes: state the nature of the interest]` |
| (B) The research analyst has received compensation based upon the firm's investment banking revenues. | `[Yes / No]` |
| (C)(i) The firm or an affiliate managed or co-managed a public offering of securities for the subject company in the past 12 months. | `[Yes / No]` |
| (C)(ii) The firm or an affiliate received compensation for investment banking services from the subject company in the past 12 months. | `[Yes / No]` |
| (C)(iii) The firm or an affiliate expects to receive or intends to seek compensation for investment banking services from the subject company in the next 3 months. | `[Yes / No]` |
| (D) The firm or an affiliate received compensation from the subject company for products or services other than investment banking services in the past 12 months. | `[Yes / No]` |
| (E) The subject company is, or over the past 12 months has been, a client of the firm (identifying the types of services: investment banking services, non-investment banking securities-related services, or non-securities services). | `[Yes / No]`. `[If Yes: specify type(s) of services]` |
| (F) The firm or an affiliate beneficially owns 1% or more of any class of common equity securities of the subject company. | `[Yes / No]` |
| (G) The firm was making a market in the securities of the subject company at the time of publication or distribution of this report. | `[Yes / No]` |
| (H) The research analyst received any compensation from the subject company in the past 12 months. | `[Yes / No]` |
| (I) Any other material conflict of interest of the research analyst or firm that the research analyst or an associated person with the ability to influence the content of this report knows or has reason to know. | `[None / Describe the conflict]` |

*For independent / unaffiliated research reports: a statement that the analyst and
firm are independent of the subject company, receive no compensation from it, and
have no material conflicts of interest may replace the line-item table, provided the
statement addresses each disclosure item (A) through (I) substantively.*

### B.5 Price Target Methodology

The price target and/or intrinsic value estimate for `[Company Name]` (`[TICKER]`)
was derived using the following valuation methods. The final target reflects a
triangulation across methods, with weights assigned by the analyst based on each
method's applicability to the company's business model, life-cycle stage, and the
availability of reliable inputs.

**Method 1 — Discounted Cash Flow (DCF):** *Primary.* Free cash flows to the firm
were projected over an explicit forecast period of `[N]` years and discounted at a
weighted average cost of capital (`[WACC range]`, transitioning from `[initial]`% to
`[terminal]`%). The terminal value was estimated using the perpetual growth method
with a terminal growth rate of `[g]`%, anchored to but not exceeding the risk-free
rate. Accounting adjustments applied: `[e.g., R&D capitalization, operating lease
capitalization, SBC expensing]`. DCF-derived intrinsic value: **`$[value]` per
share**.

**Method 2 — Reverse DCF / Market-Implied:** *Secondary.* The current market price
was inverted to solve for the growth rate, operating margin, and/or return on
invested capital that the market price implies. These implied inputs were assessed
for plausibility against: (a) the company's own historical trajectory, (b) the
industry's economics and growth ceiling, and (c) the competitive landscape. The gap
between the price-implied driver and the analyst's base-case driver is the crux of
the rating.

**Method 3 — `[Comparables Analysis / Sum-of-the-Parts / Dividend Discount Model /
Monte Carlo Simulation / Other]`:** `[Description of the method, including the
specific comps set and multiples applied, or the SOTP components and holding-company
discount, or the simulation parameters and distribution assumptions. Always state
the resulting value range.]`

**Triangulation summary:**

| Method | Value Range ($/share) | Weight |
|--------|----------------------|--------|
| DCF (primary) | `[$low – $high]` | `[XX]`% |
| Reverse DCF / Market-Implied | `[$low – $high]` | `[XX]`% |
| `[Method 3]` | `[$low – $high]` | `[XX]`% |
| **Target / Intrinsic Value** | **`$[value]`** | 100% |

**Valuation horizon:** 12 months from the date of this report. **Key assumptions
that carry the result:** `[list the 2–3 most sensitive drivers, e.g., terminal growth
rate, target operating margin, cost of capital.]` The assumptions table (Appendix A)
provides the full driver set with low/base/high ranges.

### B.6 Risk Factors

The following risks, if they materialize, could cause the actual results or
performance of `[Company Name]` to differ materially from the views expressed in this
report. Each risk is specific, monitorable, and tied to a driver in the valuation
model.

| Risk | Driver(s) Affected | Severity | Monitoring Trigger |
|------|-------------------|----------|-------------------|
| `[Risk 1]` | `[Driver, e.g., Revenue growth]` | `[High / Med]` | `[Observable threshold]` |
| `[Risk 2]` | `[Driver]` | `[High / Med]` | `[Observable threshold]` |
| `[Risk 3]` | `[Driver]` | `[High / Med]` | `[Observable threshold]` |
| `[Risk 4]` | `[Driver]` | `[High / Med]` | `[Observable threshold]` |
| `[Risk 5]` | `[Driver]` | `[High / Med]` | `[Observable threshold]` |

*This list is not exhaustive. Investors should review the company's most recent
filings with the relevant securities regulator (SEC 10-K/20-F, CSRC/SSE/SZSE filings,
HKEX filings, etc.) for a comprehensive discussion of risk factors.*

### B.7 General Disclaimer

This report is published for informational and educational purposes only and does not
constitute investment advice, a solicitation, or an offer to buy or sell any security.
The analysis herein is based on publicly available information as of
`[Information Cutoff Date]`. The author and `[Firm Name]` make no representation as
to the accuracy or completeness of such information and undertake no obligation to
update this report. Past performance is not indicative of future results. Investing
in securities involves risk, including the possible loss of principal. Readers should
conduct their own independent due diligence and consult with a qualified financial
advisor before making any investment decision.

*Report published: `[Publication Date]`. Valuation assumptions as of:
`[Assumptions Date]`. All figures in `[Currency]` unless otherwise stated.
valid-as-of `[Date]` · revisit-by `[Next Catalyst Date]`.*

---

### B.8 China-Listed Names — Supplemental Independence Statement

**This section is REQUIRED for any report on a China A-share listed company
(SSE/SZSE/BJSE), a company with a primary CSRC-regulated listing, or a company whose
principal operating entity is a China-domiciled issuer.** For Hong Kong-listed
companies with primarily China operations, include this section as a best practice.

In accordance with the Securities Association of China (SAC / 中国证券业协会)
*Guidelines for Securities Companies Providing Investment Value Research Reports*
(《证券公司提供投资价值研究报告行为指引》, SAC Announcement No. 96 of 2024,
effective May 24, 2024) and the SAC *Code of Conduct for Publishing Securities
Research Reports* (《发布证券研究报告执业规范》, 2025 revision):

**分析师独立性声明 (Analyst Independence Statement):** 本报告由分析师独立撰写，基于
公开信息和合理推断。报告中的盈利预测和估值结论由分析师独立判断，未受投资银行业务
部门、证券发行与承销部门、发行人及其他利益相关方的影响或干扰。撰写本报告的分析师
及其关联方与所覆盖公司之间不存在影响报告客观性、独立性的利益冲突。分析师薪酬不与
特定项目的业务收入挂钩。

**信息来源声明 (Information Source Statement):** 本报告所依据的信息来源于公开可
获取的资料，包括但不限于公司公告、定期报告（年报/半年报/季报）、招股说明书、
行业公开数据、宏观统计数据以及公开市场信息。本报告所载资料、意见及推测仅反映
分析师于发布本报告当日的判断，相关判断可能因后续信息变化而调整。分析师未从
发行人处获取未公开的重大信息。

**免责声明 (Disclaimer):** 本报告仅供合格投资者参考使用，不构成对任何人的投资
建议、要约或要约邀请。投资者应当基于自身的投资目标、财务状况和风险承受能力，
独立作出投资决策，自行承担投资风险。本报告的版权归发布机构所有，未经书面许可，
任何机构和个人不得以任何形式翻版、复制、刊登、转载和引用。市场有风险，投资
需谨慎。

---

### Placement note

The Disclosures & Certifications appendix must be placed **after** the report
conclusion and before any technical appendices (assumptions table, numbers ledger,
chart sources). In the report structure, the full sequence is:

```
[Report body sections: Header → Opening → Industry → Company → Theme → DCF → SOTP →
 Market-Implied → Scenarios → Evaluation of Narratives → Catalysts → Conclusion →
 Limitations]
→ Disclosures & Certifications (B.1 through B.7, plus B.8 if China-listed)
→ Appendix A: Numbers Ledger
→ [Optional: Assumptions table, Chart index, Sources]
```

The front page or header of the report must contain a reference directing readers to
the Disclosures & Certifications appendix, per FINRA Rule 2241(c)(6): *"Disclosures
and certifications appear at the end of this report."*

---

## Template B — Research critique memo (Mode B)

Investor-facing prose, same register. Audits the *reasoning* of a third-party
report, not just its conclusion.

**Header:** Report title · author/firm · date · verdict (Reliable /
Usable-with-adjustments / Not reliable as stated).

**What the report claims.** Recommendation, value/target, date & price, method(s),
horizon, and the four drivers + terminal assumptions as stated — quoted where it
matters.

**Assessment of the reasoning.** Walk through the seven dimensions from
[`report-critique-rubric.md`](report-critique-rubric.md) — structural completeness,
input defensibility, internal consistency, accounting integrity, terminal-value
scrutiny, uncertainty handling, bias & independence — as prose, each claim backed by
a quote and a reason. (A compact scored table may accompany the prose; it does not
replace it.)

**Re-run results.** Whether the report's own inputs reproduce its value, and what
those inputs require to be true (reverse-solve), using the engine.

**Findings, by severity.** CRITICAL / HIGH / MEDIUM / LOW, each a specific, sourced
statement of what cannot bear the weight placed on it.

**Verdict & what would change it.** The overall judgment (apply the rubric's verdict
rule) and the specific evidence that would move it.

---

## Template C — Refresh / update memo (Mode C)

A short, dated note that keeps a prior valuation current — not a rebuild. Same
investor-facing register. Procedure: [`live-tracking.md`](live-tracking.md).

**Header:** Company (ticker) · prior call & date · updated call · price then → now ·
new valid-as-of / revisit-by.

**What changed since [prior date].** Dated developments over the period, each
tagged CONFIRMS / STRENGTHENS / BREAKS for the driver it touches — in prose, led
by date.

**Driver delta & revised value.** If nothing broke: state that the prior value
stands and why. If a driver broke: the re-run engine output, the new value, and a
one-paragraph explanation of exactly what moved it (the NVDA $240→$87 discipline).

**Price-implied re-test.** Re-run `reverse_dcf.py` at the current price — has the
gap that mattered widened or closed? Is the market now pricing more or less?

**Refreshed catalyst calendar & triggers.** Updated dated events and the monitoring
thresholds that would flip the call. Re-stamp valid-as-of / revisit-by.

---

## Style reminders (both)
- Conclusion first; numbers carry the argument (replace "high growth" with "34%
  CAGR", "expensive" with "94th percentile of value").
- Show the range, not just the point.
- State assumptions as assumptions, with their basis and date.
- No second-person address to the reader; treat any handed-in thesis as a market
  hypothesis to evaluate.
- Analysis, not personalized investment advice — say so once.
