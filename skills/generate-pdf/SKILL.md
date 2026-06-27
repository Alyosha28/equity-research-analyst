---
name: equity-research-analyst/generate-pdf
description: >
  Render the finished equity research report to a typographic PDF with embedded
  charts, proper Chinese/English font handling, and professional layout. The final
  output step — produces a distribution-ready document. Step 11 of Mode A.
license: MIT
---

# Generate PDF

**Pipeline position:** STEP 11 of Mode A. Final output step — produces a polished,
distribution-ready PDF from the Markdown report. Also available for Mode B audit
memos and Mode C update memos.

## Input
- Final report Markdown file (post-self-audit, gate-passed)
- Chart images from `/run-valuation` (PNG/SVG in `figs/` directory)
- Optional: company logo, custom styling preferences

## What you produce

A **typographic, professional PDF** suitable for:
- Distribution to investors / clients
- Archival / compliance
- Print (A4/US Letter, with proper margins)

## Rendering pipeline

### Step 1 — Prepare assets
- Verify all chart images exist and are readable
- Resize/optimize charts for print (~150–300 DPI)
- Confirm font availability for target languages (Chinese + English)

### Step 2 — Choose rendering path

| Path | Tool | Best for |
|------|------|----------|
| **A: Markdown → PDF** | `pandoc` + `wkhtmltopdf` / `weasyprint` | Quick, good enough for internal |
| **B: Markdown → LaTeX → PDF** | `pandoc` → `xelatex` | Highest typographic quality, professional distribution |
| **C: Markdown → HTML → PDF** | custom CSS → `weasyprint` | Flexible styling, web-quality typography |
| **D: Programmatic** | Python `reportlab` / `fpdf2` | Full control, automated pipeline |

**Default:** Path C (weasyprint) for speed + quality. Path B for external
distribution when typographic excellence matters.

### Step 3 — Render

```bash
# Path C (recommended default)
python scripts/render_pdf.py ../PATH/TICKER_report.md --out ../PATH/TICKER_report.pdf --style professional

# Path B (external distribution)
pandoc TICKER_report.md \
  --pdf-engine=xelatex \
  -V mainfont="Times New Roman" \
  -V CJKmainfont="SimSun" \
  -V geometry:margin=2.5cm \
  -V fontsize=11pt \
  -o TICKER_report.pdf

# Path A (quick)
pandoc TICKER_report.md --pdf-engine=weasyprint -o TICKER_report.pdf
```

### Step 4 — Verify
- [ ] All pages render without overflow
- [ ] Charts are embedded at correct positions
- [ ] Chinese characters render correctly (no tofu/boxes)
- [ ] Page numbers present
- [ ] Table of contents (if >10 pages)
- [ ] File size < 10MB (reasonable for email)

## PDF design standards

### Typography
- **Body:** 10–11pt serif (Times New Roman / Source Serif / SimSun for Chinese)
- **Headings:** Sans-serif for contrast (Helvetica / Source Sans / SimHei for Chinese)
- **Exhibits (tables):** Monospace or condensed sans-serif
- **Line height:** 1.5–1.6 for body text
- **Justified** body text with hyphenation

### Layout
- **A4** (210×297mm) with 2.5cm margins
- **Header:** Company name + ticker + report date (right-aligned, small caps)
- **Footer:** Page X of Y + disclaimer snippet
- **First page:** Rating box (prominent), no running header
- **Charts:** Full-width, centered, with numbered captions ("Figure 1: ...")

### Color
- **Monochrome-primary:** Professionally printable in B&W
- **Accent:** One corporate or rating-appropriate color (dark blue for BUY, dark red for SELL)
- **Charts:** Grayscale-safe palette (distinguishable when printed B&W)

### Rating box (first page, prominent)

```
┌─────────────────────────────────────────┐
│  NVIDIA Corporation (NVDA)               │
│                                         │
│  RATING:    REDUCE                       │
│  VALUE:     ~$240 / share                │
│  PRICE:     $409 (10 Jun 2023)           │
│  DOWNSIDE:  ~40%                         │
│                                         │
│  [Thesis paragraph — 3-5 sentences]      │
└─────────────────────────────────────────┘
```

## The PDF render script

Create `scripts/render_pdf.py` if it doesn't exist:

```python
"""Render a Markdown equity research report to PDF via weasyprint.

Usage:
    python render_pdf.py ../PATH/report.md --out ../PATH/report.pdf
    python render_pdf.py ../PATH/report.md --out ../PATH/report.pdf --style professional
"""

import markdown
from weasyprint import HTML
import sys, os, argparse

def render(md_path: str, pdf_path: str, style: str = "professional"):
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Convert MD → HTML
    html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

    # Wrap in styled HTML
    css = load_css(style)
    html = f"""<html><head><meta charset="utf-8">{css}</head><body>{html_body}</body></html>"""

    HTML(string=html).write_pdf(pdf_path)
    return pdf_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to report.md")
    parser.add_argument("--out", required=True, help="Output PDF path")
    parser.add_argument("--style", default="professional")
    args = parser.parse_args()
    render(args.input, args.out, args.style)
```

Requirements: `pip install markdown weasyprint` (weasyprint requires system deps:
on Windows, install GTK3; on macOS, `brew install weasyprint`; on Linux,
`apt install weasyprint`).

## Chinese + English mixed typography

Critical for A-share/HK reports. Requirements:
- Body font that supports both Latin and CJK: "Noto Serif CJK SC" + "Source Serif"
- Monospace for numbers: "Source Code Pro" or "Fira Code"
- Test rendering before distributing — CJK font fallback is fragile
- `weasyprint` needs explicit `@font-face` declarations for CJK fonts

```css
@font-face {
  font-family: 'Noto Serif CJK SC';
  src: local('Noto Serif CJK SC');
}
body {
  font-family: 'Source Serif', 'Noto Serif CJK SC', serif;
}
```

## Output

- `TICKER_report.pdf` — the final, gate-passed, distribution-ready document
- Optional: `TICKER_report.html` — web-viewable version

## Integration with the loop
- PDF is generated only AFTER the self-audit gate passes
- If PDF rendering reveals layout issues (overflow, missing charts), fix the
  Markdown or chart assets and re-render — no need to loop back to earlier steps
- The PDF is the final deliverable alongside the Markdown report

## Self-check
- [ ] All charts embedded at correct positions
- [ ] Chinese characters render correctly
- [ ] Rating box on first page is prominent
- [ ] Pages numbered
- [ ] Disclaimer present on last page
- [ ] Printable in B&W without loss of information
- [ ] File size reasonable (<10MB)
