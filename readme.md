# DePoços Downloader

Aplicativo desktop em Python/PyQt5 para baixar vídeos individuais e converter áudio para MP3. Interface inspirada no Poços Hub, mantendo o projeto original.

## Executar

Windows 10/11, Python 3.10 ou superior. Na pasta do projeto:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python DePocosDownloader.py
```

FFmpeg e FFprobe são necessários e já estão neste repositório. São procurados ao lado do código/executável e no PATH. Para o YouTube, instale Node.js 22+ ou Deno conforme a [documentação do yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/EJS). O aplicativo detecta e habilita esses runtimes automaticamente. O pacote `yt-dlp[default]` inclui o solver EJS.

## Usar

1. Cole o link completo de um vídeo. “Ver detalhes” consulta título, autor e duração sem baixar.
2. Escolha vídeo e resolução máxima, ou áudio MP3 de 192 kbps.
3. Escolha a pasta e clique em “Baixar arquivo”.
4. Use “Abrir pasta” ao terminar. A pasta de um download concluído fica salva nas preferências.

Vídeo usa a melhor opção até a resolução escolhida, com preferência por H.264/AAC. Arquivos separados são unidos em MKV para aceitar os codecs disponíveis; arquivos já combinados mantêm o contêiner original. A qualidade selecionada é um limite, não uma promessa de disponibilidade. Os nomes incluem o ID para evitar colisão entre títulos iguais. Não há suporte a playlists.

Cancelar é cooperativo: aguarda a próxima resposta de rede ou o fim de um subprocesso do FFmpeg. Fechar a janela solicita cancelamento e só fecha depois que a thread termina. Arquivos parciais podem permanecer para retomada.

## Atualizar o motor

```powershell
.venv\Scripts\python -m pip install --upgrade "yt-dlp[default]"
```

Ou execute `atualizar.bat`. Para uma cópia compilada, gere um novo pacote depois da atualização. Não há atualização automática do executável. Erros de login, região, remoção ou bloqueio da plataforma ainda podem ocorrer; veja “Mostrar diagnóstico”. O aplicativo não importa cookies do navegador.

## Gerar executável

Execute `build.bat` após criar o ambiente e instalar as dependências. O script instala o PyInstaller nesse ambiente e gera `dist/DePocosDownloader/DePocosDownloader.exe`. Distribua a pasta inteira. FFmpeg, FFprobe e o solver EJS são incluídos. Node/Deno deve estar instalado na máquina de destino.

## Testes

```powershell
.venv\Scripts\python -m pip install pytest
.venv\Scripts\python -m pytest tests -q
```

Testes de validação, resolução, dependências, progresso, cancelamento e falha de download não dependem da rede. Testes reais dependem da disponibilidade das plataformas.

## Estrutura

- `DePocosDownloader.py`: interface, preferências e ciclo de vida das threads.
- `downloader.py`: opções do yt-dlp, detecção de dependências e worker.
- `DESIGN.md`: identidade visual e decisões.
- `tests/`: testes de regressão.

Use com conteúdo que você tem autorização para baixar. Autoria original: GabrielDePoços. Esta atualização não altera a licença dos componentes de terceiros; verifique os termos de distribuição de FFmpeg, Qt e yt-dlp ao redistribuir binários.
