import sys
import os
import time

# --- MAGIC GLUE ---
# Add 'core' to path so we can import voice_lock
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))

try:
    from voice_lock import security_system
except ImportError:
    print("CRITICAL ERROR: Could not find 'core/voice_lock.py'.")
    print("Make sure you moved voice_lock.py into the 'core' folder!")
    input("Press Enter to exit...")
    sys.exit(1)


def run_enrollment():
    print("---------------------------------------")
    print("   VERA VOICE SECURITY ENROLLMENT      ")
    print("---------------------------------------")
    print("I need to learn your voice to authorize dangerous commands.")
    print("(Shutdown, Opening Apps, Typing, etc.)")
    print("\nWhen you press Enter, read the following sentence clearly:")
    print('\n"My voice is my passport. Verify me."\n')

    input("Press Enter to start recording (6 seconds)...")

    print("3...")
    time.sleep(0.5)
    print("2...")
    time.sleep(0.5)
    print("1...")
    time.sleep(0.5)
    print("GO!")

    security_system.enroll_user()

    print("\n---------------------------------------")
    print("SUCCESS! Voice print saved to 'data/naeem_voice.npy'")
    print("You can now run 'python main.py'")
    time.sleep(3)


if __name__ == "__main__":
    run_enrollment()
