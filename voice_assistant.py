import speech_recognition as sr
import pyttsx3
import requests
import time


# ==========================================
# NOVA API
# ==========================================

API_URL = "http://127.0.0.1:8001/smart-command"
CONFIRM_URL = "http://127.0.0.1:8001/confirm-command"


# ==========================================
# SETTINGS
# ==========================================

CONVERSATION_TIMEOUT = 8


# ==========================================
# TEXT TO SPEECH
# ==========================================

engine = pyttsx3.init()
engine.setProperty("rate", 170)


def speak(text):

    print(f"\nNova: {text}")

    try:
        engine.say(text)
        engine.runAndWait()

    except Exception as e:

        print("TTS ERROR:", e)


# ==========================================
# LISTEN
# ==========================================

def listen(timeout=5, phrase_time_limit=8):

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:

        print("\n🎤 Listening...")

        try:

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.3
            )

            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )

        except sr.WaitTimeoutError:

            return ""

        except Exception as e:

            print("MICROPHONE ERROR:", e)

            return ""

    try:

        text = recognizer.recognize_google(audio)

        print(f"\nYou: {text}")

        return text.lower().strip()

    except sr.UnknownValueError:

        print("❌ Sorry, I couldn't understand you.")

        return ""

    except sr.RequestError as e:

        print("❌ Speech recognition error:", e)

        speak(
            "Speech recognition is currently unavailable."
        )

        return ""

    except Exception as e:

        print("SPEECH ERROR:", e)

        return ""


# ==========================================
# WAKE WORD
# ==========================================

def extract_command(text):

    wake_words = [
        "hey nova",
        "okay nova",
        "ok nova",
        "nova"
    ]

    text = text.lower().strip()

    for wake_word in wake_words:

        if text.startswith(wake_word):

            command = text[len(wake_word):].strip()

            command = command.lstrip(",.!? ")

            return command.strip()

    return ""


# ==========================================
# EXIT COMMAND
# ==========================================

def is_exit_command(command):

    exit_commands = [

        "exit",
        "quit",
        "stop",
        "goodbye",
        "good bye",
        "bye",

        "close nova",
        "shutdown nova",
        "exit nova"

    ]

    return command.lower().strip() in exit_commands


# ==========================================
# SEND TO API
# ==========================================

def send_to_api(message):

    try:

        response = requests.post(

            API_URL,

            json={
                "message": message
            },

            timeout=90
        )

        response.raise_for_status()

        data = response.json()

        print("\n========== API RESPONSE ==========")

        print(data)

        print("==================================")

        return data

    except requests.exceptions.Timeout:

        return {

            "status": "error",

            "message":
            "The Nova API took too long to respond."

        }

    except requests.exceptions.ConnectionError:

        return {

            "status": "error",

            "message":
            "I couldn't connect to the Nova API. "
            "Please make sure FastAPI is running."

        }

    except requests.exceptions.RequestException as e:

        print("API REQUEST ERROR:", e)

        return {

            "status": "error",

            "message":
            "There was a problem communicating with Nova."

        }

    except Exception as e:

        print("API ERROR:", repr(e))

        return {

            "status": "error",

            "message":
            "Something went wrong."

        }


# ==========================================
# CONFIRM COMMAND
# ==========================================

