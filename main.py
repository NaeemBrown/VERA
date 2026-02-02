import sys
import os

# 1. SETUP PATHS (So Python finds 'core' and 'ui')
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "core"))
sys.path.append(os.path.join(current_dir, "ui"))

# 2. IMPORT THE NEW UI
try:
    from ui.hologram import VeraHologram
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import UI. {e}")
    print("Check that 'ui/hologram.py' exists.")
    sys.exit(1)

# 3. LAUNCH V.E.R.A.
if __name__ == "__main__":
    print(">> SYSTEM: Initializing V.E.R.A. Kernel...")
    app = VeraHologram()
