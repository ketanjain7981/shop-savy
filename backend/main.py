import argparse
import os, httpx
import subprocess
from contextlib import asynccontextmanager
from typing import Any, Dict

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse


# Load environment variables from .env file
load_dotenv(override=True)
DAILY_API_KEY = os.environ.get("DAILY_API_KEY")
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Maximum number of bot instances allowed per room
MAX_BOTS_PER_ROOM = 1

# Dictionary to track bot processes: {pid: (process, room_url)}
bot_procs = {}

daily_client = httpx.AsyncClient(base_url="https://api.daily.co/v1", headers={"Authorization": f"Bearer {DAILY_API_KEY}"})

def cleanup():
    """Cleanup function to terminate all bot processes.

    Called during server shutdown.
    """
    for entry in bot_procs.values():
        proc = entry[0]
        proc.terminate()
        proc.wait()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager that handles startup and shutdown tasks.

    - Creates aiohttp session
    - Initializes Daily API helper
    - Cleans up resources on shutdown
    """
    aiohttp_session = aiohttp.ClientSession()
    yield
    await aiohttp_session.close()
    cleanup()


# Initialize FastAPI app with lifespan manager
app = FastAPI(lifespan=lifespan)

# Configure CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    # 2. Generate a user token for this room
    user_token_payload = {
        "properties": {
            "room_name": room_name,
            "is_owner": False  # token for the user
        }
    }
    user_token_resp = await daily_client.post("/meeting-tokens", json=user_token_payload)
    user_token = user_token_resp.json()["token"]

    return room_url, user_token


@app.post("/connect")
async def rtvi_connect(request: Request) -> Dict[Any, Any]:
    print("Creating room for RTVI connection")
    room_url, token = await create_room_and_token()
    print(f"Room URL: {room_url}")

    # Start the bot process
    try:
        proc = subprocess.Popen(
            [f"python3 -m bot -u {room_url} -t {token}"],
            shell=True,
            bufsize=1,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        bot_procs[proc.pid] = (proc, room_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start subprocess: {e}")

    # Return the authentication bundle in format expected by DailyTransport
    return {"room_url": room_url, "token": token}


@app.get("/status/{pid}")
def get_status(pid: int):
    # Look up the subprocess
    proc = bot_procs.get(pid)

    # If the subprocess doesn't exist, return an error
    if not proc:
        raise HTTPException(status_code=404, detail=f"Bot with process id: {pid} not found")

    # Check the status of the subprocess
    status = "running" if proc[0].poll() is None else "finished"
    return JSONResponse({"bot_id": pid, "status": status})


if __name__ == "__main__":
    import uvicorn

    # Parse command line arguments for server configuration
    default_host = os.getenv("HOST", "0.0.0.0")
    default_port = int(os.getenv("FAST_API_PORT", "7860"))

    parser = argparse.ArgumentParser(description="Daily Storyteller FastAPI server")
    parser.add_argument("--host", type=str, default=default_host, help="Host address")
    parser.add_argument("--port", type=int, default=default_port, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Reload code on change")

    config = parser.parse_args()

    # Start the FastAPI server
    uvicorn.run(
        "server:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
    )
