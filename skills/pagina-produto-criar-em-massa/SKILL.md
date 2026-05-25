---
name: pagina-produto-criar-em-massa
description: Cria os 6 campos editoriais (subtitle, shortDescription, pros, cons, specs, fullReview) de TODAS as páginas individuais vazias de um site, em PARALELO via sub-agents — qualidade IDÊNTICA à skill individual `pagina-produto-criar` (cada sub-agent é conversa fresh do Opus, sem cross-contamination). Skill mãe orquestra: pre-flight bíblias → confirmação interativa → N Agents paralelos (até 10) → 1 commit lote → push + VPS pull → report. Aceita `site` (todos os stubs vazios) OU `site/ASIN1,ASIN2` (subset). Flag opcional `--audit` dispara audit pós-batch em paralelo. NÃO toca em stubs parciais. NÃO cria stubs (pré-requisito: stubs no painel).
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS, com flag opcional `--audit`:

**A) Site sozinho** (modo "todos os stubs vazios"):
- `melhorpretreino` → processa todos os stubs vazios em `sites/melhorpretreino/src/content/products/`

**B) Site + lista de ASINs** (modo "subset"):
- `melhorpretreino/B07XYZ123A,B08ABC456B` → só esses ASINs (filtra pelos slugs/asins correspondentes)

**Flag opcional `--audit`** (default OFF — opt-in pra qualidade extra):
- `melhorpretreino --audit` → após criar páginas, roda `pagina-produto-auditar` em paralelo pra cada uma
- Sem a flag, skill batch tem comportamento idêntico à skill individual (não audita automaticamente)
- Adicione `--audit` quando: site novo importante, qualidade-crítico, primeiro batch
- Pule `--audit` quando: re-rodar, batch rotineiro, vai auditar separado depois

Detecção:
- Se `$ARGUMENTS` tem `/` seguido de algo com vírgulas ou regex `[A-Z0-9]{10}` → caminho B
- Senão → caminho A
- Se contém substring `--audit` em qq posição → audit ativo

# Criar páginas individuais em massa (paralelo via sub-agents)

> Esta skill é **orquestrador leve**. O trabalho editorial real (gerar os 6 campos) é feito por sub-agents independentes via Agent tool, cada um executando o equivalente da skill `pagina-produto-criar` numa conversa nova e isolada. Skill mãe coordena listagem, pre-flight, paralelismo, agregação e commit lote.

## Pré-requisitos

1. **Stubs já criados** em `sites/{site}/src/content/products/*.mdx` (via painel: site detail → "+ Nova página de produto"). A skill NÃO cria stubs — só preenche conteúdo editorial.
2. **Bíblias completas** dos produtos correspondentes em `docs/biblias-v2/{ASIN}.json` com `pontosFortes`, `pontosFracos`, `angulosConversao` populados. Pre-flight aborta se alguma bíblia estiver incompleta.
3. **Site existe** em `sites/{site}/src/config.ts`. Se 404, abortar.

## Invariantes

- **Sub-agents NÃO fazem git operations.** Eles só fazem `Read` (bíblia/config/.mdx/artigos), `Edit/Write` no `.mdx` do produto e backup. **Skill mãe controla TUDO de git** (1 commit lote no fim, 1 push, 1 VPS pull).
- **Detecção rigorosa de stub vazio.** Só processa stubs 100% vazios (marker no body + ausência de TODOS os 6 campos editoriais no frontmatter). Stub parcial NÃO entra no batch — protege trabalho manual em andamento.
- **Pre-flight bíblias é obrigatório.** Skill aborta antes do paralelo se alguma bíblia faltar `pontosFortes` ou `angulosConversao` — senão sub-agent vai produzir página fraca em silêncio.
- **Confirmação interativa.** Mostra lista de stubs encontrados + tempo estimado. Pergunta `S/N` antes de disparar paralelo (pra evitar disparar batch errado).
- **Limite de paralelismo: 10 sub-agents simultâneos.** Acima disso, batch é dividido em levas (10 + 10 + ...). Throttling do harness pode degradar acima de 10.
- **Erro em 1 não quebra batch.** Sub-agent que falha retorna `{ok: false, error: ...}`. Skill mãe agrega e reporta no fim. Outros sub-agents continuam.
- **Português brasileiro editorial.** Tom analítico.

