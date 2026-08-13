---
name: pagina-produto-criar-em-massa
description: Cria os 6 campos editoriais de TODAS as páginas individuais vazias de um site em PARALELO via sub-agents (até 10 simultâneos). Qualidade IDÊNTICA à skill individual `pagina-produto-criar` — cada sub-agent é conversa fresh do Opus, sem cross-contamination. Skill mãe orquestra: pre-flight bíblias (única barreira, aborta se incompleto) → imprime plano e dispara direto (SEM confirmação S/N) → N Agents paralelos → 1 commit lote → push + VPS pull → report. Aceita `site` (todos stubs vazios) OU `site/ASIN1,ASIN2` (subset). Flag opcional `--audit` dispara audit pós-batch em paralelo. NÃO toca em stubs parciais. NÃO cria stubs (pré-requisito: stubs no painel). Sub-agents herdam toda a régua editorial da `pagina-produto-criar` (chavões por nicho, concordância PT-BR, ban "declarado pelo fabricante" muleta, health YMYL, hard caps, voz consultiva).
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS, com flag opcional `--audit`:

**A) Site sozinho** (modo "todos os stubs vazios"):
- `melhorpretreino` → processa todos os stubs vazios em `sites/melhorpretreino/src/content/products/`

**B) Site + lista de ASINs** (modo "subset"):
- `melhorpretreino/B07XYZ123A,B08ABC456B` → só esses ASINs (filtra pelos slugs/asins correspondentes)

**Flag opcional `--audit`** (default OFF — opt-in pra qualidade extra):
- `melhorpretreino --audit` → após criar páginas, roda `pagina-produto-auditar` em paralelo pra cada uma
- ⚠️ **`--audit` não é mais só relatório.** Desde 2026-08-06 ele **conserta o erro de FATO** que
  passa no teste da frase nova (apagar termo que a bíblia não tem, trocar por como ela chama,
  restaurar qualificador que ela exige) e **reporta** o resto. **`warn` continua report-only**.
  Ver passo 12 e a seção homônima da `pagina-produto-auditar`.
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
- **Plano automático (SEM confirmação S/N).** Mostra lista de stubs encontrados + o que pula + tempo estimado, e **dispara direto** — não pergunta, não espera "S/N". A barreira de segurança é o pré-flight (aborta em site inexistente, zero stubs vazios, ou bíblia incompleta), não um beat humano. Decisão do Marcelo 2026-07-24: o pré-flight já protege qualidade; a confirmação era só atrito. O plano continua sendo IMPRESSO (transparência), mas é notificação, não pergunta.
- **Limite de paralelismo: 10 sub-agents simultâneos.** Acima disso, batch é dividido em levas (10 + 10 + ...). Throttling do harness pode degradar acima de 10.
- **Erro em 1 não quebra batch.** Sub-agent que falha retorna `{ok: false, error: ...}`. Skill mãe agrega e reporta no fim. Outros sub-agents continuam.
- **Português brasileiro editorial.** Tom analítico.

## Fluxo

