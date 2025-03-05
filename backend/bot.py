import asyncio
import os, httpx
import sqlite3
import sys
import json

import aiohttp
from dotenv import load_dotenv
from loguru import logger
from PIL import Image
from openai.types.chat import ChatCompletionToolParam


from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    Frame,
    OutputImageRawFrame,
    SpriteFrame, TranscriptionFrame, LLMTextFrame,
)
from pipecat.services.deepgram import DeepgramSTTService, DeepgramTTSService, LiveOptions
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.services.openai import OpenAILLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from api import (
    get_current_weather,
    search_products,
    filter_products,
    get_product_details,
    get_product_recommendations,
    get_categories,
    get_brands,
    get_trending_products,
    get_deals_of_the_day
)
from tools import tools

load_dotenv(override=True)
logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

load_dotenv(override=True)
DAILY_API_KEY = os.environ.get("DAILY_API_KEY")
daily_client = httpx.AsyncClient(base_url="https://api.daily.co/v1", headers={"Authorization": f"Bearer {DAILY_API_KEY}"})

DB_PATH = "chat_history.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(role, content):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

# Global pipeline runner to manage our voice processing pipeline
init_db()

class TranscriptionLogger(FrameProcessor):
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TranscriptionFrame):
            logger.info(f"Transcription: {frame.text}")
        if isinstance(frame, LLMTextFrame):
            logger.info(f"LLM: {frame.text}")
        return frame

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

        # Optional start callback - called when function execution begins
        async def start_fetch_weather(function_name, llm, context):
            logger.debug(f"Starting weather fetch: {function_name}")

        # Main function handler - called to execute the function
        async def fetch_weather_from_api(function_name, tool_call_id, args, llm, context, result_callback):
            # Fetch weather data using our API function
            location = args.get("location", "San Francisco, CA")
            format_unit = args.get("format", "celsius")
            weather_data = get_current_weather(location, format_unit)
            await result_callback(weather_data)

        # Register the weather function
        llm_service.register_function(
            "get_current_weather",
            fetch_weather_from_api,
            start_callback=start_fetch_weather
        )
        
        # E-commerce function handlers
        
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
        
        # Get product details function handler
        async def get_product_details_handler(function_name, tool_call_id, args, llm, context, result_callback):
            product_id = args.get("product_id", "")
            results = get_product_details(product_id)
            await result_callback(results)
        
        # Get product recommendations function handler
        async def get_product_recommendations_handler(function_name, tool_call_id, args, llm, context, result_callback):
            product_id = args.get("product_id", None)
            user_preferences = args.get("user_preferences", None)
            limit = args.get("limit", 5)
            results = get_product_recommendations(product_id, user_preferences, limit)
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
            
        # Register all e-commerce functions
        llm_service.register_function("search_products", search_products_handler)
        llm_service.register_function("filter_products", filter_products_handler)
        llm_service.register_function("get_product_details", get_product_details_handler)
        llm_service.register_function("get_product_recommendations", get_product_recommendations_handler)
        llm_service.register_function("get_categories", get_categories_handler)
        llm_service.register_function("get_brands", get_brands_handler)
        llm_service.register_function("get_trending_products", get_trending_products_handler)
        llm_service.register_function("get_deals_of_the_day", get_deals_of_the_day_handler)

        # Set up conversation context and management
        # The context_aggregator will automatically collect conversation context
        context = OpenAILLMContext(
            messages=[{
                "role": "system", 
                "content": "You are ShopSavy, an AI-powered shopping assistant designed to help users find the perfect products. Your goal is to understand user preferences and recommend products that match their needs. You can search, filter, and provide detailed information about products. Be conversational, helpful, and guide users through their shopping journey. When appropriate, suggest related products or alternatives that might interest them."
            }],
            tools=tools,
            tool_choice="auto"
        )
        context_aggregator = llm_service.create_context_aggregator(context)

        logger_service = TranscriptionLogger()
        rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

        pipeline = Pipeline(
            [
                daily_transport.input(),
                stt_service,
                rtvi,
                # logger_service,
                context_aggregator.user(),
                llm_service,
                # logger_service,
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
        
        # No need for the event_handler, we're using register_function instead

        
        runner = PipelineRunner()

        await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())