## Fluxo

1. **Parse args**: detecta site sozinho OU site/asins. Valida regex `[a-z0-9-]+` no site.

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   git stash push -m "skill-pagina-produto-criar-em-massa-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Painel VPS commita+pusha automaticamente quando user cria stubs novos pela UI. Mac local pode estar 5-30s atrás. Pull antes evita falso-negativo "stub não existe localmente".

2. **List candidatos**:
   - Glob `sites/{site}/src/content/products/*.mdx`
   - Se modo B (subset): filtrar pelo ASIN do frontmatter
   - Se nenhum: abortar com mensagem "Site {site} não tem stubs (verifica painel)"

3. **Classificar cada candidato** (detecção rigorosa):
   - **Stub vazio**: body contém `{/* STUB GERADO POR ` E frontmatter NÃO tem `pros`, `cons`, `specs`, `fullReview`, `subtitle`, `shortDescription`
   - **Stub parcial**: tem qq um dos 6 campos preenchidos → **PULA**
   - **Já preenchido**: tem todos os 6 campos → **PULA** (idempotência)

   Categorias retornadas:
   - `stubsVazios`: candidatos pra processar
   - `stubsParciais`: pulados (com warning na lista)
   - `jaPreenchidos`: pulados silenciosamente (idempotência)

   Se `stubsVazios.length === 0`: abortar com mensagem clara distinguindo parciais vs já-preenchidos.

4. **Pre-flight bíblias** (CRÍTICO — abortar se incompletas):
   - Pra cada stub vazio, ler `docs/biblias-v2/{ASIN}.json`
   - Validar: `pontosFortes.length > 0` E `angulosConversao.length > 0`
   - Se ASINs inválidas (bíblia faltando): adicionar à lista de erros
   - Se bíblia tem `pontosFortes=[]` ou `angulosConversao=[]`: adicionar à lista de "curadoria incompleta"
   - Se houver QUALQUER problema: **abortar batch** com lista dos ASINs e instrução pra rodar `biblia-preencher` antes

5. **Confirmação interativa** (obrigatória):

   ```
   📋 Encontrei {N} stubs vazios em {site}, todos com bíblia completa:
     - {slug-1} (ASIN {asin-1}) — {name-do-produto}
     - {slug-2} (ASIN {asin-2}) — {name-do-produto}
     - ...

   ⏭️  Pulando (já tinham conteúdo):
     - {slug-parcial} (parcial: tem subtitle mas falta o resto)
     - {slug-preenchido} (já tem os 6 campos)

   Cada produto será processado por um sub-agent Opus INDEPENDENTE
   (conversa fresh, isolada, sem cross-contamination). Mesma régua editorial
   da skill individual `pagina-produto-criar`.

   {{Se flag --audit ativa}}: Audit pós-batch via `pagina-produto-auditar`
   em paralelo pra cada página criada (opt-in pra qualidade extra).
   {{Se flag --audit ausente}}: SEM audit automático (user pode rodar
   `pagina-produto-auditar` separado quando quiser).

   Tempo estimado: ~3-5 min (paralelo até 10 simultâneos).

   Confirma processar? (S/N)
   ```

   **NÃO PROSSEGUIR sem resposta afirmativa do user.** Se user disser N ou ambíguo, abortar limpo.

6. **Read affiliateTag do site** (uma única vez, passa pros sub-agents): `Read sites/{site}/src/config.ts` → extrai via regex `/affiliateTag:\s*['"]([^'"]*)['"]/`.

7. **Dispara sub-agents em paralelo**:
   - Se `stubsVazios.length <= 10`: 1 leva (todos paralelos)
   - Se `stubsVazios.length > 10`: divide em levas de 10 (sequencial entre levas, paralelo dentro)

   **Cada sub-agent recebe**:
   - `site`, `slug`, `asin`
   - `affiliateTag` (resolvida)
   - Instrução completa pra executar fluxo da skill individual (ver "Prompt do sub-agent" abaixo)
   - Instrução EXPLÍCITA: **NÃO fazer git operations** (sem commit, sem push)

   **Tool calls em paralelo numa única mensagem**:
   ```
   Agent({...}, Agent({...}, ..., Agent({...})  ← N invocações na mesma mensagem
   ```
   Harness do Claude Code executa concorrente.

