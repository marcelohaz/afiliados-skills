---
name: biblia-auditar-em-massa
description: Audita VÁRIAS bíblias v2 de uma vez, cada uma ISOLADA (zero contaminação cruzada, SEM passada comparativa entre bíblias). Duas camadas — (1) MECÂNICA por grep, AUTO-CONSERTA só deleção/formato (strip de HTML na curadoria, remover "declarado pelo fabricante", capitalização, typo de concordância, duplicação, travessão→vírgula): determinístico, sem reescrita; (2) tudo que exige REESCRITA ou decisão (voz-comprador, contaminação-cruzada/termo técnico, superlativo absoluto, spec ambiental/origem) + os factuais via sub-agents Opus read-only (≤10) das 5 categorias da biblia-auditar — vira FLAG no relatório, NÃO auto-aplica (preserva o propor→aprovar da individual = mesma qualidade). Aceita lista de ASINs, niche=/sub=, ou "todas". Relatório consolidado 🟢/🟡/🔴 + .audits/<ASIN>-last.md por bíblia. Sync R2 nas 2 pontas. Botão "🔍 Auditar bíblias" do produtos.html copia o comando pra cá.
---

## Parse de input

Args no `$ARGUMENTS`:
- **Lista de ASINs** (forma do botão do painel): `B0CH5RSZTP,B01I78MAHW,B093Q7LLD6` (vírgula, sem espaço). Cada um `^[A-Z0-9]{10}$`.
- **`todas`**: varre `docs/biblias-v2/*.json`, pega as **preenchidas** (coreDone) auditáveis (ver Etapa 0.4).
- **Filtro** (opcional): `niche=Panela Elétrica` ou `sub=panela-eletrica` → restringe o "todas" àquela subcategoria.
- **Flag `--fix-only-mecanico`** (default ligado): a camada mecânica auto-conserta; a LLM só reporta. Esse é o comportamento padrão e recomendado (ver "Garantia de qualidade"). NÃO existe modo "auto-aplicar achado de julgamento" — por design.

# Auditar bíblias em massa (paralelo via sub-agents, isolado)

> Esta skill é **orquestrador leve**. A auditoria real (as 5 categorias) é a régua canônica do `biblia-auditar` (fonte editorial: aquela skill + `docs/painel/_data/regras-biblia.md`). Esta skill NÃO reimplementa a régua — ela fan-out + camada mecânica grep + consolida + sincroniza. Análoga à `biblia-preencher-em-massa`, mas pra auditar em vez de preencher.

## O que esta skill É (e não é)

- **É** o auditor em massa: roda em N bíblias **já preenchidas**, cada uma isolada, e entrega triagem consolidada.
- **NÃO é** auto-corretor de julgamento. A camada mecânica conserta o **determinístico** (travessão, HTML, termo banido — onde não há o que julgar); os achados de **julgamento** (claim factual, contradição, frescor) **viram flag no relatório**, NUNCA são aplicados em silêncio. O conserto de julgamento é da `biblia-auditar` individual (propor→aprovar) nas bíblias que a triagem apontar.
- **NÃO é a IA do painel** (botão "✨ Auditar"). Roda na assinatura (Claude Code), Opus 4.8.

## Garantia de qualidade (igual à individual)

A `biblia-auditar` individual é **propor→aprovar**: você aprova cada conserto, e essa aprovação faz parte da qualidade. Esta skill preserva isso separando achado por tipo. **A linha divisória é REESCRITA: o que se conserta por DELEÇÃO ou FORMATO (sem reescrever prosa) é auto-aplicável; o que exige reescrever o texto é julgamento → flag.**

| Tipo | Exemplos | Ação | Por quê é seguro |
|---|---|---|---|
| **Auto-fixável (deleção/formato puro)** | strip de HTML/`<strong>` na curadoria; remover "declarado pelo fabricante"/"declarados" (parentético); capitalizar 1ª letra de bullet; typo de concordância (mapa fixo, ex: `composiçãos`→`composições`); duplicação contígua; travessão→vírgula | **auto-conserta** | não há reescrita nem escolha de sinônimo: é apagar/normalizar. Auto-aplicar = exatamente o que você aprovaria 100% das vezes. Só eleva a qualidade. |
| **Julgamento (exige REESCRITA ou decisão)** | voz-comprador implícita ("um comprador relata X" → prosa analítica); "contaminação cruzada" / termo técnico-industrial → linguagem editorial; superlativo absoluto → qualificado; spec ambiental/origem nos curados (remover ou manter por ângulo?); + os factuais: claim-vs-bible, contradição interna, frescor, verificação externa | **flag no relatório, NÃO aplica** | reescrever prosa ou decidir é julgamento. As MESMAS decisões chegam até você — num relatório no fim, em vez de inline. Você resolve com a `biblia-auditar` individual nas marcadas. |

