---
name: artigo-reviews-auditar
description: Audita TODOS os reviews do artigo como CONJUNTO (cross-produto). Aceita URL do painel (editor-artigo.html?site=X&slug=Y) OU args canônicos `site/slug-artigo`. 26 critérios — tone-clone, repetição intra-artigo (mecânica: frase igual em 4+ ocorrências, abertura igual, fecho de preço), redundância, incoerência, qualidade vaga, buyer-reference explícita, links incorretos, claim-vs-lineup-fato, número sem lastro na bíblia, voz-citação ficha-técnica, voz-comprador implícita, termos técnico-industriais, jargão-técnico-vazado, html-texto-puro, tamanho-escannavel, chavões-por-nicho, concordância PT-BR, template "Para quem é", números-em-excesso, health-absolutes-YMYL, voz-eximir-responsabilidade, naturalidade (palavra fora do sentido, frase-sacada, tiques com teto), subtitle-keyword-first, badge-ausente, voltagem-citada, ymyl-aviso-repetido, peso-por-fonte. Output: relatório em chat com diffs por produto, user aplica granular ("aplica produto 2") ou em lote.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**`PIPELINE=yes`** (opcional, canon 2026-08-15): passado pela `artigo-clonar-em-massa`/`artigo-clonar-fila`. Efeito: modo full-auto — aplica os fixes **óbvios E de julgamento** (auto-fix, re-audita, máx 3 rodadas), não espera aprovação, não encerra o turno para perguntar; o que não convergir vai como "⚠ não convergiu" no relatório. Sem a flag, vale o propor→aprovar normal.

**A) URL do painel** (forma preferida):
- `https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio`
- Extrai `site` e `slug` do artigo

**B) Args canônicos**:
- `melhorimpressora/melhor-impressora-custo-beneficio`

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B.

