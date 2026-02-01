import asyncio
import edge_tts
import os
import pygame
import ai_ops
import datetime
import psutil
import threading
import sounddevice as sd
import numpy as np
import time

# --- HOOKS ---
gui_popup_hook = None
gui_stats_hook = None
toggle_hand_mouse = None
shutdown_hook = None


class VeraState:
    is_speaking = False


state = VeraState()
VOICE = "en-US-AriaNeural"
OUTPUT_FILE = "speech.mp3"


# --- BARGE-IN MONITOR (SUSTAINED) ---
def listen_for_interrupt():
    """Sniffs the mic. Only stops if noise persists for > 0.7 seconds."""

    # Wait 1.0s so she doesn't hear her own startup "pop"
    time.sleep(1.0)

    # We use a list to store the start time so the inner function can edit it
    noise_start = [None]

    def audio_callback(indata, frames, time_info, status):
        if not state.is_speaking:
            return

        volume_norm = np.linalg.norm(indata) * 10
        THRESHOLD = 45
        SUSTAIN_DURATION = 0.7  # <--- Adjust this! 1.0 is very strict, 0.5 is snappy.

        if volume_norm > THRESHOLD:
            # Noise is happening.
            if noise_start[0] is None:
                # Start the timer
                noise_start[0] = time.time()
            else:
                # Check how long it's been
                elapsed = time.time() - noise_start[0]
                if elapsed > SUSTAIN_DURATION:
                    print(f"DEBUG: Interrupt! (Sustained for {elapsed:.2f}s)")
                    pygame.mixer.music.stop()
                    state.is_speaking = False
        else:
            # Silence returned. Reset the timer.
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

    # PHONETIC NAME REPLACEMENT
    clean_text = text.replace("V.E.R.A.", "Vera").replace("VERA", "Vera")

    print(f"VERA: {clean_text}")
    if gui_popup_hook:
        try:
            gui_popup_hook(clean_text)
        except:
            pass

    try:
        # 1. Generate the audio
        communicate = edge_tts.Communicate(clean_text, VOICE)
        asyncio.run(communicate.save(OUTPUT_FILE))

        # 2. Initialize Mixer
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # 3. Play
        pygame.mixer.music.load(OUTPUT_FILE)
        pygame.mixer.music.play()

        state.is_speaking = True

        # Start the "ear" thread
        threading.Thread(target=listen_for_interrupt, daemon=True).start()

        # Keep the thread alive while she talks
        while pygame.mixer.music.get_busy() and state.is_speaking:
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        state.is_speaking = False

    except Exception as e:
        print(f"Audio Error: {e}")
        state.is_speaking = False


# --- Standard Helpers ---


def get_time():
    return datetime.datetime.now().strftime("It's %H:%M.")


def get_system_stats():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    percent = battery.percent if battery else 100
    return {"cpu": cpu, "ram": ram, "battery": percent}


# --- ADD THESE IMPORTS ---
import webbrowser
import subprocess


# --- UPDATE PROCESS_COMMAND ---
def process_command(command, source=None):
    if not command:
        return

    # SHUTDOWN LOGIC
    if any(word in command for word in ["shutdown", "terminate", "exit program"]):
        speak("Shutting down. Goodbye.")
        if shutdown_hook:
            threading.Timer(2.0, shutdown_hook).start()
        return

    # 1. IDENTIFY
    intent = ai_ops.identify_intent(command)
    print(f"DEBUG: Intent = {intent}")

    try:
        if intent == "CMD_OPEN":
            speak("On it.")
            # 2. EXTRACT TARGET
            target_data = ai_ops.extract_open_intent(command)

            if target_data:
                if target_data["type"] == "web":
                    speak(f"Opening {target_data['target']}")
                    webbrowser.open(target_data["target"])

                elif target_data["type"] == "app":
                    speak(f"Launching {target_data['target']}")
                    # Try to run it as a command (works for 'code', 'notepad', 'calc', 'explorer')
                    try:
                        subprocess.Popen(target_data["target"], shell=True)
                    except:
                        speak(f"I couldn't find an app named {target_data['target']}")
            else:
                speak("I'm not sure what you want me to open.")

        elif intent == "CMD_SEE":
            speak("Checking screen.")
            response = ai_ops.see_screen(command)
            speak(response)

        elif intent == "CMD_CAM":
            speak("Checking camera.")
            response = ai_ops.see_camera(command)
            speak(response)

        elif intent == "CMD_TIME":
            speak(get_time())

        elif intent == "CHAT_DEEP":
            speak("Let me think...")
            response = ai_ops.ask_brain(command, use_smart_model=True)
            speak(response)

        else:
            # CHAT_FAST
            response = ai_ops.ask_brain(command, use_smart_model=False)
            speak(response)

    except Exception as e:
        print(f"Logic Error: {e}")
        speak("I had a glitch.")
