import speech_recognition as sr
import sys
import os
import time
import threading
import subprocess
import pyttsx3
import datetime

# --- IMPORTS ---
import skills
import security_ops
import admin
import tools
import volume_ops
import work_ops
import window_ops
import ai_ops
import app_ops
import voice_engine

# --- STATE ---
LAST_INTERACTION = 0
hand_mouse_process = None


# --- OUTPUT HANDLERS ---
def gui_popup_hook(text):
    print(f"POPUP: {text}")


def gui_stats_hook(data):
    print(f"STATS: {data}")


# Placeholder hook that interface.py will override
def gui_cam_hook():
    return None


def speak(text):
    voice_engine.speak(text)


def reply(text, user_command):
    gui_popup_hook(text)
    speak(text)


def threaded_action(target_function, *args):
    t = threading.Thread(target=target_function, args=args)
    t.daemon = True
    t.start()


# --- HAND MOUSE CONTROLLER ---
def toggle_hand_mouse():
    global hand_mouse_process

    # 1. Check if it's already running
    if hand_mouse_process and hand_mouse_process.poll() is None:
        hand_mouse_process.terminate()
        hand_mouse_process = None
        speak("Vision systems offline.")
        return

    # 2. Define the path dynamically
    # sys.executable ensures we use the SAME venv that is running main.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "hand_mouse_equator.py")

    speak("Engaging optical sensors.")

    try:
        # 3. Launch the process
        # subprocess.CREATE_NEW_CONSOLE makes it pop up in its own cool window
        hand_mouse_process = subprocess.Popen(
            [sys.executable, script_path],
            cwd=current_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    except Exception as e:
        print(f"VISION LAUNCH ERROR: {e}")
        speak("Optical sensors failed to initialize.")


def process_command(command, source):
    global LAST_INTERACTION

    # --- HAND MOUSE PRIORITY ---
    triggers = [
        "activate mouse",
        "hand mouse",
        "start camera",
        "hand camera",
        "gesture",
        "tracking",
    ]
    if any(phrase in command for phrase in triggers):
        status = toggle_hand_mouse()
        if status:
            speak(status)
        return

    # --- MEDIA CONTROLS ---
    elif "stop" in command or "pause" in command or "resume" in command:
        skills.media_play_pause()
        return
    elif "next song" in command or "skip" in command:
        skills.media_next()
        return
    elif "previous song" in command or "go back" in command:
        skills.media_prev()
        return
    elif "volume" in command or "mute" in command:
        volume_ops.handle_volume_command(command, speak)
        return

    # --- SPECIFIC CAMERA CONTROLS ---
    elif "close camera" in command or "stop vision" in command:
        if hand_mouse_process:
            speak("Deactivating vision systems.")
            toggle_hand_mouse()  # This toggles it OFF
        else:
            speak("Camera is not active.")
        return

    elif "minimize camera" in command or "hide camera" in command:
        # The window title is set in hand_mouse_equator.py as "V.E.R.A. Vision V9"
        found = window_ops.minimize_window("V.E.R.A. Vision V9")
        if found:
            speak("Minimizing vision feed.")
        else:
            speak("I can't find the camera window.")
        return

    # --- WINDOW MANAGEMENT ---
    elif "maximize" in command:
        target = command.replace("maximize", "").strip()
        window_ops.maximize_window(target)
        return
    elif "snap" in command:
        target = (
            command.replace("snap", "").replace("left", "").replace("right", "").strip()
        )
        direction = "right" if "right" in command else "left"
        window_ops.snap_window(target, direction)
        return

    # --- APP CONTROL ---
    elif "open" in command:
        target = command.replace("open", "").strip()
        if target:
            speak(f"Opening {target}...")
            threaded_action(app_ops.open_application, target)
        return
    elif "close" in command:
        target = command.replace("close", "").strip()
        if target:
            speak(f"Closing {target}...")
            app_ops.close_application(target)
        return

    # --- UTILITIES ---
    elif "screenshot" in command:
        threaded_action(skills.take_screenshot)
        speak("Saved.")
        return
    elif "read clipboard" in command:
        threaded_action(skills.read_clipboard, speak)
        return
    elif "note" in command:
        text = command.split("note", 1)[1].strip() if "note" in command else ""
        if text:
            skills.save_note(text)
            speak("Saved.")
        return
    elif "sentry mode" in command or "trap" in command:
        security_ops.engage_sentry_mode(speak)
        return
    elif "exit" in command:
        speak("Goodbye Sir.")

        if hand_mouse_process:
            try:
                hand_mouse_process.terminate()
            except:
                pass

        os._exit(0)

    # --- SMART ROUTER ---
    intent = ai_ops.identify_intent(command)

    if "system status" in command or "stats" in command:
        data = admin.get_system_status()
        gui_stats_hook(data)
        speak(data["speech"])
        return
    elif intent == "CMD_SEE":
        speak("Analyzing screen...")
        analysis = ai_ops.see_screen(command)
        reply(analysis, command)
    elif intent == "CMD_CAM":
        speak("Visual sensors active.")
        analysis = ai_ops.see_camera(command)
        reply(analysis, command)
    elif intent == "CMD_TIME":
        now = datetime.datetime.now().strftime("%H:%M")
        reply(f"The time is {now}", command)
    elif intent == "CMD_MUSIC":
        clean_name = command.replace("play", "").replace("put on", "").strip()
        threaded_action(skills.play_music, clean_name)
        speak(f"Playing {clean_name}.")
    elif intent == "CMD_CHAT" or intent == "UNKNOWN":
        response = ai_ops.ask_brain(command)
        reply(response, command)


# --- MAIN LOOP ---
recognizer = sr.Recognizer()
recognizer.pause_threshold = 0.8


def main():
    with sr.Microphone() as source:
        print(">> CALIBRATING MIC...")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        speak("V.E.R.A. online.")
        while True:
            try:
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                command = recognizer.recognize_google(audio, language="en-ZA").lower()
                process_command(command, source)
            except:
                continue


if __name__ == "__main__":
    main()
