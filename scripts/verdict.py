"""
verdict.py — Verdict artifact manager for the equity-research-analyst pipeline.

Produces and consumes cross-model verdict artifacts as frozen, inspectable JSON
files on disk. Part of the same-family-safe loop protocol: every Type-B gate
must route to a cross-model verdict, and the pipeline reads verdicts — it never
re-judges them.

CLI usage:
    python verdict.py --save PATH --gate self-audit --type B \\
        --verdict PASS --reviewer external-reviewer --notes "TV sensitivity checked"
    python verdict.py --load PATH
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_VERDICTS = frozenset({"PASS", "PASS-WITH-NOTES", "REVISE", "BLOCK", "SKIPPED-TIER3"})
VALID_GATE_TYPES = frozenset({"A", "B"})
KNOWN_MODEL_FAMILIES = {
    "claude": "anthropic",
    "codex": "openai",
    "gpt": "openai",
    "gemini": "google",
    "llama": "meta",
    "mistral": "mistral",
    "deepseek": "deepseek",
}


def _infer_family(model: str) -> str:
    """Return the model family for a given model identifier string."""
    lower = model.lower()
    for key, family in KNOWN_MODEL_FAMILIES.items():
        if key in lower:
            return family
    return "unknown"


# ---------------------------------------------------------------------------
# Verdict dataclass (frozen, with immutable defaults)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Verdict:
    """Immutable record of a gate verdict, possibly from a cross-model reviewer.

    All fields are frozen after construction.  dimensions defaults to an empty
    dict (which is okay because the field is read-only via the frozen class).
    """

    gate: str
    type: Literal["A", "B"]
    reviewer_model: str
    reviewer_family: str
    timestamp: str
    overall_verdict: Literal["PASS", "PASS-WITH-NOTES", "REVISE", "BLOCK"]
    dimensions: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    is_cross_model: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Verdict":
        """Construct a Verdict from a plain dictionary (e.g. loaded from JSON)."""
        return cls(
            gate=data["gate"],
            type=data["type"],
            reviewer_model=data["reviewer_model"],
            reviewer_family=data.get("reviewer_family", _infer_family(data.get("reviewer_model", ""))),
            timestamp=data["timestamp"],
            overall_verdict=data["overall_verdict"],
            dimensions=data.get("dimensions", {}),
            notes=data.get("notes", ""),
            is_cross_model=data.get("is_cross_model", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dictionary suitable for JSON serialization."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_verdict(verdict: Verdict, path: Path | str) -> Path:
    """Serialize *verdict* to *path* as JSON and return the resolved Path."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = verdict.to_dict()
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out.resolve()


def load_verdict(path: Path | str) -> Verdict:
    """Deserialize a Verdict from a JSON file at *path*."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return Verdict.from_dict(raw)


def is_same_family_safe(verdicts: list[Verdict]) -> bool:
    """Return True when the list of verdicts meets same-family-safe conditions.

    A set of verdicts is same-family-safe iff **every** Type-B verdict was
    issued by a cross-model reviewer (i.e. reviewer_family differs from the
    pipeline's home family, which is "openai" for the Codex runtime).
    """
    HOME_FAMILY = "openai"
    type_b_verdicts = [v for v in verdicts if v.type == "B"]
    if not type_b_verdicts:
        # No Type-B gates at all — trivially safe (Type-A only pipeline).
        return True
    return all(v.reviewer_family != HOME_FAMILY for v in type_b_verdicts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Save or load a gate-verdict artifact for the equity-research-analyst pipeline."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --save
    save_p = sub.add_parser("--save", help="Create a verdict artifact")
    save_p.add_argument("path", help="Output file path (JSON)")
    save_p.add_argument("--gate", required=True, help="Gate identifier, e.g. self-audit")
    save_p.add_argument("--type", required=True, choices=["A", "B"], help="Gate type")
    save_p.add_argument(
        "--verdict",
        required=True,
        choices=list(VALID_VERDICTS),
        help="Overall verdict",
    )
    save_p.add_argument("--reviewer", required=True, help="Model that issued the verdict")
    save_p.add_argument("--notes", default="", help="Free-text notes")
    save_p.add_argument("--cross-model", action="store_true", default=False, help="Mark as cross-model")
    save_p.add_argument(
        "--dimensions",
        default="{}",
        help="Dimensions as a JSON object string, e.g. '{\"tv\":\"PASS\"}'",
    )

    # --load
    load_p = sub.add_parser("--load", help="Load and display a verdict artifact")
    load_p.add_argument("path", help="Input file path (JSON)")

    return parser


def _main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "--save":
        dimensions: Dict[str, Any] = {}
        try:
            dimensions = json.loads(args.dimensions)
        except json.JSONDecodeError:
            print(f"ERROR: --dimensions must be valid JSON. Got: {args.dimensions}", file=sys.stderr)
            sys.exit(1)

        verdict = Verdict(
            gate=args.gate,
            type=args.type,
            reviewer_model=args.reviewer,
            reviewer_family=_infer_family(args.reviewer),
            timestamp=datetime.now(timezone.utc).isoformat(),
            overall_verdict=args.verdict,
            dimensions=dimensions,
            notes=args.notes,
            is_cross_model=args.cross_model,
        )
        out = save_verdict(verdict, args.path)
        print(json.dumps(verdict.to_dict(), indent=2, ensure_ascii=False))
        print(f"\nSaved to: {out}")

    elif args.command == "--load":
        verdict = load_verdict(args.path)
        print(json.dumps(verdict.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    _main()
