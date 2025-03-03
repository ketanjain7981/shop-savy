import os
import sqlite3
from dotenv import load_dotenv
from fastapi import FastAPI

# Load environment variables from .env file
load_dotenv()
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.transports.services.daily import DailyTransport, DailyParams
from pipecat.services.deepgram import DeepgramSTTService, DeepgramTTSService
from pipecat.services.openai import OpenAILLMService

app = FastAPI()

# Path for the SQLite database file
DB_PATH = "data/chatbot.db"

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
runner = PipelineRunner()

@app.on_event("startup")
async def startup_event():
    init_db()

    # Daily transport: joins the specified Daily room.
    daily_room = os.environ.get("DAILY_ROOM_URL")
    transport = DailyTransport(
        room_url=daily_room,
        token=None,  # Use token here if your room is secured
        bot_name="AI Bot",
        params=DailyParams(audio_out_enabled=True)
    )

    # Deepgram STT service to convert incoming audio to text.
    stt = DeepgramSTTService(
        api_key=os.environ.get("DEEPGRAM_API_KEY")
        # Additional configuration (e.g., VAD) can be added here.
    )

    # OpenAI LLM service to generate responses.
    llm = OpenAILLMService(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model="gpt-3.5-turbo"
    )

    # Deepgram TTS service to synthesize text to speech.
    tts = DeepgramTTSService(
        api_key=os.environ.get("DEEPGRAM_API_KEY"),
        voice="en-US-Standard-B",  # Choose a preferred voice
        sample_rate=24000
    )

    # Optional: Log messages to SQLite via a custom processor.
    # Using Pipecat's TranscriptionFrame and LLMTextFrame types.
    from pipecat.processors.frame_processor import FrameProcessor
    from pipecat.frames.frames import TranscriptionFrame, LLMTextFrame

    class MessageLogger(FrameProcessor):
        def process(self, frame):
            # Log final transcriptions (user input)
            if isinstance(frame, TranscriptionFrame) and frame.is_final:
                save_to_db("user", frame.text)
            # Log LLM responses (assistant output)
            if isinstance(frame, LLMTextFrame):
                save_to_db("assistant", frame.text)
            return frame

    logger_processor = MessageLogger()

    # Assemble the Pipecat pipeline.
    pipeline = Pipeline([
        transport.input(),   # Audio coming in from Daily
        stt,                 # Convert speech-to-text
        logger_processor,    # Log user transcript
        llm,                 # Generate AI response
        logger_processor,    # Log assistant response
        tts,                 # Convert text-to-speech
        transport.output()   # Send audio back via Daily
    ])

    # Create a pipeline task and run it
    from pipecat.pipeline.task import PipelineTask
    task = PipelineTask(pipeline)
    await runner.run(task)

@app.get("/health")
def read_health():
    return {"status": "ok"}

@app.get("/chatlogs")
def get_chatlogs():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT role, content, timestamp FROM messages ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [{"role": role, "content": content, "timestamp": timestamp} for (role, content, timestamp) in rows]