Resultado: **mesma qualidade final** da individual. O que é deleção/formato sai consertado; o que exige reescrita ou decisão chega pra você. **Nada que precise de reescrita é alterado em silêncio** (era exatamente a regressão de qualidade a evitar).

## Modelo

Opus 4.8 (ou mais novo). Sub-agents fixados com `model: opus` no Agent tool. NUNCA Sonnet/Haiku.

## ⚠️ Playbook anti-contaminação (o coração desta skill)

Auditar em massa é estruturalmente AINDA MAIS seguro que preencher, porque:

1. **A maior parte é grep, não IA.** A camada mecânica (Etapa 1) é busca de texto determinística — **zero LLM, zero chance de contaminação**.
2. **Auditar lê, não cria.** A contaminação do preencher vinha do risco de a IA *escrever* a spec de um produto na bíblia de outro. Auditar só **confere** o que já está lá — não há o momento de "escrever do zero".
3. **Isolamento estrito.** 1 sub-agent por bíblia, conversa fresh, vê **SÓ** aquela bíblia. NUNCA um prompt com várias bíblias, NUNCA contexto compartilhado.
4. **SEM etapa comparativa entre bíblias.** O único vetor de contaminação seria a IA **comparar uma bíblia com outra**. **Esta skill NÃO faz isso** — cada bíblia é julgada só contra os próprios dados brutos + a régua. Sem justaposição = sem confusão. (Lembrete: "rita lobo" aparecendo em 2 Electrolux NÃO é contaminação — cada bíblia tirou isso dos próprios dados; veja `afiliados.regras.criacao-escreve-livre-dedup-no-audit`.)
5. **Conserto serial, 1 arquivo por vez.** A camada mecânica edita bíblia por bíblia, chaveada por ASIN (igual a Etapa 2 do preencher). Sem race de escrita.
6. **Trava de ASIN.** O sub-agent devolve o `asin` no JSON; confere `asin_retornado == asin_pedido` antes de usar o resultado.

## Invariantes

- **NUNCA aplica achado de JULGAMENTO** (factual/contradição/frescor/verificação). Esses são report-only — vão pro relatório, o humano resolve na `biblia-auditar` individual.
- **Camada mecânica só toca CAMPOS CURADOS** (`sentimentoCompradores`, `angulosConversao`, `pontosFortes`, `pontosFracos`, `dicasAcionaveis`, `dadosInconsistentes`, `observacoesAgente`). **NUNCA edita campos BRUTOS** (`sobreEsteItem`, `doFabricante`, `descricaoProduto`, `specsAmazon`, `conteudoBrutoFabricante`) nem `lastAuthor`.
- **`lastModified` bumpado via `new Date().toISOString()`** SÓ quando a camada mecânica aplicou algo (UTC real). NUNCA hand-roll via getHours/pad (armadilha de timezone). Se não consertou nada numa bíblia, NÃO toca lastModified dela (senão push desnecessário).
- **NUNCA compartilha contexto entre bíblias** (Etapa 2) nem faz passada comparativa — isolamento é a regra dura.
- **Só audita bíblia PREENCHIDA** (coreDone). Pendente → pula com aviso "preencha primeiro" (use `biblia-preencher-em-massa`). Contaminada-hard → exclui (corrigir à mão via `biblia-auditar` individual). Sem-dados-brutos → exclui.
- **Sync R2 nas 2 pontas**: pull no começo (bíblias podem estar só no R2), push no fim SÓ se a camada mecânica aplicou fixes.
- **Full-auto, sem checkpoint humano no meio.** Confirmação só ANTES do disparo (lista + estimativa).
- **NÃO faz deploy** (bíblia não é deployada).
- **Cap de paralelismo: 10 sub-agents** simultâneos. Acima → levas.
- **Nunca inventa achados.** Categoria sem problema = "nenhum". Toda flag precisa de evidência (trecho literal < 15 palavras).

