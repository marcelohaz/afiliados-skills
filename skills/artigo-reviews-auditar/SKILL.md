---
name: artigo-reviews-auditar
description: Audita TODOS os reviews do artigo como CONJUNTO (cross-produto). Aceita URL do painel (editor-artigo.html?site=X&slug=Y) OU args canônicos `site/slug-artigo`. 20 critérios — tone-clone, redundância, incoerência, qualidade vaga, buyer-reference explícita, links incorretos, claim-vs-lineup-fato, voz-citação ficha-técnica, voz-comprador implícita, termos técnico-industriais, html-texto-puro, tamanho-escannavel, chavões-por-nicho, concordância PT-BR, template "Para quem é", números-em-excesso, health-absolutes-YMYL, voz-eximir-responsabilidade ("declarado pelo fabricante" muleta). Output: relatório em chat com diffs por produto, user aplica granular ("aplica produto 2") ou em lote.
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

## Nota terminológica — "lineup"

**"lineup" é jargão técnico interno** do projeto pra "lista de produtos do artigo" (campo `products[]` no frontmatter). Aparece em nomes de critérios (`claim-vs-lineup-fato`), endpoints e mensagens técnicas.

**No output editorial dos .mdx, "lineup" é BANIDA** — é uma das palavras-chavão que esta audit flagra como Crítico no critério 2b. Quando você vê "lineup" na própria SKILL.md (em nomes de critério, contexto técnico), isso é OK — é a régua descrevendo a si mesma.

**Distinção mental**: nome de critério/contexto técnico ≠ ocorrência no `.mdx` do artigo.

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

7. **Analisar cross-produto** pelos 20 critérios (seção abaixo). Gerar `changes` (por produto com proposta) e `passed` (produtos OK).

8. **Reportar em chat** no formato canônico (seção "Formato do relatório").

8.5. **Gravar marcador de auditoria** (registra QUANDO os reviews foram auditados — alimenta a barra "Reviews auditados" + o log de atividade do editor-artigo). Roda **SEMPRE**, logo após o relatório, mesmo que o user depois rejeite todas as mudanças (auditar é o evento; aplicar é outro):
   - `Write` em `docs/biblias-v2/.audits/reviews/{site}-{slug}-last.md` com: título (`# Auditoria de reviews: {site}/{slug}`), `- Produtos auditados: {N}`, `- Achados: {M}` (+ lista curta das rules disparadas, ou "nenhum"). A data é só pra leitura humana — **NÃO** invente timestamp pra sort (a fonte de tempo é o commit do git; e gerar `Date().toISOString()` cai no bug de timezone). Crie o diretório se não existir.
   - Commit + push + VPS pull:
     ```bash
     git add docs/biblias-v2/.audits/reviews/{site}-{slug}-last.md
     git commit --no-verify -m "audit-reviews({site}): {slug} ({M} achados)"
     git push origin main
     bash scripts/painel-vps-pull.sh
     ```
   - **Por quê:** o nome `-last.md` (sem dígitos de data) NÃO cai no `.gitignore` de audits timestampados → fica TRACKED e sincroniza. O editor-artigo lê via `git log` (endpoint `/article/:site/:slug/activity`), então o evento aparece em qualquer máquina. Prefixo `audit-reviews(` faz o log classificar como auditoria de reviews (ícone 🔍). Sem este passo, "Reviews auditados" fica "sem registro" pra sempre.

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

## Os 20 critérios da análise

### 1. `tone-clone` — abertura/frase idêntica entre produtos

**NÃO flagrar** (são intencionais):
- Prefixos `Para quem é:`, `Por que gostamos:`, `Pontos de atenção:`, `Resumo:` — template editorial
- Abertura `A [Produto X] é para quem...` — padrão Wirecutter

**FLAGRAR**:
- Mesma frase concreta em 2+ reviews (claim copiado)
- Parágrafos quase idênticos só trocando nome do produto
- Explicação de conceito repetida (ex: "EcoTank é um sistema de tanque..." em 3 reviews em vez de 1)

### 2. `redundancy` — conceito explicado várias vezes + palavras-chavão repetidas

