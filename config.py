import os
from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """Raised when required runtime configuration is missing."""


def _get_required(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None


# Airtable
AIRTABLE_API_KEY = _get_required("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = _get_required("AIRTABLE_BASE_ID")
PRODUCTS_TABLE = os.getenv("AIRTABLE_PRODUCTS_TABLE", "Products")
PRICE_HISTORY_TABLE = os.getenv("AIRTABLE_PRICE_HISTORY_TABLE", "Price History")

# Shopify
SHOPIFY_STORE_DOMAIN = os.getenv("SHOPIFY_STORE_DOMAIN", "feastitaly.com")
COLLECTION_HANDLE = os.getenv(
    "SHOPIFY_COLLECTION_HANDLE",
    "short-dated-but-delicious",
)

# Further-reduction threshold for products already in Airtable.
# A drop counts when it is at least this percent AND at least this amount.
SIGNIFICANT_DROP_PERCENT = float(os.getenv("SIGNIFICANT_DROP_PERCENT", "5"))
SIGNIFICANT_DROP_AMOUNT = float(os.getenv("SIGNIFICANT_DROP_AMOUNT", "0.50"))


def validate_required_config() -> None:
    """Fail with a clear message instead of an import-time KeyError."""
    missing = [
        name
        for name, value in {
            "AIRTABLE_API_KEY": AIRTABLE_API_KEY,
            "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
        }.items()
        if not value
    ]
    if missing:
        raise ConfigError(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". Set them in Railway service variables or in a local .env file."
        )
