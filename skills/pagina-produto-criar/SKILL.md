---
name: pagina-produto-criar
description: Cria os 6 campos editoriais (subtitle, shortDescription, pros, cons, specs, fullReview) da página individual de produto a partir da bíblia. Aceita URL do painel (editor-produto.html?site=X&slug=Y) OU args canônicos site/slug. Stub precisa existir (criado no painel via "+ Nova página de produto"). Cria backup, commit, push, dispatch VPS pull.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida):
- `https://painel.melhorserum.com.br/editor-produto.html?site=melhorimpressora&slug=hp-laser-107w`
- Extrai `site` e `slug` do query string

**B) Args canônicos**:
- `melhorimpressora/hp-laser-107w` (formato `site/slug`)
- `melhorimpressora hp-laser-107w` (separado por espaço)

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B.

# Preencher página individual de produto

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:create_product_page`.
> O conteúdo essencial está duplicado abaixo pra autocontenção; em caso de divergência, o prompt canônico ganha.

Você é o curador editorial da página individual do produto. A página existe em `sites/{site}/src/content/products/{slug}.mdx`, criada como stub pelo endpoint `POST /product/:site/_actions/create-from-bible`. Sua função é **gerar os 6 campos editoriais** (subtitle, shortDescription, pros, cons, specs, fullReview) a partir da bíblia, com qualidade editorial alta e SEM duplicar conteúdo do produto-no-artigo (anti-duplicate-content SEO).

## Pré-requisitos

O `.mdx` da página já deve existir como **stub** com frontmatter mínimo (asin, name, image, imageAlt, category, categorySlug, publishDate). Se não existir, abortar com mensagem clara:

> "Página individual {slug} não existe ainda em {site}. Antes de preencher, crie o stub no painel: site detail → tabela 'Páginas de produto' → '+ Nova página de produto'."

## Invariantes

- **Nunca invente dados.** Tudo que você escrever precisa ter origem rastreável na bíblia (`pontosFortes`, `pontosFracos`, `angulosConversao`, `sentimentoCompradores`, `specsAmazon`, `doFabricante`, etc).
- **Conteúdo INDEPENDENTE do produto-no-artigo.** A página individual tem ângulo editorial próprio. Não copie/parafraseie do `fullReview` do review — usa estrutura, voz e ângulo diferentes (anti-duplicate-content). Se o produto aparece em algum review (campo `apareceNosArtigos` da bíblia ou via Grep nos `.mdx` de `sites/{site}/src/content/reviews/`), leia pra saber o que NÃO repetir.
- **Sem travessão (—).** Em nenhum campo. Use vírgula, ponto, parênteses ou dois pontos.
- **Sem superlativos absolutos** sem evidência ("o melhor", "o único", "incomparável").
- **Voz analítica.** NUNCA cite compradores/reviews/avaliações/estrelas (proibido pela voz editorial). Reescreva insights do `sentimentoCompradores` da bíblia como observação analítica direta.
- **HTML allowlist no `fullReview`.** Permitido: `<p>`, `<strong>`, `<em>`, `<a>`. **Proibido**: `<h2>`, `<h3>`, `<ul>`, `<ol>`, `<table>`, `<img>`, `<script>`, `<iframe>`, `<style>`.
- **Tag-aware nos links Amazon.** Se `siteConfig.affiliateTag` está preenchida, usar `?tag={tag}&linkCode=ogi&th=1&psc=1`. Se está vazia (`''`, estado de construção), usar **URL crua** sem `?tag=...`.
- **Não listar concorrentes.** É função do artigo comparativo, não da página individual.
- **Português brasileiro editorial.** Sem gírias, sem anglicismos desnecessários.

## Fluxo

1. **Parse args**: aceita formatos `{site}/{slug}` (canônico) ou nomes humanos. Exemplos válidos:
   - `melhorimpressora/epson-ecotank-l3250` ✓
   - `melhorimpressora epson-ecotank-l3250` ✓
   - `L3250 melhorimpressora` (descobrir slug via ASIN da bíblia + procurar em `sites/{site}/src/content/products/`)
   - `B098YHFT9S melhorimpressora` (idem)
   - Se ambíguo, perguntar antes de prosseguir.

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   git stash push -m "skill-pagina-produto-criar-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Painel VPS commita+pusha automaticamente quando user cria/edita conteúdo na UI; Mac local pode estar 5-30s atrás. Sem este pull, skill pode ler estado stale e abortar com falso "X não existe localmente". Caso real Bárbara 2026-05-24: ela criou site melhoromega3 + stub vitafor-omegafor-plus pelo painel VPS; sub-agent rodou git fetch (sem novidades), assumiu que site não existia. Pull antes evita esse falso-negativo.

2. **Read .mdx atual**: `Read sites/{site}/src/content/products/{slug}.mdx`. Se 404, abortar com mensagem do pré-requisito.

3. **Parsear frontmatter**: extrair `asin`, `name`, `image`, `imageAlt`, `category`, `categorySlug`. Validar que `asin` está no formato `[A-Z0-9]{10}`.

4. **Read bíblia**: `Read docs/biblias-v2/{asin}.json`. Se não existir, abortar (bíblia foi deletada após criação do stub — raro mas possível).

5. **Read affiliateTag do site**: `Read sites/{site}/src/config.ts` e extrair `affiliateTag` via regex `/affiliateTag:\s*['"]([^'"]*)['"]/`. Pode ser string vazia (`''`, construção) ou preenchida.

6. **Montar amazonUrl** baseado na tag:
   - Tag preenchida: `https://www.amazon.com.br/dp/{ASIN}?tag={TAG}&linkCode=ogi&th=1&psc=1`
   - Tag vazia: `https://www.amazon.com.br/dp/{ASIN}` (crua)

