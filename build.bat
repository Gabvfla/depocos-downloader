@echo off
chcp 65001 >nul
title DePoços Downloader - Compilação
color 0B

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║     DePoços Downloader - Script de Compilação     ║
echo ║          Gerando executável (.exe)                ║
echo ╚════════════════════════════════════════════════════╝
echo.

python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  PyInstaller não encontrado. Instalando...
    pip install pyinstaller
    echo.
)

echo [1/5] Verificando arquivos necessários...
if not exist "youtube_downloader_gui.py" (
    echo ❌ Erro: youtube_downloader_gui.py não encontrado!
    pause
    exit /b 1
)

if not exist "ffmpeg.exe" (
    echo ⚠️  Aviso: ffmpeg.exe não encontrado!
    echo    Baixe em: https://www.gyan.dev/ffmpeg/builds/
    pause
)

if not exist "ffprobe.exe" (
    echo ⚠️  Aviso: ffprobe.exe não encontrado!
    echo    Baixe em: https://www.gyan.dev/ffmpeg/builds/
    pause
)

echo ✅ Arquivos verificados!
echo.
echo [2/5] Limpando builds anteriores...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del /q *.spec
echo ✅ Limpeza concluída!
echo.
echo [3/5] Compilando executável...
echo    ⏳ Isso pode levar alguns minutos...
echo.
python -m PyInstaller --onefile --windowed --noconsole ^
--add-binary "ffmpeg.exe;." ^
--add-binary "ffprobe.exe;." ^
--icon "icone.ico" ^
--name "DePoçosDownloader" ^
--clean ^
DePocosDownloader.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Erro durante a compilação!
    pause
    exit /b 1
)

echo.
echo ✅ Compilação concluída!
echo.

echo [4/5] Verificando executável...
if exist "dist\DePoçosDownloader.exe" (
    echo ✅ Executável criado com sucesso!
    echo    📁 Local: dist\DePoçosDownloader.exe
    for %%I in ("dist\DePoçosDownloader.exe") do (
        echo    📊 Tamanho: %%~zI bytes
    )
) else (
    echo ❌ Erro: Executável não foi criado!
    pause
    exit /b 1
)
echo.
echo [5/5] Limpando arquivos temporários...
if exist "build" rmdir /s /q build
if exist "*.spec" del /q *.spec
echo ✅ Limpeza concluída!
echo.
echo ═══════════════════════════════════════════════════════
echo.
echo ✅ Processo concluído com sucesso! 🎉
echo.
echo 📦 Seu executável está pronto em:
echo    dist\DePoçosDownloader.exe
echo.
echo 💡 Você pode distribuir apenas esse arquivo .exe
echo    O FFmpeg já está incluído nele!
echo.
echo ═══════════════════════════════════════════════════════
echo.
pause