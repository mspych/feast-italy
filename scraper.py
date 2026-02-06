"""Shopify JSON price fetcher.

Shopify stores expose product data at /products/<handle>.json,
returning structured JSON with price, compare-at price, availability, etc.
"""

import requests
from dataclasses import dataclass
from typing import Optional

import config


@dataclass
class ProductPrice:
    """Parsed price data from a Shopify product."""
    title: str
    handle: str
    price: float
    compare_at_price: Optional[float]
    currency: str
    available: bool
    inventory_quantity: int
    image_url: Optional[str]


def fetch_price(handle: str, domain: str = None) -> ProductPrice:
    """Fetch current price for a product from Shopify's JSON endpoint.

    Args:
        handle: The Shopify product handle (URL slug), e.g. "acacia-honey-and-almonds-170g"
        domain: Shopify store domain. Defaults to config.SHOPIFY_STORE_DOMAIN.

    Returns:
        ProductPrice with current pricing data.

    Raises:
        requests.HTTPError: If the request fails.
        KeyError: If the JSON structure is unexpected.
    """
    domain = domain or config.SHOPIFY_STORE_DOMAIN
    url = f"https://{domain}/products/{handle}.json"

    response = requests.get(url, timeout=15)
    response.raise_for_status()

    data = response.json()
    product = data["product"]
    variant = product["variants"][0]

    compare_at = variant.get("compare_at_price")

    image_url = None
    if product.get("image") and product["image"].get("src"):
        image_url = product["image"]["src"]

    return ProductPrice(
        title=product["title"],
        handle=product["handle"],
        price=float(variant["price"]),
        compare_at_price=float(compare_at) if compare_at else None,
        currency=variant.get("price_currency", "GBP"),
        available=variant.get("inventory_quantity", 0) > 0,
        inventory_quantity=variant.get("inventory_quantity", 0),
        image_url=image_url,
    )
