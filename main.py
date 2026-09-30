from fastapi import FastAPI
from pydantic import BaseModel
from typing import Literal
from pathlib import Path
import requests
import sys
import re

from commands import execute_command
from local_commands import detect_local_command
from memory import (
    init_db,
    save_message,
    clear_memory
)


# =========================================================
# PATH / ENVIRONMENT
# =========================================================

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent


# =========================================================
# NOVA CLOUD API
# =========================================================

CLOUD_API_URL = "https://nova-cloud-api-i7jv.onrender.com"

# Cloud requests can take several seconds.
CLOUD_TIMEOUT = 90


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Nova AI Assistant API",
    description="An intelligent AI-powered Windows laptop assistant",
    version="1.0.0"
)


# =========================================================
# DATABASE
# =========================================================

init_db()


# =========================================================
# REQUEST MODELS
# =========================================================

class ChatRequest(BaseModel):
    message: str


class SmartCommandRequest(BaseModel):
    message: str


class ConfirmCommandRequest(BaseModel):
    action: Literal[
        "shutdown_computer",
        "restart_computer",
        "lock_computer"
    ]
    query: str = ""


# =========================================================
# LOCAL COMMAND ACTIONS
# =========================================================

DANGEROUS_ACTIONS = {
    "shutdown_computer",
    "restart_computer",
    "lock_computer"
}


ALLOWED_ACTIONS = {
    # Websites
    "open_youtube",
    "search_youtube",
    "open_google",
    "search_google",
    "open_gmail",

    # Applications
    "open_calculator",
    "close_calculator",
    "open_notepad",
    "open_file_explorer",
    "close_file_explorer",
    "open_task_manager",
    "open_command_prompt",
    "open_settings",

    # Folders
    "open_desktop",
    "open_documents",
    "open_downloads",

    # Files
    "create_folder",
    "create_text_file",

    # System
    "get_time",
    "get_date",
    "get_battery",
    "get_ram",
    "get_cpu",
    "get_system_info",

    # Screenshot
    "take_screenshot",

    # Volume
    "volume_up",
    "volume_down",
    "volume_mute",
    "get_volume",

    # Brightness
    "brightness_up",
    "brightness_down",
    "get_brightness",

    # Media
    "play_pause",
    "next_song",
    "previous_song",

    # Computer
    "lock_computer",
    "shutdown_computer",
    "restart_computer",

    # Weather
    "get_weather"
}


# =========================================================
# HELPERS
# =========================================================

def cloud_chat(message: str):
    """
    Send normal conversation directly to Cloud /chat.
    This avoids the unnecessary /smart-command call.
    """

    try:

        response = requests.post(
            f"{CLOUD_API_URL}/chat",
            json={
                "message": message
            },
            timeout=CLOUD_TIMEOUT
        )

    except requests.Timeout:

        return {
            "status": "error",
            "source": "cloud_chat",
            "message": "Nova Cloud is taking too long to respond."
        }

    except requests.RequestException as e:

        return {
            "status": "error",
            "source": "cloud_chat",
            "message": "Nova Cloud API is unavailable.",
            "details": str(e)
        }

    try:

        data = response.json()

    except ValueError:

        return {
            "status": "error",
            "source": "cloud_chat",
            "message": "Nova Cloud returned invalid JSON."
        }

    if response.status_code != 200:

        return {
            "status": "error",
            "source": "cloud_chat",
            "message": "Nova Cloud returned an error.",
            "details": data
        }

    answer = data.get("response", "")

    if answer:

        save_message(
            "user",
            message
        )

        save_message(
            "assistant",
            answer
        )

    return {
        "status": "success",
        "source": "cloud_chat",
        "user_message": message,
        "response": answer
    }


