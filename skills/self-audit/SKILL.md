---
name: equity-research-analyst/self-audit
description: >
  The pre-publish quality gate. Runs report_lint.py (mechanical) + adversarial
  self-critique using the Mode B seven-dimension rubric (reasoning). CRITICAL
  findings BLOCK publication and route back to the failing sub-skill. Step 10 of Mode A.
license: MIT
---

# Self-Audit Gate

**Pipeline position:** STEP 10 of Mode A — the FINAL BARRIER before PDF generation.
Also the final step of Mode C refreshes. This is the self-iterating loop's quality
enforcement mechanism.

## Input
- Draft report from step 9 (`TICKER_report.md`)
- All prior step outputs (for fact-checking against)

## The gate — two checks, both must pass

### Check 1 — Mechanical (`report_lint.py`)

```bash
cd scripts/
python report_lint.py ../PATH/TICKER_report.md            # blocks on FAIL
python report_lint.py ../PATH/TICKER_report.md --strict    # fresh reports: WARN also blocks
```

The linter catches: second-person address ("you", "你"), emoji, banned callout
patterns, missing disclaimer/rating/value-and-price, missing MoS buy-band,
missing numbers ledger (`--strict`), missing valid-as-of stamp (`--strict`),
AI-answer sentence patterns (`--strict`).

**Fix every FAIL.** There is no excuse for shipping a FAIL.

### Check 2 — Adversarial self-audit (Mode B rubric, inward)

Apply `references/report-critique-rubric.md` to your own draft. Score each of
seven dimensions **Pass / Weak / Fail** with quoted evidence:

1. **Structural completeness** — Top-down? Story possible/plausible/probable?
2. **Input defensibility** — Each driver justified with data/peers/history?
3. **Internal consistency** — Growth vs reinvestment, margins vs R&D, implied
   share vs 100%, growth vs CoC in perpetuity.
4. **Accounting integrity** — R&D/leases capitalized? SBC counted? One-offs normalized?
5. **Terminal-value scrutiny** — Terminal growth ≤ riskfree? Terminal % stated?
   Terminal ROC defensible?
6. **Uncertainty handling** — Distribution? Breakeven? Scenarios?
7. **Bias & independence** — Bear case as rigorous as bull? Self-falsification?
   Numbers sourced and tiered?

## Severity → publish rule

| Level | Rule |
|-------|------|
| **CRITICAL** | **BLOCK** — fix root cause, re-run both checks |
| **HIGH** | Publish with issue disclosed in limitations |
| **MEDIUM** | Note the caveat |
| **LOW** | Fix if easy |

## Feedback routing (the self-iteration mechanism)

When a CRITICAL or pattern of HIGHs is found, route to the root sub-skill:

| Issue type | Route to | Example directive |
|-----------|----------|-------------------|
| Voice/register/tone | `/write-report` | "¶3 and ¶7 use second-person; rewrite institutional" |
| Missing depth elements | `/analyze-industry` `/analyze-company` `/analyze-theme` | "No 10-year leader rotation table" |
| Input/assumption errors | `/build-assumptions` | "Revenue implies 112% TAM share in Y8; cap at 85%" |
| Engine/calculation | `/run-valuation` | "Terminal growth 4% > riskfree 3%" |
| Terminal/moat issues | `/durability-check` | "CAP 25 yrs vs 5-yr leader rotation" |
| Triangulation errors | `/triangulate` | "Lenses averaged; rewrite as pattern interpretation" |

**After fixing, re-run BOTH checks.** Iterate until:
- Zero FAILs on `report_lint.py` (`--strict` for fresh reports)
- Zero CRITICALs on self-audit
- HIGHs disclosed in report limitations

## The psychological hurdle

It is harder to audit your own draft than a stranger's. Defeat this by
**depersonalizing**: treat the draft as an anonymous third-party note handed to
you for hostile review. The strongest self-audit finds the CRITICAL a competitor
would have found first.

## Pre-publish checklist
- [ ] `report_lint.py` passes (FAILs cleared; `--strict` clean for fresh report)
- [ ] Seven dimensions scored on own draft with quoted evidence
- [ ] No unresolved CRITICAL
- [ ] HIGH issues disclosed
- [ ] Value, price, rating, terminal %, price percentile, MoS buy-band, numbers
      ledger all present
- [ ] Bear case argued as hard as bull
- [ ] Self-falsification woven into conclusion
- [ ] valid-as-of / revisit-by stamped

## Output

```json
{
  "gate_result": "PASS" | "BLOCKED",
  "lint": { "fails": 0, "warns": 2 },
  "self_audit": {
    "critical_count": 0,
    "high_count": 1,
    "medium_count": 3,
    "low_count": 2,
    "worst_dimension": "uncertainty_handling",
    "verdict": "PUBLISHABLE_WITH_DISCLOSURE"
  },
  "feedback_routing": [
    { "target_skill": "/write-report", "issue": "Missing MoS buy-band in section 5", "severity": "HIGH" }
  ]
}
```
