import os
import json
import threading
import webbrowser
import subprocess
import time
import pyautogui
from dotenv import load_dotenv
from groq import Groq
import google.generativeai as genai
from PIL import ImageGrab, Image
import cv2
from fuzzywuzzy import process

# --- PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
APP_LIBRARY_FILE = os.path.join(DATA_DIR, "app_library.json")
MEMORY_FILE = os.path.join(DATA_DIR, "vera_memory.json")
FACTS_FILE = os.path.join(DATA_DIR, "vera_facts.json")

# Load environment variables
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

# --- SYSTEM INSTRUCTION (FIXED) ---
SYSTEM_INSTRUCTION = (
    "Your name is Vera. "
    "1. IDENTITY: Never spell your name as an acronym. "
    "2. PERSONALITY: Be casual, slightly sarcastic, and confident. "
    "3. BREVITY: Keep responses punchy (under 3 sentences) unless asked for code. "
    "4. VISUALS: If a diagram helps explain a complex topic, insert a tag like ."
)

# --- GLOBALS ---
groq_client = None
google_model = None


# --- MEMORY SYSTEM (SHORT TERM) ---
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return [{"role": "system", "content": SYSTEM_INSTRUCTION}]
    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            # Ensure System Instruction is always up to date
            if data and data[0]["role"] == "system":
                data[0]["content"] = SYSTEM_INSTRUCTION
            return data
    except:
        return [{"role": "system", "content": SYSTEM_INSTRUCTION}]


def save_memory(history):
    try:
        if len(history) > 21:
            history = [history[0]] + history[-20:]
        with open(MEMORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Memory Error: {e}")


conversation_history = load_memory()


# --- MEMORY SYSTEM (LONG TERM VAULT) ---
def save_long_term_fact(fact):
    """Saves a permanent truth about the user."""
    facts = []
    if os.path.exists(FACTS_FILE):
        with open(FACTS_FILE, "r") as f:
            facts = json.load(f)

    if fact not in facts:
        facts.append(fact)
        with open(FACTS_FILE, "w") as f:
            json.dump(facts, f, indent=2)


def get_relevant_facts(query):
    """Finds facts related to the current topic."""
    if not os.path.exists(FACTS_FILE):
        return ""
    with open(FACTS_FILE, "r") as f:
        facts = json.load(f)

    # Simple keyword search to find relevant memories
    relevant = [
        f for f in facts if any(word in f.lower() for word in query.lower().split())
    ]
    if not relevant:
        return ""
    return "\n".join(relevant[:3])  # Limit to top 3


def _learn_fact_background(text):
    """Background worker to extract facts without slowing down chat."""
    if not groq_client:
        return
    try:
        prompt = f"Extract a timeless fact about the user from: '{text}'. Return ONLY the fact (e.g. 'User lives in London'). If none, return NOTHING."
        fact = (
            groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}], model=MODEL_FAST
            )
            .choices[0]
            .message.content.strip()
        )

        if fact and "NOTHING" not in fact and len(fact) > 5:
            save_long_term_fact(fact)
            print(f"DEBUG: Learned -> {fact}")
    except:
        pass


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
    except:
        pass


def find_installed_app(app_name):
    """Fuzzy search for an app in the library."""
    if not os.path.exists(APP_LIBRARY_FILE):
        return None
    try:
        with open(APP_LIBRARY_FILE, "r") as f:
            app_map = json.load(f)
        match, score = process.extractOne(app_name.lower(), list(app_map.keys()))
        if score > 75:
            print(f"DEBUG: Found {match} ({score}%)")
            return app_map[match]
    except:
        pass
    return None


