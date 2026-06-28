---
name: equity-research-analyst/generate-pdf
description: >
  Render the finished equity research report to a professional-grade typographic PDF
  with embedded vector charts, CJK+Latin font handling, reader spreads, rating box,
  running headers/footers, and page-numbered auto-generated table of contents.
  The final output step — produces a distribution-ready document from the gate-passed
  Markdown report and pre-rendered chart SVGs. Step 11 of Mode A (Wave 8).
  Also available for Mode B audit memos and Mode C update memos.
license: MIT
---

# Generate PDF

**Pipeline position:** STEP 11 of Mode A (Wave 8). Final output step — renders the
gate-passed Markdown report into a polished, professional PDF suitable for investor
distribution, archival, and print. Runs after `/self-audit` passes and the adversarial
reviewer signs off.

## Architecture overview

```
Input                           Process                            Output
─────                           ───────                            ──────
MU_research_report.md   ──┐
figs/*.svg, *.png       ──┤  1. Detect available PDF engines
assumptions.json        ──┤  2. Resolve chart placeholders -> <img>
                          ├─ 3. MD -> styled HTML (Pandoc or Python)
                          ├─ 4. HTML -> PDF (primary or fallback engine)
                          └─ 5. Quality-gate verification
                                                                    ├─ TICKER_report.pdf
                                                                    └─ TICKER_report.html (optional)
```

### Input

| Artifact | Source | Required | Notes |
|----------|--------|----------|-------|
| `TICKER_report.md` | `/write-report` -> `/self-audit` gate | Yes | UTF-8, <50KB prose body |
| `figs/*.svg` | `/run-valuation` -> `charts.py --kind ... --out figs/` | Yes | Vector charts, resolution-independent |
| `figs/*.png` | Same as above (charts.py dual-output) | No | Raster fallback if SVG fails |
| `assumptions.json` | `/build-assumptions` | No | Used for metadata population |

### Output

- `TICKER_report.pdf` — the final, gate-passed, distribution-ready document
- `TICKER_report.html` — optional web-viewable version (same content, no print CSS)

---

## Pipeline architecture — three rendering paths

The skill auto-detects which PDF engine is available and selects the best path.
A fallback chain ensures the pipeline never dead-ends on a missing system dependency.

### Path A: WeasyPrint (PRIMARY — best typography)

```
Markdown --[Python markdown]--> HTML --[WeasyPrint]--> PDF
                                      |
                              Professional CSS template
                              (see assets/professional.css)
```

**When:** WeasyPrint is installed and functional (`weasyprint --version` exits 0).
**Quality:** Best CSS-based typography, native SVG embedding (not rasterized),
`@page` headers/footers, Harfbuzz CJK subsetting (v63+).

### Path B: Playwright browser (FALLBACK 1 — zero system deps)

```
Markdown --[Python markdown]--> HTML --[Playwright headless Chrome]--> PDF
```

**When:** WeasyPrint unavailable, but `playwright` Python package + Chromium
are installed.
**Quality:** Reliable page-breaking, full CSS support, always works. No CJK font
embedding unless fonts are present on the system. Headers/footers via CSS
`@page` margin boxes (Chromium 115+ supports this). Charts rendered as
embedded images.

### Path C: Pandoc direct (FALLBACK 2 — if Pandoc available)

```
Markdown --[pandoc --pdf-engine=weasyprint]--> PDF
```

**When:** Pandoc is installed. Fastest two-step path when both Pandoc and
WeasyPrint coexist.
**Quality:** Same as Path A, but Pandoc handles the MD->HTML conversion with
its own template system.

### Engine detection (auto-select)

```python
def detect_engine() -> str:
    """Return 'weasyprint' | 'playwright' | 'pandoc-weasyprint' | None."""
    import shutil
    # 1. Check weasyprint
    if shutil.which("weasyprint") or _python_import_ok("weasyprint"):
        if shutil.which("pandoc"):
            return "pandoc-weasyprint"  # fastest
        return "weasyprint"
    # 2. Check playwright
    if _python_import_ok("playwright"):
        return "playwright"
    # 3. Pandoc alone (generates HTML only — user must convert)
    if shutil.which("pandoc"):
        return "pandoc-only"
    return None
```

**Priority logic:** Pandoc+WeasyPrint > WeasyPrint alone > Playwright > Pandoc-only.

### System dependency requirements by platform

