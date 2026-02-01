import os
import json
from dotenv import load_dotenv
from groq import Groq
import google.generativeai as genai
import threading
from PIL import ImageGrab, Image
import cv2

# --- CONFIGURATION ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

# MODELS
MODEL_FAST = "llama-3.1-8b-instant"  # The Speedster (0.5s)
MODEL_SMART = "llama-3.3-70b-versatile"  # The Genius (2.0s)
VISION_MODEL = "gemini-2.0-flash-exp"

# --- THE PERSONA ---
SYSTEM_INSTRUCTION = (
    "Your name is Vera (pronounced V-Air-Ruh). "
    "1. IDENTITY: Never spell your name as an acronym. "
    "2. PERSONALITY: Be casual, slightly sarcastic, and confident. "
    "3. BREVITY: Keep responses punchy (under 3 sentences) unless asked for code or deep explanations."
)

# --- MEMORY SYSTEM (Kept same as before) ---
MEMORY_FILE = "vera_memory.json"


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"history": [{"role": "system", "content": SYSTEM_INSTRUCTION}]}
    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            if data["history"][0]["role"] == "system":
                data["history"][0]["content"] = SYSTEM_INSTRUCTION
            return data
    except:
        return {"history": [{"role": "system", "content": SYSTEM_INSTRUCTION}]}


def save_memory(data):
    try:
        if len(data["history"]) > 21:
            data["history"] = [data["history"][0]] + data["history"][-20:]
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Memory Error: {e}")


# Initialize
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


bg_thread = threading.Thread(target=_connect_brains)
bg_thread.daemon = True
bg_thread.start()


# --- THE ROUTER (Traffic Cop) ---
def identify_intent(user_command):
    """Classifies the command."""
    if not groq_client:
        return "CHAT_FAST"

    prompt = f"""
    Analyze: "{user_command}"
    
    Classify into ONE code:
    - CMD_OPEN: Requests to open apps, websites, OR play music.
    - CMD_SEE: Asks to look at screen.
    - CMD_CAM: Asks to check webcam.
    - CMD_TIME: Asks for time.
    - CHAT_DEEP: Coding tasks, complex questions.
    - CHAT_FAST: Greetings, jokes, simple status.
    
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
    """Figures out WHAT to open (URL or App Name)."""
    if not groq_client:
        return None

    prompt = f"""
    Extract the target from: "{user_command}"
    
    RULES:
    1. If user says "Play [X]", use YouTube Music search URL.
    2. If user says "Open [App]", use the executable name.
    
    EXAMPLES:
    - "Play lo-fi hip hop" -> {{"type": "web", "target": "https://music.youtube.com/search?q=lo-fi+hip+hop"}}
    - "Open YouTube Music" -> {{"type": "web", "target": "https://music.youtube.com"}}
    - "Open Google" -> {{"type": "web", "target": "https://www.google.com"}}
    - "Launch VS Code" -> {{"type": "app", "target": "code"}}
    - "Open Calculator" -> {{"type": "app", "target": "calc"}}
    
    Return ONLY the JSON string.
    """
    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_FAST,
            temperature=0,
            max_tokens=100,
        )
        # Clean the response to ensure it's pure JSON
        clean_json = (
            completion.choices[0]
            .message.content.replace("```json", "")
            .replace("```", "")
            .strip()
        )
        return json.loads(clean_json)
    except:
        return None


def ask_brain(user_text, use_smart_model=False):
    """Chat with ability to switch brains."""
    global conversation_history
    if not groq_client:
        return "Brain offline."

    # Select the engine based on the Router's decision
    selected_model = MODEL_SMART if use_smart_model else MODEL_FAST

    print(f"DEBUG: Using {selected_model}")  # So you can see which brain is working

    try:
        conversation_history.append({"role": "user", "content": user_text})

        completion = groq_client.chat.completions.create(
            messages=conversation_history,
            model=selected_model,
            temperature=0.7,
            max_tokens=(
                400 if use_smart_model else 150
            ),  # Allow more words for smart mode
        )

        response_text = completion.choices[0].message.content.strip()
        conversation_history.append({"role": "assistant", "content": response_text})
        save_memory({"history": conversation_history})

        return response_text

    except Exception as e:
        return f"I had a brain fart: {e}"


# --- VISION TOOLS (Kept same) ---
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
