"""Input model for cyclical/commodity valuation.

The standard FCFF engine is intentionally generic. For commodity producers,
memory, panels, shipping, chemicals, and other deep cyclicals, the valuation
needs one more layer: price deck, cost deck, volume/capacity, and mid-cycle
normalization. This module loads that structured layer without changing the
generic DCF input contract.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from typing import Optional


@dataclass(frozen=True)
class CommodityInfo:
    name: str
    price_unit: str
    volume_unit: str = ""
    currency: str = ""


@dataclass(frozen=True)
class CycleState:
    current_phase: str
    current_price: float
    normalized_price: float
    trough_price: float
    peak_price: float
    price_shift_mode: str = "relative"  # relative or absolute

    @property
    def price_percentile(self) -> float:
        spread = self.peak_price - self.trough_price
        if spread <= 0:
            return 0.5
        return max(0.0, min(1.0, (self.current_price - self.trough_price) / spread))


@dataclass(frozen=True)
class RevenueModel:
    """How price and volume become revenue.

    type = physical:
        revenue_m = price * volume * volume_multiplier / 1,000,000
        Example: RMB/t * kt * 1000 / 1e6 = RMB millions.

    type = indexed:
        revenue_m = base_revenue_m * (price/base_price) * (volume/base_volume)
        Useful for panel, memory, or shipping index models.

    type = explicit:
        each forecast row must provide revenue_m directly.
    """

    type: str = "physical"
    volume_multiplier: float = 1.0
    base_revenue_m: Optional[float] = None
    base_price: Optional[float] = None
    base_volume: Optional[float] = None


@dataclass(frozen=True)
class ForecastYear:
    year: int
    price: float
    volume: float = 0.0
    cash_cost: Optional[float] = None
    utilization: Optional[float] = None
    ebitda_margin: Optional[float] = None
    revenue_m: Optional[float] = None
    ebitda_m: Optional[float] = None
    fixed_cost_m: float = 0.0
    da_m: float = 0.0
    capex_m: float = 0.0
    working_capital_m: float = 0.0
    wacc: Optional[float] = None
    phase: str = ""


@dataclass(frozen=True)
class ValuationConfig:
    shares_outstanding: float
    net_debt_m: float = 0.0
    tax_rate: float = 0.25
    wacc: float = 0.09
    terminal_ebitda_multiple: float = 6.0
    midcycle_ev_ebitda_multiple: float = 6.0
    normalized_ebitda_m: Optional[float] = None
    normalized_ebitda_price_sensitivity_m_per_unit: Optional[float] = None
    normalized_ebitda_floor_m: float = 0.0
    asset_npv_m: Optional[float] = None
    method_weights: dict = field(default_factory=dict)


@dataclass(frozen=True)
class CyclicalInputs:
    company: str
    ticker: str
    valuation_date: str
    commodity: CommodityInfo
    cycle: CycleState
    revenue_model: RevenueModel
    forecast: tuple[ForecastYear, ...]
    valuation: ValuationConfig
    cost_curve: tuple[dict, ...] = field(default_factory=tuple)
    source_notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def horizon(self) -> int:
        return len(self.forecast)

    def with_normalized_price(self, normalized_price: float) -> "CyclicalInputs":
        """Return a copy with the cycle's normalized price changed.

        The explicit forecast deck is shifted by the same relative factor or
        absolute delta, controlled by cycle.price_shift_mode. This lets reverse
        DCF answer "what commodity/panel price deck is embedded in the share
        price?" rather than solving a generic revenue growth rate.
        """
        if normalized_price <= 0:
            raise ValueError("normalized_price must be positive.")

        old = self.cycle.normalized_price
        if old <= 0:
            raise ValueError("existing normalized_price must be positive.")

        if self.cycle.price_shift_mode == "absolute":
            delta = normalized_price - old
            shifted = tuple(replace(row, price=max(0.0, row.price + delta)) for row in self.forecast)
        else:
            factor = normalized_price / old
            delta = normalized_price - old
            shifted = tuple(replace(row, price=max(0.0, row.price * factor)) for row in self.forecast)

        valuation = self.valuation
        sensitivity = valuation.normalized_ebitda_price_sensitivity_m_per_unit
        if valuation.normalized_ebitda_m is not None and sensitivity is not None:
            adjusted_ebitda = max(
                valuation.normalized_ebitda_floor_m,
                valuation.normalized_ebitda_m + delta * sensitivity,
            )
            valuation = replace(valuation, normalized_ebitda_m=adjusted_ebitda)

        return replace(
            self,
            cycle=replace(self.cycle, normalized_price=normalized_price),
            forecast=shifted,
            valuation=valuation,
        )

    def to_dict(self) -> dict:
        return asdict(self)


def _strip_comments(obj):
    if isinstance(obj, dict):
        return {k: _strip_comments(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_strip_comments(v) for v in obj]
    return obj


def _tuple_of(cls, values) -> tuple:
    return tuple(cls(**dict(v)) for v in values)


def inputs_from_dict(raw: dict) -> CyclicalInputs:
    data = _strip_comments(raw)
    commodity = CommodityInfo(**data["commodity"])
    cycle = CycleState(**data["cycle"])
    revenue_model = RevenueModel(**data.get("revenue_model", {}))
    forecast = _tuple_of(ForecastYear, data["forecast"])
    valuation = ValuationConfig(**data["valuation"])
    cost_curve = tuple(dict(v) for v in data.get("cost_curve", ()))
    source_notes = tuple(str(v) for v in data.get("source_notes", ()))
    inp = CyclicalInputs(
        company=data["company"],
        ticker=data["ticker"],
        valuation_date=data["valuation_date"],
        commodity=commodity,
        cycle=cycle,
        revenue_model=revenue_model,
        forecast=forecast,
        valuation=valuation,
        cost_curve=cost_curve,
        source_notes=source_notes,
    )
    _validate(inp)
    return inp


def load_cyclical_inputs(path: str) -> CyclicalInputs:
    with open(path, "r", encoding="utf-8") as fh:
        return inputs_from_dict(json.load(fh))


def _validate(inp: CyclicalInputs) -> None:
    if not inp.forecast:
        raise ValueError("forecast must contain at least one year.")
    if inp.valuation.shares_outstanding <= 0:
        raise ValueError("shares_outstanding must be positive.")
    if not (0 <= inp.valuation.tax_rate < 1):
        raise ValueError("tax_rate must be in [0, 1).")
    if inp.valuation.wacc <= 0:
        raise ValueError("wacc must be positive.")
    if inp.valuation.terminal_ebitda_multiple < 0:
        raise ValueError("terminal_ebitda_multiple must be non-negative.")
    if inp.valuation.midcycle_ev_ebitda_multiple < 0:
        raise ValueError("midcycle_ev_ebitda_multiple must be non-negative.")
    if inp.cycle.peak_price <= inp.cycle.trough_price:
        raise ValueError("peak_price must exceed trough_price.")
    if inp.cycle.price_shift_mode not in {"relative", "absolute"}:
        raise ValueError("price_shift_mode must be 'relative' or 'absolute'.")

    model = inp.revenue_model
    if model.type not in {"physical", "indexed", "explicit"}:
        raise ValueError("revenue_model.type must be physical, indexed, or explicit.")
    if model.type == "physical" and model.volume_multiplier <= 0:
        raise ValueError("physical revenue model needs volume_multiplier > 0.")
    if model.type == "indexed":
        missing = [
            k for k in ("base_revenue_m", "base_price", "base_volume")
            if getattr(model, k) in (None, 0)
        ]
        if missing:
            raise ValueError(f"indexed revenue model missing: {', '.join(missing)}")
    if model.type == "explicit":
        for row in inp.forecast:
            if row.revenue_m is None:
                raise ValueError("explicit revenue model requires row.revenue_m.")
