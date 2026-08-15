---
name: biblia-preencher-em-massa
description: Preenche a curadoria (7 campos) de VÁRIAS bíblias v2 de uma vez, em PARALELO via sub-agents (até 10 simultâneos), cada um isolado na sua bíblia (zero contaminação cruzada). Aceita lista de ASINs OU "todas as pendentes". Exclui contaminadas e sem-dados-brutos do lote. Cada sub-agent LÊ as imagens anexadas (conteudoBrutoFabricanteImagens/doFabricanteImagens) como fonte factual antes de curar. Flag --enriquecer = modo backfill que NUNCA sobrescreve curadoria existente, só acrescenta (obrigatório em bíblia já curada). Sync R2 nas 2 pontas, bump lastModified, backup. Botão roxo "✨ Preencher bíblias" do produtos.html copia o comando pra cá.
---

## Parse de input

Args no `$ARGUMENTS`:
- **Lista de ASINs** (forma do botão do painel): `B0CH5RSZTP,B01I78MAHW,B093Q7LLD6` (vírgula, sem espaço). Cada um `^[A-Z0-9]{10}$`.
- **`todas` / `todas as pendentes`**: varre `docs/biblias-v2/*.json`, pega as `pend` preenchíveis (ver Etapa 0.4).
- **Filtro** (opcional): `niche=Panela Elétrica` ou `sub=panela-eletrica` → restringe o "todas" àquela subcategoria.
- **`RETOMAR=yes`** (opcional): invocação nascida do heartbeat; re-arme, re-rode a Etapa 0 (idempotente) e dispare só o que falta (ver Invariantes → Turno vivo).
- **`--enriquecer`** (opcional, mas **OBRIGATÓRIO pro backfill das 216**): liga o modo enriquecer da `biblia-preencher` em TODOS os sub-agents. **Nesse modo nenhum campo curado existente é sobrescrito — só se ACRESCENTA.**

> ⚠️ **PERIGO — leia antes de rodar batch em bíblia já curada.** O fluxo normal desta skill **REESCREVE os 7 campos**. As **216 bíblias com imagem anexada já têm curadoria escrita** (foi feita sem ler as imagens, que é o motivo do backfill existir). Rodar o batch nelas **sem `--enriquecer` destrói curadoria boa em massa.** A Etapa 0.4 filtra "pendentes" justamente pra não pegar essas — mas se o alvo vier por lista explícita de ASINs, esse filtro não protege. **Regra: alvo que já tem curadoria ⇒ `--enriquecer` obrigatório.** Com a flag, o prompt do sub-agent manda seguir a seção "Modo `--enriquecer`" da `biblia-preencher` (acrescenta fato ausente, manda contradição pra `dadosInconsistentes` sem reescrever, marketing pra `angulosConversao`, e carimba `imagensVerificadasEm` mesmo quando não achou nada).

# Preencher curadoria de bíblias em massa (paralelo via sub-agents)

> Esta skill é **orquestrador leve**. A curadoria real (os 7 campos) é feita por sub-agents independentes, **um por ASIN**, cada um seguindo a régua canônica do `biblia-preencher` (a fonte editorial é aquela skill + `docs/painel/_data/regras-biblia.md`). Esta skill NÃO reimplementa a régua — ela fan-out + escreve + sincroniza. Análoga à `pagina-produto-criar-em-massa`, mas pra bíblia em vez de página.

## Modelo

Opus 5 (ou o Opus mais novo disponível). Sub-agents fixados com `model: opus` no Agent tool. NUNCA Sonnet/Haiku (régua do projeto: skills sempre Opus).

## ⚠️ Playbook anti-contaminação (o coração desta skill)

Preencher bíblia em massa é estruturalmente MAIS seguro que clonar artigo, porque **não há etapa comparativa** (cada bíblia é destilada só dos próprios dados brutos, sem justaposição de produtos — o brand-swap do clone vinha do guia/lineup, que aqui não existe). Os guards abaixo garantem isso:

