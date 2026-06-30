---
name: equity-research-analyst
description: >
  Fundamental equity valuation & research in Aswath Damodaran's "story -> numbers
  -> value" style, for ANY company. ORCHESTRATOR: routes to Mode A/B/C, spawns
  parallel agent teams for concurrent sub-skills, and runs adversarial review
  agents after every step (1鈥? revision rounds). 鐢ㄤ腑鏂囦篃鍙Е鍙戙€?
license: MIT
---

# Equity Research Analyst 鈥?Orchestrator

This is the **orchestrator** for the equity-research-analyst skill family. It does
THREE things that make the pipeline rigorous:

1. **Agent Team 鈥?default parallelism.** Where sub-skills are independent, the
   orchestrator spawns parallel agents (not sequential). Industry + Theme analysis
   run simultaneously. Durability + Triangulation run simultaneously after the
   engine. No manual "run these in parallel" instruction needed 鈥?it's the default.

2. **Adversarial Review 鈥?per-step gate.** After EVERY sub-skill completes, an
   adversarial review agent critiques the output. The reviewer's job is to find
   flaws and demand fixes. Each sub-skill gets 1鈥? revision rounds. Only when the
   reviewer signs PASS does the output proceed to the next step.

3. **Loop Protocol 鈥?Type-A/B gates + adversarial review.** Every gate is
   classified Type-A (machine-checkable: exit code, math, counter) or Type-B
   (requires taste/judgment). Type-B gates use adversarial review agents 鈥?currently
   same-model, with different-family or human review as the target architecture. The
   five same-family-safe conditions and their compliance status are maintained in
   `references/loop-protocol.md` 搂6. Honest gap disclosure: the pipeline does NOT
   claim same-family safety until cross-model routing is operational; all current
   gaps are documented, not hidden. A convergence terminator caps iterations at 3
   before escalating to risk annotation.

Together these create a **self-iterating pipeline with honest gap disclosure**.
Quality is enforced at every boundary.

## Architecture

```
/equity-research-analyst          鈫?YOU ARE HERE (orchestrator)
鈹溾攢鈹€ /classify-archetype           鈫?classify company 鈫?archetype + life-cycle phase
鈹溾攢鈹€ /analyze-industry             鈫?industry lifecycle, profit cycles, leader rotation
鈹溾攢鈹€ /analyze-company              鈫?business model, moat, 10yr financials, drawdowns
鈹溾攢鈹€ /analyze-theme                鈫?thematic driver, TAM 脳 share, competitive map
鈹溾攢鈹€ /build-assumptions            鈫?story鈫抧umbers, accounting adj, write assumptions.json
鈹溾攢鈹€ /run-valuation                鈫?execute Python engine suite (DCF/MC/reverse/breakeven)
鈹溾攢鈹€ /durability-check             鈫?ROIC-WACC spread, CAP, RONIC fade, moat decomposition
鈹溾攢鈹€ /triangulate                  鈫?cross-check 8 lenses, identify dispute locus
鈹溾攢鈹€ /generate-charts              鈫?render 12 publication-grade charts from engine JSON
鈹溾攢鈹€ /write-report                 鈫?produce investor-facing long-form prose
鈹溾攢鈹€ /self-audit                   鈫?lint + adversarial self-critique 鈫?gate
鈹溾攢鈹€ /generate-pdf                 鈫?render finished report to PDF (typographic, chart embeds)
鈹溾攢鈹€ /research                     鈫?shared: single-point web research, fact-checking
鈹溾攢鈹€ /fetch-data                   鈫?shared: fetch financials, build skeleton
鈹溾攢鈹€ /fetch-damodaran-data         鈫?NEW: fetch current ERP, CRP, betas, CoC from NYU Stern
鈹溾攢鈹€ /critique-report              鈫?Mode B: audit third-party research
鈹斺攢鈹€ /refresh-valuation            鈫?Mode C: currency sweep, driver delta, update memo
```
## Shared agents

Analysis sub-skills invoke these instead of duplicating logic:

| Agent | Purpose | Called by |
|-------|---------|-----------|
| /research | Web research, fact-checking, source annotation | industry, company, theme, assumptions, refresh, critique |
| /fetch-data | Financial data skeleton from filings/APIs | assumptions, standalone |

**Rule:** Send a research brief to /research -- do not run web search in analysis skills.


