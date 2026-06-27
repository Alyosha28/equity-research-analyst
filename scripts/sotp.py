"""Sum-of-the-parts (SOTP) valuation -- for holding-company / conglomerate
hybrids where an operating business sits alongside a large investment portfolio
(Tencent, SoftBank, Berkshire-likes, Naspers/Prosus).

  SOTP equity = core operating value          (from the intrinsic DCF)
              + listed investments  x (1 - listed_haircut)
              + unlisted investments x (1 - unlisted_haircut)
              ... the portfolio then x (1 - holding_company_discount)
              + net cash
              - minority interests
  per share (valuation ccy) = SOTP equity / shares
  per share (report ccy)    = above x fx_report_per_valuation

Also runs the "stub" cross-check: back the portfolio + net cash out of the
market cap to reveal the multiple the market is paying for the CORE business
alone -- the heart of any "hidden value / 价值洼地" thesis.

Money is in MILLIONS of the valuation currency (e.g. RMB millions); per-share
prices are in their stated currency. Keys starting with "_" are comments.

    python sotp.py ../templates/tencent.sotp.json
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from typing import Optional

try:
    from valuation_inputs import load_inputs
    import dcf_valuation as dcf
except ImportError:
    from scripts.valuation_inputs import load_inputs  # type: ignore
    from scripts import dcf_valuation as dcf  # type: ignore


@dataclass(frozen=True)
class SotpInputs:
    company: str
    valuation_currency: str                 # e.g. "RMB"
    report_currency: str                    # e.g. "HKD"
    fx_report_per_valuation: float          # report ccy per 1 unit of valuation ccy

    shares_outstanding: float               # millions
    market_price_report_ccy: float          # current price in report ccy (for upside/stub)

    # --- core operating business -----------------------------------------
    core_assumptions_path: Optional[str] = None   # JSON to run the core DCF
    core_operating_value: Optional[float] = None  # OR provide directly (val ccy, M)
    core_earnings: float = 0.0                     # core net earnings (val ccy, M) for stub P/E

    # --- investment portfolio --------------------------------------------
    listed_investments: float = 0.0          # market value (val ccy, M)
    listed_haircut: float = 0.0              # e.g. 0.15 tax-on-disposal
    unlisted_investments: float = 0.0        # carrying value (val ccy, M)
    unlisted_haircut: float = 0.0
    holding_company_discount: float = 0.0    # applied to the post-haircut portfolio

    # --- bridge ----------------------------------------------------------
    net_cash: float = 0.0                    # cash - debt (val ccy, M)
    minority_interests: float = 0.0          # (val ccy, M)

    def portfolio_value(self, hold_disc: Optional[float] = None) -> float:
        hd = self.holding_company_discount if hold_disc is None else hold_disc
        gross = (self.listed_investments * (1.0 - self.listed_haircut)
                 + self.unlisted_investments * (1.0 - self.unlisted_haircut))
        return gross * (1.0 - hd)


@dataclass(frozen=True)
class SotpResult:
    company: str
    core_value: float
    portfolio_value: float
    net_cash: float
    minority_interests: float
    equity_value_val_ccy: float
    per_share_val_ccy: float
    per_share_report_ccy: float
    market_price: float
    upside: float
    implied_core_value: float            # market-implied core (val ccy, M)
    implied_core_pe: float               # market-implied core P/E
    dcf_core_pe: float                   # P/E the DCF puts on the core
    val_ccy: str
    report_ccy: str

    def summary(self) -> str:
        L = []
        L.append(f"SOTP valuation: {self.company}")
        L.append("=" * 60)
        L.append(f"Core operating value:        {self.core_value:>14,.0f} {self.val_ccy}M")
        L.append(f"+ Investment portfolio:      {self.portfolio_value:>14,.0f} {self.val_ccy}M")
        L.append(f"+ Net cash:                  {self.net_cash:>14,.0f} {self.val_ccy}M")
        if self.minority_interests:
            L.append(f"- Minority interests:        {self.minority_interests:>14,.0f} {self.val_ccy}M")
        L.append("-" * 60)
        L.append(f"= SOTP equity value:         {self.equity_value_val_ccy:>14,.0f} {self.val_ccy}M")
        L.append(f"  per share:                 {self.per_share_val_ccy:>14,.2f} {self.val_ccy}")
        L.append(f"  per share ({self.report_ccy}):           {self.per_share_report_ccy:>14,.2f} {self.report_ccy}")
        L.append("=" * 60)
        L.append(f"Market price:                {self.market_price:>14,.2f} {self.report_ccy}")
        L.append(f"Upside / (downside):         {self.upside:>13.1%}")
        L.append("")
        L.append("Stub cross-check (what the market pays for the CORE alone):")
        L.append(f"  Market-implied core value: {self.implied_core_value:>14,.0f} {self.val_ccy}M")
        L.append(f"  Market-implied core P/E:   {self.implied_core_pe:>14.1f} x")
        L.append(f"  (DCF puts the core at:     {self.dcf_core_pe:>14.1f} x of the same earnings)")
        return "\n".join(L)


def value(inp: SotpInputs) -> SotpResult:
    # 1. core operating value -- run the DCF or take the provided number.
    if inp.core_operating_value is not None:
        core = inp.core_operating_value
    elif inp.core_assumptions_path:
        core = dcf.value(load_inputs(inp.core_assumptions_path)).operating_asset_value
    else:
        raise ValueError("Provide core_operating_value or core_assumptions_path.")

    portfolio = inp.portfolio_value()
    equity = core + portfolio + inp.net_cash - inp.minority_interests
    ps_val = equity / inp.shares_outstanding
    ps_rep = ps_val * inp.fx_report_per_valuation
    upside = ps_rep / inp.market_price_report_ccy - 1.0

    # stub: back portfolio + net cash out of market cap -> implied core
    market_cap_val = (inp.market_price_report_ccy * inp.shares_outstanding) / inp.fx_report_per_valuation
    implied_core = market_cap_val - portfolio - inp.net_cash
    implied_pe = implied_core / inp.core_earnings if inp.core_earnings else float("nan")
    dcf_pe = core / inp.core_earnings if inp.core_earnings else float("nan")

    return SotpResult(
        company=inp.company, core_value=core, portfolio_value=portfolio,
        net_cash=inp.net_cash, minority_interests=inp.minority_interests,
        equity_value_val_ccy=equity, per_share_val_ccy=ps_val,
        per_share_report_ccy=ps_rep, market_price=inp.market_price_report_ccy,
        upside=upside, implied_core_value=implied_core, implied_core_pe=implied_pe,
        dcf_core_pe=dcf_pe, val_ccy=inp.valuation_currency, report_ccy=inp.report_currency,
    )


def sensitivity(inp: SotpInputs, core: float, discounts) -> str:
    """Per-share (report ccy) across a range of holding-company discounts."""
    L = ["", "Sensitivity -- value/share vs holding-company discount on the portfolio:"]
    L.append(f"  {'discount':>10} {'port. value':>14} {'per share ('+inp.report_currency+')':>16} {'upside':>9}")
    for hd in discounts:
        port = inp.portfolio_value(hold_disc=hd)
        eq = core + port + inp.net_cash - inp.minority_interests
        ps = eq / inp.shares_outstanding * inp.fx_report_per_valuation
        up = ps / inp.market_price_report_ccy - 1.0
        L.append(f"  {hd:>10.0%} {port:>14,.0f} {ps:>16,.2f} {up:>9.1%}")
    return "\n".join(L)


def _tuplify(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("_")}


def load_sotp(path: str) -> SotpInputs:
    with open(path, "r", encoding="utf-8") as fh:
        raw = _tuplify(json.load(fh))
    # resolve core_assumptions_path relative to the sotp file
    if raw.get("core_assumptions_path"):
        base = os.path.dirname(os.path.abspath(path))
        raw["core_assumptions_path"] = os.path.join(base, raw["core_assumptions_path"])
    return SotpInputs(**raw)


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Sum-of-the-parts valuation for holding companies.")
    ap.add_argument("sotp_json")
    ap.add_argument("--no-sensitivity", action="store_true")
    args = ap.parse_args(argv)
    inp = load_sotp(args.sotp_json)
    result = value(inp)
    print(result.summary())
    if not args.no_sensitivity:
        print(sensitivity(inp, result.core_value, [0.0, 0.10, 0.20, 0.30, 0.40]))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
