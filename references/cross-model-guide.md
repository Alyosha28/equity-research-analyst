# Cross-Model Verdict Routing — Operational Guide

How the equity-research-analyst pipeline obtains verdicts on Type-B
(quality/correctness/acceptance) gates, depending on whether a cross-model
reviewer is reachable.

---

## Overview

The pipeline classifies every gate as **Type-A** (machine-checkable: exit codes,
JSON validity, numeric comparisons) or **Type-B** (requires taste, domain
knowledge, holistic judgment). Type-A gates may be self-judged. Type-B gates
require an independent verdict from outside the pipeline's authoring model
family. How that verdict is obtained depends on operational tier.

This guide defines three tiers, from strongest to weakest, and specifies the
configuration, behavior, artifact format, and disclosure obligations for each.

---

## Tier 1 — Cross-Model Review Available (PREFERRED)

**When this tier applies:**
- A model from a different family (e.g. Codex / OpenAI) is reachable and has
  sufficient quota.
- This tier should be used whenever possible — it is the only tier that is
  fully same-family-safe.

**Behavior:**

```
Pipeline step completes → Type-B gate reached →
    → Orchestrator saves work product to disk
    → Orchestrator routes to Codex (reasoning_effort: xhigh) for verdict
    → Codex reads work product, issues verdict artifact (JSON)
    → Orchestrator reads artifact, continues or loops back
```

**Configuration (settings.json or environment):**

```json
{
  "cross_model": {
    "enabled": true,
    "provider": "codex",
    "model": "xhigh",
    "reasoning_effort": "xhigh",
    "verdict_dir": "verdicts/"
  }
}
```

**Same-family-safety:** YES. All Type-B verdicts come from a differently-built
model family. The author family never reviews its own work on Type-B gates.

**Disclosure required:** None — this is the target configuration. The pipeline
operates as designed.

---

## Tier 2 — Cross-Model Unavailable (STRENGTHENED SAME-MODEL)

**When this tier applies:**
- The cross-model reviewer cannot be reached (API down, quota exhausted, rate
  limited, network failure).
- The pipeline has already retried the cross-model route and recorded the
  failure.
- The pipeline CANNOT silently self-acquit on Type-B gates — it MUST apply
  the strengthened same-model protocol below.

**Behavior:**

1. **Mandatory disagreement.** The same model reviews its own work, but the
   reviewer prompt is injected with a **devil's-advocate framing** that
   instructs the model to find at least three specific flaws, even if the work
   appears correct. The prompt MUST include:

   ```
   ROLE: You are an adversarial reviewer. Your MODEL FAMILY is {self}.
   You share architecture and biases with the author model. This makes
   you MORE likely to miss the same mistakes the author made — be
   EXTRA skeptical. You MUST find and articulate at least three
   critique points. If you genuinely cannot find flaws, explain WHY
   each dimension is clean rather than issuing a blanket PASS.
   ```

2. **Rotated critique angles.** On successive reviews of the same gate, the
   orchestrator rotates through a fixed set of critique lenses so the model
   is forced to evaluate from a different angle each time:

   | Round | Lens |
   |-------|------|
   | 1 | Numeracy / quantitative rigor |
   | 2 | Narrative coherence / logic flow |
   | 3 | Bear-case sufficiency / balance |
   | 4 | External evidence alignment |
   | 5 | Edge-case / extreme-scenario stress |

   No round uses the same lens as the previous round on the same gate.

3. **Verdict artifacts still saved.** The same-model verdict is written to disk
   with `is_cross_model: false` and the reviewer_family set to the home family.
   This preserves the artifact chain for later audit.

4. **Honest disclosure.** The pipeline MUST publish a disclosure node in the
   gate history and in the final report output:

   ```
   ⚠️ SAME-MODEL VERDICT — This Type-B gate was reviewed by the same model
   family that authored the work (cross-model reviewer unavailable).
   Same-family review is inherently less reliable than cross-model review.
   The reviewer was instructed with mandatory-disagreement framing and a
   rotated critique lens ("{lens_used}"). This verdict reduces but does
   not eliminate the risk of shared blind spots.
   ```

