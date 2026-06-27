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

> Appendix (optional): the assumptions table (the JSON), sources & dates, accounting
> adjustments made.

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
