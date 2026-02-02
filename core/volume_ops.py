import threading
import time
import math
import pyautogui
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL, CoInitialize

# --- CONFIG ---
USE_PYCAW = True
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
except ImportError:
    USE_PYCAW = False
    print("WARNING: 'pycaw' not installed. Volume fading disabled.")


# --- INTERNAL HELPERS ---
def _get_volume_interface_safe():
    """Safely attempts to get the Windows Volume Interface."""
    if not USE_PYCAW:
        return None
    try:
        CoInitialize()  # Required for threads
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except:
        return None


def fade_volume(target_percent, duration=1.5):
    """
    The Smooth Engine: Slides volume to target_percent over 'duration' seconds.
    Run this in a thread to avoid freezing the UI!
    """
    volume = _get_volume_interface_safe()
    if not volume:
        return

    try:
        # Get start level (0.0 to 1.0)
        start_scalar = volume.GetMasterVolumeLevelScalar()
        target_scalar = target_percent / 100.0

        if abs(start_scalar - target_scalar) < 0.01:
            return

        steps = 30
        delay = duration / steps
        step_change = (target_scalar - start_scalar) / steps

        for i in range(steps):
            new_level = start_scalar + (step_change * (i + 1))
            new_level = max(0.0, min(1.0, new_level))
            volume.SetMasterVolumeLevelScalar(new_level, None)
            time.sleep(delay)

        volume.SetMasterVolumeLevelScalar(target_scalar, None)
    except:
        pass


# --- PUBLIC COMMAND HANDLER ---
def handle_volume_command(command, speak_func):
    """Decides what volume action to take."""

    # 1. Parse Target
    target = None
    if "mute" in command:
        target = "mute"
    elif "unmute" in command:
        target = "unmute"
    else:
        # Check for numbers
        words = command.split()
        for word in words:
            if word.isdigit():
                target = int(word)
                break

        # Check for Up/Down if no number
        if target is None:
            if "up" in command:
                target = "up"
            elif "down" in command:
                target = "down"

    if target is None:
        speak_func("I didn't catch the volume level.")
        return

    # 2. Execute (Threaded for smoothness)
    def volume_worker():
        volume = _get_volume_interface_safe()

        # --- PYCAW METHOD ---
        if volume:
            if target == "mute":
                is_muted = volume.GetMute()
                volume.SetMute(not is_muted, None)
                speak_func("Muted." if not is_muted else "Unmuted.")
            elif target == "unmute":
                volume.SetMute(0, None)
                speak_func("Unmuted.")
            elif isinstance(target, int):
                safe_target = max(0, min(100, target))
                speak_func(f"Volume {safe_target}%.")
                fade_volume(safe_target)
            elif target == "up":
                curr = volume.GetMasterVolumeLevelScalar() * 100
                fade_volume(min(100, curr + 15), duration=0.5)
            elif target == "down":
                curr = volume.GetMasterVolumeLevelScalar() * 100
                fade_volume(max(0, curr - 15), duration=0.5)

        # --- LEGACY METHOD (Fallback) ---
        else:
            if target == "mute" or target == "unmute":
                pyautogui.press("volumemute")
            elif target == "up":
                pyautogui.press("volumeup", presses=5)
            elif target == "down":
                pyautogui.press("volumedown", presses=5)
            elif isinstance(target, int):
                # Reset to 0 then go up
                pyautogui.press("volumedown", presses=50)
                pyautogui.press("volumeup", presses=int(target / 2))
                speak_func(f"Volume set to {target}.")

    # Run in background so UI doesn't freeze
    threading.Thread(target=volume_worker, daemon=True).start()
