"""Shared pytest fixtures for render_pdf.py tests.

Provides:
  - mock_chart_figs: Temporary directory with mock SVG/PNG chart files
  - mock_chart_figs_empty: Empty figs/ directory (no charts)
  - minimal_report_md: Minimal valid report markdown string
  - sample_chart_index: Sample chart-index.json as a Python dict
  - html_with_rating: HTML body suitable for _style_rating_box testing
  - valid_pdf_bytes: Minimal valid PDF bytes for verification tests
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# SVG / PNG helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _make_svg(width: int = 640, height: int = 480,
              content_id: str = "test-chart",
              title: str = "Test Chart") -> str:
    """Return a valid SVG string for testing.

    Args:
        width, height: Viewport dimensions.
        content_id: SVG element ID for identification.
        title: Chart title text.
    """
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
        f'"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" id="{content_id}">\n'
        f'  <defs><style>'
        f'    text {{ font-family: "Noto Sans CJK SC", sans-serif; font-size: 12px; }}'
        f'  </style></defs>\n'
        f'  <rect width="{width}" height="{height}" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>\n'
        f'  <text x="20" y="30" font-weight="bold">{title}</text>\n'
        f'  <line x1="20" y1="50" x2="{width - 20}" y2="50" stroke="#1a3a6b" stroke-width="1"/>\n'
        f'  <text x="20" y="80">Value distribution (10,000 trials)</text>\n'
        f'</svg>\n'
    )


def _make_large_svg(line_count: int = 3000) -> str:
    """Return an oversized SVG string for inline-size warning tests."""
    circles = "".join(
        f"<circle cx='{i % 800}' cy='{i % 600}' r='5' fill='#333'/>\n"
        for i in range(line_count)
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">\n'
        f'{circles}'
        '</svg>\n'
    )


def _make_png_bytes() -> bytes:
    """Return minimal valid PNG bytes (1x1 pixel)."""
    import struct
    import zlib

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = zlib.crc32(c) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + c + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\x00"))
        + _chunk(b"IEND", b"")
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Directory / file fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_chart_figs(tmp_path: Path) -> Path:
    """Create a temporary figs/ directory with mock SVG and PNG chart files.

    Populates:
      figs/MU_montecarlo.svg
      figs/MU_football.svg
      figs/MU_breakeven.svg
      figs/MU_terminal.svg
      figs/MU_tornado.svg
      figs/MU_montecarlo.png   (dual-output, for PNG fallback tests)
      figs/MU_breakeven.png

    Charts NOT created (tested via separate fixture when needed):
      Any stems not listed above trigger the missing-chart code path.

    Returns:
        Path to the figs/ directory.
    """
    figs_dir = tmp_path / "figs"
    figs_dir.mkdir(parents=True, exist_ok=True)

    svg_charts = {
        "MU_montecarlo": _make_svg(640, 480, "montecarlo", "Monte Carlo Simulation"),
        "MU_football": _make_svg(800, 600, "football", "Football Field Analysis"),
        "MU_breakeven": _make_svg(640, 480, "breakeven", "Breakeven Analysis"),
        "MU_terminal": _make_svg(640, 480, "terminal", "Terminal Value Sensitivity"),
        "MU_tornado": _make_svg(640, 480, "tornado", "Tornado Chart — Key Drivers"),
    }

    for stem, svg_content in svg_charts.items():
        (figs_dir / f"{stem}.svg").write_text(svg_content, encoding="utf-8")

    # Also create PNG fallbacks for a subset
    png_bytes = _make_png_bytes()
    for stem in ("MU_montecarlo", "MU_breakeven"):
        (figs_dir / f"{stem}.png").write_bytes(png_bytes)

    return figs_dir


@pytest.fixture
def mock_chart_figs_empty(tmp_path: Path) -> Path:
    """Create an empty figs/ directory (no chart files)."""
    figs_dir = tmp_path / "figs_empty"
    figs_dir.mkdir(parents=True, exist_ok=True)
    return figs_dir


@pytest.fixture
def mock_chart_figs_large_svg(tmp_path: Path) -> Path:
    """Create a figs/ directory with an oversized inline SVG for size-warning tests."""
    figs_dir = tmp_path / "figs_large"
    figs_dir.mkdir(parents=True, exist_ok=True)
    large_svg = _make_large_svg(line_count=3000)
    (figs_dir / "LARGE_chart.svg").write_text(large_svg, encoding="utf-8")
    return figs_dir


# ═══════════════════════════════════════════════════════════════════════════════
# Content fixtures (strings / dicts)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def minimal_report_md() -> str:
    """Minimal valid markdown report for pipeline integration tests.

    Contains:
      - H1 title
      - Rating box metadata (Rating, Intrinsic value, Price, Downside, %ile)
      - Thesis paragraph
      - MoS buy-band
      - H2 section with prose
      - Chart reference
      - Disclaimer
    """
    return """# MU Corporation — Equity Research Report