# Auditar/melhorar reviews em artigo (cross-produto)

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:improve_reviews`.
> Conteúdo essencial duplicado abaixo pra autocontenção. **Esta SKILL.md é a fonte viva** desta execução (o `agent-prompts.json` é o espelho do path do painel/API e pode defasar — o projeto roda via Claude Code).

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
- **APLICA O ÓBVIO, PROPÕE O JULGAMENTO (canon Marcelo 2026-07-24, alinha com `biblia-auditar`).** Se a mudança proposta pra um produto for **puramente mecânica** — só travessão→pontuação, `;`→pontuação, ou concordância PT-BR quebrada (gênero/número), **sem tocar em voz/claim/estrutura** — **APLICA DIRETO** (sem esperar) e marca ✅ CORRIGIDO no relatório. Qualquer mudança que envolva **reescrita editorial** (voz-comprador→análise, `buyer-reference`, `claim-vs-lineup-fato`, `redundancy`, `quality`, `tone-clone`, badge, subtitle-keyword-first) vai por **propor→aprovar** e espera aprovação granular. Na dúvida entre mecânico e editorial, trate como editorial (proponha).
- **Mexer em 1 campo é OK**: pode propor mudança só em `pros`, deixar `fullReview` e `cons` intactos.
- **null É LITERAL** quando inalterado. NUNCA `''` ou `[]`.
- **Tamanho de pros/cons**: preserve número de itens. Max +1 novo se claro da bíblia. NÃO reordene itens existentes.
- **Sem travessão (—).**
- **Sem ponto-e-vírgula (;)** (régua 2026-06-20): tem cara de IA. Auto-fixável (;→"." ou ","). Detecção entity-aware (ignora &amp; e entidades).
- **Sem superlativo sem evidência** (coberto como critério pela `artigo-auditar`, gate 4; aqui só se saltar aos olhos no cross-produto: "o mais X" contradito por outro produto do lineup = claim-vs-lineup-fato).
- **Preservar estrutura do `fullReview`**: 4 parágrafos com prefixos exatos (`Para quem é:`, `Por que gostamos:`, `Pontos de atenção:`, `Resumo:`). `Por que gostamos` pode ter 2 parágrafos.
- **Preservar formato pros/cons**: `<strong>Título</strong>: explicação`.
- **Nunca inventar dados**: cada claim com origem rastreável na bíblia.
- **🚨 AUDITORIA POR AMOSTRAGEM É PROIBIDA (gate de cobertura, canon Marcelo 2026-06-27).** Percorra os **26 critérios um a um** e produza a **Checklist de cobertura** no relatório (passo 7 + seção no "Formato do relatório"): cada critério marcado `✓ pass` / `⚠ flag` / `n/a`, com nota de 1 linha. **Varredura seletiva por grep NÃO basta** — vários critérios (esp. os de NORMALIZAÇÃO: **22 subtitle-keyword-first** e **23 badge-ausente**) NÃO aparecem em grep de defeito porque não são "defeito", são transformação proativa que quase SEMPRE gera proposta. Pular qualquer critério sem marcar na checklist = bug da auditoria. Incidente-origem: melhorairfryer-com/melhor-air-fryer 2026-06-27, subtitles e badges passaram batido porque a auditoria foi por amostragem (só os 3 achados que saltaram no grep) — Marcelo pegou os dois no olho. Ver Armadilha "auditoria por amostragem".

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

6. **Read `affiliateTag`**: `sites/{site}/src/config.ts` via regex. Serve pra detectar tag **diferente** (`?tag=X` com X ≠ config, `AFFILIATE_TAG_AQUI`). URL crua `/dp/{ASIN}` é OK sempre: o build injeta a tag (`injectAffiliateTag`, canon 2026-08-15).

6.8. **Rodar o detector mecânico de repetição intra-artigo** (critério 1b, canon Marcelo 2026-08-15):
   ```bash
   python3 .claude/skills/artigo-reviews-auditar/repeticao-intra-artigo.py sites/{site}/src/content/reviews/{slug}.mdx
   ```
   Guarde a saída (lista FIX/INFO, aberturas iguais, fecho de preço, **verbos-curinga total**). O número de verbos-curinga é a linha de base: depois de aplicar qualquer conserto, rode de novo e ele **não pode subir**.

7. **Analisar cross-produto percorrendo os 26 critérios UM A UM** (seção abaixo). **OBRIGATÓRIO (gate de cobertura):** pra CADA um dos 26, decida `✓ pass` / `⚠ flag` / `n/a` e anote 1 linha — isso vira a **Checklist de cobertura** do relatório. **Proibido pular ou "achar que está ok" sem avaliar.** Atenção redobrada aos critérios de NORMALIZAÇÃO, que não saltam em grep de defeito e quase sempre geram proposta:
   - **22 `subtitle-keyword-first`**: leia os N subtitles e avalie CADA um (lead keyword-first? gancho? ≤13 palavras? sem dois-pontos? lead distinto dos outros?). Desde 2026-09-01 a `artigo-review-criar` já escreve no formato híbrido (lead keyword-first + gancho); aqui você confere o conjunto (leads distintos, ≤13 palavras, sem dois-pontos) e normaliza o que veio fora do formato (produto antigo, edição manual, clone pré-2026-09-01).
   - **23 `badge-ausente`**: confira se TODO produto tem `badge`. Faltando → propor `newBadge`.
   - **24 `voltagem-citada`**: nenhum produto cita 110V/127V/220V nem tem row "Voltagem"; "bivolt" só com o `specsAmazon` do ASIN confirmando.
   - **25 `ymyl-aviso-repetido`**: rode o `ymyl-avisos.py` e pode o excedente da fatia dos reviews.
   - **26 `peso-por-fonte`**: pró central/subtitle/shortDescription cuja única origem é o `specsAmazon` → mover pra tabela.
   Gerar `changes` (por produto com proposta) e `passed` (produtos OK).

8. **Reportar em chat** no formato canônico (seção "Formato do relatório") — **incluindo a Checklist de cobertura dos 26 critérios** (sem ela o relatório é inválido).

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

9. **Aplicar o óbvio + esperar aprovação só do julgamento** (canon 2026-07-24):
   - **Mudanças puramente mecânicas** (travessão, `;`, concordância PT-BR — sem tocar voz/claim/estrutura) → **APLICA DIRETO** junto com o backup+Edit dos passos 10-11, sem esperar, e marca ✅ CORRIGIDO no relatório.
   - **Repetição intra-artigo (1b)**: apagar a cópia excedente quando o fato já está num pró/tabela/outra frase do MESMO produto = mecânico (aplica direto); reescrever pelos 3 movimentos literais = julgamento (espera). Em pipeline (clone gate 1.4) os dois são auto-fix, sempre com a verificação de que os verbos-curinga não subiram.
   - **Mudanças com julgamento editorial** (voz-comprador, claim-vs-lineup, redundância, quality, tone-clone, badge, subtitle) → **espera resposta do user**, granularidade per-produto:
     - `aplica tudo` / `aplica todos` → todas as mudanças editoriais
     - `aplica produto 1, 3` → granular por número
     - `aplica L1250 e 107W` → granular por nome (fuzzy match)
     - `rejeita tudo` → encerra sem as editoriais (os mecânicos já foram aplicados)
     - `rejeita produto 2` → todas exceto produto 2
   - Se um produto só tem mudança mecânica, ele nem entra na espera (já foi aplicado). Se não houver nenhuma mudança editorial, pula a espera e vai direto pro build/commit.

10. **Backup**: `docs/painel/.painel-backups/{YYYY-MM-DD}/article-{site}-{slug}-{HHMMSS}-improve.mdx`. Pattern paralelo ao painel pra aparecer no card "Histórico de versões".

11. **Aplicar mudanças** (óbvios já aplicados + editoriais aprovados): usar `Edit` cirúrgico no `.mdx` pra cada produto com mudança a aplicar.
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

## Os 26 critérios da análise

(Numeração: 1, 1b, 2-19, 21-26 — o antigo 20 foi absorvido pelo 21 `naturalidade`; o 25 fica no topo por ser poda mecânica; são 26 critérios.)

### 25. `ymyl-aviso-repetido` — poda do excedente (🟡, canon 2026-06-25 + 2026-07-30)

A régua limita o aviso "procure um médico/nutricionista" a **1 por ARTIGO**. Quem
CONTA é a `artigo-auditar` (única com escopo de artigo inteiro); esta skill **poda
a fatia dos reviews**.

Rode o mesmo script que ela usa, para não inventar regex próprio:

```bash
python3 .claude/skills/artigo-auditar/ymyl-avisos.py sites/{site}/src/content/reviews/{slug}.mdx --json
```

Ele já marca cada ocorrência como `KEEP` ou `PODA` e diz em que seção está. **Você
aplica só as `PODA` cujo `secao` é `reviews`** — as do `guide` são da
`artigo-guia-auditar`, e o `KEEP` fica.

⚠ **Fato de rótulo NÃO entra na poda** (achado da Bárbara, 2026-08-30). Aviso que
  cita fabricante, embalagem ou bula, ou que amarra idade e dose — "o fabricante
  orienta que crianças até 3 anos só consumam sob orientação de pediatra", "o
  próprio rótulo avisa que dose acima de 2 comprimidos só com indicação médica" —
  é **informação de produto**, da mesma classe de dose e alérgeno, e é exatamente
  o caso que a régua manda MANTER ("só quando o ponto é genuinamente sensível,
  ex.: contraindicação real de um produto específico"). O `KEEP`/`PODA` do script
  é POSICIONAL e não distingue: já marcou PODA no fato de rótulo e KEEP no
  disclaimer genérico, invertendo o valor. **Quando isso acontecer, ignore o
  script.** Não há classificador de propósito — a fronteira não é nítida e ler
  2 ou 3 trechos custa menos que errar no automático.

⚠ **Só APAGA quando o aviso é frase inteira ou oração removível deixando o texto
válido.** Se tirar exigir reescrever a frase em volta, é prosa nova: vai pro
relatório, não aplica. Exemplos reais do pior caso da rede:
- `"Por ser suplemento infantil, o uso pede acompanhamento do pediatra."` → frase
  inteira, APAGA.
- `"...praticidade na nutrição infantil, sempre com a orientação de um profissional
  de saúde."` → a oração final sai e a frase fica de pé, APAGA a oração.
- `"...a partir dos 4 anos com orientação do pediatra."` dentro de uma
  `shortDescription` que só tem essa frase → apagar deixaria o campo sem fecho:
  REPORTA.

**Severidade 🟡 e não 🔴:** aviso a mais não é erro de fato nem risco ao leitor,
é repetição que cansa. Não bloqueia nada.

### 1. `tone-clone` — abertura/frase idêntica entre produtos

**NÃO flagrar** (são intencionais):
- Prefixos `Para quem é:`, `Por que gostamos:`, `Pontos de atenção:`, `Resumo:` — template editorial
- Abertura `A [Produto X] é para quem...` — padrão Wirecutter

