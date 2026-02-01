import os
from dotenv import load_dotenv
from groq import Groq
import google.generativeai as genai
import threading
from PIL import ImageGrab, Image
import cv2
import time

# --- CONFIGURATION ---
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

# OPTIMIZATION: Updated to new supported models
MODEL_FAST = "llama-3.1-8b-instant"  # New fast model
MODEL_SMART = "llama-3.3-70b-versatile"  # Smart model
VISION_MODEL = "gemini-2.0-flash-exp"

# --- SYSTEM PERSONA ---
SYSTEM_INSTRUCTION = (
    "You are V.E.R.A. (Virtual Electronic Remote Assistant). "
    "You are highly efficient. "
    "Keep answers under 2 sentences unless asked for detail. "
    "Be professional, slightly dry, and intelligent."
)

groq_client = None
google_model = None
BRAIN_ACTIVE = False
VISION_ACTIVE = False
conversation_history = [{"role": "system", "content": SYSTEM_INSTRUCTION}]


def _connect_brains():
    """Background connection to avoid startup lag."""
    global groq_client, google_model, BRAIN_ACTIVE, VISION_ACTIVE

    # 1. Groq
    try:
        if GROQ_API_KEY:
            groq_client = Groq(api_key=GROQ_API_KEY)
            # Warm up the connection
            groq_client.chat.completions.create(
                messages=[{"role": "user", "content": "ping"}],
                model=MODEL_FAST,
                max_tokens=1,
            )
            BRAIN_ACTIVE = True
            print("DEBUG: Groq Online.")
    except Exception as e:
        print(f"Groq Error: {e}")

    # 2. Vision
    try:
        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            google_model = genai.GenerativeModel(VISION_MODEL)
            VISION_ACTIVE = True
            print("DEBUG: Vision Online.")
    except Exception as e:
        print(f"Vision Error: {e}")


# Start connections immediately
bg_thread = threading.Thread(target=_connect_brains)
bg_thread.daemon = True
bg_thread.start()


def identify_intent(user_command):
    """Uses the FAST model to decide what to do."""
    if not BRAIN_ACTIVE:
        return "UNKNOWN"

    # Minimal prompt to save tokens
    prompt = f"""
    Classify command: "{user_command}"
    Codes: CMD_SEE, CMD_CAM, CMD_TIME, CMD_TIMER, CMD_MUSIC, CMD_CHAT
    Return ONLY the code.
    """

    try:
        # Temperature 0 for maximum speed and consistency
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_FAST,
            temperature=0,
            max_tokens=5,  # We only need a short code
        )
        return completion.choices[0].message.content.strip()
    except:
        return "CMD_CHAT"  # Default to chat on error


def ask_brain(user_text):
    global conversation_history
    if not BRAIN_ACTIVE:
        return "Systems initializing."

    try:
        conversation_history.append({"role": "user", "content": user_text})

        # OPTIMIZATION: Keep history very short (Last 6 turns)
        if len(conversation_history) > 7:
            conversation_history = [conversation_history[0]] + conversation_history[-6:]

        completion = groq_client.chat.completions.create(
            messages=conversation_history,
            model=MODEL_SMART,
            temperature=0.7,
            max_tokens=150,  # Cap response length for speed
        )

        response_text = completion.choices[0].message.content.strip()
        conversation_history.append({"role": "assistant", "content": response_text})

        return response_text

    except Exception as e:
        return "I encountered a processing error."


def see_screen(user_prompt):
    if not VISION_ACTIVE:
        return "Vision offline."
    try:
        screenshot = ImageGrab.grab()
        # OPTIMIZATION: Resize to 1024x1024 to prevent Rate Limits
        screenshot.thumbnail((1024, 1024))

        if len(user_prompt) < 5:
            user_prompt = "Describe this screen."

        response = google_model.generate_content([user_prompt, screenshot])
        return response.text
    except Exception as e:
        if "429" in str(e):
            return "Visual buffers overloaded. Standby."
        return "I cannot see the screen right now."


def see_camera(user_prompt):
    if not VISION_ACTIVE:
        return "Camera offline."

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "Camera not found."

    # Warm up frame
    for _ in range(5):
        cap.read()
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return "Camera error."

    # Process
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_frame)
    pil_img.thumbnail((1024, 1024))  # Optimization

    try:
        if len(user_prompt) < 5:
            user_prompt = "Identify this."
        response = google_model.generate_content([user_prompt, pil_img])
        return response.text
    except:
        return "Identification failed."
