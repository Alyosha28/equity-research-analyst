"""Reverse DCF / expectations investing (Mauboussin style).

Instead of asking "what is the company worth?", ask "what does today's PRICE
imply the market believes?" -- then judge whether those implied expectations are
plausible. Given a price, solve for the single driver that makes intrinsic value
== price, holding the others at their base-case values.

    python reverse_dcf.py ../templates/assumptions.example.json --price 409 --solve-for terminal_revenue
    python reverse_dcf.py ../templates/assumptions.example.json --price 409 --solve-for target_operating_margin
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


SOLVABLE = ("terminal_revenue", "target_operating_margin",
            "sales_to_capital", "cost_of_capital_initial")


def _value_given(base_inp, variable, x) -> float:
    if variable == "terminal_revenue":
        growth = build_declining_growth(base_inp.base_revenue, x,
                                        base_inp.terminal_growth, base_inp.horizon)
        inp = base_inp.with_(revenue_growth=growth)
    elif variable == "cost_of_capital_initial":
        inp = base_inp.with_(cost_of_capital_initial=x,
                             cost_of_capital_terminal=min(base_inp.cost_of_capital_terminal, x))
    else:
        inp = base_inp.with_(**{variable: x})
    return dcf.value(inp).value_per_share


def solve(base_inp, price, variable, lo, hi, monotonic_up=True):
    """Bisection for the value of `variable` that makes intrinsic value == price.
    `monotonic_up`: value rises as the variable rises (True for revenue/margin/
    sales-to-capital, False for cost of capital). If `price` is not bracketed by
    [lo, hi], return the endpoint nearest to price -- the caller detects this
    'no solution in range' case by comparing the achieved value to the price."""
    v_lo = _value_given(base_inp, variable, lo)
    v_hi = _value_given(base_inp, variable, hi)
    if (v_lo - price) * (v_hi - price) > 0:        # price outside achievable range
        return lo if abs(v_lo - price) < abs(v_hi - price) else hi
    for _ in range(200):
        mid = (lo + hi) / 2
        v = _value_given(base_inp, variable, mid)
        higher = (v < price) == monotonic_up
        lo, hi = (mid, hi) if higher else (lo, mid)
    return (lo + hi) / 2


def _bounds(variable, base_inp):
    """Return (lo, hi, monotonic_up) for each solvable variable. monotonic_up
    means intrinsic value rises as the variable rises."""
    return {
        "terminal_revenue": (base_inp.base_revenue, 3_000_000.0, True),
        "target_operating_margin": (0.01, 0.95, True),
        "sales_to_capital": (0.30, 5.0, True),     # more $rev per $capital -> less reinvest -> higher value
        "cost_of_capital_initial": (base_inp.cost_of_capital_terminal, 0.40, False),
    }[variable]


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Reverse DCF: solve for price-implied expectations.")
    ap.add_argument("assumptions")
    ap.add_argument("--price", type=float, required=True)
    ap.add_argument("--solve-for", choices=SOLVABLE, default="terminal_revenue")
    ap.add_argument("--json", action="store_true",
                    help="emit the implied-expectation result as JSON (for charts.py)")
    args = ap.parse_args(argv)

    base = load_inputs(args.assumptions)
    base_value = dcf.value(base).value_per_share

    lo, hi, monotonic_up = _bounds(args.solve_for, base)
    implied = solve(base, args.price, args.solve_for, lo, hi, monotonic_up=monotonic_up)
    achieved = _value_given(base, args.solve_for, implied)
    converged = abs(achieved - args.price) <= 0.01 * args.price

    if args.json:
        print(json.dumps({
            "company": base.company,
            "solve_for": args.solve_for,
            "price": args.price,
            "base_value": base_value,
            "implied": implied,
            "achieved": achieved,
            "converged": converged,
        }, indent=2))
        return 0

    print(f"Reverse DCF for {base.company}")
    print("-" * 56)
    print(f"Base-case intrinsic value/share: {base_value:>10.2f}")
    print(f"Market price:                    {args.price:>10.2f}")
    print(f"Solving for: {args.solve_for}")
    print("-" * 56)
    if not converged:
        # Bisection hit a bound: no value of this driver alone reaches the price.
        direction = "below" if achieved < args.price else "above"
        print(f"NO SOLUTION within plausible bounds for '{args.solve_for}'.")
        print(f"  Even at the extreme ({args.solve_for} = {implied:.4g}), intrinsic value")
        print(f"  tops out at {achieved:.2f}, still {direction} the {args.price:.0f} price.")
        print("  => the price CANNOT be justified by this driver alone; it needs a")
        print("     joint move across several drivers (see breakeven.py).")
        print("-" * 56)
        return 0
    if args.solve_for == "terminal_revenue":
        cagr = (implied / base.base_revenue) ** (1 / base.horizon) - 1
        base_y10 = base.revenue_path()[-1]
        print(f"Price-implied year-{base.horizon} revenue: {implied:>12,.0f} $M "
              f"({implied/1000:,.0f}B)")
        print(f"  vs base-case year-{base.horizon} revenue: {base_y10:>9,.0f} $M "
              f"({base_y10/1000:,.0f}B)")
        print(f"Implied {base.horizon}-yr revenue CAGR:  {cagr:>10.1%}")
        print(f"Implied uplift over base case:   {implied/base_y10 - 1:>10.1%}")
    elif args.solve_for == "target_operating_margin":
        print(f"Price-implied target operating margin: {implied:>8.1%}")
        print(f"  vs base-case target margin:          {base.target_operating_margin:>8.1%}")
    elif args.solve_for == "sales_to_capital":
        print(f"Price-implied sales-to-capital: {implied:>10.2f}")
        print(f"  vs base case:                 {base.sales_to_capital:>10.2f}")
    else:
        print(f"Price-implied initial cost of capital: {implied:>8.2%}")
        print(f"  vs base case:                        {base.cost_of_capital_initial:>8.2%}")
    print("-" * 56)
    print("Judge: are these implied expectations plausible vs history, peers,")
    print("and the addressable market? If not, the price embeds too much.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
