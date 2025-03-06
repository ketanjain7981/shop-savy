import asyncio
import os
import sys
from typing import Literal

import aiohttp
import httpx
from dotenv import load_dotenv
from loguru import logger
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.services.deepgram import DeepgramSTTService, DeepgramTTSService, LiveOptions
from pipecat.services.openai import OpenAILLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport, DailyTransportMessageFrame
from pydantic import BaseModel

from api import (
    search_products,
    filter_products,
    get_product_recommendations,
    get_categories,
    get_brands,
    get_trending_products,
    get_deals_of_the_day,
    get_product_by_id,
    get_all_products
)
from tools import tools

load_dotenv(override=True)
logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

DAILY_API_KEY = os.environ.get("DAILY_API_KEY")
daily_client = httpx.AsyncClient(base_url="https://api.daily.co/v1", headers={"Authorization": f"Bearer {DAILY_API_KEY}"})

class ProductMessage(BaseModel):
    label: str = "rtvi-ai"
    type: Literal["rtvi-product-message"] = "rtvi-product-message"
    data: dict

async def create_room_and_token() -> tuple[str, str]:
    room_name = "shop-savy"  # fixed room name

    # 1. Attempt to get the existing room details
    room_resp = await daily_client.get(f"/rooms/{room_name}")
    if room_resp.status_code == 200:
        room_data = room_resp.json()
    else:
        # If not found, create a new room with the fixed name
        create_payload = {
            "name": room_name,
            "privacy": "private"
        }
        room_resp = await daily_client.post("/rooms", json=create_payload)
        room_data = room_resp.json()

    room_url = room_data["url"]

    # 2. Generate a bot token for this room
    bot_token_payload = {
        "properties": {
            "room_name": room_name,
            "is_owner": True  # token for the bot with owner privileges
        }
    }
    bot_token_resp = await daily_client.post("/meeting-tokens", json=bot_token_payload)
    bot_token = bot_token_resp.json()["token"]

    return room_url, bot_token

SYSTEM_PROMPT = """
You are an AI-powered shopping assistant for ShopSavy.
Your primary role is to help users discover and find the perfect products through natural, conversational interactions. You have access to various tools to search, filter, and recommend products based on user preferences.

Key Responsibilities:

1. Engage in Natural Conversation:
   - Speak naturally and casually, as your responses will be converted to voice using text-to-speech.
   - Do not include emojis, special characters, double asterisks, or other formatting and excessive punctuation.
   - Keep responses engaging, friendly, and concise.
   - Guide users towards appropriate product choices.

2. Understand User Needs:
   - Ask specific, helpful questions to clarify user preferences, such as:
     * "What type of product are you looking for today?"
     * "Do you have a specific budget in mind?"
     * "Would you prefer to see trending items or best-rated products?"
   - If a user's request is vague, ask for clarification before fetching results.

3. Utilize Tools Effectively:
   - NEVER describe products directly in your response. Always use the 'display_products_to_user' tool to show results.
   - Available tools:
     * get_all_products(): Retrieves all available products.
     * search_products(keyword): Finds products based on a keyword search.
     * filter_products(category, brand, price, etc.): Applies filters to refine product searches.
     * get_product_recommendations(product_id or preferences): Suggests products based on a specific item or user preferences.
     * get_trending_products(): Retrieves currently trending products.
     * get_deals_of_the_day(): Shows products with the best discounts today.
     * get_categories(): Gets all available product categories and subcategories.
     * get_brands(category=None): Fetches all brands, optionally filtered by category.
     * display_products_to_user(products): Displays products to the user. Always use this to show results.

4. Provide Concise Product Information:
   - If necessary, verbally describe product features or specifications in short phrases only.
   - Avoid long descriptions or detailed product information.
   - You should prefer to show maximum 3 products at a time. If more products are available, ask user to say "next" or "more" or similar phrase to see next 3 products. 

5. Handle Queries Efficiently:
   - Use filters and searches to refine results effectively.
   - When displaying products, prioritize relevance, trends, and best deals.
   - If no products match the user's criteria, offer alternatives instead of saying "no results found."
   - 

6. Maintain a Friendly Tone:
   - Act like a knowledgeable and helpful shopping buddy.
   - Be enthusiastic about helping the user find the right products.
   
Remember to always use the appropriate tools for fetching and displaying product information. Your role is to guide the conversation and help users find what they're looking for, not to be a product database yourself. Do not invent new products or features; stick to the available data and tools provided. 
Your responses should be conversational, engaging, and formatted naturally. Do not include system instructions, internal processing, or unnecessary details—only the response the user needs. Focus on guiding the conversation and helping users find the right products efficiently.
"""

