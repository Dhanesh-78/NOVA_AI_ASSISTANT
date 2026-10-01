from fastapi import FastAPI
from pydantic import BaseModel
from typing import Literal
from pathlib import Path

import requests
import sys
import re

from commands import execute_command
from local_commands import detect_local_command
from api_services import get_weather

from memory import (
    init_db,
    save_message,
    get_recent_messages,
    get_memories,
    save_memory,
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
# MEMORY DETECTION
# =========================================================

def is_memory_request(message: str) -> bool:
    """
    Detect whether the user is asking Nova to remember
    something or explicitly providing personal information.

    Examples that SHOULD trigger memory:

        remember that I like Python
        can you remember my favourite language is Tamil
        my favourite language is Tamil
        I like Python
        I prefer Python

    Examples that SHOULD NOT trigger memory:

        my favourite language
        what is my favourite language
        how are you
    """

    text = message.lower().strip()

    if not text:
        return False

    # ---------------------------------------------
    # Explicit memory requests
    # ---------------------------------------------

    direct_memory_phrases = [
        "remember that",
        "remember this",
        "can you remember",
        "please remember",
        "save this",
        "save that",
        "keep this in mind",
        "don't forget",
        "do not forget"
    ]

    if any(phrase in text for phrase in direct_memory_phrases):
        return True

    # ---------------------------------------------
    # Personal information statements
    # ---------------------------------------------

    personal_memory_patterns = [
        "my favourite language is",
        "my favorite language is",
        "my favourite languages are",
        "my favorite languages are",
        "my favourite programming language is",
        "my favorite programming language is",
        "i like",
        "i love",
        "i prefer",
        "my preferred",
        "my name is"
    ]

    if any(pattern in text for pattern in personal_memory_patterns):
        return True

    return False


# =========================================================
# MEMORY TEXT CLEANUP
# =========================================================

def clean_memory_text(message: str) -> str:
    """
    Convert a memory request into a clean statement that can
    be stored permanently.
    """

    text = message.strip()

    prefixes = [
        "remember that ",
        "remember this: ",
        "remember this ",
        "can you remember that ",
        "can you remember ",
        "please remember that ",
        "please remember ",
        "save this: ",
        "save this ",
        "save that ",
        "keep this in mind: ",
        "keep this in mind "
    ]

    lower_text = text.lower()

    for prefix in prefixes:
        if lower_text.startswith(prefix):
            return text[len(prefix):].strip()

    return text


# =========================================================
# MEMORY RESPONSE
# =========================================================

def handle_memory_request(message: str):

    memory_text = clean_memory_text(message)

    if not memory_text:
        return {
            "status": "success",
            "source": "memory",
            "response": (
                "Sure. What would you like me to remember?"
            )
        }

    saved = save_memory(
        memory_text,
        category="user_preference"
    )

    if saved:
        return {
            "status": "success",
            "source": "memory",
            "response": (
                f"Got it! I'll remember that: {memory_text}"
            )
        }

    return {
        "status": "success",
        "source": "memory",
        "response": (
            "I already have that in my memory."
        )
    }


# =========================================================
# WEATHER RESPONSE FORMATTER
# =========================================================

def format_weather_result(weather_result, location: str):
    """
    Convert different possible return formats from
    api_services.get_weather() into a GUI-friendly string.
    """

    if weather_result is None:
        return "I couldn't get the weather information right now."

    # Already a string
    if isinstance(weather_result, str):
        return weather_result

    # Dictionary returned by weather service
    if isinstance(weather_result, dict):

        # If API itself returned a message
        if weather_result.get("message"):
            return str(weather_result["message"])

        # Common possible weather keys
        temperature = weather_result.get(
            "temperature",
            weather_result.get("temp")
        )

        feels_like = weather_result.get(
            "feels_like",
            weather_result.get("feels_like_temperature")
        )

        humidity = weather_result.get("humidity")

        wind_speed = weather_result.get(
            "wind_speed",
            weather_result.get("windspeed")
        )

        description = weather_result.get(
            "description",
            weather_result.get(
                "weather",
                weather_result.get("condition")
            )
        )

        city = weather_result.get(
            "location",
            weather_result.get(
                "city",
                location
            )
        )

        parts = []

        if city:
            parts.append(f"Weather in {city}")

        if temperature is not None:
            parts.append(f"Temperature: {temperature}°C")

        if feels_like is not None:
            parts.append(f"Feels like: {feels_like}°C")

        if description:
            parts.append(f"Condition: {description}")

        if humidity is not None:
            parts.append(f"Humidity: {humidity}%")

        if wind_speed is not None:
            parts.append(f"Wind: {wind_speed}")

        if len(parts) > 1:
            return ". ".join(parts) + "."

        # Last-resort dictionary response
        return str(weather_result)

    return str(weather_result)


# =========================================================
# WEATHER DETECTION
# =========================================================

def extract_weather_location(message: str):
    """
    Extract location from natural weather requests.

    Examples:

        weather in Chennai
        weather in Nerul
        weather in Nerul Navi Mumbai
        what is the weather in Mumbai
        tell me weather for Delhi
    """

    text = message.strip()

    patterns = [
        r"\bweather\s+in\s+(.+)$",
        r"\bweather\s+at\s+(.+)$",
        r"\bweather\s+for\s+(.+)$",
        r"\btemperature\s+in\s+(.+)$",
        r"\btemperature\s+at\s+(.+)$",
        r"\bforecast\s+in\s+(.+)$",
        r"\bforecast\s+for\s+(.+)$",
        r"\bwhat\s+is\s+the\s+weather\s+in\s+(.+)$",
        r"\bwhat\s+is\s+the\s+weather\s+at\s+(.+)$",
        r"\bwhat\s+is\s+the\s+weather\s+for\s+(.+)$",
        r"\btell\s+me\s+the\s+weather\s+in\s+(.+)$",
        r"\btell\s+me\s+weather\s+in\s+(.+)$"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            location = match.group(1).strip()

            # Remove common trailing conversational words
            location = re.sub(
                r"\s+(please|now|today)\s*$",
                "",
                location,
                flags=re.IGNORECASE
            )

            return location.strip()

    return ""


def is_weather_request(message: str) -> bool:

    text = message.lower().strip()

    weather_words = [
        "weather",
        "temperature",
        "forecast"
    ]

    return any(
        word in text
        for word in weather_words
    )


# =========================================================
# WEATHER HANDLER
# =========================================================

def handle_weather(message: str):

    location = extract_weather_location(message)

    if not location:

        return {
            "status": "success",
            "source": "local",
            "action": "get_weather",
            "response": (
                "Sure! Which city or area would you like "
                "the weather for?"
            )
        }

    try:

        weather_result = get_weather(location)

        formatted_result = format_weather_result(
            weather_result,
            location
        )

        return {
            "status": "success",
            "source": "local",
            "action": "get_weather",
            "query": location,
            "user_message": message,
            "response": formatted_result
        }

    except Exception as e:

        return {
            "status": "error",
            "source": "local",
            "action": "get_weather",
            "user_message": message,
            "message": (
                "I couldn't get the weather right now."
            ),
            "details": str(e)
        }


# =========================================================
# CLOUD CHAT
# =========================================================

def cloud_chat(message: str):
    """
    Send normal conversation directly to Cloud /chat.
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
            "message": (
                "Nova Cloud is taking too long to respond."
            )
        }

    except requests.RequestException as e:

        return {
            "status": "error",
            "source": "cloud_chat",
            "message": (
                "Nova Cloud API is unavailable."
            ),
            "details": str(e)
        }

    try:

        data = response.json()

    except ValueError:

        return {
            "status": "error",
            "source": "cloud_chat",
            "message": (
                "Nova Cloud returned invalid JSON."
            )
        }

    if response.status_code != 200:

        return {
            "status": "error",
            "source": "cloud_chat",
            "message": (
                "Nova Cloud returned an error."
            ),
            "details": data
        }

    answer = data.get(
        "response",
        data.get("message", "")
    )

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


# =========================================================
# CLOUD SMART COMMAND
# =========================================================

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
            "message": (
                "Nova Cloud is taking too long to respond."
            )
        }

    except requests.RequestException as e:

        return {
            "status": "error",
            "source": "cloud_api",
            "user_message": message,
            "message": (
                "Nova Cloud API is unavailable."
            ),
            "details": str(e)
        }

    try:

        data = response.json()

    except ValueError:

        return {
            "status": "error",
            "source": "cloud_api",
            "user_message": message,
            "message": (
                "Nova Cloud returned invalid JSON."
            )
        }

    if response.status_code != 200:

        return {
            "status": "error",
            "source": "cloud_api",
            "user_message": message,
            "message": (
                "Nova Cloud returned an error."
            ),
            "details": data
        }

    return data


# =========================================================
# COMMAND DETECTION
# =========================================================

def looks_like_command(text: str) -> bool:
    """
    Decide locally whether a request looks like an action command.

    General conversation:
        hello
        how are you?
        explain machine learning

    goes directly to /chat.

    Action requests:
        open YouTube
        search Google
        weather in Chennai
        take screenshot

    go through smart command routing.
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

        if re.search(
            pattern,
            text
        ):
            return True

    return False


# =========================================================
# LOCAL COMMAND EXECUTION
# =========================================================

def execute_local_result(
    message: str,
    action: str,
    query: str
):
    """
    Execute a locally detected action.
    """

    # ---------------------------------------------
    # Unknown action protection
    # ---------------------------------------------

    if not action or action == "unknown":

        return {
            "status": "unknown",
            "source": "local",
            "user_message": message,
            "message": (
                "I don't know how to perform that action yet."
            )
        }

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

        return {
            "status": "error",
            "source": "local",
            "user_message": message,
            "action": action,
            "query": query,
            "message": (
                "I couldn't execute that command."
            ),
            "details": str(e)
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

    message = request.message.strip()

    if not message:

        return {
            "status": "error",
            "source": "local",
            "message": "Please provide a message."
        }

    # Memory request
    if is_memory_request(message):

        return handle_memory_request(message)

    return cloud_chat(
        message
    )


# =========================================================
# MEMORY RESET
# =========================================================

@app.post("/memory/reset")
def reset_memory():

    clear_memory()

    return {
        "status": "success",
        "message": (
            "Nova's permanent memory has been cleared."
        )
    }


# =========================================================
# DIRECT COMMAND
# =========================================================

@app.post("/command")
def command(request: ChatRequest):

    message = request.message.strip()

    if not message:

        return {
            "status": "error",
            "message": "Please provide a command."
        }

    result = execute_command(
        message
    )

    return {
        "status": "success",
        "command": message,
        "result": result
    }


# =========================================================
# SMART COMMAND
# =========================================================

@app.post("/smart-command")
def smart_command(
    request: SmartCommandRequest
):

    # IMPORTANT:
    # Define message BEFORE using it anywhere.
    message = request.message.strip()

    if not message:

        return {
            "status": "error",
            "source": "local",
            "message": "Please provide a command or message."
        }

    # =====================================================
    # STEP 1: MEMORY
    # =====================================================

    if is_memory_request(message):

        return handle_memory_request(
            message
        )

    # =====================================================
    # STEP 2: WEATHER
    # =====================================================

    # Handle weather locally BEFORE local command detection.
    #
    # This prevents:
    #
    # weather in Nerul
    #
    # from falling through to unknown/cloud routing.

    if is_weather_request(message):

        return handle_weather(
            message
        )

    # =====================================================
    # STEP 3: LOCAL COMMAND DETECTION
    # =====================================================

    local_action, local_query = detect_local_command(
        message
    )

    # IMPORTANT:
    #
    # detect_local_command() can return:
    #
    # ("unknown", "")
    #
    # "unknown" is truthy in Python, so we MUST explicitly
    # reject it.

    if (
        local_action
        and local_action != "unknown"
    ):

        return execute_local_result(
            message,
            local_action,
            local_query
        )

    # =====================================================
    # STEP 4: FAST CHAT ROUTING
    # =====================================================

    # Normal conversation goes directly to /chat.

    if not looks_like_command(message):

        return cloud_chat(
            message
        )

    # =====================================================
    # STEP 5: COMMAND-LIKE REQUEST
    # =====================================================

    # Send command-like request to cloud /smart-command.

    cloud_data = cloud_smart_command(
        message
    )

    if not isinstance(
        cloud_data,
        dict
    ):

        return {
            "status": "error",
            "source": "cloud_api",
            "user_message": message,
            "message": (
                "Nova Cloud returned an invalid response."
            )
        }

    # =====================================================
    # STEP 6: CLOUD ERROR
    # =====================================================

    if cloud_data.get(
        "status"
    ) == "error":

        return cloud_data

    # =====================================================
    # STEP 7: CLOUD UNKNOWN
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

        # If it isn't actually a command, let Gemini
        # answer it as normal conversation.

        return cloud_chat(
            message
        )

    # =====================================================
    # STEP 8: CLOUD CONFIRMATION
    # =====================================================

    if cloud_status == "confirmation_required":

        return cloud_data

    # =====================================================
    # STEP 9: DANGEROUS CLOUD ACTION
    # =====================================================

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
    # STEP 10: WEATHER FROM CLOUD
    # =====================================================

    if cloud_action == "get_weather":

        return cloud_data

    # =====================================================
    # STEP 11: VALIDATE ACTION
    # =====================================================

    if cloud_action not in ALLOWED_ACTIONS:

        return {
            "status": "error",
            "source": "cloud_api",
            "user_message": message,
            "message": (
                "Cloud returned an unsupported action."
            ),
            "action": cloud_action
        }

    # =====================================================
    # STEP 12: EXECUTE CLOUD-IDENTIFIED ACTION LOCALLY
    # =====================================================

    query = cloud_data.get(
        "query",
        ""
    )

    return execute_local_result(
        message,
        cloud_action,
        query
    )


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
            "message": (
                "Invalid confirmation action."
            )
        }

    try:

        result = execute_command(
            request.action,
            request.query
        )

        return {
            "status": "success",
            "action": request.action,
            "response": result
        }

    except Exception as e:

        return {
            "status": "error",
            "action": request.action,
            "message": (
                "Could not execute confirmed command."
            ),
            "details": str(e)
        }