import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageSequence, ImageDraw
import itertools
import threading
import speech_recognition as sr
import os
import sys
import re
import requests
import subprocess
import atexit
import time
import queue
from io import BytesIO
from duckduckgo_search import DDGS
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import numpy as np

# Try to import sounddevice, gracefully disable waveform if not available
try:
    import sounddevice as sd

    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    print("Note: sounddevice not available, waveform disabled")

# --- IMPORT CORE ---
try:
    from core import processor
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "core"))
    from core import processor

# --- REFINED VISUAL CONFIG ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Elegant Minimal Palette
BG_DARK = "#0a0a0a"
BG_CARD = "#151515"
BG_HOVER = "#1f1f1f"
BORDER_SUBTLE = "#2a2a2a"
BORDER_ACCENT = "#00d4ff"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#8a8a8a"
TEXT_MUTED = "#4a4a4a"
ACCENT_PRIMARY = "#00d4ff"
ACCENT_SUCCESS = "#00ff88"
ACCENT_WARNING = "#ffa500"
ACCENT_ERROR = "#ff4466"
TRANS_KEY = "#000001"

# Performance Constants
MAX_IMAGE_SIZE = 10 * 1024 * 1024
NETWORK_TIMEOUT = 10
GIF_FRAME_SIZE = (80, 80)
THUMBNAIL_SIZE = (380, 380)
MIN_BUBBLE_TIME = 3500
BUBBLE_TIME_PER_CHAR = 50
LONG_TEXT_THRESHOLD = 400
MAX_HISTORY_ITEMS = 30

# Compiled Regex
IMAGE_TAG_PATTERN = re.compile(
    r"<image_search>\s*(.+?)\s*</image_search>", re.IGNORECASE
)


# --- SMOOTH WAVEFORM VISUALIZER ---
class WaveformVisualizer(ctk.CTkFrame):
    """Minimal, smooth audio waveform visualization."""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, fg_color="transparent", *args, **kwargs)

        if not SOUNDDEVICE_AVAILABLE:
            # Show a simple static indicator instead
            self.static_label = ctk.CTkLabel(
                self, text="● ● ●", font=("Inter", 12), text_color=TEXT_MUTED
            )
            self.static_label.pack(pady=5)
            return

        self.canvas = tk.Canvas(
            self, bg=BG_DARK, highlightthickness=0, width=200, height=40
        )
        self.canvas.pack(pady=5)

        self.samples = [0] * 20
        self.is_listening = False
        self.draw_waveform()

    def update_audio(self, level):
        """Update audio level smoothly."""
        if SOUNDDEVICE_AVAILABLE:
            self.samples.pop(0)
            self.samples.append(min(level, 100))

    def draw_waveform(self):
        """Draw smooth minimalist waveform with rounded bars."""
        if not SOUNDDEVICE_AVAILABLE:
            return

        self.canvas.delete("all")
        bar_width = 6
        spacing = 3

        for i, sample in enumerate(self.samples):
            height = max(4, (sample / 100) * 32)
            x = i * (bar_width + spacing) + 10
            y_center = 20

            # Smooth gradient effect with opacity
            if self.is_listening:
                alpha = int(255 * (0.3 + 0.7 * (sample / 100)))
                color = self._blend_colors(BG_DARK, ACCENT_PRIMARY, alpha / 255)
            else:
                color = BORDER_SUBTLE

            # Draw rounded rectangles (using ovals for rounded ends)
            radius = bar_width / 2

            # Top cap
            self.canvas.create_oval(
                x,
                y_center - height / 2,
                x + bar_width,
                y_center - height / 2 + bar_width,
                fill=color,
                outline="",
            )

            # Middle rectangle
            if height > bar_width:
                self.canvas.create_rectangle(
                    x,
                    y_center - height / 2 + radius,
                    x + bar_width,
                    y_center + height / 2 - radius,
                    fill=color,
                    outline="",
                )

            # Bottom cap
            self.canvas.create_oval(
                x,
                y_center + height / 2 - bar_width,
                x + bar_width,
                y_center + height / 2,
                fill=color,
                outline="",
            )

        self.after(60, self.draw_waveform)

    def _blend_colors(self, color1, color2, ratio):
        """Blend two hex colors."""
        c1 = tuple(int(color1[i : i + 2], 16) for i in (1, 3, 5))
        c2 = tuple(int(color2[i : i + 2], 16) for i in (1, 3, 5))
        blended = tuple(int(c1[i] * (1 - ratio) + c2[i] * ratio) for i in range(3))
        return f"#{blended[0]:02x}{blended[1]:02x}{blended[2]:02x}"

    def set_listening(self, state):
        """Set listening state."""
        self.is_listening = state


