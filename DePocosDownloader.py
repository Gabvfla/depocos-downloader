import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QComboBox, QTextEdit, QFileDialog, QProgressBar,
                             QGroupBox, QRadioButton, QMessageBox, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
import yt_dlp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def base_path() -> str:
    """Retorna o diretório base, compatível com PyInstaller."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def configurar_ffmpeg():
    """Adiciona ffmpeg/ffprobe ao ambiente se estiverem na pasta do app."""
    bp = base_path()
    for nome in ('ffmpeg.exe', 'ffprobe.exe'):
        caminho = os.path.join(bp, nome)
        if os.path.exists(caminho):
            chave = 'FFMPEG_BINARY' if 'ffmpeg' in nome else 'FFPROBE_BINARY'
            os.environ[chave] = caminho


# ---------------------------------------------------------------------------
# Thread de download
# ---------------------------------------------------------------------------

class DownloadThread(QThread):
    progresso = pyqtSignal(str)
    concluido = pyqtSignal(bool, str)
    progresso_percentual = pyqtSignal(int)

    # Plataformas cujas URLs são aceitas
    PLATAFORMAS_VALIDAS = (
        'youtube.com', 'youtu.be',
        'instagram.com', 'twitter.com', 'x.com',
        'tiktok.com', 'vimeo.com', 'facebook.com',
        'twitch.tv', 'dailymotion.com',
    )

    def __init__(self, url: str, qualidade: str, tipo: str, pasta_destino: str):
        super().__init__()
        self.url = url
        self.qualidade = qualidade
        self.tipo = tipo
        self.pasta_destino = pasta_destino
        self._cancelar = False
        configurar_ffmpeg()

    def cancelar(self):
        self._cancelar = True

    # ------------------------------------------------------------------
    # Construção de opções compartilhadas
    # ------------------------------------------------------------------

    def _opcoes_base(self) -> dict:
        opcoes = {
            'outtmpl': os.path.join(self.pasta_destino, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progresso_hook],
            'quiet': True,
            'no_warnings': True,
            # Tenta múltiplos clientes em ordem; tv_embedded e ios
            # contornam bloqueios regionais e de age-gate na maioria dos casos.
            'extractor_args': {
                'youtube': {
                    'player_client': ['tv_embedded', 'ios', 'android', 'web'],
                }
            },
            # Não aborta na primeira indisponibilidade — tenta os fallbacks acima.
            'ignoreerrors': False,
            'geo_bypass': True,
        }
        if 'FFMPEG_BINARY' in os.environ:
            opcoes['ffmpeg_location'] = os.path.dirname(os.environ['FFMPEG_BINARY'])
        return opcoes

    # ------------------------------------------------------------------
    # Hooks de progresso
    # ------------------------------------------------------------------

    def progresso_hook(self, d: dict):
        if self._cancelar:
            raise Exception("Download cancelado pelo usuário.")

        if d['status'] == 'downloading':
            pct_str = d.get('_percent_str', '0%').strip()
            vel = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')

            try:
                pct = float(pct_str.replace('%', ''))
                self.progresso_percentual.emit(int(pct))
            except ValueError:
                pass

            self.progresso.emit(f"Baixando... {pct_str} | Velocidade: {vel} | ETA: {eta}")

        elif d['status'] == 'finished':
            self.progresso.emit("Download concluído! Processando arquivo...")

    # ------------------------------------------------------------------
    # Execução
    # ------------------------------------------------------------------

    def run(self):
        try:
            if self.tipo == 'audio':
                self._baixar_audio()
            else:
                self._baixar_video()
        except Exception as e:
            msg = str(e)
            if 'cancelado' in msg.lower():
                self.concluido.emit(False, "⚠️ Download cancelado.")
            elif 'not available' in msg.lower() or 'unavailable' in msg.lower():
                self.concluido.emit(False,
                    "❌ Este vídeo não está disponível na sua região ou foi removido.\n\n"
                    "Dicas:\n"
                    "• Tente outro vídeo\n"
                    "• Use uma VPN se o vídeo for bloqueado regionalmente\n"
                    f"\nDetalhe técnico: {msg}"
                )
            else:
                self.concluido.emit(False, f"Erro: {msg}")

    def _baixar_video(self):
        ALTURA_MAP = {
            '4K (2160p)': 2160,
            '2K (1440p)': 1440,
            'Full HD (1080p)': 1080,
            'HD (720p)': 720,
            'SD (480p)': 480,
            'Baixa (360p)': 360,
            'Melhor disponível': None,
        }
        altura = ALTURA_MAP.get(self.qualidade)
        if altura:
            fmt = f'bestvideo[height<={altura}][ext=mp4]+bestaudio[ext=m4a]/best[height<={altura}]'
        else:
            fmt = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best'

        opcoes = self._opcoes_base()
        opcoes['format'] = fmt
        opcoes['merge_output_format'] = 'mp4'

        with yt_dlp.YoutubeDL(opcoes) as ydl:
            self.progresso.emit("Obtendo informações do vídeo...")
            info = ydl.extract_info(self.url, download=False)
            titulo = info.get('title', 'Sem título')
            self.progresso.emit(f"Baixando: {titulo}")
            ydl.download([self.url])
            self.concluido.emit(True, f"✅ Vídeo baixado com sucesso!\n\n{titulo}")

    def _baixar_audio(self):
        opcoes = self._opcoes_base()
        opcoes['format'] = 'bestaudio/best'
        opcoes['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

        with yt_dlp.YoutubeDL(opcoes) as ydl:
            self.progresso.emit("Obtendo informações do áudio...")
            info = ydl.extract_info(self.url, download=False)
            titulo = info.get('title', 'Sem título')
            self.progresso.emit(f"Baixando áudio: {titulo}")
            ydl.download([self.url])
            self.concluido.emit(True, f"✅ Áudio baixado com sucesso!\n\n{titulo}")


# ---------------------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------------------

STYLE = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #5D3A9B, stop:0.5 #764ba2, stop:1 #5D3A9B);
}
QGroupBox {
    background-color: rgba(255, 255, 255, 0.95);
    border-radius: 12px;
    padding: 15px;
    margin-top: 10px;
    font-weight: bold;
    font-size: 13px;
    color: #333;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 5px 10px;
    background-color: #764ba2;
    color: white;
    border-radius: 6px;
}
QLineEdit, QComboBox {
    background-color: white;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    padding: 10px;
    font-size: 13px;
    color: #333;
}
QLineEdit:focus, QComboBox:focus {
    border: 2px solid #FBC02D;
}
QTextEdit {
    background-color: rgba(255, 255, 255, 0.95);
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    padding: 10px;
    font-size: 12px;
    color: #333;
}
QProgressBar {
    background-color: rgba(255, 255, 255, 0.9);
    border: none;
    border-radius: 10px;
    text-align: center;
    font-weight: bold;
    color: #333;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #764ba2, stop:1 #A166FF);
    border-radius: 10px;
}
QRadioButton {
    color: #333;
    font-size: 13px;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
}
QPushButton#pastaBtn, QPushButton#previewBtn {
    background-color: #764ba2;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton#pastaBtn:hover, QPushButton#previewBtn:hover {
    background-color: #5D3A9B;
}
QPushButton#cancelBtn {
    background-color: #c0392b;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton#cancelBtn:hover {
    background-color: #a93226;
}
"""

