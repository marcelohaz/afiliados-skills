---
name: artigo-clonar-em-massa
description: Clona um artigo comparativo de um site IRMÃO para outro, reescrevendo TODO o conteúdo do ZERO a partir das bíblias v2 (modo biblia-only) — usa o artigo fonte SÓ como molde estrutural (quantidade de produtos, keyword, badges, ordem, H2/H3 do guide). Pipeline 100% AUTOMATIZADO em etapas, cada uma com gate de auditoria + auto-fix em loop (sem parada humana no meio); o usuário só revisa o resultado final + relatório. Estratégia SERP-monopoly: site novo da rede clona artigo de um existente com texto divergente. Orquestra as skills-peça (review por produto biblia-only via sub-agents Opus paralelos, artigo-intro/guia/meta-escrever) + shuffle determinístico dos produtos do meio (top-3 fixo) + comparador de duplicata vs fonte no fim. NÃO faz deploy. NÃO trava o artigo (contentLocked fica false). Para em "commitado + buildado + preview pronto".
---

## Parse de input

Args canônico: `targetSite SOURCE=sourceSite/sourceSlug [TITLE="..."] [HOME=yes|no] [MODE=biblia-only|hybrid]`

Exemplo real:
```
melhorpretreino SOURCE=melhorpretreino-com/melhor-pre-treino TITLE="Os 11 melhores pré-treinos em 2026 (Atualizado)" HOME=yes MODE=biblia-only
```

- `targetSite` (obrigatório): site destino (ex: `melhorpretreino`).
- `SOURCE=` (obrigatório): `site/slug` do artigo fonte (ex: `melhorpretreino-com/melhor-pre-treino`).
- `TITLE=` (opcional): título do artigo destino. **REGRA DURA: o título SEMPRE segue o padrão-assinatura do SITE-DESTINO, MESMO quando `TITLE=` é passado.** A clone NUNCA grava o `TITLE=` ao pé da letra (causa-raiz da reincidência 2026-06-14: passaram o `TITLE` do FONTE em P1 e a clone gravou idêntico no destino, que é P2). Fluxo obrigatório:
  1. **Inferir o padrão do destino**: ler 2-3 títulos de artigos JÁ EXISTENTES em `sites/{target}/src/content/reviews/*.mdx` → descobrir qual padrão-assinatura é o do site (P1 `{keyword}: as {N} melhores (Atualizado 2026)` · P2 `As {N} {keywordPlural} (Guia 2026)` · P3 `{keyword}: {N} opções para comprar (Guia Completo)` · P4 — mapa na memória `afiliados.seo.titulos-artigo-3-padroes-anti-dup.md`). NÃO chutar: o padrão é o que os irmãos do PRÓPRIO site usam.
  2. **Ler os títulos dos IRMÃOS cross-site** (mesmo slug nos outros sites) pra garantir divergência.
  3. **Gerar/normalizar**:
     - `TITLE` omitido → gera no padrão do destino (lead = campo `keyword`, sem forçar "Melhor", número N obrigatório, ≤60 chars, tag-assinatura do site).
     - `TITLE` passado → trata como **HINT, não literal**. Só usa se JÁ estiver no padrão do destino E divergir de todos os irmãos. Se for o título da FONTE/de um irmão ou estiver em outro padrão, **DESCARTA e regera** no padrão do destino, avisando no relatório.
  4. **HARD GATE** (rodado na **Etapa 0 passo 8**, ao decidir o título, ANTES do assembler; re-conferido na Etapa 6 antes do build): o título final (a) bate o regex do padrão-assinatura do destino E (b) é diferente do de TODOS os irmãos (normalizar caixa/acentos + comparar). Falhou qualquer um → regera. Causa-raiz dos 21 títulos idênticos (auditoria 2026-06-13) + reincidência via `TITLE` explícito (2026-06-14): a clone não validava o título contra o padrão do destino.
- `HOME=` (opcional, default `no`): se `yes`, configura o artigo como home do site (homeReviewSlug).
- `FILA=yes` (opcional): a `artigo-clonar-fila` passa isso quando invoca esta skill por item. Efeito único: **NÃO armar heartbeat próprio** (o da fila já cobre; há um só despertar pendente por sessão e o seu substituiria o dela). Ver "## Turno vivo".
- `RETOMAR=yes` (opcional): esta invocação nasceu de um despertar do heartbeat. Efeito: pular o `clone-log init` (o log existe), ler o clone-log e retomar da primeira etapa não marcada. Ver "## Turno vivo".
- `MODE=` (opcional, default `biblia-only`): `biblia-only` (texto 100% da bíblia, zero leakage do fonte) ou `hybrid` (top-3 da bíblia, 4+ pode considerar o fonte). **Default e recomendado: biblia-only.**

Slug do artigo destino = mesmo slug do fonte (ex: `melhor-pre-treino`), salvo override futuro.

## O que esta skill É (e não é)

É o **orquestrador full-auto** de clone de artigo. Análogo de `pagina-produto-criar-em-massa`, mas pra artigo inteiro.

- **Reusa** as skills-peça (`artigo-review-criar` régua, `artigo-intro-escrever`, `artigo-guia-escrever`, `artigo-meta-escrever`, `artigo-reviews-auditar`, `artigo-auditar`) — NÃO reimplementa régua editorial (evita drift; paridade com `agent-prompts.json`). **Princípio único (v1.54.0): a clone APONTA pra régua, nunca a RE-ESCREVE.** Guide/intro/meta/audits são INVOCADOS via Skill tool (loop principal, sequencial). Os reviews (Etapa 1.1) são N sub-agents PARALELOS e sub-agent não chama Skill tool → cada um LÊ `artigo-review-criar/SKILL.md` direto. Resumo inline de régua = proibido (era a fonte do drift: subtitle desatualizado, voz-comprador vazada, "Para quem é" repetitivo).
- **Conteúdo 100% do ZERO** a partir das bíblias. O artigo fonte serve SÓ de molde: nº de produtos, lineup, badges, keyword/keywordPlural/listHeading, e a estrutura de H2/H3 do guide. Em `biblia-only` os sub-agents NÃO veem o texto do fonte (sem leakage).
- **NÃO é a IA do painel.** Roda na assinatura (Claude Code), Opus 5 (ou o Opus mais novo). (A op `clone-article` do painel usa API key e está fora do fluxo.)

## Modelo

Opus 5 (ou o Opus mais novo disponível). Sub-agents herdam o modelo da sessão (`settings.json: opus[1m]`) OU são fixados com `model: opus` no Agent tool. NUNCA Sonnet/Haiku (régua do projeto: skills sempre Opus).

## Ambiente (CRÍTICO)

Edição roda onde os arquivos do projeto estão acessíveis. Se a sessão é VPS-only (Mac local EPERM-blocked), TODO I/O de arquivo é via SSH na VPS (`/home/melhorserum-painel/afiliados`), e os sub-agents geram conteúdo retornando dados estruturados; a skill-mãe centraliza a escrita via SSH (ownership `melhorserum-painel`, 1 commit). Caso contrário, opera direto no repo local. Detecte no início.

## Invariantes

