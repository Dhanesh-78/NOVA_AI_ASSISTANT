from fastapi import FastAPI
from pydantic import BaseModel
from typing import Literal
from pathlib import Path
import requests
import re

from commands import execute_command
from local_commands import detect_local_command
from api_services import get_weather

from memory import (
    init_db,
    save_message,
    clear_memory
)


# ============================================================
# CONFIGURATION
# ============================================================

CLOUD_API_URL = "https://nova-cloud-api-i7jv.onrender.com"
CLOUD_TIMEOUT = 90


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="NOVA AI Assistant",
    version="1.0.0"
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

init_db()


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str


class SmartCommandRequest(BaseModel):
    message: str


class CommandRequest(BaseModel):
    message: str


class ConfirmCommandRequest(BaseModel):
    action: Literal[
        "shutdown_computer",
        "restart_computer",
        "lock_computer"
    ]
    query: str = ""


# ============================================================
# DANGEROUS ACTIONS
# ============================================================

DANGEROUS_ACTIONS = {
    "shutdown_computer",
    "restart_computer",
    "lock_computer"
}


# ============================================================
# ALLOWED ACTIONS
# ============================================================

ALLOWED_ACTIONS = {
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
    "media_play",
    "media_pause",
    "media_next",
    "media_previous",

    # Websites
    "open_youtube",
    "open_google",
    "open_gmail",
    "search_google",
    "search_youtube",

    # Applications
    "open_calculator",
    "close_calculator",
    "open_notepad",
    "open_file_explorer",
    "open_task_manager",
    "open_cmd",
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

    # Computer
    "lock_computer",
    "shutdown_computer",
    "restart_computer",

    # Weather
    "get_weather"
}


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "status": "success",
        "message": "NOVA AI Assistant API is running.",
        "cloud_api": CLOUD_API_URL
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    cloud_status = "unknown"

    try:
        response = requests.get(
            f"{CLOUD_API_URL}/health",
            timeout=15
        )

        if response.ok:
            cloud_status = "online"
        else:
            cloud_status = "offline"

    except Exception:
        cloud_status = "offline"

    return {
        "status": "ok",
        "local_api": "online",
        "cloud_api": CLOUD_API_URL,
        "cloud_status": cloud_status
    }


# ============================================================
# CLOUD CHAT
# ============================================================

