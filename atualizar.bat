@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Crie o ambiente conforme o readme.md primeiro.
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install --upgrade "yt-dlp[default]"
exit /b %errorlevel%