- **⚠️ GATES DE AUDITORIA OBRIGATÓRIOS — NUNCA PULAR**: Etapa 1.4 (`artigo-reviews-auditar`, cross-produto) E Etapa 4 (`artigo-auditar`) são TRAVAS DURAS. O pipeline NÃO pode reportar "pronto/concluído" sem ter RODADO as duas e obtido `readyToLock: SIM`. Pular = execução INVÁLIDA. **Caso real (1º run, melhorpretreino 2026-05-29): os audits foram pulados e o artigo carregava 8 erros factuais críticos** (4 claims de cafeína falsos: "único sem cafeína"/"no topo"/"no teto"/"sem pico" com 400mg; + 3 brand-swaps no guide: Dux descrito com specs do True Source, 3VS como "contém glúten"). **Build + gates mecânicos NÃO pegam isso — só os audits editoriais.** Os audits são o que separa "lê bonito" de "está correto".
- **NÃO faz deploy.** Para em "commitado + buildado + preview pronto". Deploy exige aprovação humana explícita (régua do projeto).
- **NÃO trava** (`contentLocked` fica false/ausente) — editável após revisão.
- **Full-auto, sem checkpoint humano no meio.** Cada etapa: gera → audita (auto) → auto-fix loop → segue. Humano só vê o final + relatório.
- **O turno não termina antes do relatório final** (canon Marcelo 2026-08-15). "Full-auto" só é verdade enquanto o turno está vivo: sub-agents em primeiro plano, heartbeat armado quando standalone, progresso no clone-log e não no chat. Ver "## Turno vivo" — é a seção que faz as três linhas acima valerem na prática.
- **Auto-fix com limite + não-bloqueia.** Cada gate que falha dispara correção e re-valida (máx 3 tentativas). Se não convergir, NÃO trava o pipeline — registra "⚠ não convergiu, revisar" no relatório final e segue. Nada ruim é escondido.
- **Commit/push do conteúdo: sim** (fluxo de criação). Deploy: não.
- **Português brasileiro editorial**, voz analítica.
- **Idempotência defensiva:** artigo destino já existe e está `contentLocked: true` → ABORTAR (não sobrescrever trabalho travado). Existe **commitado e sem lock** → é run concluído: ABORTAR com "já concluído" (a fila classifica como PULAR). Existe **sem commit** (montagem de um run anterior) → **RETOMAR** pela primeira etapa não marcada no clone-log — nunca perguntar.

## Turno vivo — primeiro plano + heartbeat + chat só no fim (canon Marcelo 2026-08-15)

**Por que existe (medido):** em ~80 clone-runs desde 15/07, 9 pararam no meio e só voltaram quando o Marcelo cutucou ("travou?", "fez os artigos?"). **Em nenhum dos 9 a skill mandava parar.** O turno do agente terminou por um destes motivos, e "seguir pra próxima etapa" só acontece com o turno vivo: (a) esperar sub-agent/skill em background escrevendo "aguardo… te aviso" (23/07 gate 1.4; 02/08 consulta cega do lineup); (b) mensagem de progresso no meio (fim de item, plano, checkpoint: 30/07 três vezes); (c) ramo de exceção que virou pergunta (pré-flight abortou; sub-agent não voltou; ambiguidade no gate 14/08); (d) cota estourada. As três regras abaixo atacam a mecânica, não a "vontade" (dizer "não pare" mais uma vez não segura: já está escrito 3× nesta skill).

**Regra 1 — Primeiro plano, sempre.**
- Sub-agents (Agent tool) rodam com `run_in_background: false`. **Paralelismo = várias chamadas `Agent(...)` no MESMO bloco de ferramentas** (todas bloqueiam até voltar; foi assim que os 10 reviews sempre deveriam rodar). NUNCA `run_in_background: true` para trabalho do pipeline.
- Auditoras e skills-peça via Skill tool executam **inline, no turno**. O gate 1.4 e o 4.1 NUNCA viram sub-agent em background.
- Se um resultado depende de processo externo (script longo, VPS), **bloqueie com espera ativa** dentro do turno — o harness bloqueia `sleep` em primeiro plano, então use `until [ -f {arquivo} ]; do perl -e 'select(undef,undef,undef,5)'; done` em Bash (≤10 min por chamada, repita) — o turno não termina para esperar.
- **Encerrar o turno para esperar é defeito**, não paciência. A frase "te aviso quando voltar" é proibida.

**Regra 2 — Heartbeat próprio quando standalone (`ScheduleWakeup`).** Mesmo com a Regra 1, o turno pode morrer por cota, compactação ou erro. O heartbeat é o que faz a etapa seguinte começar sozinha depois disso.
- **Passo 0 da Etapa 0** (antes do `clone-log init`): `ScheduleWakeup(1800, prompt="/artigo-clonar-em-massa {os MESMOS args desta invocação} RETOMAR=yes")`. 1800s, não 3600: com retomada por etapa o despertar espúrio é barato e o tempo morto máximo cai pela metade.
- **⚠️ SE `FILA=yes`: NÃO arme.** Há **um único** despertar pendente por sessão e cada `ScheduleWakeup` substitui o anterior (medido na fila, 2026-07-30). Se você armar com o comando de 1 artigo, o prompt da fila some e ela não volta. A fila re-arma antes de cada item e cobre este.
- **Ao acordar (`RETOMAR=yes`)**: (1) re-arme o heartbeat como PRIMEIRO ATO; (2) `git log -- sites/{target}/src/content/reviews/{slug}.mdx` + `bun scripts/clone-log.ts verify {target} {slug}`: se commitado e verify OK → `ScheduleWakeup(stop:true)` e relatório curto "já concluído"; (3) senão, leia o clone-log e retome da **primeira etapa não marcada**; reviews persistidos em `docs/biblias-v2/.audits/clone-runs/rev/{target}-{slug}/*.json` (Etapa 2.5) são reusados; se 1.1 está marcada e os arquivos não existem, refaça 1.1; se 1.2 está marcada mas o `.mdx` destino não foi montado, refaça a montagem (não confie no log sem o disco); (4) `clone-log init` NÃO roda de novo (apagaria o progresso).
- **Circuit breaker** (igual à fila): guarde em `<scratchpad>/clone-{target}-{slug}-heartbeat.json` `{etapasMarcadas, streakSemProgresso}`; despertar sem etapa nova = streak++; **streak ≥ 3 (~1h30 parado) → `ScheduleWakeup(stop:true)`** + relatório dizendo em que etapa travou e o erro visto. Não tente para sempre.
- **Stop obrigatório (SÓ quando foi você que armou, ou seja, standalone)**: `ScheduleWakeup(stop:true)` **antes** do Relatório final (Etapa 6 concluída) e no aborto do pré-flight. Sem isso o despertar dispara depois do fim e reagenda à toa. Se o usuário mandar parar/pausar: `stop:true` na hora. **⚠️ Com `FILA=yes` esta skill NÃO chama `ScheduleWakeup` NUNCA — nem para armar, nem para parar.** O despertar pendente é o da fila; um `stop:true` seu aqui mataria a fila em silêncio no próximo fim de turno (é a fila que para o dela na F2).

**Regra 3 — Chat só no fim; ramo de exceção tem fallback, não pergunta.**
- Progresso = `clone-log check` (arquivo). Nenhuma etapa termina com "mensagem de estado" no chat. Uma linha curta por etapa **é permitida só se a mesma mensagem continua com chamadas de ferramenta** — o que encerra o turno não é a linha, é ela ser a última coisa. Antes da Etapa 6 + relatório, **não existe mensagem final**.
- Pré-flight abortou → relatório de aborto (+ `stop:true` só se standalone; com `FILA=yes` a fila trata o item como "⚠ abortado" e segue). É o único fim antecipado legítimo. Sub-agent morreu/deu timeout → refaz **inline** no mesmo turno (nunca "pulei a etapa, quer que eu rode depois?"). Ambiguidade que a régua não resolve → decide pelo lado conservador, registra em skill-notes como `ambiguidade`, segue. Fix determinístico → aplica (canon 24/06). Decisão que a régua já resolveu (título pelo HARD GATE, desempate de peer) → vai no relatório final, não em turno próprio (incidente 12/08).

## Pipeline (full-auto, etapa por etapa)

### Etapa 0 — Pré-flight (auto; aborta cedo se faltar)
0. **Arma o heartbeat** (só se NÃO for `FILA=yes` — com `FILA=yes` esta skill não toca em `ScheduleWakeup`, nem arma nem para; ver "## Turno vivo" Regra 2): `ScheduleWakeup(1800, prompt="/artigo-clonar-em-massa {args} RETOMAR=yes")`. Se `RETOMAR=yes`, re-arme e **pule o `init` abaixo** (leia o clone-log e retome da primeira etapa não marcada).
0b. **Abre o log de execução** (vale nos DOIS modos, individual e fila):
   ```bash
   bun scripts/clone-log.ts init {target} {slug} --source={source-site}/{slug}
   ```
   O `init` é **idempotente** (canon 2026-08-15): se o log já existe com alguma etapa `[x]`, ele NÃO sobrescreve (avisa e mantém — é retomada). Recomeçar do zero de propósito exige `--force`. Antes disso, um `init` em retomada apagava o progresso e a janela do gate de invocação.
   A partir daqui, **feche cada etapa com `check`** assim que ela terminar (não no fim, de memória):
   ```bash
   bun scripts/clone-log.ts check {target} {slug} <etapa> "<o que foi feito, com números>"
   ```
