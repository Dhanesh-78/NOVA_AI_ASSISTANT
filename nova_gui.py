import tkinter as tk
from tkinter import messagebox
import threading
import requests
import speech_recognition as sr
import pyttsx3
import psutil

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL


# =========================================================
# API URLS
# =========================================================

API_URL = "http://127.0.0.1:8000/smart-command"
CONFIRM_URL = "http://127.0.0.1:8000/confirm-command"


# =========================================================
# VOICE ENGINE
# =========================================================

engine = pyttsx3.init()
engine.setProperty("rate", 170)


def speak(text):
    engine.say(text)
    engine.runAndWait()


# =========================================================
# SPEECH RECOGNITION
# =========================================================

def listen():

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:

        status_label.config(
            text="Listening..."
        )

        recognizer.adjust_for_ambient_noise(
            source,
            duration=0.3
        )

        try:

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )

        except sr.WaitTimeoutError:

            return ""

    try:

        return recognizer.recognize_google(audio)

    except sr.UnknownValueError:

        return ""

    except sr.RequestError:

        return ""


# =========================================================
# CHAT DISPLAY
# =========================================================

def add_message(sender, message):

    chat_box.config(
        state=tk.NORMAL
    )

    chat_box.insert(
        tk.END,
        f"{sender}: {message}\n\n"
    )

    chat_box.config(
        state=tk.DISABLED
    )

    # Automatically move to the newest message
    chat_box.see(
        tk.END
    )


# =========================================================
# API REQUEST
# =========================================================

def send_command(message):

    try:

        response = requests.post(
            API_URL,
            json={
                "message": message
            },
            timeout=120
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:

        return {
            "status": "error",
            "message": "Nova API is not running."
        }

    except requests.exceptions.Timeout:

        return {
            "status": "error",
            "message": "Nova API took too long to respond."
        }

    except requests.exceptions.RequestException:

        return {
            "status": "error",
            "message": "There was a problem connecting to Nova."
        }


# =========================================================
# CONFIRM COMMAND
# =========================================================

def confirm_action(action, query):

    try:

        response = requests.post(
            CONFIRM_URL,
            json={
                "action": action,
                "query": query
            },
            timeout=120
        )

        response.raise_for_status()

        return response.json()

    except Exception:

        return {
            "status": "error",
            "message": "Could not execute the command."
        }


# =========================================================
# PROCESS API RESULT
# =========================================================

def process_result(data):

    status = data.get(
        "status"
    )

    # -----------------------------------------------------
    # ERROR
    # -----------------------------------------------------

    if status == "error":

        message = data.get(
            "message",
            "Something went wrong."
        )

        add_message(
            "Nova",
            message
        )

        speak(
            message
        )

        status_label.config(
            text="Ready"
        )

        return

    # -----------------------------------------------------
    # UNKNOWN
    # -----------------------------------------------------

    if status == "unknown":

        message = data.get(
            "response",
            "I don't know how to do that yet."
        )

        add_message(
            "Nova",
            message
        )

        speak(
            message
        )

        status_label.config(
            text="Ready"
        )

        return

    # -----------------------------------------------------
    # CONFIRMATION REQUIRED
    # -----------------------------------------------------

    if status == "confirmation_required":

        message = data.get(
            "confirmation_message",
            "Do you want me to continue?"
        )

        add_message(
            "Nova",
            message
        )

        root.after(
            0,
            lambda: ask_confirmation(
                data["action"],
                data.get(
                    "query",
                    ""
                ),
                message
            )
        )

        return

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    message = data.get(
        "response",
        "Command completed successfully."
    )

    add_message(
        "Nova",
        message
    )

    speak(
        message
    )

    status_label.config(
        text="Ready"
    )


# =========================================================
# CONFIRMATION DIALOG
# =========================================================

def ask_confirmation(
    action,
    query,
    message
):

    answer = messagebox.askyesno(
        "Nova Confirmation",
        message
    )

    if not answer:

        add_message(
            "Nova",
            "Okay, I cancelled the command."
        )

        speak(
            "Okay, I cancelled the command."
        )

        status_label.config(
            text="Ready"
        )

        return

    status_label.config(
        text="Executing..."
    )

    def worker():

        result = confirm_action(
            action,
            query
        )

        root.after(
            0,
            lambda: process_result(result)
        )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


# =========================================================
# TEXT COMMAND
# =========================================================

def handle_command():

    message = entry.get().strip()

    if not message:

        return

    entry.delete(
        0,
        tk.END
    )

    add_message(
        "You",
        message
    )

    status_label.config(
        text="Thinking..."
    )

    def worker():

        data = send_command(
            message
        )

        root.after(
            0,
            lambda: process_result(data)
        )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


# =========================================================
# MICROPHONE
# =========================================================

def handle_microphone():

    status_label.config(
        text="Listening..."
    )

    def worker():

        text = listen()

        if not text:

            root.after(
                0,
                lambda: status_label.config(
                    text="Ready"
                )
            )

            return

        root.after(
            0,
            lambda: entry.insert(
                0,
                text
            )
        )

        root.after(
            0,
            handle_command
        )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


# =========================================================
# GET VOLUME
# =========================================================

def get_volume():

    try:

        devices = AudioUtilities.GetSpeakers()

        interface = devices.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )

        volume = (
            interface.GetMasterVolumeLevelScalar()
            * 100
        )

        return round(
            volume
        )

    except Exception:

        return 0