**Rating:** REDUCE / SELL

**Intrinsic value:** ~$632 / share

**Price:** $1,134.00 (2026-06-27)

**Downside:** ~44% to intrinsic value

**Price %ile:** 95th

MU is pricing in perfection. Despite being the market leader in DRAM with
substantial competitive moats, at the current price of $1,134 the stock is
trading at 1.8x our base-case intrinsic value of $632, at the 95th
percentile of our Monte Carlo distribution. The market is discounting
the most optimistic scenario—above-trend memory demand, sustained pricing
power, and flawless execution—into the share price today.

MoS buy-band: Accumulate <= $442 | Fair ~ $632 | Rich above $885

## Executive Summary

Micron Technology (NASDAQ: MU) is the world's third-largest DRAM
manufacturer and one of the dominant players in NAND flash memory.
The company benefits from secular demand tailwinds (AI, data centers,
edge computing) and the oligopolistic structure of the memory industry.

## Monte Carlo Valuation

![Monte Carlo value distribution](figs/MU_montecarlo)

*Monte Carlo distribution of intrinsic value per share (n=10,000 trials).
The red line marks the current price at the 95th percentile.*

## Key Risks

1. **Cyclicality.** Memory is one of the most cyclical sub-sectors in
   semiconductors. Revenue can swing 30-40% in a single year.

2. **Capital intensity.** DRAM fabs cost $15-20B each. MU must continually
   invest just to maintain competitive parity.

3. **Commoditization risk.** Chinese memory producers (CXMT) are
   advancing rapidly, threatening the oligopolistic pricing structure.

---

*This analysis is for educational and informational purposes only and does
not constitute personalized investment advice. Inputs as of June 2026.*
"""


@pytest.fixture
def sample_chart_index() -> Dict:
    """Sample chart-index.json used for chart coverage verification.

    The 'required' list contains charts that MUST appear in the report.
    The 'optional' list contains charts that are nice-to-have but not blocking.
    """
    return {
        "ticker": "MU",
        "date": "2026-06-27",
        "required": [
            "MU_montecarlo",
            "MU_football",
            "MU_breakeven",
        ],
        "optional": [
            "MU_terminal",
            "MU_tornado",
        ],
        "meta": {
            "generator": "charts.py",
            "n_trials": 10000,
            "price": 1134.00,
        },
    }


@pytest.fixture
def sample_chart_index_json_file(tmp_path: Path,
                                  sample_chart_index: Dict) -> Path:
    """Write sample_chart_index to a real JSON file on disk."""
    json_path = tmp_path / "chart-index.json"
    json_path.write_text(
        json.dumps(sample_chart_index, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return json_path


@pytest.fixture
def html_with_rating() -> str:
    """HTML body suitable for _style_rating_box integration testing.

    Contains H1 company name, bold metadata in <strong> tags, a
    thesis paragraph long enough to be detected (>100 chars), and
    an <h2> delimiter that marks the end of the header block.
    """
    return (
        '<h1>MU Corporation</h1>\n'
        '<p><strong>Rating:</strong> REDUCE / SELL</p>\n'
        '<p><strong>Intrinsic value:</strong> ~$632 / share</p>\n'
        '<p><strong>Price:</strong> $1,134.00</p>\n'
        '<p>MU is pricing in perfection. Despite being the market leader '
        'in DRAM with substantial competitive moats, at the current price '
        'of $1,134 the stock is trading at 1.8x our base-case intrinsic '
        'value of $632, at the 95th percentile of our Monte Carlo '
        'distribution.</p>\n'
        '<h2>Executive Summary</h2>\n'
        '<p>More content here.</p>'
    )


@pytest.fixture
def valid_pdf_bytes() -> bytes:
    """Minimal valid PDF bytes for testing verification logic."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<</Type /Catalog /Pages 2 0 R>>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<</Type /Pages /Kids [3 0 R] /Count 1>>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]>>\n"
        b"endobj\n"
        b"xref\n"
        b"0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer\n"
        b"<</Size 4 /Root 1 0 R>>\n"
        b"startxref\n"
        b"190\n"
        b"%%EOF\n"
    )
