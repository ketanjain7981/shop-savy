import json
import os
from pathlib import Path

# Path to the products data file
DATA_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"

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
    """Get a specific product by ID"""
    data = load_products_data()
    products = data.get("products", [])

    for product in products:
        if product.get("id") == product_id:
            return {"product": product}

    return {"error": "Product not found", "product_id": product_id}

def get_all_products(limit=20, offset=0):
    """Get all product IDs with pagination"""
    data = load_products_data()
    products = data.get("products", [])

    paginated_products = products[offset:offset + limit]
    product_ids = [product["id"] for product in paginated_products]

    return {"product_ids": product_ids}

def search_products(query, limit=10):
    """Search products by name, description, or tags and return product IDs"""
    data = load_products_data()
    products = data.get("products", [])
    query = query.lower()

    results = []
    for product in products:
        if (query in product.get("name", "").lower() or
                query in product.get("description", "").lower() or
                any(query in tag.lower() for tag in product.get("tags", []))):
            results.append(product["id"])
            if len(results) >= limit:
                break

    return {"product_ids": results}

def filter_products(**filters):
    """Filter products by various criteria and return product IDs"""
    data = load_products_data()
    products = data.get("products", [])

    def matches(product):
        return all([
            filters.get("category") is None or product.get("category") == filters["category"],
            filters.get("subcategory") is None or product.get("subcategory") == filters["subcategory"],
            filters.get("brand") is None or product.get("brand") == filters["brand"],
            filters.get("min_price") is None or product.get("price", 0) >= filters["min_price"],
            filters.get("max_price") is None or product.get("price", 0) <= filters["max_price"],
            filters.get("min_rating") is None or product.get("rating", 0) >= filters["min_rating"],
            filters.get("colors") is None or any(color in product.get("colors", []) for color in filters["colors"]),
            filters.get("tags") is None or any(tag in product.get("tags", []) for tag in filters["tags"]),
            filters.get("in_stock") is None or product.get("stock", 0) > 0
        ])

    filtered_products = [product["id"] for product in products if matches(product)]
    paginated_product_ids = filtered_products[
                            filters.get("offset", 0):filters.get("offset", 0) + filters.get("limit", 20)]

    return {"product_ids": paginated_product_ids}

def get_product_recommendations(product_id=None, user_preferences=None, limit=5):
    """Get recommended product IDs based on product or user preferences"""
    data = load_products_data()
    products = data.get("products", [])
    recommendations = []

    if product_id:
        source_product = next((p for p in products if p["id"] == product_id), None)
        if source_product:
            recommendations = [p["id"] for p in products if
                               p["id"] != product_id and p["category"] == source_product["category"]][:limit]
    elif user_preferences:
        recommendations = [p["id"] for p in products if p["category"] in user_preferences.get("categories", [])][:limit]
    else:
        recommendations = [p["id"] for p in sorted(products, key=lambda x: x.get("rating", 0), reverse=True)[:limit]]

    return {"product_ids": recommendations}

def get_trending_products(limit=5):
    """Get trending product IDs"""
    data = load_products_data()
    products = data.get("products", [])
    trending_ids = [p["id"] for p in sorted(products, key=lambda x: x.get("rating", 0), reverse=True)[:limit]]
    return {"product_ids": trending_ids}

def get_deals_of_the_day(limit=5):
    """Get product IDs for deals of the day"""
    data = load_products_data()
    products = data.get("products", [])
    deals_ids = [p["id"] for p in sorted(products, key=lambda x: x.get("discountPercentage", 0), reverse=True)[:limit]]
    return {"product_ids": deals_ids}

def get_categories():
    """Get all product categories and subcategories"""
    data = load_products_data()
    return {"categories": data.get("categories", [])}

def get_brands(category=None):
    """Get all brands, optionally filtered by category"""
    data = load_products_data()
    brands = data.get("brands", [])

    if category:
        filtered_brands = [brand for brand in brands if brand.get("category") == category]
        return {"brands": filtered_brands, "category": category}

    return {"brands": brands}
