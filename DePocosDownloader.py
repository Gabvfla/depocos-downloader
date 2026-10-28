"""DePoços Downloader: desktop interface inspired by Poços Hub."""
import sys
from pathlib import Path
from PyQt5.QtCore import Qt, QSettings, QStandardPaths, QUrl
from PyQt5.QtGui import QDesktopServices, QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QPlainTextEdit,
    QFileDialog, QProgressBar, QFrame, QScrollArea)
from downloader import Worker, base_path, validate_url

STYLE = '''
QWidget { background: #170F28; color: #F7F3FF; font-family: "Segoe UI"; font-size: 14px; }
QLabel { background: transparent; }
QLabel#title { font-size: 28px; font-weight: 700; }
QLabel#subtitle, QLabel#muted { color: #AEA0C9; }
QFrame#panel { background: #211337; border: 1px solid #604081; border-radius: 12px; }
QLineEdit, QComboBox, QPlainTextEdit { background: #211337; border: 1px solid #604081; border-radius: 6px; padding: 8px; selection-background-color: #7547DD; }
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus { border: 1px solid #AD7DFF; }
QComboBox QAbstractItemView { background: #322044; color: #F7F3FF; selection-background-color: #7547DD; }
QPushButton { background: #322044; border: 1px solid #604081; border-radius: 6px; padding: 10px 16px; font-weight: 600; }
QPushButton:hover { background: #46305F; }
QPushButton:focus { border: 1px solid #AD7DFF; }
QPushButton#primary { background: #7547DD; border-color: #7547DD; color: #FFFFFF; }
QPushButton#primary:hover { background: #8E64F3; }
QPushButton:disabled, QComboBox:disabled { background: #211337; color: #AEA0C9; border-color: #322044; }
QProgressBar { background: #322044; border: 0; border-radius: 4px; min-height: 8px; }
QProgressBar::chunk { background: #AD7DFF; border-radius: 4px; }
QScrollArea { border: 0; }
'''