**FLAGRAR**:
- Mesma frase concreta em 2+ reviews (claim copiado)
- Parágrafos quase idênticos só trocando nome do produto
- Explicação de conceito repetida (ex: "EcoTank é um sistema de tanque..." em 3 reviews em vez de 1)

### 1b. `repeticao-intra-artigo` — a mesma FRASE em vários produtos (mecânico, canon Marcelo 2026-08-15)

**Por que existe:** os 11 sub-agents de review escrevem cada um 1 produto isolado (por design) e convergem nas mesmas frases: no `melhoraspirador/melhor-aspirador-de-po-vertical` (15/08, régua de voz nova) "em casa grande você troca de tomada algumas vezes" saiu 5×, "cômodo inteiro sem trocar de tomada" 6×, "limpeza rápida do dia a dia" 5×, 6 de 11 descrições curtas começando com "Aspirador vertical com fio para", fecho de preço em 9 de 11. Cada review sozinho estava natural; em sequência viram formulário. O `tone-clone` (1) já dizia "mesma frase concreta em 2+ reviews", mas por leitura não pegava — este critério é a versão **mecânica** dele: o script do passo 6.8 lista, você julga e conserta.

**Limiar (frequência, não presença — o Marcelo aceita repetição baixa):**
- Sequência de **6+ palavras** igual: **≤3 ocorrências = INFO** (fica; entra no relatório só como registro). **≥4 = FIX**: reduzir a 3.
- **Abertura igual** (4 primeiras palavras da shortDescription ou do "Para quem é") em **≥4 produtos = FIX**: variar as excedentes; 3 = INFO.
- **Fecho de preço** ("…preço médio de R$ X" como última frase da shortDescription ou do Resumo) em **>50% dos produtos = FIX**: deixar em no máximo metade (o preço já está na tabela).
- Fora do cálculo (o script já exclui): os 4 rótulos, nomes de produto, keyword/keywordPlural, URLs. Repetir **palavra** ("aspira", "sem saco", "cabo") nunca é achado. **Spec pura repetida** ("Wi-Fi dual band 2,4 e 5 GHz", "1450 W de potência") é fato, não frase-molde: o script marca como INFO mesmo acima de 4; só vira FIX se a frase inteira em volta da spec for a mesma.

**Conserto — as 5 salvaguardas (o risco real é trocar repetição por frase estranha, o defeito que a régua de voz acabou de tirar):**
1. **Apagar antes de reescrever.** Se o fato da cópia já está num pró, na tabela de specs ou em outra frase do mesmo review, a cópia é apagada. É o caso mais comum ("sem trocar de tomada" ao lado de "cabo de X metros").
2. **A 1ª ocorrência do artigo fica literal.** Só a 2ª, 3ª… são tocadas, e só até voltar ao limiar.
3. **Reescrita só por 3 movimentos literais:** (a) o número/fato vira sujeito ("Com 5 metros de cabo, em casa grande é preciso trocar de tomada"); (b) fundir na frase vizinha; (c) mover o fato para um pró/contra. **PROIBIDO** sinônimo, figura ou "variação de estilo" — se a frase nova tem verbo da lista do critério 21c (resolve, dá conta, entrega, segura, pede, exige, aguenta, sustenta, encara, cobra, cobre, vira, brilha), ela reprovou.
4. **Verificar depois:** rode o script de novo — repetições FIX zeradas ou reduzidas E `verbos-curinga` igual ou menor E tetos do 21f ok. Se algum piorou, **reverta aquela frase** e deixe a repetição com ⚠ no relatório. Repetição natural é melhor que frase inventada.
5. **Nunca** instrução do tipo "varie a redação" para si mesmo nem para sub-agent.

**Severidade:** FIX = 🟡 Médio (propor→aplicar no lote dos óbvios: apagar cópia é determinístico; reescrever é julgamento e espera aprovação junto com os demais). INFO = só relatório.

### 2. `redundancy` — conceito explicado várias vezes + palavras-chavão repetidas

**Sub-check 2a — Conceito explicado várias vezes**: Reviews 2+ devem **referenciar** conceitos já explicados em reviews anteriores do mesmo artigo, não re-explicar:
- ✅ "como mencionado, o sistema EcoTank..."
- ✅ "conforme a L3250 desta lista, o tanque de tinta..."
- ❌ "EcoTank é um sistema sem cartuchos onde você abre uma tampa e..." (explicação completa em review 3 depois de já ter feito em review 1)

**Sub-check 2b — Palavras-chavão de alta frequência** (canon 2026-08-15: a fonte é o JSON, não esta tabela):

Conta ocorrências no `.mdx` inteiro (reviews + intro + guide) contra `docs/painel/_data/chavoes-por-nicho.json`: `_genericos.termos_banidos_absoluto` (lineup, do lineup, SKU…) = 0; `_genericos.chavoes_estruturais_max` ("desta/nesta/na/da seleção" = **0**, com a exceção canônica abaixo); `industrial_max` (preço médio 15, fabricante 12, declarado…); e o bloco do nicho **só se o site está em `_sites_aplicaveis`** (ex.: os caps de "fórmula/ativo/parestesia" são do bloco Pré Treino, não valem para tablet). A tabela hardcoded que vivia aqui ("seleção ≤4", "fórmula ≤60") era um snapshot de 1 nicho de 05/2026 e contradizia o critério 13 — foi removida; o 13 é quem aplica o JSON, este 2b só cobre **conceito re-explicado** (2a) e delega chavão ao 13.

**Exceção canônica pra "seleção"** (não contar como chavão — frases LEGADAS permitidas pela `artigo-intro-escrever`; até a v1.30 eram o padrão, a v1.31+ não as empurra mais):
- Abertura do body: "Preparamos uma **seleção** pra..."
- Fechamento do body: "Esta **seleção** reúne os melhores X disponíveis... ✅"
- Total acceptable: 2 ocorrências de "seleção" por artigo (= 4 totais em 2 artigos).

**Padrões proibidos especificamente** (variantes de chavão estrutural):
- ❌ "ocupa nesta seleção o papel de X" — em todos os reviews vira repetição forte
- ❌ "X nesta seleção é a presença de Y" — variante do mesmo problema
- ❌ "outros pré-treinos da seleção" — usar "outros pré-treinos analisados"
- ❌ "única da seleção" — drop "da seleção" (contexto já é claro)