1. **Isolamento estrito.** 1 sub-agent por ASIN, conversa fresh, vê **SÓ** os dados brutos daquela bíblia. NUNCA um prompt com várias bíblias, NUNCA contexto compartilhado entre itens. (É o mecanismo nº1 — mesma lógica "conversa fresh, isolada, sem cross-contamination" da `pagina-produto-criar-em-massa`.)
2. **Sub-agent RETORNA JSON; a skill-mãe ESCREVE.** Nada de sub-agent gravando arquivo (evita race). A skill-mãe grava serialmente, chaveando por ASIN.
3. **Trava de ASIN.** O sub-agent devolve o `asin` no JSON. A skill-mãe **confere `asin_retornado == asin_pedido` ANTES de gravar**. Mismatch → descarta aquele resultado, re-dispara (pega qualquer mix-up A→B).
4. **Exclusão na entrada (Etapa 0.4):** bíblia **contaminada** (`contaminado: true` no painel = `check-contamination.ts` com hard issue tipo `cross-brand-mention`) **NÃO entra no lote** — preencher com info de outro produto propaga o erro. Vai pra lista "corrigir à mão antes" (a singular `biblia-preencher` tem o tratamento por-campo + revisão humana). Idem bíblia **sem dados brutos** (nada pra destilar).
5. **Post-check de leak por bíblia (Etapa 2.5):** a curadoria gravada não pode citar **nome/marca/modelo de OUTRO produto do lote**. Se vazar → flag no relatório + não grava aquele (re-dispara isolado).
6. **Gate opcional `--audit`:** encadeia a `biblia-auditar-em-massa` no lote (camada mecânica auto-conserta resíduo de régua: voz-comprador, travessão, `<strong>` vazado; camada de julgamento vira flag pro humano). É o fluxo "preencheu → audita automático".

## Invariantes

- **NUNCA preenche bíblia `contaminado`** (hard) nem sem dados brutos — exclui na Etapa 0.4, lista no relatório.
- **NUNCA compartilha contexto entre bíblias** (Etapa 1) — isolamento é a régra dura.
- **`lastModified` E `lastFilledAt` bumpados via `new Date().toISOString()`** ao gravar (UTC real); NUNCA `lastAuthor`, NUNCA hand-roll via getHours/pad (armadilha de timezone). Sem o bump do `lastModified`, o pull do R2 CLOBBERA o edit. O `lastFilledAt` é o carimbo de re-preenchimento (painel marca "auditar de novo" via `lastFilledAt > lastAuditedAt`; regra Marcelo 2026-06-15).
- **Sync R2 nas 2 pontas**: pull no começo (as bíblias cruas podem estar SÓ no R2 — caso real: lote de panela elétrica criado no painel, ausente no Mac local), push no fim (uma vez, batch).
- **Idempotente**: pula bíblia já preenchida (coreDone) — re-rodar o lote não retrabalha.
- **Full-auto, sem checkpoint humano** (igual aos outros em-massa, canon 24/07 e 15/08): o pré-flight (Etapa 0) é a barreira; passou → imprime o plano como notificação e **dispara na MESMA mensagem** (não pergunta S/N — era a única em-massa que ainda perguntava). Cap de segurança: lote > 30 bíblias ou custo estimado incomum → aí sim confirma antes.
- **Turno vivo (canon 15/08)**: sub-agents em primeiro plano (`run_in_background: false`, N `Agent()` no mesmo bloco); heartbeat `ScheduleWakeup(1800, prompt="/biblia-preencher-em-massa {os MESMOS args} RETOMAR=yes")` como passo 0.0; ao acordar re-arme, re-rode a Etapa 0 (é idempotente: coreDone/já carimbada pula) e dispare só o que falta; `ScheduleWakeup(stop:true)` antes do relatório final e no aborto; sub-agent morto → refaz inline no mesmo turno; nunca "te aviso quando voltar".
- **NÃO faz deploy** (bíblia não é deployada; ela sincroniza R2).
- **Cap de paralelismo: 10 sub-agents** simultâneos. Acima → levas (10 + 10 + ...).
- **Português brasileiro editorial**, régua do `biblia-preencher` (sem travessão, sem superlativo absoluto, chavões por nicho, health YMYL, não-inventar).

