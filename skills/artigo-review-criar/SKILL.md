---
name: artigo-review-criar
description: Cria o review editorial de UM produto dentro de um artigo comparativo (6 campos: subtitle, shortDescription, pros, cons, specs, fullReview de 4 parágrafos). Aceita URL do painel (editor-artigo.html?site=X&slug=Y) — detecta stubs vazios e pergunta qual preencher 1 por vez — OU args canônicos `site/slug-artigo ASIN`. Carrega chavões nicho-específicos de `docs/painel/_data/chavoes-por-nicho.json` (Pré Treino, Creatinas, Tablets, etc). Aplica régua editorial: concordância PT-BR, ban "declarado pelo fabricante" como muleta, health absolutes YMYL, hard caps de tamanho (shortDescription ≤250, pros/cons ≤180 texto puro), shortDescription benefício-first, voz consultiva (não corporativa), "Para quem é" varia abertura. Cria backup, commit, push, dispatch VPS pull.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida — fluxo natural depois de adicionar produtos via "+ Adicionar produto"):
- `https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio`
- Extrai `site` e `slug` do artigo

**Comportamento quando URL é fornecida:**
1. Read .mdx do artigo
2. Detecta produtos com **stub vazio** (`fullReview: |` seguido de nada antes do próximo campo, OU `fullReview: ""`)
3. **Cenários:**
   - **0 stubs vazios**: avisa "todos os produtos já têm review preenchido. Use `artigo-reviews-auditar` se quer revisar."
   - **1 stub vazio**: preenche aquele direto
   - **2+ stubs vazios**: **pergunta qual** preencher, listando posição + nome + ASIN. Padrão é **1 por vez** pra controle de qualidade. Exemplo:
     ```
     Encontrei 3 produtos com review vazio:
     1. HP Laser 107W (B07S61ZJCS) — posição 6 no lineup
     2. Canon Pixma MG3620 (B0XXXXXXXX) — posição 7
     3. Brother HL-L2350DW (B0YYYYYYYY) — posição 8

     Qual preencher? (responda com 1, 2 ou 3, ou ASIN direto)
     ```

**B) Args canônicos** (forma direta — power user já sabe ASIN):
- `melhorimpressora/melhor-impressora-custo-beneficio B07S61ZJCS`
- Skill preenche só o ASIN indicado, ignora outros stubs.

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B.

# Preencher review de um produto dentro de um artigo

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:rewrite_product` + (quando o artigo é stub) `make_reviews` pros campos top-level. O conteúdo essencial está duplicado abaixo; em caso de divergência, o prompt canônico ganha.

Você é o curador editorial que escreve o conteúdo do produto-no-artigo. O artigo existe como stub criado pelo endpoint `make-reviews-stub` ou `add-products-stub` do painel. Sua função é **preencher os 6 campos editoriais de um produto específico** seguindo a régua do `formato_full_review` (4 parágrafos marcados, comparativo), e quando o artigo é stub, **também os campos top-level** (title, excerpt, keywordPlural, listHeading, specLabels — **exceto a meta `description`**, que fica pra `artigo-meta-escrever` no fim).

## Pré-requisitos

O `.mdx` do artigo já existe em `sites/{site}/src/content/reviews/{slug}.mdx` com lineup de produtos (criado pelo make-reviews-stub) ou recém-adicionado (add-products-stub). Se não existir, abortar com mensagem clara apontando o botão "✨ Criar artigo" no site detail.

A bíblia do ASIN está OK e a página individual existe (verificado pelo gate Fase 2 quando o stub foi criado).

## Nota terminológica — "lineup"

**"lineup" é jargão técnico interno** do projeto pra "lista de produtos do artigo" (campo `products[]` no frontmatter). Aparece em mensagens de erro técnicas, nomes de endpoints (`make-reviews-stub`, `add-products-stub`), código do painel.

**No output editorial PÚBLICO (o que o usuário lê no site), "lineup" é BANIDA** — termo em inglês que não cabe na voz editorial PT-BR. Use "lista de produtos", "comparativo", "entre os modelos analisados".

Na própria SKILL.md você verá "lineup" em contexto técnico (passos do fluxo, exemplos ❌ ruins, definição da régua de ban). Isso é OK — é a régua descrevendo a si mesma. **Distinção mental**: contexto técnico (skill, código, erros) ≠ output editorial (texto do .mdx).

## Invariantes

- **Nunca invente.** Cada claim numérico tem origem rastreável na bíblia (`specsAmazon`, `doFabricante`, `pontosFortes`, etc).
- **Conteúdo COMPARATIVO** (diferente da página individual): pode comparar com outros produtos do artigo, citar por nome, dizer "vs HP X" se houver dado na bíblia. Pode falar "neste comparativo", "entre os modelos analisados", "aqui". **Banido no output**: "lineup", "desta seleção", "do lineup". Ver ângulo comparativo no campo `fullReview` abaixo.
- **Anti-duplicate vs página individual**: leia o `fullReview` da página individual antes (`sites/{site}/src/content/products/{slug-do-produto}.mdx`). O texto do produto-no-artigo deve ter ângulo DIFERENTE — comparativo, posicionamento no comparativo, etc.
- **Sem travessão (—)** em nenhum campo.
- **Voz analítica**: NUNCA cite compradores/reviews/avaliações/estrelas/Amazon.
- **HTML allowlist no `fullReview`**: `<p>`, `<strong>`, `<em>`, `<a>`. Proibido: `<h2>`, `<h3>`, `<ul>`, `<ol>`, `<table>`, `<img>`, `<script>`.

- **CAMPOS TEXTO-PURO — sem HTML inline** (régua v1.11.5, canon 2026-05-26). A allowlist HTML acima é EXCLUSIVA do `fullReview`. Os demais campos do produto-no-artigo são texto puro renderizado por Astro com `{var}` (escape XSS automático):
  - `subtitle`: texto puro
  - `shortDescription`: texto puro (renderizado em `<p>{var}</p>` no card — `<strong>` literal vira texto pro usuário)
  - `specs[].value`: strings simples sem HTML
  - `pros[N]` / `cons[N]`: formato `<strong>Título</strong>: explicação` — `<strong>` está PERMITIDO **apenas no Título inicial** (template usa `set:html` ali), **NÃO** no meio do texto após o `:`.

  **AUTO-CHECK obrigatório**: antes de gravar o `.mdx`, grep `<strong>`, `<em>`, `<a `, `<p>` em subtitle/shortDescription/specs.value. Se achar — ERRADO. Reescreva como texto puro. Caso real 2026-05-26: `Integralmédica Huger` (página individual) vazou `<strong>energia...</strong>` na shortDescription, apareceu literal no card pro usuário. Mesmo bug-class é vulnerável em produto-no-artigo.
- **Tag-aware**: leia `siteConfig.affiliateTag`. Vazia (sites em construção) → URL crua `https://www.amazon.com.br/dp/{ASIN}`. Preenchida → `?tag={tag}&linkCode=ogi&th=1&psc=1`.
- **Português brasileiro editorial** sem gírias.

## Fluxo