7. **Verificar se há reviews que citam o ASIN** (anti-duplicate): `Grep` por `asin:.*{ASIN}` em `sites/{site}/src/content/reviews/*.mdx`. Se houver, leia o `fullReview` daquele produto-no-artigo pra saber o ÂNGULO daquele texto — sua página individual tem que ter ângulo DIFERENTE.

8. **Gerar 6 campos** seguindo as regras detalhadas em "Os 6 campos" abaixo.

9. **Validar mentalmente** antes de salvar:
   - Tamanhos (limites editoriais abaixo)
   - HTML allowlist em fullReview
   - Sem travessão em nenhum campo
   - Tag correta nos links (ou ausente se config vazia)
   - Voz analítica (zero menção a compradores/reviews/avaliações)

10. **Backup**: copiar `.mdx` atual pra `docs/painel/.painel-backups/{YYYY-MM-DD}/product-{site}-{slug}-{HHMMSS}.mdx`. **Pattern idêntico ao painel** (ver `server.ts:5008`) — sem isso, backups da skill não aparecem no card "Histórico de versões" do editor-produto (que filtra por `product-{site}-{slug}-*`).

    ```bash
    DAY=$(date +%Y-%m-%d); TIME=$(date +%H%M%S); SITE={site}; SLUG={slug}
    mkdir -p "docs/painel/.painel-backups/$DAY"
    cp "sites/$SITE/src/content/products/$SLUG.mdx" "docs/painel/.painel-backups/$DAY/product-${SITE}-${SLUG}-${TIME}.mdx"
    ```

11. **Write `.mdx`**: monta o novo conteúdo:
    - **Frontmatter**: preserva todos os campos base existentes (asin, name, image, imageAlt, category, categorySlug, publishDate, contentLocked se existir). **Adiciona** os 6 campos editoriais (subtitle, shortDescription, pros, cons, specs, fullReview).
    - **Body**: remove o marker de stub (`{/* STUB GERADO POR ... [TODO: preencher] */}`). Body fica vazio ou com 1 linha em branco.

    Use YAML válido. Strings com aspas duplas (escape `\"` interno). Arrays multi-linha:
    ```yaml
    pros:
      - "Primeiro ponto positivo"
      - "Segundo ponto positivo"
    specs:
      - label: "Tela"
        value: "10.1 polegadas"
    ```

12. **Git add + commit + push** (auto, do diretório raiz do projeto):
    ```bash
    git add sites/{site}/src/content/products/{slug}.mdx
    git commit -m "feat({site}): preenche página individual {slug} via skill" \
      -m "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
    git push origin main
    ```

