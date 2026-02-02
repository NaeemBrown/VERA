import os
import speedtest
import webbrowser
import psutil


# --- FOLDER OPS ---
def open_folder(folder_name):
    """Scans Desktop/Docs/Downloads for a folder and opens it."""
    try:
        user_path = os.path.expanduser("~")
        search_locations = [
            "Desktop",
            "Documents",
            "Downloads",
            "Music",
            "Pictures",
            "Videos",
        ]

        for loc in search_locations:
            target = os.path.join(user_path, loc, folder_name)
            # Case insensitive check could be added here, but exact match is faster
            if os.path.exists(target) and os.path.isdir(target):
                os.startfile(target)
                return True
        return False
    except Exception as e:
        print(f"Folder Error: {e}")
        return False


# --- NETWORK OPS ---
def run_speedtest():
    """Runs a network speed test. WARNING: This blocks for 10-20 seconds."""
    try:
        print("DEBUG: Starting Speedtest...")
        st = speedtest.Speedtest()
        st.get_best_server()

        # Measure
        down = st.download() / 1_000_000  # Convert to Mbps
        up = st.upload() / 1_000_000

        result = f"Download: {round(down, 1)} Mbps. Upload: {round(up, 1)} Mbps."
        print(f"DEBUG: {result}")
        return result

    except Exception as e:
        print(f"Speedtest Error: {e}")
        return "I couldn't connect to the speed test server."


# --- BROWSER OPS ---
def open_website(url):
    """Opens a URL in default browser (Safety Wrapper)."""
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)


# --- SYSTEM MONITOR ---
def get_battery_status():
    battery = psutil.sensors_battery()
    if not battery:
        return "Battery info unavailable."

    plugged = "Plugged in" if battery.power_plugged else "On battery"
    return f"{plugged}, {battery.percent}% remaining."
