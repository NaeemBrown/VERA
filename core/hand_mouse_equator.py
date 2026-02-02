import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import sys
import time

# --- CONFIGURATION ---
FRAME_REDUCTION = 100  # The safety margin (Active Zone)
SENSITIVITY = 1.0  # Leave at 1.0 for 1:1 mapping
SCROLL_SPEED = 8
DEADZONE = 40
WINDOW_NAME = "V.E.R.A. Vision Interface"

# --- PRO THEME (BGR) ---
COL_WHITE = (245, 245, 245)
COL_GRAY = (50, 50, 50)
COL_CYAN = (255, 200, 0)  # Deep Cyan/Blue
COL_RED = (50, 50, 255)  # Active Action
COL_DARK = (20, 20, 20)  # HUD Backgrounds

# --- SETUP ---
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# --- MODERN IMPORT BLOCK (The Fix) ---
try:
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles
except Exception as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    sys.exit(1)

hands = mp_hands.Hands(
    max_num_hands=1, model_complexity=0, min_detection_confidence=0.7
)

# Camera: Force DSHOW for speed
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)

cap.set(3, 640)
cap.set(4, 480)

# Monitor Stats
screen_w, screen_h = pyautogui.size()
prev_x, prev_y = 0, 0
is_pinched = False
p_time = 0

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
print(">> V.E.R.A. VISION: PRO MODE ACTIVE")


def draw_corner_rect(img, x, y, w, h, color, length=20, thickness=2):
    """Draws only the corners of a rectangle for a cleaner look."""
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


def draw_pro_hud(img, fps, mode, x_curr, y_curr):
    h, w, _ = img.shape

    # 1. Top Status Bar (Semi-transparent)
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (w, 35), COL_DARK, -1)
    cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)

    # 2. Text Info
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Left: System Name
    cv2.putText(
        img,
        "V.E.R.A. OS // OPTICAL LINK",
        (15, 22),
        font,
        0.5,
        COL_WHITE,
        1,
        cv2.LINE_AA,
    )

    # Right: Telemetry
    stats = f"FPS: {int(fps)} | POS: {int(x_curr)},{int(y_curr)}"
    cv2.putText(img, stats, (w - 230, 22), font, 0.5, COL_CYAN, 1, cv2.LINE_AA)

    # 3. Mode Indicator (Bottom Center)
    if mode != "IDLE":
        cv2.rectangle(img, (w // 2 - 60, h - 40), (w // 2 + 60, h - 10), COL_DARK, -1)

        color = COL_RED if mode == "CLICK" else COL_CYAN
        cv2.putText(img, mode, (w // 2 - 20, h - 18), font, 0.6, color, 1, cv2.LINE_AA)

    # 4. Active Region Markers (The "Workspace")
    box_x = FRAME_REDUCTION
    box_y = FRAME_REDUCTION
    box_w = w - (FRAME_REDUCTION * 2)
    box_h = h - (FRAME_REDUCTION * 2)

    draw_corner_rect(img, box_x, box_y, box_w, box_h, COL_CYAN, length=15, thickness=1)


def draw_crosshair(img, x, y, active=False):
    """Draws a precision sniper-style crosshair."""
    color = COL_RED if active else COL_WHITE
    size = 15

    # Main Lines
    cv2.line(img, (x - size, y), (x + size, y), color, 1)
    cv2.line(img, (x, y - size), (x, y + size), color, 1)

    # Outer Circle
    cv2.circle(img, (x, y), 10, color, 1)

    if active:
        # Solid center dot for click confirmation
        cv2.circle(img, (x, y), 4, color, -1)


while True:
    # Check for X button close
    if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
        break

    success, img = cap.read()
    if not success:
        break

    # Mirror and Filter
    img = cv2.flip(img, 1)

    # Make the image slightly "cooler" (Blue tint for tech feel)
    img[:, :, 2] = np.clip(img[:, :, 2] * 0.9, 0, 255)

    h, w, c = img.shape

    # FPS Calculation
    c_time = time.time()
    fps = 1 / (c_time - p_time) if p_time > 0 else 0
    p_time = c_time

    current_mode = "IDLE"
    target_x, target_y = 0, 0

    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_img)

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            lm = hand_lms.landmark

            # Draw Skeleton (Clean Style)
            mp_drawing.draw_landmarks(
                img,
                hand_lms,
                mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style(),
            )

            # Coordinates
            x1, y1 = int(lm[8].x * w), int(lm[8].y * h)  # Index
            x_thumb, y_thumb = int(lm[4].x * w), int(lm[4].y * h)  # Thumb

            # Logic
            index_up = lm[8].y < lm[6].y
            middle_up = lm[12].y < lm[10].y

            # --- CURSOR ---
            if index_up and not middle_up:
                current_mode = "NAV"

                # Map active region to screen
                x_mapped = np.interp(
                    x1, (FRAME_REDUCTION, w - FRAME_REDUCTION), (0, screen_w)
                )
                y_mapped = np.interp(
                    y1, (FRAME_REDUCTION, h - FRAME_REDUCTION), (0, screen_h)
                )

                # Clamp
                target_x = max(0, min(screen_w - 1, x_mapped))
                target_y = max(0, min(screen_h - 1, y_mapped))

                # Smooth
                curr_x = prev_x + (target_x - prev_x) / 4
                curr_y = prev_y + (target_y - prev_y) / 4

                try:
                    pyautogui.moveTo(curr_x, curr_y)
                except:
                    pass

                prev_x, prev_y = curr_x, curr_y

                # Click
                dist = ((x1 - x_thumb) ** 2 + (y1 - y_thumb) ** 2) ** 0.5
                if dist < 30:
                    current_mode = "CLICK"
                    if not is_pinched:
                        pyautogui.mouseDown()
                        is_pinched = True
                else:
                    if is_pinched:
                        pyautogui.mouseUp()
                        is_pinched = False

                draw_crosshair(img, x1, y1, active=is_pinched)

            # --- SCROLL ---
            elif index_up and middle_up:
                current_mode = "SCROLL"

                # Vertical Center Line
                centerY = h // 2
                distance = centerY - y1

                # Draw Scroll UI
                cv2.line(img, (w // 2, centerY), (w // 2, y1), COL_CYAN, 2)

                if abs(distance) > DEADZONE:
                    speed = int(np.interp(abs(distance), (DEADZONE, 150), (0, 20)))
                    if distance > 0:
                        pyautogui.scroll(-speed * SCROLL_SPEED)
                    else:
                        pyautogui.scroll(speed * SCROLL_SPEED)

    draw_pro_hud(img, fps, current_mode, prev_x, prev_y)

    cv2.imshow(WINDOW_NAME, img)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
sys.exit()