**Configuration:**

```json
{
  "cross_model": {
    "enabled": true,
    "provider": "codex",
    "model": "xhigh",
    "fallback_tier": 2,
    "max_retries": 2,
    "verdict_dir": "verdicts/",
    "fallback_lenses": [
      "numeracy",
      "narrative-coherence",
      "bear-case-sufficiency",
      "external-evidence",
      "edge-case-stress"
    ]
  }
}
```

**Same-family-safety:** NO. This tier is a strengthened mitigation, not a
fix. Same-model review cannot achieve the heterogeneous check that Tier 1
provides. The disclosure is mandatory and must not be buried.

---

## Tier 3 — Fully Automated (TYPE-A ONLY)

**When this tier applies:**
- The pipeline is running in a fully automated context where no reviewer model
  (cross-family or same-family) is available, OR the pipeline is configured
  explicitly for Type-A-only gates (e.g. CI linting, data-freshness checks).
- OR when a specific invocation of the equity-research-analyst skill is
  explicitly requested in "quick scan" / "automated-only" mode.

**Behavior:**

1. **Type-A gates run normally.** All machine-checkable gates (`report_lint.py`,
   JSON validity, engine sanity, numeric comparisons) execute and gate as usual.

2. **Type-B gates are SKIPPED.** The orchestrator does not invoke any Type-B
   reviewer. The gate is recorded with `overall_verdict: SKIPPED-TIER3` in the
   gate history.

3. **Mandatory disclosure.** The final output MUST include a prominent notice:

   ```
   ⚠️ AUTOMATED-ONLY PIPELINE — This analysis ran in fully automated mode.
   All quality/correctness gates (Type-B) were SKIPPED. Only machine-
   checkable gates (Type-A) were executed. The output has NOT been
   reviewed for quality, correctness, or bias. It is raw model output
   and should be treated as a first draft. Human review is REQUIRED
   before any investment decision.
   ```

**Configuration:**

```json
{
  "cross_model": {
    "enabled": false,
    "tier": 3,
    "type_b_behavior": "skip_with_disclosure",
    "verdict_dir": "verdicts/"
  }
}
```

**Same-family-safety:** NOT APPLICABLE (trivially safe). No Type-B verdicts
are issued, so there is no same-family review risk. However, the output is
unreviewed and carries the highest disclosure burden of all three tiers.

---

## Tier Selection Decision Tree

```
Can a cross-model reviewer be reached?
├── YES → Tier 1 (cross-model, same-family-safe)
│
└── NO  → Is this a fully automated / quick-scan invocation?
          ├── YES → Tier 3 (Type-A only, no Type-B review at all)
          │
          └── NO  → Tier 2 (strengthened same-model with disclosures)
                    (escalate to human review at earliest opportunity)
```

---

## Verdict Artifact Format

Every Type-B gate, regardless of tier, produces a verdict artifact on disk.
The format is defined by `verdict.py` and is the same for all tiers — the
`is_cross_model` and `reviewer_family` fields carry the tier signal.

**File naming convention:** `verdicts/{step}-{gate-id}-{iso8601-timestamp}.json`

**Schema (produced by `verdict.py --save`):**

```json
{
  "gate": "self-audit-7dim",
  "type": "B",
  "reviewer_model": "codex-xhigh",
  "reviewer_family": "openai",
  "timestamp": "2026-06-28T02:00:00Z",
  "overall_verdict": "PASS-WITH-NOTES",
  "dimensions": {
    "structural_completeness": {"score": "PASS", "evidence": "Top-down framing present throughout"},
    "input_defensibility": {"score": "PASS", "evidence": "All drivers cited to source data"},
    "internal_consistency": {"score": "PASS", "evidence": "DCF inputs match narrative drivers"},
    "accounting_integrity": {"score": "PASS", "evidence": "No circular references or double-counts"},
    "terminal_value_scrutiny": {"score": "WEAK", "evidence": "TV is 82% of total, sensitivity not prominent"},
    "uncertainty_handling": {"score": "PASS", "evidence": "MC simulation and scenario table present"},
    "bias_and_independence": {"score": "PASS", "evidence": "Bear case matches bull case in rigor"}
  },
  "notes": "TV dominance is disclosed but should be more prominent in executive summary",
  "is_cross_model": true
}
```