## Pipeline

### Etapa 0 — Pré-flight (auto; aborta/exclui cedo)

0.1. **Sync R2 pull** (CRÍTICO):
   ```bash
   bun scripts/sync-biblias-r2.ts --apply 2>&1 | tail -3
   ```
   `--apply` sem `--push` é pull-only (seguro). Se falhar (offline/creds), seguir mesmo assim — avisar que ASINs ausentes localmente vão pular.

0.2. **Parse** dos ASINs (ou expandir `todas`/filtro). Validar `^[A-Z0-9]{10}$`.

0.3. **Carregar cada bíblia** (`docs/biblias-v2/<ASIN>.json`). Ausente local (mesmo após sync) → pular + listar.

0.4. **Classificar cada uma** (decide quem entra no lote):
   - **Pendente** (NÃO coreDone: `angulosConversao`/`pontosFortes`/`pontosFracos` algum vazio) → **PULA** + lista "preencha primeiro (biblia-preencher-em-massa)".
   - **Contaminada-hard** — roda `bun scripts/check-contamination.ts <ASIN>`; se `hasContamination: true` com hard issue (`cross-brand-mention`) → **EXCLUI** + lista "informações erradas, corrigir à mão (biblia-auditar individual)". (Auditar em massa não conserta julgamento, e contaminação hard é exatamente julgamento.)
   - **Sem dados brutos** (todos vazios) → **EXCLUI** + lista "sem matéria-prima".
   - **Preenchida + não-hard-contaminada** → **ENTRA no lote**.

0.5. **Mostrar o plano + confirmar**: tabela (ASIN, nome, ENTRA/PULA/EXCLUI + motivo) + nº no lote + estimativa (~1-3 min/leva). Pergunta `S/N` antes do paralelo.

### Etapa 1 — Camada MECÂNICA (grep determinístico, sem IA)

Pra cada bíblia do lote, rode um scan determinístico nos **campos curados** (serializados) e nos campos editoriais. Pega o resíduo de régua (o que o preenchimento em massa às vezes deixa). Sem LLM = sem custo, sem contaminação. Padrões (régua canônica `regras-biblia.md` + `biblia-auditar`), divididos por destino:

**(A) AUTO-FIXÁVEL — deleção/formato puro, a Etapa 3 aplica:**
- **HTML na curadoria**: qualquer `<\w+[^>]*>` (ex: `<strong>`) em texto de campo curado → **strip da tag** (curadoria é TEXTO PURO; caso real do lote de panela: `<strong>` vazou em `pontosFortes`).
- **Muleta de fabricante**: `declarado pelo fabricante`, `declarados` (parentético) → **deletar a expressão** (o mg/spec já é fato sem ela).
- **Travessão** `—`/`–` em campo curado → **trocar por vírgula**. Se estiver em fronteira de sentença (maiúscula depois, ou fim de frase), é ambíguo (podia ser ponto/dois-pontos) → **NÃO auto-troca, vira flag**.
- **Concordância PT-BR** (mapa fixo): `composiçãos`→`composições`, `combinaçãos`→`combinações`, `porçãos`→`porções`, `a produto`→`o produto`, `o fórmula`→`a fórmula`, `o dose`→`a dose`, `disponíveis no em 2026`→`disponíveis em 2026`.
- **Capitalização**: bullet de array editorial (`pontosFortes`/`pontosFracos`/`dicasAcionaveis`) começando minúsculo → maiúscula na 1ª letra.
- **Duplicação contígua** `([a-zA-ZÀ-ÿ\s]{8,40})\1` → remover a 2ª cópia.

