from pathlib import Path
import sys
import threading
from unittest.mock import patch

from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from DePocosDownloader import YouTubeDownloader

APP = QApplication.instance() or QApplication([])


def test_invalid_link_stays_idle():
    window = YouTubeDownloader()
    window.url_input.setText('not a link')
    window.download()
    assert window.worker is None
    assert window.download_btn.isEnabled()
    assert 'https://' in window.status.text()
    window.close()


def test_audio_disables_video_quality():
    window = YouTubeDownloader()
    window.kind.setCurrentIndex(1)
    assert not window.quality.isEnabled()
    window.kind.setCurrentIndex(0)
    assert window.quality.isEnabled()
    window.close()


def test_preview_is_async_and_close_waits_for_worker():
    entered, release = threading.Event(), threading.Event()
    def slow_extract(*args, **kwargs):
        entered.set()
        release.wait(3)
        return {'title': 'Test', 'duration': 19}
    window = YouTubeDownloader()
    window.show()
    window.url_input.setText('https://example.com/video')
    ticks = []
    timer = QTimer()
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start(10)
    with patch('downloader.yt_dlp.YoutubeDL') as fake:
        fake.return_value.__enter__.return_value.extract_info.side_effect = slow_extract
        window.preview()
        try:
            for _ in range(100):
                QTest.qWait(10)
                if entered.is_set():
                    break
            assert entered.is_set()
            assert ticks
            assert not window.download_btn.isEnabled()
            window.close()
            assert window.isVisible()
            assert window.worker.cancel_event.is_set()
        finally:
            release.set()
            for _ in range(100):
                QTest.qWait(10)
                if window.worker is None:
                    break
            timer.stop()
        assert window.worker is None
        assert not window.isVisible()
