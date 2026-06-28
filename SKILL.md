---
name: equity-research-analyst
description: >
  Fundamental equity valuation & research in Aswath Damodaran's "story -> numbers
  -> value" style, for ANY company. ORCHESTRATOR: routes to Mode A/B/C, spawns
  parallel agent teams for concurrent sub-skills, and runs adversarial review
  agents after every step (1–2 revision rounds). 用中文也可触发。
license: MIT
---

# Equity Research Analyst — Orchestrator

This is the **orchestrator** for the equity-research-analyst skill family. It does
THREE things that make the pipeline rigorous:

1. **Agent Team — default parallelism.** Where sub-skills are independent, the
   orchestrator spawns parallel agents (not sequential). Industry + Theme analysis
   run simultaneously. Durability + Triangulation run simultaneously after the
   engine. No manual "run these in parallel" instruction needed — it's the default.

2. **Adversarial Review — per-step gate.** After EVERY sub-skill completes, an
   adversarial review agent critiques the output. The reviewer's job is to find
   flaws and demand fixes. Each sub-skill gets 1–2 revision rounds. Only when the
   reviewer signs PASS does the output proceed to the next step.

3. **Loop Protocol — Type-A/B gates + adversarial review (target: cross-model).** Every gate is
   classified Type-A (machine-checkable: exit code, math, counter) or Type-B
   (requires taste/judgment). Currently, Type-B gates use same-model adversarial
   review (Claude critiques Claude). The target architecture routes Type-B gates to
   Codex xhigh for a heterogeneous verdict — Claude can DRIVE the loop but cannot
   ACQUIT its own work. One of five same-family-safe conditions remains partially
   unmet (no same-family jury — Tier 1 achieves cross-model safety via Codex xhigh;
   Tiers 2/3 use strengthened same-model review with mandatory disagreement and
   honest disclosure). The other four conditions are implemented: verdict artifacts
   saved via `verdict.py`, Type-B gates routed per `cross-model-guide.md`. All gaps
   are disclosed, not hidden. A convergence terminator caps iterations at 3 before
   escalating to risk annotation.

Together these create a **self-iterating pipeline with honest gap disclosure**.
Quality is enforced at every boundary. The pipeline does NOT claim same-family
safety until cross-model routing is operational; current gaps are documented in
`references/loop-protocol.md` Section 6.

## Architecture

```
/equity-research-analyst          ← YOU ARE HERE (orchestrator)
├── /classify-archetype           ← classify company → archetype + life-cycle phase
├── /analyze-industry             ← industry lifecycle, profit cycles, leader rotation
├── /analyze-company              ← business model, moat, 10yr financials, drawdowns
├── /analyze-theme                ← thematic driver, TAM × share, competitive map
├── /build-assumptions            ← story→numbers, accounting adj, write assumptions.json
├── /run-valuation                ← execute Python engine suite (DCF/MC/reverse/breakeven)
├── /durability-check             ← ROIC-WACC spread, CAP, RONIC fade, moat decomposition
├── /triangulate                  ← cross-check 7 lenses, identify dispute locus
├── /generate-charts              ← render 12 publication-grade charts from engine JSON
├── /write-report                 ← produce investor-facing long-form prose
├── /self-audit                   ← lint + adversarial self-critique → gate
├── /generate-pdf                 ← render finished report to PDF (typographic, chart embeds)
├── /research                     ← shared: single-point web research, fact-checking
├── /fetch-data                   ← shared: fetch financials, build skeleton
├── /fetch-damodaran-data         ← NEW: fetch current ERP, CRP, betas, CoC from NYU Stern
├── /critique-report              ← Mode B: audit third-party research
└── /refresh-valuation            ← Mode C: currency sweep, driver delta, update memo
```
## Shared agents

Analysis sub-skills invoke these instead of duplicating logic:

