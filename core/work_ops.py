import time
import webbrowser
import os
import subprocess
import threading

# --- LOCAL IMPORTS ---
# We need these to find apps and snap windows
try:
    import window_ops
    import ai_ops
except ImportError:
    # Fallback for direct testing
    import sys

    sys.path.append(os.path.dirname(__file__))
    import window_ops
    import ai_ops


def work_mode_init(speak_func):
    """
    The 'Getting Things Done' Protocol:
    1. Opens VS Code & Chrome.
    2. Snaps VS Code to the Left (Code).
    3. Snaps Chrome to the Right (Research).
    """
    speak_func("Initializing Workspace Protocol...")

    # 1. LAUNCH VS CODE
    # Try finding it via the smart library first
    code_path = ai_ops.find_installed_app("visual studio code")
    if not code_path:
        code_path = ai_ops.find_installed_app("code")

    if code_path:
        os.startfile(code_path)
    else:
        # Fallback: Assume it's in the system PATH
        try:
            subprocess.Popen("code", shell=True)
        except:
            speak_func("I couldn't find VS Code.")

    # 2. LAUNCH BROWSER
    webbrowser.open("https://google.com")

    # 3. WAIT FOR WINDOWS (Crucial)
    # Windows take time to render. We give them 4 seconds.
    time.sleep(4)

    # 4. ARRANGE (The Magic)
    # We try multiple names because window titles change
    snapped_code = False
    if window_ops.snap_window("Visual Studio Code", side="left"):
        snapped_code = True
    elif window_ops.snap_window("Code", side="left"):
        snapped_code = True

    snapped_chrome = False
    if window_ops.snap_window("Google Chrome", side="right"):
        snapped_chrome = True
    elif window_ops.snap_window("Chrome", side="right"):
        snapped_chrome = True

    # 5. REPORT
    if snapped_code and snapped_chrome:
        speak_func("Workspace ready. Good luck.")
    else:
        speak_func("Apps opened, but I couldn't snap the windows perfectly.")


def study_mode_init(speak_func):
    """
    Example of a second mode:
    1. Opens YouTube Music (Chill)
    2. Opens Notepad (Notes)
    """
    speak_func("Study mode engaged.")

    webbrowser.open("https://music.youtube.com")
    subprocess.Popen("notepad")

    time.sleep(3)

    window_ops.snap_window("Notepad", side="right")
    window_ops.snap_window("Music", side="left")
