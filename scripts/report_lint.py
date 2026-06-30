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
        or _present(text, r"本报告.*分析师.*独立.*撰写",
                        r"分析师.*证明.*观点|本人.*证明.*观点|我们.*证明.*观点",
                        r"特此.*证明|谨此.*证明")
    )
    has_cert_comp = (
        bool(re.search(r"no part of[\s\S]*?compensation was, is, or will be[\s\S]*?related to the specific[\s\S]*?recommendations", text, re.IGNORECASE))
        or _present(text, r"薪酬.*与.*特定.*推荐|特定.*建议.*无关",
                        r"薪酬.*不受.*影响|薪酬.*独立.*于|报酬.*独立.*于")
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
        r"评级.*占比|评级.*结构|投资评级.*分布|评级.*构成",
    )
    has_dist_table = _present(text, r"% Investment Banking", r"investment banking clients",
        r"投行.*客户|投行业务.*占比|投行.*收入",
    )
    if not has_rating_dist:
        out.append(Finding("WARN", "disclosure-missing-rating-distribution", None,
            "no rating distribution disclosure — B.2 is missing"))
    elif not has_dist_table:
        out.append(Finding("WARN", "disclosure-incomplete-rating-distribution", None,
            "rating distribution missing '% Investment Banking Clients' column — B.2 incomplete"))

    # B.3 — Meaning of Ratings
    has_meaning = _present(text,
        r"meaning of ratings", r"rating definitions", r"评级定义",
        r"评级.*含义|评级.*说明|评级.*标准",
        r"total return.*exceed.*benchmark",
        r"expects the total return",
    )
    if not has_meaning:
        out.append(Finding("WARN", "disclosure-missing-meaning-of-ratings", None,
            "no 'Meaning of Ratings' section — B.3 is missing"))

    # B.4 — Conflicts of Interest (FINRA 2241 items A–I)
    has_conflict_section = _present(text,
        r"conflicts? of interest", r"利益冲突.*披露",
        r"利益冲突|冲突.*披露|关联关系.*披露|潜在.*冲突",
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
        r"估值.*方法|定价.*方法|目标价.*方法|估值.*框架",
    )
    has_triangulation = _present(text,
        r"triangulation|synthesis.*method",
        r"交叉.*验证|多.*方法.*验证|综合.*估值|多.*维度.*验证|多.*透镜",
    )
    has_two_methods = _present(text, r"Method 1|Method 2|Primary.*Secondary",
        r"方法\s*一|方法\s*二|主要.*方法|次要.*方法",
    )
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
        r'(?:^|\n)#{1,3}\s*(?:risk factors?|风险因素|主要风险|关键风险|下行风险|重大.*风险)\s*\n(.*?)(?=\n#{1,3}\s|\Z)',
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
    has_info_date = _present(text, r"information.*as of|数据截至|as of.*date",
        r"信息.*截至.*日|数据.*截至.*日|截至.*日期|报告.*日期")
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
        r"证券.*协会|中国.*证监会|证券.*监管",
        r"科创板|创业板|新三板",
    )
    if is_china_name:
        has_independence = _present(text, r"分析师独立性声明|独立性声明|独立.*披露")
        has_info_source = _present(text, r"信息来源声明|数据.*来源.*声明")
        if not has_independence:
            out.append(Finding("WARN", "disclosure-missing-china-independence", None,
                "China-listed name detected but B.8 independence statement (分析师独立性声明) missing"))
        if not has_info_source:
            out.append(Finding("WARN", "disclosure-missing-china-info-source", None,
                "China-listed name detected but B.8 information source statement (信息来源声明) missing"))

    return out


# ---------------------------------------------------------------------------
# Type-A mechanical gates — Damodaran framework discipline
# ---------------------------------------------------------------------------

# Regex to extract a percentage or decimal from Chinese/English text around
# a given anchor phrase. Returns the numeric value (as a float in decimal
# form, e.g. 0.03 for 3%) or None.
def _extract_pct_near(text: str, anchor: str, radius: int = 120) -> float | None:
    """Return the percentage nearest to *anchor* (regex, case-insensitive)."""
    m_anchor = re.search(anchor, text, re.IGNORECASE)
    if not m_anchor:
        return None
    anchor_center = (m_anchor.start() + m_anchor.end()) // 2
    window = text[max(0, anchor_center - radius):anchor_center + radius]
    pct_matches = list(re.finditer(r"(\d+(?:\.\d+)?)\s*%", window))
    if not pct_matches:
        return None
    window_anchor_pos = anchor_center - max(0, anchor_center - radius)
    pct_matches.sort(key=lambda m: abs(m.start() - window_anchor_pos))
    return float(pct_matches[0].group(1)) / 100.0