0.5. **Carregar chavões do nicho** (régua v1.18.0, expandida v1.19.0):
   ```bash
   # Identificar nicho do site
   bun -e "console.log(require('./docs/painel/sites-meta.json')['$SITE'].niche)"
   # Ler limites por nicho
   Read docs/painel/_data/chavoes-por-nicho.json
   ```
   Use o bloco `_genericos` + o bloco do nicho específico (ex: `Pré Treino`, `Creatinas`). Durante geração, **respeite os limites como guard rail editorial**:
   - `termos_banidos_absoluto` → 0 ocorrências (inclui peers/claim/stack/SKU/ASIN/lineup)
   - `ingles_max` (vive nos blocos de NICHO, não em `_genericos`) → não passar do número
   - `linguagem_artificial_max` (vive no bloco do NICHO, ex. Pré Treino — NÃO é genérico; v1.32.0 corrige drift) → calibrar/empilhar/pico-e-queda = 0 QUANDO o bloco do nicho listar; em nichos sem o bloco, evite mesmo assim o uso figurado ("calibrada pra rotina" → "feita pra")
   - `corporativo_max` → "diferencial central" cap 2, "posicionamento" cap 3 (v1.19.0)
   - `voz_eximir_responsabilidade` (v1.19.1) → ban "X mg declarados" parentético, "declarado pelo fabricante", "todos/todas/doses declaradas pelo fabricante", "sem mg declarado". Inclui "segundo a [marca]" em spec factual: rendimento/economia/velocidade afirme direto, sem atribuir (atribuição só pra recomendação tipo "a HP recomenda 50-100 págs/mês")
   - `health_absolutes_banidos` → "uso regular é seguro", "alternativa segura", "não causa dano" = 0 (YMYL, v1.19.0)
   - `chavoes_estruturais_max` → "ocupa o papel" cap 2, "rotina de emagrecimento" cap 4, "sustenta intensidade" cap 4 (v1.19.0)
   - `concordancia_quebrada_regex` → composiçãos/combinaçãos/"a produto"/"a formigamento"/"no em 20XX" = 0 (v1.19.0)
   - `comparacoes_max.max_valores_numericos_por_frase` (por nicho) → max 2 valores mg/g/R$ por frase (v1.19.0)
   - `medico_tecnico_max` (por nicho) → variar léxico após atingir limite
   - `industrial_max` → variar com sinônimos PT-BR
   - `indicacao_medica_max` (por nicho) → não repetir advertência médica em N produtos

   Se nicho não listado: usa só `_genericos` (limites menos restritivos).

1. **Parse args**: aceita `{site}/{slug-do-artigo} {ASIN-ou-slug-do-produto}` ou variantes humanas. Eu (Claude) interpreto e formato args canônicos antes.

1.5. **Git pull antes de ler o .mdx** (CRÍTICO — evita falso "produto não está no lineup"):
   ```bash
   git stash push -m "skill-artigo-review-criar-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Pattern de falha resolvida em 2026-05-24: user adiciona produto no painel da VPS (botão "+ Adicionar produto"), painel commita + push pro GitHub. Mac local fica desatualizado (sem auto-pull). Skill lê o .mdx local STALE, não encontra o ASIN, aborta dizendo "produto não está no lineup" — mas o user JÁ ADICIONOU. Pull antes elimina esse falso-negativo.

   Se pull falhar (rede offline, conflito), seguir mesmo assim — o stash pop pode pegar stale. Documentar no relatório.

2. **Read artigo**: `Read sites/{site}/src/content/reviews/{slug}.mdx`. Se 404, abortar.

3. **Localizar o produto** no `products[]` do frontmatter pelo ASIN. Se não encontrado APÓS o pull, abortar com mensagem "Produto X não está no lineup do artigo; use '+ Adicionar produto' antes" — agora sim com confiança que o local está sincronizado.

4. **Read bíblia**: `Read docs/biblias-v2/{ASIN}.json`. Se não existir, abortar.

5. **Read página individual**: tenta `Read sites/{site}/src/content/products/{slugify(bíblia.identidade.nome)}.mdx`. Lê o `fullReview` pra **NÃO REPETIR** ângulo no artigo. Se a página individual não tiver `fullReview` (stub puro), tudo bem — só toma cuidado com o conceito.

6. **Read `affiliateTag`**: `sites/{site}/src/config.ts`. Pode ser `''` (construção, links crus) ou preenchida.

7. **Detectar se o artigo é stub** (`title` e/ou `excerpt` vazios — **NÃO** usar `description` no critério, porque ela fica vazia de propósito até o fim): se sim, gerar também os campos top-level (passo 8a). Se não, só os campos do produto (passo 8b).

8a. **Gerar campos top-level do artigo** (só se stub):
   - `title`: 30-100 chars. Formato: keyword capitalizado + ":" (o resto user completa). Ex: keyword "melhor impressora custo benefício" → title "Melhor Impressora Custo Benefício:"
   - `description` (meta description): **NÃO gerar aqui — deixar vazia (`""`).** A meta description é uma das ÚLTIMAS coisas do artigo: é escrita por `artigo-meta-escrever` só no fim, quando o conteúdo está completo. Gerá-la agora (artigo só com 1 produto, sem intro/guide) produziria uma meta baseada em conteúdo incompleto.
   - `keywordPlural`: forma plural do keyword pro H2 "Comparativo técnico dos {keywordPlural}". Ex: "melhores impressoras custo benefício"
   - `listHeading`: 10-200 chars. H2 que abre a tabela. **SEMPRE plural** (lineup tem 2+ produtos): derive de `keywordPlural`, NUNCA de `keyword` singular. Ex correto: "Quais os melhores pré-treinos em 2026?". Errado: "Qual o melhor pré-treino em 2026?" (singular com lineup multi-produto).
   - `excerpt`: 50-300 chars. Teaser do topo
   - `specLabels`: array de 3-10 labels (intersecção dos specs.label dos produtos no lineup). Pra primeiro produto, deriva direto. Pra produtos adicionados depois, deixa como está e atualiza só se o novo produto tiver labels diferentes.

8b. **Gerar os 6 campos editoriais do produto** seguindo a régua do `formato_full_review` (4 parágrafos marcados):

```html
<p><strong>Para quem é:</strong> perfil de uso. Inclua 1 link Amazon no nome do produto.</p>
<p><strong>Por que gostamos:</strong> features-chave com dados concretos. Inclua 1 link Amazon na primeira menção. Pode dividir em 2 parágrafos se >5-6 frases (primeiro features-chave, segundo specs gerais).</p>
<p><strong>Pontos de atenção:</strong> trade-offs, limitações. SEM link de afiliado neste parágrafo.</p>
<p><strong>Resumo:</strong> fechamento conciso. Inclua 1 link Amazon na última menção.</p>
```

**🚨 RÉGUA "Para quem é" — VARIAR ABERTURA (v1.19.0, canon 2026-05-28)**

**Bug detectado em batch melhorpretreino v1.18.x**: 7 dos 11 produtos abriram com `[Produto] ocupa o papel de [Badge] porque...` — template óbvio, pareceu gerado em bloco. **ChatGPT-Bárbara flagou crítico**.

**Régua nova**: o "Para quem é:" **NUNCA** deve começar com a fórmula `[Produto] ocupa o papel de [Badge]`. Varie entre 6+ aberturas canônicas:

| Padrão | Exemplo |
|---|---|
| **Perfil + benefício** | "Para quem treina à noite e busca disposição sem cafeína..." |
| **Contexto comparativo** | "Entre as opções sem cafeína da seleção, este produto se destaca..." |
| **Conexão funcional** | "Combina melhor com quem busca pump intenso e foco mental..." |
| **Proposta direta** | "A proposta aqui é atender quem precisa de dose alta de creatina..." |
| **Diferencial-âncora** | "O grande ponto deste produto é a fórmula sem aditivos artificiais..." |
| **Cenário concreto** | "Se você imprime poucas páginas por mês e quer custo baixo de entrada..." |
| **Adjetivo posicional + perfil** | "Vegano e com sabor agradável, é ideal pra quem..." |

**Limite duro**: máximo **2 produtos por artigo** podem usar "ocupa o papel de [badge]" (já está no JSON como `chavoes_estruturais_max.ocupa o papel: 2`). Os demais variam.

**Auto-check antes de gravar**: grep `ocupa o papel` no review gerado. Se aparecer + outros 2 produtos do artigo já usam — reescreve abertura.

**Adendo PT-BR — title case mid-sentence (v1.20.0)**: posicionadores como "é o melhor para X", "ganha o título de X", "entra como X" são ok — mas X deve ir em **minúsculo** em PT-BR, pois a frase continua no meio de um parágrafo. O campo `subtitle` do produto usa title case (exibido no card), mas ao adaptá-lo para prosa, converta para lowercase.

❌ "é o **M**elhor para **G**astar mais **E**nergia porque..."
✅ "é o **m**elhor para gastar mais energia porque..."

❌ "ganha o título de **M**elhor **F**órmula **E**quilibrada"
✅ "ganha o título de melhor fórmula equilibrada"

**Auto-check adicional**: no Para quem é gerado, grep `é o [A-Z]`, `é a [A-Z]`, `como [A-Z]`, `título de [A-Z]`. Se encontrar maiúscula — verifique se é nome próprio de produto/marca. Se não for, converta pra minúsculo.

**Régua keyword no Para quem é (v1.20.1, canon 2026-05-29)**: prefira inserir a **keyword-raiz do nicho** no claim, com estrutura fixa `o [Produto] é o melhor [keyword] para/de/com [ângulo]`, VARIANDO só a abertura antes dela. A keyword consistente reforça SEO; a abertura variada evita tone-clone.

Estrutura: `[abertura variada], o [Produto] é o melhor [keyword] para [ângulo do produto]`

Exemplos (nicho pré-treino, ângulo vindo do subtitle de cada produto):
- "Se você prioriza treino intenso, o FTW Diabo Verde é o melhor pré-treino para treino intenso, porque..."
- "Para quem treina à noite, o Night Train é o melhor pré-treino para treino noturno, por ser..."
- "Quando a concentração é o que falta, o Darkness é o melhor pré-treino para foco mental, porque..."

Aberturas variam (Se você prioriza X / Para quem busca X / Ideal para quem X / Quando o objetivo é X / Pensando em X / Voltado a quem X). O miolo `é o melhor [keyword] para [ângulo]` é o constante.

Ângulos que não encaixam em "para X" usam "de X" / "com X" / adjetivo: "o melhor pré-treino premium", "o melhor pré-treino de fórmula natural", "o melhor pré-treino clean label".

**Não force nos 100%**: 1-2 produtos com abertura narrativa própria ("o X sobe um degrau", "o X ocupa espaço único") são variação saudável — não precisam do claim-keyword se a abertura já é forte e distinta.

- **3 links de afiliado** total (Para quem é + Por que gostamos + Resumo). SEM link em "Pontos de atenção".
- Formato dos links: `<a href="{amazonUrl}" rel="nofollow" target="_blank">Nome do Produto</a>` onde `amazonUrl` é crua quando tag vazia, com tag quando preenchida.

- **pros** (3-8 itens): formato `<strong>Título</strong>: explicação com dado concreto`.
  - ✓ "<strong>Rendimento elevado</strong>: 4.500 páginas em preto por kit T544" (spec factual direto, sem "segundo o fabricante")
  - ❌ "<strong>Rendimento alto</strong>: a impressora rende muito" (sem dado)

- **cons** (1-5 itens): mesma formatação.

- **specs** (3-10 pares label/value): strings simples sem HTML. Reuso labels comuns do lineup pra alinhar com `specLabels`.

- **subtitle** (10-150 chars): título descritivo curto, sem redundância com nome.

- **shortDescription** (50-250 chars, alvo 180-230): padrão BENEFÍCIO-FIRST. 1-2 frases que abrem com posicionamento/perfil, técnico justifica depois. **HARD CAP 250 chars.** Drop "[Tipo] brasileiro/a da [marca]", drop "preço médio em torno", drop público verboso. Ver seção dedicada abaixo com 3 moldes + exemplos.

9. **Validar mentalmente** antes de salvar:
   - **Tamanhos** (hard caps — v1.16.0):
     - `shortDescription` ≤ 250 chars (alvo 180-230, **padrão benefício-first** — 1ª frase é posicionamento, não ficha técnica)
     - cada item de `pros` ≤ 180 chars (alvo 80-130)
     - cada item de `cons` ≤ 180 chars (alvo 80-130)
     - `fullReview` 800-3000 chars
     - Passou? reescreve **só o item que estourou** (não o review inteiro)
   - **Banidas no output** (v1.16.0): grep por `lineup`, `desta seleção`, `do lineup`, `do nosso lineup`, `do nosso comparativo` — se achar, reescreve
   - **Cota cross-produto**: máximo 2 peers citados por bullet/parágrafo (ver Armadilha 7)
   - HTML allowlist OK no fullReview
   - Sem travessão
   - Tag correta nos links (ou cruas se config vazia)
   - Voz analítica (zero "compradores", "reviews", "avaliações", "posicionamento Amazon")
   - Voz-citação ficha-técnica (zero "alérgenos confirmam", "atributos declaram", "conforme tipo de dieta", "apontada pelo fabricante como") — spec factual vai direto; atribuição só pra recomendação/calibração do fabricante, ver Armadilha 4
   - Anti-duplicate vs página individual (frases não-repetidas)
   - Tom natural (v1.32.0): rótulos passam no teste-da-Amazon, zero meta-SEO, máx 1 coloquialismo, sem antropomorfismo com gíria

10. **Backup**: `docs/painel/.painel-backups/{YYYY-MM-DD}/article-{site}-{slug}-{HHMMSS}-prod-{ASIN}.mdx`. Pattern paralelo ao do painel pra aparecer no card "Histórico de versões".

11. **Write `.mdx`**: usa parseYaml + stringifyYaml lib pra reconstruir, OU editar cirurgicamente o trecho do produto-alvo. Cuidado pra:
    - Preservar produtos não-alvo intactos (não tocar)
    - Preservar `fullReview` block scalar (`|`) — re-parsear+stringificar pode bagunçar HTML multi-linha. Recomendo edição cirúrgica via Edit tool quando possível.
    - Atualizar campos top-level só se foram detectados como stub

12. **Git add + commit + push**:
    ```bash
    git add sites/{site}/src/content/reviews/{slug}.mdx
    git commit --no-verify -m "feat({site}): preenche review de {ASIN} em {slug} via skill" \
      -m "Co-Authored-By: {modelo da sessão} <noreply@anthropic.com>"
    git push origin main
    ```
    `--no-verify` é OBRIGATÓRIO: o pre-commit hook roda `audit-article.ts` no artigo staged e bloqueia se houver QUALQUER erro — artigo no meio do pipeline (sem meta/intro/guide, reviews faltando) sempre tem. A skill é o caminho oficial de escrita.

13. **Disparar git pull no painel da VPS**:
    ```bash
    bash scripts/painel-vps-pull.sh
    ```
    Script usa Basic Auth do painel (creds em `.env.painel-skills`).
    Substituiu SSH direto — funciona pra Marcelo e Bárbara.

14. **Reportar no chat**: counts por campo + se gerou campos top-level + path do arquivo.

## Os 6 campos do produto-no-artigo

### subtitle (10-150 chars)
Título descritivo curto, sem redundância com nome. Ex: para "Epson EcoTank L3250": "Multifuncional EcoTank com Wi-Fi, ideal para casa e home office".

### shortDescription (50-250 chars, alvo 180-230) — padrão BENEFÍCIO-FIRST

**HARD CAP em 250 chars.** Aparece num card visual (TabelaProdutos / TopPickCard) e é a primeira coisa que o leitor lê pra decidir se quer ler mais. **NÃO PODE SER FICHA TÉCNICA** — tem que enganchar pelo benefício/posicionamento.

**Padrão obrigatório (régua v1.17.0, canon 2026-05-28): benefício/posicionamento PRIMEIRO, técnico DEPOIS.**

Estrutura geral em 3 partes:
1. **Frase de abertura: benefício, posicionamento ou perfil** — engancha o leitor
2. **2-3 specs essenciais** — justifica com o concreto
3. **Destaque, diferencial ou fecho com benefício** — reforça

**3 moldes recomendados (varie entre produtos do mesmo artigo):**

**Molde A — Perfil + benefício** (estilo "câmera de segurança"):
> "Ideal pra quem [perfil/objetivo], entrega [função/spec curta]. Você ganha [benefício]."

**Molde B — Adjetivo posicional + spec + destaque** (estilo "aspirador"):
> "[Adjetivos] pra [perfil]. Combina/Reúne [spec 1] e [spec 2]. Destaque para [diferencial]."

**Molde C — Posicionamento direto + técnico justifica** (estilo "Custo-benefício forte..."):
> "[Posicionamento curto] pra [perfil]. [Fórmula/spec essencial]. [Embalagem ou diferencial]."

**Exemplos ✅** (canon `melhorpretreino` V4, validado editorialmente):

```
"Custo-benefício forte e fórmula completa pra iniciantes ou rotina contínua.
Combina creatina, beta-alanina, taurina e cafeína anidra em dose pequena de 5g,
com pote de 300g que rende 60 doses por cerca de R$ 55."
(211 ch — Molde C: posicionamento + spec + embalagem)

