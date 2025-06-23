@echo off
echo Setting up Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo Building executable...
pyinstaller app_gui_win.spec

echo Build complete! The executable is in the dist folder.
pause 