# PDF Rendering Pipeline — Adversarial Review Fixes

Date: 2026-06-28
Source: Adversarial cross-model review (8-point checklist)
Status: Must-fix before Wave 8 ships

---

## Fix 1: Runtime Fallback Chaining

### Problem

The current `render()` function selects ONE engine via `detect_engine()` and
calls it. If that single engine fails (e.g. WeasyPrint segfaults on a mixed
GTK DLL environment), the pipeline returns `None` immediately — even though
Playwright is installed and could have succeeded.

### Required behavior

The `render()` function must iterate through ALL available engines in priority
order, trying each one. Only return `None` if EVERY engine fails. On success
with a non-primary engine, emit a `[WARN]` indicating the fallback was used.

### Engine priority (highest to lowest)

1. `pandoc-weasyprint` — Pandoc + WeasyPrint (fastest, best Pandoc templates)
2. `weasyprint` — WeasyPrint alone (best CSS typography)
3. `playwright` — Headless Chromium (most reliable, zero system deps)
4. `pandoc-only` — Pandoc standalone HTML (no PDF, generates HTML only)

### Code to add to `render_pdf.py`

Replace the engine selection and rendering block in the `render()` function
(approximately lines 766-801) with the following:

```python
# ── Engine Fallback Chain ────────────────────────────────────────────────
# Defined in priority order: best -> worst
_FALLBACK_CHAIN = [
    "pandoc-weasyprint",
    "weasyprint",
    "playwright",
    "pandoc-only",
]


def _try_render_with_engine(
    engine: str,
    html_doc: str,
    md_path_abs: Path,
    pdf_path: str,
    css: str,
    toc: bool,
) -> Optional[str]:
    """Attempt rendering with a specific engine. Returns pdf_path or None."""
    try:
        if engine == "weasyprint":
            return render_weasyprint(html_doc, pdf_path)
        elif engine == "playwright":
            return render_playwright(html_doc, pdf_path)
        elif engine == "pandoc-weasyprint":
            return render_pandoc_weasyprint(
                str(md_path_abs), pdf_path, css, toc=toc,
            )
        elif engine == "pandoc-only":
            html_out_path = pdf_path.replace(".pdf", ".html")
            subprocess.run(
                [
                    "pandoc", str(md_path_abs),
                    "--standalone", "--embed-resources",
                    "-o", html_out_path,
                ],
                check=True,
            )
            sys.stderr.write(
                f"[INFO] Pandoc-only: generated {html_out_path}\n"
                f"  To convert to PDF, install weasyprint and re-run.\n"
            )
            return html_out_path
    except Exception as exc:
        sys.stderr.write(
            f"[FALLBACK] Engine '{engine}' failed: {exc}\n"
        )
    return None


# ── Inside render(), replace lines 761-801 with: ─────────────────────────

    # Step 6: Render PDF with fallback chain
    result = None
    pdf_dir = Path(pdf_path).parent
    pdf_dir.mkdir(parents=True, exist_ok=True)

    # Determine which engines to try
    if engine == "auto":
        engines_to_try = _FALLBACK_CHAIN
    else:
        # User specified a specific engine — try that one only,
        # but also try fallbacks if the user-specified engine truly fails
        # (the user chose a preference, not a strict requirement)
        engines_to_try = [engine] + [
            e for e in _FALLBACK_CHAIN if e != engine
        ]

    # Check which engines are actually available before attempting
    available_engines = []
    for eng in engines_to_try:
        if eng == "weasyprint":
            if shutil.which("weasyprint") or _python_import_ok("weasyprint"):
                available_engines.append(eng)
        elif eng == "playwright":
            if _python_import_ok("playwright"):
                available_engines.append(eng)
        elif eng == "pandoc-weasyprint":
            if (shutil.which("weasyprint") or _python_import_ok("weasyprint")) \
                    and shutil.which("pandoc"):
                available_engines.append(eng)
        elif eng == "pandoc-only":
            if shutil.which("pandoc"):
                available_engines.append(eng)

    if not available_engines:
        sys.stderr.write(
            "[ERROR] No PDF engine available.\n"
            "  Install one of: weasyprint, playwright, or pandoc.\n"
            "  Run: python render_pdf.py --check-deps\n"
        )
        return None

    # Try each engine in priority order
    primary_engine = available_engines[0] if available_engines else None
    for idx, eng in enumerate(available_engines):
        print(f"Trying engine [{idx + 1}/{len(available_engines)}]: {eng}")
        result = _try_render_with_engine(
            eng, html_doc, md_path_abs, pdf_path, css, toc,
        )
        if result:
            if idx > 0:
                # Not the primary engine — warn that we fell back
                sys.stderr.write(
                    f"[WARN] Primary engine ({primary_engine}) failed. "
                    f"Fell back to {eng}.\n"
                )
            break
    else:
        # All engines failed
        sys.stderr.write(
            "[ERROR] All PDF engines failed.\n"
            "  Check dependencies: python render_pdf.py --check-deps\n"
        )
        return None
```