13. **Disparar git pull no painel da VPS** (propaga pro painel da Bárbara/produção):
    ```bash
    bash scripts/painel-vps-pull.sh
    ```
    Script usa Basic Auth do painel (creds em `.env.painel-skills` gitignored).
    Substituiu SSH direto pra funcionar tanto pro Marcelo quanto pra Bárbara
    (ela não tem SSH key na VPS). Se falhar (sem creds, painel offline),
    avisa mas não aborta — commit+push já aconteceu, painel só fica
    desatualizado até alguém puxar.

14. **Reportar no chat**: counts por campo + path do arquivo + status do push/pull. Mencionar se algum campo ficou no limite mínimo (sinaliza pra usuário revisar).

## Os 6 campos

### 1. `subtitle` (string, 10-150 chars)

Título descritivo curto, **sem redundância com o nome do produto**. Aparece como meta-info abaixo do H1.

Exemplos bons:
- Para "Epson EcoTank L3250": `"Multifuncional EcoTank com Wi-Fi, ideal para casa e home office"`
- Para "Kärcher VCL 2": `"Aspirador vertical 2 em 1 com filtro HEPA"`

Exemplos ruins:
- ❌ `"Epson EcoTank L3250"` (redundante com o nome)
- ❌ `"Impressora"` (genérico demais, < 10 chars)

### 2. `shortDescription` (string, 40-800 chars)

1-2 frases que aparecem no hero, abaixo do nome. Resumo do produto + ângulo principal.

Exemplo: `"Impressora EcoTank com tanque de tinta recarregável, custo por página baixo e impressão duplex automática. Indicada para uso doméstico ou escritório pequeno com volume médio de impressão."`

### 3. `pros` (array de strings, 3-8 itens, cada 8-300 chars)

Formato: `<strong>Título</strong>: explicação`. A explicação **SEMPRE com dado concreto**, nunca genérico. Paridade com prompts de artigo (`formato_pros_cons_specs` shared).

Exemplos bons:
- ✓ `"<strong>Rendimento elevado</strong>: 4.500 páginas em preto por kit T544 segundo o fabricante."`
- ✓ `"<strong>MicroPiezo Heat-Free</strong>: não aquece a tinta no processo, com consumo de cerca de 12W em operação."`

Errados:
- ❌ `"<strong>Rendimento alto</strong>: a impressora rende muito"` (sem dado)
- ❌ `"Sistema EcoTank com rendimento de até <strong>4.500 páginas</strong>..."` (strong inline em vez de Título: explicação — esse era o padrão antigo, NÃO usar)
- ❌ `"Melhor opção do mercado"` (superlativo sem evidência)
- ❌ `"Mais barata que a HP Smart Tank 581"` (comparação com concorrente — função do artigo)

### 4. `cons` (array de strings, 1-5 itens, cada 8-300 chars)

Mesma formatação dos pros: `<strong>Título</strong>: explicação`. Pontos de atenção, trade-offs, contextos onde NÃO comprar. Se a bíblia tem `pontosFracos` populados, use como ponto de partida.

Exemplo: `"<strong>Duplex manual</strong>: imprimir frente e verso exige virar o papel à mão, sem mecanismo automático."`

### 5. `specs` (array de objetos, 3-10 pares label/value)

Specs técnicas relevantes derivadas da bíblia (`specsAmazon`, `doFabricante`, `conteudoBrutoFabricante`). Label e value são **strings simples** (sem HTML).

```yaml
specs:
  - label: "Tipo"
    value: "Tanque de tinta (EcoTank)"
  - label: "Velocidade"
    value: "Até 10 ppm em preto"
  - label: "Conectividade"
    value: "Wi-Fi, USB"
  - label: "Funções"
    value: "Imprime, copia, digitaliza"
```

### 6. `fullReview` (string HTML, 300-3000 chars)

**Estrutura obrigatória — 4 parágrafos marcados, paridade com `formato_full_review` dos prompts de artigo**:

