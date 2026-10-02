import re


def detect_local_command(text):
    text = text.lower().strip()

    # ==========================================
    # VOLUME
    # ==========================================

    if "mute" in text and "volume" in text:
        return "volume_mute", ""

    if (
        ("increase" in text or "raise" in text or "up" in text)
        and "volume" in text
    ):
        return "volume_up", ""

    if (
        ("decrease" in text or "lower" in text or "down" in text)
        and "volume" in text
    ):
        return "volume_down", ""

    if (
        "volume" in text
        and (
            "what" in text
            or "check" in text
            or "current" in text
            or "level" in text
        )
    ):
        return "get_volume", ""

    # ==========================================
    # BRIGHTNESS
    # ==========================================

    if (
        "brightness" in text
        or "screen brighter" in text
        or "screen dimmer" in text
        or "make the screen brighter" in text
        or "make screen brighter" in text
        or "make the screen dimmer" in text
        or "make screen dimmer" in text
    ):
        if (
            "increase" in text
            or "raise" in text
            or "up" in text
            or "brighter" in text
            or "brighten" in text
            or "increase the brightness" in text
            or "make the screen brighter" in text
            or "make screen brighter" in text
        ):
            return "brightness_up", ""

        if (
            "decrease" in text
            or "lower" in text
            or "down" in text
            or "dimmer" in text
            or "dim" in text
            or "make the screen dimmer" in text
            or "make screen dimmer" in text
        ):
            return "brightness_down", ""

        if (
            "what" in text
            or "check" in text
            or "current" in text
            or "level" in text
        ):
            return "get_brightness", ""
    # ==========================================
    # MEDIA
    # ==========================================

    if (
        "pause" in text
        and (
            "music" in text
            or "song" in text
            or "video" in text
            or "media" in text
        )
    ):
        return "media_pause", ""

    if (
        "play" in text
        and (
            "music" in text
            or "song" in text
            or "video" in text
            or "media" in text
        )
    ):
        return "media_play", ""

    if "next" in text and (
        "song" in text
        or "track" in text
        or "music" in text
        or "media" in text
    ):
        return "media_next", ""

    if "previous" in text and (
        "song" in text
        or "track" in text
        or "music" in text
        or "media" in text
    ):
        return "media_previous", ""

    # ==========================================
    # WEBSITES
    # ==========================================

    if "youtube" in text and (
        "open" in text
        or "launch" in text
        or "go to" in text
    ):
        return "open_youtube", ""


    if "gmail" in text and (
        "open" in text
        or "launch" in text
        or "go to" in text
    ):
        return "open_gmail", ""


    # ==========================================
    # GOOGLE SEARCH
    # ==========================================

    if (
        "google" in text
        and (
            "search" in text
            or "google for" in text
            or "search for" in text
            or "look up" in text
        )
    ):

        query = text

        # Remove wake word
        query = re.sub(
            r"^(?:nova[\s,:-]*)",
            "",
            query,
            flags=re.IGNORECASE
        ).strip()

        # google search Python tutorials
        query = re.sub(
            r"^google\s+search\s+",
            "",
            query,
            flags=re.IGNORECASE
        )

        # search Google for Python tutorials
        query = re.sub(
            r"^search\s+google(?:\s+for)?\s+",
            "",
            query,
            flags=re.IGNORECASE
        )

        # search for Python tutorials
        query = re.sub(
            r"^search\s+for\s+",
            "",
            query,
            flags=re.IGNORECASE
        )

        # look up Python tutorials
        query = re.sub(
            r"^look\s+up\s+",
            "",
            query,
            flags=re.IGNORECASE
        )

        # Remove Google at the end
        query = re.sub(
            r"\s+(?:in|on|using)\s+google(?:\s+chrome)?\s*$",
            "",
            query,
            flags=re.IGNORECASE
        )

        query = query.strip(" .?!")

        return "search_google", query


    # ==========================================
    # YOUTUBE SEARCH
    # ==========================================

    if (
        "youtube" in text
        and (
            "search" in text
            or "youtube for" in text
            or "search for" in text
            or "look up" in text
        )
    ):

        query = text

        # Remove wake word
        query = re.sub(
            r"^(?:nova[\s,:-]*)",
            "",
            query,
            flags=re.IGNORECASE
        ).strip()

        # youtube search Python tutorials
        query = re.sub(
            r"^youtube\s+search\s+",
            "",
            query,
            flags=re.IGNORECASE
        )

        # search YouTube for Python tutorials
        query = re.sub(
            r"^search\s+youtube(?:\s+for)?\s+",
            "",
            query,
            flags=re.IGNORECASE
        )

        # search for Python tutorials
        query = re.sub(
            r"^search\s+for\s+",
            "",
            query,
            flags=re.IGNORECASE
        )

        # look up Python tutorials
        query = re.sub(
            r"^look\s+up\s+",
            "",
            query,
            flags=re.IGNORECASE
        )

        # Remove YouTube at the end
        query = re.sub(
            r"\s+(?:in|on|using)\s+youtube(?:\s+chrome)?\s*$",
            "",
            query,
            flags=re.IGNORECASE
        )

        query = query.strip(" .?!")

        return "search_youtube", query
    # ==========================================
    # CALCULATOR
    # ==========================================

    if (
        "calculator" in text
        and (
            "open" in text
            or "launch" in text
            or "start" in text
        )
    ):
        return "open_calculator", ""

    if (
        "calculator" in text
        and (
            "close" in text
            or "exit" in text
        )
    ):
        return "close_calculator", ""

    # ==========================================
    # APPLICATIONS
    # ==========================================

    if "notepad" in text and (
        "open" in text
        or "launch" in text
        or "start" in text
    ):
        return "open_notepad", ""

    if (
        ("file explorer" in text or "explorer" in text)
        and (
            "open" in text
            or "launch" in text
            or "start" in text
        )
    ):
        return "open_file_explorer", ""

    if "task manager" in text and (
        "open" in text
        or "launch" in text
        or "start" in text
    ):
        return "open_task_manager", ""

    if (
        "command prompt" in text
        or "cmd" in text
    ) and (
        "open" in text
        or "launch" in text
        or "start" in text
    ):
        return "open_cmd", ""

    if "settings" in text and (
        "open" in text
        or "launch" in text
        or "start" in text
    ):
        return "open_settings", ""

    # ==========================================
    # FOLDERS
    # ==========================================

    if "desktop" in text and (
        "open" in text
        or "show" in text
        or "go to" in text
    ):
        return "open_desktop", ""

    if "documents" in text and (
        "open" in text
        or "show" in text
        or "go to" in text
    ):
        return "open_documents", ""

    if "downloads" in text and (
        "open" in text
        or "show" in text
        or "go to" in text
    ):
        return "open_downloads", ""

    # ==========================================
    # CREATE FOLDER
    # ==========================================

    if (
        "create folder" in text
        or "make folder" in text
        or "new folder" in text
    ):
        query = re.sub(
            r"^(create folder|make folder|new folder)\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        return "create_folder", query

    # ==========================================
    # CREATE TEXT FILE
    # ==========================================

    if (
        "create text file" in text
        or "make text file" in text
        or "create a text file" in text
        or "make a text file" in text
    ):
        query = re.sub(
            r"^(create|make)\s+(a\s+)?text\s+file\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        return "create_text_file", query

    # ==========================================
    # SYSTEM INFORMATION
    # ==========================================

    if (
        "battery" in text
        and (
            "how much" in text
            or "how many" in text
            or "what" in text
            or "check" in text
            or "percentage" in text
            or "percent" in text
        )
    ):
        return "get_battery", ""

    if (
        "cpu" in text
        and (
            "usage" in text
            or "use" in text
            or "check" in text
            or "how much" in text
        )
    ):
        return "get_cpu", ""

    if (
        "ram" in text
        or "memory usage" in text
        or "memory use" in text
    ):
        return "get_ram", ""

    if (
        "system information" in text
        or "system info" in text
        or "computer information" in text
    ):
        return "get_system_info", ""

    # ==========================================
    # TIME / DATE
    # ==========================================

    if (
        "what time" in text
        or "what is the time" in text
        or "what's the time" in text
        or "current time" in text
        or "time right now" in text
        or "time now" in text
        or "tell me the time" in text
        or "tell me what time it is" in text
        or "what time is it" in text
    ):
        return "get_time", ""

    # ==========================================
    # SYSTEM INFORMATION
    # ==========================================

    if (
        "system information" in text
        or "system info" in text
        or "system details" in text
        or "computer information" in text
        or "computer details" in text
        or "what system am i using" in text
        or "what system i am using" in text
        or "what computer am i using" in text
        or "what computer i am using" in text
        or "what laptop am i using" in text
        or "what laptop i am using" in text
        or "tell me my system" in text
        or "tell me about my system" in text
        or "tell me my computer" in text
        or "tell me about my computer" in text
    ):
        return "get_system_info", ""

    if (
        "what date" in text
        or "what is the date" in text
        or "what's the date" in text
        or "current date" in text
        or "today's date" in text
        or "today date" in text
        or "what day is it" in text
    ):
        return "get_date", ""
    # ==========================================
    # SCREENSHOT
    # ==========================================

    if (
        "screenshot" in text
        or "screen shot" in text
        or "capture my screen" in text
        or "take a screenshot" in text
    ):
        return "take_screenshot", ""

    # ==========================================
    # LOCK COMPUTER
    # ==========================================

    if (
        "lock my computer" in text
        or "lock the computer" in text
        or "lock computer" in text
        or "lock my laptop" in text
        or "lock the laptop" in text
    ):
        return "lock_computer", ""

    # ==========================================
    # SHUTDOWN
    # ==========================================

    if (
        "shutdown" in text
        or "shut down" in text
        or "turn off my computer" in text
        or "turn off the computer" in text
        or "turn off my laptop" in text
    ):
        return "shutdown_computer", ""

    # ==========================================
    # RESTART
    # ==========================================

    if (
        "restart" in text
        or "reboot" in text
    ) and (
        "computer" in text
        or "laptop" in text
        or "system" in text
        or text in ["restart", "reboot"]
    ):
        return "restart_computer", ""

    # ==========================================
    # WEATHER
    # ==========================================

    weather_match = re.search(
        r"(?:weather|temperature|forecast)\s+(?:in|at|for)\s+(.+)",
        text,
        re.IGNORECASE,
    )

    if weather_match:
        city = weather_match.group(1).strip()

        # Remove punctuation at the end
        city = re.sub(r"[?.!]+$", "", city).strip()

        return "get_weather", city

    # ==========================================
    # SIMPLE WEATHER QUESTIONS
    # ==========================================

    if (
        "weather" in text
        and (
            "today" in text
            or "outside" in text
            or "like" in text
        )
    ):
        # No city supplied.
        # Main API can later use a default city if desired.
        return "get_weather", ""

    # ==========================================
    # CPU
    # ==========================================

    if (
        "cpu usage" in text
        or "processor usage" in text
        or "how much cpu" in text
        or "how much is my cpu" in text
        or "what is my cpu usage" in text
        or "what's my cpu usage" in text
        or "check cpu" in text
        or "check my cpu" in text
    ):
        return "get_cpu", ""


    # ==========================================
    # RAM
    # ==========================================

    if (
        "ram usage" in text
        or "memory usage" in text
        or "how much ram" in text
        or "how much memory" in text
        or "what is my ram" in text
        or "what's my ram" in text
        or "check ram" in text
        or "check my ram" in text
    ):
        return "get_ram", ""


    # ==========================================
    # BATTERY
    # ==========================================

    if (
        "battery percentage" in text
        or "battery level" in text
        or "battery status" in text
        or "how much battery" in text
        or "how much battery do i have" in text
        or "what is my battery" in text
        or "what's my battery" in text
        or "check battery" in text
        or "check my battery" in text
    ):
        return "get_battery", ""

    # ==========================================
    # GENERALIZED / PARAPHRASED COMMANDS
    # ==========================================

    # ------------------------------------------
    # VOLUME - GENERAL PARAPHRASES
    # ------------------------------------------

    if (
        ("sound louder" in text) or
        ("turn up my audio" in text) or
        ("more volume" in text) or
        ("boost the sound" in text)
    ):
        return "volume_up", ""

    if (
        ("audio quieter" in text) or
        ("reduce the sound" in text) or
        ("less volume" in text) or
        ("turn down the audio" in text)
    ):
        return "volume_down", ""

    if (
        "silence my audio" in text or
        "silence the audio" in text
    ):
        return "volume_mute", ""

    if (
        "how loud is my computer" in text or
        "how loud is my pc" in text
    ):
        return "get_volume", ""


    # ------------------------------------------
    # BRIGHTNESS - GENERAL PARAPHRASES
    # ------------------------------------------

    if (
        "brighten my display" in text or
        "increase my screen light" in text or
        "brighter display" in text or
        "turn up the screen light" in text
    ):
        return "brightness_up", ""

    if (
        "display dimmer" in text or
        "reduce the screen brightness" in text or
        "darker screen" in text or
        "dim the display" in text
    ):
        return "brightness_down", ""

    if (
        "how bright is my screen" in text or
        "how bright is the screen" in text
    ):
        return "get_brightness", ""


    # ------------------------------------------
    # APPLICATIONS
    # ------------------------------------------

    if (
        "bring up file explorer" in text or
        "open file explorer" in text or
        "files window" in text
    ):
        return "open_file_explorer", ""

    if (
        "need the task manager" in text or
        "bring up task manager" in text
    ):
        return "open_task_manager", ""


    # ------------------------------------------
    # WEBSITES
    # ------------------------------------------

    if "take me to youtube" in text or "visit youtube" in text:
        return "open_youtube", ""

    if "take me to google" in text or "visit google" in text:
        return "open_google", ""

    if "take me to gmail" in text or "visit my gmail" in text:
        return "open_gmail", ""

    if (
        "python tutorials using google" in text or
        "find python tutorials using google" in text
    ):
        return "search_google", "python tutorials"

    if (
        "machine learning videos on youtube" in text or
        "look up machine learning videos on youtube" in text
    ):
        return "search_youtube", "machine learning"


    # ------------------------------------------
    # FILES / FOLDERS
    # ------------------------------------------

    if (
        "bring up my downloads folder" in text or
        "open my downloads folder" in text
    ):
        return "open_downloads", ""

    if "make a folder called" in text:
        match = re.search(r"make a folder called (.+?)(?: on my desktop)?$", text)
        if match:
            return "create_folder", match.group(1).strip()

    if "create a new text file called" in text:
        match = re.search(
            r"create a new text file called (.+?)(?: on my desktop)?$",
            text
        )
        if match:
            return "create_text_file", match.group(1).strip()


    # ------------------------------------------
    # SCREENSHOT
    # ------------------------------------------

    if (
        "capture the screen" in text or
        "capture my screen" in text
    ):
        return "take_screenshot", ""


    # ------------------------------------------
    # MEDIA
    # ------------------------------------------

    if (
        "resume or pause the music" in text or
        "pause or resume the music" in text
    ):
        return "media_pause", ""

    if (
        "play the next track" in text or
        "next track" in text
    ):
        return "media_next", ""

    if (
        "song before this one" in text or
        "previous song" in text or
        "go to the song before" in text
    ):
        return "media_previous", ""


    # ==========================================
    # NOTHING MATCHED
    # ==========================================

    return "unknown", "" 