def rule_terminal_growth_constraint(text: str) -> list[Finding]:
    """C2: terminal growth <= risk-free rate (Damodaran CRITICAL constraint)."""
    g_term = _extract_pct_near(text, "终期增速") or _extract_pct_near(text, "terminal growth")
    rf = (_extract_pct_near(text, "无风险利率") or _extract_pct_near(text, "riskfree rate")
          or _extract_pct_near(text, "risk-free rate") or _extract_pct_near(text, "risk free rate"))
    if g_term is None and rf is None:
        return []  # neither stated — not a failure, just can't check
    if g_term is not None and rf is not None and g_term > rf:
        return [Finding(
            "FAIL", "terminal-growth-gt-riskfree", None,
            f"Terminal growth {g_term:.1%} exceeds risk-free rate {rf:.1%}. "
            f"This violates the Damodaran DCF constraint (g_terminal <= riskfree)."
        )]
    return []


def rule_multi_lens_present(text: str) -> list[Finding]:
    """C1-C4: at least 3 of DCF/reverse-DCF/MC/comps lenses present."""
    checks = [
        ("DCF", _present(text, r"DCF|FCFF|折现现金流")),
        ("reverse-DCF", _present(text, r"反向.*DCF|reverse.*DCF|implied.*price|价格隐含")),
        ("Monte Carlo", _present(text, r"蒙特卡洛|Monte Carlo|monte.*carlo")),
        ("comps/football", _present(text, r"可比公司|comps|football|足球场|EV/Sales|P/E")),
    ]
    present_lenses = [name for name, ok in checks if ok]
    if len(present_lenses) < 3:
        missing = [name for name, ok in checks if not ok]
        return [Finding(
            "WARN", "multi-lens-incomplete", None,
            f"Only {len(present_lenses)}/4 valuation lenses present "
            f"({', '.join(present_lenses)}). Missing: {', '.join(missing)}. "
            f"Damodaran framework requires >=3 independent lenses."
        )]
    return []


def rule_terminal_pct_stated(text: str) -> list[Finding]:
    """B6: terminal value as % of operating value explicitly stated."""
    has_terminal_pct = _present(text, r"终值.*占比|terminal.*%|终值.*比例|terminal.*pct")
    has_terminal_keyword = _present(text, r"终值|terminal value")
    if has_terminal_keyword and not has_terminal_pct:
        return [Finding(
            "WARN", "terminal-pct-not-stated", None,
            "Terminal value discussed but terminal % of operating value not "
            "explicitly stated. This is a diagnostic signal — the % tells "
            "the reader where the value sits (explicit vs. terminal)."
        )]
    return []


def rule_explicit_horizon(text: str) -> list[Finding]:
    """B1: 10-year explicit forecast period acknowledged."""
    has_y10 = _present(text, r"Y10|Yr\s*10|Year\s*10|第10年|10.?年.*预测|10.?年.*显式|10.?year")
    has_decade = _present(text, r"十年.*预测|十年.*显式|decade.*forecast|10.?年.*现金流")
    if not has_y10 and not has_decade:
        return [Finding(
            "WARN", "explicit-horizon-unspecified", None,
            "10-year explicit forecast period not mentioned. Damodaran framework "
            "uses 10-year explicit FCFF projections with growth converging to "
            "terminal rate — shorter periods inflate terminal value weight."
        )]
    return []


