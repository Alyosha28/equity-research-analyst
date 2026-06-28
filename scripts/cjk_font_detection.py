"""CJK font auto-detection shared by charts.py and generate-pdf/ render_pdf.py.

Three-tier detection strategy:
  Tier 1: matplotlib.font_manager   (fastest, Python-only, works everywhere)
  Tier 2: fc-list system call       (Linux/macOS, most accurate)
  Tier 3: filesystem directory scan (cross-platform fallback, slowest)

Returns a normalized dict with keys:
  sans_serif, serif, mono          -- best font name found for each category
  available                         -- bool: any CJK font detected
  detection_method                  -- "matplotlib" | "fc-list" | "filesystem" | "none"
  all_cjk_fonts                     -- list of all detected CJK font names
  warning                           -- str or None: platform-specific install hint

Also provides ``configure_cjk_rcparams()`` which applies the detected fonts to
matplotlib rcParams so that charts.py can render CJK labels without tofu.

Usage:
  python cjk_font_detection.py                           # detect, print JSON to stdout
  python cjk_font_detection.py --lang zh-CN --verbose   # verbose to stderr
  python cjk_font_detection.py -o fonts.json             # write JSON to file
  python cjk_font_detection.py --matplotlib-only          # Tier 1 only
  python cjk_font_detection.py --html-css                 # emit CSS @font-face rules
  python cjk_font_detection.py --format markdown          # emit markdown table

Exit codes: 0 = CJK fonts found, 1 = no CJK fonts detected.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys as _sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# CJK Unicode blocks for font-name heuristic and content scanning
# ---------------------------------------------------------------------------

# Regex for detecting CJK-related font names (case-insensitive)
_CJK_FONT_NAME_RE = re.compile(
    r"cjk|sc|tc|jp|kr|chinese|japanese|korean|yahei|sim(h|sun)|dengxian|"
    r"fangsong|kaiti|ping[Ff]ang|hiragino|heiti|stheiti|wenquanyi|source.han|"
    r"noto.(sans|serif|mono)(.?cjk)?|malgun|nanum|batang|gungsuh|dotum|"
    r"msgothic|ipagothic|meiryo|yu.?gothic|mincho|songti|stsong|n?simsun|"
    r"apple.?gothic",
    re.IGNORECASE,
)

# Major CJK Unicode blocks -- used for heuristic detection of CJK-capable fonts
_CJK_UNICODE_BLOCKS = [
    (0x4E00, 0x9FFF),
    (0x3400, 0x4DBF),
    (0x3040, 0x30FF),
    (0xAC00, 0xD7AF),
    (0x3000, 0x303F),
    (0xFF00, 0xFFEF),
    (0x2E80, 0x2EFF),
    (0x31C0, 0x31EF),
    (0x3200, 0x32FF),
    (0x3300, 0x33FF),
    (0xF900, 0xFAFF),
    (0xFE30, 0xFE4F),
    (0x20000, 0x2A6DF),
    (0x2A700, 0x2B73F),
    (0x2B740, 0x2B81F),
    (0x2F800, 0x2FA1F),
]

# Valid font file extensions for filesystem scanning
_FONT_EXTENSIONS = frozenset({".ttf", ".ttc", ".otf", ".otc", ".dfont"})

# Platform-specific font preference stacks (ordered best -> fallback)
_PLATFORM_SANS_SERIF = {
    "windows": [
        "Noto Sans SC", "Noto Sans CJK SC",
        "Microsoft YaHei", "SimHei", "Source Han Sans SC",
    ],
    "darwin": [
        "Noto Sans CJK SC", "PingFang SC",
        "Hiragino Sans GB", "Source Han Sans SC", "Heiti SC",
    ],
    "linux": [
        "Noto Sans CJK SC", "WenQuanYi Micro Hei",
        "Noto Sans SC", "Source Han Sans SC",
    ],
}

_PLATFORM_SERIF = {
    "windows": [
        "Noto Serif CJK SC", "SimSun", "NSimSun",
        "Source Han Serif SC", "FangSong",
    ],
    "darwin": [
        "Noto Serif CJK SC", "Songti SC",
        "STSong", "Source Han Serif SC",
    ],
    "linux": [
        "Noto Serif CJK SC", "WenQuanYi Zen Hei",
        "Source Han Serif SC",
    ],
}

_PLATFORM_MONO = {
    "windows": ["SimHei", "SimSun"],
    "darwin": ["PingFang SC", "Hiragino Sans GB"],
    "linux": ["Noto Sans Mono CJK SC", "WenQuanYi Micro Hei"],
}

# Platform-specific install hints shown when no CJK font is detected
_PLATFORM_HINTS = {
    "windows": (
        "No CJK fonts detected. Install Noto Sans CJK SC from "
        "https://github.com/googlefonts/noto-cjk/releases "
        "(download OTF files and install via Windows Font Settings)."
    ),
    "darwin": (
        "No CJK fonts detected. Run: "
        "brew install font-noto-sans-cjk-sc font-noto-serif-cjk-sc"
    ),
    "linux": (
        "No CJK fonts detected. Run: "
        "sudo apt install fonts-noto-cjk"
    ),
}


def _detect_os() -> str:
    """Return normalized OS key: 'windows', 'darwin', or 'linux'."""
    sys_name = platform.system().lower()
    if "win" in sys_name:
        return "windows"
    if "darwin" in sys_name:
        return "darwin"
    return "linux"


def _is_cjk_font_name(name: str) -> bool:
    """Heuristic: does the font name suggest CJK capability?

    Checks two signals:
      1. Contains CJK Unicode characters directly in the name.
      2. Matches the known CJK font-name regex.
    """
    try:
        for ch in name:
            cp = ord(ch)
            if any(lo <= cp <= hi for lo, hi in _CJK_UNICODE_BLOCKS[:6]):
                return True
    except (TypeError, ValueError):
        pass
    return bool(_CJK_FONT_NAME_RE.search(name))


# ---------------------------------------------------------------------------
# Tier 1: matplotlib.font_manager
# ---------------------------------------------------------------------------

def _detect_via_matplotlib() -> list[str]:
    """Detect CJK fonts using matplotlib's built-in font manager."""
    try:
        from matplotlib.font_manager import fontManager
    except ImportError:
        return []

    out: list[str] = []
    seen: set[str] = set()
    for font in fontManager.ttflist:
        if font.name not in seen and _is_cjk_font_name(font.name):
            seen.add(font.name)
            out.append(font.name)
    return out


