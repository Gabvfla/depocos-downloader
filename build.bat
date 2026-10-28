@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Crie o ambiente primeiro: python -m venv .venv
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" build_app.py
if errorlevel 1 exit /b 1
echo Aplicativo pronto em dist\DePocosDownloader\DePocosDownloader.exe
