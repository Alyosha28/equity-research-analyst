# Report Critique Rubric (Mode B — auditing a third-party research report)

Use this to stress-test someone else's equity research (a sell-side note, a blog
valuation, an LLM-generated report, your own draft). The goal is not to agree or
disagree with the *conclusion* but to test whether the *reasoning* survives
scrutiny. A report can reach the right call for indefensible reasons, and vice
versa — judge the machinery.

Workflow: (1) extract the thesis and inputs, (2) score the seven dimensions,
(3) re-run the numbers in the engine if the report gives enough inputs,
(4) write the audit memo (template in `output-templates.md`).

---

## Step 1 — Extract before you judge
Pull out, verbatim where possible:
- The **recommendation** and price target / value, and the **date** and **price** then.
- The **four drivers** (growth, margin, reinvestment, discount rate) and the
  **time horizon**.
- The **terminal assumptions** (stable growth, terminal multiple/ROC).
- The **method(s)** used (DCF? multiple? sum-of-parts? just a narrative?).
- The **comps set** and the multiple applied.
- What **uncertainty analysis**, if any, was done.

If a number isn't stated, that absence is itself a finding.

---

## Step 2 — Score the seven dimensions

Rate each **Pass / Weak / Fail** and attach evidence (quote + why).

1. **Structural completeness** — Does it reason top-down (industry → company →
   theme → numbers → uncertainty → decision), or does it jump to a number? Is the
   story *possible, plausible, probable*?
2. **Input defensibility** — Is each driver justified with data/peers/history, or
   asserted? Watch for round-number TAMs, share gains with no mechanism, margin
   expansion with no source, a target multiple with no basis.
3. **Internal consistency** — Do the inputs cohere? Red flags: high growth with
   trivial reinvestment (free growth); margins rising while the firm cuts R&D;
   a discount rate that ignores cyclicality; revenue that implies an >100% market
   share; growth above the cost of capital in perpetuity.
4. **Accounting integrity** — R&D/leases capitalized? SBC and dilution counted
   (not added back and forgotten)? One-offs normalized? Cash flows, not just EPS?
5. **Terminal-value scrutiny** — Is terminal growth ≤ the riskfree rate? What % of
   value is in the terminal (and do they admit it)? Does a terminal ROC > cost of
   capital secretly assume a perpetual moat?
6. **Uncertainty handling** — Did they quantify the range (scenarios / simulation /
   sensitivity), or hide behind "too uncertain to model"? Does the recommendation
   acknowledge the distribution, or pretend the point estimate is certain?
7. **Bias & independence** — Whose book is being talked? Selective data, anchoring
   on the current price, confirmation bias, an incentive (banking relationship,
   ownership, narrative attachment)? Is the bear case argued as hard as the bull?

---

## Step 3 — Re-run the numbers
If the report supplies enough inputs, encode them in an `assumptions.json` and run
`dcf_valuation.py`, then `reverse_dcf.py` and `breakeven.py`. Two high-value checks:
- **Replicate:** do their inputs actually produce their value? (Often they don't.)
- **Reverse:** what do their inputs imply must be true, and is it? Solve for the
  price-implied growth/margin and judge plausibility.

---

## Severity levels (for findings)

Mirror a code review. Tag every finding:

| Level | Meaning | Example |
|---|---|---|
| **CRITICAL** | Breaks the conclusion; the number is unsupportable. | Terminal growth > riskfree; revenue implies >100% share; double-counted cash flows. |
| **HIGH** | Materially shifts value; likely wrong. | Margin target far above any precedent with no mechanism; cost of capital ignores cyclicality; SBC ignored. |
| **MEDIUM** | Weakens rigor; should be addressed. | No uncertainty analysis; thin comps set; terminal value 85% of total, unacknowledged. |
| **LOW** | Style / transparency. | Inputs not tabulated; date/price not stated; no source for TAM. |

**Verdict rule:** any CRITICAL → the valuation is *not reliable* as stated
(regardless of whether the call turns out right). HIGH only → *directionally
usable with adjustments*. MEDIUM/LOW only → *sound; note the caveats*.

---

## Step 4 — Output
Write the audit memo using the **Critique memo** template in
`output-templates.md`: thesis restatement → scored dimensions with evidence →
re-run results → severity-tagged findings → overall verdict → what would change
your mind. Be specific and quote the report; vague critique is as useless as a
vague valuation.

> Tone: skeptical but fair. The strongest critique steel-mans the report first,
> then shows precisely where the reasoning cannot bear the weight placed on it.
