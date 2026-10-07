---
name: amazon-relatorios-analisar
description: "Baixa os relatórios mensais (CSV) do Associados Amazon da própria conta pelo Claude in Chrome, guarda cada mês na máquina da pessoa, consolida tudo num arquivo único nosso (meses, produtos, IDs, categorias, tipos de produto) e analisa o que vende, o que caiu e desde quando. Use quando pedirem para baixar, atualizar, consolidar ou analisar os relatórios ou CSVs da Amazon, ou na rodada mensal (vazio, `baixar AAAA-MM...`, `consolidar` ou `analisar`). Baixa só com o sim da pessoa; ganho nunca vai para o repositório nem para recado."
---

## Parse de input

- vazio: rodada completa (Fases 0 a 4).
- `baixar AAAA-MM [AAAA-MM...]`: só esses meses (Fases 1 a 4).
- `consolidar` ou `analisar`: sem Chrome, com o que já está guardado (Fase 3 e/ou 4).

# Relatórios da Amazon: baixar, consolidar e analisar

O painel do Associados esconde o que tem pouco tráfego e só deixa baixar os relatórios de comissões **um mês por vez**. Esta skill guarda cada mês como veio, monta o nosso arquivo único consolidado e lê o conjunto. O programa é `scripts/amazon-relatorios.ts`; os dados ficam em `~/Backups/afiliados/amazon-relatorios/{StoreID}/` (ou `$AMAZON_RELATORIOS_DIR`), fora do repositório:

- `brutos/AAAA-MM/`: `linked-product.csv`, `tracking-id.csv`, `category.csv`, `top-sellers.csv`, os `.zip` originais e `info.json` (quando foi pedido e baixado).
- `consolidado/amazon-consolidado.csv`: o arquivo único, no padrão das planilhas em português (ponto e vírgula entre colunas, vírgula nas casas decimais). A coluna `nivel` diz o que é cada linha: `mês`, `tipo de produto`, `categoria`, `ID`, `produto` (mês × produto), `produto (período todo)` (pico, quanto tem hoje do pico, ganho total) e `mais vendido`. Célula vazia = não vale para o nível ou foi escondida pela Amazon (a coluna `ganho_escondido` diz qual). Na linha de mês, `situacao_do_mes` e `dias` dizem se o mês está inteiro: o mais antigo pode começar no meio (a Amazon já tinha apagado o começo), e o baixado até o dia 10 do mês seguinte ainda muda. A análise só usa mês inteiro nas médias. Gerado de novo a cada `consolidar`; não editar à mão. A pasta da conta tem um `LEIA-ME.md` com cada coluna.
- `analises/AAAA-MM-DD.md`: a análise de cada rodada.

Caso-origem (07/10/2026): o Marcelo baixou 21 meses (jan/2025 a set/2026) e pediu "o nosso próprio csv, com tudo organizado e consolidado", para baixar de tempo em tempo e a Bárbara rodar na conta dela.

## Invariantes

- **Cada pessoa roda na própria conta**, a que está logada no Chrome dela. O StoreID aparece no topo do Associados ("StoreID: ..."); use-o em `--loja=`. Os sites de uma pessoa não aparecem na conta da outra.
- **Ganho fica na máquina da pessoa.** Nunca no repositório, em recado, em commit ou em skill. O relatório vai no chat.
- **Avisar antes de usar o Chrome**, numa linha: o quê, o site (`associados.amazon.com.br`) e a conta (a logada). Pedido de login: parar e pedir para a pessoa entrar; nunca digitar senha.
- **Baixar só com o sim**, dizendo antes os meses e os relatórios. Na conta, só leitura e download: nada de configuração, lista de sites, IDs, pagamento ou termos.
- **Análise é sinal, não regra** (Marcelo, 07/10/2026). Separar o fato (número) da hipótese ("pode ser", "combina com").

## Fase 0 — o que falta

`bun scripts/amazon-relatorios.ts faltando --loja={StoreID}` lista, da data mínima até o último mês que já acabou, os meses sem arquivo e os baixados até o dia 10 do mês seguinte (envios e devoluções ainda mudam o número: baixar de novo). **A Amazon só guarda os últimos 2 anos**, na tela e no download (em 07/10/2026 a data mínima era 07/10/2024), e o dia mais antigo some a cada dia que passa. Por isso o que baixamos é o único histórico que fica. Na primeira vez da conta, baixe tudo desde a data mínima, começando pelo mês mais antigo: o período personalizado desse mês começa na data mínima, não no dia 1. `faltando` mostra a data mínima e começa nesse mês, também numa conta que já tem meses guardados (`--desde=AAAA-MM` começa depois). Mostre a lista e peça o sim.

## Fase 1 — baixar (Claude in Chrome)

Carregue a skill `chrome-browser` e as ferramentas do Chrome numa chamada só (`browser_batch`, `find`, `javascript_tool`, `form_input`, `get_page_text`, `computer`). Abra `https://associados.amazon.com.br/p/reporting/earnings` numa aba nova e confira o StoreID no topo.