Severidade: **Crítico** pra "lineup" + "do lineup" (banidas) E "seleção" se > 4 ocorrências totais; **Médio** pras outras (chavão).

Fix proposto: suprimir muletas (não trocar por sinônimo figurado). Ex: "ocupa nesta seleção o papel" → "ocupa o papel"; "da seleção" → "analisados"; "nesta seleção é a presença" → "é a presença".

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

Formato esperado: `<a href="https://www.amazon.com.br/dp/{ASIN}?tag={tag}&linkCode=ogi&th=1&psc=1" rel="nofollow" target="_blank">Nome do Produto</a>` **ou a URL crua** `https://www.amazon.com.br/dp/{ASIN}` (o build injeta a tag do config — canon 2026-08-15; cru NÃO é defeito).

Flag se: total fora de 2-3 OU tag **diferente** da do config / `AFFILIATE_TAG_AQUI` OU `target="_blank"` ausente OU `rel="nofollow"` ausente.

### 7. `claim-vs-lineup-fato` — comparações com lineup factualmente erradas

**Específico cross-produto, fora do `improve_reviews` canônico** mas valioso.

Verificar comparações de preço/spec entre produtos do lineup contra dados reais:
- Se review diz "menor preço entre tanques", confirmar via `schemaPrice` que é verdade
- Se review diz "única laser desta seleção", confirmar via lineup que é verdade
- Se review diz "rende 3x mais que produto X", confirmar via specs/bíblia

**Caso real (commit a58a33b)**: L1250 dizia "menor preço entre opções de tanque" mas Smart Tank 581 (R$ 820) é mais barata que L1250 (R$ 850). Comparação falsa, requer correção.

Sugestão de fix: reformular pra escopo verdadeiro ("menor preço entre as Epson EcoTank" em vez de "entre as opções de tanque") ou remover o claim.

### 7b. `numero-sem-lastro-na-biblia` — todo número do review tem que existir na bíblia (régua 2026-08-14)

Irmão do 7: o 7 confere o número **contra o lineup**, este confere **contra a
bíblia do próprio produto**. É a checagem mais barata que existe e a que mais
rende, porque o sub-agent de criação arredonda, troca dígito ou herda número de
modelo irmão sem perceber.

**Rode, não confira a olho** — é varredura de conjunto, não leitura:

```python
import json, re
b = json.dumps(json.load(open(f'docs/biblias-v2/{asin}.json')), ensure_ascii=False)
na_biblia = set(re.findall(r'\d[\d\.\,]*', b.replace('.', '').replace(',', '')))
no_review = set(re.findall(r'\d[\d\.]*', campos_do_produto.replace('.', '')))
orfaos = [n for n in no_review if len(n) >= 3 and n not in na_biblia]
```

**Como ler a saída:** a lista é de **candidatos**, não veredito. Número
composto ("2 anos" virando 24 meses), soma feita pelo redator e ano corrente
saem como órfãos legítimos. O que importa é olhar cada um e achar a origem —
se você não consegue apontar de onde o número veio, ele é invenção.

**Caso real 2026-08-14** (`guiamelhorcompra/melhores-impressoras-multifuncionais`,
clone biblia-only): o scan devolveu **um** órfão, `5500`, na Epson EcoTank L8180.
A bíblia trazia `snapshot.precoBRL = 5400` e `observacoesAgente` repetia "~R$
5.400"; o `schemaPrice` do próprio produto no artigo era `5400` e o guia já
escrevia "R$ 5.400". Só o review dizia R$ 5.500, em dois lugares. **O artigo se
contradizia sozinho e o gate mecânico da Etapa 1.2 passou limpo**, porque ele
confere forma (travessão, `;`, links, rótulos, tamanho) e não confere fato. Foi
parar na `artigo-auditar` (Etapa 4), duas etapas e um guia inteiro depois.
Rodando aqui, custa um script e para na hora.

**Bloqueia?** Sim quando o órfão é fato do produto (preço, rendimento,
velocidade, capacidade, peso, garantia). Fix = usar o número da bíblia, e
conferir se o mesmo número errado não vazou pro `schemaPrice`, pras specs e pro
guia.

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
- **Padrões OK na 1ª frase**: para quem serve ou o que faz de melhor, dito de forma literal ("Aspirador com fio para apartamento pequeno e limpeza rápida", "Creatina pura para uso contínuo", "Vegano, sem cafeína, para treino noturno").
- **Também flagrar (canon 2026-08-15, ver 21c/21f)**: molde de abertura/fecho "Ideal pra quem…", "Feito pra quem…", "Você ganha…", "Destaque para…", "Custo-benefício forte pra…" — eram os "padrões OK" até 2026-08-15 e viraram assinatura da rede; e figura no lugar de posicionamento ("Combustível pra sessões longas").
- Fix proposto: 1ª frase literal (para quem é / o que faz), técnico na 2ª, fecho de fato. Ver seção shortDescription em `artigo-review-criar`.

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

**⚠ `_sites_aplicaveis` é o GATE do bloco de nicho, e o `_genericos` é obrigatório (canon 2026-08-15).**

1. **Bloco de nicho só vale se o slug do site estiver em `_sites_aplicaveis`.** Não force o bloco pelo `niche` do `sites-meta.json`. Caso real: `melhoraspirador-com` tem `niche: "Aspiradores"`, mas o bloco `Aspiradores` lista `_sites_aplicaveis: ["melhoraspirador"]`, que é OUTRO site — o bloco não se aplica. Precedente consistente na rede (`.audits/products/oguiacompra-wap-high-speed-plus-last.md`, `guiaesportivo-vitafor-v-fort`, `compraguia-melhor-impressora-epson`): site fora da lista → **vale só o `_genericos`**. Se o bloco DEVERIA cobrir o site, reporte como sugestão de incluí-lo em `_sites_aplicaveis` — é descalibração do JSON, **não achado contra o texto**.
2. **CONTE O `_genericos` SEMPRE, e conte PRIMEIRO.** Ele não tem gate, vale em qualquer site, e é o que costuma disparar de verdade: `termos_banidos_absoluto`, `chavoes_estruturais_max` (as 4 variantes de "seleção" têm cap **0**, são banidas — salvo as `frases_excecao_canon`) e `industrial_max` (`declarado` 3, `fabricante` 12, `rótulo` 20, `preço médio` 15).