**Sub-check 2a — Conceito explicado várias vezes**: Reviews 2+ devem **referenciar** conceitos já explicados em reviews anteriores do mesmo artigo, não re-explicar:
- ✅ "como mencionado, o sistema EcoTank..."
- ✅ "conforme a L3250 desta lista, o tanque de tinta..."
- ❌ "EcoTank é um sistema sem cartuchos onde você abre uma tampa e..." (explicação completa em review 3 depois de já ter feito em review 1)

**Sub-check 2b — Palavras-chavão de alta frequência** (régua v1.16.0, canon 2026-05-28):

Conta ocorrências no `.mdx` inteiro (reviews + intro + guide). Flag se passar dos limites:

| Palavra | Limite | Caso real `melhorpretreino` |
|---|---|---|
| `lineup` | **0** (BANIDA) | 50+14 ocorrências em 2 artigos |
| **TODAS variantes de "seleção"** (régua v1.17.2) | **≤ 4 totais** | 29+42 = 71 ocorrências em 2 artigos |
| └ `desta seleção` | (incluso no acima) | 85+65 originais |
| └ `nesta seleção` | (incluso no acima) | 9+17 originais |
| └ `na seleção` | (incluso no acima) | 3+0 originais |
| └ `da seleção` | (incluso no acima) | 14+18 originais |
| `do lineup` / `do nosso lineup` | **0** | 50+11 ocorrências |
| `fórmula` | ≤ 60 | 109+94 |
| `ativo` / `ativos` | ≤ 50 | 94+97 |
| `preço médio` | ≤ 15 | 31+29 |
| `parestesia` + `formigamento` | ≤ 20 combinados | 43+52 (cada review repete os 2 termos) |

**Exceção canônica pra "seleção"** (não contar como chavão — exigida pela `artigo-intro-escrever`):
- Abertura do body: "Preparamos uma **seleção** pra..."
- Fechamento do body: "Esta **seleção** reúne os melhores X disponíveis... ✅"
- Total acceptable: 2 ocorrências de "seleção" por artigo (= 4 totais em 2 artigos).

**Padrões proibidos especificamente** (variantes de chavão estrutural):
- ❌ "ocupa nesta seleção o papel de X" — em todos os reviews vira repetição forte
- ❌ "X nesta seleção é a presença de Y" — variante do mesmo problema
- ❌ "outros pré-treinos da seleção" — usar "outros pré-treinos analisados"
- ❌ "única da seleção" — drop "da seleção" (contexto já é claro)

Severidade: **Crítico** pra "lineup" + "do lineup" (banidas) E "seleção" se > 4 ocorrências totais; **Médio** pras outras (chavão).

Fix proposto: variação léxica + suprimir muletas. Ex: "ocupa nesta seleção o papel" → "ocupa o papel"; "da seleção" → "analisados"; "nesta seleção é a presença" → "é a presença".

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
1. **(a)** é recomendação/calibração/política do fabricante (ex: "a HP recomenda 50-100 págs/mês"), NÃO spec factual — rendimento/economia/velocidade vão direto, sem atribuir
2. **(b)** adiciona valor editorial ao leitor (calibra expectativa, sinaliza honestidade, faz crítica útil)

**❌ Agora flag** (régua v1.21.1): "rende até 4.500 páginas em preto, segundo a Epson" — atribuir spec de fabricante (rendimento) é muleta; fix = afirmar direto "rende até 4.500 páginas em preto". Atribuição só vale pra recomendação/calibração ("a HP recomenda 50-100 págs/mês").

**❌ Burocrática** (flag): "alérgenos da Amazon confirmam ausência de glúten" → propor "sem glúten".

Reportar com sugestão de reformulação destilada. User decide se aceita.

### 9. `voz-comprador-implicita` — voz-comprador SUTIL (categoria D, régua v1.11.4)

**Complementa #5** (`buyer-reference` cobre citação EXPLÍCITA — "compradores destacam"). Esta cobre voz-comprador **IMPLÍCITA** — fraseado que parece análise editorial mas é relato disfarçado copiado da bíblia.

**Padrões pra grep** (palavras-flag):
- "um comprador", "alguns compradores", "parte dos compradores"
- "relata", "relatos", "relatado", "relatada"
- "divide opiniões", "vista por alguns", "considerada por", "elogiada por"
- "queixas", "elogios", "feedback dos"
- "relatos recorrentes", "relato recorrente"

