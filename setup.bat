@echo off
title Depository Setup
cls

echo.
echo  ====================================================
echo     Depository Setup  --  Dependency Installer
echo  ====================================================
echo.

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python was not found in your PATH.
    echo.
    echo   Please install Python 3.10 or newer from:
    echo     https://www.python.org/downloads/
    echo.
    echo   Make sure to check "Add Python to PATH" during installation.
    goto end
)

:: Show detected Python version
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo   Detected: %PYVER%

:: Check if version meets the 3.10+ requirement
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo   WARNING: %PYVER% is not supported.
    echo   Depository requires Python 3.10 or newer.
    echo   Please upgrade at https://www.python.org/downloads/
    goto end
)

echo.

:: Menu
echo   What would you like to do?
echo   1.  Install / upgrade required packages
echo   2.  Exit
echo.

:menu
set /p CHOICE="  Choice (1 or 2): "

if "%CHOICE%"=="1" goto install
if "%CHOICE%"=="2" goto bye
echo   Please enter 1 or 2.
goto menu

:: Install
:install
cls
echo.
echo  ====================================================
echo     Depository Setup  --  Dependency Installer
echo  ====================================================
echo.
echo   Installing: requests, gitpython, tqdm
echo.

python -m pip install --upgrade requests gitpython tqdm

if errorlevel 1 (
    echo.
    echo   ERROR: Package installation failed.
    echo   Try running this script as Administrator, or install manually:
    echo     pip install requests gitpython tqdm
    goto end
)

cls
echo.
echo  ====================================================
echo     Depository Setup  --  Dependency Installer
echo  ====================================================
echo.
echo   All packages installed successfully!
echo.
echo   You are ready to run Depository.py or MDepository.py.
echo.
echo   Tip: Set GITHUB_TOKEN_DEPOSITORY as an environment variable
echo   with a GitHub personal access token to raise the API rate
echo   limit from 60 to 5,000 requests per hour.

:end
echo.
echo   Press any key to exit...
pause >nul
exit /b

:bye
echo.
echo   Goodbye!
exit /b
