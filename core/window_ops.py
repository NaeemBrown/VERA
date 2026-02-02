import pygetwindow as gw
import pyautogui


def get_window(partial_title):
    """Finds a window by part of its name (e.g., 'code' finds 'Visual Studio Code')."""
    try:
        # Get all windows
        windows = gw.getAllWindows()
        for win in windows:
            if win.title and partial_title.lower() in win.title.lower():
                return win
        return None
    except Exception as e:
        print(f"Window Find Error: {e}")
        return None


def maximize_window(app_name):
    win = get_window(app_name)
    if win:
        try:
            if not win.isMaximized:
                win.maximize()
            # Bring to front
            win.activate()
            return True
        except:
            return False
    return False


def snap_window(app_name, side="left"):
    """Snaps a window to the left or right half of the screen (Dynamic Resolution)."""
    win = get_window(app_name)
    if win:
        try:
            if win.isMaximized:
                win.restore()

            # Get current screen resolution
            screen_w, screen_h = pyautogui.size()

            # Calculate dimensions
            width = screen_w // 2
            height = screen_h - 40  # Leave room for taskbar

            if side == "left":
                win.moveTo(0, 0)
            elif side == "right":
                win.moveTo(width, 0)

            win.resizeTo(width, height)
            return True
        except Exception as e:
            print(f"Snap Error: {e}")
    return False


def minimize_window(app_name):
    """Finds a window and minimizes it."""
    win = get_window(app_name)
    if win:
        try:
            if not win.isMinimized:
                win.minimize()
            return True
        except:
            pass
    return False