1. Clique em **"Fazer download de relatórios"** (clique de verdade; por `ref` às vezes não abre). No formulário: marque as quatro caixas de **Comissões** (Produto relacionado, Categoria, ID de rastreamento, Mais vendidos), deixe Recompensas desmarcado e escolha **CSV**. Conferir por JavaScript ajuda: as caixas são `creativeasinWithPrivacy`, `categoryWithPrivacy`, `trackingidWithPrivacy` e `topsellersWithPrivacy`.
2. **Um mês por pedido.** Ano e trimestre voltam `DURATION_EXCEEDED`. Para cada mês: abra o seletor de período do formulário, marque `input[name=ac-daterange-radio-report-download-timeInterval][value=custom]` e preencha por JavaScript `ac-daterange-cal-input-from-report-download-timeInterval` e `...-to-...` com MM/DD/AAAA, disparando `input` e `change`. Depois clique no "Aplicar" visível do seletor. Confira o texto "Período: ..." do formulário.
3. Espere 2 segundos e clique **uma vez** em "Gerar Relatórios". Clique em "Atualizar" e confira se apareceu uma linha nova com a hora de agora. Às vezes o primeiro clique só fecha o seletor; aí clique de novo. Pedido repetido volta `THROTTLED`, e é **um pedido por vez**.
4. Espere a situação virar "Fazer download" (de 1 a 6 minutos; o mês corrente pode passar de 10). Clique em cada "Fazer download" com **clique de verdade**: o clique por JavaScript não baixa. Para achar a posição, use `getBoundingClientRect()` do link na linha certa (nome do relatório e hora do pedido) e converta para o quadro do screenshot (largura do screenshot ÷ `innerWidth`).
5. Cada relatório chega como `.zip` na pasta Downloads. Depois de cada mês, rode `bun scripts/amazon-relatorios.ts guardar --loja={StoreID}`: ele leva os zips para o mês certo (o mês sai da data de dentro do arquivo) e recusa mistura de meses.

Armadilhas vistas: o link às vezes abre uma aba "Opa! Desculpe..." em vez de baixar (feche e siga; esse arquivo fica faltando); "Mais vendidos" vem vazio ("Informações não encontradas") quando há pouco tráfego; a página volta para "Hoje" quando a janela do Chrome muda de tamanho; a resposta do `javascript_tool` é cortada perto de 1.000 caracteres; a extensão às vezes desconecta (espere e confira o estado da lista antes de pedir de novo). No fim, feche a aba criada.

## Fase 2 — guardar

`guardar` roda a cada mês baixado (Fase 1, passo 5). Para trazer zips de outra pasta: `bun scripts/amazon-relatorios.ts importar <pasta> --loja={StoreID}`. Mês baixado de novo substitui o anterior; o zip antigo fica em `brutos/AAAA-MM/zips/`.

## Fase 3 — consolidar

`bun scripts/amazon-relatorios.ts consolidar --loja={StoreID}`. Ele liga cada produto aos sites pelos artigos e páginas de produto do repositório e, quando existe, pelas cópias dos WordPress em `~/Backups/afiliados/wp-export`. O tipo do produto vem da subcategoria da bíblia e, sem bíblia, do nome, pela regra que casa mais cedo no texto (o nome do produto vem no começo do título: "Microfone de lapela para celular" é microfone). Confira a saída: meses, produtos, e a parte dos cliques com tipo conhecido e ligada a algum site. Se o tipo `outros` passar de uns 5% dos cliques, veja os maiores no nível `produto (período todo)` e acrescente a regra em `REGRAS_TIPO` do programa (07/10/2026: os Galaxy Book estavam em `outros` e as roçadeiras em `cadeira`, porque "rocadeira" tem "cadeira" dentro).

## Fase 4 — analisar e relatar

`bun scripts/amazon-relatorios.ts analisar --loja={StoreID} [--meses=3]` grava `analises/AAAA-MM-DD.md` com: mês a mês, com a situação de cada mês; últimos meses contra os mesmos do ano anterior; tipos de produto (começo × agora); desde quando cada tipo ficou abaixo da metade sem voltar; o que vende agora; os que mais ganharam e quanto do pico têm hoje; produtos com muitos cliques e nenhuma venda visível (conferir preço e disponibilidade); IDs. Se houver análise anterior em `analises/`, compare e diga o que mudou desde ela.

O relatório no chat, em linguagem simples: o que aconteceu (3 ou 4 frases), os principais sinais com números e o que os dados não separam. Cuidados ao ler:

- **O escondido cresce quando o tráfego cai.** A linha "Other" e o "-" juntam o que vende pouco; com tráfego baixo, quase todo o ganho fica escondido. Os cliques por produto vêm completos.
- **O ID muda quando o site muda** (port, troca de domínio, site refeito). Um ID que vai a zero pode ser só troca. Confira `git log --all -S'{id}' -- 'sites/*/src/config.ts'` e `docs/painel/_data/grupos-legado.json`.
- **Produto em vários sites:** a ligação produto → site é aproximada. Tipo de produto e produto são leituras firmes; site, não.
- **O ganho entra no dia do envio**; o último mês ainda muda por uns 10 dias.
- Três de cada quatro compras costumam ser de outro produto que não o do link: o que conta é a pessoa chegar à Amazon.

## Quando rodar

Uma vez por mês, depois do dia 10: baixa o mês anterior e o que `faltando` apontar. A cada rodada a análise fica melhor; se uma leitura nova se mostrar útil, acrescente no `analisar` do programa (e nesta skill) em vez de refazer à mão.
