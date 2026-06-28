"""Intrinsic equity valuation for FINANCIALS (banks, insurers, lenders).

The FCFF engine in ``dcf_valuation.py`` is *wrong* for a bank: a bank has no
"revenue x operating margin", and it reinvests through regulatory capital / risk-
weighted assets, not sales-to-capital. The right lens values the EQUITY directly.

Primary model -- Excess Return on Equity (residual income):

    EquityValue = BV0 + sum( PV(RI_t) ) + PV(terminal RI)
    RI_t        = (ROE_t - Ke_t) * BV_{t-1}          # excess return over the
                                                       # cost of equity
    NI_t        = ROE_t * BV_{t-1}
    BV_t        = BV_{t-1} + NI_t*(1 - payout)        # clean-surplus book growth
    TV_N        = RI_{N+1} / (Ke_term - g),  RI_{N+1} = (ROE_term - Ke_term)*BV_N

A bank only creates value when ROE > Ke; the model makes that spread, and the
Competitive Advantage Period over which it persists, the whole story (Buffett's
"a bank earns its cost of capital plus a spread, or it is worth book at best").

Secondary cross-check -- two-stage Dividend Discount Model on the SAME path (under
clean surplus RIM and DDM are equivalent; a large gap means an input error).

    python financial_valuation.py ../templates/financials.example.json
    python financial_valuation.py ../templates/financials.example.json --json
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class FinancialInputs:
    company: str
    valuation_date: str
    book_value_equity: float          # BV0 of common equity ($M)
    shares_outstanding: float         # millions

    base_roe: float                   # current return on equity
    target_roe: float                 # steady-state ROE through the cycle
    roe_convergence_year: int         # year target ROE is reached

    payout_ratio: float               # dividends + buybacks as a share of NI
    cost_of_equity_initial: float     # Ke during the explicit period
    cost_of_equity_terminal: float    # mature Ke
    coe_glide_start_year: int
    coe_glide_end_year: int

    horizon: int                      # explicit forecast years (N)
    terminal_growth: float            # stable growth (<= Ke_terminal)
    terminal_roe: float               # stable ROE (sets perpetual excess return)

    failure_probability: float = 0.0  # P(catastrophic impairment, e.g. 2008)
    failure_value_per_share: float = 0.0
    price: Optional[float] = None     # current price, for display only
    _notes: tuple = field(default_factory=tuple)

    def __post_init__(self):
        if self.shares_outstanding <= 0:
            raise ValueError("shares_outstanding must be positive.")
        if self.horizon < 1:
            raise ValueError("horizon must be >= 1.")
        if self.terminal_growth < 0:
            raise ValueError("terminal_growth must be >= 0.")
        if self.cost_of_equity_terminal <= self.terminal_growth:
            raise ValueError(
                f"terminal cost of equity ({self.cost_of_equity_terminal}) must "
                f"exceed terminal growth ({self.terminal_growth}).")
        if self.terminal_roe <= self.terminal_growth:
            raise ValueError(
                f"terminal_roe ({self.terminal_roe}) must exceed terminal_growth "
                f"({self.terminal_growth}); otherwise the implied sustainable dividend "
                f"(ROE - g) * BV is non-positive and the DDM terminal value collapses.")
        if not (0.0 <= self.payout_ratio <= 1.0):
            raise ValueError("payout_ratio must be in [0, 1].")
        if self.roe_convergence_year < 1:
            raise ValueError("roe_convergence_year must be >= 1.")
        if self.coe_glide_start_year < 1:
            raise ValueError("coe_glide_start_year must be >= 1.")
        if self.coe_glide_end_year <= self.coe_glide_start_year:
            raise ValueError(
                f"coe_glide_end_year ({self.coe_glide_end_year}) must exceed "
                f"coe_glide_start_year ({self.coe_glide_start_year}); otherwise "
                f"the CoE path degenerates to a step function instead of a glide.")


def _glide(base, target, conv_year, n):
    """Linear glide from base (year 0) to target by conv_year, held flat after."""
    cy = max(1, conv_year)
    return [target if t >= cy else base + (target - base) * (t / cy)
            for t in range(1, n + 1)]


def _coe_path(inp):
    ci, ct = inp.cost_of_equity_initial, inp.cost_of_equity_terminal
    s, e = inp.coe_glide_start_year, inp.coe_glide_end_year
    out = []
    for t in range(1, inp.horizon + 1):
        if t <= s:
            out.append(ci)
        elif t >= e:
            out.append(ct)
        else:
            out.append(ci + (ct - ci) * ((t - s) / (e - s)))
    return out


@dataclass(frozen=True)
class FinancialResult:
    company: str
    valuation_date: str
    rows: tuple
    book_value: float
    pv_residual_income: float
    pv_terminal_value: float
    equity_value: float
    value_per_share: float
    going_concern_value_per_share: float
    implied_price_to_book: float
    terminal_pct_of_value: float
    ddm_value_per_share: float

    def summary(self) -> str:
        lines = [
            f"Financial (excess-return) valuation: {self.company}  (as of {self.valuation_date})",
            "-" * 70,
            f"{'Yr':>3} {'BV(open)':>12} {'ROE':>7} {'Ke':>7} {'NetInc':>11} "
            f"{'ResidInc':>11} {'PV(RI)':>11}",
        ]
        for r in self.rows:
            lines.append(
                f"{r['year']:>3} {r['bv_open']:>12,.0f} {r['roe']:>7.1%} {r['coe']:>7.2%} "
                f"{r['net_income']:>11,.0f} {r['residual_income']:>11,.0f} {r['pv_ri']:>11,.0f}")
        lines += [
            "-" * 70,
            f"Opening book value of equity:      {self.book_value:>15,.0f} $M",
            f"PV of excess returns (explicit):   {self.pv_residual_income:>15,.0f} $M",
            f"PV of terminal excess return:      {self.pv_terminal_value:>15,.0f} $M "
            f"({self.terminal_pct_of_value:.0%} of value above book)",
            f"Equity value:                      {self.equity_value:>15,.0f} $M",
            f"Implied price / book:              {self.implied_price_to_book:>15.2f} x",
            "=" * 70,
            f"VALUE PER SHARE (excess-return):   {self.value_per_share:>15,.2f}",
            f"Cross-check, two-stage DDM:        {self.ddm_value_per_share:>15,.2f}",
        ]
        if self.rows and self.value_per_share:
            return "\n".join(lines)
        return "\n".join(lines)


def value(inp: FinancialInputs) -> FinancialResult:
    roes = _glide(inp.base_roe, inp.target_roe, inp.roe_convergence_year, inp.horizon)
    coes = _coe_path(inp)
    n = inp.horizon

    bv_open = inp.book_value_equity
    rows = []
    pv_ri_sum = 0.0
    pv_div_sum = 0.0
    cumulative_df = 1.0
    for t in range(1, n + 1):
        roe = roes[t - 1]
        coe = coes[t - 1]
        net_income = roe * bv_open
        residual_income = (roe - coe) * bv_open
        dividend = inp.payout_ratio * net_income
        cumulative_df *= 1.0 / (1.0 + coe)
        pv_ri_sum += residual_income * cumulative_df
        pv_div_sum += dividend * cumulative_df
        rows.append({
            "year": t, "bv_open": bv_open, "roe": roe, "coe": coe,
            "net_income": net_income, "residual_income": residual_income,
            "dividend": dividend, "pv_ri": residual_income * cumulative_df,
        })
        bv_open = bv_open + net_income * (1.0 - inp.payout_ratio)   # clean surplus

    bv_n = bv_open                                   # book value at end of year N
    g = inp.terminal_growth
    ct = inp.cost_of_equity_terminal

    # Terminal excess return (residual income), grown into year N+1.
    ri_terminal = (inp.terminal_roe - ct) * bv_n
    tv_ri = ri_terminal / (ct - g)
    pv_tv_ri = tv_ri * cumulative_df

    equity = inp.book_value_equity + pv_ri_sum + pv_tv_ri
    going_concern_ps = equity / inp.shares_outstanding

    # Two-stage DDM cross-check on the same path: explicit dividends + Gordon TV.
    # The terminal dividend uses the payout CONSISTENT with stable growth
    # (g = (1 - payout*) * ROE  =>  payout* = 1 - g/ROE), so the terminal dividend
    # is (ROE - g) * BV_N. Under clean surplus the RIM and DDM are then the same
    # identity -- a residual gap signals an input/code error, not an economic view.
    div_terminal = (inp.terminal_roe - g) * bv_n
    tv_div = div_terminal / (ct - g)
    ddm_equity = pv_div_sum + tv_div * cumulative_df
    ddm_ps = ddm_equity / inp.shares_outstanding

    # Failure branch (a bank can impair its equity in a crisis).
    p = inp.failure_probability
    vps = (1.0 - p) * going_concern_ps + p * inp.failure_value_per_share

    value_above_book = pv_ri_sum + pv_tv_ri
    return FinancialResult(
        company=inp.company,
        valuation_date=inp.valuation_date,
        rows=tuple(rows),
        book_value=inp.book_value_equity,
        pv_residual_income=pv_ri_sum,
        pv_terminal_value=pv_tv_ri,
        equity_value=equity,
        value_per_share=vps,
        going_concern_value_per_share=going_concern_ps,
        implied_price_to_book=equity / inp.book_value_equity,
        terminal_pct_of_value=(pv_tv_ri / value_above_book if value_above_book else float("nan")),
        ddm_value_per_share=ddm_ps,
    )


def _tuplify(raw: dict) -> dict:
    out = {k: v for k, v in raw.items() if not k.startswith("_") or k == "_notes"}
    if "_notes" in out and out["_notes"] is not None:
        out["_notes"] = tuple(out["_notes"])
    return out


def load_inputs(path: str) -> FinancialInputs:
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return FinancialInputs(**_tuplify(raw))


def _main(argv) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    inp = load_inputs(argv[1])
    result = value(inp)
    if "--json" in argv:
        print(json.dumps({
            "company": result.company,
            "value_per_share": result.value_per_share,
            "going_concern_value_per_share": result.going_concern_value_per_share,
            "ddm_value_per_share": result.ddm_value_per_share,
            "equity_value": result.equity_value,
            "book_value": result.book_value,
            "implied_price_to_book": result.implied_price_to_book,
            "terminal_pct_of_value": result.terminal_pct_of_value,
            "price": inp.price,
        }, indent=2))
        return 0
    print(result.summary())
    if inp.price:
        gap = result.value_per_share / inp.price - 1.0
        print(f"Price:                             {inp.price:>15,.2f}  "
              f"(value implies {gap:+.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
