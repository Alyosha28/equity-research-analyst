"""Cyclical valuation engine.

This engine complements, rather than replaces, the standard FCFF DCF. It makes
the commodity or industry price deck explicit, then triangulates three lenses:

1. Price-deck DCF with a normalized terminal EBITDA multiple
2. Mid-cycle EV/EBITDA
3. Asset NPV when a separate asset model is available

The output JSON is designed for report text, reverse DCF, and four cyclical
chart types: price deck, cost-curve position, cycle-position dashboard, and
mid-cycle multiple bridge.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from statistics import mean

try:
    from cyclical_inputs import CyclicalInputs, ForecastYear, load_cyclical_inputs
except ImportError:
    from scripts.cyclical_inputs import CyclicalInputs, ForecastYear, load_cyclical_inputs  # type: ignore


METHOD_LABELS = {
    "price_deck_dcf": "价格表 DCF",
    "midcycle_ev_ebitda": "中周期 EV/EBITDA",
    "asset_npv": "资产 NPV",
}


def revenue_m(inp: CyclicalInputs, row: ForecastYear) -> float:
    if row.revenue_m is not None:
        return float(row.revenue_m)

    model = inp.revenue_model
    if model.type == "physical":
        return row.price * row.volume * model.volume_multiplier / 1_000_000.0
    if model.type == "indexed":
        assert model.base_revenue_m is not None
        assert model.base_price is not None
        assert model.base_volume is not None
        return model.base_revenue_m * (row.price / model.base_price) * (row.volume / model.base_volume)
    raise ValueError("explicit revenue model requires row.revenue_m.")


def ebitda_m(inp: CyclicalInputs, row: ForecastYear, revenue: float) -> float:
    if row.ebitda_m is not None:
        return float(row.ebitda_m)
    if row.ebitda_margin is not None:
        return revenue * row.ebitda_margin
    if inp.revenue_model.type == "physical" and row.cash_cost is not None:
        spread_m = (row.price - row.cash_cost) * row.volume * inp.revenue_model.volume_multiplier / 1_000_000.0
        return spread_m - row.fixed_cost_m
    raise ValueError(
        f"Forecast year {row.year} needs ebitda_m, ebitda_margin, or physical cash_cost."
    )


def _rows(inp: CyclicalInputs) -> tuple[dict, ...]:
    rows = []
    discount_factor = 1.0
    for row in inp.forecast:
        rev = revenue_m(inp, row)
        ebitda = ebitda_m(inp, row, rev)
        ebit = ebitda - row.da_m
        tax_rate = inp.valuation.tax_rate
        fcff = ebit * (1.0 - tax_rate) + row.da_m - row.capex_m - row.working_capital_m
        wacc = row.wacc if row.wacc is not None else inp.valuation.wacc
        discount_factor *= 1.0 / (1.0 + wacc)
        rows.append({
            "year": row.year,
            "phase": row.phase,
            "commodity_price": row.price,
            "cash_cost": row.cash_cost,
            "volume": row.volume,
            "utilization": row.utilization,
            "revenue_m": rev,
            "ebitda_m": ebitda,
            "ebitda_margin": ebitda / rev if rev else None,
            "da_m": row.da_m,
            "ebit_m": ebit,
            "capex_m": row.capex_m,
            "working_capital_m": row.working_capital_m,
            "fcff_m": fcff,
            "wacc": wacc,
            "discount_factor": discount_factor,
            "pv_fcff_m": fcff * discount_factor,
        })
    return tuple(rows)


def _normalized_ebitda(inp: CyclicalInputs, rows: tuple[dict, ...]) -> float:
    if inp.valuation.normalized_ebitda_m is not None:
        return float(inp.valuation.normalized_ebitda_m)
    if not rows:
        return 0.0
    return mean(float(r["ebitda_m"]) for r in rows)


def _method_values(inp: CyclicalInputs, rows: tuple[dict, ...]) -> tuple[dict, ...]:
    if not rows:
        return tuple()
    normalized_ebitda = _normalized_ebitda(inp, rows)
    last_df = float(rows[-1]["discount_factor"])
    pv_fcff = sum(float(r["pv_fcff_m"]) for r in rows)

    terminal_ev = normalized_ebitda * inp.valuation.terminal_ebitda_multiple
    price_deck_ev = pv_fcff + terminal_ev * last_df
    midcycle_ev = normalized_ebitda * inp.valuation.midcycle_ev_ebitda_multiple

    methods = [
        {
            "method": "price_deck_dcf",
            "label": METHOD_LABELS["price_deck_dcf"],
            "enterprise_value_m": price_deck_ev,
            "equity_value_m": price_deck_ev - inp.valuation.net_debt_m,
            "value_per_share": (price_deck_ev - inp.valuation.net_debt_m) / inp.valuation.shares_outstanding,
            "detail": {
                "pv_explicit_fcff_m": pv_fcff,
                "terminal_ev_m": terminal_ev,
                "pv_terminal_ev_m": terminal_ev * last_df,
            },
        },
        {
            "method": "midcycle_ev_ebitda",
            "label": METHOD_LABELS["midcycle_ev_ebitda"],
            "enterprise_value_m": midcycle_ev,
            "equity_value_m": midcycle_ev - inp.valuation.net_debt_m,
            "value_per_share": (midcycle_ev - inp.valuation.net_debt_m) / inp.valuation.shares_outstanding,
            "detail": {
                "normalized_ebitda_m": normalized_ebitda,
                "multiple": inp.valuation.midcycle_ev_ebitda_multiple,
            },
        },
    ]

    if inp.valuation.asset_npv_m is not None:
        asset_ev = float(inp.valuation.asset_npv_m)
        methods.append({
            "method": "asset_npv",
            "label": METHOD_LABELS["asset_npv"],
            "enterprise_value_m": asset_ev,
            "equity_value_m": asset_ev - inp.valuation.net_debt_m,
            "value_per_share": (asset_ev - inp.valuation.net_debt_m) / inp.valuation.shares_outstanding,
            "detail": {"source": "input.asset_npv_m"},
        })

    return tuple(methods)


def _weighted_value(inp: CyclicalInputs, methods: tuple[dict, ...]) -> dict:
    if not methods:
        return {
            "enterprise_value_m": 0.0,
            "equity_value_m": 0.0,
            "value_per_share": 0.0,
            "weights": {},
        }

    raw_weights = inp.valuation.method_weights or {}
    weights = {
        m["method"]: float(raw_weights.get(m["method"], 0.0))
        for m in methods
    }
    total = sum(weights.values())
    if total <= 0:
        equal = 1.0 / len(methods)
        weights = {m["method"]: equal for m in methods}
    else:
        weights = {k: v / total for k, v in weights.items()}

    ev = sum(float(m["enterprise_value_m"]) * weights[m["method"]] for m in methods)
    equity = ev - inp.valuation.net_debt_m
    return {
        "enterprise_value_m": ev,
        "equity_value_m": equity,
        "value_per_share": equity / inp.valuation.shares_outstanding,
        "weights": weights,
    }


def run_valuation(inp: CyclicalInputs, include_sensitivity: bool = True) -> dict:
    rows = _rows(inp)
    methods = _method_values(inp, rows)
    weighted = _weighted_value(inp, methods)
    normalized_ebitda = _normalized_ebitda(inp, rows)
    current_vs_normalized = inp.cycle.current_price / inp.cycle.normalized_price - 1.0

    output = {
        "company": inp.company,
        "ticker": inp.ticker,
        "valuation_date": inp.valuation_date,
        "commodity": inp.commodity.__dict__,
        "cycle": inp.cycle.__dict__ | {"price_percentile": inp.cycle.price_percentile},
        "rows": list(rows),
        "normalization": {
            "current_phase": inp.cycle.current_phase,
            "current_price": inp.cycle.current_price,
            "normalized_price": inp.cycle.normalized_price,
            "trough_price": inp.cycle.trough_price,
            "peak_price": inp.cycle.peak_price,
            "cycle_price_percentile": inp.cycle.price_percentile,
            "current_vs_normalized_price_pct": current_vs_normalized,
            "normalized_ebitda_m": normalized_ebitda,
        },
        "methods": list(methods),
        "weighted": weighted,
        "cost_curve": list(inp.cost_curve),
        "source_notes": list(inp.source_notes),
    }

    if include_sensitivity:
        output["commodity_price_sensitivity"] = _price_sensitivity(inp)
    return output


def _price_sensitivity(inp: CyclicalInputs) -> list[dict]:
    lo = inp.cycle.trough_price
    hi = inp.cycle.peak_price
    if hi <= lo:
        return []
    points = [lo + (hi - lo) * i / 8 for i in range(9)]
    out = []
    for price in points:
        shifted = inp.with_normalized_price(price)
        value = run_valuation(shifted, include_sensitivity=False)["weighted"]["value_per_share"]
        out.append({
            "normalized_price": price,
            "value_per_share": value,
        })
    return out


def solve_implied_normalized_price(
    inp: CyclicalInputs,
    target_price_per_share: float,
    lo: float | None = None,
    hi: float | None = None,
) -> dict:
    """Solve for the normalized commodity/panel price that matches the stock price."""
    lo = inp.cycle.trough_price if lo is None else lo
    hi = inp.cycle.peak_price if hi is None else hi
    if lo <= 0 or hi <= lo:
        raise ValueError("invalid price bounds for implied commodity price solve.")

    def value_at(price: float) -> float:
        shifted = inp.with_normalized_price(price)
        return run_valuation(shifted, include_sensitivity=False)["weighted"]["value_per_share"]

    v_lo = value_at(lo)
    v_hi = value_at(hi)
    if (v_lo - target_price_per_share) * (v_hi - target_price_per_share) > 0:
        implied = lo if abs(v_lo - target_price_per_share) < abs(v_hi - target_price_per_share) else hi
        achieved = value_at(implied)
        converged = False
    else:
        a, b = lo, hi
        for _ in range(120):
            mid = (a + b) / 2
            v_mid = value_at(mid)
            if v_mid < target_price_per_share:
                a = mid
            else:
                b = mid
        implied = (a + b) / 2
        achieved = value_at(implied)
        converged = abs(achieved - target_price_per_share) <= max(0.01, abs(target_price_per_share) * 0.005)

    return {
        "company": inp.company,
        "ticker": inp.ticker,
        "solve_for": "commodity_price",
        "price": target_price_per_share,
        "base_value": run_valuation(inp, include_sensitivity=False)["weighted"]["value_per_share"],
        "implied_normalized_price": implied,
        "base_normalized_price": inp.cycle.normalized_price,
        "trough_price": lo,
        "peak_price": hi,
        "achieved": achieved,
        "converged": converged,
        "implied_vs_base_pct": implied / inp.cycle.normalized_price - 1.0,
    }


def _round_for_json(obj):
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: _round_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_for_json(v) for v in obj]
    return obj


def _main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run cyclical valuation from a cyclical_inputs JSON file.")
    parser.add_argument("cyclical_inputs")
    parser.add_argument("--output", default=None, help="write JSON output to this path")
    parser.add_argument("--json", action="store_true", help="print JSON to stdout")
    args = parser.parse_args(argv)

    inp = load_cyclical_inputs(args.cyclical_inputs)
    result = _round_for_json(run_valuation(inp))
    text = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.write("\n")
    if args.json or not args.output:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