## Shared resources
- `scripts/` 鈥?Python valuation engine (17 programs: dcf, mc, reverse_dcf, breakeven, comps, sotp, financial_valuation, fetch_financials, fetch_consensus, report_lint, financial_stress, verdict, build_manifest, build_industry_memory, management_credibility, select_charts)
- `skills/generate-charts/scripts/` 鈥?Chart rendering system (13 chart modules + theme + CJK + charts CLI). Story-driven chart selection via `scripts/select_charts.py`.
- `references/` 鈥?Methodology, playbooks, style guides (18 docs: 4 archetype playbooks + default, cross-model-guide, loop-protocol, methodology-damodaran, valuation-lenses, input-estimation, analyst-playbook, report-critique-rubric, output-templates, report-voice, live-tracking, self-audit-gate, holding-company-sotp, report-quality-gate)
- `skills/` 鈥?17 sub-skills with SKILL.md manifests
- `templates/` 鈥?Assumption sheets, worked examples, report templates
- Project entry point: `src/common/build_report.py` 鈥?reproducible PDF render (WeasyPrint default, logo auto-detect, config-driven). Chart contract: `![](figs/<ticker>_<kind>)`.

---

## Three Core Mechanisms

### Mechanism 1 鈥?Agent Team (Default Parallelism)

The orchestrator **automatically** spawns parallel agents for independent work.
You do NOT need to ask for concurrency 鈥?it's the default behavior.

**Mode A agent team deployment:**

```
WAVE 1 鈹€鈹€鈹€ spawn 2 agents in PARALLEL 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹? Agent A: /analyze-industry  (industry lifecycle, leader rotation)鈹?
鈹? Agent B: /analyze-theme     (TAM 脳 share, competitive map)      鈹?
鈹? 鈫?each followed by its adversarial reviewer                     鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                              鈫?(both pass review)
WAVE 2 鈹€鈹€鈹€ single agent (industry context needed) 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹? Agent C: /analyze-company  (business model, 10yr financials)    鈹?
鈹? 鈫?followed by adversarial reviewer                              鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                              鈫?(passes review)
WAVE 3 鈹€鈹€鈹€ single agent 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹? Agent D: /build-assumptions (story鈫抧umbers, write .json)        鈹?
鈹? 鈫?followed by adversarial reviewer + quick engine sanity run    鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                              鈫?(passes review)
WAVE 4 鈹€鈹€鈹€ single agent 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹? Agent E: /run-valuation    (DCF, MC, breakeven, reverse DCF)    鈹?
鈹? 鈫?followed by adversarial reviewer                              鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                              鈫?(passes review)
WAVE 5 鈹€鈹€鈹€ spawn 3 agents in PARALLEL 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹? Agent F: /durability-check (ROIC-WACC, CAP, RONIC, moat)        鈹?
鈹? Agent G: /triangulate      (8-lens cross-check, dispute locus)  鈹?
鈹? Agent H: /generate-charts  (story-driven charts from engine     鈹?
鈹?          JSON; runs select_charts.py first, renders all charts   鈹?
鈹?          whose source data is ready, defers roic_spread until   鈹?
鈹?          durability.json exists)                                 鈹?
鈹? 鈫?each followed by its adversarial reviewer                     鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                              鈫?(all pass review)
                              鈹屸攢鈹€鈹€ CONSISTENCY CHECK 鈹€鈹€鈹€鈹?
                              鈹?Do durability +         鈹?
                              鈹?triangulation agree?    鈹?
                              鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                              鈫?(consistent)
WAVE 6 鈹€鈹€鈹€ single agent 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹? Agent I: /write-report     (3,500-5,000 word investor prose)    鈹?
鈹? 鈫?followed by adversarial reviewer                              鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                              鈫?(passes review)
WAVE 7 鈹€鈹€鈹€ single agent 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹? Agent J: /self-audit       (lint.py + 7-dim self-critique)      鈹?
鈹? 鈫?FINAL GATE: CRITICAL 鈫?route back to root sub-skill           鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                              鈫?(PASS)
WAVE 8 鈹€鈹€鈹€ single agent 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹? Agent K: /generate-pdf     (typographic PDF with chart embeds)  鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                              鈫?
                          DELIVER
```

### Mechanism 2 鈥?Adversarial Review (Per-Step Gate)

After **EVERY** sub-skill completes, the orchestrator spawns an adversarial
review agent. This is NOT the same as the final self-audit 鈥?it's a per-step
quality check that catches errors early.

**Review agent design:**

