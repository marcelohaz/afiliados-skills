---
name: artigo-review-criar
description: Cria o review editorial de UM produto dentro de um artigo comparativo. Aceita URL do painel (editor-artigo.html?site=X&slug=Y) — detecta stubs vazios na lista de produtos e pergunta qual preencher, 1 por vez (controle de qualidade) — OU args canônicos site/slug-artigo + ASIN. Régua v1.17.0 (2026-05-28) — shortDescription PADRÃO BENEFÍCIO-FIRST (posicionamento/benefício na 1ª frase, técnico justifica depois; 3 moldes A/B/C; drop marca+preço+público verboso), hard caps de tamanho (shortDescription ≤250 chars, pros/cons ≤180 chars cada), ban total de "lineup"/"desta seleção" no output editorial, anti-listagem-exaustiva de peers, anti-repetição de frases-padrão. Cria backup, commit, push, dispatch VPS pull.
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

Você é o curador editorial que escreve o conteúdo do produto-no-artigo. O artigo existe como stub criado pelo endpoint `make-reviews-stub` ou `add-products-stub` do painel. Sua função é **preencher os 6 campos editoriais de um produto específico** seguindo a régua do `formato_full_review` (4 parágrafos marcados, comparativo), e quando o artigo é stub, **também os campos top-level** (title, description, excerpt, keywordPlural, listHeading, specLabels).

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

7. **Detectar se o artigo é stub** (`title`/`description`/`excerpt` vazios): se sim, gerar também os campos top-level (passo 8a). Se não, só os campos do produto (passo 8b).

8a. **Gerar campos top-level do artigo** (só se stub):
   - `title`: 30-100 chars. Formato: keyword capitalizado + ":" (o resto user completa). Ex: keyword "melhor impressora custo benefício" → title "Melhor Impressora Custo Benefício:"
   - `description`: 50-160 chars, meta-description SEO
   - `keywordPlural`: forma plural do keyword pro H2 "Comparativo técnico dos {keywordPlural}". Ex: "melhores impressoras custo benefício"
   - `listHeading`: 10-200 chars. H2 que abre a tabela. Ex: "Quais são as melhores impressoras custo benefício?"
   - `excerpt`: 50-300 chars. Teaser do topo
   - `specLabels`: array de 3-10 labels (intersecção dos specs.label dos produtos no lineup). Pra primeiro produto, deriva direto. Pra produtos adicionados depois, deixa como está e atualiza só se o novo produto tiver labels diferentes.

8b. **Gerar os 6 campos editoriais do produto** seguindo a régua do `formato_full_review` (4 parágrafos marcados):

```html
<p><strong>Para quem é:</strong> perfil de uso. Inclua 1 link Amazon no nome do produto.</p>
<p><strong>Por que gostamos:</strong> features-chave com dados concretos. Inclua 1 link Amazon na primeira menção. Pode dividir em 2 parágrafos se >5-6 frases (primeiro features-chave, segundo specs gerais).</p>
<p><strong>Pontos de atenção:</strong> trade-offs, limitações. SEM link de afiliado neste parágrafo.</p>
<p><strong>Resumo:</strong> fechamento conciso. Inclua 1 link Amazon na última menção.</p>
```

- **3 links de afiliado** total (Para quem é + Por que gostamos + Resumo). SEM link em "Pontos de atenção".
- Formato dos links: `<a href="{amazonUrl}" rel="nofollow" target="_blank">Nome do Produto</a>` onde `amazonUrl` é crua quando tag vazia, com tag quando preenchida.

- **pros** (3-8 itens): formato `<strong>Título</strong>: explicação com dado concreto`.
  - ✓ "<strong>Rendimento elevado</strong>: 4.500 páginas em preto por kit T544 segundo o fabricante"
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
   - Voz-citação ficha-técnica (zero "alérgenos confirmam", "atributos declaram", "conforme tipo de dieta", "apontada pelo fabricante como") — exceção: claim só-fabricante que adiciona valor editorial, ver Armadilha 4
   - Anti-duplicate vs página individual (frases não-repetidas)

