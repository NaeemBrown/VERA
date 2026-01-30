import time
import tools
import window_ops

def work_mode_init():
    # 1. Open Apps (Using tools.py so we don't duplicate code)
    tools.open_app("code") # VS Code
    tools.open_website("google.com")
    
    # Wait for windows to actually appear
    time.sleep(3)
    
    # 2. Arrange Windows (Using the new window_ops)
    window_ops.snap_window("Visual Studio Code", side="left")
    window_ops.snap_window("Google Chrome", side="right")
    
    return "Workspace organized."