1. **Parse args**: detecta site sozinho OU site/asins. Valida regex `[a-z0-9-]+` no site.

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   git stash push -u -m "skill-pagina-produto-criar-em-massa-temp" 2>&1 | tail -1
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>&1 | tail -1
   # CONTROLE: o pull funcionou mesmo?
   echo "local: $(git rev-parse --short=12 HEAD) · remote: $(git ls-remote origin main | cut -c1-12)"
   ```
   O user cria os stubs pela UI do painel (VPS) e invoca a skill aqui em seguida. O
   estado só chega no Mac por git, e **há duas formas de ele não chegar**.

   ⚠️ **Use `-u` e NÃO engula o erro do pull.** `git stash push` com pathspec (ou sem
   `-u`) deixa modificação de fora, e aí o pull morre com *"cannot pull with rebase: You
   have unstaged changes"*. Com `2>/dev/null` isso passa despercebido e a skill segue
   lendo o disco velho. Caso real 2026-08-13: 10 stubs existiam no remote, o pull falhou
   em silêncio e o passo 2 reportou "SEM STUB 10". A linha de controle acima é o que
   distingue "puxei e não tem" de "não puxei".

2. **List candidatos**:
   - Glob `sites/{site}/src/content/products/*.mdx`
   - Se modo B (subset): filtrar pelo ASIN do frontmatter
   - **Se nenhum: NÃO aborte ainda.** Zero é o sintoma de dessincronia, não só de stub
     ausente. Antes de abortar, force a VPS a soltar o que ela tem e puxe de novo:

     ```bash
     # 1) empurra commit que ficou preso na VPS (o /admin/update também pusha)
     set -a; source .env.painel-skills; set +a
     A=$(printf '%s:%s' "$PAINEL_USER" "$PAINEL_PASS" | base64 | tr -d '\n')
     curl -s -m 90 -X POST -H "Authorization: Basic $A" -H "Content-Type: application/json" \
       "${PAINEL_URL:-https://painel.melhorserum.com.br}/admin/update" | head -c 300
     # 2) puxa de novo e re-checa os ASINs
     git pull --rebase origin main 2>&1 | tail -2
     ```

     Só aborte se continuar zero DEPOIS disso, com a mensagem "Site {site} não tem stubs
     (verifica painel)".

   ⚠️ **A VPS commita mas NEM SEMPRE pusha** — a linha antiga desta skill dizia
   "commita+pusha automaticamente" e isso é falso. Caso real 2026-08-13 (monitores no
   `guiamelhorcompra`): os 10 stubs estavam num commit LOCAL da VPS
   (`e333dba89 scaffold 10 páginas individualis`) que nunca tinha sido empurrado. O
   `painel-vps-pull.sh` respondia "já estava atualizado" — ele puxa, não empurra. Foi o
   `POST /admin/update` que soltou ("1 commit local enviado pro origin/main"), e aí o
   batch rodou normal. Sem esse passo, o abort culpa o user por não ter criado stub que
   ele criou.

   ⚠️ **`POST /product/:site/_actions/create-from-bible` respondendo 409 "já existe" com
   o arquivo ausente no seu disco é a assinatura desse estado** — a VPS enxerga o próprio
   disco, você enxerga o git. Os dois estão certos sobre estados diferentes. Não conclua
   daí que o produto foi removido do site de propósito.

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

5. **Imprimir plano e PROSSEGUIR (sem confirmação)**:

   Chegou aqui = o pré-flight (passos 2-4) passou (site existe, há stubs vazios, bíblias completas). Imprime o plano como **notificação de transparência** e dispara os sub-agents **direto**, sem perguntar `S/N`:

   ```
   📋 Criando {N} páginas em {site} (bíblias completas, disparando agora):
     - {slug-1} (ASIN {asin-1}) — {name-do-produto}
     - {slug-2} (ASIN {asin-2}) — {name-do-produto}
     - ...

   ⏭️  Pulando (já tinham conteúdo):
     - {slug-parcial} (parcial: tem subtitle mas falta o resto)
     - {slug-preenchido} (já tem os 6 campos)

   Cada produto = um sub-agent Opus INDEPENDENTE (conversa fresh, isolada,
   sem cross-contamination). Mesma régua da skill individual `pagina-produto-criar`.

   {{Se flag --audit ativa}}: + audit pós-batch via `pagina-produto-auditar`.
   {{Se flag --audit ausente}}: sem audit automático.

   Tempo estimado: ~3-5 min (paralelo até 10 simultâneos).
   ```

   **NÃO pergunte `S/N`.** Os aborts do pré-flight são a única barreira; se o pré-flight passou, dispara. (Se o input do user for genuinamente ambíguo — ex. um slug/ASIN que não casa com nenhum stub — isso já é abort do passo 2/3, não motivo pra confirmação.)

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

   **GUARDAS MECÂNICAS — RODAR OS DOIS SCRIPTS, não redigitar (canon 2026-07-30, corrigido 2026-07-31):**

   ```bash
   # 1) audit-editorial, 1× por slug — AUTORITATIVO. ⚠ ele SEMPRE sai com exit 0,
   #    mesmo com achado: o gate tem que ler o JSON, não o exit code.
   SITE={site}; FAIL=0        # ⚠ {site} é o site DO BATCH, não um valor fixo
   for S in {slug-1} {slug-2} ...; do
     bun scripts/audit-editorial.ts "$SITE/$S" --json 2>/dev/null | python3 -c "
   import json,sys
   raw=sys.stdin.read().strip()
   if not raw.startswith('{'):            # ex.: '404: <path>' quando o slug/site não casa
       print('  ⛔ $S: audit-editorial não retornou JSON →', raw[:80]); sys.exit(1)
   d=json.loads(raw); bad=[f for f in (d.get('findings') or []) if f.get('sev') in ('error','warn')]
   if bad:
       print('  ⛔ '+d['slug'])
       for f in bad: print(f\"       {f['sev']:5} {f['rule']:22} {f.get('field','')} · {str(f.get('detail',''))[:60]}\")
       sys.exit(1)
   " || FAIL=1
   done
   [ "$FAIL" = "0" ] && echo "  ✅ audit-editorial limpo"

   # 2) guarda (cobre o mesmo núcleo + tem o modo --rede)
   bun scripts/pagina-produto-guardas.ts {site} {slug-1} {slug-2} ...
   ```

   Qualquer achado = **não commite**, conserte e re-rode. Bloqueie nos DOIS níveis
   de `sev`: `error` (fence, html-invalido, tamanho-fora-de-faixa, termo-banido,
   yaml-invalido) **e** `warn` (travessao, no-ponto-e-virgula) — os dois `warn` são
   proibições duras da régua com conserto determinístico (`—`→vírgula, `;`→`.`/`,`),
   então não há motivo pra deixar passar.

   **Por que os DOIS, e nesta ordem** (medido 2026-07-31, injetando cada defeito e restaurando): o `audit-editorial.ts` é **superset** da guarda para checagem por página. A guarda sozinha **deixa passar travessão, `;` em prosa e HTML literal em campo texto-puro** — testado, os três passaram limpos por ela e os três foram pegos pelo `audit-editorial`. Como o sub-agent de criação PULA o `audit-editorial` em modo batch (ver `pagina-produto-criar`, passo 11), rodar só a guarda aqui deixava esses três sem checagem alguma no caminho default (sem `--audit`). É buraco de cobertura, não redundância.

   | defeito | `pagina-produto-guardas` | `audit-editorial` |
   |---|---|---|
   | fence, `shortDescription` >250, `pros`/`cons` >180 | ✓ | ✓ |
   | 4 `<p>` com os 4 rótulos | ✓ | ✓ (`fullReview-prefixo-e-ancoras`) |
   | travessão · `;` em prosa · HTML em texto-puro · termo banido · YAML inválido | **✗** | ✓ |

   A guarda continua no fluxo porque tem o modo `--rede` (agregação por site com dono/live), que o `audit-editorial` não tem.

   Por que existem, com o caso que originou cada uma:
   - **Fence** — 1 de 6 saiu sem o `---` de fechamento (Bárbara, `melhoressuplementos/flora-nativa-b12`, 2026-06-15): o block scalar do `fullReview` correu até o EOF, o build quebrou com `asin: Required / name: Required`, e **passou silencioso porque o sub-agent reportou `ok:true`**. É o auto-check do sub-agent que não basta.
   - **Parágrafos** — o padrão é sempre 5 `<p>` com 4 rotulados, o órfão no "Por que gostamos". Medido 2026-07-26: 93 de 2.681 páginas (3,5%).
   - **Tamanho** — o sub-agent conta caractere de cabeça e **erra ~14% das vezes**: 3 de 22 páginas com `shortDescription` em 256-264 chars apesar do cap 250 na régua, pego só pelo `--audit`.

   ⚠️ **A guarda impede defeito NOVO, não limpa o antigo.** Re-medido em 2026-07-30: **93 → 74**, com `cozinhaideal` em 24 nas duas contagens e `melhoraspirador-com` em 9 nas duas. O que foi medido em 26/07 seguiu no ar. É exatamente o buraco que o modo `--rede` fecha — sem varredura, medir não conserta.

   ⛔ **Não reescreva isso inline.** Em 2026-07-30 duas implementações do mesmo check discordaram (6 achados × 74) por dois bugs de porte: `\Z` não existe em JS, e o regex só casava `fullReview: |` quando a rede tem **6 formatos de scalar** (`>-` em 1885 páginas, `|-`, `|`, `"<p`, `>`, `'<p`). Guarda que precisa ser redigitada mede outra coisa a cada vez.

   ⚠️ **Reprovação não é sinal de conteúdo ruim até ser investigada.** Reprovar bloqueia o commit, então falso positivo custa retrabalho e nunca dado corrompido. Se a guarda estiver errada, conserte o script.

   **Conserto por tipo:** parágrafo órfão → fundir no "Por que gostamos" (determinístico, mais barato que re-disparar). Tamanho → re-disparar o sub-agent isolado pedindo só aquele campo (máx 2 tentativas), depois trim mecânico da última frase. Fence 1 → anexar `\n---\n` e reconferir; 0 ou >2 → re-disparar.

   **Varredura da rede** (o snippet só via o lote da vez, e é assim que defeito escapa e fica):
   ```bash
   bun scripts/pagina-produto-guardas.ts --rede     # agrupa por site com dono e live
   ```

   ```bash
   git commit -m "feat({site}): preenche {N} páginas individuais em batch via skill" \
     -m "Co-Authored-By: {modelo da sessão} <noreply@anthropic.com>"
   ```

   Sem `--no-verify` (corrigido v1.33.0): o hook pre-commit só bloqueia `.mdx` de `reviews/` (e `.html` de guides/pages) — páginas individuais vivem em `products/` e passam limpo, igual na skill individual `pagina-produto-criar`.

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
    - **A camada mecânica JÁ PASSOU limpa no passo 9** (`audit-editorial.ts`
      rodou por slug e o commit só aconteceu porque não havia `error`).
      **NÃO re-rode `audit-editorial.ts`** — gaste o contexto no JULGAMENTO:
      claim-vs-bible, voz-comprador implícita, voz-citação, naturalidade,
      duplicata-cross-site, chavões, superlativo. Se desconfiar de um achado
      mecânico específico, confira aquele campo à mão em vez de re-rodar tudo.
      (Antes de 2026-07-31 os N sub-agents re-rodavam o script: 1 tool call e
      uma leitura de arquivo por agente, jogadas fora.)
    - Faça o audit completo (ler .mdx + bíblia, gerar relatório com
      errors/warnings/info)
    - **CONSERTE o que passa no TESTE DA FRASE NOVA** (seção homônima da
      `pagina-produto-auditar`, canon Marcelo 2026-08-06). A pergunta é uma só:
      **dá pra consertar sem escrever nenhuma frase nova?** Apagar um termo que
      a bíblia não tem, trocar por como a bíblia chama, restaurar um qualificador
      que ela exige → **aplica**. Se o substituto for redação sua → **reporta**.
      Backup antes, `Edit` cirúrgico, re-audita o que tocou, e **reverte do
      backup** se não convergir em ≤3 tentativas. ⚠️ **`warn` NUNCA aplica**,
      nem parecendo óbvio: frase colada na página irmã, coloquialismo acima do
      teto e redundância bullet↔parágrafo são report-only, sem exceção
      (canon 2026-07-10, que esta régua refina e não revoga). ⚠️ Se a página
      contradiz a `decisaoEditorial` **mas obedece outro campo da mesma bíblia**,
      NÃO toque na página — o alvo é a bíblia, e o relatório aponta pra lá.
    - **Escreva o relatório `.md`** em `docs/biblias-v2/.audits/products/{site}-{slug}-last.md`,
      distinguindo **CORRIGIDO** (com o diff) de **REPORTADO**
    - **NÃO faça** `git add`, `git commit`, `git push`, nem
      `painel-vps-pull.sh` — skill mãe controla isso
    - Retorne: `{ok: true, slug, severity, corrigidos: [{campo, de, para}], issues: [...]}`

    Skill mãe agrega:
    - **Páginas SEM issues críticos**: aprovadas
    - **Páginas com warnings**: lista no report final pra user revisar
    - **Páginas com errors críticos que sobraram** (os que não passaram no teste):
      alerta que precisam revisão individual via `pagina-produto-criar` em modo rewrite

    **12b. RE-RODAR AS DUAS GUARDAS nas páginas que o audit CONSERTOU (obrigatório).**

    O conserto entra **depois** do passo 9, ou seja, fora de qualquer guarda. Sem
    este passo, um `Edit` pode estourar o cap de tamanho, quebrar o fence ou
    deixar o `fullReview` fora da forma canônica e **ir pro commit sem ninguém
    olhar** — exatamente o buraco que as guardas existem pra fechar.

    ```bash
    # SÓ os slugs que voltaram com corrigidos[] não-vazio
    SITE={site}; FAIL=0
    for S in {slugs-corrigidos}; do
      bun scripts/audit-editorial.ts "$SITE/$S" --json 2>/dev/null | python3 -c "
    import json,sys
    raw=sys.stdin.read().strip()
    if not raw.startswith('{'): print('  ⛔ $S sem JSON →',raw[:80]); sys.exit(1)
    d=json.loads(raw); bad=[f for f in (d.get('findings') or []) if f.get('sev') in ('error','warn')]
    if bad:
        print('  ⛔ '+d['slug'])
        for f in bad: print(f\"       {f['sev']:5} {f['rule']:22} {str(f.get('detail',''))[:60]}\")
        sys.exit(1)
    " || FAIL=1
    done
    bun scripts/pagina-produto-guardas.ts {site} {slugs-corrigidos}
    ```

    Reprovou? **Reverta aquela página do backup** que o sub-agent criou e mova o
    achado pra REPORTADO. Conserto que não passa na guarda não vale o risco.

    ⚠️ **Antes de rodar as guardas, reconcilie o `git status` contra os `corrigidos[]`
    reportados — nos DOIS sentidos.** O passo 9 já cobre "reportou e não escreveu";
    aqui o que morde é o inverso:

    ```bash
    git status --short sites/{site}/src/content/products/    # modificados de FATO
    ```

    - **modificado E reportado** → normal, entra no 12b.
    - **reportado E não modificado** → sub-agent alucinou o conserto. Investigue.
    - **modificado E NÃO reportado** → ⛔ **edição órfã.** Trate como suspeita: o
      agente editou e não chegou a validar. Rode as guardas nela **e** confira a
      edição contra a bíblia à mão antes de commitar.

    Caso real 2026-08-06 (`somprofissional/lg-xboom-grab`): o sub-agent de auditoria
    morreu por erro de API **depois** do `Edit` e **antes** de re-auditar e de escrever
    o relatório. Deixou o `.mdx` modificado, sem relatório e sem re-checagem — e o
    retorno dele foi um erro, não um `corrigidos[]`. Só apareceu no `git status`. A
    edição estava certa (era um RESTAURAR com texto literal da bíblia), mas isso foi
    **sorte**: nada no fluxo garantia. Quando a auditoria de uma página morre assim,
    termine-a **inline** em vez de re-disparar o sub-agent — o `Edit` dele já está no
    disco, e um agente novo re-audita um arquivo que já mudou sem saber disso.

    **12c.** Skill mãe faz **DOIS commits separados**, nesta ordem:
    1. os `.mdx` consertados (se houver), com a mensagem dizendo o que foi trocado
    2. os `.md` de audit
    Lista específica em cada `git add`, nunca glob. Depois push + VPS pull.

    Separar importa: o commit de conteúdo tem que ser legível sozinho no
    histórico e revertível sem levar os relatórios junto.

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
      🔧 {slug-3} → 2 fatos CORRIGIDOS + 1 warning
      ⚠ {slug-4} → audit: 1 error que exige decisão → revisar via pagina-produto-criar

    CORRIGIDO NA HORA ({F}) — passou no teste da frase nova:
      {slug-3} · specs[3]  "0,5ms MPRT (1ms GtG)" → "0,5ms MPRT"
                           (o GtG só existe no bloco global do modelo irmão)
      {slug-3} · subtitle  + "pela DisplayPort"
                           (a HDMI do mesmo monitor faz 144)

    FALHAS NO BATCH ({M}):
      ✗ {slug-x} — {erro do sub-agent}

    PULADOS ({Z}):
      ⏭️  {slug-y} (stub parcial)
      ⏭️  {slug-z} (já preenchido)

    📦 Commit (criação): {hash-1}
    📦 Commit (fixes):   {hash-2}   ← só se houve conserto
    📦 Commit (audits):  {hash-3}
    🔄 VPS sincronizado: {OK | bloqueado}
    🔍 Audits: {ok} OK / {fix} corrigidos / {warn} warnings / {err} críticos abertos
    ```

    **Todo conserto aplicado vai no report com o de→para**, não só a contagem. O
    usuário precisa poder discordar de uma troca sem abrir o diff do git.

    Erros críticos que sobraram NÃO bloqueiam o commit lote (já foi). Sinalizam
    revisão individual depois — e sobraram justamente porque o substituto era
    decisão editorial, não porque foram ignorados.

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

**A régua editorial NÃO é re-escrita aqui — o sub-agent LÊ a `pagina-produto-criar/SKILL.md` e a executa à risca (régua v1.34.0, fonte única).** Resumo inline de régua = proibido: era a fonte do drift (o antigo inline tinha ficado pra trás em **Peso por fonte**, **Filtros editoriais** eco/origem, **banner de descontinuado** e atribuição-elíptica v1.21.1). Lendo o arquivo vivo, o batch herda SEMPRE a régua atual da individual, sem drift. Sub-agent do Agent tool não consegue invocar a Skill tool (são N agents PARALELOS), por isso ele LÊ o arquivo em vez de invocar.

```
Tarefa: gerar os 6 campos editoriais (subtitle, shortDescription, pros, cons,
specs, fullReview) da página individual de UM produto, em conversa fresh isolada.

PASSO 1 — LEIA a régua canônica e EXECUTE À RISCA (não improvise, não use resumo de memória):
- Read `.claude/skills/pagina-produto-criar/SKILL.md` e execute o **Fluxo, passos 2 a 11**:
  Read .mdx → parse frontmatter → Read bíblia → affiliateTag → montar amazonUrl →
  anti-dup vs review-no-artigo → gerar os 6 campos pela seção "Os 6 campos" → validar →
  backup → Write + AUTO-CHECK de fence (`grep -c '^---$'` == 2).
  TODA a régua daquele arquivo vale; reforço as que costumam escapar:
  benefício-first + hard caps (shortDescription ≤250, pros/cons ≤180 texto-puro),
  subtitle = ângulo (v1.34, vinculante se o stub já traz subtitle/badge),
  destilação categoria D (voz-comprador implícita → observação analítica),
  **Peso por fonte** (specsAmazon sozinho NÃO vira pró central, só tabela specs),
  **Filtros editoriais** (dropar specs ambientais/Energy Star + origem de fabricação),
  **banner de descontinuado** (setar `descontinuado:{asin,nome}` no frontmatter se a bíblia sinalizar),
  atribuição-elíptica/voz-citação = muleta (spec factual vai direto), tom natural (rótulo real),
  sem travessão, sem `;`, campos texto-puro, health-YMYL, âncora = NOME do produto (nunca CTA).
- Read `docs/painel/_data/chavoes-por-nicho.json` → use `_genericos` + bloco do `{{site}}.niche`
  (de `docs/painel/sites-meta.json`) como guard rail.

Inputs deste produto (já resolvidos pela skill-mãe — NÃO faça parse de args nem git pull):
- Site: {{site}} · Slug: {{slug}} · ASIN: {{asin}} · AffiliateTag: {{tag}} (pode ser '')

OVERRIDES DO BATCH (sobrepõem o Fluxo da individual):
- ⛔⛔ **REGRA ZERO — NÃO RODE NENHUM COMANDO GIT.** Você NÃO tem os passos de git da
  individual. É **PROIBIDO** `git add`/`git commit`/`git push`/`git stash`/`git pull` E
  `painel-vps-pull.sh`. Pule o passo 1.5 (git pull) E os passos 12-13 inteiros. **A
  skill-mãe faz TODO o git num commit-lote no fim** — você só faz `Read` + `cp` (backup) +
  `Write` do `.mdx`. ⚠️ A `pagina-produto-criar.SKILL.md` que você leu TEM passos de
  commit/push (12-13) — IGNORE-OS. O impulso de "seguir o fluxo da individual e commitar" é
  exatamente o BUG: N sub-agents commitando em paralelo = race condition que corrompe o
  histórico (caso real 2026-06-28: 2 de 11 sub-agents commitaram/pusharam no meio do batch e
  bagunçaram a árvore). Se você se pegar prestes a rodar git, PARE — não é seu trabalho.
- Isolamento: você vê SÓ este produto. Não compare com outros sites nem "divirja ângulo" de
  propósito (dedup cross-site é trabalho da auditoria).
- Você MESMO escreve o `.mdx` (passos 10-11 da individual: backup + Write + fence check).

SAÍDA — reporte curto:
- Sucesso: { ok: true, slug: '{{slug}}', path: '...', summary: 'subtitle 67c / fullReview 1842c / 3 links' }
- Erro:    { ok: false, slug: '{{slug}}', error: 'motivo curto' }
```

Se o ambiente impedir o sub-agent de ler `pagina-produto-criar/SKILL.md` (raro, VPS-only), a skill-mãe lê o arquivo e cola o conteúdo no prompt — NUNCA cair num resumo de memória.

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
| Audit pós-criação | Manual via `pagina-produto-auditar`, read-only | Opt-in via `--audit`, e **conserta o fato que passa no teste da frase nova** (warn segue report-only) |
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

### 5. Pedir confirmação `S/N` (atrito desnecessário)
**NÃO pergunte `S/N` antes de disparar** (mudança 2026-07-24). A régua antiga exigia confirmação; hoje a barreira é o pré-flight (passos 2-4), que aborta em site inexistente, zero stubs vazios ou bíblia incompleta. Se o pré-flight passou, imprime o plano (transparência) e dispara direto. Perguntar de novo só duplica o beat que o pré-flight já dá. Ambiguidade real (slug/ASIN que não casa com stub) é abort do passo 2/3, não pedido de confirmação.

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

A skill INDIVIDUAL `pagina-produto-criar` continua sincronizada com `agent-prompts.json:create_product_page` (espelho do painel/API) — a SKILL.md individual é a fonte viva editorial. Sub-agents do batch seguem a mesma régua (paridade garantida porque sub-agent prompt cita a SKILL.md individual como fonte da verdade).

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

### Auto-check de capitalização + duplicação (régua v1.18.3, canon 2026-05-28)

**Bug-class real** (caso `melhorpretreino` commit `a72e7d9`): substituições mecânicas podem causar duplicação contígua, bullets minúsculos ou minúscula após ponto.

**Auto-check obrigatório ANTES de gravar**:

```python
import re

# Para cada campo gerado (shortDescription, fullReview, pros, cons, specs.value):

# 14a) Duplicação contígua (>=8 chars repetidos em sequência)
for m in re.finditer(r'([a-zA-ZÀ-ÿ\s]{8,40})\1', campo):
    print(f"⚠ duplicação: {m.group(0)}")
    # → Reescreve removendo a metade duplicada

# 14b) Bullet começa com minúscula (em pros/cons)
for bullet in pros + cons:
    if re.match(r'<strong>[a-záéíóúâêôãõàèìòùç]', bullet):
        print(f"⚠ bullet minúsculo: {bullet[:60]}")
        # → Capitalize primeira letra dentro de <strong>...</strong>

# 14c) Minúscula após ponto (texto editorial — excluir URLs)
for m in re.finditer(r'\. ([a-záéíóúâêôãõàèìòùç])', campo):
    ctx = campo[max(0,m.start()-30):m.end()+30]
    if 'http' in ctx or 'amazon.com.br' in ctx: continue
    if re.search(r'\d+\. \w', ctx[:50]): continue  # lista numerada
    print(f"⚠ minúsc após ponto: ...{ctx}...")
    # → Capitalize a letra (.+ espaço + Letra)
```

**Exemplos reais** (commit a72e7d9, melhorpretreino):
- 14a: `"sem empilhar suplementos sem empilhar suplementos"`
- 14b: `"<strong>aminoácidos essenciais na fórmula</strong>"` (era BCAAs → minúsculo)
- 14c: `"(maior dose declarada). pra emagrecer onde"` (era "em cutting" → minúsculo)

Se achar qualquer bug: corrija ANTES de gravar. Não bloqueia geração, mas evita commit com erro.

## Limitação intrínseca conhecida

1. **Sem progress logging incremental** — sub-agents só reportam no fim do trabalho, não emitem "[3/10] processando..." conforme andam. Pra batch de 5 min, aceitável; pra batch de 30 min (50+ produtos), user fica no escuro. Mitigação: dividir batches grandes em levas explícitas (skill mãe loga "Leva 1/3 começando").

2. **Anti-duplicate cross-páginas IMPOSSÍVEL no paralelo** — sub-agents isolados não veem outras páginas do mesmo site sendo criadas. Se 2 produtos similares (ex: 2 whey isolados da mesma marca) processam simultâneo, podem ter parágrafos parecidos. **Skill individual atual também não faz isso**, então paridade total. Se virar problema real (raro), adicionar passo extra: skill mãe carrega contexto cumulativo após cada leva (mas perde benefício do paralelo).

3. **Limite de paralelismo do harness** ≈10 sub-agents simultâneos. Batches >10 são divididos em levas. Não é limite formal documentado — assumido conservador. Pode ser mais (15-20) na prática, mas evita timeouts/throttling.

4. **Falha silenciosa possível** — sub-agent pode retornar `{ok: true}` mas o `.mdx` ficou com problema sutil. **A subclasse MECÂNICA já é pega pela skill-mãe sempre** (guarda de fence = frontmatter quebrado; guarda de tamanho = shortDescription/pros/cons estourados — ambas no passo 9, determinísticas, com re-dispatch). Resta a subclasse de JULGAMENTO editorial (travessão escapado, HTML inválido em campo texto-puro, voz-citação burocrática, claim-vs-bible) — risco real mas baixo (mesma régua + sub-agent fresh do Opus). Mitigação pra ESSA: rodar com `--audit`, que desde 2026-08-06 não só detecta como **conserta o erro de fato que passa no teste da frase nova** (passo 12). Sem `--audit`, user audita quando quiser — paridade com a individual (que também não auto-audita). Ou seja: fence+tamanho são rede automática do passo 9; `--audit` é a rede do julgamento, e nela o fato de direção única fecha sozinho enquanto o que exige redação vai pro relatório.

   ⚠️ **Medição que motivou o auto-fix** (4 batches de 10 páginas em 2026-08-06, `melhorcaixadesom`, `somprofissional`, `melhordosom`, `compraguia`): as guardas do passo 9 pegaram **zero** dos ~23 claims sem lastro. Todos vieram do `--audit`. A única coisa que a guarda achou foi 1 parágrafo órfão — e era falso positivo. Ou seja, sem `--audit` o batch **não tem rede factual nenhuma**, e com ele metade dos achados era substituição de uma palavra que custava um round-trip inteiro pra aplicar.

5. **Sobreposição CROSS-SITE ~20-25% é ESPERADA e SEO-aceitável — NÃO auto-divergir (canon Marcelo 2026-07-10).** Quando o mesmo produto (mesma bíblia) vira página em sites irmãos, a criação ISOLADA converge naturalmente em ~20-25% de texto idêntico (⇒ ~75-80% diferente). Medido em 3 nichos: aspirador (masp↔escritorioecasa 74% dif), airfryer (melhorairfryer↔-com 73%), impressora (melhorimpressora↔impressoraideal 80%). **Nunca chega aos ~99% que a divergência explícita atinge — e não deveria tentar.** A razão é estrutural, não falta de "liberdade" do Opus: dois sub-agents destilando a MESMA bíblia chegam na forma natural de dizer o mesmo FATO ("bateria de íon de lítio com autonomia de até 25 minutos…"). Mais liberdade não move esse piso; só divergência explícita move.
   - **Política:** ~20% de sobreposição **não prejudica SEO** em página de produto (ativo secundário; indexada + self-canonical + em `sitemap-produtos`, mas de baixo risco; o footprint da rede — template/dono/linkagem/personas — pesa muito mais que 20% de texto igual). O grosso dos 20% é FATO (spec/autonomia/filtro), que o Google espera parecido entre qualquer site descrevendo o mesmo produto.
   - **⛔ NÃO faça create-already-diverging** (mandar o sub-agent LER as irmãs e divergir na criação): quebra a Isolação, empurra a prosa pro COLOQUIAL (a fuga de 6-gramas vira gíria) e gera warns de naturalidade. Já custou caro (o incidente que gerou esta nota). Isolação é o default correto.
   - **Quem detecta:** o `--audit` (`duplicata-cross-site`). Divergir é **decisão HUMANA**, e só compensa nos **outliers abaixo de ~60% diferente** (metade do texto igual = near-duplicate de verdade). O regime ≥70% fica como está.