| Agent | Purpose | Called by |
|-------|---------|-----------|
| /research | Web research, fact-checking, source annotation | industry, company, theme, assumptions, refresh, critique |
| /fetch-data | Financial data skeleton from filings/APIs | assumptions, standalone |

**Rule:** Send a research brief to /research -- do not run WebSearch in analysis skills.


## Shared resources
- `scripts/` — Python valuation engine (13 programs: dcf, mc, reverse_dcf, breakeven, comps, sotp, financial_valuation, fetch_financials, charts, report_lint, financial_stress, verdict, build_manifest)
- `references/` — Methodology, playbooks, style guides (17 docs: 4 archetype playbooks + default, cross-model-guide, loop-protocol, methodology-damodaran, valuation-lenses, input-estimation, analyst-playbook, report-critique-rubric, output-templates, report-voice, live-tracking, self-audit-gate, holding-company-sotp)
- `skills/` — 17 sub-skills with SKILL.md manifests
- `templates/` — Assumption sheets, worked examples, report templates

---

## Three Core Mechanisms

### Mechanism 1 — Agent Team (Default Parallelism)

The orchestrator **automatically** spawns parallel agents for independent work.
You do NOT need to ask for concurrency — it's the default behavior.

**Mode A agent team deployment:**

```
WAVE 1 ─── spawn 2 agents in PARALLEL ─────────────────────────────┐
│  Agent A: /analyze-industry  (industry lifecycle, leader rotation)│
│  Agent B: /analyze-theme     (TAM × share, competitive map)      │
│  → each followed by its adversarial reviewer                     │
└──────────────────────────────────────────────────────────────────┘
                              ↓ (both pass review)
WAVE 2 ─── single agent (industry context needed) ─────────────────┐
│  Agent C: /analyze-company  (business model, 10yr financials)    │
│  → followed by adversarial reviewer                              │
└──────────────────────────────────────────────────────────────────┘
                              ↓ (passes review)
WAVE 3 ─── single agent ───────────────────────────────────────────┐
│  Agent D: /build-assumptions (story→numbers, write .json)        │
│  → followed by adversarial reviewer + quick engine sanity run    │
└──────────────────────────────────────────────────────────────────┘
                              ↓ (passes review)
WAVE 4 ─── single agent ───────────────────────────────────────────┐
│  Agent E: /run-valuation    (DCF, MC, breakeven, reverse DCF)    │
│  → followed by adversarial reviewer                              │
└──────────────────────────────────────────────────────────────────┘
                              ↓ (passes review)
WAVE 5 ─── spawn 2 agents in PARALLEL ─────────────────────────────┐
│  Agent F: /durability-check (ROIC-WACC, CAP, RONIC, moat)        │
│  Agent G: /triangulate      (7-lens cross-check, dispute locus)  │
│  → each followed by its adversarial reviewer                     │
└──────────────────────────────────────────────────────────────────┘
                              ↓ (both pass review)
                              ┌─── CONSISTENCY CHECK ───┐
                              │ Do durability +         │
                              │ triangulation agree?    │
                              └──────────────────────────┘
                              ↓ (consistent)
WAVE 5.5 ── single agent ───────────────────────────────────────────┐
│  Agent H: /generate-charts  (12 publication-grade charts from     │
│           engine JSON outputs; Monte Carlo, breakeven, football,  │
│           terminal, tornado, scenarios, waterfall, capex, risks)  │
│  → followed by adversarial reviewer                               │
│  → Type-A gates: all chart JSON valid, SVGs rendered,             │
│     chart-index.json cross-references complete                    │
└──────────────────────────────────────────────────────────────────┘
                              ↓ (passes review)
WAVE 6 ─── single agent ───────────────────────────────────────────┐
│  Agent I: /write-report     (3,500-5,000 word investor prose)    │
│  → followed by adversarial reviewer                              │
└──────────────────────────────────────────────────────────────────┘
                              ↓ (passes review)
WAVE 7 ─── single agent ───────────────────────────────────────────┐
│  Agent J: /self-audit       (lint.py + 7-dim self-critique)      │
│  → FINAL GATE: CRITICAL → route back to root sub-skill           │
└──────────────────────────────────────────────────────────────────┘
                              ↓ (PASS)
WAVE 8 ─── single agent ───────────────────────────────────────────┐
│  Agent K: /generate-pdf     (typographic PDF with chart embeds)  │
└──────────────────────────────────────────────────────────────────┘
                              ↓
                          DELIVER
```

