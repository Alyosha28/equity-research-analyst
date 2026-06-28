"""Auto-discover engine JSON outputs and assemble output-manifest.json.

Scans a directory for known valuation-engine JSON files (DCF, Monte Carlo,
breakeven, football field, comps, durability, plus 5 unsourced chart types:
scenarios, history, waterfall, capex, risks). Extracts metadata from the first
viable file, then writes a complete manifest consumed by downstream consumers:

  - /generate-charts   (reads chart_requests to render figures)
  - /write-report      (reads engine_outputs paths for prose integration)
  - /self-audit        (reads manifest to verify completeness)
  - /generate-pdf      (reads chart_requests for vector embeds)

Ten chart types mirror the 10-chart catalog in /generate-charts. Five are
sourced directly from engine scripts; five are unsourced and must be produced by
upstream analysis sub-skills before chart inputs exist. Unsourced charts are
prioritised "optional" with a `produced_by` annotation naming the responsible
sub-skill.

Additionally, this script validates the generate-pdf sub-skill's own file
manifest (SKILL.md Phase 7) to ensure all CSS templates, font assets, and
required support files exist before the PDF pipeline is invoked.

Usage:
    python build_manifest.py --engine-dir engine_outputs/ -o output-manifest.json
    python build_manifest.py -d engine_outputs/ --theme goldman --lang zh-CN
    python build_manifest.py -d engine_outputs/ --ticker 0700.HK --company "Tencent"
    python build_manifest.py -d engine_outputs/ --ticker MU --company "Micron Technology"
    python build_manifest.py --validate-pdf-skill   (checks generate-pdf file structure)
    python build_manifest.py --check-all              (full validation: engines + PDF skill)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date as dt_date
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Discovery configuration -- output slots from valuation engines
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OutputSlot:
    """One slot in the engine_outputs mapping."""

    key: str
    label: str
    filename_patterns: tuple
    json_fields: tuple
    sourced: bool = True
    chart_kind: Optional[str] = None
    chart_title: Optional[str] = None
    produced_by: Optional[str] = None


OUTPUT_SLOTS = (
    # ---- Sourced: engine scripts produce these JSON files (required charts) ----
    OutputSlot(
        key="dcf_result",
        label="DCF intrinsic valuation",
        filename_patterns=("dcf", "dcf_result", "dcf_valuation"),
        json_fields=(
            "value_per_share",
            "operating_asset_value",
            "terminal_pct_of_value",
        ),
        sourced=True,
        chart_kind="terminal",
        chart_title="Terminal Value Dependency -- {ticker}",
    ),
    OutputSlot(
        key="monte_carlo",
        label="Monte Carlo simulation",
        filename_patterns=("mc", "monte_carlo", "montecarlo"),
        json_fields=("values", "percentiles", "mos_band"),
        sourced=True,
        chart_kind="montecarlo",
        chart_title="Intrinsic Value Distribution -- Monte Carlo -- {ticker}",
    ),
    OutputSlot(
        key="breakeven",
        label="Breakeven / what-has-to-be-true analysis",
        filename_patterns=("be", "breakeven", "breakeven_grid"),
        json_fields=("grid", "revenues", "margins"),
        sourced=True,
        chart_kind="breakeven",
        chart_title="Breakeven: What Must Be True -- {ticker}",
    ),
    OutputSlot(
        key="football",
        label="Football field (valuation range comparison)",
        filename_patterns=("ff", "football", "football_field"),
        json_fields=("lenses",),
        sourced=True,
        chart_kind="football",
        chart_title="Valuation Football Field -- {ticker}",
    ),
    OutputSlot(
        key="comps",
        label="Comparable companies / relative valuation",
        filename_patterns=("comp", "comps", "peer"),
        json_fields=("multiples", "implied"),
        sourced=True,
        chart_kind="tornado",
        chart_title="Sensitivity Tornado -- {ticker}",
    ),
    OutputSlot(
        key="durability",
        label="Durability / ROIC-WACC spread analysis",
        filename_patterns=("durability", "roic", "roic_spread", "moat"),
        json_fields=("roic", "wacc", "spread", "competitive_advantage_period"),
        sourced=True,
        chart_kind="roic_spread",
        chart_title="ROIC-WACC Spread -- Durability Assessment -- {ticker}",
    ),
    # ---- Unsourced: analysis sub-skills must produce these (optional charts) ----
    OutputSlot(
        key="scenarios",
        label="Scenario comparison (bull / base / bear)",
        filename_patterns=("scenario", "scenarios"),
        json_fields=("scenarios",),
        sourced=False,
        chart_kind="scenarios",
        chart_title="Scenario Analysis -- {ticker} Value Ranges",
        produced_by="/build-assumptions",
    ),
    OutputSlot(
        key="history",
        label="Price vs intrinsic value history",
        filename_patterns=("history", "price_history", "price_vs_value"),
        json_fields=("dates", "price", "value_low", "value_mid", "value_high"),
        sourced=False,
        chart_kind="price_vs_value",
        chart_title="Price vs. Intrinsic Value -- {ticker}",
        produced_by="/analyze-company",
    ),
    OutputSlot(
        key="waterfall",
        label="Driver waterfall bridge",
        filename_patterns=("waterfall", "value_bridge", "driver_waterfall"),
        json_fields=("steps", "intrinsic_value"),
        sourced=False,
        chart_kind="waterfall",
        chart_title="Value Bridge: Driver Contributions -- {ticker}",
        produced_by="/triangulate",
    ),
    OutputSlot(
        key="capex",
        label="CAPEX cycle chart",
        filename_patterns=("capex", "capex_cycle", "capacity"),
        json_fields=("demand_growth", "capacity_additions", "utilization_rate"),
        sourced=False,
        chart_kind="capex_cycle",
        chart_title="Industry Capacity Cycle -- {ticker}",
        produced_by="/analyze-industry",
    ),
    OutputSlot(
        key="risks",
        label="Risk matrix",
        filename_patterns=("risk", "risks", "risk_matrix"),
        json_fields=("risks",),
        sourced=False,
        chart_kind="risk_matrix",
        chart_title="Risk Matrix -- Probability vs. Value Impact -- {ticker}",
        produced_by="/durability-check",
    ),
)


# ---------------------------------------------------------------------------
# generate-pdf sub-skill file manifest (SKILL.md Phase 7)
# ---------------------------------------------------------------------------

# Relative to the equity-research-analyst skill root
SKILL_ROOT = Path(__file__).resolve().parent.parent  # .../equity-research-analyst/

PDF_SKILL_MANIFEST = {
    "directory": "skills/generate-pdf",
    "required_files": [
        "SKILL.md",
        "scripts/render_pdf.py",
        "templates/professional.css",
        "templates/professional-bw.css",
        "templates/internal.css",
        "templates/cjk-overrides.css",
        "assets/fonts/README.md",
    ],
    "optional_files": [
        "README.md",
        "PDF_FIXES.md",
    ],
    "parent_skill_dependencies": [
        "scripts/charts.py",
        "scripts/report_lint.py",
        "scripts/cjk_font_detection.py",
        "scripts/valuation_inputs.py",
        "scripts/dcf_valuation.py",
    ],
}


# ---------------------------------------------------------------------------
# Metadata extraction helpers
# ---------------------------------------------------------------------------

METADATA_PATHS = ("company", "company_name", "name")
DATE_PATHS = ("valuation_date", "date", "as_of", "as_of_date")
TICKER_PATHS = ("ticker", "symbol")


def _get_nested(d, *keys, default=None):
    """Return the first key that exists in dict *d* and is not None."""
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def _extract_metadata(json_data):
    """Pull ticker, company, valuation_date, lang, and theme from JSON data.

    Scans multiple known key paths so it works across all engine output formats.
    """
    meta = {}
    val = _get_nested(json_data, *METADATA_PATHS)
    if isinstance(val, str) and val.strip():
        meta["company"] = val.strip()
    val = _get_nested(json_data, *DATE_PATHS)
    if isinstance(val, str) and val.strip():
        meta["valuation_date"] = val.strip()
    val = _get_nested(json_data, *TICKER_PATHS)
    if isinstance(val, str) and val.strip():
        meta["ticker"] = val.strip()
    lang_raw = _get_nested(json_data, "lang", "_lang")
    if isinstance(lang_raw, str) and lang_raw.strip():
        meta["lang"] = lang_raw.strip()
    val = _get_nested(json_data, "theme")
    if isinstance(val, str) and val.strip():
        meta["theme"] = val.strip()
    return meta


# ---------------------------------------------------------------------------
# Engine output discovery (2-pass: filename then content)
# ---------------------------------------------------------------------------

def _match_filename(fname_stem_lower: str, slot: OutputSlot) -> bool:
    """True if any filename pattern appears in the lowercased stem."""
    return any(pat in fname_stem_lower for pat in slot.filename_patterns)


def _match_content(json_data: dict, slot: OutputSlot) -> bool:
    """True if enough expected JSON fields are present in the data.

    Requires at least ceil(N/2)+1 of the declared fields to be present
    so a single coincidental field doesn't cause a false-positive match.
    """
    if not slot.json_fields:
        return False
    hits = sum(1 for f in slot.json_fields if f in json_data)
    threshold = max(1, len(slot.json_fields) // 2 + 1)
    return hits >= threshold


def discover_engine_outputs(scan_dir: str):
    """Scan *scan_dir* for engine JSON files and assign them to output slots.

    Two-pass strategy:
      1. Filename matching (fast, preferred).
      2. Content inspection for remaining unassigned files.

    Returns
    -------
    (assignments, metadata) where *assignments* is ``{slot_key: file_path}``
    and *metadata* is a dict of auto-detected fields (ticker, company, etc.).
    """
    scan = Path(scan_dir).resolve()
    if not scan.is_dir():
        raise FileNotFoundError(f"Directory not found: {scan_dir}")

    json_files = sorted(
        p for p in scan.iterdir()
        if p.is_file() and p.suffix.lower() == ".json"
    )

    assignments = {}
    best_meta = {}
    seen_paths = set()

    # Pass 1: filename matching
    for slot in OUTPUT_SLOTS:
        for jp in json_files:
            if str(jp) in seen_paths:
                continue
            if _match_filename(jp.stem.lower(), slot):
                assignments[slot.key] = str(jp)
                seen_paths.add(str(jp))
                break

    # Pass 2: content matching for unassigned files
    for jp in json_files:
        if str(jp) in seen_paths:
            continue
        try:
            with open(jp, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError):
            continue
        for slot in OUTPUT_SLOTS:
            if slot.key in assignments:
                continue
            if _match_content(data, slot):
                assignments[slot.key] = str(jp)
                seen_paths.add(str(jp))
                break
        meta = _extract_metadata(data)
        for k, v in meta.items():
            if v and not best_meta.get(k):
                best_meta[k] = v

    # Collect metadata from filename-matched files (takes priority)
    for slot in OUTPUT_SLOTS:
        if slot.key in assignments:
            jp_path = assignments[slot.key]
            try:
                with open(jp_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except (json.JSONDecodeError, OSError):
                continue
            meta = _extract_metadata(data)
            for k, v in meta.items():
                if v and (not best_meta.get(k)):
                    best_meta[k] = v

    # Enrich: always try to read ticker/symbol from any JSON, even content-matched
    if not best_meta.get("ticker"):
        for jp in json_files:
            try:
                with open(jp, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except (json.JSONDecodeError, OSError):
                continue
            ticker_val = _get_nested(data, *TICKER_PATHS)
            if ticker_val:
                best_meta["ticker"] = str(ticker_val).strip()
                break

    return assignments, best_meta


# ---------------------------------------------------------------------------
# Manifest assembly
# ---------------------------------------------------------------------------

def _format_title(template: str, ticker: str, company: str) -> str:
    """Substitute ``{ticker}`` and ``{company}`` in a title template."""
    return template.format(ticker=ticker, company=company)


def assemble_manifest(
    engine_outputs: dict,
    meta: dict,
    ticker: Optional[str] = None,
    company: Optional[str] = None,
    valuation_date: Optional[str] = None,
    theme: str = "default",
    lang: str = "en-US",
) -> dict:
    """Build the full output-manifest.json dict.

    Resolution order for metadata fields:
      1. Explicit CLI argument (highest priority)
      2. Auto-detected from JSON content
      3. Fallback default

    The manifest declares every chart slot regardless of whether its input
    JSON was found.  Downstream consumers use the ``priority`` field to skip
    optional charts whose input is not yet available.
    """
    resolved_ticker = ticker or meta.get("ticker", "UNKNOWN")
    resolved_company = company or meta.get("company", resolved_ticker)
    resolved_date = valuation_date or meta.get(
        "valuation_date", dt_date.today().isoformat()
    )
    resolved_theme = theme or meta.get("theme", "default")
    resolved_lang = lang or meta.get("lang", "en-US")

    engine_paths = {}
    for slot in OUTPUT_SLOTS:
        if slot.key not in engine_outputs:
            continue
        engine_paths[slot.key] = Path(engine_outputs[slot.key]).name

    chart_requests = []
    missing_optionals = []
    for slot in OUTPUT_SLOTS:
        if slot.chart_kind is None:
            continue
        entry = {
            "kind": slot.chart_kind,
            "title": _format_title(
                slot.chart_title or "", resolved_ticker, resolved_company
            ),
        }
        if slot.sourced:
            entry["priority"] = "required"
        else:
            entry["priority"] = "optional"
            if slot.produced_by:
                entry["produced_by"] = slot.produced_by
                entry["note"] = (
                    f"Input JSON not produced by any valuation engine script. "
                    f"Run {slot.produced_by} to generate the source data for "
                    f"this chart."
                )
            if slot.key not in engine_outputs:
                missing_optionals.append(
                    {
                        "kind": slot.chart_kind,
                        "label": slot.label,
                        "produced_by": slot.produced_by,
                    }
                )
        chart_requests.append(entry)

    manifest = {
        "$schema": "equity-research output-manifest v2",
        "generated_at": dt_date.today().isoformat(),
        "ticker": resolved_ticker,
        "company": resolved_company,
        "valuation_date": resolved_date,
        "theme": resolved_theme,
        "lang": resolved_lang,
        "output_dir": f"figs/{resolved_ticker}",
        "engine_outputs": engine_paths,
        "chart_requests": chart_requests,
    }

    if missing_optionals:
        manifest["missing_optional_inputs"] = missing_optionals

    return manifest


# ---------------------------------------------------------------------------
# generate-pdf sub-skill file structure validation
# ---------------------------------------------------------------------------

def validate_pdf_skill_manifest(skill_root: Optional[Path] = None) -> dict:
    """Validate that all required files exist for the generate-pdf sub-skill.

    Checks:
      - All required files in skills/generate-pdf/ exist
      - Parent-skill dependencies (scripts/*.py) exist
      - Optional files are reported but do not cause failure

    Returns:
        dict with keys: passed (bool), missing_required (list[str]),
        missing_optional (list[str]), missing_deps (list[str]),
        all_checks_pass (bool).
    """
    root = skill_root or SKILL_ROOT

    missing_required = []
    missing_deps = []
    missing_optional = []

    pdf_dir = root / PDF_SKILL_MANIFEST["directory"]

    for rel_path in PDF_SKILL_MANIFEST["required_files"]:
        full_path = pdf_dir / rel_path
        if not full_path.exists():
            missing_required.append(str(full_path))

    for rel_path in PDF_SKILL_MANIFEST["optional_files"]:
        full_path = pdf_dir / rel_path
        if not full_path.exists():
            missing_optional.append(str(full_path))

    for rel_path in PDF_SKILL_MANIFEST["parent_skill_dependencies"]:
        full_path = root / rel_path
        if not full_path.exists():
            missing_deps.append(str(full_path))

    passed = len(missing_required) == 0 and len(missing_deps) == 0

    return {
        "passed": passed,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "missing_deps": missing_deps,
        "all_checks_pass": passed,
        "pdf_skill_dir": str(pdf_dir),
    }


def _print_pdf_skill_validation(result: dict) -> None:
    """Print a formatted report of the generate-pdf skill file validation."""
    print("\n  Generate-PDF Sub-Skill File Manifest Validation", file=sys.stderr)
    print(f"  PDF skill dir: {result['pdf_skill_dir']}", file=sys.stderr)
    print("-" * 50, file=sys.stderr)

    if result["missing_required"]:
        count = len(result["missing_required"])
        print(
            f"\n  MISSING REQUIRED FILES ({count}):", file=sys.stderr
        )
        for f in result["missing_required"]:
            print(f"    FAIL  {f}", file=sys.stderr)
    else:
        req_count = len(PDF_SKILL_MANIFEST["required_files"])
        print(f"\n  Required files ({req_count}): ALL PRESENT", file=sys.stderr)

    if result["missing_optional"]:
        count = len(result["missing_optional"])
        print(
            f"\n  MISSING OPTIONAL FILES ({count}):", file=sys.stderr
        )
        for f in result["missing_optional"]:
            print(f"    NOTE  {f}", file=sys.stderr)

    if result["missing_deps"]:
        count = len(result["missing_deps"])
        print(
            f"\n  MISSING PARENT SKILL DEPENDENCIES ({count}):",
            file=sys.stderr,
        )
        for f in result["missing_deps"]:
            print(f"    FAIL  {f}", file=sys.stderr)
    else:
        dep_count = len(PDF_SKILL_MANIFEST["parent_skill_dependencies"])
        print(
            f"  Parent skill dependencies ({dep_count}): ALL PRESENT",
            file=sys.stderr,
        )

    if result["all_checks_pass"]:
        print(
            "\n  Verdict: PASS -- generate-pdf sub-skill is complete.\n",
            file=sys.stderr,
        )
    else:
        print(
            "\n  Verdict: FAIL -- missing required files or dependencies.\n",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _print_summary(manifest: dict, assigned_count: int) -> None:
    """Print a human-readable summary of the manifest to stderr."""
    lines = [
        "",
        f"  Ticker:         {manifest['ticker']}",
        f"  Company:        {manifest['company']}",
        f"  Valuation date: {manifest['valuation_date']}",
        f"  Theme / Lang:   {manifest['theme']} / {manifest['lang']}",
        f"  Output dir:     {manifest['output_dir']}",
        "",
        "  Engine outputs found:",
    ]
    for slot in OUTPUT_SLOTS:
        found = slot.key in manifest["engine_outputs"]
        marker = "  OK " if found else "---- "
        path = manifest["engine_outputs"].get(slot.key, "(not found)")
        source_tag = " [SCRIPT]" if slot.sourced else " [SKILL]"
        lines.append(f"    {marker} {slot.key:<14} -> {path}{source_tag}")

    req_count = sum(
        1 for c in manifest["chart_requests"] if c["priority"] == "required"
    )
    opt_count = sum(
        1 for c in manifest["chart_requests"] if c["priority"] == "optional"
    )
    lines += [
        "",
        f"  Chart requests:  {len(manifest['chart_requests'])} total",
        f"    Required: {req_count}  |  Optional: {opt_count}",
    ]

    missing = manifest.get("missing_optional_inputs")
    if missing:
        lines.append("")
        lines.append(
            "  Missing optional inputs "
            "(run upstream sub-skills to populate):"
        )
        for m in missing:
            producer = m.get("produced_by", "?")
            lines.append(
                f"    - {m['kind']:<16} <- {producer}  [{m['label']}]"
            )

    print("\n".join(lines), file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Auto-discover engine JSON outputs and assemble "
            "output-manifest.json."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python build_manifest.py --engine-dir engine_outputs/ -o manifest.json
  python build_manifest.py -d engine_outputs/ --ticker MU --company "Micron Technology"
  python build_manifest.py -d engine_outputs/ --theme goldman --lang zh-CN
  python build_manifest.py -d engine_outputs/ --ticker 0700.HK --company "Tencent" --quiet
  python build_manifest.py --validate-pdf-skill
  python build_manifest.py --check-all -d engine_outputs/
""",
    )
    ap.add_argument(
        "scan_dir",
        nargs="?",
        help=(
            "Directory containing engine JSON output files "
            "(positional, for backward compatibility)."
        ),
    )
    ap.add_argument(
        "-d",
        "--engine-dir",
        dest="engine_dir",
        default=None,
        help="Directory containing engine JSON output files.",
    )
    ap.add_argument(
        "-o",
        "--output",
        default="output-manifest.json",
        help=(
            "Path to write the assembled manifest "
            "(default: output-manifest.json)."
        ),
    )
    ap.add_argument(
        "--ticker",
        default=None,
        help="Override ticker (auto-detected from JSON content otherwise).",
    )
    ap.add_argument(
        "--company",
        default=None,
        help=(
            "Override company name "
            "(auto-detected from JSON content otherwise)."
        ),
    )
    ap.add_argument(
        "--valuation-date",
        default=None,
        help=(
            "Override valuation date YYYY-MM-DD "
            "(auto-detected from JSON otherwise)."
        ),
    )
    ap.add_argument(
        "--theme",
        default="default",
        help=(
            "Chart theme name (default: default). "
            "Options: default, goldman, ms, cjk."
        ),
    )
    ap.add_argument(
        "--lang",
        default="en-US",
        help=(
            "Report language code (default: en-US). "
            "E.g., zh-CN, ja-JP, ko-KR."
        ),
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress summary output to stderr.",
    )
    ap.add_argument(
        "--output-dir-base",
        default=None,
        help=(
            "Base directory for relative paths "
            "in engine_outputs segment."
        ),
    )
    ap.add_argument(
        "--validate-pdf-skill",
        action="store_true",
        help=(
            "Validate the generate-pdf sub-skill file manifest "
            "(SKILL.md Phase 7) and exit."
        ),
    )
    ap.add_argument(
        "--check-all",
        action="store_true",
        help=(
            "Run both engine output discovery and "
            "generate-pdf skill validation."
        ),
    )

    args = ap.parse_args(argv)

    exit_code = 0

    # ---- validate-pdf-skill mode ------------------------------------------
    if args.validate_pdf_skill or args.check_all:
        validation = validate_pdf_skill_manifest()
        _print_pdf_skill_validation(validation)
        if not validation["all_checks_pass"]:
            exit_code = 1
        if args.validate_pdf_skill and not args.check_all:
            return exit_code

    # ---- engine output discovery mode -------------------------------------
    scanned_dir = args.engine_dir or args.scan_dir
    if not scanned_dir:
        if args.validate_pdf_skill:
            return exit_code
        ap.error(
            "A scan directory is required. Use --engine-dir PATH or pass it "
            "as the first positional argument."
        )
        return 2

    engine_outputs, meta = discover_engine_outputs(scanned_dir)
    if not engine_outputs:
        print(
            "WARNING: No engine JSON outputs discovered in",
            scanned_dir,
            file=sys.stderr,
        )

    # Normalise paths to be relative to the specified base when requested
    if args.output_dir_base:
        base = Path(args.output_dir_base).resolve()
        for slot_key in list(engine_outputs):
            try:
                rel = (
                    Path(engine_outputs[slot_key]).resolve().relative_to(base)
                )
                engine_outputs[slot_key] = str(rel.as_posix())
            except ValueError:
                pass

    manifest = assemble_manifest(
        engine_outputs,
        meta,
        ticker=args.ticker,
        company=args.company,
        valuation_date=args.valuation_date,
        theme=args.theme,
        lang=args.lang,
    )

    out_path = args.output
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    if not args.quiet:
        _print_summary(manifest, len(engine_outputs))
        print(f"\nWrote: {os.path.abspath(out_path)}", file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(_main())