**Exemplos pareados (errado vs fix)** — casos reais 2026-05-26 (batch melhorpretreino dux-energy-kick, dux-pre-workout):

| ❌ Detectado | ✓ Fix proposto |
|---|---|
| "um comprador relata sentir energia em 15 minutos" | "início rápido percebido em ~15 minutos" |
| "divide opiniões pelo sabor adocicado" | "sabor adocicado, agrada perfis específicos" |
| "vista por alguns como queda de energia depois de 2h" | "duração efetiva ~2h, requer dose espaçada em treinos longos" |
| "elogiada pela facilidade de dissolução" | "dissolve facilmente" |
| "relatada como menos potente que a versão anterior" | "potência reduzida vs versão anterior" |

**Severidade: Crítico** (sempre propor mudança) — voz-citação implícita quebra confiança editorial igual à explícita; só é mais difícil de detectar.

### 10. `termos-tecnico-industriais` — termos de rotulagem técnica (régua v1.11.4)

Termos de **rotulagem industrial** soam burocráticos e quebram voz editorial (especialista→amigo). Régua existia em audits desde 2026-05-17 mas só formalizada em 2026-05-26.

**Termos proibidos pra grep**:
- "contaminação cruzada"
- "linha de produção compartilhada" (sem contexto editorial)
- "padrões de fabricação ISO XXXX" (sem agregar valor)
- "boas práticas de fabricação" (BPF — só técnico)
- "rastreabilidade do lote", "lote de fabricação" (regulatório)

**Substituições editoriais**:
- ❌ "Pode ter contaminação cruzada com glúten" → ✓ "Pode conter traços de glúten. Leia a rotulagem antes do uso."
- ❌ "Linha de produção compartilhada com produtos com lactose" → ✓ "Pode conter traços de lactose. Confira a rotulagem se você é sensível."
- ❌ "Atende padrões ISO 22000 de segurança alimentar" → drop ou "produto seguindo padrões reconhecidos da categoria" (se agregar)

**Severidade: Crítico** — quebra voz editorial direta. Auditoria deve sempre propor fix.

### 10b. `jargao-tecnico-vazado` (régua v1.17.3, severidade: CRÍTICO)

Termos de dev/estoque/regulatório que vazaram pro texto público — usuário não entende e quebra confiança editorial. Gap real descoberto no melhorpretreino: "E o SKU avaliado vem só em Laranja", "o ASIN com cafeína só vem em Pink Lemonade".

**Termos PROIBIDOS no texto público** (fullReview, pros, cons, shortDescription, subtitle, specs.value):
- `\bSKU\b` — jargão de estoque
- `\bASIN\b` — identificador Amazon interno
- `\bUPC\b`, `\bEAN\b`, `\bGTIN\b` — códigos de barras
- `\bdatasheet\b` — jargão engenharia
- `\bdataset\b`, `\bfrontmatter\b`, `\bmetadata\b` — jargão dev
- `\bnotificado\b` (regulatório) — soa bula

**Filtro do search** — IGNORAR matches no frontmatter YAML (campos `asin:`, `image:`, etc são técnicos por design e NÃO renderizam pro usuário).

**Fix proposto** (substituições editoriais):
| ❌ Jargão | ✅ Editorial |
|---|---|
| "SKU avaliado" / "SKU disponível" | "versão avaliada" / "este modelo" / "esta apresentação" |
| "ASIN aqui" / "ASIN com cafeína" | "versão analisada" / "produto avaliado" |
| "datasheet do fabricante" | "ficha técnica" / "rótulo" |
| "alimento notificado sob N°..." | "produto registrado na ANVISA" |
| "o rótulo cita possíveis traços" | "pode conter traços" |

**Severidade: Crítico** — usuário casual vê SKU/ASIN e fica confuso, quebra confiança editorial direto.

### 11. `html-texto-puro` — HTML literal em campos texto-puro (régua v1.11.5)

A allowlist HTML do `fullReview` (`<p>`, `<strong>`, `<em>`, `<a>`) é **EXCLUSIVA do fullReview**. Demais campos do produto-no-artigo são renderizados por Astro com `{var}` (escape XSS automático) — HTML inline vira **TEXTO LITERAL** no card pro usuário.

