# Loop Protocol — Self-Iterating Pipeline with Cross-Model Gates

The equity-research-analyst pipeline is a **self-iterating loop** where quality
is enforced at every sub-skill boundary. This document defines the protocol that
makes the loop safe: gate taxonomy, baton-passing state, cross-model verdict
routing, and convergence rules.

Distilled from three reference architectures:
- `autonomy-loop` (inferencegod) — builder↔reviewer baton, 5-lens critic, frozen invariants
- `mission` (tackeyy) — plan→execute→review→score→iterate with threshold gate
- `acceptance-gate.md` (Auto-claude-code-research-in-sleep) — Type-A/B gate taxonomy, same-family-safe conditions

---

## 1. Type-A vs Type-B Gate Taxonomy

Every gate in the pipeline MUST be classified. No third bucket exists — if a
gate seems to be both, it is two gates and must be split.

### Type-A — EXECUTION / OBJECTIVE gate

A machine-checkable signal of *what happened* with no merit judgment.

**Dividing test:** "Could a dumb script with no taste answer this gate?"

| Gate | Check | Verdict source |
|------|-------|---------------|
| `report_lint.py` passes | Exit code 0, zero FAIL lines | Shell exit code |
| JSON validity | `json.load()` succeeds | Python `json` module |
| Engine sanity | DCF produces positive value | Math comparison |
| MC trials sufficient | trials >= 10000 | Integer comparison |
| Terminal growth ≤ riskfree | Numeric comparison | Math |
| `report_lint.py --strict` | Exit code 0, zero FAIL + zero WARN | Shell exit code |

**Rule:** Type-A gates MAY be self-judged by the same model.

### Type-B — QUALITY / CORRECTNESS / ACCEPTANCE gate

A judgment of merit, correctness, or sufficiency that requires taste, domain
knowledge, or holistic evaluation.

**Dividing test:** "Does this gate need taste / correctness / domain judgment?"

| Gate | What it judges | Why Type-B |
|------|---------------|-----------|
| 7-dim self-audit (structural completeness) | Is the reasoning top-down? | Requires holistic judgment of argument structure |
| 7-dim self-audit (input defensibility) | Are drivers justified with data? | Requires domain knowledge of what counts as "justified" |
| 7-dim self-audit (internal consistency) | Do inputs cohere sensibly? | Requires detecting subtle contradictions |
| 7-dim self-audit (bias & independence) | Is the bear case as rigorous? | Requires judgment of balance and fairness |
| Adversarial review (write-report) | Does the report read as investor research? | Requires judgment of prose quality and register |
| Adversarial review (triangulate) | Is the dispute locus correctly identified? | Requires synthesis judgment |
| Currency sweep (BREAKS verdict) | Does new data actually break the driver? | Requires domain-specific threshold judgment |

**Rule:** Type-B gates MUST route to a cross-model verdict. The loop reads the
verdict artifact — it does not re-judge it.

---

## 2. Cross-Model Verdict Routing

### When required

Every Type-B gate routes its verdict to a **different model family**:

```
Primary Codex agent runs the pipeline → Type-B gate reached →
    → Route to a different-family reviewer or human reviewer for verdict
    → Reviewer returns verdict artifact (JSON)
    → Orchestrator reads artifact, continues or loops back
```

### Verdict artifact format

Every cross-model verdict is a JSON file saved to disk:

```json
{
  "gate": "self-audit-7dim",
  "type": "B",
  "reviewer_model": "external-reviewer",
  "reviewer_family": "openai",
  "timestamp": "2026-06-28T02:00:00Z",
  "dimensions": {
    "structural_completeness": { "score": "PASS", "evidence": "..." },
    "input_defensibility": { "score": "PASS", "evidence": "..." },
    "internal_consistency": { "score": "PASS", "evidence": "..." },
    "accounting_integrity": { "score": "PASS", "evidence": "..." },
    "terminal_value_scrutiny": { "score": "WEAK", "evidence": "..." },
    "uncertainty_handling": { "score": "PASS", "evidence": "..." },
    "bias_and_independence": { "score": "PASS", "evidence": "..." }
  },
  "overall_verdict": "PASS_WITH_HIGH",
  "critical_count": 0,
  "high_count": 1,
  "high_details": ["Terminal value 82% of total not flagged prominently enough"],
  "recommendation": "PUBLISH_WITH_DISCLOSURE"
}
```

### What a cross-model PASS means

A cross-model PASS means a differently-built model, reading the artifact cold,
did not find the flaw the author would miss. It does NOT mean the work is correct,
novel, or publishable — it is the strongest automatable heterogeneous check
available. A green gate lowers risk; it does not transfer accountability.

