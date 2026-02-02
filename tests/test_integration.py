import os


def test_project_structure():
    """Verify that core files exist before building."""
    assert os.path.exists("ui/hologram.py")
    assert os.path.exists("core/processor.py")
    assert os.path.exists("assets/head.gif")


def test_environment_vars():
    """Ensure the project isn't missing critical folders."""
    assert os.path.isdir("data")
    assert os.path.isdir("assets")
