@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating virtual environment...
    py -3 -m venv .venv 2>nul || python -m venv .venv
) else (
    echo [1/4] Reusing existing virtual environment...
)

if not exist ".venv\Scripts\python.exe" (
    echo Failed to create .venv. Make sure Python 3.10+ is installed.
    exit /b 1
)

echo [2/4] Upgrading pip...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo [3/4] Installing project dependencies...
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo [4/4] Installing project in editable mode...
call ".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 exit /b 1

echo.
echo Environment is ready.
echo Use this interpreter in VS Code:
echo   %cd%\.venv\Scripts\python.exe
echo.
echo To run the app:
echo   .venv\Scripts\python.exe main.py
endlocal