def cloud_chat(message: str):

    try:
        response = requests.post(
            f"{CLOUD_API_URL}/chat",
            json={
                "message": message
            },
            timeout=CLOUD_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        return {
            "success": True,
            "data": data
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": "Cloud AI request timed out."
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "error": str(e)
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# CLOUD SMART COMMAND
# ============================================================

def cloud_smart_command(message: str):

    try:

        response = requests.post(
            f"{CLOUD_API_URL}/smart-command",
            json={
                "message": message
            },
            timeout=CLOUD_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        return {
            "success": True,
            "data": data
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": "Cloud smart-command request timed out."
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "error": str(e)
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# COMMAND-LIKE CHECK
# ============================================================

def looks_like_command(text: str):

    text = text.lower().strip()

    patterns = [

        # Volume
        r"\bvolume\b",
        r"\bmute\b",

        # Brightness
        r"\bbrightness\b",
        r"\bbrighter\b",
        r"\bdimmer\b",
        r"\bscreen brighter\b",

        # Media
        r"\bplay\b",
        r"\bpause\b",
        r"\bnext song\b",
        r"\bprevious song\b",

        # Websites
        r"\byoutube\b",
        r"\bgmail\b",
        r"\bgoogle\b",

        # Applications
        r"\bcalculator\b",
        r"\bnotepad\b",
        r"\bfile explorer\b",
        r"\btask manager\b",
        r"\bcommand prompt\b",
        r"\bcmd\b",
        r"\bsettings\b",

        # Folders
        r"\bdesktop\b",
        r"\bdocuments\b",
        r"\bdownloads\b",

        # System
        r"\bbattery\b",
        r"\bcpu\b",
        r"\bram\b",
        r"\bmemory usage\b",
        r"\bsystem information\b",
        r"\bsystem info\b",

        # Time/date
        r"\bwhat time\b",
        r"\bcurrent time\b",
        r"\bwhat date\b",
        r"\btoday's date\b",
        r"\btodays date\b",

        # Screenshot
        r"\bscreenshot\b",
        r"\bscreen shot\b",

        # Weather
        r"\bweather\b",
        r"\btemperature\b",
        r"\bforecast\b",

        # Computer
        r"\bshutdown\b",
        r"\bshut down\b",
        r"\brestart\b",
        r"\breboot\b",
        r"\block my computer\b",
        r"\block the computer\b",

        # Files
        r"\bcreate folder\b",
        r"\bmake folder\b",
        r"\bnew folder\b",
        r"\bcreate text file\b",
        r"\bmake text file\b"
    ]

    for pattern in patterns:

        if re.search(pattern, text):
            return True

    return False


# ============================================================
# WEATHER EXECUTION
# ============================================================

def execute_weather(message: str, query: str):

    try:

        if not query:

            return {
                "status": "error",
                "source": "weather_api",
                "message": "Please specify a city."
            }

        weather = get_weather(query)

        if not weather:

            return {
                "status": "error",
                "source": "weather_api",
                "message": "I couldn't reach the weather service."
            }

        if not weather.get("success"):

            return {
                "status": "error",
                "source": "weather_api",
                "message": weather.get(
                    "error",
                    "I couldn't reach the weather service."
                )
            }

        response = (
            f"Weather in {weather['city']}, "
            f"{weather['country']}: "
            f"{weather['temperature']}°C, "
            f"feels like {weather['feels_like']}°C, "
            f"humidity {weather['humidity']}%, "
            f"{weather['description']}."
        )

        save_message(
            "user",
            message
        )

        save_message(
            "assistant",
            response
        )

        return {
            "status": "success",
            "source": "weather_api",
            "action": "get_weather",
            "query": query,
            "response": response
        }

    except Exception as e:

        print(
            "WEATHER ERROR:",
            repr(e)
        )

        return {
            "status": "error",
            "source": "weather_api",
            "message": "I couldn't reach the weather service.",
            "details": str(e)
        }


# ============================================================
# LOCAL COMMAND EXECUTION
# ============================================================

def execute_local_result(
    message: str,
    action: str,
    query: str
):

    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    if action == "get_weather":

        return execute_weather(
            message,
            query
        )

    # --------------------------------------------------------
    # DANGEROUS ACTION
    # --------------------------------------------------------

    if action in DANGEROUS_ACTIONS:

        return {
            "status": "confirmation_required",
            "source": "local",
            "user_message": message,
            "action": action,
            "query": query,
            "message": (
                f"Please confirm before I execute "
                f"{action.replace('_', ' ')}."
            )
        }

    # --------------------------------------------------------
    # VALIDATE ACTION
    # --------------------------------------------------------

    if action not in ALLOWED_ACTIONS:

        return {
            "status": "error",
            "source": "local",
            "message": f"Unknown action: {action}"
        }

    # --------------------------------------------------------
    # EXECUTE WINDOWS COMMAND
    # --------------------------------------------------------

    try:

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

    except Exception as e:

        print(
            "LOCAL COMMAND ERROR:",
            repr(e)
        )

        return {
            "status": "error",
            "source": "local",
            "user_message": message,
            "action": action,
            "query": query,
            "message": str(e)
        }


# ============================================================
# CHAT ENDPOINT
# ============================================================

@app.post("/chat")
def chat(request: ChatRequest):

    message = request.message.strip()

    if not message:

        return {
            "status": "error",
            "message": "Message cannot be empty."
        }

    result = cloud_chat(message)

    if not result["success"]:

        return {
            "status": "error",
            "source": "cloud_chat",
            "message": result["error"]
        }

    data = result["data"]

    response_text = (
        data.get("response")
        or data.get("message")
        or data.get("text")
        or str(data)
    )

    save_message(
        "user",
        message
    )

    save_message(
        "assistant",
        response_text
    )

    return {
        "status": "success",
        "source": "cloud_chat",
        "user_message": message,
        "response": response_text
    }


# ============================================================
# SMART COMMAND ENDPOINT
# ============================================================

@app.post("/smart-command")
def smart_command(request: SmartCommandRequest):

    message = request.message.strip()

    if not message:

        return {
            "status": "error",
            "message": "Message cannot be empty."
        }

    # --------------------------------------------------------
    # LOCAL DETECTION
    # IMPORTANT:
    # detect_local_command() can return None.
    # Never unpack None directly.
    # --------------------------------------------------------

    local_result = detect_local_command(message)

    if local_result is not None:

        local_action, local_query = local_result

        return execute_local_result(
            message,
            local_action,
            local_query
        )

    # --------------------------------------------------------
    # CLOUD SMART COMMAND
    # --------------------------------------------------------

    result = cloud_smart_command(message)

    if not result["success"]:

        return {
            "status": "error",
            "source": "cloud_smart_command",
            "message": result["error"]
        }

    data = result["data"]

    action = data.get("action")
    query = data.get("query", "")

    is_command = data.get(
        "is_command",
        False
    )

    # --------------------------------------------------------
    # NORMAL QUESTION
    # --------------------------------------------------------

    if not is_command:

        chat_result = cloud_chat(message)

        if not chat_result["success"]:

            return {
                "status": "error",
                "source": "cloud_chat",
                "message": chat_result["error"]
            }

        chat_data = chat_result["data"]

        response_text = (
            chat_data.get("response")
            or chat_data.get("message")
            or chat_data.get("text")
            or str(chat_data)
        )

        save_message(
            "user",
            message
        )

        save_message(
            "assistant",
            response_text
        )

        return {
            "status": "success",
            "source": "cloud_chat",
            "user_message": message,
            "response": response_text
        }

    # --------------------------------------------------------
    # CLOUD WEATHER
    # --------------------------------------------------------

    if action == "get_weather":

        return execute_weather(
            message,
            query
        )

    # --------------------------------------------------------
    # DANGEROUS COMMAND
    # --------------------------------------------------------

    if action in DANGEROUS_ACTIONS:

        return {
            "status": "confirmation_required",
            "source": "cloud",
            "user_message": message,
            "action": action,
            "query": query,
            "message": (
                f"Please confirm before I execute "
                f"{action.replace('_', ' ')}."
            )
        }

    # --------------------------------------------------------
    # VALIDATE CLOUD ACTION
    # --------------------------------------------------------

    if action not in ALLOWED_ACTIONS:

        return {
            "status": "error",
            "source": "cloud",
            "message": f"Unknown action: {action}"
        }

    # --------------------------------------------------------
    # EXECUTE CLOUD-DETECTED LOCAL COMMAND
    # --------------------------------------------------------

    try:

        result = execute_command(
            action,
            query
        )

        return {
            "status": "success",
            "source": "cloud",
            "user_message": message,
            "action": action,
            "query": query,
            "response": result
        }

    except Exception as e:

        print(
            "CLOUD COMMAND EXECUTION ERROR:",
            repr(e)
        )

        return {
            "status": "error",
            "source": "cloud",
            "action": action,
            "query": query,
            "message": str(e)
        }


# ============================================================
# MAIN COMMAND ENDPOINT
# ============================================================

@app.post("/command")
def command(request: CommandRequest):

    message = request.message.strip()

    if not message:

        return {
            "status": "error",
            "message": "Command cannot be empty."
        }

    # ========================================================
    # 1. LOCAL COMMAND DETECTION
    # ========================================================

    local_result = detect_local_command(message)

    # IMPORTANT:
    # local_result may be None.
    # We must check it before unpacking.
    if local_result is not None:

        local_action, local_query = local_result

        return execute_local_result(
            message,
            local_action,
            local_query
        )

    # ========================================================
    # 2. IF NOT COMMAND-LIKE → CLOUD CHAT
    # ========================================================

    if not looks_like_command(message):

        result = cloud_chat(message)

        if not result["success"]:

            return {
                "status": "error",
                "source": "cloud_chat",
                "message": result["error"]
            }

        data = result["data"]

        response_text = (
            data.get("response")
            or data.get("message")
            or data.get("text")
            or str(data)
        )

        save_message(
            "user",
            message
        )

        save_message(
            "assistant",
            response_text
        )

        return {
            "status": "success",
            "source": "cloud_chat",
            "user_message": message,
            "response": response_text
        }

    # ========================================================
    # 3. CLOUD SMART COMMAND
    # ========================================================

    result = cloud_smart_command(message)

    if not result["success"]:

        return {
            "status": "error",
            "source": "cloud_smart_command",
            "message": result["error"]
        }

    data = result["data"]

    action = data.get("action")
    query = data.get("query", "")

    is_command = data.get(
        "is_command",
        False
    )

    # ========================================================
    # 4. CLOUD SAYS IT IS NOT A COMMAND
    # ========================================================

    if not is_command:

        chat_result = cloud_chat(message)

        if not chat_result["success"]:

            return {
                "status": "error",
                "source": "cloud_chat",
                "message": chat_result["error"]
            }

        chat_data = chat_result["data"]

        response_text = (
            chat_data.get("response")
            or chat_data.get("message")
            or chat_data.get("text")
            or str(chat_data)
        )

        save_message(
            "user",
            message
        )

        save_message(
            "assistant",
            response_text
        )

        return {
            "status": "success",
            "source": "cloud_chat",
            "user_message": message,
            "response": response_text
        }

    # ========================================================
    # 5. CLOUD WEATHER
    # ========================================================

    if action == "get_weather":

        return execute_weather(
            message,
            query
        )

    # ========================================================
    # 6. DANGEROUS CLOUD COMMAND
    # ========================================================

    if action in DANGEROUS_ACTIONS:

        return {
            "status": "confirmation_required",
            "source": "cloud",
            "user_message": message,
            "action": action,
            "query": query,
            "message": (
                f"Please confirm before I execute "
                f"{action.replace('_', ' ')}."
            )
        }

    # ========================================================
    # 7. VALIDATE ACTION
    # ========================================================

    if action not in ALLOWED_ACTIONS:

        return {
            "status": "error",
            "source": "cloud",
            "user_message": message,
            "action": action,
            "query": query,
            "message": f"Unknown action: {action}"
        }

    # ========================================================
    # 8. EXECUTE COMMAND LOCALLY
    # ========================================================

    try:

        result = execute_command(
            action,
            query
        )

        return {
            "status": "success",
            "source": "cloud",
            "user_message": message,
            "action": action,
            "query": query,
            "response": result
        }

    except Exception as e:

        print(
            "COMMAND EXECUTION ERROR:",
            repr(e)
        )

        return {
            "status": "error",
            "source": "cloud",
            "user_message": message,
            "action": action,
            "query": query,
            "message": str(e)
        }


# ============================================================
# CONFIRM DANGEROUS COMMAND
# ============================================================

@app.post("/confirm-command")
def confirm_command(
    request: ConfirmCommandRequest
):

    action = request.action
    query = request.query

    if action not in DANGEROUS_ACTIONS:

        return {
            "status": "error",
            "message": "This action does not require confirmation."
        }

    try:

        result = execute_command(
            action,
            query
        )

        return {
            "status": "success",
            "source": "local",
            "action": action,
            "query": query,
            "response": result
        }

    except Exception as e:

        print(
            "CONFIRMED COMMAND ERROR:",
            repr(e)
        )

        return {
            "status": "error",
            "source": "local",
            "action": action,
            "message": str(e)
        }


# ============================================================
# CLEAR MEMORY
# ============================================================

@app.post("/clear-memory")
def clear_memory_endpoint():

    try:

        clear_memory()

        return {
            "status": "success",
            "message": "Conversation memory cleared."
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }