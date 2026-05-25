---
name: artigo-reviews-auditar
description: Audita TODOS os reviews do artigo como CONJUNTO (cross-produto). Aceita URL do painel (editor-artigo.html?site=X&slug=Y) OU args canônicos site/slug-artigo. Detecta tone-clone, redundância, buyer-reference, claim-vs-lineup-fato (comparações factualmente erradas), links incorretos. Output: relatório em chat com diffs por produto, user aplica granular ("aplica produto 2") ou em lote.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida):
- `https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio`
- Extrai `site` e `slug` do artigo

**B) Args canônicos**:
- `melhorimpressora/melhor-impressora-custo-beneficio`

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B.

# Auditar/melhorar reviews em artigo (cross-produto)

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:improve_reviews`.
> Conteúdo essencial duplicado abaixo pra autocontenção; em caso de divergência, o prompt canônico ganha.

Você é o editor de reviews no estilo Wirecutter. O usuário passa `{site}/{slug}` de um artigo cujos reviews já foram preenchidos (≥2 produtos com `fullReview`). Sua função é **analisar todos os reviews JUNTOS** (não um isolado por vez), identificar incongruências cross-produto, e **propor correções cirúrgicas** pra user aprovar produto-a-produto.

## Diferença vs `artigo-review-criar`

- `artigo-review-criar`: gera review do zero pra **1 produto** (sem ver os outros)
- `artigo-reviews-auditar`: analisa **TODOS** os reviews simultaneamente, detecta padrões cross-produto que skill per-produto não pode pegar

Usar **a cada 3 produtos preenchidos** ou **no final do artigo antes de travar** (`contentLocked: true`). Não rodar a cada produto isolado — desperdiça.

## Pré-requisitos

- Artigo existe em `sites/{site}/src/content/reviews/{slug}.mdx`
- **≥2 produtos com `fullReview` preenchido** (cross-product não faz sentido com 1)
- Todas as bíblias dos produtos existem em `docs/biblias-v2/<ASIN>.json`
- Artigo NÃO travado (`contentLocked: false` ou ausente no frontmatter)
- `affiliateTag` do site existe em `sites/{site}/src/config.ts` (vazia OU preenchida, ambas OK — define a regra de validação dos links)

Se algum requisito falhar, abortar com mensagem clara.

## Invariantes

- **EDIÇÃO MÍNIMA**: preserve wording original sempre que possível. Só proponha mudança onde tem violação clara de critério.
- **CONVERGÊNCIA**: produto que já passa em todos critérios vai pra `passed`, NÃO pra `changes`. Re-runs no mesmo artigo não devem gerar mudanças aleatórias.
- **Mexer em 1 campo é OK**: pode propor mudança só em `pros`, deixar `fullReview` e `cons` intactos.
- **null É LITERAL** quando inalterado. NUNCA `''` ou `[]`.
- **Tamanho de pros/cons**: preserve número de itens. Max +1 novo se claro da bíblia. NÃO reordene itens existentes.
- **Sem travessão (—).**
- **Sem superlativo sem evidência.**
- **Preservar estrutura do `fullReview`**: 4 parágrafos com prefixos exatos (`Para quem é:`, `Por que gostamos:`, `Pontos de atenção:`, `Resumo:`). `Por que gostamos` pode ter 2 parágrafos.
- **Preservar formato pros/cons**: `<strong>Título</strong>: explicação`.
- **Nunca inventar dados**: cada claim com origem rastreável na bíblia.

## Fluxo

1. **Parse args**: aceita `{site}/{slug}` canônico. Ex: `melhorimpressora/melhor-impressora-custo-beneficio`.

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   git stash push -m "skill-artigo-reviews-auditar-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Painel VPS commita+pusha automaticamente quando user cria/edita conteúdo na UI; Mac local pode estar 5-30s atrás. Sem este pull, skill pode ler estado stale e abortar com falso "X não existe localmente". Se pull falhar (rede offline, conflito), seguir mesmo assim.

2. **Read artigo**: `Read sites/{site}/src/content/reviews/{slug}.mdx`. Se 404, abortar. Se `contentLocked: true` no frontmatter, abortar com mensagem "Artigo travado — destrave antes".

3. **Parsear `products[]` do frontmatter**: extrair lista de ASINs + campos editoriais (`name`, `schemaPrice`, `subtitle`, `shortDescription`, `pros`, `cons`, `specs`, `fullReview`). Filtrar só produtos com `fullReview` não-vazio.

4. **Validar count**: se `productsWithReview.length < 2`, abortar — cross-product não faz sentido.

5. **Read bíblias**: pra cada ASIN, `Read docs/biblias-v2/<ASIN>.json`. Se alguma faltar, abortar listando quais.

6. **Read `affiliateTag`**: `sites/{site}/src/config.ts` via regex. Vazia → links Amazon devem ser crus. Preenchida → `?tag={tag}&linkCode=ogi&th=1&psc=1`.

7. **Analisar cross-produto** pelos 8 critérios (seção abaixo). Gerar `changes` (por produto com proposta) e `passed` (produtos OK).

8. **Reportar em chat** no formato canônico (seção "Formato do relatório").

9. **Esperar resposta do user**: granularidade per-produto. Possíveis comandos:
   - `aplica tudo` / `aplica todos` → todas as mudanças
   - `aplica produto 1, 3` → granular por número
   - `aplica L1250 e 107W` → granular por nome (fuzzy match)
   - `rejeita tudo` → encerra sem mudanças
   - `rejeita produto 2` → todas exceto produto 2

10. **Backup**: `docs/painel/.painel-backups/{YYYY-MM-DD}/article-{site}-{slug}-{HHMMSS}-improve.mdx`. Pattern paralelo ao painel pra aparecer no card "Histórico de versões".

11. **Aplicar mudanças**: usar `Edit` cirúrgico no `.mdx` pra cada produto aprovado.
    - Preservar produtos NÃO-alvo intactos (não tocar)
    - Preservar block scalar `|` do fullReview (não usar parseYaml/stringifyYaml)
    - Aplicar `newFullReview`, `newPros`, `newCons` quando não-null

12. **Build local**: `pnpm --filter {site} build` pra validar Zod do Astro. Se falhar, reverter do backup e reportar erro.

13. **Git add + commit + push + dispatch VPS pull**:
    ```bash
    git add sites/{site}/src/content/reviews/{slug}.mdx
    git commit --no-verify -m "fix({site}): auditoria cross-produto de {slug} via skill"
    git push origin main
    bash scripts/painel-vps-pull.sh
    ```
    `--no-verify` necessário porque pre-commit hook bloqueia commits diretos de `.mdx` em `sites/*/src/content/reviews/` — a skill é o caminho oficial alternativo.
    `painel-vps-pull.sh` substitui SSH direto pra funcionar pra Marcelo e Bárbara (script usa Basic Auth do painel via `.env.painel-skills`).

14. **Reportar resultado**: counts de produtos aplicados + path do backup.

## Os 8 critérios da análise

### 1. `tone-clone` — abertura/frase idêntica entre produtos

**NÃO flagrar** (são intencionais):
- Prefixos `Para quem é:`, `Por que gostamos:`, `Pontos de atenção:`, `Resumo:` — template editorial
- Abertura `A [Produto X] é para quem...` — padrão Wirecutter

**FLAGRAR**:
- Mesma frase concreta em 2+ reviews (claim copiado)
- Parágrafos quase idênticos só trocando nome do produto
- Explicação de conceito repetida (ex: "EcoTank é um sistema de tanque..." em 3 reviews em vez de 1)

### 2. `redundancy` — conceito explicado várias vezes

Reviews 2+ devem **referenciar** conceitos já explicados em reviews anteriores do mesmo artigo, não re-explicar:
- ✅ "como mencionado, o sistema EcoTank..."
- ✅ "conforme a L3250 desta lista, o tanque de tinta..."
- ❌ "EcoTank é um sistema sem cartuchos onde você abre uma tampa e..." (explicação completa em review 3 depois de já ter feito em review 1)

### 3. `incoherence` — contradição interna

Flag só se for **CONTRADIÇÃO CLARA**:
- ✅ pros diz "alto rendimento" mas fullReview diz "gasta muito"
- ❌ NÃO é contradição: fullReview menciona "doméstico", pros menciona "home office" (compatíveis)

Verifique:
- `Resumo` bate semanticamente com `Para quem é` e `Por que gostamos`?
- `Para quem é` menciona perfil **concreto** (uso, espaço, frequência)?

### 4. `quality` — pros vagos sem dado concreto

Pros com `<strong>X</strong>: explicação` precisam ter **dado verificável** na explicação:
- ❌ `<strong>Rendimento alto</strong>: a impressora rende muito`
- ✅ `<strong>Rendimento elevado por kit</strong>: 4.500 páginas em preto e 7.500 coloridas por kit T544`

Parágrafos NÃO devem virar wall-of-text (>5-6 frases). `Por que gostamos` que estourou pode dividir em 2 parágrafos: features-chave + specs gerais.

### 5. `buyer-reference` — citações EXPLÍCITAS de comprador/Amazon/avaliações

**REMOÇÃO OBRIGATÓRIA** (citação explícita):
- ❌ "Compradores recorrentemente citam..."
- ❌ "Um comprador relata..."
- ❌ "Bem avaliada por usuários"
- ❌ "Histórico extenso de compradores satisfeitos"
- ❌ "#1 mais vendido da Amazon" / "campeão de vendas"
- ❌ "X estrelas / Y avaliações na Amazon"

**OK (claims de mercado, NÃO flag)**:
- ✅ "Uma das mais populares do Brasil" (claim de mercado, não Amazon)
- ✅ "Consagrada no segmento"
- ✅ "Modelo estabelecido no mercado"
- ✅ "Top de vendas da categoria"

Reescreva pra voz analítica APENAS quando houver citação explícita.

### 6. `links-incorretos` — target 2-3 links por review

Cada review deve ter **2-3 links Amazon**, posições preferidas:
- 1 em `Para quem é` (no nome do produto)
- 1 em `Por que gostamos` (primeira menção)
- 1 em `Resumo`

Formato esperado (depende de `affiliateTag` do site):
- **Tag preenchida**: `<a href="https://www.amazon.com.br/dp/{ASIN}?tag={tag}&linkCode=ogi&th=1&psc=1" rel="nofollow" target="_blank">Nome do Produto</a>`
- **Tag vazia**: `<a href="https://www.amazon.com.br/dp/{ASIN}" rel="nofollow" target="_blank">Nome do Produto</a>` (URL crua)

Flag se: total fora de 2-3 OU tag/formato errado OU `target="_blank"` ausente OU `rel="nofollow"` ausente.

### 7. `claim-vs-lineup-fato` — comparações com lineup factualmente erradas

**Específico cross-produto, fora do `improve_reviews` canônico** mas valioso.

Verificar comparações de preço/spec entre produtos do lineup contra dados reais:
- Se review diz "menor preço entre tanques", confirmar via `schemaPrice` que é verdade
- Se review diz "única laser desta seleção", confirmar via lineup que é verdade
- Se review diz "rende 3x mais que produto X", confirmar via specs/bíblia

**Caso real (commit a58a33b)**: L1250 dizia "menor preço entre opções de tanque" mas Smart Tank 581 (R$ 820) é mais barata que L1250 (R$ 850). Comparação falsa, requer correção.

Sugestão de fix: reformular pra escopo verdadeiro ("menor preço entre as Epson EcoTank" em vez de "entre as opções de tanque") ou remover o claim.

### 8. `voz-citacao-ficha-tecnica` — marcadores de procedência burocráticos

Detecta quando o modelo copiou da bíblia sem destilar. Diferente da #5 `buyer-reference` (que cobre cita comprador/Amazon explícita) — esta cobre **cita fonte burocrática** ("alérgenos confirmam", "atributos declaram", "conforme tipo de dieta").

**Padrões pra grep**:
- "alérgenos da Amazon confirmam"
- "atributos de material declaram"
- "conforme tipo de dieta"
- "conforme declarado pelo fabricante" / "conforme o fabricante" (sem qualificar)
- "apontada pelo fabricante como"
- "relato recorrente nas opiniões" / "segundo relatos de compradores"
- "citada como motivo de preferência por um comprador"
- "datasheet" / "no datasheet"
- "anúncio Amazon" / "apesar do anúncio Amazon listar"

**Severidade: Médio** (propor mudança) — porque pode ser editorial OK em casos específicos.

Régua: voz-citação OK SÓ quando atende AS DUAS condições:
1. **(a)** qualifica claim que SÓ o fabricante pode fazer (rendimento, garantia interna, certificação proprietária)
2. **(b)** adiciona valor editorial ao leitor (calibra expectativa, sinaliza honestidade, faz crítica útil)

**✓ Editorial OK** (não flag): "rende até 4.500 páginas em preto, segundo a Epson" — claim só-fabricante + qualifica rendimento.

**❌ Burocrática** (flag): "alérgenos da Amazon confirmam ausência de glúten" → propor "sem glúten".

Reportar com sugestão de reformulação destilada. User decide se aceita.

## Filtros de severidade

- **Crítico** (sempre propor mudança): buyer-reference explícita, claim-vs-lineup-fato errado, links-incorretos (tag errada), travessão, html-invalido
- **Médio** (propor mudança): tone-clone óbvio, redundancy de conceito, quality vago, incoherence, voz-citacao-ficha-tecnica burocrática
- **Info** (mencionar mas não obrigatório aplicar): parágrafo no limite de tamanho, posição de link sub-ótima

## Formato do relatório

Apresentar em chat após análise:

```markdown
# Auditoria cross-produto: {site}/{slug}

**Lineup**: {N} produtos analisados, {N-X} com fullReview preenchido (auditados)
**Resultado**: {X} produtos com mudanças propostas, {Y} passaram limpos

---

## ✅ Passaram (sem mudanças)

- {Nome Produto A} (ASIN B0...)
- {Nome Produto B} (ASIN B0...)

## 🟡 Mudanças propostas

### 1. {Nome Produto C} (ASIN B0...) — {N} issues

**Issue 1** `[tone-clone]` `fullReview`
- **Problema**: ...
- **Fix proposto**: ...

**Issue 2** `[quality]` `pros[2]`
- **Problema**: ...
- **Fix proposto**: ...

**Diff fullReview** (se mudou):
```html
ANTES: <p>...</p>
DEPOIS: <p>...</p>
```

**Diff pros** (se mudou):
- ❌ "<strong>...</strong>: ..."
- ✅ "<strong>...</strong>: ..."

---

### 2. {Nome Produto D} ...

(idem)

---

## Como aplicar

Me responda com um destes:
- **"aplica tudo"** → todas as mudanças propostas
- **"aplica produto 1, 3"** → granular por número
- **"aplica L1250 e 107W"** → por nome (fuzzy)
- **"rejeita produto 2"** → todas exceto produto 2
- **"rejeita tudo"** → encerra sem mudanças
- **"refaz produto 1 issue 2"** → me peça pra repensar uma issue específica
```

## Apply: como editar o .mdx

**Estratégia**: `Edit` cirúrgico, **nunca** parseYaml/stringifyYaml (risco de bagunçar block scalar `|` do fullReview).

Pra cada produto aprovado:

1. **Se `newFullReview != null`**: localizar bloco do produto no .mdx (`- name: "Nome"` até o próximo `- name:` ou `---`). Substituir TODOS os parágrafos dentro do `fullReview: |` pela nova versão. Manter a indentação de 6 espaços.

2. **Se `newPros != null`**: substituir o array `pros:` inteiro do produto. Manter indentação.

3. **Se `newCons != null`**: idem `cons:`.

4. **NÃO** alterar outros campos (`name`, `asin`, `image`, `imageAlt`, `badge`, `schemaPrice`, `store`, `subtitle`, `shortDescription`, `specs`).

5. **NÃO** alterar outros produtos do lineup.

## Validar antes de salvar

- Sem travessão (—) em nenhum campo
- HTML allowlist em fullReview: `<p>`, `<strong>`, `<em>`, `<a>`
- Tag correta nos links (ou crua se config vazia)
- Voz analítica (zero compradores/Amazon/reviews/avaliações)
- Anti-duplicate vs página individual (não reintroduzir frases que estão no fullReview da página individual)

Depois do Edit, rodar `pnpm --filter {site} build`. Se Zod do Astro falhar (raríssimo), reverter do backup e reportar erro.

## Armadilhas recorrentes

### 1. Re-flagrar estrutura padrão como tone-clone

Prefixos `Para quem é:`, `Por que gostamos:`, etc são intencionais. **Nunca** flaggar.

### 2. Forçar mudanças quando não tem problema real

Se um review está limpo, vai pra `passed`. Não invente issue pra justificar "ter dado análise".

### 3. Quebrar a estrutura de 4 parágrafos

Quando reescrever `fullReview`, manter os 4 prefixos exatos. `Por que gostamos` pode ter 2 parágrafos (1 features-chave + 1 specs gerais), mas os outros 3 devem ter 1 parágrafo cada.

### 4. Aplicar via parseYaml/stringifyYaml

Bagunça o block scalar `|` do `fullReview` (vira string single-line quoted). Use SEMPRE `Edit` cirúrgico.

### 5. Esquecer de validar links

Affiliate tag vazia (sites em construção) → links DEVEM ser crus. Affiliate tag preenchida → DEVEM ter `?tag={tag}&linkCode=ogi&th=1&psc=1`. Validar todos os 2-3 links de cada produto-alvo.

### 6. Propor mudanças contraditórias entre produtos

Se review 1 menciona "compacta", review 2 não pode flagrar review 1 como redundante por dizer "compacta" também — desde que cada um use no contexto próprio (review 1 fala compacta DO PRODUTO; review 2 não menciona).

## Invocação

```
audita os reviews do artigo melhor-impressora-custo-beneficio do melhorimpressora
audita melhorimpressora/melhor-impressora-custo-beneficio
audita os reviews cross-produto desse artigo
```

Args canônico que invoco: `Skill(skill="artigo-reviews-auditar", args="melhorimpressora/melhor-impressora-custo-beneficio")`.

## Limitação intrínseca

Sem schema Zod programático no output (diferente do painel), validação fica editorial — eu sigo as regras. Risco real: propor mudança que viole alguma diretriz por engano. **Mitigação**: você revisa o diff antes de aprovar, e o build do Astro é gate final pós-Edit.

Sem modal de approval visual com diff lado-a-lado, troca pela experiência de chat — você decide produto-a-produto via mensagem. Pra artigos muito grandes (10+ produtos com mudanças propostas), o relatório fica longo no chat.

## Sincronização painel ↔ skill ↔ prompt canônico

```
docs/painel/_data/agent-prompts.json  (SOURCE OF TRUTH editorial)
    └── ops.improve_reviews (handler do painel usa)

.claude/skills/artigo-reviews-auditar/SKILL.md  → segue
```

Quando Marcelo edita regras editoriais (via `agent-config.html` no painel):
- Atualiza `agent-prompts.json` (canônico)
- Esta SKILL.md pode ficar atrasada — atualizar manualmente quando notar drift