| Dependency | Debian/Ubuntu | macOS | Windows |
|-----------|---------------|-------|---------|
| Pango/Cairo/Harfbuzz | `apt install libpango-1.0-0 libcairo2 libharfbuzz0b libgdk-pixbuf2.0-0` | Bundled with weasyprint Homebrew | Requires GTK3+ runtime |
| Pandoc | `apt install pandoc` | `brew install pandoc` | `choco install pandoc` |
| CJK fonts | `apt install fonts-noto-cjk` | Bundled (PingFang SC) | Bundled (Microsoft YaHei) |
| Chromium (Playwright) | `playwright install chromium` | Same | Same |

**Docker path (recommended for CI/reproducibility):** Use `python:3.12-slim-bookworm`
base + `apt install libpango-1.0-0 libcairo2 libharfbuzz0b fonts-noto-cjk pandoc`
+ `pip install weasyprint~=65.0`. Total image: ~500MB.

---

## PDF specification

### Page geometry

| Parameter | Value |
|-----------|-------|
| Page size | A4 (210mm x 297mm) |
| Top margin | 2.2cm |
| Bottom margin | 2.4cm |
| Left margin | 2.4cm |
| Right margin | 2.4cm |

### Typography stack

```
CSS font-family stack:

  --font-body:   "Noto Serif CJK SC", "Source Serif 4", Georgia,
                 "SimSun", serif

  --font-heading: "Noto Sans CJK SC", "Source Sans 3", Helvetica,
                  "Microsoft YaHei", sans-serif

  --font-mono:    "Cascadia Code", "Source Code Pro", Consolas,
                  "Courier New", monospace

  --font-display: "Noto Sans CJK SC", "Source Sans 3",
                  "Microsoft YaHei", sans-serif
                  (used for rating box, page headers, figure caps)
```

**Sizes and leading:**
- Body: `11pt`, `line-height: 1.75` (CJK needs more vertical space)
- H1: `18pt bold`, H2: `14pt bold`, H3: `12pt semibold`
- Mono (tables, code): `9.5pt`, `line-height: 1.5`
- Figure captions: `8.5pt`, `color: #6b7280`
- Page header: `7.5pt`, uppercase, tracking `0.05em`
- Page footer: `7.5pt`, `color: #6b7280`
- Disclaimer: `8pt`, `color: #6b7280`, `line-height: 1.4`

### Color palette

```css
:root {
  --ink:        #1a1e2b;   /* body text — near-black navy */
  --ink-light:  #4a5568;   /* secondary text */
  --accent:     #1a3a6b;   /* navy accent — headers, rules, rating box border */
  --accent-dim: #2d5a9e;   /* lighter navy for hover states, table headers */
  --surface:    #f8fafc;   /* rating box background */
  --rule:       #cbd5e1;   /* horizontal rules, table borders */
  --rule-light: #e2e8f0;   /* subtle separators */
  --up:         #15803d;   /* green — undervalued, BUY signals */
  --down:       #b91c1c;   /* red — overvalued, SELL signals */
  --neutral:    #6b7280;   /* gray — neutral ratings, meta */
}
```

**B/W print compatibility:** All semantic information (rating, price position,
chart data) MUST be distinguishable in grayscale. Rule: lines, markers, and
labels carry meaning — color is reinforcement only. Test by converting to
grayscale before shipping.

### Rating box (first page, prominent)

The rating box is the single most important visual element on page 1. It is
NOT buried in prose — it is a styled box, set apart, immediately visible.

```
+-------------------------------------------------------------+
|                                                             |
|  NVIDIA Corporation                        Nasdaq: NVDA     |
|  -------------------------------------------------------   |
|                                                             |
|  RATING        REDUCE / SELL                                |
|  INTRINSIC     ~ $240 / share                               |
|  PRICE         $409.00              (2023-06-10)            |
|  DOWNSIDE      ~ 40%   to intrinsic value                   |
|  PRICE %ILE    94th    of simulated value distribution       |
|                                                             |
|  THESIS                                                      |
|  NVIDIA is a genuinely exceptional business that, at $409,   |
|  is priced for a future in which almost everything goes      |
|  right. An upbeat intrinsic valuation produces a value of    |
|  roughly $240 per share, about 40% below the current price.  |
|  The rating is a reflection of price, not of the company.    |
|                                                             |
|  MoS BUY-BAND   Accumulate <= $190  |  Fair ~ $240          |
|                 Rich above $310                             |
|                                                             |
+-------------------------------------------------------------+
```