DOWNLOAD_BTN_STYLE = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #FBC02D, stop:1 #FFD700);
    color: #333;
    font-size: 16px;
    font-weight: bold;
    border: none;
    border-radius: 10px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #FFD700, stop:1 #FBC02D);
}
QPushButton:pressed {
    background: #FBC02D;
}
QPushButton:disabled {
    background: #cccccc;
    color: #666666;
}
"""


class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.thread: DownloadThread | None = None
        self.pasta_destino = os.path.join(os.path.expanduser('~'), 'Downloads')
        self._construir_ui()

    # ------------------------------------------------------------------
    # Construção da interface
    # ------------------------------------------------------------------

    def _construir_ui(self):
        self.setWindowTitle('DePoços Downloader')
        self.setGeometry(100, 100, 750, 730)
        self.setStyleSheet(STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(self._criar_header())
        layout.addWidget(self._criar_grupo_url())
        layout.addLayout(self._criar_linha_tipo_qualidade())
        layout.addWidget(self._criar_grupo_pasta())
        layout.addWidget(self._criar_progress_bar())
        layout.addWidget(self._criar_log())
        layout.addLayout(self._criar_botoes_acao())
        layout.addWidget(self._criar_rodape())

    def _criar_header(self) -> QFrame:
        frame = QFrame()
        logo_path = os.path.join(base_path(), 'logo_fundo.png')
        bg = f"background-image: url({logo_path.replace(chr(92), '/')});" if os.path.exists(logo_path) else ""
        frame.setStyleSheet(f"""
            QFrame {{
                {bg}
                background-repeat: no-repeat;
                background-position: center;
                background-color: rgba(118, 75, 162, 0.9);
                border-radius: 15px;
                padding: 20px;
            }}
        """)

        vbox = QVBoxLayout(frame)
        emoji = QLabel('🎬')
        emoji.setAlignment(Qt.AlignCenter)
        emoji.setStyleSheet('font-size: 50px; background: transparent;')
        vbox.addWidget(emoji)

        titulo = QLabel('DePoços Downloader')
        f = QFont(); f.setPointSize(24); f.setBold(True)
        titulo.setFont(f)
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet('color: white; background: transparent;')
        vbox.addWidget(titulo)

        sub = QLabel('Baixe vídeos e músicas de YouTube, Instagram, TikTok e muito mais')
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet('color: rgba(255,255,255,0.95); font-size: 13px; background: transparent;')
        vbox.addWidget(sub)
        return frame

    def _criar_grupo_url(self) -> QGroupBox:
        group = QGroupBox('🔗 URL do Vídeo')
        vbox = QVBoxLayout()

        linha = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('Cole aqui a URL do YouTube, Instagram, TikTok...')
        self.url_input.setMinimumHeight(40)
        linha.addWidget(self.url_input)

        preview_btn = QPushButton('🔍 Preview')
        preview_btn.setObjectName('previewBtn')
        preview_btn.setMinimumHeight(40)
        preview_btn.clicked.connect(self._buscar_preview)
        linha.addWidget(preview_btn)
        vbox.addLayout(linha)

        self.preview_label = QLabel('')
        self.preview_label.setStyleSheet('color: #555; font-size: 12px; padding: 4px;')
        self.preview_label.setWordWrap(True)
        vbox.addWidget(self.preview_label)

        group.setLayout(vbox)
        return group

    def _criar_linha_tipo_qualidade(self) -> QHBoxLayout:
        hbox = QHBoxLayout()

        tipo_group = QGroupBox('🎯 Tipo de Download')
        tipo_layout = QVBoxLayout()
        self.radio_video = QRadioButton('📹 Vídeo')
        self.radio_audio = QRadioButton('🎵 Áudio (MP3)')
        self.radio_video.setChecked(True)
        self.radio_video.toggled.connect(self._atualizar_qualidade)
        tipo_layout.addWidget(self.radio_video)
        tipo_layout.addWidget(self.radio_audio)
        tipo_group.setLayout(tipo_layout)
        hbox.addWidget(tipo_group)

        qual_group = QGroupBox('⚙️ Qualidade')
        qual_layout = QVBoxLayout()
        self.qualidade_combo = QComboBox()
        self.qualidade_combo.addItems([
            'Melhor disponível',
            '4K (2160p)', '2K (1440p)', 'Full HD (1080p)',
            'HD (720p)', 'SD (480p)', 'Baixa (360p)',
        ])
        self.qualidade_combo.setCurrentIndex(3)
        self.qualidade_combo.setMinimumHeight(40)
        qual_layout.addWidget(self.qualidade_combo)
        qual_group.setLayout(qual_layout)
        hbox.addWidget(qual_group)

        return hbox

    def _criar_grupo_pasta(self) -> QGroupBox:
        group = QGroupBox('📁 Pasta de Destino')
        hbox = QHBoxLayout()

        self.pasta_label = QLabel(self.pasta_destino)
        self.pasta_label.setStyleSheet(
            'padding: 10px; background-color: #f5f5f5; border-radius: 8px; color: #555; font-size: 12px;'
        )
        self.pasta_label.setWordWrap(True)

        pasta_btn = QPushButton('Escolher Pasta')
        pasta_btn.setObjectName('pastaBtn')
        pasta_btn.setMinimumHeight(40)
        pasta_btn.clicked.connect(self._escolher_pasta)

        hbox.addWidget(self.pasta_label, 1)
        hbox.addWidget(pasta_btn)
        group.setLayout(hbox)
        return group

    def _criar_progress_bar(self) -> QProgressBar:
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setTextVisible(True)
        return self.progress_bar

    def _criar_log(self) -> QTextEdit:
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(110)
        self.log_text.setPlaceholderText('Status do download aparecerá aqui...')
        return self.log_text

    def _criar_botoes_acao(self) -> QHBoxLayout:
        hbox = QHBoxLayout()

        self.download_btn = QPushButton('⬇️  BAIXAR AGORA')
        self.download_btn.setMinimumHeight(50)
        self.download_btn.setStyleSheet(DOWNLOAD_BTN_STYLE)
        self.download_btn.clicked.connect(self._iniciar_download)

        self.cancel_btn = QPushButton('✖ Cancelar')
        self.cancel_btn.setObjectName('cancelBtn')
        self.cancel_btn.setMinimumHeight(50)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancelar_download)

        hbox.addWidget(self.download_btn, 3)
        hbox.addWidget(self.cancel_btn, 1)
        return hbox

    def _criar_rodape(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet('background: transparent;')
        vbox = QVBoxLayout(frame)
        vbox.setSpacing(4)

        r1 = QLabel('Feito com ❤️ por GabrielDePoços')
        r1.setAlignment(Qt.AlignCenter)
        r1.setStyleSheet('color: white; font-size: 13px; font-weight: bold;')

        r2 = QLabel('Requer FFmpeg instalado | v2.0 — YouTube, Instagram, TikTok e mais')
        r2.setAlignment(Qt.AlignCenter)
        r2.setStyleSheet('color: rgba(255,255,255,0.7); font-size: 10px;')

        vbox.addWidget(r1)
        vbox.addWidget(r2)
        return frame

    # ------------------------------------------------------------------
    # Lógica
    # ------------------------------------------------------------------

    def _atualizar_qualidade(self):
        self.qualidade_combo.setEnabled(self.radio_video.isChecked())

    def _escolher_pasta(self):
        pasta = QFileDialog.getExistingDirectory(self, 'Escolher Pasta', self.pasta_destino)
        if pasta:
            self.pasta_destino = pasta
            self.pasta_label.setText(pasta)

    def _adicionar_log(self, msg: str):
        self.log_text.append(msg)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def _buscar_preview(self):
        url = self.url_input.text().strip()
        if not url:
            self.preview_label.setText('⚠️ Cole uma URL primeiro.')
            return

        self.preview_label.setText('🔍 Buscando informações...')
        QApplication.processEvents()

        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            titulo = info.get('title', 'N/A')
            duracao = info.get('duration')
            duracao_str = f'{duracao // 60}:{duracao % 60:02d}' if duracao else 'N/A'
            uploader = info.get('uploader', 'N/A')
            self.preview_label.setText(
                f'🎬 {titulo}  •  ⏱ {duracao_str}  •  👤 {uploader}'
            )
        except Exception as e:
            self.preview_label.setText(f'❌ Não foi possível obter informações: {e}')

    def _iniciar_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, '⚠️ Aviso', 'Por favor, insira uma URL válida!')
            return

        # Verifica se yt-dlp consegue identificar o domínio (mais robusto que checar string)
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                ydl.extract_info(url, download=False, process=False)
        except yt_dlp.utils.UnsupportedError:
            QMessageBox.warning(self, '⚠️ URL inválida', 'Plataforma não suportada pelo yt-dlp.')
            return
        except Exception:
            pass  # Outros erros serão capturados na thread com mensagem adequada

        self.download_btn.setEnabled(False)
        self.download_btn.setText('⏳ Baixando...')
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.preview_label.setText('')

        qualidade = self.qualidade_combo.currentText()
        tipo = 'audio' if self.radio_audio.isChecked() else 'video'

        self.thread = DownloadThread(url, qualidade, tipo, self.pasta_destino)
        self.thread.progresso.connect(self._adicionar_log)
        self.thread.concluido.connect(self._download_concluido)
        self.thread.progresso_percentual.connect(self.progress_bar.setValue)
        self.thread.start()

    def _cancelar_download(self):
        if self.thread and self.thread.isRunning():
            self.thread.cancelar()
            self.cancel_btn.setEnabled(False)
            self._adicionar_log('⚠️ Cancelando download...')

    def _download_concluido(self, sucesso: bool, mensagem: str):
        self.download_btn.setEnabled(True)
        self.download_btn.setText('⬇️  BAIXAR AGORA')
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(100 if sucesso else 0)
        self._adicionar_log('\n' + mensagem)

        if sucesso:
            QMessageBox.information(self, '✅ Sucesso', mensagem)
        else:
            if 'cancelado' not in mensagem.lower():
                QMessageBox.critical(self, '❌ Erro', mensagem)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    janela = YouTubeDownloader()
    janela.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()