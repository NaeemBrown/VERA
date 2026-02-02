import cv2
import time
import os
import datetime
import ctypes
import winsound

# --- PATH SETUP ---
# Save intruder photos inside 'data/intruders'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
EVIDENCE_DIR = os.path.join(ROOT_DIR, "data", "intruders")


def engage_sentry_mode(speak_func):
    """
    Monitors the webcam for motion. If detected:
    1. Saves a photo to data/intruders
    2. Locks the Workstation (Win+L)
    3. Sounds an alarm
    """
    if not os.path.exists(EVIDENCE_DIR):
        os.makedirs(EVIDENCE_DIR)

    speak_func("Sentry Protocol Engaged. I am watching.")

    # Grace period to leave the room
    time.sleep(5)

    # Arm Camera
    # Note: cv2.CAP_DSHOW starts faster on Windows
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        speak_func("Error. Camera unavailable.")
        return

    # Read Baseline Frames
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()

    print("DEBUG: Sentry Armed.")

    while cap.isOpened():
        # Motion Detection (Frame Difference)
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # SENSITIVITY: Ignore small movements (flies, lighting flicker)
            if cv2.contourArea(contour) < 5000:
                continue

            # --- TRAP TRIGGERED ---
            print("DEBUG: MOTION DETECTED!")

            # A. Evidence Collection
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(EVIDENCE_DIR, f"Intruder_{timestamp}.jpg")

            cv2.imwrite(filename, frame1)

            # B. Psychological Warfare (Alarm)
            # Run asynchronously so it doesn't block the lock
            winsound.Beep(2500, 1000)

            # C. The Nuke (Lock PC)
            ctypes.windll.user32.LockWorkStation()

            # Exit after triggering
            cap.release()
            cv2.destroyAllWindows()
            return

        # Advance Frames
        frame1 = frame2
        ret, frame2 = cap.read()

        if not ret:
            break

        # CPU SAVER: Check 10 times per second, not 60
        time.sleep(0.1)

    cap.release()
    cv2.destroyAllWindows()
