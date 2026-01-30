import os
from dotenv import load_dotenv
from groq import Groq
import google.generativeai as genai
import threading
from PIL import ImageGrab
import cv2 
import time
from PIL import Image

# --- CONFIGURATION ---
# 1. LOAD SECRETS (The safe way)
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

# 2. MODEL SETTINGS
GROQ_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "gemini-2.0-flash" 

# --- THE PERSONALITY ---
SYSTEM_INSTRUCTION = (
    "You are V.E.R.A. (Virtual Electronic Remote Assistant). "
    "You are a highly advanced, efficient, and polite AI assistant. "
    "Your tone is professional, slightly dry, and British. "
    "Do not use slang. Provide answers immediately without fluff. "
    "If the user asks for code, provide only the code and a one-sentence explanation."
)

# Initialize safely
groq_client = None
google_model = None
BRAIN_ACTIVE = False
VISION_ACTIVE = False

conversation_history = [
    {"role": "system", "content": SYSTEM_INSTRUCTION}
]

def _connect_brains():
    """Connects both Groq (Speed) and Google (Vision) in background."""
    global groq_client, google_model, BRAIN_ACTIVE, VISION_ACTIVE
    
    # 1. Connect Groq
    try:
        if GROQ_API_KEY:
            print("DEBUG: Connecting to Groq...")
            groq_client = Groq(api_key=GROQ_API_KEY)
            groq_client.chat.completions.create(
                messages=[{"role": "user", "content": "Ping"}],
                model=GROQ_MODEL
            )
            BRAIN_ACTIVE = True
            print("DEBUG: Groq Online (Speed Brain).")
        else:
            print("DEBUG: Groq Key missing in .env")
    except Exception as e:
        print(f"Groq Error: {e}")

    # 2. Connect Google Vision
    try:
        if GOOGLE_API_KEY:
            print("DEBUG: Connecting to Vision...")
            genai.configure(api_key=GOOGLE_API_KEY)
            google_model = genai.GenerativeModel(VISION_MODEL)
            VISION_ACTIVE = True
            print("DEBUG: Vision Online (Eye Connected).")
        else:
            print("DEBUG: Google Key missing in .env")
    except Exception as e:
        print(f"Vision Error: {e}")

# --- AUTO-START ---
bg_thread = threading.Thread(target=_connect_brains)
bg_thread.daemon = True
bg_thread.start()

def identify_intent(user_command):
    if not BRAIN_ACTIVE: return "UNKNOWN"

    prompt = f"""
    Classify the user command into one of these EXACT codes:
    
    - CMD_SEE   (User wants you to look/read screen. E.g. "What is this?", "Read this error", "Look at screen")
    - CMD_CAM   (User wants you to use the CAMERA/WEBCAM to look at a physical object. E.g. "What is this?", "Look at what I'm holding", "Identify this")
    - CMD_TIME  (User asks for current time/clock. E.g. "What time is it?")
    - CMD_TIMER (User wants to set a countdown/alarm. E.g. "Set timer", "Remind me in 5m")
    - CMD_CLEAN (Organize files/downloads)
    - CMD_MUSIC (Play songs)
    - CMD_WORK  (Work mode)
    - CMD_GAME  (Gaming mode)
    - CMD_CHAT  (General questions)

    User Command: "{user_command}"
    
    Return ONLY the code.
    """
    
    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
            temperature=0, 
            max_tokens=10
        )
        return completion.choices[0].message.content.strip()
    except:
        return "UNKNOWN"

def ask_brain(user_text):
    global conversation_history
    if not BRAIN_ACTIVE: return "Systems still initializing."
        
    try:
        conversation_history.append({"role": "user", "content": user_text})
        
        if len(conversation_history) > 10:
            conversation_history = [conversation_history[0]] + conversation_history[-9:]

        completion = groq_client.chat.completions.create(
            messages=conversation_history,
            model=GROQ_MODEL,
            temperature=0.7,
            max_tokens=200
        )
        
        response_text = completion.choices[0].message.content.strip()
        conversation_history.append({"role": "assistant", "content": response_text})
        
        return response_text.replace("*", "").replace("#", "")
        
    except Exception as e:
        print(f"Groq Fail: {e}")
        return "I hit a snag processing that."

def see_screen(user_prompt):
    if not VISION_ACTIVE: return "My vision sensors are offline."
    
    try:
        print("DEBUG: Capturing screen for analysis...")
        screenshot = ImageGrab.grab()
        
        if len(user_prompt) < 5: 
            user_prompt = "What am I looking at? Be concise and helpful."
        
        final_prompt = user_prompt + ". Answer casually in 1-2 sentences."
        response = google_model.generate_content([final_prompt, screenshot])
        return response.text.replace("*", "")
    except Exception as e:
        print(f"Vision Fail: {e}")
        return "I couldn't analyze the screen."
    
def see_camera(user_prompt):
    if not VISION_ACTIVE: return "Vision sensors offline."
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "I cannot access the camera."
    
    print("DEBUG: Camera warming up...")
    for _ in range(15):
        cap.read()
        
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return "Failed to capture image."
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_frame)
    
    try:
        print("DEBUG: Sending photo to V.E.R.A. Vision...")
        if len(user_prompt) < 5: 
            user_prompt = "Identify this object casually."
            
        final_prompt = user_prompt + " Answer in 1 short sentence. Be definitive."
        response = google_model.generate_content([final_prompt, pil_img])
        return response.text.replace("*", "")
    except Exception as e:
        print(f"Vision Error: {e}")
        return "I couldn't identify that."