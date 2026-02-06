import os
from dotenv import load_dotenv

load_dotenv()

# Airtable
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
PRODUCTS_TABLE = os.getenv("AIRTABLE_PRODUCTS_TABLE", "Products")
PRICE_HISTORY_TABLE = os.getenv("AIRTABLE_PRICE_HISTORY_TABLE", "Price History")

# Shopify
SHOPIFY_STORE_DOMAIN = os.getenv("SHOPIFY_STORE_DOMAIN", "feastitaly.com")
