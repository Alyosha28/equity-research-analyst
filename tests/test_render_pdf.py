"""Tests for render_pdf.py — the PDF generation pipeline.

Tests cover the full rendering pipeline from chart resolution through
PDF output verification.  Minimum 12 tests as specified.

Run with:
    python -m pytest tests/test_render_pdf.py -v
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# ── Import the render_pdf module ──────────────────────────────────────────────
SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "generate-pdf"
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from render_pdf import (  # type: ignore[import-not-found]
    _resolve_charts,
    _extract_kv,
    _style_rating_box,
    _detect_cjk_fonts,
    _check_inline_svg_size,
    verify_chart_coverage,
    load_chart_index,
    render_weasyprint,
    render_playwright,
    _render_with_fallback,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. resolve_charts — SVG found / PNG fallback / missing
# ═══════════════════════════════════════════════════════════════════════════════

class TestResolveCharts:
    """Chart placeholder resolution: ![](figs/stem) -> SVG / PNG / placeholder."""

    def test_svg_found_inlines_content(self, mock_chart_figs: Path):
        """When an SVG chart exists, inline its content into a <figure>.

        The output must contain the raw <svg> element wrapped in a
        <figure class="chart"> with a <!-- chart: name.svg --> comment
        so the chart coverage gate can cross-reference later.
        """
        md_input = "![Monte Carlo](figs/MU_montecarlo)"
        result = _resolve_charts(
            md_input, str(mock_chart_figs), inline_svg=True,
        )

        assert '<figure class="chart">' in result, (
            f"SVG must be wrapped in <figure class=\"chart\">, got: {result[:300]}"
        )
        assert '<svg class="plot"' in result, (
            f"Inlined SVG must carry class=\"plot\", got: {result[:300]}"
        )
        assert '<!-- chart: MU_montecarlo.svg -->' in result, (
            f"HTML comment with chart name required for coverage gate, got: {result[:300]}"
        )
        assert '<figcaption>Monte Carlo</figcaption>' in result, (
            f"Alt text should become <figcaption>, got: {result[:300]}"
        )
        # XML declaration and DOCTYPE must be stripped
        assert '<?xml' not in result, "XML declaration must be stripped"
        assert '<!DOCTYPE' not in result, "DOCTYPE must be stripped"

    def test_png_fallback_when_svg_missing(self, tmp_path: Path):
        """When SVG is absent but a PNG exists, emit an <img> tag.

        This test creates a figs directory that contains ONLY a PNG
        (no SVG), then calls _resolve_charts with inline_svg=False to
        verify the standard <img> fallback path.
        """
        figs_dir = tmp_path / "figs_png_only"
        figs_dir.mkdir()

        import struct, zlib
        def _chunk(t, d):
            c = t + d
            return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        png = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\x00")) + _chunk(b"IEND", b"")

        (figs_dir / "TEST_fallback.png").write_bytes(png)

        md_input = "![Fallback](figs/TEST_fallback)"
        result = _resolve_charts(md_input, str(figs_dir), inline_svg=False)

        assert '<img' in result, (
            f"PNG fallback must produce <img> tag, got: {result[:300]}"
        )
        assert 'png' in result.lower(), (
            f"PNG fallback must reference .png, got: {result[:300]}"
        )
        assert '<figure' in result, "Must still be wrapped in <figure>"

    def test_missing_both_returns_placeholder_with_warning(
        self, mock_chart_figs_empty: Path,
    ):
        """When neither SVG nor PNG exists, emit a detectable placeholder.

        The placeholder uses class=\"chart-missing\" and a data-chart
        attribute so the chart-coverage gate can detect missing charts.
        A warning is also written to stderr.
        """
        # Use stem with underscore so CHART_RE matches
        md_input = "![Missing](figs/TEST_nonexistent)"
        stem = "TEST_nonexistent"

        with patch("sys.stderr.write") as mock_stderr:
            result = _resolve_charts(
                md_input, str(mock_chart_figs_empty), inline_svg=True,
            )

        assert 'chart-missing' in result, (
            f"Missing chart must produce chart-missing placeholder, got: {result[:300]}"
        )
        assert f'data-chart="{stem}"' in result, (
            f"Placeholder must carry data-chart=\"{stem}\" attribute for coverage gate"
        )
        assert 'CHART MISSING' in result.upper(), (
            "Placeholder text must be human-readable"
        )
        # Stderr warning must be emitted
        mock_stderr.assert_called()
        stderr_calls = "".join(
            str(c[0][0]) if c[0] else "" for c in mock_stderr.call_args_list
        )
        assert stem in stderr_calls, (
            f"stderr warning must mention the missing stem '{stem}'"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. extract_kv — simple / multiline
# ═══════════════════════════════════════════════════════════════════════════════

class TestExtractKV:
    """Key-value extraction from report header markdown."""

    def test_simple_rating_extraction(self):
        """Extract 'REDUCE / SELL' from a single bold-key line.

        _extract_kv uses the regex pattern **KEY:** value (bold closes
        right after the key). This is the canonical report header format.
        """
        text = "**Rating:** REDUCE / SELL"
        result = _extract_kv(text, "Rating")

        assert result is not None, "Should extract a non-None value"
        assert "REDUCE" in result.upper(), (
            f"Expected REDUCE in extracted value, got: {result!r}"
        )
        assert "SELL" in result.upper(), (
            f"Expected SELL in extracted value, got: {result!r}"
        )

    def test_multiline_header_extracts_all_keys(self):
        """Parse a complete multiline markdown header extracting every key.

        A real report header has Rating, Intrinsic value, Price, Downside,
        and Price %ile on separate bold-key lines.  _extract_kv must find
        them all independently.
        """
        header = (
            "# MU Corporation\n\n"
            "**Rating:** REDUCE / SELL\n\n"
            "**Intrinsic value:** ~$632 / share\n\n"
            "**Price:** $1,134.00 (2026-06-27)\n\n"
            "**Downside:** ~44% to intrinsic value\n\n"
            "**Price %ile:** 95th\n\n"
        )

        rating = _extract_kv(header, "Rating")
        intrinsic = _extract_kv(header, "Intrinsic value")
        price = _extract_kv(header, "Price")
        downside = _extract_kv(header, "Downside")
        percentile = _extract_kv(header, "Price.*ile")

        assert rating is not None, "Rating must be extracted"
        assert "REDUCE" in rating.upper()
        assert intrinsic is not None, "Intrinsic value must be extracted"
        assert "632" in intrinsic
        assert price is not None, "Price must be extracted"
        assert "1,134" in price
        assert downside is not None, "Downside must be extracted"
        assert percentile is not None, "Price %ile must be extracted"
        assert "95" in percentile


# ═══════════════════════════════════════════════════════════════════════════════
# 3. style_rating_box
# ═══════════════════════════════════════════════════════════════════════════════

class TestStyleRatingBox:
    """Rating box HTML structure — the styled header block on page 1."""

    def test_rating_box_contains_structural_elements(self, html_with_rating: str):
        """_style_rating_box wraps the header in .rating-box with kv-grid.

        The output must contain:
          - <div class="rating-box"> wrapper
          - <div class="kv-grid"> for key-value pairs
          - The company name from <h1>
          - Rating box positioned before the first <h2>
        """
        result = _style_rating_box(html_with_rating)

        assert '<div class="rating-box">' in result, (
            "Rating box wrapper must be present"
        )
        assert 'kv-grid' in result, (
            "Key-value grid structure must be present"
        )
        assert 'MU Corporation' in result, (
            "Company name extracted from H1 must appear in output"
        )
        # The rating box must appear before the H2 content
        h2_pos = result.find('<h2>')
        rating_pos = result.find('rating-box')
        assert h2_pos >= 0, "Output must contain the <h2> delimiter"
        assert rating_pos >= 0, "Output must contain rating-box"
        assert rating_pos < h2_pos, (
            "Rating box must appear before the first <h2>"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. cjk_font_detection — found / missing
# ═══════════════════════════════════════════════════════════════════════════════

class TestCJKFontDetection:
    """CJK font availability detection for PDF rendering."""

    def test_fonts_found_via_fc_list(self):
        """When fc-list returns CJK font families, return them as a list.

        The fc-list output format is one family per line, with the first
        comma-separated token being the primary family name.
        """
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = (
                "Noto Sans CJK SC\n"
                "Noto Serif CJK SC\n"
                "Source Han Sans SC\n"
            )
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            fonts = _detect_cjk_fonts()

            assert len(fonts) > 0, f"Should find at least one font, got {fonts}"
            assert any("Noto" in f or "CJK" in f or "Source Han" in f
                       for f in fonts), (
                f"Expected CJK font names, got: {fonts}"
            )

    def test_fonts_missing_returns_empty_list(self):
        """When no CJK fonts are available, return an empty list.

        On Windows (without fc-list) this tests the platform fallback path
        via C:\\Windows\\Fonts; on other platforms it defaults to empty.
        """
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("fc-list not found")

            with patch("os.path.exists", return_value=False):
                fonts = _detect_cjk_fonts()

        assert isinstance(fonts, list), "Must return a list even when empty"
        assert fonts == [], (
            f"No fonts should be found when none are installed, got: {fonts}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 5. verify_chart_coverage — all present / missing required
# ═══════════════════════════════════════════════════════════════════════════════

class TestVerifyChartCoverage:
    """Cross-reference chart-index.json against embedded document references."""

    def test_all_required_present_passes(self, sample_chart_index: dict):
        """When every required chart is found in the document, PASS."""
        # Build HTML with chart comments that the coverage scanner recognises
        html_body = (
            "<!-- chart: MU_montecarlo.svg -->\n"
            "<!-- chart: MU_football.svg -->\n"
            "<!-- chart: MU_breakeven.svg -->\n"
            "<!-- chart: MU_terminal.svg -->\n"
            "<figure class=\"chart\">...</figure>"
        )

        result = verify_chart_coverage(sample_chart_index, html_body,
                                       scan_mode="html")

        assert result["passed"] is True, (
            f"Should pass, missing_required={result['missing_required']}"
        )
        assert len(result["missing_required"]) == 0, (
            f"No required charts should be missing, got: "
            f"{result['missing_required']}"
        )
        assert "MU_montecarlo" in result["embedded"], (
            "MU_montecarlo must appear in embedded list"
        )
        assert "MU_football" in result["embedded"]
        assert "MU_breakeven" in result["embedded"]
        # MU_terminal is optional; missing it must not cause failure
        assert "MU_tornado" in result["missing_optional"], (
            "MU_tornado (optional, not in HTML) must appear in missing_optional"
        )

    def test_missing_required_returns_fail(self):
        """When a required chart is missing from the document, FAIL.

        The pre-render gate should block PDF generation when required
        charts are absent, returning passed=False with the missing stems
        listed in missing_required.
        """
        chart_index = {
            "ticker": "NVDA",
            "required": ["NVDA_montecarlo", "NVDA_breakeven", "NVDA_terminal"],
            "optional": [],
        }
        # Only montecarlo is present; breakeven and terminal are missing
        html_body = "<!-- chart: NVDA_montecarlo.svg -->\n<p>Content.</p>"

        result = verify_chart_coverage(chart_index, html_body,
                                       scan_mode="html")

        assert result["passed"] is False, (
            "Must FAIL when required charts are missing"
        )
        assert "NVDA_breakeven" in result["missing_required"], (
            f"Expected NVDA_breakeven in missing_required, got: "
            f"{result['missing_required']}"
        )
        assert "NVDA_terminal" in result["missing_required"]
        assert "NVDA_montecarlo" in result["embedded"], (
            "The one present chart must appear in embedded"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. fallback_chain — weasyprint fails -> playwright tried
# ═══════════════════════════════════════════════════════════════════════════════

class TestFallbackChain:
    """Render engine fallback chain: try engines in priority order."""

    def test_weasyprint_fails_playwright_is_tried(self, tmp_path: Path):
        """When WeasyPrint returns None, the fallback loop tries Playwright.

        The _render_with_fallback function iterates through ENGINE_CHAIN
        (pandoc-weasyprint -> weasyprint -> playwright -> pandoc-only).
        If weasyprint fails, playwright must be invoked as the next engine.
        """
        md_path = tmp_path / "dummy.md"
        md_path.write_text("# Test\n\nContent.\n", encoding="utf-8")
        pdf_path = str(tmp_path / "out.pdf")
        html_doc = "<html><body>Test</body></html>"
        css = "body { font-family: serif; }"

        with patch("render_pdf.render_pandoc_weasyprint",
                   return_value=None) as mock_pandoc, \
             patch("render_pdf.render_weasyprint",
                   return_value=None) as mock_weasy, \
             patch("render_pdf.render_playwright",
                   return_value=pdf_path) as mock_play:

            result = _render_with_fallback(
                md_path, pdf_path, html_doc, css, toc=False,
            )

            # All prior engines must have been tried
            mock_pandoc.assert_called_once()
            mock_weasy.assert_called_once_with(html_doc, pdf_path)
            mock_play.assert_called_once_with(html_doc, pdf_path)

            assert result == pdf_path, (
                "Fallback chain must return the first successful result"
            )

    def test_all_engines_fail_returns_none(self, tmp_path: Path):
        """When every engine fails, _render_with_fallback returns None.

        No exception is raised — callers check for None and exit
        gracefully with a diagnostic message.
        """
        md_path = tmp_path / "dummy.md"
        md_path.write_text("# Test\n", encoding="utf-8")
        pdf_path = str(tmp_path / "out.pdf")
        html_doc = "<html>Test</html>"
        css = ""

        with patch("render_pdf.render_pandoc_weasyprint",
                   return_value=None), \
             patch("render_pdf.render_weasyprint",
                   return_value=None), \
             patch("render_pdf.render_playwright",
                   return_value=None), \
             patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError

            result = _render_with_fallback(
                md_path, pdf_path, html_doc, css, toc=False,
            )

            assert result is None, (
                "All engines failed — must return None"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 7. svg_inline_size_warning
# ═══════════════════════════════════════════════════════════════════════════════

class TestSVGInlineSize:
    """Warn when combined inline SVG content exceeds the safety threshold."""

    def test_exceeds_threshold_emits_stderr_warning(self):
        """When combined inline <svg> bytes exceed --max-inline-size, warn.

        The _check_inline_svg_size function scans the HTML body for inline
        <svg> elements, sums their UTF-8 byte sizes, and writes a warning
        to stderr when the total exceeds max_inline_mb (default 1.0 MB).
        """
        # Build an HTML body with a single multi-kilobyte SVG
        huge_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'width="800" height="600" viewBox="0 0 800 600">\n'
        )
        # 30000 circle elements (~50 bytes each => ~1.5 MB)
        for i in range(30000):
            huge_svg += (
                f'<circle cx="{i % 800}" cy="{i % 600}" r="3" '
                f'fill="#3366cc" opacity="0.5"/>\n'
            )
        huge_svg += "</svg>"
        html_body = f"<body>\n{huge_svg}\n</body>"

        with patch("sys.stderr.write") as mock_stderr:
            _check_inline_svg_size(html_body, max_inline_mb=0.001)

            # The SVG is ~1.5 MB so a 0.001 MB threshold will fire
            mock_stderr.assert_called()
            call_text = "".join(
                str(c[0][0]) if c[0] else ""
                for c in mock_stderr.call_args_list
            )
            assert "inline SVG" in call_text, (
                f"Warning must mention 'inline SVG', got: {call_text[:200]}"
            )
            assert "no-inline-svg" in call_text, (
                f"Warning must suggest --no-inline-svg, got: {call_text[:200]}"
            )

    def test_below_threshold_no_warning(self):
        """Small SVGs under the threshold produce no stderr output."""
        small_svg = (
            '<svg width="100" height="100">'
            '<rect width="100" height="100" fill="#ccc"/>'
            '</svg>'
        )
        html_body = f"<body>{small_svg}</body>"

        with patch("sys.stderr.write") as mock_stderr:
            _check_inline_svg_size(html_body, max_inline_mb=1.0)

            mock_stderr.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Minimal integration test
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    """End-to-end integration: markdown through to HTML generation."""

    def test_minimal_render_produces_html_body(
        self, tmp_path: Path, minimal_report_md: str, mock_chart_figs: Path,
    ):
        """Full pipeline from markdown to HTML body.

        Uses the real md_to_html path (which chains _resolve_charts,
        markdown conversion, _wrap_figures, _style_rating_box, and
        _wrap_wide_tables).  Verifies that the output HTML contains the
        structural elements expected in a professional PDF report.
        """
        from render_pdf import md_to_html, build_html_document

        # --- Act: convert markdown to HTML ---
        html_body = md_to_html(minimal_report_md, str(mock_chart_figs),
                               inline_svg=True)

        # --- Assert structural elements ---
        assert len(html_body) > 0, "HTML body must not be empty"

        # Rating box must be present
        assert '<div class="rating-box">' in html_body, (
            "Output must contain a rating-box div"
        )

        # Chart must be inlined
        assert '<svg class="plot"' in html_body, (
            "Output must contain inlined SVG from chart resolution"
        )

        # Figure wrapping must have occurred
        assert '<figure' in html_body, (
            "Output must contain <figure> elements"
        )

        # Risk items must be present (rendered as list items)
        assert '<li>' in html_body, (
            "Markdown list items must be converted to HTML <li>"
        )

        # Header elements (markdown lib may add id= attributes)
        assert '<h1' in html_body, "H1 must be present"
        assert '<h2' in html_body, "H2 must be present"

        # --- Assert: assemble full HTML document ---
        html_doc = build_html_document(html_body, "body{}", title="Test")
        assert '<!DOCTYPE html>' in html_doc
        assert '<html' in html_doc
        assert '<body>' in html_doc
        assert '</body>' in html_doc
        assert '</html>' in html_doc

        # --- Assert: verify_pdf checks ---
        from render_pdf import verify_pdf
        pdf_path = tmp_path / "out.pdf"
        # Write a minimal file that verify_pdf would accept
        pdf_path.write_bytes(b"%PDF-1.4\n")
        verification = verify_pdf(str(pdf_path))
        assert verification["exists"] is True
