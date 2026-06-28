"""Breakeven / "what has to be true" analysis.

Damodaran's two-variable table: vary year-10 revenue (growth) against the target
operating margin and read off intrinsic value/share in each cell. It answers
"what combination of revenue and margin would JUSTIFY today's price?" -- usually
revealing that the price requires a daunting combination of both.

    python breakeven.py ../templates/assumptions.example.json --price 409
"""

from __future__ import annotations

import argparse
import json

try:
    from valuation_inputs import load_inputs, build_declining_growth
    import dcf_valuation as dcf
except ImportError:
    from scripts.valuation_inputs import load_inputs, build_declining_growth  # type: ignore
    from scripts import dcf_valuation as dcf  # type: ignore


def grid(base_inp, revenues, margins):
    """Return rows of (revenue, [value/share per margin])."""
    n = base_inp.horizon
    out = []
    for rev in revenues:
        growth = build_declining_growth(base_inp.base_revenue, rev,
                                        base_inp.terminal_growth, n)
        row = []
        for m in margins:
            trial = base_inp.with_(revenue_growth=growth, target_operating_margin=m)
            row.append(dcf.value(trial).value_per_share)
        out.append((rev, row))
    return out


def render(rows, margins, price=None) -> str:
    header = "Year10 Rev \\ Margin |" + "".join(f"{m:>9.0%}" for m in margins)
    lines = ["Breakeven table -- intrinsic value/share", "=" * len(header), header,
             "-" * len(header)]
    for rev, vals in rows:
        cells = []
        for v in vals:
            mark = "*" if (price is not None and v >= price) else " "
            cells.append(f"{v:>8.0f}{mark}")
        lines.append(f"{rev/1000:>16,.0f}B |" + "".join(cells))
    if price is not None:
        lines += ["-" * len(header),
                  f"* = intrinsic value >= price ({price:.0f}); cells WITHOUT a star are "
                  f"where the stock is overvalued."]
    return "\n".join(lines)


def _frange(lo, hi, steps):
    if steps == 1:
        return [lo]
    return [lo + (hi - lo) * i / (steps - 1) for i in range(steps)]


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Two-variable breakeven table.")
    ap.add_argument("assumptions")
    ap.add_argument("--price", type=float, default=None)
    ap.add_argument("--rev-min", type=float, default=None,
                    help="year-10 revenue low ($M); auto-derived from base case if omitted")
    ap.add_argument("--rev-max", type=float, default=None,
                    help="year-10 revenue high ($M); auto-derived from base case if omitted")
    ap.add_argument("--rev-steps", type=int, default=8)
    ap.add_argument("--margin-min", type=float, default=None,
                    help="target operating margin low; auto-derived from base case if omitted")
    ap.add_argument("--margin-max", type=float, default=None,
                    help="target operating margin high; auto-derived from base case if omitted")
    ap.add_argument("--margin-steps", type=int, default=6)
    ap.add_argument("--json", action="store_true",
                    help="emit the grid as JSON (for charts.py breakeven heatmap)")
    args = ap.parse_args(argv)

    base = load_inputs(args.assumptions)
    base_yN = base.revenue_path()[-1]

    # Auto-derive ranges centred on the base case's own numbers (same discipline as
    # monte_carlo.py's auto-derived distributions -- Damodaran's "simulate around the
    # analyst's base estimate"). The previous hardcoded defaults ($150B-$500B revenue,
    # 30-55% margin) were NVDA-specific and produced irrelevant tables for every other
    # company.
    rev_min = args.rev_min if args.rev_min is not None else base_yN * 0.30
    rev_max = args.rev_max if args.rev_max is not None else base_yN * 3.00
    margin_min = args.margin_min if args.margin_min is not None else max(0.01, base.target_operating_margin * 0.50)
    margin_max = args.margin_max if args.margin_max is not None else min(0.95, base.target_operating_margin * 1.50)

    revenues = _frange(rev_min, rev_max, args.rev_steps)
    margins = _frange(margin_min, margin_max, args.margin_steps)
    rows = grid(base, revenues, margins)
    if args.json:
        print(json.dumps({
            "company": base.company,
            "price": args.price,
            "margins": list(margins),
            "revenues": [rev for rev, _ in rows],
            "grid": [vals for _, vals in rows],   # grid[i][j] = value at revenue i, margin j
        }, indent=2))
        return 0
    print(render(rows, margins, price=args.price))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
