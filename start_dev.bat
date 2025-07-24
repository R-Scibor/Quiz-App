@echo off

REM ============================================================================
REM         Development Environment Startup Script (Single File Version)
REM
REM This script uses arguments to act as its own helper.
REM - When run without arguments, it launches Windows Terminal.
REM - When called with an argument (e.g., :django), it jumps to that label
REM   and executes the specific commands for that service.
REM ============================================================================

REM Check if an argument was passed (e.g., :django or :celery)
if "%1" neq "" goto %1


REM ============================================================================
REM  MAIN SCRIPT LOGIC (runs only if no arguments are passed)
REM ============================================================================

REM --- Configuration ---
set "SCRIPT_DIR=%~dp0"
REM The line below removes the trailing backslash from the path, which prevents parsing errors in wt.exe
if %SCRIPT_DIR:~-1%==\ set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "VITE_PATH=%SCRIPT_DIR%\frontend"


REM --- Launch Windows Terminal with a three-pane layout ---
REM %~f0 is a special variable that expands to the full path of THIS script file.
REM We call this script again, but with arguments to trigger the helper sections.

wt.exe new-tab --title "Vite" -d "%VITE_PATH%" cmd /k "npm run dev" ; ^
split-pane --title "Django" -V -d "%SCRIPT_DIR%" cmd /k ""%~f0" :django" ; ^
split-pane --title "Celery" -H -d "%SCRIPT_DIR%" cmd /k ""%~f0" :celery"

echo.
echo Starting development environment in Windows Terminal...
echo.

REM End the main part of the script to prevent it from running the helper sections.
goto :eof


REM ============================================================================
REM  HELPER SECTIONS (triggered by arguments)
REM ============================================================================

:django
REM This section runs when the script is called with the :django argument.
echo Activating virtual environment...
call "%~dp0\env\Scripts\activate.bat"
echo.
echo Starting Django server...
python manage.py runserver
goto :eof

:celery
REM This section runs when the script is called with the :celery argument.
echo Activating virtual environment...
call "%~dp0\env\Scripts\activate.bat"
echo.
echo Starting Celery worker...
celery -A backend_project worker -l info -P solo
goto :eof
