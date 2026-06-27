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

3. **Loop Protocol — Type-A/B gates + cross-model verdict.** Every gate is
   classified Type-A (machine-checkable: exit code, math, counter) or Type-B
   (requires taste/judgment). Type-B gates route to a cross-model reviewer
   (Codex xhigh) — Claude can DRIVE the loop but cannot ACQUIT its own work.
   A convergence terminator caps iterations at 3 before escalating to risk
   annotation. Full protocol: `references/loop-protocol.md`.

Together these create a **same-family-safe self-iterating pipeline** where
quality is enforced at every boundary and no single model family grades
its own homework.

## Architecture

```
/equity-research-analyst          ← YOU ARE HERE (orchestrator)
├── /classify-archetype           ← classify company → pick engine/playbook
├── /analyze-industry             ← industry lifecycle, profit cycles, leader rotation
├── /analyze-company              ← business model, moat, 10yr financials, drawdowns
├── /analyze-theme                ← thematic driver, TAM × share, competitive map
├── /build-assumptions            ← story→numbers, accounting adj, write assumptions.json
├── /run-valuation                ← execute Python engine suite (DCF/MC/reverse/breakeven)
├── /durability-check             ← ROIC-WACC spread, CAP, RONIC fade, moat decomposition
├── /triangulate                  ← cross-check 7 lenses, identify dispute locus
├── /write-report                 ← produce investor-facing long-form prose
├── /self-audit                   ← lint + adversarial self-critique → gate
├── /generate-pdf                 ← render finished report to PDF (typographic, chart embeds)
├── /research                     ← shared: single-point web research, fact-checking
├── /fetch-data                   ← shared: fetch financials, build skeleton
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
- `scripts/` — Python valuation engine (10 programs)
- `references/` — Methodology, playbooks, style guides (14 docs)
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
WAVE 6 ─── single agent ───────────────────────────────────────────┐
│  Agent H: /write-report     (3,500-5,000 word investor prose)    │
│  → followed by adversarial reviewer                              │
└──────────────────────────────────────────────────────────────────┘
                              ↓ (passes review)
WAVE 7 ─── single agent ───────────────────────────────────────────┐
│  Agent I: /self-audit       (lint.py + 7-dim self-critique)      │
│  → FINAL GATE: CRITICAL → route back to root sub-skill           │
└──────────────────────────────────────────────────────────────────┘
                              ↓ (PASS)
WAVE 8 ─── single agent ───────────────────────────────────────────┐
│  Agent J: /generate-pdf     (typographic PDF with chart embeds)  │
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

**Type-B gates** — require taste/judgment, MUST route to cross-model:

| Gate | Routes to | Artifact |
|------|----------|----------|
| Adversarial review (every sub-skill) | Codex xhigh | `verdicts/{step}.json` |
| 7-dim self-audit | Codex xhigh | `verdicts/audit.json` |
| Write-report voice/depth | Codex xhigh | `verdicts/report.json` |

**Cross-model verdict flow:**
```
Claude produces output → Type-B gate reached →
  → Route to Codex (reasoning: xhigh) with the output + review criteria
  → Codex returns verdict JSON artifact saved to verdicts/{step}.json
  → Claude reads artifact → PASS: proceed | REVISE: fix + retry | BLOCK: escalate
```

**The rule:** "A loop can DRIVE; it cannot ACQUIT." Claude orchestrates and
executes, but a different model family signs off on quality.

**Same-family-safe conditions (all must hold):**
1. Every gate classified A or B
2. Every Type-B gate routes to cross-model
3. Cross-model verdict saved as inspectable artifact
4. No same-family majority treated as jury
5. Type-A self-judgment uses external checks

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

### Phase 0: Archetype

```
1. Invoke /classify-archetype
2. Spawn adversarial reviewer for classify-archetype
   - Review criteria: archetype classification correctness, engine/playbook match,
     edge cases considered, traps avoided
   - If REVISE: fix classification → re-review (max 2 rounds)
   - If BLOCK: halt — wrong company understanding
3. When PASS: lock archetype (all downstream steps inherit it)
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
  → adversarial review: accounting adjustments done? revenue bottom-up? each driver
    has basis + low/base/high? JSON valid? quick engine sanity run passes?
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

### Phase 7: Report (WAVE 6)

```
Agent H: /write-report
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
Agent I: /self-audit
  → This IS the adversarial review for the report, but more systematic:
    Check 1: report_lint.py (mechanical — must pass)
    Check 2: 7-dimension self-critique (reasoning — CRITICAL must be zero)
  → CRITICAL finding → route to root sub-skill → re-run from that step
  → HIGH only → disclose in limitations → PASS
  → CLEAN → PASS → proceed to PDF
```

### Phase 9: PDF (WAVE 8)

```
Agent J: /generate-pdf
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
