import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageSequence
import itertools
import threading
import speech_recognition as sr
import os
import subprocess
import sys
import main

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")

# PENDANT PALETTE
COL_TRANS = "#000001"  # Transparent Key
COL_BG = "#0A0A0A"  # Deep Dark Glass
COL_BORDER_IDLE = "#00FFFF"  # Cyan
COL_BORDER_TALK = "#FFFFFF"  # White
COL_BORDER_WORK = "#B026FF"  # Purple
COL_BORDER_CAM = "#00FF00"  # Green
COL_TEXT = "#FFFFFF"


class JarvisUI:
    def __init__(self):
        self.root = tk.Tk()
        self.vision_process = None

        # --- WINDOW SETUP ---
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", COL_TRANS)
        self.root.configure(bg=COL_TRANS)

        screen_w = self.root.winfo_screenwidth()

        # Position: TOP RIGHT Corner
        window_w = 350
        window_h = 400
        x_pos = screen_w - window_w - 20
        y_pos = 20
        self.root.geometry(f"{window_w}x{window_h}+{x_pos}+{y_pos}")

        # --- MAIN CONTAINER ---
        self.container = tk.Frame(self.root, bg=COL_TRANS)
        self.container.pack(fill="both", expand=True)

        # --- 1. THE AVATAR TILE (Always Visible) ---
        self.tile = ctk.CTkFrame(
            self.container,
            width=100,
            height=100,
            corner_radius=20,
            fg_color=COL_BG,
            border_width=2,
            border_color=COL_BORDER_IDLE,
        )
        self.tile.pack(side="top", anchor="e", padx=10, pady=(0, 5))

        # Avatar Image Holder
        self.lbl_gif = tk.Label(self.tile, bg=COL_BG, borderwidth=0)
        self.lbl_gif.place(relx=0.5, rely=0.5, anchor="center")

        # --- 2. SPEECH BUBBLE (Hidden Dropdown) ---
        self.bubble = ctk.CTkFrame(
            self.container,
            width=300,
            height=100,
            corner_radius=15,
            fg_color=COL_BG,
            border_width=1,
            border_color="#333333",
        )
        # Note: We don't pack it yet.

        self.lbl_text = ctk.CTkLabel(
            self.bubble,
            text="",
            font=("Segoe UI", 13),
            text_color=COL_TEXT,
            wraplength=280,
            justify="left",
        )
        self.lbl_text.pack(padx=15, pady=15, fill="both", expand=True)

        # --- ASSETS ---
        try:
            self.load_gif("head.gif")
        except:
            self.lbl_gif.configure(text="●", font=("Arial", 40), fg="white", bg=COL_BG)

        # --- HOOKS ---
        main.gui_popup_hook = self.thread_safe_speech
        main.gui_stats_hook = self.thread_safe_stats
        main.toggle_hand_mouse = self.toggle_vision

        # --- STARTUP FLASH (Visual Confirmation) ---
        self.flash_boot()

        # --- START THREADS ---
        self.thread = threading.Thread(target=self.run_voice_loop)
        self.thread.daemon = True
        self.thread.start()

        self.root.mainloop()

    # --- THREAD SAFETY WRAPPERS ---
    def thread_safe_speech(self, text):
        self.root.after(0, lambda: self.show_speech(text))

    def thread_safe_stats(self, data):
        self.root.after(0, lambda: self.show_stats(data))

    def thread_safe_state(self, state):
        self.root.after(0, lambda: self.set_state(state))

    # --- VISUALS ---
    def flash_boot(self):
        """Flashes the border white on startup to prove it's alive."""
        self.tile.configure(border_color="white")
        self.root.after(500, lambda: self.tile.configure(border_color=COL_BORDER_IDLE))

    def set_state(self, state):
        color = COL_BORDER_IDLE
        if state == "speaking":
            color = COL_BORDER_TALK
        elif state == "working":
            color = COL_BORDER_WORK
        elif state == "vision":
            color = COL_BORDER_CAM

        self.tile.configure(border_color=color)

    # --- SPEECH BUBBLE LOGIC ---
    def show_speech(self, text):
        self.set_state("speaking")

        # Show bubble (Drop down below avatar)
        self.bubble.pack(side="top", anchor="e", padx=10, pady=5)
        self.lbl_text.configure(text="")

        # Typewriter
        self.type_char(text, 0)

    def type_char(self, full_text, index):
        if index < len(full_text):
            self.lbl_text.configure(text=full_text[: index + 1])
            self.root.after(15, lambda: self.type_char(full_text, index + 1))
        else:
            # Auto-hide based on length
            delay = 2000 + (len(full_text) * 40)
            self.root.after(delay, self.hide_speech)

    def hide_speech(self):
        self.bubble.pack_forget()
        if self.vision_process is None:
            self.set_state("idle")

    # --- STATS ---
    def show_stats(self, data):
        self.show_speech(f"CPU: {data['cpu']}% | RAM: {data['ram']}%")

    # --- GIF ENGINE ---
    def load_gif(self, path):
        if not os.path.exists(path):
            return
        img = Image.open(path)
        self.frames = []
        for frame in ImageSequence.Iterator(img):
            frame = frame.resize((80, 80))
            self.frames.append(ImageTk.PhotoImage(frame))
        self.frame_cycle = itertools.cycle(self.frames)
        self.animate_gif()

    def animate_gif(self):
        try:
            self.lbl_gif.config(image=next(self.frame_cycle))
            self.root.after(30, self.animate_gif)
        except:
            pass

    # --- VISION LOGIC ---
    def toggle_vision(self):
        if self.vision_process and self.vision_process.poll() is None:
            self.vision_process.terminate()
            self.vision_process = None
            main.speak("Vision offline.")
            self.thread_safe_state("idle")
            return

        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "hand_mouse_equator.py")

        main.speak("Vision engaged.")
        self.thread_safe_state("vision")

        try:
            self.vision_process = subprocess.Popen(
                [sys.executable, script_path],
                cwd=current_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        except Exception as e:
            print(e)
        return "Active"

    # --- VOICE LOOP ---
    def run_voice_loop(self):
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 0.5
        recognizer.non_speaking_duration = 0.3

        with sr.Microphone() as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
            except:
                pass

            main.speak("Online.")

            while True:
                try:
                    audio = recognizer.listen(source, timeout=None)

                    # Use thread_safe call for UI update
                    self.thread_safe_state("working")

                    command = recognizer.recognize_google(
                        audio, language="en-ZA"
                    ).lower()
                    print(f"User: {command}")

                    main.process_command(command, source)

                    # Reset check (Only if bubble closed)
                    if not self.bubble.winfo_ismapped() and self.vision_process is None:
                        self.thread_safe_state("idle")

                except sr.UnknownValueError:
                    if self.vision_process is None:
                        self.thread_safe_state("idle")
                    continue
                except:
                    if self.vision_process is None:
                        self.thread_safe_state("idle")
                    continue


if __name__ == "__main__":
    app = JarvisUI()