1. Git pull no repo de trabalho (evita estado stale; painel/Bárbara commitam em paralelo).
2. Parse args. Valida `targetSite`/`sourceSite` (`[a-z0-9-]+`).
3. Lê o `.mdx` fonte → extrai: produtos (ASIN, name, image, imageAlt, badge, **rating**, schemaPrice, store), keyword, keywordPlural, listHeading, category, e a estrutura de H2/H3 do `guideContent`. **`rating` é a nota editorial do fonte e DEVE ser preservada — o clone biblia-only NÃO regenera nota, e sem ela o artigo/página perde a fonte de estrela (caso real escritoriocasa 2026-06-11: clones saíram com 0 rating).**
4. Valida bíblias de TODOS os ASINs: existem em `docs/biblias-v2/{ASIN}.json` + `pontosFortes` não-vazio + `angulosConversao` não-vazio. Falta qualquer → ABORTA listando.
4b. **Valida a análise de concorrentes da keyword EXATA** (`docs/painel/_data/competitor-analyses/{slugify(keyword)}.md`). A `artigo-guia-escrever` (Cenário C) **para e pede** ao usuário se ela não existir — e ela só é invocada na Etapa 2, depois de ~10 sub-agents Opus pagos.

    ⚠ **NÃO ABORTE se o artigo FONTE tem guia completo** (canon Marcelo 2026-08-20). Em clone a análise **já foi feita**: o artigo fonte só existe porque alguém colou os concorrentes daquela keyword na criação dele, e o "Como escolher" dele É o resultado disso. Concluir "a análise não foi feita" a partir da ausência do arquivo é **inferência falsa** — o que houve foi o repo perder o arquivo, não o insumo faltar. Duas causas medidas: a `artigo-guia-escrever` não confirmava a gravação (7 keywords do cluster de creatina sumiram assim) e o `competitor-sources/**` ficou fora das EXCEPTIONS do guard até 20/08, revertendo as gravações de quem não pusha pela conta do Marcelo.

    Regra:
    - Análise existe → segue normal.
    - **Não existe MAS o guide do fonte tem os 5 H2 base** → **SEGUE**, passando a estrutura de H2/H3 do fonte como mapa de tópicos pra Etapa 2, e **registra no relatório final**: "sem ficha de concorrentes; usei a estrutura do fonte como mapa". Isso já era o que a Etapa 2 fazia com o fonte de qualquer jeito.
    - Não existe **e** o fonte também não tem guia → aí sim **ABORTA** ("clone de {keyword} precisa da análise de concorrentes: cole 1-3 'Como escolher' da SERP ou rode a guia-escrever antes"); com `FILA=yes` o item vira "⚠ abortado (sem análise)" e a fila segue.

    Travou 3 vezes a Bárbara antes desta régua. O gate continua valendo pro caso que ele foi feito pra pegar: artigo NOVO, onde a análise realmente falta.
5. Valida páginas de produto no destino (`sites/{target}/src/content/products/{slug}.mdx`): se existem, os links hub-and-spoke do guide resolvem.

   **🚨 Se faltar alguma, é BUILD-BREAKER — crie a página ANTES do assembler.** Este passo dizia "AVISA, não bloqueia" e isso estava **errado**: o `name`↔slug é resolvido pelo Astro contra `products/`, então produto sem página quebra o build com `Entry products → {slug} was not found`. Não é o link caindo no fallback Amazon, é o site não compilar. Mordeu duas vezes no mesmo dia (10/08, `jbl-sw8a-ms` em `somprofissional` e depois em `compraguia`) — na primeira o build quebrou, na segunda a página foi criada antes justamente por causa da primeira. Pra cada faltante: (1) crie o STUB com `bun scripts/painel-criar-stubs.ts {target} {ASIN}...` seguido de `bash scripts/git-pull-seguro.sh` (o script é o caminho único desde 2026-09-05: bate no `create-from-bible-batch`, monta o Basic Auth em base64 e traz `.mdx` + `.webp`; NÃO redigite o curl — ver o cabeçalho dele); (2) rode a `pagina-produto-criar` nele; (3) confira que a imagem existe em `public/` do destino (a da fonte NÃO serve, o filename é por-site).
6. Lê `affiliateTag` do destino (`sites/{target}/src/config.ts`). Vazia = links crus; preenchida = `?tag=...`.
7. Confere que o artigo destino NÃO existe travado.
8. **Decide o TÍTULO do destino AGORA (antes do assembler da Etapa 1)** — aplica a regra `TITLE=` do topo: (a) lê 2-3 títulos de `sites/{target}/src/content/reviews/*.mdx` pra inferir o padrão-assinatura do PRÓPRIO site (P1/P2/P3/P4); (b) lê os títulos dos IRMÃOS cross-site (mesmo slug nos outros sites); (c) se `TITLE=` foi passado, só aceita se JÁ estiver no padrão do destino E divergir dos irmãos, senão DESCARTA; (d) gera/normaliza no padrão do destino (lead = campo `keyword`, sem forçar "Melhor", número N, ≤60 chars, tag-assinatura do site); (e) **HARD GATE**: o título escolhido bate o regex do padrão-assinatura do destino E é ≠ do de TODOS os irmãos (normaliza caixa/acentos antes de comparar). Falhou → regera. Guarda esse título pro assembler usar; a Etapa 6 só re-confere (backstop).

### Etapa 1 — Reviews (gerar + auditar + auto-fix)
1. **1.0 Lineup + shuffle**: ordem = top-3 do fonte FIXOS + posições 4+ embaralhadas com shuffle determinístico (seed = hash do target+source+slug; FNV-1a + xorshift32, igual `scripts/faq-shuffle.ts`, a implementação canônica que a 6.3.5 usa). Badge **e `rating`** viajam COM o produto (mapeados por ASIN). Top-3 fixo garante "Melhor Escolha" na posição 1.
   - **GATE DE BADGE — TODO produto leva etiqueta (HARD GATE):** a convenção da rede é que **cada produto do comparativo tem badge** (ex.: melhor-impressora-hp e melhor-impressora-tanque-de-tinta = 7 produtos / 7 badges). Como o badge viaja por ASIN, **buraco no fonte vira buraco no destino** (causa-raiz 2026-06-14: o fonte sublimática tinha badge só nos 2 primeiros → o clone propagou L3250/L1250 SEM etiqueta nos 2 sites). Regra: os 2 primeiros mantêm os de ranking ("Melhor Escolha"/"Boa Alternativa"); **toda posição sem badge recebe um badge DESCRITIVO curto** derivado do ângulo/categoria do produto (ex.: "Multifuncional Adaptável", "Mais Barata", "Laser Monocromática", "Fotográfica", "Frente e Verso Automático", "Boa e Barata"). Badge é **texto livre**: renderiza com a cor padrão (`#1a56db`) via fallback de `getBadgeLabel`/`getBadgeColor`, **sem precisar registrar no `packages/ui/src/utils/amazon.ts`** (registro só pra cor custom, ex.: cinza de "Fora de Linha"). **AUTO-CHECK pós-lineup (OBRIGATÓRIO):** `nº de produtos com badge == nº de produtos`. Se faltar qualquer um, atribuir antes de seguir. Esse mesmo invariante é re-conferido na Etapa 4 (`artigo-auditar` critério `badge-ausente`).