```html
<p><strong>Para quem é:</strong> perfil de uso, ambiente, tipo de comprador. Inclua 1 link Amazon no nome do produto neste parágrafo.</p>

<p><strong>Por que gostamos:</strong> features-chave com dados concretos. Inclua 1 link Amazon na primeira menção do produto. Se houver muito o que cobrir (>5-6 frases), divida em 2 parágrafos: primeiro features-chave, segundo specs gerais (peso, dimensões, conectividade, garantia).</p>

<p><strong>Pontos de atenção:</strong> trade-offs reais, limitações, contextos onde NÃO comprar. SEM link de afiliado neste parágrafo (não tenta vender no parágrafo de objeções).</p>

<p><strong>Resumo:</strong> fechamento conciso. Inclua 1 link Amazon na última menção do produto.</p>
```

**Total: 3 links de afiliado** no fullReview, nas posições preferidas (Para quem é / Por que gostamos / Resumo).

**Formato dos links**:
```html
<a href="{amazonUrl}" rel="nofollow" target="_blank">Nome do Produto</a>
```
(Use o `amazonUrl` do contexto — crua quando affiliateTag vazia, com tag quando preenchida.)

**Tags HTML permitidas**: `<p>`, `<strong>`, `<em>`, `<a>`.

**Proibido**:
- `<h2>` ou `<h3>` (quebra hierarquia)
- `<ul>`/`<ol>`/`<li>` (use parágrafos)
- `<table>` (specs têm seção própria)
- `<img>` (imagem do produto vem do hero)

**Densidade de números**: 5-7 dados quantitativos da bíblia ao longo dos 4 parágrafos. Sem injetar números só por densidade.

## Restrições específicas da página individual (CRÍTICO)

O fullReview e os pros/cons **NÃO PODEM** ter:

**Comparações com concorrentes pelo nome**:
- ❌ `"vs HP Smart Tank 581"`
- ❌ `"comparada à Canon Pixma"`

**Comparações implícitas vagas que pressupõem lista**:
- ❌ `"uma das mais econômicas do mercado"` (mercado não foi auditado pra dizer isso)
- ❌ `"entre as melhores"` (não houve seleção comparativa)
- ❌ `"mais X que tradicionalmente se vê"` (especulação)

**Referências à lista/artigo**:
- ❌ `"nesta seleção"`
- ❌ `"neste artigo"`
- ❌ `"diferente do produto anterior"`
- ❌ `"comparado ao primeiro da lista"`

**Termos que pressupõem comparação não-feita**:
- ❌ `"a melhor opção"` (sem dado)
- ❌ `"incomparável"`

**Permitido** (não é comparação, é análise):
- ✓ `"oferece X em Y"`
- ✓ `"sistema sem cartuchos rende Z páginas"`
- ✓ `"consumo de 12W em operação"`

A razão: leitor pode ter chegado direto via Google sem passar por nenhum artigo. **Texto se sustenta sozinho.**

## Voz editorial (CRÍTICO)

Os reviews têm voz de **quem testou/analisou** o produto. Tom: "nós identificamos / a impressora entrega / o produto tem".

**NUNCA** cite compradores, opiniões, Amazon, avaliações, reviews, estrelas. Frases proibidas:
- ❌ "Compradores recorrentemente citam..."
- ❌ "Um comprador relata..."
- ❌ "Bem avaliada por usuários"
- ❌ "Conforme reviews na Amazon"

**Reescreva** insights da bíblia em voz analítica:
- ✓ "O custo-benefício se destaca: {dado concreto}"
- ✓ "Um trade-off identificado é..."
- ✓ "O equipamento entrega {feature} em {condição}"

## Como usar a bíblia

- `pontosFortes` / `pontosFracos`: base dos pros/cons. NÃO invente.
- `angulosConversao`: ângulos editoriais. Use pra estruturar parágrafos do `fullReview` ("para quem é", "por que gostamos").
- `sentimentoCompradores`: insights — **REESCREVA** como observação editorial, NÃO cite compradores. Ex: "compradores citam custo-benefício" → "O custo-benefício se destaca por {dado da bíblia}".
- `dicasAcionaveis`: incorpore se fizer sentido no `fullReview` ou como item em `cons` (quando for limitação contextual).
- `dadosInconsistentes` + `decisaoEditorial`: SE existir, **RESPEITE**. A decisão editorial diz qual valor usar e qual ignorar.
- `observacoesAgente`: notas internas pra você. Leia.
- `specsAmazon` + `doFabricante` + `conteudoBrutoFabricante`: fontes pra `specs` e claims numéricos no `fullReview`.

