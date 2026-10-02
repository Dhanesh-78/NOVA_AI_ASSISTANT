import tkinter as tk
import threading
import uvicorn
from tkinter import messagebox
import threading
import queue
import requests
import speech_recognition as sr
import pyttsx3
import psutil
import re
import time

def start_local_api():
    """
    Start NOVA's FastAPI server in the background.

    COM is initialized here because several Windows-specific
    NOVA components use COM and the API is running in a
    separate thread.
    """
    try:
        import comtypes

        # Initialize COM for this background thread
        comtypes.CoInitialize()

        print("NOVA: COM initialized")
        
        # Import main only AFTER COM initialization
        import main

        print("NOVA: FastAPI module loaded")
        print("NOVA: Starting local API...")

        uvicorn.run(
            main.app,
            host="127.0.0.1",
            port=8000,
            log_level="warning",
            reload=False,
            workers=1
        )

    except Exception as e:
        print("NOVA API error:", repr(e))

    finally:
        try:
            import comtypes
            comtypes.CoUninitialize()
        except Exception:
            pass
                  
# Optional Windows volume support
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    PYCAW_AVAILABLE = True
except Exception:
    PYCAW_AVAILABLE = False


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "http://127.0.0.1:8000"

SMART_COMMAND_URL = f"{BASE_URL}/smart-command"
CHAT_URL = f"{BASE_URL}/chat"
CONFIRM_URL = f"{BASE_URL}/confirm-command"
HEALTH_URL = f"{BASE_URL}/health"

REQUEST_TIMEOUT = 60


# ============================================================
# GLOBAL STATE
# ============================================================

# TTS queue
tts_queue = queue.Queue()

# This event is TRUE while NOVA is speaking.
# The microphone uses this to prevent NOVA hearing itself.
nova_is_speaking = threading.Event()

# Prevent multiple microphone threads at once
microphone_busy = threading.Event()

# Prevent duplicate command processing
command_busy = threading.Event()

# Current pending dangerous command
pending_confirmation = None

# Application running state
app_running = True


# ============================================================
# COLORS
# ============================================================

BG = "#080B12"
CARD = "#111722"
CARD_2 = "#151C29"
INPUT_BG = "#1A2230"

WHITE = "#F5F7FA"
SECONDARY = "#9CA8B8"
MUTED = "#6E7B8F"

BLUE = "#4DA3FF"
CYAN = "#55E6FF"
GREEN = "#48D597"
RED = "#FF5C70"
YELLOW = "#FFC857"

BORDER = "#273244"


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title("NOVA AI Assistant")
root.geometry("900x700")
root.minsize(720, 620)
root.configure(bg=BG)


# ============================================================
# SAFE UI HELPERS
# ============================================================

def ui_call(function, *args, **kwargs):
    """
    Safely execute Tkinter UI code from any thread.
    """
    if not app_running:
        return

    try:
        root.after(
            0,
            lambda: function(*args, **kwargs)
        )
    except Exception:
        pass


def set_status(text, status_type="ready"):
    """
    Update status label safely.
    """

    def update():
        status_label.config(text=text)

        if status_type == "listening":
            status_label.config(fg=CYAN)

        elif status_type == "processing":
            status_label.config(fg=YELLOW)

        elif status_type == "error":
            status_label.config(fg=RED)

        elif status_type == "speaking":
            status_label.config(fg=GREEN)

        else:
            status_label.config(fg=SECONDARY)

    ui_call(update)


# ============================================================
# TTS
# ============================================================

def tts_worker():

    try:
        tts_engine = pyttsx3.init("sapi5")

        tts_engine.setProperty(
            "rate",
            175
        )

        tts_engine.setProperty(
            "volume",
            1.0
        )

        print("NOVA TTS: Ready")

    except Exception as e:

        print(
            "NOVA TTS initialization error:",
            e
        )

        return

    while True:

        try:
            text = tts_queue.get()

            if text is None:

                tts_queue.task_done()

                break

            try:

                nova_is_speaking.set()

                ui_call(
                    set_status,
                    "NOVA is speaking...",
                    "speaking"
                )

                print(
                    "NOVA SPEAKING:",
                    text
                )

                tts_engine.say(
                    str(text)
                )

                tts_engine.runAndWait()

            except Exception as e:

                print(
                    "NOVA TTS error:",
                    e
                )

            finally:

                nova_is_speaking.clear()

                ui_call(
                    set_status,
                    "Ready",
                    "ready"
                )

                tts_queue.task_done()

        except Exception as e:

            print(
                "TTS worker error:",
                e
            )


