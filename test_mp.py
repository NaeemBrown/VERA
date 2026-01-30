try:
    import mediapipe as mp
    print(f"MediaPipe Location: {mp.__file__}")
    
    # Try explicit import (sometimes fixes 3.13 issues)
    import mediapipe.python.solutions.hands as mp_hands
    print("SUCCESS: Explicit import worked!")
except ImportError:
    print("FAIL: MediaPipe is not installed correctly.")
except AttributeError:
    print("FAIL: The library is empty. This confirms Python 3.13 incompatibility.")
except Exception as e:
    print(f"FAIL: {e}")