class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.closing = False
        self.settings = QSettings('GabrielDePocos', 'DePocosDownloader')
        self.setWindowTitle('DePoços Downloader')
        self.setWindowIcon(QIcon(str(base_path() / 'icone.ico')))
        self.resize(780, 720)
        self.setMinimumSize(520, 580)
        self.setStyleSheet(STYLE)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)
        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(12)
        title = QLabel('DePoços <span style="color:#AD7DFF">Downloader</span>')
        title.setObjectName('title')
        layout.addWidget(title)
        subtitle = QLabel('Seus vídeos e músicas, salvos no seu computador.')
        subtitle.setObjectName('subtitle')
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        layout.addWidget(QLabel('Link do vídeo'))
        row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setAccessibleName('Link do vídeo')
        self.url_input.setPlaceholderText('https://www.youtube.com/watch?v=…')
        self.url_input.setClearButtonEnabled(True)
        self.url_input.returnPressed.connect(self.preview)
        row.addWidget(self.url_input, 1)
        self.preview_btn = QPushButton('Ver detalhes')
        self.preview_btn.clicked.connect(self.preview)
        row.addWidget(self.preview_btn)
        layout.addLayout(row)
        panel = QFrame()
        panel.setObjectName('panel')
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        self.media_title = QLabel('Pronto para o próximo download')
        self.media_title.setTextFormat(Qt.PlainText)
        self.media_title.setWordWrap(True)
        self.media_title.setStyleSheet('font-size: 18px; font-weight: 600;')
        self.media_detail = QLabel('Cole um link para consultar o título e a duração.')
        self.media_detail.setObjectName('muted')
        self.media_detail.setTextFormat(Qt.PlainText)
        self.media_detail.setWordWrap(True)
        panel_layout.addWidget(self.media_title)
        panel_layout.addWidget(self.media_detail)
        layout.addWidget(panel)
        row = QHBoxLayout()
        self.kind = QComboBox()
        self.kind.addItem('Vídeo', False)
        self.kind.addItem('Áudio MP3 · 192 kbps', True)
        self.quality = QComboBox()
        for label, height in [('Melhor disponível', None), ('4K · 2160p', 2160), ('2K · 1440p', 1440), ('Full HD · 1080p', 1080), ('HD · 720p', 720), ('SD · 480p', 480), ('360p', 360)]:
            self.quality.addItem(label, height)
        self.quality.setCurrentIndex(3)
        for label, widget in [('Formato', self.kind), ('Qualidade máxima', self.quality)]:
            group = QVBoxLayout()
            group.addWidget(QLabel(label))
            widget.setAccessibleName(label)
            group.addWidget(widget)
            row.addLayout(group, 1)
        self.kind.currentIndexChanged.connect(self.update_quality)
        layout.addLayout(row)
        hint = QLabel('Vídeo: formato original ou MKV quando houver união de áudio e vídeo.')
        hint.setObjectName('muted')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addWidget(QLabel('Salvar em'))
        row = QHBoxLayout()
        default = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation) or str(Path.home() / 'Downloads')
        self.folder = QLineEdit(str(self.settings.value('folder', default)))
        self.folder.setAccessibleName('Pasta de destino')
        self.folder_btn = QPushButton('Escolher pasta')
        self.folder_btn.clicked.connect(self.choose_folder)
        row.addWidget(self.folder, 1)
        row.addWidget(self.folder_btn)
        layout.addLayout(row)
        self.status = QLabel('Aguardando um link.')
        self.status.setTextFormat(Qt.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        row = QHBoxLayout()
        self.download_btn = QPushButton('Baixar arquivo')
        self.download_btn.setObjectName('primary')
        self.download_btn.clicked.connect(self.download)
        self.cancel_btn = QPushButton('Cancelar')
        self.cancel_btn.clicked.connect(self.cancel)
        self.cancel_btn.setEnabled(False)
        self.open_btn = QPushButton('Abrir pasta')
        self.open_btn.clicked.connect(self.open_folder)
        row.addWidget(self.download_btn, 1)
        row.addWidget(self.cancel_btn)
        row.addWidget(self.open_btn)
        layout.addLayout(row)
        self.details_btn = QPushButton('Mostrar diagnóstico')
        self.details_btn.setCheckable(True)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(150)
        self.log.setMaximumHeight(120)
        self.log.hide()
        self.details_btn.toggled.connect(self.log.setVisible)
        layout.addWidget(self.details_btn, alignment=Qt.AlignLeft)
        layout.addWidget(self.log)
        layout.addStretch()
        footer = QLabel('DePoços · YouTube, Instagram, TikTok e outras plataformas compatíveis')
        footer.setObjectName('muted')
        footer.setWordWrap(True)
        layout.addWidget(footer)

    def update_quality(self):
        self.quality.setEnabled(self.worker is None and not self.kind.currentData())

    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, 'Salvar downloads em', self.folder.text())
        if path:
            self.folder.setText(path)

    def open_folder(self):
        path = Path(self.folder.text()).expanduser()
        if path.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))
        else:
            self.status.setText('A pasta ainda não existe. Escolha uma pasta ou inicie o download para criá-la.')

    def preview(self):
        self.start(False)

    def download(self):
        self.start(True)

    def start(self, downloading):
        if self.worker is not None:
            return
        try:
            url = validate_url(self.url_input.text())
            if downloading and not self.folder.text().strip():
                raise ValueError('Escolha uma pasta de destino.')
        except ValueError as exc:
            self.status.setText(str(exc))
            self.url_input.setFocus()
            return
        self.log.clear()
        self.progress_bar.setRange(0, 0)
        self.media_title.setText('Buscando informações…')
        self.media_detail.setText('A consulta pode levar alguns segundos.')
        self.worker = Worker(url, self.folder.text().strip() if downloading else None,
                             self.quality.currentData(), self.kind.currentData(), self)
        self.worker.status.connect(self.on_status)
        self.worker.progress.connect(self.on_progress)
        self.worker.metadata.connect(self.on_metadata)
        self.worker.result.connect(self.on_result)
        self.worker.finished.connect(self.on_finished)
        self.set_busy(True)
        self.worker.start()

    def set_busy(self, busy):
        for widget in (self.url_input, self.preview_btn, self.kind, self.quality,
                       self.folder, self.folder_btn, self.download_btn):
            widget.setEnabled(not busy)
        self.cancel_btn.setEnabled(busy)
        if not busy:
            self.update_quality()

    def on_status(self, message):
        self.status.setText(message)
        if not message.startswith('Baixando arquivo'):
            self.log.appendPlainText(message)

    def on_progress(self, value):
        self.progress_bar.setRange(0, 0 if value < 0 else 100)
        if value >= 0:
            self.progress_bar.setValue(value)

    def on_metadata(self, data):
        self.media_title.setText(data.get('title') or 'Sem título')
        duration = data.get('duration')
        seconds = int(duration) if duration is not None else None
        time = f'{seconds // 60}:{seconds % 60:02d}' if seconds is not None else 'Duração não informada'
        self.media_detail.setText(f"{data.get('uploader') or 'Autor não informado'} · {time}")

    def on_result(self, success, message):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success and self.worker.folder else 0)
        if not success:
            self.media_title.setText('Operação cancelada' if self.worker.cancel_event.is_set() else 'Não foi possível concluir')
            self.media_detail.setText('Confira os detalhes abaixo e tente novamente.')
        self.on_status(message)
        if success and self.worker.folder:
            self.settings.setValue('folder', self.folder.text())

    def on_finished(self):
        self.worker.deleteLater()
        self.worker = None
        self.set_busy(False)
        if self.closing:
            self.close()

    def cancel(self):
        if self.worker:
            self.worker.cancel()
            self.cancel_btn.setEnabled(False)
            self.status.setText('Cancelando… Uma conversão em andamento precisa terminar primeiro.')

    def closeEvent(self, event):
        if self.worker:
            self.closing = True
            self.cancel()
            event.ignore()
        else:
            event.accept()


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont('Segoe UI', 10))
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