**Verdict values for `overall_verdict`:**

| Verdict | Meaning | Pipeline action |
|---------|---------|-----------------|
| `PASS` | No issues found | Advance to next step |
| `PASS-WITH-NOTES` | Minor improvements suggested | Advance; notes recorded for next iteration |
| `REVISE` | Material issues found | Loop back to author sub-skill (same iteration) |
| `BLOCK` | Fundamental issue; cannot proceed | Escalate to orchestrator; do not loop |
| `SKIPPED-TIER3` | Type-B gate not executed (Tier 3 only) | Record; proceed with disclosure |

---

## Escalation Rules

### Cross-model reviewer unreachable (triggers tier downgrade)

```
IF cross-model call fails with 5xx / timeout / quota-exceeded:
    1. Retry once after 30s backoff
    2. If still failing, record failure in LOOP-STATE
    3. Downgrade to Tier 2 for current gate
    4. Attempt cross-model again for next Type-B gate
    5. If 3+ consecutive Type-B gates downgrade, record escalation
       ESC-CROSS-MODEL-UNAVAILABLE and recommend human reviewer
```

### Same-model verdict loops (Tier 2 stuck detection)

```
IF same gate fails Tier-2 review 3 times with same root cause:
    1. Escalate to orchestrator (ESC-SAME-MODEL-STUCK)
    2. Do NOT try a 4th same-model review — diminishing returns
    3. Record the irreducible uncertainty in report limitations
    4. Mark the gate as UNVERIFIED-TIER2 in LOOP-STATE
    5. Publish with escalated disclosure and recommend human review
```

### Tier 3 escalation (when human review is needed)

```
IF pipeline runs in Tier 3:
    1. All Type-B gates are SKIPPED-TIER3
    2. Output MUST carry the Tier-3 disclosure block
    3. LOOP-STATE records PIPELINE_TIER=3
    4. The final output is NOT marked PUBLISHABLE
    5. A human reviewer must re-run at Tier 1 or Tier 2 before publication
```

---

## Verdict Storage and Audit Trail

All verdict artifacts live under `verdicts/` relative to the pipeline run
directory. The LOOP-STATE file links each gate to its artifact path.

**Directory layout:**

```
verdicts/
├── classify-archetype-2026-06-28T010000Z.json
├── analyze-industry-2026-06-28T011500Z.json
├── ...
├── self-audit-7dim-2026-06-28T020000Z.json
└── MANIFEST.txt          # ordered list of all artifacts in this run
```

**MANIFEST.txt** is a simple newline-delimited list of artifact filenames,
written in gate-execution order. It allows an auditor to replay the verdict
chain without needing the LOOP-STATE.

---

## Quick Reference: Tier Comparison

| Property | Tier 1 | Tier 2 | Tier 3 |
|----------|--------|--------|--------|
| Cross-model reviewer | Required | Unavailable | N/A |
| Same-family-safe | YES | NO | N/A (no Type-B) |
| Type-A gates | Normal | Normal | Normal |
| Type-B gates | Cross-model verdict | Same-model, adversarial framing | SKIPPED |
| Disclosure required | No | Yes (mandatory) | Yes (mandatory, most prominent) |
| Output status | PUBLISHABLE | PUBLISHABLE-WITH-DISCLOSURE | DRAFT-ONLY |
| Human review needed | Recommended | Strongly recommended | REQUIRED |

---

*Guide version: 1.0. Last updated: 2026-06-28.*
