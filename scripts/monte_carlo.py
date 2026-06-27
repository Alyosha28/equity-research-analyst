"""Monte Carlo simulation over the four value drivers -- Damodaran's way of
turning estimation uncertainty into a value DISTRIBUTION instead of a single
point estimate.

For NVIDIA (June 2023) Damodaran varied:
  * year-10 revenue   : segment distributions; aggregate ranged <$100B to >$600B (mode $267B)
  * target op margin  : triangular, 30% / 40% / 50%
  * sales-to-capital  : 0.65 (historic) / 1.15 (base) / 1.94 (75th pct)
  * cost of capital   : 8.85% (market) / 12.21% (base) / 15% (90th pct)

Each trial re-shapes the revenue path to the sampled year-10 revenue, then runs
the intrinsic DCF. Output: percentiles of value/share + where the price sits.

    python monte_carlo.py ../templates/assumptions.example.json --price 409 --trials 20000
"""

from __future__ import annotations

import argparse
import json
import math
import random

try:
    from valuation_inputs import load_inputs, build_declining_growth
    import dcf_valuation as dcf
except ImportError:
    from scripts.valuation_inputs import load_inputs, build_declining_growth  # type: ignore
    from scripts import dcf_valuation as dcf  # type: ignore


# Distribution specs mirror Damodaran's NVDA simulation.
#   ("triangular", low, mode, high)   -- bounded, for margins / ratios / CoC
#   ("lognormal", median, sigma)      -- positive & right-skewed, for revenue
# Revenue is lognormal centered on the base year-10 revenue ($267B) so the
# distribution's CENTRE matches the base case; sigma=0.33 puts the ~1st/99th
# percentiles near Damodaran's stated <$100B / >$600B extremes.
DEFAULT_DISTRIBUTIONS = {
    "terminal_revenue": ("lognormal", 267_000.0, 0.33),
    "target_operating_margin": ("triangular", 0.30, 0.40, 0.50),
    "sales_to_capital": ("triangular", 0.65, 1.15, 1.94),
    "cost_of_capital_initial": ("triangular", 0.0885, 0.1221, 0.15),
}


# Margin-of-safety buy-band. MoS = clamp(K * coefficient-of-dispersion, FLOOR, CEIL),
# i.e. the discount-to-fair an investor demands WIDENS as the value distribution
# widens (Graham/Buffett "margin of safety", made operational on the simulated
# spread rather than asserted). These are calibration constants -- tune against
# backtested over/under-valuation; kept as named constants so they are easy to move.
MOS_DISPERSION_K = 0.5
MOS_FLOOR = 0.15
MOS_CEIL = 0.50


def _sample(rng, spec):
    kind = spec[0]
    if kind == "triangular":
        _, lo, mode, hi = spec
        return rng.triangular(lo, hi, mode)
    if kind == "lognormal":
        _, median, sigma = spec
        return rng.lognormvariate(math.log(median), sigma)
    raise ValueError(f"unknown distribution type: {kind}")


def _percentile(sorted_vals, q):
    if not sorted_vals:
        return float("nan")
    idx = q * (len(sorted_vals) - 1)
    lo = int(idx)
    frac = idx - lo
    if lo + 1 < len(sorted_vals):
        return sorted_vals[lo] * (1 - frac) + sorted_vals[lo + 1] * frac
    return sorted_vals[lo]


def mos_band(values):
    """Margin-of-safety buy-band derived from the simulated distribution.

    The discount-to-fair an investor should demand widens with the spread of the
    value distribution: MoS = clamp(K * (P90 - P10) / median, FLOOR, CEIL).
    Returns the median (fair), the accumulate-below threshold (fair * (1 - MoS))
    and the rich-above threshold (fair * (1 + MoS))."""
    median = _percentile(values, 0.50)
    p10 = _percentile(values, 0.10)
    p90 = _percentile(values, 0.90)
    dispersion = (p90 - p10) / median if median else float("nan")
    mos = max(MOS_FLOOR, min(MOS_CEIL, MOS_DISPERSION_K * dispersion))
    return {
        "median": median,
        "dispersion": dispersion,
        "mos": mos,
        "buy_below": median * (1.0 - mos),
        "rich_above": median * (1.0 + mos),
    }