2. **1.1 Geração**: N sub-agents Opus paralelos (levas de até 10), **todos no MESMO bloco de chamadas `Agent(...)`, com `run_in_background: false`** — o turno fica bloqueado até a leva voltar e a 1.2 começa no mesmo turno (Regra 1 do "Turno vivo"). Cada um gera os campos do review-no-artigo (subtitle, shortDescription, pros, cons, specs, fullReview de 4 parágrafos) — **biblia-only** (vê SÓ a bíblia do produto — não lê a página individual nem irmãos; ver canon 2026-08-13 na Etapa 1.3). NUNCA vê o texto do fonte (`biblia-only`).
   - **⚠️ RÉGUA = FONTE ÚNICA, NÃO RESUMO (régua v1.54.0).** O prompt de cada sub-agent **manda LER `.claude/skills/artigo-review-criar/SKILL.md` INTEIRA + `docs/painel/_data/chavoes-por-nicho.json` (bloco do nicho + `_genericos`) e APLICAR a régua dela na geração** — NÃO um resumo destilado inline. Sub-agent do Agent tool não consegue invocar a Skill tool (skills rodam no loop principal, e aqui são N agents PARALELOS), por isso ele LÊ o arquivo canônico em vez de invocar. Isso elimina o DRIFT nos campos cuja régua de CRIAÇÃO vive na review-criar: "Para quem é" (variar abertura + cap "ocupa o papel ≤2", v1.19.0), shortDescription benefício-first (cap ≤250), voz-comprador (lista AMPLA categoria D), jargão dev (SKU/ASIN/datasheet), concordância PT-BR e capitalização, hard caps — passam a vir SEMPRE da skill viva, sem o resumo da clone ficar pra trás quando a `artigo-review-criar` evolui. **Subtitle**: a criação segue a review-criar (subtitle = ângulo, derivado do badge no modo biblia-only — v1.34.0); a normalização **híbrido fluindo / keyword-first cross-produto (crit.22) NÃO é da review-criar, é da Etapa 1.4** (`artigo-reviews-auditar`), que tem visão do conjunto. A clone só acrescenta os **deltas dela** (ver "Prompt do sub-agent de review" abaixo): biblia-only, superlativo-só-posição-1, retornar JSON.
   - Os 4 parágrafos do fullReview usam os rótulos canônicos LITERAIS (`Para quem é:` / `Por que gostamos:` / `Pontos de atenção:` / `Resumo:`), NUNCA parafraseados — o audit (regra `review`) exige os literais (canon Marcelo 2026-06-14).
2.5. **PERSISTIR os reviews em disco ANTES de seguir (obrigatório).** Os 6 campos que os N sub-agents retornaram vivem só no contexto do orquestrador e **evaporam se o turno morrer**. Grave em `docs/biblias-v2/.audits/clone-runs/rev/{target}-{slug}/{ASIN}.json` — **um arquivo por ASIN, no repo (dir gitignored), NÃO no scratchpad** (canon 2026-08-15: o scratchpad é por sessão; a retomada numa sessão nova não achava `rev-*` e refazia os 10 sub-agents) — **antes** do gate 1.2. Cada worker pode gravar o próprio arquivo (nome = ASIN, nunca um arquivo compartilhado) (**nunca** um arquivo compartilhado entre agentes paralelos — ver o aviso no fim do "Prompt do sub-agent"). Se estiver retomando um item interrompido e esse arquivo existir, **reuse-o em vez de re-disparar os sub-agents**. ⚠️ E só marque `clone-log check {t} {slug} 1.1` **depois** que o arquivo estiver gravado — marcar antes faz o log mentir, e a retomada pula pra 1.2 sem ter os dados. Sem esta etapa, uma queda no meio do item joga fora todos os sub-agents Opus já pagos.
3. **1.2 Gate mecânico** (auto): por review — travessão (0), **ponto-e-vírgula `;` (0 na prosa, detecção entity-aware: ignora `&amp;`/`&#..;` e a querystring de href; régua 2026-06-20)**, links Amazon (formato + contagem 2-3, tag-aware), texto-puro (subtitle/shortDescription/specs.value sem HTML), 4 parágrafos com prefixos, tamanhos, **voz-comprador com LISTA AMPLA** (incluir "de forma recorrente", bare "recorrente", "aparece como", "parte das opiniões/observações", "citado/citados de forma"; caso real: "de forma recorrente" escapou de uma lista curta). Falha → auto-fix (sub-agent corrige só o campo) → re-valida (máx 3x).
4. **1.3 REMOVIDA — anti-dup intra-site de prosa NÃO é mais etapa (canon Marcelo 2026-08-13).** A versão antiga media jaccard 0.80 contra 2 frentes (página individual + irmãos intra-site) e passava "ângulos ocupados" no prompt. Foi cortada com base em medição, não em opinião:
   - **O gate nunca disparava no defeito real**: no clone medido, jaccard máx foi 0,62 (teto 0,80) e mesmo assim havia colisões de frase — que quem pegou foi o `verify-output` (frase exata), não o jaccard.
   - **Contrafactual por data de commit** (44 pares, corte 2026-07-30): artigos SEM a maquinaria = 8-grama mediana 0,6%/máx 2,4%; COM = 0,4%/0,7%. A régua comprava ~0,2pp.
   - **Passar a página no prompt não impedia colisão**: caso Brother DCP-T430W (2026-08-13) — o sub-agent leu a página e repetiu "a operação é por botões e luzes" literal dela.
   - **O que segura o overlap baixo é a VARIAÇÃO ESTRUTURAL** (lineup embaralhado, badges distintos, ângulo por posição, guide por gaps), que continua toda em pé — não a obrigação de divergir. Prova inversa: páginas de produto do mesmo ASIN cross-site, que sempre operaram sem divergência forçada, convergem a 6,65% mediana / 22% máx. Artigos ficam em 0,5% porque a montagem varia.
   - **Sobreposição residual com irmãos intra-site é ACEITA por padrão** (mesma régua de `afiliados.regras.pagina-produto-sobreposicao-crosssite-ok`). Spec é spec, número factual repete. NÃO invente ângulo, NÃO contorça texto, NÃO leia a página individual pra "fugir" dela.
   - O que continua protegendo: gate **1.2** (mecânico), audit **1.4** (tone-clone/redundância pega frase concreta repetida entre os reviews DO artigo), e o **`verify-output --source`** na 6.3.6 (frase exata vs fonte). Medição completa em `docs/proposta-afrouxar-antidup.md`.
5. **1.4 Audit cross-produto** (`artigo-reviews-auditar` com `PIPELINE=yes` nos args, **inline via Skill tool, no turno — nunca como sub-agent em background**; foi aqui que o clone de 23/07 parou). `PIPELINE=yes` diz à auditora: aplica óbvio E julgamento (auto-fix, máx 3 rodadas), não espera aprovação, não encerra o turno: tone-clone, redundância, incoerência, claim-vs-lineup, buyer-refs, etc. → AUTO-APLICA as correções propostas → re-audita (máx 3x). Não-convergido → flag no relatório.

### Etapa 2 — Guide (gerar + auditar + auto-fix)
1. **2.1 INVOCAR DE VERDADE** `artigo-guia-escrever` **via Skill tool** (`Skill(skill="afiliados-skills:artigo-guia-escrever", args="{target}/{slug} PIPELINE=yes")` — o `PIPELINE=yes` diz à skill que a análise de concorrentes já foi checada no pré-flight 4b e que ela não pode parar para perguntar), passando a estrutura de H2/H3 do guide do fonte como **mapa de tópicos** (referência estrutural, NÃO copia frases). Prosa do zero.
   - **⚠️ INVOCAR ≠ INLINE (régua v1.54.0).** "Invoca" significa CHAMAR a Skill tool, NÃO escrever um sub-agent/Python que re-implementa o guia. A skill viva já carrega a régua COMPLETA dela (health-YMYL, voz-eximir, Amazon-zero nas seções educativas, âncora=keyword + slug REAL + home via `/`, FAQ H2 literal "Perguntas Frequentes", densidade de negrito, chavões por nicho). Re-implementar inline = re-introduzir o drift que esta skill existe pra evitar. Incidente real 2026-06-24: o clone inlinou guide/intro/meta e perdeu o anti-clone intra-site da intro + checks YMYL do guide.
   - **OBRIGATÓRIO: passar uma TABELA CANÔNICA de specs por marca/produto** (cafeína/dose, glúten, ativos-chave, preço) extraída das bíblias, e instruir "use SÓ esta tabela pras seções de marca/cafeína". **Caso real: sem a tabela o sub-agent FEZ BRAND-SWAP** (descreveu o Dux com specs do True Source: 200mg/L-teanina; e o 3VS como "contém glúten" quando é sem glúten). Auto-check pós-geração: nenhuma spec de uma marca aparece em outra; produto X "para iniciantes" não é o de maior cafeína.