### Mechanism 2 — Adversarial Review (Per-Step Gate)

After **EVERY** sub-skill completes, the orchestrator spawns an adversarial
review agent. This is NOT the same as the final self-audit — it's a per-step
quality check that catches errors early.

**Review agent design:**

```
┌─────────────────────────────────────────────┐
│         ADVERSARIAL REVIEW AGENT             │
│                                             │
│  Given:                                     │
│  - Sub-skill's output                       │
│  - Sub-skill's self-check checklist         │
│  - Sub-skill's review criteria              │
│                                             │
│  Task:                                      │
│  1. Find at least ONE thing wrong or weak   │
│  2. Rate: PASS / REVISE / BLOCK             │
│  3. For REVISE: specific, actionable fix   │
│  4. For PASS: state why it survives scrutiny│
│                                             │
│  Rules:                                     │
│  - Default stance: SKEPTICAL (not rubber-  │
│    stamp — adversarial, not friendly)       │
│  - Must find at least 1 weakness. If the   │
│    output is genuinely flawless, the       │
│    reviewer states: "Best-effort critique  │
│    found no material issues — PASS."        │
│  - Max 2 revision rounds. After round 2,   │
│    unresolved issues are escalated to the  │
│    orchestrator with a RISK ANNOTATION.     │
│  - BLOCK verdict only for fatal errors      │
│    (e.g., wrong archetype, broken math,     │
│    fabricated numbers).                     │
└─────────────────────────────────────────────┘
```

**Review verdicts:**

| Verdict | Meaning | Orchestrator action |
|---------|---------|-------------------|
| **PASS** | Output survives scrutiny; minor suggestions only | Proceed to next step |
| **PASS-WITH-NOTES** | Pass but with caveats recorded | Proceed; notes forwarded to downstream steps |
| **REVISE** | Material issues found; fix needed | Send specific feedback to sub-skill; re-run sub-skill + re-review (max 2 rounds) |
| **BLOCK** | Fatal error (wrong archetype, fabricated data, broken logic) | Halt pipeline; escalate to orchestrator with diagnosis |

**Revision loop per step:**

```
sub-skill → output → adversarial review → REVISE?
    ↑                                        │
    └──────── fix + re-submit (round 2) ─────┘
                                                 ↓
                                            REVISE again?
                                                 │
                                    ┌────────────┴────────────┐
                                    ↓                         ↓
                                  PASS                    ESCALATE
                              (proceed to               (flag to user
                               next step)              with risk note)
```

### Mechanism 3 — Loop Protocol (Type-A/B Gates + Cross-Model Verdict)

Every gate in the pipeline is classified Type-A or Type-B. The taxonomy and
rules come from `references/loop-protocol.md`.

**Type-A gates** — machine-checkable, same-model self-judgment allowed:

| Gate | Check | Verdict source |
|------|-------|---------------|
| `report_lint.py` | Exit code 0, zero FAIL | Shell exit code |
| JSON validity | `json.load()` succeeds | Python stdlib |
| Engine sanity | DCF produces positive value | Math comparison |
| MC trials | trials >= 10000 | Integer comparison |
| Terminal growth | growth <= riskfree rate | Math |

**Type-B gates** — require taste/judgment. Currently self-judged by adversarial
review agents (same model family). Target: cross-model routing (see gap assessment
in `references/loop-protocol.md` Section 6).

| Gate | Current reviewer | Target reviewer | Target artifact |
|------|------------------|-----------------|-----------------|
| Adversarial review (every sub-skill) | Claude (same-model) | Codex xhigh | `verdicts/{step}.json` |
| 7-dim self-audit | Claude (same-model) | Codex xhigh | `verdicts/audit.json` |
| Write-report voice/depth | Claude (same-model) | Codex xhigh | `verdicts/report.json` |
| Generate-charts visual quality | Claude (same-model) | Codex xhigh | `verdicts/charts.json` |

**Current (same-model adversarial) flow:**
```
Claude produces output → Type-B gate reached →
  → Same-model adversarial review agent critiques output
  → Review verdict returned inline (not saved as artifact)
  → PASS: proceed | REVISE: fix + retry | BLOCK: escalate
```

**Target (cross-model) flow:**
```
Claude produces output → Type-B gate reached →
  → Route to Codex (reasoning: xhigh) with the output + review criteria
  → Codex returns verdict JSON artifact saved to verdicts/{step}.json
  → Claude reads artifact → PASS: proceed | REVISE: fix + retry | BLOCK: escalate
```

**The rule:** "A loop can DRIVE; it cannot ACQUIT." This is the target — Claude
orchestrates and executes, but a different model family should sign off on quality.
Currently, same-model adversarial review provides the best available check; the
gap to cross-model routing is openly documented.

**Same-family-safe conditions (target — 3 of 5 currently unmet):**
1. Every gate classified A or B ✅
2. Every Type-B gate routes to cross-model ⚠️ (currently self-judged)
3. Cross-model verdict saved as inspectable artifact ⚠️ (not yet saved)
4. No same-family majority treated as jury ⚠️ (current reviewer is same family)
5. Type-A self-judgment uses external checks ✅

See `references/loop-protocol.md` Section 6 for the detailed gap assessment.

**Convergence terminator:**
- Max 2 adversarial review rounds per sub-skill
- Max 3 pipeline iterations for same error signature
- On third failure: escalate with risk annotation, publish with disclosure
- Rule: NEVER silently pass; unresolved issues are always surfaced

**LOOP-STATE.md** — the baton file that records current step, gate history,
verdict artifacts, revision history, and escalations. Full format in
`references/loop-protocol.md`.

---

## Mode A — Full Pipeline Execution

### Phase 0: Archetype + Life-Cycle Phase + Damodaran Data

```
1. Invoke /fetch-damodaran-data
   - Fetch latest implied ERP (monthly update from pages.stern.nyu.edu/~adamodar)
   - Fetch country risk premiums (latest ctryprem.xlsx — Jan or July update)
   - Fetch industry betas and cost of capital (betas.xls, wacc.xls)
   - Record current riskfree rate (10-year government bond, adjusted for sovereign default spread)
   - Evaluate trust-deficit signals (sovereign downgrade, USD trend, gold, CB independence, governance)
   - Output: damodaran_data.json with all fetched data + dates → fed to /build-assumptions

2. Invoke /classify-archetype
   - Produces BOTH business-model archetype AND corporate life-cycle phase (6 phases from Damodaran 2024 book)
   - Life-cycle phase determines: narrative emphasis, driver sensitivity, convergence shape, terminal structure

3. Spawn adversarial reviewer for classify-archetype
   - Review criteria: archetype + phase correctness, consistency, engine/playbook match, edge cases, traps avoided
   - If REVISE: fix classification → re-review (max 2 rounds)
   - If BLOCK: halt — wrong company understanding

4. When PASS: lock archetype + phase + current market data (all downstream steps inherit)
   - Data dates are recorded — the valuation is dated at this point
```

### Phase 1: Research (WAVE 1 — parallel)

```
SPAWN 2 AGENTS IN PARALLEL:

Agent A: /analyze-industry
  → adversarial review: are lifecycle/margin/leader data sourced and spanning 10+ years?
  → if REVISE: fix gaps → re-review

Agent B: /analyze-theme
  → adversarial review: is TAM sourced? two revenue paths attempted? Big Market Delusion checked?
  → if REVISE: fix gaps → re-review

(Both agents run concurrently. Orchestrator waits for both to PASS.)
```

