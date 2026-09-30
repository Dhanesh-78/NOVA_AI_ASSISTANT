from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import os
import time
import json


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="NOVA AI Cloud API",
    description="Cloud AI backend for NOVA AI Assistant",
    version="1.0.0"
)


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("WARNING: GEMINI_API_KEY is not configured.")

client = (
    genai.Client(api_key=api_key)
    if api_key
    else None
)

MODEL_NAME = "gemini-3.5-flash-lite"


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str


class SmartCommandRequest(BaseModel):
    message: str


# ============================================================
# GEMINI RETRY FUNCTION
# ============================================================

def generate_with_retry(
    prompt: str,
    max_retries: int = 3
):

    if client is None:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    for attempt in range(max_retries):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            return response

        except Exception as e:

            error_text = str(e)

            temporary_error = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            )

            if not temporary_error:

                raise

            if attempt == max_retries - 1:

                raise

            delay = 2 ** attempt

            print(
                f"Gemini temporarily unavailable. "
                f"Retrying in {delay} seconds..."
            )

            time.sleep(delay)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "status": "online",
        "service": "NOVA AI Cloud API",
        "version": "1.0.0",
        "model": MODEL_NAME
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "gemini_configured": client is not None,
        "model": MODEL_NAME
    }


# ============================================================
# CHAT
# ============================================================

@app.post("/chat")
def chat(request: ChatRequest):

    message = request.message.strip()

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    try:

        response = generate_with_retry(
            message
        )

        text = response.text.strip()

        return {
            "success": True,
            "response": text
        }

    except Exception as e:

        print("Gemini chat error:", e)

        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable."
        )


# ============================================================
# SMART COMMAND
# ============================================================

@app.post("/smart-command")
def smart_command(
    request: SmartCommandRequest
):

    message = request.message.strip()

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    prompt = f"""
You are NOVA, a Windows AI assistant.

Your task is to determine whether the user's message
is a computer command.

USER MESSAGE:
"{message}"

If it is a command, return ONLY valid JSON:

{{
    "is_command": true,
    "action": "ACTION_NAME",
    "query": "QUERY"
}}

If it is NOT a computer command, return ONLY:

{{
    "is_command": false,
    "action": "",
    "query": ""
}}

Allowed action names include:

volume_up
volume_down
volume_mute
get_volume

brightness_up
brightness_down
get_brightness

open_youtube
open_google
open_gmail
search_google
search_youtube

open_calculator
close_calculator
open_notepad
open_file_explorer
open_task_manager
open_command_prompt
open_settings

open_desktop
open_documents
open_downloads

create_folder
create_text_file

get_time
get_date
get_battery
get_ram
get_cpu
get_system_info

take_screenshot

play_pause
next_song
previous_song

lock_computer
shutdown_computer
restart_computer

Examples:

"make the volume louder"

{{
    "is_command": true,
    "action": "volume_up",
    "query": ""
}}

"turn the volume down"

{{
    "is_command": true,
    "action": "volume_down",
    "query": ""
}}

"open youtube"

{{
    "is_command": true,
    "action": "open_youtube",
    "query": ""
}}

"search google for Python tutorials"

{{
    "is_command": true,
    "action": "search_google",
    "query": "Python tutorials"
}}

"create a folder called Research"

{{
    "is_command": true,
    "action": "create_folder",
    "query": "Research"
}}

"what is machine learning?"

{{
    "is_command": false,
    "action": "",
    "query": ""
}}

Return ONLY JSON.
Do not use markdown.
Do not add explanations.
"""

    try:

        response = generate_with_retry(
            prompt
        )

        raw_text = response.text.strip()

        # ----------------------------------------------------
        # Remove accidental markdown fences
        # ----------------------------------------------------

        if raw_text.startswith("```"):

            raw_text = raw_text.replace(
                "```json",
                ""
            ).replace(
                "```",
                ""
            ).strip()

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        result = json.loads(
            raw_text
        )

        return {
            "success": True,
            "is_command": result.get(
                "is_command",
                False
            ),
            "action": result.get(
                "action",
                ""
            ),
            "query": result.get(
                "query",
                ""
            )
        }

    except json.JSONDecodeError as e:

        print(
            "Smart command JSON error:",
            e
        )

        raise HTTPException(
            status_code=502,
            detail="AI returned an invalid command format."
        )

    except Exception as e:

        print(
            "Smart command error:",
            e
        )

        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable."
        )