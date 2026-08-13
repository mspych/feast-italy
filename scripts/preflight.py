#!/usr/bin/env python3
"""Preflight checks before enabling or redeploying the Railway cron worker.

Usage:
    python scripts/preflight.py
    railway run python scripts/preflight.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from scraper import fetch_collection_products  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def main() -> int:
    try:
        config.validate_required_config()
    except config.ConfigError as exc:
        log.error("%s", exc)
        return 2

    log.info("Config OK: Airtable base %s", config.AIRTABLE_BASE_ID)
    try:
        products = fetch_collection_products("short-dated-but-delicious")
    except Exception as exc:
        log.error("Shopify connectivity failed: %s", exc, exc_info=True)
        return 1

    log.info(
        "Shopify OK: %s — %d product(s) in short-dated-but-delicious",
        config.SHOPIFY_STORE_DOMAIN,
        len(products),
    )
    log.info("Preflight passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
