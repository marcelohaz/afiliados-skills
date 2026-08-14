---
name: biblia-auditar-em-massa
description: Audita E CORRIGE VÁRIAS bíblias v2 de uma vez, cada uma ISOLADA (zero contaminação cruzada, sem passada comparativa). Escopo = FATO + DADO LIMPO + NAMING (bíblia é fonte de fato, nunca renderizada; voz editorial é do review). AUTO-APLICA conserto de direção conhecida (lixo de dado, voz-comprador→analítica, contradição com a própria decisaoEditorial, fonte atribuída errada), cada um com re-auditoria automática e reversão do backup se não convergir em ≤3. REPORT-ONLY pro indeterminável (frescor, verificação externa, naming ambíguo). NÃO mexe em voz editorial. Roda como 2ª etapa do preencher-em-massa --audit OU sozinha. Sub-agents paralelos (≤10). Sync R2 nas 2 pontas. Botão '🔍 Auditar bíblias' do produtos.html copia o comando.
---

## Parse de input

Args no `$ARGUMENTS`:
- **Lista de ASINs** (forma do botão do painel): `B0CH5RSZTP,B01I78MAHW,B093Q7LLD6` (vírgula, sem espaço). Cada um `^[A-Z0-9]{10}$`.
- **`todas`**: varre `docs/biblias-v2/*.json`, pega as **preenchidas** (coreDone) auditáveis (ver Etapa 0.4).
- **Filtro** (opcional): `niche=Panela Elétrica` ou `sub=panela-eletrica` → restringe o "todas" àquela subcategoria.
- **Flag `--report-only`** (opcional, default DESLIGADO): se passada, NÃO auto-aplica nada — só reporta tudo (modo conservador, vira a antiga triagem). Default é auto-aplicar o conhecível.

# Auditar + corrigir bíblias em massa (paralelo, isolado, auto-apply + re-audit)

> Esta skill é **orquestrador**. A régua de auditoria (as 5 categorias) é a canônica do `biblia-auditar` (fonte editorial: aquela skill + `docs/painel/_data/regras-biblia.md`). Esta NÃO reimplementa a régua — ela fan-out + camada mecânica grep + auto-apply + re-auditoria + sincroniza. Análoga à `biblia-preencher-em-massa`, mas pra auditar+corrigir.

## O que esta skill É

- **É** o auditor-corretor em massa: roda em N bíblias **já preenchidas**, cada uma isolada, **conserta o que tem solução conhecida**, e lista só o que precisa de você.
- **NÃO** delega o conserto pra outra skill. A `biblia-auditar` individual vira **fallback** pra mexer numa bíblia só — não é etapa obrigatória depois desta.
- **NÃO é a IA do painel** (botão "✨ Auditar"). Roda na assinatura (Claude Code), Opus 5 (ou o Opus mais novo).

## Garantia de qualidade (= skill individual)

A `biblia-auditar` individual é propor→aprovar: o sub-agent redige o conserto, você aprova. Esta skill **redige o mesmo conserto (mesma régua, mesmo modelo)** e, no lugar da sua aprovação manual, põe **uma re-auditoria automática + backup**:

| | Individual (`biblia-auditar`) | Em massa (esta) |
|---|---|---|
| Quem redige o conserto | sub-agent Opus, régua canônica | **mesmo** sub-agent, mesma régua |
| Texto do conserto | idêntico | **idêntico** |
| Trava antes de "ficar" | você aprova | **re-auditoria automática** (desfaz se piorar) + backup + diff no relatório (você revê depois) |

O texto sai igual; a fiscalização vira **automática (re-audit) + pós-fato (relatório/git)**. Caveat honesto: o caso raro de um conserto sutilmente ruim passar é pego no relatório/backup, não num gate antes. Quem quer paridade 100% literal usa `--report-only` (não aplica, só lista pra aprovar 1-a-1 na individual).

## Classificação de cada achado (3 grupos — decide o destino)

- **(A) Mecânico — deleção/formato puro → AUTO-APLICA.** Sem reescrita, sem julgamento.
- **(B) Reescrita/correção de direção CONHECIDA → AUTO-APLICA + re-audita.** Há uma resposta certa sabida.
- **(C) Indeterminável sem dado novo → REPORT-ONLY (flag).** Não há valor certo pra aplicar; chutar seria pior.

