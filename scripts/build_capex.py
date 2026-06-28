"""Build capex.json -- industry capacity-cycle data for DRAM + NAND memory.

Produces a multi-year view of demand growth, capacity additions, utilization rates,
and cycle-phase classifications, plus per-producer capex and market-share data.
All values are industry estimates sourced from TrendForce and Goldman Sachs.

    python build_capex.py
    python build_capex.py --output capex.json
"""

from __future__ import annotations

import argparse
import json
import sys

HARDCODED_CAPEX = {
    "industry": "DRAM + NAND Memory",
    "current_cycle_phase": "late-expansion",
    "years": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028],
    "demand_growth_pct": [22, -5, 15, 20, -8, -20, 10, 30, 55, 25, 10],
    "capacity_additions_pct": [10, 15, 5, 8, 20, 5, 3, 8, 25, 30, 25],
    "utilization_pct": [92, 78, 85, 95, 82, 65, 80, 95, 98, 90, 75],
    "cycle_phase": [
        {"year": 2018, "phase": "peak"},
        {"year": 2019, "phase": "downturn"},
        {"year": 2020, "phase": "trough"},
        {"year": 2021, "phase": "recovery"},
        {"year": 2022, "phase": "peak"},
        {"year": 2023, "phase": "downturn"},
        {"year": 2024, "phase": "recovery"},
        {"year": 2025, "phase": "expansion"},
        {"year": 2026, "phase": "peak"},
        {"year": 2027, "phase": "peak"},
        {"year": 2028, "phase": "downturn-forecast"},
    ],
    "producers": [
        {
            "name": "Samsung",
            "capex_bn": [15, 10, 8, 12, 18, 10, 12, 18, 28, 30, 25],
            "market_share_pct": [45, 44, 43, 42, 40, 39, 38, 38, 37, 36, 35],
        },
        {
            "name": "SK Hynix",
            "capex_bn": [10, 7, 6, 9, 14, 8, 10, 15, 25, 27, 22],
            "market_share_pct": [28, 28, 29, 29, 30, 30, 29, 29, 28, 28, 27],
        },
        {
            "name": "Micron",
            "capex_bn": [8, 5, 5, 7, 12, 7, 8, 14, 27, 28, 24],
            "market_share_pct": [20, 20, 20, 21, 22, 23, 22, 22, 23, 24, 24],
        },
        {
            "name": "CXMT",
            "capex_bn": [1, 1, 2, 3, 4, 3, 4, 6, 10, 12, 15],
            "market_share_pct": [1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 11],
        },
    ],
}


def _validate(data: dict) -> list[str]:
    """Check array lengths are consistent across all parallel lists."""
    issues = []
    n = len(data["years"])
    for key in ("demand_growth_pct", "capacity_additions_pct", "utilization_pct"):
        if len(data[key]) != n:
            issues.append(f"'{key}' length {len(data[key])} != years length {n}")
    for p in data["producers"]:
        for key in ("capex_bn", "market_share_pct"):
            if len(p[key]) != n:
                issues.append(
                    f"{p['name']}.{key} length {len(p[key])} != years length {n}"
                )
    return issues


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Build capex.json -- industry capacity-cycle data."
    )
    ap.add_argument(
        "--output",
        default=None,
        help="write JSON to this file instead of stdout",
    )
    ap.add_argument(
        "--validate",
        action="store_true",
        help="validate internal consistency of the hardcoded data",
    )
    args = ap.parse_args(argv)

    data = HARDCODED_CAPEX

    if args.validate:
        issues = _validate(data)
        if issues:
            for i in issues:
                print(f"VALIDATION ERROR: {i}", file=sys.stderr)
            return 1
        print("Validation passed: all array lengths consistent.")
        if args.output is None:
            return 0  # --validate alone: report only, no JSON dump

    text = json.dumps(data, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.write("\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