# --- COMMAND HISTORY (MINIMAL) ---
class CommandHistory(ctk.CTkFrame):
    """Clean, minimal command history."""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, fg_color=BG_CARD, corner_radius=12, *args, **kwargs)

        # Title
        self.title_label = ctk.CTkLabel(
            self, text="Recent", font=("Inter", 11, "bold"), text_color=TEXT_SECONDARY
        )
        self.title_label.pack(pady=(12, 8), padx=15, anchor="w")

        # Separator
        separator = ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE)
        separator.pack(fill="x", padx=15)

        # Scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=120,
            scrollbar_button_color=BORDER_SUBTLE,
            scrollbar_button_hover_color=BORDER_ACCENT,
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.history_items = []

    def add_command(self, command, status="success"):
        """Add command to history with minimal styling."""
        timestamp = time.strftime("%H:%M")

        color_map = {
            "success": TEXT_SECONDARY,
            "error": ACCENT_ERROR,
            "processing": ACCENT_PRIMARY,
        }

        item_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        item_frame.pack(fill="x", pady=3)

        # Time
        time_label = ctk.CTkLabel(
            item_frame,
            text=timestamp,
            font=("JetBrains Mono", 9),
            text_color=TEXT_MUTED,
            width=35,
        )
        time_label.pack(side="left", padx=(8, 4))

        # Command text
        cmd_text = command[:35] + "..." if len(command) > 35 else command
        cmd_label = ctk.CTkLabel(
            item_frame,
            text=cmd_text,
            font=("Inter", 10),
            text_color=color_map.get(status, TEXT_SECONDARY),
            anchor="w",
        )
        cmd_label.pack(side="left", fill="x", expand=True)

        # Status dot
        if status == "processing":
            dot = ctk.CTkLabel(
                item_frame,
                text="●",
                font=("Inter", 8),
                text_color=ACCENT_PRIMARY,
                width=10,
            )
            dot.pack(side="right", padx=5)

        self.history_items.append(item_frame)

        # Limit history
        if len(self.history_items) > MAX_HISTORY_ITEMS:
            self.history_items[0].destroy()
            self.history_items.pop(0)

        # Auto-scroll
        self.scroll_frame._parent_canvas.yview_moveto(1.0)


