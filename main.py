"""Feast Italy Price Drop Monitor.

Twice a day, scan the short-dated Shopify collection, add any new products
to Airtable at their first-seen price, and flag existing products when the
sale price drops again by a significant amount.
"""

import logging
import sys

import config
from scraper import fetch_collection_products
from pricing import drop_amount, drop_percent, is_significant_drop
from airtable_client import (
    products_by_handle,
    upsert_product,
    update_product,
    log_price_check,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def scan_collection_product(product, existing: dict | None) -> str:
    """Compare one collection product against the Airtable record.

    Returns:
        One of: "added", "further_reduction", "checked".
    """
    if existing is None:
        record, _created = upsert_product(
            name=product.title,
            handle=product.handle,
            url=product.url,
            price=product.price,
            vendor=product.vendor,
            monitor=True,
        )
        log_price_check(
            product_record_id=record["id"],
            price=product.price,
            previous_price=None,
            price_dropped=False,
        )
        log.info(
            "  [added] %s — first seen at %s%.2f",
            product.title,
            product.currency,
            product.price,
        )
        return "added"

    previous_price = existing.get("fields", {}).get("Current Price")
    current_price = product.price
    amount = drop_amount(previous_price, current_price)
    percent = drop_percent(previous_price, current_price)
    significant = is_significant_drop(
        previous_price,
        current_price,
        min_percent=config.SIGNIFICANT_DROP_PERCENT,
        min_amount=config.SIGNIFICANT_DROP_AMOUNT,
    )

    if previous_price is None:
        log.info(
            "  [baseline] %s — recording %s%.2f",
            product.title,
            product.currency,
            current_price,
        )
    elif significant:
        log.info(
            "  [further reduction] %s — %s%.2f -> %s%.2f (%.1f%% / %s%.2f)",
            product.title,
            product.currency,
            previous_price,
            product.currency,
            current_price,
            percent or 0.0,
            product.currency,
            amount or 0.0,
        )
    elif amount is not None and amount > 0:
        log.info(
            "  [small drop] %s — %s%.2f -> %s%.2f (below threshold)",
            product.title,
            product.currency,
            previous_price,
            product.currency,
            current_price,
        )
    else:
        log.info(
            "  [checked] %s — still %s%.2f",
            product.title,
            product.currency,
            current_price,
        )

    log_price_check(
        product_record_id=existing["id"],
        price=current_price,
        previous_price=previous_price,
        price_dropped=significant,
        change=amount,
    )
    update_product(
        existing["id"],
        current_price,
        further_reduction=significant,
        monitor=True,
    )
    return "further_reduction" if significant else "checked"


def main() -> None:
    """Scan the short-dated collection and record further markdowns."""
    log.info("=== Feast Italy Price Monitor ===")
    config.validate_required_config()
    log.info(
        "Collection: %s | significant drop: >= %.1f%% and >= %.2f",
        config.COLLECTION_HANDLE,
        config.SIGNIFICANT_DROP_PERCENT,
        config.SIGNIFICANT_DROP_AMOUNT,
    )

    collection = fetch_collection_products(config.COLLECTION_HANDLE)
    log.info("Found %d product(s) on Shopify.", len(collection))

    if not collection:
        log.warning("Collection is empty. Nothing to check.")
        return

    existing_by_handle = products_by_handle()
    added = 0
    reductions = 0
    checked = 0
    errors = 0

    for product in collection:
        try:
            result = scan_collection_product(
                product,
                existing_by_handle.get(product.handle),
            )
        except Exception as exc:
            log.error("Error checking '%s': %s", product.title, exc, exc_info=True)
            errors += 1
            continue

        if result == "added":
            added += 1
        elif result == "further_reduction":
            reductions += 1
        else:
            checked += 1

    log.info(
        "Done. %d added, %d further reduction(s), %d unchanged, %d error(s).",
        added,
        reductions,
        checked,
        errors,
    )

    if errors:
        sys.exit(1)


def check_config() -> None:
    """Validate required env vars and Shopify connectivity (preflight)."""
    config.validate_required_config()
    log.info("Config OK: Airtable base %s", config.AIRTABLE_BASE_ID)
    products = fetch_collection_products(config.COLLECTION_HANDLE)
    log.info(
        "Shopify OK: %s — %d product(s) in %s",
        config.SHOPIFY_STORE_DOMAIN,
        len(products),
        config.COLLECTION_HANDLE,
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in {"--check-config", "check-config"}:
        try:
            check_config()
        except config.ConfigError as exc:
            log.error("%s", exc)
            sys.exit(2)
        except Exception as exc:
            log.error("Preflight failed: %s", exc, exc_info=True)
            sys.exit(1)
        else:
            log.info("Preflight passed.")
            sys.exit(0)

    try:
        main()
    except config.ConfigError as exc:
        log.error("%s", exc)
        # Missing config is a real deployment failure. restartPolicyType=NEVER
        # prevents Railway restart loops for this one-shot worker.
        sys.exit(2)