8. **Aggrega resultados** dos N sub-agents:
   - `sucessos`: `[{slug, asin, path, summary}]`
   - `falhas`: `[{slug, asin, error}]`

9. **git add específico + commit lote** (se houve sucesso):

   **CRÍTICO**: NÃO usar `git add sites/{site}/src/content/products/*.mdx` (captura arquivos não-relacionados que estavam modificados antes do batch). Usar SÓ a lista dos paths retornados pelos sub-agents com sucesso:

   ```bash
   # Lista de paths dos sucessos (variável da agregação do passo 8):
   git add sites/{site}/src/content/products/{slug-1}.mdx \
           sites/{site}/src/content/products/{slug-2}.mdx \
           ... (cada path explícito)
   ```

   Antes do add, confirmar com `git status --short` que os paths esperados estão modificados. Se algum sucesso reportado não está modificado, alertar (sub-agent reportou ok mas não escreveu?).

   ```bash
   git commit --no-verify -m "feat({site}): preenche {N} páginas individuais em batch via skill" \
     -m "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
   ```

   `--no-verify` é necessário porque hook pre-commit bloqueia edits direto de .mdx (skill batch passa por esse mesmo bypass que a skill individual já usa — exceção documentada na memória do projeto).

10. **Pull rebase + push**:
    ```bash
    git pull --rebase origin main 2>&1 | tail -2
    git push origin main 2>&1 | tail -3
    ```

11. **Disparar git pull no painel VPS**:
    ```bash
    bash scripts/painel-vps-pull.sh 2>&1 | tail -3
    ```

12. **Audit pós-batch (CONDICIONAL — só se flag `--audit` ativa)**:

    Default da skill batch é **NÃO auditar** (paridade com skill individual,
    que também não auto-audita). User opta-in via `--audit` quando quer
    garantia extra contra "falha silenciosa" do paralelismo.

    Se `--audit` ativa: pra cada página criada com sucesso, disparar audit
    independente em paralelo:

    ```
    Agent({...pagina-produto-auditar pra produto 1...},
          {...pagina-produto-auditar pra produto 2...},
          ...
          {...pagina-produto-auditar pra produto N...})
    ```

    **CRÍTICO — sub-agents de audit também NÃO fazem git** (mesma regra dos
    sub-agents de criação, pra evitar race condition). Cada sub-agent de
    audit recebe instrução explícita:
    - Faça o audit completo (ler .mdx + bíblia, gerar relatório com
      errors/warnings/info)
    - **Escreva o relatório `.md`** em `docs/biblias-v2/.audits/products/{site}-{slug}-last.md`
    - **NÃO faça** `git add`, `git commit`, `git push`, nem
      `painel-vps-pull.sh` — skill mãe controla isso
    - Retorne resumo estruturado: `{ok: true, slug, severity: 'ok'|'warn'|'error', issues: [...]}`

    Skill mãe agrega:
    - **Páginas SEM issues críticos**: aprovadas
    - **Páginas com warnings**: lista no report final pra user revisar
    - **Páginas com errors críticos**: alerta que precisam revisão individual via `pagina-produto-criar` em modo rewrite

    Após agregar, skill mãe faz **1 commit lote dos `.md` de audit**
    (`git add docs/biblias-v2/.audits/products/{site}-{slug}-last.md ...` —
    lista específica, não glob) + push + VPS pull.

    Sem `--audit`, pula este passo inteiro. User pode rodar
    `pagina-produto-auditar` separado quando quiser (1 produto por vez
    via skill individual, ou paralelo manual via múltiplas invocações).

