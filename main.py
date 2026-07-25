import os
import sys
import ctypes
import subprocess
import urllib.request
import zipfile
import io

# Fix working directory & pathing
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

GITHUB_USER = "Haikim6792"
REPO_NAME = "RobloxManager"
BRANCH = "main"

GITHUB_REPO_URL = f"https://github.com/{GITHUB_USER}/{REPO_NAME}.git"
ZIP_URL = f"https://github.com/{GITHUB_USER}/{REPO_NAME}/archive/refs/heads/{BRANCH}.zip"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    if not is_admin():
        print("[+] Requesting Administrator privileges...")
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', BASE_DIR, 1
        )
        
        if ret > 32:
            sys.exit(0)
        else:
            print("[!] Admin privileges denied. Some process actions may fail.")


def is_winget_working():
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
    print(" -> Winget is missing or corrupted. Attempting automatic installation/repair...")
    winget_msix_url = "https://github.com/microsoft/winget-cli/releases/latest/download/Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
    temp_installer_path = os.path.join(os.environ.get("TEMP", "C:\\Windows\\Temp"), "winget_installer.msixbundle")

    try:
        print(" -> Downloading Winget package...")
        req = urllib.request.Request(winget_msix_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(temp_installer_path, "wb") as out_file:
            out_file.write(response.read())

        print(" -> Installing Winget via PowerShell...")
        ps_command = f'Add-AppxPackage -Path "{temp_installer_path}" -ForceApplicationShutdown'
        subprocess.run(["powershell", "-Command", ps_command], check=True)
        
        if os.path.exists(temp_installer_path):
            os.remove(temp_installer_path)

        print(" -> Winget successfully installed/reinstalled!")
        return True
    except Exception as e:
        print(f" -> Winget repair failed: {e}")
        if os.path.exists(temp_installer_path):
            os.remove(temp_installer_path)
        return False


def try_install_git():
    if not is_winget_working():
        if not install_or_repair_winget():
            return False

    print(" -> Installing Git via Winget...")
    try:
        cmd = [
            "winget", "install", "--id", "Git.Git",
            "-e", "--source", "winget",
            "--accept-source-agreements", "--accept-package-agreements",
            "--silent"
        ]
        subprocess.run(cmd, check=True)
        print(" -> Git installed successfully!")
        
        git_path = r"C:\Program Files\Git\cmd"
        if git_path not in os.environ["PATH"]:
            os.environ["PATH"] += f";{git_path}"
            
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(" -> Git installation via Winget failed.")
        return False


def download_zip_fallback():
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
                    
                    target_path = os.path.join(BASE_DIR, relative_path)
                    if file_info.is_dir():
                        os.makedirs(target_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with z.open(file_info) as source, open(target_path, "wb") as target:
                            target.write(source.read())

        print(" -> Successfully downloaded and extracted files!")
    except Exception as e:
        raise RuntimeError(f"Failed to download repository archive: {e}")


def sync_github_files():
    print("[1/3] Checking repository files...")
    if os.path.exists(os.path.join(BASE_DIR, ".git")):
        print(" -> Existing Git repository found. Pulling latest updates...")
        try:
            subprocess.run(["git", "pull", "origin", BRANCH], check=False)
        except FileNotFoundError:
            print(" -> Git executable not found on system path. Skipping pull.")
        return

    app_py_path = os.path.join(BASE_DIR, "appfolder", "app.py")
    if os.path.exists(app_py_path):
        print(" -> Local files detected.")
        return

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

    download_zip_fallback()


def ensure_requirements(requirements_path):
    if not os.path.exists(requirements_path):
        print(f" -> [Notice] {requirements_path} not found. Skipping library check.")
        return

    print("[2/3] Checking required Python libraries...")
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


def main():
    run_as_admin()
    sync_github_files()

    req_path = os.path.join(BASE_DIR, "appfolder", "requirements.txt")
    ensure_requirements(req_path)

    print("[3/3] Launching Roblox Manager GUI...")
    from appfolder.app import launch
    launch()


if __name__ == "__main__":
    try:
        main()
        # Automatically exit process and close console on normal GUI close
        sys.exit(0)
    except Exception as err:
        # If console was hidden, restore it to show the error
        try:
            from appfolder.hidecmd import show_console
            show_console()
        except ImportError:
            pass

        print(f"\n" + "=" * 50)
        print(f" ERROR DETECTED: {err}")
        print("=" * 50)
        input("\nPress Enter to close this window...")