### Fallback when cross-model is unavailable

If the cross-model reviewer cannot be reached (API down, quota exhausted):
1. **Record the failure** in the LOOP-STATE
2. **Publish with escalated disclosure** — the Type-B gate is marked UNVERIFIED
3. **Never silently self-acquit** — no same-model fallback for Type-B

---

## 3. LOOP-STATE.md — The Baton

The pipeline's shared state lives in a committed file. Because "state lives in
git," a crash resumes from the last commit rather than losing synchronization.

### Format

```markdown
# LOOP-STATE
pipeline: equity-research-analyst
company: NVIDIA Corporation (NVDA)
archetype: default
mode: A
started: 2026-06-28T01:00:00Z

## Current
step: self-audit
iteration: 2/3
turn: cross-model-reviewer
subskill_agent: self-audit

## Gate history
| # | Step | Gate | Type | Verdict | Reviewer | Artifact |
|---|------|------|------|---------|----------|----------|
| 1 | classify | adversarial-review | B | PASS | codex-primary | - |
| 2 | industry | adversarial-review | B | PASS | codex-primary | - |
| 3 | company | adversarial-review | B | PASS | codex-primary | - |
| 4 | theme | adversarial-review | B | PASS | codex-primary | - |
| 5 | assumptions | adversarial-review | B | PASS | codex-primary | - |
| 6 | assumptions | engine-sanity | A | PASS | script | - |
| 7 | valuation | adversarial-review | B | PASS | codex-primary | - |
| 8 | durability | adversarial-review | B | PASS | codex-primary | - |
| 9 | triangulate | adversarial-review | B | PASS | codex-primary | - |
| 10 | write-report | adversarial-review | B | PASS | codex-primary | - |
| 11 | self-audit | lint-check | A | PASS | script | - |
| 12 | self-audit | 7-dim-critique | B | PENDING | external-reviewer | verdicts/self-audit-001.json |

## Revision history
| Round | Step | Issue | Fixed? |
|-------|------|-------|--------|
| 1 | write-report | Second-person "you" in ¶3 | ✅ |
| 1 | write-report | Missing leader rotation table in industry | ✅ |
| 2 | write-report | MoS buy-band not stated in conclusion | ✅ |

## Escalations
(None)
```

### Turn transitions

```
turn: sub-skill-agent     → sub-skill produces output
turn: adversarial-review  → reviewer critiques output
    → REVISE: turn goes back to sub-skill-agent (same iteration, round+1)
    → PASS: turn goes to next sub-skill-agent (iteration stays, step+1)
    → BLOCK: turn goes to orchestrator (escalation)

turn: cross-model-reviewer → Type-B gate sends to external model
    → PASS: turn goes to next step
    → FAIL: turn goes back to sub-skill-agent with cross-model feedback

turn: orchestrator → convergence check, escalation decisions
```

---

## 4. Convergence Terminator

When a sub-skill and its reviewer keep trading the same failure, the system
must not loop indefinitely.

### Rules

1. **Max 2 adversarial review rounds per sub-skill per iteration.**
   After round 2, unresolved issues are escalated with a risk annotation —
   NEVER silently passed.

2. **Max 3 pipeline iterations for the same error signature.**
   If the same gate fails 3 times with the same root cause, escalate:
   - Flag the irreducible uncertainty
   - Record it in the report's limitations section
   - Proceed with the highest-quality output available
   - Mark the LOOP-STATE with the escalation

3. **Model upgrade on repeated failure.**
   If a sub-skill fails adversarial review twice:
   - First retry: same model, same prompt (clarify the feedback)
   - Second retry: upgrade model tier (e.g., haiku→sonnet, sonnet→opus)
   - Third retry: escalate to orchestrator with full diagnosis

### Escalation record

```json
{
  "escalation_id": "ESC-001",
  "gate": "self-audit-7dim",
  "type": "B",
  "root_cause": "Terminal value sensitivity analysis missing",
  "iterations_attempted": 3,
  "resolution": "PUBLISH_WITH_RISK_ANNOTATION",
  "risk_annotation": "Terminal value comprises 82% of total; sensitivity to ±2pp terminal ROC is ±$45/share. This uncertainty is disclosed in the report limitations.",
  "human_review_recommended": true
}
```

---

## 5. Score History

