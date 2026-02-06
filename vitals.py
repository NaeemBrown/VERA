import psutil
import time

print(">> INITIALIZING V.E.R.A. DIAGNOSTICS...")

# 1. Get CPU Core Count (Logical vs Physical)
core_count = psutil.cpu_count(logical=False)
thread_count = psutil.cpu_count(logical=True)

print(f">> DETECTED HARDWARE: {core_count} Cores / {thread_count} Threads")

# 2. Get Memory (RAM) details
mem = psutil.virtual_memory()
total_gb = round(mem.total / (1024**3), 2)

print(f">> SYSTEM MEMORY: {total_gb} GB Installed")

# 3. Real-time loop (Ctrl+C to stop)
try:
    while True:
        # Read stats
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent

        # Fancy formatting
        status = "NORMAL"
        if cpu > 50 or ram > 80:
            status = "HIGH LOAD"

        print(f"STATUS: {status} | CPU: {cpu}% | RAM: {ram}%")
except KeyboardInterrupt:
    print("\n>> DIAGNOSTICS OFFLINE.")
