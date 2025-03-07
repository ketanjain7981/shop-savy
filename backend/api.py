import json
import os
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()
# Path to the products data file
DATA_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"
SHOPIFY_ACCESS_KEY = os.environ.get("SHOPIFY_ACCESS_KEY")
SHOPIFY_STORE_NAME = os.environ.get("SHOPIFY_STORE_NAME")

def transform_product_response(product):
    
    transformed_product = {
        "product": {
            "id": product.get("id"),
            "title": product.get("title"),
            "tags": product.get("tags", ""),
            "status": product.get("status"),
            "variants": [
                {
                    "id": variant.get("id"),
                    "product_id": variant.get("product_id"),
                    "title": variant.get("title"),
                    "price": variant.get("price"),
                    "position": variant.get("position"),
                    "inventory_policy": variant.get("inventory_policy"),
                    "compare_at_price": variant.get("compare_at_price"),
                    "option1": variant.get("option1"),
                    "option2": variant.get("option2"),
                    "option3": variant.get("option3"),
                    "taxable": variant.get("taxable"),
                    "barcode": variant.get("barcode"),
                    "grams": variant.get("grams"),
                    "requires_shipping": variant.get("requires_shipping"),
                    "sku": variant.get("sku"),
                    "weight": variant.get("weight"),
                    "weight_unit": variant.get("weight_unit"),
                }
                for variant in product.get("variants", [])
            ],
            "options": [
                {
                    "id": option.get("id"),
                    "product_id": option.get("product_id"),
                    "name": option.get("name"),
                    "position": option.get("position"),
                    "values": option.get("values", []),
                }
                for option in product.get("options", [])
            ],
            "image": {
                "id": product.get("image", {}).get("id"),
                "product_id": product.get("image", {}).get("product_id"),
                "width": product.get("image", {}).get("width"),
                "height": product.get("image", {}).get("height"),
                "src": product.get("image", {}).get("src"),
            } if product.get("image") else None,
        }
    }
    
    return transformed_product

# E-commerce functions
def load_products_data():
    """Load product data from JSON file"""
    try:
        with open(PRODUCTS_FILE, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading products data: {e}")
        return {"products": [], "categories": [], "brands": []}

def get_product_by_id(product_id):
    """Fetch a specific product by ID from Shopify API"""
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2025-01/products/{product_id}.json"
    
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_KEY    
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return {"error": f"Shopify API request failed: {response.status_code} - {response.text}", "product_id": product_id}
    
    data = response.json()
    return transform_product_response(data.get("product", {}))

def get_all_products(limit=20, page_info=None):
    """Fetch all product IDs with pagination from Shopify API"""
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2025-01/products.json"
    
    params = {"limit": limit}
    if page_info:
        params["page_info"] = page_info  # Use cursor-based pagination

    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_KEY    
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Shopify API request failed: {response.status_code} - {response.text}")

    data = response.json()
    products = data.get("products", [])
    
    # Extract product IDs
    product_ids = [product["id"] for product in products]

    # Get pagination cursors
    next_page_info = None
    prev_page_info = None
    if "Link" in response.headers:
        links = response.headers["Link"].split(", ")
        for link in links:
            if 'rel="next"' in link and "page_info=" in link:
                next_page_info = link.split("page_info=")[1].split(">")[0]
            elif 'rel="previous"' in link and "page_info=" in link:
                prev_page_info = link.split("page_info=")[1].split(">")[0]
    
    return {
        "product_ids": product_ids,
        "next_page_info": next_page_info,
        "prev_page_info": prev_page_info,
    }

def search_products(query, limit=10):
    """Search products by title using Shopify API and return product IDs"""
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2025-01/products.json"
    
    params = {
        "title": query,
        "limit": limit
    }
    
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_KEY    
    }
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        return {"error": f"Shopify API request failed: {response.status_code} - {response.text}", "query": query}
    
    data = response.json()
    products = data.get("products", [])
    product_ids = [product["id"] for product in products]
    
    return {"product_ids": product_ids}