### Updated `detect_engine()` (add `pandoc-only` awareness)

```python
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
```

### Test coverage

See `tests/test_render_pdf.py`:
- `TestFallbackChain::test_fallback_chain_weasyprint_fails_playwright_tried`
- `TestFallbackChain::test_fallback_chain_all_fail_returns_none`
- `TestFallbackChain::test_fallback_engine_order_respected`

---

## Fix 2: SVG Inline Size Check

### Problem

When a report contains many large SVG charts (or charts with embedded
raster data), the combined inline SVG content in a single HTML document
can exceed 1MB. This causes:
- Slower render times (WeasyPrint parses all SVG into DOM)
- Bloated PDF output
- Memory pressure during rendering

There is currently no check or warning for this condition. An operator
would only discover the issue when the PDF is already generated and
oversized.

### Required behavior

After `md_to_html()` produces the HTML body, calculate the total byte size
of all inline `<svg>` blocks. If the combined size exceeds a configurable
threshold (default: 1MB), emit a `[WARN]` with:
- Total inline SVG size in MB
- Number of SVG blocks found
- Recommendation to use `--no-inline-svg` or increase `--max-inline-size`

### New CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--no-inline-svg` | bool flag | `False` | Skip SVG inlining entirely — use `<img src="...">` tags instead. This avoids the 1MB check entirely. |
| `--max-inline-size` | float | `1.0` | Maximum combined inline SVG size in MB before warning. Set to 0 to disable the check. Set higher for reports with many charts. |

### Code to add to `render_pdf.py`

Add this function after the `md_to_html()` block (after approximately line 193):

```python
# ── SVG Inline Size Check ─────────────────────────────────────────────────

# Default maximum combined inline SVG bytes before warning
DEFAULT_MAX_INLINE_SVG_MB = 1.0


def _check_inline_svg_size(html_body: str, max_size_mb: float = 1.0) -> dict:
    """Check the combined size of all inline <svg> blocks in HTML.

    Args:
        html_body: HTML body content (after md_to_html processing).
        max_size_mb: Maximum combined size in MB before warning.

    Returns:
        dict with keys: total_bytes, total_mb, svg_count, exceeds_threshold,
        threshold_mb.
    """
    svg_blocks = re.findall(r'<svg[^>]*>.*?</svg>', html_body, re.DOTALL)
    svg_count = len(svg_blocks)
    total_bytes = sum(len(block.encode("utf-8")) for block in svg_blocks)
    total_mb = total_bytes / (1024 * 1024)
    threshold_bytes = int(max_size_mb * 1024 * 1024)
    exceeds = total_bytes > threshold_bytes

    result = {
        "total_bytes": total_bytes,
        "total_mb": round(total_mb, 2),
        "svg_count": svg_count,
        "exceeds_threshold": exceeds,
        "threshold_mb": max_size_mb,
    }

    if exceeds and max_size_mb > 0:
        sys.stderr.write(
            f"[WARN] Combined inline SVG size ({total_mb:.1f} MB, "
            f"{svg_count} blocks) exceeds {max_size_mb:.1f} MB threshold.\n"
            f"  Consider:\n"
            f"    - Using --no-inline-svg to reference files instead\n"
            f"    - Setting --max-inline-size higher if large SVGs are expected\n"
            f"    - Simplifying chart SVGs (reduce data points, simplify paths)\n"
        )

    return result
```

### Modify `render()` function signature to accept new parameters

Add to the `render()` function signature (around line 688):

