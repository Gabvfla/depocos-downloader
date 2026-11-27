"""Build without deleting unrelated build folders or spec files."""
from importlib.util import find_spec
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
           '--collect-all', 'curl_cffi',
           '--add-data', f'{root / "icone.ico"};.',
           '--add-binary', f'{root / "ffmpeg.exe"};.',
           '--add-binary', f'{root / "ffprobe.exe"};.',
           '--distpath', str(root / 'dist'), '--workpath', str(root / 'build'),
           '--specpath', str(root / 'build'), str(root / 'DePocosDownloader.py')]
curl = find_spec('curl_cffi')
if curl is None:
    raise SystemExit('Instale as dependências de requirements.txt antes de compilar.')
curl_libraries = Path(curl.submodule_search_locations[0]).with_name('curl_cffi.libs')
if curl_libraries.is_dir():
    command[4:4] = ['--add-binary', f'{curl_libraries / "*.dll"};curl_cffi.libs']
# The Codex-provided Python ssl.py loads this bundled CA distrust list at runtime.
ca_list = Path(sys.base_prefix) / 'Lib' / 'codex-rejected-cas.pem'
if ca_list.is_file():
    command[4:4] = ['--add-data', f'{ca_list};.']
subprocess.run(command, cwd=root, check=True)