"Vegano, com sabor agradável Pink Lemonade e sem o formigamento da beta-alanina.
Entrega 150mg de cafeína moderada e 16g de palatinose (energia gradual) em
embalagem de 500g, a maior da categoria."
(195 ch — Molde B: adjetivos + perfil + spec + destaque)

"Ideal pra quem treina à noite ou é sensível a estimulantes, entrega disposição
muscular via 2g de beta-alanina e aminoácidos, sem cafeína na fórmula.
Você ganha mais intensidade no treino sem comprometer o descanso."
(225 ch — Molde A: perfil + spec + benefício)
```

**Exemplos ❌ (técnico-first, REGRESSÃO real do melhorpretreino pré-v1.17.0):**

```
"Pré-treino brasileiro da Adaptogen Science com 400 mg de cafeína, 2 g de beta-alanina,
1 g de creatina e 1 g de taurina por porção de 10 g, todos declarados pelo fabricante.
Sabor morango, pote de 300 g, preço médio em torno de R$ 78. Voltado para quem treina
em rotina de emagrecimento e quer manter intensidade no treino..."
(391 ch — começa com marca + listagem completa de specs; perde o leitor antes de
chegar no posicionamento que está no fim)
```

→ **Fix**: inverta. Coloca posicionamento/benefício na 1ª frase. Drop "brasileiro da X",
drop "todos declarados pelo fabricante", drop "preço médio em torno", drop público verboso.

**Drop SEMPRE:**
- ❌ "**brasileiro da [marca]**" — marca já está no campo `name` (renderizado no card acima)
- ❌ "**todos declarados pelo fabricante**" — implícito
- ❌ "**preço médio em torno de R$ X**" — preço já está nas specs e na tabela
- ❌ **Público-alvo verboso** ("Voltado para quem treina em rotina de emagrecimento e quer manter intensidade no treino mesmo em déficit calórico...")
- ❌ **Lista completa de ingredientes** — pega só 2-3 chave, resto vai pro fullReview

**Adicionar:**
- ✅ **Adjetivos posicionais** ("Custo-benefício forte", "Vegano", "Premium", "Foco mental")
- ✅ **Conexão emocional/funcional** ("Ideal pra quem...", "Você ganha...", "Pra quem...")
- ✅ **Destaque do diferencial** ("Destaque para...")

**Régua de corte mental** — antes de salvar, leia a 1ª frase do shortDescription:
- Começa com "Pré-treino com X mg de Y..." ou "[Tipo] brasileiro da [marca]..." → **ERRADO**. Inverta.
- Começa com adjetivo posicional, "Ideal pra...", "Você ganha...", "Custo-benefício..." → **CERTO**.

### fullReview (HTML, ~800-3000 chars)
**Estrutura obrigatória — 4 parágrafos marcados** (idêntico ao `formato_full_review` shared):

```html
<p><strong>Para quem é:</strong> ... <a href="{amazonUrl}">{nome}</a> ...</p>
<p><strong>Por que gostamos:</strong> ... <a href="{amazonUrl}">{nome ou variante}</a> ...</p>
<p><strong>Pontos de atenção:</strong> ...</p>
<p><strong>Resumo:</strong> ... <a href="{amazonUrl}">{nome}</a> ...</p>
```

**Ângulo COMPARATIVO** (diferente da página individual que é autônoma):
- Pode mencionar "neste comparativo", "entre os modelos analisados", "aqui"
- Pode comparar com outros produtos pelo nome (sem prefixo "do lineup")
- Pode dizer "diferente do produto anterior" se houver fluxo narrativo

**Banidas no output editorial** (régua v1.16.0 + v1.17.2 + v1.17.3, canon 2026-05-28):

**🚨 JARGÃO TÉCNICO/INTERNO ABSOLUTAMENTE PROIBIDO** (régua v1.17.3 — gap descoberto via melhorpretreino vazou "SKU avaliado" + "ASIN aqui só vem em..."):
- ❌ `SKU` — termo de dev/estoque que ninguém entende. Use "a versão", "este modelo", "esta apresentação"
- ❌ `ASIN` — identificador Amazon interno. Use "o produto avaliado", "a versão analisada", "este item"
- ❌ `UPC`, `EAN`, `GTIN` — códigos de barras, jargão técnico. Drop ou usar "código do produto" se relevante
- ❌ `datasheet` — jargão de engenharia. Use "ficha técnica" / "rótulo"
- ❌ `dataset`, `metadata`, `frontmatter` — jargão dev
- ❌ `notificado` (regulatório) — soa bula. Use "registrado" / "regulado pela ANVISA"
- ❌ Procedência burocrática: "anúncio Amazon", "datasheet do fabricante", "número de notificação N°..." — drop ou simplifica

**Outras banidas:**
- ❌ "lineup" — palavra puramente interna, jamais aparece em texto público
- ❌ **TODAS as variantes de "seleção"** como muleta repetida em reviews de produto:
  - "desta seleção", "nesta seleção", "na seleção", "da seleção"
  - "do lineup", "do nosso lineup", "do nosso comparativo"
  - **Padrão proibido**: "ocupa nesta seleção o papel de X", "X nesta seleção é a presença de Y", "outros pré-treinos da seleção"
  - **Exceção CANÔNICA**: 2 frases da intro do body (`artigo-intro-escrever`):
    - Abertura: "Preparamos uma seleção pra..."
    - Fechamento: "Esta seleção reúne os melhores X disponíveis... ✅"
    - Essas 2 são frases LEGADAS permitidas pela régua de intro (padrão até v1.30; a v1.31+ não as empurra mais) e **não contam** como chavão
- ❌ Listar mais de 2 peers num único trecho (ver Armadilha 7 abaixo)

Substitua:
| ❌ Antes | ✓ Depois |
|---|---|
| "único do lineup com cromo" | "único com cromo entre os analisados" |
| "Black Skull B.O.P.E desta seleção" | "Black Skull B.O.P.E" (sem qualificar — contexto claro) |
| "as outras opções desta seleção (X, Y, Z)" | "as outras opções aqui" |
| "todos os 9 outros desta seleção" | "todos os outros analisados" |
| "vantagem vs o Adaptogen Panic do lineup" | "vantagem vs o Adaptogen Panic" |

**Quota dura**: máximo **1 menção** a "comparativo"/"seleção"/"aqui"/"analisados" **por bullet ou parágrafo**. Repetir = drop.

### pros (3-8 itens, cada item 60-180 chars, alvo 80-130)
`<strong>Título</strong>: explicação com dado concreto`. Sempre dado verificável.

**HARD CAP em 180 chars por item** — passou = reescreve mais curto. Canon `melhoraspirador`: média 65 chars/item, máx 93.

✅ **BOM** (88 chars):
> "<strong>Preço mais acessível</strong>: cerca de R$ 40, o mais barato deste comparativo."

❌ **RUIM** (310 chars, caso real FTW Diabo Verde):
> "<strong>Preço mais acessível do lineup</strong>: cerca de R$ 40, abaixo do Black Skull B.O.P.E (R$ 55), Adaptogen Panic (R$ 78), 3VS Prohibido (R$ 80), Max Titanium Night Train e Darkness Évora XT (R$ 90 cada), Dux Pre Workout (R$ 110) e +Mu Exquenta (R$ 130) desta seleção."

A lista exaustiva de 8 preços virou tabela em texto. Quem quer comparar vai na TabelaTop. Bullet é pra escannar em 2 segundos.

### cons (1-5 itens, cada item 60-180 chars, alvo 80-130)
Mesma formatação e mesmos limites dos pros. Trade-offs reais.

### specs (3-10 pares label/value)
Specs técnicas derivadas de `specsAmazon`/`doFabricante`/`conteudoBrutoFabricante`. Strings simples. Reuso labels do lineup quando possível.

## Voz editorial

Idêntica à da página individual (mesma régua):
- Tom de quem testou/analisou
- NUNCA cite **compradores, reviews, avaliações, estrelas, posicionamento Amazon**
- Reescreva insights de `sentimentoCompradores` como observação editorial direta

> **Sobre citar o fabricante**: regra diferente. Spec factual (rendimento, velocidade, economia) vai afirmado direto, sem "segundo X". Atribuir só vale pra recomendação/calibração/política do fabricante (ex: "a HP recomenda 50-100 págs/mês"). Ver Armadilha 4 abaixo pra régua completa.

## Tom conversacional (CRÍTICO)

A pergunta-teste antes de salvar qualquer campo:
> *"Um amigo que não entende disso entenderia e saberia o que fazer?"*

Se não → simplifica.

Reviews afiliados são **especialista explicando pra amigo ou vizinho**: claro, direto, fluido. Sem jargão corporativo, sem formalidade institucional. Use 2ª pessoa quando faz sentido ("se você imprime em casa..."), descreva uso real ("você abre uma tampa, derrama a garrafa direto, e pronto"), conecte com a situação do leitor ("está cansado de gastar com cartucho").

**Padrões de tom — antes/depois:**

| ❌ Formal/corporativo | ✓ Conversacional |
|---|---|
| "atende quem busca dose alta de EPA e DHA" | "se você quer dose cheia de EPA e DHA em poucas cápsulas" |
| "O posicionamento da X em suplementação esportiva" | "se você treina e quer um da linha esportiva" |
| "alinhado à narrativa de procedência" | "isso encaixa com a história de pureza do produto" |
| "estrutura química mais próxima do óleo de peixe in natura" | "molécula mais parecida com o óleo natural" |
| "perfil de absorção favorável" | "absorve melhor" |
| "uma rotina de suplementação séria" | "uma rotina contínua" |
| "números compatíveis com" | "boa dose pra" |
| "tradicionalmente associada a" | "conhecida por" |

**Referências canônicas do projeto pra calibrar tom** (leia se desconfia que o output está formal demais):
- `sites/melhorimpressora/src/content/products/epson-ecotank-l3250.mdx`
- `sites/melhorimpressora/src/content/reviews/melhor-impressora-custo-beneficio.mdx`

## Tom natural e rótulos REAIS (v1.32.0, canon Marcelo 2026-06-10)

Conversacional ≠ personagem. Caso real: a home do melhorimpressora acumulou "máquina de trabalho", "impressora para imagem", "no batente", "se reconserta", "desembolso" — 16 trechos não-naturais num artigo só.

**1. Teste-da-Amazon pros rótulos de categoria**: só use rótulo que EXISTE no varejo (você digitaria isso na busca da Amazon?).

| ❌ Inventado | ✓ Real |
|---|---|
| "máquina de trabalho" | "impressora de escritório" |
| "impressora para imagem" | "impressora fotográfica" |
| "faixa fotográfica" | "conjunto de 6 tintas" |
| "cadência de negócio" | "velocidade pra escritório" |
| "preço de custo-benefício" | "preço justo" |

**2. Elipse de categoria é LIBERADA** (não invente substituto): "a barata", "a doméstica", "a laser", "as de tanque", "a fotográfica" são português natural — use-as pra não repetir o nome da categoria 40 vezes.

**3. PROIBIDO meta-SEO**: nunca mencionar a busca/keyword do leitor ("tem gente que digita X na busca...", "quando a busca esconde..."). O leitor não veio ler sobre a própria pesquisa — reescreva pelo cenário direto ("Nem toda impressora é pra casa...").

**4. Antropomorfismo com gíria = 0**: aparelho "no batente", rede que "se reconserta" (verbo inventado), impressora que "quer um canto". Personificação leve SÓ quando explica ("o Wi-Fi se conserta sozinho" ✓).

**5. Jargão financeiro/burocrático**: "desembolso"→"preço" · "comprometer dinheiro"→"gastar" · "reprografia"→"cópia e digitalização" · "na frente do consumível"→"no consumível".

**6. Atribuição elíptica é a mesma muleta de "segundo a [marca]"** (v1.21.1): "tinta pra milhares de páginas, conta da Epson" → afirme o número direto ("tinta pra 6.600 páginas em preto").

**7. Máximo 1 expressão coloquial leve por review** (pode ser zero); analogia só quando explica algo. Teste final: leia em voz alta como se explicasse pra um cliente — soou personagem ou corporativo, simplifica.

## Subtitle humano = ângulo do review (v1.34.0, canon Marcelo 2026-06-10)

Quando o stub já vem com `subtitle` (e/ou `badge`) preenchido pelo editor humano (modal "+ Adicionar produto" do painel), isso NÃO é placeholder: **é a direção editorial** — "normalmente é o ângulo que queremos que você aborde o produto" (Marcelo).

1. **Ângulo VINCULANTE**: o review inteiro aborda o produto por esse ângulo — o "Para quem é" deriva dele (reforça a régua v1.20.1, que já manda derivar o claim do subtitle), os pros priorizam o que o sustenta.
2. **Texto MELHORÁVEL**: você tem liberdade de polir o subtitle (concisão, clareza, régua 10-150 chars, title case) — mas o SENTIDO não muda. Trocar "tanque pra alto volume" por "multifuncional compacta" = violação; polir "boa pra muito volume" → "Tanque de alto volume pra rotina pesada" = ok.
3. **Subtitle vazio** = comportamento atual (criar do zero a partir da bíblia + badge).
4. **NUNCA descartar silenciosamente** o ângulo humano. Se a bíblia CONTRADIZ o ângulo (ex: subtitle diz "a mais rápida" e a bíblia mostra que não é), NÃO grave nada conflitante: pare e pergunte ao usuário.

Histórico: até v1.33 a skill regenerava o subtitle sem ler o existente (~80% dos subtitles humanos sobrescritos; os ~20% "mantidos" eram convergência por acaso). O badge sempre teve esse tratamento (var + hint editorial) — esta régua espelha pro subtitle.

## Operação de destilação bíblia → .mdx (CRÍTICO)

A bíblia carrega claims COM marcadores de procedência (`fonte: "specs"`, "conforme declarado pelo fabricante", "confirmado nos alérgenos"). É correto e útil internamente — rastreabilidade evita invenção. **O .mdx público é destilado**: droppa marcadores que viraram ruído burocrático.

**4 categorias de claim — como destilar cada:**

| Tipo | Bíblia (raw, OK) | .mdx destilado |
|---|---|---|
| **A) Fato verificável simples** | "Sem glúten confirmado nos alérgenos da Amazon" | "Sem glúten" |
| **B) Claim do fabricante repetível** | "Forma triglicerídeo, apontada pelo fabricante como mais absorvível" | "Forma triglicerídeo, considerada mais absorvível" |
| **C) Claim institucional / PR** | "Marca tradicional brasileira segundo o próprio fabricante" | "Marca brasileira" (ou omite se não agrega) |
| **D) Voz comprador implícita** | "Cápsulas sem sabor segundo relatos de compradores" | "Cápsulas sem sabor" |

**Exceção (raro, mas existe)**: recomendação/calibração/política do fabricante (ex: "a HP recomenda 50-100 págs/mês") pode manter "segundo X". Spec factual (rendimento, velocidade) NÃO — vai direto. Ver Armadilha 4 abaixo.

### AUTO-CHECK categoria D — voz-comprador IMPLÍCITA (régua v1.11.4, canon 2026-05-26)

**Categoria D é a mais traiçoeira** porque a voz-comprador vem SUTIL — não tem palavra-flag óbvia ("compradores destacam"), tem fraseado conversacional que parece análise editorial mas é relato disfarçado.

**Bíblias com voz EXPLÍCITA** ("elogiado nas opiniões", "relato recorrente"): você reconhece e destila. Fácil.
**Bíblias com voz IMPLÍCITA** ("um comprador relata", "divide opiniões", "vista por alguns como"): você COPIA LITERAL achando que é análise. Erro.

**Exemplos pareados (errado vs certo)** — TODOS de casos reais 2026-05-26 (batch melhorpretreino: dux-energy-kick, dux-pre-workout):

| ❌ Voz-comprador implícita (copiado da bíblia) | ✓ Destilado pra voz editorial |
|---|---|
| "um comprador relata sentir energia em 15 minutos" | "início rápido percebido em ~15 minutos" |
| "divide opiniões pelo sabor adocicado" | "sabor adocicado, agrada perfis específicos" |
| "vista por alguns como queda de energia depois de 2h" | "duração efetiva ~2h, requer dose espaçada em treinos longos" |
| "elogiada pela facilidade de dissolução" | "dissolve facilmente" |
| "relatada como menos potente que a versão anterior" | "potência reduzida vs versão anterior" |
| "considerada cara por parte dos compradores" | drop (preço já tem qualificador objetivo em outro lugar) |

**Auto-check obrigatório antes de gravar — grep por palavras-flag**:
- "um comprador", "alguns compradores", "parte dos compradores"
- "relata", "relatos", "relatado", "relatada"
- "divide opiniões", "vista por alguns", "considerada por", "elogiada por"
- "queixas", "elogios", "feedback dos"

Se aparecer QUALQUER ocorrência → reescreva como observação editorial direta. Sem citar quem fala. Categoria D bem destilada vira **observação técnica curta sem sujeito-comprador**.

### TERMOS TÉCNICO-INDUSTRIAIS PROIBIDOS (régua v1.11.4 formalizada, canon 2026-05-26)

Termos de **rotulagem industrial** soam burocráticos e quebram voz editorial. Régua existia em audits desde 2026-05-17 mas só foi formalizada em 2026-05-26.

**Proibidos em todo o conteúdo do produto-no-artigo**:
- "contaminação cruzada"
- "linha de produção compartilhada" (sem contexto editorial)
- "padrões de fabricação ISO XXXX" (sem agregar valor ao leitor)
- "boas práticas de fabricação" (BPF — só técnico)
- "lote de fabricação", "rastreabilidade do lote" (técnico-regulatório)

**Substituições editoriais**:
- ❌ "Pode ter contaminação cruzada com glúten" → ✓ "Pode conter traços de glúten. Leia a rotulagem antes do uso."
- ❌ "Linha de produção compartilhada com produtos com lactose" → ✓ "Pode conter traços de lactose. Confira a rotulagem se você é sensível."
- ❌ "Atende padrões ISO 22000 de segurança alimentar" → drop ou "produto seguindo padrões reconhecidos da categoria" (se agregar)

**Por quê proibido**: reviews afiliados são especialista→amigo, não bula técnica. Termo técnico-industrial sinaliza copy-paste de ficha técnica ou ChatGPT genérico — quebra confiança editorial.

## Peso por fonte

Ao decidir QUAL claim vira pro central no artigo vs. spec:

| Combinação de fontes | Confiança | Onde usar |
|---|---|---|
| Fabricante + Amazon coincidem | **FORTE** | Pode ser pro central, strong, ênfase no fullReview |
| Só fabricante | MÉDIO | OK em pros/specs, descrição própria (sem "segundo X") |
| Só Amazon (specsAmazon) | **FRACO** | Só na tabela specs, NÃO vira pro central |
| Só opiniões | FRACO | Inspira voz, não cita |

**Caso real (Vitafor B07L5W6GVC)**: "Composição cetogênica" vem de `Tipo de dieta: Cetogênica` nas specs Amazon — fonte fraca, classificação automática do marketplace. Vai na tabela specs, **não vira pro central**. Óleo de peixe é trivialmente keto; elevar isso a "diferencial" engana o leitor.

## Filtros editoriais

- Specs ambientais (Energy Star, EPEAT, RoHS, % reciclado) → omitir
- Origem de fabricação (Brasil, Made in X) → omitir
- Exceção: se bíblia tem ângulo explícito (sustentabilidade, produto-nacional) em `angulosConversao`

## Restrições finais

- Sem travessão (—)
- Sem superlativos ABSOLUTOS sem evidência ("o melhor", "o mais X", "incomparável", "único", "imbatível")
- ✓ Qualificadores positivos simples ("excelente", "ótimo", "muito bom") são OK — reviews são levemente inclinados ao positivo por design (diretriz #2 da bíblia)
- ✓ Superlativas qualificadas com dado: "entre as mais econômicas da categoria" (se houver concorrentes na bíblia)
- Densidade ~5-7 dados quantitativos no fullReview

## Anti-duplicate vs página individual

**Antes de gerar**, leia a página individual do produto (`content/products/{slug}.mdx`) e identifique frases-chave do `fullReview`. **Não repita** essas frases no artigo. Use ângulo comparativo (vs autônomo da página individual):

| Página individual (autônoma) | Produto no artigo (comparativo) |
|---|---|
| "A L3250 é uma multifuncional pensada para uso doméstico" | "Aqui, a L3250 cobre o perfil doméstico" |
| "O diferencial central é o sistema EcoTank" | "Comparada às outras impressoras analisadas, a L3250 destaca-se pelo sistema EcoTank" |

## Armadilhas recorrentes

### 1. Repetir frase exata da página individual
Confere antes de salvar. Se uma frase específica está na página individual, reescreva.

### 2. HTML proibido por hábito
`<ul>` é tentador pra listar features. Use parágrafos.

### 3. Comparações sem dado
"Uma das mais econômicas" sem `concorrentes` na bíblia é especulação. Use linguagem absoluta com dado: "rende 4.500 páginas por kit" em vez de "rende mais que a maioria".

### 4. Voz de citação — comprador, fabricante, Amazon ("segundo X", "alérgenos confirmam", "atributos declaram")

**Armadilha mais comum e fácil de cair.** Quando os dados da bíblia vêm de várias fontes, o modelo tende a citar a fonte pra justificar o claim. Há 3 tipos de citação com tratamentos diferentes:

**A) Citar comprador → SEMPRE proibido**
- ❌ "Compradores destacam X" → "X destaca-se por {dado da bíblia}"
- ❌ "Relato recorrente nas opiniões indica cápsulas sem sabor" → "cápsulas sem sabor"
- ❌ "Citada como motivo de preferência por um comprador" → drop ou reformula

**B) Citar Amazon/specs → SEMPRE proibido (burocrático)**
- ❌ "alérgenos da Amazon confirmam ausência de glúten" → "sem glúten"
- ❌ "atributos de material declaram ausência de contaminantes" → "livre de contaminantes"
- ❌ "conforme tipo de dieta declarado" → "compatível com dieta X"

**C) Citar fabricante → CONDICIONAL (editorial OK em casos específicos)**

Régua: voz-citação do fabricante OK SÓ quando atende AS DUAS condições:
1. **(a)** é recomendação/calibração/política do fabricante (ex: "a HP recomenda 50-100 págs/mês"), NÃO spec factual — rendimento/economia/velocidade vão direto, sem atribuir
2. **(b)** adiciona valor editorial ao leitor (calibra expectativa, sinaliza honestidade, faz crítica)

**✓ EDITORIAL OK** (referência: `sites/melhorimpressora/src/content/products/epson-ecotank-l3250.mdx`):
- "rende até 4.500 páginas em preto" → spec de fabricante afirmado direto, sem "segundo a Epson"
- "número de marketing 33 ppm, mas a **velocidade ISO (padrão da indústria)** é mais realista" → crítica útil
- "a HP recomenda volume de 50 a 100 páginas mensais" → claim só-fabricante + ajuda leitor calibrar

**❌ BUROCRÁTICA** (drop sempre):
- "apontada pelo fabricante como mais absorvível" → "considerada mais absorvível"
- "segundo o próprio fabricante" como muleta repetitiva → drop
- "conforme o fabricante" sem qualificar nada → drop

**Tratamento de divergências internas** (dadosInconsistentes): a `decisaoEditorial` da bíblia já diz qual lado tomar. Aplica direto, sem mencionar o conflito.

**Antes de gravar, faça grep mental**: se aparece "confirmado", "declarado", "apontada", "conforme X", "segundo Y", "relato recorrente", "atributos de material" — reescreva. Exceção: passou nos 2 critérios editoriais (C) acima.

### 5. Atualizar campos top-level quando não-stub
Se o artigo já tem `title`, `description`, `excerpt` populados, NÃO sobrescreva (preserva trabalho do user). Só preenche se estão vazios.

### 6. Block scalar `|` no fullReview
Se reusar a abordagem yaml.parseYaml + stringify, fullReview pode mudar de `|` pra string quoted, bagunçando HTML. Recomendado: edição cirúrgica com Edit tool no trecho do produto-alvo, preservando o resto do arquivo intacto.

### 7. Listagem exaustiva de peers num único bullet (régua v1.16.0)

**Armadilha clássica em pros/cons de preço/rendimento**: o modelo lista TODOS os outros produtos do comparativo num bullet só, virando uma mini-tabela em texto.

**Limite duro**: máximo **2 peers citados por bullet ou parágrafo**. Se a comparação precisa mostrar 3+ produtos, **deixa pra TabelaTop** (que já é tabela visual com todos os preços/specs).

❌ **Caso real FTW Diabo Verde** (310 chars, lista 8 preços):
> "<strong>Preço mais acessível do lineup</strong>: cerca de R$ 40, abaixo do Black Skull B.O.P.E (R$ 55), Adaptogen Panic (R$ 78), 3VS Prohibido (R$ 80), Max Titanium Night Train e Darkness Évora XT (R$ 90 cada), Dux Pre Workout (R$ 110) e +Mu Exquenta (R$ 130) desta seleção."

✓ **Reescrito** (~85 chars):
> "<strong>Preço mais acessível</strong>: cerca de R$ 40, o mais barato deste comparativo."

✓ **Variante com 1-2 peers concretos** (também OK):
> "<strong>Preço bem abaixo da média</strong>: R$ 40, contra R$ 110 do mais caro analisado."

A lista exaustiva diz "olha quanto cada um custa" — função da tabela. O bullet diz "este é barato" — função do bullet.

### 8. Repetição de frases-padrão entre produtos (régua v1.16.0)

Frases idênticas literais (ou quase) repetidas em N reviews viram chavão e perdem peso editorial.

**Padrões reais que precisam de tratamento especial:**

| Frase repetida em N produtos | Solução |
|---|---|
| "Gestantes, lactantes, hipertensos e cardíacos devem consultar profissional antes do consumo" (em 4 reviews idênticas) | Move pro `guideContent` (FAQ "faz mal à saúde"). NÃO repete no review individual |
| "Beta-alanina pode causar parestesia leve (formigamento na pele) nos primeiros minutos, efeito esperado e benigno" (em 8 bullets cons) | 1ª menção: explica completo. 2ª em diante: "mesma parestesia já descrita" ou só "formigamento leve" |
| "ativo que dá suporte à recuperação muscular" (sobre creatina ausente, em 5 cons) | Encurta pra "ativo importante pra recuperação" e varia léxico |
| "declarados pelo fabricante" colado a cada lista de mg | Drop quase sempre (info do rótulo já é por definição do fabricante) |

**Régua**: se uma frase específica aparece **literal em 3+ reviews do mesmo artigo**, é chavão. Encurta a partir da 2ª aparição.

### 9. Auto-check de tamanho final (régua v1.16.0)

**Antes de gravar o .mdx**, conta caracteres dos campos críticos (texto puro, descontando tags `<strong>`/`<a>`/`<em>`):

```
shortDescription: max 250 chars (texto puro — campo não tem HTML mesmo)
pros[i]: max 180 chars texto puro (cada item, descontando markup)
cons[i]: max 180 chars texto puro (cada item, descontando markup)
```

**Por que texto puro**: o HTML é estrutura (template de `<strong>Título</strong>: explicação`), não conteúdo. O leitor lê o texto, não o markup. Cota visual = palavras renderizadas, não bytes do arquivo.

**Como contar mentalmente**: olha o bullet sem `<strong>...</strong>` e sem `<a href="...">...</a>` (mas mantendo o texto entre as tags). Se o resultado passa de 180 chars = reescreve.

Mecânica: depois de gerar o review completo, antes do Edit tool, faz 1 passada de validação. Se algum item passa, **reescreve aquele item específico** (não o review inteiro). Custa 1 round-trip extra de modelo, mas evita gerar o problema do `melhorpretreino` (média bullets 175 chars vs canon 65).

**Por que importa**: bullets longos viram parágrafos. Parágrafos viram wall-of-text. Wall-of-text quebra escanabilidade — usuário não lê, vai pro próximo produto, pula a decisão.

### 10. Auto-check de concordância PT-BR (régua v1.19.0, canon 2026-05-28)

**Bug-class real** (batch melhorpretreino v1.17-1.18): substituições mecânicas (BCAAs→aminoácidos, parestesia→formigamento, fórmula→composição) **NÃO reconcordaram** plural/gênero/artigo. ChatGPT-Bárbara identificou 11+ casos novos só nos 2 artigos pré-treino.

**Padrões mais comuns + auto-check**:

```python
import re

