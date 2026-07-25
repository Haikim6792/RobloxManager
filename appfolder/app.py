import tkinter as tk
import psutil
from appfolder.hidecmd import hide_console

# Target process names
ROBLOX_PROCESSES = ["robloxplayerbeta.exe", "robloxapp.exe"]
CRASH_HANDLER_PROCESS = "robloxcrashhandler.exe"


def kill_process_by_name(process_name):
    """Searches and terminates all instances matching the given executable name."""
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                proc.kill()
                killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return killed_count


def check_is_running(process_names):
    """Checks if any process from a list is currently active."""
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in process_names:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


class DarkRobloxManager(tk.Tk):
    def __init__(self):
        super().__init__()

        # Hide command prompt as soon as Tkinter starts
        hide_console()

        # Theme Colors
        self.BG_DARK = "#0f172a"
        self.CARD_BG = "#1e293b"
        self.TEXT_MAIN = "#f8fafc"
        self.TEXT_MUTED = "#94a3b8"
        self.COLOR_BLUE = "#3b82f6"
        self.COLOR_BLUE_HOVER = "#2563eb"
        self.COLOR_RED = "#ef4444"
        self.COLOR_RED_HOVER = "#dc2626"
        self.STATUS_ONLINE = "#22c55e"
        self.STATUS_OFFLINE = "#64748b"

        self.title("Roblox Manager")
        self.geometry("380x300")
        self.configure(bg=self.BG_DARK)
        self.resizable(False, False)

        self.setup_ui()
        self.auto_detect_loop()

    def setup_ui(self):
        # Header Container
        header_frame = tk.Frame(self, bg=self.BG_DARK)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = tk.Label(
            header_frame,
            text="Tắt Roblox Time Limit",
            font=("Segoe UI", 14, "bold"),
            fg=self.TEXT_MAIN,
            bg=self.BG_DARK
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            header_frame,
            text="Tự động quản lý các tiến trình Roblox và bỏ qua giới hạn thời gian",
            font=("Segoe UI", 9),
            fg=self.TEXT_MUTED,
            bg=self.BG_DARK
        )
        subtitle_label.pack(anchor="w")

        # Status Card
        self.card = tk.Frame(self, bg=self.CARD_BG, highlightbackground="#334155", highlightthickness=1)
        self.card.pack(fill="x", padx=20, pady=10, ipady=8)

        self.status_dot = tk.Label(
            self.card, text="●", font=("Segoe UI", 12), fg=self.STATUS_OFFLINE, bg=self.CARD_BG
        )
        self.status_dot.pack(side="left", padx=(15, 5))

        self.status_text = tk.Label(
            self.card,
            text="Roblox Status: Checking...",
            font=("Segoe UI", 9, "bold"),
            fg=self.TEXT_MUTED,
            bg=self.CARD_BG
        )
        self.status_text.pack(side="left")

        # Action Buttons Container
        btn_frame = tk.Frame(self, bg=self.BG_DARK)
        btn_frame.pack(fill="x", padx=20, pady=10)

        self.inject_btn = tk.Button(
            btn_frame,
            text="Inject",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_BLUE,
            fg="white",
            activebackground=self.COLOR_BLUE_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            height=2,
            command=self.on_inject_click
        )
        self.inject_btn.pack(fill="x", pady=(0, 8))

        self.kill_btn = tk.Button(
            btn_frame,
            text="Kill Roblox",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_RED,
            fg="white",
            activebackground=self.COLOR_RED_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            height=2,
            command=self.on_kill_roblox_click
        )
        self.kill_btn.pack(fill="x")

        # Log Footer
        self.log_label = tk.Label(
            self, text="Ready", font=("Segoe UI", 8), fg=self.TEXT_MUTED, bg=self.BG_DARK
        )
        self.log_label.pack(side="bottom", pady=10)

    def auto_detect_loop(self):
        """Periodically scans active background processes every 2 seconds."""
        is_running = check_is_running(ROBLOX_PROCESSES)

        if is_running:
            self.status_dot.config(fg=self.STATUS_ONLINE)
            self.status_text.config(text="Roblox Status: Active", fg=self.TEXT_MAIN)
        else:
            self.status_dot.config(fg=self.STATUS_OFFLINE)
            self.status_text.config(text="Roblox Status: Not Running", fg=self.TEXT_MUTED)

        self.after(2000, self.auto_detect_loop)

    def on_inject_click(self):
        if check_is_running(ROBLOX_PROCESSES):
            count = kill_process_by_name(CRASH_HANDLER_PROCESS)
            if count > 0:
                self.log_label.config(text=f"Ended {count} instance(s) of CrashHandler.", fg="#4ade80")
            else:
                self.log_label.config(text="Roblox is active, but CrashHandler wasn't found.", fg="#facc15")
        else:
            self.log_label.config(text="Roblox is not currently running.", fg="#f87171")

    def on_kill_roblox_click(self):
        total_killed = sum(kill_process_by_name(name) for name in ROBLOX_PROCESSES)
        if total_killed > 0:
            self.log_label.config(text=f"Successfully killed {total_killed} Roblox process(es).", fg="#4ade80")
            self.status_dot.config(fg=self.STATUS_OFFLINE)
            self.status_text.config(text="Roblox Status: Not Running", fg=self.TEXT_MUTED)
        else:
            self.log_label.config(text="No active Roblox processes found to kill.", fg="#facc15")


def launch():
    app = DarkRobloxManager()
    app.mainloop()
