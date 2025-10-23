# 🎬 DePoços Downloader

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

> **Baixe vídeos e músicas do YouTube com qualidade e facilidade!**

Um downloader moderno e elegante para YouTube com interface gráfica intuitiva, desenvolvido em Python com PyQt5.

---

## ✨ Recursos

- 🎥 **Download de Vídeos** - Suporte para múltiplas resoluções (360p até 4K)
- 🎵 **Download de Áudio** - Conversão automática para MP3 (192 kbps)
- 🎨 **Interface Moderna** - Design bonito com gradientes roxo e amarelo
- ⚡ **Rápido e Eficiente** - Utiliza yt-dlp e FFmpeg para melhor performance
- 📊 **Barra de Progresso** - Acompanhe o download em tempo real
- 📁 **Escolha a Pasta** - Salve onde preferir
- 🔄 **Atualizado** - Contorna bloqueios do YouTube (erro 403)

---

## 📋 Pré-requisitos

### Para usar o executável (.exe)

- ✅ Windows 7 ou superior
- ✅ **Nada mais!** (FFmpeg já incluído)

### Para rodar o código Python

- Python 3.8 ou superior
- FFmpeg instalado no sistema

---

## 🚀 Instalação

### Opção 1: Usar o Executável (Recomendado)

1. Baixe o arquivo `DePoçosDownloader.exe` da seção [Releases](https://github.com/gabvfla/depocos-downloader/releases)
2. Execute o arquivo
3. Pronto! 🎉

### Opção 2: Executar o Código Python

1. **Clone o repositório:**

```bash
git clone https://github.com/gabvfla/depocos-downloader.git
cd depocos-downloader
```

2. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

3. **Instale o FFmpeg:**

**Windows (Chocolatey):**

```bash
choco install ffmpeg
```

**Windows (Manual):**

- Baixe: https://www.gyan.dev/ffmpeg/builds/
- Extraia para `C:\ffmpeg`
- Adicione `C:\ffmpeg\bin` ao PATH

**Linux:**

```bash
sudo apt install ffmpeg
```

**Mac:**

```bash
brew install ffmpeg
```

4. **Execute o programa:**

```bash
python youtube_downloader_gui.py
```

---

## 📖 Como Usar

1. **Cole a URL** do vídeo do YouTube
2. **Escolha o tipo:** Vídeo ou Áudio (MP3)
3. **Selecione a qualidade** desejada
4. **Escolha a pasta** de destino (opcional)
5. **Clique em "BAIXAR AGORA"**
6. **Aguarde** o download concluir! ✅

---

## 🛠️ Como Compilar o Executável

Se quiser gerar seu próprio executável:

```bash
# Instale o PyInstaller
pip install pyinstaller

# Compile o programa
pyinstaller --onefile --windowed --noconsole ^
--add-binary "ffmpeg.exe;." ^
--add-binary "ffprobe.exe;." ^
--add-data "logo_fundo.png;." ^
--icon "icone.ico" ^
--name "DePoçosDownloader" ^
--clean ^
youtube_downloader_gui.py
```

O executável estará em: `dist/DePoçosDownloader.exe`

---

## 🐛 Solução de Problemas

### Erro 403: Forbidden

Se aparecer erro 403, atualize o yt-dlp:

```bash
pip install --upgrade yt-dlp
```

### FFmpeg não encontrado

**Se estiver usando o executável:** O FFmpeg já está incluído!

**Se estiver rodando o código Python:**

1. Verifique se o FFmpeg está instalado:

```bash
ffmpeg -version
```

2. Se não estiver, instale seguindo as instruções acima
3. Reinicie o terminal após a instalação

### Programa não abre ou fecha imediatamente

Execute `fix_ytdlp.bat` para atualizar o yt-dlp automaticamente.

### Antivírus bloqueando

Alguns antivírus podem bloquear executáveis PyInstaller. Adicione uma exceção para o arquivo.

---

## 📁 Estrutura do Projeto

```
depocos-downloader/
│
├── youtube_downloader_gui.py    # Código principal
├── fix_ytdlp.bat                # Script de atualização do yt-dlp
├── requirements.txt             # Dependências Python
├── README.md                    # Este arquivo
├── LICENSE                      # Licença MIT
├── icone.ico                    # Ícone do programa
├── logo_fundo.png               # Imagem de fundo (opcional)
├── ffmpeg.exe                   # FFmpeg (para compilação)
└── ffprobe.exe                  # FFprobe (para compilação)
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer um Fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abrir um Pull Request

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## ⚠️ Aviso Legal

Este software é fornecido apenas para fins educacionais. O download de conteúdo protegido por direitos autorais sem permissão pode violar as leis de direitos autorais em seu país. Use por sua própria conta e risco.

---

## 👨‍💻 Autor

**Feito com ❤️ por GabrielDePoços**

- GitHub: [@GabrielDePoços](https://github.com/Gabvfla)
- Email: gabrielmvcontato@gmail.com

---

## 🌟 Apoie o Projeto

Se este projeto foi útil para você, considere dar uma ⭐ no GitHub!

---

## 📚 Tecnologias Utilizadas

- [Python 3](https://www.python.org/)
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/)
- [PyInstaller](https://www.pyinstaller.org/)

---

## 🔄 Histórico de Versões

### v1.0.0 (2025-10-23)

- ✨ Lançamento inicial
- 🎨 Interface gráfica moderna
- 🎥 Suporte para download de vídeos
- 🎵 Suporte para download de áudio
- 📊 Barra de progresso em tempo real
- 🔧 Correção do erro 403

---

**Desenvolvido com Python 🐍 e muito ☕**