**Sub-checks** (paridade com `pagina-produto-auditar` 6a/6b/6c):
- **11a** `subtitle`: grep `<strong>`, `<em>`, `<a `, `<p>` — se achar, flag crítico
- **11b** `shortDescription`: idem — bug-class real (Integralmédica Huger vazou `<strong>energia...</strong>` em 2026-05-26, apareceu literal no card)
- **11c** `specs[].value`: idem — strings devem ser puras
- **11d** `pros[N]` / `cons[N]`: `<strong>` permitido **APENAS no Título inicial** (template usa `set:html` ali). Proibido `<strong>`, `<em>`, `<a>` no texto APÓS o `:`. Ex: ❌ `<strong>Rendimento</strong>: <strong>4.500</strong> páginas`.

**Severidade: Crítico** — usuário vê HTML literal renderizado como texto, quebra UX.

**Fix proposto**: reescrever como texto puro. Pra ênfase em shortDescription, omitir bold ou reescrever pra colocar o termo no Título da spec.

### 12. `tamanho-escannavel` — shortDescription/pros/cons longos demais (régua v1.16.0)

Bullets e shortDescriptions inchados quebram a leitura escannável que o card e a tabela exigem. Usuário lê em segundos: passou da linha, vira parágrafo, vira wall-of-text → pula a decisão.

**Limites duros** (canon `melhoraspirador` validado live):

| Campo | Hard cap | Alvo | Caso real `melhorpretreino` |
|---|---|---|---|
| `shortDescription` | 250 chars | 150-220 | média 329-414 chars (8 de 11 > 300) |
| `pros[i]` item | 180 chars | 80-130 | média 175-182 chars (60 de 212 > 200) |
| `cons[i]` item | 180 chars | 80-130 | idem pros |

**Sub-checks:**

**12a — shortDescription longo demais:**
- Mede chars do campo `shortDescription` puro (sem HTML — não tem HTML neste campo de qualquer forma)
- Flag se > 250 chars
- Fix proposto: cortar pra **posicionamento + 1-2 specs-chave**. Drop marca completa + ASIN + preço + rendimento + público (resto é função do fullReview e tabela)

**12a-bis — shortDescription técnico-first (régua v1.17.0):**
- Detecta abertura técnica em vez de benefício-first
- **Antipadrões na 1ª frase** (flag se aparecer):
  - "[Tipo] brasileiro/a da [marca]..." (ex: "Pré-treino brasileiro da Black Skull...")
  - "[Tipo] com X mg de Y..." (ex: "Pré-treino com 400 mg de cafeína...")
  - "[Tipo] multifuncional/premium/etc da [marca]..."
- **Padrões OK na 1ª frase**:
  - Adjetivo posicional ("Custo-benefício forte", "Vegano", "Premium", "Foco mental")
  - "Ideal pra quem..."
  - "Você ganha..."
  - Posicionamento direto ("Combustível pra sessões longas", "Energia gradual pra cardio")
- Fix proposto: inverter ordem — colocar posicionamento/benefício na 1ª frase, mover técnico pra 2ª frase. Ver 3 moldes em `artigo-review-criar` v1.17.0.

**12b — bullet pros/cons longo demais:**
- Mede chars do bullet (texto puro, descontando tags `<strong>`/`<a>`)
- Flag se > 180 chars/item
- Fix proposto: cortar listas exaustivas (ver Armadilha 7 da `artigo-review-criar`), reduzir comparações cross-produto pra max 2 peers/bullet

**12c — listagem exaustiva de peers:**
- Conta nomes de produtos OUTROS citados num único bullet/parágrafo
- Flag se ≥ 4 peers citados num único trecho
- Fix proposto: substituir lista por "o mais X deste comparativo" ou citar 1-2 peers extremos

**Severidade: Crítico** — afeta UX direto (cards viram parágrafos), regressão visível do canon vivo.

**Caso real**: bullet do FTW Diabo Verde listou 8 preços de peers num único item (310 chars). Reescrita corta pra "o mais barato deste comparativo" (~85 chars).

### 13. `chavoes-por-nicho` (régua v1.18.0, severidade: 🔴 Crítico)

