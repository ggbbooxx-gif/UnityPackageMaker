@echo off
setlocal

cd /d "%~dp0"

set "BUILD_OK="

echo [1/4] Initializing Python environment...
call init_env.bat
if errorlevel 1 exit /b 1

echo [2/4] Installing PyInstaller...
call ".venv\Scripts\python.exe" -m pip install pyinstaller
if errorlevel 1 exit /b 1

echo [3/4] Cleaning old build output...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [4/4] Building UnityPackageMaker.exe...
call :build_with_retry
if not defined BUILD_OK exit /b 1

echo.
echo Build complete.
echo EXE path:
echo   %cd%\dist\UnityPackageMaker.exe
endlocal

goto :eof

:build_with_retry
for /l %%I in (1,1,3) do (
    call :build_once %%I
    if defined BUILD_OK goto :eof
)
echo Build failed after 3 attempts.
exit /b 1

:build_once
echo   Attempt %1/3...
if exist "dist\UnityPackageMaker.exe" del /f /q "dist\UnityPackageMaker.exe" >nul 2>nul
call ".venv\Scripts\pyinstaller.exe" ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onefile ^
  --name "UnityPackageMaker" ^
  --paths "src" ^
  --hidden-import "PyQt6.sip" ^
  --collect-submodules "unity_package_maker" ^
  "main.py"
if not errorlevel 1 (
    set "BUILD_OK=1"
    exit /b 0
)
echo   Build attempt %1 failed, waiting 5 seconds before retry...
powershell -NoProfile -Command "Start-Sleep -Seconds 5" >nul
exit /b 0