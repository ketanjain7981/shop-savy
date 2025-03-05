import json
import os
from pathlib import Path

# Path to the products data file
DATA_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"

# Weather function (keeping for backward compatibility)
def get_current_weather(location, format="celsius"):
    # In a real application, you would make an API call to a weather service
    # For this example, we'll return mock data
    temperature = 25 if format == "celsius" else 77  # Mock temperature
    return {
        "location": location,
        "temperature": temperature,
        "unit": format,
        "condition": "sunny"
    }

# E-commerce functions
def load_products_data():
    """Load product data from JSON file"""
    try:
        with open(PRODUCTS_FILE, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading products data: {e}")
        return {"products": [], "categories": [], "brands": []}

def get_all_products(limit=20, offset=0):
    """Get all products with pagination"""
    data = load_products_data()
    products = data.get("products", [])
    
    # Apply pagination
    paginated_products = products[offset:offset+limit]
    
    return {
        "products": paginated_products,
        "total": len(products),
        "limit": limit,
        "offset": offset
    }

def get_product_by_id(product_id):
    """Get a specific product by ID"""
    data = load_products_data()
    products = data.get("products", [])
    
    for product in products:
        if product.get("id") == product_id:
            return {"product": product}
    
    return {"error": "Product not found", "product_id": product_id}

def search_products(query, limit=10):
    """Search products by name, description, or tags"""
    data = load_products_data()
    products = data.get("products", [])
    query = query.lower()
    
    results = []
    for product in products:
        # Search in name, description, and tags
        if (query in product.get("name", "").lower() or 
            query in product.get("description", "").lower() or 
            any(query in tag.lower() for tag in product.get("tags", []))):
            results.append(product)
            
            # Limit results
            if len(results) >= limit:
                break
    
    return {
        "results": results,
        "count": len(results),
        "query": query
    }

def filter_products(category=None, subcategory=None, brand=None, min_price=None, 
                   max_price=None, min_rating=None, colors=None, tags=None, 
                   in_stock=None, limit=20, offset=0):
    """Filter products by various criteria"""
    data = load_products_data()
    products = data.get("products", [])
    
    filtered_products = []
    for product in products:
        # Apply filters
        if category and product.get("category") != category:
            continue
        if subcategory and product.get("subcategory") != subcategory:
            continue
        if brand and product.get("brand") != brand:
            continue
        if min_price is not None and product.get("price", 0) < min_price:
            continue
        if max_price is not None and product.get("price", 0) > max_price:
            continue
        if min_rating is not None and product.get("rating", 0) < min_rating:
            continue
        if colors and not any(color in product.get("colors", []) for color in colors):
            continue
        if tags and not any(tag in product.get("tags", []) for tag in tags):
            continue
        if in_stock and product.get("stock", 0) <= 0:
            continue
            
        filtered_products.append(product)
    
    # Apply pagination
    paginated_products = filtered_products[offset:offset+limit]
    
    return {
        "products": paginated_products,
        "total": len(filtered_products),
        "limit": limit,
        "offset": offset,
        "filters": {
            "category": category,
            "subcategory": subcategory,
            "brand": brand,
            "price_range": [min_price, max_price],
            "min_rating": min_rating,
            "colors": colors,
            "tags": tags,
            "in_stock": in_stock
        }
    }

def get_product_recommendations(product_id=None, user_preferences=None, limit=5):
    """Get product recommendations based on a product or user preferences"""
    data = load_products_data()
    products = data.get("products", [])
    
    # If product_id is provided, find similar products
    if product_id:
        source_product = None
        for product in products:
            if product.get("id") == product_id:
                source_product = product
                break
        
        if source_product:
            # Find products in the same category/subcategory or with similar tags
            similar_products = []
            for product in products:
                # Skip the source product
                if product.get("id") == product_id:
                    continue
                    
                # Check if in same category/subcategory
                same_category = product.get("category") == source_product.get("category")
                same_subcategory = product.get("subcategory") == source_product.get("subcategory")
                
                # Check for common tags
                source_tags = set(source_product.get("tags", []))
                product_tags = set(product.get("tags", []))
                common_tags = source_tags.intersection(product_tags)
                
                # Score the similarity
                score = 0
                if same_category:
                    score += 1
                if same_subcategory:
                    score += 2
                score += len(common_tags)
                
                if score > 0:
                    similar_products.append({"product": product, "score": score})
            
            # Sort by similarity score and take top results
            similar_products.sort(key=lambda x: x["score"], reverse=True)
            recommendations = [item["product"] for item in similar_products[:limit]]
            
            return {
                "recommendations": recommendations,
                "source_product_id": product_id,
                "count": len(recommendations)
            }
    
    # If user_preferences provided, use those to find matching products
    elif user_preferences:
        preferred_categories = user_preferences.get("categories", [])
        preferred_brands = user_preferences.get("brands", [])
        preferred_tags = user_preferences.get("tags", [])
        
        scored_products = []
        for product in products:
            score = 0
            
            # Score based on preferences
            if product.get("category") in preferred_categories:
                score += 2
            if product.get("brand") in preferred_brands:
                score += 2
            
            # Score based on tags
            product_tags = set(product.get("tags", []))
            for tag in preferred_tags:
                if tag in product_tags:
                    score += 1
            
            if score > 0:
                scored_products.append({"product": product, "score": score})
        
        # Sort by score and take top results
        scored_products.sort(key=lambda x: x["score"], reverse=True)
        recommendations = [item["product"] for item in scored_products[:limit]]
        
        return {
            "recommendations": recommendations,
            "based_on_preferences": True,
            "count": len(recommendations)
        }
    
    # If no specific criteria, return top-rated products
    else:
        # Sort by rating and return top products
        top_products = sorted(products, key=lambda x: x.get("rating", 0), reverse=True)[:limit]
        
        return {
            "recommendations": top_products,
            "based_on": "top_rated",
            "count": len(top_products)
        }

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

def get_product_details(product_id):
    """Get detailed information about a specific product"""
    product_data = get_product_by_id(product_id)
    
    if "error" in product_data:
        return product_data
    
    product = product_data["product"]
    
    # Get recommendations for this product
    recommendations = get_product_recommendations(product_id=product_id, limit=3)
    
    # Calculate discounted price if applicable
    original_price = product.get("price", 0)
    discount_percentage = product.get("discountPercentage", 0)
    discounted_price = original_price * (1 - discount_percentage/100) if discount_percentage > 0 else None
    
    # Enhance the product details
    detailed_product = product.copy()
    detailed_product["discounted_price"] = discounted_price
    detailed_product["savings"] = original_price - discounted_price if discounted_price else 0
    detailed_product["in_stock"] = product.get("stock", 0) > 0
    detailed_product["recommendations"] = recommendations.get("recommendations", [])
    
    return {"product": detailed_product}

def get_trending_products(limit=5):
    """Get trending products (mock implementation)"""
    data = load_products_data()
    products = data.get("products", [])
    
    # In a real system, this would use actual trending data
    # For mock purposes, we'll just return some products with high ratings
    trending = sorted(products, key=lambda x: (x.get("rating", 0), x.get("stock", 0)), reverse=True)[:limit]
    
    return {"trending_products": trending, "count": len(trending)}

def get_deals_of_the_day(limit=5):
    """Get deals of the day (products with highest discounts)"""
    data = load_products_data()
    products = data.get("products", [])
    
    # Sort by discount percentage and return top discounted products
    deals = sorted(products, key=lambda x: x.get("discountPercentage", 0), reverse=True)[:limit]
    
    return {"deals": deals, "count": len(deals)}
