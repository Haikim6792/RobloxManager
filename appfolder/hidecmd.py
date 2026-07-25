import ctypes

# Windows API constants
SW_HIDE = 0
SW_SHOW = 5


def hide_console():
    """Hides the current command prompt console window."""
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)


def show_console():
    """Shows the command prompt console window if it was hidden."""
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW)