def confirm_command(action, query):

    try:

        response = requests.post(

            CONFIRM_URL,

            json={

                "action": action,

                "query": query

            },

            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        print(
            "\n========== CONFIRMATION RESPONSE =========="
        )

        print(data)

        print("===========================================")

        return data.get(

            "response",

            data.get(
                "message",
                "Command completed."
            )

        )

    except requests.exceptions.Timeout:

        return "The confirmation request timed out."

    except requests.exceptions.ConnectionError:

        return "I couldn't connect to the Nova API."

    except requests.exceptions.RequestException as e:

        print("CONFIRMATION ERROR:", e)

        return "I couldn't execute the confirmed command."

    except Exception as e:

        print("CONFIRMATION ERROR:", repr(e))

        return "I couldn't execute the confirmed command."


# ==========================================
# YES / NO
# ==========================================

def is_positive_answer(answer):

    positive_answers = [

        "yes",
        "yeah",
        "yep",
        "yes please",
        "sure",
        "okay",
        "ok",
        "do it",
        "continue",
        "go ahead",
        "confirm",
        "confirmed",
        "please do",
        "do that"

    ]

    return answer.lower().strip() in positive_answers


def is_negative_answer(answer):

    negative_answers = [

        "no",
        "nope",
        "cancel",
        "cancel it",
        "don't",
        "do not",
        "stop",
        "never mind",
        "forget it"

    ]

    return answer.lower().strip() in negative_answers


# ==========================================
# HANDLE CONFIRMATION
# ==========================================

def handle_confirmation(data):

    action = data.get(
        "action",
        ""
    )

    query = data.get(
        "query",
        ""
    )

    confirmation_message = data.get(
        "confirmation_message"
    )

    if not confirmation_message:

        confirmation_message = data.get(

            "message",

            "Do you want me to continue?"

        )

    speak(
        confirmation_message
    )

    # --------------------------------------
    # IMPORTANT:
    # Confirmation does NOT need "Nova"
    # --------------------------------------

    answer = listen(
        timeout=5,
        phrase_time_limit=5
    )

    if not answer:

        speak(
            "I didn't hear your answer. "
            "The command was cancelled."
        )

        return


    # --------------------------------------
    # Remove wake word if user says:
    # "Nova yes"
    # --------------------------------------

    wake_command = extract_command(
        answer
    )

    if wake_command:

        answer = wake_command


    answer = answer.lower().strip()

    print(
        f"\nConfirmation answer: {answer}"
    )


    # --------------------------------------
    # YES
    # --------------------------------------

    if is_positive_answer(answer):

        speak("Okay.")

        result = confirm_command(

            action,

            query

        )

        speak(result)

        return


    # --------------------------------------
    # NO
    # --------------------------------------

    if is_negative_answer(answer):

        speak(
            "Okay, I cancelled the command."
        )

        return


    # --------------------------------------
    # UNKNOWN
    # --------------------------------------

    speak(
        "I didn't understand your answer. "
        "The command was cancelled."
    )


# ==========================================
# HANDLE API RESPONSE
# ==========================================

def handle_response(data):

    if not data:

        speak(
            "I didn't receive a response."
        )

        return


    status = data.get(
        "status"
    )


    # --------------------------------------
    # ERROR
    # --------------------------------------

    if status == "error":

        speak(

            data.get(

                "message",

                "Something went wrong."

            )

        )

        return


    # --------------------------------------
    # CONFIRMATION
    # --------------------------------------

    if status == "confirmation_required":

        handle_confirmation(data)

        return


    # --------------------------------------
    # SUCCESS
    # --------------------------------------

    if status == "success":

        response_text = data.get(
            "response"
        )

        if response_text:

            speak(response_text)

        else:

            speak(
                "Command completed successfully."
            )

        return


    # --------------------------------------
    # UNKNOWN
    # --------------------------------------

    speak(

        data.get(

            "response",

            "I don't know how to handle that response."

        )

    )


# ==========================================
# PROCESS COMMAND
# ==========================================

def process_command(command):

    command = command.lower().strip()


    # --------------------------------------
    # EMPTY COMMAND
    # --------------------------------------

    if not command:

        return True


    # --------------------------------------
    # EXIT
    # --------------------------------------

    if is_exit_command(command):

        speak(
            "Goodbye."
        )

        return False


    # --------------------------------------
    # SEND COMMAND
    # --------------------------------------

    speak(
        "Sure."
    )

    data = send_to_api(
        command
    )

    handle_response(
        data
    )

    return True


# ==========================================
# CONVERSATION MODE
# ==========================================

def conversation_mode():

    print(
        "\n💬 Conversation mode activated."
    )

    speak(
        "Yes?"
    )


    while True:

        # ----------------------------------
        # Listen for next command
        # ----------------------------------

        command = listen(

            timeout=CONVERSATION_TIMEOUT,

            phrase_time_limit=8

        )


        # ----------------------------------
        # Silence
        # ----------------------------------

        if not command:

            print(
                "\n💤 Conversation mode ended."
            )

            return True


        # ----------------------------------
        # Check if user said wake word
        # ----------------------------------

        wake_command = extract_command(
            command
        )


        if wake_command:

            command = wake_command


        # ----------------------------------
        # EXIT
        # ----------------------------------

        if is_exit_command(command):

            speak(
                "Goodbye."
            )

            return False


        # ----------------------------------
        # Process command
        # ----------------------------------

        should_continue = process_command(
            command
        )


        if not should_continue:

            return False


# ==========================================
# MAIN
# ==========================================

def main():

    print("\n")

    print(
        "========================================"
    )

    print(
        "        NOVA AI ASSISTANT"
    )

    print(
        "========================================"
    )

    print(
        "Voice assistant is starting..."
    )

    print(
        "Say 'Nova' followed by your command."
    )

    print(
        "After saying Nova, you can give"
    )

    print(
        "multiple commands without repeating it."
    )

    print(
        "Say 'Nova goodbye' to stop."
    )

    print(
        "========================================"
    )


    speak(
        "Nova is ready."
    )


    while True:

        # ----------------------------------
        # WAKE WORD MODE
        # ----------------------------------

        text = listen(
            timeout=5,
            phrase_time_limit=8
        )


        if not text:

            continue


        # ----------------------------------
        # Allow standalone goodbye
        # ----------------------------------

        if is_exit_command(text):

            speak(
                "Goodbye."
            )

            break


        # ----------------------------------
        # Extract wake command
        # ----------------------------------

        command = extract_command(
            text
        )


        # ----------------------------------
        # Wake word not detected
        # ----------------------------------

        if not command:

            print(
                "Wake word not detected."
            )

            continue


        print(
            f"\nNova command: {command}"
        )


        # ----------------------------------
        # Just saying "Nova"
        # ----------------------------------

        if not command:

            conversation_mode()

            continue


        # ----------------------------------
        # Process first command
        # ----------------------------------

        should_continue = process_command(
            command
        )


        if not should_continue:

            break


        # ----------------------------------
        # ENTER CONVERSATION MODE
        # ----------------------------------

        print(
            "\n💬 Entering conversation mode..."
        )


        continue_conversation = conversation_mode()


        if not continue_conversation:

            break


# ==========================================
# START
# ==========================================

if __name__ == "__main__":

    main()