"""Chart-selection agent: determines which charts a ticker needs based on its
company archetype and lifecycle phase.

Baseline rules encode Damodaran's lifecycle framework; narrative adjustments
apply story-driven overrides from the classification JSON before a final
data-readiness check confirms which chart source files exist on disk.

Usage:
    python select_charts.py TICKER --data-dir path/to/data --json
    python select_charts.py TICKER --data-dir path/to/data --manifest path/to/output.json
    python select_charts.py xpev --data-dir data --classification data/xpev/xpev_classification.json --json --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# All chart kinds referenced by the baseline rules
# ---------------------------------------------------------------------------
ALL_CHART_KINDS: tuple[str, ...] = (
    "montecarlo",
    "breakeven",
    "terminal",
    "price_vs_value",
    "football",
    "tornado",
    "scenarios",
    "revenue_traj",
    "roic_spread",
    "waterfall",
    "capex_cycle",
    "risk_matrix",
)

# ---------------------------------------------------------------------------
# Chart kind → candidate data file stems (without ticker prefix)
# ---------------------------------------------------------------------------
CHART_DATA_MAP: dict[str, tuple[str, ...]] = {
    "montecarlo": ("{ticker}_mc.json",),
    "breakeven": ("{ticker}_breakeven.json",),
    "football": ("{ticker}_football.json",),
    "tornado": ("{ticker}_tornado.json",),
    "terminal": ("{ticker}_dcf.json",),
    "revenue_traj": ("{ticker}_dcf.json",),
    "roic_spread": ("{ticker}_roic.json", "{ticker}_dcf.json"),
    "scenarios": ("{ticker}_scenarios.json",),
    "price_vs_value": ("{ticker}_mc.json",),
    "waterfall": ("{ticker}_waterfall.json",),
    "capex_cycle": ("{ticker}_capex.json",),
    "risk_matrix": ("{ticker}_risks.json",),
}

# ---------------------------------------------------------------------------
# Baseline rules table
#
# Each archetype maps to three buckets: required, optional, skip.
# All category names stay in-sync with ALL_CHART_KINDS above.
# ---------------------------------------------------------------------------
BASELINE_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    "young_growth": {
        "required": ("montecarlo", "breakeven", "terminal", "price_vs_value"),
        "optional": ("football", "tornado", "scenarios", "revenue_traj"),
        "skip": ("roic_spread", "waterfall", "capex_cycle", "risk_matrix"),
    },
    "high_growth": {
        "required": ("revenue_traj", "tornado", "terminal", "price_vs_value"),
        "optional": ("montecarlo", "football", "breakeven", "scenarios", "waterfall"),
        "skip": ("roic_spread", "capex_cycle", "risk_matrix"),
    },
    "mature": {
        "required": ("tornado", "revenue_traj", "roic_spread", "waterfall", "terminal"),
        "optional": ("montecarlo", "scenarios", "football", "price_vs_value"),
        "skip": ("breakeven", "capex_cycle", "risk_matrix"),
    },
    "cyclical": {
        "required": ("montecarlo", "tornado", "breakeven", "capex_cycle"),
        "optional": ("football", "scenarios", "risk_matrix", "revenue_traj", "price_vs_value"),
        "skip": ("roic_spread", "terminal", "waterfall"),
    },
    "financial": {
        "required": ("roic_spread", "scenarios", "tornado", "risk_matrix"),
        "optional": ("montecarlo", "price_vs_value", "revenue_traj"),
        "skip": ("breakeven", "capex_cycle", "football", "terminal", "waterfall"),
    },
    "declining": {
        "required": ("breakeven", "waterfall", "terminal"),
        "optional": ("risk_matrix", "tornado", "price_vs_value", "scenarios"),
        "skip": (
            "roic_spread",
            "capex_cycle",
            "football",
            "montecarlo",
            "revenue_traj",
        ),
    },
}

# ── Module-load validation: every archetype must cover all 12 chart kinds ──
_all_kinds = frozenset(ALL_CHART_KINDS)
for _arch, _buckets in BASELINE_RULES.items():
    _covered = frozenset(_buckets["required"]) | frozenset(_buckets["optional"]) | frozenset(_buckets["skip"])
    _missing = _all_kinds - _covered
    _extra = _covered - _all_kinds
    assert not _missing, f"BASELINE_RULES[{_arch!r}] missing charts: {sorted(_missing)}"
    assert not _extra, f"BASELINE_RULES[{_arch!r}] unknown charts: {sorted(_extra)}"

# ---------------------------------------------------------------------------
# Archetype alias resolution — short labels from classification JSON map to
# the canonical BASELINE_RULES keys.
# ---------------------------------------------------------------------------
ARCHETYPE_ALIASES: dict[str, str] = {
    "young": "young_growth",
    "young_growth": "young_growth",
    "high": "high_growth",
    "high_growth": "high_growth",
    "mature": "mature",
    "cyclical": "cyclical",
    "financial": "financial",
    "declining": "declining",
    "default": "mature",  # standard FCFF frame → mature behaviour
}

# ---------------------------------------------------------------------------
# Narrative override rules
#
# Each tuple: (keyword_tuple, chart, source_bucket, destination_bucket)
#   source_bucket / destination_bucket ∈ {"skip", "optional", "required"}
# ---------------------------------------------------------------------------
NARRATIVE_OVERRIDES: tuple[tuple[tuple[str, ...], str, str, str], ...] = (
    # Cash burn / runway / liquidity — capital-cycle chart becomes relevant
    (("cash burn", "runway", "liquidity"), "capex_cycle", "skip", "optional"),
    # Competitive dynamics / market share — peer comparison becomes essential
    (("competitive", "market share"), "football", "optional", "required"),
    # Price war / margin pressure — breakeven analysis becomes essential.
    # Two rules cover the common starting positions: skip (mature/declining
    # baseline) → optional, and optional (young/high growth baseline) → required.
    (("price war", "price competition", "margin compression", "margin pressure",
      "margin erosion", "ASP decline"), "breakeven", "skip", "optional"),
    (("price war", "price competition", "margin compression", "margin pressure",
      "margin erosion", "ASP decline"), "breakeven", "optional", "required"),
    # Dilution / SBC — waterfall bridge clarifies equity-value drivers
    (("dilution", "SBC"), "waterfall", "skip", "optional"),
    # Macro / commodity cycle — capital-cycle context becomes relevant.
    # Uses "cyclical" and "business cycle" rather than bare "cycle" to avoid
    # matching "lifecycle" in industry-lifecycle discussions.
    (("macro", "cyclical", "commodity", "business cycle"), "capex_cycle", "skip", "optional"),
    # Terminal value / perpetuity dominant — terminal-dependency chart becomes essential
    (("terminal value", "perpetuity"), "terminal", "optional", "required"),
)

# ---------------------------------------------------------------------------
# Frozen data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SkippedChart:
    """One chart excluded from generation, with rationale."""

    chart: str
    reason: str
    requires_data: tuple[str, ...]

    def to_dict(self) -> dict:
        """Convert to JSON-serialisable dict."""
        return {
            "chart": self.chart,
            "reason": self.reason,
            "requires_data": list(self.requires_data),
        }


@dataclass(frozen=True)
class SelectResult:
    """Complete chart-selection result for one ticker."""

    ticker: str
    archetype: str
    lifecycle_phase: str
    required: tuple[str, ...]
    optional: tuple[str, ...]
    skipped: tuple[SkippedChart, ...]
    data_ready: tuple[str, ...]
    data_missing: tuple[str, ...]

    def to_dict(self) -> dict:
        """Convert to JSON-serialisable dict matching the output schema."""
        return {
            "ticker": self.ticker,
            "archetype": self.archetype,
            "lifecycle_phase": self.lifecycle_phase,
            "required": list(self.required),
            "optional": list(self.optional),
            "skipped": [s.to_dict() for s in self.skipped],
            "data_ready": list(self.data_ready),
            "data_missing": list(self.data_missing),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_archetype(raw: str) -> str:
    """Normalise a short-form archetype label to a canonical BASELINE_RULES key.

    >>> _resolve_archetype("young")
    'young_growth'
    >>> _resolve_archetype("high_growth")
    'high_growth'
    """
    if not raw or not raw.strip():
        raise ValueError(
            "Classification JSON is missing or has an empty 'archetype' field. "
            "Cannot determine chart selection baseline."
        )
    key = raw.strip().lower().replace("-", "_")
    if key in ARCHETYPE_ALIASES:
        return ARCHETYPE_ALIASES[key]
    raise ValueError(
        f"Unknown archetype '{raw}'. Expected one of: "
        f"{', '.join(sorted(set(ARCHETYPE_ALIASES.values())))}"
    )


def _requires_data_for_chart(chart: str, ticker: str) -> tuple[str, ...]:
    """Return the concrete filenames this chart needs at generation time."""
    candidates = CHART_DATA_MAP.get(chart, ())
    return tuple(fn.format(ticker=ticker) for fn in candidates)


# ---------------------------------------------------------------------------
# Narrative adjustment engine
# ---------------------------------------------------------------------------


def _build_narrative_text(classification: dict) -> str:
    """Concatenate narrative_emphasis + special_checks into a searchable string.

    Both fields live inside the classification JSON; this function flattens
    them into a single lowercased blob so keyword matching is simple.
    """
    parts: list[str] = []
    emphasis = classification.get("narrative_emphasis", "")
    if emphasis:
        parts.append(str(emphasis))
    downstream = classification.get("downstream_consequences")
    if isinstance(downstream, dict):
        special_checks = downstream.get("special_checks", [])
        if isinstance(special_checks, list):
            for item in special_checks:
                parts.append(str(item))
    return " ".join(parts).lower()


def _narrative_adjustments(
    classification: dict,
    required: set[str],
    optional: set[str],
    skipped: dict[str, SkippedChart],
) -> tuple[set[str], set[str], dict[str, SkippedChart]]:
    """Apply keyword-driven story overrides to chart buckets.

    Scans the narrative text for trigger keywords and promotes charts between
    buckets (skip → optional, optional → required).  Every change is logged
    with a reason.  The function never mutates its inputs — it builds and
    returns new collections.

    Parameters
    ----------
    classification : dict
        Full classification JSON payload (archetype, narrative_emphasis, etc.).
    required : set[str]
        Chart kinds currently required per baseline rules.
    optional : set[str]
        Chart kinds currently optional per baseline rules.
    skipped : dict[str, SkippedChart]
        Chart kinds currently skipped per baseline rules, keyed by chart kind.

    Returns
    -------
    (required, optional, skipped)
        Updated buckets after narrative overrides have been applied.
    """
    text = _build_narrative_text(classification)
    new_required = set(required)
    new_optional = set(optional)
    new_skipped = dict(skipped)

    archetype_label = classification.get("archetype", "?")

    for keywords, chart, from_bucket, to_bucket in NARRATIVE_OVERRIDES:
        # Locate the first matching keyword (if any)
        matched_keyword = next((kw for kw in keywords if kw in text), None)
        if matched_keyword is None:
            continue

        # --- Promote: skip → optional ---------------------------------------
        if from_bucket == "skip" and to_bucket == "optional":
            if chart in new_skipped:
                del new_skipped[chart]
                new_optional.add(chart)
                logger.info(
                    "Narrative override: promoted '%s' from skip to optional "
                    "(keyword: '%s', archetype: %s)",
                    chart,
                    matched_keyword,
                    archetype_label,
                )

        # --- Promote: skip → required (two-step promotion) ------------------
        elif from_bucket == "skip" and to_bucket == "required":
            if chart in new_skipped:
                del new_skipped[chart]
                new_required.add(chart)
                logger.info(
                    "Narrative override: promoted '%s' from skip to required "
                    "(keyword: '%s', archetype: %s)",
                    chart,
                    matched_keyword,
                    archetype_label,
                )

        # --- Promote: optional → required -----------------------------------
        elif from_bucket == "optional" and to_bucket == "required":
            if chart in new_optional:
                new_optional.discard(chart)
                new_required.add(chart)
                logger.info(
                    "Narrative override: promoted '%s' from optional to required "
                    "(keyword: '%s', archetype: %s)",
                    chart,
                    matched_keyword,
                    archetype_label,
                )
            elif chart in new_required:
                # Already required — no change needed.
                pass
            else:
                logger.info(
                    "Narrative override: '%s' not in optional bucket "
                    "(currently in %s) — skipping promotion to required "
                    "(keyword: '%s', archetype: %s)",
                    chart,
                    "skip" if chart in new_skipped else "unknown",
                    matched_keyword,
                    archetype_label,
                )

        # --- Silently skip unexpected directions ----------------------------
        else:
            logger.debug(
                "Narrative override: no handler for %s → %s (chart '%s')",
                from_bucket,
                to_bucket,
                chart,
            )

    return new_required, new_optional, new_skipped


# ---------------------------------------------------------------------------
# Data readiness check
# ---------------------------------------------------------------------------


def _check_data(
    data_dir: str,
    ticker: str,
    chart_stems: set[str],
) -> tuple[set[str], set[str]]:
    """Verify which chart data files exist on disk.

    For each chart in *chart_stems*, resolves the expected data file(s) via
    ``CHART_DATA_MAP`` and checks whether at least one candidate exists inside
    ``{data_dir}/{ticker}/``.

    Parameters
    ----------
    data_dir : str
        Parent data directory (e.g. ``D:/equity-research/data/``).
    ticker : str
        Ticker symbol used as filename prefix and subdirectory name.
    chart_stems : set[str]
        Chart kinds to check (e.g. ``{"montecarlo", "breakeven"}``).

    Returns
    -------
    (data_ready, data_missing)
        Chart kinds with at least one data file on disk, and those without.
    """
    ticker_dir = Path(data_dir).resolve() / ticker
    if not ticker_dir.is_dir():
        logger.warning("Ticker data directory not found: %s", ticker_dir)
        return set(), set(chart_stems)  # all missing

    data_ready: set[str] = set()
    data_missing: set[str] = set()

    for chart in chart_stems:
        candidates = CHART_DATA_MAP.get(chart, ())
        filenames = [fn.format(ticker=ticker) for fn in candidates]
        if any((ticker_dir / fn).is_file() for fn in filenames):
            data_ready.add(chart)
        else:
            data_missing.add(chart)

    return data_ready, data_missing


# ---------------------------------------------------------------------------
# Main selection API
# ---------------------------------------------------------------------------


def select(
    ticker: str,
    data_dir: str,
    classification_path: Optional[str] = None,
) -> SelectResult:
    """Determine which charts a ticker needs.

    Pipeline
    --------
    1. Load (or auto-derive) the classification JSON.
    2. Resolve the canonical archetype from the raw label.
    3. Apply baseline chart rules → required / optional / skipped.
    4. Apply narrative (story-driven) adjustments.
    5. Check data readiness for required + optional charts.

    Parameters
    ----------
    ticker : str
        Ticker symbol, lowercased for filesystem paths (e.g. ``"xpev"``).
    data_dir : str
        Parent data directory — files are expected in ``{data_dir}/{ticker}/``.
    classification_path : str, optional
        Explicit path to the classification JSON.  When ``None``, the function
        auto-derives ``{data_dir}/{ticker}/{ticker}_classification.json``.

    Returns
    -------
    SelectResult
        Frozen result with archetype, lifecycle phase, chart buckets, and
        data-readiness split.
    """
    # ---- 1. Load classification --------------------------------------------
    if classification_path is None:
        classification_path = str(
            Path(data_dir) / ticker / f"{ticker}_classification.json"
        )

    cls_path = Path(classification_path)
    if not cls_path.is_file():
        raise FileNotFoundError(
            f"Classification file not found: {cls_path}\n"
            f"  Run the classification pipeline first to generate it, or pass "
            f"  --classification to specify an alternate path."
        )

    with open(str(cls_path), "r", encoding="utf-8") as fh:
        classification = json.load(fh)

    # ---- 2. Resolve archetype ----------------------------------------------
    raw_archetype = classification.get("archetype", "")
    canonical = _resolve_archetype(raw_archetype)
    lifecycle_phase = classification.get("lifecycle_phase", canonical)

    # ---- 3. Apply baseline rules -------------------------------------------
    baseline = BASELINE_RULES.get(canonical)
    if baseline is None:
        raise ValueError(
            f"No baseline rules for archetype '{canonical}' "
            f"(resolved from '{raw_archetype}')."
        )

    required = set(baseline["required"])
    optional = set(baseline["optional"])
    skipped: dict[str, SkippedChart] = {
        chart: SkippedChart(
            chart=chart,
            reason=f"Baseline rule: skipped for {canonical} archetype",
            requires_data=_requires_data_for_chart(chart, ticker),
        )
        for chart in baseline["skip"]
    }

    # ---- 4. Apply narrative adjustments ------------------------------------
    required, optional, skipped = _narrative_adjustments(
        classification, required, optional, skipped
    )

    # ---- 5. Data readiness check -------------------------------------------
    all_to_check = required | optional
    data_ready, data_missing = _check_data(data_dir, ticker, all_to_check)

    # ---- 6. Assemble result ------------------------------------------------
    return SelectResult(
        ticker=ticker,
        archetype=canonical,
        lifecycle_phase=lifecycle_phase,
        required=tuple(sorted(required)),
        optional=tuple(sorted(optional)),
        skipped=tuple(skipped[chart] for chart in sorted(skipped)),
        data_ready=tuple(sorted(data_ready)),
        data_missing=tuple(sorted(data_missing)),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the CLI entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Chart-selection agent: determine which charts a ticker needs "
            "based on archetype, lifecycle phase, and narrative story."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python select_charts.py xpev --data-dir data --json
  python select_charts.py MU --data-dir data --manifest charts.json
  python select_charts.py BYD --data-dir data --classification data/byd/byd_classification.json --json --verbose
""",
    )
    parser.add_argument(
        "ticker",
        help="Ticker symbol (lowercase for filesystem paths).",
    )
    parser.add_argument(
        "--data-dir",
        required=True,
        help=(
            "Parent data directory.  Ticker files are expected in "
            "<data-dir>/<ticker>/."
        ),
    )
    parser.add_argument(
        "--classification",
        dest="classification_path",
        default=None,
        help=(
            "Path to classification JSON.  Default: "
            "<data-dir>/<ticker>/<ticker>_classification.json"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print result as JSON to stdout.",
    )
    parser.add_argument(
        "--manifest",
        dest="manifest_path",
        default=None,
        help="Write result JSON to this file path.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable INFO-level logging to stderr (narrative override log).",
    )
    return parser


def _main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point.  Returns an exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s: %(message)s",
            stream=sys.stderr,
        )

    try:
        result = select(
            ticker=args.ticker,
            data_dir=args.data_dir,
            classification_path=args.classification_path,
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    output = result.to_dict()

    if args.manifest_path:
        with open(args.manifest_path, "w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"Wrote: {args.manifest_path}", file=sys.stderr)

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))

    # If neither --json nor --manifest was passed, print a summary to stderr
    # and JSON to stdout as a reasonable default.
    if not args.json and not args.manifest_path:
        print(json.dumps(output, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