# --- ROUTER (CLASSIFIER) ---
def identify_intent(user_command):
    """Decides if the user wants to CHAT or RUN A COMMAND."""
    cmd = user_command.lower().strip()

    # 1. QUESTION GUARD (Prevents "Do you have access" -> CMD_TYPE)
    question_starters = (
        "what",
        "who",
        "where",
        "when",
        "why",
        "how",
        "do you",
        "can you",
        "are you",
        "is there",
    )
    if cmd.startswith(question_starters):
        if "generate" in cmd or "code" in cmd or "list" in cmd:
            return "CHAT_DEEP"
        return "CHAT_FAST"

    # 2. KEYWORDS
    if cmd.startswith("open "):
        return "CMD_OPEN"
    if "screenshot" in cmd:
        return "CMD_SEE"
    if "webcam" in cmd:
        return "CMD_CAM"

    # 3. AI CLASSIFICATION
    if not groq_client:
        return "CHAT_FAST"

    prompt = f"""
    Analyze: "{user_command}"
    Classify into ONE code:
    - CMD_OPEN: Open apps, websites.
    - CMD_TYPE: Type text, emails.
    - CMD_SEE: Look at screen.
    - CMD_CAM: Check webcam.
    - CHAT_FAST: General conversation.
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


# --- SMART EXTRACTION ---
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
    if "email" in lower_cmd:
        return USER_DATA["email"]
    if "username" in lower_cmd:
        return USER_DATA["username"]

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


# --- BRIDGE FUNCTIONS (Compatibility) ---
def ask_groq_fast(prompt):
    return ask_brain(prompt, use_smart_model=False)


def ask_google_gemini(prompt):
    return ask_brain(prompt, use_smart_model=True)


def execute_open_command(command, speak_func):
    """Executes the open logic smartly."""
    # Try AI Extraction first
    data = extract_open_intent(command)

    target = ""
    if data and "target" in data:
        target = data["target"]
        if data["type"] == "web":
            webbrowser.open(target)
            speak_func(f"Opening {target}")
            return
    else:
        # Fallback to simple slice
        target = command.lower().replace("open", "").strip()
        if "." in target:
            webbrowser.open(f"https://{target}")
            return

    # Try App Library
    path = find_installed_app(target)
    if path:
        os.startfile(path)
        speak_func(f"Launching {target}")
        return

    # Windows Fallback
    try:
        pyautogui.press("win")
        time.sleep(0.1)
        pyautogui.write(target)
        time.sleep(0.2)
        pyautogui.press("enter")
        speak_func(f"Searching for {target}")
    except:
        speak_func(f"I couldn't open {target}")


# --- CORE BRAIN (INTELLIGENT) ---
def ask_brain(user_text, use_smart_model=False):
    global conversation_history
    if not groq_client:
        return "Brain offline."

    # A. LEARN: Check if user shared a fact (Background Thread)
    if any(
        x in user_text.lower() for x in ["my name is", "i live in", "i like", "i am a"]
    ):
        threading.Thread(target=lambda: _learn_fact_background(user_text)).start()

    # B. RECALL: Get facts relevant to this exact question
    memory_context = get_relevant_facts(user_text)

    # C. THINK: Inject memory into the system prompt (invisible to you)
    system_msg = {
        "role": "system",
        "content": SYSTEM_INSTRUCTION + f"\nKNOWN FACTS:\n{memory_context}",
    }

    # Create temporary history so we don't mess up the chat logs
    # We use -15 to keep context but allow room for the memory injection
    temp_history = (
        [system_msg]
        + conversation_history[-15:]
        + [{"role": "user", "content": user_text}]
    )

    try:
        completion = groq_client.chat.completions.create(
            messages=temp_history,
            model=MODEL_SMART if use_smart_model else MODEL_FAST,
            temperature=0.7,
            max_tokens=400 if use_smart_model else 150,
        )

        response_text = completion.choices[0].message.content.strip()

        # Save to Short-Term Memory (for flow)
        conversation_history.append({"role": "user", "content": user_text})
        conversation_history.append({"role": "assistant", "content": response_text})
        save_memory(conversation_history)

        return response_text
    except Exception as e:
        return f"Brain Error: {e}"


def see_screen(user_prompt="Describe this"):
    if not google_model:
        return "Vision offline."
    try:
        screenshot = ImageGrab.grab()
        response = google_model.generate_content([user_prompt, screenshot])
        return response.text
    except:
        return "Screen capture failed."


def see_camera(user_prompt="Describe this"):
    if not google_model:
        return "Camera offline."
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "Camera broken."
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return "Camera error."

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    response = google_model.generate_content([user_prompt, img])
    return response.text
