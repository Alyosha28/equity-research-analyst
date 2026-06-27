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
    ap.add_argument("--rev-min", type=float, default=150_000.0, help="year-10 revenue low ($M)")
    ap.add_argument("--rev-max", type=float, default=500_000.0, help="year-10 revenue high ($M)")
    ap.add_argument("--rev-steps", type=int, default=8)
    ap.add_argument("--margin-min", type=float, default=0.30)
    ap.add_argument("--margin-max", type=float, default=0.55)
    ap.add_argument("--margin-steps", type=int, default=6)
    ap.add_argument("--json", action="store_true",
                    help="emit the grid as JSON (for charts.py breakeven heatmap)")
    args = ap.parse_args(argv)

    base = load_inputs(args.assumptions)
    revenues = _frange(args.rev_min, args.rev_max, args.rev_steps)
    margins = _frange(args.margin_min, args.margin_max, args.margin_steps)
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