def rule_coc_glide(text: str) -> list[Finding]:
    """B3: cost-of-capital glide (initial != terminal WACC)."""
    coc_init = _extract_pct_near(text, "初始.*WACC") or _extract_pct_near(text, "initial.*WACC")
    coc_term = _extract_pct_near(text, "终期.*WACC") or _extract_pct_near(text, "terminal.*WACC")
    has_glide = _present(text, r"滑行|glide|收敛.*WACC|WACC.*收敛")
    if coc_init is not None and coc_term is not None:
        if abs(coc_init - coc_term) < 0.001:
            return [Finding(
                "WARN", "coc-no-glide", None,
                f"Initial and terminal WACC are both {coc_init:.1%}. "
                f"Damodaran: cost of capital should glide from company-specific "
                f"(early years, higher risk) to market-average (later years)."
            )]
        return []  # different → glide present, OK
    if coc_init is not None and coc_term is None and not has_glide:
        return [Finding(
            "WARN", "coc-glide-unstated", None,
            "Initial WACC stated but terminal WACC / glide path not mentioned. "
            "A fixed WACC across all 10 years is unusual for Damodaran."
        )]
    return []


# ---------------------------------------------------------------------------
# A4 framework rules — 框架化 lint (检查结构 + 解释存在，不检查数值对错)
# 全部 WARN 级别 (与 A1 warnings.warn 哲学一致)。机器提醒缺失，分析师判断合理性。
# ---------------------------------------------------------------------------

def rule_rd_capitalization_explained(text: str) -> list[Finding]:
    """F1: 若报告提及 R&D 资本化，检查是否同时出现 (a) 摊销年限数字 + (b) 调整后营业利润率 +
    (c) 一段说明 terminal_roc 如何反映调整后投资资本基数。任一缺失 → WARN。
    **不检查具体年限或利润率数值**——经济附加值 spread 因行业而异，机器无法判断"过窄"。
    """
    rd_mentioned = _present(text,
        r"R&D.*资本化", r"研发.*资本化", r"research.*development.*capitaliz",
        r"rd_amortization", r"rd_asset_base",
    )
    if not rd_mentioned:
        return []  # 未提及 R&D 资本化，不检查
    has_amort_life = _present(text,
        r"摊销年限.*\d", r"amortization.*life.*\d", r"资本化.*\d+\s*年",
        r"rd_amortization_life.*\d",
    )
    has_adj_margin = _present(text,
        r"调整后.*营业利润率", r"R&D.*adjusted.*margin", r"rd_adj.*margin",
        r"资本化后.*利润率",
    )
    has_roc_explanation = _present(text,
        r"terminal_roc.*调整后", r"terminal.*roc.*adjust",
        r"终期.*ROIC.*资本化", r"ROIC.*R&D.*资本化",
        r"调整后投资资本", r"adjusted.*invested.*capital",
    )
    missing = []
    if not has_amort_life:
        missing.append("摊销年限数字")
    if not has_adj_margin:
        missing.append("调整后营业利润率")
    if not has_roc_explanation:
        missing.append("terminal_roc 如何反映调整后投资资本基数的说明")
    if missing:
        return [Finding(
            "WARN", "rd-capitalization-incomplete", None,
            f"报告提及 R&D 资本化但缺失: {', '.join(missing)}。"
            f"框架化要求 (F1): narrative 必须回答 资本化后 ROIC 是否 > WACC，若否为何。"
        )]
    return []


def rule_s2c_industry_context(text: str) -> list[Finding]:
    """F2: 若报告提及 S2C，检查是否同时出现 (a) 行业中位数数字 + (b) 行业名称。
    缺失 → WARN "S2C 未与行业基准对照"。**不检查具体偏离程度**——偏离是否合理是分析师判断。
    """
    s2c_mentioned = _present(text,
        r"sales-to-capital", r"sales.to.capital", r"收入资本比", r"营收资本比",
        r"sales_to_capital", r"S2C",
    )
    if not s2c_mentioned:
        return []
    has_industry_name = _present(text,
        r"行业.*中位数", r"industry.*median", r"同业.*均值",
        r"Damodaran.*行业", r"industry_s2c",
    )
    has_industry_number = bool(re.search(
        r"(行业|industry).{0,40}\d+(?:\.\d+)?", text, re.IGNORECASE
    )) or _present(text, r"industry_s2c_benchmark.*\d")
    if not (has_industry_name and has_industry_number):
        return [Finding(
            "WARN", "s2c-no-industry-context", None,
            "报告提及 S2C 但未与行业基准对照 (行业中位数 + 行业名称)。"
            "框架化要求 (F2): 防止 silent failure，industry 字段填了则 benchmark 必填或显式声明跳过。"
        )]
    return []


