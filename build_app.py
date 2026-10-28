"""Build without deleting unrelated build folders or spec files."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
for name in ('ffmpeg.exe', 'ffprobe.exe', 'icone.ico'):
    if not (root / name).is_file():
        raise SystemExit(f'Arquivo obrigatório ausente: {name}')
command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir', '--windowed',
           '--name', 'DePocosDownloader', '--icon', str(root / 'icone.ico'),
           '--collect-all', 'yt_dlp', '--collect-all', 'yt_dlp_ejs',
           '--add-data', f'{root / "icone.ico"};.',
           '--add-binary', f'{root / "ffmpeg.exe"};.',
           '--add-binary', f'{root / "ffprobe.exe"};.',
           '--distpath', str(root / 'dist'), '--workpath', str(root / 'build'),
           '--specpath', str(root / 'build'), str(root / 'DePocosDownloader.py')]
# The Codex-provided Python ssl.py loads this bundled CA distrust list at runtime.
ca_list = Path(sys.base_prefix) / 'Lib' / 'codex-rejected-cas.pem'
if ca_list.is_file():
    command[4:4] = ['--add-data', f'{ca_list};.']
subprocess.run(command, cwd=root, check=True)