# --- SETTINGS PANEL (REFINED) ---
class SettingsPanel(ctk.CTkToplevel):
    """Clean, modern settings panel."""

    def __init__(self, vera_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vera = vera_instance
        self.geometry("320x420")
        self.title("Settings")
        self.attributes("-topmost", True)
        self.configure(fg_color=BG_DARK)

        # Main container
        container = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0)
        container.pack(fill="both", expand=True, padx=1, pady=1)

        # Title
        title = ctk.CTkLabel(
            container,
            text="Settings",
            font=("Inter", 18, "bold"),
            text_color=TEXT_PRIMARY,
        )
        title.pack(pady=(20, 10))

        # Sections
        self._create_section(container, "Appearance")

        # Theme buttons
        theme_frame = ctk.CTkFrame(container, fg_color="transparent")
        theme_frame.pack(pady=10, padx=20, fill="x")

        themes = [
            ("Azure", ACCENT_PRIMARY),
            ("Mint", "#00ff88"),
            ("Amber", "#ffa500"),
            ("Rose", "#ff4466"),
        ]

        for name, color in themes:
            btn = ctk.CTkButton(
                theme_frame,
                text=name,
                width=60,
                height=32,
                fg_color=color,
                hover_color=self._darken_color(color),
                command=lambda c=color: self.vera.change_theme(c),
                corner_radius=6,
                font=("Inter", 11),
            )
            btn.pack(side="left", padx=4, expand=True)

        self._create_section(container, "Features")

        # Toggle switches
        self.show_waveform = tk.BooleanVar(value=SOUNDDEVICE_AVAILABLE)
        self._create_switch(
            container, "Audio Visualizer", self.show_waveform, self.on_toggle_waveform
        )

        self.show_history = tk.BooleanVar(value=True)
        self._create_switch(
            container, "Command History", self.show_history, self.on_toggle_history
        )

        # Close button
        close_btn = ctk.CTkButton(
            container,
            text="Close",
            command=self.destroy,
            fg_color=BORDER_SUBTLE,
            hover_color=BG_HOVER,
            height=36,
            corner_radius=8,
            font=("Inter", 12),
        )
        close_btn.pack(pady=20, padx=20, fill="x")

    def _create_section(self, parent, title):
        """Create section header."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(15, 5), padx=20)

        label = ctk.CTkLabel(
            frame, text=title, font=("Inter", 12, "bold"), text_color=TEXT_SECONDARY
        )
        label.pack(anchor="w")

        separator = ctk.CTkFrame(frame, height=1, fg_color=BORDER_SUBTLE)
        separator.pack(fill="x", pady=(5, 0))

    def _create_switch(self, parent, label_text, variable, command):
        """Create a toggle switch."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5, padx=20)

        label = ctk.CTkLabel(
            frame, text=label_text, font=("Inter", 11), text_color=TEXT_PRIMARY
        )
        label.pack(side="left")

        switch = ctk.CTkSwitch(
            frame,
            text="",
            variable=variable,
            command=command,
            width=44,
            height=24,
            progress_color=ACCENT_PRIMARY,
            button_color=TEXT_PRIMARY,
            fg_color=BORDER_SUBTLE,
        )
        switch.pack(side="right")

    def _darken_color(self, hex_color, factor=0.7):
        """Darken a hex color."""
        rgb = tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
        darker = tuple(int(c * factor) for c in rgb)
        return f"#{darker[0]:02x}{darker[1]:02x}{darker[2]:02x}"

    def on_toggle_waveform(self):
        if SOUNDDEVICE_AVAILABLE:
            if self.show_waveform.get():
                self.vera.waveform.pack(before=self.vera.avatar_container, pady=(0, 10))
            else:
                self.vera.waveform.pack_forget()

    def on_toggle_history(self):
        if self.show_history.get():
            self.vera.history_panel.pack(side="top", fill="both", expand=True, pady=10)
        else:
            self.vera.history_panel.pack_forget()


# --- IMAGE FETCHER ---
class ImageFetcher:
    def __init__(self, max_workers=3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    @lru_cache(maxsize=32)
    def search_and_download(self, query):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(query, max_results=1))
                if results:
                    img_url = results[0]["image"]
                    response = requests.get(
                        img_url, timeout=NETWORK_TIMEOUT, stream=True
                    )
                    response.raise_for_status()

                    img_data = BytesIO()
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        downloaded += len(chunk)
                        if downloaded > MAX_IMAGE_SIZE:
                            return None
                        img_data.write(chunk)

                    img_data.seek(0)
                    return Image.open(img_data)
        except Exception as e:
            print(f"!! IMAGE ERROR: {e}")
        return None

    def shutdown(self):
        self.executor.shutdown(wait=False)


