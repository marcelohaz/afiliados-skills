---
name: biblia-auditar-em-massa
description: Audita E CORRIGE VÁRIAS bíblias v2 de uma vez, cada uma ISOLADA (zero contaminação cruzada, SEM passada comparativa entre bíblias). AUTO-APLICA todo conserto de direção CONHECIDA — mecânico/deleção-formato (strip HTML na curadoria, remover "declarado pelo fabricante", capitalização, typo de concordância, travessão→vírgula) E reescrita conhecida (voz-comprador→analítico, superlativo→qualificado, contradição contra a própria decisaoEditorial, fonte atribuída errada). Cada conserto passa por RE-AUDITORIA automática (verifica que ficou limpo e não mudou sentido; não convergiu em ≤3 → reverte do backup + vira flag). REPORT-ONLY só pro indeterminável (frescor, verificação externa não feita, contradição no bruto sem valor certo). Qualidade do texto = skill individual; a re-auditoria + backup substituem a aprovação humana. Roda como 2ª etapa do preencher-em-massa --audit (preenche → audita+conserta) OU sozinha. Sub-agents Opus paralelos (≤10). Sync R2 nas 2 pontas. Botão "🔍 Auditar bíblias" do produtos.html copia o comando.
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
- **NÃO é a IA do painel** (botão "✨ Auditar"). Roda na assinatura (Claude Code), Opus 4.8.

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

Opus 4.8 (ou mais novo). Sub-agents fixados com `model: opus` no Agent tool. NUNCA Sonnet/Haiku.

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
- **Só toca CAMPOS CURADOS** (`sentimentoCompradores`, `angulosConversao`, `pontosFortes`, `pontosFracos`, `dicasAcionaveis`, `dadosInconsistentes`, `observacoesAgente`). **NUNCA edita BRUTOS** (`sobreEsteItem`/`doFabricante`/`descricaoProduto`/`specsAmazon`/`conteudoBrutoFabricante`) nem `lastAuthor`.
- **`lastModified` bumpado via `new Date().toISOString()`** SÓ nas bíblias que tiveram conserto aplicado. NUNCA hand-roll (timezone). Sem fix → não toca.
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

Scan determinístico nos campos curados. Padrões e o conserto (todos = deleção/formato, sem reescrita):
- **HTML na curadoria**: `<\w+[^>]*>` em qualquer campo curado → **strip da tag** (vale em TODOS os campos curados).
- **Muleta**: `declarado pelo fabricante`, `declarados` (parentético) → **deletar a expressão**.
- **Travessão** `—`/`–` em campo curado → **trocar por vírgula**; em fronteira de sentença (ambíguo) → NÃO troca, vira (C)/flag.
- **Concordância** (mapa fixo): `composiçãos`→`composições`, `combinaçãos`→`combinações`, `porçãos`→`porções`, `a produto`→`o produto`, `o fórmula`→`a fórmula`, `o dose`→`a dose`, `disponíveis no em 2026`→`disponíveis em 2026`.
- **Capitalização**: bullet de array editorial começando minúsculo → maiúscula na 1ª letra.
- **Duplicação contígua** `([a-zA-ZÀ-ÿ\s]{8,40})\1` → remover a 2ª cópia.

**Escopo de campos (aprendizado 1º run):** termo-banido/voz-comprador/superlativo (grupo B abaixo) valem só nos campos que ALIMENTAM o review (`sentimentoCompradores`/`angulosConversao`/`pontosFortes`/`pontosFracos`/`dicasAcionaveis`). NÃO nos internos (`dadosInconsistentes`/`observacoesAgente`) — `EAN`/`ASIN`/`specsAmazon`/`127V` ali é legítimo (caso real: "EAN" deu falso-positivo). **HTML-strip vale em todos.**

### Etapa 2 — Camada LLM: achar + redigir conserto (sub-agents ISOLADOS)

