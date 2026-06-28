"""Cross-platform CJK font auto-detection for matplotlib.

Detects the best available CJK font on the current system and configures
matplotlib rcParams to use it. Handles Windows, macOS, and Linux with
appropriate font stacks for each platform.

Usage (call once at module init, before any figure creation):
    from cjk_fonts import configure_cjk_fonts
    configure_cjk_fonts()
"""

import platform
import matplotlib
from matplotlib.font_manager import fontManager

_FONT_STACKS = {
    "windows": [
        "Noto Sans SC", "Microsoft YaHei", "SimHei",
        "DengXian", "FangSong", "KaiTi",
    ],
    "darwin": [
        "Noto Sans CJK SC", "PingFang SC", "Hiragino Sans GB",
        "Heiti SC", "STHeiti",
    ],
    "linux": [
        "Noto Sans CJK SC", "Noto Sans SC",
        "WenQuanYi Micro Hei", "WenQuanYi Zen Hei",
        "Source Han Sans SC",
    ],
    "jp": [
        "Noto Sans CJK JP", "Hiragino Sans", "MS Gothic", "IPA Gothic",
    ],
    "kr": [
        "Noto Sans CJK KR", "Malgun Gothic", "Nanum Gothic", "Apple Gothic",
    ],
}


def _available_fonts():
    """Return a set of font names available in the matplotlib font manager."""
    return {f.name for f in fontManager.ttflist}


def _detect_best_cjk(target_lang="zh-CN"):
    """Return the first available CJK font for the target language.

    Args:
        target_lang: Language code. 'zh-CN', 'zh-TW', 'ja-JP', 'ko-KR'.

    Returns:
        Font name string, or None if no CJK font found.
    """
    available = _available_fonts()
    system = platform.system().lower()

    if "windows" in system:
        stack = _FONT_STACKS["windows"]
    elif "darwin" in system:
        stack = _FONT_STACKS["darwin"]
    else:
        stack = _FONT_STACKS["linux"]

    # Append JP/KR stacks for those languages
    if "ja" in target_lang.lower():
        stack = _FONT_STACKS["jp"] + stack
    elif "ko" in target_lang.lower():
        stack = _FONT_STACKS["kr"] + stack

    for font_name in stack:
        if font_name in available:
            return font_name

    return None


def configure_cjk_fonts(lang="zh-CN"):
    """Configure matplotlib rcParams for CJK font rendering.

    Prepends the best available CJK font to rcParams['font.sans-serif'].
    Call this ONCE at module init, BEFORE any pyplot.figure() call.

    Args:
        lang: Language code for CJK variant selection.
              'zh-CN' (Simplified Chinese), 'zh-TW' (Traditional Chinese),
              'ja-JP' (Japanese), 'ko-KR' (Korean).

    Returns:
        The name of the font that was configured, or None if no CJK font found.
    """
    cjk_font = _detect_best_cjk(lang)
    if cjk_font is None:
        import warnings
        warnings.warn(
            f"No CJK font found for lang={lang}. "
            f"CJK characters will render as tofu boxes. "
            f"Install Noto Sans CJK from Google Fonts."
        )
        return None

    current = matplotlib.rcParams["font.sans-serif"]
    if isinstance(current, str):
        current = [current]
    if cjk_font not in current:
        matplotlib.rcParams["font.sans-serif"] = [cjk_font] + list(current)

    # Ensure negative signs render as proper minus signs
    matplotlib.rcParams["axes.unicode_minus"] = False

    return cjk_font