**CSS implementation:** A `div.rating-box` with `border: 2pt solid var(--accent)`,
`background: var(--surface)`, `padding: 18pt 22pt`, `border-radius: 4pt`.
Rating label in bold navy, value in dark ink, thesis in body font at 10pt.

### Running headers

```
Left page:   ---  NVIDIA Corporation (NVDA)  ---
Right page:  ---  Equity Research  ---  June 2023  ---
```

Implemented via CSS `@top-left` / `@top-right` with `string-set` on the title
heading.

### Running footers

```
Center:       Page X of Y
```

Implemented via CSS `@bottom-center { content: "Page " counter(page) " of " counter(pages); }`.

### Table of contents

Auto-generated if report exceeds 10 pages. Generated from H1/H2 headings at
the start of the document (after the rating box). Cannot be generated purely
in CSS — needs either:
- Pandoc `--toc` flag (Path C)
- Python TOC extraction from HTML heading structure (Paths A, B)

### Disclaimer

Last page, separated by a horizontal rule:
> *This analysis is for educational and informational purposes only and does not
> constitute personalized investment advice. Inputs as of [date]; valuation is
> sensitive to assumptions, the cost of capital most of all. Past performance
> does not guarantee future results.*

Font: `8pt`, color `var(--neutral)`, `line-height: 1.4`.

---

## Chart embedding strategy

### Vector-first principle

ALWAYS embed charts as **SVG** (not PNG). SVG is resolution-independent,
small file size, and renders as vector paths in WeasyPrint — producing
sharp charts at any zoom level and cleanly separating from text.

### Chart placeholder syntax in markdown

The report author writes chart placeholders using the **canonical flat format**.
The PDF script resolves these to actual `<img>` tags during HTML generation.

**Canonical markdown image syntax (extension-less, preferred):**

```markdown
![Monte Carlo value distribution](figs/NVDA_montecarlo)
![Breakeven heatmap](figs/NVDA_breakeven)
```

The canonical format is `![](figs/{TICKER}_{kind})` where:
- `{TICKER}` is the company ticker (e.g., `NVDA`, `9988.HK`, `BRK.A`)
- `{kind}` is the chart type: `montecarlo`, `breakeven`, `football`, `tornado`, or `terminal`
- Path is flat: `figs/` directly, **no ticker subdirectory**
- **No file extension** in the markdown reference — the PDF engine resolves `.svg` first, then `.png`

Charts are generated by `charts.py --ticker {TICKER} --kind {kind} --out figs/`
and output as both `figs/{TICKER}_{kind}.svg` and `figs/{TICKER}_{kind}.png`.

**Also accepted (backward compatible):**

```markdown
![Monte Carlo value distribution](figs/NVDA_montecarlo.svg)
```

The report writer places the `![](...)` reference at the correct position
in the prose. The PDF script:
1. Detects `![](figs/{TICKER}_{kind})` references in the markdown (CHART_RE)
2. Verifies the file exists, trying `.svg` first, then `.png`
3. Inlines the SVG content as raw `<svg>` in the HTML (preferred for WeasyPrint)
4. Falls back to `<img src="figs/NVDA_montecarlo.svg">` if inline fails
5. If SVG is missing, tries the PNG equivalent
6. If neither exists, inserts a placeholder note and flags the quality gate

**Inline SVG preference:** WeasyPrint natively translates SVG paths into PDF
content stream operators — **not rasterized**. Inlining SVG means the PDF has
zero external file dependencies.

### Chart placement rules

- Charts float within text flow at the position the markdown author placed them
- CSS: `img, svg.plot { max-width: 100%; page-break-inside: avoid; }`
- A chart should never break across a page — if it would, force a page break
  before the chart
- Charts may span the full text width; exceptionally wide charts (landscape
  sensitivity tables) may use a landscape page

### Auto-numbering

Charts receive automatic figure numbering via CSS counters:

```css
figure {
  counter-increment: figure-counter;
  page-break-inside: avoid;
  margin: 16pt 0;
}
figure figcaption::before {
  content: "Figure " counter(figure-counter) ": ";
  font-weight: 600;
}
```

The markdown writer writes:

```markdown
![Monte Carlo value distribution](figs/NVDA_montecarlo)

*Monte Carlo distribution of intrinsic value with the price at the 94th percentile.*
```

The PDF script wraps each image + following italic paragraph into
`<figure><img><figcaption>` during HTML conversion.