Persistent, cross-iteration scoring (inspired by mission's `.mission-state`):

```json
{
  "pipeline": "equity-research-analyst",
  "company": "NVDA",
  "subskill_scores": {
    "write-report": {
      "iterations": [6, 7, 8],
      "current": 8,
      "threshold": 8,
      "trend": "improving",
      "stuck": false
    },
    "self-audit": {
      "critical_count": [2, 1, 0],
      "high_count": [3, 2, 1],
      "trend": "improving",
      "stuck": false
    }
  },
  "pipeline_verdict": "PUBLISHABLE_WITH_DISCLOSURE"
}
```

### Score trend detection

- **Improving:** consecutive scores rising or stable above threshold
- **Stuck:** 3+ iterations at same score below threshold → convergence terminator triggers
- **Degrading:** scores falling → re-examine the feedback routing; may be routing to wrong sub-skill

---

## 6. Same-Family-Safe Loop Conditions

A loop is same-family-safe iff ALL five hold:

1. ✅ Every stop/accept gate is classified Type-A or Type-B (compound gates split)
2. ✅ Every Type-B gate routes to a cross-model verdict; loop reads verdict, doesn't re-judge
3. ✅ Cross-model verdict is an inspectable artifact (JSON file on disk)
4. ✅ No same-family majority is treated as a Type-B jury
5. ✅ Type-A self-judgment prefers external checks (exit codes, stats) over LLM opinion

**Current pipeline compliance:**

| Condition | Status | Gap |
|-----------|--------|-----|
| 1. Gate classification | ✅ | All gates now classified in this document |
| 2. Cross-model routing | ✅ IMPLEMENTED (tiered) | Tier 1 routes to a different-family or human reviewer; Tier 2/3 defined in cross-model-guide.md |
| 3. Verdict artifacts | ✅ IMPLEMENTED (verdict.py) | All Type-B verdicts saved as frozen JSON artifacts on disk |
| 4. No same-family jury | ⚠️ PARTIAL (Tier 1 only) | Tier 1 achieves full cross-model safety; Tier 2 uses same-model with adversarial mitigations; Tier 3 skips Type-B entirely |
| 5. Type-A external checks | ✅ | Lint, JSON, engine sanity all use external checks |

### Honest disclosure: Tier 2 and Tier 3 are NOT same-family-safe

Tier 2 (strengthened same-model) applies mandatory disagreement, rotated
critique lenses, and artifact saving — but the reviewer shares the same
underlying architecture and training distribution as the author. These
mitigations **reduce** the risk of shared blind spots; they do **not**
eliminate it. A same-model reviewer cannot provide the heterogeneous
check that a cross-model reviewer provides.

Tier 3 (fully automated) does not execute Type-B gates at all. The output
is unreviewed for quality, correctness, and bias. It is a draft.

**Only Tier 1 — cross-model routing to a different model family — achieves
the same-family-safe conditions required by this protocol.** The pipeline
MUST disclose its operational tier to the consumer of its output. When Tier
2 or Tier 3 is active, the disclosure block defined in `cross-model-guide.md`
must appear in both the LOOP-STATE gate history and the final report.

---

## 7. Integration with the Pipeline

### Gate map (Mode A)

| Step | Gate | Type | Reviewer | Artifact |
|------|------|------|----------|----------|
| classify-archetype | adversarial-review | B | cross-model (codex) | `verdicts/classify.json` |
| analyze-industry | adversarial-review | B | cross-model | `verdicts/industry.json` |
| analyze-company | adversarial-review | B | cross-model | `verdicts/company.json` |
| analyze-theme | adversarial-review | B | cross-model | `verdicts/theme.json` |
| build-assumptions | adversarial-review | B | cross-model | `verdicts/assumptions.json` |
| build-assumptions | engine-sanity | A | script | exit code |
| run-valuation | adversarial-review | B | cross-model | `verdicts/valuation.json` |
| durability-check | adversarial-review | B | cross-model | `verdicts/durability.json` |
| triangulate | adversarial-review | B | cross-model | `verdicts/triangulate.json` |
| write-report | adversarial-review | B | cross-model | `verdicts/report.json` |
| self-audit | lint-check | A | script | exit code |
| self-audit | 7-dim-critique | B | cross-model | `verdicts/audit.json` |
| generate-pdf | adversarial-review | B | cross-model | `verdicts/pdf.json` |

### Loop termination

```
loop continues WHILE:
  - any Type-A gate returns FAIL
  - any Type-B gate returns REVISE or CRITICAL
  - iteration count < max_iterations (default: 3)
  - convergence score trend is "improving" or "stable"

loop terminates WHEN:
  - ALL gates PASS (Type-A clear, Type-B PASS from cross-model)
  - max_iterations reached → publish with escalated disclosure
  - convergence terminator triggers → publish with risk annotation
```

---

*Protocol version: 1.0. Last updated: 2026-06-28.*
