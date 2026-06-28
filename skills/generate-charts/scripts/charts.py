"""Research-report charts CLI -- delegates to per-chart modules and theme system."""

from __future__ import annotations
import argparse, json, os, sys

_scripts_dir = os.path.dirname(os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import matplotlib
matplotlib.use("Agg")

from theme import apply_theme, _deep_merge
from cjk_fonts import configure_cjk_fonts

from chart_montecarlo import render as render_montecarlo
from chart_breakeven import render as render_breakeven
from chart_terminal import render as render_terminal
from chart_football import render as render_football
from chart_tornado import render as render_tornado
from chart_revenue_traj import render as render_revenue_traj
from chart_roic_spread import render as render_roic_spread
from chart_scenarios import render as render_scenarios
from chart_price_vs_value import render as render_price_vs_value
from chart_waterfall import render as render_waterfall
from chart_capex_cycle import render as render_capex_cycle
from chart_risk_matrix import render as render_risk_matrix

KINDS = {
    "montecarlo": render_montecarlo,
    "football": render_football,
    "breakeven": render_breakeven,
    "tornado": render_tornado,
    "terminal": render_terminal,
    "revenue_traj": render_revenue_traj,
    "roic_spread": render_roic_spread,
    "scenarios": render_scenarios,
    "price_vs_value": render_price_vs_value,
    "waterfall": render_waterfall,
    "capex_cycle": render_capex_cycle,
    "risk_matrix": render_risk_matrix,
}


def render_single(kind, in_path, out_dir, name=None, ticker=None,
                  theme_name="default", lang="en-US"):
    theme = apply_theme(theme_name, lang)
    with open(in_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    fn = KINDS[kind]
    default_name = f"{ticker}_{kind}" if ticker else kind
    return fn(data, out_dir, name=name or default_name, theme=theme, lang=lang)


def render_manifest(manifest_path):
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    ticker = manifest.get("ticker", "UNKNOWN")
    output_dir = manifest.get("output_dir", f"figs/{ticker}")
    lang = manifest.get("lang", "en-US")
    theme_name = manifest.get("theme", "default")
    theme_overrides = manifest.get("theme_overrides", {})
    charts = manifest.get("charts", [])

    theme = apply_theme(theme_name, lang)
    if theme_overrides:
        theme = _deep_merge(theme, theme_overrides)
    cjk_font = configure_cjk_fonts(lang)

    files = []
    for chart in charts:
        kind = chart["kind"]
        in_path = chart["in"]
        if kind not in KINDS or not os.path.exists(in_path):
            continue
        with open(in_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        fn = KINDS[kind]
        out_name = f"{ticker}_{chart.get('name', kind)}"
        paths = fn(data, output_dir, name=out_name, theme=theme, lang=lang)
        svg_path = next((p for p in paths if p.endswith(".svg")), "")
        png_path = next((p for p in paths if p.endswith(".png")), "")
        files.append({
            "kind": kind, "svg": svg_path, "png": png_path,
            "title": chart.get("title_override", kind),
            "width": theme.get("figure", {}).get("default_width", 7.0),
            "height": theme.get("figure", {}).get("default_height", 4.2),
        })

    chart_index = {
        "ticker": ticker,
        "generated_at": manifest.get("generated_at", ""),
        "theme": theme_name,
        "lang": lang,
        "cjk_font": cjk_font,
        "cjk_font_available": cjk_font is not None,
        "files": files,
    }
    os.makedirs(output_dir, exist_ok=True)
    index_path = os.path.join(output_dir, "chart-index.json")
    with open(index_path, "w", encoding="utf-8") as fh:
        json.dump(chart_index, fh, indent=2, ensure_ascii=False)
    print(f"Chart index: {index_path}")
    return index_path


def _main(argv=None):
    ap = argparse.ArgumentParser(
        description="Render research-report charts from engine JSON."
    )
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--theme", default="default")
    ap.add_argument("--lang", default="en-US")
    ap.add_argument("--kind", default=None, choices=sorted(KINDS))
    ap.add_argument("--in", dest="in_path", default=None)
    ap.add_argument("--out", default="figs")
    ap.add_argument("--ticker", default=None)
    ap.add_argument("--name", default=None)
    args = ap.parse_args(argv)

    if args.manifest:
        if not os.path.exists(args.manifest):
            print("Error: manifest not found", file=sys.stderr)
            return 1
        render_manifest(args.manifest)
        return 0

    if not args.kind or not args.in_path:
        ap.print_help()
        return 1
    if not os.path.exists(args.in_path):
        print("Error: input not found", file=sys.stderr)
        return 1

    paths = render_single(
        kind=args.kind, in_path=args.in_path, out_dir=args.out,
        name=args.name, ticker=args.ticker,
        theme_name=args.theme, lang=args.lang,
    )
    print("wrote:")
    for p in paths:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
