import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageSequence
import itertools
import threading
import speech_recognition as sr
import main
import time
import os
import subprocess

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class JarvisUI:
    def __init__(self):
        self.root = tk.Tk()

        # --- WINDOW SETUP ---
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "#000001")
        self.root.configure(bg="#000001")

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        window_w = 700
        window_h = 250
        x_pos = screen_w - window_w - 50
        y_pos = screen_h - window_h - 100
        self.root.geometry(f"{window_w}x{window_h}+{x_pos}+{y_pos}")

        # --- MAIN CARD ---
        self.card = ctk.CTkFrame(
            self.root,
            width=window_w,
            height=window_h,
            corner_radius=20,
            fg_color="black",
            bg_color="#000001",
            border_width=2,
            border_color="#333333",
        )
        self.card.pack(fill="both", expand=True)

        # --- LEFT COLUMN (AVATAR) ---
        self.frame_left = ctk.CTkFrame(self.card, width=200, fg_color="transparent")
        self.frame_left.pack(side="left", fill="y", padx=20, pady=20)

        self.lbl_gif = tk.Label(self.frame_left, bg="black", borderwidth=0)
        self.lbl_gif.pack(pady=(10, 0))

        self.lbl_status = ctk.CTkLabel(
            self.frame_left,
            text="ONLINE",
            font=("Consolas", 16, "bold"),
            text_color="gray",
        )
        self.lbl_status.pack(side="bottom", pady=10)

        self.separator = ctk.CTkFrame(
            self.card, width=2, height=150, fg_color="#333333"
        )
        self.separator.pack(side="left", fill="y", pady=40)

        # --- RIGHT COLUMN (DYNAMIC CONTENT) ---
        self.frame_right = ctk.CTkFrame(self.card, fg_color="transparent")
        self.frame_right.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        self.lbl_header = ctk.CTkLabel(
            self.frame_right,
            text="V.E.R.A. OS v1.0",
            font=("Arial", 12, "bold"),
            text_color="#00BFFF",
            anchor="w",
        )
        self.lbl_header.pack(fill="x")

        # 1. TEXT MODE WIDGET
        self.lbl_text = ctk.CTkLabel(
            self.frame_right,
            text="",
            font=("Roboto", 18),
            text_color="white",
            wraplength=400,
            justify="left",
            anchor="nw",
        )
        self.lbl_text.pack(fill="both", expand=True, pady=(10, 0))

        # 2. STATS MODE WIDGET
        self.frame_stats = ctk.CTkFrame(self.frame_right, fg_color="transparent")

        # --- GIF LOADING ---
        try:
            self.load_gif("head.gif")
        except:
            self.lbl_gif.configure(text="[IMG]", fg="white")

        # --- HOOKS ---
        main.gui_popup_hook = self.start_typewriter
        main.gui_stats_hook = self.show_stats_dashboard
        main.gui_cam_hook = self.launch_vision_system  # Trigger vision via VENV

        # Start Voice Loop in Thread
        self.thread = threading.Thread(target=self.run_voice_loop)
        self.thread.daemon = True
        self.thread.start()

        self.root.mainloop()

    def launch_vision_system(self):
        """Forces the use of the 3.12 VENV to avoid 3.13 library errors."""
        venv_path = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
        if os.path.exists(venv_path):
            subprocess.Popen(
                [venv_path, "hand_mouse_equator.py"],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            return "Vision system initiated."
        else:
            return "VENV not found. Manual intervention required."

    def show_stats_dashboard(self, data):
        self.root.after(0, lambda: self._build_stats_ui(data))

    def _build_stats_ui(self, data):
        self.lbl_text.pack_forget()
        for widget in self.frame_stats.winfo_children():
            widget.destroy()
        self.frame_stats.pack(fill="both", expand=True, pady=(10, 0))

        def draw_bar(label, value, color):
            row = ctk.CTkFrame(self.frame_stats, fg_color="transparent")
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(
                row, text=label, font=("Consolas", 14, "bold"), width=60, anchor="w"
            ).pack(side="left")
            bar = ctk.CTkProgressBar(
                row, height=15, corner_radius=5, progress_color=color
            )
            bar.set(value / 100)
            bar.pack(side="left", fill="x", expand=True, padx=10)
            ctk.CTkLabel(
                row, text=f"{value}%", font=("Consolas", 14), width=40, anchor="e"
            ).pack(side="right")

        draw_bar("CPU", data.get("cpu", 0), "#00BFFF")
        draw_bar("RAM", data.get("ram", 0), "#00FF00")
        draw_bar("PWR", data.get("battery", 0), "#FFA500")

    def reset_to_text_mode(self):
        self.frame_stats.pack_forget()
        self.lbl_text.pack(fill="both", expand=True, pady=(10, 0))

    def start_typewriter(self, text):
        self.root.after(0, self.reset_to_text_mode)
        self.root.after(0, lambda: self.lbl_text.configure(text=""))
        self.type_char(text, 0)

    def load_gif(self, path):
        img = Image.open(path)
        self.frames = []
        for frame in ImageSequence.Iterator(img):
            frame = frame.resize((140, 140))
            self.frames.append(ImageTk.PhotoImage(frame))
        self.frame_cycle = itertools.cycle(self.frames)
        self.animate()

    def animate(self):
        try:
            self.lbl_gif.config(image=next(self.frame_cycle))
            self.root.after(30, self.animate)
        except:
            pass

    def type_char(self, full_text, index):
        if index < len(full_text):
            self.lbl_text.configure(text=full_text[: index + 1])
            self.root.after(15, lambda: self.type_char(full_text, index + 1))

    def update_status(self, text, color="white"):
        self.root.after(
            0, lambda: self.lbl_status.configure(text=text, text_color=color)
        )

    def run_voice_loop(self):
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 0.8
        with sr.Microphone() as source:
            self.update_status("CALIBRATING", "gray")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self.update_status("ONLINE", "#00FF00")
            main.speak("Interface ready.")
            while True:
                try:
                    self.update_status("LISTENING", "white")
                    audio = recognizer.listen(source, timeout=None)
                    self.update_status("PROCESSING", "cyan")
                    command = recognizer.recognize_google(
                        audio, language="en-ZA"
                    ).lower()
                    print(f"User: {command}")
                    main.process_command(command, source)
                    self.update_status("ONLINE", "#00FF00")
                except:
                    self.update_status("ONLINE", "#00FF00")
                    continue


if __name__ == "__main__":
    app = JarvisUI()