## Modelo

Opus 5 (ou o Opus mais novo disponível). Sub-agents fixados com `model: opus` no Agent tool. NUNCA Sonnet/Haiku.

## ⚠️ Playbook anti-contaminação (o coração desta skill)

1. **A maior parte mecânica é grep, não IA** (Etapa 1) — zero contaminação ali.
2. **Auditar lê o que já existe**; a reescrita (B) é feita pelo sub-agent ISOLADO daquela bíblia, vendo SÓ ela.
3. **Isolamento estrito.** 1 sub-agent por bíblia, conversa fresh, vê **SÓ** aquela bíblia. NUNCA prompt com várias, NUNCA contexto compartilhado.
4. **SEM etapa comparativa entre bíblias.** Cada uma é julgada só contra os próprios dados brutos + régua. (Lembrete: "rita lobo" em 2 Electrolux NÃO é contaminação — cada bíblia tirou dos próprios dados.)
5. **Conserto serial, 1 arquivo por vez**, chaveado por ASIN. Sem race de escrita.
6. **Trava de ASIN.** Sub-agent devolve o `asin`; confere `asin_retornado == asin_pedido` antes de aplicar.

## Invariantes

- **AUTO-APLICA (A) e (B)**; **(C) é report-only** (não há o que aplicar sem dado novo). `--report-only` desliga todo auto-apply.
- **Todo conserto passa por re-auditoria** (Etapa 3.5). Não convergiu em ≤3 tentativas → **reverte do backup** + vira (C) no relatório. Nada fica aplicado sem ter sido re-conferido.
- **Backup ANTES de qualquer escrita** (`.painel-backups/<dia>/`). Tudo reversível.
- **Toca CAMPOS CURADOS** (`sentimentoCompradores`, `angulosConversao`, `pontosFortes`, `pontosFracos`, `dicasAcionaveis`, `dadosInconsistentes`, `observacoesAgente`) **+ naming em `identidade` (`nome`/`marca`) quando o fix é óbvio** (derivável dos dados da própria bíblia, ex.: `marca` vazia e o `nome`/`specsAmazon` dizem "Philco"). **NUNCA edita BRUTOS** (`sobreEsteItem`/`doFabricante`/`descricaoProduto`/`specsAmazon`/`conteudoBrutoFabricante`) nem `lastAuthor`.
- **`lastAuditedAt` carimbado via `new Date().toISOString()` em TODAS as bíblias auditadas** (com ou sem fix) — é o que faz o painel parar de marcar "auditar de novo" (compara `lastFilledAt > lastAuditedAt`; regra Marcelo 2026-06-15). Ver Etapa 3.6.
- **`lastModified` bumpado via `new Date().toISOString()`** sempre que gravar a bíblia (todo conserto E todo carimbo de auditoria → toda bíblia do lote). NUNCA hand-roll (timezone). NUNCA toca `lastAuthor`.
- **`auditFlags` gravado junto do `lastAuditedAt`** (Etapa 3.6): avisos semânticos `{type,label}` pro chip do painel (`'wrong-info'`/`'off-niche'`/`'review'`) — vêm dos `report_C` que sobraram. **Esvaziar (`[]`) quando limpo** é obrigatório (chip preso = bug). É o que surfaça contaminação cross-produto que o detector mecânico não pega.
- **NUNCA compartilha contexto entre bíblias** nem faz passada comparativa.
- **Só audita PREENCHIDA** (coreDone). Pendente → pula ("preencha primeiro"). Contaminada-hard → exclui (corrigir à mão na individual). Sem-dados-brutos → exclui.
- **Sync R2**: pull no começo; push no fim SÓ se aplicou algum fix.
- **NÃO faz deploy.**
- **Cap de paralelismo: 10 sub-agents.** Acima → levas.
- **Nunca inventa achado.** Categoria sem problema = "nenhum". Toda flag/conserto precisa de evidência (trecho literal < 15 palavras).

## Pipeline

### Etapa 0 — Pré-flight (auto; aborta/exclui cedo)

