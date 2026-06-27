"""Pre-fill an assumptions skeleton for a ticker -- cut the data-gathering chore.

This does the MECHANICAL part (recent revenue, shares, cash, debt, price) and
leaves every JUDGMENT field (target margin, TAM/share, terminal, cost of capital)
as an explicit ``_TODO``. It NEVER produces a finished valuation, and everything it
fetches is tagged as third-party data that a human must confirm before publishing.

Sources, in order: yfinance (if installed) -> SEC EDGAR companyfacts (stdlib only).
If neither is reachable it still emits a fully-commented skeleton, so the command is
useful offline.

    python fetch_financials.py NVDA --out ../path/nvda.skeleton.json
    python fetch_financials.py JPM  --financials --out jpm.skeleton.json

Guardrail: output rows are tier=third-party-aggregator. Confirm against filings,
then delete the `_source`/`_TODO` scaffolding before running the engine.
"""

from __future__ import annotations

import argparse
import json
import sys

EDGAR_TICKERS = "https://www.sec.gov/files/company_tickers.json"
EDGAR_FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
# SEC requires a descriptive User-Agent; this is a research/educational tool.
UA = {"User-Agent": "equity-research-analyst skill (educational; contact: analyst@example.com)"}

TODO = "FILL-IN: judgment input, not mechanically fetchable"


def _fcff_skeleton():
    return {
        "_comment": "AUTO-GENERATED skeleton. Mechanical fields are third-party data "
                    "(confirm vs filings). _TODO fields are YOUR judgment. Delete this "
                    "scaffolding before running dcf_valuation.py.",
        "company": None, "valuation_date": None,
        "base_revenue": None, "_base_revenue_source": None,
        "revenue_growth": TODO, "_revenue_growth": "story->numbers: TAM x share path",
        "base_operating_margin": None, "_base_margin_source": None,
        "target_operating_margin": TODO, "margin_convergence_year": TODO,
        "sales_to_capital": TODO, "tax_rate": TODO,
        "cost_of_capital_initial": TODO, "cost_of_capital_terminal": TODO,
        "coc_glide_start_year": TODO, "coc_glide_end_year": TODO,
        "terminal_growth": TODO, "terminal_roc": TODO,
        "cash": None, "_cash_source": None,
        "debt": None, "_debt_source": None,
        "shares_outstanding": None, "_shares_source": None,
        "_price": None,
    }


def _financial_skeleton():
    return {
        "_comment": "AUTO-GENERATED financials skeleton for financial_valuation.py. "
                    "Mechanical fields are third-party data; _TODO fields are judgment.",
        "company": None, "valuation_date": None,
        "book_value_equity": None, "_book_value_source": None,
        "shares_outstanding": None, "_shares_source": None,
        "base_roe": None, "_base_roe_source": None,
        "target_roe": TODO, "_target_roe": "THROUGH-CYCLE, not peak",
        "roe_convergence_year": TODO, "payout_ratio": TODO,
        "cost_of_equity_initial": TODO, "cost_of_equity_terminal": TODO,
        "coe_glide_start_year": TODO, "coe_glide_end_year": TODO,
        "horizon": 10, "terminal_growth": TODO, "terminal_roe": TODO,
        "failure_probability": TODO, "_price": None,
    }


def _try_yfinance(ticker, skel, financials):
    try:
        import yfinance as yf
    except Exception:
        return False, "yfinance not installed"
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        skel["company"] = info.get("longName") or ticker
        skel["shares_outstanding"] = _millions(info.get("sharesOutstanding"))
        skel["_shares_source"] = "yfinance info.sharesOutstanding"
        skel["_price"] = info.get("currentPrice") or info.get("previousClose")
        if financials:
            bv = info.get("bookValue")
            if bv and skel["shares_outstanding"]:
                skel["book_value_equity"] = round(bv * skel["shares_outstanding"], 1)
                skel["_book_value_source"] = "yfinance bookValue x shares (CONFIRM: tangible?)"
            roe = info.get("returnOnEquity")
            if roe:
                skel["base_roe"] = round(roe, 4)
                skel["_base_roe_source"] = "yfinance returnOnEquity (CONFIRM: normalize through-cycle)"
        else:
            rev = info.get("totalRevenue")
            if rev:
                skel["base_revenue"] = _millions(rev)
                skel["_base_revenue_source"] = "yfinance info.totalRevenue"
            skel["cash"] = _millions(info.get("totalCash"))
            skel["_cash_source"] = "yfinance info.totalCash"
            skel["debt"] = _millions(info.get("totalDebt"))
            skel["_debt_source"] = "yfinance info.totalDebt"
            m = info.get("operatingMargins")
            if m is not None:
                skel["base_operating_margin"] = round(m, 4)
                skel["_base_margin_source"] = "yfinance operatingMargins (CONFIRM: R&D-adjust)"
        return True, "yfinance"
    except Exception as e:
        return False, f"yfinance error: {e}"