```
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹?        ADVERSARIAL REVIEW AGENT             鈹?
鈹?                                            鈹?
鈹? Given:                                     鈹?
鈹? - Sub-skill's output                       鈹?
鈹? - Sub-skill's self-check checklist         鈹?
鈹? - Sub-skill's review criteria              鈹?
鈹?                                            鈹?
鈹? Task:                                      鈹?
鈹? 1. Find at least ONE thing wrong or weak   鈹?
鈹? 2. Rate: PASS / REVISE / BLOCK             鈹?
鈹? 3. For REVISE: specific, actionable fix   鈹?
鈹? 4. For PASS: state why it survives scrutiny鈹?
鈹?                                            鈹?
鈹? Rules:                                     鈹?
鈹? - Default stance: SKEPTICAL (not rubber-  鈹?
鈹?   stamp 鈥?adversarial, not friendly)       鈹?
鈹? - Must find at least 1 weakness. If the   鈹?
鈹?   output is genuinely flawless, the       鈹?
鈹?   reviewer states: "Best-effort critique  鈹?
鈹?   found no material issues 鈥?PASS."        鈹?
鈹? - Max 2 revision rounds. After round 2,   鈹?
鈹?   unresolved issues are escalated to the  鈹?
鈹?   orchestrator with a RISK ANNOTATION.     鈹?
鈹? - BLOCK verdict only for fatal errors      鈹?
鈹?   (e.g., wrong archetype, broken math,     鈹?
鈹?   fabricated numbers).                     鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
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
sub-skill 鈫?output 鈫?adversarial review 鈫?REVISE?
    鈫?                                       鈹?
    鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€ fix + re-submit (round 2) 鈹€鈹€鈹€鈹€鈹€鈹?
                                                 鈫?
                                            REVISE again?
                                                 鈹?
                                    鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹粹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                                    鈫?                        鈫?
                                  PASS                    ESCALATE
                              (proceed to               (flag to user
                               next step)              with risk note)
```

### Mechanism 3 鈥?Loop Protocol (Type-A/B Gates + Cross-Model Verdict)

Every gate in the pipeline is classified Type-A or Type-B. The taxonomy and
rules come from `references/loop-protocol.md`.

**Type-A gates** 鈥?machine-checkable, same-model self-judgment allowed:

| Gate | Check | Verdict source |
|------|-------|---------------|
| `report_lint.py` | Exit code 0, zero FAIL | Shell exit code |
| JSON validity | `json.load()` succeeds | Python stdlib |
| Engine sanity | DCF produces positive value | Math comparison |
| MC trials | trials >= 10000 | Integer comparison |
| Terminal growth | growth <= riskfree rate | Math |

**Type-B gates** 鈥?require taste/judgment. Currently self-judged by adversarial
review agents (same model family). Target: cross-model routing (see gap assessment
in `references/loop-protocol.md` Section 6).

| Gate | Current reviewer | Target reviewer | Target artifact |
|------|------------------|-----------------|-----------------|
| Adversarial review (every sub-skill) | Primary Codex agent team (same-family) | Different-family reviewer or human review | `verdicts/{step}.json` |
| 7-dim self-audit | Primary Codex agent team (same-family) | Different-family reviewer or human review | `verdicts/audit.json` |
| Write-report voice/depth | Primary Codex agent team (same-family) | Different-family reviewer or human review | `verdicts/report.json` |
| Generate-charts visual quality | Primary Codex agent team (same-family) | Different-family reviewer or human review | `verdicts/charts.json` |

**Current (same-model adversarial) flow:**
```
Primary Codex agent produces output 鈫?Type-B gate reached 鈫?  鈫?Same-model adversarial review agent critiques output
  鈫?Review verdict returned inline (not saved as artifact)
  鈫?PASS: proceed | REVISE: fix + retry | BLOCK: escalate
```

**Target (cross-model) flow:**
```
Primary Codex agent produces output 鈫?Type-B gate reached 鈫?  鈫?Route to a different-family reviewer or human reviewer with the output + review criteria
  鈫?Reviewer returns verdict JSON artifact saved to verdicts/{step}.json
  鈫?Orchestrator reads artifact 鈫?PASS: proceed | REVISE: fix + retry | BLOCK: escalate
```

**The rule:** "A loop can DRIVE; it cannot ACQUIT." This is the target 鈥?the
primary Codex agent team orchestrates and executes, but a different model family
or a human reviewer should sign off on material quality gates.
Currently, same-model adversarial review provides the best available check; the
gap to cross-model routing is openly documented.

