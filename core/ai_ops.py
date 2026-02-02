import os
import json
from dotenv import load_dotenv
from groq import Groq
import google.generativeai as genai
import threading
from PIL import ImageGrab, Image
import cv2
from fuzzywuzzy import process

# --- PATH SETUP ---
# Calculate paths relative to this file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")

# Load environment variables from Root
load_dotenv(os.path.join(ROOT_DIR, ".env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

# --- CONFIGURATION ---
MODEL_FAST = "llama-3.1-8b-instant"  # Speed (0.5s)
MODEL_SMART = "llama-3.3-70b-versatile"  # Intelligence (2.0s)
VISION_MODEL = "gemini-2.0-flash-exp"

# Safe Autofill Data
USER_DATA = {
    "email": "naeem@example.com",
    "username": "NaeemDev",
    "address": "Cape Town, SA",
}

SYSTEM_INSTRUCTION = (
    "Your name is Vera. "
    "1. IDENTITY: Never spell your name as an acronym. "
    "2. PERSONALITY: Be casual, slightly sarcastic, and confident. "
    "3. BREVITY: Keep responses punchy (under 3 sentences) unless asked for code."
)

# --- FILE PATHS ---
MEMORY_FILE = os.path.join(DATA_DIR, "vera_memory.json")
APP_LIBRARY_FILE = os.path.join(DATA_DIR, "app_library.json")


# --- MEMORY SYSTEM ---
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"history": [{"role": "system", "content": SYSTEM_INSTRUCTION}]}
    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            # Ensure System Instruction is always up to date
            if data["history"][0]["role"] == "system":
                data["history"][0]["content"] = SYSTEM_INSTRUCTION
            return data
    except:
        return {"history": [{"role": "system", "content": SYSTEM_INSTRUCTION}]}


def save_memory(data):
    try:
        # Keep context window manageable (Last 20 turns)
        if len(data["history"]) > 21:
            data["history"] = [data["history"][0]] + data["history"][-20:]
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Memory Error: {e}")


# Initialize Globals
groq_client = None
google_model = None
memory = load_memory()
conversation_history = memory["history"]


# --- CONNECTION ---
def _connect_brains():
    global groq_client, google_model
    try:
        if GROQ_API_KEY:
            groq_client = Groq(api_key=GROQ_API_KEY)
            print("DEBUG: Brain connected.")
    except:
        pass
    try:
        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            google_model = genai.GenerativeModel(VISION_MODEL)
            print("DEBUG: Eyes connected.")
    except:
        pass


# Connect in background to avoid startup lag
bg_thread = threading.Thread(target=_connect_brains, daemon=True)
bg_thread.start()


# --- APP SEARCH ENGINE ---
def update_app_library():
    """Scans Windows Start Menu for shortcuts."""
    print("DEBUG: Starting App Scan...")
    paths = [
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"),
    ]

    app_map = {}
    for path in paths:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".lnk"):
                    clean_name = (
                        file.lower().replace(".lnk", "").replace("shortcut", "").strip()
                    )
                    full_path = os.path.join(root, file)
                    app_map[clean_name] = full_path

    try:
        with open(APP_LIBRARY_FILE, "w") as f:
            json.dump(app_map, f, indent=2)
        return len(app_map)
    except Exception as e:
        print(f"Error saving library: {e}")
        return 0


def find_installed_app(app_name):
    """Fuzzy search for an app in the library."""
    if not os.path.exists(APP_LIBRARY_FILE):
        return None

    try:
        with open(APP_LIBRARY_FILE, "r") as f:
            app_map = json.load(f)
    except:
        return None

    # Fuzzy Match (e.g., "code" -> "visual studio code")
    match, score = process.extractOne(app_name.lower(), list(app_map.keys()))

    if score > 75:
        print(f"DEBUG: Found {match} ({score}%)")
        return app_map[match]

    return None


# --- ROUTER (CLASSIFIER) ---
def identify_intent(user_command):
    if not groq_client:
        return "CHAT_FAST"

    prompt = f"""
    Analyze: "{user_command}"
    Classify into ONE code:
    - CMD_OPEN: Open apps, websites, media.
    - CMD_TYPE: Type text, emails, autofill.
    - CMD_SEE: Look at screen.
    - CMD_CAM: Check webcam.
    - CMD_TIME: Ask for time.
    - CHAT_DEEP: Coding, complex logic.
    - CHAT_FAST: Greetings, simple status.
    Return ONLY the code.
    """
    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_FAST,
            temperature=0,
            max_tokens=10,
        )
        return completion.choices[0].message.content.strip()
    except:
        return "CHAT_FAST"


def extract_open_intent(user_command):
    if not groq_client:
        return None

    prompt = f"""
    Extract target from: "{user_command}"
    JSON Format: {{ "type": "web" | "app", "target": "URL_OR_APP_NAME" }}
    Examples:
    - "Open Google" -> {{ "type": "web", "target": "https://google.com" }}
    - "Launch Blender" -> {{ "type": "app", "target": "blender" }}
    """
    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_FAST,
            temperature=0,
            max_tokens=100,
        )
        clean_json = (
            completion.choices[0]
            .message.content.replace("```json", "")
            .replace("```", "")
            .strip()
        )
        return json.loads(clean_json)
    except:
        return None


def extract_type_intent(user_command):
    if not groq_client:
        return None

    lower_cmd = user_command.lower()
    # Fast Local Matches
    if "email" in lower_cmd:
        return USER_DATA["email"]
    if "username" in lower_cmd:
        return USER_DATA["username"]

    # AI Extraction
    prompt = f"""User said: "{user_command}". Extract ONLY the text to type."""
    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_FAST,
            temperature=0,
            max_tokens=50,
        )
        return completion.choices[0].message.content.strip()
    except:
        return None


# --- CHAT ENGINE ---
def ask_brain(user_text, use_smart_model=False):
    global conversation_history
    if not groq_client:
        return "Brain offline."

    selected_model = MODEL_SMART if use_smart_model else MODEL_FAST
    print(f"DEBUG: Using {selected_model}")

    try:
        conversation_history.append({"role": "user", "content": user_text})

        completion = groq_client.chat.completions.create(
            messages=conversation_history,
            model=selected_model,
            temperature=0.7,
            max_tokens=400 if use_smart_model else 150,
        )

        response_text = completion.choices[0].message.content.strip()
        conversation_history.append({"role": "assistant", "content": response_text})
        save_memory({"history": conversation_history})

        return response_text
    except Exception as e:
        return f"I had a brain fart: {e}"


# --- VISION ENGINE ---
def see_screen(user_prompt):
    if not google_model:
        return "Vision offline."
    try:
        screenshot = ImageGrab.grab()
        screenshot.thumbnail((1024, 1024))
        if len(user_prompt) < 5:
            user_prompt = "What's on my screen? Be brief."
        response = google_model.generate_content([user_prompt, screenshot])
        return response.text
    except:
        return "I can't see right now."


def see_camera(user_prompt):
    if not google_model:
        return "Camera offline."
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "Camera broken."

    # Warmup
    for _ in range(5):
        cap.read()
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return "Camera error."

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    img.thumbnail((1024, 1024))

    if len(user_prompt) < 5:
        user_prompt = "What is this? Be brief."
    try:
        response = google_model.generate_content([user_prompt, img])
        return response.text
    except:
        return "Identification failed."
