@echo off
REM ============================================================================
REM  FILE 1: start-dev.bat (Main script)
REM  This is the main script you will run.
REM ============================================================================

REM --- Configuration ---
set "SCRIPT_DIR=%~dp0"
REM The line below removes the trailing backslash from the path, which prevents parsing errors in wt.exe
if %SCRIPT_DIR:~-1%==\ set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "VITE_PATH=%SCRIPT_DIR%\frontend"

REM --- Reminder ---
echo.
echo ============================================================================
echo.
echo          !!! PAMIETAJ O URUCHOMIENIU DOCKERA Z REDIS !!!
echo.
echo ============================================================================
echo.


REM --- Launch Windows Terminal with a three-pane layout ---
REM This script now calls helper batch files to avoid complex quoting issues.

wt.exe new-tab --title "Vite" -d "%VITE_PATH%" cmd /k "npm run dev" ; ^
split-pane --title "Django" -V -d "%SCRIPT_DIR%" cmd /k "%SCRIPT_DIR%\run-django.bat" ; ^
split-pane --title "Celery" -H -d "%SCRIPT_DIR%" cmd /k "%SCRIPT_DIR%\run-celery.bat"

echo.
echo Starting development environment in Windows Terminal...
echo.

goto:eof

REM ============================================================================
REM  END OF FILE 1: start-dev.bat
REM ============================================================================