## Pipeline

### Etapa 0 — Pré-flight (auto; aborta/exclui cedo)

0.1. **Sync R2 pull** (CRÍTICO — as bíblias do lote podem estar só no R2):
   ```bash
   bun scripts/sync-biblias-r2.ts --apply 2>&1 | tail -3
   ```
   `--apply` sem `--push` é pull-only (seguro). Se falhar (offline/creds), seguir mesmo assim — mas avisar que ASINs ausentes localmente vão pular.

0.2. **Parse** dos ASINs (ou expandir `todas`/filtro). Validar `^[A-Z0-9]{10}$`.

0.3. **Carregar cada bíblia** (`docs/biblias-v2/<ASIN>.json`). Ausente local (mesmo após sync) → pular + listar.

0.4. **Classificar cada uma** (decide quem entra no lote):
   - **Já preenchida** (`angulosConversao` + `pontosFortes` + `pontosFracos` todos não-vazios = coreDone) → **PULA** (idempotência) — **EXCETO no modo `--enriquecer`**, cujo alvo são justamente as coreDone: aí a chave é `imagensVerificadasEm` — ausente, ou anterior à última mudança da lista de imagens (`conteudoBrutoFabricanteImagens`/`doFabricanteImagens`) → **ENTRA**; presente e atual → PULA. Sem esta regra o lote enriquecer não processa ninguém (bug até 15/08).
   - **Sem dados brutos** (todos vazios: `sobreEsteItem`/`doFabricante`/`specsAmazon`/`opinioesCompradores`/`descricaoProduto`) → **EXCLUI** + lista "sem matéria-prima, capturar antes".
   - **Contaminada** — roda `bun scripts/check-contamination.ts <ASIN>`; se `hasContamination: true` com hard issue (`cross-brand-mention`) → **EXCLUI** + lista "informações erradas, corrigir à mão (biblia-preencher individual)".

   **Comportamento real hoje:** os três tipos são `hard` e EXCLUEM, com duas saídas condicionais:
   - **`brand-mismatch` vira soft** se `identidade.confirmadoPelaEditora === true` (canon 2026-07-26). É a saída projetada pra co-branding e submarca. Casos reais: Tapo é linha da TP-Link (o próprio `urlFabricante` é `tp-link.com/br/.../tapo`), Multi Saúde é do grupo Multilaser (`urlFabricante` é `multilaser.com.br`). **Confirme pela evidência dentro da bíblia, não por conhecimento de mundo.** Não há UI pro campo — hoje é edição manual.
   - **`asin-mismatch` vira soft** quando o modelo bate e não há ambiguidade de voltagem (`irmaoBenigno`): é relistagem, não produto trocado. Com voltagens conflitantes ou modelo diferente, continua hard e pede recaptura.

   Manter `hard` como bloqueio é a decisão certa: `brand-mismatch` PODE ser ficha capturada de outra marca, e admitir todas automaticamente deixaria spec errada ser curada como se fosse do produto.
   - **Preenchível** (pend + tem dado bruto + não-hard-contaminada) → **ENTRA no lote**.

0.5. **Imprimir o plano** (tabela ASIN, nome, ENTRA/PULA/EXCLUI + motivo, nº no lote, estimativa ~1-3 min/leva) **e disparar na mesma mensagem** — sem `S/N` (canon 24/07: o pré-flight é a barreira). Defina `RUN` = `<scratchpad>/biblia-lote-{YYYYMMDD-HHMM}` e crie `RUN/payloads/` e `RUN/antes/`.