**Same-family-safe conditions (target 鈥?3 of 5 currently unmet):**
1. Every gate classified A or B 鉁?
2. Every Type-B gate routes to cross-model 鈿狅笍 (currently self-judged)
3. Cross-model verdict saved as inspectable artifact 鈿狅笍 (only safe when available)
4. No same-family majority treated as jury 鈿狅笍 (same-family agent teams are useful reviewers, not independent acquitters)
5. Type-A self-judgment uses external checks 鉁?

See `references/loop-protocol.md` Section 6 for the detailed gap assessment.

**Convergence terminator:**
- Max 2 adversarial review rounds per sub-skill
- Max 3 pipeline iterations for same error signature
- On third failure: escalate with risk annotation, publish with disclosure
- Rule: NEVER silently pass; unresolved issues are always surfaced

**LOOP-STATE.md** 鈥?the baton file that records current step, gate history,
verdict artifacts, revision history, and escalations. Full format in
`references/loop-protocol.md`.

---

## Mode A 鈥?Full Pipeline Execution

### Phase 0: Archetype + Life-Cycle Phase + Damodaran Data

```
1. Invoke /fetch-damodaran-data
   - Fetch latest implied ERP (monthly update from pages.stern.nyu.edu/~adamodar)
   - Fetch country risk premiums (latest ctryprem.xlsx 鈥?Jan or July update)
   - Fetch industry betas and cost of capital (betas.xls, wacc.xls)
   - Record current riskfree rate (10-year government bond, adjusted for sovereign default spread)
   - Evaluate trust-deficit signals (sovereign downgrade, USD trend, gold, CB independence, governance)
   - Output: damodaran_data.json with all fetched data + dates 鈫?fed to /build-assumptions
   - **Offline fallback:** If Damodaran pages are unreachable (network, site maintenance):
     a) Use cached damodaran_data.json from a prior run if within acceptable age
        (ERP <2mo, riskfree <1wk, CRP <7mo, betas/WACC <13mo)
     b) Annotate output with STALE_DATA or UNCACHED_FALLBACK per data class
     c) If no cache exists: use historically-reasonable defaults (ERP=5%,
        riskfree=current 10yr Treasury) with UNCACHED_FALLBACK annotation
     d) The annotation is carried into the report's limitations section
     e) Never silently use stale/fallback data without disclosure

2. Invoke /classify-archetype
   - Produces BOTH business-model archetype AND corporate life-cycle phase (6 phases from Damodaran 2024 book)
   - Life-cycle phase determines: narrative emphasis, driver sensitivity, convergence shape, terminal structure

3. Spawn adversarial reviewer for classify-archetype
   - Review criteria: archetype + phase correctness, consistency, engine/playbook match, edge cases, traps avoided
   - If REVISE: fix classification 鈫?re-review (max 2 rounds)
   - If BLOCK: halt 鈥?wrong company understanding

4. When PASS: lock archetype + phase + current market data (all downstream steps inherit)
   - Data dates are recorded 鈥?the valuation is dated at this point
```

### Phase 1: Research (WAVE 1 鈥?parallel)

```
SPAWN 2 AGENTS IN PARALLEL:

Agent A: /analyze-industry
  鈫?adversarial review: are lifecycle/margin/leader data sourced and spanning 10+ years?
  鈫?if REVISE: fix gaps 鈫?re-review

Agent B: /analyze-theme
  鈫?adversarial review: is TAM sourced? two revenue paths attempted? Big Market Delusion checked?
  鈫?if REVISE: fix gaps 鈫?re-review

(Both agents run concurrently. Orchestrator waits for both to PASS.)
```

### Phase 2: Company (WAVE 2)

```
Agent C: /analyze-company (uses Agent A's industry context)
  鈫?adversarial review: business model clear? moat decomposed? 10yr trajectory +
    drawdowns present? SBC dilution stated?
  鈫?if REVISE: fix gaps 鈫?re-review
```

### Phase 3: Cross-phase sanity (GATE A)

```
Orchestrator runs a quick consistency check across phases 1+2:
- Does the industry analysis contradict the theme?
- Does the company's moat make sense given the industry structure?
- Does the TAM share trajectory fit the competitive landscape?
鈫?If contradiction found: identify which sub-skill is the source, route fix
```