13. **Report final no chat** (template muda conforme `--audit` ativa ou não):

    **Sem `--audit`** (default — paridade com skill individual):

    ```
    ✅ Batch concluído em {tempo}

    PÁGINAS CRIADAS ({N}/{total}):
      ✓ {slug-1} ({chars} chars no fullReview, 3 links Amazon)
      ✓ {slug-2} ({chars} chars no fullReview, 3 links Amazon)

    FALHAS NO BATCH ({M}):
      ✗ {slug-x} — {erro do sub-agent}

    PULADOS ({Z}):
      ⏭️  {slug-y} (stub parcial: skill batch não sobrescreve)
      ⏭️  {slug-z} (já preenchido)

    📦 Commit: {commit-hash}
    🔄 VPS sincronizado: {OK | bloqueado}

    💡 Pra auditar as páginas criadas, rode `pagina-produto-auditar`
       em cada uma ou re-rode esta skill com --audit.
    ```

    **Com `--audit`** (após auditar todas as criadas):

    ```
    ✅ Batch concluído em {tempo}

    PÁGINAS CRIADAS ({N}/{total}):
      ✓ {slug-1} → audit OK
      ✓ {slug-2} → audit: 1 warning (link Amazon com tag faltando)
      ⚠ {slug-3} → audit: 2 errors → revisar via pagina-produto-criar

    FALHAS NO BATCH ({M}):
      ✗ {slug-x} — {erro do sub-agent}

    PULADOS ({Z}):
      ⏭️  {slug-y} (stub parcial)
      ⏭️  {slug-z} (já preenchido)

    📦 Commit (criação): {commit-hash-1}
    📦 Commit (audits): {commit-hash-2}
    🔄 VPS sincronizado: {OK | bloqueado}
    🔍 Audits: {ok} OK / {warn} warnings / {err} críticos
    ```

    Páginas com errors críticos NÃO bloqueiam o commit lote (já foi). Apenas sinalizam pro user que precisam revisão individual depois.

## Detecção rigorosa de stub vazio (CRÍTICO)

Skill INDIVIDUAL atual permite sobrescrever (modo individual = ação explícita do user). Skill BATCH **NÃO sobrescreve nada** — só toca em stubs 100% vazios pra proteger trabalho manual em andamento.

**Stub VAZIO** (entra no batch):
- Body contém o marker literal: `{/* STUB GERADO POR `
- Frontmatter NÃO tem **NENHUM** destes campos: `subtitle`, `shortDescription`, `pros`, `cons`, `specs`, `fullReview`

**Stub PARCIAL** (PULA):
- Frontmatter tem PELO MENOS UM dos 6 campos populado (mesmo que vazio array)
- Sinal de trabalho manual em andamento — NÃO arriscar sobrescrever

**Já PREENCHIDO** (PULA):
- Frontmatter tem TODOS os 6 campos populados
- Idempotência: re-rodar skill é safe

Lógica em pseudo-Python:
```python
def classify(frontmatter, body):
    has_marker = '{/* STUB GERADO POR ' in body
    fields = ['subtitle', 'shortDescription', 'pros', 'cons', 'specs', 'fullReview']
    populated = [f for f in fields if frontmatter.get(f)]

    if len(populated) == 0 and has_marker:
        return 'stub_vazio'  # entra no batch
    elif len(populated) == 6:
        return 'ja_preenchido'  # pula (idempotência)
    else:
        return 'stub_parcial'  # pula (proteção)
```

## Prompt do sub-agent

Cada Agent recebe esta instrução (inline, ~40 linhas):