2. **2.2 Confirmar que a skill rodou** (NÃO re-listar a régua dela): a `artigo-guia-escrever` já aplicou + auto-validou a régua completa dela ao gravar. Aqui o gate só confirma o ESSENCIAL ESTRUTURAL que a clone tem que garantir: (a) `guideContent` não-vazio e gravado, (b) 5 H2 obrigatórios presentes, (c) **2-5 links internos hub-and-spoke** resolvendo pras páginas reais do destino (caso real: regen ZEROU os links por ler "opcional"). Os demais critérios editoriais (YMYL, voz, âncoras, FAQ literal, negrito, chavões) são responsabilidade da skill invocada — se ela rodou de verdade, já passaram. Se a clone tiver inlinado em vez de invocar, RE-INVOQUE a skill. Algum essencial falhar → re-rodar a skill ou auto-fix dirigido → re-valida (máx 3x).

### Etapa 3 — Intro + Meta (gerar + auditar + auto-fix)
1. **3.1 INVOCAR DE VERDADE** `artigo-intro-escrever` + `artigo-meta-escrever` **via Skill tool** (`Skill(skill="afiliados-skills:artigo-intro-escrever", ...)` e idem meta), NÃO inline.
   - **⚠️ A intro carrega o ANTI-CLONE INTRA-SITE** (a skill lê as intros IRMÃS do mesmo site e garante zero sequências de ≥6 palavras iguais). Esse check só acontece se a skill for INVOCADA — inline o clone não vê as intros irmãs e gera abertura colada (incidente das 3 intros idênticas no melhorimpressora). A meta carrega benefício-first + divergência cross-site. Invocar de verdade herda os dois.
2. **3.2 Confirmar que as skills rodaram** (NÃO re-listar a régua): só o ESSENCIAL ESTRUTURAL — intro gravada (2-3 parágrafos, §1 com keyword bold + §final com keywordPlural bold `. ✅`, exatos 2 bolds, sem heading/travessão/marca) e meta gravada (50-160 chars, single-line). Anti-clone intra-site da intro e benefício-first da meta são da skill invocada. Inlinou em vez de invocar → RE-INVOQUE. Falha → re-rodar a skill ou auto-fix → re-valida.

### Etapa 4 — Audit do artigo inteiro (auto-fix)
1. **4.1** Invoca `artigo-auditar` com `PIPELINE=yes` (**inline, no turno; nunca em background**) (39 categorias editoriais + 4 estruturais hasIntro/hasGuide/productCount≥3/hasMeta + `readyToLock`). Issues críticos → auto-fix dirigido → re-audita (máx 3x). Não-convergido → flag.

### Etapa 5 — Duplicata vs fonte: SÓ FRASE EXATA (canon Marcelo 2026-08-13)
1. **5.1** Roda o comparador `compare-cross-site.py` **desta pasta**, pelo caminho literal, entre o artigo destino e o fonte: frases idênticas (≥6 palavras, HTML→espaço), near-dup (jaccard ≥0.8 e ≥0.6), overlap 5-grama e 8-grama, specs label↔value.

   ```bash
   python3 .claude/skills/artigo-clonar-em-massa/compare-cross-site.py \
     sites/{target}/src/content/reviews/{slug}.mdx \
     sites/{source}/src/content/reviews/{slug}.mdx
   ```

   ⚠ **O exit code NÃO é o gate — leia o JSON.** O script sai **1** sempre que `frases_exatas > 0` OU `near_dup_0.8 > 0`, e num clone saudável isso é o estado NORMAL: os 5 H2 base são slots do template e coincidem com a fonte por construção (ver 5.1.5). Gate por exit code reprovaria 100% dos clones. O que decide é a **lista classificada** (`exatas_lista` / `near_lista`) depois de descartar as classes isentas. Mesma armadilha, invertida, do `audit-editorial.ts` na `pagina-produto-criar-em-massa`, que sai 0 mesmo com achado.

   ✅ **Desde a v1.91.0 isso é gate, não confiança:** a Etapa 6.3.6 roda o `verify-output --source=` que executa ESTE script e reprova frase exata fora dos H2-slot antes do commit. Rodar aqui na 5.1 continua sendo o certo (é onde você conserta em loop), mas se pular, o 6.3.6 barra.

   🚨 **PROIBIDO escrever um comparador próprio inline.** Ter a régua no contexto NÃO substitui rodar o script — a implementação dele difere da que você escreveria, e é exatamente nessa diferença que mora o achado. **Caso real (somprofissional/melhor-caixa-de-som-jbl, 2026-08-10):** rodei um comparador inline "equivalente" e ele reportou 3 exatas + 3 near-dup ≥0.8, enquanto o `compare-cross-site.py` reportou **4 + 7** no mesmo par de arquivos. Os 5 a mais eram defeito real (2 títulos de bullet, 1 frase de review, 2 frases do guia, uma delas quase idêntica à da fonte) e teriam ido pro ar. Mesma classe das memórias [[feedback_seguir_skill_a_risca_nao_reusar_contexto]] e [[feedback_clone_regua_fonte_unica_invocar_de_verdade]]: reusar contexto no lugar de rodar a ferramenta.
1.5. **⚠️ FALSOS POSITIVOS QUE VOCÊ NÃO DEVE CONSERTAR (canon 2026-07-30).** Antes de reescrever qualquer coisa, descarte estas classes — elas convergem **por construção** e "consertar" só quebra consistência:
   - **Os 5 H2 base do guide** (`Vale a pena…` / `Como escolher…` / `Qual a melhor marca…` / `Perguntas Frequentes` / `Conclusão`). São slots do template da `artigo-guia-escrever`, e dois deles são obrigatoriamente literais em toda a rede. Coincidir com o fonte é **esperado**. Não parafraseie para baixar jaccard.
   - **Subtitle keyword-first** do mesmo produto (crit. 22 deriva de keyword+badge, converge por design).
   - **`specs_identicas`** — é ficha do mesmo produto, é fato, não texto.
   - Frase factual rígida (dose, contraindicação, rendimento, medida).
   - **Near-dup ≥0.8 e overlap de n-grama em geral (canon 2026-08-13): NÃO reescrever.** Medido na rede: 30 pares de irmãos publicados têm 8-grama mediana 0,5%/máx 1,6% sem ninguém reescrever near-dup — o overlap baixo vem da variação estrutural. O comparador continua IMPRIMINDO near-dup pra revisão humana, mas ele não dispara reescrita. O que dispara reescrita é **frase exata** fora dos H2-slot, que é exatamente o que o `verify-output` bloqueia.
2. **5.2** Sobrou **frase exata** fora das classes isentas (exatas > 0)? Corrija, escolhendo o meio pelo tamanho do trecho:
   - **Fragmento isolado** (heading, título de bullet, frase curta) → **conserte inline** com substituição determinística. Medido em 3 clones (2026-07-30): 2 de 2 achados reais eram fragmento, e um `replace` resolveu. Disparar sub-agent pra isso é desperdício.
   - **Prosa corrida** (parágrafo, bloco) → aí sim sub-agent reescreve SÓ aquele trecho, sem mudar fato.
   → **5.3 re-scan** → loop até limpo OU máx 3 rodadas. Sobra → flag no relatório.
   - Nota honesta: frases factuais rígidas (contraindicação/dose/alérgeno) convergem por serem boilerplate de indústria; o foco da reescrita é o conteúdo AUTORAL (subtitles, prosa), não bula que aparece igual no mundo todo.
3. **5.4 RE-GATE mecânico dos campos reescritos (OBRIGATÓRIO, régua v1.54.0):** a reescrita anti-dup é o ponto de MAIOR risco de re-introduzir defeito mecânico (concordância PT-BR quebrada, capitalização errada, travessão/`;` que voltou, voz-comprador que vazou na nova frase, rótulo canônico do fullReview alterado). Após CADA rodada de reescrita que tocou um campo, re-rodar o **gate mecânico da Etapa 1.2** SÓ nos campos mexidos (travessão=0, `;`=0 entity-aware, links Amazon 2-3 tag-aware, texto-puro, 4 parágrafos com rótulos LITERAIS, voz-comprador lista ampla, concordância/capitalização). Falhou → corrigir antes de fechar o loop. NÃO fechar a Etapa 5 com campo reescrito que regrediu no gate 1.2.

