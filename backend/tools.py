from openai.types.chat import ChatCompletionToolParam

tools = [
    # Weather tool (keeping for backward compatibility)
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_current_weather",
            "description": "Get the current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The temperature unit to use.",
                    },
                },
                "required": ["location"],
            },
        },
    ),
    
    # E-commerce tools
    
    # Search products
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "search_products",
            "description": "Search for products by keywords in name, description, or tags",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'wireless headphones', 'running shoes')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                    },
                },
                "required": ["query"],
            },
        },
    ),
    
    # Filter products
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "filter_products",
            "description": "Filter products by various criteria such as category, price range, rating, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Product category (e.g., 'Electronics', 'Fashion')",
                    },
                    "subcategory": {
                        "type": "string",
                        "description": "Product subcategory (e.g., 'Audio', 'Footwear')",
                    },
                    "brand": {
                        "type": "string",
                        "description": "Brand name",
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Minimum price",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price",
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "Minimum rating (1-5)",
                    },
                    "colors": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of colors to filter by",
                    },
                    "tags": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of tags to filter by (e.g., 'wireless', 'bluetooth')",
                    },
                    "in_stock": {
                        "type": "boolean",
                        "description": "Filter for products in stock",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of results to skip (for pagination)",
                    },
                },
                "required": [],
            },
        },
    ),
    
    # Get product details
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_product_details",
            "description": "Get detailed information about a specific product",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The unique ID of the product",
                    },
                },
                "required": ["product_id"],
            },
        },
    ),
    
    # Get product recommendations
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_product_recommendations",
            "description": "Get product recommendations based on a product ID or user preferences",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Product ID to get similar products",
                    },
                    "user_preferences": {
                        "type": "object",
                        "properties": {
                            "categories": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "List of preferred categories",
                            },
                            "brands": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "List of preferred brands",
                            },
                            "tags": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "List of preferred product tags",
                            },
                        },
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of recommendations to return",
                    },
                },
                "required": [],
            },
        },
    ),
    
    # Get categories
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_categories",
            "description": "Get all product categories and subcategories",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    ),
    
    # Get brands
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_brands",
            "description": "Get all brands, optionally filtered by category",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter brands by category",
                    },
                },
                "required": [],
            },
        },
    ),
    
    # Get trending products
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_trending_products",
            "description": "Get trending products",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of trending products to return",
                    },
                },
                "required": [],
            },
        },
    ),
    
    # Get deals of the day
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_deals_of_the_day",
            "description": "Get deals of the day (products with highest discounts)",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of deals to return",
                    },
                },
                "required": [],
            },
        },
    )
]