```
Tarefa: gerar os 6 campos editoriais (subtitle, shortDescription, pros, cons,
specs, fullReview) da página individual de produto.

Inputs:
- Site: {{site}}
- Slug: {{slug}}
- ASIN: {{asin}}
- AffiliateTag do site: {{tag}} (pode ser vazia '' em sites em construção)

Execute o fluxo da skill `.claude/skills/pagina-produto-criar/SKILL.md` à risca,
EXCETO os passos de git operations (12, 13). Especificamente:

1. Read .mdx atual: `sites/{{site}}/src/content/products/{{slug}}.mdx`
2. Read bíblia: `docs/biblias-v2/{{asin}}.json`
3. Verifique reviews-em-artigo que citam o ASIN (anti-duplicate vs página individual):
   `Grep "asin.*{{asin}}" sites/{{site}}/src/content/reviews/*.mdx`
4. Se houver review, leia o fullReview do produto naquele review pra saber
   o ÂNGULO daquele texto. Sua página individual DEVE ter ângulo DIFERENTE
   (anti-duplicate-content SEO).
5. Monte amazonUrl:
   - Tag preenchida: `https://www.amazon.com.br/dp/{{asin}}?tag={{tag}}&linkCode=ogi&th=1&psc=1`
   - Tag vazia: `https://www.amazon.com.br/dp/{{asin}}` (crua)
6. Gere os 6 campos seguindo as regras detalhadas em pagina-produto-criar/SKILL.md:
   - subtitle (10-150 chars): título descritivo editorial, sem redundância
     com o nome do produto, SEM spec dump
   - shortDescription (40-800 chars): 1-2 frases resumindo + ângulo
   - pros (3-8 items, 8-300 chars cada): formato `<strong>Título</strong>: explicação`
     com dado concreto
   - cons (1-5 items, mesmo formato): pontos de atenção
   - specs (3-10 pares): label + value strings simples
   - fullReview (300-3000 chars HTML): 4 parágrafos marcados:
     `<p><strong>Para quem é:</strong> ...</p>`
     `<p><strong>Por que gostamos:</strong> ...</p>`
     `<p><strong>Pontos de atenção:</strong> ...</p>`
     `<p><strong>Resumo:</strong> ...</p>`
     3 links Amazon nas posições: Para quem é, Por que gostamos, Resumo.
7. Régua editorial DURA (NÃO violar):
   - Sem travessão (—) em nenhum campo
   - Sem superlativos absolutos ("o melhor", "incomparável")
   - Voz analítica (NUNCA cite compradores/reviews/avaliações/estrelas)
   - HTML allowlist em fullReview: só `<p>`, `<strong>`, `<em>`, `<a>`
   - Tag-aware nos links Amazon (formato acima)
   - Sem comparações com concorrentes (página individual é sobre o produto sozinho)
   - Voz-citação ("segundo X", "alérgenos confirmam") drop sempre EXCETO
     quando qualifica claim só-fabricante + adiciona valor editorial
   - Operação de destilação bíblia → .mdx (drop marcadores burocráticos)
8. Validações antes de escrever:
   - Tamanhos no limite
   - HTML allowlist
   - Sem travessão
   - 3 links Amazon no fullReview com tag/sem-tag conforme config
9. Backup ANTES de escrever:
   ```bash
   DAY=$(date +%Y-%m-%d); TIME=$(date +%H%M%S)
   mkdir -p "docs/painel/.painel-backups/$DAY"
   cp "sites/{{site}}/src/content/products/{{slug}}.mdx" \
      "docs/painel/.painel-backups/$DAY/product-{{site}}-{{slug}}-${TIME}.mdx"
   ```
10. Write o .mdx novo: preserva frontmatter base (asin, name, image, etc),
    adiciona os 6 campos editoriais, remove o marker `{/* STUB GERADO POR ... */}`
    do body.

❌ NÃO FAÇA: git add / git commit / git push / painel-vps-pull.sh.
Esses são responsabilidade da skill mãe que vai aggregar todos os
sub-agents e fazer 1 commit lote no fim.

Reporte em formato curto:
- Sucesso: `{ ok: true, slug: '{{slug}}', path: '...', summary: 'subtitle 67c / fullReview 1842c / 3 links Amazon' }`
- Erro: `{ ok: false, slug: '{{slug}}', error: 'motivo curto' }`
```

## Limites e edge cases

### Bíblia faltando ou incompleta (pre-flight)
- Bíblia 404 → abortar batch ANTES de qualquer sub-agent, com lista de ASINs
- Bíblia com `pontosFortes=[]` ou `angulosConversao=[]` → abortar batch, instrução:
  > "ASINs {X, Y, Z} têm bíblia mas curadoria incompleta. Rode `biblia-preencher`
  > nessas ASINs antes de criar páginas individuais em massa."