### Multi-page charts

For exceptionally long exhibits (e.g., 20-row breakeven heatmaps), the chart
starts on a fresh page with:
- A "continued" indicator in the footer
- Repeated column headers
- A note: "Figure X continued on next page"

Implemented via CSS `page-break-before: always` on a wrapper div with
`@top-center` repetition rule.

### Color space

**sRGB** is the default for all pipelines — financial research reports are
95% screen-distributed (PDF via email/portal).

For **B/W print compatibility**, charts MUST:
- Use distinguishable line styles (solid, dashed, dotted) — not just hue
- Have sufficient luminance contrast between elements
- Test: render to grayscale and verify all data is distinguishable

---

## Company logo & recurring header images

A company logo (or any per-page header image) is placed in the **page top-margin
box**, not in the body. The engine determines the mechanism — and getting this
wrong is the single most common logo bug.

### The rule: NEVER use `position: fixed` for a logo in Chromium print

In Chromium's print-to-PDF pipeline, a `position: fixed` element anchors to the
**content box** (the area *inside* the print margins), not the physical page
edge. With `top: 0.4cm` it lands 0.4cm into the content area — directly on top of
the first line of body text (the H1 title on page 1, the first H2 on later
pages). Widening the page margin does **not** fix it: the fixed element moves
down with the content box. This produces a logo that overlaps the title on every
page. (This exact bug shipped once before it was caught by visual inspection.)

### Correct mechanism per engine

| Engine | Logo mechanism | Why |
|--------|---------------|-----|
| **Chromium / Playwright** | Native `headerTemplate` via `display_header_footer=True` | The header template renders *inside* the reserved top-margin box, physically separated from body text. Chromium does NOT support CSS `element()`. |
| **WeasyPrint** | CSS `position: running(name)` + `@page { @top-left { content: element(name) } }` | WeasyPrint supports CSS Paged Media running elements; this is the standard way to repeat content in the margin box. It does NOT honor a headerTemplate. |

The two mechanisms are mutually exclusive and engine-specific — `render_pdf.py`
injects the right one per engine (`render_playwright` builds a headerTemplate;
`render_weasyprint` injects a running element + `@page` rule).

### Sizing and clearance (auto-grown top margin)

The top margin must always exceed the logo height plus a clearance band, or the
logo will overlap text again at larger sizes. `render_pdf.py` computes:

```
top_margin = max(2.5cm, logo_height + 1.4cm)
```

So enlarging the logo (e.g. `--logo-height 1.9` for a 2× logo) automatically
grows the top margin and can never reintroduce overlap. Never hard-code a top
margin smaller than `logo_height + clearance`.

### Embed the logo as base64 (not a file path)

The logo — like all images — is embedded as a base64 data URI, never referenced
by a `file://` or relative path. See the next subsection for why.

### CLI usage

```bash
python render_pdf.py report.md --out report.pdf \
    --logo company_logo.jpg --logo-height 1.4 --verify-visual
```

---

## Image paths: ALWAYS base64-embed (non-ASCII path trap)

**Chromium silently fails to load images referenced by relative or `file://`
paths when the working directory contains non-ASCII characters** (e.g.
`D:\研报生成`, `/données/`, `/プロジェクト/`). The chart/logo renders blank with
no error and no log line — the PDF looks "successful" but is missing images.

**Rule:** every image (charts AND logo) is embedded as a base64 data URI
(`data:image/png;base64,...`). This has zero path dependency and renders
identically on every engine and every locale. `render_pdf.py`'s
`_img_to_data_uri()` and `_resolve_charts()` enforce this for PNG charts; inline
SVG is already path-free. Only fall back to a path reference if base64 encoding
itself fails (logged as a WARN).

This applies to WeasyPrint too — data URIs work there as well, so base64 is the
single engine-neutral choice.

---

## Visual self-verification (MANDATORY for layout changes)

File-size and exit-code checks **cannot** catch the layout failures that matter:
logo-over-text overlap, oversized charts that swallow a page, CJK tofu, figures
split across a page break. The only reliable check is to **render the output PDF
back to images and look at them.**

`render_pdf.py --verify-visual` renders the first pages of the finished PDF to
PNG previews (via PyMuPDF / `fitz`) next to the output file:

```bash
python render_pdf.py report.md --out report.pdf --logo logo.jpg --verify-visual
# -> report_preview_p1.png, report_preview_p2.png, report_preview_p3.png
```

