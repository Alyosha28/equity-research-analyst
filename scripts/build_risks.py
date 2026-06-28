"""Build risks.json -- quantified risk matrix for equity research.

Produces a structured catalogue of risks with probability estimates, impact on
value-per-share, monitorable indicators, trigger thresholds, and expected
timeframes. Used to feed risk-register and tornado-priority chart types.

    python build_risks.py
    python build_risks.py --output risks.json
"""

from __future__ import annotations

import argparse
import json
import sys

HARDCODED_RISKS = {
    "company": "MU",
    "valuation_date": "2026-06-28",
    "risks": [
        {
            "id": "R1",
            "category": "Cycle",
            "description": (
                "Samsung/SK Hynix break supply discipline, "
                "adding capacity beyond demand"
            ),
            "probability": 0.35,
            "impact_value_per_share": -400,
            "monitorable_indicator": "Samsung quarterly DRAM bit growth guidance",
            "trigger_threshold": "DRAM bit growth >25% YoY for 2 consecutive quarters",
            "timeframe": "2027-2028",
        },
        {
            "id": "R2",
            "category": "Competition",
            "description": (
                "CXMT achieves competitive yields on DDR5/HBM, "
                "price war in mid-range"
            ),
            "probability": 0.25,
            "impact_value_per_share": -250,
            "monitorable_indicator": "CXMT quarterly capacity announcements",
            "trigger_threshold": "CXMT DRAM share >15%",
            "timeframe": "2028-2030",
        },
        {
            "id": "R3",
            "category": "Technology",
            "description": (
                "Near-memory compute or alternative architectures "
                "reduce HBM demand per GPU"
            ),
            "probability": 0.15,
            "impact_value_per_share": -300,
            "monitorable_indicator": "GPU HBM stack count per generation",
            "trigger_threshold": "Next-gen GPU reduces HBM stacks vs prior gen",
            "timeframe": "2028-2030",
        },
        {
            "id": "R4",
            "category": "Demand",
            "description": "AI capex cycle turns, hyperscalers cut orders",
            "probability": 0.20,
            "impact_value_per_share": -500,
            "monitorable_indicator": "Hyperscaler combined capex guidance",
            "trigger_threshold": "Aggregate hyperscaler capex growth <10% YoY",
            "timeframe": "2027-2028",
        },
        {
            "id": "R5",
            "category": "Customer Concentration",
            "description": "NVIDIA shifts HBM supplier mix away from Micron",
            "probability": 0.10,
            "impact_value_per_share": -350,
            "monitorable_indicator": "NVIDIA supplier qualification announcements",
            "trigger_threshold": (
                "Micron loses NVIDIA HBM qualification for next-gen GPU"
            ),
            "timeframe": "2027-2028",
        },
        {
            "id": "R6",
            "category": "Geopolitical",
            "description": (
                "China export controls expand to include advanced memory"
            ),
            "probability": 0.15,
            "impact_value_per_share": -200,
            "monitorable_indicator": (
                "BIS entity list additions, export control rule updates"
            ),
            "trigger_threshold": "HBM added to export control list",
            "timeframe": "2026-2028",
        },
        {
            "id": "R7",
            "category": "Financial",
            "description": (
                "Debt-funded capex at cycle peak leads to "
                "balance sheet stress in downturn"
            ),
            "probability": 0.15,
            "impact_value_per_share": -150,
            "monitorable_indicator": "Net debt / TTM EBITDA ratio",
            "trigger_threshold": "Net debt / EBITDA >2.0x",
            "timeframe": "2028-2029",
        },
    ],
}


def _validate(data: dict) -> list[str]:
    """Check risk probabilities are in [0, 1] and total is not wildly off."""
    issues = []
    for r in data["risks"]:
        p = r.get("probability", -1.0)
        if not (0.0 <= p <= 1.0):
            issues.append(f"{r['id']}: probability {p} not in [0, 1]")
        if r.get("impact_value_per_share", 0) >= 0:
            issues.append(
                f"{r['id']}: impact_value_per_share should be negative (it is a risk)"
            )
    total_p = sum(r["probability"] for r in data["risks"])
    if total_p > 3.0:
        issues.append(
            f"Sum of probabilities ({total_p:.2f}) exceeds 3.0 -- "
            f"risks may overlap, verify independence"
        )
    return issues


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Build risks.json -- quantified risk matrix."
    )
    ap.add_argument(
        "--output",
        default=None,
        help="write JSON to this file instead of stdout",
    )
    ap.add_argument(
        "--validate",
        action="store_true",
        help="validate risk data consistency",
    )
    args = ap.parse_args(argv)

    data = HARDCODED_RISKS

    if args.validate:
        issues = _validate(data)
        if issues:
            for i in issues:
                print(f"VALIDATION ERROR: {i}", file=sys.stderr)
            return 1
        print("Validation passed: all risk entries consistent.")
        if args.output is None:
            return 0  # --validate alone: report only, no JSON dump

    text = json.dumps(data, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.write("\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
