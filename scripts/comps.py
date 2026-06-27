"""Relative valuation (comparable companies).

The intrinsic DCF asks "what is it worth?"; comps ask "what is the market paying
for similar businesses?" Apply peer-median multiples (EV/Sales, EV/EBITDA, P/E,
PEG) to the target's metrics to triangulate against the DCF. Big gaps between the
two lenses are a signal to investigate -- not to average away.

Input JSON (see templates/comps.example.json):
  {
    "target": {"name","revenue","ebitda","net_income","eps","growth","net_debt","shares"},
    "peers":  [{"name","ev","revenue","ebitda","market_cap","eps","price","growth"}, ...]
  }

    python comps.py ../templates/comps.example.json
"""

from __future__ import annotations

import argparse
import json
import statistics


def _median(xs):
    xs = [x for x in xs if x is not None and x == x]
    return statistics.median(xs) if xs else None


def peer_multiples(peers):
    ev_sales, ev_ebitda, pe, peg = [], [], [], []
    for p in peers:
        ev, rev, ebitda = p.get("ev"), p.get("revenue"), p.get("ebitda")
        mcap, eps, price = p.get("market_cap"), p.get("eps"), p.get("price")
        growth = p.get("growth")
        if ev is not None and rev:        # rev falsy (0/None) -> would divide by zero
            ev_sales.append(ev / rev)
        if ev is not None and ebitda:     # ebitda falsy -> would divide by zero
            ev_ebitda.append(ev / ebitda)
        pe_val = None
        if price and eps and eps > 0:
            pe_val = price / eps
        elif mcap and p.get("net_income") and p["net_income"] > 0:
            pe_val = mcap / p["net_income"]
        if pe_val is not None and pe_val > 0:
            pe.append(pe_val)
            if growth and growth > 0:
                peg.append(pe_val / (growth * 100))
    return {
        "EV/Sales": _median(ev_sales),
        "EV/EBITDA": _median(ev_ebitda),
        "P/E": _median(pe),
        "PEG": _median(peg),
    }


def implied_values(target, mult):
    """Return implied equity value per share by each multiple."""
    shares = target["shares"]
    net_debt = target.get("net_debt", 0.0)
    out = {}
    if mult["EV/Sales"] and target.get("revenue"):
        ev = mult["EV/Sales"] * target["revenue"]
        out["EV/Sales"] = (ev - net_debt) / shares
    if mult["EV/EBITDA"] and target.get("ebitda"):
        ev = mult["EV/EBITDA"] * target["ebitda"]
        out["EV/EBITDA"] = (ev - net_debt) / shares
    if mult["P/E"] and target.get("eps"):
        out["P/E"] = mult["P/E"] * target["eps"]
    if mult["PEG"] and target.get("eps") and target.get("growth"):
        implied_pe = mult["PEG"] * (target["growth"] * 100)
        out["PEG"] = implied_pe * target["eps"]
    return out


def render(target, mult, implied, price=None) -> str:
    lines = [f"Relative valuation: {target['name']}", "=" * 56,
             "Peer-median multiples:"]
    for k, v in mult.items():
        lines.append(f"  {k:<10}: {v:>8.2f}" if v is not None else f"  {k:<10}:      n/a")
    lines += ["", "Implied equity value per share (peer median applied to target):"]
    vals = []
    for k, v in implied.items():
        vals.append(v)
        tag = ""
        if price:
            tag = "  (price implies cheaper)" if v >= price else "  (price implies richer)"
        lines.append(f"  {k:<10}: {v:>10.2f}{tag}")
    if vals:
        lines += ["", f"Range: {min(vals):.2f} - {max(vals):.2f}   "
                      f"Median: {statistics.median(vals):.2f}"]
    if price:
        lines.append(f"Market price: {price:.2f}")
    lines += ["", "Note: comps inherit the market's mood -- if the whole peer set is",
              "richly priced, comps will look 'fair' even when intrinsically expensive.",
              "Always read comps ALONGSIDE the intrinsic DCF, never instead of it."]
    return "\n".join(lines)


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Comparable-company relative valuation.")
    ap.add_argument("comps_json")
    ap.add_argument("--price", type=float, default=None)
    ap.add_argument("--json", action="store_true",
                    help="emit peer multiples + implied values as JSON (for charts.py)")
    args = ap.parse_args(argv)
    with open(args.comps_json, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    target = data["target"]
    mult = peer_multiples(data["peers"])
    implied = implied_values(target, mult)
    price = args.price if args.price is not None else target.get("price")
    if args.json:
        vals = [v for v in implied.values() if v is not None]
        print(json.dumps({
            "target": target.get("name"),
            "price": price,
            "multiples": mult,
            "implied": implied,
            "range": ({"min": min(vals), "max": max(vals),
                       "median": statistics.median(vals)} if vals else None),
        }, indent=2))
        return 0
    print(render(target, mult, implied, price=price))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