Lê `docs/painel/_data/chavoes-por-nicho.json` baseado no `niche` do site. Para cada termo definido em `_genericos` + bloco do nicho, conta ocorrências NO TEXTO PÚBLICO (excluindo nomes de produto + frontmatter YAML técnico). Flag Crítico se passar do limite.

Filtros:
- Excluir matches em campos YAML (`asin:`, `image:`, `name:` quando contém o termo só por ser nome de produto)
- Excluir frases canônicas da intro: "Preparamos uma seleção pra", "Esta seleção reúne os melhores"
- Excluir URLs Amazon (`/dp/`, `/s?k=`)

Severidade:
- `termos_banidos_absoluto` > 0 → Crítico (lineup, SKU, ASIN, trade-off, hardcore, etc.)
- Limite numérico ultrapassado → Crítico se passou 50%+, Médio se 10-50%, Info se <10%

Fix proposto: variação léxica conforme alternativas PT-BR documentadas em `artigo-review-criar` v1.17.x ou destilação cirúrgica.




### 14. `capitalizacao-duplicacao` (régua v1.18.3, severidade: 🔴 Crítico)

Detecta bugs de substituição mecânica que vazam pro output:

**Sub-checks:**
- **14a — duplicação contígua**: regex `([a-zA-ZÀ-ÿ\s]{8,40})\1` em qualquer campo. Ex real (`a72e7d9`): "sem empilhar suplementos sem empilhar suplementos"
- **14b — bullet minúsculo**: bullet de pros/cons começa com `<strong>[a-z]`. Ex real: `<strong>aminoácidos essenciais na fórmula</strong>` (era `<strong>BCAAs na fórmula</strong>` antes da substituição)
- **14c — minúscula após ponto**: padrão `\. [a-z]` em texto editorial (excluir URLs amazon.com.br). Ex real: "(maior dose declarada). pra emagrecer onde"

**Causa raiz**: substituições mecânicas com palavras minúsculas viram bug em posição de início de frase/bullet, ou colidem com cauda já existente.

**Fix proposto**: capitalizar primeira letra ou destilar duplicação. Bug-class encontrado pela 1ª vez em commit a72e7d9 (melhorpretreino).

### 15. `concordancia-quebrada-pt-br` (régua v1.19.0, severidade: 🔴 Crítico)

**Bug-class** (ChatGPT-Bárbara 2026-05-28): substituições mecânicas v1.17-1.18 (BCAAs→aminoácidos, parestesia→formigamento, fórmula→composição) **não reconcordaram** plural/gênero/artigo. Identificados 11+ casos em 2 artigos do melhorpretreino.

**Sub-checks** (auto-grep em todos os campos editoriais):

| Sub | Padrão | Exemplo |
|---|---|---|
| **15a** | Plural errado `-ãos` (deve ser `-ões`) | `composiçãos` (8x principal, 3x emagrecer), `combinaçãos` (3+1x) |
| **15b** | Artigo feminino antes de subst. masculino | `a produto` (4x), `a formigamento` (7x), `a mesma formigamento` |
| **15c** | Artigo masculino antes de subst. feminino | `o fórmula`, `este dose` |
| **15d** | Adjetivo concordância quebrada | `produto ampla`, `produtos elaboradas`, `formula natural` (sem acento) |
| **15e** | Duplicação preposicional | `disponíveis no em 2026`, `pra a maioria` |
| **15f** | Gênero gramatical errado | `as produtos em geral`, `os fórmulas` |
| **15g** | Termo entre parênteses duplicado | `formigamento (formigamento)` |

**Regex referência** (do JSON `concordancia_quebrada_regex`):
- `\b(composição|combinação|porção|injeção|reação|opção|posição)s\b`
- `\b(a|na|da|esta|nessa|nesta|essa) (produto|formigamento|ingrediente|ativo|estímulo|composto)\b`
- `\b(o|no|do|este|nesse|neste|esse) (fórmula|dose|porção|composição|combinação|tolerância)\b`
- `produtos? elaboradas?\b|produto ampla|formula natural`
- `\b(?:disponíveis?|disponível) no em \d{4}`
- `\bPra a (maioria|minoria|primeira|melhor|pior)\b`
- `\b(as produtos|os fórmulas|as ingredientes)\b`
- `([a-zA-ZÀ-ÿ]{5,30}) \(\1\)`

