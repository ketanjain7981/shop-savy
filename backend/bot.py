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
from api import get_current_weather
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
            print(f"User Transcript: {frame.text}")
            save_to_db("user", frame.text)
        elif isinstance(frame, LLMTextFrame):
            print(f"LLM Response: {frame.text}")
            save_to_db("assistant", frame.text)
        await self.push_frame(frame, direction)

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

        # Register the function
        llm_service.register_function(
            "get_current_weather",
            fetch_weather_from_api,
            start_callback=start_fetch_weather
        )

        # Set up conversation context and management
        # The context_aggregator will automatically collect conversation context
        context = OpenAILLMContext(
            messages=[{"role": "system", "content": "You are Chatbot, a friendly, helpful robot"}],
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
