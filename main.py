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


# --- 2. WINGET HEALTH CHECK & AUTO-INSTALLER ---
def is_winget_working():
    """Tests if winget is available and responding correctly."""
    try:
        result = subprocess.run(
            ["winget", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_or_repair_winget():
    """Downloads and installs/reinstalls Microsoft AppInstaller (winget) via PowerShell."""
    print(" -> Winget is missing or corrupted. Attempting automatic installation/repair...")
    
    # Official Microsoft Winget package download URL
    winget_msix_url = "https://github.com/microsoft/winget-cli/releases/latest/download/Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
    temp_installer_path = os.path.join(os.environ.get("TEMP", "C:\\Windows\\Temp"), "winget_installer.msixbundle")

    try:
        print(" -> Downloading Winget package from official source...")
        req = urllib.request.Request(winget_msix_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(temp_installer_path, "wb") as out_file:
            out_file.write(response.read())

        print(" -> Installing Winget via PowerShell Add-AppxPackage...")
        ps_command = f'Add-AppxPackage -Path "{temp_installer_path}" -ForceApplicationShutdown'
        subprocess.run(["powershell", "-Command", ps_command], check=True)
        
        # Cleanup installer file
        if os.path.exists(temp_installer_path):
            os.remove(temp_installer_path)

        print(" -> Winget successfully installed/reinstalled!")
        return True
    except Exception as e:
        print(f" -> Winget repair failed: {e}")
        if os.path.exists(temp_installer_path):
            os.remove(temp_installer_path)
        return False


# --- 3. AUTOMATIC GIT INSTALLER ---
def try_install_git():
    """Ensures Winget is working, then uses Winget to install Git."""
    if not is_winget_working():
        # Try to repair or install winget first
        if not install_or_repair_winget():
            return False

    print(" -> Installing Git executable via Winget...")
    try:
        cmd = [
            "winget", "install", "--id", "Git.Git",
            "-e", "--source", "winget",
            "--accept-source-agreements", "--accept-package-agreements",
            "--silent"
        ]
        subprocess.run(cmd, check=True)
        print(" -> Git installed successfully!")
        
        # Add default Git path to PATH environment variable for the current process
        git_path = r"C:\Program Files\Git\cmd"
        if git_path not in os.environ["PATH"]:
            os.environ["PATH"] += f";{git_path}"
            
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(" -> Git installation via Winget failed.")
        return False


# --- 4. AUTOMATIC FILE DOWNLOAD & SYNC ---
def download_zip_fallback():
    """Downloads repository as a ZIP archive if Git is unavailable."""
    print(" -> Downloading repository archive directly via HTTPS...")
    try:
        req = urllib.request.Request(ZIP_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            zip_data = response.read()

        print(" -> Extracting files...")
        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            root_prefix = f"{REPO_NAME}-{BRANCH}/"
            for file_info in z.infolist():
                if file_info.filename.startswith(root_prefix):
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
    """Clones/pulls repository via Git, repairs Winget/Git if needed, or falls back to ZIP."""
    print("[1/3] Checking repository files...")
    
    # 1. Existing Git repository -> Pull latest
    if os.path.exists(".git"):
        print(" -> Existing Git repository found. Pulling latest updates...")
        try:
            subprocess.run(["git", "pull", "origin", BRANCH], check=False)
        except FileNotFoundError:
            print(" -> Git executable not found on system path. Skipping pull.")
        return

    # 2. Files exist locally -> Skip download
    if os.path.exists("appfolder") and os.path.exists(os.path.join("appfolder", "app.py")):
        print(" -> Local files detected.")
        return

    # 3. Missing files -> Check Git -> Repair Winget & Install Git if needed -> Fallback to ZIP
    print(" -> Project files missing. Attempting download...")
    
    git_installed = True
    try:
        subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        git_installed = try_install_git()

    if git_installed:
        try:
            subprocess.run(["git", "clone", GITHUB_REPO_URL, "."], check=True)
            print(" -> Successfully cloned repository via Git!")
            return
        except subprocess.CalledProcessError:
            print(" -> Git clone failed. Falling back to direct ZIP download...")

    # Direct ZIP fallback if Git or Winget couldn't complete the setup
    download_zip_fallback()


# --- 5. AUTOMATIC PIP LIBRARY INSTALLER ---
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