0.6. **Snapshots `-antes.json` (OBRIGATÓRIO — sem eles o aplicador REPROVA tudo).** Pra cada ASIN que ENTRA: `cp docs/biblias-v2/{ASIN}.json RUN/antes/{ASIN}-antes.json`. O `biblia-aplicar.ts` exige o snapshot pra guarda de não-perda e de ASIN (`sem snapshot -antes.json` = REPROVADA, e reprovada não é gravada). Até 15/08 este passo não existia na skill.

### Etapa 1 — Geração (sub-agents paralelos, ISOLADOS)

N sub-agents Opus, levas de ≤10. Cada sub-agent (Agent tool, `model: opus`, conversa fresh):
- **Input + régua (FONTE ÚNICA, não resumo)**: cole no prompt SÓ os DADOS (o ASIN + o conteúdo bruto daquela bíblia / JSON). A **régua dos 7 campos NÃO é colada** — o prompt manda o sub-agent **LER `.claude/skills/biblia-preencher/SKILL.md` à risca** (estrutura de cada campo + invariantes PT-BR + armadilhas + destilação) **+ `docs/painel/_data/chavoes-por-nicho.json`** (`_genericos` + bloco do nicho) e aplicar essa régua VIVA. Resumo inline de régua = proibido (evita drift; sub-agent não invoca Skill tool, então LÊ o arquivo — mesma fonte única da `pagina-produto-criar-em-massa` e da clone).
- **⚠ IMAGENS ANEXADAS: passar as URLs no prompt (canon 2026-07-26).** A etapa 2.5 da individual manda **ler** `conteudoBrutoFabricanteImagens` e `doFabricanteImagens` antes de gerar qualquer campo. Isso só funciona no batch se o sub-agent tiver como abrir: **cole as URLs das imagens no prompt** (elas estão no JSON que você já cola, mas explicite que ele DEVE baixá-las) e diga que ele pode `curl` + `sips -Z 1400` + `Read`. Sem isso o sub-agent gera a curadoria só com os campos de texto — exatamente o buraco que gerou 216 bíblias curadas sem ninguém abrir uma imagem. **Se a bíblia tem `imagensVerificadasEm` e a lista de imagens não mudou, avise no prompt que já foram lidas** (evita rebaixar 731 imagens a cada batch).
- **Tarefa**: gerar os 7 campos de curadoria (`sentimentoCompradores`, `angulosConversao`, `pontosFortes`, `pontosFracos`, `dicasAcionaveis`, `dadosInconsistentes`, `observacoesAgente`) + (se houver ruído) o `conteudoBrutoFabricante` limpo. Destilar SÓ dos dados daquela bíblia, sem inventar, sem copiar verbatim.
- **NÃO descreva o produto no prompt.** Passe o ASIN e mande ler a bíblia. Caso real 2026-07-30: o orquestrador escreveu "notebook VAIO" num prompt e o produto era um **tablet** — o agente leu a bíblia e não propagou, mas isso foi sorte, não desenho. Descrição de produto escrita pela mãe é contexto factual que ela redige vendo todos os N ao mesmo tempo, exatamente o vetor que o isolamento existe pra fechar.
- **Anti-contaminação no prompt**: "Você vê SÓ este produto. NÃO mencione nenhum outro produto/marca/modelo que não seja o deste ASIN. Comece o JSON com `\"asin\": \"<ASIN>\"`."
- **⚠ RECONCILIAÇÃO, no modo `--enriquecer` (canon 2026-07-30)**: o objetivo é bíblia **mais completa E ainda confiável**, não só maior. Ponha isto no prompt, porque **isolamento não resolve** (o agente sozinho não sabe que o banner é institucional nem que aquela decisão editorial ficou obsoleta) e **não há check mecânico** pra parte semântica:
  > "Antes de escrever, LEIA os `dadosInconsistentes` que já existem nesta bíblia. Se o rótulo/imagem **contradiz um claim curado e dá o valor certo**, CORRIJA o claim e mova o texto anterior, literal, pra `dadosInconsistentes`. Se contradiz mas **não há valor único** (ex.: duas comparações com bases diferentes, ambas verdadeiras), só registre — não invente conserto. E verifique se alguma `decisaoEditorial` existente ficou **obsoleta** com o dado novo: se ficou, marque como SUPERADA (ou ATUALIZADA, se a obsolescência for parcial) preservando o texto anterior dentro dela. Uma decisão antiga vigente que mande o contrário do conserto desfaz a correção na hora de escrever o review."

  A régua completa, com os casos reais (Kimera, Lavitan, Sustagen), está na seção **Reconciliação** da `biblia-preencher/SKILL.md`, que o sub-agent já lê como fonte única.