**Fix proposto**: corrigir concordância. Bug está sempre em texto colável, sem ambiguidade semântica.

### 16. `template-para-quem-e` (régua v1.19.0, severidade: 🟡 Médio)

**Bug-class** (ChatGPT-Bárbara ponto 4): se >2 produtos do artigo abrem o parágrafo "Para quem é:" com o mesmo padrão `[Produto] ocupa o papel de [Badge]`, vira template óbvio.

**Check programático**:
```python
import re
abertura_template = 0
for produto in products:
    review = produto.get('fullReview', '')
    m = re.search(r'Para quem é:</strong>\s*([^.<]{20,150})', review)
    if m and re.search(r'ocupa (o|um) (papel|espaço)', m.group(1), re.IGNORECASE):
        abertura_template += 1
if abertura_template > 2:
    print(f"⚠ {abertura_template} produtos usam 'ocupa o papel'. Limite: 2.")
```

**Caso real melhorpretreino principal**: 7 dos 11 produtos abriram com "ocupa o papel de [Badge]". Severidade médio porque cada review individual é tecnicamente OK; o problema é cross-produto (homogeneidade).

**Fix proposto**: reescrever aberturas dos 4-5 produtos excedentes usando aberturas alternativas:
- "Para quem treina à noite..." (perfil)
- "Entre as opções sem cafeína..." (contexto comparativo)
- "Combina melhor com quem busca..." (conexão funcional)
- "A proposta aqui é atender quem..." (proposta direta)
- "O grande ponto deste produto é..." (diferencial-âncora)
- "Se você imprime poucas páginas..." (cenário concreto)

### 17. `numeros-em-excesso` (régua v1.19.0, severidade: 🟡 Médio)

**Bug-class** (ChatGPT-Bárbara ponto 10): frases comparativas com 3+ valores em mg/g/R$ viram tabela em prosa, perdem escanabilidade.

**Check programático**:
```python
import re
for produto in products:
    review = produto.get('fullReview', '')
    for frase in re.split(r'[.!?]\s+', re.sub(r'<[^>]+>', '', review)):
        valores = re.findall(r'\d+[\.,]?\d*\s*(?:mg|g|R\$)', frase, re.IGNORECASE)
        if len(valores) > 2:
            print(f"⚠ {len(valores)} valores em 1 frase: {frase[:200]}")
```

**Caso real melhorpretreino emagrecer**:
> "R$ 130 fica abaixo só do Essential Nutrition Beta Action (R$ 225) e acima do Dux Pre Workout (R$ 110), Vitafor V-Fort (R$ 95), Darkness Évora XT e Night Train (R$ 90 cada), 3VS Prohibido (R$ 80), Adaptogen Panic (R$ 78)..."
> (8 preços em 1 frase = tabela em prosa)

**Fix proposto**: quebrar em 2 frases OU substituir lista por categoria ("entre os 3 mais caros analisados", "no piso da Anvisa", "abaixo só do mais caro do comparativo").

**Exceção canônica**: 1 frase comparativa de doses entre 3 produtos vale por review SE houver gancho narrativo claro. Repetir = chavão.

### 18. `health-absolutes-ymyl` (régua v1.19.0, severidade: 🔴 Crítico)

**Bug-class** (ChatGPT-Bárbara ponto 7): absolutos de segurança/saúde violam diretrizes YMYL do Google ("Your Money Your Life") — Google penaliza páginas afiliadas que afirmam segurança absoluta sem fonte.

**Termos banidos absolutos** (limite 0 em qualquer campo):
- `uso regular é seguro`
- `alternativa segura` (sem qualificar contra o quê)
- `não causa dano`
- `totalmente seguro` / `100% seguro` / `sem riscos`
- `sem efeitos colaterais`
- `cientificamente comprovado` / `clinicamente comprovado` (sem citar estudo)

