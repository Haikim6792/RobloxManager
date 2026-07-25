@echo off
setlocal enabledelayedexpansion

:: =========================================================
:: 1. AUTO ELEVATE TO ADMIN PRIVILEGES
:: =========================================================
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrative Privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Set working directory to the folder where this batch script is saved
cd /d "%~dp0"

:: =========================================================
:: CONFIGURATION - Updated for Haikim6792/RobloxManager
:: =========================================================
set "GITHUB_USER=Haikim6792"
set "REPO_NAME=RobloxManager"
set "BRANCH=main"

set "REPO_URL=https://github.com/%GITHUB_USER%/%REPO_NAME%.git"
set "ZIP_URL=https://github.com/%GITHUB_USER%/%REPO_NAME%/archive/refs/heads/%BRANCH%.zip"

echo =========================================================
echo  Roblox Manager - AIO Downloader & Launcher
echo =========================================================
echo.

:: =========================================================
:: 2. DOWNLOAD / UPDATE FILES FROM GITHUB
:: =========================================================
where git >nul 2>&1
if %errorLevel% equ 0 (
    echo [1/2] Git detected. Syncing repository...
    if exist ".git" (
        call git pull origin %BRANCH%
    ) else (
        call git clone %REPO_URL% .
    )
) else (
    echo [1/2] Git not found. Downloading ZIP directly via PowerShell...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile 'repo.zip'"
    
    echo Extracting files...
    powershell -Command "Expand-Archive -Path 'repo.zip' -DestinationPath 'temp_extract' -Force"
    
    :: Move extracted contents into current folder and clean up temporary archive
    xcopy /E /H /Y "temp_extract\%REPO_NAME%-%BRANCH%\*" "." >nul
    rmdir /S /Q "temp_extract"
    del /F /Q "repo.zip"
)

echo Files up to date!
echo.

:: =========================================================
:: 3. RUN MAIN.PY
:: =========================================================
echo [2/2] Launching main.py...
python main.py

pause
