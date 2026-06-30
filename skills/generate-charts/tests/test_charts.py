"""Tests for chart rendering modules.

These tests verify that chart render functions accept valid input data
and produce output files. They do NOT test visual correctness.
"""

import sys
import os
import json
import tempfile

_package_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _package_dir)

import pytest
import matplotlib
matplotlib.use("Agg")


# Mock theme for testing (avoids YAML file dependency)
MOCK_THEME = {
    "name": "test",
    "palette": {
        "ink": "#1A1A1A",
        "muted": "#6B7280",
        "grid": "#D1D5DB",
        "accent": "#002D72",
        "accent_light": "#4A7AB5",
        "up": "#0E6E4D",
        "down": "#CC0000",
        "band": "#F3F4F6",
        "surface": "#FFFFFF",
    },
    "figure": {
        "default_width": 7.0,
        "default_height": 4.2,
        "dpi": 100,
    },
    "chart_defaults": {
        "title_fontsize": 10,
        "title_fontweight": "bold",
        "title_loc": "left",
        "title_pad": 10,
        "subtitle_fontsize": 7.5,
        "source_fontsize": 6.5,
    },
}


def _render_and_check(render_fn, data, kind_name):
    """Helper: render a chart to a temp dir and verify output files exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = render_fn(data, tmpdir, name=kind_name, theme=MOCK_THEME)
        assert len(paths) >= 2
        svg = next(p for p in paths if p.endswith(".svg"))
        png = next(p for p in paths if p.endswith(".png"))
        assert os.path.exists(svg), f"SVG missing for {kind_name}"
        assert os.path.exists(png), f"PNG missing for {kind_name}"
        # Verify SVG is valid XML
        import xml.etree.ElementTree as ET
        try:
            ET.parse(svg)
        except ET.ParseError as e:
            pytest.fail(f"Invalid SVG for {kind_name}: {e}")


class TestMonteCarlo:
    def test_render(self):
        import numpy as np
        from scripts.chart_montecarlo import render
        data = {
            "values": list(np.random.normal(145, 30, 1000)),
            "percentiles": {"p5": 95, "p25": 125, "p50": 145, "p75": 165, "p95": 195},
            "price": 120.0,
            "price_percentile": 0.20,
            "mos_band": {
                "buy_below": 101.5,
                "median": 145.0,
                "rich_above": 217.5,
                "mos": 0.30,
            },
        }
        _render_and_check(render, data, "montecarlo")


class TestFootball:
    def test_render(self):
        from scripts.chart_football import render
        data = {
            "price": 95.0,
            "lenses": [
                {"label": "DCF (base)", "low": 120, "high": 170, "mid": 145},
                {"label": "Peer P/E", "low": 100, "high": 155, "mid": 128},
                {"label": "DCF (bear)", "low": 75, "high": 110, "mid": 92},
            ],
        }
        _render_and_check(render, data, "football")


class TestBreakeven:
    def test_render(self):
        from scripts.chart_breakeven import render
        revenues = [50000, 75000, 100000, 125000, 150000]
        margins = [0.10, 0.15, 0.20, 0.25, 0.30]
        grid = [[r * m for m in margins] for r in revenues]
        data = {
            "revenues": revenues,
            "margins": margins,
            "grid": grid,
            "price": 95.0,
        }
        _render_and_check(render, data, "breakeven")


class TestTerminal:
    def test_render(self):
        from scripts.chart_terminal import render
        data = {
            "terminal_pct_of_value": 0.72,
            "explicit_pct": 0.28,
            "dcf_value": 145.0,
            "terminal_value": 104.4,
            "explicit_value": 40.6,
            "growth_rate": 0.03,
            "risk_free_rate": 0.04,
        }
        _render_and_check(render, data, "terminal")


class TestTornado:
    def test_render(self):
        from scripts.chart_tornado import render
        data = {
            "base": 145.0,
            "drivers": [
                {"name": "Revenue growth (Y1-5)", "low": 105, "high": 195},
                {"name": "Terminal op. margin", "low": 118, "high": 168},
                {"name": "WACC", "low": 125, "high": 160},
            ],
        }
        _render_and_check(render, data, "tornado")


class TestRevenueTraj:
    def test_render(self):
        from scripts.chart_revenue_traj import render
        data = {
            "years": [2025, 2026, 2027, 2028, 2029],
            "revenue": [9350, 10285, 11314, 12445, 13690],
            "revenue_growth": [0.10, 0.10, 0.10, 0.10, 0.10],
            "op_margin": [0.23, 0.24, 0.25, 0.26, 0.27],
            "fcff_margin": [0.15, 0.16, 0.17, 0.18, 0.18],
            "historical_revenue": [5800, 6700, 7600],
            "historical_margin": [0.19, 0.20, 0.21],
            "historical_years": [2022, 2023, 2024],
        }
        _render_and_check(render, data, "revenue_traj")


class TestRoicSpread:
    def test_render(self):
        from scripts.chart_roic_spread import render
        data = {
            "years": list(range(1, 6)),
            "roic": [0.18, 0.19, 0.20, 0.19, 0.17],
            "wacc": [0.09] * 5,
            "spread": [0.09, 0.10, 0.11, 0.10, 0.08],
            "competitive_advantage_period": 4,
        }
        _render_and_check(render, data, "roic_spread")


class TestScenarios:
    def test_render(self):
        from scripts.chart_scenarios import render
        data = {
            "scenarios": [
                {"name": "Bear", "value_low": 75, "value_high": 105,
                 "value_mid": 90, "probability": 0.25},
                {"name": "Base", "value_low": 120, "value_high": 170,
                 "value_mid": 145, "probability": 0.50},
                {"name": "Bull", "value_low": 175, "value_high": 240,
                 "value_mid": 208, "probability": 0.25},
            ],
            "price": 95.0,
        }
        _render_and_check(render, data, "scenarios")


class TestPriceVsValue:
    def test_render(self):
        from scripts.chart_price_vs_value import render
        data = {
            "dates": ["2023-12-31", "2024-06-30", "2024-12-31"],
            "price": [85, 78, 95],
            "value_low": [105, 110, 120],
            "value_mid": [135, 140, 145],
            "value_high": [165, 170, 170],
            "events": [],
        }
        _render_and_check(render, data, "price_vs_value")


class TestWaterfall:
    def test_render(self):
        from scripts.chart_waterfall import render
        data = {
            "price": 95.0,
            "intrinsic_value": 145.0,
            "steps": [
                {"label": "Current price", "value": 95.0},
                {"label": "Revenue growth", "delta": 18.0, "direction": "up"},
                {"label": "Margin expansion", "delta": 14.0, "direction": "up"},
                {"label": "Competitive fade", "delta": -2.0, "direction": "down"},
                {"label": "Intrinsic value", "value": 145.0},
            ],
        }
        _render_and_check(render, data, "waterfall")


class TestCapexCycle:
    def test_render(self):
        from scripts.chart_capex_cycle import render
        data = {
            "years": [2020, 2021, 2022, 2023, 2024],
            "demand_growth": [3.0, 3.5, 4.0, 4.5, 5.0],
            "capacity_additions": [2.0, 2.5, 3.0, 4.0, 5.5],
            "utilization_rate": [0.85, 0.87, 0.88, 0.86, 0.82],
            "industry": "Semiconductors",
            "current_cycle_phase": "mid-cycle",
        }
        _render_and_check(render, data, "capex_cycle")


class TestRiskMatrix:
    def test_render(self):
        from scripts.chart_risk_matrix import render
        data = {
            "risks": [
                {"name": "Regulatory crackdown", "probability": 0.15,
                 "impact_pct": -0.40, "category": "regulatory"},
                {"name": "Key person departure", "probability": 0.10,
                 "impact_pct": -0.15, "category": "operational"},
                {"name": "Competitor entry", "probability": 0.30,
                 "impact_pct": -0.25, "category": "competitive"},
            ],
            "value": 145.0,
        }
        _render_and_check(render, data, "risk_matrix")
