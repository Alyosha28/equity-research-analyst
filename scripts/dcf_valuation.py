"""Intrinsic DCF engine -- Damodaran "story -> numbers -> value".

Two-stage free-cash-flow-to-firm (FCFF) model:

  FCFF_t   = EBIT_t * (1 - tax) - reinvestment_t
  reinvest = (Revenue_t - Revenue_{t-1}) / sales_to_capital
  margin_t = linear glide from base -> target by margin_convergence_year
  CoC_t    = held at initial, then glides to terminal between glide_start/end
  TV_N     = FCFF_{N+1} / (CoC_terminal - g)  with reinvestment = g / terminal_roc

Operating asset value = sum(PV(FCFF)) + PV(TV).
Equity value = operating assets + cash + non-operating - debt - minority.
A failure branch lets value = p*distress + (1-p)*going-concern.

Run directly to value an assumptions JSON:
    python dcf_valuation.py ../templates/assumptions.example.json
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass

try:
    from valuation_inputs import ValuationInputs, load_inputs
except ImportError:  # allow `python scripts/dcf_valuation.py`
    from scripts.valuation_inputs import ValuationInputs, load_inputs  # type: ignore


@dataclass(frozen=True)
class YearRow:
    year: int
    revenue: float
    growth: float
    margin: float
    ebit: float
    after_tax_ebit: float
    reinvestment: float
    fcff: float
    cost_of_capital: float
    discount_factor: float
    pv_fcff: float


@dataclass(frozen=True)
class DCFResult:
    company: str
    valuation_date: str
    rows: tuple
    terminal_value: float
    pv_terminal_value: float
    pv_fcff_sum: float
    operating_asset_value: float
    equity_value: float
    value_per_share: float
    going_concern_value_per_share: float
    terminal_revenue: float
    terminal_pct_of_value: float

    def summary(self) -> str:
        lines = [
            f"Intrinsic valuation: {self.company}  (as of {self.valuation_date})",
            "-" * 64,
            f"{'Yr':>3} {'Revenue':>11} {'Grw':>6} {'Mgn':>6} "
            f"{'FCFF':>11} {'CoC':>6} {'PV(FCFF)':>11}",
        ]
        for r in self.rows:
            lines.append(
                f"{r.year:>3} {r.revenue:>11,.0f} {r.growth:>6.1%} {r.margin:>6.1%} "
                f"{r.fcff:>11,.0f} {r.cost_of_capital:>6.2%} {r.pv_fcff:>11,.0f}"
            )
        lines += [
            "-" * 64,
            f"Terminal revenue (yr {self.rows[-1].year}):   {self.terminal_revenue:>15,.0f} $M",
            f"PV of explicit FCFF:               {self.pv_fcff_sum:>15,.0f} $M",
            f"PV of terminal value:              {self.pv_terminal_value:>15,.0f} $M "
            f"({self.terminal_pct_of_value:.0%} of operating value)",
            f"Operating asset value:             {self.operating_asset_value:>15,.0f} $M",
            f"Equity value:                      {self.equity_value:>15,.0f} $M",
            "=" * 64,
            f"VALUE PER SHARE:                   {self.value_per_share:>15,.2f}",
        ]
        return "\n".join(lines)


def _linear_to_target(base: float, target: float, convergence_year: int, n: int) -> list:
    """Linear glide from `base` (treated as year 0) to `target`, reaching it at
    convergence_year and held flat after. Year t (1..n) sits t/cy of the way from
    base to target, so year 0 == base and year cy == target."""
    cy = max(1, convergence_year)
    return [target if t >= cy else base + (target - base) * (t / cy)
            for t in range(1, n + 1)]


def _margin_path(inp: ValuationInputs) -> list:
    """R&D-adjusted operating margin gliding from base to target by year cy."""
    return _linear_to_target(inp.base_operating_margin, inp.target_operating_margin,
                             inp.margin_convergence_year, inp.horizon)


def _tax_path(inp: ValuationInputs) -> list:
    """Effective tax ramping up to the marginal rate by tax_convergence_year;
    flat tax_rate if no effective rate is given."""
    if inp.effective_tax_rate is None:
        return [inp.tax_rate] * inp.horizon
    return _linear_to_target(inp.effective_tax_rate, inp.tax_rate,
                             inp.tax_convergence_year, inp.horizon)


def _coc_path(inp: ValuationInputs) -> list:
    """Hold CoC at initial, then linearly glide to terminal between
    glide_start_year and glide_end_year."""
    n = inp.horizon
    ci, ct = inp.cost_of_capital_initial, inp.cost_of_capital_terminal
    s, e = inp.coc_glide_start_year, inp.coc_glide_end_year
    out = []
    for t in range(1, n + 1):
        if t <= s:
            out.append(ci)
        elif t >= e:
            out.append(ct)
        else:
            out.append(ci + (ct - ci) * ((t - s) / (e - s)))
    return out


def value(inp: ValuationInputs) -> DCFResult:
    revs = inp.revenue_path()              # years 0..N
    margins = _margin_path(inp)
    cocs = _coc_path(inp)
    taxes = _tax_path(inp)
    n = inp.horizon

    rows = []
    pv_sum = 0.0
    cumulative_df = 1.0
    for t in range(1, n + 1):
        rev = revs[t]
        growth = rev / revs[t - 1] - 1.0
        margin = margins[t - 1]
        ebit = rev * margin
        after_tax = ebit * (1.0 - taxes[t - 1])
        reinvestment = (rev - revs[t - 1]) / inp.sales_to_capital
        fcff = after_tax - reinvestment
        coc = cocs[t - 1]
        cumulative_df *= 1.0 / (1.0 + coc)
        pv = fcff * cumulative_df
        pv_sum += pv
        rows.append(
            YearRow(t, rev, growth, margin, ebit, after_tax,
                    reinvestment, fcff, coc, cumulative_df, pv)
        )

    # Terminal value at year N (FCFF in year N+1, stable growth). The terminal
    # year is taxed at the converged (last explicit-year) rate so it stays
    # consistent with the glide path rather than jumping to a different rate.
    g = inp.terminal_growth
    term_rev = revs[n] * (1.0 + g)
    term_ebit_at = term_rev * inp.target_operating_margin * (1.0 - taxes[-1])
    reinvest_rate = g / inp.terminal_roc          # validated: terminal_roc > g > 0
    term_fcff = term_ebit_at * (1.0 - reinvest_rate)
    ct = inp.cost_of_capital_terminal
    if ct <= g:                                   # defensive; also enforced in __post_init__
        raise ValueError(f"terminal CoC ({ct}) must exceed terminal growth ({g}).")
    tv = term_fcff / (ct - g)
    pv_tv = tv * cumulative_df

    operating = pv_sum + pv_tv
    equity = operating + inp.cash + inp.nonoperating_assets - inp.debt - inp.minority_interests
    going_concern_ps = equity / inp.shares_outstanding

    # Failure-adjusted value (Damodaran's failure branch).
    p = inp.failure_probability
    vps = (1.0 - p) * going_concern_ps + p * inp.failure_value_per_share

    return DCFResult(
        company=inp.company,
        valuation_date=inp.valuation_date,
        rows=tuple(rows),
        terminal_value=tv,
        pv_terminal_value=pv_tv,
        pv_fcff_sum=pv_sum,
        operating_asset_value=operating,
        equity_value=equity,
        value_per_share=vps,
        going_concern_value_per_share=going_concern_ps,
        terminal_revenue=revs[n],
        terminal_pct_of_value=pv_tv / operating if operating > 0 else float("nan"),
    )


def _main(argv) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    inp = load_inputs(argv[1])
    result = value(inp)
    print(result.summary())
    if "--json" in argv:
        print(json.dumps({
            "value_per_share": result.value_per_share,
            "operating_asset_value": result.operating_asset_value,
            "equity_value": result.equity_value,
            "terminal_revenue": result.terminal_revenue,
            "terminal_pct_of_value": result.terminal_pct_of_value,
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
