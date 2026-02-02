import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageSequence
import itertools
import threading
import speech_recognition as sr
import os
import sys
import re
import requests
import subprocess
from io import BytesIO
from duckduckgo_search import DDGS

# --- IMPORT CORE ---
try:
    from core import processor
except ImportError:
    # Adding root to sys.path if launched directly from /ui/ folder
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "core"))
    from core import processor

# --- VISUAL CONFIG (THEME) ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

HUD_BG = "#050505"  # Almost Black
HUD_BORDER = "#00FFFF"  # Cyan Neon
HUD_TEXT = "#E0E0E0"  # Soft White
HUD_ACCENT = "#D63384"  # Cyberpunk Pink
TRANS_KEY = "#000001"  # Transparency Key for window masking


# --- IMAGE PROCESSING ENGINE ---
class ImageFetcher:
    """Background worker to find and download images on the fly via DuckDuckGo."""

    def search_and_download(self, query):
        try:
            print(f"DEBUG: Searching visuals for '{query}'...")
            with DDGS() as ddgs:
                # Fetch only the first high-res result
                results = list(ddgs.images(query, max_results=1))
                if results:
                    img_url = results[0]["image"]
                    response = requests.get(img_url, timeout=5)
                    img_data = BytesIO(response.content)
                    return Image.open(img_data)
        except Exception as e:
            print(f"!! IMAGE ENGINE ERROR: {e}")
        return None


