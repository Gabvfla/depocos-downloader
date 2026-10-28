# DESIGN.md: DePoços Downloader

## 1. Product truth
Ferramenta desktop para salvar vídeos individuais e áudio. Público: usuário Windows, português brasileiro. Manter Python/PyQt5, nome, ícone e funções de qualidade/pasta. Sucesso: download finalizado sem bloquear a interface, com resultado compreensível.

## 2. Design Read
Superfície operate, linguagem compacta de utilitário desktop. Dials V3 M1 D7. Referência fornecida pelo usuário: MainWindow.xaml do Poços Hub.

## 3. Direção visual
Fundo escuro e roxo da referência, alinhamento à esquerda, hierarquia por tipografia e espaçamento. Roxo é identidade explícita do Poços Hub, não um gradiente decorativo. Sem hero, emojis decorativos ou métricas inventadas.

## 4. Tokens
```design-tokens
fonts: Segoe UI
colors: #170F28, #F7F3FF, #AEA0C9, #211337, #604081, #AD7DFF, #7547DD, #322044, #46305F, #FFFFFF, #8E64F3
radii: 0, 4px, 6px, 12px
```
Fundo #170F28, superfícies #211337, texto #F7F3FF, texto secundário #AEA0C9. #7547DD marca a ação principal. #AD7DFF identifica a marca, progresso e foco. Demais roxos: contornos e estados.

## 5. Tipografia
Fonte Segoe UI nativa do Windows. Texto 14px, título de mídia 18px e marca 28px. Pesos regular, semibold e bold para hierarquia sem imagens decorativas.

## 6. Espaçamento e layout
Escala 4/8/12/16/24/32. Janela inicial 780x720; mínimo 520x580. Conteúdo rolável para diagnóstico e escalas maiores do Windows. Duas colunas apenas para formato/qualidade.

## 7. Componentes
Controles com raio 6px; preview com 12px; progresso com 4px. Um botão primário, ações secundárias com contorno. Textos externos sempre em modo plain text.

## 8. Motion
Sem animações decorativas. Progresso indeterminado apenas durante consultas e conversão reais.

## 9. Conteúdo
Título, autor e duração vêm do extrator. Não criar miniaturas falsas. Mensagens em português e diagnóstico técnico sob demanda.

## 10. Do / Don't
Preservar foco visível e navegação por teclado. Não bloquear a interface com chamadas de rede. Não declarar sucesso antes da finalização do FFmpeg.

## 11. Decision log
2026-10-27: adotar paleta do Poços Hub fornecido pelo usuário. Manter janela nativa redimensionável para acessibilidade. Separar worker da UI. MKV permite unir codecs sem prometer MP4 para todo conteúdo; explicar o contêiner na tela.

## 12. Referências
Poços Hub local (MainWindow.xaml). Skill antiwebslop, aplicada aos princípios visuais compatíveis com PyQt5; validação por renderização Qt, pois não é uma página web.