The agent (or a cross-model reviewer) then **opens these PNGs** and checks the
Type-B gate criteria visually. Adjusting CSS/margins without looking at a
rendered page is a known anti-pattern — it wastes cycles and ships overlap bugs.
Render, look, then decide.

---

## CJK (Chinese/Japanese/Korean) handling

### The problem

PDF renders Chinese characters as tofu (square box) if fonts are missing.
This is the **most common PDF failure mode** on Windows and CI environments.

### Font strategy — three tiers

| Tier | Font | CJK Coverage | Latin Quality | Use |
|------|------|-------------|---------------|-----|
| **1 (best)** | Noto Sans CJK SC | 44,000+ (GB18030) | Good | Body + headings, all CJK text |
| **1 (best)** | Noto Serif CJK SC | 44,000+ (GB18030) | Good | Body text (serif reports) |
| 2 (system) | Microsoft YaHei (Win) | GB2312 (6,763) | Mediocre | Fallback on Windows |
| 2 (system) | PingFang SC (macOS) | GB18030 | Excellent | Fallback on macOS |
| 2 (system) | WenQuanYi Micro Hei (Linux) | GB18030 | Poor | Fallback on Linux |

### CSS @font-face strategy

```css
/* Tier 1: best available */
@font-face {
  font-family: 'CJK Body';
  src: local('Noto Serif CJK SC'),
       local('Source Han Serif SC'),
       local('SimSun');
  unicode-range: U+2E80-2EFF, U+3000-303F, U+3400-4DBF, U+4E00-9FFF,
                 U+F900-FAFF, U+FE30-FE4F, U+FF00-FFEF;
}

@font-face {
  font-family: 'CJK Heading';
  src: local('Noto Sans CJK SC'),
       local('Source Han Sans SC'),
       local('Microsoft YaHei'),
       local('PingFang SC');
  unicode-range: U+2E80-2EFF, U+3000-303F, U+3400-4DBF, U+4E00-9FFF,
                 U+F900-FAFF, U+FE30-FE4F, U+FF00-FFEF;
}

body {
  font-family: 'CJK Body', 'Source Serif 4', Georgia, serif;
}
h1, h2, h3, h4 { font-family: 'CJK Heading', 'Source Sans 3', sans-serif; }
```

### Font embedding requirement

**ALL pipelines MUST embed CJK fonts** (subset is acceptable). Never rely on
PDF viewer fallback fonts — without embedding, CJK text renders as tofu on
systems without matching fonts.

WeasyPrint v63+ automatically subsets embedded fonts via Harfbuzz, producing
small PDF files even with full CJK fonts installed (~120MB installed font
produces a ~200KB subset for a typical report).

### CJK-specific layout adjustments

```css
body {
  font-size: 11pt;
  line-height: 1.75;       /* CJK needs 1.6-1.8 vs Latin 1.4-1.5 */
  text-align: justify;
  hanging-punctuation: allow-end;  /* WeasyPrint v65+ */
}
p {
  text-indent: 0;           /* No first-line indent (financial style) */
  margin-bottom: 0.6em;
}
```

### CJK verification checklist

Embedded in the quality gate (see below). Pre-flight check:

- [ ] Open PDF in a viewer that has NO CJK fonts installed
- [ ] Search for tofu (empty rectangles)
- [ ] Verify mixed CJK+Latin paragraphs: no glyph substitution, consistent baseline
- [ ] Verify table cells with CJK: no overflow, alignment preserved
- [ ] Verify chart labels (SVG): SVG `<text>` elements must specify `font-family`
  with a CJK-capable font

---

## Quality gates

### Pre-render checks (run before PDF generation)

```
[ ] All chart SVGs exist in figs/ (as {TICKER}_{kind}.svg) and are valid XML
[ ] report.md passes report_lint.py --strict
[ ] Markdown image references resolve to existing files
[ ] CJK fonts are detectable on the system
[ ] WeasyPrint/Playwright is installed and functional
```

### Post-render adversarial review gate

This is the **8-point checklist** from the orchestrator's adversarial review
system. The reviewer MUST check every item. This is a Type-B gate (requires
taste/judgment), so it routes to a cross-model reviewer per the loop protocol.