def json_summary(values, price=None) -> dict:
    """Machine-readable summary for charts.py / programmatic consumers."""
    n = len(values)
    pcts = {str(int(q * 100)): _percentile(values, q)
            for q in (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)}
    out = {
        "trials": n,
        "mean": sum(values) / n,
        "median": _percentile(values, 0.50),
        "min": values[0],
        "max": values[-1],
        "percentiles": pcts,
        "mos_band": mos_band(values),
        "values": values,
    }
    if price is not None:
        out["price"] = price
        out["price_percentile"] = sum(1 for v in values if v <= price) / n
        out["p_value_ge_price"] = sum(1 for v in values if v >= price) / n
    return out


def simulate(base_inp, trials=20000, seed=42, distributions=None):
    rng = random.Random(seed)
    d = {**DEFAULT_DISTRIBUTIONS, **(distributions or {})}
    n = base_inp.horizon
    values, skipped = [], 0
    for _ in range(trials):
        rev_y10 = _sample(rng, d["terminal_revenue"])
        margin = _sample(rng, d["target_operating_margin"])
        s2c = _sample(rng, d["sales_to_capital"])
        coc = _sample(rng, d["cost_of_capital_initial"])

        growth = build_declining_growth(base_inp.base_revenue, rev_y10,
                                         base_inp.terminal_growth, n)
        # Keep terminal CoC strictly above terminal growth so the TV denominator
        # stays positive even when a very low initial CoC is sampled.
        coc_term = max(base_inp.terminal_growth + 0.005,
                       min(base_inp.cost_of_capital_terminal, coc))
        try:
            trial = base_inp.with_(
                revenue_growth=growth,
                target_operating_margin=margin,
                sales_to_capital=s2c,
                cost_of_capital_initial=coc,
                cost_of_capital_terminal=coc_term,
            )
            values.append(dcf.value(trial).value_per_share)
        except ValueError:
            skipped += 1                          # invalid draw; drop it, don't crash
    values.sort()
    return values, skipped


def report(values, price=None) -> str:
    n = len(values)
    mean = sum(values) / n
    median = _percentile(values, 0.5)
    lines = [
        f"Monte Carlo: {n:,} trials",
        "-" * 48,
        f"Mean value/share:   {mean:>10.2f}",
        f"Median value/share: {median:>10.2f}",
        f"Min / Max:          {values[0]:>10.2f} / {values[-1]:.2f}",
        "",
        "Percentiles of intrinsic value/share:",
    ]
    for q in (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99):
        lines.append(f"  {int(q*100):>3d}th: {_percentile(values, q):>10.2f}")
    band = mos_band(values)
    lines += [
        "",
        f"Margin-of-safety buy-band  (MoS {band['mos']:.0%}, widens with dispersion):",
        f"  Accumulate below: {band['buy_below']:>10.2f}",
        f"  Fair (median):    {band['median']:>10.2f}",
        f"  Rich above:       {band['rich_above']:>10.2f}",
    ]
    if price is not None:
        above = sum(1 for v in values if v >= price) / n
        pctile = sum(1 for v in values if v <= price) / n
        lines += [
            "",
            f"Current price:                 {price:>10.2f}",
            f"P(intrinsic value >= price):   {above:>9.1%}",
            f"Price sits at the {pctile:.0%} percentile of the value distribution",
            "  -> " + ("price is in the optimistic tail (likely OVERVALUED)"
                       if pctile >= 0.80 else
                       "price is within the plausible value range"),
        ]
    return "\n".join(lines)


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Monte Carlo intrinsic-value simulation.")
    ap.add_argument("assumptions", help="path to assumptions JSON")
    ap.add_argument("--price", type=float, default=None, help="current market price")
    ap.add_argument("--trials", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON (percentiles + MoS band + raw "
                         "values) instead of the text report -- consumed by charts.py")
    args = ap.parse_args(argv)
    base = load_inputs(args.assumptions)
    values, skipped = simulate(base, trials=args.trials, seed=args.seed)
    if args.json:
        print(json.dumps(json_summary(values, price=args.price), indent=2))
        return 0
    print(report(values, price=args.price))
    if skipped:
        print(f"\nNote: {skipped:,} of {args.trials:,} trials were dropped as "
              f"economically invalid (terminal CoC <= terminal growth).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