# --- UI COMPONENTS (POPUPS) ---
class MediaPopup(ctk.CTkToplevel):
    """A floating glass panel that displays fetched visual data."""

    def __init__(self, pil_image, title="Visual Data", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x420")
        self.title(title)
        self.attributes("-topmost", True)
        self.configure(fg_color=HUD_BG)

        # Maintain aspect ratio for the display
        pil_image.thumbnail((380, 380))
        self.photo = ctk.CTkImage(
            light_image=pil_image, dark_image=pil_image, size=pil_image.size
        )

        self.lbl = ctk.CTkLabel(self, text="", image=self.photo)
        self.lbl.pack(expand=True, fill="both", padx=10, pady=10)

        self.lbl_cap = ctk.CTkLabel(
            self, text=title.upper(), font=("Consolas", 12), text_color="gray"
        )
        self.lbl_cap.pack(side="bottom", pady=5)


class ResultPopup(ctk.CTkToplevel):
    """The Deep Research Data-Pad for long-form text or code."""

    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("600x500")
        self.title("V.E.R.A. DATALINK")
        self.attributes("-topmost", True)
        self.configure(fg_color=HUD_BG)

        self.textbox = ctk.CTkTextbox(
            self,
            font=("Roboto Mono", 14),
            wrap="word",
            fg_color="#101010",
            text_color=HUD_TEXT,
        )
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("0.0", text)
        self.textbox.configure(state="disabled")


# --- MAIN HOLOGRAM INTERFACE ---
class VeraHologram:
    def __init__(self):
        self.root = tk.Tk()
        self.fetcher = ImageFetcher()
        self.vision_process = None

        # --- HUD WINDOW SETUP ---
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", TRANS_KEY)
        self.root.configure(bg=TRANS_KEY)

        # Bottom Right Placement Logic
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        window_w, window_h = 450, 650
        x_pos = screen_w - window_w - 20
        y_pos = screen_h - window_h - 40
        self.root.geometry(f"{window_w}x{window_h}+{x_pos}+{y_pos}")

        # Bind Mouse Events for Dragging
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        # --- LAYOUT CONTAINER ---
        self.container = tk.Frame(self.root, bg=TRANS_KEY)
        self.container.pack(fill="both", expand=True, side="bottom", anchor="e")

        # 1. THE SPEECH BUBBLE (Cyberpunk Glass Style)
        self.bubble = ctk.CTkFrame(
            self.container,
            width=300,
            corner_radius=20,
            fg_color="#0F0F0F",
            border_width=1,
            border_color="#333333",
            bg_color=TRANS_KEY,
        )
        self.lbl_text = ctk.CTkLabel(
            self.bubble,
            text="Initializing...",
            font=("Segoe UI", 14),
            text_color="white",
            wraplength=280,
            justify="left",
        )
        self.lbl_text.pack(padx=20, pady=15, fill="both", expand=True)

        # 2. THE AVATAR (The Core Eye)
        self.avatar_frame = ctk.CTkFrame(
            self.container,
            width=120,
            height=120,
            corner_radius=60,
            fg_color="black",
            border_width=3,
            border_color=HUD_BORDER,
            bg_color=TRANS_KEY,
        )
        self.avatar_frame.pack(side="bottom", anchor="e", padx=20, pady=10)

        self.lbl_gif = tk.Label(self.avatar_frame, bg="black", borderwidth=0)
        self.lbl_gif.place(relx=0.5, rely=0.5, anchor="center")

        # Load Animation Assets
        try:
            self.load_gif("head.gif")
        except:
            # Fallback if asset is missing
            self.lbl_gif.configure(
                text="[V]", font=("Consolas", 35), fg="cyan", bg="black"
            )

        # --- CORE HOOKS ---
        processor.gui_popup_hook = self.thread_safe_display
        processor.toggle_hand_mouse = self.toggle_vision

        # Start System
        self.flash_status(HUD_BORDER)
        threading.Thread(target=self.run_voice_loop, daemon=True).start()
        self.root.mainloop()

    # --- WINDOW NAVIGATION ---
    def start_move(self, event):
        self.x, self.y = event.x, event.y

    def do_move(self, event):
        nx = self.root.winfo_x() + (event.x - self.x)
        ny = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{nx}+{ny}")

    # --- VISUAL FEEDBACK ---
    def flash_status(self, color):
        self.avatar_frame.configure(border_color=color)

    def load_gif(self, filename):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(os.path.dirname(current_dir), "assets", filename)
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
            self.root.after(40, self.animate_gif)
        except:
            pass

    # --- BRAIN-TO-UI HANDLER ---
    def thread_safe_display(self, text):
        """Bridge between background brain threads and the main GUI thread."""
        self.root.after(0, lambda: self.process_output(text))

    def process_output(self, text):
        """
                Scans text for

        [Image of X]
         tags, strips them for speech/display,
                and triggers the ImageFetcher for visuals.
        """
        # --- REGEX ENGINE (STRICT) ---
        # Using double backslashes to escape brackets safely without breaking the string
        tag_pattern = "\\"

        img_match = re.search(tag_pattern, text, re.IGNORECASE)
        clean_text = re.sub(tag_pattern, "", text).strip()

        # Display Logic: Split long responses into the Research Data-Pad
        if len(clean_text) > 400:
            ResultPopup(clean_text)
            self.show_bubble("Sending full technical data to datalink...")
        else:
            self.show_bubble(clean_text)

        # Trigger Visual Data Fetching
        if img_match:
            try:
                query = img_match.group(1)
                self.show_bubble(
                    f"{clean_text}\n\n[ACCESSING VISUAL DATA: {query.upper()}]"
                )
                threading.Thread(target=self.render_image, args=(query,)).start()
            except Exception as e:
                print(f"DEBUG: Regex extraction failure: {e}")

    def render_image(self, query):
        """Runs in background to prevent UI freezing while downloading."""
        img = self.fetcher.search_and_download(query)
        if img:
            self.root.after(0, lambda: MediaPopup(img, title=query))
        else:
            print(f"DEBUG: No visual found for '{query}'")

    def show_bubble(self, text):
        """Animate speech bubble into view."""
        self.bubble.pack(side="bottom", anchor="e", padx=20, pady=(0, 10))
        self.lbl_text.configure(text=text)

        # Display time based on text length (min 4 seconds)
        read_time = max(4000, len(text) * 65)
        self.root.after(read_time, self.hide_bubble)

    def hide_bubble(self):
        """Animate speech bubble out of view."""
        self.bubble.pack_forget()

    # --- HARDWARE & VISION CONTROL ---
    def toggle_vision(self):
        """Toggles the Hand Mouse / Eye tracking script."""
        if self.vision_process:
            self.vision_process.terminate()
            self.vision_process = None
            processor.speak("Vision Offline.")
            self.flash_status(HUD_BORDER)
            return

        # Path to the vision script in /core/ folder
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "core", "hand_mouse_equator.py"
        )
        processor.speak("Vision Engaged.")
        self.flash_status("#00FF00")  # Status: Active
        try:
            self.vision_process = subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            print(f"CRITICAL: Failed to launch vision script: {e}")

    # --- SPEECH-TO-BRAIN LOOP ---
    def run_voice_loop(self):
        """Constant listening loop for VERA's microphone input."""
        r = sr.Recognizer()
        with sr.Microphone() as source:
            # Calibrate for room noise
            r.adjust_for_ambient_noise(source, duration=0.8)
            processor.speak("V.E.R.A. Systems online. Listening.")

            while True:
                try:
                    # Visual cue for listening
                    self.flash_status("#FFFFFF")
                    audio = r.listen(source, timeout=None, phrase_time_limit=12)

                    # Visual cue for processing
                    self.flash_status(HUD_ACCENT)
                    cmd = r.recognize_google(audio, language="en-ZA").lower()
                    print(f"RECOGNIZED: {cmd}")

                    # Pass to logic processor
                    processor.process_command(cmd, audio_data=audio, source=source)

                    # Return to idle state
                    self.flash_status(HUD_BORDER)
                except Exception:
                    # Silent catch for empty audio/noise
                    self.flash_status(HUD_BORDER)
                    continue


# --- ENTRY POINT ---
if __name__ == "__main__":
    VeraHologram()
