"""Management credibility assessment and DCF adjustment framework.

Evaluates management track record using guidance vs. actual data, producing a
credibility score that feeds into valuation adjustments (failure probability,
margin convergence, growth discount). Designed to integrate with Damodaran's
"story -> numbers -> value" framework where management quality is a narrative
driver that gets quantified before flowing into the DCF.

Usage:
    python management_credibility.py --records records.json --assumptions assumptions.json
    python management_credibility.py --records records.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

try:
    from valuation_inputs import ValuationInputs, inputs_from_dict
except ImportError:
    from scripts.valuation_inputs import ValuationInputs, inputs_from_dict  # type: ignore

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Weights for overall credibility score (must sum to 1.0)
_W_REVENUE = 0.35
_W_MARGIN = 0.25
_W_TIMING = 0.20
_W_CAP_ALLOC = 0.20

# Map capital-allocation grade string to numeric sub-score
_CAP_ALLOC_MAP: dict[str, float] = {
    "excellent": 1.00,
    "good": 0.80,
    "neutral": 0.60,
    "poor": 0.30,
    "destructive": 0.00,
}

# Accuracy floor — even perfect guidance cannot exceed 1.0
_ACCURACY_MIN = 0.0
_ACCURACY_MAX = 1.0

# Adjustment bands: (min_score, max_score) -> AdjustmentFactors
# Ordered from highest credibility to lowest; first match wins.
_ADJUSTMENT_BANDS: list[tuple[tuple[float, float], dict]] = [
    ((0.80, 1.00), dict(failure_probability_mult=1.00, margin_convergence_delay=0,
                        growth_discount=0.00, reasoning="High credibility: no adjustment.")),
    ((0.60, 0.80), dict(failure_probability_mult=1.20, margin_convergence_delay=1,
                        growth_discount=0.02, reasoning="Mild concerns: small haircuts.")),
    ((0.40, 0.60), dict(failure_probability_mult=1.50, margin_convergence_delay=2,
                        growth_discount=0.05, reasoning="Moderate concerns: meaningful haircuts.")),
    ((0.20, 0.40), dict(failure_probability_mult=2.00, margin_convergence_delay=3,
                        growth_discount=0.10, reasoning="Significant concerns: large haircuts.")),
    ((0.00, 0.20), dict(failure_probability_mult=3.00, margin_convergence_delay=5,
                        growth_discount=0.15, reasoning="Severe concerns: punitive haircuts.")),
]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GuidanceRecord:
    """A single management guidance-vs-actual observation.

    Attributes:
        period: Label for the reporting period (e.g. "FY2024", "Q3 2024").
        metric: Category of the guidance (e.g. "revenue", "operating_margin",
                "timing_product_launch").
        guided_value: The value management guided (in reporting currency or
                      decimal for ratios).
        actual_value: The actual reported value.
        deviation_pct: Computed in __post_init__ as
                       (actual - guided) / |guided|. Positive deviation means
                       management beat their guidance (conservative); negative
                       means they missed (optimistic).
    """

    period: str
    metric: str
    guided_value: float
    actual_value: float
    deviation_pct: float = 0.0  # set in __post_init__

    def __post_init__(self):
        if self.guided_value == 0.0:
            # Avoid division by zero; treat zero-guidance as infinitely
            # imprecise (deviation = -1.0 for misses, 0.0 for hits).
            dev = 0.0 if self.actual_value == 0.0 else -1.0
        else:
            dev = (self.actual_value - self.guided_value) / abs(self.guided_value)
        object.__setattr__(self, "deviation_pct", round(dev, 6))


@dataclass(frozen=True)
class CredibilityScore:
    """Aggregated management credibility assessment.

    Attributes:
        company: Issuer / ticker identifier.
        records: Tuple of GuidanceRecord observations used for this assessment.
        revenue_accuracy: Accuracy score for revenue guidance [0, 1].
        margin_accuracy: Accuracy score for margin guidance [0, 1].
        timing_accuracy: Accuracy score for timing/schedule guidance [0, 1].
        capital_allocation_grade: Qualitative grade string.
        capital_allocation_score: Numeric mapping of capital_allocation_grade [0, 1].
        overall_score: Weighted-average credibility score [0, 1].
    """

    company: str
    records: tuple
    revenue_accuracy: float
    margin_accuracy: float
    timing_accuracy: float
    capital_allocation_grade: str
    capital_allocation_score: float
    overall_score: float


@dataclass(frozen=True)
class AdjustmentFactors:
    """Valuation adjustments derived from management credibility.

    Attributes:
        failure_probability_mult: Multiply existing failure_probability by this
                                  factor (capped at 0.99 in apply).
        margin_convergence_delay: Additional years tacked onto
                                  margin_convergence_year.
        growth_discount: Absolute reduction applied to each year's revenue
                         growth rate (e.g. 0.02 means g -> max(0, g - 0.02)).
        reasoning: Human-readable explanation for the selected adjustments.
    """

    failure_probability_mult: float
    margin_convergence_delay: int
    growth_discount: float
    reasoning: str


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------


def _categorize_record(record: GuidanceRecord) -> str:
    """Map a GuidanceRecord metric string to one of the three accuracy
    categories: 'revenue', 'margin', or 'timing'."""
    m = record.metric.lower()
    if "revenue" in m or "sales" in m or "topline" in m or "top_line" in m:
        return "revenue"
    if "margin" in m or "ebit" in m or "ebitda" in m or "profit" in m or "eps" in m:
        return "margin"
    return "timing"


def _accuracy_from_deviations(deviations: list[float]) -> float:
    """Convert a list of deviation_pct values into a [0, 1] accuracy score.

    Uses mean absolute deviation: accuracy = max(0, 1 - mean_abs_deviation).
    """
    if not deviations:
        return 0.5  # neutral — no data, no opinion
    mae = sum(abs(d) for d in deviations) / len(deviations)
    return max(_ACCURACY_MIN, min(_ACCURACY_MAX, 1.0 - mae))


def compute_credibility(
    records: tuple | list,
    cap_allocation: str = "neutral",
    company: str = "",
) -> CredibilityScore:
    """Compute a CredibilityScore from guidance records and a capital-
    allocation qualitative assessment.

    Args:
        records: Iterable of GuidanceRecord (or dicts that can be unpacked).
        cap_allocation: One of 'excellent','good','neutral','poor','destructive'.
        company: Optional company identifier for the result.

    Returns:
        CredibilityScore with computed accuracy fields and weighted overall_score.
    """
    # Normalize records to GuidanceRecord instances
    parsed: list[GuidanceRecord] = []
    for r in records:
        if isinstance(r, GuidanceRecord):
            parsed.append(r)
        elif isinstance(r, dict):
            parsed.append(GuidanceRecord(**r))
        else:
            raise TypeError(f"Expected GuidanceRecord or dict, got {type(r).__name__}")

    cap_grade = cap_allocation.lower()
    if cap_grade not in _CAP_ALLOC_MAP:
        raise ValueError(
            f"capital_allocation must be one of {sorted(_CAP_ALLOC_MAP.keys())}, "
            f"got '{cap_allocation}'"
        )
    cap_score = _CAP_ALLOC_MAP[cap_grade]

    # Group deviations by category
    buckets: dict[str, list[float]] = {"revenue": [], "margin": [], "timing": []}
    for rec in parsed:
        cat = _categorize_record(rec)
        buckets[cat].append(rec.deviation_pct)

    revenue_acc = _accuracy_from_deviations(buckets["revenue"])
    margin_acc = _accuracy_from_deviations(buckets["margin"])
    timing_acc = _accuracy_from_deviations(buckets["timing"])

    overall = round(
        _W_REVENUE * revenue_acc
        + _W_MARGIN * margin_acc
        + _W_TIMING * timing_acc
        + _W_CAP_ALLOC * cap_score,
        6,
    )

    return CredibilityScore(
        company=company,
        records=tuple(parsed),
        revenue_accuracy=round(revenue_acc, 6),
        margin_accuracy=round(margin_acc, 6),
        timing_accuracy=round(timing_acc, 6),
        capital_allocation_grade=cap_grade,
        capital_allocation_score=cap_score,
        overall_score=overall,
    )


def credibility_to_adjustments(score: CredibilityScore) -> AdjustmentFactors:
    """Map a CredibilityScore.overall_score to concrete valuation adjustments.

    The score bands are defined in _ADJUSTMENT_BANDS and use half-open
    intervals (min <= score < max, except the top band which is inclusive).
    """
    s = score.overall_score
    for (lo, hi), kwargs in _ADJUSTMENT_BANDS:
        if lo <= s <= hi or (s >= lo and hi == 1.0 and s <= hi):
            return AdjustmentFactors(**kwargs)
    # Fallback (should never reach here for scores in [0, 1])
    return AdjustmentFactors(
        failure_probability_mult=3.0,
        margin_convergence_delay=5,
        growth_discount=0.15,
        reasoning="Fallback: score out of expected range, applying severe adjustments.",
    )


def apply_adjustments(
    inp: ValuationInputs,
    adj: AdjustmentFactors,
) -> ValuationInputs:
    """Return a new ValuationInputs with credibility-driven adjustments applied.

    Adjustments:
        - failure_probability: multiplied by failure_probability_mult,
          capped at 0.99.
        - margin_convergence_year: delayed by margin_convergence_delay.
        - revenue_growth: each year's growth rate reduced by growth_discount,
          floored at 0.
        - cost_of_capital_initial: nudged up slightly for lower credibility
          via a small premium proportional to growth_discount (0.5 * gd).
    """
    # Adjust failure probability
    new_fail = min(0.99, inp.failure_probability * adj.failure_probability_mult)

    # Delay margin convergence
    new_margin_conv = inp.margin_convergence_year + adj.margin_convergence_delay

    # Discount growth rates (floor at 0)
    new_growth = tuple(max(0.0, g - adj.growth_discount) for g in inp.revenue_growth)

    # Small CoC premium for lower credibility
    coc_premium = 0.5 * adj.growth_discount  # e.g. 0.05 discount -> 0.025 CoC bump
    new_coc_init = inp.cost_of_capital_initial + coc_premium
    new_coc_term = inp.cost_of_capital_terminal + coc_premium

    return inp.with_(
        failure_probability=new_fail,
        margin_convergence_year=new_margin_conv,
        revenue_growth=new_growth,
        cost_of_capital_initial=new_coc_init,
        cost_of_capital_terminal=new_coc_term,
    )


# ---------------------------------------------------------------------------
# JSON serialisation helpers
# ---------------------------------------------------------------------------


def _score_to_dict(score: CredibilityScore) -> dict:
    return {
        "company": score.company,
        "revenue_accuracy": score.revenue_accuracy,
        "margin_accuracy": score.margin_accuracy,
        "timing_accuracy": score.timing_accuracy,
        "capital_allocation_grade": score.capital_allocation_grade,
        "capital_allocation_score": score.capital_allocation_score,
        "overall_score": score.overall_score,
        "n_records": len(score.records),
        "record_deviations": [
            {"period": r.period, "metric": r.metric, "deviation_pct": r.deviation_pct}
            for r in score.records
        ],
    }


def _adjustments_to_dict(adj: AdjustmentFactors) -> dict:
    return {
        "failure_probability_mult": adj.failure_probability_mult,
        "margin_convergence_delay": adj.margin_convergence_delay,
        "growth_discount": adj.growth_discount,
        "reasoning": adj.reasoning,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Management credibility assessment and DCF adjustments.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python management_credibility.py --records records.json
  python management_credibility.py --records records.json --assumptions assumptions.json --company BYD
  python management_credibility.py --records records.json --cap-allocation poor
        """.strip(),
    )
    p.add_argument(
        "--records",
        required=True,
        type=Path,
        help="Path to JSON array of guidance records (period, metric, guided_value, actual_value).",
    )
    p.add_argument(
        "--assumptions",
        type=Path,
        default=None,
        help="Optional path to DCF assumptions JSON. If supplied, adjusted assumptions are printed.",
    )
    p.add_argument(
        "--company",
        default="",
        help="Company/ticker identifier (default: empty).",
    )
    p.add_argument(
        "--cap-allocation",
        default="neutral",
        choices=sorted(_CAP_ALLOC_MAP.keys()),
        help="Qualitative capital-allocation assessment (default: neutral).",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path for credibility assessment JSON.",
    )
    return p


