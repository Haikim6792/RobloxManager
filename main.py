import os
import sys
import subprocess


def install_requirements(requirements_path):
    """Reads requirements.txt and installs any missing packages automatically."""
    if not os.path.exists(requirements_path):
        print(f"Warning: {requirements_path} not found. Skipping auto-install.")
        return

    with open(requirements_path, "r", encoding="utf-8") as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"[{package}] is not installed. Installing now...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"Successfully installed [{package}].")
            except subprocess.CalledProcessError:
                print(f"Failed to install [{package}]. Please install manually.")
                sys.exit(1)


if __name__ == "__main__":
    # Path to requirements inside appfolder
    base_dir = os.path.dirname(os.path.abspath(__file__))
    req_file = os.path.join(base_dir, "appfolder", "requirements.txt")

    # Step 1: Check and install missing libraries
    install_requirements(req_file)

    # Step 2: Import and run the main application from appfolder
    from appfolder.app import launch
    launch()