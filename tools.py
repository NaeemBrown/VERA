import os
import webbrowser

# Map spoken names to actual .exe names
APP_MAP = {
    "notepad": "notepad.exe",
    "discord": "discord.exe",
    "calculator": "calc.exe",
    "chrome": "chrome.exe",
    "spotify": "spotify.exe",
    "vsc": "code.exe",
    "code": "code.exe"
}

def open_smart(command, speak_func):
    """Intelligently decides if the user wants a website, app, or folder."""
    target = command.replace("open", "").strip()
    
    # 1. Websites
    if "google" in target:
        speak_func("Opening Google.")
        webbrowser.open("https://google.com")
        return
    elif "youtube" in target:
        speak_func("Opening YouTube.")
        webbrowser.open("https://youtube.com")
        return
    elif "music" in target:
        speak_func("Opening YouTube Music.")
        webbrowser.open("https://music.youtube.com")
        return
    
    # 2. Apps
    # Check if the target matches any known app nickname
    for app_name, exe_name in APP_MAP.items():
        if app_name in target:
            speak_func(f"Opening {app_name}.")
            # 'start' command lets Windows find the path automatically
            os.system(f"start {exe_name}")
            return

    # 3. Folders (Fallback)
    if open_folder(target):
        speak_func("Folder opened.")
    else:
        speak_func(f"I couldn't find {target}.")

def open_folder(folder_name):
    """Scans Desktop/Docs/Downloads for a folder and opens it."""
    user_path = os.path.expanduser("~")
    search_locations = ["Desktop", "Documents", "Downloads", "Music", "Pictures"]
    
    for loc in search_locations:
        target = os.path.join(user_path, loc, folder_name)
        if os.path.exists(target) and os.path.isdir(target):
            os.startfile(target)
            return True
    return False

def open_website(url):
    """Opens a URL in default browser."""
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)

def close_app(command, speak_func):
    """Force closes an app by name."""
    target = command.replace("close", "").strip()
    speak_func(f"Closing {target}.")
    
    # Look up the exe name, or guess it matches the spoken name
    exe_name = APP_MAP.get(target, f"{target}.exe")
    
    try:
        os.system(f"taskkill /f /im {exe_name}")
    except:
        pass

def open_app(app_name):
    """Direct launcher for internal use (like Work Mode)."""
    exe_name = APP_MAP.get(app_name, app_name)
    os.system(f"start {exe_name}")