N sub-agents Opus, levas ≤10. Cada um (Agent tool, `model: opus`, fresh) vê SÓ sua bíblia. Anti-contaminação no prompt: "Você vê SÓ esta bíblia. NÃO mencione/leia outra. NÃO compare com outras." Roda as 5 categorias da `biblia-auditar` (consistência interna, verificação externa, frescor, completude, higiene editorial-factual). Pra cada achado, **classifica B ou C e, se B, JÁ REDIGE o texto corrigido**:
- **(B) direção conhecida → redige o fix**: voz-comprador crua → observação analítica; superlativo absoluto → qualificado; termo técnico-industrial → linguagem editorial; contradição contra a **própria `decisaoEditorial`** da bíblia → seguir a decisão; fonte atribuída errada num item curado → corrigir a fonte; claim curado que contradiz o bruto quando o bruto tem o valor certo → alinhar ao bruto.
- **(C) indeterminável → só aponta**: frescor (precisa re-captura); claim que exige verificação externa não feita; contradição no dado BRUTO sem valor certo nem `decisaoEditorial`; qualquer coisa que dependa de dado que a bíblia não tem.
- **Retorna SÓ JSON**: `{ asin, fixes_B: [{categoria, campo, evidencia, problema, antes, depois}], report_C: [{categoria, campo, evidencia, problema, sugestao}] }`. NÃO grava arquivo, NÃO aplica.

### Etapa 3 — Aplicar (A) + (B) (skill-mãe, SERIAL, chaveada por ASIN)

Pra cada bíblia com fix (A) confirmado ou (B) retornado:
3.1. **Trava de ASIN**: `json.asin == pedido`? Não → descarta + re-dispara isolado.
3.2. **Backup**: `cp docs/biblias-v2/<ASIN>.json docs/painel/.painel-backups/<dia>/<ASIN>-v2-<HHMMSS>.json`.
3.3. **Aplicar (A)** (deleção/formato) **+ (B)** (substituir `antes`→`depois` no campo curado exato). NUNCA tocar brutos. NUNCA aplicar (C).
3.4. **Bumpar `lastModified = new Date().toISOString()`**. Manter `lastAuthor`. Write `JSON.stringify(b,null,2)+'\n'`.

### Etapa 3.5 — RE-AUDITORIA (a trava no lugar da aprovação humana)

Pra cada bíblia que recebeu conserto, dispare um sub-agent Opus ISOLADO (fresh, vê só essa bíblia + a lista do que foi consertado) pra verificar:
1. **Os achados originais sumiram?** (o conserto resolveu de fato)
2. **Não introduziu violação nova de régua?** (travessão, HTML, voz-comprador, superlativo, etc.)
3. **Não mudou o SENTIDO factual** vs os dados brutos? (a reescrita não inventou nem distorceu fato)
- **Passou** → mantém o conserto. ✅
- **Reprovou** → re-redige o(s) item(ns) problemático(s) e re-aplica → re-audita (máx **3** ciclos no total).
- **Não convergiu em 3** → **reverte aquela bíblia do backup** + move os itens dela pra (C) no relatório (flag "conserto não convergiu, revisar à mão"). Nada ruim fica gravado.

⚠️ **Ordem (senão painel marca stale):** o painel deriva "auditada" pelo mtime de `.audits/<ASIN>-last.md` e marca stale se `auditedAt < lastModified` (`biblia-status.ts`). A Etapa 3 bumpa `lastModified`; o relatório (Etapa 4) é escrito DEPOIS → mtime > lastModified → não-stale. Não inverta.

### Etapa 4 — Relatório (por bíblia + consolidado)

4.1. **Por bíblia**: `docs/biblias-v2/.audits/<ASIN>-last.md` (formato `biblia-auditar`; painel lê). Lista o que foi **auto-consertado** (A+B, com antes→depois) + os **report-only (C)** pendentes.
4.2. **Consolidado no chat**: tabela por bíblia 🟢/🟡/🔴 + nº consertado + nº report-only. Resumo: X auto-consertadas, Y itens report-only (com o porquê de não dar pra aplicar).
4.3. **Commit dos relatórios** (`.audits/<ASIN>-last.md` tracked) + push + `bash scripts/painel-vps-pull.sh`.

### Etapa 5 — Sync R2 push (só se aplicou fix)

`bun scripts/sync-biblias-r2.ts --apply --push 2>&1 | tail -5`. Conferir `enviado` (não `recebido`) nas bíblias consertadas. Nenhum fix → PULAR (só os .md já foram commitados no git).

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
4. **Falso-positivo do grep**: "o mais leve da categoria" (qualificado) NÃO é superlativo; "rita lobo" em 2 produtos da mesma marca NÃO é contaminação. Confirmar contexto antes de aplicar; na dúvida, (C).
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
