import webbrowser
import subprocess
import datetime
import os
import ctypes

import psutil
import pyautogui

from urllib.parse import quote_plus

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import screen_brightness_control as sbc


def execute_command(action: str, query: str = ""):

    action = action.lower().strip()

    # ==========================================
    # VOLUME
    # ==========================================

    if action == "volume_up":

        pyautogui.press("volumeup", presses=3)

        return "Volume increased."

    elif action == "volume_down":

        pyautogui.press("volumedown", presses=3)

        return "Volume decreased."

    elif action == "volume_mute":

        pyautogui.press("volumemute")

        return "Volume muted."

    elif action == "get_volume":

        try:
            devices = AudioUtilities.GetSpeakers()

            interface = devices.Activate(
                IAudioEndpointVolume._iid_,
                CLSCTX_ALL,
                None
            )

            volume = interface.GetMasterVolumeLevelScalar() * 100

            return f"Your current volume is {volume:.0f}%."

        except Exception as e:

            print("Volume error:", e)

            return "I couldn't read the current volume."

    # ==========================================
    # BRIGHTNESS
    # ==========================================

    elif action == "brightness_up":

        try:
            current = sbc.get_brightness(display=0)[0]

            new_value = min(current + 10, 100)

            sbc.set_brightness(new_value)

            return f"Brightness increased to {new_value}%."

        except Exception as e:

            print("Brightness error:", e)

            return "I couldn't change the brightness."

    elif action == "brightness_down":

        try:
            current = sbc.get_brightness(display=0)[0]

            new_value = max(current - 10, 0)

            sbc.set_brightness(new_value)

            return f"Brightness decreased to {new_value}%."

        except Exception as e:

            print("Brightness error:", e)

            return "I couldn't change the brightness."

    elif action == "get_brightness":

        try:
            current = sbc.get_brightness(display=0)[0]

            return f"Your brightness is {current}%."

        except Exception as e:

            print("Brightness error:", e)

            return "I couldn't read the brightness."

    # ==========================================
    # MEDIA CONTROL
    # ==========================================

    elif action == "play_pause":

        pyautogui.press("playpause")

        return "Media playback toggled."

    elif action == "next_song":

        pyautogui.press("nexttrack")

        return "Skipped to the next track."

    elif action == "previous_song":

        pyautogui.press("prevtrack")

        return "Went back to the previous track."

    # ==========================================
    # WEBSITES
    # ==========================================

    elif action == "open_youtube":

        webbrowser.open("https://www.youtube.com")

        return "YouTube opened successfully."

    elif action == "open_google":

        webbrowser.open("https://www.google.com")

        return "Google opened successfully."

    elif action == "open_gmail":

        webbrowser.open("https://mail.google.com")

        return "Gmail opened successfully."

    elif action == "search_google":

        webbrowser.open(
            f"https://www.google.com/search?q={quote_plus(query)}"
        )

        return f"I searched Google for {query}."

    elif action == "search_youtube":

        webbrowser.open(
            f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        )

        return f"I searched YouTube for {query}."

    # ==========================================
    # WINDOWS APPLICATIONS
    # ==========================================

    elif action == "open_calculator":

        subprocess.Popen("calc.exe")

        return "Calculator opened successfully."

    elif action == "close_calculator":

        subprocess.run(
            ["taskkill", "/F", "/IM", "CalculatorApp.exe"],
            capture_output=True
        )

        return "Calculator closed."

    elif action == "open_notepad":

        subprocess.Popen("notepad.exe")

        return "Notepad opened successfully."

    elif action == "open_file_explorer":

        subprocess.Popen("explorer.exe")

        return "File Explorer opened successfully."

    elif action == "open_task_manager":

        subprocess.Popen("taskmgr.exe")

        return "Task Manager opened successfully."

    elif action == "open_command_prompt":

        subprocess.Popen("cmd.exe")

        return "Command Prompt opened successfully."

    elif action == "open_settings":

        subprocess.Popen(
            "start ms-settings:",
            shell=True
        )

        return "Windows Settings opened."

    # ==========================================
    # COMMON FOLDERS
    # ==========================================

    elif action == "open_desktop":

        path = os.path.join(
            os.path.expanduser("~"),
            "Desktop"
        )

        os.startfile(path)

        return "Desktop opened."

    elif action == "open_documents":

        path = os.path.join(
            os.path.expanduser("~"),
            "Documents"
        )

        os.startfile(path)

        return "Documents opened."

    elif action == "open_downloads":

        path = os.path.join(
            os.path.expanduser("~"),
            "Downloads"
        )

        os.startfile(path)

        return "Downloads opened."

    # ==========================================
    # FILE / FOLDER CREATION
    # ==========================================

    elif action == "create_folder":

        folder_name = query.strip()

        if not folder_name:

            return "Please tell me the folder name."

        folder_path = os.path.join(
            os.path.expanduser("~"),
            "Desktop",
            folder_name
        )

        os.makedirs(
            folder_path,
            exist_ok=True
        )

        return (
            f"I created the folder "
            f"{folder_name} on your Desktop."
        )

    elif action == "create_text_file":

        file_name = query.strip()

        if not file_name:

            return "Please tell me the file name."

        if not file_name.lower().endswith(".txt"):

            file_name += ".txt"

        file_path = os.path.join(
            os.path.expanduser("~"),
            "Desktop",
            file_name
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write("")

        return (
            f"I created {file_name} "
            f"on your Desktop."
        )

    # ==========================================
    # SYSTEM INFORMATION
    # ==========================================

    elif action == "get_time":

        current_time = datetime.datetime.now().strftime(
            "%I:%M %p"
        )

        return f"The current time is {current_time}."

    elif action == "get_date":

        current_date = datetime.datetime.now().strftime(
            "%d %B %Y"
        )

        return f"Today's date is {current_date}."

    elif action == "get_battery":

        battery = psutil.sensors_battery()

        if battery is None:

            return "I couldn't read the battery information."

        percentage = battery.percent

        charging = battery.power_plugged

        status = (
            "charging"
            if charging
            else "not charging"
        )

        return (
            f"Your battery is at "
            f"{percentage:.0f}% and is {status}."
        )

    elif action == "get_ram":

        memory = psutil.virtual_memory()

        used_gb = memory.used / (1024 ** 3)
        total_gb = memory.total / (1024 ** 3)

        return (
            f"RAM usage is {memory.percent:.0f}%. "
            f"You are using about "
            f"{used_gb:.1f} GB of {total_gb:.1f} GB."
        )

    elif action == "get_cpu":

        usage = psutil.cpu_percent(interval=1)

        return (
            f"Your current CPU usage is "
            f"{usage:.0f}%."
        )

    elif action == "get_system_info":

        memory = psutil.virtual_memory()

        cpu = psutil.cpu_percent(interval=1)

        battery = psutil.sensors_battery()

        if battery:

            battery_info = f"{battery.percent:.0f}%"

        else:

            battery_info = "Unavailable"

        return (
            f"CPU usage: {cpu:.0f}%. "
            f"RAM usage: {memory.percent:.0f}%. "
            f"Battery: {battery_info}."
        )

    # ==========================================
    # SCREENSHOT
    # ==========================================

    elif action == "take_screenshot":

        screenshot = pyautogui.screenshot()

        timestamp = datetime.datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        path = os.path.join(
            os.path.expanduser("~"),
            "Desktop",
            f"Nova_Screenshot_{timestamp}.png"
        )

        screenshot.save(path)

        return (
            f"Screenshot saved on your Desktop as "
            f"{os.path.basename(path)}."
        )

    # ==========================================
    # LOCK COMPUTER
    # ==========================================

    elif action == "lock_computer":

        ctypes.windll.user32.LockWorkStation()

        return "Your computer is locked."

    # ==========================================
    # SHUTDOWN
    # ==========================================

    elif action == "shutdown_computer":

        subprocess.Popen(
            ["shutdown", "/s", "/t", "10"]
        )

        return (
            "Your computer will shut down "
            "in 10 seconds."
        )

    # ==========================================
    # RESTART
    # ==========================================

    elif action == "restart_computer":

        subprocess.Popen(
            ["shutdown", "/r", "/t", "10"]
        )

        return (
            "Your computer will restart "
            "in 10 seconds."
        )

    # ==========================================
    # UNKNOWN
    # ==========================================

    else:

        return (
            "I don't know how to perform "
            "that action yet."
        )