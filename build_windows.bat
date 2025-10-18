@echo off
REM Build script for Windows
REM Thai ID Card Reader - Build for Windows

echo ====================================
echo Thai ID Card Reader - Windows Build
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed. Please install Python 3 first.
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r build_requirements.txt

REM Build with PyInstaller
echo Building application...
pyinstaller --clean id_card_reader.spec

REM Check if build was successful
if exist "dist\ThaiIDCardReader.exe" (
    echo.
    echo Build successful!
    echo Executable: dist\ThaiIDCardReader.exe
    echo.
    echo To test the application:
    echo   dist\ThaiIDCardReader.exe
) else (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo.
echo Build completed!
pause
