import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import itertools
import threading
import speech_recognition as sr
import customtkinter as ctk
import main
import time

# --- CONFIG ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")


class ResultPopup(ctk.CTkToplevel):
    """A sleek, modern popup for reading long answers."""

    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("500x300")
        self.title("V.E.R.A. Output")
        self.attributes("-topmost", True)

        # Text Area
        self.textbox = ctk.CTkTextbox(self, font=("Roboto", 16), wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("0.0", text)
        self.textbox.configure(state="disabled")


class VeraHologram:
    def __init__(self):
        self.root = tk.Tk()

        # --- 1. WINDOW SETUP (The "Invisible" Container) ---
        self.root.overrideredirect(True)  # No borders/title bar
        self.root.attributes("-topmost", True)  # Always on top
        self.root.wm_attributes(
            "-transparentcolor", "black"
        )  # THE MAGIC: Black = Invisible
        self.root.configure(bg="black")

        # Position: Bottom Right
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"400x450+{screen_w - 420}+{screen_h - 500}")

        # --- 2. DRAGGABLE WINDOW ---
        # Since we have no title bar, we need to let you drag the head
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        # --- 3. THE HOLOGRAM (GIF) ---
        self.lbl = tk.Label(self.root, bg="black")
        self.lbl.pack()

        try:
            self.load_gif("head.gif")  # <--- YOUR SPIRAL/HEAD
        except:
            print("ERROR: Could not find 'head.gif'. Using text fallback.")
            self.lbl.configure(
                text="[ NO GIF ]", fg="cyan", bg="black", font=("Arial", 20)
            )

        # --- 4. STATUS TEXT (Floating below head) ---
        self.status_label = tk.Label(
            self.root,
            text="INITIALIZING",
            font=("Consolas", 14, "bold"),
            fg="#00FF00",  # Hacker Green
            bg="black",
        )
        self.status_label.pack(pady=10)

        # --- 5. HOOKS INTO MAIN ---
        # Override the Popup logic in main.py
        main.gui_popup_hook = self.show_popup_window

        # Start Voice Loop
        self.thread = threading.Thread(target=self.run_voice_loop)
        self.thread.daemon = True
        self.thread.start()

        self.root.mainloop()

    def load_gif(self, path):
        """Loads and animates the GIF."""
        img = Image.open(path)
        self.frames = []
        for frame in ImageSequence.Iterator(img):
            # Resize to fit nicely
            frame = frame.resize((300, 300))
            self.frames.append(ImageTk.PhotoImage(frame))

        self.frame_cycle = itertools.cycle(self.frames)
        self.animate()

    def animate(self):
        """Updates the GIF frame."""
        try:
            self.lbl.config(image=next(self.frame_cycle))
            self.root.after(30, self.animate)  # 30ms = ~30 FPS
        except:
            pass

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def show_popup_window(self, text):
        """Spawns the modern CTk window for text."""
        # Use .after to interact with GUI thread safely
        self.root.after(0, lambda: ResultPopup(text))

    def update_status(self, text, color="#00FF00"):
        self.root.after(0, lambda: self.status_label.config(text=text, fg=color))

    def run_voice_loop(self):
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 0.5
        recognizer.energy_threshold = 300

        with sr.Microphone() as source:
            self.update_status("CALIBRATING...", "cyan")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            main.speak("Systems online.")

            while True:
                try:
                    self.update_status("LISTENING", "white")
                    audio = recognizer.listen(source, timeout=None)

                    self.update_status("PROCESSING", "orange")
                    command = recognizer.recognize_google(
                        audio, language="en-ZA"
                    ).lower()

                    print(f"User: {command}")  # Debug to console
                    main.process_command(command, source)

                except Exception as e:
                    # e.g., Silence / Timeout
                    continue


if __name__ == "__main__":
    app = VeraHologram()