def filter_products(**filters):
    """Filter products from Shopify API by various criteria and return product IDs"""
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2025-01/products.json"
    
    params = {
        "limit": filters.get("limit", 20),
    }
    
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_KEY    
    }
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        return {"error": f"Shopify API request failed: {response.status_code} - {response.text}"}
    
    data = response.json()
    products = data.get("products", [])
    
    def matches(product):
        return all([
            filters.get("category") is None or product.get("product_type", "").lower() == filters["category"].lower(),
            filters.get("vendor") is None or product.get("vendor", "").lower() == filters["vendor"].lower(),
            filters.get("min_price") is None or float(product.get("variants", [{}])[0].get("price", 0)) >= filters["min_price"],
            filters.get("max_price") is None or float(product.get("variants", [{}])[0].get("price", 0)) <= filters["max_price"],
            filters.get("tags") is None or any(tag.lower() in map(str.lower, product.get("tags", "").split(", ")) for tag in filters["tags"]),
            filters.get("in_stock") is None or any(int(variant.get("inventory_quantity", 0)) > 0 for variant in product.get("variants", []))
        ])
    
    filtered_products = [product["id"] for product in products if matches(product)]
    
    return {"product_ids": filtered_products}

def get_product_recommendations(product_id=None, user_preferences=None, limit=5):
    """Fetch recommended product IDs from Shopify's recommendations API"""
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2025-01/products/{product_id}/recommendations.json"
    
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_KEY    
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return {"error": f"Shopify API request failed: {response.status_code} - {response.text}", "product_id": product_id}
    
    data = response.json()
    recommended_products = data.get("products", [])[:limit]
    recommended_product_ids = [p["id"] for p in recommended_products]
    
    return {"product_ids": recommended_product_ids}

def get_trending_products(limit=5):
    """Fetch trending products from Shopify API based on sales data"""
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2025-01/products.json"
    
    params = {"limit": 50}  # Fetch a larger set of products to determine trending ones
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_KEY    
    }
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        return {"error": f"Shopify API request failed: {response.status_code} - {response.text}"}
    
    data = response.json()
    products = data.get("products", [])
    
    # Sort by some metric of popularity (e.g., sales rank, views, or ratings if available)
    trending_products = sorted(products, key=lambda x: x.get("sales_rank", 0), reverse=True)[:limit]
    
    trending_ids = [p["id"] for p in trending_products]
    return {"product_ids": trending_ids}

def get_deals_of_the_day(limit=5):
    """Fetch products with the highest discounts from Shopify API"""
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2025-01/products.json"
    
    params = {"limit": 250}  # Fetch max products per request
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_KEY    
    }
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        return {"error": f"Shopify API request failed: {response.status_code} - {response.text}"}
    
    data = response.json()
    products = data.get("products", [])
    
    # Sort by discount (assuming discount info is in product variants or metafields)
    deals = sorted(products, key=lambda p: float(p.get("variants", [{}])[0].get("compare_at_price", 0)) - float(p.get("variants", [{}])[0].get("price", 0)), reverse=True)
    
    deals_ids = [p["id"] for p in deals[:limit]]
    
    return {"product_ids": deals_ids}

def get_categories():
    """Fetch all product categories from Shopify API"""
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2025-01/smart_collections.json"
    
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_KEY    
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return {"error": f"Shopify API request failed: {response.status_code} - {response.text}"}
    
    data = response.json()
    categories = [collection["title"] for collection in data.get("smart_collections", [])]
    
    return {"categories": categories}

def get_brands(category=None):

    """Fetch all brands from Shopify, optionally filtered by category"""
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2025-01/smart_collections.json"
    
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_KEY    
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return {"error": f"Shopify API request failed: {response.status_code} - {response.text}"}
    
    data = response.json()
    brands = data.get("smart_collections", [])
    
    if category:
        filtered_brands = [brand for brand in brands if brand.get("handle") == category]
        return {"brands": filtered_brands, "category": category}
    
    return {"brands": brands}

print(get_all_products(20))
print(get_product_by_id(7336674557995))