# ---------------------------------------------------------------------------
# Tier 2: fc-list system call
# ---------------------------------------------------------------------------

def _detect_via_fc_list() -> list[str]:
    """Detect CJK fonts using the fc-list system utility."""
    out: list[str] = []
    for lang in ("zh", "zh-cn", "zh-tw", "ja", "ko"):
        try:
            result = subprocess.run(
                ["fc-list", ":lang=" + lang, "-f", "%{family[0]}\\n"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                for name in filter(None, map(str.strip,
                                             result.stdout.split("\n"))):
                    if name not in out:
                        out.append(name)
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            break
    return out


# ---------------------------------------------------------------------------
# Tier 3: filesystem directory scan
# ---------------------------------------------------------------------------

def _detect_via_filesystem() -> list[str]:
    """Detect CJK fonts by scanning OS-specific font directories."""
    os_key = _detect_os()
    font_dirs: list[str]

    if os_key == "windows":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        font_dirs = [os.path.join(windir, "Fonts")]
    elif os_key == "darwin":
        font_dirs = [
            "/System/Library/Fonts",
            "/System/Library/Fonts/Supplemental",
            os.path.expanduser("~/Library/Fonts"),
        ]
    else:
        font_dirs = [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            os.path.expanduser("~/.fonts"),
            os.path.expanduser("~/.local/share/fonts"),
        ]

    out: list[str] = []
    seen_names: set[str] = set()

    for base_dir in font_dirs:
        if not os.path.isdir(base_dir):
            continue
        for dirpath, _dirnames, filenames in os.walk(base_dir):
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in _FONT_EXTENSIONS:
                    continue
                if not _CJK_FONT_NAME_RE.search(fname):
                    continue
                stem = os.path.splitext(fname)[0]
                stem = re.sub(
                    r"[-_](Regular|Bold|Italic|Light|Medium|Thin|Black"
                    r"|Heavy|ExtraLight|ExtraBold|SemiBold|DemiBold"
                    r"|Normal|Oblique|It|Bd|Rg)",
                    "", stem, flags=re.IGNORECASE,
                )
                name = stem.replace("_", " ").replace("-", " ").strip()
                name_lower = name.lower()
                if name_lower not in seen_names:
                    seen_names.add(name_lower)
                    out.append(name)
    return out


# ---------------------------------------------------------------------------
# Unified detection
# ---------------------------------------------------------------------------

def _find_best(stack: list[str], available: set[str],
               all_fonts: list[str]) -> Optional[str]:
    """Given a preference stack, return the first available match."""
    for name in stack:
        if name in available:
            return name
        name_lower = name.lower()
        for f in all_fonts:
            if f.lower() == name_lower:
                return f
    return all_fonts[0] if all_fonts else None


def detect_cjk_fonts(lang: str = "zh-CN") -> dict:
    """Run three-tier CJK font detection.

    Attempts detection in priority order:
      1. matplotlib.font_manager  (pure Python, no subprocess)
      2. fc-list                   (fontconfig system utility)
      3. filesystem scan          (universal fallback)

    Returns:
        dict with keys: sans_serif, serif, mono, available,
        detection_method, all_cjk_fonts, warning.
    """
    cjk_fonts: list[str] = []
    method: str = "none"

    for tier_name, detector in [
        ("matplotlib", _detect_via_matplotlib),
        ("fc-list", _detect_via_fc_list),
        ("filesystem", _detect_via_filesystem),
    ]:
        cjk_fonts = detector()
        if cjk_fonts:
            method = tier_name
            break

    if not cjk_fonts:
        os_key = _detect_os()
        return {
            "sans_serif": "DejaVu Sans",
            "serif": "DejaVu Serif",
            "mono": "DejaVu Sans Mono",
            "available": False,
            "detection_method": "none",
            "all_cjk_fonts": [],
            "warning": _PLATFORM_HINTS.get(os_key,
                                           _PLATFORM_HINTS["linux"]),
        }

    available_set = set(cjk_fonts)
    os_key = _detect_os()

    sans_stack = list(_PLATFORM_SANS_SERIF.get(os_key,
                       _PLATFORM_SANS_SERIF["linux"]))
    serif_stack = list(_PLATFORM_SERIF.get(os_key,
                       _PLATFORM_SERIF["linux"]))
    mono_stack = list(_PLATFORM_MONO.get(os_key,
                     _PLATFORM_MONO["linux"]))

    sans = _find_best(sans_stack, available_set, cjk_fonts)
    serif = _find_best(serif_stack, available_set, cjk_fonts) or sans
    mono = _find_best(mono_stack, available_set, cjk_fonts) or sans

    return {
        "sans_serif": sans,
        "serif": serif,
        "mono": mono,
        "available": True,
        "detection_method": method,
        "all_cjk_fonts": cjk_fonts,
        "warning": None,
    }


# ---------------------------------------------------------------------------
# Matplotlib rcParams configuration
# ---------------------------------------------------------------------------

def configure_cjk_rcparams(lang: str = "zh-CN") -> dict:
    """Run CJK font detection and apply results to matplotlib rcParams.

    Call BEFORE importing pyplot. Prepends detected CJK fonts to
    font.sans-serif, font.serif, and font.monospace rcParams so CJK
    is preferred without discarding Latin fallbacks. Also sets
    axes.unicode_minus=False.
    """
    result = detect_cjk_fonts(lang)

    try:
        import matplotlib as _mpl
    except ImportError:
        return result

    _mpl.rcParams["axes.unicode_minus"] = False

    if not result["available"]:
        import warnings
        warnings.warn(result["warning"])
        return result

    font_mappings = [
        ("sans_serif", "font.sans-serif"),
        ("serif", "font.serif"),
        ("mono", "font.monospace"),
    ]
    for key, rc_key in font_mappings:
        cur = _mpl.rcParams.get(rc_key, [])
        if not isinstance(cur, list):
            cur = [str(cur)]
        cur = list(cur)
        font_name = result.get(key)
        if font_name and font_name not in cur:
            _mpl.rcParams[rc_key] = [font_name] + cur

    return result


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_as_css_fontface(result: dict) -> str:
    """Generate CSS @font-face rules for embedding in HTML/PDF templates.

    Produces two @font-face blocks (CJK Body, CJK Heading) using
    local() references matching the detected fonts.
    """
    if not result["available"]:
        return "/* No CJK fonts detected -- @font-face rules skipped. */"

    sans = result["sans_serif"]
    serif = result["serif"]

    sans_fallbacks: list[str] = [sans] if sans else []
    serif_fallbacks: list[str] = [serif] if serif else []

    os_key = _detect_os()
    for name in _PLATFORM_SANS_SERIF.get(os_key, []):
        if name not in sans_fallbacks:
            sans_fallbacks.append(name)
    for name in _PLATFORM_SERIF.get(os_key, []):
        if name not in serif_fallbacks:
            serif_fallbacks.append(name)

    sans_local = ",\n       ".join(
        'local("{}")'.format(n) for n in sans_fallbacks[:5]
    )
    serif_local = ",\n       ".join(
        'local("{}")'.format(n) for n in serif_fallbacks[:5]
    )

    unicode_ranges = (
        "U+2E80-2EFF, U+3000-303F, U+31C0-31EF, U+3200-32FF,\n"
        "    U+3300-33FF, U+3400-4DBF, U+4E00-9FFF, U+F900-FAFF,\n"
        "    U+FE10-FE1F, U+FE30-FE4F, U+FF00-FFEF,\n"
        "    U+20000-2A6DF, U+2A700-2B73F, U+2B740-2B81F, U+2F800-2FA1F"
    )

    return (
        "/* Auto-generated CJK @font-face rules by cjk_font_detection.py */\n"
        "/* Detection method: {method} */\n\n"
        "@font-face {{\n"
        '  font-family: "CJK Body";\n'
        "  src: {serif_local};\n"
        "  unicode-range:\n"
        "    {unicode_ranges};\n"
        "}}\n\n"
        "@font-face {{\n"
        '  font-family: "CJK Heading";\n'
        "  src: {sans_local};\n"
        "  unicode-range:\n"
        "    {unicode_ranges};\n"
        "}}"
    ).format(
        method=result["detection_method"],
        serif_local=serif_local,
        sans_local=sans_local,
        unicode_ranges=unicode_ranges,
    )


def format_as_markdown(result: dict) -> str:
    """Format detection result as a markdown table for diagnostics."""
    lines = [
        "## CJK Font Detection",
        "",
        "- **Available:** {}".format("YES" if result["available"] else "NO"),
        "- **Method:** {}".format(result["detection_method"]),
        "- **Sans-serif:** {}".format(result.get("sans_serif", "N/A")),
        "- **Serif:** {}".format(result.get("serif", "N/A")),
        "- **Monospace:** {}".format(result.get("mono", "N/A")),
        "",
    ]
    if result["warning"]:
        lines.append("**Warning:** {}".format(result["warning"]))
        lines.append("")

    if result["all_cjk_fonts"]:
        lines.append("### All Detected CJK Fonts")
        lines.append("")
        for name in sorted(result["all_cjk_fonts"]):
            lines.append("- {}".format(name))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="CJK font auto-detection for equity research PDF/chart pipelines.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python cjk_font_detection.py                          # detect, print JSON
  python cjk_font_detection.py --lang zh-CN --verbose   # verbose output
  python cjk_font_detection.py -o fonts.json            # write JSON to file
  python cjk_font_detection.py --html-css               # emit CSS @font-face
  python cjk_font_detection.py --format markdown        # emit markdown table
  python cjk_font_detection.py --matplotlib-only        # Tier 1 only
""",
    )
    ap.add_argument(
        "--lang", default="zh-CN",
        help="Language code (default: zh-CN). E.g., ja-JP, ko-KR.",
    )
    ap.add_argument(
        "-o", "--output",
        help="Path to write the detection result as JSON.",
    )
    ap.add_argument(
        "--verbose", "-v", action="store_true",
        help="Emit diagnostic summary to stderr.",
    )
    ap.add_argument(
        "--format", dest="output_format", default="json",
        choices=["json", "markdown", "css"],
        help="Output format (default: json).",
    )
    ap.add_argument(
        "--html-css", action="store_true",
        help="Shorthand for --format css. Emit CSS @font-face rules.",
    )
    ap.add_argument(
        "--matplotlib-only", action="store_true",
        help="Use only matplotlib font_manager (Tier 1). Faster, no subprocess.",
    )

    args = ap.parse_args(argv)

    if args.matplotlib_only:
        cjk_fonts = _detect_via_matplotlib()
        if cjk_fonts:
            result = {
                "sans_serif": cjk_fonts[0],
                "serif": cjk_fonts[0],
                "mono": cjk_fonts[0],
                "available": True,
                "detection_method": "matplotlib",
                "all_cjk_fonts": cjk_fonts,
                "warning": None,
            }
        else:
            os_key = _detect_os()
            result = {
                "sans_serif": "DejaVu Sans",
                "serif": "DejaVu Serif",
                "mono": "DejaVu Sans Mono",
                "available": False,
                "detection_method": "none",
                "all_cjk_fonts": [],
                "warning": _PLATFORM_HINTS.get(os_key,
                                               _PLATFORM_HINTS["linux"]),
            }
    else:
        result = detect_cjk_fonts(args.lang)

    if args.verbose:
        status = "AVAILABLE" if result["available"] else "NOT FOUND"
        _sys.stderr.write(
            "status={}  method={}  sans={}  n_fonts={}\n".format(
                status, result["detection_method"],
                result["sans_serif"], len(result["all_cjk_fonts"]),
            )
        )

    fmt = "css" if args.html_css else args.output_format

    if fmt == "css":
        text = format_as_css_fontface(result)
    elif fmt == "markdown":
        text = format_as_markdown(result)
    else:
        text = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        _sys.stdout.write(text + "\n")

    return 0 if result["available"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