0.1. **Sync R2 pull**: `bun scripts/sync-biblias-r2.ts --apply 2>&1 | tail -3` (pull-only). Falhou → seguir, avisar que ausentes pulam.
0.2. **Parse** dos ASINs (ou expandir `todas`/filtro). Validar `^[A-Z0-9]{10}$`.
0.3. **Carregar cada bíblia** (`docs/biblias-v2/<ASIN>.json`). Ausente → pular + listar.
0.4. **Classificar**: Pendente (não coreDone) → **PULA** ("preencha primeiro"). Contaminada-hard (`check-contamination.ts` com `cross-brand-mention`) → **EXCLUI** (corrigir à mão na individual). Sem-dados-brutos → **EXCLUI**. Preenchida + não-hard-contaminada → **ENTRA**.
0.5. **Mostrar plano + confirmar** (tabela ENTRA/PULA/EXCLUI + nº no lote + estimativa). `S/N` antes do paralelo. (Quando encadeada pelo `preencher-em-massa --audit`, herda o lote recém-preenchido, sem nova confirmação.)

### Etapa 1 — Camada MECÂNICA grupo (A) (grep determinístico, sem IA)

Scan determinístico nos campos curados. **Só LIXO DE DADO + NAMING** (não voz editorial — ver escopo abaixo). Padrões e o conserto:
- **HTML na curadoria**: `<\w+[^>]*>` em qualquer campo curado → **strip da tag** (curadoria é texto puro; tag = ruído, não info). Vale em TODOS os campos curados.
- **Caractere invisível / BOM** (`﻿`, zero-width) no `nome`/`marca`/curado → **remover**.
- **Espaço duplo** no `nome`/`marca` → **colapsar pra um**.
- **Marca duplicada no nome** ("Epson Epson L3250") → **remover a 2ª**.
- **`marca` vazia mas DERIVÁVEL** (campo `identidade.marca` em branco e o `nome`/`specsAmazon` dizem a marca de forma inequívoca, ex.: nome "Philco PAF40A" + specsAmazon "Nome da marca PHILCO") → **preencher `identidade.marca`** com a marca canônica (régua Marcelo 2026-06-27). Marca real INCERTA (vários candidatos, placeholder `—` sem fonte clara) NÃO entra aqui → fica (C) report-only.
- **Duplicação contígua** `([a-zA-ZÀ-ÿ\s]{8,40})\1` em campo curado → remover a 2ª cópia.

⛔ **FORA do escopo da bíblia (NÃO scaneia, NÃO conserta — é do review/página):** travessão, muleta "declarado pelo fabricante", superlativo/claim absoluto, concordância PT-BR. Essas regras de VOZ são aplicadas pelas skills de criação sobre o texto reescrito (régua + auto-check próprios). Enforçar aqui é trabalho dobrado.

**Escopo de campos:** voz-comprador (grupo B) vale só nos campos que ALIMENTAM o review (`sentimentoCompradores`/`angulosConversao`/`pontosFortes`/`pontosFracos`/`dicasAcionaveis`). NÃO nos internos (`dadosInconsistentes`/`observacoesAgente`) — `EAN`/`ASIN`/`specsAmazon`/`127V` ali é legítimo. **HTML-strip vale em todos.**

### Etapa 2 — Camada LLM: achar + redigir conserto (sub-agents ISOLADOS)

