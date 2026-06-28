"""Deterministic linter for an equity-research report (Mode A / C output).

The skill already has *descriptive* voice & depth standards (report-voice.md); this
is the *procedural* gate that makes them enforceable. It mechanically flags the
"AI-answer" tells that descriptive guidance keeps failing to prevent, so a draft
can be checked (and revised) before it is published.

Two severities so the pre-existing gold-standard example still passes by default,
while new reports can be held to the full bar:

  FAIL  -- established anti-patterns / always-required (block by default)
  WARN  -- newer required sections the gold standard predates (MoS band, numbers
           ledger, ...). Pass by default; with --strict they become FAIL.

Exit code: non-zero if any FAIL (or, with --strict, any FAIL or WARN).

    python report_lint.py path/to/report.md
    python report_lint.py path/to/report.md --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import namedtuple

Finding = namedtuple("Finding", "severity rule line excerpt")

# --- detectors -----------------------------------------------------------------

SECOND_PERSON = re.compile(r"\b(you|your|yours|yourself|yourselves)\b", re.IGNORECASE)
SECOND_PERSON_ZH = re.compile(r"[你您]")
BANNED_CALLOUTS = re.compile(r"校准命题|回到你的|[①-⑳]")   # circled ①..⑳
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
HEADING = re.compile(r"^\s*#")
# numeric token: $1,234.5 / 40% / 267bn / 1.15x ...
NUMERIC = re.compile(r"\$?\d[\d,]*(?:\.\d+)?\s?(?:%|bn|billion|m|million|x)?", re.IGNORECASE)
SOURCE_MARKER = re.compile(
    r"\[\^|\]\(|\(source|audited|guidance|consensus|estimate|filing|10-?[KQ]|"
    r"http|来源|审计|指引|测算|管理层|彭博|bloomberg",
    re.IGNORECASE,
)

IMAGE_REF = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')  # captures the path in ![](path)
EMOJI_EXCLUDE = {0x2713, 0x2714}   # ✓ ✔ are legitimate table marks, not emoji


def _is_emoji(ch: str) -> bool:
    cp = ord(ch)
    if cp in EMOJI_EXCLUDE:
        return False
    return (0x1F000 <= cp <= 0x1FAFF) or (0x2600 <= cp <= 0x27BF)


def _present(text: str, *patterns: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


# --- rules ---------------------------------------------------------------------

def _body_lines(lines):
    """(line_no, text) for prose lines: skip blank, table rows and headings."""
    for i, ln in enumerate(lines, 1):
        if not ln.strip() or TABLE_ROW.match(ln) or HEADING.match(ln):
            continue
        yield i, ln


def rule_second_person(lines):
    out = []
    for i, ln in _body_lines(lines):
        if SECOND_PERSON.search(ln) or SECOND_PERSON_ZH.search(ln):
            out.append(Finding("FAIL", "second-person", i, ln.strip()[:90]))
    return out


def rule_emoji(lines):
    out = []
    for i, ln in enumerate(lines, 1):
        bad = [c for c in ln if _is_emoji(c)]
        if bad:
            out.append(Finding("FAIL", "emoji", i, f"{''.join(bad)}  in: {ln.strip()[:70]}"))
    return out


def rule_banned_callouts(lines):
    out = []
    for i, ln in enumerate(lines, 1):
        if BANNED_CALLOUTS.search(ln):
            out.append(Finding("FAIL", "banned-callout", i, ln.strip()[:90]))
    return out


def rule_required_fail(text):
    out = []
    if not _present(text, r"not.*invest(ment)? advice", r"educational", r"非投资建议", r"投资建议"):
        out.append(Finding("FAIL", "missing-disclaimer", None, "no investment-advice disclaimer found"))
    if not _present(text, r"\brating\b", r"评级", r"\b(BUY|SELL|HOLD|REDUCE|ACCUMULATE|OVERWEIGHT|UNDERWEIGHT|NEUTRAL)\b",
                    r"买入|卖出|增持|减持|中性|持有"):
        out.append(Finding("FAIL", "missing-stance", None, "no rating / stance line found"))
    has_value = _present(text, r"intrinsic", r"fair value", r"内在价值", r"合理价值", r"value\s*/\s*share", r"value per share")
    has_price = _present(text, r"\bprice\b", r"现价", r"股价")
    if not (has_value and has_price):
        out.append(Finding("FAIL", "missing-value-or-price",
                           None, f"value_kw={has_value} price_kw={has_price}"))
    return out


def rule_chart_coverage(text, report_path=None):
    """Check that chart images are referenced in the report and point to real files.

    This is the automated enforcement of what was previously a manual visual check
    in the generate-pdf adversarial review (quality gate #1: "All charts embedded").

    Two checks, two severities:
      FAIL — image reference points to a file that does NOT exist (broken link)
      WARN — chart files exist in figs/ but are NOT referenced in the report
    """
    out = []
    # -- Collect image references from the report -------------------------------
    refs = set(IMAGE_REF.findall(text))
    # Strip extensions for comparison (the canonical format omits them)
    ref_stems = set()
    for r in refs:
        stem = r.rsplit(".", 1)[0] if "." in r.split("/")[-1] else r
        ref_stems.add(stem)

    # -- If a report_path is given, check filesystem ---------------------------
    if report_path:
        import os as _os
        report_dir = _os.path.dirname(_os.path.abspath(report_path))
        figs_dir = _os.path.join(report_dir, "figs")
        if _os.path.isdir(figs_dir):
            chart_files = [
                f for f in _os.listdir(figs_dir)
                if f.endswith((".png", ".svg"))
            ]
            chart_stems = set()
            for cf in chart_files:
                stem = _os.path.splitext(cf)[0]
                chart_stems.add(stem)
                # Also add with figs/ prefix for matching
                chart_stems.add(f"figs/{stem}")

            # FAIL: image reference points to non-existent file
            for r in refs:
                # Resolve: try figs/r, figs/r.png, figs/r.svg
                candidates = [
                    _os.path.join(report_dir, r),
                    _os.path.join(report_dir, f"{r}.png"),
                    _os.path.join(report_dir, f"{r}.svg"),
                ]
                if not any(_os.path.exists(c) for c in candidates):
                    out.append(Finding(
                        "FAIL", "broken-chart-ref", None,
                        f"image reference '{r}' points to a file that does not exist"
                    ))

            # WARN: chart files exist but aren't referenced
            unreferenced = []
            for cf in chart_files:
                stem = _os.path.splitext(cf)[0]
                if stem not in ref_stems and f"figs/{stem}" not in ref_stems:
                    unreferenced.append(cf)
            if unreferenced:
                out.append(Finding(
                    "WARN", "unreferenced-charts", None,
                    f"{len(unreferenced)} chart(s) in figs/ not referenced in report: "
                    + ", ".join(unreferenced[:5])
                    + (f" ... and {len(unreferenced)-5} more" if len(unreferenced) > 5 else "")
                ))

    return out


def rule_required_warn(text, lines):
    out = []
    if not _present(text, r"margin of safety", r"安全边际", r"\bMoS\b", r"buy-band", r"accumulate below", r"增持线"):
        out.append(Finding("WARN", "missing-mos-band", None, "no margin-of-safety buy-band"))
    if not _present(text, r"as of", r"valid[- ]as[- ]of", r"截至", r"revisit"):
        out.append(Finding("WARN", "missing-valid-as-of", None, "no valid-as-of / revisit-by stamp"))
    has_ledger = _present(text, r"ledger", r"数字台账", r"来源台账", r"sources?:")
    if not has_ledger:
        out.append(Finding("WARN", "missing-numbers-ledger", None, "no numbers ledger / source list"))
    if not _present(text, r"terminal"):
        out.append(Finding("WARN", "missing-terminal-pct", None, "terminal-value share not discussed"))
    if not _present(text, r"percentile", r"分位"):
        out.append(Finding("WARN", "missing-price-percentile", None, "price-in-distribution percentile not shown"))

    # table density
    table_rows = sum(1 for ln in lines if TABLE_ROW.match(ln))
    prose = sum(1 for _ in _body_lines(lines))
    denom = table_rows + prose
    if denom and table_rows / denom > 0.40:
        out.append(Finding("WARN", "table-density",
                           None, f"{table_rows} table rows vs {prose} prose lines (>40%)"))

    # Unsourced numbers (summary, not per-number). A numbers ledger IS the
    # document-level sourcing apparatus, so when one is present the prose-number
    # heuristic is satisfied -- the house voice deliberately weaves numbers into
    # sentences, and demanding an inline tag on each would fight that. The WARN
    # therefore fires only when there is NEITHER a ledger NOR inline sourcing.
    if not has_ledger:
        unsourced = 0
        for _, ln in _body_lines(lines):
            if NUMERIC.search(ln) and not SOURCE_MARKER.search(ln):
                unsourced += len(NUMERIC.findall(ln))
        if unsourced > 8:
            out.append(Finding("WARN", "unsourced-numbers",
                               None, f"~{unsourced} numeric mentions and no numbers ledger to source them"))
    return out


def rule_disclosure_requirements(text, lines):
    """Check for the mandatory disclosures & certifications appendix (B.1–B.7 + B.8).

    These are WARN (becoming FAIL under --strict) because legacy gold-standard examples
    predate the disclosure requirement, but every new report MUST include them.
    """
    out = []

    # B.1 — Analyst Certification (Reg AC language)
    # Use [\s\S]*? (re.DOTALL equivalent) since certification text often wraps across lines.
    # Patterns are deliberately loose to tolerate line breaks mid-sentence.
    has_cert_views = (
        bool(re.search(r"certify[\s\S]*?that[\s\S]*?(?:all of )?the views expressed[\s\S]*?accurately reflect[\s\S]*?personal\s+views", text, re.IGNORECASE))
        or _present(text, r"本报告.*分析师.*独立.*撰写")
    )
    has_cert_comp = (
        bool(re.search(r"no part of[\s\S]*?compensation was, is, or will be[\s\S]*?related to the specific[\s\S]*?recommendations", text, re.IGNORECASE))
        or _present(text, r"薪酬.*与.*特定.*推荐|特定.*建议.*无关")
    )
    if not (has_cert_views or has_cert_comp):
        out.append(Finding("WARN", "disclosure-missing-certification", None,
            "no analyst certification (Reg AC) found — B.1 is missing or unpopulated"))
    elif not has_cert_views:
        out.append(Finding("WARN", "disclosure-incomplete-certification", None,
            "analyst certification missing 'views accurately reflect personal views' prong"))
    elif not has_cert_comp:
        out.append(Finding("WARN", "disclosure-incomplete-certification", None,
            "analyst certification missing compensation prong"))

    # B.2 — Rating Distribution table
    has_rating_dist = _present(text,
        r"rating\s*(distribution|breakdown)", r"评级分布", r"% of.*Coverage",
        r"coverage universe (comprised|had)",
    )
    has_dist_table = _present(text, r"% Investment Banking", r"investment banking clients")
    if not has_rating_dist:
        out.append(Finding("WARN", "disclosure-missing-rating-distribution", None,
            "no rating distribution disclosure — B.2 is missing"))
    elif not has_dist_table:
        out.append(Finding("WARN", "disclosure-incomplete-rating-distribution", None,
            "rating distribution missing '% Investment Banking Clients' column — B.2 incomplete"))

    # B.3 — Meaning of Ratings
    has_meaning = _present(text,
        r"meaning of ratings", r"rating definitions", r"评级定义",
        r"total return.*exceed.*benchmark",
        r"expects the total return",
    )
    if not has_meaning:
        out.append(Finding("WARN", "disclosure-missing-meaning-of-ratings", None,
            "no 'Meaning of Ratings' section — B.3 is missing"))

    # B.4 — Conflicts of Interest (FINRA 2241 items A–I)
    has_conflict_section = _present(text,
        r"conflicts? of interest", r"利益冲突.*披露",
        r"FINRA Rule 2241", r"FINRA 2241",
    )
    # Check for at least a few of the 9 disclosure items
    conflict_items_found = sum(1 for p in [
        r"\(A\).*financial interest",
        r"\(B\).*compensation.*investment banking",
        r"\(C\).*managed or co-managed",
        r"\(D\).*non-investment[- ]banking",
        r"\(E\).*client of the (firm|member)",
        r"\(F\).*beneficially own.*1%",
        r"\(G\).*making a market",
        r"\(H\).*compensation from the subject company",
        r"\(I\).*other material conflict",
    ] if _present(text, p))
    if not has_conflict_section:
        out.append(Finding("WARN", "disclosure-missing-conflicts", None,
            "no conflicts of interest disclosure — B.4 is missing"))
    elif conflict_items_found < 3:
        out.append(Finding("WARN", "disclosure-incomplete-conflicts", None,
            f"conflicts disclosure has only {conflict_items_found}/9 FINRA 2241 items — B.4 incomplete"))

    # B.5 — Price Target Methodology
    has_dcf_method = _present(text,
        r"discounted cash flow.*primary|DCF.*primary|DCF.*forecast",
        r"现金流量折现|现金流折现",
    )
    has_triangulation = _present(text,
        r"triangulation|synthesis.*method|加权",
    )
    has_two_methods = _present(text, r"Method 1|Method 2|Primary.*Secondary")
    if not (has_dcf_method or has_two_methods):
        out.append(Finding("WARN", "disclosure-missing-methodology", None,
            "no price target methodology with DCF description — B.5 is missing"))
    elif not has_triangulation:
        out.append(Finding("WARN", "disclosure-incomplete-methodology", None,
            "price target methodology missing triangulation table — B.5 incomplete"))
    elif not has_two_methods:
        out.append(Finding("WARN", "disclosure-incomplete-methodology", None,
            "price target methodology has fewer than 2 methods — B.5 requires at least 2"))

    # B.6 — Risk Factors (at least 3 specific, DRIVER-TIED risks — generic boilerplate doesn't count)
    # Match a heading that names "Risk Factors" and capture content until the next heading or end
    risk_section_match = re.search(
        r'(?:^|\n)#{1,3}\s*(?:risk factors?|风险因素)\s*\n(.*?)(?=\n#{1,3}\s|\Z)',
        text, re.IGNORECASE | re.DOTALL,
    )
    if risk_section_match:
        risk_block = risk_section_match.group(1)  # group(1) is the content after the heading
        # Count risk items: bullet points, numbered items, or data rows in a risk table
        bullet_items = re.findall(r'(?:^[ \t]*[*\-]\s|^[ \t]*\d+\.\s)', risk_block, re.MULTILINE)
        # Also count table data rows (rows starting with | that have content between pipes,
        # excluding header/separator rows)
        table_data_rows = re.findall(r'^\|[^|\n]+\|[^|\n]+\|', risk_block, re.MULTILINE)
        n_risks = max(len(bullet_items), len(table_data_rows))
        if n_risks < 3:
            out.append(Finding("WARN", "disclosure-incomplete-risks", None,
                f"risk factors section has only {n_risks} items (<3 required) — B.6 incomplete"))
    else:
        out.append(Finding("WARN", "disclosure-missing-risks", None,
            "no dedicated risk factors section — B.6 is missing"))

    # B.7 — General Disclaimer (stricter than the minimal FAIL check)
    has_info_date = _present(text, r"information.*as of|数据截至|as of.*date")
    if not has_info_date:
        out.append(Finding("WARN", "disclosure-incomplete-disclaimer", None,
            "general disclaimer missing information cutoff date — B.7 incomplete"))

    # B.8 — China supplement (only checked when China indicators are present)
    # Use word-boundary-aware patterns to avoid substring false matches (e.g. "SSE" in "assess")
    is_china_name = _present(text,
        r"中国证券业协会|SAC.*指引|CSRC",
        r"\bSSE\b|\bSZSE\b|\bBJSE\b|上交所|深交所|北交所",
        r"\bA[- ]share\b|A股",
        r"分析师独立性声明",
    )
    if is_china_name:
        has_independence = _present(text, r"分析师独立性声明|独立性声明")
        has_info_source = _present(text, r"信息来源声明")
        if not has_independence:
            out.append(Finding("WARN", "disclosure-missing-china-independence", None,
                "China-listed name detected but B.8 independence statement (分析师独立性声明) missing"))
        if not has_info_source:
            out.append(Finding("WARN", "disclosure-missing-china-info-source", None,
                "China-listed name detected but B.8 information source statement (信息来源声明) missing"))

    return out


def lint(text, report_path=None):
    lines = text.splitlines()
    findings = []
    findings += rule_second_person(lines)
    findings += rule_emoji(lines)
    findings += rule_banned_callouts(lines)
    findings += rule_required_fail(text)
    findings += rule_chart_coverage(text, report_path)
    findings += rule_required_warn(text, lines)
    findings += rule_disclosure_requirements(text, lines)
    return findings


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Lint an equity-research report for voice/depth compliance.")
    ap.add_argument("report", help="path to the markdown report")
    ap.add_argument("--strict", action="store_true", help="treat WARN as FAIL (full bar for new reports)")
    args = ap.parse_args(argv)
    # Findings can contain emoji / CJK; keep output from crashing on a non-UTF-8
    # console (e.g. Windows GBK) by re-encoding stdout with replacement.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    with open(args.report, "r", encoding="utf-8") as fh:
        text = fh.read()

    findings = lint(text, report_path=args.report)
    fails = [f for f in findings if f.severity == "FAIL"]
    warns = [f for f in findings if f.severity == "WARN"]

    for f in findings:
        loc = f"line {f.line}" if f.line else "doc"
        print(f"[{f.severity}] {f.rule} ({loc}): {f.excerpt}")
    if not findings:
        print("clean: no findings.")

    blocking = fails + (warns if args.strict else [])
    print("-" * 60)
    print(f"{len(fails)} FAIL, {len(warns)} WARN"
          + ("  [--strict: WARN counts as FAIL]" if args.strict else ""))
    if blocking:
        print(f"RESULT: BLOCK ({len(blocking)} blocking issue(s)) -- revise before publishing.")
        return 1
    print("RESULT: PASS" + ("" if not warns else f" (with {len(warns)} non-blocking warning(s))"))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
