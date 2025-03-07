from openai.types.chat import ChatCompletionToolParam

tools = [
    # Get all products
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_all_products",
            "description": "Get all product IDs with pagination from Shopify API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of products to return (default: 20, max: 250).",
                    },
                    "page_info": {
                        "type": "string",
                        "description": "Cursor for pagination (use next_page_info from the previous response). Leave empty for the first request.",
                    },
                },
                "required": ["limit"],
            },
        },
    ),
    # Get a specific product by ID
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_product_by_id",
            "description": "Fetch a specific product by ID from Shopify API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "Unique identifier of the product.",
                    },
                },
                "required": ["product_id"],
            },
        },
    ),
    # Search products by title
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "search_products",
            "description": "Search for products by title using Shopify API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword to match product titles.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of products to return (default: 10).",
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
            "description": "Filter products from Shopify API by various criteria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Product category."},
                    "vendor": {"type": "string", "description": "Product vendor/brand."},
                    "min_price": {"type": "number", "description": "Minimum product price."},
                    "max_price": {"type": "number", "description": "Maximum product price."},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of product tags.",
                    },
                    "in_stock": {"type": "boolean", "description": "Filter by stock availability."},
                    "limit": {"type": "integer", "description": "Maximum number of products to return."},
                },
                "required": [],
            },
        },
    ),
    # Get product recommendations
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_product_recommendations",
            "description": "Fetch recommended product IDs from Shopify's recommendations API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "ID of the product to base recommendations on.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of recommendations to return (default: 5).",
                    },
                },
                "required": ["product_id"],
            },
        },
    ),
    # Get trending products
    ChatCompletionToolParam(
        type="function",
        function={
            "name": "get_trending_products",
            "description": "Fetch trending products from Shopify API based on sales data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of trending products to return (default: 5).",
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
            "description": "Fetch products with the highest discounts from Shopify API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of deals to return (default: 5).",
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
            "description": "Fetch all product categories from Shopify API.",
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
            "description": "Fetch all brands from Shopify API, optionally filtered by category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category to filter brands (optional).",
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
