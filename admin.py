import psutil
import speedtest
import requests


def get_system_status():
    """Returns a Dictionary of stats + a Speech string."""
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent

    # Try to get battery (Desktop PCs might return None)
    battery = psutil.sensors_battery()
    bat_percent = battery.percent if battery else 100

    speech = f"CPU is at {cpu} percent. Memory is at {ram} percent."

    return {"cpu": cpu, "ram": ram, "battery": bat_percent, "speech": speech}


def run_speedtest():
    # (Same as before)
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        down = st.download() / 1_000_000
        up = st.upload() / 1_000_000
        return f"Download: {round(down, 1)} Mbps. Upload: {round(up, 1)} Mbps."
    except:
        return "Speedtest failed."
