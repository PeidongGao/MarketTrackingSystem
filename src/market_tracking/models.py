from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class DailyBar:
    date: date
    close: float
    high: float
    low: float
    timestamp: datetime


@dataclass(frozen=True)
class MarketData:
    bars: list[DailyBar]
    fifty_two_week_low: float | None = None
    fifty_two_week_high: float | None = None
    regular_market_time: datetime | None = None
    source: str = "unknown"


@dataclass(frozen=True)
class TickerReport:
    ticker: str
    source: str
    source_url: str
    week_ending: date
    data_time: datetime
    close_price: float
    fifty_two_week_low: float
    fifty_two_week_high: float
    previous_week_close_date: date
    previous_week_close_price: float
    drawdown: float
    week_over_week: float


@dataclass(frozen=True)
class FieldCheck:
    """One cross-checked value across sources and/or methods."""

    field: str
    values: dict[str, float | None]
    status: str  # "confirmed" | "single" | "advisory" | "mismatch" | "unavailable"
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status != "mismatch"


@dataclass(frozen=True)
class ValidationReport:
    ticker: str
    checks: list[FieldCheck] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    @property
    def mismatches(self) -> list[FieldCheck]:
        return [check for check in self.checks if check.status == "mismatch"]
