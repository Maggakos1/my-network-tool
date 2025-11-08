@echo off
echo Installing Network Testing Tool Dependencies...
echo.

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo Python is not installed or not in PATH!
    echo Please install Python from https://python.org first.
    pause
    exit /b 1
)

echo Installing required packages...
pip install requests==2.31.0
pip install PySocks==1.7.1
pip install aiohttp==3.8.5
pip install socksio==1.0.0

echo.
echo Installation complete!
echo You can now run: python network_tool.py
pause