"""Phase 0 unit tests: MoS band, JSON schema, report linter, chart rendering,
and the NVDA reproducibility guard (so the new code does not regress the engine).

    python -m pytest tests/test_phase0.py -q
"""

import os
import sys

HERE = os.path.dirname(__file__)
SCRIPTS = os.path.abspath(os.path.join(HERE, "..", "scripts"))
TEMPLATES = os.path.abspath(os.path.join(HERE, "..", "templates"))
sys.path.insert(0, SCRIPTS)

import monte_carlo as mc            # noqa: E402
import dcf_valuation as dcf         # noqa: E402
import financial_valuation as fv    # noqa: E402
import report_lint as rl            # noqa: E402
import charts                       # noqa: E402
from valuation_inputs import load_inputs  # noqa: E402

ASSUMP = os.path.join(TEMPLATES, "assumptions.example.json")


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def test_mos_band_ordering_and_bounds():
    band = mc.mos_band([float(x) for x in range(50, 451)])
    assert 0.15 <= band["mos"] <= 0.50
    assert band["buy_below"] < band["median"] < band["rich_above"]


def test_json_summary_schema():
    base = load_inputs(ASSUMP)
    values, _ = mc.simulate(base, trials=500, seed=1)
    js = mc.json_summary(values, price=409)
    for k in ("trials", "mean", "median", "percentiles", "mos_band",
              "values", "price", "price_percentile", "p_value_ge_price"):
        assert k in js
    assert len(js["values"]) == js["trials"]
    assert 0.0 <= js["price_percentile"] <= 1.0


def test_report_lint_example_passes():
    fails = [f for f in rl.lint(_read(os.path.join(TEMPLATES, "report.example.md")))
             if f.severity == "FAIL"]
    assert fails == [], f"gold-standard should have no FAILs, got {fails}"


def test_report_lint_bad_blocks():
    findings = rl.lint(_read(os.path.join(HERE, "bad_report.sample.md")))
    fails = [f for f in findings if f.severity == "FAIL"]
    rules = {f.rule for f in fails}
    assert {"second-person", "emoji", "banned-callout"} <= rules
    assert len(fails) >= 5


def test_charts_render(tmp_path):
    base = load_inputs(ASSUMP)
    values, _ = mc.simulate(base, trials=300, seed=2)
    paths = charts.monte_carlo_hist(mc.json_summary(values, price=409), str(tmp_path))
    assert paths and all(os.path.getsize(p) > 0 for p in paths)


def test_nvda_reproducibility_unbroken():
    v = dcf.value(load_inputs(ASSUMP)).value_per_share
    assert 225.0 <= v <= 250.0, f"NVDA intrinsic drifted to {v:.2f} (expected ~236)"


def test_financial_rim_ddm_consistency():
    r = fv.value(fv.load_inputs(os.path.join(TEMPLATES, "financials.example.json")))
    gap = abs(r.going_concern_value_per_share - r.ddm_value_per_share) / r.ddm_value_per_share
    assert gap < 0.01, f"RIM and DDM diverge {gap:.1%} (should be ~0 under clean surplus)"
    assert 200 <= r.going_concern_value_per_share <= 260, "financials anchor drifted"


def test_fcff_archetype_templates_run():
    for name in ("cyclical.freeport", "young.example", "mature.example"):
        v = dcf.value(load_inputs(os.path.join(TEMPLATES, name + ".json"))).value_per_share
        assert v > 0, f"{name} produced non-positive value {v}"


def test_freeport_report_passes_lint():
    findings = rl.lint(_read(os.path.join(TEMPLATES, "freeport.report.example.md")))
    assert [f for f in findings if f.severity == "FAIL"] == []