10. **Backup**: `docs/painel/.painel-backups/{YYYY-MM-DD}/article-{site}-{slug}-{HHMMSS}-prod-{ASIN}.mdx`. Pattern paralelo ao do painel pra aparecer no card "Histórico de versões".

11. **Write `.mdx`**: usa parseYaml + stringifyYaml lib pra reconstruir, OU editar cirurgicamente o trecho do produto-alvo. Cuidado pra:
    - Preservar produtos não-alvo intactos (não tocar)
    - Preservar `fullReview` block scalar (`|`) — re-parsear+stringificar pode bagunçar HTML multi-linha. Recomendo edição cirúrgica via Edit tool quando possível.
    - Atualizar campos top-level só se foram detectados como stub

12. **Git add + commit + push**:
    ```bash
    git add sites/{site}/src/content/reviews/{slug}.mdx
    git commit -m "feat({site}): preenche review de {ASIN} em {slug} via skill" \
      -m "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
    git push origin main
    ```

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

**Banidas no output editorial** (régua v1.16.0, canon 2026-05-28):
- ❌ "lineup" — palavra puramente interna, jamais aparece em texto público
- ❌ "desta seleção" / "do lineup" / "do nosso lineup" / "do nosso comparativo" como muleta repetida
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

> **Sobre citar o fabricante**: regra diferente. Citar fabricante pode ser editorial OK em casos específicos (rendimento, garantia interna, certificação proprietária). Ver Armadilha 4 abaixo pra régua completa.

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

## Operação de destilação bíblia → .mdx (CRÍTICO)

A bíblia carrega claims COM marcadores de procedência (`fonte: "specs"`, "conforme declarado pelo fabricante", "confirmado nos alérgenos"). É correto e útil internamente — rastreabilidade evita invenção. **O .mdx público é destilado**: droppa marcadores que viraram ruído burocrático.

**4 categorias de claim — como destilar cada:**

| Tipo | Bíblia (raw, OK) | .mdx destilado |
|---|---|---|
| **A) Fato verificável simples** | "Sem glúten confirmado nos alérgenos da Amazon" | "Sem glúten" |
| **B) Claim do fabricante repetível** | "Forma triglicerídeo, apontada pelo fabricante como mais absorvível" | "Forma triglicerídeo, considerada mais absorvível" |
| **C) Claim institucional / PR** | "Marca tradicional brasileira segundo o próprio fabricante" | "Marca brasileira" (ou omite se não agrega) |
| **D) Voz comprador implícita** | "Cápsulas sem sabor segundo relatos de compradores" | "Cápsulas sem sabor" |

**Exceção (raro, mas existe)**: claim do fabricante VERIFICÁVEL SÓ por ele (rendimento, garantia interna, certificação proprietária) pode manter "segundo X" se adiciona valor editorial — ver Armadilha 4 abaixo.

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
1. **(a)** qualifica claim que SÓ o fabricante pode fazer (rendimento, garantia interna, certificação proprietária)
2. **(b)** adiciona valor editorial ao leitor (calibra expectativa, sinaliza honestidade, faz crítica)

**✓ EDITORIAL OK** (referência: `sites/melhorimpressora/src/content/products/epson-ecotank-l3250.mdx`):
- "rende até 4.500 páginas em preto, **segundo a Epson**" → claim só-fabricante + qualifica rendimento
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

## Invocação

Exemplos válidos do user:
- "preenche o review da L3250 no artigo melhor-impressora-custo-beneficio do melhorimpressora"
- "preenche o produto B098YHFT9S no artigo X de Y"
- "preenche melhorimpressora/melhor-impressora-custo-beneficio B098YHFT9S"

Args canônicos que invoco:
- `Skill(skill="artigo-review-criar", args="melhorimpressora/melhor-impressora-custo-beneficio B098YHFT9S")`

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), validação fica editorial — eu sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial. Build do Astro é gate final.
