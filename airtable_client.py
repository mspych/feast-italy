"""Airtable read/write helpers for Products and Price History tables."""

from datetime import datetime, timezone
import logging
from typing import Optional

from pyairtable import Api

import config

log = logging.getLogger(__name__)


def _get_api() -> Api:
    config.validate_required_config()
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


def get_monitored_products() -> list[dict]:
    """Return only products where the Monitor checkbox is checked."""
    return _products_table().all(formula="{Monitor}")


def get_product_by_handle(handle: str) -> Optional[dict]:
    """Find a single product by its Shopify Handle field."""
    escaped_handle = handle.replace("'", "\\'")
    records = _products_table().all(
        formula=f"{{Shopify Handle}} = '{escaped_handle}'"
    )
    return records[0] if records else None


def products_by_handle() -> dict[str, dict]:
    """Index every product that has a Shopify Handle."""
    indexed: dict[str, dict] = {}
    for record in get_all_products():
        handle = record.get("fields", {}).get("Shopify Handle")
        if handle:
            indexed[handle] = record
    return indexed


def upsert_product(
    name: str,
    handle: str,
    url: str,
    price: float,
    vendor: str = "",
    monitor: bool = True,
) -> tuple[dict, bool]:
    """Create a product if it doesn't exist, or return the existing record.

    New collection products are created with Monitor checked so later scans
    can detect a further markdown against this first-seen price.

    Returns:
        A tuple of (record, created).
    """
    existing = get_product_by_handle(handle)
    if existing:
        return existing, False

    fields = {
        "Name": name,
        "Shopify Handle": handle,
        "URL": url,
        "Current Price": price,
        "Monitor": monitor,
    }
    if vendor:
        fields["Vendor"] = vendor

    try:
        return _products_table().create(fields), True
    except Exception:
        # If some fields don't exist in the table, try with just the essentials
        return _products_table().create({
            "Name": name,
            "Shopify Handle": handle,
            "URL": url,
            "Current Price": price,
            "Monitor": monitor,
        }), True


def _format_date(dt: datetime) -> str:
    """Format a datetime as a date string for Airtable (YYYY-MM-DD)."""
    return dt.strftime("%Y-%m-%d")


def update_product(
    record_id: str,
    price: float,
    checked_at: datetime = None,
    further_reduction: Optional[bool] = None,
    monitor: Optional[bool] = None,
):
    """Update a product's Current Price, Last Checked, and reduction flag."""
    checked_at = checked_at or datetime.now(timezone.utc)
    fields = {
        "Current Price": price,
        "Last Checked": _format_date(checked_at),
    }
    if further_reduction is not None:
        fields["Further Reduction"] = further_reduction
    if monitor is not None:
        fields["Monitor"] = monitor
    try:
        _products_table().update(record_id, fields)
    except Exception as exc:
        log.warning("Could not update product %s: %s", record_id, exc)


# ---------------------------------------------------------------------------
# Price History table
# ---------------------------------------------------------------------------


def log_price_check(
    product_record_id: str,
    price: float,
    previous_price: Optional[float],
    price_dropped: bool = False,
    change: Optional[float] = None,
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
        "Checked At": _format_date(checked_at),
        "Price Dropped": price_dropped,
    }
    if previous_price is not None:
        fields["Previous Price"] = previous_price
    if change is not None:
        fields["Change"] = change

    return _price_history_table().create(fields)
