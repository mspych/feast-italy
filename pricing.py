"""Helpers for deciding when a further markdown is significant."""

from typing import Optional


def drop_amount(previous: Optional[float], current: float) -> Optional[float]:
    """Return previous minus current, or None when there is no baseline."""
    if previous is None:
        return None
    return round(previous - current, 2)


def drop_percent(previous: Optional[float], current: float) -> Optional[float]:
    """Return the drop as a percentage of the previous price."""
    if previous is None or previous <= 0:
        return None
    return round((previous - current) / previous * 100, 2)


def is_significant_drop(
    previous: Optional[float],
    current: float,
    min_percent: float,
    min_amount: float,
) -> bool:
    """True when an existing product got another meaningful markdown.

    First-seen products (no previous price) are a baseline, not a drop.
    Tiny penny moves are ignored unless they also clear the percent floor
    and the absolute amount floor.
    """
    if previous is None or current >= previous:
        return False
    amount = previous - current
    percent = amount / previous * 100
    return amount + 1e-9 >= min_amount and percent + 1e-9 >= min_percent
