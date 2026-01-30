import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# --- CONFIGURATION ---
MARGIN = 20           
SENSITIVITY = 1.8     
SCROLL_SPEED = 8      
DEADZONE = 40         

# --- VISUAL THEME (BGR Colors) ---
CYAN = (255, 255, 0)   # Note: OpenCV uses BGR, not RGB
GREEN = (0, 255, 0)
RED = (0, 0, 255)
DARK_GREEN = (0, 100, 0)

# --- SETUP ---
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, model_complexity=0, min_detection_confidence=0.6)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, 640)
cap.set(4, 480)

screen_w, screen_h = pyautogui.size()
prev_x, prev_y = 0, 0
is_pinched = False 

print(">> V.E.R.A. VISION SYSTEM: ONLINE")

def draw_hud_overlay(img, w, h):
    """Draws the static Sci-Fi elements."""
    # 1. Corner Brackets (The "Scope" look)
    length = 40
    thickness = 2
    # Top Left
    cv2.line(img, (10, 10), (10 + length, 10), CYAN, thickness)
    cv2.line(img, (10, 10), (10, 10 + length), CYAN, thickness)
    # Top Right
    cv2.line(img, (w-10, 10), (w-10-length, 10), CYAN, thickness)
    cv2.line(img, (w-10, 10), (w-10, 10+length), CYAN, thickness)
    # Bottom Left
    cv2.line(img, (10, h-10), (10+length, h-10), CYAN, thickness)
    cv2.line(img, (10, h-10), (10, h-10-length), CYAN, thickness)
    # Bottom Right
    cv2.line(img, (w-10, h-10), (w-10-length, h-10), CYAN, thickness)
    cv2.line(img, (w-10, h-10), (w-10, h-10-length), CYAN, thickness)

    # 2. Status Text
    cv2.putText(img, "OPTICAL SENSORS: ONLINE", (25, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREEN, 1)
    cv2.putText(img, "TRACKING PROTOCOL: ACTIVE", (w - 240, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREEN, 1)

while True:
    success, img = cap.read()
    if not success: break
    
    # Flip for mirror effect
    img = cv2.flip(img, 1)
    
    # --- COOL FILTER EFFECT ---
    # Darken the background slightly to make the UI pop
    img = cv2.convertScaleAbs(img, alpha=0.8, beta=0)
    
    h, w, c = img.shape
    centerY = h // 2
    
    # Draw Static HUD
    draw_hud_overlay(img, w, h)
    
    # DRAW EQUATOR (The "Laser Grid")
    cv2.line(img, (0, centerY), (w, centerY), CYAN, 1)
    cv2.putText(img, "SCROLL THRESHOLD", (10, centerY - 5), cv2.FONT_HERSHEY_PLAIN, 1, CYAN, 1)
    
    # Deadzone Box (Subtle)
    cv2.line(img, (w//2 - 50, centerY - DEADZONE), (w//2 + 50, centerY - DEADZONE), DARK_GREEN, 1)
    cv2.line(img, (w//2 - 50, centerY + DEADZONE), (w//2 + 50, centerY + DEADZONE), DARK_GREEN, 1)
    
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_img)

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            lm = hand_lms.landmark
            
            x1, y1 = int(lm[8].x * w), int(lm[8].y * h)   # Index
            x_thumb, y_thumb = int(lm[4].x * w), int(lm[4].y * h) # Thumb
            
            # Draw "Targeting Box" around the finger
            cv2.rectangle(img, (x1-15, y1-15), (x1+15, y1+15), GREEN, 1)
            cv2.line(img, (x1, y1-20), (x1, y1+20), GREEN, 1) # Crosshair V
            cv2.line(img, (x1-20, y1), (x1+20, y1), GREEN, 1) # Crosshair H
            
            # Logic Vars
            index_up = lm[8].y < lm[6].y
            middle_up = lm[12].y < lm[10].y

            # --- MODE 1: POINTER ---
            if index_up and not middle_up:
                cv2.putText(img, "MODE: CURSOR", (w//2 - 60, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, CYAN, 2)
                
                # Move Mouse
                x_virtual = np.interp(x1, (MARGIN, w-MARGIN), (0, screen_w * SENSITIVITY))
                y_virtual = np.interp(y1, (MARGIN, h-MARGIN), (0, screen_h * SENSITIVITY))
                
                x_final = x_virtual - (screen_w * (SENSITIVITY - 1) / 2)
                y_final = y_virtual - (screen_h * (SENSITIVITY - 1) / 2)

                curr_x = prev_x + (x_final - prev_x) / 3
                curr_y = prev_y + (y_final - prev_y) / 3
                
                try: pyautogui.moveTo(curr_x, curr_y)
                except: pass
                prev_x, prev_y = curr_x, curr_y

                # Click Logic
                dist = ((x1 - x_thumb)**2 + (y1 - y_thumb)**2)**0.5
                if dist < 30:
                    cv2.putText(img, "CLICK", (x1+20, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, RED, 2)
                    if not is_pinched:
                        pyautogui.mouseDown()
                        is_pinched = True
                else:
                    if is_pinched:
                        pyautogui.mouseUp()
                        is_pinched = False

            # --- MODE 2: SCROLL ---
            elif index_up and middle_up:
                distance = centerY - y1 
                
                if abs(distance) > DEADZONE:
                    speed = int(np.interp(abs(distance), (DEADZONE, 150), (0, 20)))
                    
                    if distance > 0: 
                        pyautogui.scroll(-speed * SCROLL_SPEED)
                        cv2.arrowedLine(img, (x1, y1), (x1, y1 + 50), GREEN, 3) # Arrow Down
                        cv2.putText(img, "SCROLLING DOWN", (w//2 - 80, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, GREEN, 2)
                    else:
                        pyautogui.scroll(speed * SCROLL_SPEED)
                        cv2.arrowedLine(img, (x1, y1), (x1, y1 - 50), GREEN, 3) # Arrow Up
                        cv2.putText(img, "SCROLLING UP", (w//2 - 80, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, GREEN, 2)
                else:
                    cv2.putText(img, "HOLD", (w//2 - 30, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, RED, 2)

    cv2.imshow("V.E.R.A. Vision V9", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()