### Sub-agent falha individual
- Falha não-fatal: skill mãe agrega no `falhas[]`, continua
- Tipos comuns: bíblia bate em erro de parse, .mdx do stub não existe,
  validação editorial falhou (HTML allowlist violado, tamanho fora do
  limite, travessão escapou)
- User vê no report final + pode rodar skill INDIVIDUAL pra debugar
  produto-a-produto

### Stub aparece preenchido mas marker ainda lá
- Casuística esperada se user editou frontmatter no painel mas não tocou no body
- Classificação: stub_parcial → pula (skill batch não decide se sobrescreve)

### Throttling do harness (>10 simultâneos)
- Skill mãe divide em levas de 10 automaticamente
- Entre levas: aguarda leva atual terminar antes de disparar próxima
- Log: `Leva 1/3 (10 sub-agents)... ✓ → Leva 2/3 (10 sub-agents)...`

### Context window dos sub-agents
- Cada sub-agent é independente — não acumula contexto de outros
- Carrega apenas: bíblia do SEU produto, .mdx do SEU stub, config, review-em-artigo (se houver)
- Total ~30-50 KB por sub-agent → folgado dentro do limite Opus

## Comparação com fluxo individual

| Aspecto | Individual (`pagina-produto-criar`) | Batch (`em-massa`) |
|---|---|---|
| Invocação | 1× por produto | 1× por site (todos os stubs vazios) |
| **Qualidade por página** | **Alta** | **IDÊNTICA** (cada sub-agent é conversa fresh do Opus) |
| Tempo total (10 produtos) | ~30-50 min sequencial | ~3-5 min paralelo |
| Anti-duplicate cross-páginas | Não (skill individual também não faz) | Não (paridade) |
| Commits no git | N commits | 1 commit lote |
| Audit pós-criação | Manual via `pagina-produto-auditar` | Opt-in via flag `--audit` (paridade default) |
| Pode sobrescrever conteúdo? | Sim (modo individual = ação explícita) | **NÃO** (só stubs vazios) |
| Logging incremental | Sim (passo a passo) | Não (sub-agents reportam só no fim) |

## Armadilhas recorrentes

### 1. Tentar invocar skill `pagina-produto-criar` via Skill tool dentro do sub-agent
Sub-agent NÃO deve invocar `Skill(skill="pagina-produto-criar", ...)` porque a skill individual faz commit+push (passos 12-13) que conflitariam com 10 sub-agents simultâneos. **Sub-agent executa o fluxo INLINE** (passos 1-11 da individual, sem git).

### 2. Pular pre-flight de bíblias
Tentação: começar batch direto, deixar sub-agent abortar individualmente. Errado — desperdiça ~$0.50 + 3 min pra descobrir que metade falhou por bíblia incompleta. **Pre-flight é obrigatório, antes de qualquer paralelismo.**

### 3. Sobrescrever stub parcial sem perguntar
Stub com `subtitle` preenchido mas resto vazio é trabalho manual em andamento. Batch NÃO toca. User pode terminar via skill individual.

### 4. Commit por sub-agent (race condition)
Sub-agents simultâneos fazendo `git add + commit + push` = race condition garantida. Skill mãe controla TODO o git. Sub-agents só escrevem `.mdx`.

### 5. Confirmação interativa skippada
"S/N" é importante pra evitar disparar batch errado. **NÃO PROSSEGUIR sem confirmação afirmativa explícita do user.** Em caso de ambiguidade, abortar limpo.

### 6. Pular VPS pull no fim
Skill mãe DEVE rodar `bash scripts/painel-vps-pull.sh` depois do push. Sem isso, painel da Bárbara/produção não vê o batch até alguém manualmente puxar.

### 7. Tone-clone entre sub-agents (paranoia infundada)
Sub-agents são conversas INDEPENDENTES no Opus. Cada um é "fresh", sem contexto de outros. Tone-clone só rolaria se rodasse sequencial na mesma conversa. **Paralelo é seguro.**

