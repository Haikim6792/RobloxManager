import os
import sys
import ctypes
import subprocess

# --- 1. ADMIN AUTO-ELEVATION ---
def is_admin():
    """Checks if the script is currently running with Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    """Relaunches the current script with Administrator privileges if needed."""
    if not is_admin():
        print("Requesting Administrator privileges...")
        # Re-run the script with 'runas' verb to trigger Windows UAC
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        
        # If the user accepted UAC (ret > 32), exit this non-admin instance
        if ret > 32:
            sys.exit(0)
        else:
            print("Failed to acquire Admin privileges. Proceeding anyway...")

# --- 2. GITHUB AUTO-UPDATE ---
def update_from_github():
    """Pulls the latest updates from the GitHub repository."""
    print("[1/2] Checking for GitHub updates...")
    try:
        # Check if git is installed and repository exists
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print("Git update output:", result.stdout.strip())
        else:
            print("Git pull failed or directory is not a git repo. Skipping update.")
    except FileNotFoundError:
        print("Git is not installed on this system. Skipping auto-update.")

# --- 3. REQUIREMENTS CHECKER ---
def ensure_requirements(requirements_path):
    """Checks and installs missing requirements automatically."""
    if not os.path.exists(requirements_path):
        return

    print("[2/2] Checking required packages...")
    with open(requirements_path, "r", encoding="utf-8") as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing missing package: [{package}]...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])


# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    # Ensure Admin elevation first
    run_as_admin()

    # Get path to appfolder/requirements.txt
    base_dir = os.path.dirname(os.path.abspath(__file__))
    req_path = os.path.join(base_dir, "appfolder", "requirements.txt")

    # Sync code and check requirements
    update_from_github()
    ensure_requirements(req_path)

    # Import and launch the UI from appfolder
    print("Launching Roblox Manager...")
    from appfolder.app import launch
    launch()
