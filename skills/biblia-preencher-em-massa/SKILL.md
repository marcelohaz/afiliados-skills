---
name: biblia-preencher-em-massa
description: Preenche a curadoria (7 campos) de VÁRIAS bíblias v2 de uma vez, em PARALELO via sub-agents (até 10 simultâneos), cada um isolado na sua bíblia (zero contaminação cruzada). Aceita lista de ASINs OU "todas as pendentes". Exclui contaminadas e sem-dados-brutos do lote. Sync R2 nas 2 pontas, bump lastModified, backup. Botão roxo "✨ Preencher bíblias" do produtos.html copia o comando pra cá.
---

## Parse de input

Args no `$ARGUMENTS`:
- **Lista de ASINs** (forma do botão do painel): `B0CH5RSZTP,B01I78MAHW,B093Q7LLD6` (vírgula, sem espaço). Cada um `^[A-Z0-9]{10}$`.
- **`todas` / `todas as pendentes`**: varre `docs/biblias-v2/*.json`, pega as `pend` preenchíveis (ver Etapa 0.4).
- **Filtro** (opcional): `niche=Panela Elétrica` ou `sub=panela-eletrica` → restringe o "todas" àquela subcategoria.

# Preencher curadoria de bíblias em massa (paralelo via sub-agents)

> Esta skill é **orquestrador leve**. A curadoria real (os 7 campos) é feita por sub-agents independentes, **um por ASIN**, cada um seguindo a régua canônica do `biblia-preencher` (a fonte editorial é aquela skill + `docs/painel/_data/regras-biblia.md`). Esta skill NÃO reimplementa a régua — ela fan-out + escreve + sincroniza. Análoga à `pagina-produto-criar-em-massa`, mas pra bíblia em vez de página.

## Modelo

Opus 4.8 (ou mais novo). Sub-agents fixados com `model: opus` no Agent tool. NUNCA Sonnet/Haiku (régua do projeto: skills sempre Opus).

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
- **`lastModified` bumpado via `new Date().toISOString()`** ao gravar (UTC real); NUNCA `lastAuthor`, NUNCA hand-roll via getHours/pad (armadilha de timezone). Sem o bump, o pull do R2 CLOBBERA o edit.
- **Sync R2 nas 2 pontas**: pull no começo (as bíblias cruas podem estar SÓ no R2 — caso real: lote de panela elétrica criado no painel, ausente no Mac local), push no fim (uma vez, batch).
- **Idempotente**: pula bíblia já preenchida (coreDone) — re-rodar o lote não retrabalha.
- **Full-auto, sem checkpoint humano no meio** (igual aos outros em-massa). Confirmação só ANTES do disparo (lista + estimativa).
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
   - **Já preenchida** (`angulosConversao` + `pontosFortes` + `pontosFracos` todos não-vazios = coreDone) → **PULA** (idempotência).
   - **Sem dados brutos** (todos vazios: `sobreEsteItem`/`doFabricante`/`specsAmazon`/`opinioesCompradores`/`descricaoProduto`) → **EXCLUI** + lista "sem matéria-prima, capturar antes".
   - **Contaminada** — roda `bun scripts/check-contamination.ts <ASIN>`; se `hasContamination: true` com hard issue (`cross-brand-mention`) → **EXCLUI** + lista "informações erradas, corrigir à mão (biblia-preencher individual)". Issue soft (`asin-mismatch`/`brand-mismatch`) NÃO exclui — entra e o sub-agent trata por-campo + flag em `dadosInconsistentes` (régua do biblia-preencher passo 1.5).
   - **Preenchível** (pend + tem dado bruto + não-hard-contaminada) → **ENTRA no lote**.

0.5. **Mostrar o plano + confirmar**: tabela (ASIN, nome, ENTRA/PULA/EXCLUI + motivo) + nº no lote + estimativa (~1-3 min/leva). Pergunta `S/N` antes do paralelo (evita disparar lote errado).

### Etapa 1 — Geração (sub-agents paralelos, ISOLADOS)