- **GRAVA O PRÓPRIO PAYLOAD EM ARQUIVO (canon 2026-07-30)** e devolve só um recibo curto (`{asin, arquivo, itens_por_campo}`). Caminho: `RUN/payloads/{ASIN}.json` (o `RUN` definido no 0.5), um arquivo por ASIN, nome derivado do ASIN; o payload inclui `imagensLidas` (o aplicador lê esse campo).
  **Isto NÃO afrouxa o guard nº2.** A proibição existe contra **race no arquivo da bíblia**, e ela continua integral: nenhum sub-agent toca `docs/biblias-v2/`, a escrita da bíblia segue serial e só na mãe, e o sync R2 não enxerga o scratchpad. O que muda é que o orquestrador **para de redigitar** o JSON pra conseguir gravá-lo — redigitação é a maior categoria de geração da mãe e é caminho de contaminação (ela vê os N produtos ao mesmo tempo).
  Ganhos colaterais: a trava de ASIN vira **dupla** (nome do arquivo × campo do payload), e JSON inválido vira falha de parse determinística — a resposta certa passa a ser **re-disparar o sub-agent isolado**, não o orquestrador remendar curadoria à mão.
- **ESCREVE O PRÓPRIO RELATÓRIO** em `docs/biblias-v2/.audits/<ASIN>-fill-last.md` (**não** `<ASIN>-last.md`: esse é o relatório de AUDITORIA que o painel exibe e usa como fallback de `auditedAt` — server.ts 502/670/818; um relatório de preenchimento ali sobrescreve o último audit e "carimba" auditoria que não houve). Mesma razão: escrever N relatórios de N produtos numa geração só é o momento de maior risco de cruzamento de contexto do pipeline. A mãe escreve zero relatório.
- **Retorna**: SÓ o recibo `{asin, arquivo, itens_por_campo}`. O JSON completo `{ asin, sentimentoCompradores, angulosConversao, pontosFortes, pontosFracos, dicasAcionaveis, dadosInconsistentes, observacoesAgente, imagensLidas, conteudoBrutoFabricanteLimpo?, correcoes? }` (`correcoes` = `[{campo, antes, depois, motivo}]` pra guarda (b)) vai no ARQUIVO do payload, não na resposta.

### Etapa 2 — Escrita (skill-mãe, SERIAL, chaveada por ASIN)

Pra cada JSON retornado:
2.1–2.3 e 2.5 **são feitas PELO SCRIPT da 2.4**, não à mão. Ele faz trava de ASIN (dupla), backup no padrão canônico, merge dos 7 campos, bump de `lastModified`/`lastFilledAt` sem tocar `lastAuthor`, e o write. Estão descritas aqui só para você saber o que ele garante — **não as reexecute por fora**, senão você grava duas vezes e o backup da segunda já é do estado novo.

