"""Feast Italy Price Drop Monitor.

Entry point: fetches prices for all products in the Airtable Products table,
logs each check to Price History, and flags price drops so Airtable automations
can handle notifications.
"""

import logging
import sys

import config  # noqa: F401 — ensures env vars are loaded early
from scraper import fetch_price
from airtable_client import (
    get_monitored_products,
    update_product,
    log_price_check,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def check_product(record: dict) -> None:
    """Check a single product for price changes.

    Args:
        record: An Airtable record dict from the Products table.
    """
    fields = record["fields"]
    name = fields.get("Name", "Unknown")
    handle = fields.get("Shopify Handle")
    previous_price = fields.get("Current Price")

    if not handle:
        log.warning("Skipping product '%s' — no Shopify Handle set.", name)
        return

    # 1. Fetch current price from Shopify
    log.info("Checking price for: %s", name)
    price_data = fetch_price(handle)
    current_price = price_data.price

    log.info(
        "  %s — current: %s%.2f | previous: %s",
        name,
        price_data.currency,
        current_price,
        f"{price_data.currency}{previous_price:.2f}" if previous_price else "first check",
    )

    # 2. Determine if the price dropped
    price_dropped = (
        previous_price is not None and current_price < previous_price
    )

    if price_dropped:
        log.info(
            "  PRICE DROP detected! %s%.2f -> %s%.2f",
            price_data.currency, previous_price,
            price_data.currency, current_price,
        )
    elif previous_price is None:
        log.info("  First check recorded.")
    else:
        log.info("  No price change.")

    # 3. Log to Price History table (Airtable automation will handle email if Price Dropped is true)
    log_price_check(
        product_record_id=record["id"],
        price=current_price,
        previous_price=previous_price,
        price_dropped=price_dropped,
    )

    # 4. Update product's current price and last-checked timestamp
    update_product(record["id"], current_price)


def main() -> None:
    """Run the price check for all products in Airtable."""
    log.info("=== Feast Italy Price Monitor ===")

    products = get_monitored_products()
    log.info("Found %d monitored product(s) to check.", len(products))

    if not products:
        log.warning("No monitored products found. Tick the 'Monitor' checkbox in the '%s' table.", config.PRODUCTS_TABLE)
        return

    errors = 0
    for record in products:
        try:
            check_product(record)
        except Exception as exc:
            name = record.get("fields", {}).get("Name", record["id"])
            log.error("Error checking '%s': %s", name, exc, exc_info=True)
            errors += 1

    log.info("Done. Checked %d product(s), %d error(s).", len(products), errors)

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