**Incidente-origem (2026-08-15, `melhoraspirador-com/melhor-aspirador-de-po-vertical`):** três auditorias seguidas contaram só o bloco de nicho. Erro duplo — reprovaram o artigo por 4 termos de um bloco que nem se aplicava, e deixaram passar o achado real: 8 ocorrências de "nesta/desta/da seleção" (cap 0 no `_genericos`) no `guideContent`.

Lê `docs/painel/_data/chavoes-por-nicho.json` baseado no `niche` do site. Para cada termo definido em `_genericos` + bloco do nicho, conta ocorrências NO TEXTO PÚBLICO (excluindo nomes de produto + frontmatter YAML técnico). Flag Crítico se passar do limite.

Filtros:
- Excluir matches em campos YAML (`asin:`, `image:`, `name:` quando contém o termo só por ser nome de produto)
- Excluir frases canônicas da intro: "Preparamos uma seleção pra", "Esta seleção reúne os melhores"
- Excluir URLs Amazon (`/dp/`, `/s?k=`)

Severidade:
- `termos_banidos_absoluto` > 0 → Crítico (lineup, SKU, ASIN, trade-off, hardcore, etc.)
- Limite numérico ultrapassado → Crítico se passou 50%+, Médio se 10-50%, Info se <10%

Fix proposto: encurtar/omitir a frase repetida ou destilação cirúrgica. NÃO "variação léxica" por sinônimo figurado (é o defeito do 21c).




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
- "A fórmula não tem aditivos, e isso decide para quem..." (diferencial-âncora; NÃO "o grande ponto deste produto é", virou molde)
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

### 21. `naturalidade` (v1.32.0, canon Marcelo 2026-06-10, severidade: 🔴/🟡)

**Bug-class** (caso real melhorimpressora/melhor-impressora, home): frases de OCORRÊNCIA ÚNICA que nenhum falante usaria — grep de frequência NÃO pega; exige **leitura frase a frase** de fullReview/pros/cons/shortDescription/subtitle.

**21a — rótulo de categoria inventado** (🔴): locução que não existe no varejo. **Teste-da-Amazon**: digitaria isso na busca? Casos reais: "máquina de trabalho"→"impressora de escritório" · "impressora para imagem"→"impressora fotográfica" · "faixa fotográfica"→"conjunto de 6 tintas" · "cadência de negócio"→"velocidade pra escritório" · "preço de custo-benefício"→"preço justo". **EXCEÇÃO LIBERADA** (NÃO flagrar): elipse com adjetivo real da categoria ("a barata", "a doméstica", "a laser", "as de tanque", "a fotográfica") é português natural.

**21b — meta-SEO / quebra da 4ª parede** (🔴): texto comentando a busca do leitor ("tem gente que digita 'melhor impressora' na busca...", "quando a busca esconde uma necessidade..."). Fix: cenário direto ("Nem toda impressora é pra casa...").

**21c — palavra fora do sentido / verbo-curinga com sujeito-coisa (canon Marcelo 2026-08-15, substitui "antropomorfismo com gíria")** (🟡; 🔴 quando ≥3 no mesmo review ou repetido como fecho em ≥3 produtos): é a **classe** que mais produz "cara de IA" e passa em toda lista de termo. Palavra comum usada num sentido que não é o do dicionário, quase sempre colocação inglesa vertida: objeto/preço/peso que "resolve, dá conta, entrega, segura, pede, exige, aguenta, sustenta, encara, cobra, junta, trabalha, cobre, vira, brilha" ("resolver a casa inteira", "o aparelho pede tomada", "a conta da potência vem no peso", "sem transformar a limpeza numa produção", "o que os R$ 295 compram", "casa grande pede remanejo"); substantivo-figura ("a conta", "degrau", "piso", "porta de entrada", "pacote", "produção", "trunfo", "fôlego"); frase-sacada ("não é X: é Y", "o que X é Y", "é aí que…"); fecho com rótulo de público ("é a escolha de quem", "faz sentido pra quem", "ele é o que resolve"); "pra" no texto público. **Teste**: a palavra está no sentido em que você a usaria falando com um cliente? Fix: sujeito concreto + verbo literal ("limpar a casa toda", "precisa de tomada", "a potência tem um custo: o peso", "sem muito esforço", "por R$ 295 você tem…", "você troca de tomada algumas vezes"), "para". Repetir a palavra exata ("aspira" 3×) NÃO é defeito e não deve ser trocada por sinônimo figurado. Personificação que EXPLICA ("o Wi-Fi se conecta sozinho") não flagra; verbo inventado/gíria ("se reconserta", "no batente") continua flagrando aqui.

**21d — jargão financeiro/burocrático** (🟡): "desembolso", "comprometer dinheiro", "reprografia", "na(s) frente(s) de". Fix: "preço", "gastar", "cópia e digitalização".

**21e — gramática/ambiguidade que trava a leitura** (🔴): casos reais: "só imprime em preto e a laser" (faltou "é"); "que ainda não aquece a tinta" (lê-se "ainda não"); "papel cortado pela metade" (parece papel rasgado); "cabe na escrivaninha sem virar uma estação de trabalho" (sujeito ambíguo); "troca inteligente pela Epson" (direção invertida). Inclui atribuição elíptica "conta da Epson" (= "segundo a Epson", muleta v1.21.1 → número direto).

**21f — tiques com teto por ARTIGO** (🟡): complemento mecânico do 21c, não substituto. Os tetos vivem em `docs/painel/_data/chavoes-por-nicho.json` → `_genericos.naturalidade_max` (canon 2026-08-15: daqui 2, pede 3, resolve 3, dá conta 2, entrega 3, segura 2, vira 3, de verdade 1, com folga/de sobra 1, trunfo/fôlego/degrau/porta de entrada 1, "é o que resolve" 1, "o grande ponto" 1…) + `naturalidade_banidos` (0), somados ao bloco do nicho quando houver (o mais restritivo vence). Não copie a lista pra cá: cite a chave. Casos reais: "daqui" 13× e "pede" 9× no impressoraideal/melhor-impressora-multifuncional; "resolve" 33×, "pede" 23×, "daqui" 11× no melhoraspirador-com/melhor-aspirador-de-po-vertical (2026-08-15).

### 22. `subtitle-keyword-first` (v1.56.0, canon Marcelo 2026-06-24, severidade: 🟡 Médio)

