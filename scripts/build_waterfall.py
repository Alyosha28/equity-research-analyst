"""Build waterfall.json -- bridging from DCF base value to the market price.

Shows the incremental contributions that lift intrinsic value from the base DCF
to the observed market price, making visible what the market is implicitly pricing
in (higher terminal revenue, higher margins, lower discount rate, and any residual
speculative premium).

    python build_waterfall.py
    python build_waterfall.py --assumptions ../templates/assumptions.example.json --price 1134
    python build_waterfall.py --output waterfall.json
"""

from __future__ import annotations

import argparse
import json
import sys

HARDCODED_MU = {
    "company": "MU",
    "base_value": 299,
    "price": 1134,
    "steps": [
        {
            "label": "DCF Base Value",
            "value": 299,
            "delta": 0,
            "is_positive": True,
        },
        {
            "label": "Higher Terminal Revenue (+$400B)",
            "value": 520,
            "delta": 221,
            "is_positive": True,
        },
        {
            "label": "Higher Operating Margin (+15pp)",
            "value": 750,
            "delta": 230,
            "is_positive": True,
        },
        {
            "label": "Lower Cost of Capital (-2pp)",
            "value": 880,
            "delta": 130,
            "is_positive": True,
        },
        {
            "label": "Peak Cycle Extrapolation",
            "value": 1134,
            "delta": 254,
            "is_positive": True,
        },
        {
            "label": "Implied Speculative Premium",
            "value": 1134,
            "delta": 0,
            "is_positive": False,
        },
    ],
}


def _from_assumptions(path: str, price: float) -> dict:
    """Load assumptions, run the base DCF, then programmatically build waterfall
    steps by incrementally perturbing each value driver."""
    try:
        from valuation_inputs import load_inputs, build_declining_growth
        import dcf_valuation as dcf
    except ImportError:
        from scripts.valuation_inputs import load_inputs, build_declining_growth  # type: ignore
        from scripts import dcf_valuation as dcf  # type: ignore

    inp = load_inputs(path)
    base_result = dcf.value(inp)
    base_vps = base_result.value_per_share

    steps = [
        {"label": "DCF Base Value", "value": round(base_vps, 0), "delta": 0,
         "is_positive": True},
    ]

    # Step 1: raise terminal revenue 50%
    rev0 = inp.revenue_path()[-1]
    rev1 = rev0 * 1.5
    g1 = build_declining_growth(inp.base_revenue, rev1,
                                inp.terminal_growth, inp.horizon)
    v1 = dcf.value(inp.with_(revenue_growth=g1)).value_per_share
    steps.append({
        "label": f"Higher Terminal Revenue (+${rev1 - rev0:,.0f}M)",
        "value": round(v1, 0),
        "delta": round(v1 - base_vps, 0),
        "is_positive": True,
    })

    # Step 2: raise target margin +10pp
    m2 = min(inp.target_operating_margin + 0.10, 0.50)
    inp2 = inp.with_(revenue_growth=g1, target_operating_margin=m2)
    v2 = dcf.value(inp2).value_per_share
    steps.append({
        "label": f"Higher Operating Margin (+{m2 - inp.target_operating_margin:.0%})",
        "value": round(v2, 0),
        "delta": round(v2 - v1, 0),
        "is_positive": True,
    })

    # Step 3: lower cost of capital 2pp
    coc3 = max(inp.cost_of_capital_initial - 0.02,
               inp.terminal_growth + 0.005)
    inp3 = inp2.with_(cost_of_capital_initial=coc3,
                       cost_of_capital_terminal=min(inp.cost_of_capital_terminal, coc3))
    v3 = dcf.value(inp3).value_per_share
    steps.append({
        "label": f"Lower Cost of Capital (-{inp.cost_of_capital_initial - coc3:.0%})",
        "value": round(v3, 0),
        "delta": round(v3 - v2, 0),
        "is_positive": True,
    })

    # Step 4: gap to price (peak-cycle extrapolation / speculative)
    if price > v3:
        gap = round(price - v3, 0)
        steps.append({
            "label": "Peak Cycle / Speculative Premium",
            "value": round(price, 0),
            "delta": gap,
            "is_positive": True,
        })
    steps.append({
        "label": "Implied Speculative Premium",
        "value": round(price, 0),
        "delta": 0,
        "is_positive": False,
    })

    return {
        "company": inp.company,
        "base_value": round(base_vps, 0),
        "price": price,
        "steps": steps,
    }


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Build waterfall.json -- DCF-to-price bridge."
    )
    ap.add_argument(
        "--assumptions",
        default=None,
        help="path to assumptions JSON (optional; uses hardcoded MU data if omitted)",
    )
    ap.add_argument(
        "--price",
        type=float,
        default=None,
        help="current market price (required with --assumptions)",
    )
    ap.add_argument(
        "--output",
        default=None,
        help="write JSON to this file instead of stdout",
    )
    args = ap.parse_args(argv)

    if args.assumptions:
        if args.price is None:
            print("ERROR: --price is required when --assumptions is given.",
                  file=sys.stderr)
            return 1
        data = _from_assumptions(args.assumptions, args.price)
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
