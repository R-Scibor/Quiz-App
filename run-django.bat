REM ============================================================================
REM  FILE 2: run-django.bat (Helper script)
REM ============================================================================
@echo off
echo Activating virtual environment...
call "%~dp0\env\Scripts\activate.bat"
echo.
echo Starting Django server...
python manage.py runserver
goto:eof
REM ============================================================================
REM  END OF FILE 2: run-django.bat
REM ============================================================================