### Phase 4: Assumptions (WAVE 3)

```
Agent D: /build-assumptions
  鈫?Consumes: damodaran_data.json (current ERP, CRP, betas, riskfree), industry/company/theme analyses, archetype + life-cycle phase
  鈫?Uses current implied ERP (not hardcoded) for cost of capital estimation
  鈫?Life-cycle phase informs: margin glide shape, growth deceleration rate, cost-of-capital glide timing, failure probability, terminal structure
  鈫?Evaluates trust-deficit / institutional-risk overlay (documented as named, separate premium if applied)
  鈫?Adversarial review: accounting adjustments done? revenue bottom-up? each driver has basis + low/base/high? ERP/CRP data dated? trust-deficit overlay evaluated? JSON valid? quick engine sanity run passes?
  鈫?if REVISE: fix 鈫?re-review
```

### Phase 5: Engine (WAVE 4)

```
Agent E: /run-valuation
  鈫?adversarial review: all applicable scripts executed? terminal % stated?
    price percentile reported? MoS band extracted? reverse-DCF plausible?
  鈫?if REVISE: re-run with fixes 鈫?re-review
```

### Phase 6: Analysis & Charts (WAVE 5 鈥?parallel)

```
SPAWN 3 AGENTS IN PARALLEL:

Agent F: /durability-check
  鈫?adversarial review: ROIC R&D-adjusted? each moat component has named threat +
    monitorable indicator? CAP justified? terminal sensitivity shown?
  鈫?if REVISE: fix 鈫?re-review

Agent G: /triangulate
  鈫?adversarial review: all 8 lenses present? dispute locus specific? variant
    perception falsifiable? not averaging lenses?
  鈫?if REVISE: fix 鈫?re-review

Agent H: /generate-charts (runs IN PARALLEL with durability + triangulation 鈥?
  charts only consume engine JSON, not durability/triangulation outputs)
  鈫?STEP 0: Run scripts/select_charts.py TICKER --data-dir data/ --json
    (reads classification 鈫?archetype rules 鈫?narrative overrides 鈫?checks data
    readiness; outputs manifest with required/optional/skipped/data_ready/data_missing)
  鈫?Renders all REQUIRED + OPTIONAL charts whose source JSON is ready
  鈫?Charts needing durability.json (roic_spread) are deferred 鈥?a quick follow-up
    render runs after durability passes
  鈫?Chart contract: ![](figs/<ticker>_<kind>)
  鈫?Output: figs/<ticker>/<ticker>_{kind}.{svg,png} + chart-index.json
  鈫?CJK font auto-detection, theme from config (default: Goldman-style palette)
  鈫?adversarial review:
    - Type-A: all required SVGs rendered? chart-index.json matches manifest?
      file sizes OK? data_missing reported?
    - Type-B: visual quality? CJK rendering correct? chart titles declarative?
      color palette consistent? charts support the narrative?
  鈫?if REVISE: fix specific charts 鈫?re-review (max 2 rounds)

POST-WAVE 5 CONSISTENCY CHECK (durability + triangulation):
- Does the CAP from durability match the dispute locus from triangulation?
- If durability says "moat is strong for 15 years" but triangulation says
  "fight is about terminal margin" 鈫?resolve the tension
```


### Phase 7: Report (WAVE 6)

```
Agent I: /write-report
  鈫?adversarial review (most thorough 鈥?this is the deliverable):
    - Voice check: grep for "you"/"浣?, emoji, banned patterns
    - Depth check: all 6 Damodaran depth elements present?
    - Numbers check: every material figure sourced and tiered?
    - Structure check: sections follow Template A?
    - Register check: reads like a research report, not an AI answer?
  鈫?if REVISE: fix 鈫?re-review (may need 2 rounds for prose quality)
```

### Phase 8: Audit (WAVE 7)

```
Agent J: /self-audit
  鈫?This IS the adversarial review for the report, but more systematic:
    Check 1: report_lint.py (mechanical 鈥?must pass)
    Check 2: 7-dimension self-critique (reasoning 鈥?CRITICAL must be zero)
  鈫?CRITICAL finding 鈫?route to root sub-skill 鈫?re-run from that step
  鈫?HIGH only 鈫?disclose in limitations 鈫?PASS
  鈫?CLEAN 鈫?PASS 鈫?proceed to PDF
```

### Phase 9: PDF (WAVE 8)

