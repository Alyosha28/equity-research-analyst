"""Fetch analyst consensus estimates and compare against intrinsic assumptions.

Consensus is a reality check, not a valuation input. Wide deviations between
the sell-side crowd and our own story-driven numbers flag areas where the market
may be mispricing the asset -- or where our story needs re-examination.

    python fetch_consensus.py NVDA --assumptions ../templates/assumptions.example.json --json
    python fetch_consensus.py MSFT --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date
from typing import Optional

try:
    from valuation_inputs import ValuationInputs, load_inputs
except ImportError:
    from scripts.valuation_inputs import ValuationInputs, load_inputs  # type: ignore


# ---------------------------------------------------------------------------
# frozen dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConsensusData:
    """Analyst consensus estimates for a single ticker at a point in time.

    All monetary values are in millions of the reporting currency (USD by
    default).  Estimates are stored as tuples where each element represents a
    fiscal period (typically current fiscal year, next fiscal year).

    When estimates cannot be fetched (network error, no coverage, ticker not
    found) the estimate tuples will be empty and ``num_analysts`` will be 0.
    """

    ticker: str
    fetch_date: str
    revenue_estimates: tuple   # (fy0_mean, fy1_mean, ...) in $M
    eps_estimates: tuple       # (fy0_eps, fy1_eps, ...) in reporting currency / share
    ebitda_estimates: Optional[tuple] = None  # trailing EBITDA in $M (yfinance does not carry forward EBITDA)
    target_price: Optional[float] = None      # mean analyst price target
    num_analysts: int = 0
    source: str = "yfinance"

    @property
    def has_data(self) -> bool:
        """True if at least one revenue or EPS estimate was successfully fetched."""
        return len(self.revenue_estimates) > 0 or len(self.eps_estimates) > 0


@dataclass(frozen=True)
class DeviationAnalysis:
    """Comparison between consensus-implied drivers and our intrinsic assumptions.

    Positive deviations mean the market is *more* optimistic than our model;
    negative deviations mean the market is *less* optimistic.
    """

    growth_deviation_pct: float   # consensus-implied CAGR minus our y1 growth (pp)
    margin_deviation_pct: float   # consensus-implied pre-tax margin minus our target (pp)
    revenue_deviation_pct: float  # consensus fy1 revenue % above/below our model
    summary: str                  # one-line interpretation
    flags: tuple = ()             # warning / observation tags


# ---------------------------------------------------------------------------
# extraction helpers (yfinance internals)
# ---------------------------------------------------------------------------

def _extract_revenue_estimates(t, info: dict) -> list:
    """Return [fy0_rev_m, fy1_rev_m, ...] in $M, or empty list."""
    estimates: list = []

    # -- primary: yfinance revenue_estimates (DataFrame, dict, or list depending on version)
    try:
        raw = t.revenue_estimates
        if raw is not None:
            if hasattr(raw, "iterrows"):
                # pandas DataFrame with columns: avg, low, high, numberOfAnalysts, year, growth
                for _, row in raw.iterrows():
                    avg = row.get("avg")
                    if avg is not None and float(avg) > 0:
                        estimates.append(round(float(avg) / 1e6, 1))
            elif isinstance(raw, dict):
                # older yfinance dict format
                for _k in sorted(raw.keys()):
                    v = raw[_k]
                    if isinstance(v, (int, float)) and float(v) > 0:
                        estimates.append(round(float(v) / 1e6, 1))
            elif isinstance(raw, (list, tuple)):
                for item in raw:
                    if isinstance(item, dict) and item.get("avg"):
                        estimates.append(round(float(item["avg"]) / 1e6, 1))
            if estimates:
                return estimates[:2]
    except Exception:
        pass

    # -- fallback: compound info["totalRevenue"] by info["revenueGrowth"]
    base_rev = info.get("totalRevenue")
    if base_rev is not None and float(base_rev) > 0:
        base_m = float(base_rev) / 1e6
        growth = info.get("revenueGrowth")
        if growth is not None and float(growth) != 0:
            fy0 = round(base_m * (1.0 + float(growth)), 1)
            estimates.append(fy0)
            # guess fy1 conservatively at the same growth rate
            estimates.append(round(fy0 * (1.0 + float(growth)), 1))
        else:
            estimates.append(round(base_m, 1))

    return estimates


def _extract_eps_estimates(t, info: dict) -> list:
    """Return [fy0_eps, fy1_eps, ...] in reporting currency / share, or empty list."""
    estimates: list = []

    # -- primary: yfinance earnings_estimates (DataFrame / dict)
    try:
        raw = t.earnings_estimates
        if raw is not None:
            if hasattr(raw, "iterrows"):
                for _, row in raw.iterrows():
                    avg = row.get("avg")
                    if avg is not None and float(avg) != 0:
                        estimates.append(round(float(avg), 2))
            elif isinstance(raw, dict):
                for _k in sorted(raw.keys()):
                    v = raw[_k]
                    if isinstance(v, (int, float)):
                        estimates.append(round(float(v), 2))
            elif isinstance(raw, (list, tuple)):
                for item in raw:
                    if isinstance(item, dict) and item.get("avg") is not None:
                        estimates.append(round(float(item["avg"]), 2))
            if estimates:
                return estimates[:2]
    except Exception:
        pass

    # -- fallback: info dict forwardEps
    fwd = info.get("forwardEps")
    if fwd is not None and float(fwd) != 0:
        estimates.append(round(float(fwd), 2))
        # try for a second year via long-term growth
        ltg = info.get("longTermGrowth") or info.get("earningsGrowth")
        if ltg is not None:
            estimates.append(round(estimates[0] * (1.0 + float(ltg)), 2))

    return estimates


def _extract_ebitda_estimates(t, info: dict) -> list:
    """Return [trailing_ebitda_m] in $M, or empty list.  yfinance does not
    publish forward EBITDA consensus, so this is always trailing."""
    estimates: list = []
    ebitda = info.get("ebitda")
    if ebitda is not None and float(ebitda) > 0:
        estimates.append(round(float(ebitda) / 1e6, 1))
    return estimates


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def fetch_consensus(ticker: str) -> ConsensusData:
    """Fetch analyst consensus estimates for *ticker* via yfinance.

    Network errors, missing tickers, and yfinance quirks are caught and
    reported in the returned object -- the function never raises.  Check
    ``consensus.has_data`` to see whether estimates were obtained.

    Parameters
    ----------
    ticker : str
        Yahoo Finance ticker symbol (e.g. "NVDA", "0700.HK").

    Returns
    -------
    ConsensusData
        Frozen consensus snapshot, possibly empty if the fetch failed.
    """
    today = date.today().isoformat()

    # --- guard: yfinance installed? ---
    try:
        import yfinance as yf  # noqa: F811
    except ImportError:
        return ConsensusData(
            ticker=ticker.upper(),
            fetch_date=today,
            revenue_estimates=(),
            eps_estimates=(),
            source="yfinance (not installed)",
        )

    # --- fetch ---
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        rev = _extract_revenue_estimates(t, info)
        eps = _extract_eps_estimates(t, info)
        ebitda = _extract_ebitda_estimates(t, info)

        # target price -- try info dict first, then analyst_price_targets attr
        target_price: Optional[float] = None
        tp_raw = info.get("targetMeanPrice")
        if tp_raw is not None:
            target_price = float(tp_raw)
        else:
            try:
                apt = t.analyst_price_targets
                if apt is not None:
                    target_price = float(apt.get("mean") or apt.get("current") or 0) or None
            except Exception:
                pass

        num_analysts = int(info.get("numberOfAnalystOpinions", 0) or 0)

        return ConsensusData(
            ticker=ticker.upper(),
            fetch_date=today,
            revenue_estimates=tuple(rev),
            eps_estimates=tuple(eps),
            ebitda_estimates=tuple(ebitda) if ebitda else None,
            target_price=target_price,
            num_analysts=num_analysts,
            source="yfinance",
        )

    except Exception as exc:
        return ConsensusData(
            ticker=ticker.upper(),
            fetch_date=today,
            revenue_estimates=(),
            eps_estimates=(),
            source=f"yfinance (error: {exc})",
        )


# ---------------------------------------------------------------------------
# deviation analysis
# ---------------------------------------------------------------------------

def _back_out_consensus_margin(consensus: ConsensusData,
                               our: ValuationInputs) -> Optional[float]:
    """Back out a rough pre-tax operating margin from consensus EPS and revenue.

    Simplification: this treats EPS-derived net income as if it were EBIT *
    (1 - tax), ignoring interest, non-operating items, and minority interests.
    For the purpose of flagging large deviations between market and model this
    approximation is adequate, but it should not be used as a precision estimate.
    """
    if not consensus.eps_estimates or not consensus.revenue_estimates:
        return None

    shares = our.shares_outstanding          # millions of shares
    consensus_eps = consensus.eps_estimates[0]  # raw currency / share
    consensus_rev = consensus.revenue_estimates[0]  # $M

    if shares <= 0 or consensus_rev <= 0:
        return None

    # net income in $M = EPS (raw) * shares (millions)
    net_income_m = consensus_eps * shares

    # gross up to pre-tax income
    if our.tax_rate >= 1.0:
        return None
    pre_tax_m = net_income_m / (1.0 - our.tax_rate)

    margin = pre_tax_m / consensus_rev

    # reject nonsensical values
    if margin < -0.50 or margin > 0.95:
        return None

    return round(margin, 4)


def analyze_deviation(consensus: ConsensusData,
                      our: ValuationInputs) -> DeviationAnalysis:
    """Compare consensus-implied growth and margin against our model assumptions.

    Backs out:
    * Consensus-implied FY1/FY0 revenue growth and compares to our year-1 growth.
    * Consensus-implied pre-tax margin (via EPS) and compares to our target margin.
    * FY1 revenue level divergence in percent.

    Parameters
    ----------
    consensus : ConsensusData
        Result from ``fetch_consensus``.
    our : ValuationInputs
        Our intrinsic-DCF assumptions.

    Returns
    -------
    DeviationAnalysis
        Frozen analysis with percentage deviations, a human-readable summary,
        and a tuple of observation flags.
    """
    flags: list[str] = []

    # ---- growth deviation ------------------------------------------------
    our_y1_growth = our.revenue_growth[0] if our.horizon >= 1 else 0.0

    consensus_growth = 0.0
    if len(consensus.revenue_estimates) >= 2:
        fy0, fy1 = consensus.revenue_estimates[0], consensus.revenue_estimates[1]
        if fy0 > 0:
            consensus_growth = fy1 / fy0 - 1.0

    growth_dev = (consensus_growth - our_y1_growth) * 100.0   # percentage points

    # ---- revenue-level deviation ------------------------------------------
    our_fy1_rev = our.revenue_path()[1] if our.horizon >= 1 else our.base_revenue
    revenue_dev = 0.0
    if consensus.revenue_estimates and our_fy1_rev > 0:
        c_rev = consensus.revenue_estimates[0]
        revenue_dev = (c_rev - our_fy1_rev) / our_fy1_rev * 100.0

    # ---- margin deviation -------------------------------------------------
    consensus_margin = _back_out_consensus_margin(consensus, our)
    margin_dev = 0.0
    if consensus_margin is not None:
        margin_dev = (consensus_margin - our.target_operating_margin) * 100.0

    # ---- flags ------------------------------------------------------------
    if abs(growth_dev) > 5.0:
        direction = "above" if growth_dev > 0 else "below"
        flags.append(f"consensus growth {abs(growth_dev):.1f}pp {direction} model")

    if abs(margin_dev) > 3.0:
        direction = "above" if margin_dev > 0 else "below"
        flags.append(f"consensus margin {abs(margin_dev):.1f}pp {direction} model target")

    if abs(revenue_dev) > 10.0:
        direction = "above" if revenue_dev > 0 else "below"
        flags.append(f"consensus revenue {abs(revenue_dev):.1f}% {direction} model fy1")

    # ---- summary ----------------------------------------------------------
    parts: list[str] = []

    if not consensus.has_data:
        parts.append("no consensus data available")
    else:
        if growth_dev > 3.0:
            parts.append("market more optimistic on growth")
        elif growth_dev < -3.0:
            parts.append("market more cautious on growth")
        else:
            parts.append("growth broadly aligned")

        if margin_dev > 2.0:
            parts.append("market pricing in higher margins")
        elif margin_dev < -2.0:
            parts.append("market pricing in lower margins")
        else:
            parts.append("margins broadly aligned")

    summary = "; ".join(parts) + "."

    return DeviationAnalysis(
        growth_deviation_pct=round(growth_dev, 1),
        margin_deviation_pct=round(margin_dev, 1),
        revenue_deviation_pct=round(revenue_dev, 1),
        summary=summary,
        flags=tuple(flags),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Fetch analyst consensus estimates and compare against intrinsic assumptions."
    )
    ap.add_argument("ticker", help="Yahoo Finance ticker symbol (e.g. NVDA, 0700.HK)")
    ap.add_argument("--assumptions", default=None,
                    help="path to a ValuationInputs JSON; if given, run deviation analysis")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON instead of a human summary")
    args = ap.parse_args(argv)

    ticker = args.ticker.strip().upper()

    # --- fetch consensus ---------------------------------------------------
    consensus = fetch_consensus(ticker)
    if not consensus.has_data:
        sys.stderr.write(f"# No consensus data returned for {ticker} "
                         f"(source: {consensus.source})\n")

    # --- deviation analysis (if assumptions provided) -----------------------
    deviation: Optional[DeviationAnalysis] = None
    if args.assumptions:
        try:
            our = load_inputs(args.assumptions)
            deviation = analyze_deviation(consensus, our)
        except Exception as exc:
            sys.stderr.write(f"# Could not load/analyze assumptions: {exc}\n")

    # --- output ------------------------------------------------------------
    if args.json:
        output: dict = {
            "ticker": consensus.ticker,
            "fetch_date": consensus.fetch_date,
            "source": consensus.source,
            "revenue_estimates": list(consensus.revenue_estimates),
            "eps_estimates": list(consensus.eps_estimates),
            "ebitda_estimates": (list(consensus.ebitda_estimates)
                                 if consensus.ebitda_estimates else None),
            "target_price": consensus.target_price,
            "num_analysts": consensus.num_analysts,
        }
        if deviation is not None:
            output["deviation"] = {
                "growth_deviation_pp": deviation.growth_deviation_pct,
                "margin_deviation_pp": deviation.margin_deviation_pct,
                "revenue_deviation_pct": deviation.revenue_deviation_pct,
                "summary": deviation.summary,
                "flags": list(deviation.flags),
            }
        print(json.dumps(output, indent=2))
        return 0

    # --- human-readable output ---------------------------------------------
    print(f"Consensus: {consensus.ticker}  (fetched {consensus.fetch_date})")
    print(f"  Source:       {consensus.source}")
    print(f"  Analysts:     {consensus.num_analysts}")
    print(f"  Target price: {consensus.target_price:.2f}" if consensus.target_price
          else "  Target price: n/a")
    print(f"  Revenue ests ($M): {list(consensus.revenue_estimates)}"
          if consensus.revenue_estimates else "  Revenue ests: n/a")
    print(f"  EPS ests:          {list(consensus.eps_estimates)}"
          if consensus.eps_estimates else "  EPS ests: n/a")
    if consensus.ebitda_estimates:
        print(f"  EBITDA trailing ($M): {consensus.ebitda_estimates[0]:,.0f}")
    print()

    if deviation is not None:
        print(f"Deviation vs model ({our.company}):")
        print(f"  Growth deviation:  {deviation.growth_deviation_pct:+.1f} pp")
        print(f"  Margin deviation:  {deviation.margin_deviation_pct:+.1f} pp")
        print(f"  Revenue deviation: {deviation.revenue_deviation_pct:+.1f} %")
        print(f"  Summary: {deviation.summary}")
        if deviation.flags:
            for flag in deviation.flags:
                print(f"    [!] {flag}")
    elif not args.assumptions:
        print("(pass --assumptions <path.json> to compare against your model)")

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
