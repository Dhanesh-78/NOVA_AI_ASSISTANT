import speech_recognition as sr
import pyttsx3
import requests


API_URL = "http://127.0.0.1:8000/smart-command"
CONFIRM_URL = "http://127.0.0.1:8000/confirm-command"


# ---------------------------------
# Text-to-Speech
# ---------------------------------

engine = pyttsx3.init()
engine.setProperty("rate", 170)


def speak(text):
    print(f"Nova: {text}")
    engine.say(text)
    engine.runAndWait()


# ---------------------------------
# Listen to microphone
# ---------------------------------

def listen():

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:

        print("\n🎤 Listening...")

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

        text = recognizer.recognize_google(audio)

        print(f"You: {text}")

        return text.lower().strip()

    except sr.UnknownValueError:

        print("Sorry, I couldn't understand you.")
        return ""

    except sr.RequestError:

        speak("Speech recognition is currently unavailable.")
        return ""


# ---------------------------------
# Extract command after wake word
# ---------------------------------

def extract_command(text):

    wake_words = [
        "nova",
        "hey nova",
        "okay nova",
        "ok nova"
    ]

    text = text.lower().strip()

    for wake_word in wake_words:

        if text.startswith(wake_word):

            command = text[len(wake_word):].strip()

            command = command.lstrip(",")

            return command.strip()

    return ""


# ---------------------------------
# Send command to Nova API
# ---------------------------------

def send_to_api(message):

    try:

        response = requests.post(
            API_URL,
            json={
                "message": message
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        print("\nAPI Response:")
        print(data)

        return data

    except requests.exceptions.Timeout:

        return {
            "status": "error",
            "message": "The Nova API took too long to respond."
        }

    except requests.exceptions.ConnectionError:

        return {
            "status": "error",
            "message": (
                "I couldn't connect to the Nova API. "
                "Please make sure FastAPI is running."
            )
        }

    except requests.exceptions.RequestException as e:

        print("API Error:", e)

        return {
            "status": "error",
            "message": "There was a problem communicating with Nova."
        }


# ---------------------------------
# Confirm dangerous command
# ---------------------------------

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

        return data.get(
            "response",
            "Command completed."
        )

    except requests.exceptions.Timeout:

        return "The confirmation request timed out."

    except requests.exceptions.ConnectionError:

        return "I couldn't connect to the Nova API."

    except requests.exceptions.RequestException as e:

        print("Confirmation error:", e)

        return "I couldn't execute the confirmed command."


# ---------------------------------
# Main Nova Loop
# ---------------------------------

def main():

    speak("Nova is ready.")

    while True:

        # -----------------------------
        # Listen
        # -----------------------------

        text = listen()

        if not text:

            continue


        # -----------------------------
        # Check wake word
        # -----------------------------

        command = extract_command(text)

        if not command:

            print("Wake word not detected.")

            continue


        print(f"Nova command: {command}")


        # -----------------------------
        # Exit
        # -----------------------------

        if command in [
            "exit",
            "quit",
            "stop",
            "goodbye"
        ]:

            speak("Goodbye.")
            break


        # -----------------------------
        # Send command to API
        # -----------------------------

        speak("Sure.")

        data = send_to_api(command)


        # -----------------------------
        # API ERROR
        # -----------------------------

        if data.get("status") == "error":

            speak(
                data.get(
                    "message",
                    "Something went wrong."
                )
            )

            continue


        # -----------------------------
        # UNKNOWN COMMAND
        # -----------------------------

        if data.get("status") == "unknown":

            speak(
                data.get(
                    "response",
                    "I don't know how to do that yet."
                )
            )

            continue


        # -----------------------------
        # CONFIRMATION REQUIRED
        # -----------------------------

        if data.get("status") == "confirmation_required":

            confirmation_message = data.get(
                "confirmation_message",
                "Do you want me to continue?"
            )

            speak(confirmation_message)


            # Listen for YES / NO
            answer = listen()


            # Remove wake word if the user says
            # "Nova yes" or "Hey Nova yes"
            if answer:

                answer = extract_command(answer)

                if not answer:

                    # If no wake word, use the original answer
                    answer = listen().strip()


            positive_answers = [
                "yes",
                "yeah",
                "yep",
                "sure",
                "okay",
                "ok",
                "do it",
                "continue"
            ]


            if answer in positive_answers:

                speak("Okay.")

                result = confirm_command(
                    data["action"],
                    data.get("query", "")
                )

                speak(result)

            else:

                speak(
                    "Okay, I cancelled the command."
                )

            continue


        # -----------------------------
        # NORMAL SUCCESS
        # -----------------------------

        speak(
            data.get(
                "response",
                "Command completed successfully."
            )
        )


# ---------------------------------
# Start program
# ---------------------------------

if __name__ == "__main__":
    main()