| # | Criterion | Check method | Type | Fail -> verdict |
|---|-----------|-------------|------|----------------|
| 1 | **All charts embedded** | Programmatic: verify_chart_coverage() cross-references chart-index.json against HTML chart refs. Required missing -> PRE-RENDER FAIL. Optional missing -> WARNING. | Type-A | REVISE |
| 2 | **CJK rendering** | Visual inspection: No tofu anywhere. All CJK characters render in correct font. Mixed CJK/Latin paragraphs have consistent baseline | Type-B | REVISE |
| 3 | **Rating box prominent** | Visual inspection: First page has clearly visible rating box with ticker, rating, value, price, thesis. Not buried or missing | Type-B | REVISE |
| 4 | **Pages numbered** | Visual inspection: "Page X of Y" in footer on every page except first. Correct count | Type-B | REVISE |
| 5 | **Disclaimer visible** | Visual inspection: Full Disclosures & Certifications appendix (B.1-B.7, +B.8 if China-listed) on final pages, separated by horizontal rule | Type-B | REVISE |
| 6 | **B/W printable** | Visual inspection: Charts and text distinguishable when printed grayscale | Type-B | REVISE |
| 7 | **File size** | Programmatic: verify_pdf() size check <5MB | Type-A | REVISE |
| 8 | **No layout overflow** | Visual inspection: No text clipping, tables fit page width, charts don't spill off page, no orphan lines | Type-B | REVISE |

### Verdict thresholds

| Verdict | Condition | Action |
|---------|-----------|--------|
| **PASS** | All 8 criteria met | PDF is distribution-ready |
| **REVISE** | Any criterion fails (fixable) | Fix the issue, re-render, re-review |
| **BLOCK** | PDF generation fails entirely, output corrupt, or engine unavailable with no fallback | Escalate to orchestrator |

### Common failure modes and mitigations

| Failure | Root cause | Fix |
|---------|-----------|-----|
| CJK tofu | Font not found | Install `fonts-noto-cjk`; verify `@font-face` local() names |
| WeasyPrint segfault | Mixed GTK DLLs on Windows | Use Playwright fallback; install GTK3 runtime |
| Charts missing | SVG path wrong in markdown | Verify relative path; use `--figs-dir` override |
| Table overflow | Wide tables exceed A4 width | CSS `font-size: 8pt` for wide tables; wrap in scroll container |
| Page break mid-chart | CSS not honored | Add `page-break-inside: avoid` to figure |
| File too large | Unsubset fonts or high-res PNGs | Use SVG charts; enable font subsetting; compress PNGs |
| Pandoc CJK fails | Pandoc doesn't inject CJK CSS | Use Path A (Python markdown -> HTML -> WeasyPrint) |
| Logo overlaps title text | `position: fixed` used in Chromium print (anchors to content box, not page edge) | Use native `headerTemplate` (Chromium) / `position: running()` (WeasyPrint); see "Company logo" section |
| Logo/chart renders blank | Image referenced by `file://`/relative path under a non-ASCII working dir | Base64-embed every image (data URI); `_img_to_data_uri()` |
| Oversized chart fills page | No `max-height` on chart img | CSS `max-height: 8.5cm; object-fit: contain` on `figure img, svg.plot` |
| `--check-deps` crashes on Windows | `_python_import_ok` only caught `ImportError`; WeasyPrint raises `OSError` (Pango DLL) at import | Catch broad `Exception` -> treat as unavailable -> fall back to Playwright |
| Larger logo overlaps text again | Hard-coded top margin | Auto-grow `top = max(2.5cm, logo_height + 1.4cm)` |

---

## Implementation plan

### Phase 1 — Core SKILL.md (this file)

The authoritative specification. Describes what the sub-skill does, its
interface, quality gates, and operation. Replaces the current stub.

### Phase 2 — PDF render script (`scripts/render_pdf.py`)

A single, self-contained Python script (`render_pdf.py` in the parent skill's
scripts/ directory) with the interface:

```
render_pdf.py REPORT.md --out REPORT.pdf [--style professional] [--engine auto]
                         [--figs-dir figs/] [--cjk] [--toc] [--html]
```

Responsibilities:
1. Parse markdown -> HTML (Python `markdown` library with extensions: `tables`,
   `fenced_code`, `codehilite`, `toc`, `footnotes`)
2. Resolve chart placeholders: detect `![](figs/{TICKER}_{kind})` (canonical format), inline SVG content,
   wrap in `<figure>` with `<figcaption>`
3. Detect and apply CJK font declarations
4. Load and inject the CSS template
5. Route to the detected PDF engine
6. Verify the output (size check, page count)
7. Return exit code 0 on success