N sub-agents Opus, levas ≤10. Cada um (Agent tool, `model: opus`, fresh) vê SÓ sua bíblia. Anti-contaminação no prompt: "Você vê SÓ esta bíblia. NÃO mencione/leia outra. NÃO compare com outras." **Régua = FONTE ÚNICA: o prompt manda o sub-agent LER `.claude/skills/biblia-auditar/SKILL.md` + `docs/painel/_data/regras-biblia.md` à risca e aplicar as categorias de FATO de lá** — resumo inline de régua = proibido (evita drift; sub-agent não invoca Skill tool, por isso LÊ o arquivo; mesma fonte única da `pagina-produto-criar-em-massa`/clone). ⚠️ **A lista de categorias é a do arquivo lido, NÃO a deste parágrafo.** O que vem a seguir é orientação **não-exaustiva** pra montar o prompt — a checklist operativa do sub-agent tem que sair de `regras-biblia.md` (categorias do auditor) + categorias da `biblia-auditar`. Esta skill proíbe resumo inline de régua justamente porque ele drifta: em 2026-07-30 esta enumeração já estava sem **voz-comprador**, e 9 auditores em sequência deixaram passar a moldura de comprador plural por tomarem a enumeração como a lista fechada. Se você (skill-mãe) colar um "## Escopo" no prompt, marque-o como não-exaustivo e mande o sub-agent conferir a lista canônica antes de fechar o JSON. Escopo de FATO (orientação): consistência interna, **contaminação cross-produto** (dado de OUTRO produto em qualquer campo inclusive bruto), verificação externa, frescor, completude, naming, **voz-comprador** (inclui a moldura de sujeito humano MESMO com cardinalidade certa — ver categoria 5 da `biblia-auditar`), **e imagem anexada não lida** (canon 2026-07-26 — passar as URLs de `conteudoBrutoFabricanteImagens`/`doFabricanteImagens` no prompt e autorizar `curl` + `sips -Z 1400` + `Read`; sem isso o sub-agent audita só o texto e o achado nunca aparece. Se `imagensVerificadasEm` existe e a lista não mudou, avisar que já foram lidas). **NÃO audita voz editorial** (travessão/muleta/superlativo/concordância — é do review). Pra cada achado, **classifica B ou C e, se B, JÁ REDIGE o texto corrigido**:
- **(B) direção conhecida → redige o fix**: voz-comprador crua → observação analítica (vira fato usável) — **preservando a cardinalidade**: 1 review vira "há relato de X" (hedge singular), nunca consenso plural cru (Armadilha 1 da biblia-preencher); contradição contra a **própria `decisaoEditorial`** da bíblia → seguir a decisão; fonte atribuída errada num item curado → corrigir a fonte; claim curado que contradiz o bruto quando o bruto tem o valor certo → alinhar ao bruto.
- **(C) indeterminável / precisa de decisão → só aponta**: frescor (precisa re-captura); claim que exige verificação externa não feita; contradição no dado BRUTO sem valor certo nem `decisaoEditorial`; **contaminação cross-produto num campo BRUTO** (dado de outro produto que não dá pra consertar curando — precisa re-captura); naming que precisa de DECISÃO — marca real INCERTA (vários candidatos, placeholder `—` sem fonte clara), nome linha-vs-fabricante (marca vazia mas DERIVÁVEL dos dados NÃO é (C): vira fix mecânico (A), ver Etapa 1); spec ambiental/origem nos curados; qualquer coisa que dependa de dado que a bíblia não tem.
- **Marque cada (C) com `flagType`** (vira o chip do painel na Etapa 3.6): `'wrong-info'` — SÓ em 3 casos: **(a) ASIN da captura divergente** — o ASIN que aparece DENTRO do `specsAmazon` (linha `ASIN  B0...`) é DIFERENTE do `asin` da bíblia → captura de outro produto. ⚠️ **ÚNICO gatilho de `wrong-info` para o campo `specsAmazon`** (teste mecânico de igualdade de ASIN, NÃO julgamento de conteúdo). **(b) fato errado em campo CURADO** sobre ESTE produto. **(c) contaminação cross-produto** = texto de um produto GENUINAMENTE diferente (outra marca/outro modelo, não variante-irmã) colado em qualquer campo. ⚠️ **NÃO acende NENHUM chip (nem `wrong-info`, nem `review`)**: divergência de ATRIBUTO entre `specsAmazon` e fabricante (CPU/tela/RAM/SO/bateria/peso/Wi-Fi capturado errado) **com o ASIN da ficha CONFERINDO**, atributos espúrios de listagem (AWD/Art Deco/etc.), ou material de variante-irmã no `conteudoBrutoFabricante` com ASIN certo → registra em `dadosInconsistentes` (fix B) e NÃO vira flag. Âncora (Marcelo 2026-06-22): o campo `specsAmazon` só gera "informações erradas" se o ASIN lá for diferente do da bíblia; divergência de atributo com ASIN certo NÃO gera nem "revisar". `'off-niche'` (tipo de produto do bruto contradiz a `categoria`/`subcategoria` declarada NA PRÓPRIA bíblia — raro; NÃO é "produto no site errado", isso a bíblia não sabe), `'review'` (SÓ frescor que exige re-captura / verificação externa pendente que importa / valor genuinamente incerto. NÃO emitir por divergência de atributo specsAmazon×fabricante nem por estado que já tem chip operacional próprio — sem opiniões/sem preço/indisponível).
- **Retorna SÓ JSON**: `{ asin, fixes_B: [{categoria, campo, evidencia, problema, antes, depois}], report_C: [{categoria, campo, evidencia, problema, sugestao, flagType}] }`. NÃO grava arquivo, NÃO aplica.