tts_thread = threading.Thread(
    target=tts_worker,
    daemon=True
)

tts_thread.start()


def speak(text):

    if not text:
        return

    text = str(text).strip()

    if not text:
        return

    tts_queue.put(text)


# ============================================================
# CHAT DISPLAY
# ============================================================

def add_message(sender, message):

    if not message:
        return

    message = str(message).strip()

    if not message:
        return

    def update_chat():

        try:

            chat_box.config(
                state=tk.NORMAL
            )

            if sender == "YOU":

                chat_box.insert(
                    tk.END,
                    "\nYOU\n",
                    "user_header"
                )

                chat_box.insert(
                    tk.END,
                    message + "\n",
                    "user_message"
                )

            else:

                chat_box.insert(
                    tk.END,
                    "\nNOVA\n",
                    "nova_header"
                )

                chat_box.insert(
                    tk.END,
                    message + "\n",
                    "nova_message"
                )

            chat_box.config(
                state=tk.DISABLED
            )

            chat_box.see(tk.END)

        except Exception as e:

            print(
                "Chat display error:",
                e
            )

    ui_call(update_chat)


# ============================================================
# HTTP HELPER
# ============================================================

def post_json(url, payload, timeout=REQUEST_TIMEOUT):

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=timeout
        )

        print(
            f"POST {url} -> {response.status_code}"
        )

        try:
            data = response.json()

        except ValueError:

            print(
                "Server returned invalid JSON."
            )

            return {
                "status": "error",
                "message": "Server returned invalid JSON.",
                "http_status": response.status_code
            }

        if response.status_code >= 400:

            return {
                "status": "error",
                "message": data.get(
                    "message",
                    "Server returned an error."
                ),
                "http_status": response.status_code,
                "details": data
            }

        return data

    except requests.exceptions.Timeout:

        return {
            "status": "error",
            "message": "The server took too long to respond."
        }

    except requests.exceptions.ConnectionError:

        return {
            "status": "error",
            "message": "Cannot connect to NOVA local API. Make sure main.py is running."
        }

    except Exception as e:

        print(
            "HTTP error:",
            e
        )

        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# LOCAL COMMAND DETECTION
# ============================================================

def looks_like_local_command(text):

    if not text:
        return False

    text = text.lower().strip()

    patterns = [

        # Volume
        r"\b(volume|sound|audio)\b",

        # Brightness
        r"\b(brightness|screen brightness)\b",

        # Media
        r"\b(play|pause|resume|next song|previous song|skip song|media)\b",

        # Apps
        r"\b(open|launch|start)\b.*\b(chrome|edge|notepad|calculator|explorer|task manager|settings|cmd)\b",

        # Websites
        r"\b(open|go to|visit)\b.*\b(youtube|google|github|instagram|facebook|gmail|whatsapp)\b",

        # Files
        r"\b(create|make|open|delete)\b.*\b(file|folder|directory)\b",

        # System
        r"\b(cpu|ram|memory usage|battery|system information|system info)\b",

        # Screenshot
        r"\b(screenshot|screen shot|capture screen)\b",

        # Computer
        r"\b(shutdown|restart|reboot|lock computer|lock pc)\b",

        # Time/date
        r"\b(what time|current time|today's date|what date)\b",

        # Weather
        r"\b(weather|temperature|forecast)\b",

    ]

    for pattern in patterns:

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):
            return True

    return False


# ============================================================
# PROCESS SERVER RESULT
# ============================================================