2.4. **RODAR O APLICADOR VERSIONADO — não reimplementar as guardas (canon 2026-07-30).**

   ```bash
   bun scripts/biblia-aplicar.ts RUN/payloads RUN/antes [--imagens] [--dry-run]
   ```
   **`--imagens` é OBRIGATÓRIO no modo `--enriquecer`/backfill de imagem**: é a única forma de o script carimbar `imagensVerificadasEm` (biblia-aplicar.ts:80/252). Sem a flag, a bíblia não sai do backlog e o próximo run refaz tudo.

   O script faz backup, aplica, carimba e roda TODAS as travas. Exit 1 se alguma bíblia reprovar, e **reprovada não é gravada**. Rode `--dry-run` antes em lote grande.

   ⛔ **NÃO reescreva essas guardas inline.** Elas viviam como snippet aqui pra ser redigitado a cada execução, e em 2026-07-30 o orquestrador as reimplementou 5 vezes num dia e **errou 4**: comparou `angulosConversao` por hash do objeto (acrescentar frase lia como perda), comparou o `nome` inteiro no leak-check (reprovou 3 de 5 por "biotina"/"vitamina"), comparou contra `JSON.stringify` (aspas internas viram `\"` e o substring falha), e só preservou o que o agente declarava. **A régua aqui estava certa nas 4 vezes; o erro foi a reimplementação.** Guarda que precisa ser redigitada não é trava.

   O que o script garante, e por quê:

   | trava | por quê |
   |---|---|
   | **trava de ASIN dupla** (nome do arquivo + campo do payload + snapshot) | com payload em arquivo dá pra checar os dois; antes existia só a comparação |
   | **(a) 3 chaves em `dadosInconsistentes`** | sem `decisaoEditorial` a bíblia é **revertida no R2 em silêncio** — o push responde `enviado / 0 falhas` e 1-2 min depois o remoto voltou. Foi diagnosticado como "escrita concorrente" antes de acharem a causa |
   | **(b) não-perda, consciente do shape** | `angulosConversao` é `{tema, frases[]}` e compara **por frase**; o resto por item, sempre contra **texto cru** (nunca `JSON.stringify`) |
   | **(b.2) rastro das correções declaradas** | `correcoes` é payload de transporte e **não persiste** na bíblia |
   | **(b.3) arquivamento por construção** | o agente só declara o que percebeu que mudou; item reescrito sem declaração é arquivado em `observacoesAgente` e **contado no relatório**, em vez de virar reprovação |
   | **leak-check por marca+modelo** | o `nome` carrega categoria e ingrediente, que aparece legitimamente no nicho todo |
   | **(c) não carimbar quando reprovar** | carimbo em falha tira a bíblia do backlog em silêncio e, como manda toda execução futura pular, torna o erro permanente |
   | **guarda de schema pós-write** | baseline em memória, não o backup (numa reaplicação o backup já é do estado corrompido); divergiu → restaura |
   | **backup `{ASIN}-v2-{HHMMSS}.json`** | sufixo inventado some da UI de restore do painel (210 de 459 invisíveis por isso) |

   ⚠️ **REPROVAÇÃO DE GUARDA NÃO É SINAL DE DADO RUIM ATÉ SER INVESTIGADA.** Nos 4 casos de 2026-07-30 o dado estava bom e a guarda é que estava torta. Reprovar sempre **bloqueia a escrita**, então falso positivo custa retrabalho, nunca dado corrompido. **Investigue antes de "consertar" o dado pra guarda passar** — esse conserto é que quebra a bíblia. Se a guarda estiver errada, conserte o script e re-rode.

2.6. **Reler do R2 ~60s depois do push.** `enviado` **não é prova** (ver guarda (a)). Confirme que `imagensVerificadasEm` está lá de verdade. Se a reversão atingir sempre o MESMO conjunto de bíblias, é invalidez de schema, não concorrência — não saia acusando escritor concorrente, e note que `lastAuthor` é campo de CONTEÚDO (os scripts de sync nunca o tocam), então ele não identifica quem fez o upload.

### Etapa 2.5 — Post-check de leak (auto)

Pra cada bíblia gravada: a curadoria (todos os 7 campos serializados) não pode conter `identidade.nome`/`marca`/`modelo` de **outra bíblia do lote**. Se contiver → flag "⚠ possível leak de <outro ASIN>", reverte do backup, re-dispara aquele isolado (máx 2x). Não-convergiu → deixa o backup e flag no relatório (não esconde).

### Etapa 3 — Sync R2 push (uma vez, batch)

