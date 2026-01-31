import pytest
import os
import sys

# 1. Dynamic Pathing: Ensures the test runner finds your 'src' code
# This is "Best Practice" so tests can run on any server (Linux/Windows)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Import Modules
import tools
import admin
import volume_ops

# --- INTEGRATION TEST SUITE ---

def test_critical_modules_import():
    """Verifies that all sub-systems are loadable without syntax errors."""
    try:
        import ai_ops
        import skills
        import work_ops
    except ImportError as e:
        pytest.fail(f"Critical Module Failure: {e}")

def test_app_registry_integrity():
    """Verifies the application mapping logic is valid."""
    # DevOps Check: Ensure no 'None' values in our config
    for key, value in tools.APP_MAP.items():
        assert value.endswith(".exe"), f"Configuration Error: {key} maps to invalid file extension"

def test_system_monitor_returns_valid_metrics():
    """Verifies the Admin module connects to OS hardware sensors."""
    metrics = admin.get_system_status()
    
    # Contract Testing: The API must return these exact keys
    required_keys = ["cpu", "ram", "battery", "speech"]
    for key in required_keys:
        assert key in metrics, f"API Contract Violation: Missing key '{key}'"
        
    # Data Validation: CPU must be a percentage
    assert 0 <= metrics['cpu'] <= 100, "Logic Error: CPU usage out of bounds"

def test_volume_interface_fallback():
    """Ensures the volume controller fails gracefully if hardware is missing."""
    # On a GitHub runner, there are no speakers. 
    # This test proves your code handles 'Headless' environments correctly.
    try:
        volume_ops._get_volume_interface_safe()
    except Exception:
        pytest.fail("Volume module crashed instead of handling missing hardware gracefully")