### Phase 2: Company (WAVE 2)

```
Agent C: /analyze-company (uses Agent A's industry context)
  → adversarial review: business model clear? moat decomposed? 10yr trajectory +
    drawdowns present? SBC dilution stated?
  → if REVISE: fix gaps → re-review
```

### Phase 3: Cross-phase sanity (GATE A)

```
Orchestrator runs a quick consistency check across phases 1+2:
- Does the industry analysis contradict the theme?
- Does the company's moat make sense given the industry structure?
- Does the TAM share trajectory fit the competitive landscape?
→ If contradiction found: identify which sub-skill is the source, route fix
```

### Phase 4: Assumptions (WAVE 3)

```
Agent D: /build-assumptions
  → Consumes: damodaran_data.json (current ERP, CRP, betas, riskfree), industry/company/theme analyses, archetype + life-cycle phase
  → Uses current implied ERP (not hardcoded) for cost of capital estimation
  → Life-cycle phase informs: margin glide shape, growth deceleration rate, cost-of-capital glide timing, failure probability, terminal structure
  → Evaluates trust-deficit / institutional-risk overlay (documented as named, separate premium if applied)
  → Adversarial review: accounting adjustments done? revenue bottom-up? each driver has basis + low/base/high? ERP/CRP data dated? trust-deficit overlay evaluated? JSON valid? quick engine sanity run passes?
  → if REVISE: fix → re-review
```

### Phase 5: Engine (WAVE 4)

```
Agent E: /run-valuation
  → adversarial review: all applicable scripts executed? terminal % stated?
    price percentile reported? MoS band extracted? reverse-DCF plausible?
  → if REVISE: re-run with fixes → re-review
```

### Phase 6: Analysis (WAVE 5 — parallel)

```
SPAWN 2 AGENTS IN PARALLEL:

Agent F: /durability-check
  → adversarial review: ROIC R&D-adjusted? each moat component has named threat +
    monitorable indicator? CAP justified? terminal sensitivity shown?
  → if REVISE: fix → re-review

Agent G: /triangulate
  → adversarial review: all 7 lenses present? dispute locus specific? variant
    perception falsifiable? not averaging lenses?
  → if REVISE: fix → re-review

CONSISTENCY CHECK between durability + triangulation outputs:
- Does the CAP from durability match the dispute locus from triangulation?
- If durability says "moat is strong for 15 years" but triangulation says
  "fight is about terminal margin" → resolve the tension
```

### Phase 6.5: Charts (WAVE 5.5)

```
Agent H: /generate-charts
  → Reads output-manifest.json produced by /run-valuation
  → Renders 7 required chart types (Monte Carlo, breakeven, terminal, football,
    tornado, revenue trajectory, ROIC-WACC spread) + up to 5 optional types
    (scenarios, price history, driver waterfall, CAPEX cycle, risk matrix)
  → All chart data sourced from engine JSON (dcf_result.json, mc.json,
    be.json, football.json, durability.json, scenarios.json, etc.)
  → Output: figs/{TICKER}_{kind}.{svg,png} + chart-index.json manifest
  → CJK font auto-detection: charts render correctly on Windows/macOS/Linux
  → Theme: default (Goldman-style restrained palette) or per-report override
  → adversarial review:
    - Type-A: all required SVGs rendered? chart-index.json valid? file sizes OK?
    - Type-B (routes to cross-model): visual quality? CJK rendering correct?
      chart titles declarative? color palette consistent?
  → if REVISE: fix specific charts → re-review (max 2 rounds)
```


### Phase 7: Report (WAVE 6)

