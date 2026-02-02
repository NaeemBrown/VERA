import asyncio
import edge_tts
import os
import pygame
import datetime
import psutil
import threading
import sounddevice as sd
import numpy as np
import time
import webbrowser
import subprocess
import pyautogui
from fuzzywuzzy import process

# --- LOCAL MODULES ---
# We import these directly because 'core' is now in the system path
import ai_ops
import voice_lock

# --- PATH SETUP ---
# Get the root VERA folder (Up one level from core)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
OUTPUT_FILE = os.path.join(ROOT_DIR, "assets", "speech.mp3")

# --- CONFIG ---
VOICE = "en-US-AriaNeural"

# --- HOOKS ---
gui_popup_hook = None
gui_stats_hook = None
toggle_hand_mouse = None
shutdown_hook = None


class VeraState:
    is_speaking = False


state = VeraState()


# --- AUDIO SYSTEMS ---
def listen_for_interrupt():
    """Stops speaking if the user interrupts (talks over VERA)."""
    time.sleep(1.0)
    noise_start = [None]

    def audio_callback(indata, frames, time_info, status):
        if not state.is_speaking:
            return
        # Check volume level
        volume_norm = np.linalg.norm(indata) * 10
        if volume_norm > 45:  # Sensitivity threshold
            if noise_start[0] is None:
                noise_start[0] = time.time()
            elif time.time() - noise_start[0] > 0.7:
                print("DEBUG: Interrupt detected! Stopping audio.")
                pygame.mixer.music.stop()
                state.is_speaking = False
        else:
            noise_start[0] = None

    try:
        with sd.InputStream(callback=audio_callback):
            while state.is_speaking:
                sd.sleep(100)
    except:
        pass


def speak(text):
    if not text:
        return

    # Pronunciation Fixes
    clean_text = text.replace("V.E.R.A.", "Vera").replace("VERA", "Vera")
    print(f"VERA: {clean_text}")

    # Send text to GUI
    if gui_popup_hook:
        try:
            gui_popup_hook(clean_text)
        except:
            pass

    try:
        # Generate Audio
        communicate = edge_tts.Communicate(clean_text, VOICE)
        asyncio.run(communicate.save(OUTPUT_FILE))

        # Play Audio
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(OUTPUT_FILE)
        pygame.mixer.music.play()

        state.is_speaking = True
        # Start looking for interruptions in a background thread
        threading.Thread(target=listen_for_interrupt, daemon=True).start()

        # Wait for audio to finish
        while pygame.mixer.music.get_busy() and state.is_speaking:
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        state.is_speaking = False

    except Exception as e:
        print(f"Audio Error: {e}")
        state.is_speaking = False


# --- UTILS ---
def get_system_stats():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    percent = battery.percent if battery else 100
    return {"cpu": cpu, "ram": ram, "battery": percent}


def get_time():
    return datetime.datetime.now().strftime("It's %H:%M.")


# --- BRAIN ---
def process_command(command, audio_data=None, source=None):
    if not command:
        return

    # 1. AUTO-CORRECT (The Dictionary)
    COMMAND_MAP = {
        "app": "scan for apps",
        "scan": "scan for apps",
        "app scan": "scan for apps",
        "apps": "scan for apps",
        "update": "scan for apps",
        "shutdown": "shutdown",
        "stop": "shutdown",
        "exit": "shutdown",
    }

    if command in COMMAND_MAP:
        print(f"DEBUG: Auto-Correcting '{command}' -> '{COMMAND_MAP[command]}'")
        command = COMMAND_MAP[command]

    # 2. GLOBAL COMMANDS
    if "shutdown" in command:
        speak("Shutting down. Goodbye.")
        if shutdown_hook:
            threading.Timer(2.0, shutdown_hook).start()
        return

    # 3. IDENTIFY INTENT
    intent = ai_ops.identify_intent(command)
    print(f"DEBUG: Intent = {intent}")

    # 4. SECURITY CHECK
    if intent in ["CMD_OPEN", "CMD_TYPE", "CMD_SCAN"]:
        if audio_data:
            print("DEBUG: Checking Voice ID...")
            if not voice_lock.security_system.verify_audio(audio_data):
                speak("Voice authorization failed.")
                return
        else:
            print("WARNING: No audio data available for security check.")

    try:
        # --- ROUTING ---
        if "scan" in command:
            speak("Scanning system for apps...")
            count = ai_ops.update_app_library()
            speak(f"Done. Found {count} apps.")

        elif intent == "CMD_OPEN":
            target = ai_ops.extract_open_intent(command)
            if target:
                speak("On it.")
                if target["type"] == "web":
                    webbrowser.open(target["target"])
                elif target["type"] == "app":
                    app_cmd = target["target"].lower().strip()
                    SAFE_APPS = ["notepad", "calc", "code", "spotify", "explorer"]
                    if app_cmd in SAFE_APPS:
                        subprocess.Popen(app_cmd, shell=True)
                    else:
                        path = ai_ops.find_installed_app(app_cmd)
                        if path:
                            os.startfile(path)
                        else:
                            speak(f"I couldn't find {app_cmd}.")
            else:
                speak("I'm not sure what to open.")

        elif intent == "CMD_TYPE":
            text = ai_ops.extract_type_intent(command)
            if text:
                speak("Typing.")
                time.sleep(0.5)
                pyautogui.write(text, interval=0.05)
            else:
                speak("I'm not sure what to type.")

        elif intent == "CMD_SEE":
            speak("Checking screen.")
            speak(ai_ops.see_screen(command))

        elif intent == "CMD_CAM":
            speak("Checking camera.")
            speak(ai_ops.see_camera(command))

        elif intent == "CMD_TIME":
            speak(get_time())

        elif "status" in command:
            stats = get_system_stats()
            if gui_stats_hook:
                gui_stats_hook(stats)
            speak(f"Systems green. CPU {stats['cpu']}%.")

        elif intent == "CHAT_DEEP":
            speak("Let me think...")
            speak(ai_ops.ask_brain(command, use_smart_model=True))

        else:
            speak(ai_ops.ask_brain(command, use_smart_model=False))

    except Exception as e:
        print(f"Error: {e}")
        speak("I had a glitch.")
