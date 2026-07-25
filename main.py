import os
import sys
import ctypes
import subprocess
import urllib.request
import zipfile
import io

# --- CONFIGURATION ---
GITHUB_USER = "Haikim6792"
REPO_NAME = "RobloxManager"
BRANCH = "main"

GITHUB_REPO_URL = f"https://github.com/{GITHUB_USER}/{REPO_NAME}.git"
ZIP_URL = f"https://github.com/{GITHUB_USER}/{REPO_NAME}/archive/refs/heads/{BRANCH}.zip"


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
        
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        
        if ret > 32:
            sys.exit(0)
        else:
            print("[!] Admin privileges denied. Some process actions may fail.")


# --- 2. AUTOMATIC FILE DOWNLOAD & SYNC ---
def download_zip_fallback():
    """Downloads repository as a ZIP archive if Git is not installed."""
    print(" -> Git not found. Downloading repository archive directly...")
    try:
        # Download ZIP into memory
        req = urllib.request.Request(ZIP_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            zip_data = response.read()

        # Extract ZIP contents to the current folder
        print(" -> Extracting files...")
        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            # GitHub ZIP archives wrap contents in 'RepoName-branch/' folder
            root_prefix = f"{REPO_NAME}-{BRANCH}/"
            for file_info in z.infolist():
                if file_info.filename.startswith(root_prefix):
                    # Remove the folder prefix so files unpack into the root directory
                    relative_path = file_info.filename[len(root_prefix):]
                    if not relative_path:
                        continue
                    
                    target_path = os.path.join(".", relative_path)
                    if file_info.is_dir():
                        os.makedirs(target_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with z.open(file_info) as source, open(target_path, "wb") as target:
                            target.write(source.read())

        print(" -> Successfully downloaded and extracted repository files!")
    except Exception as e:
        raise RuntimeError(f"Failed to download repository archive: {e}")


def sync_github_files():
    """Clones/pulls repository via Git, or falls back to direct ZIP download."""
    print("[1/3] Checking repository files...")
    
    if os.path.exists(".git"):
        print(" -> Existing Git repository found. Pulling latest updates...")
        try:
            subprocess.run(["git", "pull", "origin", BRANCH], check=False)
        except FileNotFoundError:
            print(" -> Git not installed. Skipping git pull.")
    elif os.path.exists("appfolder") and os.path.exists(os.path.join("appfolder", "app.py")):
        print(" -> Local files detected.")
    else:
        print(" -> Project files missing. Attempting download...")
        try:
            subprocess.run(["git", "clone", GITHUB_REPO_URL, "."], check=True)
            print(" -> Successfully cloned repository via Git!")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fall back to downloading ZIP via Python if Git is missing/fails
            download_zip_fallback()


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
    run_as_admin()
    sync_github_files()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    req_path = os.path.join(base_dir, "appfolder", "requirements.txt")
    ensure_requirements(req_path)

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
        print("\nExecution finished.")
        input("Press Enter to close this window...")