```
Agent I: /write-report
  → adversarial review (most thorough — this is the deliverable):
    - Voice check: grep for "you"/"你", emoji, banned patterns
    - Depth check: all 6 Damodaran depth elements present?
    - Numbers check: every material figure sourced and tiered?
    - Structure check: sections follow Template A?
    - Register check: reads like a research report, not an AI answer?
  → if REVISE: fix → re-review (may need 2 rounds for prose quality)
```

### Phase 8: Audit (WAVE 7)

```
Agent J: /self-audit
  → This IS the adversarial review for the report, but more systematic:
    Check 1: report_lint.py (mechanical — must pass)
    Check 2: 7-dimension self-critique (reasoning — CRITICAL must be zero)
  → CRITICAL finding → route to root sub-skill → re-run from that step
  → HIGH only → disclose in limitations → PASS
  → CLEAN → PASS → proceed to PDF
```

### Phase 9: PDF (WAVE 8)

```
Agent K: /generate-pdf
  → adversarial review: all charts embedded? CJK fonts render? rating box prominent?
    pages numbered? disclaimer present? printable in B&W?
  → if REVISE: fix rendering → re-review
```

### Phase 10: Deliver

```
Final package:
- TICKER_report.md
- TICKER_report.pdf
- TICKER_assumptions.json (for reproducibility)
- figs/ (charts, PNG + SVG)
```

---

## Mode B — Critique Pipeline

```
Agent: /critique-report
  1. Extract thesis + inputs from the report
  2. Score seven dimensions (Pass/Weak/Fail)
  3. Re-run their inputs through the engine
  4. Write severity-tagged findings
  5. Verdict + what would change it

  → adversarial review: is each scored dimension backed by quoted evidence?
    are re-run results present? CRITICAL findings block a "reliable" verdict?

  → Optionally /generate-pdf the audit memo
  → Deliver
```

---

## Mode C — Refresh Pipeline

```
Agent: /refresh-valuation
  1. Sweep developments since last as-of date
  2. Compute driver delta (CONFIRMS/STRENGTHENS/BREAKS)
  3. If nothing broke → short update memo
  4. If a driver broke → re-run affected engine, new value

  → adversarial review: is every development dated and source-tiered?
    driver delta explicit for each driver? reverse-DCF re-run at current price?

  → Lightweight self-audit
  → Optionally /generate-pdf
  → Deliver
```

---

## Escalation rules (when revision rounds are exhausted)

After 2 rounds of adversarial review without PASS:

1. **Record the unresolved issue** with a risk annotation
2. **Publish with disclosure** — the issue must be stated in the report's limitations section
3. **Flag to user** — "Note: [sub-skill] output has an unresolved weakness: [specific].
   Published with this caveat. To strengthen, re-run with better input data."
4. **Never silently pass** — unresolved adversarial feedback is always surfaced

## Quality principles (applied at every adversarial review)

1. **Story → numbers → value.** No spreadsheet without narrative, no narrative without numbers.
2. **Quantify uncertainty.** Output a distribution, not a point.
3. **Self-falsify.** Name the assumption that carries the result and what breaks it.
4. **Investor-facing register.** Every output is for an anonymous investor — no "you", no chat context, long-form prose.
5. **Numbers ledger.** Every material figure is sourced and tiered.

## Guardrails (inherited by all sub-skills and reviewers)
- This is analysis, not personalized investment advice.
- State assumptions with basis and low/base/high ranges.
- Always report terminal-value %, price-in-distribution percentile, MoS buy-band.
- Make the bear case as rigorously as the bull case.
- Note data dates. A valuation is a living document.
- **Every Mode A report MUST include a Disclosures & Certifications appendix**
  (see `references/output-templates.md` Appendix B): Analyst Certification (Reg AC),
  Rating Distribution, Meaning of Ratings, Conflicts of Interest (FINRA 2241),
  Price Target Methodology (>=2 methods), Risk Factors, General Disclaimer.
  For China-listed names, add B.8 CSRC/SAC independence statement. A report
  without this appendix is not publishable under a regulated entity's name.
