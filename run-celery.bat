REM ============================================================================
REM  FILE 3: run-celery.bat (Helper script)
REM ============================================================================
@echo off
echo Activating virtual environment...
call "%~dp0\env\Scripts\activate.bat"
echo.
echo Starting Celery worker...
celery -A backend_project worker -l info -P solo
goto:eof
REM ============================================================================
REM  END OF FILE 3: run-celery.bat
REM ============================================================================