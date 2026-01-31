import pygetwindow as gw
import time


def get_window(partial_title):
    """Finds a window by part of its name (e.g., 'code' finds 'Visual Studio Code')."""
    try:
        # Get all windows
        windows = gw.getAllWindows()
        for win in windows:
            if partial_title.lower() in win.title.lower():
                return win
        return None
    except:
        return None


def maximize_window(app_name):
    win = get_window(app_name)
    if win:
        if not win.isMaximized:
            win.maximize()
        # Bring to front
        try:
            win.activate()
        except:
            pass
        return True
    return False


def snap_window(app_name, side="left"):
    """Snaps a window to the left or right half of the screen (1920x1080)."""
    win = get_window(app_name)
    if win:
        if win.isMaximized:
            win.restore()

        # Standard HD Monitor Logic
        width = 960
        height = 1040  # Leaves a little room for taskbar

        if side == "left":
            win.moveTo(0, 0)
        elif side == "right":
            win.moveTo(960, 0)

        win.resizeTo(width, height)
        return True
    return False


def move_to_primary(app_name):
    """Drags a window to 0,0 (Top Left)."""
    win = get_window(app_name)
    if win:
        if win.isMaximized:
            win.restore()
        win.moveTo(0, 0)
        return True
    return False


def minimize_window(app_name):
    """Finds a window and minimizes it."""
    win = get_window(app_name)
    if win:
        if not win.isMinimized:
            win.minimize()
        return True
    return False
