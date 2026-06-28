# Self-Audit Gate (run before publishing any Mode A / Mode C output)

The skill already has *descriptive* standards (`report-voice.md`, the SKILL.md depth
standards). Descriptive standards do not enforce themselves — a draft can satisfy
none of them and still get shipped. This gate is the *procedural* step that makes
them binding: **before a report leaves the building, it must clear three checks, and
you revise until it does.** No new rubric is invented here; the gate reuses the
mechanical linter, the Mode B critique rubric, and a regulatory-sufficiency checklist
— all turned inward.

## The gate — three checks, all must pass

### Check 1 — Mechanical (`report_lint.py`)
Run the deterministic linter on the draft:
```bash
python scripts/report_lint.py path/to/report.md            # blocks on FAIL
python scripts/report_lint.py path/to/report.md --strict    # fresh reports: WARN also blocks
```
Fix **every FAIL** before proceeding: second-person address, emoji, banned
callout boxes, missing disclaimer / rating / value-and-price. For a freshly written
report (not a historical reconstruction), run `--strict` and clear the warnings too —
a margin-of-safety buy-band, a numbers ledger, a valid-as-of stamp, the terminal
share, the price percentile, AND the disclosures & certifications appendix should all
be present. The linter is fast and unambiguous; there is no excuse for shipping a FAIL.

### Check 2 — Adversarial self-audit (Mode B rubric, turned inward)
Mechanical checks catch *form*, not *reasoning*. So audit the draft exactly as Mode B
audits a stranger's report — apply `references/report-critique-rubric.md` to your own
work and score the **seven dimensions** Pass / Weak / Fail with quoted evidence:

1. Structural completeness · 2. Input defensibility · 3. Internal consistency ·
4. Accounting integrity · 5. Terminal-value scrutiny · 6. Uncertainty handling ·
7. Bias & independence.

Then tag your own findings with the same severity levels (CRITICAL / HIGH / MEDIUM /
LOW). **The publish rule mirrors the Mode B verdict rule:**
- **Any self-identified CRITICAL → do not publish.** Fix it and re-audit. (A terminal
  growth above the riskfree rate, revenue implying >100% share, a double-counted cash
  flow, peak-cycle margins capitalized as permanent — these are disqualifying in your
  own draft, not just someone else's.)
- **HIGH only → publish only with the issue disclosed** in the report's limitations,
  not buried.
- **MEDIUM / LOW only → publishable**, with the caveats noted.

### Check 3 — Disclosure completeness (regulatory sufficiency)
A mechanical and reasoning audit does not guarantee regulatory compliance. Verify the
Disclosures & Certifications appendix against the mandatory checklist from
`references/output-templates.md` Appendix B:

- [ ] **B.1 Analyst Certification** — Reg AC language present ("certify that all of the views
      expressed… accurately reflect my personal views" + "no part of my compensation was, is,
      or will be… related to the specific recommendations"). If the analyst's compensation
      IS tied to the recommendation, option (ii) disclosure is made instead.
- [ ] **B.2 Rating Distribution table** — Coverage universe count + Buy/Hold/Sell percentages
      + % IB Clients in each bucket, with an as-of date (quarter-end). For independent
      research, the table appears with a statement that no IB business is conducted.
- [ ] **B.3 Meaning of Ratings** — Each rating category (Buy/Hold/Sell or equivalent) defined
      with the total-return expectation, benchmark, and investment horizon (12 months).
- [ ] **B.4 Conflicts of Interest (FINRA 2241)** — All nine disclosure items (A) through (I)
      are addressed, each with a Yes/No and explanatory detail where affirmative. No item
      is omitted. For independent/unaffiliated research, a consolidated independence
      statement that substantively covers each item is acceptable.
- [ ] **B.5 Price Target Methodology** — At least two valuation methods described; the DCF
      includes forecast horizon, WACC range, terminal growth rate, and accounting adjustments.
      The triangulation table shows value ranges, weights, and the final target. The
      valuation horizon is stated (12 months). Key assumptions that carry the result are
      named.
- [ ] **B.6 Risk Factors** — At least five specific, monitorable risks, each tied to a
      valuation driver with a severity and a monitoring trigger. Not generic boilerplate.
- [ ] **B.7 General Disclaimer** — Not-advice disclaimer, information cutoff date, currency,
      valid-as-of and revisit-by stamps.
- [ ] **B.8 China supplement (if applicable)** — For A-share / CSRC-regulated listings:
      analyst independence statement (分析师独立性声明), information source statement
      (信息来源声明), and disclaimer (免责声明) in Chinese, compliant with the 2024 SAC
      指引 and the 2025 SAC 执业规范 revision.

**Check 3 verdict:**
- **Any required section MISSING → CRITICAL → do not publish.** Fix and re-check.
- **All sections present but a disclosure item left as "[Yes/No]" placeholder instead of
  resolved → HIGH → fix before publishing.**
- **All sections complete and all fields populated → PASS.**

### The loop
```
draft → report_lint (fix FAILs) → self-audit 7 dims (fix CRITICALs) →
disclosure check (fix missing sections) → re-run all three → publish
```
Iterate until **all three checks are clean**. A report that cannot survive its own
author's Mode B audit AND pass a regulatory-sufficiency check is not finished.

## The asymmetry to beat
It is psychologically harder to audit your own draft than a stranger's — you know what
you *meant*, so you read it charitably. Defeat that by **depersonalizing**: treat the
draft as an anonymous third-party note handed to you for a hostile review, and
steel-man it before you attack it. The strongest self-audit is the one that finds the
CRITICAL a competitor would have found first. The skill's whole register exists to
stop "an AI answering the user"; this gate is where that intention becomes a check
with teeth.

## Pre-publish checklist (the gate in one screen)
- [ ] `report_lint.py` passes (FAILs cleared; `--strict` clean for a fresh report).
- [ ] The seven Mode B dimensions scored on the **own** draft; evidence attached.
- [ ] **No unresolved CRITICAL** in the self-audit. HIGH issues disclosed, not buried.
- [ ] Value, price, rating, terminal %, price-in-distribution percentile, **MoS
      buy-band**, and a **numbers ledger** are all present.
- [ ] **Disclosures & Certifications appendix complete** — all sections B.1–B.7
      (plus B.8 for China-listed names) present and populated. No "[Yes/No]" or
      "[XX]" placeholders remain.
- [ ] The bear case is argued as hard as the bull; the self-falsification is woven in.
- [ ] `valid-as-of` / `revisit-by` stamped.

> Integration: this gate is **Mode A step 9** (immediately before delivering) and the
> final step of a **Mode C** refresh. Rubric reused: `references/report-critique-rubric.md`.
> Mechanical rules: `scripts/report_lint.py`. Voice & ledger: `references/report-voice.md`.
> Disclosure template: `references/output-templates.md` Appendix B.