### Etapa 6 — Home + infra + build + commit
1. **6.1 Frontmatter final**: (a) **categorySlug** força sem acento (`pré-treino` → `pre-treino`, bug conhecido do `/categoria/`); (b) **backstop do título** — re-confere que o `title` gravado bate o regex do padrão-assinatura do destino E diverge de TODOS os irmãos cross-site (a Etapa 0 passo 8 já decidiu/validou; aqui é só a rede de segurança caso algo tenha sobrescrito o título no meio do pipeline). Falhou → regera no padrão do destino antes de buildar.
2. **6.2 Home (se HOME=yes)**: configura homeReviewSlug:
   - `sites/{target}/src/config.ts`: adiciona/ajusta `homeReviewSlug: '{slug}'`.
   - `sites/{target}/src/pages/index.astro`: troca `IndexPage` → `HomeAsReviewPage`.
   - (`[slug].astro` do template1 já filtra o home-slug via siteConfig.homeReviewSlug — confirmar.)
   - Registra `melhorpretreino`/target em `TEMPLATE_KNOWN_DIVERGENCES` (index.astro) no server.ts + scripts/template-diff.ts se o site virar homeReviewSlug e ainda não estiver lá (senão o chip "Template" acusa falso drift).
3. **6.3 Build** (`pnpm --filter {target} build`): gate Zod/YAML. Falha → conserta (YAML do .mdx) → rebuild.
3.5. **6.3.5 FAQ-shuffle anti-footprint (OBRIGATÓRIO se há irmão na keyword)**: se o artigo clonado tem irmão(s) na MESMA keyword em outro(s) site(s) da rede (quase sempre o caso num clone, já que a fonte é um irmão), rodar `bun scripts/faq-shuffle.ts {target}/{slug} --apply` ANTES do commit. Determinístico/idempotente (função pura por seed), só reordena a FAQ, não muda redação. NÃO é opcional nem "deixa pro batch depois" — faz parte do fechamento do clone (canon Marcelo 2026-06-24: "já era pra ter feito, nem precisa perguntar"). Rebuildar após o shuffle. Ver [[feedback_aplicar_fix_deterministico_seguro_sem_pedir]].
3.6. **6.3.6 GATE MECÂNICO ANTES DO COMMIT (obrigatório):**

   ```bash
   bun scripts/clone-log.ts verify-output {target} {slug} --source={source-site}
   bun scripts/clone-log.ts verify {target} {slug}
   ```

   **Nesta ordem** (o `verify` lê a seção mecânica que o `verify-output` escreve). Exit 1 em qualquer um → **NÃO commite**, conserte e re-rode. O `verify` reprova etapa não-soft sem `[x]` (o clone de 15/08 fechou com 1.2/2.2/3.2 desmarcadas porque só o `verify-output` rodava): marque cada etapa com `check` quando ela termina, não no fim de memória. Checa o artefato de verdade (fence == 2, sem `contentLocked`, title não-vazio com contagem, `productCount >= 3`, guide com 5 H2, FAQ literal, intro no body fechando em ✅, sem travessão) — coisas que passam despercebidas quando quem confere é a mesma cabeça que escreveu.

   **`--source` é obrigatório em clone** e é o que torna a Etapa 5 um gate de verdade: com ele, o `verify-output` **roda o `compare-cross-site.py` ele mesmo** e reprova qualquer **frase exata** compartilhada com a fonte que não seja um `<h2>` presente nos DOIS guias. Ou seja, não há como commitar sem o comparador canônico ter rodado e voltado limpo — a régua do 5.1 deixou de depender de eu lembrar. Near-dup ≥0.8 e specs idênticas são **impressos pra revisão e não travam** (exigem julgamento: subtitle keyword-first converge por design, ficha é fato). Sem `--source` o script avisa que a checagem de duplicata não rodou.

   A `artigo-clonar-fila` já exigia isso por artigo; a clone individual não, e a assimetria não fazia sentido: rodar 1 clone sozinho tinha MENOS trava que rodar o mesmo clone dentro de uma fila. Se estiver dentro da fila, ela também roda o `verify` (etapas do clone-log).

   **⚠️ A clone individual TAMBÉM mantém o log agora (canon 2026-08-10).** Antes só a fila mantinha, e o efeito foi medido: em 10/08 duas clones individuais rodaram e **não deixaram rastro nenhum** — os 62 logs existentes eram todos de fila, ou seja, o modo mais usado era o único sem registro. Fluxo igual nos dois modos: `init` na Etapa 0 · `check` ao fechar cada etapa · `note` quando houver desvio ou sugestão · `verify` + `verify-output` no fim. Ver "Log de execução" no fim desta skill.

4. **6.4 Commit + push** (`--no-verify`, hook bloqueia .mdx direto) + **regen `gen.ts`** (senão painel mostra "0 artigos") + **`bash scripts/painel-vps-pull.sh`** (VPS; retry 1-2× se der erro de lock de ref, é transitório) + **restart do dev server** do target (`POST /dev/stop` + `POST /dev/start` no painel local, ou reiniciar o `pnpm dev`; senão getStaticPaths fica stale e a rota nova dá 404).
5. **6.5 Verifica infra** (auto): build OK + dev serve a home + `/{slug}/` 200 + painel lista o artigo.

### Relatório final (o que o humano lê)

**Antes de escrever o relatório: `ScheduleWakeup(stop:true)` se você armou heartbeat (standalone). Com `FILA=yes`, NÃO chame `ScheduleWakeup` (o despertar é da fila).** O relatório final é a ÚNICA mensagem que encerra o turno neste pipeline.
- Artigo criado: site/slug, título, N produtos (ordem final + badges), home sim/não.
- Por etapa: o que cada audit pegou, o que foi auto-corrigido, **o que NÃO convergiu** (⚠ revisar).
- Comparação vs fonte: frases idênticas, near-dup, overlap, specs — antes e depois da reescrita.
- Build/infra: status. Commit hash. FAQ-shuffle aplicada (Etapa 6.3.5).
- Próximo passo: revisar a home renderizada; se aprovar, travar (contentLocked) + deploy (ambos manuais).

## Prompt do sub-agent de review (Etapa 1.1) — LÊ a régua canônica, não resume

**A régua NÃO é re-escrita aqui — o sub-agent LÊ a skill `artigo-review-criar` viva.** Resumo inline drifta toda vez que a `artigo-review-criar` evolui (era a causa-raiz de o clone gerar subtitle desatualizado, voz-comprador vazada, "Para quem é" repetitivo, jargão dev). Em vez disso, o prompt do sub-agent é:

