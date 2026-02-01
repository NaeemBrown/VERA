import asyncio
import edge_tts
import pygame
import os
import sys
import ai_ops
import datetime
import psutil
import threading

# Hooks for the UI
gui_popup_hook = None
gui_stats_hook = None
toggle_hand_mouse = None

# --- AUDIO SYSTEM ---
VOICE = "en-GB-SoniaNeural"
OUTPUT_FILE = "speech.mp3"


def speak(text):
    """Generates and plays audio."""
    if not text:
        return
    print(f"VERA: {text}")  # Debug print

    # 1. Update UI (If connected)
    if gui_popup_hook:
        try:
            gui_popup_hook(text)
        except Exception as e:
            print(f"UI Hook Error: {e}")

    # 2. Generate Audio
    try:
        communicate = edge_tts.Communicate(text, VOICE, rate="+15%")
        asyncio.run(communicate.save(OUTPUT_FILE))

        pygame.mixer.init()
        pygame.mixer.music.load(OUTPUT_FILE)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()
    except Exception as e:
        print(f"Audio Error: {e}")


def get_time():
    now = datetime.datetime.now()
    return now.strftime("It is %H:%M.")


def get_system_stats():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    plugged = "Plugged In" if battery and battery.power_plugged else "Battery"
    percent = battery.percent if battery else 100
    return {"cpu": cpu, "ram": ram, "battery": percent}


def process_command(command, source=None):
    """The Central Logic Hub"""
    if not command:
        return

    # 1. IDENTIFY INTENT
    intent = ai_ops.identify_intent(command)
    print(f"DEBUG: Intent = {intent}")

    response = ""

    # 2. EXECUTE
    try:
        if intent == "CMD_SEE":
            speak("Analyzing visual data...")
            response = ai_ops.see_screen(command)

        elif intent == "CMD_CAM":
            speak("Accessing optical sensors...")
            response = ai_ops.see_camera(command)

        elif intent == "CMD_TIME":
            response = get_time()

        elif intent == "CMD_MUSIC":
            speak("I do not have a music module installed yet.")
            return

        elif "hand mouse" in command or "vision" in command:
            if toggle_hand_mouse:
                status = toggle_hand_mouse()
                return

        elif "system" in command or "status" in command:
            stats = get_system_stats()
            if gui_stats_hook:
                gui_stats_hook(stats)
            response = f"CPU at {stats['cpu']} percent. RAM at {stats['ram']} percent."

        else:
            # Default: Chat
            response = ai_ops.ask_brain(command)

        # 3. RESPOND
        speak(response)

    except Exception as e:
        print(f"Logic Error: {e}")
        speak("I encountered an internal error.")