### Etapa 3 — Aplicar (A) + (B) (skill-mãe, SERIAL, chaveada por ASIN)

Pra cada bíblia com fix (A) confirmado ou (B) retornado:
3.1. **Trava de ASIN**: `json.asin == pedido`? Não → descarta + re-dispara isolado.
3.2. **Backup**: `cp docs/biblias-v2/<ASIN>.json docs/painel/.painel-backups/<dia>/<ASIN>-v2-<HHMMSS>.json`. ⚠️ **O nome é EXATAMENTE esse — não invente sufixo** (`-preaudit`, `-audit`, `-voz`, `-stamp`…). O painel só lista o que casa o regex de `docs/painel/_lib/handlers/backups.ts` (`{ASIN}-v2-{6 dígitos}` + uma allowlist curta de sufixos), então backup com sufixo improvisado **existe no disco mas some da UI de restore** — o usuário não consegue desfazer. Medição 2026-07-30: 210 de 459 backups de bíblia estavam invisíveis, acumulados por sufixos ad-hoc de vários runs. `HHMMSS` é 6 dígitos: nada de epoch nem de `aud170950`.
3.3. **Aplicar (A)** (deleção/formato + naming óbvio em `identidade.nome`/`identidade.marca`, ex.: preencher marca vazia derivável) **+ (B)** (substituir `antes`→`depois` no campo curado exato). NUNCA tocar brutos. NUNCA aplicar (C).
3.4. **Bumpar `lastModified = new Date().toISOString()`**. Manter `lastAuthor`. Write `JSON.stringify(b,null,2)+'\n'`.
3.4.1. **GUARDA DE SCHEMA pós-write (OBRIGATÓRIA, canon 2026-07-30).** Guarde **em memória**, antes de escrever, um mapa `campo → tipo` de cada campo curado (e, dentro de `angulosConversao`, o tipo de cada `frases` e de cada item dela). Depois do write, recarregue o arquivo e compare: nenhum array pode ter virado string, nenhum objeto pode ter virado escalar, nenhum item de `frases` pode deixar de ser string. ⚠️ **O baseline é esse snapshot em memória, NÃO o backup da 3.2** — numa reaplicação a 3.2 gera um backup novo, já do estado corrompido, e a comparação passaria em falso.
   - **Divergiu?** Restaure aquele campo do backup **pré-fix** (o mais antigo da rodada, não o recém-criado), **conserte a resolução de caminho no seu aplicador** e só então reaplique. Reaplicar com o mesmo aplicador quebrado é loop.
   - **Por que existe:** o `campo` do fix vem como caminho aninhado (`angulosConversao[0].frases[2]`, `sentimentoCompradores[3].resumo`). Um aplicador que resolve só os dois primeiros tokens pega a LISTA `frases`, faz `str(lista)` e grava o **repr da linguagem** por cima do array. O JSON continua válido, o texto novo até aparece lá dentro, e o schema morre em silêncio. Caso real 2026-07-30: 9 arrays corrompidos em 6 bíblias num único lote. **Resolva o caminho inteiro até a folha e só edite se a folha for string.**
   - Este check é mecânico e determinístico: **não delegue à re-auditoria da 3.5.** Lá dependeu de os auditores repararem, e reparar não é garantia.

### Etapa 3.5 — RE-AUDITORIA (a trava no lugar da aprovação humana)

