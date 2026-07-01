---
name: equity-research-analyst/self-audit
description: >
  The pre-publish quality gate. Check 1 (Type-A): report_lint.py mechanical.
  Check 2 (Type-B): 7-dimension self-critique — routes to a different-family
  reviewer or human reviewer
  for verdict. CRITICAL findings BLOCK and route back to root sub-skill.
  Step 10 of Mode A.
license: MIT
---

# Self-Audit Gate

**Pipeline position:** STEP 10 of Mode A — the FINAL BARRIER before PDF generation.
Also the final step of Mode C refreshes. This is the self-iterating loop's quality
enforcement mechanism.

## Input
- Draft report from step 9 (`TICKER_report.md`)
- All prior step outputs (for fact-checking against)
- Publishing contract: `references/publishing-contract.md`

## The gate — three checks, all must pass

### Check 1 — Mechanical (`report_lint.py`)

```bash
cd scripts/
python report_lint.py ../PATH/TICKER_report.md            # blocks on FAIL
python report_lint.py ../PATH/TICKER_report.md --strict    # fresh reports: WARN also blocks
```

The linter catches: second-person address ("you", "你"), emoji, banned callout
patterns, missing disclaimer/rating/value-and-price, missing MoS buy-band,
missing numbers ledger (`--strict`), missing valid-as-of stamp (`--strict`),
AI-answer sentence patterns (`--strict`), AND missing/incomplete disclosure
appendix sections (analyst certification, rating distribution, meaning of ratings,
conflicts of interest, price target methodology, risk factors, China supplement
where applicable — all WARN under default, FAIL under `--strict`).

For Chinese reports, the linter also blocks English broker-template leakage such
as standalone English ratings and labels like `THESIS`, `INTRINSIC`,
`DOWNSIDE`, `MoS BUY-BAND`, or `Figure N:`.

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

### Check 3 — Disclosure completeness (regulatory sufficiency)

Verify the Disclosures & Certifications appendix against the mandatory checklist
from `references/output-templates.md` Appendix B:

- B.1 Analyst Certification (Reg AC) — both prongs present
- B.2 Rating Distribution table — with as-of date
- B.3 Meaning of Ratings — with 12-month horizon
- B.4 Conflicts of Interest — all 9 FINRA 2241 items (A)–(I) addressed
- B.5 Price Target Methodology — >=2 methods + triangulation table
- B.6 Risk Factors — >=5 specific, driver-tied, monitorable risks
- B.7 General Disclaimer — not-advice, dates, currency, stamps
- B.8 China supplement (if China-listed) — CSRC/SAC independence statement

**Any missing required section → CRITICAL → BLOCK.**
Placeholder-filled sections → HIGH → fix before publishing.

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

**After fixing, re-run ALL THREE checks.** Iterate until:
- Zero FAILs on `report_lint.py` (`--strict` for fresh reports)
- Zero CRITICALs on self-audit
- All disclosure sections B.1–B.7 (plus B.8 if China-listed) present and populated
- HIGHs disclosed in report limitations

## The psychological hurdle

It is harder to audit your own draft than a stranger's. Defeat this by
**depersonalizing**: treat the draft as an anonymous third-party note handed to
you for hostile review. The strongest self-audit finds the CRITICAL a competitor
would have found first.

## Pre-publish checklist
- [ ] `report_lint.py` passes (FAILs cleared; `--strict` clean for fresh report)
- [ ] **Disclosures & Certifications appendix complete** — B.1–B.7 all present
      and populated (no "[Yes/No]" or "[XX]" placeholders)
- [ ] **If China-listed: B.8 supplement present**
- [ ] Seven dimensions scored on own draft with quoted evidence
- [ ] No unresolved CRITICAL
- [ ] HIGH issues disclosed
- [ ] Value, price, rating, terminal %, price percentile, MoS buy-band, numbers
      ledger all present
- [ ] Report language is consistent across prose, rating box, charts, captions,
      disclosure appendix, and PDF output
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

## Adversarial Review Gate (meta-review)

### Gate classification

| Check | Type | Reviewer | Rationale |
|-------|------|----------|-----------|
| `report_lint.py` | **Type-A** | Same-model (script) | Machine-checkable: exit code, grep counts |
| 7-dim self-critique | **Type-B** | **Different-family reviewer or human review** | Requires taste/judgment of reasoning quality |

### Cross-model verdict routing (Check 2)

The 7-dim self-critique is a Type-B gate. The loop CANNOT self-acquit:

```
Primary Codex agent runs self-audit → produces draft audit scores →
  → Route to a different-family reviewer or human reviewer with:
    - The draft report text
    - The 7-dim critique rubric (references/report-critique-rubric.md)
    - The author's self-assessment scores
  → Reviewer returns verdict artifact: verdicts/audit.json
  → Orchestrator reads artifact:
    - PASS → proceed to PDF
    - REVISE → route to root sub-skill, re-run from there
    - BLOCK → escalate to orchestrator
```

### Verdict artifact format

```json
{
  "gate": "self-audit-7dim",
  "type": "B",
  "reviewer_model": "external-reviewer",
  "reviewer_family": "openai",
  "dimensions": {
    "structural_completeness": {"score": "PASS", "author_score": "PASS", "agrees": true},
    "input_defensibility": {"score": "PASS", "author_score": "WEAK", "agrees": false, "note": "..."},
    "internal_consistency": {"score": "PASS", "author_score": "PASS", "agrees": true},
    "accounting_integrity": {"score": "PASS", "author_score": "PASS", "agrees": true},
    "terminal_value_scrutiny": {"score": "WEAK", "author_score": "PASS", "agrees": false, "note": "Terminal 82% not flagged; HIGH"},
    "uncertainty_handling": {"score": "PASS", "author_score": "PASS", "agrees": true},
    "bias_and_independence": {"score": "PASS", "author_score": "PASS", "agrees": true}
  },
  "overall_verdict": "PASS_WITH_HIGH",
  "critical_count": 0,
  "high_count": 1,
  "high_details": ["Terminal value 82% of total not flagged prominently enough — disclose in limitations"],
  "author_self_assessment_honest": false,
  "author_inflated_dimensions": ["terminal_value_scrutiny"],
  "recommendation": "PUBLISH_WITH_DISCLOSURE"
}
```

### Meta-review criteria
- [ ] **Cross-model verdict obtained:** Verdict artifact exists and is from a different
  model family. Missing artifact → BLOCK.
- [ ] **Self-assessment honesty checked:** The reviewer explicitly flags whether the
  author's self-scores were inflated. If the author gave PASS on a dimension the reviewer scored WEAK →
  the self-audit was dishonest → record this.
- [ ] **Lint actually run:** Spot-check by Codex — does any "you"/"你" exist that lint
  didn't flag?
- [ ] **CRITICAL not dodged:** Codex checks: terminal growth vs riskfree, implied
  share vs 100%, double-counted cash flows.
- [ ] **Feedback routing correct:** If CRITICAL, does feedback point to correct root?

### Fallback when cross-model unavailable

If Codex cannot be reached:
1. Record failure in LOOP-STATE.md
2. Mark the Type-B gate as UNVERIFIED
3. Publish with escalated disclosure: "Self-audit gate not independently verified"
4. NEVER silently self-acquit with same-model fallback

### Verdict thresholds
- **PASS:** Lint passes (Type-A), cross-model returns PASS on all 7 dims.
- **PASS-WITH-HIGH:** Cross-model returns HIGH(s) — disclose, proceed.
- **REVISE:** Cross-model returns CRITICAL → route to root sub-skill.
- **BLOCK:** Gate bypass attempted, cross-model unreachable without fallback record.