O subtitle é o **heading do card** do produto = slot de alto peso SEO. **Esta etapa confere o CONJUNTO e normaliza o que veio fora do formato.** Desde 2026-09-01 a `artigo-review-criar` já escreve o subtitle no formato híbrido abaixo (antes escrevia só o ângulo v1.34 e esta etapa reformatava, o que só fechava no pipeline de clone); o cross-produto (leads distintos) continua sendo decisão daqui, porque a criação vê um produto por vez.

**Formato-alvo: HÍBRIDO FLUINDO** (canon Marcelo 2026-06-24) — **LEAD keyword-first capitalizado emendado DIRETO num gancho descritivo**, numa frase só que flui. **NUNCA use dois-pontos (`:`)** entre lead e gancho — é emenda natural (`com`/`de`/`que`/`e`/vírgula), não rótulo+legenda.
- **LEAD = keyword-first** (a keyword do artigo, ou um pedaço dela, + um qualificador curto). Capitalizado tipo título no lead só (ex: "Impressora Tanque de Tinta em Geral", "Tablet Custo Benefício", "Tablet para Desenho Profissional").
- **GANCHO (tail) = o ângulo/spec concreto do produto**, em **caixa natural de frase** (não Title Case). **Spec técnica é PERMITIDA aqui** (Hz/GB/polegada/chip/tinta etc.) — é o que torna o card útil e único.
- **≤13 palavras no total** (lead incluso). Conte de verdade, palavra a palavra — o lead come 2-3 palavras. Corte spec sobrando pra caber.
- ✅ EX: `Impressora Tanque de Tinta em Geral que equilibra funções, custo e tamanho` · `Tablet Custo Benefício com S Pen inclusa, tela de 10,9 polegadas a 90Hz` · `Impressora Multifuncional a Laser com texto preto firme a até 21 ppm`.

**Vocabulário de qualificador do LEAD (SUGESTÃO, não regra — o agente analisa e usa quando faz sentido):** em Geral · Custo Benefício (sem hífen no lead) · Boa e Barata (feminino) / Bom e Barato (masculino) · Barato e Bom · Premium · Topo de Linha · Profissional · de Entrada · a Laser · Fotográfica · Frente e Verso · de Tanque de Tinta {Marca} (termo COMPLETO "tanque de tinta", nunca só "tanque") · da {Marca} · para {perfil} · com {feature}. A keyword no lead **não é obrigatória em todo produto** — é o alvo preferido; se ficar forçado, o agente prioriza naturalidade.
- **Concordância de gênero pelo núcleo da keyword:** impressora→"Boa e Barata"; tablet→"Bom e Barato". Nunca trocar.
- **Cross-produto (o porquê de morar no audit):** LEADs DISTINTOS entre os produtos (anti-clone) — não repetir o mesmo qualificador 2× (os 2 "a laser" se separam por marca: "a Laser da HP" × "a Laser da Brother"). Sequência típica: pos 0 = "em geral", pos 1 = "custo benefício", pos 2 = "boa e barata", pos 3+ = perfil/marca/feature.
- **🚨 O slot "em Geral" SEMPRE leva "Melhor" no lead (canon Marcelo 2026-06-27): `Melhor {Categoria} em Geral ...`.** "em Geral" significa "a melhor no geral" — sem "Melhor" o lead fica truncado e sem sentido ("Air Fryer em Geral" ≠ frase; "Melhor Air Fryer em Geral" = a melhor air fryer no geral). É também o lead MAIS keyword-first quando a keyword começa com "Melhor" (ex. "melhor air fryer" → lead = a keyword inteira). **Exceção do "solte o Melhor":** nos DEMAIS qualificadores descritivos (Custo Benefício, Boa e Barata, Compacta, Premium, Barbecue, a Laser, para Desenho, etc.) o "Melhor" é solto — eles se sustentam sozinhos ("Tablet Custo Benefício", "Impressora Compacta"). Só o slot "em Geral" carrega o "Melhor" obrigatório.
- Se a keyword já contém o diferenciador (ex "melhor tablet custo benefício"), o lead já é "Tablet Custo Benefício" — **varie a 2ª palavra** com marca/perfil pra distinguir os produtos.

**FLAGRAR (e propor o subtitle novo, campo `newSubtitle`)**: subtitle que NÃO é keyword-first no lead, OU usa dois-pontos (`:`) entre lead e gancho, OU repete o LEAD de outro produto, OU passa de 13 palavras, OU está vazio, OU é rótulo puro SEM gancho descritivo (ex "Melhor Impressora Multifuncional em Geral" sozinho — falta o tail concreto), **OU é slot "em Geral" SEM o "Melhor" no lead (ex "Air Fryer em Geral..." → "Melhor Air Fryer em Geral...")**.

**Exceção (v1.34.0 reconciliada):** subtitle escrito À MÃO pelo editor no stub é rótulo deliberado — **respeite** (não force por cima). O ângulo que guia o REVIEW é o `badge`, não o subtitle. Só normalize subtitles gerados/vazios/claramente fora do padrão.

❌ ERRADO (rótulo + dois-pontos): "Tablet para Desenho: topo do Android com AMOLED". ❌ ERRADO (rótulo puro sem gancho): "Melhor tablet para desenho topo de linha". ✅ CERTO (híbrido fluindo): "Tablet para Desenho Topo de Linha Android com AMOLED 120Hz e S Pen".

### 23. `badge-ausente` (severidade: 🔴 Crítico, canon Marcelo 2026-06-22)

TODO produto do `products[]` precisa do campo `badge` (etiqueta do card). Convenção da rede: os 2 primeiros = ranking ("Melhor Escolha"/"Melhor Custo Benefício"/"Boa Alternativa"); os demais = descritivos do ângulo ("Duplo Cesto", "Mais Silenciosa", "Formato Forno", "Boa e Barata", "Cesto Quadrado"). **Esta audit roda cross-produto, então é o lugar natural pra pegar badge faltando ANTES do gate final da `artigo-auditar`** — lá o `badge-ausente` é `error` e BLOQUEIA readyToLock. Pegar aqui evita chegar no fim do pipeline com o gate vermelho.

**Como detectar**: pra cada item de `products[]`, conferir se existe a linha `badge:`. Flag cada produto sem.

**Fix proposto (campo `newBadge`)**: badge descritivo curto (≤3 palavras) derivado do `subtitle`/ângulo/categoria do produto, **DISTINTO dos demais** (anti-repetição cross-produto — é por isso que mora numa audit que vê os N juntos). Texto livre, cor fallback (NÃO precisa registrar em `amazon.ts`: o render usa `badgeColors[badge] ?? DEFAULT_BADGE_COLOR`). Não mexe em badge JÁ preenchido (rótulo humano é deliberado).

