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
import admin           
import tools           
import volume_ops     
import work_ops
import window_ops
import ai_ops         
import app_ops  # <--- Ensure app_ops.py is in the same folder
import voice_engine

# --- STATE ---
LAST_INTERACTION = 0
hand_mouse_process = None 

# --- VOICE ENGINE SETUP ---
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 230) 
    engine.setProperty('volume', 1.0)
except:
    engine = None

# --- OUTPUT HANDLERS ---
def gui_popup_hook(text):
    print(f"POPUP: {text}")

# --- NEW: STATS HOOK ---
def gui_stats_hook(data):
    """
    This function gets overridden by interface.py to show the bars.
    If running without interface, it just prints the data.
    """
    print(f"STATS: {data}")

def speak(text):
    voice_engine.speak(text)

def reply(text, user_command):
    """
    Shows text on the hologram AND speaks it.
    """
    gui_popup_hook(text) # Visual
    speak(text) 

def threaded_action(target_function, *args):
    """Runs a function in the background."""
    t = threading.Thread(target=target_function, args=args)
    t.daemon = True
    t.start()

# --- HAND MOUSE CONTROLLER ---
def toggle_hand_mouse():
    global hand_mouse_process
    
    PYTHON_311 = r"C:\Python311\python.exe"
    
    # DYNAMIC ABSOLUTE PATH (Fixes "File Not Found" errors)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    SCRIPT_PATH = os.path.join(current_dir, "hand_mouse_equator.py")
    
    if hand_mouse_process is None or hand_mouse_process.poll() is not None:
        print(f">> V.E.R.A.: Launching Vision System ({SCRIPT_PATH})...")
        try:
            hand_mouse_process = subprocess.Popen(
                [PYTHON_311, SCRIPT_PATH],
                cwd=current_dir, 
                creationflags=subprocess.CREATE_NEW_CONSOLE 
            )
            return "Vision systems online."
        except Exception as e:
            print(f"Error launching mouse: {e}")
            return "Vision system failure."
            
    else:
        print(">> V.E.R.A.: Deactivating Hand Mouse...")
        hand_mouse_process.terminate()
        hand_mouse_process = None
        return "Vision systems offline."

def process_command(command, source):
    global LAST_INTERACTION
    
    # ==========================================
    # TIER 1: REFLEXES (Instant & Threaded)
    # ==========================================
    
    # --- HAND MOUSE PRIORITY ---
    triggers = ["activate mouse", "hand mouse", "start camera", "hand camera", "gesture", "tracking"]
    
    if any(phrase in command for phrase in triggers):
        status = toggle_hand_mouse()
        speak(status)
        return

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

    elif "maximize" in command:
        target = command.replace("maximize", "").strip()
        window_ops.maximize_window(target)
        return
    
    elif "snap" in command:
        target = command.replace("snap", "").replace("left", "").replace("right", "").strip()
        direction = "right" if "right" in command else "left"
        window_ops.snap_window(target, direction)
        return

    # --- APP CONTROL (OPEN/CLOSE) ---
    elif "open" in command:
        target = command.replace("open", "").strip()
        if target:
            speak(f"Opening {target}...")
            threaded_action(app_ops.open_application, target)
        else:
            speak("Open what?")
        return

    elif "close" in command:
        target = command.replace("close", "").strip()
        if target:
            speak(f"Closing {target}...")
            app_ops.close_application(target)
        else:
            speak("Close what?")
        return
    # -------------------------------

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
    
    elif "exit" in command:
        speak("Good hunting.")
        os._exit(0)

    # ==========================================
    # TIER 2: SMART ROUTER (Groq Powered)
    # ==========================================
    
    intent = ai_ops.identify_intent(command)
    print(f"DEBUG: Intent identified as {intent}") 

    # --- NEW: SYSTEM STATS TRIGGER ---
    if "system status" in command or "stats" in command or "cpu" in command:
        # 1. Get Data
        data = admin.get_system_status()
        
        # 2. Show Visuals (Bars)
        gui_stats_hook(data)
        
        # 3. Speak the result
        speak(data['speech'])
        return

    elif intent == "CMD_SEE":
        speak("Analyzing screen...") 
        analysis = ai_ops.see_screen(command)
        reply(analysis, "read this") 

    elif intent == "CMD_CAM":
        speak("Visual sensors active.")
        analysis = ai_ops.see_camera(command)
        reply(analysis, "identify")

    elif intent == "CMD_TIME":
        now = datetime.datetime.now().strftime("%H:%M")
        reply(f"The time is {now}", command)

    elif intent == "CMD_CLEAN":
        threaded_action(skills.clean_downloads, lambda x: None)
        speak("Cleaning downloads.")

    elif intent == "CMD_TIMER":
        try:
            words = command.split()
            duration = 0
            unit = "seconds"
            for word in words:
                if word.isdigit():
                    duration = int(word)
                    break
            
            if "minute" in command: duration *= 60; unit = "minutes"
            elif "hour" in command: duration *= 3600; unit = "hours"

            if duration > 0:
                speak(f"Timer set.")
                skills.start_timer(duration, "Time is up", speak)
            else:
                speak("How long?")
        except:
            speak("Error.")

    elif intent == "CMD_MUSIC":
        clean_name = command.replace("play", "").replace("put on", "").strip()
        threaded_action(skills.play_music, clean_name)
        speak(f"Playing {clean_name}.")

    elif intent == "CMD_WORK":
        threaded_action(work_ops.open_profile, "coding")
        speak("Work mode.")

    elif intent == "CMD_GAME":
        threaded_action(work_ops.open_profile, "gaming")
        speak("Gaming mode.")

    elif intent == "CMD_CHAT" or intent == "UNKNOWN":
        response = ai_ops.ask_brain(command)
        reply(response, command)

# --- MAIN LOOP CONFIGURATION ---
recognizer = sr.Recognizer()
recognizer.pause_threshold = 0.8  
recognizer.non_speaking_duration = 0.5
recognizer.dynamic_energy_threshold = True 
recognizer.energy_threshold = 300 

def main():
    with sr.Microphone() as source:
        print(">> CALIBRATING MIC (Stay Silent)...")
        recognizer.adjust_for_ambient_noise(source, duration=1.0) 
        speak("V.E.R.A. online.")
        
        while True:
            try:
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                command = recognizer.recognize_google(audio, language='en-ZA').lower()
                print(f"User: {command}")
                process_command(command, source)
                
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"Error: {e}")
                continue

if __name__ == "__main__":
    main()