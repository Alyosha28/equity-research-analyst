"""Stress-test a financials valuation across discrete scenarios.

The standard Monte Carlo (``monte_carlo.py``) samples value drivers as if they were
independent. For financials (banks, insurers) that assumption is *wrong* — the
drivers are regime-dependent:

- High NIM (rising rates) cannot co-exist with high credit losses (recession) in
  the same regime. NIM widens when the Fed hikes; credit losses peak when the
  Fed is already cutting. Both spiking simultaneously is a contradiction.
- Cost of equity rises in stress regimes alongside credit losses, not independently.
- Payout ratios get cut by regulators in credit crunches.

This script replaces random-sampling Monte Carlo with **grid-based scenario
analysis** — a small number of discrete, internally-consistent scenarios — and
produces a scenario-weighted margin-of-safety buy-band.

Usage::

    cd scripts
    python financial_stress.py ../templates/financials.example.json
    python financial_stress.py ../templates/financials.example.json --output stress.json

Output ``stress.json`` is compatible with ``charts.py`` (``scenarios`` and
``football`` chart kinds) and contains scenario-weighted statistics.

Scenarios (hardcoded; extend by adding entries to ``SCENARIO_SPECS``):
1. Base (50%)          — analyst's base assumptions, through-cycle normal
2. Optimistic (15%)    — benign credit, expanding NIM, lower CoE
3. Pessimistic (15%)   — mild recession, NIM compression, higher CoE
4. Credit Crunch (10%) — severe credit cycle, capital adequacy tested
5. Rate Shock (10%)    — rapid rate-hike cycle, NIM widens but terminal growth
                          compresses and CoE rises

Implausibility guard: any scenario where both NIM and credit losses rise strongly
at the same time is flagged and excluded from the weighted distribution.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

# Import the financial valuation engine from the same directory.
try:
    from financial_valuation import (
        FinancialInputs,
        FinancialResult,
        load_inputs,
        value,
    )
except ImportError:
    from scripts.financial_valuation import (  # type: ignore[no-redef]
        FinancialInputs,
        FinancialResult,
        load_inputs,
        value,
    )


# ---------------------------------------------------------------------------
# Scenario definitions — each entry specifies additive adjustments to the
# base financial assumptions.
# ---------------------------------------------------------------------------

# Thresholds for implausible regime combinations.
IMPLAUSIBLE_NIM_THRESHOLD = 0.010    # NIM contribution to ROE > +100 bp
IMPLAUSIBLE_CREDIT_THRESHOLD = 0.020  # credit-loss drag on ROE > +200 bp


@dataclass(frozen=True)
class ScenarioSpec:
    """A single stress scenario with per-driver deltas and a probability weight.

    ``*_delta`` fields are **additive percentage-point adjustments to ROE**
    (expressed as decimals; 0.01 = 100 bp).  Positive ``credit_loss_delta``
    means *more* credit losses, i.e. a drag on ROE.  Positive
    ``cost_ratio_delta`` means a *worse* cost/income ratio, i.e. a drag on ROE.

    ``roe_convergence_shift`` adds/subtracts years to the convergence horizon:
    positive = slower convergence (more stress), negative = faster.
    """

    name: str
    probability: float

    nim_delta: float = 0.0
    fee_delta: float = 0.0
    credit_loss_delta: float = 0.0
    cost_ratio_delta: float = 0.0

    coe_delta: float = 0.0
    terminal_growth_delta: float = 0.0
    terminal_roe_delta: float = 0.0
    payout_ratio_delta: float = 0.0
    roe_convergence_shift: int = 0

    failure_probability_override: Optional[float] = None
    failure_value_per_share_override: Optional[float] = None

    notes: str = ""


# ---------------------------------------------------------------------------
# Hardcoded scenario library — calibrated to span the economically-meaningful
# outcome space for a large bank.  Tune these for the specific company under
# research; the structure stays the same.
# ---------------------------------------------------------------------------

SCENARIO_SPECS: list[ScenarioSpec] = [
    ScenarioSpec(
        name="Base",
        probability=0.50,
        nim_delta=0.0,
        fee_delta=0.0,
        credit_loss_delta=0.0,
        cost_ratio_delta=0.0,
        coe_delta=0.0,
        terminal_growth_delta=0.0,
        terminal_roe_delta=0.0,
        payout_ratio_delta=0.0,
        roe_convergence_shift=0,
        failure_probability_override=None,
        notes="Analyst base case — through-cycle normal, no regime tilt.",
    ),
    ScenarioSpec(
        name="Optimistic",
        probability=0.15,
        nim_delta=+0.015,
        fee_delta=+0.005,
        credit_loss_delta=-0.005,
        cost_ratio_delta=-0.005,
        coe_delta=-0.01,
        terminal_growth_delta=+0.005,
        terminal_roe_delta=+0.01,
        payout_ratio_delta=+0.05,
        roe_convergence_shift=-1,
        failure_probability_override=0.005,
        notes="Goldilocks: above-trend GDP, steep yield curve, low defaults.",
    ),
    ScenarioSpec(
        name="Pessimistic",
        probability=0.15,
        nim_delta=-0.005,
        fee_delta=-0.01,
        credit_loss_delta=+0.01,
        cost_ratio_delta=+0.01,
        coe_delta=+0.01,
        terminal_growth_delta=-0.005,
        terminal_roe_delta=-0.01,
        payout_ratio_delta=-0.05,
        roe_convergence_shift=+1,
        failure_probability_override=0.05,
        notes="Mild recession: GDP contracts 1-2 quarters, unemployment ticks up.",
    ),
    ScenarioSpec(
        name="Credit Crunch",
        probability=0.10,
        nim_delta=-0.02,
        fee_delta=-0.015,
        credit_loss_delta=+0.04,
        cost_ratio_delta=+0.015,
        coe_delta=+0.025,
        terminal_growth_delta=-0.01,
        terminal_roe_delta=-0.02,
        payout_ratio_delta=-0.20,
        roe_convergence_shift=+3,
        failure_probability_override=0.10,
        failure_value_per_share_override=None,
        notes=(
            "Severe credit cycle: NPLs spike, provisions overwhelm pre-provision "
            "profit, CET1 tested. NIM compresses because the Fed is cutting "
            "(NOT hiking). This is the consistent regime pair."
        ),
    ),
    ScenarioSpec(
        name="Rate Shock",
        probability=0.10,
        nim_delta=+0.015,
        fee_delta=-0.005,
        credit_loss_delta=+0.005,
        cost_ratio_delta=0.0,
        coe_delta=+0.015,
        terminal_growth_delta=-0.005,
        terminal_roe_delta=+0.005,
        payout_ratio_delta=-0.05,
        roe_convergence_shift=0,
        failure_probability_override=0.03,
        notes=(
            "Rapid rate-hiking cycle: NIM benefit from asset repricing, but "
            "HTM bond losses stress tangible book, CoE rises, and terminal "
            "growth compresses. Credit losses only modestly elevated — if "
            "credit losses were ALSO severe this combination would be "
            "implausible (the Fed hiking into a credit crisis)."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Implausibility check
# ---------------------------------------------------------------------------

def _check_implausible(spec: ScenarioSpec) -> list[str]:
    """Return warnings if a scenario combines contradictory regime assumptions.

    The principal contradiction: high NIM (rising-rate environment) cannot
    co-exist with severe credit losses (recession/relief-rate environment)
    because the macro regime that produces one is the opposite of the regime
    that produces the other.
    """
    warnings: list[str] = []
    if (
        spec.nim_delta >= IMPLAUSIBLE_NIM_THRESHOLD
        and spec.credit_loss_delta >= IMPLAUSIBLE_CREDIT_THRESHOLD
    ):
        warnings.append(
            f"IMPLAUSIBLE: NIM delta +{spec.nim_delta:.1%} and credit-loss "
            f"delta +{spec.credit_loss_delta:.1%} cannot coexist — rising "
            f"rates (high NIM) and severe credit losses imply contradictory "
            f"macro regimes. Adjust NIM down or credit losses down."
        )
    return warnings


# ---------------------------------------------------------------------------
# Scenario application — maps a ScenarioSpec onto a FinancialInputs instance
# ---------------------------------------------------------------------------

def _apply_scenario(
    base_inp: FinancialInputs,
    spec: ScenarioSpec,
) -> FinancialInputs:
    """Create a modified FinancialInputs for *spec* applied to *base_inp*.

    The ROE adjustment is computed as the sum of the four revenue/cost driver
    deltas::

        delta_ROE = nim_delta + fee_delta - credit_loss_delta - cost_ratio_delta

    All deltas are in decimal form (0.01 = 1 percentage point).
    """
    roe_delta = (
        spec.nim_delta
        + spec.fee_delta
        - spec.credit_loss_delta
        - spec.cost_ratio_delta
    )

    base_roe = max(0.001, base_inp.base_roe + roe_delta)
    target_roe = max(0.001, base_inp.target_roe + roe_delta)
    terminal_roe = max(
        0.001,
        base_inp.terminal_roe + spec.terminal_roe_delta,
    )

    coe_initial = max(0.02, base_inp.cost_of_equity_initial + spec.coe_delta)
    coe_terminal = max(0.02, base_inp.cost_of_equity_terminal + spec.coe_delta)

    # Ensure CoE > terminal growth plus a margin.
    tg_raw = base_inp.terminal_growth + spec.terminal_growth_delta
    terminal_growth = max(0.005, min(tg_raw, coe_terminal - 0.005,
                                     terminal_roe - 0.005))

    payout = max(0.0, min(1.0, base_inp.payout_ratio + spec.payout_ratio_delta))

    roe_conv = max(1, base_inp.roe_convergence_year + spec.roe_convergence_shift)

    # CoE glide years shift in proportion, bounded.
    coe_glide_start = max(1, base_inp.coe_glide_start_year
                          + spec.roe_convergence_shift)
    coe_glide_end = max(coe_glide_start + 1,
                        base_inp.coe_glide_end_year
                        + spec.roe_convergence_shift)

    fp = spec.failure_probability_override
    if fp is None:
        fp = base_inp.failure_probability
    fv = spec.failure_value_per_share_override
    if fv is None:
        fv = base_inp.failure_value_per_share

    return FinancialInputs(
        company=f"{base_inp.company} [{spec.name}]",
        valuation_date=base_inp.valuation_date,
        book_value_equity=base_inp.book_value_equity,
        shares_outstanding=base_inp.shares_outstanding,
        base_roe=base_roe,
        target_roe=target_roe,
        roe_convergence_year=roe_conv,
        payout_ratio=payout,
        cost_of_equity_initial=coe_initial,
        cost_of_equity_terminal=coe_terminal,
        coe_glide_start_year=coe_glide_start,
        coe_glide_end_year=coe_glide_end,
        horizon=base_inp.horizon,
        terminal_growth=terminal_growth,
        terminal_roe=terminal_roe,
        failure_probability=fp,
        failure_value_per_share=fv,
        price=base_inp.price,
    )


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StressResult:
    """The output of running one scenario through the valuation engine."""
    name: str
    probability: float
    value_per_share: float
    implied_price_to_book: float
    ddm_cross_check: float
    implausible: bool = False
    warnings: tuple[str, ...] = ()
    adjusted_drivers: dict = field(default_factory=dict)
    # Value range for charting (± estimation band)
    value_low: float = 0.0
    value_high: float = 0.0
    value_mid: float = 0.0


def _percentile(sorted_values, sorted_probs, q):
    """Compute the q-th percentile from a discrete probability distribution.

    *sorted_values* and *sorted_probs* must be the same length, with
    *sorted_values* in ascending order.  *sorted_probs* do NOT need to sum to
    1 (they are normalised internally).
    """
    if not sorted_values or not sorted_probs:
        return float("nan")
    total = sum(sorted_probs)
    if total == 0:
        return float("nan")
    cum = 0.0
    for v, p in zip(sorted_values, sorted_probs):
        np_val = p / total
        if cum + np_val >= q:
            return v
        cum += np_val
    return sorted_values[-1]


def _mos_band_from_scenarios(results: list[StressResult]) -> dict:
    """Compute a margin-of-safety buy-band from discrete scenario outcomes.

    Uses the (max - min) / median dispersion metric since we have too few
    points for a meaningful P90-P10 spread.  The coefficient is calibrated
    lower than the Monte Carlo version to avoid over-wide bands from a small
    number of scenarios.
    """
    valid = [r for r in results if not r.implausible]
    if not valid:
        return {"median": float("nan"), "dispersion": float("nan"),
                "mos": 0.15, "buy_below": float("nan"),
                "rich_above": float("nan")}

    values = [r.value_per_share for r in valid]
    probs = [r.probability for r in valid]
    paired = sorted(zip(values, probs), key=lambda x: x[0])
    values_sorted = [p[0] for p in paired]
    probs_sorted = [p[1] for p in paired]

    median = _percentile(values_sorted, probs_sorted, 0.50)
    vmin = values_sorted[0]
    vmax = values_sorted[-1]

    dispersion = (vmax - vmin) / median if median else float("nan")

    MOS_K_SCENARIO = 0.35
    MOS_FLOOR = 0.10
    MOS_CEIL = 0.50

    mos = max(MOS_FLOOR, min(MOS_CEIL, MOS_K_SCENARIO * dispersion))

    return {
        "median": median,
        "dispersion": dispersion,
        "mos": mos,
        "buy_below": median * (1.0 - mos),
        "rich_above": median * (1.0 + mos),
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_stress(
    assumptions_path: str,
    scenario_specs: list[ScenarioSpec] | None = None,
    estimation_band: float = 0.05,
) -> dict:
    """Run the full stress-test pipeline and return a dict for JSON serialisation.

    Parameters
    ----------
    assumptions_path : str
        Path to a financial-assumptions JSON (same format as
        ``financial_valuation.py`` consumes).
    scenario_specs : list[ScenarioSpec] or None
        Scenario library.  If *None*, uses the hardcoded ``SCENARIO_SPECS``.
    estimation_band : float
        Width of the plus/minus band around each scenario's point estimate for
        chart range bars (default 5 percent of the point value).

    Returns
    -------
    dict
        A structured result with keys ``scenarios``, ``lenses``,
        ``weighted_mean``, ``percentiles``, ``mos_band``, ``price``,
        and ``implausible_filtered``.
    """
    if scenario_specs is None:
        scenario_specs = SCENARIO_SPECS

    base_inp = load_inputs(assumptions_path)

    results: list[StressResult] = []
    implausible_filtered: list[dict] = []

    for spec in scenario_specs:
        warnings = _check_implausible(spec)
        is_implausible = len(warnings) > 0

        inp = _apply_scenario(base_inp, spec)
        fin_result: FinancialResult = value(inp)

        band = fin_result.value_per_share * estimation_band

        sr = StressResult(
            name=spec.name,
            probability=spec.probability,
            value_per_share=round(fin_result.value_per_share, 2),
            implied_price_to_book=round(fin_result.implied_price_to_book, 3),
            ddm_cross_check=round(fin_result.ddm_value_per_share, 2),
            implausible=is_implausible,
            warnings=tuple(warnings),
            adjusted_drivers={
                "base_roe": inp.base_roe,
                "target_roe": inp.target_roe,
                "terminal_roe": inp.terminal_roe,
                "cost_of_equity_initial": inp.cost_of_equity_initial,
                "cost_of_equity_terminal": inp.cost_of_equity_terminal,
                "terminal_growth": inp.terminal_growth,
                "payout_ratio": inp.payout_ratio,
                "failure_probability": inp.failure_probability,
                "roe_convergence_year": inp.roe_convergence_year,
            },
            value_low=round(fin_result.value_per_share * (1.0 - estimation_band), 2),
            value_high=round(fin_result.value_per_share * (1.0 + estimation_band), 2),
            value_mid=round(fin_result.value_per_share, 2),
        )

        if is_implausible:
            implausible_filtered.append({
                "name": spec.name,
                "warnings": warnings,
            })

        results.append(sr)

    # --- Weighted statistics (exclude implausible from the distribution) ---
    valid = [r for r in results if not r.implausible]
    total_prob = sum(r.probability for r in valid)

    weighted_mean = (
        sum(r.value_per_share * r.probability for r in valid) / total_prob
        if total_prob > 0
        else float("nan")
    )

    # Build percentile distribution from valid scenarios.
    paired = sorted(
        [(r.value_per_share, r.probability) for r in valid],
        key=lambda x: x[0],
    )
    vals_sorted = [p[0] for p in paired]
    probs_sorted = [p[1] for p in paired]

    percentiles = {}
    for q in (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95):
        pct_key = str(int(q * 100))
        percentiles[pct_key] = round(
            _percentile(vals_sorted, probs_sorted, q), 2
        )

    band = _mos_band_from_scenarios(results)

    # Build chart-compatible shapes.
    scenarios_chart_data = []
    for r in results:
        scenarios_chart_data.append({
            "name": r.name,
            "probability": r.probability,
            "value_per_share": r.value_per_share,
            "value_low": r.value_low,
            "value_high": r.value_high,
            "value_mid": r.value_mid,
            "implied_price_to_book": r.implied_price_to_book,
            "ddm_cross_check": r.ddm_cross_check,
            "implausible": r.implausible,
            "warnings": list(r.warnings),
        })

    # Football-field lenses (same data, different key names for charts.py).
    lenses = []
    for r in results:
        lenses.append({
            "label": r.name,
            "low": r.value_low,
            "high": r.value_high,
            "mid": r.value_mid,
        })

    return {
        "company": base_inp.company,
        "valuation_date": base_inp.valuation_date,
        "scenarios": scenarios_chart_data,
        "lenses": lenses,
        "weighted_mean": round(weighted_mean, 2),
        "percentiles": percentiles,
        "mos_band": {
            k: round(v, 2) if isinstance(v, float) else v
            for k, v in band.items()
        },
        "price": base_inp.price,
        "implausible_filtered": implausible_filtered,
    }


# ---------------------------------------------------------------------------
# Text report
# ---------------------------------------------------------------------------

def _report(data: dict) -> str:
    """Human-readable stress-test summary."""
    lines = [
        f"Financials Stress Test: {data['company']}",
        f"Valuation date: {data['valuation_date']}",
        "=" * 70,
        "",
        f"{'Scenario':<18} {'Prob':>6} {'Value/sh':>10} {'P/B':>7} {'DDM x-check':>12}",
        "-" * 58,
    ]
    for s in data["scenarios"]:
        flag = " [!]" if s["implausible"] else ""
        lines.append(
            f"{s['name'] + flag:<18} {s['probability']:>5.0%} "
            f"{s['value_per_share']:>10.2f} "
            f"{s['implied_price_to_book']:>6.2f}x "
            f"{s['ddm_cross_check']:>12.2f}"
        )
        for w in s.get("warnings", []):
            lines.append(f"  WARNING: {w}")

    lines += [
        "",
        "-" * 58,
        f"Weighted-mean value/share:  {data['weighted_mean']:>10.2f}",
        "",
        "Percentiles of scenario-weighted distribution:",
    ]
    for k, v in data["percentiles"].items():
        lines.append(f"  {k:>3}th: {v:>10.2f}")

    mb = data["mos_band"]
    lines += [
        "",
        f"Margin-of-Safety Buy-Band (MoS {mb['mos']:.0%}, "
        f"dispersion {mb['dispersion']:.3f}):",
        f"  Accumulate below: {mb['buy_below']:>10.2f}",
        f"  Fair (median):    {mb['median']:>10.2f}",
        f"  Rich above:       {mb['rich_above']:>10.2f}",
    ]

    if data["price"]:
        price = data["price"]
        above = sum(
            1 for s in data["scenarios"]
            if not s["implausible"] and s["value_per_share"] >= price
        )
        total_valid = sum(
            1 for s in data["scenarios"] if not s["implausible"]
        )
        prob_above = (
            sum(s["probability"] for s in data["scenarios"]
                if not s["implausible"]
                and s["value_per_share"] >= price)
            / sum(s["probability"] for s in data["scenarios"]
                  if not s["implausible"])
            if total_valid > 0
            else 0.0
        )
        lines += [
            "",
            f"Current price:                       {price:>10.2f}",
            f"Scenarios where value >= price:      {above}/{total_valid}",
            f"Probability-weighted P(value >= price):  {prob_above:.0%}",
        ]

    if data["implausible_filtered"]:
        lines += [
            "",
            f"WARNING: {len(data['implausible_filtered'])} scenario(s) filtered "
            f"as implausible:",
        ]
        for f in data["implausible_filtered"]:
            lines.append(f"  - {f['name']}")
            for w in f["warnings"]:
                lines.append(f"    {w}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Financials stress-test: grid-based scenario analysis "
                    "replacing random-sampling Monte Carlo for banks/insurers.",
    )
    ap.add_argument(
        "assumptions",
        help="Path to financial-assumptions JSON (e.g. "
             "../templates/financials.example.json)",
    )
    ap.add_argument(
        "--output", "-o",
        default=None,
        help="Path for stress.json output (default: stdout as JSON if --json, "
             "else text report to stdout).",
    )
    ap.add_argument(
        "--json", action="store_true",
        help="Emit machine-readable JSON to stdout instead of the text report.",
    )
    ap.add_argument(
        "--estimation-band", type=float, default=0.05,
        help="Plus/minus band width around point estimates for chart ranges "
             "(default: 0.05 = 5 percent).",
    )
    args = ap.parse_args(argv)

    if not os.path.exists(args.assumptions):
        print(f"Error: file not found: {args.assumptions}", file=sys.stderr)
        return 1

    data = run_stress(
        args.assumptions,
        estimation_band=args.estimation_band,
    )

    # Serialize
    output_json = json.dumps(data, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output_json)
            fh.write("\n")
        print(f"Wrote stress.json -> {args.output}")
        # Also print the text report for convenience.
        print()
        print(_report(data))
    elif args.json:
        print(output_json)
    else:
        print(_report(data))

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
