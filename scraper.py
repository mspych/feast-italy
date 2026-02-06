"""Shopify JSON price fetcher.

Shopify stores expose product data at /products/<handle>.json,
returning structured JSON with price, compare-at price, availability, etc.
Collections are available at /collections/<handle>/products.json.
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


@dataclass
class CollectionProduct:
    """Basic product info from a Shopify collection listing."""
    title: str
    handle: str
    vendor: str
    product_type: str
    price: float
    compare_at_price: Optional[float]
    currency: str
    url: str


def fetch_collection_products(
    collection_handle: str,
    domain: str = None,
) -> list[CollectionProduct]:
    """Fetch all products from a Shopify collection.

    Args:
        collection_handle: The collection URL slug, e.g. "short-dated-but-delicious"
        domain: Shopify store domain. Defaults to config.SHOPIFY_STORE_DOMAIN.

    Returns:
        List of CollectionProduct with basic product data.
    """
    domain = domain or config.SHOPIFY_STORE_DOMAIN
    products = []
    page = 1

    while True:
        url = f"https://{domain}/collections/{collection_handle}/products.json?limit=50&page={page}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        data = response.json()
        batch = data.get("products", [])
        if not batch:
            break

        for p in batch:
            variant = p["variants"][0]
            compare_at = variant.get("compare_at_price")
            products.append(CollectionProduct(
                title=p["title"],
                handle=p["handle"],
                vendor=p.get("vendor", ""),
                product_type=p.get("product_type", ""),
                price=float(variant["price"]),
                compare_at_price=float(compare_at) if compare_at else None,
                currency=variant.get("price_currency", "GBP"),
                url=f"https://{domain}/products/{p['handle']}",
            ))

        page += 1

    return products


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
