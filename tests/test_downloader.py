from pathlib import Path
import sys
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from downloader import Worker, Cancelled, validate_url, download_options

APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize('url', ['', 'file:///tmp/movie', 'ftp://example.com', 'https://', 'https://user:pass@example.com', 'https://example.com:wrong'])
def test_invalid_url(url):
    with pytest.raises(ValueError):
        validate_url(url)


def test_valid_url():
    assert validate_url(' https://youtu.be/abc ') == 'https://youtu.be/abc'


def test_quality_limit_applies_to_fallback(tmp_path):
    with patch('downloader.executable', return_value='/bin/ffmpeg'):
        options = download_options(tmp_path, 720)
    assert options['format'] == 'bv*[height<=720]+ba/b[height<=720]'
    assert 'extractor_args' not in options
    assert options['noplaylist']
    assert '%(id)s' in options['outtmpl']


def test_missing_ffmpeg(tmp_path):
    with patch('downloader.executable', return_value=None):
        with pytest.raises(RuntimeError, match='FFmpeg'):
            download_options(tmp_path, audio=True)


def test_numeric_progress_and_unknown_length():
    worker = Worker('https://example.com/video')
    values = []
    worker.progress.connect(values.append)
    worker.hook(dict(status='downloading', total_bytes=1000, downloaded_bytes=540, _percent_str='\x1b[94m54%'))
    worker.hook(dict(status='downloading', downloaded_bytes=100))
    assert values == [54, -1]
    worker.cancel()
    with pytest.raises(Cancelled):
        worker.hook(dict(status='finished'))


def test_playlist_rejected_before_processing(tmp_path):
    worker = Worker('https://example.com/playlist', str(tmp_path))
    results = []
    worker.result.connect(lambda *args: results.append(args))
    with patch('downloader.yt_dlp.YoutubeDL') as fake, patch('downloader.executable', return_value='/bin/ffmpeg'):
        ydl = fake.return_value.__enter__.return_value
        ydl.extract_info.return_value = {'_type': 'playlist', 'entries': [{}]}
        worker.run()
        ydl.process_ie_result.assert_not_called()
    assert results[0][0] is False


def test_download_failure_never_reports_success(tmp_path):
    worker = Worker('https://example.com/video', str(tmp_path))
    results = []
    worker.result.connect(lambda *args: results.append(args))
    with patch('downloader.yt_dlp.YoutubeDL') as fake, patch('downloader.executable', return_value='/bin/ffmpeg'):
        ydl = fake.return_value.__enter__.return_value
        ydl.extract_info.return_value = {'title': 'A video'}
        ydl.process_ie_result.side_effect = RuntimeError('disk full')
        worker.run()
    assert results == [(False, 'disk full')]


def test_precancelled_worker_never_starts_network():
    worker = Worker('https://example.com/video')
    worker.cancel()
    with patch('downloader.yt_dlp.YoutubeDL') as fake:
        worker.run()
        fake.assert_not_called()