# 10a) Plural errado em -ãos (em vez de -ões)
for m in re.finditer(r'\b(composição|combinação|porção|injeção|reação|opção|posição)s\b', campo):
    print(f"⚠ plural errado: {m.group(0)} → use -ões")
    # composiçãos → composições, combinaçãos → combinações

# 10b) Artigo errado antes de substantivo masculino (com "a/na/da/esta")
for m in re.finditer(r'\b(a|na|da|esta|nessa|nesta|essa) (produto|formigamento|ingrediente|ativo|estímulo|composto|atleta)\b', campo, re.IGNORECASE):
    print(f"⚠ artigo errado: {m.group(0)} → use 'o/no/do/este'")

# 10c) Artigo errado antes de substantivo feminino (com "o/no/do/este")
for m in re.finditer(r'\b(o|no|do|este|nesse|neste|esse) (fórmula|dose|porção|composição|combinação|tolerância)\b', campo, re.IGNORECASE):
    print(f"⚠ artigo errado: {m.group(0)} → use 'a/na/da/esta'")

# 10d) Concordância de adjetivo quebrada
for m in re.finditer(r'produto[s]? elaborada[s]?\b|produto ampla|formula natural', campo, re.IGNORECASE):
    print(f"⚠ concordância: {m.group(0)}")
    # "produto ampla" → "fórmula ampla"; "formula natural" → "fórmula natural"

