"""Render a gate-passed equity research Markdown report to professional PDF.

Pipeline (auto-selects best available engine):
  1. Parse Markdown -> HTML (Python markdown library)
  2. Resolve chart placeholders -> inline SVG  <img>
  3. Extract rating box from first-paragraph bold/strong pattern
  4. Inject professional CSS + CJK @font-face overrides
  5. [If --chart-index] Verify chart coverage against chart-index.json
     (Type-A programmatic gate — PRE-RENDER FAIL on required missing)
  6. Render HTML -> PDF via WeasyPrint (primary) or Playwright (fallback)
  7. Verify output (file exists, size <5MB)

Usage:
  python render_pdf.py path/to/report.md --out path/to/report.pdf
  python render_pdf.py report.md --out report.pdf --style professional
  python render_pdf.py report.md --out report.pdf --cjk --toc
  python render_pdf.py report.md --out report.pdf --chart-index figs/chart-index.json
  python render_pdf.py --check-deps
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

# ── Constants ──────────────────────────────────────────────────────────────

SKILL_DIR = Path(__file__).resolve().parent.parent  # skills/generate-pdf/
TEMPLATES_DIR = SKILL_DIR / "templates"
DEFAULT_STYLE = "professional"
STYLE_CSS_MAP = {
    "professional": "professional.css",
    "bw": "professional-bw.css",
    "internal": "internal.css",
}
CJK_CSS = "cjk-overrides.css"

MARKDOWN_EXTENSIONS = [
    "tables",
    "fenced_code",
    "codehilite",
    "toc",
    "footnotes",
    "attr_list",
    "def_list",
]

# Chart placeholder regex: canonical format ![](figs/{TICKER}_{kind})
# with optional .svg or .png extension. Also accepts portable repo paths
# ![](figs/{TICKER}/{TICKER}_{kind}.png). Stem must contain underscore.
CHART_RE = re.compile(
    r'!\[([^\]]*)\]\(figs/(?:[\w.-]+/)?([\w.]+_\w+)(?:\.(svg|png))?\)',
    re.IGNORECASE,
)

ENGINE_CHAIN = [
    "pandoc-weasyprint",
    "weasyprint",
    "playwright",
    "pandoc-only",
]

# Caption pattern: italic paragraph immediately following a chart
CAPTION_RE = re.compile(r'^\*([^*]+)\*$')

# Rating box extraction: first bold line with format "**Rating:** ..."
RATING_LINE_RE = re.compile(r'^\*\*Rating:\s*(.+?)\*\*', re.IGNORECASE)


# ── Engine Detection ───────────────────────────────────────────────────────

def _python_import_ok(module_name: str) -> bool:
    """Check if a Python module can be imported AND loaded.

    Catches Exception (not just ImportError) because some packages import but
    fail to load native dependencies at import time. WeasyPrint on Windows
    raises OSError ("cannot load library 'libpango-1.0-0'") when GTK/Pango is
    not installed — that must be treated as 'unavailable' so the engine chain
    falls back to Playwright instead of crashing dependency detection.
    """
    try:
        __import__(module_name)
        return True
    except Exception:
        return False


def detect_engine() -> Optional[str]:
    """Return best available engine: 'pandoc-weasyprint' | 'weasyprint'
    | 'playwright' | 'pandoc-only' | None."""
    has_weasy = shutil.which("weasyprint") or _python_import_ok("weasyprint")
    has_pandoc = shutil.which("pandoc") is not None
    has_playwright = _python_import_ok("playwright")

    if has_weasy and has_pandoc:
        return "pandoc-weasyprint"
    if has_weasy:
        return "weasyprint"
    if has_playwright:
        return "playwright"
    if has_pandoc:
        return "pandoc-only"
    return None


def check_dependencies() -> dict:
    """Return a table of installed/missing dependencies for diagnostics."""
    deps = {
        "weasyprint": {
            "installed": _python_import_ok("weasyprint"),
            "pip": "weasyprint",
            "system_deps": {
                "linux": "apt install libpango-1.0-0 libcairo2 libharfbuzz0b",
                "macos": "brew install weasyprint",
                "windows": "Install GTK3 runtime from github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer",
            },
        },
        "pandoc": {
            "installed": shutil.which("pandoc") is not None,
            "install": "See https://pandoc.org/installing.html",
        },
        "playwright": {
            "installed": _python_import_ok("playwright"),
            "pip": "playwright",
            "browser": "playwright install chromium",
        },
        "markdown": {
            "installed": _python_import_ok("markdown"),
            "pip": "markdown",
        },
    }
    # Check CJK font presence
    cjk_fonts = _detect_cjk_fonts()
    deps["cjk_fonts"] = {"installed": len(cjk_fonts) > 0, "found": cjk_fonts}
    return deps


def _detect_cjk_fonts() -> list[str]:
    """Detect installed CJK fonts via fc-list or platform heuristic."""
    fonts = []
    try:
        result = subprocess.run(
            ["fc-list", ":lang=zh", "-f", "%{family}\n"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().split("\n"):
            name = line.split(",")[0].strip()
            if name and name not in fonts:
                fonts.append(name)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: check common platform paths
    if not fonts:
        if sys.platform == "win32":
            font_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
            cjk_names = [
                "NotoSansSC-VF.ttf",
                "Noto Sans SC (TrueType).otf",
                "msyh.ttc",
                "simsun.ttc",
                "simhei.ttf",
            ]
            for name in cjk_names:
                if os.path.exists(os.path.join(font_dir, name)):
                    fonts.append(name)
        elif sys.platform == "darwin":
            font_dir = "/System/Library/Fonts"
            cjk_check = ["PingFang.ttc", "Hiragino Sans GB.ttc"]
            for name in cjk_check:
                if os.path.exists(os.path.join(font_dir, name)):
                    fonts.append(name)

    return fonts


def _lang_requires_cjk(lang: str | None) -> bool:
    if not lang:
        return False
    normalized = lang.lower()
    return normalized.startswith(("zh", "ja", "ko"))


# ── Chart Index Verification (Type-A Programmatic Gate) ──────────────────────

def load_chart_index(chart_index_path: str) -> dict:
    """Load and normalize chart-index.json.

    Supports two formats:
      1. Simple (chart-index.json):
         {"ticker": "MU", "required": ["MU_montecarlo", ...], "optional": [...]}
      2. Output-manifest style (output-manifest.json):
         {"ticker": "MU", "chart_requests": [
             {"kind": "montecarlo", "priority": "required"}, ...]}

    Returns normalized dict with keys:
      ticker, required, optional
    """
    path = Path(chart_index_path)
    if not path.exists():
        sys.stderr.write(f"[WARN] Chart index not found: {chart_index_path}\n")
        return {"ticker": "", "required": [], "optional": []}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        sys.stderr.write(
            f"[ERROR] Failed to parse chart index {chart_index_path}: {exc}\n"
        )
        return {"ticker": "", "required": [], "optional": []}

    ticker = data.get("ticker", "")

    # Format 2: output-manifest style — construct stems
    if "chart_requests" in data:
        required = []
        optional = []
        for cr in data["chart_requests"]:
            kind = cr.get("kind", "")
            priority = cr.get("priority", "required")
            stem = f"{ticker}_{kind}"
            if priority == "required":
                required.append(stem)
            else:
                optional.append(stem)
        return {"ticker": ticker, "required": required, "optional": optional}

    # Format 1: simple — stems already formed
    required = data.get("required", [])
    optional = data.get("optional", [])
    return {"ticker": ticker, "required": list(required), "optional": list(optional)}


def verify_chart_coverage(
    chart_index: dict,
    document_text: str,
    scan_mode: str = "html",
) -> dict:
    """Cross-reference chart-index.json against embedded chart references.

    This is a Type-A (programmatic) gate — no visual inspection required.
    The function scans the document for chart references and compares them
    against the chart index.

    Args:
        chart_index: Normalized dict from load_chart_index() with
                     'required' and 'optional' lists.
        document_text: HTML body (scan_mode='html') or markdown text
                       (scan_mode='markdown') to scan for chart refs.
        scan_mode: 'html' — scan <!-- chart: ... --> comments and
                   .chart-missing placeholders.
                   'markdown' — scan ![](figs/...) references.

    Returns:
        dict with keys:
          - passed (bool): True if no required charts are missing
          - missing_required (list[str]): required charts not found
          - missing_optional (list[str]): optional charts not found
          - embedded (list[str]): charts found in document AND in index
          - extra (list[str]): charts found in document but NOT in index
          - all_expected (list[str]): all charts listed in the index
    """
    required = set(chart_index.get("required", []))
    optional = set(chart_index.get("optional", []))
    all_expected = required | optional

    if scan_mode == "html":
        # Scan for <!-- chart: name.svg --> / <!-- chart: name.png --> comments
        # produced by _resolve_charts during inline SVG embedding
        chart_comment_re = re.compile(
            r'<!--\s*chart:\s*([^\s>]+)', re.IGNORECASE,
        )
        found_comments = {
            m.group(1).replace(".svg", "").replace(".png", "")
            for m in chart_comment_re.finditer(document_text)
        }

        # Scan for .chart-missing placeholders (data-chart="stem" attribute)
        missing_re = re.compile(r'data-chart="([^"]+)"')
        found_missing = {
            m.group(1) for m in missing_re.finditer(document_text)
        }

        # Scan for bare <img> tags inside <figure class="chart"> as fallback
        img_re = re.compile(
            r'<figure[^>]*class="chart"[^>]*>.*?<img[^>]*src="figs/([^"]+)"',
            re.DOTALL | re.IGNORECASE,
        )
        found_img = {
            m.group(1).replace(".svg", "").replace(".png", "")
            for m in img_re.finditer(document_text)
        }

        found = found_comments | found_missing | found_img
    else:
        # Markdown mode: ![](figs/stem) or ![](figs/stem.ext)
        chart_ref_re = re.compile(
            r'!\[([^\]]*)\]\(figs/([^)\s]+?)(?:\.(?:svg|png))?\)',
            re.IGNORECASE,
        )
        found = {m.group(2) for m in chart_ref_re.finditer(document_text)}

    # Compute differences
    missing_required = sorted(required - found)
    missing_optional = sorted(optional - found)
    embedded = sorted(all_expected & found)
    extra = sorted(found - all_expected)

    passed = len(missing_required) == 0

    return {
        "passed": passed,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "embedded": embedded,
        "extra": extra,
        "all_expected": sorted(all_expected),
    }


# ── Markdown -> HTML ───────────────────────────────────────────────────────

def md_to_html(md_text: str, figs_dir: str = "figs",
               inline_svg: bool = True) -> str:
    """Convert Markdown to HTML, resolving chart placeholders.

    Args:
        md_text: Raw markdown content.
        figs_dir: Directory containing chart image files.
        inline_svg: If True, inline SVG content directly into HTML.

    Returns:
        HTML body content string.
    """
    import markdown

    # Pre-process: resolve chart placeholders before markdown conversion.
    # This prevents markdown from munging the SVG content.
    md_text = _resolve_charts(md_text, figs_dir, inline_svg)

    # Convert markdown to HTML
    html_body = markdown.markdown(md_text, extensions=MARKDOWN_EXTENSIONS)

    # Post-process: wrap images in <figure> with captions
    html_body = _wrap_figures(html_body)

    # Post-process: extract and style rating box
    html_body = _style_rating_box(html_body)

    # Post-process: wrap tables that are too wide
    html_body = _wrap_wide_tables(html_body)

    return html_body


def _img_to_data_uri(img_path: Path) -> Optional[str]:
    """Return a base64 data URI for an image file, or None on failure.

    Why base64 (not a file:// path): Chromium's print pipeline silently fails
    to load images referenced by relative or file:// paths when the working
    directory contains non-ASCII characters (e.g. D:\\研报生成). The chart then
    renders blank with no error. Base64 data URIs have zero path dependency and
    always render. WeasyPrint also accepts data URIs, so this is engine-neutral.
    """
    mime_by_ext = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml", ".gif": "image/gif",
    }
    mime = mime_by_ext.get(img_path.suffix.lower())
    if mime is None:
        return None
    try:
        b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except OSError as exc:
        sys.stderr.write(f"[WARN] Failed to read image {img_path}: {exc}\n")
        return None


def _resolve_charts(md_text: str, figs_dir: str,
                    inline_svg: bool = True) -> str:
    """Find ![](figs/...) references and resolve them.

    Strategy:
      1. Try .svg first (preferred — vector)
      2. Fall back to .png
      3. If inline_svg=True and SVG found, inline the raw <svg> content
      4. Otherwise, embed as a base64 data URI <img> (NEVER a bare file path —
         non-ASCII working dirs make file:// paths fail silently in Chromium)
      5. If neither found, insert a red placeholder note.
    """
    figs_path = Path(figs_dir)
    is_zh = _has_cjk(md_text)

    def _replace_chart(match: re.Match) -> str:
        raw_alt = (match.group(1) or "").strip()
        alt_text = raw_alt or ("图表" if is_zh else "Chart")
        if is_zh and raw_alt and not _has_cjk(raw_alt):
            alt_text = "图表"
        stem = match.group(2)
        ext = match.group(3)  # explicit extension or None

        # Build candidate file paths
        candidates = []
        if ext:
            candidates.append(figs_path / f"{stem}.{ext}")
        else:
            candidates.append(figs_path / f"{stem}.svg")
            candidates.append(figs_path / f"{stem}.png")

        img_path = None
        for candidate in candidates:
            if candidate.exists():
                img_path = candidate
                break

        if img_path is None:
            sys.stderr.write(
                f"[WARN] Chart not found: {stem} in {figs_dir}/ "
                f"(tried .svg, .png)\n"
            )
            # Return a placeholder that the quality gate can detect
            return (
                f'<div class="chart-missing" data-chart="{stem}" '
                f'style="border:1pt dashed red;padding:12pt;text-align:center;'
                f'color:red;">'
                f'[CHART MISSING: {stem}]</div>'
            )

        # Inline SVG
        if inline_svg and img_path.suffix.lower() == ".svg":
            try:
                svg_content = img_path.read_text(encoding="utf-8")
                # Remove XML declaration and doctype — keep only <svg>...</svg>
                svg_content = re.sub(
                    r'<\?xml[^?]*\?>', '', svg_content, count=1,
                )
                svg_content = re.sub(
                    r'<!DOCTYPE[^>]*>', '', svg_content, count=1,
                )
                # Add class for CSS targeting
                svg_content = svg_content.replace(
                    '<svg', '<svg class="plot"', 1,
                )
                return (
                    f'<!-- chart: {img_path.name} -->\n'
                    f'<figure class="chart">\n{svg_content}\n'
                    f'<figcaption>{alt_text}</figcaption>\n</figure>'
                )
            except Exception as exc:
                sys.stderr.write(
                    f"[WARN] Failed to inline SVG {img_path}: {exc}\n"
                )

        # Embed as a base64 data URI (path-independent — survives non-ASCII dirs)
        data_uri = _img_to_data_uri(img_path)
        if data_uri is None:
            # Last-resort fallback: bare path (may fail on non-ASCII dirs)
            rel_path = str(img_path).replace("\\", "/")
            data_uri = rel_path
            sys.stderr.write(
                f"[WARN] Could not base64-embed {img_path.name}; "
                f"falling back to a path reference that may not load in "
                f"Chromium on non-ASCII directories.\n"
            )
        return (
            f'<!-- chart: {img_path.name} -->\n'
            f'<figure class="chart">\n'
            f'<img src="{data_uri}" alt="{alt_text}" />\n'
            f'<figcaption>{alt_text}</figcaption>\n</figure>'
        )

    return CHART_RE.sub(_replace_chart, md_text)


def _check_inline_svg_size(html_body: str, max_inline_mb: float = 1.0) -> None:
    """Check combined size of inline <svg> elements against threshold.

    Emits a warning to stderr when combined SVG bytes exceed
    *max_inline_mb*, suggesting ``--no-inline-svg`` to reduce PDF size.
    """
    svg_tags = re.findall(r'<svg\b[^>]*>.*?</svg>', html_body, re.DOTALL)
    if not svg_tags:
        return
    total_bytes = sum(len(s.encode("utf-8")) for s in svg_tags)
    total_mb = total_bytes / (1024 * 1024)
    if total_mb > max_inline_mb:
        sys.stderr.write(
            f"[WARN] Combined inline SVG size is {total_mb:.1f} MB "
            f"(exceeds --max-inline-size {max_inline_mb:.0f} MB). "
            f"Consider --no-inline-svg to reduce PDF size.\n"
        )


def _wrap_figures(html_body: str) -> str:
    """Wrap <img> tags that are NOT already inside <figure> into <figure>.
    Detect following italic paragraph as caption."""
    # This is a best-effort post-process.
    # Charts already resolved by _resolve_charts are wrapped.
    # Any remaining bare <img> gets a default figure wrapper.
    # Wrap bare images that aren't inside figure
    lines = html_body.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.search(r'<img\s[^>]*>', line)
        # Check if already inside figure
        if m and '<figure' not in line:
            alt = ""
            alt_m = re.search(r'alt="([^"]*)"', line)
            if alt_m:
                alt = alt_m.group(1)
            caption_html = ""
            # Check if next non-empty line is an italic paragraph
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                cap_m = CAPTION_RE.match(next_line)
                if cap_m:
                    caption_html = f"\n<figcaption>{cap_m.group(1)}</figcaption>"
                    i += 1  # consume caption line
            result.append(
                f'<figure class="chart">\n{line.strip()}{caption_html}\n</figure>'
            )
        else:
            result.append(line)
        i += 1
    return "\n".join(result)


def _style_rating_box(html_body: str) -> str:
    """Detect report header pattern and wrap in a styled .rating-box div.

    The report header typically looks like:
      <p><strong>Rating: REDUCE / SELL</strong> ...</p>

    Strategy: Find the first <p> containing <strong>Rating: and wrap
    a <div class="rating-box"> around the whole header block
    (from document start to first <h2> or <hr>).
    """
    # Detect the rating box content: from start of body to first <h2>
    h2_match = re.search(r'<h2[ >]', html_body)
    if h2_match:
        cutoff = h2_match.start()
    else:
        # No h2 — take first 3 paragraphs
        para_matches = list(re.finditer(r'</p>', html_body))
        if len(para_matches) >= 3:
            cutoff = para_matches[2].end()
        else:
            return html_body  # Too short to style

    header_block = html_body[:cutoff]
    rest = html_body[cutoff:]

    # Extract company name from <h1> if present
    company_name = ""
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', header_block)
    if h1_match:
        company_name = h1_match.group(1)

    is_zh = _has_cjk(header_block)
    labels = {
        "rating": "评级" if is_zh else "Rating",
        "intrinsic": "每股内在价值" if is_zh else "Intrinsic Value",
        "price": "当前价格" if is_zh else "Price",
        "downside": "上行/目标" if is_zh else "Downside",
        "percentile": "价格分位" if is_zh else "Price %ile",
        "thesis": "投资要点" if is_zh else "Thesis",
    }

    # Extract rating data from the header
    rating = _extract_kv(header_block, "Rating") or _extract_kv(header_block, "评级")
    intrinsic = (
        _extract_kv(header_block, "Intrinsic value")
        or _extract_kv(header_block, "每股内在价值")
    )
    price = _extract_kv(header_block, "Price") or _extract_kv(header_block, "当前价格")
    downside = (
        _extract_kv(header_block, "Downside")
        or _extract_kv(header_block, "上行空间")
        or _extract_kv(header_block, "下行空间")
        or _extract_kv(header_block, "目标区间")
    )
    percentile = (
        _extract_kv(header_block, "Price.*ile")
        or _extract_kv(header_block, "价格分位")
    )

    # Build the rating box HTML
    box_parts = ['<div class="rating-box">']

    if company_name:
        box_parts.append(
            f'<p class="company-name">{company_name}</p>'
        )

    box_parts.append('<hr class="divider">')
    box_parts.append('<div class="kv-grid">')

    if rating:
        value_class = _rating_color_class(rating)
        box_parts.append(f'<span class="kv-label">{labels["rating"]}</span>')
        box_parts.append(
            f'<span class="kv-value {value_class}">{rating}</span>'
        )
    if intrinsic:
        box_parts.append(f'<span class="kv-label">{labels["intrinsic"]}</span>')
        box_parts.append(f'<span class="kv-value">{intrinsic}</span>')
    if price:
        box_parts.append(f'<span class="kv-label">{labels["price"]}</span>')
        box_parts.append(f'<span class="kv-value">{price}</span>')
    if downside:
        box_parts.append(f'<span class="kv-label">{labels["downside"]}</span>')
        box_parts.append(f'<span class="kv-value">{downside}</span>')
    if percentile:
        box_parts.append(f'<span class="kv-label">{labels["percentile"]}</span>')
        box_parts.append(f'<span class="kv-value">{percentile}</span>')

    box_parts.append('</div>')  # close kv-grid

    # Extract thesis text — the paragraph after the bold rating line
    thesis = _extract_thesis(header_block)
    if thesis:
        box_parts.append(f'<p class="thesis-label">{labels["thesis"]}</p>')
        box_parts.append(f'<p class="thesis-text">{thesis}</p>')

    # MOS buy-band extraction
    mos = _extract_kv(header_block, "MoS buy-band")
    if mos:
        box_parts.append(f'<p class="mos-band">{mos}</p>')

    box_parts.append('</div>')  # close rating-box

    rating_box_html = "\n".join(box_parts)

    # Replace the original header block with the styled rating box
    # followed by the rest of the header content (minus what we extracted)
    # Actually, simpler: output the rating box, then the original content
    # but with the first strong paragraph (which we consumed) removed
    first_strong_p = re.search(
        r'<p><strong>\s*(?:Rating|评级).*?</strong>.*?</p>', header_block, re.DOTALL
    )
    if first_strong_p:
        header_block = header_block[:first_strong_p.start()] + \
                       header_block[first_strong_p.end():]

    return rating_box_html + "\n" + header_block + rest


def _extract_kv(text: str, key: str) -> Optional[str]:
    """Extract a key-value pair from text. E.g. 'Rating: REDUCE' -> 'REDUCE'."""
    patterns = [
        r'<strong>\s*' + key + r'\s*[:：]\s*([^<]+?)</strong>',
        r'<strong>\s*' + key + r'\s*[:：]?\s*</strong>\s*(.+?)(?=<strong>|<br|</p>)',
        r'\*\*\s*' + key + r'\s*[:：]?\s*\*\*\s*(.+?)(?:\s*\*\*|$|<br|</p)',
    ]
    for raw_pattern in patterns:
        m = re.search(raw_pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            value = m.group(1).strip()
            # Clean up markdown / HTML formatting
            value = re.sub(r'<[^>]+>', '', value)
            value = re.sub(r'\*\*', '', value)
            return value.strip(" \t\r\n|")
    return None


def _has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _extract_thesis(header_block: str) -> Optional[str]:
    """Extract the thesis paragraph — the longest paragraph after Rating line."""
    # Find all paragraph text
    paragraphs = re.findall(r'<p>(.*?)</p>', header_block, re.DOTALL)
    # Filter out lines that contain key metadata
    meta_keys = [
        'Rating', 'Intrinsic', 'Price', 'Downside', 'MoS',
        '评级', '当前价格', '每股内在价值', '上行空间', '下行空间',
        '目标区间', '估值日期', '复核时点', '主要方法',
    ]
    thesis_candidates = []
    for p in paragraphs:
        clean = re.sub(r'<[^>]+>', '', p).strip()
        clean = re.sub(r'\*\*', '', clean)
        if any(k in clean for k in meta_keys):
            continue
        if len(clean) > 100:
            thesis_candidates.append(clean)
    if thesis_candidates:
        # Return the longest paragraph (likely the thesis)
        return max(thesis_candidates, key=len)
    return None


def _rating_color_class(rating: str) -> str:
    """Return CSS class for rating color: 'up', 'down', or ''."""
    rating_upper = rating.upper()
    if any(w in rating_upper for w in ["BUY", "ACCUMULATE", "OVERWEIGHT"]):
        return "up"
    if any(w in rating_upper for w in ["SELL", "REDUCE", "UNDERWEIGHT"]):
        return "down"
    return ""


def _wrap_wide_tables(html_body: str) -> str:
    """Add class="wide" to tables that are likely to overflow A4 margins."""
    # Simple heuristic: tables with more than 4 columns
    def _add_wide_class(match: re.Match) -> str:
        table_html = match.group(0)
        # Count <th> or <td> in the first row
        first_row = re.search(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
        if first_row:
            col_count = len(re.findall(r'<t[dh]', first_row.group(1)))
            if col_count >= 4:
                return table_html.replace('<table>', '<table class="wide">', 1)
        return table_html

    return re.sub(r'<table>.*?</table>', _add_wide_class, html_body,
                  flags=re.DOTALL)


# ── CSS Loading ────────────────────────────────────────────────────────────

def load_css(style: str = DEFAULT_STYLE, cjk: bool = True,
             extra_css: Optional[str] = None) -> str:
    """Load CSS from templates, with 3-tier resolution:
    1. Direct path (extra_css)
    2. Project-local: comms/templates/{style}.css
    3. Skill-bundled: skills/generate-pdf/templates/{style}.css
    """
    css_parts = []

    # Main style CSS
    css_content = _resolve_css(style)
    if css_content:
        css_parts.append(css_content)

    # CJK overrides
    if cjk:
        cjk_content = _resolve_css("cjk-overrides")
        if cjk_content:
            css_parts.append(cjk_content)

    # Extra user CSS
    if extra_css:
        extra_path = Path(extra_css)
        if extra_path.exists():
            css_parts.append(extra_path.read_text(encoding="utf-8"))
        else:
            sys.stderr.write(f"[WARN] Extra CSS not found: {extra_css}\n")

    return "\n".join(css_parts)


def _resolve_css(name: str) -> Optional[str]:
    """3-tier CSS resolution."""
    if name.endswith(".css"):
        style_key = name.replace(".css", "")
    else:
        style_key = name

    filename = STYLE_CSS_MAP.get(style_key, f"{style_key}.css")

    # 1. Direct path
    if os.path.isfile(name):
        return Path(name).read_text(encoding="utf-8")

    # 2. Project-local
    local_path = Path("comms/templates") / filename
    if local_path.exists():
        return local_path.read_text(encoding="utf-8")

    # 3. Skill-bundled
    bundled_path = TEMPLATES_DIR / filename
    if bundled_path.exists():
        return bundled_path.read_text(encoding="utf-8")

    sys.stderr.write(f"[WARN] CSS template not found: {filename}\n")
    return None


# ── HTML Document Assembly ─────────────────────────────────────────────────

def build_html_document(html_body: str, css: str,
                        title: str = "Equity Research Report",
                        lang: str = "en") -> str:
    """Assemble complete HTML document with CSS injection."""
    lang_attr = f'lang="{lang}"' if lang else ""
    return f"""<!DOCTYPE html>
<html {lang_attr}>
<head>
<meta charset="utf-8">
<meta name="generator" content="equity-research-analyst/generate-pdf">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
{html_body}
</body>
</html>"""


# ── PDF Rendering ──────────────────────────────────────────────────────────

def _inject_weasyprint_logo(html: str, logo: str,
                            logo_height_cm: float = 1.2) -> str:
    """Inject a recurring logo into HTML for WeasyPrint via a running element.

    WeasyPrint supports CSS Paged Media `position: running()` + `element()`,
    which is the correct way to repeat a logo in the @page margin box. (This is
    the inverse of Chromium, which needs headerTemplate and does NOT support
    `element()`.) The logo is removed from normal flow and painted in @top-left.
    The @page top margin auto-grows with the logo so it never overlaps text.
    """
    lp = Path(logo)
    if not lp.exists():
        sys.stderr.write(f"[WARN] Logo not found: {logo}\n")
        return html
    logo_uri = _img_to_data_uri(lp)
    if logo_uri is None:
        return html
    top_margin_cm = max(2.6, logo_height_cm + 1.4)
    inject_css = (
        ".report-logo{position:running(logoRun);}"
        f"@page{{margin-top:{top_margin_cm}cm;@top-left{{content:element(logoRun);}}}}"
    )
    logo_div = (
        f'<div class="report-logo"><img src="{logo_uri}" '
        f'style="height:{logo_height_cm}cm;width:auto;"></div>'
    )
    if "</style>" in html:
        html = html.replace("</style>", inject_css + "</style>", 1)
    if "<body>" in html:
        html = html.replace("<body>", "<body>" + logo_div, 1)
    return html


def render_weasyprint(html: str, pdf_path: str,
                      timeout: int = 120,
                      logo: Optional[str] = None,
                      logo_height_cm: float = 1.2) -> Optional[str]:
    """Render HTML to PDF using WeasyPrint."""
    try:
        from weasyprint import HTML
        if logo:
            html = _inject_weasyprint_logo(html, logo, logo_height_cm)
        HTML(string=html).write_pdf(pdf_path)
        return pdf_path
    except ImportError:
        sys.stderr.write("[ERROR] WeasyPrint not installed.\n")
        return None
    except Exception as exc:
        sys.stderr.write(f"[ERROR] WeasyPrint render failed: {exc}\n")
        return None


def render_playwright(html: str, pdf_path: str,
                      logo: Optional[str] = None,
                      logo_height_cm: float = 0.95) -> Optional[str]:
    """Render HTML to PDF using Playwright headless Chromium.

    Logo handling (CRITICAL): a recurring company logo MUST go in Chromium's
    native headerTemplate — NOT a CSS `position: fixed` element. In Chromium's
    print pipeline a fixed element anchors to the CONTENT box (inside the print
    margins), so it lands on top of the first line of body text on every page.
    The headerTemplate renders inside the reserved top-margin box, physically
    separated from body text. The top margin is auto-grown to fit the logo plus
    a clearance band, so enlarging the logo never reintroduces overlap.
    """
    import asyncio

    logo_uri = None
    if logo:
        lp = Path(logo)
        if lp.exists():
            logo_uri = _img_to_data_uri(lp)
        else:
            sys.stderr.write(f"[WARN] Logo not found: {logo}\n")

    async def _render():
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            sys.stderr.write("[ERROR] Playwright not installed.\n")
            return None

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch()
            except Exception:
                sys.stderr.write(
                    "[ERROR] Chromium not installed. "
                    "Run: playwright install chromium\n"
                )
                return None
            page = await browser.new_page()
            await page.set_content(html, wait_until="networkidle")

            pdf_kwargs = dict(
                path=pdf_path,
                format="A4",
                margin={
                    "top": "2.2cm", "bottom": "2.4cm",
                    "left": "2.4cm", "right": "2.4cm",
                },
                print_background=True,
                display_header_footer=False,
            )

            if logo_uri:
                # Logo in the top-margin box; page number in the footer.
                # Top margin = logo height + 1.4cm clearance band (>= 2.5cm) so
                # the body text never collides with the logo, at any logo size.
                top_margin_cm = max(2.5, logo_height_cm + 1.4)
                header_template = (
                    '<div style="width:100%; margin:0; padding:0 0 0 1.0cm; '
                    '-webkit-print-color-adjust:exact;">'
                    f'<img src="{logo_uri}" style="height:{logo_height_cm}cm; width:auto;" />'
                    '</div>'
                )
                footer_template = (
                    '<div style="width:100%; font-size:8px; color:#999; '
                    'text-align:center; font-family:Georgia,serif;">'
                    '— <span class="pageNumber"></span> —</div>'
                )
                pdf_kwargs["margin"]["top"] = f"{top_margin_cm}cm"
                pdf_kwargs["display_header_footer"] = True
                pdf_kwargs["header_template"] = header_template
                pdf_kwargs["footer_template"] = footer_template

            await page.pdf(**pdf_kwargs)
            await browser.close()
        return pdf_path

    try:
        return asyncio.run(_render())
    except Exception as exc:
        sys.stderr.write(f"[ERROR] Playwright render failed: {exc}\n")
        return None


def render_pandoc_weasyprint(md_path: str, pdf_path: str,
                             css: str, toc: bool = False) -> Optional[str]:
    """Render Markdown to PDF via Pandoc + WeasyPrint."""
    # Write CSS to temp file for Pandoc to read
    css_path = pdf_path.replace(".pdf", "_temp.css")
    Path(css_path).write_text(css, encoding="utf-8")

    cmd = [
        "pandoc", md_path,
        "--pdf-engine=weasyprint",
        "-f", "markdown+pipe_tables+footnotes",
        "-o", pdf_path,
        "--css", css_path,
        "--metadata", "title=Equity Research Report",
        "-V", "geometry:margin=2.4cm",
        "-V", "mainfont=Source Serif 4",
        "-V", "fontsize=11pt",
    ]
    if toc:
        cmd.insert(2, "--toc")

    try:
        subprocess.run(cmd, check=True, timeout=180)
        # Clean up temp CSS
        os.unlink(css_path)
        return pdf_path
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(f"[ERROR] Pandoc render failed: {exc}\n")
        return None
    except FileNotFoundError:
        sys.stderr.write("[ERROR] Pandoc not found.\n")
        return None
    finally:
        if os.path.exists(css_path):
            os.unlink(css_path)


def _render_with_fallback(
    md_path_abs: Path, pdf_path: str, html_doc: str, css: str,
    toc: bool = False, start_from: Optional[str] = None,
    logo: Optional[str] = None, logo_height_cm: float = 0.95,
) -> Optional[str]:
    """Try engines in fallback order; return result on first success.

    Loops through ``ENGINE_CHAIN``, attempting each engine in turn.
    If *start_from* is given, begin at that engine's position in the
    chain (earlier engines are skipped).  Returns ``None`` only when
    **every** engine in the attempted span has failed.
    """
    chain = list(ENGINE_CHAIN)
    if start_from and start_from in chain:
        idx = chain.index(start_from)
        chain = chain[idx:]

    for engine_name in chain:
        # pandoc-weasyprint renders straight from markdown and cannot inject a
        # logo running element — skip it when a logo is required so the logo is
        # never silently dropped.
        if logo and engine_name == "pandoc-weasyprint":
            print("Skipping pandoc-weasyprint (no logo support); using a logo-capable engine.")
            continue
        print(f"Trying engine: {engine_name}")
        result = None
        if engine_name == "pandoc-weasyprint":
            result = render_pandoc_weasyprint(
                str(md_path_abs), pdf_path, css, toc=toc,
            )
        elif engine_name == "weasyprint":
            # WeasyPrint running element renders slightly smaller; nudge up so
            # both engines yield a visually similar logo size.
            result = render_weasyprint(html_doc, pdf_path, logo=logo,
                                       logo_height_cm=logo_height_cm + 0.25)
        elif engine_name == "playwright":
            result = render_playwright(html_doc, pdf_path, logo=logo,
                                       logo_height_cm=logo_height_cm)
        elif engine_name == "pandoc-only":
            html_out_path = pdf_path.replace(".pdf", ".html")
            cmd = [
                "pandoc", str(md_path_abs),
                "--standalone", "--embed-resources",
                "-o", html_out_path,
            ]
            try:
                subprocess.run(cmd, check=True)
                sys.stderr.write(
                    f"[INFO] Pandoc-only: generated {html_out_path}\n"
                    f"  To convert to PDF, install weasyprint and re-run.\n"
                )
                result = html_out_path
            except Exception as exc:
                sys.stderr.write(f"[ERROR] Pandoc-only failed: {exc}\n")
        if result:
            return result
    return None


# ── Output Verification ────────────────────────────────────────────────────

def verify_pdf(pdf_path: str, max_size_mb: float = 5.0) -> dict:
    """Run post-render verification checks on the PDF.

    Returns a dict with check results suitable for the quality gate.
    """
    result = {
        "pdf_path": pdf_path,
        "exists": False,
        "size_bytes": 0,
        "size_mb": 0.0,
        "size_ok": False,
        "all_checks_pass": False,
    }

    if not os.path.exists(pdf_path):
        return result

    result["exists"] = True
    result["size_bytes"] = os.path.getsize(pdf_path)
    result["size_mb"] = result["size_bytes"] / (1024 * 1024)
    result["size_ok"] = result["size_mb"] <= max_size_mb

    result["all_checks_pass"] = result["exists"] and result["size_ok"]

    return result


# ── Main Entry Point ───────────────────────────────────────────────────────

def render(md_path: str, pdf_path: str,
           style: str = DEFAULT_STYLE,
           engine: str = "auto",
           figs_dir: str = "figs",
           cjk: bool = True,
           toc: bool = False,
           html_out: Optional[str] = None,
           extra_css: Optional[str] = None,
           lang: str = "en",
           chart_index: Optional[str] = None,
           no_inline_svg: bool = False,
           max_inline_size: float = 1.0,
           logo: Optional[str] = None,
           logo_height_cm: float = 0.95,
           verify_visual: bool = False) -> Optional[str]:
    """Main rendering function.

    Args:
        md_path: Path to the Markdown report.
        pdf_path: Output PDF path.
        style: CSS style name ('professional', 'bw', 'internal').
        engine: 'auto', 'weasyprint', 'playwright', or 'pandoc-weasyprint'.
        figs_dir: Directory containing chart image files.
        cjk: Enable CJK font support.
        toc: Generate table of contents.
        html_out: Optional path to save the intermediate HTML.
        extra_css: Optional path to additional CSS.
        lang: Language code for HTML lang attribute.
        chart_index: Optional path to chart-index.json for Type-A
                     programmatic chart coverage verification.
        logo: Optional path to a company logo image. Rendered in the page
              top-margin on every page (Chromium headerTemplate / WeasyPrint
              running element). NEVER a CSS position:fixed element.
        verify_visual: If True, render the first pages of the output PDF to PNG
              previews (requires PyMuPDF) so the layout can actually be
              inspected — the only reliable way to catch logo overlap, oversized
              charts, and tofu. Blind CSS tweaks without looking are a trap.

    Returns:
        pdf_path on success, None on failure.
    """
    # Resolve paths relative to the markdown file
    md_path_abs = Path(md_path).resolve()
    if not md_path_abs.exists():
        sys.stderr.write(f"[ERROR] Report not found: {md_path}\n")
        return None

    figs_dir_abs = Path(figs_dir)
    if not figs_dir_abs.is_absolute():
        # Resolve relative to markdown file's directory
        figs_dir_abs = (md_path_abs.parent / figs_dir).resolve()

    print(f"Input:  {md_path_abs}")
    print(f"Output: {pdf_path}")
    print(f"Figs:   {figs_dir_abs}")

    # Step 1: Detect engine
    if engine == "auto":
        engine = detect_engine()
        if engine is None:
            sys.stderr.write(
                "[ERROR] No PDF engine available.\n"
                "  Install one of: weasyprint, playwright, or pandoc.\n"
                "  Run: python render_pdf.py --check-deps\n"
            )
            return None
    print(f"Engine: {engine}")

    # Step 2: Read markdown
    md_text = md_path_abs.read_text(encoding="utf-8")
    print(f"Markdown: {len(md_text)} chars")

    if cjk and _lang_requires_cjk(lang):
        cjk_fonts = _detect_cjk_fonts()
        if not cjk_fonts:
            sys.stderr.write(
                "[ERROR] CJK rendering requested for a Chinese/Japanese/Korean "
                "report, but no CJK-capable font was detected. Install Noto Sans CJK, "
                "Microsoft YaHei, SimSun, SimHei, PingFang, or equivalent before "
                "rendering the PDF.\n"
            )
            return None
        print(f"CJK fonts: {', '.join(cjk_fonts[:3])}")

    # Step 3: Convert Markdown -> HTML
    html_body = md_to_html(md_text, str(figs_dir_abs), inline_svg=not no_inline_svg)

    # Step 3b: Check inline SVG size
    _check_inline_svg_size(html_body, max_inline_mb=max_inline_size)

    # Step 4: Load CSS
    css = load_css(style, cjk=cjk, extra_css=extra_css)
    print(f"CSS: {len(css)} chars")

    # Step 5: Assemble HTML document
    title = _extract_title(md_path_abs) or "Equity Research Report"
    html_doc = build_html_document(html_body, css, title=title, lang=lang)

    # Optional: save intermediate HTML
    if html_out:
        Path(html_out).write_text(html_doc, encoding="utf-8")
        print(f"HTML:  {html_out}")

    # Step 5.5: Chart coverage verification (Type-A programmatic gate)
    if chart_index:
        print(f"\nChart index: {chart_index}")
        ci = load_chart_index(chart_index)
        if ci["required"] or ci["optional"]:
            coverage = verify_chart_coverage(ci, html_body, scan_mode="html")

            # --- Report embedded ---
            if coverage["embedded"]:
                print(
                    f"  Charts embedded ({len(coverage['embedded'])}): "
                    + ", ".join(coverage["embedded"])
                )
            else:
                print("  Charts embedded: (none)")

            # --- Report extra ---
            if coverage["extra"]:
                sys.stderr.write(
                    f"[INFO] Extra charts in document (not in index): "
                    + ", ".join(coverage["extra"]) + "\n"
                )

            # --- Required missing -> PRE-RENDER FAIL ---
            if coverage["missing_required"]:
                sys.stderr.write(
                    f"\n[FAIL] PRE-RENDER FAIL — Required charts missing "
                    f"({len(coverage['missing_required'])}):\n"
                )
                for stem in coverage["missing_required"]:
                    sys.stderr.write(f"  - {stem}\n")
                sys.stderr.write(
                    "  Run charts.py to generate missing charts, then re-render.\n"
                )
                return None

            # --- Optional missing -> WARNING ---
            if coverage["missing_optional"]:
                sys.stderr.write(
                    f"[WARN] Optional charts missing "
                    f"({len(coverage['missing_optional'])}):\n"
                )
                for stem in coverage["missing_optional"]:
                    sys.stderr.write(f"  - {stem}\n")
                sys.stderr.write(
                    "  Proceeding with render — optional charts are not blocking.\n"
                )

            if coverage["passed"]:
                print("  Chart coverage: PASS")

    # Step 6: Render PDF
    result = None
    pdf_dir = Path(pdf_path).parent
    pdf_dir.mkdir(parents=True, exist_ok=True)

    result = _render_with_fallback(
        md_path_abs, pdf_path, html_doc, css, toc=toc,
        start_from=None if engine == "auto" else engine,
        logo=logo, logo_height_cm=logo_height_cm,
    )

    # Step 7: Verify output
    if result:
        verification = verify_pdf(result)
        print(
            f"PDF: {verification['size_mb']:.1f} MB "
            f"({'OK' if verification['size_ok'] else 'OVERSIZE'})"
        )
        if not verification["size_ok"]:
            sys.stderr.write(
                f"[WARN] PDF exceeds {5.0}MB. "
                "Consider using SVG charts or enabling font subsetting.\n"
            )

        # Step 8: Visual self-verification (catches logo overlap / oversized
        # charts / tofu that file-size checks never will).
        if verify_visual:
            previews = render_pdf_previews(result, n_pages=3)
            if previews:
                print("Visual previews (INSPECT THESE — do not tweak CSS blind):")
                for p in previews:
                    print(f"  {p}")

    return result


def render_pdf_previews(pdf_path: str, n_pages: int = 3,
                        dpi: int = 110) -> list[str]:
    """Render the first *n_pages* of a PDF to PNG previews for inspection.

    Returns the list of PNG paths written (empty if PyMuPDF is unavailable).
    This exists to enforce the hard-won lesson: ALWAYS look at the rendered
    output. A logo overlapping the title, an oversized chart, or CJK tofu are
    invisible to size/exit-code checks but obvious in a 1-second glance at a PNG.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        sys.stderr.write(
            "[WARN] PyMuPDF (fitz) not installed — cannot render visual "
            "previews. Install with: pip install pymupdf\n"
        )
        return []
    out_paths = []
    try:
        doc = fitz.open(pdf_path)
        stem = Path(pdf_path).with_suffix("")
        for i in range(min(n_pages, len(doc))):
            pix = doc[i].get_pixmap(dpi=dpi)
            out = f"{stem}_preview_p{i + 1}.png"
            pix.save(out)
            out_paths.append(out)
        doc.close()
    except Exception as exc:
        sys.stderr.write(f"[WARN] Preview rendering failed: {exc}\n")
    return out_paths


def _extract_title(md_path: Path) -> Optional[str]:
    """Extract report title from the first H1 heading in markdown."""
    try:
        first_lines = md_path.read_text(encoding="utf-8")[:2000]
        m = re.search(r'^#\s+(.+)$', first_lines, re.MULTILINE)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return None


def _print_deps_table(deps: dict) -> None:
    """Print a formatted dependency table."""
    print("\nDependency check:\n")
    print(f"{'Component':<20} {'Installed':<12} {'Details'}")
    print("-" * 60)
    for name, info in deps.items():
        installed = "YES" if info.get("installed") else "NO"
        details = ""
        if name == "cjk_fonts" and info.get("found"):
            details = ", ".join(info["found"][:3])
        elif name == "cjk_fonts":
            details = ("No CJK fonts detected. "
                       "Install fonts-noto-cjk (Linux) or equivalent.")
        print(f"{name:<20} {installed:<12} {details}")

    # Engine recommendation
    engine = detect_engine()
    print(f"\nRecommended engine: {engine or 'NONE — install dependencies'}")

    # Platform-specific install hints
    if not deps.get("weasyprint", {}).get("installed"):
        print("\nTo install WeasyPrint:")
        if sys.platform == "linux":
            print("  apt install libpango-1.0-0 libcairo2 libharfbuzz0b")
            print("  pip install weasyprint")
        elif sys.platform == "darwin":
            print("  brew install weasyprint")
        elif sys.platform == "win32":
            print("  Install GTK3 runtime: "
                  "github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer")
            print("  pip install weasyprint")
            print("  OR use Playwright fallback: pip install playwright && playwright install chromium")


# ── CLI ─────────────────────────────────────────────────────────────────────

def _main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Render equity research Markdown report to professional PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python render_pdf.py report.md --out report.pdf
  python render_pdf.py report.md --out report.pdf --cjk --toc
  python render_pdf.py report.md --out report.pdf --style bw --extra-css custom.css
  python render_pdf.py report.md --out report.pdf --chart-index figs/chart-index.json
  python render_pdf.py --check-deps
""",
    )
    ap.add_argument(
        "input", nargs="?", help="Path to the Markdown report file.",
    )
    ap.add_argument(
        "--out", dest="out_path", help="Output PDF path (required unless --check-deps).",
    )
    ap.add_argument(
        "--style", default=DEFAULT_STYLE,
        choices=["professional", "bw", "internal"],
        help="CSS style template (default: professional).",
    )
    ap.add_argument(
        "--engine", default="auto",
        choices=["auto", "weasyprint", "playwright", "pandoc-weasyprint", "pandoc-only"],
        help="PDF engine (default: auto-detect).",
    )
    ap.add_argument(
        "--figs-dir", default="figs",
        help="Directory containing chart SVGs/PNGs (default: figs/).",
    )
    ap.add_argument(
        "--cjk", action="store_true", default=True,
        help="Enable CJK font support (default: on).",
    )
    ap.add_argument(
        "--no-cjk", dest="cjk", action="store_false",
        help="Disable CJK font support.",
    )
    ap.add_argument(
        "--toc", action="store_true",
        help="Generate table of contents for reports >10 pages.",
    )
    ap.add_argument(
        "--html", dest="html_out",
        help="Save intermediate HTML to this path.",
    )
    ap.add_argument(
        "--extra-css", dest="extra_css",
        help="Additional CSS file to inject.",
    )
    ap.add_argument(
        "--lang", default="en",
        help="HTML lang attribute (default: en; use zh for Chinese reports).",
    )
    ap.add_argument(
        "--no-inline-svg", dest="no_inline_svg", action="store_true",
        help="Disable SVG inlining (use <img> tags instead).",
    )
    ap.add_argument(
        "--max-inline-size", dest="max_inline_size", type=float, default=1.0,
        help="Maximum combined inline SVG size in MB before warning (default: 1.0).",
    )
    ap.add_argument(
        "--chart-index", dest="chart_index",
        help="Path to chart-index.json for Type-A programmatic chart "
             "coverage verification. Required charts missing -> "
             "PRE-RENDER FAIL. Optional charts missing -> WARNING.",
    )
    ap.add_argument(
        "--logo", dest="logo",
        help="Path to a company logo image. Rendered in the page top-margin on "
             "every page (Chromium headerTemplate / WeasyPrint running element). "
             "Embedded as base64 — survives non-ASCII working directories.",
    )
    ap.add_argument(
        "--logo-height", dest="logo_height", type=float, default=0.95,
        help="Logo height in cm (default: 0.95). The top page margin auto-grows "
             "to logo height + 1.4cm so a larger logo never overlaps body text.",
    )
    ap.add_argument(
        "--verify-visual", dest="verify_visual", action="store_true",
        help="After rendering, write PNG previews of the first pages (needs "
             "PyMuPDF) so the layout can be visually inspected. Strongly "
             "recommended whenever a logo or new chart layout is involved.",
    )
    ap.add_argument(
        "--check-deps", action="store_true",
        help="Check and print dependency status, then exit.",
    )

    args = ap.parse_args(argv)

    if args.check_deps:
        deps = check_dependencies()
        _print_deps_table(deps)
        return 0

    if not args.input:
        ap.error("INPUT is required (or use --check-deps)")
        return 2

    if not args.out_path:
        ap.error("--out is required")
        return 2

    result = render(
        md_path=args.input,
        pdf_path=args.out_path,
        style=args.style,
        engine=args.engine,
        figs_dir=args.figs_dir,
        cjk=args.cjk,
        toc=args.toc,
        html_out=args.html_out,
        extra_css=args.extra_css,
        lang=args.lang,
        chart_index=args.chart_index,
        no_inline_svg=args.no_inline_svg,
        max_inline_size=args.max_inline_size,
        logo=args.logo,
        logo_height_cm=args.logo_height,
        verify_visual=args.verify_visual,
    )

    if result:
        print(f"\nDone: {result}")
        return 0
    else:
        sys.stderr.write("\n[FAILED] PDF generation did not succeed.\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(_main())
