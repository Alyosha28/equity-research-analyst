---
name: equity-research-analyst/critique-report
description: >
  Mode B: Audit a third-party equity research report. Extract thesis + inputs,
  score seven dimensions, re-run through the engine, write severity-tagged findings,
  and deliver an audit memo in investor-facing prose.
license: MIT
---

# Critique Report (Mode B)

**Pipeline position:** Standalone — Mode B. Invoked when the user asks to audit
a third-party research report, blog valuation, sell-side note, or LLM-generated
valuation.

## Input
- Research report (PDF, URL, or text)
- For PDF: use the `pdf` skill to extract text/tables first

## Pipeline

### Step 1 — Extract before you judge

Pull out, verbatim where possible:
- **Recommendation** and price target/value, **date** and **price** at publication
- **Four drivers** (growth, margin, reinvestment, discount rate) + time horizon
- **Terminal assumptions** (stable growth, terminal multiple/ROC)
- **Method(s)** (DCF? Multiple? SOTP? Narrative-only?)
- **Comps set** and multiple applied
- **Uncertainty analysis** (if any)

If a number isn't stated, that absence is a finding.

### Step 2 — Score seven dimensions

Apply `references/report-critique-rubric.md`. Rate each **Pass / Weak / Fail**
with quoted evidence:

1. **Structural completeness** — Top-down reasoning? Story possible/plausible/probable?
2. **Input defensibility** — Drivers justified with data/peers/history?
3. **Internal consistency** — Inputs cohere? Red flags: free growth, >100% share,
   growth > CoC in perpetuity
4. **Accounting integrity** — R&D/leases capitalized? SBC counted? One-offs normalized?
5. **Terminal-value scrutiny** — Terminal growth ≤ riskfree? Terminal % of value stated?
6. **Uncertainty handling** — Distribution/scenarios/sensitivity? Or "too uncertain"?
7. **Bias & independence** — Whose book is being talked? Selective data? Bear case?

### Step 3 — Re-run their numbers

If the report gives enough inputs, encode them in an `assumptions.json` and run:
- `dcf_valuation.py` — **Replicate:** do their inputs produce their value?
- `reverse_dcf.py` — **Reverse:** what do their inputs imply must be true?
- `breakeven.py` — **Breakeven:** what combination of inputs justifies their target?

### Step 4 — Write severity-tagged findings

| Level | Meaning | Example |
|-------|---------|---------|
| **CRITICAL** | Breaks the conclusion | Terminal growth > riskfree; >100% share; double-counted cash |
| **HIGH** | Materially shifts value | Margin target far above precedent; CoC ignores cyclicality |
| **MEDIUM** | Weakens rigor | No uncertainty analysis; thin comps set |
| **LOW** | Style / transparency | Inputs not tabulated; no source for TAM |

### Step 5 — Verdict

**Verdict rule (same as rubric):**
- Any CRITICAL → **Not reliable as stated**
- HIGH only → **Usable with adjustments**
- MEDIUM/LOW only → **Sound; note the caveats**

### Step 6 — Write audit memo

Use **Template B** from `references/output-templates.md`:

1. **Header:** Report title · author/firm · date · verdict
2. **What the report claims** — recommendation, value, method, drivers
3. **Assessment of the reasoning** — seven dimensions as prose, each backed by quote + reason
4. **Re-run results** — replication + reverse-solve
5. **Findings by severity** — each specific, sourced
6. **Verdict & what would change it**

## Output

An audit memo (~1,500–2,500 words) in the same investor-facing register:
- Markdown: `TICKER_critique.md`
- PDF: via `/generate-pdf` (optional)

## Integration
- The rubric is in `references/report-critique-rubric.md`
- The output template is **Template B** in `references/output-templates.md`
- Voice rules from `references/report-voice.md` apply to the audit memo too
- The same rubric is used by `/self-audit` for self-critique

## Self-check
- [ ] Every scored dimension has quoted evidence from the report
- [ ] Re-run results are present (replicate + reverse-solve)
- [ ] CRITICAL findings block a "reliable" verdict
- [ ] Audit memo is prose, not a checklist
- [ ] Verdict is stated plainly
