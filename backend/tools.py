from openai.types.chat import ChatCompletionToolParam

tools = [
    # Get all products
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_all_products",
            "description": "Get all product IDs with pagination",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of products to return",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of products to skip before returning results",
                    },
                },
                "required": [],
            },
        },
    ),
    # Get a specific product by ID
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_product_by_id",
            "description": "Get a specific product by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Unique identifier of the product",
                    },
                },
                "required": ["product_id"],
            },
        },
    ),
    # Search products by name, description, or tags
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "search_products",
            "description": "Search for products by name, description, or tags",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword to match product names, descriptions, or tags",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of products to return",
                    },
                },
                "required": ["query"],
            },
        },
    ),
    # Filter products based on various criteria
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "filter_products",
            "description": "Filter products based on various criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Product category"},
                    "subcategory": {"type": "string", "description": "Product subcategory"},
                    "brand": {"type": "string", "description": "Product brand"},
                    "min_price": {"type": "number", "description": "Minimum product price"},
                    "max_price": {"type": "number", "description": "Maximum product price"},
                    "min_rating": {"type": "number", "description": "Minimum product rating"},
                    "colors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of preferred colors",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of product tags",
                    },
                    "in_stock": {"type": "boolean", "description": "Whether product is in stock"},
                    "limit": {"type": "integer", "description": "Maximum number of products to return"},
                    "offset": {"type": "integer", "description": "Number of products to skip"},
                },
                "required": [],
            },
        },
    ),
    # Get recommended products based on product ID or user preferences
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_product_recommendations",
            "description": "Get recommended products based on product ID or user preferences",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "ID of the product to base recommendations on",
                    },
                    "user_preferences": {
                        "type": "object",
                        "properties": {
                            "categories": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Preferred product categories",
                            },
                            "brands": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Preferred brands",
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Preferred product tags",
                            },
                        },
                        "description": "User preference-based recommendations",
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
            "description": "Get deals of the day based on highest discounts",
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
    ),
    # Get all product categories
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
    # Get all brands, optionally filtered by category
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
                        "description": "Category to filter brands (optional)",
                    },
                },
                "required": [],
            },
        },
    ),
    # Display products to the user in the UI
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "display_products_to_user",
            "description": "Display products to the user in the UI",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_ids": {
                        "type": "array",
                        "items": {
                            "type": "integer",
                        },
                        "description": "List of product IDs to display to the user",
                    },
                },
                "required": ["product_ids"],
            },
        },
    )
]
