@echo off

REM Move to project root (one level above /bat)
cd /d "%~dp0\.."

REM Check venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: venv not found.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Running Scale Logger GUI...
python py\scale_logger_gui.py

echo.
echo Script finished.
pause