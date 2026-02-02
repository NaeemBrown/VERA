import sys
import importlib.util

print("------------------------------------------------")
print("      V.E.R.A. VISION DIAGNOSTIC TOOL          ")
print("------------------------------------------------")

# 1. CHECK PYTHON VERSION
v = sys.version_info
print(f"Python Version: {v.major}.{v.minor}.{v.micro}")

if v.major == 3 and v.minor > 11:
    print("WARNING: MediaPipe is unstable on Python 3.12+.")
    print("RECOMMENDATION: Use Python 3.10 or 3.11 for best results.")

print("------------------------------------------------")

# 2. CHECK OPENCV
try:
    import cv2

    print(f"[PASS] OpenCV is installed. Version: {cv2.__version__}")
except ImportError:
    print("[FAIL] OpenCV not found. Run: pip install opencv-python")

# 3. CHECK MEDIAPIPE
try:
    import mediapipe as mp

    print(f"[PASS] MediaPipe found at: {mp.__file__}")

    # Deep Import Check (The real test)
    try:
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(static_image_mode=True, max_num_hands=1)
        print("[PASS] MediaPipe Hands initialized successfully.")
        hands.close()
    except Exception as e:
        print(f"[FAIL] MediaPipe installed, but Hands module crashed: {e}")

except ImportError:
    print("[FAIL] MediaPipe NOT installed.")
    print("FIX: Run 'pip install mediapipe'")
except Exception as e:
    print(f"[FAIL] Critical Error: {e}")

print("------------------------------------------------")
input("Press Enter to exit...")
