import os
import datetime
import pyautogui
import ctypes
import threading
import time
import pyperclip
import shutil
import webbrowser


# --- FILES & NOTES ---
def save_note(text):
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        folder = os.path.join(desktop, "V.E.R.A. Notes")
        if not os.path.exists(folder):
            os.makedirs(folder)

        filepath = os.path.join(folder, "notes_log.txt")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        with open(filepath, "a") as f:
            f.write(f"[{timestamp}] {text}\n")
        return True
    except:
        return False


def take_screenshot():
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        folder = os.path.join(desktop, "V.E.R.A. Screenshots")
        if not os.path.exists(folder):
            os.makedirs(folder)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = os.path.join(folder, f"Shot_{timestamp}.png")

        pyautogui.screenshot(path)
        return True
    except:
        return False


def lock_system():
    ctypes.windll.user32.LockWorkStation()


# --- MEDIA CONTROLS ---
def media_play_pause():
    pyautogui.press("playpause")


def media_next():
    pyautogui.press("nexttrack")


def media_prev():
    pyautogui.press("prevtrack")


def play_youtube(song):
    # LAZY IMPORT: Speeds up startup significantly
    import pywhatkit

    try:
        pywhatkit.playonyt(song)
    except:
        webbrowser.open(f"https://www.youtube.com/results?search_query={song}")


def play_music(song_name):
    """Searches YouTube Music for 'Song by Artist' and auto-plays."""
    try:
        # LAZY IMPORT
        from ytmusicapi import YTMusic

        yt = YTMusic()
        # filter="songs" ensures we get audio tracks, not videos
        results = yt.search(song_name, filter="songs")

        if results:
            video_id = results[0]["videoId"]
            url = f"https://music.youtube.com/watch?v={video_id}"
            webbrowser.open(url)
            return True
        else:
            url = f"https://music.youtube.com/search?q={song_name.replace(' ', '+')}"
            webbrowser.open(url)
            return False

    except ImportError:
        print("Error: 'ytmusicapi' not installed.")
        webbrowser.open(f"https://music.youtube.com/search?q={song_name}")
    except Exception as e:
        print(f"Music API Error: {e}")
        webbrowser.open(f"https://music.youtube.com/search?q={song_name}")


# --- UTILITIES ---
def start_timer(seconds, message, speak_func):
    def timer_thread():
        time.sleep(seconds)
        speak_func(f"ALARM: {message}")

    t = threading.Thread(target=timer_thread)
    t.daemon = True
    t.start()


def read_clipboard(speak_func):
    try:
        text = pyperclip.paste()
        if text:
            if len(text) > 500:
                speak_func("The text is too long, reading the first part.")
                text = text[:500]
            speak_func(text)
        else:
            speak_func("Clipboard is empty.")
    except:
        speak_func("I couldn't read the clipboard.")


# --- THE JANITOR ---
def clean_downloads(speak_func):
    """Sorts files in Downloads into categories."""
    try:
        user_path = os.path.expanduser("~")
        downloads_path = os.path.join(user_path, "Downloads")

        extensions = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
            "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".csv"],
            "Installers": [".exe", ".msi", ".zip", ".rar", ".7z"],
            "Audio": [".mp3", ".wav", ".flac"],
            "Video": [".mp4", ".mkv", ".mov"],
        }

        moved_count = 0

        for filename in os.listdir(downloads_path):
            file_path = os.path.join(downloads_path, filename)

            if os.path.isfile(file_path):
                file_ext = os.path.splitext(filename)[1].lower()

                # Check categories
                for category, exts in extensions.items():
                    if file_ext in exts:
                        target_folder = os.path.join(downloads_path, category)
                        if not os.path.exists(target_folder):
                            os.makedirs(target_folder)

                        try:
                            shutil.move(
                                file_path, os.path.join(target_folder, filename)
                            )
                            moved_count += 1
                        except PermissionError:
                            print(f"Skipped {filename} (In use)")
                        except Exception as e:
                            print(f"Error moving {filename}: {e}")
                        break

        speak_func(f"Clean up complete. I moved {moved_count} files.")

    except Exception as e:
        speak_func(f"I encountered an error: {e}")