def process_result(result, original_text=""):

    global pending_confirmation

    if not result:

        add_message(
            "NOVA",
            "Sorry, I couldn't understand that."
        )

        speak(
            "Sorry, I couldn't understand that."
        )

        return

    print(
        "SERVER RESULT:",
        result
    )

    status = result.get(
        "status",
        ""
    )

    message = result.get(
        "message",
        ""
    )

    # --------------------------------------------------------
    # ERROR
    # --------------------------------------------------------

    if status == "error":

        if not message:
            message = "Something went wrong."

        add_message(
            "NOVA",
            message
        )

        speak(message)

        set_status(
            "Ready",
            "ready"
        )

        return

    # --------------------------------------------------------
    # CONFIRMATION REQUIRED
    # --------------------------------------------------------

    if (
        status == "confirmation_required"
        or result.get("requires_confirmation")
        or result.get("confirmation_required")
    ):

        action = result.get(
            "action"
        )

        query = result.get(
            "query",
            original_text
        )

        pending_confirmation = {
            "action": action,
            "query": query
        }

        confirmation_text = message

        if not confirmation_text:

            confirmation_text = (
                f"Are you sure you want to "
                f"{action.replace('_', ' ')}?"
            )

        add_message(
            "NOVA",
            confirmation_text
        )

        speak(
            confirmation_text
        )

        ui_call(
            show_confirmation_dialog,
            confirmation_text,
            action,
            query
        )

        return

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    if status == "success":

        if not message:

            message = (
                result.get(
                    "response"
                )
                or result.get(
                    "result"
                )
                or "Done."
            )

        add_message(
            "NOVA",
            message
        )

        speak(message)

        set_status(
            "Ready",
            "ready"
        )

        return

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    if status == "unknown":

        message = result.get(
            "message",
            "I don't know how to perform that action yet."
        )

        add_message(
            "NOVA",
            message
        )

        speak(message)

        return

    # --------------------------------------------------------
    # NORMAL RESPONSE
    # --------------------------------------------------------

    response_text = (
        result.get("response")
        or result.get("answer")
        or result.get("message")
        or result.get("text")
    )

    if response_text:

        add_message(
            "NOVA",
            response_text
        )

        speak(response_text)

        return

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    fallback = "Sorry, I couldn't understand that."

    add_message(
        "NOVA",
        fallback
    )

    speak(fallback)


# ============================================================
# SEND SMART COMMAND
# ============================================================

def send_smart_command(text):

    if not text:
        return

    text = str(text).strip()

    if not text:
        return

    # Prevent microphone feedback
    if nova_is_speaking.is_set():

        print(
            "NOVA is speaking - command ignored."
        )

        return

    if command_busy.is_set():

        print(
            "A command is already being processed."
        )

        return

    command_busy.set()

    try:

        set_status(
            "Thinking...",
            "processing"
        )

        result = post_json(
            SMART_COMMAND_URL,
            {
                "message": text
            },
            timeout=REQUEST_TIMEOUT
        )

        process_result(
            result,
            text
        )

    finally:

        command_busy.clear()

        if not nova_is_speaking.is_set():

            set_status(
                "Ready",
                "ready"
            )


# ============================================================
# SEND TEXT COMMAND
# ============================================================

def send_text_command(text):

    if nova_is_speaking.is_set():

        print(
            "NOVA is speaking - command ignored."
        )

        return

    if not text:

        return

    text = str(text).strip()

    if not text:

        return

    # Display user's message
    add_message(
        "YOU",
        text
    )

    # Clear input field
    ui_call(
        input_entry.delete,
        0,
        tk.END
    )

    # Process in background
    worker = threading.Thread(
        target=send_smart_command,
        args=(text,),
        daemon=True
    )

    worker.start()


# ============================================================
# SEND BUTTON
# ============================================================

def send_button_clicked():

    if nova_is_speaking.is_set():

        return

    text = input_entry.get().strip()

    if not text:

        return

    send_text_command(text)


# ============================================================
# ENTER KEY
# ============================================================

def enter_pressed(event):

    send_button_clicked()

    return "break"


# ============================================================
# MICROPHONE
# ============================================================

