"""Immutable input model for the intrinsic-DCF valuation engine.

All monetary values are in MILLIONS of the reporting currency (USD by default).
Rates are decimals (0.40 == 40%). Everything here is frozen / immutable so a set
of assumptions can be passed around, copied with overrides, and reasoned about
without hidden mutation (see coding-style: immutability).

Design follows Damodaran's "story -> numbers -> value" model: the four value
drivers are revenue growth, target operating margin, reinvestment efficiency
(sales-to-capital), and risk (cost of capital + terminal assumptions).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace, asdict, field
from typing import Optional


@dataclass(frozen=True)
class Segment:
    """A revenue segment built bottom-up as TAM x market-share, or via an
    explicit revenue path. Used to reproduce Damodaran/SemiAnalysis-style
    bottoms-up revenue builds (AI chips, Auto, Gaming, ...)."""

    name: str
    base_revenue: float                       # year-0 revenue ($M)
    tam_path: Optional[tuple] = None          # total market size, years 1..N ($M)
    share_path: Optional[tuple] = None        # market share, years 1..N (decimal)
    revenue_path: Optional[tuple] = None      # explicit revenue, years 1..N ($M)

    def revenues(self, n_years: int) -> tuple:
        """Return revenue for years 1..n_years ($M)."""
        if self.revenue_path is not None:
            _require_len(self.revenue_path, n_years, f"{self.name}.revenue_path")
            return tuple(float(x) for x in self.revenue_path)
        if self.tam_path is not None and self.share_path is not None:
            _require_len(self.tam_path, n_years, f"{self.name}.tam_path")
            _require_len(self.share_path, n_years, f"{self.name}.share_path")
            return tuple(float(t) * float(s) for t, s in zip(self.tam_path, self.share_path))
        raise ValueError(
            f"Segment '{self.name}' needs either revenue_path or (tam_path & share_path)."
        )


@dataclass(frozen=True)
class ValuationInputs:
    """The full set of intrinsic-DCF assumptions for one company at one date."""

    company: str
    valuation_date: str                       # ISO date, e.g. "2023-06-10"

    # --- Driver 1: growth -------------------------------------------------
    base_revenue: float                       # trailing/base-year revenue ($M)
    revenue_growth: tuple                     # growth rate for each of years 1..N
    #   (length N defines the explicit forecast horizon)

    # --- Driver 2: profitability -----------------------------------------
    base_operating_margin: float              # current (adjusted) pre-tax op margin
    target_operating_margin: float            # steady-state pre-tax op margin
    margin_convergence_year: int              # year by which target is reached

    # --- Driver 3: reinvestment efficiency -------------------------------
    sales_to_capital: float                   # $ revenue per $ capital invested

    # --- Driver 4: risk ---------------------------------------------------
    tax_rate: float                           # marginal tax rate
    cost_of_capital_initial: float            # CoC during initial growth period
    cost_of_capital_terminal: float           # mature/market CoC
    coc_glide_start_year: int                 # year CoC begins drifting down
    coc_glide_end_year: int                   # year CoC reaches terminal

    # --- Terminal value ---------------------------------------------------
    terminal_growth: float                    # stable growth (<= riskfree rate)
    terminal_roc: float                       # stable return on capital -> reinvestment

    # --- Bridge from operating assets to per-share value ------------------
    cash: float                               # cash + marketable securities ($M)
    debt: float                               # total debt ($M)
    shares_outstanding: float                 # millions of shares
    minority_interests: float = 0.0           # ($M)
    nonoperating_assets: float = 0.0          # cross-holdings etc. ($M)
    failure_probability: float = 0.0          # P(catastrophic failure)
    failure_value_per_share: float = 0.0      # distress value / share if failure

    # --- Optional tax ramp (effective today -> marginal long-term) -------
    effective_tax_rate: Optional[float] = None  # initial effective rate; if None, flat tax_rate
    tax_convergence_year: int = 1               # year effective rate reaches marginal (tax_rate)

    # --- Optional bottoms-up segments (override base_revenue/revenue_growth)
    segments: tuple = field(default_factory=tuple)

    def __post_init__(self):
        """Validate economic invariants up front so a bad assumption fails loudly
        with a clear message instead of silently producing a wrong value."""
        if self.shares_outstanding <= 0:
            raise ValueError("shares_outstanding must be positive.")
        if self.terminal_growth < 0:
            raise ValueError("terminal_growth must be >= 0.")
        if self.terminal_roc <= self.terminal_growth:
            raise ValueError(
                f"terminal_roc ({self.terminal_roc}) must exceed terminal_growth "
                f"({self.terminal_growth}); otherwise the implied reinvestment rate "
                f"g/ROC is >= 100% and terminal FCFF is non-positive.")
        if self.cost_of_capital_terminal <= self.terminal_growth:
            raise ValueError(
                f"terminal cost of capital ({self.cost_of_capital_terminal}) must "
                f"exceed terminal_growth ({self.terminal_growth}).")
        if self.margin_convergence_year < 1:
            raise ValueError("margin_convergence_year must be >= 1.")
        if self.coc_glide_start_year < 1:
            raise ValueError("coc_glide_start_year must be >= 1.")
        if self.coc_glide_end_year <= self.coc_glide_start_year:
            raise ValueError(
                f"coc_glide_end_year ({self.coc_glide_end_year}) must exceed "
                f"coc_glide_start_year ({self.coc_glide_start_year}); otherwise "
                f"the CoC path degenerates to a step function instead of a glide.")
        if not (0.0 <= self.tax_rate < 1.0):
            raise ValueError("tax_rate must be in [0, 1).")

    # ---- helpers --------------------------------------------------------
    @property
    def horizon(self) -> int:
        return len(self.revenue_growth)

    def with_(self, **overrides) -> "ValuationInputs":
        """Return a new ValuationInputs with fields replaced (immutable update)."""
        return replace(self, **overrides)

    def revenue_path(self) -> tuple:
        """Revenue for years 0..N. If segments are supplied, build bottom-up
        and DERIVE base_revenue + growth from them; otherwise compound
        base_revenue by revenue_growth."""
        n = self.horizon
        if self.segments:
            base = sum(s.base_revenue for s in self.segments)
            per_year = [sum(col) for col in zip(*[s.revenues(n) for s in self.segments])]
            return tuple([base] + per_year)
        revs = [self.base_revenue]
        for g in self.revenue_growth:
            revs.append(revs[-1] * (1.0 + g))
        return tuple(revs)

    def to_dict(self) -> dict:
        return asdict(self)


def _require_len(seq, n: int, label: str) -> None:
    if len(seq) != n:
        raise ValueError(f"{label} must have length {n}, got {len(seq)}.")


def _tuplify(d: dict) -> dict:
    """Convert JSON lists into tuples for the frozen dataclasses.
    Keys starting with '_' are treated as comments and dropped."""
    out = {k: v for k, v in d.items() if not k.startswith("_")}
    for key in ("revenue_growth",):
        if key in out and out[key] is not None:
            out[key] = tuple(out[key])
    segs = out.get("segments")
    if segs:
        built = []
        for s in segs:
            s = dict(s)
            for k in ("tam_path", "share_path", "revenue_path"):
                if s.get(k) is not None:
                    s[k] = tuple(s[k])
            built.append(Segment(**s))
        out["segments"] = tuple(built)
    return out


def build_declining_growth(base_revenue: float, target_terminal_revenue: float,
                           terminal_growth: float, n: int) -> tuple:
    """Solve the year-1 growth rate for a path that declines linearly from g1
    (year 1) to terminal_growth (year n) and compounds base_revenue up to
    target_terminal_revenue in year n. Returns n growth rates.

    Used to (a) generate the example growth path and (b) re-shape the path in
    Monte Carlo trials when year-10 revenue is sampled."""
    def path(g1: float) -> list:
        return [g1 + (terminal_growth - g1) * ((t - 1) / (n - 1)) for t in range(1, n + 1)]

    def final(g1: float) -> float:
        rev = base_revenue
        for g in path(g1):
            rev *= (1.0 + g)
        return rev

    lo, hi = -0.5, 5.0
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if final(mid) < target_terminal_revenue else (lo, mid)
    return tuple(round(x, 6) for x in path((lo + hi) / 2))


def load_inputs(path: str) -> ValuationInputs:
    """Load a ValuationInputs from a JSON assumptions file."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return ValuationInputs(**_tuplify(raw))


def inputs_from_dict(raw: dict) -> ValuationInputs:
    return ValuationInputs(**_tuplify(raw))
