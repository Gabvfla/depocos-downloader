"""Download engine. Network activity stays outside the GUI thread."""
import os
from pathlib import Path
import shutil
import sys
import traceback
from threading import Event
from urllib.parse import urlsplit
from PyQt5.QtCore import QThread, pyqtSignal
import yt_dlp


def base_path():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))


def executable(name):
    local = base_path() / (name + ('.exe' if os.name == 'nt' else ''))
    return str(local) if local.is_file() else shutil.which(name)


def validate_url(url):
    url = url.strip()
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError
        parsed.port
    except ValueError:
        raise ValueError('Cole um link completo, começando com https://.') from None
    return url


def common_options():
    options = dict(quiet=True, noprogress=True, noplaylist=True, socket_timeout=20,
                   retries=3, fragment_retries=3, windowsfilenames=True)
    if executable('ffmpeg') and executable('ffprobe'):
        options['ffmpeg_location'] = str(Path(executable('ffmpeg')).parent)
    runtimes = {name: {'path': path} for name in ('deno', 'node') if (path := executable(name))}
    if runtimes:
        options['js_runtimes'] = runtimes
    # Reject playlists before any files are downloaded, including playlist-only URLs.
    def single_video(info, *, incomplete=False):
        if info.get('_type') in ('playlist', 'multi_video') or info.get('playlist_id'):
            return 'Use o link de um vídeo individual. Playlists não são suportadas.'
    options['match_filter'] = single_video
    return options


def download_options(folder, height=None, audio=False):
    options = common_options()
    if not executable('ffmpeg') or not executable('ffprobe'):
        raise RuntimeError('FFmpeg e FFprobe não encontrados. Coloque os dois na pasta do aplicativo ou no PATH.')
    folder = Path(folder).expanduser()
    folder.mkdir(parents=True, exist_ok=True)
    options.update(outtmpl=str(folder / '%(title).160B [%(id)s].%(ext)s'), overwrites=False)
    if audio:
        options.update(format='bestaudio/best', postprocessors=[{
            'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}])
    else:
        limit = f'[height<={int(height)}]' if height else ''
        options.update(format=f'bv*{limit}+ba/b{limit}', merge_output_format='mkv',
                       format_sort=['vcodec:h264', 'acodec:aac'])
    return options


class Cancelled(Exception):
    pass


class Worker(QThread):
    status = pyqtSignal(str)
    progress = pyqtSignal(int)
    result = pyqtSignal(bool, str)
    metadata = pyqtSignal(dict)

    def __init__(self, url, folder=None, height=None, audio=False, parent=None):
        super().__init__(parent)
        self.url, self.folder, self.height, self.audio = url, folder, height, audio
        self.cancel_event = Event()

    def cancel(self):
        self.cancel_event.set()

    def check_cancel(self):
        if self.cancel_event.is_set():
            raise Cancelled('Operação cancelada.')

    def hook(self, data):
        self.check_cancel()
        if data['status'] == 'downloading':
            total = data.get('total_bytes') or data.get('total_bytes_estimate')
            self.progress.emit(min(99, int(100 * data.get('downloaded_bytes', 0) / total)) if total else -1)
            speed, eta = data.get('speed'), data.get('eta')
            detail = f' · {speed / 1024 / 1024:.1f} MB/s' if speed else ''
            if eta is not None:
                detail += f' · {int(eta)} s restantes'
            self.status.emit('Baixando arquivo' + detail)
        elif data['status'] == 'finished':
            self.progress.emit(-1)
            self.status.emit('Preparando arquivo final…')

    def post_hook(self, data):
        self.check_cancel()
        self.progress.emit(-1)
        self.status.emit('Convertendo áudio…' if self.audio else 'Finalizando vídeo…')

    def run(self):
        try:
            self.check_cancel()
            url = validate_url(self.url)
            options = download_options(self.folder, self.height, self.audio) if self.folder else common_options()
            options.update(progress_hooks=[self.hook], postprocessor_hooks=[self.post_hook], logger=self)
            self.status.emit('Buscando informações…')
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False, process=False)
                self.check_cancel()
                if not info or info.get('_type') in ('playlist', 'multi_video'):
                    raise ValueError('Use o link de um vídeo individual. Playlists não são suportadas.')
                info = ydl.process_ie_result(info, download=self.folder is not None)
            self.check_cancel()
            if not info or info.get('_type') in ('playlist', 'multi_video'):
                raise ValueError('Use o link de um vídeo individual. Playlists não são suportadas.')
            self.metadata.emit({key: info.get(key) for key in ('title', 'uploader', 'duration')})
            self.result.emit(True, 'Download concluído. Arquivo salvo na pasta escolhida.' if self.folder else 'Informações carregadas.')
        except Exception as exc:
            for error in getattr(exc, 'unexpected_errors', []):
                self.status.emit('Diagnóstico de conexão: ' + ''.join(traceback.format_exception(error)))
            self.result.emit(False, 'Operação cancelada.' if self.cancel_event.is_set() else str(exc))

    def debug(self, message):
        pass

    def warning(self, message):
        self.status.emit('Aviso: ' + message)

    def error(self, message):
        pass