def rule_terminal_growth_lower_bound(text: str) -> list[Finding]:
    """F3: 若同时出现 g 和 rf，且 g < rf - 0.015 (默认 tg_lower_bound_buffer)，
    → WARN "终期增速低于无风险利率 150bps，隐含真实负增长"。**不 FAIL**——特殊行业
    (如衰退期公用事业) 可能合理，由分析师在 narrative 解释。
    """
    g_term = _extract_pct_near(text, "终期增速") or _extract_pct_near(text, "terminal growth")
    rf = (_extract_pct_near(text, "无风险利率") or _extract_pct_near(text, "riskfree rate")
          or _extract_pct_near(text, "risk-free rate") or _extract_pct_near(text, "risk free rate"))
    if g_term is None or rf is None:
        return []  # 无法检查
    buffer = 0.015  # 默认 tg_lower_bound_buffer; 报告级别 lint 用默认值，JSON 级别由 validator 处理
    lower_bound = rf - buffer
    if g_term < lower_bound:
        real_g = g_term - rf
        return [Finding(
            "WARN", "terminal-growth-below-lower-bound", None,
            f"终期增速 {g_term:.2%} 低于 无风险利率 - 150bps = {lower_bound:.2%}，"
            f"隐含真实负增长 ~{real_g*100:+.2f}pp。请在报告中解释 (衰退期/技术替代/竞争侵蚀) "
            f"或上调 g。特殊行业可配 tg_lower_bound_buffer 调整阈值。"
        )]
    return []


def rule_wacc_stacking_explained(text: str) -> list[Finding]:
    """F5: 若报告提及 failure_probability > 0，检查是否同时出现 WACC 分解表
    (含 size_premium / unprofitable_premium 等项) + 一段说明溢价与失败概率是否互斥。
    缺失 → WARN。**不设硬阈值**——是否双重折现是分析师判断。
    """
    failure_mentioned = _present(text,
        r"failure.*probability", r"失败概率", r"failure_probability",
    )
    if not failure_mentioned:
        return []
    # 检查 failure_probability 数值是否 > 0
    fp_match = re.search(r"failure[_ ]?probability[:\s]*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if fp_match:
        fp_val = float(fp_match.group(1))
        # 数值可能是小数 (0.15) 或百分比 (15) — 启发式判断
        if fp_val > 1.0:
            fp_val = fp_val / 100.0
        if fp_val <= 0:
            return []  # failure_probability = 0，无需检查
    # 没有 fp 数值但提及 failure_probability——保守起见仍检查
    has_wacc_decomp = _present(text,
        r"WACC.*分解", r"wacc_decomposition", r"WACC.*breakdown",
        r"size_premium", r"unprofitable_premium", r"小公司溢价",
    )
    has_mutex_explanation = _present(text,
        r"互斥", r"mutually.*exclusive", r"溢价.*失败概率.*互斥",
        r"互补", r"complement", r"溢价.*覆盖.*风险",
    )
    if not has_wacc_decomp or not has_mutex_explanation:
        missing = []
        if not has_wacc_decomp:
            missing.append("WACC 分解表 (含 size_premium / unprofitable_premium)")
        if not has_mutex_explanation:
            missing.append("溢价与失败概率互斥性说明")
        return [Finding(
            "WARN", "wacc-stacking-unexplained", None,
            f"报告提及 failure_probability > 0 但缺失: {', '.join(missing)}。"
            f"框架化要求 (F5): 防止双重折现——size/unprofitable premium 与 failure_probability "
            f"若覆盖同一困境风险则二选一，若互补则说明各自范畴。"
        )]
    return []


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
    # Damodaran framework discipline (2026-06-29, XPEV gold-standard gate)
    findings += rule_terminal_growth_constraint(text)
    findings += rule_multi_lens_present(text)
    findings += rule_terminal_pct_stated(text)
    findings += rule_explicit_horizon(text)
    findings += rule_coc_glide(text)
    # A4 framework rules (2026-06-30, XPEV methodology fix)
    findings += rule_rd_capitalization_explained(text)
    findings += rule_s2c_industry_context(text)
    findings += rule_terminal_growth_lower_bound(text)
    findings += rule_wacc_stacking_explained(text)
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