def cloud_smart_command(message: str):
    """
    Send a command-like request to Cloud /smart-command.
    """

    try:

        response = requests.post(
            f"{CLOUD_API_URL}/smart-command",
            json={
                "message": message
            },
            timeout=CLOUD_TIMEOUT
        )

    except requests.Timeout:

        return {
            "status": "error",
            "source": "cloud_api",
            "user_message": message,
            "message": "Nova Cloud is taking too long to respond."
        }

    except requests.RequestException as e:

        return {
            "status": "error",
            "source": "cloud_api",
            "user_message": message,
            "message": "Nova Cloud API is unavailable.",
            "details": str(e)
        }

    try:

        data = response.json()

    except ValueError:

        return {
            "status": "error",
            "source": "cloud_api",
            "user_message": message,
            "message": "Nova Cloud returned invalid JSON."
        }

    if response.status_code != 200:

        return {
            "status": "error",
            "source": "cloud_api",
            "user_message": message,
            "message": "Nova Cloud returned an error.",
            "details": data
        }

    return data


def looks_like_command(text: str) -> bool:
    """
    Decide locally whether a request looks like an action command.

    General conversation such as:
        hello
        how are you?
        explain machine learning

    goes directly to /chat.

    Requests such as:
        open YouTube
        search Google
        weather in Chennai
        take screenshot

    go to /smart-command.
    """

    text = text.lower().strip()

    command_patterns = [

        # Applications
        r"\b(open|close|launch|start)\b.*\b(calculator|notepad|file explorer|task manager|settings)\b",
        r"\bcalculator\b.*\b(please|open|start)\b",

        # Websites
        r"\b(open|launch)\b.*\b(youtube|google|gmail)\b",
        r"\b(search)\b.*\b(google|youtube|web)\b",

        # Files / folders
        r"\b(create|make|open)\b.*\b(folder|file|desktop|documents|downloads)\b",

        # System
        r"\b(battery|ram|cpu|system info|system information)\b",
        r"\b(screenshot|screen shot)\b",

        # Volume / brightness
        r"\b(mute|unmute|increase|decrease|raise|lower)\b.*\b(volume|brightness)\b",

        # Media
        r"\b(play|pause|next|previous)\b.*\b(music|song|track)\b",

        # Computer
        r"\b(lock|restart|shutdown|shut down)\b.*\b(computer|laptop|pc)\b",

        # Weather
        r"\b(weather|temperature|forecast)\b",

        # Explicit commands
        r"^\s*(open|close|launch|start|search|create|make|take|mute|unmute|restart|shutdown|shut down|lock)\b"
    ]

    for pattern in command_patterns:

        if re.search(pattern, text):
            return True

    return False


def execute_local_result(
    message: str,
    action: str,
    query: str
):
    """
    Execute a locally detected action.
    """

    # ---------------------------------------------
    # Dangerous commands
    # ---------------------------------------------

    if action in DANGEROUS_ACTIONS:

        confirmation_messages = {

            "shutdown_computer":
                "Your computer will shut down. "
                "Do you want me to continue?",

            "restart_computer":
                "Your computer will restart. "
                "Do you want me to continue?",

            "lock_computer":
                "Your computer will be locked. "
                "Do you want me to continue?"
        }

        return {
            "status": "confirmation_required",
            "source": "local",
            "user_message": message,
            "action": action,
            "query": query,
            "confirmation_message":
                confirmation_messages[action]
        }

    # ---------------------------------------------
    # Normal local command
    # ---------------------------------------------

    result = execute_command(
        action,
        query
    )

    return {
        "status": "success",
        "source": "local",
        "user_message": message,
        "action": action,
        "query": query,
        "response": result
    }


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "status": "success",
        "message": "Nova AI Assistant API is running!"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "local_api": True,
        "cloud_api": CLOUD_API_URL
    }


# =========================================================
# HELLO
# =========================================================

@app.get("/hello")
def hello():

    return {
        "message": "Hello! I am Nova."
    }


# =========================================================
# DIRECT CHAT
# =========================================================

@app.post("/chat")
def chat(request: ChatRequest):

    return cloud_chat(
        request.message
    )


# =========================================================
# MEMORY RESET
# =========================================================

