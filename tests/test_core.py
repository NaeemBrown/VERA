import pytest
import os
import sys

# --- 1. DYNAMIC PATHING ---
# Go up one level to find 'core'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- 2. IMPORT MODULES TO TEST ---
try:
    from core import tools
    from core import admin
    from core import volume_ops
    from core import ai_ops
    from core import window_ops
    from core import work_ops
except ImportError as e:
    # Fail immediately if files are missing
    pytest.fail(
        f"CRITICAL: Could not import core modules. Check your folder structure! Error: {e}"
    )

# --- TEST SUITE ---


def test_critical_modules_exist():
    """Verifies that all sub-systems are loadable."""
    assert ai_ops is not None
    assert work_ops is not None
    assert window_ops is not None


def test_ai_ops_paths():
    """Verifies that AI Operations can find the data folder."""
    # The constants should be strings and point to the data directory
    assert isinstance(ai_ops.APP_LIBRARY_FILE, str)
    assert "data" in ai_ops.APP_LIBRARY_FILE


def test_tools_battery_check():
    """Verifies the battery monitor returns a string."""
    status = tools.get_battery_status()
    assert isinstance(status, str)
    assert len(status) > 0


def test_volume_interface_safety():
    """Ensures the volume controller fails gracefully on headless servers."""
    # This should return None or an Interface, but NEVER crash
    try:
        interface = volume_ops._get_volume_interface_safe()
        # Pass if it returns None (Github Actions) or Object (Your PC)
        assert True
    except Exception as e:
        pytest.fail(f"Volume module crashed: {e}")


def test_window_ops_resolution():
    """Verifies window operations can read screen size."""
    import pyautogui

    w, h = pyautogui.size()
    assert w > 0
    assert h > 0


def test_intent_classification_simple():
    """Checks if the AI Router can handle a basic offline fallback."""
    # If Groq is offline/missing key, it should default to CHAT_FAST
    intent = ai_ops.identify_intent("Hello world")
    assert isinstance(intent, str)
    # It will likely return CHAT_FAST if no API key is set in the test env
    assert intent in ["CHAT_FAST", "CHAT_DEEP", "CMD_OPEN"]