```python
def render(md_path: str, pdf_path: str,
           style: str = DEFAULT_STYLE,
           engine: str = "auto",
           figs_dir: str = "figs",
           cjk: bool = True,
           toc: bool = False,
           html_out: Optional[str] = None,
           extra_css: Optional[str] = None,
           lang: str = "en",
           inline_svg: bool = True,          # NEW
           max_inline_size_mb: float = 1.0,  # NEW
           ) -> Optional[str]:
```

### Modify the HTML generation step in `render()` to use the new flag

Change the call to `md_to_html()` (around line 746):

```python
    # Step 3: Convert Markdown -> HTML
    html_body = md_to_html(md_text, str(figs_dir_abs), inline_svg=inline_svg)

    # Step 3.5: Check SVG inline size (only when inline_svg is True)
    if inline_svg:
        svg_size_info = _check_inline_svg_size(html_body, max_inline_size_mb)
        if svg_size_info["svg_count"] > 0:
            print(
                f"SVG inline: {svg_size_info['svg_count']} blocks, "
                f"{svg_size_info['total_mb']:.1f} MB "
                f"({'OK' if not svg_size_info['exceeds_threshold'] else 'WARN'})"
            )
```

### Add new CLI arguments to `_main()`

In the argparse setup (around line 864), add:

```python
    ap.add_argument(
        "--no-inline-svg", dest="inline_svg", action="store_false",
        default=True,
        help="Skip SVG inlining — use <img> tags instead of inline <svg>.",
    )
    ap.add_argument(
        "--max-inline-size", dest="max_inline_size",
        type=float, default=1.0,
        help=(
            "Maximum combined inline SVG size in MB before warning "
            "(default: 1.0). Set to 0 to disable."
        ),
    )
```

And pass them to `render()` (around line 929):

```python
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
        inline_svg=args.inline_svg,           # NEW
        max_inline_size_mb=args.max_inline_size,  # NEW
    )
```

### Test coverage

See `tests/test_render_pdf.py`:
- `TestSVGInlineSize::test_svg_inline_size_below_threshold`
- `TestSVGInlineSize::test_svg_inline_size_exceeds_threshold_triggers_warning`
- `TestSVGInlineSize::test_svg_inline_size_check_zero_svgs`
- `TestSVGInlineSize::test_svg_inline_custom_threshold`

---

## Fix 3: chart-index.json Consumption

### Problem

The pipeline currently has NO mechanism to verify that all required charts
are actually embedded in the rendered document. The chart generation step
(`charts.py`) produces a `chart-index.json` listing which charts were rendered
for a given ticker, but the PDF pipeline never consumes this file.