def listen_microphone():

    # --------------------------------------------------------
    # DO NOT LISTEN WHILE NOVA IS SPEAKING
    # --------------------------------------------------------

    if nova_is_speaking.is_set():

        print(
            "NOVA is speaking - microphone ignored."
        )

        return

    # --------------------------------------------------------
    # PREVENT MULTIPLE MIC THREADS
    # --------------------------------------------------------

    if microphone_busy.is_set():

        print(
            "Microphone is already active."
        )

        return

    microphone_busy.set()

    try:

        set_status(
            "Listening...",
            "listening"
        )

        recognizer = sr.Recognizer()

        recognizer.pause_threshold = 0.8
        recognizer.non_speaking_duration = 0.5

        with sr.Microphone() as source:

            print(
                "NOVA: Listening..."
            )

            # Give microphone time to understand room noise
            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )

            # IMPORTANT
            # If NOVA started speaking during calibration,
            # cancel the microphone.
            if nova_is_speaking.is_set():

                print(
                    "NOVA started speaking - microphone cancelled."
                )

                return

            try:

                audio = recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=10
                )

            except sr.WaitTimeoutError:

                print(
                    "NOVA: Listening timed out."
                )

                set_status(
                    "Ready",
                    "ready"
                )

                return

        # ----------------------------------------------------
        # AFTER RECORDING
        # ----------------------------------------------------

        if nova_is_speaking.is_set():

            print(
                "NOVA is speaking - ignoring microphone result."
            )

            return

        set_status(
            "Understanding...",
            "processing"
        )

        try:

            text = recognizer.recognize_google(
                audio
            )

        except sr.UnknownValueError:

            print(
                "NOVA: Could not understand speech."
            )

            # VERY IMPORTANT:
            # Do NOT speak an error here.
            #
            # Otherwise:
            #
            # NOVA speaks error
            # -> microphone hears NOVA
            # -> recognition fails
            # -> NOVA speaks error again
            #
            # No loop.

            set_status(
                "Ready",
                "ready"
            )

            return

        except sr.RequestError as e:

            print(
                "Speech recognition service error:",
                e
            )

            set_status(
                "Speech service unavailable",
                "error"
            )

            return

        if not text:

            set_status(
                "Ready",
                "ready"
            )

            return

        print(
            "YOU:",
            text
        )

        # Send recognized command
        send_text_command(text)

    except Exception as e:

        print(
            "Microphone error:",
            e
        )

        set_status(
            "Microphone error",
            "error"
        )

    finally:

        microphone_busy.clear()


# ============================================================
# MICROPHONE BUTTON
# ============================================================

def microphone_clicked():

    if nova_is_speaking.is_set():

        print(
            "NOVA is speaking - please wait."
        )

        return

    if microphone_busy.is_set():

        return

    worker = threading.Thread(
        target=listen_microphone,
        daemon=True
    )

    worker.start()


# ============================================================
# CONFIRMATION DIALOG
# ============================================================

def show_confirmation_dialog(
    confirmation_text,
    action,
    query
):

    global pending_confirmation

    dialog = tk.Toplevel(root)

    dialog.title(
        "NOVA Confirmation"
    )

    dialog.geometry(
        "430x230"
    )

    dialog.resizable(
        False,
        False
    )

    dialog.configure(
        bg=CARD
    )

    dialog.transient(
        root
    )

    dialog.grab_set()

    title = tk.Label(
        dialog,
        text="⚠ Confirmation Required",
        font=("Segoe UI", 16, "bold"),
        bg=CARD,
        fg=YELLOW
    )

    title.pack(
        pady=(25, 10)
    )

    text_label = tk.Label(
        dialog,
        text=confirmation_text,
        font=("Segoe UI", 11),
        bg=CARD,
        fg=WHITE,
        wraplength=370,
        justify="center"
    )

    text_label.pack(
        padx=25,
        pady=10
    )

    button_frame = tk.Frame(
        dialog,
        bg=CARD
    )

    button_frame.pack(
        pady=15
    )

    def confirm():

        dialog.destroy()

        worker = threading.Thread(
            target=confirm_action,
            args=(action, query),
            daemon=True
        )

        worker.start()

    def cancel():

        global pending_confirmation

        pending_confirmation = None

        dialog.destroy()

        add_message(
            "NOVA",
            "Action cancelled."
        )

        speak(
            "Action cancelled."
        )

    yes_button = tk.Button(
        button_frame,
        text="YES",
        command=confirm,
        font=("Segoe UI", 10, "bold"),
        bg=GREEN,
        fg="#08120D",
        activebackground=GREEN,
        activeforeground="#08120D",
        relief="flat",
        padx=25,
        pady=8,
        cursor="hand2"
    )

    yes_button.pack(
        side=tk.LEFT,
        padx=8
    )

    no_button = tk.Button(
        button_frame,
        text="CANCEL",
        command=cancel,
        font=("Segoe UI", 10, "bold"),
        bg=RED,
        fg=WHITE,
        activebackground=RED,
        activeforeground=WHITE,
        relief="flat",
        padx=20,
        pady=8,
        cursor="hand2"
    )

    no_button.pack(
        side=tk.LEFT,
        padx=8
    )


# ============================================================
# CONFIRM ACTION
# ============================================================

def confirm_action(action, query):

    global pending_confirmation

    set_status(
        "Executing...",
        "processing"
    )

    result = post_json(
        CONFIRM_URL,
        {
            "action": action,
            "query": query
        },
        timeout=60
    )

    pending_confirmation = None

    process_result(
        result,
        query
    )


