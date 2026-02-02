import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageSequence
import itertools
import threading
import speech_recognition as sr
import os
import subprocess
import sys

# --- IMPORT CORE ---
try:
    from core import processor
except ImportError:
    # Fallback to find 'core' if run directly
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "core"))
    from core import processor

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# --- VISUAL THEME ---
COL_TRANS = "#000001"  # Transparent Key
COL_BG = "#0A0A0A"  # Dark Background
COL_BORDER_IDLE = "#00FFFF"  # Cyan
COL_BORDER_TALK = "#FFFFFF"  # White
COL_BORDER_WORK = "#B026FF"  # Purple
COL_BORDER_CAM = "#00FF00"  # Green
COL_TEXT = "#FFFFFF"


class ResultPopup(ctk.CTkToplevel):
    """A sleek popup for reading long answers (Deep Research)."""

    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("600x400")
        self.title("V.E.R.A. Intelligence")
        self.attributes("-topmost", True)

        self.textbox = ctk.CTkTextbox(self, font=("Roboto", 14), wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("0.0", text)
        self.textbox.configure(state="disabled")


class VeraHologram:
    def __init__(self):
        self.root = tk.Tk()
        self.vision_process = None

        # --- WINDOW SETUP ---
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", COL_TRANS)
        self.root.configure(bg=COL_TRANS)

        # Position (Bottom Right)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        window_w, window_h = 400, 500
        x_pos = screen_w - window_w - 20
        y_pos = screen_h - window_h - 40
        self.root.geometry(f"{window_w}x{window_h}+{x_pos}+{y_pos}")

        # Drag Functionality
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        # Main Container
        self.container = tk.Frame(self.root, bg=COL_TRANS)
        self.container.pack(fill="both", expand=True)

        # 1. THE AVATAR TILE
        self.tile = ctk.CTkFrame(
            self.container,
            width=120,
            height=120,
            corner_radius=60,
            fg_color=COL_BG,
            border_width=3,
            border_color=COL_BORDER_IDLE,
        )
        self.tile.pack(side="top", anchor="e", padx=20, pady=(0, 10))

        self.lbl_gif = tk.Label(self.tile, bg=COL_BG, borderwidth=0)
        self.lbl_gif.place(relx=0.5, rely=0.5, anchor="center")

        # 2. THE SPEECH BUBBLE (Hidden by default)
        self.bubble = ctk.CTkFrame(
            self.container,
            width=300,
            height=100,
            corner_radius=15,
            fg_color=COL_BG,
            border_width=1,
            border_color="#333333",
        )
        self.lbl_text = ctk.CTkLabel(
            self.bubble,
            text="",
            font=("Segoe UI", 13),
            text_color=COL_TEXT,
            wraplength=280,
            justify="left",
        )
        self.lbl_text.pack(padx=15, pady=15, fill="both", expand=True)

        # Load Assets
        try:
            self.load_gif("head.gif")
        except:
            self.lbl_gif.configure(text="[O]", font=("Arial", 30), fg="cyan", bg=COL_BG)

        # --- PROCESSOR HOOKS ---
        # This connects the Brain to the Body
        processor.gui_popup_hook = self.thread_safe_display
        processor.toggle_hand_mouse = self.toggle_vision

        # Start Flash
        self.flash_boot()

        # Start Voice Thread
        self.thread = threading.Thread(target=self.run_voice_loop, daemon=True)
        self.thread.start()

        self.root.mainloop()

    # --- MOVEMENT ---
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    # --- VISUALS ---
    def set_state(self, state):
        color = COL_BORDER_IDLE
        if state == "listening":
            color = COL_BORDER_TALK
        elif state == "processing":
            color = COL_BORDER_WORK
        elif state == "vision":
            color = COL_BORDER_CAM
        self.tile.configure(border_color=color)

    def flash_boot(self):
        self.tile.configure(border_color="white")
        self.root.after(500, lambda: self.tile.configure(border_color=COL_BORDER_IDLE))

    def load_gif(self, filename):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        path = os.path.join(root_dir, "assets", filename)

        img = Image.open(path)
        self.frames = [
            ImageTk.PhotoImage(frame.resize((90, 90)))
            for frame in ImageSequence.Iterator(img)
        ]
        self.frame_cycle = itertools.cycle(self.frames)
        self.animate_gif()

    def animate_gif(self):
        try:
            self.lbl_gif.config(image=next(self.frame_cycle))
            self.root.after(30, self.animate_gif)
        except:
            pass

    # --- DISPLAY LOGIC ---
    def thread_safe_display(self, text):
        self.root.after(0, lambda: self.handle_output(text))

    def handle_output(self, text):
        """Decides whether to show a Bubble or a Popup."""
        if len(text) > 300:
            # Long Text -> Popup
            ResultPopup(text)
        else:
            # Short Text -> Bubble
            self.show_speech_bubble(text)

    def show_speech_bubble(self, text):
        self.bubble.pack(side="top", anchor="e", padx=20, pady=5)
        self.type_char(text, 0)

    def type_char(self, full_text, index):
        """Matrix-style typing effect."""
        if index < len(full_text):
            self.lbl_text.configure(text=full_text[: index + 1])
            self.root.after(15, lambda: self.type_char(full_text, index + 1))
        else:
            # Wait, then hide
            delay = 3000 + (len(full_text) * 40)
            self.root.after(delay, self.hide_bubble)

    def hide_bubble(self):
        self.bubble.pack_forget()

    # --- VISION TOGGLE ---
    def toggle_vision(self):
        if self.vision_process and self.vision_process.poll() is None:
            self.vision_process.terminate()
            self.vision_process = None
            processor.speak("Vision systems offline.")
            self.root.after(0, lambda: self.set_state("idle"))
            return

        # Find the script in the 'core' folder
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(root_dir, "core", "hand_mouse_equator.py")

        processor.speak("Vision engaged. Hand tracking active.")
        self.root.after(0, lambda: self.set_state("vision"))

        try:
            self.vision_process = subprocess.Popen(
                [sys.executable, script_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        except Exception as e:
            print(f"Vision Error: {e}")

    # --- VOICE LOOP ---
    def run_voice_loop(self):
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 0.8

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            processor.speak("Vera is online.")

            while True:
                try:
                    self.root.after(0, lambda: self.set_state("listening"))
                    audio = recognizer.listen(source, timeout=None)

                    self.root.after(0, lambda: self.set_state("processing"))
                    command = recognizer.recognize_google(
                        audio, language="en-ZA"
                    ).lower()
                    print(f"User: {command}")

                    # Send to Brain
                    processor.process_command(command, audio_data=audio, source=source)

                    self.root.after(0, lambda: self.set_state("idle"))

                except Exception:
                    self.root.after(0, lambda: self.set_state("idle"))
                    continue


if __name__ == "__main__":
    app = VeraHologram()