**Dependency detection:**

```
render_pdf.py --check-deps
```
Prints a table of installed/missing dependencies and platform-specific
installation commands.

### Phase 3 — CSS templates

Located at `skills/generate-pdf/templates/`:

```
templates/
├── professional.css      # Full professional report styling
├── professional-bw.css   # B/W-optimized variant (grayscale-safe palette)
├── internal.css          # Lighter styling for internal Mode B/Mode C memos
└── cjk-overrides.css     # CJK-specific font stack and layout adjustments
```

**CSS template resolution** (3-tier, adapted from wangmhao/claude-skill-pdf):
1. Direct path: `--style path/to/custom.css`
2. Project-local: `comms/templates/professional.css` (overrides per-project)
3. Skill-bundled: `skills/generate-pdf/templates/professional.css` (default)

This lets each client/project override templates without modifying the skill.

### Phase 4 — Chart placeholder syntax

The markdown writer (typically `/write-report`) references charts using the
**canonical flat format** `![](figs/{TICKER}_{kind})` — no extension, no
ticker subdirectory:

```markdown
![Monte Carlo value distribution](figs/NVDA_montecarlo)

![Valuation football field](figs/NVDA_football)

![Breakeven heatmap](figs/NVDA_breakeven)
*Breakeven analysis: year-10 revenue vs. operating margin. Asterisk marks the current price.*
```

The render script resolves these by:
1. Matching `!\[([^\]]*)\]\(figs/([\w.]+_\w+)(?:\.(svg|png))?\)` (CHART_RE) in the markdown
2. Extracting the `{TICKER}_{kind}` stem from the regex capture
3. Trying `figs/{TICKER}_{kind}.svg` first, then `figs/{TICKER}_{kind}.png`
4. Reading SVG content and injecting inline for WeasyPrint
5. For PNG files: embedding as file reference
6. Detecting the following italic paragraph as caption text
7. Wrapping in `<figure class="chart">` with `<figcaption>`

### Phase 5 — Integration with the orchestrator

The `/generate-pdf` sub-skill is called by the orchestrator after
`/self-audit` passes:

```
WAVE 8 --- single agent --------------------------------------+
|  Agent J: /generate-pdf                                     |
|    -> Verify pre-render conditions                           |
|    -> Run render_pdf.py                                      |
|    -> Inspect output PDF                                     |
|    -> Run adversarial review gate (8-point checklist)        |
|    -> If REVISE: fix + re-render (max 2 rounds)              |
|    -> If PASS: PDF is deliverable                            |
+---------------------------------------------------------------+
```

### Phase 6 — Testing and validation

First validation run: take the existing `report.example.md` (NVIDIA),
run `charts.py` to generate figs, then run `render_pdf.py` to produce
a PDF. Verify all 8 gate criteria. Iterate CSS until PASS.

Subsequent: run on `freeport.report.example.md` to validate the
cyclical archetype path with its chart set.

### Phase 7 — File manifest (complete after implementation)

```
skills/generate-pdf/
├── SKILL.md                    # This specification
├── scripts/
│   └── render_pdf.py           # Main PDF rendering script
├── templates/
│   ├── professional.css        # Professional report CSS (default)
│   ├── professional-bw.css     # B/W-optimized variant
│   ├── internal.css            # Lighter styling for internal use
│   └── cjk-overrides.css       # CJK font stack + layout adjustments
├── assets/
│   └── fonts/
│       └── README.md           # Where to get CJK fonts, how to install
├── tests/
│   ├── test_render_pdf.py      # Unit tests for render_pdf.py
│   ├── test_cjk_rendering.py   # CJK rendering validation
│   └── fixtures/
│       ├── minimal_report.md   # Minimal report for CI testing
│       └── expected_outputs/   # Reference PDFs for visual regression
└── README.md                   # Quick start and troubleshooting
```

---

## Appendix A: WeasyPrint Windows installation guide

Windows is the most problematic platform for WeasyPrint because Pango/GTK
is not part of the OS. Steps:

1. Download and install the **GTK3 Runtime** from:
   [github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)
   (Choose the latest GTK3 runtime, NOT GTK4)

2. Verify the installation:
   ```bash
   pkg-config --cflags --libs pango
   ```

3. Install WeasyPrint:
   ```bash
   pip install weasyprint~=65.0
   ```