**Caso real (melhorairfryer-com/melhor-air-fryer, 2026-06-27)**: só 5 de 11 produtos tinham badge. Os 6 sem etiqueta (Oster, WAP Barbecue, NA150, WAP FW009548, Britânia, Midea) passaram batido pela auditoria de reviews e só foram pegos no `artigo-auditar` final (readyToLock=false). Marcelo: "isso era pra ter pego no auditar reviews". Por isso o critério entrou aqui.

### 24. `voltagem-citada` (canon 2026-06-29, critério desde 2026-09-01, severidade: 🔴 Crítico)

Mesma régua dura da `artigo-review-criar` (Filtros editoriais) e da `pagina-produto-auditar` critério 21, conferida aqui porque até 2026-09-01 nenhuma auditora olhava: **nenhum produto do artigo cita 110V/127V/220V** (prosa ou spec) nem tem row "Voltagem"; **"bivolt" só com o `specsAmazon` do próprio ASIN** dizendo bivolt / 100-240V / 110-220V (fabricante, bruto e campo curado não bastam; aquecimento de alta potência é voltagem única por design). 110/127/220 → conserto determinístico (apagar a menção/row); bivolt sem lastro → reescrever o pró/spec. Confira produto a produto: é o mesmo erro que se repete em lote (caso-origem: air fryers, 2026-06-28).

### 26. `peso-por-fonte` (critério desde 2026-09-01, severidade: 🟡 Médio)

Claim cuja ÚNICA origem é o `specsAmazon` (classificação automática: "Tipo de dieta", "Material", "Característica especial") **não pode ser pró central, subtitle nem shortDescription**, só tabela. Diferente do 7b (`numero-sem-lastro`: sem origem nenhuma); aqui a origem existe mas é fraca pro lugar. Fix = mover pra `specs` ou apagar. Caso-origem: Vitafor B07L5W6GVC, "composição cetogênica" como diferencial.

## Filtros de severidade

- **Crítico** (sempre propor mudança): **voltagem-citada** (110/127/220 → apagar a menção/row; bivolt sem lastro no specsAmazon → reescrever o pró/spec), buyer-reference explícita, voz-comprador-implicita, termos-tecnico-industriais, html-texto-puro (todos sub-checks), claim-vs-lineup-fato errado, links-incorretos (tag DIFERENTE da do config), html-invalido, **tamanho-escannavel** (12a/12b/12c — cards viram parágrafos), **redundancy 2b "lineup"** (banida), **capitalizacao-duplicacao** (14a-c), **concordancia-quebrada-pt-br** (15a-g, v1.19.0), **health-absolutes-ymyl** (18, v1.19.0 — YMYL), **voz-eximir-responsabilidade** (19a-g, v1.19.1 — muleta "declarado"), **naturalidade 21a/21b/21e** (rótulo inventado, meta-SEO, gramática que trava — v1.32.0), **badge-ausente** (23, canon 2026-06-22 — todo produto leva etiqueta, alinha com o gate da `artigo-auditar`)
- **Mecânico (aplica direto, warn)**: travessão, `;`, concordância PT-BR, capitalização/duplicação, `AFFILIATE_TAG_AQUI` (régua comum das auditoras — `docs/PADROES.md`).
- **Médio** (propor mudança): **peso-por-fonte** (claim só do specsAmazon como pró central/subtitle/shortDescription → mover pra tabela), tone-clone óbvio, **repeticao-intra-artigo 1b (FIX: ≥4 ocorrências / abertura em ≥4 / fecho de preço >50%; apagar cópia é óbvio, reescrever é julgamento — com as 5 salvaguardas)**, redundancy 2a de conceito, redundancy 2b palavras-chavão (>limite), quality vago, incoherence, voz-citacao-ficha-tecnica burocrática, **template-para-quem-e** (16, v1.19.0), **numeros-em-excesso** (17, v1.19.0), **naturalidade 21c/21d/21f** (palavra fora do sentido/verbo-curinga, jargão financeiro, tiques acima do teto — v1.32.0 + canon 2026-08-15; 21c vira Crítico com ≥3 no mesmo review), **subtitle-keyword-first** (22, v1.56.0 — normaliza subtitle pro híbrido fluindo: lead keyword-first + gancho, sem dois-pontos, ≤13 palavras, cross-produto)
- **Info** (mencionar mas não obrigatório aplicar): parágrafo no limite de tamanho, posição de link sub-ótima

## Formato do relatório

Apresentar em chat após análise:

