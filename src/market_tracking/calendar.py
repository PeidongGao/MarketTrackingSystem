from __future__ import annotations

from datetime import date, timedelta

from market_tracking.models import DailyBar


def latest_completed_week_ending(today: date) -> date:
    """Return the Friday for the latest completed reporting week."""
    days_since_friday = (today.weekday() - 4) % 7
    friday = today - timedelta(days=days_since_friday)
    if today.weekday() == 4:
        friday -= timedelta(days=7)
    return friday


def validate_completed_week_ending(requested: date, today: date) -> None:
    """Require a calendar Friday whose reporting week has fully completed."""
    if requested.weekday() != 4:
        raise ValueError(
            f"Week ending must be a Friday; received {requested.isoformat()}."
        )
    latest = latest_completed_week_ending(today)
    if requested > latest:
        raise ValueError(
            f"Week ending {requested.isoformat()} is not complete; "
            f"latest completed week is {latest.isoformat()}."
        )


def select_weekly_closes(
    bars: list[DailyBar], requested_week_ending: date
) -> tuple[DailyBar, DailyBar]:
    if not bars:
        raise ValueError("No price history is available.")

    sorted_bars = sorted(bars, key=lambda bar: bar.date)
    week_start = requested_week_ending - timedelta(days=requested_week_ending.weekday())

    current_candidates = [bar for bar in sorted_bars if week_start <= bar.date <= requested_week_ending]
    if not current_candidates:
        raise ValueError(f"No trading data found for week ending {requested_week_ending}.")
    current = current_candidates[-1]

    previous_candidates = [bar for bar in sorted_bars if bar.date < week_start]
    if not previous_candidates:
        raise ValueError(f"No previous-week close found before {week_start}.")
    previous = previous_candidates[-1]

    return current, previous