```bash
bun scripts/sync-biblias-r2.ts --apply --push 2>&1 | tail -5
```
Conferir que as linhas dos ASINs do lote dizem `enviado`/`local mais novo`, NÃO `recebido` (com o bump do lastModified o push vence). Se vier `recebido` em algum → o pull clobberou (timestamp não bumpado): re-aplicar o bump + re-push.

### Etapa 4 — Audit encadeado (`--audit`)

Se `--audit` no args: encadeia a `biblia-auditar-em-massa` no MESMO lote recém-preenchido (o fluxo "preencheu → audita e conserta automático, com qualidade"). Escopo = FATO + DADO LIMPO + NAMING (voz editorial como travessão/muleta é do review, NÃO da bíblia). Ela:
- **Auto-aplica** conserto de direção CONHECIDA — lixo de dado (strip `<strong>`/HTML na curadoria, caractere invisível/BOM, espaço duplo, marca duplicada) E reescrita/correção conhecida (voz-comprador→observação analítica, contradição contra a própria `decisaoEditorial`, fonte errada, claim que contradiz o bruto). **Caso real do 1º lote: `<strong>` em `pontosFortes` e crava-de-número contra a decisaoEditorial — é o que isto fecha.**
- **Re-audita cada conserto** (resolveu? não quebrou? não mudou sentido?; não convergiu em ≤3 → reverte do backup + vira flag). Substitui a aprovação humana = mesma qualidade da individual.
- **Report-only** pro indeterminável (frescor, verificação externa, contradição no bruto sem valor certo, naming que precisa de decisão).

Default sem `--audit`: não audita (mas é o passo recomendado). A delegação reusa a `biblia-auditar-em-massa` inteira — esta skill NÃO reimplementa a auditoria.

### Relatório final

- **Preenchidas** (N): por ASIN, quantos itens por campo, alertas (campo vazio por falta de dado).
- **Puladas** (já preenchidas): lista.
- **Excluídas**: contaminadas (corrigir à mão) + sem-dados-brutos (capturar antes) — com motivo.
- **Leaks pegos** (Etapa 2.5): se houver, quais.
- **Sync R2**: X enviadas / Y recebidas (esperado: todas enviadas).
- **Próximo passo**: revisar no editor-v2 / rodar `biblia-auditar-em-massa <asins>` (ou `--audit` na próxima vez) se não auditou agora.

## Armadilhas (embutir)

1. **Bíblia só no R2** (não no Mac): o sync 0.1 resolve; sem ele, "bíblia não encontrada" pra ASINs criados no painel por outra pessoa. Caso real: lote de panela elétrica.
2. **Clobber do lastModified**: bump via `toISOString()` (UTC real). Sem isso o `--push` vira `recebido` e o edit some. NUNCA hand-roll timestamp (timezone bug 2-3h no futuro).
3. **Contaminação na ENTRADA**: o guard nº4 exclui hard-contaminadas; o resto é isolamento puro. NÃO tente "comparar" bíblias pra divergir — criação escreve livre (ver `afiliados.regras.criacao-escreve-livre-dedup-no-audit`).
4. **Race de escrita**: sub-agent NUNCA grava; só a skill-mãe (serial). Senão 2 sub-agents podem tocar o mesmo arquivo / o sync no meio.
5. **Régua residual**: mesmo isolado, sub-agent vaza voz-comprador/travessão às vezes — o `--audit` (ou `biblia-auditar` depois) é o gate.

## Limites de segurança (NUNCA faz)

- Deploy (bíblia não deploya).
- Preencher bíblia hard-contaminada (exclui).
- Tocar `lastAuthor` ou campos brutos não-curados.
- Compartilhar contexto entre bíblias.

## Invocação

```
/biblia-preencher-em-massa B0CH5RSZTP,B01I78MAHW,B093Q7LLD6
/biblia-preencher-em-massa todas as pendentes
/biblia-preencher-em-massa sub=panela-eletrica --audit
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
