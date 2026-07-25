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
    """Relaunches the script with Administrator privileges via Windows UAC if needed."""
    if not is_admin():
        print("[+] Requesting Administrator privileges...")
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        
        # Trigger UAC prompt
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        
        # If UAC was accepted (ret > 32), close this non-admin process
        if ret > 32:
            sys.exit(0)
        else:
            print("[!] Admin privileges denied. Some process actions may fail.")


# --- 2. AUTOMATIC FILE DOWNLOAD & SYNC ---
def sync_github_files():
    """Clones the repository if missing, or pulls updates if already present."""
    print("[1/3] Checking repository files...")
    
    if os.path.exists(".git"):
        print(" -> Existing Git repository found. Pulling latest updates...")
        try:
            subprocess.run(["git", "pull", "origin", BRANCH], check=False)
        except FileNotFoundError:
            print(" -> [Notice] Git executable not found on system path. Skipping pull.")
    else:
        print(" -> Repository files missing. Cloning from GitHub...")
        try:
            subprocess.run(["git", "clone", GITHUB_REPO_URL, "."], check=True)
            print(" -> Successfully downloaded repository files!")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(
                f"Failed to clone repository from GitHub ({e}). "
                "Ensure Git is installed and you have an active internet connection."
            )


# --- 3. AUTOMATIC PIP LIBRARY INSTALLER ---
def ensure_requirements(requirements_path):
    """Checks and automatically installs missing Python libraries using pip."""
    if not os.path.exists(requirements_path):
        print(f" -> [Notice] {requirements_path} not found. Skipping library check.")
        return

    print("[2/3] Checking and installing required Python libraries...")
    with open(requirements_path, "r", encoding="utf-8") as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    for package in packages:
        try:
            __import__(package)
            print(f" -> Package [{package}] is already installed.")
        except ImportError:
            print(f" -> Installing missing library: [{package}] via pip...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f" -> Successfully installed [{package}].")
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to auto-install package [{package}] via pip: {e}")


# --- MAIN ENTRY POINT ---
def main():
    # Step 1: Ensure Administrator privileges
    run_as_admin()

    # Step 2: Download/Sync files from GitHub
    sync_github_files()

    # Step 3: Automatically check and install pip dependencies
    base_dir = os.path.dirname(os.path.abspath(__file__))
    req_path = os.path.join(base_dir, "appfolder", "requirements.txt")
    ensure_requirements(req_path)

    # Step 4: Launch the GUI application
    print("[3/3] Launching Roblox Manager GUI...")
    from appfolder.app import launch
    launch()


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"\n" + "=" * 50)
        print(f" ERROR DETECTED: {err}")
        print("=" * 50)
    finally:
        # Prevents the command prompt / terminal from instantly closing
        print("\nExecution finished.")
        input("Press Enter to close this window...")