```
Você vai gerar os 6 campos do review-no-artigo de UM produto, em modo biblia-only.

PASSO 1 — LEIA a régua canônica (NÃO improvise, NÃO use resumo de memória):
- Read `.claude/skills/artigo-review-criar/SKILL.md` (régua INTEIRA: subtitle híbrido fluindo,
  "Para quem é" variar-abertura + cap "ocupa o papel ≤2", shortDescription literal sem molde, bloco "Voz natural" (verbo/substantivo no sentido do dicionário, sem sacada, "para"),
  pros/cons formato, fullReview 4 parágrafos com rótulos LITERAIS, voz analítica categoria D,
  sem travessão, sem ";", texto-puro, links tag-aware, health YMYL, hard caps, jargão dev banido).
- Read `docs/painel/_data/chavoes-por-nicho.json` → use `_genericos` + bloco do nicho deste site
  — banidos absolutos (lineup/SKU/ASIN/datasheet) são regra DURA; os limites ingles/medico/industrial são referência, não limite (não troque a palavra certa pra baixar contagem).
Aplique ESSA régua na íntegra. Onde este prompt e a SKILL.md divergirem, a SKILL.md ganha
(exceto os DELTAS DO CLONE abaixo, que são adições, não conflitos).

PASSO 2 — Inputs deste produto:
- target, slug-artigo, ASIN, badge, affiliateTag (crua se vazia)
- bíblia (conteúdo de docs/biblias-v2/{ASIN}.json) — ÚNICA fonte, não leia mais nada

DELTAS DO CLONE (adições à régua da skill):
- biblia-only: a ÚNICA fonte factual é a bíblia. NUNCA citar nem ver o artigo fonte. NÃO leia
  a página individual do produto nem outros artigos do site — anti-dup de prosa foi cortado por
  medição (canon 2026-08-13, ver Etapa 1.3); sobreposição residual com irmãos é aceita.
- subtitle: NÃO inventar ângulo novo; segue a régua de subtitle da skill (a normalização
  keyword-first cross-produto fica pra Etapa 1.4). O ângulo editorial do review é o BADGE.
- superlativo geral = SÓ a posição 1. Se este produto NÃO for a posição 1, NUNCA escreva
  "a melhor {keyword}" / "a melhor {keyword} deste comparativo" / "a melhor que analisamos"
  (superlativo geral). Ancore no ângulo de NICHO do badge ("a mais barata", "a de grande
  formato", "a de entrada", "a de sublimação"). Só o nº1 carrega o "a melhor" geral. Isso
  evita dois produtos reivindicando liderança (a Etapa 1.4 reconcilia, mas gasta ciclo —
  caso real 2026-07-23: fotos e personalizados tiveram duplo-"melhor" pego no 1.4).

SAÍDA: retorne SÓ um JSON com os 6 campos (subtitle, shortDescription, pros[], cons[], specs[],
fullReview). A skill-mãe monta o .mdx — NUNCA edite .mdx nem rode git.
```

⚠️ **Se a mãe optar por deixar CADA worker persistir o próprio JSON** (variante legítima: fecha o
buraco de 2.5, onde uma queda antes do último retorno joga fora a leva inteira), o caminho é
**`docs/biblias-v2/.audits/clone-runs/rev/{target}-{slug}/{ASIN}.json` — um arquivo POR ASIN, nunca um compartilhado.** N workers
paralelos escrevendo o mesmo path se sobrescrevem, e o vencedor é o último a fechar: sobra 1 review
de 9 e os outros 8 Opus já pagos evaporam. Caso real 2026-08-13 (clone `melhor-impressora-epson`):
um worker reportou ter encontrado o arquivo do colega no lugar do seu. O nome do arquivo é a única
trava — sem `{ASIN}` no path não existe locking entre agentes paralelos. A mãe então lê o diretório
inteiro (`rev/{target}-{slug}/*.json`) em vez do dicionário do contexto, e o resto de 2.5 vale igual.

Se o sub-agent não tiver acesso de leitura à `artigo-review-criar/SKILL.md` (ambiente VPS-only raro), a skill-mãe lê o arquivo e COLA o conteúdo dela no prompt — nunca cair num resumo de memória.

## Shuffle determinístico (Etapa 1.0)

```
top3 = sourceAsins[0:3]   # fixos
resto = seededShuffle(sourceAsins[3:], seed=FNV1a(target+source+slug))
finalOrder = top3 + resto
```
Badge **e `rating`** seguem o ASIN (cada produto mantém seu badge e sua nota editorial do fonte → preserva a estrela). Top-3 fixo mantém "Melhor Escolha" na posição 1 (régua do projeto).

## Montagem do .mdx (Etapa 1 fim)

Assembler determinístico (Python: json.dumps para campos single-line — subtitle/shortDescription/specs; **block scalar `|` para fullReview e guideContent**). Frontmatter: title (SEMPRE no padrão-assinatura do destino — ver regra `TITLE=`; passou o HARD GATE de padrão + divergência cross-site; NUNCA o literal do `TITLE=`/fonte), description (placeholder até a meta), keyword, keywordPlural, listHeading, category, categorySlug (sem acento), homeReviewSlug (se HOME), **publishDate (OBRIGATÓRIO — o schema Zod exige; sem ele o build falha com `publishDate: Invalid date`)**, **featuredImage (og:image/hero do artigo — use uma imagem que EXISTE no destino, ex.: a `image` do 1º produto; sem isso vira 404 social/hero, caso real escritorioecasa sublimatica 2026-06-17)**, + products[] na ordem final (base do fonte + 6 campos gerados). guideContent vazio nesse momento (Etapa 2 preenche via skill).

**⚠️ ORDEM DOS CAMPOS DO PRODUTO — `name` PRIMEIRO (HARD GATE).** Cada item de `products[]` DEVE começar por `- name:` (depois asin, image, ...). O parser do painel (`docs/painel/_lib/loaders.ts`) conta produtos com a regex `^\s*-\s*name:` — se o 1º campo for `asin` (`- asin:`), o painel conta **0 produtos** e mostra `PRODUTOS —` + `STATUS Vazio` mesmo com o artigo perfeito (Astro ignora ordem de campo YAML, então buildava normal e nada parecia errado). Caso real escritoriocasa/melhor-impressora-epson 2026-06-17. Convenção da rede toda = `name` 1º.

**⚠️ `name`, `image` e `imageAlt` VÊM DA PÁGINA DE PRODUTO DO DESTINO, não do fonte (régua v1.54.0).** O filename de imagem é POR-SITE (uns sites usam slug `epson-ecotank-l3250.webp`, outros prefixo legado `impressora-epson-...webp`). Copiar do fonte propaga o caminho/nome do site errado. Regra: pra cada produto, leia `sites/{target}/src/content/products/{slug-destino}.mdx` e use o `name`, `image` E `imageAlt` DELE. `badge`/`rating`/`schemaPrice`/`store` seguem do fonte (são editoriais/comerciais); `name`/`image`/`imageAlt` são re-derivados do destino.
- **`image`**: garante que o arquivo existe no `public/` do destino (senão imagem 404; casos reais escritoriocasa epson + escritorioecasa sublimatica 2026-06-17).
- **`name` (HARD GATE — build-breaker):** o link hub-and-spoke do guide e a resolução `products/{slug}.mdx` usam `slugify(name)`. Se o `name` vier do fonte e slugificar pra um slug que NÃO existe como página no destino, o **build quebra** (`Entry products → {slug} was not found`; caso real guiaesportivo-com 2026-06-24: `Dux Creatina`→`dux-creatina` vs página real `dux-creatina-monohidratada`, 5 produtos quebrados). Usar o `name` EXATO da página de produto do destino garante `slugify(name)` == slug-da-página. Se o produto NÃO tem página no destino (Etapa 0 passo 5 avisou), manter o `name` do fonte mas REGISTRAR no relatório que o link cairá no fallback Amazon /dp/.

**guideContent E cada `fullReview` de produto DEVEM ser gravados como YAML BLOCK SCALAR (`|`), NUNCA json.dumps/aspas** — guideContent: chave `guideContent: |` na coluna 0, corpo indentado 2 espaços; cada `fullReview`: **chave `fullReview: |` indentada 4 espaços (mesmo nível de subtitle/specs/pros/cons), conteúdo (`<p>`) indentado 6 espaços, um `<p>` por linha**. NÃO ponha a chave a 6 espaços (cai no nível dos itens de `cons`/`pros`) → quebra o YAML (`expected <block end>`, build falha); caso real epson 2026-06-17. O `parseArticle` (article-parser.ts) que alimenta o editor de artigo SÓ reconhece `fullReview` em block scalar `|`: em aspas o campo fica INVISÍVEL no editor (loga "campo será invisível no editor") e o painel reporta "FALTAM N reviews" mesmo com o conteúdo presente — o site renderiza normal (Astro yaml-parseia os dois). Caso real 2026-05-29: gravei os 11 fullReviews via json.dumps → painel mostrou "FALTAM 11 REVIEWS"; corrigido convertendo pra block scalar. (subtitle/shortDescription seguem single-line quoted; pros/cons/specs como listas — esses o parseArticle aceita.) **AUTO-CHECK pós-assembler (OBRIGATÓRIO, antes da Etapa 2)** — TODOS devem passar:
- `grep -c '^    fullReview: |' {target}.mdx` == nº de produtos E `grep -c '^    fullReview: "' {target}.mdx` == 0 (block scalar, não aspas; indent 4).
- `grep -c '^  - name:' {target}.mdx` == nº de produtos E `grep -c '^  - asin:' {target}.mdx` == 0 (name-first; senão painel mostra "Vazio").
- YAML parseia + nº de `products` no parse == nº esperado, E a regex do painel bate: `len(re.findall(r'^\s*-\s*name:', products_block, re.M))` == nº de produtos.
- **`name`↔slug do destino (anti build-breaker):** pra CADA produto, `slugify(name)` (com a regra `+`→`-plus`) tem que existir como `sites/{target}/src/content/products/{slug}.mdx` OU o produto está na lista de "sem página no destino" registrada na Etapa 0. Senão o build quebra com `Entry products → {slug} was not found`. Confira: pra cada `name`, `test -f sites/{target}/src/content/products/$(slugify name).mdx`. Falhou e o produto TEM página com outro slug → o `name` ficou do fonte; troque pelo `name` exato da página do destino.
- TODO `image:` e o `featuredImage:` apontam pra arquivo que EXISTE em `sites/{target}/public{path}` (rode `bun scripts/check-broken-images.ts --site {target}` → 0 quebradas). Imagem é do destino, não do fonte.
Qualquer um falhar = assembler errou; conserte antes de prosseguir. Body intro vazio (Etapa 3). SEM contentLocked.

