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
2. Escolha “Vídeo” ou “Áudio MP3”. Em “Opções”, você pode trocar a pasta e ajustar a qualidade máxima do vídeo.
3. Clique em “Baixar vídeo” ou “Baixar MP3”. Enter no campo do link também inicia o download.
4. Use “Abrir pasta” ao terminar. A pasta de um download concluído fica salva nas preferências.

No Windows, use **Ctrl+Alt+K** para abrir a janela enquanto o aplicativo está
na bandeja. O botão × recolhe a janela e deixa os downloads em andamento.
Clique com o botão direito no ícone da bandeja para escolher **Iniciar com o
Windows** ou **Sair**. A inicialização automática abre somente o ícone.

Aceita links diretos de mídia e páginas de vídeo ou áudio em plataformas como
YouTube, Vimeo, Dailymotion, TikTok, Instagram, Reddit e SoundCloud, conforme
o [suporte do yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).
Para fontes apenas de áudio, escolha **Áudio MP3**. Os links são processados
localmente pelo aplicativo.

Vídeo dá prioridade às opções que informam uma resolução dentro do limite escolhido, com preferência por H.264/AAC. Quando a fonte não informa resolução, o arquivo pode ser salvo na qualidade original. Arquivos separados são unidos em MKV para aceitar os codecs disponíveis. Os nomes incluem o ID para evitar colisão entre títulos iguais. Use links de itens individuais.

Cancelar é cooperativo: aguarda a próxima resposta de rede ou o fim de um subprocesso do FFmpeg. Fechar a janela solicita cancelamento e só fecha depois que a thread termina. Arquivos parciais podem permanecer para retomada.

## Atualizar o motor

```powershell
.venv\Scripts\python -m pip install --upgrade "yt-dlp[default,curl-cffi]"
```

Ou execute `atualizar.bat`. Para uma cópia compilada, gere um novo pacote depois da atualização. Não há atualização automática do executável. Erros de login, região, remoção ou bloqueio da plataforma ainda podem ocorrer. Consulte “Diagnóstico” no painel de atividade. O aplicativo não importa cookies do navegador.

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