### 8. Esquecer de passar `affiliateTag` resolvida pros sub-agents
Skill mãe resolve `affiliateTag` UMA vez (passo 6). Passa pros sub-agents no prompt. Se cada sub-agent tentar resolver de novo, 10 reads paralelos do mesmo `config.ts` (waste mínimo mas evitável).

## Quando NÃO usar esta skill

- **Site sem stubs criados ainda**: crie stubs no painel primeiro ("+ Nova página de produto" no site detail) ou crie via `POST /product/:site/_actions/create-from-bible` por ASIN. Skill batch só PREENCHE stubs vazios — não cria.
- **Bíblias incompletas** (pre-flight aborta): rode `biblia-preencher` nas ASINs reportadas antes do batch.
- **Quer sobrescrever páginas com conteúdo**: use `pagina-produto-criar` no modo individual (ação explícita) ou delete o .mdx + recrie stub no painel + rode batch.
- **Re-rodar é seguro (idempotente)**: pula automaticamente os já preenchidos. Skip ≠ erro.

## Sincronização painel ↔ skill ↔ prompt canônico

Esta skill **NÃO TEM op canônica** em `agent-prompts.json` (é skill local-only, sem botão equivalente no painel). Razão:

- Painel hoje tem botão "✨ Criar com IA" individual por página
- Batch via painel seria pesado (HTTP timeout, monitoramento de paralelismo)
- Bárbara/Marcelo invocam batch via Claude Code (`Skill(skill="afiliados-skills:pagina-produto-criar-em-massa", args="melhorpretreino")`)

A skill INDIVIDUAL `pagina-produto-criar` continua sincronizada com `agent-prompts.json:create_product_page` — esse é o canônico editorial. Sub-agents do batch seguem a mesma régua (paridade garantida porque sub-agent prompt cita a SKILL.md individual como fonte da verdade).

## Exemplo de invocação

```
preenche em massa as páginas individuais do melhorpretreino
roda batch de páginas individuais no melhorpretreino
pagina-produto-criar-em-massa melhorpretreino                              ← sem audit (default)
pagina-produto-criar-em-massa melhorpretreino --audit                      ← com audit pós-batch
pagina-produto-criar-em-massa melhorpretreino/B07XYZ123A,B08ABC456B        ← subset, sem audit
pagina-produto-criar-em-massa melhorpretreino/B07XYZ123A,B08ABC456B --audit ← subset, com audit
```

Args canônico que invoco: `Skill(skill="afiliados-skills:pagina-produto-criar-em-massa", args="melhorpretreino")` (ou com `--audit` se quiser qualidade extra)

## Limitação intrínseca conhecida

1. **Sem progress logging incremental** — sub-agents só reportam no fim do trabalho, não emitem "[3/10] processando..." conforme andam. Pra batch de 5 min, aceitável; pra batch de 30 min (50+ produtos), user fica no escuro. Mitigação: dividir batches grandes em levas explícitas (skill mãe loga "Leva 1/3 começando").

2. **Anti-duplicate cross-páginas IMPOSSÍVEL no paralelo** — sub-agents isolados não veem outras páginas do mesmo site sendo criadas. Se 2 produtos similares (ex: 2 whey isolados da mesma marca) processam simultâneo, podem ter parágrafos parecidos. **Skill individual atual também não faz isso**, então paridade total. Se virar problema real (raro), adicionar passo extra: skill mãe carrega contexto cumulativo após cada leva (mas perde benefício do paralelo).

3. **Limite de paralelismo do harness** ≈10 sub-agents simultâneos. Batches >10 são divididos em levas. Não é limite formal documentado — assumido conservador. Pode ser mais (15-20) na prática, mas evita timeouts/throttling.

4. **Falha silenciosa possível** — sub-agent pode retornar `{ok: true}` mas o `.mdx` ficou com problema sutil (travessão escapou, HTML inválido, voz-citação burocrática). Risco real mas baixo (mesma régua editorial canônica + sub-agent fresh do Opus). Mitigação opcional: rodar batch com flag `--audit` (dispara `pagina-produto-auditar` em paralelo após criar). Sem `--audit`, user pode auditar manualmente quando quiser — mesma paridade da skill individual (que também não auto-audita).