N sub-agents Opus, levas de ≤10. Cada sub-agent (Agent tool, `model: opus`, conversa fresh):
- **Input**: APENAS o ASIN + o conteúdo bruto daquela bíblia (cole o JSON da bíblia no prompt) + a régua dos 7 campos (do `biblia-preencher`: estrutura de cada campo + invariantes PT-BR + armadilhas + chavões do nicho via `chavoes-por-nicho.json`).
- **Tarefa**: gerar os 7 campos de curadoria (`sentimentoCompradores`, `angulosConversao`, `pontosFortes`, `pontosFracos`, `dicasAcionaveis`, `dadosInconsistentes`, `observacoesAgente`) + (se houver ruído) o `conteudoBrutoFabricante` limpo. Destilar SÓ dos dados daquela bíblia, sem inventar, sem copiar verbatim.
- **Anti-contaminação no prompt**: "Você vê SÓ este produto. NÃO mencione nenhum outro produto/marca/modelo que não seja o deste ASIN. Comece o JSON com `\"asin\": \"<ASIN>\"`."
- **Retorna**: SÓ o JSON `{ asin, sentimentoCompradores, angulosConversao, pontosFortes, pontosFracos, dicasAcionaveis, dadosInconsistentes, observacoesAgente, conteudoBrutoFabricanteLimpo? }`. NÃO grava arquivo.

### Etapa 2 — Escrita (skill-mãe, SERIAL, chaveada por ASIN)

Pra cada JSON retornado:
2.1. **Trava de ASIN**: `json.asin === asin_pedido`? Não → descarta + re-dispara aquele isolado (anti-mix-up).
2.2. **Backup**: `cp docs/biblias-v2/<ASIN>.json docs/painel/.painel-backups/<dia>/<ASIN>-v2-<HHMMSS>.json`.
2.3. **Merge**: objeto inteiro da bíblia + substitui SÓ os 7 campos + (se veio) `conteudoBrutoFabricante` limpo + **`lastModified = new Date().toISOString()`**. NÃO toca `lastAuthor` nem resto.
2.4. **Write** `JSON.stringify(obj, null, 2) + '\n'`.

### Etapa 2.5 — Post-check de leak (auto)

Pra cada bíblia gravada: a curadoria (todos os 7 campos serializados) não pode conter `identidade.nome`/`marca`/`modelo` de **outra bíblia do lote**. Se contiver → flag "⚠ possível leak de <outro ASIN>", reverte do backup, re-dispara aquele isolado (máx 2x). Não-convergiu → deixa o backup e flag no relatório (não esconde).

### Etapa 3 — Sync R2 push (uma vez, batch)

```bash
bun scripts/sync-biblias-r2.ts --apply --push 2>&1 | tail -5
```
Conferir que as linhas dos ASINs do lote dizem `enviado`/`local mais novo`, NÃO `recebido` (com o bump do lastModified o push vence). Se vier `recebido` em algum → o pull clobberou (timestamp não bumpado): re-aplicar o bump + re-push.

### Etapa 4 — Audit encadeado (`--audit`)

Se `--audit` no args: encadeia a `biblia-auditar-em-massa` no MESMO lote recém-preenchido (o fluxo "preencheu → audita e conserta automático, com qualidade"). Ela:
- **Auto-aplica** todo conserto de direção CONHECIDA — mecânico/deleção-formato (travessão, `<strong>`/HTML na curadoria, muleta, concordância) E reescrita conhecida (voz-comprador→analítico, superlativo→qualificado, contradição contra a própria `decisaoEditorial`, fonte errada). **Caso real do 1º lote: `<strong>` em `pontosFortes` e crava-de-número contra a decisaoEditorial — é o que isto fecha.**
- **Re-audita cada conserto** (verifica que ficou limpo e não mudou sentido; não convergiu em ≤3 → reverte do backup + vira flag). Essa re-auditoria substitui a aprovação humana = mesma qualidade da individual.
- **Report-only** só pro indeterminável (frescor, verificação externa, contradição no bruto sem valor certo).

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

## Disciplina de release

Nasce no project repo. Vai pro marketplace (`marcelohaz/afiliados-skills`) DEPOIS de validada num run real (1º lote). Padrão: fazer + validar → release (ver `feedback_skill_regua_release_junto`).

## Invocação

```
/biblia-preencher-em-massa B0CH5RSZTP,B01I78MAHW,B093Q7LLD6
/biblia-preencher-em-massa todas as pendentes
/biblia-preencher-em-massa sub=panela-eletrica --audit
```
