"""Sync products from a Shopify collection into the Airtable Products table.

Usage:
    python sync_products.py [collection-handle]

Defaults to "short-dated-but-delicious" if no handle is provided.
New products are added with Monitor unchecked — tick it in Airtable
to start tracking their prices.
"""

import logging
import sys

import config
from scraper import fetch_collection_products
from airtable_client import upsert_product

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

DEFAULT_COLLECTION = "short-dated-but-delicious"


def sync(collection_handle: str) -> None:
    """Fetch all products from a collection and upsert them into Airtable."""
    config.validate_required_config()
    log.info("Fetching products from collection: %s", collection_handle)

    products = fetch_collection_products(collection_handle)
    log.info("Found %d product(s) on Shopify.", len(products))

    added = 0
    skipped = 0

    for p in products:
        _record, created = upsert_product(
            name=p.title,
            handle=p.handle,
            url=p.url,
            price=p.price,
            vendor=p.vendor,
        )

        if created:
            log.info("  [added]  %s", p.title)
            added += 1
        else:
            log.info("  [exists] %s", p.title)
            skipped += 1

    log.info(
        "Sync complete. %d added, %d already existed.",
        added, skipped,
    )


if __name__ == "__main__":
    collection = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_COLLECTION
    try:
        sync(collection)
    except config.ConfigError as exc:
        log.error("%s", exc)
        sys.exit(2)
