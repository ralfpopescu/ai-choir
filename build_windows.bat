@echo off

:: Create virtual environment
python -m venv venv
call venv\Scripts\activate.bat

:: Install requirements
pip install -r requirements.txt
pip install -r requirements_gui.txt

:: Build the application
pyinstaller app_gui.spec

:: Deactivate virtual environment
call venv\Scripts\deactivate.bat

:: Clean up virtual environment
rmdir /s /q venv

echo Build complete! Check the dist folder for the executable.
pause 