# --- POPUPS (REFINED) ---
class MediaPopup(ctk.CTkToplevel):
    def __init__(self, pil_image, title="Visual", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("420x450")
        self.title(title)
        self.attributes("-topmost", True)
        self.configure(fg_color=BG_DARK)

        # Card container
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        # Image
        display_image = pil_image.copy()
        display_image.thumbnail(THUMBNAIL_SIZE)

        self.photo = ctk.CTkImage(
            light_image=display_image, dark_image=display_image, size=display_image.size
        )

        self.lbl = ctk.CTkLabel(card, text="", image=self.photo)
        self.lbl.pack(expand=True, fill="both", padx=15, pady=15)

        # Caption
        self.lbl_cap = ctk.CTkLabel(
            card, text=title, font=("Inter", 11), text_color=TEXT_SECONDARY
        )
        self.lbl_cap.pack(pady=(0, 12))


class ResultPopup(ctk.CTkToplevel):
    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("600x500")
        self.title("Output")
        self.attributes("-topmost", True)
        self.configure(fg_color=BG_DARK)

        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        self.textbox = ctk.CTkTextbox(
            card,
            font=("JetBrains Mono", 12),
            wrap="word",
            fg_color=BG_DARK,
            text_color=TEXT_PRIMARY,
            border_width=0,
        )
        self.textbox.pack(fill="both", expand=True, padx=15, pady=15)
        self.textbox.insert("0.0", text)
        self.textbox.configure(state="disabled")


# --- MAIN INTERFACE ---
class VeraHologram:
    def __init__(self):
        self.root = tk.Tk()
        self.fetcher = ImageFetcher()
        self.vision_process = None
        self._cleanup_registered = False
        self.current_accent = ACCENT_PRIMARY
        self.audio_monitor_active = False

        # Window setup
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", TRANS_KEY)
        self.root.configure(bg=TRANS_KEY)

        # Positioning
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        window_w, window_h = 360, 580
        x_pos = screen_w - window_w - 30
        y_pos = screen_h - window_h - 50
        self.root.geometry(f"{window_w}x{window_h}+{x_pos}+{y_pos}")

        # Drag support
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        # === MAIN CONTAINER ===
        self.main_frame = ctk.CTkFrame(
            self.root,
            fg_color=BG_DARK,
            corner_radius=20,
            border_width=1,
            border_color=BORDER_SUBTLE,
        )
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # === TOP BAR ===
        top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=50)
        top_bar.pack(fill="x", padx=15, pady=(15, 0))
        top_bar.pack_propagate(False)

        # Title
        title_label = ctk.CTkLabel(
            top_bar, text="VERA", font=("Inter", 16, "bold"), text_color=TEXT_PRIMARY
        )
        title_label.pack(side="left")

        # Settings button
        self.settings_btn = ctk.CTkButton(
            top_bar,
            text="⚙",
            width=36,
            height=36,
            corner_radius=18,
            fg_color=BG_CARD,
            hover_color=BG_HOVER,
            command=self.open_settings,
            font=("Inter", 16),
            text_color=TEXT_SECONDARY,
        )
        self.settings_btn.pack(side="right")

        # === CONTENT AREA ===
        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=10)

        # Command History (collapsible)
        self.history_panel = CommandHistory(content, height=150)
        self.history_panel.pack(side="top", fill="both", expand=True, pady=10)

        # Avatar Container
        self.avatar_container = ctk.CTkFrame(content, fg_color="transparent")
        self.avatar_container.pack(pady=(10, 5))

        # Outer glow ring
        self.glow_canvas = tk.Canvas(
            self.avatar_container,
            width=110,
            height=110,
            bg=BG_DARK,
            highlightthickness=0,
        )
        self.glow_canvas.pack()

        # Avatar frame
        self.avatar_frame = ctk.CTkFrame(
            self.avatar_container,
            width=100,
            height=100,
            corner_radius=50,
            fg_color="#000000",  # <--- CHANGED: Set this to pure black
            border_width=2,
            border_color=self.current_accent,
        )
        self.avatar_frame.place(
            in_=self.glow_canvas, relx=0.5, rely=0.5, anchor="center"
        )

        # <--- CHANGED: Set bg to "#000000" to match the frame and the GIF
        self.lbl_gif = tk.Label(self.avatar_frame, bg="#000000", borderwidth=0)
        self.lbl_gif.place(relx=0.5, rely=0.5, anchor="center")

        # Load GIF
        self.frames = None
        self.frame_cycle = None
        self._animation_id = None
        self.glow_phase = 0

        try:
            self.load_gif("head.gif")
        except Exception as e:
            print(f"!! GIF ERROR: {e}")
            self.lbl_gif.configure(
                text="V", font=("Inter", 28, "bold"), fg=self.current_accent, bg=BG_CARD
            )

        # Start glow animation
        self.animate_glow()

        # Waveform
        self.waveform = WaveformVisualizer(content)
        if SOUNDDEVICE_AVAILABLE:
            self.waveform.pack(pady=(0, 10))

        # Speech Bubble
        self.bubble = ctk.CTkFrame(
            content,
            fg_color=BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_SUBTLE,
        )

        self.lbl_text = ctk.CTkLabel(
            self.bubble,
            text="",
            font=("Inter", 13),
            text_color=TEXT_PRIMARY,
            wraplength=280,
            justify="left",
        )
        self.lbl_text.pack(padx=18, pady=14)

        # Hooks
        processor.gui_popup_hook = self.thread_safe_display
        processor.toggle_hand_mouse = self.toggle_vision

        # Cleanup
        self._register_cleanup()

        # Start
        self.flash_status(self.current_accent, "ready")
        threading.Thread(target=self.run_voice_loop, daemon=True).start()

        if SOUNDDEVICE_AVAILABLE:
            threading.Thread(target=self.audio_monitor, daemon=True).start()

        self.root.mainloop()

    # === ANIMATIONS ===
    def animate_glow(self):
        """Smooth pulsing glow effect."""
        try:
            self.glow_canvas.delete("glow")
            self.glow_phase = (self.glow_phase + 0.05) % (2 * np.pi)

            # Subtle pulse
            radius = 50 + 3 * np.sin(self.glow_phase)
            opacity = int(30 + 15 * np.sin(self.glow_phase))

            # Draw soft glow
            color = self._add_alpha(self.current_accent, opacity)
            self.glow_canvas.create_oval(
                55 - radius,
                55 - radius,
                55 + radius,
                55 + radius,
                outline=color,
                width=2,
                tags="glow",
            )

            self.root.after(50, self.animate_glow)
        except:
            pass

    def _add_alpha(self, hex_color, alpha):
        """Add transparency effect (simulated with darker shade)."""
        rgb = tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
        adjusted = tuple(int(c * (alpha / 100)) for c in rgb)
        return f"#{adjusted[0]:02x}{adjusted[1]:02x}{adjusted[2]:02x}"

    def load_gif(self, filename):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(os.path.dirname(current_dir), "assets", filename)

        img = Image.open(path)
        self.frames = []

        for frame in ImageSequence.Iterator(img):
            resized = frame.copy()
            resized.thumbnail(GIF_FRAME_SIZE, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(resized)
            self.frames.append(photo)

        img.close()
        self.frame_cycle = itertools.cycle(self.frames)
        self.animate_gif()

    def animate_gif(self):
        try:
            if self.lbl_gif.winfo_exists() and self.frame_cycle:
                self.lbl_gif.config(image=next(self.frame_cycle))
                self._animation_id = self.root.after(60, self.animate_gif)
        except:
            pass

    # === AUDIO MONITORING ===
    def audio_monitor(self):
        if not SOUNDDEVICE_AVAILABLE:
            return

        self.audio_monitor_active = True

        def audio_callback(indata, frames, time_info, status):
            if self.audio_monitor_active:
                volume = np.linalg.norm(indata) * 10
                self.waveform.update_audio(min(volume, 100))

        try:
            with sd.InputStream(callback=audio_callback):
                while self.audio_monitor_active:
                    sd.sleep(100)
        except Exception as e:
            print(f"!! AUDIO MONITOR ERROR: {e}")

    # === CONTROLS ===
    def change_theme(self, color):
        self.current_accent = color
        self.avatar_frame.configure(border_color=color)
        if hasattr(self.lbl_gif, "config"):
            try:
                self.lbl_gif.configure(fg=color)
            except:
                pass

    def open_settings(self):
        SettingsPanel(self)

    def start_move(self, event):
        self.x, self.y = event.x, event.y

    def do_move(self, event):
        nx = self.root.winfo_x() + (event.x - self.x)
        ny = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{nx}+{ny}")

    def flash_status(self, color, state="ready"):
        self.current_accent = color
        if self.avatar_frame.winfo_exists():
            self.avatar_frame.configure(border_color=color)
            if state == "ready":
                self.bubble.configure(border_color=BORDER_SUBTLE)
            else:
                self.bubble.configure(border_color=color)

    # === TEXT DISPLAY ===
    def thread_safe_display(self, text):
        self.root.after(0, lambda: self.process_output(text))

    def process_output(self, text):
        img_match = IMAGE_TAG_PATTERN.search(text)
        clean_text = IMAGE_TAG_PATTERN.sub("", text).strip()

        if len(clean_text) > LONG_TEXT_THRESHOLD:
            ResultPopup(clean_text)
            self.show_bubble("View full output →")
        else:
            if clean_text:
                self.show_bubble(clean_text)

        if img_match:
            try:
                query = img_match.group(1).strip()
                self.fetcher.executor.submit(self.render_image, query)
            except Exception as e:
                print(f"!! REGEX ERROR: {e}")

    def render_image(self, query):
        img = self.fetcher.search_and_download(query)
        if img:
            self.root.after(0, lambda: MediaPopup(img, title=query))

    def show_bubble(self, text):
        self.bubble.pack(side="bottom", pady=(10, 15))
        self.lbl_text.configure(text=text)

        read_time = max(MIN_BUBBLE_TIME, len(text) * BUBBLE_TIME_PER_CHAR)
        self.root.after(read_time, self.hide_bubble)

    def hide_bubble(self):
        self.bubble.pack_forget()

    # === VISION ===
    def toggle_vision(self):
        if self.vision_process:
            try:
                self.vision_process.terminate()
                self.vision_process.wait(timeout=2)
            except:
                self.vision_process.kill()
            finally:
                self.vision_process = None
                processor.speak("Vision Offline.")
                self.flash_status(ACCENT_PRIMARY, "ready")
            return

        script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "core", "hand_mouse_equator.py"
        )

        if not os.path.exists(script_path):
            return

        processor.speak("Vision Engaged.")
        self.flash_status(ACCENT_SUCCESS, "active")

        try:
            self.vision_process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            print(f"!! VISION ERROR: {e}")

    # === VOICE LOOP ===
    def run_voice_loop(self):
        r = sr.Recognizer()

        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.8)
                processor.speak("V.E.R.A. Systems online. Listening.")
                self.history_panel.add_command("System online", "success")

                while True:
                    try:
                        if SOUNDDEVICE_AVAILABLE:
                            self.waveform.set_listening(True)
                        self.flash_status(TEXT_SECONDARY, "listening")

                        audio = r.listen(source, timeout=None, phrase_time_limit=12)

                        self.flash_status(ACCENT_PRIMARY, "processing")
                        cmd = r.recognize_google(audio, language="en-ZA").lower()
                        print(f"RECOGNIZED: {cmd}")

                        self.history_panel.add_command(cmd, "processing")
                        processor.process_command(cmd, audio_data=audio, source=source)
                        self.history_panel.add_command(cmd, "success")

                        if SOUNDDEVICE_AVAILABLE:
                            self.waveform.set_listening(False)
                        self.flash_status(self.current_accent, "ready")

                    except sr.UnknownValueError:
                        if SOUNDDEVICE_AVAILABLE:
                            self.waveform.set_listening(False)
                        self.flash_status(self.current_accent, "ready")
                    except Exception as e:
                        print(f"!! VOICE ERROR: {e}")
                        if SOUNDDEVICE_AVAILABLE:
                            self.waveform.set_listening(False)
                        self.flash_status(self.current_accent, "ready")

        except KeyboardInterrupt:
            print("Stopped")
        finally:
            self._cleanup()

    # === CLEANUP ===
    def _register_cleanup(self):
        if not self._cleanup_registered:
            atexit.register(self._cleanup)
            self.root.protocol("WM_DELETE_WINDOW", self._cleanup)
            self._cleanup_registered = True

    def _cleanup(self):
        self.audio_monitor_active = False

        try:
            if self.vision_process:
                self.vision_process.terminate()
                self.vision_process.wait(timeout=2)
        except:
            pass

        try:
            self.fetcher.shutdown()
        except:
            pass

        if self._animation_id:
            try:
                self.root.after_cancel(self._animation_id)
            except:
                pass


if __name__ == "__main__":
    VeraHologram()
