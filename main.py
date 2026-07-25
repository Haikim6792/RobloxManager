import os
import sys
import ctypes
import subprocess

# --- CONFIGURATION ---
GITHUB_REPO_URL = "https://github.com/Haikim6792/RobloxManager.git"
BRANCH = "main"


# --- 1. ADMIN AUTO-ELEVATION ---
def is_admin():
    """Checks if the script is running with Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    """Relaunches the current script with Administrator privileges if needed."""
    if not is_admin():
        print("Requesting Administrator privileges...")
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        
        if ret > 32:
            sys.exit(0)
        else:
            print("Failed to acquire Admin privileges. Proceeding anyway...")


# --- 2. AUTOMATIC FILE DOWNLOAD & SYNC ---
def sync_github_files():
    """Clones the repository if missing, or pulls updates if already present."""
    print("[1/2] Checking repository files...")
    
    # Check if this directory is already a Git repository
    if os.path.exists(".git"):
        print("Existing repository found. Pulling latest updates...")
        try:
            subprocess.run(["git", "pull", "origin", BRANCH], check=False)
        except FileNotFoundError:
            print("Git is not installed. Skipping update.")
    else:
        print("Missing repository files. Cloning from GitHub...")
        try:
            # Clones all repository contents directly into the current folder
            subprocess.run(["git", "clone", GITHUB_REPO_URL, "."], check=True)
            print("Successfully downloaded repository files!")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: Git is required to download the project files automatically.")
            print("Please ensure Git is installed or clone the repository manually.")
            sys.exit(1)


# --- 3. REQUIREMENTS CHECKER ---
def ensure_requirements(requirements_path):
    """Checks and installs missing Python packages from requirements.txt."""
    if not os.path.exists(requirements_path):
        print(f"Warning: {requirements_path} not found.")
        return

    print("[2/2] Checking required Python packages...")
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
    # Ensure Admin elevation
    run_as_admin()

    # Sync files from GitHub (Clones if empty, pulls if already exists)
    sync_github_files()

    # Set path to appfolder/requirements.txt
    base_dir = os.path.dirname(os.path.abspath(__file__))
    req_path = os.path.join(base_dir, "appfolder", "requirements.txt")

    # Ensure dependencies like psutil are installed
    ensure_requirements(req_path)

    # Launch the app
    print("Launching Roblox Manager...")
    from appfolder.app import launch
    launch()
