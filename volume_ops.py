from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL, CoInitialize
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import pyautogui
import time
import math


# --- INTERNAL HELPERS ---
def _get_volume_interface_safe():
    """
    Safely attempts to get the Windows Volume Interface.
    Returns None if it fails (so we can fallback to keys).
    """
    try:
        # 1. Initialize COM (Crucial for threaded apps)
        CoInitialize()

        # 2. Get Speakers
        devices = AudioUtilities.GetSpeakers()

        # 3. Try the Direct Property Method (Newer Pycaw)
        if hasattr(devices, "EndpointVolume"):
            return devices.EndpointVolume

        # 4. Try the Manual Activation Method (Older Pycaw)
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))

    except Exception as e:
        print(f"DEBUG: Pycaw failed ({e}). Using fallback.")
        return None


def fade_volume(volume_interface, target_percent, duration=1.5):
    """
    The Smooth Engine: Slides volume to target_percent over 'duration' seconds.
    """
    try:
        # Get start level (0.0 to 1.0)
        start_scalar = volume_interface.GetMasterVolumeLevelScalar()
        target_scalar = target_percent / 100.0

        # Optimization: Don't fade if it's already there (difference < 1%)
        if abs(start_scalar - target_scalar) < 0.01:
            return

        # Animation Physics
        steps = 30  # Higher = smoother
        delay = duration / steps
        step_change = (target_scalar - start_scalar) / steps

        for i in range(steps):
            new_level = start_scalar + (step_change * (i + 1))

            # Safety Clamp (Must stay between 0.0 and 1.0)
            new_level = max(0.0, min(1.0, new_level))

            volume_interface.SetMasterVolumeLevelScalar(new_level, None)
            time.sleep(delay)

        # Ensure we hit the exact target at the end (fix rounding errors)
        volume_interface.SetMasterVolumeLevelScalar(target_scalar, None)

    except Exception as e:
        print(f"Fade failed: {e}")
        # If fade fails, just force set it instantly so the command still works
        volume_interface.SetMasterVolumeLevelScalar(target_percent / 100.0, None)


def set_volume_legacy(target_percent):
    """Fallback: Mute then pump up keys (Caveman style)."""
    pyautogui.press("volumedown", presses=50)  # Zero it out
    presses = int(target_percent / 2)
    pyautogui.press("volumeup", presses=presses)


def change_volume_legacy(direction, step=15):
    """Fallback: Relative change using keys."""
    presses = int(step / 2)  # Each press is ~2%
    if direction == "up":
        pyautogui.press("volumeup", presses=presses)
    else:
        pyautogui.press("volumedown", presses=presses)


# --- PUBLIC COMMAND HANDLER ---
def handle_volume_command(command, speak_func):
    """Decides what volume action to take with fallback protection."""

    # Attempt to get the fancy interface
    volume = _get_volume_interface_safe()

    # --- STRATEGY A: SMOOTH FADE (Pycaw) ---
    if volume:
        try:
            if "mute" in command:
                is_muted = volume.GetMute()
                # Toggle: if True make False, if False make True
                volume.SetMute(not is_muted, None)
                speak_func("Muted." if not is_muted else "Unmuted.")
                return

            elif "unmute" in command:
                volume.SetMute(0, None)
                speak_func("Unmuted.")
                return

            # Calculate current percentage
            current_scalar = volume.GetMasterVolumeLevelScalar()
            current_percent = int(round(current_scalar * 100))

            if "up" in command:
                target = min(100, current_percent + 15)
                # Shorter fade for quick adjustments
                fade_volume(volume, target, duration=0.4)

            elif "down" in command:
                target = max(0, current_percent - 15)
                fade_volume(volume, target, duration=0.4)

            else:
                # Look for a specific number
                words = command.split()
                for word in words:
                    clean = "".join(filter(str.isdigit, word))
                    if clean:
                        target = int(clean)
                        # Safety clamp 0-100
                        target = max(0, min(100, target))

                        speak_func(f"Fading volume to {target}%.")
                        # Longer fade for big jumps
                        fade_volume(volume, target, duration=1.5)
                        return

                speak_func("I didn't hear a number.")
            return  # Success! Exit function.

        except Exception as e:
            print(f"DEBUG: Pycaw Error ({e}). Switching to fallback.")

    # --- STRATEGY B: LEGACY (Keyboard) ---
    # We only reach here if pycaw failed or wasn't found
    print("Using LEGACY volume control.")

    if "mute" in command or "unmute" in command:
        pyautogui.press("volumemute")
        speak_func("Toggle mute.")

    elif "up" in command:
        change_volume_legacy("up")

    elif "down" in command:
        change_volume_legacy("down")

    else:
        words = command.split()
        for word in words:
            clean = "".join(filter(str.isdigit, word))
            if clean:
                target = int(clean)
                speak_func(f"Setting volume to {target}%.")
                set_volume_legacy(target)
                return
        speak_func("I didn't hear a number.")