4. Test:
   ```bash
   python -c "from weasyprint import HTML; HTML(string='<p>hello</p>').write_pdf('/tmp/test.pdf'); print('OK')"
   ```

5. If step 4 segfaults: there are conflicting GTK DLLs on PATH.
   Find and remove older GTK installations, or use Docker instead.

**Alternative for Windows:** Use Path B (Playwright) which requires only
`pip install playwright && playwright install chromium` — no system deps.

## Appendix B: Dockerfile for reproducible CI/CD

```dockerfile
FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libharfbuzz0b \
    libgdk-pixbuf2.0-0 \
    fonts-noto-cjk \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    weasyprint~=65.0 \
    markdown~=3.7 \
    jinja2~=3.1

COPY render_pdf.py /app/render_pdf.py
COPY templates/ /app/templates/

WORKDIR /workspace
ENTRYPOINT ["python", "/app/render_pdf.py"]
```

Usage:
```bash
docker build -t equity-research-pdf .
docker run --rm -v "$(pwd):/workspace" equity-research-pdf \
    report.md --out report.pdf
```

## Appendix C: Playwright fallback script

When WeasyPrint is unavailable (e.g. Windows without GTK/Pango — the common
case), the script falls back to Playwright/Chromium. This is the most reliable
engine on Windows and requires zero system deps beyond Chromium itself.

The logo goes in the native `headerTemplate` — NOT a `position: fixed` element
(which would overlap body text; see the "Company logo" section). The top margin
auto-grows with the logo height so overlap is impossible at any size.

```python
async def playwright_render(html: str, pdf_path: str,
                            logo_uri: str | None = None,
                            logo_height_cm: float = 0.95) -> None:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")

        kwargs = dict(
            path=pdf_path, format="A4",
            margin={"top": "2.2cm", "bottom": "2.4cm",
                    "left": "2.4cm", "right": "2.4cm"},
            print_background=True, display_header_footer=False,
        )
        if logo_uri:  # base64 data URI — never a file path
            top = max(2.5, logo_height_cm + 1.4)
            kwargs["margin"]["top"] = f"{top}cm"
            kwargs["display_header_footer"] = True
            kwargs["header_template"] = (
                '<div style="width:100%;padding:0 0 0 1cm;'
                '-webkit-print-color-adjust:exact;">'
                f'<img src="{logo_uri}" style="height:{logo_height_cm}cm;width:auto;"></div>'
            )
            kwargs["footer_template"] = (
                '<div style="width:100%;font-size:8px;color:#999;'
                'text-align:center;">— <span class="pageNumber"></span> —</div>'
            )
        await page.pdf(**kwargs)
        await browser.close()
```

**Important Chromium-print gotchas (learned the hard way):**
- `display_header_footer=True` is required for ANY margin-box content (logo, page
  numbers). With it `False`, CSS `@page` margin boxes are largely ignored.
- The `header_template`/`footer_template` render at a tiny default font and have
  their own zoom; size with explicit `cm`/`px`, and add
  `-webkit-print-color-adjust:exact` so backgrounds/colors print.
- Page numbers use `<span class="pageNumber">` / `<span class="totalPages">`
  inside the templates — NOT CSS counters.

## Appendix D: Chart label language

The existing `charts.py` uses English labels. For A-share / HK reports
requiring Chinese chart labels:

- Charts.py should be modified to accept a `--locale zh` flag
- This sets matplotlib `rcParams['font.sans-serif']` to a CJK font
- SVG output must specify `font-family="Noto Sans CJK SC"` on `<text>` elements
- This is a **future enhancement**, not required for v1

---

## Cross-references

- Called by: Orchestrator (Mode A Wave 8), optionally Mode B/C
- Calls: No sub-skills. Self-contained rendering.
- Depends on: Unix: `apt install libpango-1.0-0 fonts-noto-cjk`; macOS: `brew install weasyprint`; Windows: GTK3 runtime or Playwright
- Produces: `TICKER_report.pdf` + adversarial review verdict at `verdicts/pdf.json`
- Loop protocol: Gates #1 (chart coverage) and #7 (file size) are Type-A (programmatic — enforced by render_pdf.py). Gates #2-#6 and #8 are Type-B (require visual inspection). Routes to cross-model per the loop protocol for Type-B gates only.
- Escalation: If no PDF engine is available after trying all 3 fallback paths, escalate to orchestrator with a BLOCK verdict and platform-specific installation instructions.
