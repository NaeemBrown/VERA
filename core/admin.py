import os
import sys
import ctypes


def shutdown_pc(speak_func):
    """Shuts down Windows after a 5-second delay."""
    speak_func("Initiating system shutdown sequence. Goodbye.")
    # /s = shutdown, /t 5 = 5 seconds delay
    os.system("shutdown /s /t 5")


def restart_pc(speak_func):
    """Restarts Windows."""
    speak_func("Rebooting system.")
    # /r = restart, /t 5 = 5 seconds delay
    os.system("shutdown /r /t 5")


def sleep_pc(speak_func):
    """Puts Windows to sleep."""
    speak_func("Entering sleep mode.")
    # Call the Windows API for Sleep
    ctypes.windll.powrprof.SetSuspendState(0, 1, 0)


def abort_shutdown(speak_func):
    """Cancels a pending shutdown/restart command."""
    os.system("shutdown /a")
    speak_func("Sequence aborted.")


def restart_vera():
    """Restarts the Python script itself (The AI)."""
    print(">> RESTARTING V.E.R.A. KERNEL...")
    # Re-executes the current python script
    os.execv(sys.executable, ["python"] + sys.argv)
