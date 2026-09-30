import sys
import time
import threading
import subprocess
import urllib.request
import tkinter as tk
from tkinter import messagebox

import uvicorn
import main


HOST = "127.0.0.1"
PORT = 8000
HEALTH_URL = f"http://{HOST}:{PORT}/health"


def start_api():

    try:

        config = uvicorn.Config(
            main.app,
            host=HOST,
            port=PORT,
            log_level="info"
        )

        server = uvicorn.Server(
            config
        )

        server.run()

    except Exception as e:

        print("API ERROR:")
        print(e)


def wait_for_api(timeout=15):

    start_time = time.time()

    while time.time() - start_time < timeout:

        try:

            with urllib.request.urlopen(
                HEALTH_URL,
                timeout=1
            ) as response:

                if response.status == 200:
                    return True

        except Exception:
            pass

        time.sleep(0.5)

    return False


def show_api_error():

    root = tk.Tk()
    root.withdraw()

    messagebox.showerror(
        "Nova API Error",
        "Nova's local API could not start.\n\n"
        "Please run Nova from PowerShell to see the error."
    )

    root.destroy()


def start_gui():

    import nova_gui

    if hasattr(nova_gui, "root"):

        nova_gui.root.mainloop()

    else:

        print(
            "Nova GUI could not be started."
        )


def main_launcher():

    # =====================================================
    # NORMAL PYTHON MODE
    # =====================================================

    if not getattr(
        sys,
        "frozen",
        False
    ):

        print(
            "Starting Nova API..."
        )

        api_thread = threading.Thread(
            target=start_api,
            daemon=True
        )

        api_thread.start()

        print(
            "Waiting for Nova API..."
        )

        if not wait_for_api():

            print(
                "ERROR: Nova API failed to start."
            )

            return

        print(
            "Nova API is running."
        )

        print(
            "Starting Nova GUI..."
        )

        start_gui()

        return

    # =====================================================
    # PYINSTALLER EXE MODE
    # =====================================================

    print(
        "Starting Nova API..."
    )

    api_thread = threading.Thread(
        target=start_api,
        daemon=True
    )

    api_thread.start()

    print(
        "Waiting for Nova API..."
    )

    if not wait_for_api():

        print(
            "ERROR: Nova API failed to start."
        )

        show_api_error()

        return

    print(
        "Nova API is running."
    )

    print(
        "Starting Nova GUI..."
    )

    start_gui()


if __name__ == "__main__":
    main_launcher()