```markdown
# Auditoria cross-produto: {site}/{slug}

**Lineup**: {N} produtos analisados, {N-X} com fullReview preenchido (auditados)
**Resultado**: {X} produtos com mudanças propostas, {Y} passaram limpos

## Checklist de cobertura dos 26 critérios (OBRIGATÓRIA — sem ela o relatório é inválido)

| # | Critério | Status | Nota |
|---|---|---|---|
| 1 | tone-clone | ✓/⚠/n.a. | ... |
| 1b | repeticao-intra-artigo (script) | ✓/⚠/n.a. | ... |
| 2 | redundancy | ✓/⚠/n.a. | ... |
| 3 | incoherence | ✓/⚠/n.a. | ... |
| 4 | quality | ✓/⚠/n.a. | ... |
| 5 | buyer-reference | ✓/⚠/n.a. | ... |
| 6 | links-incorretos | ✓/⚠/n.a. | ... |
| 7 | claim-vs-lineup-fato | ✓/⚠/n.a. | ... |
| 7b | **numero-sem-lastro-na-biblia** (RODAR o scan, não conferir a olho) | ✓/⚠/n.a. | ... |
| 8 | voz-citacao-ficha-tecnica | ✓/⚠/n.a. | ... |
| 9 | voz-comprador-implicita | ✓/⚠/n.a. | ... |
| 10 | termos-tecnico-industriais | ✓/⚠/n.a. | ... |
| 10b | **jargao-tecnico-vazado** (CRÍTICO — SKU/ASIN/datasheet em prosa) | ✓/⚠/n.a. | ... |
| 11 | html-texto-puro | ✓/⚠/n.a. | ... |
| 12 | tamanho-escannavel | ✓/⚠/n.a. | ... |
| 13 | chavoes-por-nicho | ✓/⚠/n.a. | ... |
| 14 | capitalizacao-duplicacao | ✓/⚠/n.a. | ... |
| 15 | concordancia-quebrada-pt-br | ✓/⚠/n.a. | ... |
| 16 | template-para-quem-e | ✓/⚠/n.a. | ... |
| 17 | numeros-em-excesso | ✓/⚠/n.a. | ... |
| 18 | health-absolutes-ymyl | ✓/⚠/n.a. | ... |
| 19 | voz-eximir-responsabilidade | ✓/⚠/n.a. | ... |
| 21 | naturalidade | ✓/⚠/n.a. | ... |
| 22 | **subtitle-keyword-first** (NORMALIZAÇÃO — avaliar CADA subtitle) | ✓/⚠/n.a. | ... |
| 23 | **badge-ausente** (NORMALIZAÇÃO — conferir badge em TODOS) | ✓/⚠/n.a. | ... |
| 24 | **voltagem-citada** (110/127/220V, row Voltagem, bivolt sem specsAmazon) | ✓/⚠/n.a. | ... |
| 25 | ymyl-aviso-repetido (script `ymyl-avisos.py`) | ✓/⚠/n.a. | ... |
| 26 | peso-por-fonte (claim só do specsAmazon como pró central) | ✓/⚠/n.a. | ... |

> Todo critério marcado. `⚠ flag` vira mudança proposta abaixo. Os de NORMALIZAÇÃO (22, 23) raramente são `✓ pass` num artigo recém-criado — se marcar `✓`, justifique na nota (ex.: "11/11 subtitles já keyword-first").

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

3b. **Se `newSubtitle != null`** (critério 22): substituir SÓ a linha `subtitle: "..."` do produto pelo novo subtitle híbrido fluindo (lead keyword-first + gancho, SEM dois-pontos, ≤13 palavras). Linha única, texto puro entre aspas. NÃO mexer se o subtitle era escrito à mão pelo editor (exceção v1.34.0). AUTO-CHECK antes de gravar: zero `:` no valor + ≤13 palavras contadas 1 a 1 (lead incluso) + lead distinto dos outros produtos.

3c. **Se `newBadge != null`** (critério 23, badge-ausente): INSERIR a linha `    badge: "..."` no bloco do produto, logo após a linha `imageAlt:` (antes de `schemaPrice:`). Texto livre ≤3 palavras, distinto dos outros produtos, cor fallback. **Só INSERE quando o badge está AUSENTE** — nunca sobrescreve badge já preenchido (rótulo humano é deliberado).

4. **NÃO** alterar outros campos (`name`, `asin`, `image`, `imageAlt`, `schemaPrice`, `store`, `shortDescription`, `specs`). O `badge` só é TOCADO via `newBadge` (3c) quando AUSENTE — badge já existente nunca é alterado.

5. **NÃO** alterar outros produtos do lineup.

## Validar antes de salvar

- Sem travessão (—) em nenhum campo
- HTML allowlist em fullReview: `<p>`, `<strong>`, `<em>`, `<a>`
- Tag correta nos links (ou crua se config vazia)
- Voz analítica (zero compradores/Amazon/reviews/avaliações)
- Anti-duplicate vs página individual (não reintroduzir frases que estão no fullReview da página individual)

Depois do Edit, rodar `pnpm --filter {site} build`. Se Zod do Astro falhar (raríssimo), reverter do backup e reportar erro.

## Armadilhas recorrentes

### 0. Auditoria por amostragem (a pior — gate de cobertura existe pra matar isso)

**Incidente-origem (melhorairfryer-com/melhor-air-fryer, 2026-06-27):** rodei a auditoria caçando defeito por grep (claims, voz-comprador, `;`, travessão, chavões), achei 3 issues, declarei "8 passaram" e fechei — **sem avaliar os 24 critérios um a um**. Resultado: o critério **22 (subtitle-keyword-first)** e o **23 (badge-ausente)** passaram inteiros (11 subtitles sem keyword no lead, 6 produtos sem badge). Marcelo pegou os dois no olho: "só não passou pq eu tô cobrando você". 

**Por que acontece:** os critérios de NORMALIZAÇÃO (22, 23) não são "defeito que aparece em grep" — são transformação proativa que quase sempre gera proposta. Quem audita "procurando o que está errado" não os vê, porque o subtitle "lê bem" (é o ângulo da criação) e o badge ausente é uma omissão, não um erro visível no texto.

**A trava:** percorrer os 26 e **preencher a Checklist de cobertura** (passo 7 + Formato do relatório) é OBRIGATÓRIO. Produzir a linha de cada critério força avaliá-lo. Relatório sem a checklist completa = inválido. Marcar `✓ pass` em 22/23 num artigo recém-criado exige justificativa na nota.

### 1. Re-flagrar estrutura padrão como tone-clone

Prefixos `Para quem é:`, `Por que gostamos:`, etc são intencionais. **Nunca** flaggar.

### 2. Forçar mudanças quando não tem problema real

Se um review está limpo, vai pra `passed`. Não invente issue pra justificar "ter dado análise".

### 3. Quebrar a estrutura de 4 parágrafos

Quando reescrever `fullReview`, manter os 4 prefixos exatos. `Por que gostamos` pode ter 2 parágrafos (1 features-chave + 1 specs gerais), mas os outros 3 devem ter 1 parágrafo cada.

### 4. Aplicar via parseYaml/stringifyYaml

Bagunça o block scalar `|` do `fullReview` (vira string single-line quoted). Use SEMPRE `Edit` cirúrgico.

### 5. Esquecer de validar links

Validar os 2-3 links de cada produto-alvo: `rel`/`target` presentes e tag **igual** à do config quando houver `?tag=` (URL crua é OK: o build injeta). Tag diferente ou `AFFILIATE_TAG_AQUI` = flag.

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

**Fonte da verdade é ESTA `SKILL.md`** (canon 2026-08-15, ver "Régua comum das auditoras" em `docs/PADROES.md`). O `docs/painel/_data/agent-prompts.json` → `ops.improve_reviews` é **espelho** usado pelos botões do painel (pode defasar; ao mudar régua aqui, refletir lá no mesmo commit quando a mudança afeta o output). Os endpoints legados `generate-*/rewrite-*/create` do painel foram removidos em 2026-05-27; `agent-config.html` virou `editorial.html`. Listas, regex e tetos vivem em `chavoes-por-nicho.json` — cite a chave, não copie a tabela.


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
