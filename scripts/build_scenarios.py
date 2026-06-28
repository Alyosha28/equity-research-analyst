"""Build scenarios.json -- bull/base/bear scenario synthesis for DCF valuation.

Reads an optional assumptions file and synthesises three scenarios by varying the
key value drivers (terminal revenue, target operating margin, terminal ROC). When
no assumptions file is given, produces hardcoded Micron (MU) example data.

    python build_scenarios.py
    python build_scenarios.py --assumptions ../templates/assumptions.example.json
    python build_scenarios.py --output scenarios.json
"""

from __future__ import annotations

import argparse
import json
import sys

HARDCODED_MU = {
    "company": "MU",
    "valuation_date": "2026-06-28",
    "scenarios": [
        {
            "name": "Bull - Structural Shift",
            "probability": 0.10,
            "revenue_y10_m": 700000,
            "target_op_margin": 0.45,
            "terminal_roc": 0.12,
            "value_per_share": 1662,
            "key_drivers": [
                "AI demand exceeds capacity through 2030",
                "HBM share expands to 35%",
                "Industry supply discipline holds",
            ],
        },
        {
            "name": "Base - Cycle Mean Reversion",
            "probability": 0.55,
            "revenue_y10_m": 147000,
            "target_op_margin": 0.28,
            "terminal_roc": 0.09,
            "value_per_share": 632,
            "key_drivers": [
                "2026-27 peak, 2028-29 capacity release",
                "Normalized margins ~28%",
                "HBM structural premium partial",
            ],
        },
        {
            "name": "Bear - Capital Cycle Repeats",
            "probability": 0.35,
            "revenue_y10_m": 80000,
            "target_op_margin": 0.15,
            "terminal_roc": 0.07,
            "value_per_share": 200,
            "key_drivers": [
                "Samsung/CXMT break supply discipline",
                "HBM oversupply + DRAM price crash",
                "Margin <15%, recession",
            ],
        },
    ],
}


def _from_assumptions(path: str) -> dict:
    """Load assumptions, run the base-case DCF, then construct bull/bear by
    perturbing the three main value drivers."""
    try:
        from valuation_inputs import load_inputs
        import dcf_valuation as dcf
    except ImportError:
        from scripts.valuation_inputs import load_inputs  # type: ignore
        from scripts import dcf_valuation as dcf  # type: ignore

    inp = load_inputs(path)
    base = dcf.value(inp)

    # Bull: terminal revenue 3x, margin +15pp, terminal ROC +3pp
    bull_rev = inp.revenue_path()[-1] * 3.0
    bull_inp = inp.with_(
        target_operating_margin=min(inp.target_operating_margin + 0.15, 0.55),
        terminal_roc=inp.terminal_roc + 0.03,
    )
    # Rebuild growth path to hit bull_rev
    from valuation_inputs import build_declining_growth
    bull_inp = bull_inp.with_(
        revenue_growth=build_declining_growth(
            inp.base_revenue, bull_rev, inp.terminal_growth, inp.horizon
        )
    )
    bull_vps = dcf.value(bull_inp).value_per_share

    # Bear: terminal revenue 0.5x, margin -15pp, terminal ROC -2pp
    bear_rev = inp.revenue_path()[-1] * 0.5
    bear_inp = inp.with_(
        target_operating_margin=max(inp.target_operating_margin - 0.13, 0.05),
        terminal_roc=max(inp.terminal_roc - 0.02, inp.terminal_growth + 0.01),
    )
    bear_inp = bear_inp.with_(
        revenue_growth=build_declining_growth(
            inp.base_revenue, bear_rev, inp.terminal_growth, inp.horizon
        )
    )
    bear_vps = dcf.value(bear_inp).value_per_share

    return {
        "company": inp.company,
        "valuation_date": inp.valuation_date,
        "scenarios": [
            {
                "name": "Bull - Upside Case",
                "probability": 0.15,
                "revenue_y10_m": round(bull_rev),
                "target_op_margin": round(bull_inp.target_operating_margin, 3),
                "terminal_roc": round(bull_inp.terminal_roc, 3),
                "value_per_share": round(bull_vps, 0),
                "key_drivers": [
                    "Revenue compounds well above base",
                    "Margins expand structurally",
                    "Return on capital stays elevated",
                ],
            },
            {
                "name": "Base - DCF Central Case",
                "probability": 0.55,
                "revenue_y10_m": round(inp.revenue_path()[-1]),
                "target_op_margin": inp.target_operating_margin,
                "terminal_roc": inp.terminal_roc,
                "value_per_share": round(base.value_per_share, 0),
                "key_drivers": [
                    "Revenue follows base-case path",
                    "Margins converge to target",
                    "Cost of capital normalizes",
                ],
            },
            {
                "name": "Bear - Downside Case",
                "probability": 0.30,
                "revenue_y10_m": round(bear_rev),
                "target_op_margin": round(bear_inp.target_operating_margin, 3),
                "terminal_roc": round(bear_inp.terminal_roc, 3),
                "value_per_share": round(bear_vps, 0),
                "key_drivers": [
                    "Revenue growth disappoints",
                    "Margin compression",
                    "Returns fade toward cost of capital",
                ],
            },
        ],
    }


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Build scenarios.json from DCF assumptions."
    )
    ap.add_argument(
        "--assumptions",
        default=None,
        help="path to assumptions JSON (optional; uses hardcoded MU data if omitted)",
    )
    ap.add_argument(
        "--output",
        default=None,
        help="write JSON to this file instead of stdout",
    )
    args = ap.parse_args(argv)

    if args.assumptions:
        data = _from_assumptions(args.assumptions)
    else:
        data = HARDCODED_MU

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