```
Agent K: /generate-pdf
  鈫?Canonical entry point: python src/common/build_report.py TICKER
    (reads config.py for engine/logo height/inline SVG 鈥?reproducible across
    sessions without needing to remember CLI flags)
  鈫?Engine: WeasyPrint default (native vector SVG, ~5x smaller PDFs, CSS Paged
    Media page numbering). Auto-falls back to Playwright if WeasyPrint unavailable.
  鈫?Logo: auto-detected from assets/company_logo.* (when present). Top margin
    auto-grows to logo_height + 1.4cm so enlarged logos never overlap body text.
    Logo is optional 鈥?absent logo renders cleanly without branding.
  鈫?Charts: all markdown chart refs MUST use ![](figs/<ticker>_<kind>) format.
    Missing figs/ prefix 鈫?chart unrecognized 鈫?PRE-RENDER FAIL.
  鈫?--auto-charts flag runs select_charts internally for chart coverage
    verification (required charts missing 鈫?BLOCK before render)
  鈫?CJK fonts auto-detected; rating box extracted and styled
  鈫?Output: TICKER_research_report.pdf + preview PNGs (verify_visual=True)
  鈫?adversarial review: all charts embedded? CJK fonts render? rating box
    prominent? pages numbered? disclaimer present? printable in B&W?
  鈫?if REVISE: fix rendering 鈫?re-review
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

## Mode B 鈥?Critique Pipeline

```
Agent: /critique-report
  1. Extract thesis + inputs from the report
  2. Score seven dimensions (Pass/Weak/Fail)
  3. Re-run their inputs through the engine
  4. Write severity-tagged findings
  5. Verdict + what would change it

  鈫?adversarial review: is each scored dimension backed by quoted evidence?
    are re-run results present? CRITICAL findings block a "reliable" verdict?

  鈫?Optionally /generate-pdf the audit memo
  鈫?Deliver
```

---

## Mode C 鈥?Refresh Pipeline

```
Agent: /refresh-valuation
  1. Sweep developments since last as-of date
  2. Compute driver delta (CONFIRMS/STRENGTHENS/BREAKS)
  3. If nothing broke 鈫?short update memo
  4. If a driver broke 鈫?re-run affected engine, new value

  鈫?adversarial review: is every development dated and source-tiered?
    driver delta explicit for each driver? reverse-DCF re-run at current price?

  鈫?Lightweight self-audit
  鈫?Optionally /generate-pdf
  鈫?Deliver
```

---

## Escalation rules (when revision rounds are exhausted)

After 2 rounds of adversarial review without PASS:

1. **Record the unresolved issue** with a risk annotation
2. **Publish with disclosure** 鈥?the issue must be stated in the report's limitations section
3. **Flag to user** 鈥?"Note: [sub-skill] output has an unresolved weakness: [specific].
   Published with this caveat. To strengthen, re-run with better input data."
4. **Never silently pass** 鈥?unresolved adversarial feedback is always surfaced

## Quality principles (applied at every adversarial review)

1. **Story 鈫?numbers 鈫?value.** No spreadsheet without narrative, no narrative without numbers.
2. **Quantify uncertainty.** Output a distribution, not a point.
3. **Self-falsify.** Name the assumption that carries the result and what breaks it.
4. **Investor-facing register.** Every output is for an anonymous investor 鈥?no "you", no chat context, long-form prose.
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
- **End-of-session adversarial review is mandatory.** Every session that modifies
  code or produces a report MUST end with adversarial review agents examining
  every completed step. No deliverable ships without review.
- **Chart contract:** All markdown chart references MUST use
  ``![](figs/<ticker>_<kind>)`` with the ``figs/`` prefix. This is the contract
  between ``write-report``, ``generate-charts``, and ``generate-pdf``. Without it,
  ``render_pdf.py`` cannot resolve chart references to filesystem paths, and the
  pre-render chart coverage gate will BLOCK.
- **Content quality gate:** Before publishing, verify against
  ``references/report-quality-gate.md`` (52-point checklist: structural completeness,
  Damodaran framework discipline, multi-lens triangulation, narrative falsifiability).
  Type-A items must pass ``report_lint.py`` with zero FAIL. Type-B items route
  through adversarial review.
- **Story-driven chart selection:** The ticker archetype + narrative determine
  which charts to generate 鈥?NOT a fixed template. Run
  ``scripts/select_charts.py`` before ``generate-charts``. This ensures every
  chart supports the investment thesis rather than decorating it.