## Log de execução (clone-log) — o que registrar e por quê

O `clone-log.ts` grava **como a skill foi executada**, não o conteúdo produzido (isso é dos `.audits/articles`). Serve pra ler N runs depois e melhorar a skill com base no que falhou de verdade.

**Três seções, com pesos diferentes:**

| seção | quem escreve | vale pra quê |
|---|---|---|
| **Etapas** (`check`) | o agente | saber o que ele AFIRMA ter feito. Um `[x]` não prova nada, e o cabeçalho do log diz isso em voz alta. |
| **Desvios** e **Sugestões** (`note`) | o agente | é o dado que só ele tem: passo pulado, **passo inventado**, ferramenta trocada, régua ambígua. |
| **Verificação mecânica** | o `verify-output` | única parte que não passa pelo julgamento do agente: sai de ler o `.mdx`, de rodar o `compare-cross-site.py` e do **gate de invocação** (abaixo). |

**⛔ GATE DE INVOCAÇÃO (v1.102.0) — executar à mão o que a skill faria NÃO passa.** O `verify-output` confere no **transcript da sessão** se `artigo-reviews-auditar` (1.4), `artigo-guia-escrever` (2), `artigo-intro-escrever` + `artigo-meta-escrever` (3) e `artigo-auditar` (4) foram de fato invocadas via Skill tool, **com os args deste artigo e depois do `init` desta run**. Faltando qualquer uma: exit 1, sem commit.

Por que existe: em 14/08 as etapas 1.4/3.1/4.1 foram rodadas como script inline (um deles adaptado com `sed` do clone anterior) e marcadas de boa-fé no log. Custo medido ao re-rodar as skills de verdade: **7 defeitos que a passagem inline não pegou, 2 deles INTRODUZIDOS por ela** — a auditoria inline cobriu 32 de 38 categorias, faltando justamente `claim-vs-bible` e `decisao-editorial-violada`. Nenhum checkbox distingue "rodei a skill" de "fiz o que eu achei que a skill faz"; o transcript distingue, porque quem escreve nele é o harness. A janela por `init` é o que impede as invocações do clone anterior de satisfazerem este (foi exatamente o par HP → fotos).

**`note` é obrigatório quando** você (a) pulou uma etapa, (b) **criou uma etapa que a skill não tem**, (c) usou ferramenta diferente da que a skill manda, ou (d) achou a régua ambígua/contraditória. Sintaxe:

```bash
bun scripts/clone-log.ts note {target} {slug} desvio   <etapa|geral> "o que fugiu e por quê"
bun scripts/clone-log.ts note {target} {slug} sugestao <etapa|geral> "o que na skill atrapalhou"
```

**Por que os desvios importam mais que as etapas:** das 4 reincidências registradas do agente neste projeto (16/06, 10/07, 06/08, 10/08), **duas foram por INVENTAR etapa**, não por pular. Checklist de etapas não tem onde registrar isso — só o `note` tem. E não adianta esperar que o desvio apareça sozinho: o agente que pula um passo é o mesmo que marca `[x]`.

**Não maquie.** Log com desvio registrado vale mais que log limpo: run sem nenhum `note` em 12 etapas é ou execução perfeita ou desvio não declarado, e as duas se parecem no arquivo. O registro honesto é o que faz a leitura em lote valer alguma coisa.

## Comparador cross-site

`compare-cross-site.py` (nesta pasta): recebe dois `.mdx` de artigo (destino + fonte), extrai texto (products[].subtitle/shortDescription/pros/cons/fullReview + guideContent + body intro), strip HTML→espaço, e reporta: frases idênticas (≥6 palavras), pares near-dup (jaccard ≥0.8 e ≥0.6), overlap 5/8-grama, specs label↔value divergentes. Saída estruturada pra a Etapa 5 decidir o que reescrever.

## Armadilhas (todas já mordidas neste projeto — embutir)

0. **Encerrar o turno no meio** (9 casos medidos em ~80 runs, 15/07→15/08): esperar sub-agent em background com "te aviso", mensagem de progresso, ramo de exceção virando pergunta. Ver "## Turno vivo": primeiro plano + heartbeat quando standalone + chat só no fim.

1. **Dev server stale**: criar conteúdo com o dev rodando deixa `getStaticPaths` stale → rota nova dá 404 no preview. SEMPRE restart do dev do target no fim (Etapa 6.4). HMR/touch NÃO resolve (data-store cache).
2. **gen.ts não auto-regenera** em commit cru de .mdx → painel mostra "0 artigos/páginas". SEMPRE `bun docs/painel/gen.ts` no fim.
3. **categorySlug com acento** (`pré-treino`) → `/categoria/` 404. Forçar sem acento.
4. **Astro data-store cache** (`node_modules/.astro`): se mudar schema, `rm -rf` antes do build. Pro dev, restart re-scaneia content.
5. **tar do macOS** inclui AppleDouble `._*` → quebra parsing. Usar `COPYFILE_DISABLE=1` + ignorar `._` no consumidor.
6. **Ownership na VPS**: I/O como `melhorserum-painel` (git como root quebra). cp/edit via `sudo -u melhorserum-painel` ou `chown -R` no fim.
7. **Pre-commit hook** bloqueia `.mdx` direto em content/reviews → commit com `--no-verify` (caminho oficial das skills).
8. **homeReviewSlug + chip Template**: site homeReviewSlug precisa estar em `TEMPLATE_KNOWN_DIVERGENCES` (index.astro) do server.ts E do template-diff.ts, senão o chip acusa falso drift.
9. **Voz-comprador residual**: geração biblia-only ainda vaza "opiniões/relatos/elogiado/quem comprou/segundo o fabricante" — o gate 1.2 + 1.4 pegam; auto-fix destila.

## Limites de segurança (a skill NUNCA faz)

- Deploy (`cf-deploy*`) — aprovação humana explícita.
- `contentLocked: true` — fica editável.
- Preencher `affiliateTag` — fica como está (regra: tag é das últimas coisas).
- Tocar em outros sites ou no template1.

## Disciplina de release

Skill nasce no project repo. Só vai pro marketplace (`marcelohaz/afiliados-skills`) DEPOIS de validada num run real (1º artigo). Padrão: fazer + validar → release.

## Registrar desvio de execução (obrigatório quando houver)

SE você (a) executou diferente do que esta skill manda, (b) **criou um passo que ela
não tem**, (c) achou a régua ambígua/contraditória, ou (d) topou com bug numa
ferramenta dela — ENTÃO registre antes de fechar:

```bash
bun scripts/skill-log.ts note <skill> <desvio|ambiguidade|bug|inventou-passo> "<o que fugiu e por quê>" [--ctx=site/slug] [--alvo=<etapa>]
```

Execução limpa **não gera linha** — vazio é dado. O que se lê depois é
`bun scripts/skill-log.ts report`, que conta por skill e destaca o que já bateu
mais de uma vez. Sem `--alvo` a nota cai em `geral` e sai do detector de
reincidência, então **nomeie a etapa** quando ela existir.
