import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import sys

# --- CONFIGURATION ---
# The "Active Region" is the box in the middle of the camera.
# 0.2 means the box starts at 20% width/height and ends at 80%.
# Smaller box = Less hand movement needed to cross the screen.
FRAME_REDUCTION = 100  # Pixels to cut from edges (The "Green Box")
SCROLL_SPEED = 8
DEADZONE = 40
WINDOW_NAME = "V.E.R.A. Vision V9"

# --- VISUAL THEME (BGR) ---
NEON_CYAN = (255, 255, 0)
NEON_BLUE = (255, 100, 0)
WARNING_RED = (0, 0, 255)
GLASS_BLACK = (0, 0, 0)

# --- SETUP ---
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

try:
    from mediapipe.python.solutions import hands as mp_hands
    from mediapipe.python.solutions import drawing_utils as mp_drawing
    from mediapipe.python.solutions import drawing_styles as mp_styles
except ImportError:
    import mediapipe.solutions.hands as mp_hands
    import mediapipe.solutions.drawing_utils as mp_drawing
    import mediapipe.solutions.drawing_styles as mp_styles

hands = mp_hands.Hands(
    max_num_hands=1, model_complexity=0, min_detection_confidence=0.6
)

# Camera: Fast DSHOW
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)

cap.set(3, 640)
cap.set(4, 480)

# GET PRIMARY MONITOR SIZE
screen_w, screen_h = pyautogui.size()
prev_x, prev_y = 0, 0
is_pinched = False

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
print(">> V.E.R.A. VISUAL INTERFACE: ONLINE")


def draw_modern_hud(img, w, h, mode="IDLE"):
    """Draws a semi-transparent 'Glass' HUD."""
    overlay = img.copy()

    # Top/Bottom Bars
    cv2.rectangle(overlay, (0, 0), (w, 40), GLASS_BLACK, -1)
    cv2.rectangle(overlay, (0, h - 30), (w, h), GLASS_BLACK, -1)
    cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)

    # Active Region Box (The "Mouse Pad")
    # Anything outside this box is clamped to the edge of the screen
    cv2.rectangle(
        img,
        (FRAME_REDUCTION, FRAME_REDUCTION),
        (w - FRAME_REDUCTION, h - FRAME_REDUCTION),
        NEON_CYAN,
        1,
    )

    font = cv2.FONT_HERSHEY_DUPLEX
    cv2.putText(
        img, "V.E.R.A. // VISION", (15, 28), font, 0.6, NEON_CYAN, 1, cv2.LINE_AA
    )

    status_color = NEON_CYAN
    if mode == "CLICKING":
        status_color = WARNING_RED
    if mode == "SCROLLING":
        status_color = NEON_BLUE

    cv2.putText(
        img, f"STATUS: {mode}", (w - 180, 28), font, 0.6, status_color, 1, cv2.LINE_AA
    )


def draw_reticle(img, x, y, is_active=False):
    color = WARNING_RED if is_active else NEON_CYAN
    r = 20
    t = 2
    # Open bracket box
    cv2.line(img, (x - r, y - r), (x - r + 10, y - r), color, t)
    cv2.line(img, (x - r, y - r), (x - r, y - r + 10), color, t)
    cv2.line(img, (x + r, y - r), (x + r - 10, y - r), color, t)
    cv2.line(img, (x + r, y - r), (x + r, y - r + 10), color, t)
    cv2.line(img, (x - r, y + r), (x - r + 10, y + r), color, t)
    cv2.line(img, (x - r, y + r), (x - r, y + r - 10), color, t)
    cv2.line(img, (x + r, y + r), (x + r - 10, y + r), color, t)
    cv2.line(img, (x + r, y + r), (x + r, y + r - 10), color, t)

    if is_active:
        cv2.circle(img, (x, y), 5, color, -1)


while True:
    if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
        break

    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    h, w, c = img.shape
    centerY = h // 2

    current_mode = "IDLE"

    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_img)

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            lm = hand_lms.landmark

            mp_drawing.draw_landmarks(
                img,
                hand_lms,
                mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style(),
            )

            # Raw Coordinates
            x1, y1 = int(lm[8].x * w), int(lm[8].y * h)
            x_thumb, y_thumb = int(lm[4].x * w), int(lm[4].y * h)

            index_up = lm[8].y < lm[6].y
            middle_up = lm[12].y < lm[10].y

            # --- CURSOR MODE ---
            if index_up and not middle_up:
                current_mode = "CURSOR"

                # --- COORDINATE MAPPING (THE FIX) ---
                # 1. Map coordinates from the "Green Box" to the "Primary Monitor Size"
                # This ensures (0,0) is top-left and (screen_w, screen_h) is bottom-right
                x_mapped = np.interp(
                    x1, (FRAME_REDUCTION, w - FRAME_REDUCTION), (0, screen_w)
                )
                y_mapped = np.interp(
                    y1, (FRAME_REDUCTION, h - FRAME_REDUCTION), (0, screen_h)
                )

                # 2. Hard Clamp to Primary Monitor Bounds
                # This prevents the mouse from flying off to a second monitor
                x_mapped = max(0, min(screen_w - 1, x_mapped))
                y_mapped = max(0, min(screen_h - 1, y_mapped))

                # 3. Smooth it
                curr_x = (
                    prev_x + (x_mapped - prev_x) / 4
                )  # Increased smoothing slightly
                curr_y = prev_y + (y_mapped - prev_y) / 4

                try:
                    pyautogui.moveTo(curr_x, curr_y)
                except:
                    pass

                prev_x, prev_y = curr_x, curr_y

                # Pinch Logic
                dist = ((x1 - x_thumb) ** 2 + (y1 - y_thumb) ** 2) ** 0.5
                if dist < 30:
                    current_mode = "CLICKING"
                    if not is_pinched:
                        pyautogui.mouseDown()
                        is_pinched = True
                else:
                    if is_pinched:
                        pyautogui.mouseUp()
                        is_pinched = False

                draw_reticle(img, x1, y1, is_active=is_pinched)

            # --- SCROLL MODE ---
            elif index_up and middle_up:
                current_mode = "SCROLLING"
                distance = centerY - y1
                cv2.line(img, (x1, y1), (x1, centerY), NEON_BLUE, 2)

                if abs(distance) > DEADZONE:
                    speed = int(np.interp(abs(distance), (DEADZONE, 150), (0, 20)))
                    if distance > 0:
                        pyautogui.scroll(-speed * SCROLL_SPEED)
                        cv2.putText(
                            img,
                            "vvv",
                            (x1 - 20, y1 + 40),
                            cv2.FONT_HERSHEY_PLAIN,
                            2,
                            NEON_BLUE,
                            2,
                        )
                    else:
                        pyautogui.scroll(speed * SCROLL_SPEED)
                        cv2.putText(
                            img,
                            "^^^",
                            (x1 - 20, y1 - 20),
                            cv2.FONT_HERSHEY_PLAIN,
                            2,
                            NEON_BLUE,
                            2,
                        )

    draw_modern_hud(img, w, h, current_mode)
    cv2.imshow(WINDOW_NAME, img)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
sys.exit()
