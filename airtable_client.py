"""Airtable read/write helpers for Products and Price History tables."""

from datetime import datetime, timezone
from typing import Optional

from pyairtable import Api

import config


def _get_api() -> Api:
    return Api(config.AIRTABLE_API_KEY)


def _products_table():
    return _get_api().table(config.AIRTABLE_BASE_ID, config.PRODUCTS_TABLE)


def _price_history_table():
    return _get_api().table(config.AIRTABLE_BASE_ID, config.PRICE_HISTORY_TABLE)


# ---------------------------------------------------------------------------
# Products table
# ---------------------------------------------------------------------------


def get_all_products() -> list[dict]:
    """Return all rows from the Products table."""
    return _products_table().all()


def get_product_by_handle(handle: str) -> Optional[dict]:
    """Find a single product by its Shopify Handle field."""
    records = _products_table().all(
        formula=f"{{Shopify Handle}} = '{handle}'"
    )
    return records[0] if records else None


def update_product(record_id: str, price: float, checked_at: datetime = None):
    """Update a product's Current Price and Last Checked timestamp."""
    checked_at = checked_at or datetime.now(timezone.utc)
    _products_table().update(record_id, {
        "Current Price": price,
        "Last Checked": checked_at.isoformat(),
    })


# ---------------------------------------------------------------------------
# Price History table
# ---------------------------------------------------------------------------


def log_price_check(
    product_record_id: str,
    price: float,
    previous_price: Optional[float],
    price_dropped: bool = False,
    checked_at: datetime = None,
) -> dict:
    """Create a new row in the Price History table.

    Args:
        product_record_id: Airtable record ID of the product (for the linked field).
        price: The current price just fetched.
        previous_price: The price from the last check (None if first check).
        price_dropped: Whether the price decreased since the last check.
            Airtable automations can trigger on this flag to send notifications.
        checked_at: Timestamp of the check. Defaults to now (UTC).

    Returns:
        The created Airtable record.
    """
    checked_at = checked_at or datetime.now(timezone.utc)

    fields = {
        "Product": [product_record_id],
        "Price": price,
        "Checked At": checked_at.isoformat(),
        "Price Dropped": price_dropped,
    }
    if previous_price is not None:
        fields["Previous Price"] = previous_price

    return _price_history_table().create(fields)
