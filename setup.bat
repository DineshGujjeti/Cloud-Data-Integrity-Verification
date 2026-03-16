@REM Setup and Run Script for Cloud Data Integrity Verification System
@REM This batch script sets up the environment and runs the Flask application
@REM Run as: setup.bat

@echo off
cls

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║  Cloud Data Integrity Verification System                      ║
echo ║  Setup and Installation Script                                 ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH.
    echo    Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo ✓ Python found: 
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

echo ✓ Virtual environment created
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

if %errorlevel% neq 0 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✓ Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies from requirements.txt...
pip install --upgrade pip

if %errorlevel% neq 0 (
    echo ⚠️ Warning: pip upgrade failed, continuing...
)

pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✓ Dependencies installed successfully
echo.

REM Create necessary directories
echo Creating necessary directories...
if not exist uploads mkdir uploads
if not exist reports mkdir reports
if not exist sample_data mkdir sample_data

echo ✓ Directories created
echo.

REM Display instructions
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    SETUP COMPLETE                              ║
echo ╠════════════════════════════════════════════════════════════════╣
echo ║                                                                ║
echo ║  To start the Flask application, run:                          ║
echo ║                                                                ║
echo ║      python app.py                                             ║
echo ║                                                                ║
echo ║  This will start the server on: http://127.0.0.1:5000         ║
echo ║                                                                ║
echo ║  Open your web browser and navigate to that address            ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

setlocal enabledelayedexpansion
set /p start="Do you want to start the Flask application now? (y/n) "

if /i "%start%"=="y" (
    echo Starting Flask application...
    echo.
    python app.py
) else (
    echo Setup complete. Run 'python app.py' to start the application.
)

pause