## Filtros editoriais

**NÃO inclua em NENHUM dos 6 campos** (mesmo se aparecer na bíblia):

- **Specs ambientais**: % plástico reciclado, certificações eco (Energy Star, EPEAT, RoHS, FSC), programas de devolução tipo "HP Planet Partners", neutralidade de carbono. Irrelevante pra decisão do comprador típico.
- **Origem de fabricação**: "fabricado no Brasil", "made in X", "produto nacional". Idem.

**Exceção**: se a bíblia tem em `angulosConversao` um tema explícito como `sustentabilidade` ou `produto-nacional` marcado como diferencial central, pode tratar com licença editorial. Sem ângulo registrado = ignore mesmo se aparecer em `sobreEsteItem`/`doFabricante`.

## Restrições finais

- Densidade de números concretos: 5-7 dados quantitativos da bíblia ao longo dos 6 campos. Não injete números só por densidade.
- Parágrafos não passam de ~5-6 frases.
- Sem travessão (—). Vírgula ou ponto.
- Sem superlativos sem evidência ('o melhor', 'incomparável').
- Cada claim → origem rastreável na bíblia.

## Armadilhas recorrentes — evitar sempre

### 1. Duplicate content com o produto-no-artigo

Se a página individual repete o `fullReview` do artigo, o SEO penaliza. Antes de gerar, leia o `productPageReview` ou `fullReview` do produto no review (campo `apareceNosArtigos` da bíblia ajuda a localizar). Se ainda não há review citando o ASIN, ângulo é livre.

### 2. HTML proibido por hábito

Eu (modelo) tenho hábito de usar `<ul>` pra listas. **Não use** em `fullReview`. Forme bullets com parágrafos curtos, ou junte numa frase com vírgulas.

Errado:
```html
<p>Principais features:<ul><li>Wi-Fi</li><li>Duplex</li></ul></p>
```

Certo:
```html
<p>As principais features são <strong>Wi-Fi</strong>, impressão duplex automática e tanque de tinta recarregável.</p>
```

### 3. Tag em config vazio mas IA gera link com tag

Se `affiliateTag === ''`, sua `amazonUrl` é crua (`https://www.amazon.com.br/dp/{ASIN}`). Não invente uma tag genérica tipo "amzn20" ou copie de outro site — link sai cru e ponto. Quando o site for live, script futuro vai injetar a tag real.

### 4. Voz comprador escapando

Especialmente fácil de cair em `pros`. Frase como "Compradores destacam a velocidade" precisa virar "A velocidade de até 10 ppm em preto se destaca no uso diário".

### 5. Inventar specs

Se a bíblia diz "velocidade até 10 ppm" e você escrever "velocidade até 12 ppm" porque "soa melhor", é invenção. Cada número em `specs` ou `fullReview` deve casar exatamente com o que está na bíblia.

### 6. Comparar com concorrentes

Página individual é sobre o produto **sozinho**. Comparações vão no artigo. Frases como "mais rápida que a HP Smart Tank" são proibidas aqui (mesmo que verdadeiras).

### 7. Voz de citação ("segundo X", "datasheet Y") — viola diretrizes #1, #5 e #6

**Armadilha mais comum e fácil de cair.** Quando os dados da bíblia vêm de várias fontes (specsAmazon, doFabricante, conteudoBrutoFabricante, datasheet HP), o modelo tende a citar a fonte pra justificar o claim: "segundo a HP", "conforme datasheet", "o anúncio Amazon lista".

**A diretriz #5 da bíblia proíbe isso explicitamente**: *"Proibido dizer 'na ficha técnica', 'segundo as especificações' ou variantes: o review não pode parecer leitura de planilha."*
A #6 reforça: *"Integre os dados no texto como quem conhece o produto: não cite specs em bloco, costure no raciocínio."*

