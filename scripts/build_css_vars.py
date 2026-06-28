#!/usr/bin/env python3
"""
build_css_vars.py — Read design_tokens.json and emit CSS :root custom properties.

Usage:
    python build_css_vars.py                          # print to stdout
    python build_css_vars.py --output tokens.css       # write to file
    python build_css_vars.py --compact                 # single-line output (for embedding)
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

# ---------------------------------------------------------------------------
# Mapping from top-level JSON key → CSS variable prefix
# ---------------------------------------------------------------------------
PREFIX_MAP: Dict[str, str] = {
    "colors":      "color",
    "fonts":       "font",
    "spacing":     "space",
    "radius":      "radius",
    "shadow":      "shadow",
    "chart":       "chart",
    "page":        "page",
    "typography":  "text",
}


def load_tokens(path: Path) -> Dict[str, Any]:
    """Return parsed JSON, stripping metadata keys (those starting with '_')."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def flatten_tokens(tokens: Dict[str, Any]) -> Dict[str, str]:
    """
    Walk each top-level category and produce a flat {css_var_name: value} dict.

    Naming rule:  --{prefix}-{sub_key_with_underscores_to_hyphens}

    Examples:
        colors.ink          → --color-ink
        fonts.cjk_sans      → --font-cjk-sans
        chart.dpi           → --chart-dpi
        typography.h1_size_pt → --text-h1-size-pt
    """
    result: Dict[str, str] = {}

    for category, subtree in tokens.items():
        prefix = PREFIX_MAP.get(category, category)
        if isinstance(subtree, dict):
            for sub_key, value in subtree.items():
                var_name = f"--{prefix}-{sub_key.replace('_', '-')}"
                result[var_name] = _format_value(value)
        else:
            var_name = f"--{prefix}"
            result[var_name] = _format_value(subtree)

    return result


def _format_value(value: Any) -> str:
    """Convert a token value to a CSS-safe string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        # Numbers that are conceptually unitless (dpi, line-height, font-weight)
        return str(value)
    return str(value)


def build_css_block(variables: Dict[str, str], compact: bool = False) -> str:
    """Render the :root { … } CSS block."""
    if compact:
        declarations = "; ".join(f"{k}: {v}" for k, v in variables.items())
        return f":root {{ {declarations}; }}"

    lines = [":root {"]
    # Stable sort by variable name for diff-friendliness
    for name in sorted(variables.keys()):
        lines.append(f"  {name}: {variables[name]};")
    lines.append("}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build CSS custom properties from design_tokens.json"
    )
    parser.add_argument(
        "--input",
        default=str(Path(__file__).resolve().parent / "design_tokens.json"),
        help="Path to design_tokens.json (default: next to this script)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Write CSS to file instead of stdout",
    )
    parser.add_argument(
        "--compact", "-c",
        action="store_true",
        help="Emit single-line :root block (useful for embedding)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.is_file():
        print(f"Error: design_tokens.json not found at {input_path}", file=sys.stderr)
        sys.exit(1)

    tokens = load_tokens(input_path)
    variables = flatten_tokens(tokens)
    css = build_css_block(variables, compact=args.compact)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(css + "\n", encoding="utf-8")
        print(f"Wrote {len(variables)} CSS custom properties to {output_path}", file=sys.stderr)
    else:
        print(css)


if __name__ == "__main__":
    main()