Pra cada bíblia que recebeu conserto, dispare um sub-agent Opus ISOLADO (fresh, vê só essa bíblia + a lista do que foi consertado) pra verificar:
1. **Os achados originais sumiram?** (o conserto resolveu de fato)
2. **Não introduziu lixo nem voz-comprador novo?** (HTML/tag, voz-comprador crua). Voz editorial (travessão/superlativo) NÃO é checada aqui — fora do escopo da bíblia.
3. **Não mudou o SENTIDO factual** vs os dados brutos? (a reescrita não inventou nem distorceu fato)
- **Passou** → mantém o conserto. ✅
- **Reprovou** → re-redige o(s) item(ns) problemático(s) e re-aplica → re-audita (máx **3** ciclos no total).
- **Não convergiu em 3** → **reverte aquela bíblia do backup** + move os itens dela pra (C) no relatório (flag "conserto não convergiu, revisar à mão"). Nada ruim fica gravado.

### Etapa 3.6 — Carimbar auditoria + gravar `auditFlags` em TODAS as bíblias do lote (mesmo sem fix)

Pra **cada** bíblia auditada (consertada ou não), no MESMO write: backup (se ainda não fez na 3.2), e setar:
- **`b.lastAuditedAt = new Date().toISOString()`** + **`b.lastModified = new Date().toISOString()`** (mantém `lastAuthor`; não toca curados/brutos além da 3.3). Zera o "auditar de novo" (`lastAuditedAt` ≥ `lastFilledAt`).
- **`b.auditFlags`** = avisos SEMÂNTICOS que SOBRARAM pós-conserto, pra acender o chip na coluna Observações do painel (o detector mecânico `contaminado` só pega marca/ASIN; estes são os achados que só a auditoria vê). Cada flag `{ type, label }` (label ≤ ~120 ch, sem aspas duplas, com o motivo concreto):
  - **`type` = o `flagType` do `report_C`** correspondente (`'wrong-info'` ⚠ / `'off-niche'` 🧭 / `'review'` 🔍).
  - **Só `report_C` vira flag.** Achado **(B) auto-consertado NÃO vira flag** (já resolvido).
  - **Se NENHUM `report_C` qualifica → `b.auditFlags = []`** (OBRIGATÓRIO esvaziar — re-auditar depois do conserto APAGA o chip; chip preso = bug). ⚠️ **Isso vale para uma passada COMPLETA.** Numa **reaplicação parcial** (ex.: reaplicar só os fixes que o 3.4.1 restaurou) o `report_C` do payload vem vazio de propósito, e esvaziar apagaria os chips legítimos da passada cheia — nesse caso **NÃO toque em `auditFlags`**. Caso real 2026-07-30: uma reaplicação parcial zerou 3 chips já gravados.
  - ⚠️ **Antes de acender `off-niche`, confira se a taxonomia oferece destino** (`docs/painel/taxonomia-biblias.json`). Se o tipo real do produto não existe como subcategoria, o chip não tem como ser resolvido e vira chip preso, que é o bug que esta seção quer evitar. Nesse caso **não acenda**: reporte a lacuna de taxonomia no relatório consolidado, como decisão humana. Caso real 2026-07-30: 4 repetidores de Wi-Fi classificados como `roteadores`, sem `repetidores` na taxonomia — 4 chips insolúveis evitados.
- Write `JSON.stringify(b,null,2)+'\n'`.

⚠ `auditFlags` é o que faz o chip ⚠/🧭/🔍 aparecer no painel (server lê `d.auditFlags`; `_pages/biblias.ts` renderiza). NUNCA inventar flag sem evidência. **`specsAmazon`: wrong-info SÓ por ASIN divergente** (ASIN dentro da ficha ≠ `asin` da bíblia). **Contaminação cross-produto** (texto de um produto GENUINAMENTE diferente — outra marca/modelo — vazado em qualquer campo) também é `'wrong-info'` até re-captura. Mas **atributo capturado errado do PRÓPRIO produto, com ASIN certo, NÃO acende chip nenhum** (nem `wrong-info` nem `review`) — registra em `dadosInconsistentes` e segue; é ruído de captura, não problema.

ℹ️ **Stale agora é por `lastFilledAt`, não por mtime** (regra 2026-06-15): `biblia-status.ts` marca stale quando `lastFilledAt > lastAuditedAt` (re-preenchida depois da auditoria), não comparando mtime do `.md` com `lastModified`. Então a antiga preocupação de "ordem do report vs lastModified" não vale mais — o carimbo `lastAuditedAt` no JSON é a fonte.

