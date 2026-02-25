@echo off

cd /d "%~dp0\.."

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: venv not found.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Running Scale Logger (CLI)...
python py\scale_logger.py

echo.
echo Script finished.
pause