This means:
- A missing chart silently produces a broken PDF
- The adversarial reviewer must manually verify all charts are present
  (criterion #1 of the 8-point checklist)
- No automated quality gate for chart completeness

### Required behavior

The `render()` function accepts a `--chart-index PATH` flag pointing to a
`chart-index.json` file (produced by the chart generation step). Before
rendering, `verify_chart_coverage()` cross-references the chart-index entries
against chart references found in the markdown.

### chart-index.json format

```json
{
  "ticker": "MU",
  "date": "2026-06-27",
  "required": [
    "MU_montecarlo",
    "MU_football",
    "MU_breakeven"
  ],
  "optional": [
    "MU_terminal",
    "MU_tornado"
  ],
  "meta": {
    "generator": "charts.py",
    "n_trials": 10000,
    "price": 1134.00
  }
}
```

### Verdict logic

| Condition | Verdict | Action |
|-----------|---------|--------|
| All `required` charts found in markdown | **PASS** | Continue rendering |
| Any `required` chart missing | **PRE-RENDER FAIL** | Abort with error listing missing charts |
| `optional` chart missing | **WARNING** | Continue, but warn that optional chart was not referenced |
| No `--chart-index` flag provided | **SKIP** | Backward-compatible: skip check, continue rendering |

### Code to add to `render_pdf.py`

Add this function after the `_extract_title()` function (after approximately
line 814):

```python
# ── Chart Coverage Verification ───────────────────────────────────────────

def _find_chart_refs_in_markdown(md_text: str) -> set[str]:
    """Extract chart stem names referenced in markdown.

    Matches: ![alt](figs/STEM) or ![alt](figs/STEM.svg) or ![alt](figs/STEM.png)
    Returns a set of stem names (without extension or figs/ prefix).
    """
    chart_ref_re = re.compile(
        r'!\[([^\]]*)\]\(figs/([^)\s]+?)(?:\.(?:svg|png))?\)',
        re.IGNORECASE,
    )
    stems = set()
    for m in chart_ref_re.finditer(md_text):
        stems.add(m.group(2))
    return stems


def load_chart_index(chart_index_path: str) -> Optional[dict]:
    """Load and validate a chart-index.json file.

    Returns None if file is missing or malformed (with a warning).
    """
    path = Path(chart_index_path)
    if not path.exists():
        sys.stderr.write(
            f"[WARN] Chart index not found: {chart_index_path}. "
            f"Skipping chart coverage verification.\n"
        )
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        sys.stderr.write(
            f"[WARN] Failed to parse chart index {chart_index_path}: {exc}. "
            f"Skipping chart coverage verification.\n"
        )
        return None

    # Validate structure
    if not isinstance(data, dict):
        sys.stderr.write(
            f"[WARN] Chart index {chart_index_path} is not a JSON object. "
            f"Skipping.\n"
        )
        return None

    # Ensure required keys exist with sensible defaults
    if "required" not in data:
        data["required"] = []
    if "optional" not in data:
        data["optional"] = []

    return data


def verify_chart_coverage(
    chart_index: dict,
    markdown_text: str,
) -> dict:
    """Cross-reference chart-index against chart references in markdown.

    Args:
        chart_index: Loaded chart-index.json data (dict with 'required' and
                     'optional' keys, each a list of chart stem names).
        markdown_text: The full markdown content of the report.

    Returns:
        dict with keys:
          - passed (bool): True if all required charts are present.
          - missing_required (list[str]): Required chart stems not in markdown.
          - missing_optional (list[str]): Optional chart stems not in markdown.
          - total_required (int)
          - total_optional (int)
          - found_in_markdown (list[str]): All chart stems found in markdown.
    """
    required = set(chart_index.get("required", []))
    optional = set(chart_index.get("optional", []))
    all_expected = required | optional

    found = _find_chart_refs_in_markdown(markdown_text)

    missing_required = sorted(required - found)
    missing_optional = sorted(optional - found)

    passed = len(missing_required) == 0

    result = {
        "passed": passed,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "total_required": len(required),
        "total_optional": len(optional),
        "found_in_markdown": sorted(found),
    }

    # Log results
    ticker = chart_index.get("ticker", "UNKNOWN")
    print(f"\nChart coverage verification for {ticker}:")
    print(f"  Required: {len(required)} charts expected")
    print(f"  Optional: {len(optional)} charts optionally expected")
    print(f"  Found in markdown: {len(found)} chart references")

    if missing_required:
        print(f"  MISSING REQUIRED: {', '.join(missing_required)}")
        sys.stderr.write(
            f"[FAIL] Chart coverage: {len(missing_required)} required "
            f"chart(s) missing from report:\n"
        )
        for stem in missing_required:
            sys.stderr.write(f"  - {stem}\n")
        sys.stderr.write(
            f"  Ensure ![]() references exist in the markdown for "
            f"these charts, or regenerate the chart index if unused.\n"
        )

    if missing_optional:
        print(f"  MISSING OPTIONAL: {', '.join(missing_optional)}")
        sys.stderr.write(
            f"[WARN] Chart coverage: {len(missing_optional)} optional "
            f"chart(s) not referenced in report:\n"
        )
        for stem in missing_optional:
            sys.stderr.write(f"  - {stem} (optional — generating anyway)\n")

    if passed and not missing_required and not missing_optional:
        print("  Verdict: PASS — all charts accounted for.")
    elif passed:
        print("  Verdict: WARNING — optional charts missing, required OK.")
    else:
        print("  Verdict: PRE-RENDER FAIL — required charts missing.")

    return result
```

### Modify `render()` to accept and use `--chart-index`

Add `chart_index_path` parameter to the `render()` function signature:

```python
def render(md_path: str, pdf_path: str,
           style: str = DEFAULT_STYLE,
           engine: str = "auto",
           figs_dir: str = "figs",
           cjk: bool = True,
           toc: bool = False,
           html_out: Optional[str] = None,
           extra_css: Optional[str] = None,
           lang: str = "en",
           inline_svg: bool = True,
           max_inline_size_mb: float = 1.0,
           chart_index_path: Optional[str] = None,  # NEW
           ) -> Optional[str]:
```

In the `render()` body, after reading the markdown (after Step 2, around line
742), add the chart coverage check:

```python
    # Step 2: Read markdown
    md_text = md_path_abs.read_text(encoding="utf-8")
    print(f"Markdown: {len(md_text)} chars")

    # Step 2.5: Verify chart coverage (if chart-index provided)
    if chart_index_path:
        chart_index = load_chart_index(chart_index_path)
        if chart_index is not None:
            coverage = verify_chart_coverage(chart_index, md_text)
            if not coverage["passed"]:
                # Required charts missing — abort rendering
                sys.stderr.write(
                    "[BLOCK] Chart coverage verification failed. "
                    "Fix missing chart references and re-run.\n"
                )
                return None
```

### Add CLI argument for `--chart-index`

In the argparse setup, add:

```python
    ap.add_argument(
        "--chart-index", dest="chart_index_path",
        help=(
            "Path to chart-index.json (produced by the chart generation step). "
            "When provided, all required charts are verified present in the "
            "markdown before rendering. Missing required charts abort with "
            "PRE-RENDER FAIL."
        ),
    )
```

And pass to `render()`:

```python
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
        inline_svg=args.inline_svg,
        max_inline_size_mb=args.max_inline_size,
        chart_index_path=args.chart_index_path,  # NEW
    )
```

### Test coverage

See `tests/test_render_pdf.py`:
- `TestChartCoverageVerification::test_all_required_charts_present`
- `TestChartCoverageVerification::test_missing_required_chart_returns_fail`
- `TestChartCoverageVerification::test_optional_missing_returns_warning_not_fail`
- `TestChartCoverageVerification::test_empty_chart_index_always_passes`
- `TestChartCoverageVerification::test_chart_with_extension_in_markdown_matches_stem_in_index`

See `tests/conftest.py`:
- `sample_chart_index` fixture
- `sample_chart_index_json_file` fixture

---

## Integration Notes

### Fix ordering

Apply the fixes in this order:
1. **Fix 3 (chart-index)** first — adds the pre-render gate that prevents
   rendering with missing charts, which catches problems before they reach
   the render engines.
2. **Fix 2 (SVG size)** next — adds the inline SVG size warning, which helps
   diagnose oversized PDFs before they are produced.
3. **Fix 1 (fallback chaining)** last — ensures the pipeline survives engine
   failures by trying alternatives.

### Backward compatibility

All three fixes are backward-compatible:
- **Fix 1:** Existing behavior (single engine) is preserved as the first
  attempt in the chain.
- **Fix 2:** Default threshold (1MB) only warns; existing reports produce
  identical output if under threshold.
- **Fix 3:** `--chart-index` is optional. If not provided, the check is
  skipped — existing workflows continue unchanged.

### New dependencies

None. All fixes use only modules already imported by `render_pdf.py`:
`re`, `json`, `sys`, `subprocess`, `shutil`, `pathlib`.

### Updated CLI usage examples

```bash
# Standard render with all safety checks
python render_pdf.py report.md --out report.pdf \
    --chart-index chart-index.json \
    --max-inline-size 2.0

# Render with chart coverage only (skip SVG size check)
python render_pdf.py report.md --out report.pdf \
    --chart-index chart-index.json \
    --max-inline-size 0

# Render without inlining (avoids 1MB check entirely)
python render_pdf.py report.md --out report.pdf \
    --no-inline-svg

# Check dependencies
python render_pdf.py --check-deps
```

### Updated render() interface (post-fix)

```python
def render(
    md_path: str,
    pdf_path: str,
    style: str = "professional",
    engine: str = "auto",
    figs_dir: str = "figs",
    cjk: bool = True,
    toc: bool = False,
    html_out: Optional[str] = None,
    extra_css: Optional[str] = None,
    lang: str = "en",
    inline_svg: bool = True,
    max_inline_size_mb: float = 1.0,
    chart_index_path: Optional[str] = None,
) -> Optional[str]:
```

---

## Cross-References

- Adversarial review gate: 8-point checklist in `SKILL.md` (Quality gates section)
- Chart generation: `scripts/charts.py`
- Report linting: `scripts/report_lint.py`
- Tests: `tests/test_render_pdf.py`, `tests/conftest.py`

---

# Round 2 — Logo, Image-Path, and Robustness Fixes

Date: 2026-06-29
Source: Real BYD (1211.HK) report generation on a Windows host with a non-ASCII
working directory (`D:\研报生成`). Each fix below maps to a concrete failure
observed and corrected in that session. Status: APPLIED to `render_pdf.py`,
`templates/professional.css`, and `SKILL.md`.

## Fix 4: Logo placement — headerTemplate, not `position: fixed`

### Problem (observed)
A company logo placed with CSS `position: fixed; top: 0.4cm; left: 0.4cm`
overlapped the H1 title on page 1 and the first H2 on every later page.
Widening the page top margin did NOT help — the logo moved down with the text.

### Root cause
In Chromium's print pipeline, `position: fixed` anchors to the **content box**
(inside the print margins), not the physical page edge. So the logo always lands
on the first line of body text, regardless of margin size.

### Fix (applied)
- **Chromium/Playwright:** render the logo in the native `headerTemplate`
  (`display_header_footer=True`). It paints inside the reserved top-margin box,
  isolated from body text.
- **WeasyPrint:** inject `position: running(logoRun)` + `@page { @top-left {
  content: element(logoRun) } }`.
- Top margin auto-grows: `top = max(2.5cm, logo_height + 1.4cm)` so a larger
  logo can never reintroduce overlap.
- New params/flags: `render(logo=, logo_height_cm=)`, CLI `--logo`,
  `--logo-height`. See `render_playwright()` and `_inject_weasyprint_logo()`.

## Fix 5: Base64-embed all images (non-ASCII path trap)

### Problem (observed)
Charts and the logo rendered blank in the PDF — no error, no log. Working dir
was `D:\研报生成`.

### Root cause
Chromium silently fails to load images referenced by `file://`/relative paths
when the path contains non-ASCII characters. `_resolve_charts()` previously
emitted `<img src="figs/...">` for PNG charts.

### Fix (applied)
`_img_to_data_uri()` base64-embeds every image as a `data:` URI. `_resolve_charts()`
uses it for the PNG branch (inline SVG was already path-free). The logo is
embedded the same way. Engine-neutral: data URIs work in WeasyPrint too.

## Fix 6: Chart size ceiling for A4

### Problem (observed)
A 9×5.2in @144dpi raster chart filled most of an A4 page.

### Fix (applied)
`templates/professional.css`: `figure img, figure svg.plot, svg.plot` now carry
`max-height: 8.5cm; object-fit: contain` (in addition to `max-width: 100%`).

## Fix 7: Graceful engine detection when WeasyPrint import fails

### Problem (observed)
`--check-deps` and auto engine detection CRASHED on Windows: importing
`weasyprint` raises `OSError: cannot load library 'libpango-1.0-0'` (GTK/Pango
not installed), and `_python_import_ok()` only caught `ImportError`.

### Fix (applied)
`_python_import_ok()` now catches broad `Exception` and returns `False` — so a
library that imports-but-fails-to-load-native-deps is treated as unavailable and
the chain falls back to Playwright instead of crashing.

## Fix 8: Visual self-verification (`--verify-visual`)

### Problem (process)
Layout bugs (logo overlap, oversized charts, CJK tofu, split figures) are
invisible to file-size/exit-code checks. They were "fixed" blindly by tweaking
CSS without looking — wasting cycles and shipping an overlap bug.

### Fix (applied)
`render_pdf_previews()` renders the first pages of the output PDF to PNG via
PyMuPDF; `render(verify_visual=True)` / CLI `--verify-visual` invokes it. The
agent/reviewer MUST open the PNGs and inspect the Type-B criteria. Rule:
**render, look, then decide — never tweak layout blind.**

### Process lesson (the meta-fix)
The biggest time sink was adjusting margins/CSS without viewing the rendered
page. Mandate: for ANY layout/logo/chart change, render to PNG and visually
verify before declaring done.