# ============================================================
# VOLUME
# ============================================================

def get_system_volume():

    if not PYCAW_AVAILABLE:
        return None

    try:
        devices = AudioUtilities.GetSpeakers()

        # Newer pycaw versions expose EndpointVolume
        if hasattr(devices, "EndpointVolume"):
            volume = devices.EndpointVolume

            scalar = volume.GetMasterVolumeLevelScalar()

            return round(scalar * 100)

        # Older pycaw versions use Activate()
        if hasattr(devices, "Activate"):

            interface = devices.Activate(
                IAudioEndpointVolume._iid_,
                CLSCTX_ALL,
                None
            )

            volume = interface.QueryInterface(
                IAudioEndpointVolume
            )

            scalar = volume.GetMasterVolumeLevelScalar()

            return round(scalar * 100)

        print(
            "Volume API format not supported by this pycaw version."
        )

        return None

    except Exception as e:

        print(
            "Volume error:",
            e
        )

        return None

# ============================================================
# DASHBOARD UPDATE
# ============================================================

def update_dashboard():

    try:

        cpu = psutil.cpu_percent(
            interval=None
        )

        ram = psutil.virtual_memory().percent

        battery = psutil.sensors_battery()

        if battery:

            battery_value = (
                f"{battery.percent:.0f}%"
            )

        else:

            battery_value = "N/A"

        volume = get_system_volume()

        if volume is None:

            volume_value = "N/A"

        else:

            volume_value = f"{volume}%"

        cpu_value_label.config(
            text=f"{cpu:.0f}%"
        )

        ram_value_label.config(
            text=f"{ram:.0f}%"
        )

        battery_value_label.config(
            text=battery_value
        )

        volume_value_label.config(
            text=volume_value
        )

    except Exception as e:

        print(
            "Dashboard error:",
            e
        )

    if app_running:

        root.after(
            2000,
            update_dashboard
        )


# ============================================================
# API STATUS
# ============================================================

def check_api_status():

    try:

        response = requests.get(
            HEALTH_URL,
            timeout=5
        )

        if response.status_code == 200:

            api_status_label.config(
                text="● API ONLINE",
                fg=GREEN
            )

        else:

            api_status_label.config(
                text="● API ERROR",
                fg=RED
            )

    except Exception:

        api_status_label.config(
            text="● API OFFLINE",
            fg=RED
        )

    if app_running:

        root.after(
            5000,
            check_api_status
        )


# ============================================================
# CLEAR CHAT DISPLAY
# ============================================================

def clear_chat_display():

    answer = messagebox.askyesno(
        "Clear Chat",
        "Clear the chat shown in NOVA?"
    )

    if not answer:

        return

    chat_box.config(
        state=tk.NORMAL
    )

    chat_box.delete(
        "1.0",
        tk.END
    )

    chat_box.config(
        state=tk.DISABLED
    )

    add_message(
        "NOVA",
        "Chat cleared. Your saved memory is still available."
    )


# ============================================================
# WINDOW CLOSE
# ============================================================

def close_application():

    global app_running

    app_running = False

    try:

        tts_queue.put(
            None
        )

    except Exception:
        pass

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    close_application
)


# ============================================================
# HEADER
# ============================================================

header_frame = tk.Frame(
    root,
    bg=BG
)

header_frame.grid(
    row=0,
    column=0,
    sticky="ew",
    padx=25,
    pady=(18, 8)
)

header_frame.columnconfigure(
    1,
    weight=1
)


nova_title = tk.Label(
    header_frame,
    text="NOVA",
    font=(
        "Segoe UI",
        25,
        "bold"
    ),
    bg=BG,
    fg=CYAN
)

nova_title.grid(
    row=0,
    column=0,
    sticky="w"
)


subtitle = tk.Label(
    header_frame,
    text="AI DESKTOP ASSISTANT",
    font=(
        "Segoe UI",
        9,
        "bold"
    ),
    bg=BG,
    fg=MUTED
)

subtitle.grid(
    row=1,
    column=0,
    sticky="w"
)


status_label = tk.Label(
    header_frame,
    text="Ready",
    font=(
        "Segoe UI",
        10
    ),
    bg=BG,
    fg=SECONDARY
)

status_label.grid(
    row=0,
    column=1,
    rowspan=2,
    sticky="e"
)