def _load_records(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"Records file must contain a JSON array, got {type(data).__name__}")
    return data


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # 1. Load records --------------------------------------------------------
    try:
        raw_records = _load_records(args.records)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error loading records: {exc}", file=sys.stderr)
        return 1

    # 2. Compute credibility -------------------------------------------------
    try:
        score = compute_credibility(
            records=raw_records,
            cap_allocation=args.cap_allocation,
            company=args.company,
        )
    except (ValueError, TypeError) as exc:
        print(f"Error computing credibility: {exc}", file=sys.stderr)
        return 1

    # 3. Map to adjustments --------------------------------------------------
    adjustments = credibility_to_adjustments(score)

    # 4. Print summary -------------------------------------------------------
    score_data = _score_to_dict(score)
    adj_data = _adjustments_to_dict(adjustments)

    print(json.dumps({"credibility": score_data, "adjustments": adj_data}, indent=2))

    # 5. Optionally apply to assumptions -------------------------------------
    if args.assumptions:
        try:
            inp = inputs_from_dict(
                json.loads(args.assumptions.read_text(encoding="utf-8"))
            )
        except Exception as exc:
            print(f"Error loading assumptions: {exc}", file=sys.stderr)
            return 1

        adjusted = apply_adjustments(inp, adjustments)
        # Print adjusted assumptions as JSON for downstream consumption
        adjusted_json = {
            "original": inp.to_dict(),
            "adjusted": adjusted.to_dict(),
            "adjustment_reasoning": adj_data["reasoning"],
        }
        print("\n--- Adjusted Valuation Inputs ---")
        print(json.dumps(adjusted_json, indent=2, default=str))

    # 6. Optionally write output file ----------------------------------------
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"credibility": score_data, "adjustments": adj_data}, indent=2),
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
