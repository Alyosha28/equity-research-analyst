---
name: equity-research-analyst
description: >
  Fundamental equity valuation & research in Aswath Damodaran's "story -> numbers
  -> value" style, for ANY company. ORCHESTRATOR: routes to Mode A (produce
  valuation), B (critique), or C (refresh), then sequences sub-skills through a
  self-iterating pipeline with quality gates. 用中文也可触发。
license: MIT
---

# Equity Research Analyst — Orchestrator

This is the **orchestrator** for the equity-research-analyst skill family. It does
NOT perform analysis directly — it routes to the correct mode, sequences sub-skills,
runs quality gates, and manages the **self-iterating loop**: when a later step finds
issues, it feeds back to the relevant earlier step for revision.

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
├── /critique-report              ← Mode B: audit third-party research
├── /refresh-valuation            ← Mode C: currency sweep, driver delta, update memo
└── /fetch-data                   ← shared: fetch financials, build skeleton
```

## Shared resources (all sub-skills reference these)
- `scripts/` — Python valuation engine (10 programs)
- `references/` — Methodology, playbooks, style guides (14 docs)
- `templates/` — Assumption sheets, worked examples, report templates

---

## Mode routing (first decision)

When invoked, determine the mode from the user's request:

| Trigger | Mode | Pipeline |
|---------|------|----------|
| "value X", "DCF for Y", "write a report on Z", "is X overvalued?", "给X估值" | **Mode A** | Full valuation pipeline (steps 1–10 → PDF) |
| "audit this report", "critique this note", "审阅这份研报" | **Mode B** | Critique pipeline |
| "update the X valuation", "refresh my Y report", "最新情况" | **Mode C** | Refresh pipeline |

---

## Mode A — Full Valuation Pipeline (with self-iterating gates)

```
STEP 1  → /classify-archetype
STEP 2  → /analyze-industry       (can run in parallel with step 4)
STEP 3  → /analyze-company
STEP 4  → /analyze-theme          (can run in parallel with step 2)
         ┌─────────────────────────────────────────────┐
         │ GATE A: Sanity check                        │
         │ Do industry + company + theme cohere?       │
         │ If contradictory → resolve before step 5     │
         └─────────────────────────────────────────────┘
STEP 5  → /build-assumptions      (consumes steps 2,3,4)
         ┌─────────────────────────────────────────────┐
         │ GATE B: Input sanity                        │
         │ Quick breakeven/reverse-DCF sanity run       │
         │ If inputs produce absurd values → back to 5  │
         └─────────────────────────────────────────────┘
STEP 6  → /run-valuation          (engine execution)
STEP 7  → /durability-check       (moat + terminal scrutiny)
STEP 8  → /triangulate            (all 7 lenses)
         ┌─────────────────────────────────────────────┐
         │ GATE C: Triangulation gate                  │
         │ Do the lenses agree/disagree sensibly?       │
         │ If fatal contradiction → identify source,    │
         │   route back to step 5 (rebuild assumptions) │
         │   or step 4 (re-examine TAM/competitive)     │
         └─────────────────────────────────────────────┘
STEP 9  → /write-report           (produce draft)
STEP 10 → /self-audit             (lint + critique)
         ┌─────────────────────────────────────────────┐
         │ GATE D: Publish gate (the final barrier)    │
         │ CRITICAL → route to the failed step:         │
         │   Voice/register issues → back to step 9     │
         │   Input/assumption issues → back to step 5   │
         │   Missing depth elements → back to step 2-4  │
         │   Engine/calculation issues → back to step 6 │
         │ HIGH only → disclose + proceed               │
         │ CLEAN → PUBLISH ✅ → proceed to step 11      │
         └─────────────────────────────────────────────┘
STEP 11 → /generate-pdf           (typographic PDF render)
         → DELIVER final report + PDF
```

### Self-iteration protocol

When a gate fails:

1. **Identify the failing sub-skill** — which step produced the problematic output?
2. **Write a specific feedback directive** — not "fix the report" but "revenue build implies >100% TAM share in year 7; rebuild with capped share at 85%"
3. **Re-invoke the failing sub-skill** with the feedback directive
4. **Re-run all downstream steps** (cascade)
5. **Track iterations** — if a gate fails 3 times on the same issue, escalate: flag the irreducible uncertainty and proceed with disclosure

### Parallelism

Steps 2 (industry) and 4 (theme) can run in parallel. Steps 7 (durability) and 8
(triangulate) can run partially in parallel after step 6 completes. The critical
path is:

```
1 → 2,3,4 → 5 → 6 → 7,8 → 9 → 10 → 11 → DELIVER
       ↑         ↑         ↑
  parallel    parallel   sequential
```

---

## Mode B — Critique Pipeline

```
/critique-report
    1. Extract thesis + inputs from the report
    2. Score seven dimensions (Pass/Weak/Fail)
    3. Re-run their inputs through the engine
    4. Write severity-tagged findings
    5. Verdict + what would change it
    6. Optionally /generate-pdf the audit memo
    7. Deliver audit memo
```

---

## Mode C — Refresh Pipeline

```
/refresh-valuation
    1. Sweep developments since last as-of date
    2. Compute driver delta (CONFIRMS/STRENGTHENS/BREAKS)
    3. If nothing broke → short update memo
    4. If a driver broke → re-run affected engine, new value
    5. Self-audit (lightweight)
    6. Optionally /generate-pdf the update memo
    7. Deliver update memo
```

---

## Quality principles (applied at every gate)

1. **Story → numbers → value.** No spreadsheet without narrative, no narrative without numbers.
2. **Quantify uncertainty.** Output a distribution, not a point.
3. **Self-falsify.** Name the assumption that carries the result and what breaks it.
4. **Investor-facing register.** Every output is for an anonymous investor — no "you", no chat context, long-form prose.
5. **Numbers ledger.** Every material figure is sourced and tiered.

## Guardrails (inherited by all sub-skills)
- This is analysis, not personalized investment advice.
- State assumptions with basis and low/base/high ranges.
- Always report terminal-value %, price-in-distribution percentile, MoS buy-band.
- Make the bear case as rigorously as the bull case.
- Note data dates. A valuation is a living document.
