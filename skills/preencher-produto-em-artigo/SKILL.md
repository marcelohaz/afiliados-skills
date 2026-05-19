---
name: preencher-produto-em-artigo
description: Preenche o conteúdo editorial de UM produto dentro de um artigo (sites/{site}/src/content/reviews/{slug}.mdx) e opcionalmente os campos top-level do artigo (title, description, excerpt, keywordPlural, listHeading) quando estão vazios. Equivalente ao botão "🪄 Regenerar produto" do editor-artigo + parte do que o make-reviews/add-products do painel faria, mas roda aqui pra economizar ANTHROPIC_API_KEY (~$0.05-0.10/produto). Granularidade per-produto: você revisa um, ajusta, segue pro próximo.
---

# Preencher review de um produto dentro de um artigo

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:rewrite_product` + (quando o artigo é stub) `make_reviews` pros campos top-level. O conteúdo essencial está duplicado abaixo; em caso de divergência, o prompt canônico ganha.

Você é o curador editorial que escreve o conteúdo do produto-no-artigo. O artigo existe como stub criado pelo endpoint `make-reviews-stub` ou `add-products-stub` do painel. Sua função é **preencher os 6 campos editoriais de um produto específico** seguindo a régua do `formato_full_review` (4 parágrafos marcados, comparativo), e quando o artigo é stub, **também os campos top-level** (title, description, excerpt, keywordPlural, listHeading, specLabels).

## Pré-requisitos

O `.mdx` do artigo já existe em `sites/{site}/src/content/reviews/{slug}.mdx` com lineup de produtos (criado pelo make-reviews-stub) ou recém-adicionado (add-products-stub). Se não existir, abortar com mensagem clara apontando o botão "✨ Criar artigo" no site detail.

A bíblia do ASIN está OK e a página individual existe (verificado pelo gate Fase 2 quando o stub foi criado).

## Invariantes

- **Nunca invente.** Cada claim numérico tem origem rastreável na bíblia (`specsAmazon`, `doFabricante`, `pontosFortes`, etc).
- **Conteúdo COMPARATIVO** (diferente da página individual): pode comparar com outros produtos do lineup, citar por nome, dizer "vs HP X" se houver dado na bíblia. Pode falar "nesta seleção", "comparado ao primeiro da lista".
- **Anti-duplicate vs página individual**: leia o `productPageReview` da página individual antes (`sites/{site}/src/content/products/{slug-do-produto}.mdx` → campo `fullReview`). O texto do produto-no-artigo deve ter ângulo DIFERENTE — comparativo, posicionamento na seleção, etc.
- **Sem travessão (—)** em nenhum campo.
- **Voz analítica**: NUNCA cite compradores/reviews/avaliações/estrelas/Amazon.
- **HTML allowlist no `fullReview`**: `<p>`, `<strong>`, `<em>`, `<a>`. Proibido: `<h2>`, `<h3>`, `<ul>`, `<ol>`, `<table>`, `<img>`, `<script>`.
- **Tag-aware**: leia `siteConfig.affiliateTag`. Vazia (sites em construção) → URL crua `https://www.amazon.com.br/dp/{ASIN}`. Preenchida → `?tag={tag}&linkCode=ogi&th=1&psc=1`.
- **Português brasileiro editorial** sem gírias.

## Fluxo

1. **Parse args**: aceita `{site}/{slug-do-artigo} {ASIN-ou-slug-do-produto}` ou variantes humanas. Eu (Claude) interpreto e formato args canônicos antes.

2. **Read artigo**: `Read sites/{site}/src/content/reviews/{slug}.mdx`. Se 404, abortar.

3. **Localizar o produto** no `products[]` do frontmatter pelo ASIN. Se não encontrado, abortar com mensagem "Produto X não está no lineup do artigo; use '+ Adicionar produto' antes".

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

- **shortDescription** (50-800 chars): 1-2 frases que resumem o produto pra TabelaProdutos e TopPickCard.