# 10e) "no em 20XX" (sobra de substituição)
for m in re.finditer(r'\b(?:disponíveis?|disponível) no em \d{4}', campo, re.IGNORECASE):
    print(f"⚠ duplicação prep: {m.group(0)} → 'em 20XX'")

# 10f) "Pra a" / "no o" / sobras de contração
for m in re.finditer(r'\bPra a (maioria|minoria|primeira|melhor|pior)\b', campo):
    print(f"⚠ Pra a → Pra ou Para a")

# 10g) "as produtos" / "os fórmulas" — gênero errado
for m in re.finditer(r'\b(as produtos|os fórmulas|as ingredientes)\b', campo, re.IGNORECASE):
    print(f"⚠ gênero errado: {m.group(0)}")
```

**Casos reais** (commits 2026-05-28, melhorpretreino):
- 10a: `composiçãos` (11x), `combinaçãos` (4x) — devem ser composições/combinações
- 10b: `a produto` (4x), `a formigamento` (7x), `causa a formigamento` (2x)
- 10c: nenhum recente
- 10d: `produto ampla` (1x), `produtos elaboradas` (1x), `melhor formula natural` (1x)
- 10e: `disponíveis no em 2026` (1x)
- 10f: `Pra a maioria` (1x)
- 10g: `as produtos em geral` (1x)

Se achar qualquer bug: corrija ANTES de gravar. Skill atualmente faz isso mentalmente; tempo de re-check é trivial (~5s por campo).

### 11. Voz consultiva, não corporativa (régua v1.19.0, ChatGPT-Bárbara)

**Bug-class**: termos corporativos ("diferencial central", "posicionamento", "segmento", "proposta de valor") quebram voz especialista→amigo.

**Caps no JSON** (`_genericos.corporativo_max`):
- `categoria`: 15
- `diferencial central`: 2
- `diferencial principal`: 3
- `posicionamento`: 3
- `segmento`: 3
- `proposta de valor`: 0 (banido)

**Substituições editoriais**:
| ❌ Corporativo | ✓ Conversacional |
|---|---|
| "O diferencial central é a fórmula sem aditivos" | "O grande ponto é a fórmula sem aditivos" |
| "Posicionamento de mercado premium" | "Categoria premium" / "Linha mais cara" |
| "Atende ao segmento de emagrecimento" | "Funciona pra quem está emagrecendo" |
| "Proposta de valor única" | drop sempre — vazio retórico |
| "Categoria de pré-treinos sem cafeína" | "Os pré-treinos sem cafeína" |

### 12. Health absolutes YMYL banidos (régua v1.19.0, canon 2026-05-28)

**Bug-class** (ChatGPT ponto 7): absolutos de segurança/saúde violam diretrizes YMYL do Google ("Your Money Your Life") e expõem o site a penalização.

**Termos banidos absolutos** (limite 0):
- "uso regular é seguro"
- "alternativa segura" (sem qualificar contra o quê)
- "não causa dano"
- "totalmente seguro" / "100% seguro" / "sem riscos"
- "sem efeitos colaterais"
- "cientificamente comprovado" / "clinicamente comprovado" (sem citar estudo)

**Substituições**:
| ❌ Absoluto | ✓ Qualificado |
|---|---|
| "Uso regular é seguro" | "Tolerado em uso regular pela maioria; consulte um profissional se tem comorbidade" |
| "Alternativa segura ao X" | "Alternativa mais leve ao X" |
| "Não causa dano renal" | "Sem evidência de impacto renal em pessoas saudáveis em doses recomendadas" |
| "Sem efeitos colaterais" | "Efeitos colaterais raros e leves quando reportados" |
| "Cientificamente comprovado" | "Sustentado por evidências em estudos" (se houver na bíblia) |

**Auto-check**: grep dos termos exatos antes de gravar. Achou → reescreve qualificando.

### 13. Auto-check max 2 valores numéricos por frase (régua v1.19.0, canon 2026-05-28)

**Bug-class** (ChatGPT-Bárbara ponto 10): frases comparativas viram tabela em prosa quando listam 3+ valores em mg/g/R$.

**Limite duro**: máximo **2 valores numéricos por frase** em comparações cross-produto. Mais que isso → quebrar em 2 frases OU substituir por categoria ("entre os mais altos", "no piso da Anvisa").

**Auto-check**:
```python
import re
# Contar mg/g/R$ por frase
for frase in re.split(r'[.!?]\s+', campo):
    valores = re.findall(r'\d+[\.,]?\d*\s*(?:mg|g|R\$)', frase, re.IGNORECASE)
    if len(valores) > 2:
        print(f"⚠ {len(valores)} valores em 1 frase: {frase[:200]}")
