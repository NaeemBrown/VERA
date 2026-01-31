@echo off
title V.E.R.A. Installer Module
color 0A

echo ==================================================
echo      V.E.R.A. (Virtual Electronic Remote Assistant)
echo           SYSTEM DEPENDENCY INSTALLER
echo ==================================================
echo.
echo [1/3] Checking for Python...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your PATH.
    echo Please install Python 3.11+ and check "Add to PATH" in the installer.
    pause
    exit
)

echo.
echo [2/3] Upgrading PIP...
python -m pip install --upgrade pip

echo.
echo [3/3] Installing Libraries (This may take a while)...
python -m pip install -r requirements.txt

echo.
echo ==================================================
echo [SUCCESS] All systems ready.
echo You can now launch V.E.R.A. by running:
echo python interface.py
echo ==================================================
pause