# Interface do DePoços Downloader

Janela escura e compacta de 464 px, com cantos de 20 px, cabeçalho arrastável e
abertura no canto superior direito da área de trabalho. O formato segue a janela
do Poços Hub. O campo de link, a escolha de formato e o botão de download ficam
visíveis na janela inicial.

Em **Opções**, a qualidade máxima aparece para vídeo. A pasta de destino fica
disponível para os dois formatos. O painel de atividade aparece quando há
consulta, download ou erro. O diagnóstico fica recolhido até ser solicitado.

## Movimento

O pacote instalado do Volum 0.10.0.0 declara entrada de 300 ms com
`cubic-bezier(.16, 1, .3, 1)`, saída de 120 ms e entrada com deslocamento e
opacidade em `wwwroot/style.css`. O código distribuído em `wwwroot/app.js`
aplica as classes de animação ao painel. A inspeção estática do pacote no REA
está registrada em
`ev_66f5c84147edb12fd1a52b96f29d9921bdf12483c052910e40c10d5267e3302c`.

O Downloader aplica a curva a uma entrada de 10 px com opacidade e à expansão
dos painéis. O recolhimento e o fechamento pelo botão da janela duram 120 ms.
Ao inverter um painel em movimento, a próxima transição parte da altura atual.
As transições respeitam a configuração de animações do Windows.

O seletor de formato usa um indicador deslizante. O indicador e o retorno dos
botões ao soltar usam uma mola amortecida com rigidez 260 e amortecimento 22,
valores do exemplo de interação fornecido. O efeito é desenhado dentro dos
controles, mantendo fixas as áreas clicáveis e a disposição da janela.

O seletor de qualidade usa abertura gradual e rotação da seta, inspiradas
no [Inline Disclosure Menu](https://ui.watermelon.sh/animated-components/inline-disclosure-menu).
A lista marca a resolução aplicada e mantém a navegação de teclado do Qt.