### Etapa 4 — Relatório (por bíblia + consolidado)

4.1. **Por bíblia**: `docs/biblias-v2/.audits/<ASIN>-last.md` (formato `biblia-auditar`; painel lê). Lista o que foi **auto-consertado** (A+B, com antes→depois) + os **report-only (C)** pendentes + as **`auditFlags`** gravadas (chip do painel).
4.2. **Consolidado no chat**: tabela por bíblia 🟢/🟡/🔴 + nº consertado + nº report-only. Resumo: X auto-consertadas, Y itens report-only (com o porquê de não dar pra aplicar).
4.3. **Commit dos relatórios** (`.audits/<ASIN>-last.md` tracked) + push + `bash scripts/painel-vps-pull.sh`.

### Etapa 5 — Sync R2 push (SEMPRE — todas levam carimbo)

`bun scripts/sync-biblias-r2.ts --apply --push 2>&1 | tail -5`. Roda sempre: a Etapa 3.6 carimba `lastAuditedAt` em toda bíblia do lote, então TODAS têm algo pra subir (não só as consertadas). Conferir `enviado` (não `recebido`) em cada ASIN do lote.

## Relatório final (consolidado)

- **Auto-consertadas (N)**: por ASIN, lista de A (deleção/formato) + B (reescrita, antes→depois), todas re-auditadas.
- **Revertidas (não convergiram na re-auditoria)**: por ASIN, viraram report-only.
- **Report-only (C)**: por ASIN, o indeterminável + o porquê (frescor/verificação/sem-valor-certo).
- **Puladas** (pendentes de preenchimento) + **Excluídas** (contaminada-hard/sem-dados).
- **Sync R2**: X enviadas / 0 se nada mudou.

## Armadilhas (embutir)

1. **Bíblia só no R2**: sync 0.1 resolve.
2. **Clobber do lastModified**: bump via `toISOString()` SÓ quando aplicou. Sem isso o `--push` vira `recebido`.
3. **NÃO comparar bíblias**: isolamento é a defesa nº1.
4. **Falso-positivo do grep**: "EAN" em `dadosInconsistentes` (campo interno) NÃO é problema; "rita lobo" em 2 produtos da mesma marca NÃO é contaminação. **A regex de duplicação contígua da Etapa 1 (`([a-zA-ZÀ-ÿ\s]{8,40})\1`) casa através de fronteira de palavra e dá falso-positivo em expressão idiomática:** `"guiada passo a passo"` casa como `"a passo "` + `"a passo "` (o "a" final de *guiada* mais *passo a passo*). Antes de "consertar" duplicação, **imprima o trecho e leia** — se as duas cópias começam no meio de uma palavra, é ruído da regex, não do dado. Confirmar contexto antes de aplicar; na dúvida, (C).
5. **Re-auditoria é obrigatória**: nunca dar (B) por aplicado sem o passo 3.5. É ela que substitui sua aprovação.
6. **(C) não é preguiça**: é ausência de valor certo. NUNCA chutar um conserto (C) — flag.
7. **Race de escrita**: sub-agent NUNCA grava; só a skill-mãe (serial).

## Limites de segurança (NUNCA faz)

- Deploy.
- Aplicar (C) (indeterminável) — sempre flag.
- Manter (B) aplicado sem re-auditoria (3.5).
- Tocar campos brutos ou `lastAuthor`.
- Comparar/compartilhar contexto entre bíblias.
- Auditar bíblia pendente (pula) ou contaminada-hard (exclui).

## Disciplina de release

Nasce no project repo. Vai pro marketplace DEPOIS de validada num run real. Padrão: fazer + validar → release (ver `feedback_skill_regua_release_junto`).

## Invocação

```
/biblia-auditar-em-massa B0CH5RSZTP,B01I78MAHW,B093Q7LLD6
/biblia-auditar-em-massa todas
/biblia-auditar-em-massa sub=panela-eletrica
/biblia-auditar-em-massa B0CH5RSZTP --report-only     # só lista, não aplica
```

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
