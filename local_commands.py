import re


def detect_local_command(text):

    text = str(text).lower().strip()

    # =========================================================
    # VOLUME
    # =========================================================

    if any(word in text for word in [
        "mute", "silence"
    ]) and any(word in text for word in [
        "volume", "sound", "audio"
    ]):
        return "volume_mute", ""

    if any(word in text for word in [
        "increase", "raise", "turn up", "make louder",
        "louder", "boost", "more volume", "more sound"
    ]) and any(word in text for word in [
        "volume", "sound", "audio"
    ]):
        return "volume_up", ""

    if any(word in text for word in [
        "decrease", "reduce", "lower", "turn down",
        "make quieter", "quieter", "less volume",
        "less sound"
    ]) and any(word in text for word in [
        "volume", "sound", "audio"
    ]):
        return "volume_down", ""

    if any(word in text for word in [
        "how loud", "volume level", "current volume",
        "what is my volume"
    ]):
        return "get_volume", ""


    # =========================================================
    # BRIGHTNESS
    # =========================================================

    if any(word in text for word in [
        "increase brightness",
        "brighter",
        "brighten",
        "turn up the screen light",
        "increase my screen light"
    ]):
        return "brightness_up", ""

    if any(word in text for word in [
        "decrease brightness",
        "darker",
        "dim",
        "dimmer",
        "reduce the screen brightness",
        "lower brightness"
    ]):
        return "brightness_down", ""

    if any(word in text for word in [
        "how bright",
        "brightness level",
        "current brightness",
        "what is my brightness"
    ]):
        return "get_brightness", ""


    # =========================================================
    # APPLICATIONS
    # =========================================================

    if any(word in text for word in [
        "calculator",
    ]) and any(word in text for word in [
        "open", "start", "launch", "bring up"
    ]):
        return "open_calculator", ""

    if any(word in text for word in [
        "notepad"
    ]) and any(word in text for word in [
        "open", "start", "launch", "bring up"
    ]):
        return "open_notepad", ""

    if any(word in text for word in [
        "file explorer",
        "files window",
        "file window"
    ]) and any(word in text for word in [
        "open", "start", "launch", "bring up"
    ]):
        return "open_file_explorer", ""

    if "task manager" in text and any(word in text for word in [
        "open", "start", "launch", "bring up",
        "need", "want"
    ]):
        return "open_task_manager", ""

    if "windows settings" in text or (
        "settings" in text and any(word in text for word in [
            "open", "start", "launch", "bring up"
        ])
    ):
        return "open_settings", ""

    if "exit the calculator" in text or (
        "close calculator" in text
    ):
        return "close_calculator", ""


    # =========================================================
    # WEB
    # =========================================================

    if "youtube" in text and any(word in text for word in [
        "open", "launch", "visit", "take me to", "go to"
    ]):
        if any(word in text for word in [
            "search", "find", "look up"
        ]):
            pass
        else:
            return "open_youtube", ""

    if "google" in text and any(word in text for word in [
        "open", "launch", "visit", "take me to", "go to"
    ]):
        if any(word in text for word in [
            "search", "find", "look up"
        ]):
            pass
        else:
            return "open_google", ""

    if "gmail" in text and any(word in text for word in [
        "open", "launch", "visit", "take me to", "go to"
    ]):
        return "open_gmail", ""


    # Google search
    if "google" in text and any(word in text for word in [
        "search", "find", "look up"
    ]):
        query = re.sub(
            r"\b(search|find|look up)\b",
            "",
            text
        )

        query = re.sub(
            r"\b(using|on|with)?\s*google\b",
            "",
            query
        ).strip()

        return "search_google", query


    # YouTube search
    if "youtube" in text and any(word in text for word in [
        "search", "find", "look up"
    ]):
        query = re.sub(
            r"\b(search|find|look up)\b",
            "",
            text
        )

        query = re.sub(
            r"\bon\s*youtube\b",
            "",
            query
        ).strip()

        return "search_youtube", query


    # =========================================================
    # FILES / FOLDERS
    # =========================================================

    if any(word in text for word in [
        "desktop"
    ]) and any(word in text for word in [
        "open", "go to", "bring up"
    ]):
        return "open_desktop", ""

    if "documents" in text and any(word in text for word in [
        "open", "go to", "bring up"
    ]):
        return "open_documents", ""

    if "downloads" in text and any(word in text for word in [
        "open", "go to", "bring up"
    ]):
        return "open_downloads", ""

    # Create folder
    if any(word in text for word in [
        "create a folder",
        "create folder",
        "make a folder",
        "new folder",
        "folder named",
        "folder called"
    ]):
        match = re.search(
            r"(?:called|named)\s+([a-zA-Z0-9_-]+)",
            text
        )

        if match:
            return "create_folder", match.group(1)

        return "create_folder", ""

    # Create text file
    if any(word in text for word in [
        "create a text file",
        "create text file",
        "new text file",
        "text file named",
        "text file called"
    ]):
        match = re.search(
            r"(?:called|named)\s+([a-zA-Z0-9_.-]+)",
            text
        )

        if match:
            return "create_text_file", match.group(1)

        return "create_text_file", ""


    # =========================================================
    # SYSTEM INFORMATION
    # =========================================================

    if any(word in text for word in [
        "current time",
        "what time",
        "time is it"
    ]):
        return "get_time", ""

    if any(word in text for word in [
        "what day",
        "today's date",
        "what date",
        "date is it"
    ]):
        return "get_date", ""

    if any(word in text for word in [
        "battery",
        "battery level",
        "battery left"
    ]):
        return "get_battery", ""

    if any(word in text for word in [
        "ram usage",
        "memory usage",
        "how much ram"
    ]):
        return "get_ram", ""

    if any(word in text for word in [
        "cpu usage",
        "cpu being used",
        "how heavily is my cpu",
        "processor usage"
    ]):
        return "get_cpu", ""

    if any(word in text for word in [
        "system information",
        "computer information",
        "system info",
        "computer specs"
    ]):
        return "get_system_info", ""


    # =========================================================
    # SCREENSHOT
    # =========================================================

    if any(word in text for word in [
        "screenshot",
        "screen capture",
        "capture the screen",
        "capture my screen",
        "take a screen"
    ]):
        return "take_screenshot", ""


    # =========================================================
    # MEDIA
    # =========================================================

    if any(word in text for word in [
        "play pause",
        "pause the music",
        "resume the music",
        "resume or pause"
    ]):
        return "play_pause", ""

    if any(word in text for word in [
        "next song",
        "next track",
        "play the next"
    ]):
        return "next_song", ""

    if any(word in text for word in [
        "previous song",
        "previous track",
        "song before",
        "track before"
    ]):
        return "previous_song", ""


    # =========================================================
    # COMPUTER CONTROL
    # =========================================================

    if any(word in text for word in [
        "shut down",
        "shutdown",
        "power off",
        "turn off my computer",
        "turn off the computer",
        "shut my pc down"
    ]):
        return "shutdown_computer", ""

    if any(word in text for word in [
        "restart",
        "reboot"
    ]):
        return "restart_computer", ""

    if "lock" in text and any(word in text for word in [
        "computer", "pc", "laptop", "system"
    ]):
        return "lock_computer", ""


    # =========================================================
    # FALLBACK
    # =========================================================

    return None, ""