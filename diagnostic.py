import psutil
import time


def report_system_status():
    # 1. Get Battery (if on laptop)
    battery = psutil.sensors_battery()
    plugged = "AC Power" if battery.power_plugged else "Battery"

    # 2. Get CPU & RAM
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent

    # 3. Formulate the "Speech"
    status_report = (
        f">> SYSTEM STATUS: {plugged} Mode.\n"
        f">> CPU Load: {cpu_usage}%\n"
        f">> Memory Integrity: {ram_usage}%"
    )

    print(status_report)

    # Optional: Trigger warning if load is high
    if ram_usage > 90:
        print(">> WARNING: MEMORY CRITICAL. RECOMMEND PURGING CHROME TABS.")


if __name__ == "__main__":
    report_system_status()