@app.post("/memory/reset")
def reset_memory():

    clear_memory()

    return {
        "status": "success",
        "message": "Nova's permanent memory has been cleared."
    }


# =========================================================
# DIRECT COMMAND
# =========================================================

@app.post("/command")
def command(request: ChatRequest):

    result = execute_command(
        request.message
    )

    return {
        "status": "success",
        "command": request.message,
        "result": result
    }


# =========================================================
# SMART COMMAND
# =========================================================

@app.post("/smart-command")
def smart_command(request: SmartCommandRequest):

    message = request.message.strip()

    # =====================================================
    # STEP 1: LOCAL COMMAND DETECTION
    # =====================================================

    local_action, local_query = detect_local_command(
        message
    )

    if local_action:

        return execute_local_result(
            message,
            local_action,
            local_query
        )

    # =====================================================
    # STEP 2: FAST CHAT ROUTING
    #
    # Normal conversation goes DIRECTLY to /chat.
    # =====================================================

    if not looks_like_command(message):

        return cloud_chat(
            message
        )

    # =====================================================
    # STEP 3: COMMAND-LIKE REQUEST
    #
    # Send to cloud /smart-command only once.
    # =====================================================

    cloud_data = cloud_smart_command(
        message
    )

    if cloud_data.get("status") == "error":

        return cloud_data

    # =====================================================
    # STEP 4: CLOUD UNKNOWN
    #
    # If command-like request could not be understood,
    # fall back to /chat.
    # =====================================================

    cloud_action = cloud_data.get(
        "action"
    )

    cloud_status = cloud_data.get(
        "status"
    )

    if (
        cloud_status == "unknown"
        or cloud_action is None
        or cloud_action == "unknown"
    ):

        return cloud_chat(
            message
        )

    # =====================================================
    # STEP 5: DANGEROUS CLOUD ACTION
    # =====================================================

    if cloud_status == "confirmation_required":

        return cloud_data

    if cloud_action in DANGEROUS_ACTIONS:

        confirmation_messages = {

            "shutdown_computer":
                "Your computer will shut down. "
                "Do you want me to continue?",

            "restart_computer":
                "Your computer will restart. "
                "Do you want me to continue?",

            "lock_computer":
                "Your computer will be locked. "
                "Do you want me to continue?"
        }

        return {
            "status": "confirmation_required",
            "source": "cloud_ai",
            "user_message": message,
            "action": cloud_action,
            "query": cloud_data.get(
                "query",
                ""
            ),
            "confirmation_message":
                confirmation_messages[cloud_action]
        }

    # =====================================================
    # STEP 6: WEATHER
    # =====================================================

    if cloud_action == "get_weather":

        return cloud_data

    # =====================================================
    # STEP 7: VALIDATE ACTION
    # =====================================================

    if cloud_action not in ALLOWED_ACTIONS:

        return {
            "status": "error",
            "source": "cloud_api",
            "user_message": message,
            "message": "Cloud returned an unsupported action.",
            "action": cloud_action
        }

    # =====================================================
    # STEP 8: EXECUTE CLOUD-IDENTIFIED ACTION LOCALLY
    # =====================================================

    query = cloud_data.get(
        "query",
        ""
    )

    result = execute_command(
        cloud_action,
        query
    )

    return {
        "status": "success",
        "source": "cloud_ai",
        "user_message": message,
        "action": cloud_action,
        "query": query,
        "response": result
    }


# =========================================================
# CONFIRM COMMAND
# =========================================================

@app.post("/confirm-command")
def confirm_command(
    request: ConfirmCommandRequest
):

    allowed_actions = {
        "shutdown_computer",
        "restart_computer",
        "lock_computer"
    }

    if request.action not in allowed_actions:

        return {
            "status": "error",
            "message": "Invalid confirmation action."
        }

    result = execute_command(
        request.action,
        request.query
    )

    return {
        "status": "success",
        "action": request.action,
        "response": result
    }