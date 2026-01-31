import cv2
import time
import os
import datetime
import ctypes
import winsound


def engage_sentry_mode(speak_func):
    speak_func("Sentry Protocol Engaged. I am watching.")

    # 1. Give you 5 seconds to leave the desk
    time.sleep(5)

    # 2. Arm the Camera
    cap = cv2.VideoCapture(0)

    # Read the first frame as the "Baseline" (Empty chair)
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()

    triggered = False

    while cap.isOpened():
        # 3. Motion Detection Logic (Compare Frame 1 vs Frame 2)
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # SENSITIVITY: Only care if the moving object is big (like a human)
            if cv2.contourArea(contour) < 5000:
                continue

            # --- TRAP TRIGGERED ---
            triggered = True

            # A. Evidence Collection
            intruder_dir = "Intruders"
            if not os.path.exists(intruder_dir):
                os.makedirs(intruder_dir)

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{intruder_dir}/Intruder_{timestamp}.jpg"

            # Save the frame that caught them
            cv2.imwrite(filename, frame1)

            # B. The Nuke (Lock PC)
            # This is the Windows API call for "Win + L"
            ctypes.windll.user32.LockWorkStation()

            # C. Psychological Warfare (Optional Alarm)
            winsound.Beep(2500, 1000)
            break

        if triggered:
            break

        # Move to next frame
        frame1 = frame2
        ret, frame2 = cap.read()

        # Check every 100ms to save CPU
        if cv2.waitKey(10) == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