```

**Exemplo real** (caso melhorpretreino emagrecer):
> ❌ "R$ 130 fica abaixo só do Essential Nutrition Beta Action (R$ 225) e acima do Dux Pre Workout (R$ 110), Vitafor V-Fort (R$ 95), Darkness Évora XT e Night Train (R$ 90 cada), 3VS Prohibido (R$ 80), Adaptogen Panic (R$ 78), Black Skull..."
> (8 preços em 1 frase = tabela em prosa)

> ✓ "Preço médio R$ 130, entre os 3 mais caros analisados. Abaixo só do Essential Nutrition Beta Action (R$ 225)."
> (2 valores na 1ª frase, 1 na 2ª = legível)

**Exceção canônica**: tabela específica de doses comparativa em **1 lugar único** do fullReview (ex: parágrafo dedicado a comparar cafeína entre 3 produtos) pode usar 3 valores SE houver gancho narrativo claro. Vale 1x por review, não como muleta.

### 14. Auto-check de capitalização + duplicação (régua v1.18.3, canon 2026-05-28)

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

### 15. Voz-eximir-responsabilidade (régua v1.19.1, canon 2026-05-28)

**Bug-class**: "declarado pelo fabricante", "X mg declarados", "todas declaradas" viram muleta epistêmica — o site se eximindo de afirmar diretamente. **91 ocorrências combinadas** nos 2 artigos pré-treino. Soa como se a redação não confiasse nos próprios dados.

**Princípio**: se o dado está na ficha técnica do produto, é por definição declarado pelo fabricante. Repetir "declarado" é redundância pura — e transfere responsabilidade desnecessariamente. Quando o número é fato verificável, afirme direto.

**3 sub-padrões proibidos** (regex no JSON `voz_eximir_responsabilidade`):

**15a) "X mg declarados" parentético** (redundância 100%):
| ❌ Antes | ✓ Depois |
|---|---|
| "dose mais alta de cafeína (400 mg declarados)" | "dose mais alta de cafeína (400 mg)" |
| "valina (550 mg) declarados, reforço pra recuperação" | "valina (550 mg), reforço pra recuperação" |
| "óxido nítrico declarada pelo fabricante, empata com Dux (2000 mg)" | "óxido nítrico de 2000 mg, empata com Dux" |

**15b) "declarado pelo fabricante" sobrando** (transfere responsabilidade):
| ❌ Antes | ✓ Depois |
|---|---|
| "restrição etária declarada pelo fabricante é 19 anos" | "restrição etária 19 anos" (ou drop, é regulação ANVISA) |
| "doses todas declaradas pelo fabricante" | "doses transparentes" / "fórmula totalmente declarada" |
| "todos declarados pelo fabricante" | "todos com mg específico" / drop |

**15c) Alérgeno com "declarado"** (regulação obrigatória, redundância):
| ❌ Antes | ✓ Depois |
|---|---|
| "A fórmula contém glúten declarado pelo fabricante" | "Contém glúten" / "Tem glúten na fórmula" |
| "Pode conter lactose conforme declaração" | "Pode conter traços de lactose" |
| "Sem mg declarada de creatina" | "Sem creatina específica na fórmula" / "Creatina embutida sem dose declarada" (se for o caso) |

**Exceção CANÔNICA** (não flag):
- ✅ "rende até 4.500 páginas em preto" — spec de fabricante (rendimento) afirmado direto; dropar "segundo a Epson" (muleta repetitiva, igual "declarado pelo fabricante")

**Régua mental antes de gravar**: se a frase tem `\d+ mg declarad` ou `declarad\w+ pelo fabricante` ou `(todas|todos|doses) declarad`, drop "declarad*" e veja se a frase ainda faz sentido. Se sim, era redundância — drop sempre.

### 16. Qualificadores de procedência redundantes (régua v1.19.2, canon 2026-05-29)

**Princípio**: quando um valor numérico concreto já está citado, qualificadores como "declarado", "informado", "detalhado", "especificado" são redundância pura — soam burocráticos e transferem responsabilidade desnecessariamente.

**Sub-padrões proibidos**:

| ❌ Antes | ✓ Depois |
|---|---|
| "1 g de leucina declarados" | "1 g de leucina" |
| "400 mg de cafeína declarados" | "400 mg de cafeína" |
| "aminoácidos essenciais declarados (1 g de leucina...)" | "aminoácidos essenciais (1 g de leucina...)" |
| "doses totalmente declaradas em mg" | "doses em mg" |
| "todos declarados em mg pelo fabricante" | "todos com mg específicas" |
| "transparência das doses" como elogio vago | citar as doses reais |
| "fórmula com doses detalhadas" | "fórmula com 9 ativos em mg específicos" |

**Exceção legítima**: quando descrevendo AUSÊNCIA de informação — "mg não consta no rótulo", "fabricante não detalha as mg". Nesses casos o qualificador informa algo útil (que a info não existe). "não declarado" / "não informado" são OK quando descrevem falta de dado real.

**Auto-check**: grep por `declarad`, `informado`, `detalhado`, `especificado` após número concreto (ex: `\d+\s*(?:mg|g|µg|ml)\s+(?:declarad|informad|detalhad|especificad)`). Se achar — drop o qualificador e releia a frase. Se ainda faz sentido, era redundância.

## Invocação

Exemplos válidos do user:
- "preenche o review da L3250 no artigo melhor-impressora-custo-beneficio do melhorimpressora"
- "preenche o produto B098YHFT9S no artigo X de Y"
- "preenche melhorimpressora/melhor-impressora-custo-beneficio B098YHFT9S"

Args canônicos que invoco:
- `Skill(skill="artigo-review-criar", args="melhorimpressora/melhor-impressora-custo-beneficio B098YHFT9S")`

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), validação fica editorial — eu sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial. Build do Astro é gate final.