def _try_edgar(ticker, skel, financials):
    import urllib.request
    try:
        cik = _edgar_cik(ticker)
        if cik is None:
            return False, "ticker not found in EDGAR"
        req = urllib.request.Request(EDGAR_FACTS.format(cik=cik), headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            facts = json.load(r)
        skel["company"] = facts.get("entityName") or ticker
        us = facts.get("facts", {}).get("us-gaap", {})
        shares = _edgar_latest(us, ("CommonStockSharesOutstanding", "EntityCommonStockSharesOutstanding"))
        if shares:
            skel["shares_outstanding"] = _millions(shares)
            skel["_shares_source"] = "SEC EDGAR companyfacts"
        if financials:
            bv = _edgar_latest(us, ("StockholdersEquity",))
            if bv:
                skel["book_value_equity"] = _millions(bv)
                skel["_book_value_source"] = "SEC EDGAR StockholdersEquity (CONFIRM: tangible)"
        else:
            rev = _edgar_latest(us, ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"))
            if rev:
                skel["base_revenue"] = _millions(rev)
                skel["_base_revenue_source"] = "SEC EDGAR Revenues"
            cash = _edgar_latest(us, ("CashAndCashEquivalentsAtCarryingValue",))
            if cash:
                skel["cash"] = _millions(cash)
                skel["_cash_source"] = "SEC EDGAR CashAndCashEquivalents"
        return True, "edgar"
    except Exception as e:
        return False, f"edgar error: {e}"


def _edgar_cik(ticker):
    import urllib.request
    req = urllib.request.Request(EDGAR_TICKERS, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    for row in data.values():
        if row.get("ticker", "").upper() == ticker.upper():
            return int(row["cik_str"])
    return None


def _edgar_latest(us_gaap, keys):
    """Most recent annual (FY) USD value among the given concept keys."""
    for k in keys:
        node = us_gaap.get(k)
        if not node:
            continue
        units = node.get("units", {}).get("USD") or next(iter(node.get("units", {}).values()), [])
        annual = [u for u in units if u.get("form") in ("10-K", "20-F") and u.get("fp") == "FY"]
        pool = annual or units
        if pool:
            return max(pool, key=lambda u: u.get("end", "")).get("val")
    return None


def _millions(x):
    if x is None:
        return None
    try:
        return round(float(x) / 1e6, 1)
    except (TypeError, ValueError):
        return None


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Pre-fill an assumptions skeleton for a ticker.")
    ap.add_argument("ticker")
    ap.add_argument("--financials", action="store_true",
                    help="emit a financials (bank/insurer) skeleton for financial_valuation.py")
    ap.add_argument("--source", choices=("auto", "yfinance", "edgar", "offline"), default="auto")
    ap.add_argument("--out", default=None, help="output path (default: stdout)")
    args = ap.parse_args(argv)

    skel = _financial_skeleton() if args.financials else _fcff_skeleton()
    used = "offline (skeleton only)"
    notes = []

    if args.source != "offline":
        order = {"auto": ("yfinance", "edgar"), "yfinance": ("yfinance",),
                 "edgar": ("edgar",)}[args.source]
        for src in order:
            ok, msg = (_try_yfinance if src == "yfinance" else _try_edgar)(args.ticker, skel, args.financials)
            notes.append(msg)
            if ok:
                used = msg
                break

    banner = (f"# tier=third-party-aggregator | fetched via: {used} | ticker={args.ticker}\n"
              f"# CONFIRM every fetched number against filings; fill every _TODO; then "
              f"delete this scaffolding before running the engine.\n")
    sys.stderr.write(banner)
    for n in notes:
        sys.stderr.write(f"#   source attempt: {n}\n")

    out = json.dumps(skel, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
        sys.stderr.write(f"# wrote {args.out}\n")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
