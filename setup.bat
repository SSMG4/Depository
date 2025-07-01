@echo off
Setupository
cls

echo Installing required Python packages...
echo.

:: Run pip install
python -m pip install requests gitpython tqdm
if errorlevel 1 (
    echo.
    echo ERROR: Package installation failed.
    echo Please run this script as Administrator or check Python/PIP setup.
) else (
    echo.
    echo Packages installed successfully!
)

echo.
echo Press any key to exit...
pause >nul
exit /b


