"""Monte Carlo simulation over the five core value drivers -- Damodaran's way of
turning estimation uncertainty into a value DISTRIBUTION instead of a single
point estimate.

For NVIDIA (June 2023) Damodaran varied:
  * year-10 revenue   : segment distributions; aggregate ranged <$100B to >$600B (mode $267B)
  * target op margin  : triangular, 30% / 40% / 50%
  * sales-to-capital  : 0.65 (historic) / 1.15 (base) / 1.94 (75th pct)
  * cost of capital   : 8.85% (market) / 12.21% (base) / 15% (90th pct)

This implementation varies all FIVE core value drivers (terminal revenue, target
operating margin, sales-to-capital, cost of capital, terminal growth).  Terminal
growth directly affects (a) the shape of the declining-growth revenue path
(steepness of deceleration), (b) the terminal-value denominator (CoC -- g), and
(c) the reinvestment rate implied by g / terminal_roc. For terminal-heavy
valuations (60-85% of value) these effects compound materially and omitting them
understates the true value distribution.

By default ALL FIVE driver distributions are auto-derived from the base case's own
values (Damodaran's "simulate around the analyst's base estimate" discipline) so
the value distribution is centred on the company being valued, not on NVDA.
Callers may override any distribution explicitly via the ``distributions``
keyword argument; ``DEFAULT_DISTRIBUTIONS`` serves only as a last-resort
fallback when auto-derivation cannot produce a valid centre (e.g. negative
base margin, zero revenue).

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


# Distribution spec format:
#   ("triangular", low, mode, high)   -- bounded, for margins / ratios / CoC
#   ("lognormal", median, sigma)      -- positive & right-skewed, for revenue
#
# The values below are NVDA-specific LAST-RESORT FALLBACKS.  `simulate()` will
# auto-derive target_operating_margin, sales_to_capital, terminal_growth,
# terminal_revenue, and cost_of_capital_initial from the base case whenever the
# caller does not supply an explicit override.  The DEFAULT_DISTRIBUTIONS dict
# serves only as a safety net when auto-derivation cannot produce a positive
# centre (e.g. negative base margin).  In normal usage the NVDA numbers are
# never reached; they exist to prevent a crash, not to centre the distribution.
DEFAULT_DISTRIBUTIONS = {
    "terminal_revenue": ("lognormal", 267_000.0, 0.33),
    "target_operating_margin": ("triangular", 0.30, 0.40, 0.50),
    "sales_to_capital": ("triangular", 0.65, 1.15, 1.94),
    "cost_of_capital_initial": ("triangular", 0.0885, 0.1221, 0.15),
    "terminal_growth": ("triangular", 0.025, 0.0385, 0.045),
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
    merge = distributions or {}
    d = {**DEFAULT_DISTRIBUTIONS, **merge}
    n = base_inp.horizon

    # Auto-derive distributions that were NOT explicitly overridden by the caller.
    # DEFAULT_DISTRIBUTIONS are NVDA-specific placeholders; for any other company
    # they produce a value distribution centred on the wrong company's economics.
    # When the caller doesn't supply their own spec for a driver, we centre the
    # distribution on the base case's own values (Damodaran's "simulate around the
    # analyst's base-case estimate" discipline).
    #
    # terminal_revenue: lognormal centred on the base case's year-N revenue so the
    #   distribution median equals the analyst's best estimate.  sigma=0.33 is
    #   preserved from Damodaran's original (puts ~1st/99th %iles near <$100B/>$600B
    #   for NVDA; serves as a reasonable default for 10-yr forecast dispersion).
    if "terminal_revenue" not in merge:
        base_yN_rev = base_inp.revenue_path()[-1]
        # Ensure positive (the base case can't have non-positive year-N revenue)
        if base_yN_rev > 0:
            d["terminal_revenue"] = ("lognormal", base_yN_rev, 0.33)
    # cost_of_capital_initial: triangular centred on the base case's own CoC with
    #   width ratios matched to Damodaran's NVDA spread (low ~0.72x mode, high ~1.23x
    #   mode).  Clamped to [0.02, 0.50] to keep the distribution economically
    #   plausible regardless of the base rate.
    if "cost_of_capital_initial" not in merge:
        base_coc = base_inp.cost_of_capital_initial
        lo = max(0.02, base_coc * 0.72)
        hi = min(0.50, base_coc * 1.23)
        d["cost_of_capital_initial"] = ("triangular", lo, base_coc, hi)
    # target_operating_margin: triangular centred on the base case's own target
    #   margin with a +/-50% spread (lo ~0.50x mode, hi ~1.50x mode), clamped to
    #   [0.005, 0.95].  Without this the Monte Carlo would sample from NVDA's
    #   30-50% margin range for EVERY company -- a 20%-margin young-growth firm
    #   gets a ~2.5x inflated value distribution, a 3%-margin legacy retailer
    #   gets a ~13x inflated median.
    if "target_operating_margin" not in merge:
        base_margin = base_inp.target_operating_margin
        if base_margin > 0:
            lo = max(0.005, base_margin * 0.50)
            hi = min(0.95, base_margin * 1.50)
            d["target_operating_margin"] = ("triangular", lo, base_margin, hi)
    # sales_to_capital: triangular centred on the base case's own S2C with a
    #   +/-50% spread (lo ~0.50x mode, hi ~1.67x mode), clamped to [0.10, 5.0].
    #   Without this a 0.55 S2C capital-intensive cyclical (Freeport) samples
    #   from NVDA's 0.65-1.94 range, overstating reinvestment efficiency and
    #   therefore value.
    if "sales_to_capital" not in merge:
        base_s2c = base_inp.sales_to_capital
        if base_s2c > 0:
            lo = max(0.10, base_s2c * 0.50)
            hi = min(5.0, base_s2c * 1.67)
            d["sales_to_capital"] = ("triangular", lo, base_s2c, hi)
    # terminal_growth: triangular centred on the base case's own terminal growth
    #   with a narrower spread (lo ~0.65x mode, hi ~1.17x mode) because the
    #   risk-free rate bounds this driver tightly.  Clamped to [0.005, 0.06].
    if "terminal_growth" not in merge:
        base_g = base_inp.terminal_growth
        if base_g > 0:
            lo = max(0.005, base_g * 0.65)
            hi = min(0.06, base_g * 1.17)
            d["terminal_growth"] = ("triangular", lo, base_g, hi)

    values, skipped = [], 0
    for _ in range(trials):
        rev_y10 = _sample(rng, d["terminal_revenue"])
        margin = _sample(rng, d["target_operating_margin"])
        s2c = _sample(rng, d["sales_to_capital"])
        coc = _sample(rng, d["cost_of_capital_initial"])

        # Terminal growth (g_term): sampled and clamped to ensure
        # 0 < g_term < terminal CoC -- 0.005 (the DCF requires CoC > g).
        # Also clamped not to exceed terminal_roc -- 0.005 (otherwise the
        # implied reinvestment rate g/ROC >= 1 and terminal FCFF <= 0).
        # Callers may opt OUT of terminal_growth variation by passing
        # {"terminal_growth": None} in the distributions override.
        if d.get("terminal_growth") is not None:
            g_term = _sample(rng, d["terminal_growth"])
            g_term = max(0.005, min(g_term,
                                    base_inp.cost_of_capital_terminal - 0.005,
                                    base_inp.terminal_roc - 0.005))
        else:
            g_term = base_inp.terminal_growth

        growth = build_declining_growth(base_inp.base_revenue, rev_y10,
                                         g_term, n)
        # Terminal CoC is the MATURE / market-average rate to which all
        # companies converge -- it is independent of the initial CoC draw.
        # The initial CoC only affects early-year discounting through the
        # glide path (glide_start_year -> glide_end_year).  Making coc_term
        # float with coc creates asymmetric bias: low-CoC draws get amplified
        # terminal values (smaller denominator), but high-CoC draws are capped
        # at the base terminal CoC -- skewing the distribution rightward.
        # The defensive floor (g_term + 5bp) is a no-op in almost all trials
        # because g_term is already clamped below terminal CoC - 5bp, but it
        # stays as a safety net in case a caller overrides the clamping.
        coc_term = max(g_term + 0.005,
                       base_inp.cost_of_capital_terminal)
        try:
            trial = base_inp.with_(
                revenue_growth=growth,
                target_operating_margin=margin,
                sales_to_capital=s2c,
                cost_of_capital_initial=coc,
                cost_of_capital_terminal=coc_term,
                terminal_growth=g_term,
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
