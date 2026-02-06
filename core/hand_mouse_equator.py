import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import sys
import time

# --- CONFIGURATION ---
FRAME_REDUCTION = 100  # The safety margin (Active Zone)
SCROLL_SPEED = 5  # Adjusted for smoother scrolling
DEADZONE = 40  # Neutral zone size
WINDOW_NAME = "V.E.R.A. Vision Interface"

# --- THEME (BGR) ---
COL_WHITE = (245, 245, 245)
COL_CYAN = (255, 200, 0)  # Deep Cyan/Blue
COL_RED = (50, 50, 255)  # Active Action
COL_DARK = (20, 20, 20)  # HUD Backgrounds

# --- SETUP ---
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# --- INIT MEDIAPIPE ---
try:
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles
    hands = mp_hands.Hands(
        max_num_hands=1, model_complexity=0, min_detection_confidence=0.7
    )
except Exception as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    sys.exit(1)


def draw_corner_rect(img, x, y, w, h, color, length=20, thickness=2):
    """Draws sleek corners instead of a full box."""
    # Top Left
    cv2.line(img, (x, y), (x + length, y), color, thickness)
    cv2.line(img, (x, y), (x, y + length), color, thickness)
    # Top Right
    cv2.line(img, (x + w, y), (x + w - length, y), color, thickness)
    cv2.line(img, (x + w, y), (x + w, y + length), color, thickness)
    # Bottom Left
    cv2.line(img, (x, y + h), (x + length, y + h), color, thickness)
    cv2.line(img, (x, y + h), (x, y + h - length), color, thickness)
    # Bottom Right
    cv2.line(img, (x + w, y + h), (x + w - length, y + h), color, thickness)
    cv2.line(img, (x + w, y + h), (x + w, y + h - length), color, thickness)


def draw_hud(img, fps, mode, x, y):
    h, w, _ = img.shape

    # Header
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (w, 35), COL_DARK, -1)
    cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)

    # Text
    cv2.putText(
        img,
        "V.E.R.A. OPTICAL LINK",
        (15, 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        COL_WHITE,
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        img,
        f"FPS: {int(fps)}",
        (w - 100, 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        COL_CYAN,
        1,
        cv2.LINE_AA,
    )

    # Mode Indicator
    if mode != "IDLE":
        color = COL_RED if mode == "CLICK" else COL_CYAN
        cv2.putText(
            img,
            f"MODE: {mode}",
            (w // 2 - 40, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            1,
            cv2.LINE_AA,
        )

    # Active Zone
    box_w = w - (FRAME_REDUCTION * 2)
    box_h = h - (FRAME_REDUCTION * 2)
    draw_corner_rect(
        img,
        FRAME_REDUCTION,
        FRAME_REDUCTION,
        box_w,
        box_h,
        COL_CYAN,
        length=15,
        thickness=1,
    )


def run_vision_loop():
    # Camera Setup (Force DSHOW for Windows speed)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No Camera Found.")
        return

    cap.set(3, 640)
    cap.set(4, 480)

    screen_w, screen_h = pyautogui.size()
    prev_x, prev_y = 0, 0
    p_time = 0
    is_pinched = False

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 320, 240)  # Start small

    print(">> V.E.R.A. VISION ONLINE")

    while True:
        # Check if window closed
        if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
            break

        success, img = cap.read()
        if not success:
            break

        # Flip & Process
        img = cv2.flip(img, 1)
        h, w, _ = img.shape
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_img)

        # FPS
        c_time = time.time()
        fps = 1 / (c_time - p_time) if p_time > 0 else 0
        p_time = c_time

        mode = "IDLE"

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                lm = hand_lms.landmark
                mp_drawing.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)

                # Coords
                x1, y1 = int(lm[8].x * w), int(lm[8].y * h)  # Index
                x2, y2 = int(lm[4].x * w), int(lm[4].y * h)  # Thumb

                # Fingers Up?
                index_up = lm[8].y < lm[6].y
                middle_up = lm[12].y < lm[10].y

                # --- MOUSE MODE (Index Up, Middle Down) ---
                if index_up and not middle_up:
                    mode = "NAV"

                    # Map Coordinates
                    x_mapped = np.interp(
                        x1, (FRAME_REDUCTION, w - FRAME_REDUCTION), (0, screen_w)
                    )
                    y_mapped = np.interp(
                        y1, (FRAME_REDUCTION, h - FRAME_REDUCTION), (0, screen_h)
                    )

                    # Smooth
                    curr_x = prev_x + (x_mapped - prev_x) / 5
                    curr_y = prev_y + (y_mapped - prev_y) / 5

                    pyautogui.moveTo(curr_x, curr_y)
                    prev_x, prev_y = curr_x, curr_y

                    # Click?
                    dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
                    if dist < 30:
                        mode = "CLICK"
                        cv2.circle(img, (x1, y1), 10, COL_RED, -1)
                        if not is_pinched:
                            pyautogui.mouseDown()
                            is_pinched = True
                    else:
                        if is_pinched:
                            pyautogui.mouseUp()
                            is_pinched = False

                # --- SCROLL MODE (Index Up, Middle Up) ---
                elif index_up and middle_up:
                    mode = "SCROLL"
                    dist_from_center = (h // 2) - y1

                    if abs(dist_from_center) > DEADZONE:
                        speed = int(
                            np.interp(abs(dist_from_center), (DEADZONE, 150), (0, 15))
                        )
                        # Invert logic: Hand UP = Scroll UP
                        if dist_from_center > 0:
                            pyautogui.scroll(speed * SCROLL_SPEED)
                        else:
                            pyautogui.scroll(-speed * SCROLL_SPEED)

                        cv2.line(img, (w // 2, h // 2), (w // 2, y1), COL_CYAN, 2)

        draw_hud(img, fps, mode, prev_x, prev_y)
        cv2.imshow(WINDOW_NAME, img)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_vision_loop()
