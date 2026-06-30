"""Build industry memory JSON from valuation outputs.

Extracts industry-level benchmarks and competitive context from individual
company DCF valuations, persisting them as structured memory files so
subsequent valuations in the same sector can leverage prior findings.

    python build_industry_memory.py \
        --assumptions data/mu/assumptions.json \
        --dcf-result data/mu/dcf_result.json \
        --sector semiconductors
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union


# ── Path resolution ────────────────────────────────────────────────────────

def _skill_dir() -> Path:
    """Return the absolute path to the equity-research-analyst skill root."""
    return Path(__file__).resolve().parent.parent


def _memory_dir() -> Path:
    """Return the industry_insights directory (created on demand)."""
    return _skill_dir() / "industry_insights"


# ── IndustryMemory frozen dataclass ─────────────────────────────────────────

@dataclass(frozen=True)
class IndustryMemory:
    """Frozen snapshot of industry-level valuation benchmarks and context.

    Captures lifecycle assessment, competitive landscape, profitability and
    reinvestment benchmarks, and valuation snapshots for a sector.  Immutable
    by design so memories can be passed around and merged without hidden
    mutation.

    Fields:
        sector: Industry sector name (e.g. "semiconductors", "automotive").
        last_updated: ISO-8601 UTC timestamp of the most recent update.
        lifecycle_stage: Inferred lifecycle stage label.
        lifecycle_signals: Tuple of signal strings that led to the stage
            classification (e.g. "double_digit_growth", "capital_intensive").
        key_competitors: Tuple of competitor company identifiers.
        margin_benchmarks: Dict of operating-margin benchmarks (base, target,
            convergence horizon, growth rates).
        s2c_benchmarks: Dict of sales-to-capital / reinvestment-efficiency
            benchmarks.
        growth_benchmarks: Dict of revenue-growth benchmarks (avg growth,
            growth-rate tuple, horizon, terminal growth, cost of capital).
        valuation_snapshots: Tuple of per-company valuation dicts, each
            containing company, date, value_per_share, operating_asset_value,
            equity_value, terminal_revenue, terminal_pct_of_value.
    """

    sector: str
    last_updated: str
    lifecycle_stage: str
    lifecycle_signals: tuple
    key_competitors: tuple
    margin_benchmarks: dict
    s2c_benchmarks: dict
    growth_benchmarks: dict
    valuation_snapshots: tuple

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dictionary."""
        return asdict(self)

    def to_json(self, path: str) -> None:
        """Write memory to a JSON file, creating parent directories."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, ensure_ascii=False)
            fh.write("\n")


# ── Deserialization ─────────────────────────────────────────────────────────

def _from_dict(raw: dict) -> IndustryMemory:
    """Reconstruct an IndustryMemory from a deserialized dict.

    Converts JSON lists back to tuples for the frozen-dataclass fields.
    """
    return IndustryMemory(
        sector=raw["sector"],
        last_updated=raw["last_updated"],
        lifecycle_stage=raw["lifecycle_stage"],
        lifecycle_signals=tuple(raw.get("lifecycle_signals", [])),
        key_competitors=tuple(raw.get("key_competitors", [])),
        margin_benchmarks=raw.get("margin_benchmarks", {}),
        s2c_benchmarks=raw.get("s2c_benchmarks", {}),
        growth_benchmarks=raw.get("growth_benchmarks", {}),
        valuation_snapshots=tuple(raw.get("valuation_snapshots", [])),
    )


# ── Lifecycle-inference helpers ─────────────────────────────────────────────

def _infer_lifecycle_stage(
    growth_rates: tuple,
    base_margin: float,
    target_margin: float,
    margin_convergence_year: int,
    horizon: int,
) -> str:
    """Infer lifecycle stage from growth trajectory and margin profile.

    Decision tree (in priority order):
      * >20 % avg growth + expanding margins  -> "hypergrowth"
      * >15 % avg growth                       -> "growth"
      * 5-15 % avg growth, converging margins  -> "mature_growth"
      * 2-5 % avg growth, stable margins       -> "mature"
      * Low/negative margins with improvement  -> "turnaround"
      * <=2 % avg growth, no margin expansion  -> "declining"
      * Fallback                                -> "mature"
    """
    avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0.0
    margin_gap = target_margin - base_margin

    if avg_growth > 0.20 and margin_gap > 0.05:
        return "hypergrowth"
    if avg_growth > 0.15:
        return "growth"
    if avg_growth > 0.05:
        return "mature_growth"
    if base_margin < 0.05 and target_margin > 0.10:
        return "turnaround"
    if avg_growth > 0.02:
        return "mature"
    if avg_growth <= 0.02 and margin_gap <= 0.02:
        return "declining"
    return "mature"


def _infer_lifecycle_signals(inp) -> tuple:
    """Derive textual lifecycle signals from a ValuationInputs object.

    Signals encode key characteristics observable from the assumptions:
      * revenue_growth_exceeds_20pct / double_digit_growth / single_digit_growth
      * significant_margin_expansion_expected / moderate_margin_improvement
      * capital_intensive / asset_light
      * high_risk_premium
      * above_average_terminal_growth
    """
    signals: list[str] = []
    avg_growth = (
        sum(inp.revenue_growth) / len(inp.revenue_growth)
        if inp.revenue_growth
        else 0.0
    )

    if avg_growth > 0.20:
        signals.append("revenue_growth_exceeds_20pct")
    elif avg_growth > 0.10:
        signals.append("double_digit_growth")
    else:
        signals.append("single_digit_growth")

    margin_gap = inp.target_operating_margin - inp.base_operating_margin
    if margin_gap > 0.10:
        signals.append("significant_margin_expansion_expected")
    elif margin_gap > 0.03:
        signals.append("moderate_margin_improvement")

    if inp.sales_to_capital < 1.0:
        signals.append("capital_intensive")
    elif inp.sales_to_capital > 3.0:
        signals.append("asset_light")

    if inp.cost_of_capital_initial > 0.12:
        signals.append("high_risk_premium")

    if inp.terminal_growth > 0.03:
        signals.append("above_average_terminal_growth")

    return tuple(signals)


# ── Benchmark extractors ────────────────────────────────────────────────────

def _margin_benchmarks(inp) -> dict:
    """Extract operating-margin benchmarks from ValuationInputs."""
    return {
        "base_operating_margin": round(inp.base_operating_margin, 4),
        "target_operating_margin": round(inp.target_operating_margin, 4),
        "margin_convergence_years": inp.margin_convergence_year,
    }


def _s2c_benchmarks(inp) -> dict:
    """Extract sales-to-capital (reinvestment efficiency) benchmarks."""
    s2c = inp.sales_to_capital
    return {
        "sales_to_capital": round(s2c, 4),
        "implied_reinvestment_rate": (
            round(1.0 / s2c, 4) if s2c > 0 else None
        ),
    }


def _growth_benchmarks(inp) -> dict:
    """Extract revenue-growth and cost-of-capital benchmarks."""
    avg_growth = (
        sum(inp.revenue_growth) / len(inp.revenue_growth)
        if inp.revenue_growth
        else 0.0
    )
    return {
        "avg_revenue_growth": round(avg_growth, 4),
        "growth_rates": tuple(round(g, 4) for g in inp.revenue_growth),
        "forecast_horizon": inp.horizon,
        "terminal_growth": round(inp.terminal_growth, 4),
        "initial_cost_of_capital": round(inp.cost_of_capital_initial, 4),
        "terminal_cost_of_capital": round(inp.cost_of_capital_terminal, 4),
    }


def _build_snapshot(inp, dcf_data: dict | None) -> dict:
    """Build a per-company valuation snapshot dict.

    When *dcf_data* is None (DCF not yet run), valuation fields are set to
    ``None`` so the memory can still capture industry-level benchmarks.
    """
    if dcf_data is None:
        dcf_data = {}
    return {
        "company": inp.company,
        "valuation_date": inp.valuation_date,
        "value_per_share": round(dcf_data["value_per_share"], 2) if "value_per_share" in dcf_data else None,
        "operating_asset_value": round(dcf_data["operating_asset_value"], 2) if "operating_asset_value" in dcf_data else None,
        "equity_value": round(dcf_data["equity_value"], 2) if "equity_value" in dcf_data else None,
        "terminal_revenue": round(dcf_data["terminal_revenue"], 2) if "terminal_revenue" in dcf_data else None,
        "terminal_pct_of_value": round(dcf_data["terminal_pct_of_value"], 4) if "terminal_pct_of_value" in dcf_data else None,
    }


# ── Core functions ──────────────────────────────────────────────────────────

def extract_findings(
    assumptions_path: str,
    dcf_result: Union[str, dict, None],
    sector: str,
) -> IndustryMemory:
    """Load valuation inputs and a DCF result, then extract industry findings.

    Args:
        assumptions_path: Path to the assumptions JSON file (loadable by
            ``valuation_inputs.load_inputs``).
        dcf_result: Either a path to a DCF result JSON file (as emitted by
            ``dcf_valuation.py --json``), a pre-loaded dict, or ``None`` if
            DCF has not yet been run (valuation snapshot fields will be
            ``None``).
        sector: Industry sector name (e.g. ``"semiconductors"``,
            ``"automotive"``).

    Returns:
        An ``IndustryMemory`` populated with extracted benchmarks and an
        initial valuation snapshot.
    """
    # --- load valuation inputs -----------------------------------------------
    try:
        from valuation_inputs import load_inputs
    except ImportError:
        from scripts.valuation_inputs import load_inputs  # type: ignore

    inp = load_inputs(assumptions_path)

    # --- load DCF result (accept path, pre-loaded dict, or None) -------------
    if isinstance(dcf_result, str):
        with open(dcf_result, "r", encoding="utf-8") as fh:
            dcf_data: dict | None = json.load(fh)
    else:
        dcf_data = dcf_result

    # --- infer lifecycle -----------------------------------------------------
    lifecycle_stage = _infer_lifecycle_stage(
        inp.revenue_growth,
        inp.base_operating_margin,
        inp.target_operating_margin,
        inp.margin_convergence_year,
        inp.horizon,
    )
    lifecycle_signals = _infer_lifecycle_signals(inp)

    # --- assemble memory -----------------------------------------------------
    return IndustryMemory(
        sector=sector,
        last_updated=datetime.now(tz=timezone.utc).isoformat(),
        lifecycle_stage=lifecycle_stage,
        lifecycle_signals=lifecycle_signals,
        key_competitors=tuple(),
        margin_benchmarks=_margin_benchmarks(inp),
        s2c_benchmarks=_s2c_benchmarks(inp),
        growth_benchmarks=_growth_benchmarks(inp),
        valuation_snapshots=(_build_snapshot(inp, dcf_data),),
    )


def load_memory(sector: str) -> Optional[IndustryMemory]:
    """Load an existing ``IndustryMemory`` from disk.

    Looks for ``industry_insights/<sector>/memory.json`` relative to the
    equity-research-analyst skill directory.

    Args:
        sector: Industry sector name (lowercase, e.g. ``"semiconductors"``).
            The sector is used as a subdirectory name.

    Returns:
        An ``IndustryMemory`` if the file exists and is valid JSON, or
        ``None`` if the file is missing or cannot be parsed.
    """
    memory_path = _memory_dir() / sector / "memory.json"
    if not memory_path.is_file():
        return None
    try:
        with open(memory_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        return _from_dict(raw)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def merge_memories(
    existing: IndustryMemory,
    new: IndustryMemory,
    new_weight: float = 0.7,
) -> IndustryMemory:
    """Merge an existing ``IndustryMemory`` with a newly extracted one.

    Newer data receives ``new_weight`` (default 0.7); existing data receives
    ``1 - new_weight``.  The merge rules are:

    * **lifecycle_stage**: Use the stage from *new* (most recent company).
    * **lifecycle_signals / key_competitors**: Concatenate and deduplicate.
    * **margin_benchmarks / s2c_benchmarks / growth_benchmarks**: Weighted
      average for numeric values; non-numeric values prefer the newer entry.
    * **valuation_snapshots**: Append — all historical snapshots are kept.
    * **last_updated**: Maximum of the two timestamps.

    Args:
        existing: Previously persisted ``IndustryMemory``.
        new: Freshly extracted ``IndustryMemory``.
        new_weight: Weight assigned to the new memory, in [0, 1].
            Default 0.7.

    Returns:
        A new merged ``IndustryMemory``.  The original inputs are never
        mutated (immutability).
    """
    old_weight = 1.0 - new_weight

    # --- lifecycle_stage: prefer the newer source ---------------------------
    merged_stage = new.lifecycle_stage

    # --- lifecycle_signals: concat + dedup (preserves order) -----------------
    merged_signals = tuple(
        dict.fromkeys(existing.lifecycle_signals + new.lifecycle_signals)
    )

    # --- key_competitors: concat + dedup ------------------------------------
    merged_competitors = tuple(
        dict.fromkeys(existing.key_competitors + new.key_competitors)
    )

    # --- numeric benchmark dicts: weighted average ---------------------------
    merged_margin = _weighted_merge_dict(
        existing.margin_benchmarks, new.margin_benchmarks,
        new_weight, old_weight,
    )
    merged_s2c = _weighted_merge_dict(
        existing.s2c_benchmarks, new.s2c_benchmarks,
        new_weight, old_weight,
    )
    merged_growth = _weighted_merge_dict(
        existing.growth_benchmarks, new.growth_benchmarks,
        new_weight, old_weight,
    )

    # --- valuation_snapshots: keep all ---------------------------------------
    merged_snapshots = existing.valuation_snapshots + new.valuation_snapshots

    # --- last_updated: take the more recent timestamp ------------------------
    merged_updated = max(existing.last_updated, new.last_updated)

    return IndustryMemory(
        sector=new.sector,
        last_updated=merged_updated,
        lifecycle_stage=merged_stage,
        lifecycle_signals=merged_signals,
        key_competitors=merged_competitors,
        margin_benchmarks=merged_margin,
        s2c_benchmarks=merged_s2c,
        growth_benchmarks=merged_growth,
        valuation_snapshots=merged_snapshots,
    )


def _weighted_merge_dict(
    old: dict,
    new: dict,
    new_weight: float,
    old_weight: float,
) -> dict:
    """Merge two benchmark dicts via weighted averaging.

    * Keys in both dicts with *numeric* values: weighted average.
    * Keys in both dicts with *tuple* values: keep the newer tuple.
    * Keys in both dicts with other types: prefer the newer value.
    * Keys unique to one dict: carried forward as-is.

    Returns a new dict — inputs are never mutated.
    """
    merged: dict = {}
    all_keys = set(old) | set(new)
    for key in all_keys:
        old_val = old.get(key)
        new_val = new.get(key)
        if old_val is not None and new_val is not None:
            if isinstance(old_val, (int, float)) and isinstance(
                new_val, (int, float)
            ):
                merged[key] = round(
                    old_val * old_weight + new_val * new_weight, 6
                )
            elif isinstance(old_val, tuple) and isinstance(new_val, tuple):
                merged[key] = new_val
            else:
                merged[key] = new_val
        elif new_val is not None:
            merged[key] = new_val
        else:
            merged[key] = old_val
    return merged


# ── CLI ─────────────────────────────────────────────────────────────────────

def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Build or update industry memory from a DCF valuation run. "
            "Extracts lifecycle signals, margin/reinvestment/growth "
            "benchmarks, and valuation snapshots; merges with existing "
            "sector memory when available."
        ),
    )
    ap.add_argument(
        "--assumptions",
        required=True,
        help="Path to assumptions JSON (e.g. data/mu/assumptions.json).",
    )
    ap.add_argument(
        "--dcf-result",
        required=True,
        help=(
            "Path to DCF result JSON "
            "(as emitted by dcf_valuation.py --json)."
        ),
    )
    ap.add_argument(
        "--sector",
        required=True,
        help=(
            "Industry sector name "
            "(e.g. 'semiconductors', 'automotive')."
        ),
    )
    ap.add_argument(
        "--output",
        default=None,
        help=(
            "Write merged memory JSON to this file. "
            "Defaults to industry_insights/<sector>/memory.json "
            "in the equity-research-analyst skill directory."
        ),
    )
    ap.add_argument(
        "--no-merge",
        action="store_true",
        help=(
            "Skip loading existing memory; write a fresh extract only "
            "(overwrites any existing file at the output path)."
        ),
    )
    args = ap.parse_args(argv)

    # --- extract fresh findings ----------------------------------------------
    try:
        new_memory = extract_findings(
            args.assumptions, args.dcf_result, args.sector,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: File not found — {exc}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        print(
            f"ERROR: Could not parse input data — {exc}",
            file=sys.stderr,
        )
        return 1

    # --- merge with existing (unless --no-merge) -----------------------------
    if not args.no_merge:
        existing = load_memory(args.sector)
        if existing is not None:
            result = merge_memories(existing, new_memory)
        else:
            result = new_memory
    else:
        result = new_memory

    # --- determine output path -----------------------------------------------
    if args.output:
        out_path = args.output
    else:
        out_path = str(_memory_dir() / args.sector / "memory.json")

    result.to_json(out_path)
    print(f"Industry memory written to: {out_path}")
    print(f"  Sector:              {result.sector}")
    print(f"  Lifecycle stage:     {result.lifecycle_stage}")
    print(f"  Lifecycle signals:   {len(result.lifecycle_signals)}")
    print(f"  Key competitors:     {len(result.key_competitors)}")
    print(f"  Valuation snapshots: {len(result.valuation_snapshots)}")
    print(f"  Last updated:        {result.last_updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