**(B) FLAG (exige REESCRITA ou decisão) — vai pro relatório, a Etapa 3 NÃO aplica:**
- **Voz-comprador implícita**: `opiniões`, `comentários`, `um comprador relata`, `divide opiniões`, `avaliações` (sentido Amazon), `elogiado nas opiniões`, `recepção [mista/dividida]`, `queixa recorrente`. (Nuance: em `sentimentoCompradores` a destilação "é recorrente"/"é citado" é OK; flag só voz-comprador CRUA.) → exige reescrever a frase.
- **Termo técnico-industrial / banido**: `contaminação cruzada`, `linha de produção compartilhada`, `peers`, `claim`, `stack`, `trade-off`, `hardcore`, `datasheet`, `SKU`, `ASIN`, `UPC`, `EAN`, `notificado`, `calibrar/calibrada/calibragem`, `empilhar`, `energia metabólica/adrenérgica` → exige sinônimo/reescrita no contexto.
- **Superlativo absoluto**: `o melhor`, `o mais \w+` sem qualificador, `o único`, `imbatível`, `incomparável` → exige qualificar. (Qualificadores positivos "excelente/ótimo" NÃO são flag; "o mais leve da categoria" é qualificado → OK.)
- **Spec ambiental nos curados**: `plástico reciclado`, `Energy Star`, `EPEAT`, `RoHS`, `FSC`, `Planet Partners`, `neutralidade de carbono` → decisão (remover, ou manter se há ângulo `sustentabilidade`).
- **Origem nos curados**: `fabricado no Brasil`, `made in`, `produto nacional` → decisão (salvo ângulo `produto-nacional`).

**Escopo dos campos (aprendizado do 1º run):** as regras de **termo-banido, voz-comprador e superlativo** valem só nos campos que ALIMENTAM o review publicado (`sentimentoCompradores`, `angulosConversao`, `pontosFortes`, `pontosFracos`, `dicasAcionaveis`). **NÃO** aplique essas regras em `dadosInconsistentes` e `observacoesAgente` — são notas INTERNAS (o review nunca as publica verbatim), e vocabulário como `EAN`/`ASIN`/`specsAmazon`/`127V` ali é legítimo. (Caso real: "EAN" em `dadosInconsistentes` deu falso-positivo de termo-banido.) Exceção: **strip de HTML** vale em TODOS os campos curados (não pode haver tag em lugar nenhum).

**Importante**: o grep só sinaliza candidatos. Antes de auto-consertar um item (A), **confirme que é mesmo violação no contexto**. Falso-positivo NÃO conserta — vira no máximo info no relatório. Na dúvida entre (A) e (B), trate como (B) (flag) — nunca reescreva em silêncio.

### Etapa 2 — Camada LLM (sub-agents paralelos, ISOLADOS, read-only)

N sub-agents Opus, levas de ≤10. Cada sub-agent (Agent tool, `model: opus`, conversa fresh):
- **Input**: APENAS o ASIN + o conteúdo da bíblia daquele ASIN (cole o JSON no prompt) + as 5 categorias da `biblia-auditar` (consistência interna, verificação externa, frescor, completude crítica, higiene editorial-factual) + a régua (`regras-biblia.md`).
- **Anti-contaminação no prompt**: "Você vê SÓ esta bíblia. NÃO mencione nenhum outro produto/marca/modelo que não seja o deste ASIN. NÃO compare com outras bíblias. Comece o JSON com `\"asin\": \"<ASIN>\"`."
- **Tarefa**: achar problemas FACTUAIS/de julgamento (não os mecânicos da Etapa 1 — esses já foram). Read-only: NÃO propõe reescrita de campo inteiro, só aponta o achado com evidência e sugestão.
- **Retorna**: SÓ o JSON `{ asin, criticos: [{categoria, campo, evidencia, problema, sugestao}], avisos: [...], info: [...] }`. NÃO grava arquivo, NÃO conserta nada.

### Etapa 3 — Aplicar SÓ o mecânico (skill-mãe, serial, chaveada por ASIN)

Pra cada bíblia que teve achado **do grupo (A)** CONFIRMADO na Etapa 1:
3.1. **Backup**: `cp docs/biblias-v2/<ASIN>.json docs/painel/.painel-backups/<dia>/<ASIN>-v2-<HHMMSS>.json`.
3.2. **Aplicar SÓ os fixes do grupo (A)** (deleção/formato) nos campos curados (script que lê o JSON, aplica, escreve `JSON.stringify(b, null, 2) + '\n'`). NUNCA tocar nos brutos. **NUNCA aplicar item do grupo (B)** — reescrita é julgamento.
3.3. **Bumpar `lastModified = new Date().toISOString()`** (só nas que mudaram). Manter `lastAuthor`.
3.4. **Re-grep** pra confirmar que os padrões (A) sumiram. Se algo resistiu → flag no relatório (não esconde).

Os achados (B) da Etapa 1 + os de julgamento da Etapa 2 **NÃO são aplicados** — vão direto pro relatório.