# =========================================================
# UPDATE SYSTEM DASHBOARD
# =========================================================

def update_dashboard():

    # CPU
    cpu = psutil.cpu_percent(
        interval=None
    )

    # RAM
    ram = psutil.virtual_memory().percent

    # Battery
    battery = psutil.sensors_battery()

    if battery is not None:

        battery_value = battery.percent

        battery_label.config(
            text=f"Battery: {battery_value:.0f}%"
        )

    else:

        battery_label.config(
            text="Battery: N/A"
        )

    # CPU label
    cpu_label.config(
        text=f"CPU: {cpu:.0f}%"
    )

    # RAM label
    ram_label.config(
        text=f"RAM: {ram:.0f}%"
    )

    # Volume
    volume = get_volume()

    volume_label.config(
        text=f"Volume: {volume}%"
    )

    # Schedule next update
    root.after(
        2000,
        update_dashboard
    )


# =========================================================
# API STATUS
# =========================================================

def check_api():

    try:

        response = requests.get(
            "http://127.0.0.1:8000/",
            timeout=3
        )

        if response.status_code == 200:

            api_status_label.config(
                text="API: Connected"
            )

        else:

            api_status_label.config(
                text="API: Error"
            )

    except Exception:

        api_status_label.config(
            text="API: Offline"
        )

    root.after(
        5000,
        check_api
    )


# =========================================================
# MAIN WINDOW
# =========================================================

root = tk.Tk()

root.title(
    "Nova AI Assistant"
)

root.geometry(
    "800x750"
)

root.resizable(
    False,
    False
)


# =========================================================
# TITLE
# =========================================================

title_label = tk.Label(
    root,
    text="NOVA",
    font=("Arial", 30, "bold")
)

title_label.pack(
    pady=(20, 2)
)


subtitle_label = tk.Label(
    root,
    text="AI Desktop Assistant",
    font=("Arial", 12)
)

subtitle_label.pack(
    pady=(0, 15)
)


# =========================================================
# SYSTEM DASHBOARD
# =========================================================

dashboard = tk.Frame(
    root
)

dashboard.pack(
    pady=5
)


cpu_label = tk.Label(
    dashboard,
    text="CPU: 0%",
    font=("Arial", 10, "bold"),
    width=15
)

cpu_label.grid(
    row=0,
    column=0,
    padx=5
)


ram_label = tk.Label(
    dashboard,
    text="RAM: 0%",
    font=("Arial", 10, "bold"),
    width=15
)

ram_label.grid(
    row=0,
    column=1,
    padx=5
)


battery_label = tk.Label(
    dashboard,
    text="Battery: N/A",
    font=("Arial", 10, "bold"),
    width=15
)

battery_label.grid(
    row=0,
    column=2,
    padx=5
)


volume_label = tk.Label(
    dashboard,
    text="Volume: 0%",
    font=("Arial", 10, "bold"),
    width=15
)

volume_label.grid(
    row=0,
    column=3,
    padx=5
)


# =========================================================
# CHAT AREA WITH SCROLLBAR
# =========================================================

# =========================================================
# CHAT AREA WITH SCROLLBAR
# =========================================================

chat_frame = tk.Frame(
    root
)

chat_frame.pack(
    padx=20,
    pady=15
)

chat_box = tk.Text(
    chat_frame,
    height=24,
    width=78,
    state=tk.DISABLED,
    font=("Arial", 11),
    wrap=tk.WORD
)

chat_box.pack(
    side=tk.LEFT
)

chat_scrollbar = tk.Scrollbar(
    chat_frame,
    orient=tk.VERTICAL,
    command=chat_box.yview
)

chat_scrollbar.pack(
    side=tk.RIGHT,
    fill=tk.Y
)

chat_box.config(
    yscrollcommand=chat_scrollbar.set
)

# =========================================================
# INPUT
# =========================================================

input_frame = tk.Frame(
    root
)

input_frame.pack(
    pady=5
)


entry = tk.Entry(
    input_frame,
    width=50,
    font=("Arial", 12)
)

entry.grid(
    row=0,
    column=0,
    padx=5
)


send_button = tk.Button(
    input_frame,
    text="Send",
    width=10,
    command=handle_command
)

send_button.grid(
    row=0,
    column=1,
    padx=5
)


mic_button = tk.Button(
    input_frame,
    text="🎤 Speak",
    width=10,
    command=handle_microphone
)

mic_button.grid(
    row=0,
    column=2,
    padx=5
)


# =========================================================
# STATUS
# =========================================================

status_label = tk.Label(
    root,
    text="Ready",
    font=("Arial", 10)
)

status_label.pack(
    pady=3
)


api_status_label = tk.Label(
    root,
    text="API: Checking...",
    font=("Arial", 10)
)

api_status_label.pack(
    pady=3
)


# =========================================================
# WELCOME MESSAGE
# =========================================================

add_message(
    "Nova",
    "Hello! I am Nova. Your AI laptop assistant is ready."
)


# =========================================================
# START MONITORS
# =========================================================

check_api()
update_dashboard()


# =========================================================
# START GUI
# =========================================================

root.mainloop()