**Substituições propostas**:
| ❌ Absoluto | ✓ Qualificado |
|---|---|
| "Uso regular é seguro" | "Tolerado em uso regular pela maioria; consulte um profissional se tem comorbidade" |
| "Alternativa segura ao X" | "Alternativa mais leve ao X" |
| "Não causa dano renal" | "Sem evidência de impacto renal em pessoas saudáveis em doses recomendadas" |
| "Sem efeitos colaterais" | "Efeitos colaterais raros e leves quando reportados" |
| "Cientificamente comprovado" | "Sustentado por evidências em estudos" (se houver na bíblia) |

**Caso real**: melhorpretreino tem "uso regular é seguro", "alternativa segura", "não causa dano" presentes. Risco SEO YMYL real.

### 19. `voz-eximir-responsabilidade` (régua v1.19.1, severidade: 🔴 Crítico)

**Bug-class** (canon 2026-05-28, Marcelo): "declarado", "declarada", "declarados" e "pelo fabricante" viraram muleta epistêmica — site se eximindo de afirmar diretamente. 91 ocorrências combinadas em 2 artigos do melhorpretreino. Soa como se a redação não confiasse nos próprios dados.

**Princípio editorial**: se o dado está na ficha técnica, é por definição declarado pelo fabricante. Repetir "declarado" é redundância + transfere responsabilidade.

**Sub-checks (regex em todos os campos editoriais)**:

| Sub | Regex | Caso real |
|---|---|---|
| **19a** `mg-declarados-parentetico` | `\\d+\\s*(?:mg\|g\|µg\|ml\|kcal)\\s+declarad[oas]+` | "(400 mg declarados)", "valina (550 mg) declarados" |
| **19b** `declarado-pelo-fabricante` | `declarad[oas]+ pelo fabricante` | "restrição etária declarada pelo fabricante", "óxido nítrico declarada pelo fabricante" |
| **19c** `todas-doses-declaradas` | `(?:todos\|todas\|doses) declarad[oas]+` | "doses todas declaradas pelo fabricante", "todos declarados pelo fabricante" |
| **19d** `alergeno-declarado` | `contém [\\w\\s]+ declarad[oas]+ pelo fabricante` | "A fórmula contém glúten declarado pelo fabricante" |
| **19e** `sem-mg-declarado` | `sem mg declarad[ao]` | "Black Skull tem creatina embutida sem mg declarada" |
| **19f** `conforme-declaracao` | `conforme (?:declaração\|declarado\|declarada)` | "Pode conter lactose conforme declaração" |
| **19g** `segundo-declaracao-fabricante` | `segundo a declaração do fabricante` | "tem 20% mais segundo a declaração do fabricante" |

**Fix proposto** (drop "declarad*" e veja se a frase faz sentido — se sim, era redundância):
- ❌ "(400 mg declarados)" → ✓ "(400 mg)"
- ❌ "doses todas declaradas pelo fabricante" → ✓ "doses transparentes" / "fórmula totalmente declarada"
- ❌ "contém glúten declarado pelo fabricante" → ✓ "contém glúten"
- ❌ "sem mg declarada" → ✓ "sem dose específica" / "embutida sem detalhamento"

**Exceção CANÔNICA** (não flag):
- ❌ "rende 4.500 páginas, segundo a Epson" — atribuir spec de fabricante é muleta (régua v1.21.1); fix = "rende até 4.500 páginas" direto. Atribuição só pra recomendação/calibração ("a HP recomenda 50-100 págs/mês").

## Filtros de severidade

- **Crítico** (sempre propor mudança): buyer-reference explícita, voz-comprador-implicita, termos-tecnico-industriais, html-texto-puro (todos sub-checks), claim-vs-lineup-fato errado, links-incorretos (tag errada), travessão, html-invalido, **tamanho-escannavel** (12a/12b/12c — cards viram parágrafos), **redundancy 2b "lineup"** (banida), **capitalizacao-duplicacao** (14a-c), **concordancia-quebrada-pt-br** (15a-g, v1.19.0), **health-absolutes-ymyl** (18, v1.19.0 — YMYL), **voz-eximir-responsabilidade** (19a-g, v1.19.1 — muleta "declarado")
- **Médio** (propor mudança): tone-clone óbvio, redundancy 2a de conceito, redundancy 2b palavras-chavão (>limite), quality vago, incoherence, voz-citacao-ficha-tecnica burocrática, **template-para-quem-e** (16, v1.19.0), **numeros-em-excesso** (17, v1.19.0)
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
