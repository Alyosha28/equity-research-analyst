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


def lint(text):
    lines = text.splitlines()
    findings = []
    findings += rule_second_person(lines)
    findings += rule_emoji(lines)
    findings += rule_banned_callouts(lines)
    findings += rule_required_fail(text)
    findings += rule_required_warn(text, lines)
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

    findings = lint(text)
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
