from AppOpener import open as start_app
from AppOpener import close as kill_app
import os

# 1. FAST LOOKUP LIST (Add your favorites here)
DIRECT_PATHS = {
    "notepad": "notepad.exe",
    "chrome": "chrome.exe",
    "calculator": "calc.exe",
    "edge": "msedge.exe",
    "code": "code.exe",
}


def open_application(app_name):
    clean_name = app_name.lower().strip()

    # STRATEGY A: Check Favorites (Instant)
    if clean_name in DIRECT_PATHS:
        try:
            os.startfile(DIRECT_PATHS[clean_name])
            return f"Opening {clean_name} (Fast)."
        except:
            pass  # Fallback if path is wrong

    # STRATEGY B: Ask the Concierge (Slower but smart)
    try:
        start_app(app_name, match_closest=True, output=False)
        return f"Opening {app_name}."
    except:
        return f"I couldn't find {app_name}."


def close_application(app_name):
    # (Keep your existing close logic here)
    try:
        kill_app(app_name, match_closest=True, output=False)
        return f"Closing {app_name}."
    except:
        return f"Could not close {app_name}."