# ============================================================
# NOVA ORB
# ============================================================

orb_frame = tk.Frame(
    root,
    bg=BG,
    height=95
)

orb_frame.grid(
    row=1,
    column=0,
    sticky="ew"
)

orb_frame.grid_propagate(
    False
)


orb_canvas = tk.Canvas(
    orb_frame,
    width=90,
    height=90,
    bg=BG,
    highlightthickness=0
)

orb_canvas.pack(
    pady=2
)


orb_canvas.create_oval(
    12,
    12,
    78,
    78,
    fill="#111C2D",
    outline=CYAN,
    width=2
)

orb_canvas.create_oval(
    24,
    24,
    66,
    66,
    fill="#172B45",
    outline=BLUE,
    width=2
)

orb_canvas.create_oval(
    37,
    37,
    53,
    53,
    fill=CYAN,
    outline=""
)


# ============================================================
# DASHBOARD
# ============================================================

dashboard_frame = tk.Frame(
    root,
    bg=BG
)

dashboard_frame.grid(
    row=2,
    column=0,
    sticky="ew",
    padx=25,
    pady=(2, 10)
)

for i in range(4):

    dashboard_frame.columnconfigure(
        i,
        weight=1
    )


def create_dashboard_card(
    parent,
    column,
    title
):

    frame = tk.Frame(
        parent,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    frame.grid(
        row=0,
        column=column,
        sticky="ew",
        padx=4
    )

    title_label = tk.Label(
        frame,
        text=title,
        font=(
            "Segoe UI",
            8,
            "bold"
        ),
        bg=CARD,
        fg=MUTED
    )

    title_label.pack(
        pady=(8, 1)
    )

    value_label = tk.Label(
        frame,
        text="--",
        font=(
            "Segoe UI",
            14,
            "bold"
        ),
        bg=CARD,
        fg=WHITE
    )

    value_label.pack(
        pady=(0, 8)
    )

    return value_label


cpu_value_label = create_dashboard_card(
    dashboard_frame,
    0,
    "CPU"
)

ram_value_label = create_dashboard_card(
    dashboard_frame,
    1,
    "RAM"
)

battery_value_label = create_dashboard_card(
    dashboard_frame,
    2,
    "BATTERY"
)

volume_value_label = create_dashboard_card(
    dashboard_frame,
    3,
    "VOLUME"
)


# ============================================================
# CHAT AREA
# ============================================================

chat_outer_frame = tk.Frame(
    root,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)

chat_outer_frame.grid(
    row=3,
    column=0,
    sticky="nsew",
    padx=25,
    pady=(0, 10)
)


chat_outer_frame.rowconfigure(
    0,
    weight=1
)

chat_outer_frame.columnconfigure(
    0,
    weight=1
)


chat_box = tk.Text(
    chat_outer_frame,
    bg=CARD,
    fg=WHITE,
    font=(
        "Segoe UI",
        10
    ),
    wrap=tk.WORD,
    relief=tk.FLAT,
    borderwidth=0,
    padx=18,
    pady=12,
    spacing1=2,
    spacing3=4,
    insertbackground=WHITE,
    selectbackground="#29405D",
    state=tk.DISABLED
)

chat_box.grid(
    row=0,
    column=0,
    sticky="nsew"
)


# ============================================================
# CHAT SCROLLBAR
# ============================================================

chat_scrollbar = tk.Scrollbar(
    chat_outer_frame,
    orient=tk.VERTICAL,
    command=chat_box.yview,
    bg=CARD_2,
    troughcolor=CARD,
    activebackground=BLUE,
    relief=tk.FLAT,
    width=12
)

chat_scrollbar.grid(
    row=0,
    column=1,
    sticky="ns"
)


chat_box.config(
    yscrollcommand=chat_scrollbar.set
)


# ============================================================
# CHAT TEXT TAGS
# ============================================================

chat_box.tag_configure(
    "user_header",
    foreground=BLUE,
    font=(
        "Segoe UI",
        9,
        "bold"
    )
)

chat_box.tag_configure(
    "user_message",
    foreground=WHITE,
    font=(
        "Segoe UI",
        10
    )
)

chat_box.tag_configure(
    "nova_header",
    foreground=CYAN,
    font=(
        "Segoe UI",
        9,
        "bold"
    )
)

chat_box.tag_configure(
    "nova_message",
    foreground="#D9E2F0",
    font=(
        "Segoe UI",
        10
    )
)


# ============================================================
# INPUT AREA
# ============================================================

input_frame = tk.Frame(
    root,
    bg=BG
)

input_frame.grid(
    row=4,
    column=0,
    sticky="ew",
    padx=25,
    pady=(0, 10)
)

input_frame.columnconfigure(
    0,
    weight=1
)


input_entry = tk.Entry(
    input_frame,
    bg=INPUT_BG,
    fg=WHITE,
    insertbackground=WHITE,
    font=(
        "Segoe UI",
        11
    ),
    relief=tk.FLAT,
    bd=0
)

input_entry.grid(
    row=0,
    column=0,
    sticky="ew",
    ipady=12,
    padx=(0, 8)
)


# ============================================================
# SEND BUTTON
# ============================================================

send_button = tk.Button(
    input_frame,
    text="SEND",
    command=send_button_clicked,
    font=(
        "Segoe UI",
        9,
        "bold"
    ),
    bg=BLUE,
    fg="white",
    activebackground=BLUE,
    activeforeground="white",
    relief=tk.FLAT,
    bd=0,
    padx=20,
    pady=9,
    cursor="hand2"
)

send_button.grid(
    row=0,
    column=1,
    padx=(0, 8)
)


# ============================================================
# MICROPHONE BUTTON
# ============================================================

mic_button = tk.Button(
    input_frame,
    text="🎙 TALK",
    command=microphone_clicked,
    font=(
        "Segoe UI",
        9,
        "bold"
    ),
    bg=CARD_2,
    fg=CYAN,
    activebackground="#20304A",
    activeforeground=CYAN,
    relief=tk.FLAT,
    bd=0,
    padx=18,
    pady=9,
    cursor="hand2"
)

mic_button.grid(
    row=0,
    column=2
)


# ============================================================
# BOTTOM STATUS
# ============================================================

bottom_frame = tk.Frame(
    root,
    bg=BG
)

bottom_frame.grid(
    row=5,
    column=0,
    sticky="ew",
    padx=25,
    pady=(0, 14)
)

bottom_frame.columnconfigure(
    0,
    weight=1
)


api_status_label = tk.Label(
    bottom_frame,
    text="● API CHECKING...",
    font=(
        "Segoe UI",
        8,
        "bold"
    ),
    bg=BG,
    fg=MUTED
)

api_status_label.grid(
    row=0,
    column=0,
    sticky="w"
)


clear_button = tk.Button(
    bottom_frame,
    text="CLEAR CHAT",
    command=clear_chat_display,
    font=(
        "Segoe UI",
        8,
        "bold"
    ),
    bg=BG,
    fg=MUTED,
    activebackground=BG,
    activeforeground=WHITE,
    relief=tk.FLAT,
    bd=0,
    cursor="hand2"
)

clear_button.grid(
    row=0,
    column=1,
    sticky="e"
)


# ============================================================
# GRID CONFIGURATION
# ============================================================

root.grid_columnconfigure(
    0,
    weight=1
)

root.grid_rowconfigure(
    3,
    weight=1
)


# ============================================================
# KEYBOARD BINDINGS
# ============================================================

input_entry.bind(
    "<Return>",
    enter_pressed
)


# ============================================================
# WELCOME MESSAGE
# ============================================================

add_message(
    "NOVA",
    "Hello! I'm Nova. You can type or speak to me."
)


# ============================================================
# START MONITORS
# ============================================================

root.after(
    500,
    update_dashboard
)

root.after(
    500,
    check_api_status
)


# ============================================================
# INITIAL FOCUS
# ============================================================

input_entry.focus_set()


# ============================================================
# START APPLICATION
# ============================================================

print(
    "======================================"
)

print(
    "       NOVA AI ASSISTANT STARTED"
)

print(
    "======================================"
)

print(
    "Local API:",
    BASE_URL
)

print(
    "Smart Command:",
    SMART_COMMAND_URL
)

print(
    "TTS:",
    "Enabled"
)

print(
    "Microphone:",
    "Enabled"
)

print(
    "Voice feedback protection:",
    "Enabled"
)

print(
    "======================================"
)

# ============================================================
# START LOCAL API AUTOMATICALLY
# ============================================================

print("NOVA LOCAL API: Starting automatically...")

api_thread = threading.Thread(
    target=start_local_api,
    daemon=True
)

api_thread.start()

root.mainloop()