⚠️ **Ordem importa (senão o painel marca "stale"):** o painel deriva "auditada" pelo **mtime do `.audits/<ASIN>-last.md`** e marca **stale se `auditedAt < lastModified`** (`biblia-status.ts`). Então o relatório (Etapa 4) tem que ser escrito **DEPOIS** do bump de `lastModified` desta etapa. A ordem do pipeline (Etapa 3 conserta+bumpa → Etapa 4 escreve relatório) já garante isso; não inverta.

### Etapa 4 — Relatório (por bíblia + consolidado)

4.1. **Por bíblia**: escrever `docs/biblias-v2/.audits/<ASIN>-last.md` (formato idêntico ao da `biblia-auditar` individual — o painel lê esse arquivo pra marcar "auditada"). Inclui o que foi auto-consertado (mecânico) + os achados de julgamento pendentes.
4.2. **Consolidado no chat**: tabela por bíblia com selo 🟢 limpa / 🟡 avisos / 🔴 crítico + contagem + top issues. Resumo de: quantas auto-consertadas (mecânico) e o que ficou pendente de decisão humana (com o ASIN pra rodar `biblia-auditar` individual).
4.3. **Commit dos relatórios**: `.audits/<ASIN>-last.md` são tracked; commitar + push + `bash scripts/painel-vps-pull.sh`.

### Etapa 5 — Sync R2 push (só se a camada mecânica aplicou fixes)

```bash
bun scripts/sync-biblias-r2.ts --apply --push 2>&1 | tail -5
```
Conferir que as bíblias que tiveram fix mecânico dizem `enviado`, NÃO `recebido`. Se nenhuma teve fix, PULAR esta etapa (não há o que subir; só os relatórios .md já foram commitados no git).

## Relatório final (consolidado)

- **Auditadas** (N): por ASIN, selo 🟢/🟡/🔴 + nº de achados por severidade.
- **Auto-consertadas (mecânico)**: lista do que foi aplicado por bíblia (ex: "B076HYKFL7: removido `<strong>` de pontosFortes").
- **Pendentes de decisão humana (julgamento)**: por ASIN, os achados factuais/de contradição/frescor — com a instrução "rode `biblia-auditar <ASIN>` pra resolver no propor→aprovar".
- **Puladas** (pendentes de preenchimento): lista → `biblia-preencher-em-massa`.
- **Excluídas**: contaminadas-hard + sem-dados-brutos, com motivo.
- **Sync R2**: X enviadas (só as com fix mecânico) / 0 esperadas se nada mudou.

## Armadilhas (embutir)

1. **Bíblia só no R2** (não no Mac): o sync 0.1 resolve.
2. **Clobber do lastModified**: bump via `toISOString()` SÓ quando aplicou fix. Sem isso o `--push` vira `recebido`.
3. **NÃO comparar bíblias**: o isolamento é a defesa anti-contaminação nº1. Nunca um prompt com 2 bíblias, nunca passada "compare X com Y".
4. **Falso-positivo do grep**: "o mais leve da categoria" (qualificado) NÃO é superlativo absoluto; "rita lobo" em 2 produtos da mesma marca NÃO é contaminação. Confirmar no contexto antes de auto-consertar.
5. **Não auto-aplicar julgamento**: a tentação de "já que achou, conserta" quebra a paridade de qualidade com a individual. Julgamento é SEMPRE flag.
6. **Race de escrita**: sub-agent NUNCA grava; só a skill-mãe (serial) aplica o mecânico.

## Limites de segurança (NUNCA faz)

- Deploy.
- Aplicar achado de julgamento (factual/contradição/frescor).
- Tocar campos brutos ou `lastAuthor`.
- Comparar/compartilhar contexto entre bíblias.
- Auditar bíblia pendente (pula) ou contaminada-hard (exclui).

## Disciplina de release

Nasce no project repo. Vai pro marketplace (`marcelohaz/afiliados-skills`) DEPOIS de validada num run real (1º lote). Padrão: fazer + validar → release (ver `feedback_skill_regua_release_junto`).

## Invocação

```
/biblia-auditar-em-massa B0CH5RSZTP,B01I78MAHW,B093Q7LLD6
/biblia-auditar-em-massa todas
/biblia-auditar-em-massa sub=panela-eletrica
```