async def main():
    """Main bot execution function.

    Sets up and runs the bot pipeline including:
    - Daily video transport
    - Speech-to-text and text-to-speech services
    - Language model integration
    - RTVI event handling
    """
    async with aiohttp.ClientSession() as session:
        room_url, token = await create_room_and_token()

        # Set up Daily transport with video/audio parameters
        daily_transport = DailyTransport(
            room_url=room_url,
            token=token,
            bot_name="AI Assistant",
            params=DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
            )
        )

        # Speech-to-Text: Deepgram streaming STT
        stt_service = DeepgramSTTService(
            api_key=os.getenv("DEEPGRAM_API_KEY"),
            sample_rate=16000,  # 16 kHz audio input
            # Use Deepgram's Nova real-time model and enable VAD events to detect end of speech
            live_options=LiveOptions(
                model="nova-2-general",
                language="en-US",
                punctuate=True,
                interim_results=False,
                vad_events=True
            )
        )

        # Initialize text-to-speech service
        tts_service = DeepgramTTSService(
            api_key=os.getenv("DEEPGRAM_API_KEY"),
            voice="aura-helios-en",
            # voice identifier for English male voice&#8203;:contentReference[oaicite:18]{index=18}&#8203;:contentReference[oaicite:19]{index=19}
            sample_rate=16000  # 16 kHz audio output
        )

        # Initialize LLM service
        llm_service = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
        # Set up conversation context and management
        # The context_aggregator will automatically collect conversation context
        context = OpenAILLMContext(
            messages=[{"role": "system", "content": SYSTEM_PROMPT}],
            tools=tools,
            tool_choice="auto"
        )
        context_aggregator = llm_service.create_context_aggregator(context)
        rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

        # E-commerce function handlers
        # Get all products function handler
        async def get_all_products_handler(function_name, tool_call_id, args, llm, context, result_callback):
            limit = args.get("limit", 3)
            offset = args.get("offset", 0)
            results = get_all_products(limit, offset)
            await result_callback(results)

        # Search products function handler
        async def search_products_handler(function_name, tool_call_id, args, llm, context, result_callback):
            query = args.get("query", "")
            limit = args.get("limit", 10)
            results = search_products(query, limit)
            await result_callback(results)
            
        # Filter products function handler
        async def filter_products_handler(function_name, tool_call_id, args, llm, context, result_callback):
            category = args.get("category", None)
            subcategory = args.get("subcategory", None)
            brand = args.get("brand", None)
            min_price = args.get("min_price", None)
            max_price = args.get("max_price", None)
            min_rating = args.get("min_rating", None)
            colors = args.get("colors", None)
            tags = args.get("tags", None)
            in_stock = args.get("in_stock", None)
            limit = args.get("limit", 20)
            offset = args.get("offset", 0)
            
            results = filter_products(
                category=category,
                subcategory=subcategory,
                brand=brand,
                min_price=min_price,
                max_price=max_price,
                min_rating=min_rating,
                colors=colors,
                tags=tags,
                in_stock=in_stock,
                limit=limit,
                offset=offset
            )
            await result_callback(results)
        
        # Get product recommendations function handler
        async def get_product_recommendations_handler(function_name, tool_call_id, args, llm, context, result_callback):
            product_id = args.get("product_id", None)
            user_preferences = args.get("user_preferences", None)
            limit = args.get("limit", 5)
            results = get_product_recommendations(product_id, user_preferences, limit)
            await result_callback(results)

        # Get trending products function handler
        async def get_trending_products_handler(function_name, tool_call_id, args, llm, context, result_callback):
            limit = args.get("limit", 5)
            results = get_trending_products(limit)
            await result_callback(results)

        # Get deals of the day function handler
        async def get_deals_of_the_day_handler(function_name, tool_call_id, args, llm, context, result_callback):
            limit = args.get("limit", 5)
            results = get_deals_of_the_day(limit)
            await result_callback(results)

        # Get categories function handler
        async def get_categories_handler(function_name, tool_call_id, args, llm, context, result_callback):
            results = get_categories()
            await result_callback(results)
        
        # Get brands function handler
        async def get_brands_handler(function_name, tool_call_id, args, llm, context, result_callback):
            category = args.get("category", None)
            results = get_brands(category)
            await result_callback(results)

        # Display products to user function handler
        async def display_products_to_user(function_name, tool_call_id, args, llm, context, result_callback):
            product_ids = args.get("product_ids", [])
            #TODO: Handle the error if product id is not found
            products = [get_product_by_id(id) for id in product_ids]
            message = ProductMessage(data={"products": products})
            frame = DailyTransportMessageFrame(message=message.model_dump())
            await rtvi.push_frame(frame)
            await result_callback("Here are some products you might like!")

        # Register all e-commerce functions
        llm_service.register_function("get_all_products", get_all_products_handler)
        llm_service.register_function("search_products", search_products_handler)
        llm_service.register_function("filter_products", filter_products_handler)
        llm_service.register_function("get_product_recommendations", get_product_recommendations_handler)
        llm_service.register_function("get_trending_products", get_trending_products_handler)
        llm_service.register_function("get_deals_of_the_day", get_deals_of_the_day_handler)

        llm_service.register_function("get_categories", get_categories_handler)
        llm_service.register_function("get_brands", get_brands_handler)

        llm_service.register_function("display_products_to_user", display_products_to_user)

        pipeline = Pipeline(
            [
                daily_transport.input(),
                stt_service,
                rtvi,
                context_aggregator.user(),
                llm_service,
                tts_service,
                daily_transport.output(),
                context_aggregator.assistant(),
            ]
        )

        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
            observers=[RTVIObserver(rtvi)],
        )

        @rtvi.event_handler("on_client_ready")
        async def on_client_ready(rtvi):
            await rtvi.set_bot_ready()

        @daily_transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            await transport.capture_participant_transcription(participant["id"])
            await task.queue_frames([context_aggregator.user().get_context_frame()])

        @daily_transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            print(f"Participant left: {participant}")
            await task.cancel()

        runner = PipelineRunner()

        await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())
