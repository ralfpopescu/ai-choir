@echo off
echo Building ai_choir for Windows...

echo Setting up Python virtual environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo Cleaning previous builds...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo Running PyInstaller...
pyinstaller app_gui_win.spec

echo.
echo Build complete! The executable is in dist\ai_choir\ai_choir.exe
pause
