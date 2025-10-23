"""
DePoços Downloader - Aplicativo Desktop com Interface Gráfica
Feito com ❤️ por GabrielDePoços
Requer: 
- pip install yt-dlp PyQt5
- FFmpeg incluído ou instalado no PATH
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QComboBox, QTextEdit, QFileDialog, QProgressBar,
                             QGroupBox, QRadioButton, QMessageBox, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPixmap
import yt_dlp

class DownloadThread(QThread):
    progresso = pyqtSignal(str)
    concluido = pyqtSignal(bool, str)
    progresso_percentual = pyqtSignal(int)
    
    def __init__(self, url, qualidade, tipo, pasta_destino):
        super().__init__()
        self.url = url
        self.qualidade = qualidade
        self.tipo = tipo
        self.pasta_destino = pasta_destino
        self.configurar_ffmpeg()
    
    def configurar_ffmpeg(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        ffmpeg_path = os.path.join(base_path, 'ffmpeg.exe')
        ffprobe_path = os.path.join(base_path, 'ffprobe.exe')
        
        if os.path.exists(ffmpeg_path):
            os.environ['FFMPEG_BINARY'] = ffmpeg_path
        if os.path.exists(ffprobe_path):
            os.environ['FFPROBE_BINARY'] = ffprobe_path
        
    def run(self):
        try:
            if self.tipo == "audio":
                self.baixar_audio()
            else:
                self.baixar_video()
        except Exception as e:
            self.concluido.emit(False, f"Erro: {str(e)}")
    
    def progresso_hook(self, d):
        if d['status'] == 'downloading':
            porcentagem_str = d.get('_percent_str', '0%').strip()
            velocidade = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            
            try:
                porcentagem = float(porcentagem_str.replace('%', ''))
                self.progresso_percentual.emit(int(porcentagem))
            except:
                pass
            
            self.progresso.emit(f"Baixando... {porcentagem_str} | Velocidade: {velocidade} | ETA: {eta}")
            
        elif d['status'] == 'finished':
            self.progresso.emit("Download concluído! Processando arquivo...")
    
    def baixar_video(self):
        formato_map = {
            "4K (2160p)": 2160,
            "2K (1440p)": 1440,
            "Full HD (1080p)": 1080,
            "HD (720p)": 720,
            "SD (480p)": 480,
            "Baixa (360p)": 360,
            "Melhor disponível": None
        }
        
        altura = formato_map.get(self.qualidade)
        
        if altura:
            formato = f'bestvideo[height<={altura}][ext=mp4]+bestaudio[ext=m4a]/best[height<={altura}]'
        else:
            formato = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best'
        
        opcoes = {
            'format': formato,
            'outtmpl': os.path.join(self.pasta_destino, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'progress_hooks': [self.progresso_hook],
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
        }
        
        if 'FFMPEG_BINARY' in os.environ:
            opcoes['ffmpeg_location'] = os.path.dirname(os.environ['FFMPEG_BINARY'])
        
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            self.progresso.emit("Obtendo informações do vídeo...")
            info = ydl.extract_info(self.url, download=False)
            titulo = info['title']
            
            self.progresso.emit(f"Baixando: {titulo}")
            ydl.download([self.url])
            
            self.concluido.emit(True, f"✅ Vídeo baixado com sucesso!\n\n{titulo}")
    
    def baixar_audio(self):
        opcoes = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.pasta_destino, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [self.progresso_hook],
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
        }
        
        if 'FFMPEG_BINARY' in os.environ:
            opcoes['ffmpeg_location'] = os.path.dirname(os.environ['FFMPEG_BINARY'])
        
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            self.progresso.emit("Obtendo informações do áudio...")
            info = ydl.extract_info(self.url, download=False)
            titulo = info['title']
            
            self.progresso.emit(f"Baixando áudio: {titulo}")
            ydl.download([self.url])
            
            self.concluido.emit(True, f"✅ Áudio baixado com sucesso!\n\n{titulo}")


class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")
        self.inicializar_ui()
        
    def inicializar_ui(self):
        self.setWindowTitle("DePoços Downloader")
        self.setGeometry(100, 100, 750, 680)
        
        # Estilo principal
        self.setStyleSheet("""
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
                color: white;
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
            QPushButton#pastaBtn {
                background-color: #764ba2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#pastaBtn:hover {
                background-color: #5D3A9B;
            }
            QPushButton#pastaBtn:pressed {
                background-color: #4A2D7A;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header com imagem de fundo
        header_frame = QFrame()
        
        # Verifica se existe imagem de fundo
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        logo_path = os.path.join(base_path, 'logo_fundo.png')
        
        if os.path.exists(logo_path):
            # Com imagem de fundo
            header_frame.setStyleSheet(f"""
                QFrame {{
                    background-image: url({logo_path.replace(chr(92), '/')});
                    background-repeat: no-repeat;
                    background-position: center;
                    background-color: rgba(118, 75, 162, 0.9);
                    border-radius: 15px;
                    padding: 20px;
                }}
            """)
        else:
            # Sem imagem de fundo (fallback)
            header_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(118, 75, 162, 0.9);
                    border-radius: 15px;
                    padding: 20px;
                }
            """)
        
        header_layout = QVBoxLayout(header_frame)
        
        # Logo emoji
        logo = QLabel("🎬")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("font-size: 50px; background: transparent;")
        header_layout.addWidget(logo)
        
        # Título
        titulo = QLabel("DePoços Downloader")
        titulo_font = QFont()
        titulo_font.setPointSize(24)
        titulo_font.setBold(True)
        titulo.setFont(titulo_font)
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("color: white; background: transparent; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);")
        header_layout.addWidget(titulo)
        
        # Subtítulo
        subtitulo = QLabel("Baixe vídeos e músicas do YouTube com qualidade")
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setStyleSheet("color: rgba(255, 255, 255, 0.95); font-size: 13px; background: transparent;")
        header_layout.addWidget(subtitulo)
        
        layout.addWidget(header_frame)
        
        # URL Input
        url_group = QGroupBox("🔗 URL do Vídeo")
        url_layout = QVBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Cole a URL do YouTube aqui...")
        self.url_input.setMinimumHeight(40)
        url_layout.addWidget(self.url_input)
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)
        
        # Tipo e Qualidade
        tipo_qualidade_layout = QHBoxLayout()
        
        tipo_group = QGroupBox("🎯 Tipo de Download")
        tipo_layout = QVBoxLayout()
        self.radio_video = QRadioButton("📹 Vídeo")
        self.radio_audio = QRadioButton("🎵 Áudio (MP3)")
        self.radio_video.setChecked(True)
        self.radio_video.toggled.connect(self.atualizar_qualidade_options)
        tipo_layout.addWidget(self.radio_video)
        tipo_layout.addWidget(self.radio_audio)
        tipo_group.setLayout(tipo_layout)
        tipo_qualidade_layout.addWidget(tipo_group)
        
        qualidade_group = QGroupBox("⚙️ Qualidade")
        qualidade_layout = QVBoxLayout()
        self.qualidade_combo = QComboBox()
        self.qualidade_combo.addItems([
            "Melhor disponível",
            "4K (2160p)",
            "2K (1440p)",
            "Full HD (1080p)",
            "HD (720p)",
            "SD (480p)",
            "Baixa (360p)"
        ])
        self.qualidade_combo.setCurrentIndex(3)
        self.qualidade_combo.setMinimumHeight(40)
        qualidade_layout.addWidget(self.qualidade_combo)
        qualidade_group.setLayout(qualidade_layout)
        tipo_qualidade_layout.addWidget(qualidade_group)
        
        layout.addLayout(tipo_qualidade_layout)
        
        # Pasta de destino
        pasta_group = QGroupBox("📁 Pasta de Destino")
        pasta_layout = QHBoxLayout()
        self.pasta_label = QLabel(self.pasta_destino)
        self.pasta_label.setStyleSheet("""
            padding: 10px; 
            background-color: #f5f5f5; 
            border-radius: 8px;
            color: #555;
            font-size: 12px;
        """)
        self.pasta_label.setWordWrap(True)
        pasta_btn = QPushButton("Escolher Pasta")
        pasta_btn.setObjectName("pastaBtn")
        pasta_btn.clicked.connect(self.escolher_pasta)
        pasta_btn.setMinimumHeight(40)
        pasta_layout.addWidget(self.pasta_label, 1)
        pasta_layout.addWidget(pasta_btn)
        pasta_group.setLayout(pasta_layout)
        layout.addWidget(pasta_group)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Log de status
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setPlaceholderText("Status do download aparecerá aqui...")
        layout.addWidget(self.log_text)
        
        # Botão de download
        self.download_btn = QPushButton("⬇️  BAIXAR AGORA")
        self.download_btn.setMinimumHeight(50)
        self.download_btn.setStyleSheet("""
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
        """)
        self.download_btn.clicked.connect(self.iniciar_download)
        layout.addWidget(self.download_btn)
        
        # Rodapé
        rodape_frame = QFrame()
        rodape_frame.setStyleSheet("background: transparent;")
        rodape_layout = QVBoxLayout(rodape_frame)
        rodape_layout.setSpacing(5)
        
        rodape1 = QLabel("Feito com ❤️ por GabrielDePoços")
        rodape1.setAlignment(Qt.AlignCenter)
        rodape1.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        
        rodape2 = QLabel("Requer FFmpeg instalado | v1.0")
        rodape2.setAlignment(Qt.AlignCenter)
        rodape2.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 10px;")
        
        rodape_layout.addWidget(rodape1)
        rodape_layout.addWidget(rodape2)
        layout.addWidget(rodape_frame)
        
    def atualizar_qualidade_options(self):
        if self.radio_audio.isChecked():
            self.qualidade_combo.setEnabled(False)
        else:
            self.qualidade_combo.setEnabled(True)
    
    def escolher_pasta(self):
        pasta = QFileDialog.getExistingDirectory(self, "Escolher Pasta", self.pasta_destino)
        if pasta:
            self.pasta_destino = pasta
            self.pasta_label.setText(pasta)
    
    def adicionar_log(self, mensagem):
        self.log_text.append(mensagem)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def iniciar_download(self):
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "⚠️ Aviso", "Por favor, insira uma URL válida!")
            return
        
        if "youtube.com" not in url and "youtu.be" not in url:
            QMessageBox.warning(self, "⚠️ Aviso", "Por favor, insira uma URL válida do YouTube!")
            return
        
        self.download_btn.setEnabled(False)
        self.download_btn.setText("⏳ Baixando...")
        self.progress_bar.setValue(0)
        self.log_text.clear()
        
        qualidade = self.qualidade_combo.currentText()
        tipo = "audio" if self.radio_audio.isChecked() else "video"
        
        self.thread = DownloadThread(url, qualidade, tipo, self.pasta_destino)
        self.thread.progresso.connect(self.adicionar_log)
        self.thread.concluido.connect(self.download_concluido)
        self.thread.progresso_percentual.connect(self.progress_bar.setValue)
        self.thread.start()
    
    def download_concluido(self, sucesso, mensagem):
        self.download_btn.setEnabled(True)
        self.download_btn.setText("⬇️  BAIXAR AGORA")
        self.progress_bar.setValue(100 if sucesso else 0)
        
        if sucesso:
            QMessageBox.information(self, "✅ Sucesso", mensagem)
            self.adicionar_log("\n" + mensagem)
        else:
            QMessageBox.critical(self, "❌ Erro", mensagem)
            self.adicionar_log("\n❌ " + mensagem)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    janela = YouTubeDownloader()
    janela.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()