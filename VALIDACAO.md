# Validação da atualização

Data: 28/10/2026.

- 16 testes automatizados aprovados (pytest).
- Consulta real e downloads de vídeo e MP3 concluídos em Python; FFprobe confirmou H.264/AAC e MP3.
- Interface renderizada e revisada em 520x680, 780x720 e 1100x800.
- Executável gerado com PyInstaller, aberto e validado com consulta HTTPS e download real do vídeo público de teste jNQXAC9IVRw.
- O pacote inclui a lista de certificados exigida pelo Python usado nesta compilação; a primeira versão do executável falhava sem esse arquivo, e o reteste passou.
- Instagram, TikTok e demais plataformas não foram testadas individualmente.
- Node/Deno é dependência externa do pacote compilado. Node 24 está instalado neste computador.

Alterações locais no clone Git, branch fix/downloader-pocos-hub. Não publicadas no GitHub.