9. **Validar mentalmente** antes de salvar:
   - Tamanhos dentro dos ranges
   - HTML allowlist OK no fullReview
   - Sem travessão
   - Tag correta nos links (ou cruas se config vazia)
   - Voz analítica (zero "compradores", "reviews", "avaliações")
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

### shortDescription (50-800 chars)
1-2 frases que resumem o produto. Aparece na TabelaProdutos e no TopPickCard. Ex: "Multifuncional 3 em 1 com tanque de tinta, Wi-Fi Direct e rendimento de até 4.500 páginas em preto por kit. Indicada para uso doméstico ou escritório pequeno com volume médio."

### fullReview (HTML, ~800-3000 chars)
**Estrutura obrigatória — 4 parágrafos marcados** (idêntico ao `formato_full_review` shared):

```html
<p><strong>Para quem é:</strong> ... <a href="{amazonUrl}">{nome}</a> ...</p>
<p><strong>Por que gostamos:</strong> ... <a href="{amazonUrl}">{nome ou variante}</a> ...</p>
<p><strong>Pontos de atenção:</strong> ...</p>
<p><strong>Resumo:</strong> ... <a href="{amazonUrl}">{nome}</a> ...</p>
```

**Ângulo COMPARATIVO** (diferente da página individual que é autônoma):
- Pode mencionar "nesta seleção", "entre os modelos analisados"
- Pode comparar com outros produtos do lineup pelo nome
- Pode dizer "diferente do produto anterior" se houver fluxo narrativo

### pros (3-8 itens)
`<strong>Título</strong>: explicação com dado concreto`. Sempre dado verificável.

### cons (1-5 itens)
Mesma formatação dos pros. Trade-offs reais.

### specs (3-10 pares label/value)
Specs técnicas derivadas de `specsAmazon`/`doFabricante`/`conteudoBrutoFabricante`. Strings simples. Reuso labels do lineup quando possível.

## Voz editorial

Idêntica à da página individual (mesma régua):
- Tom de quem testou/analisou
- NUNCA cite compradores, reviews, avaliações, estrelas, Amazon como entidade
- Reescreva insights de `sentimentoCompradores` como observação editorial direta

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
| "A L3250 é uma multifuncional pensada para uso doméstico" | "Na seleção, a L3250 cobre o perfil doméstico" |
| "O diferencial central é o sistema EcoTank" | "Comparada às outras impressoras desta lista, a L3250 destaca-se pelo sistema EcoTank" |

## Armadilhas recorrentes

### 1. Repetir frase exata da página individual
Confere antes de salvar. Se uma frase específica está na página individual, reescreva.

### 2. HTML proibido por hábito
`<ul>` é tentador pra listar features. Use parágrafos.

### 3. Comparações sem dado
"Uma das mais econômicas" sem `concorrentes` na bíblia é especulação. Use linguagem absoluta com dado: "rende 4.500 páginas por kit" em vez de "rende mais que a maioria".

### 4. Misturar voz comprador
"Compradores destacam X" → "X destaca-se por {dado da bíblia}".

### 5. Atualizar campos top-level quando não-stub
Se o artigo já tem `title`, `description`, `excerpt` populados, NÃO sobrescreva (preserva trabalho do user). Só preenche se estão vazios.

### 6. Block scalar `|` no fullReview
Se reusar a abordagem yaml.parseYaml + stringify, fullReview pode mudar de `|` pra string quoted, bagunçando HTML. Recomendado: edição cirúrgica com Edit tool no trecho do produto-alvo, preservando o resto do arquivo intacto.

## Invocação

Exemplos válidos do user:
- "preenche o review da L3250 no artigo melhor-impressora-custo-beneficio do melhorimpressora"
- "preenche o produto B098YHFT9S no artigo X de Y"
- "preenche melhorimpressora/melhor-impressora-custo-beneficio B098YHFT9S"

Args canônicos que invoco:
- `Skill(skill="preencher-produto-em-artigo", args="melhorimpressora/melhor-impressora-custo-beneficio B098YHFT9S")`

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), validação fica editorial — eu sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial. Build do Astro é gate final.