**Padrões proibidos** (caso real B0C1L2R4HH gerou 16 ocorrências numa única passada):
- "segundo a HP" / "conforme a HP" / "conforme o fabricante"
- "datasheet HP" / "datasheet técnico" / "no datasheet"
- "anúncio Amazon" / "apesar do anúncio Amazon listar"
- "pico de marketing" / "número de marketing"
- "métrica ISO (padrão da indústria)" / "padrão da indústria"
- "na recomendação do fabricante" / "faixa recomendada pela HP"

**Reformulação correta** — afirmar como conhecimento próprio:

| ❌ Citação | ✓ Análise própria |
|---|---|
| "rende até 12.000 páginas, **segundo a HP**" | "o kit rende até 12.000 páginas" |
| "**a métrica ISO (padrão da indústria) fica em** 12 ppm" | "no uso normal entrega 12 ppm" |
| "**o pico de marketing é** 30 ppm em rascunho" | "pico de 30 ppm em rascunho rápido quando o tempo aperta mais que a qualidade" |
| "**apesar do anúncio Amazon listar** duplex automático, **o datasheet HP descreve** manual" | "a impressão frente e verso é manual" *(toma o lado correto, ignora conflito interno)* |
| "volume mensal recomendado **pela HP**" | "volume mensal confortável" *(descrição editorial nossa)* |
| "cabo separadamente, **conforme a HP**" | "cabo separadamente" *(afirmação direta)* |

**Tratamento de divergências internas** (dadosInconsistentes): a `decisaoEditorial` da bíblia já diz qual lado tomar. Aplica direto, sem mencionar o conflito (ex: duplex Amazon-diz-Auto vs HP-diz-Manual → escolhe Manual e afirma; o leitor não precisa saber da contradição interna, é problema nosso).

**Quando referenciar "HP" é OK**: quando "HP" é parte do contexto factual real, não citação de autoridade. Exemplos:
- ✓ "cadastro no site da HP em até 60 dias" *(site da HP é informação prática)*
- ✓ "app HP Smart centraliza configuração" *(nome do app)*
- ❌ "rende 12.000 páginas segundo a HP" *(HP como fonte de autoridade pro número)*

**Antes de gravar, faça grep mental**: se aparece "segundo X", "conforme Y", "datasheet Z", "anúncio W", reescreva.

## Limpeza do stub

O endpoint `create-from-bible` deixa esse marker no body do `.mdx`:

```
{/* STUB GERADO POR scripts/scaffold-product-mdx ou painel — abra o editor-produto e clique "✨ Criar com IA" pra gerar os 6 campos editoriais (subtitle, shortDescription, pros, cons, specs, fullReview). [TODO: preencher] */}
```

**Remover ao escrever**. O body pode ficar vazio (só os 6 campos no frontmatter já populam a página via SlugPage). Se quiser, deixe 1 linha em branco depois do `---`.

## Sincronização painel ↔ skill ↔ prompt canônico

```
docs/painel/_data/agent-prompts.json  (SOURCE OF TRUTH editorial)
    ├── ops.create_product_page (handler do painel usa)
    └── ops.audit_product_page  (handler do painel usa)

.claude/skills/preencher-pagina-produto/SKILL.md  → segue
.claude/skills/auditar-pagina-produto/SKILL.md    → segue
```

Quando Marcelo edita regras editoriais (via `agent-config.html` no painel):
- Atualiza `agent-prompts.json` (canônico)
- Esta SKILL.md pode ficar atrasada — atualizar manualmente quando notar drift

## Exemplo de invocação

```
preenche a página individual da L3250 no melhorimpressora
preenche o produto epson-ecotank-l3250 do melhorimpressora
preenche melhorimpressora/epson-ecotank-l3250
preenche B098YHFT9S no melhorimpressora
```

Args canônico que invoco: `Skill(skill="preencher-pagina-produto", args="melhorimpressora/epson-ecotank-l3250")`.

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), a validação fica editorial — eu (modelo) sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial (subtitle de 9 chars, fullReview de 290 chars, etc).

Mitigação: depois de gerar, conferir tamanhos antes de salvar. Se algum estiver no limite, expandir/encurtar com cuidado.
