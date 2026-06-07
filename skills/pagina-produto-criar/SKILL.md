---
name: pagina-produto-criar
description: Cria os 6 campos editoriais (subtitle, shortDescription, pros, cons, specs, fullReview) da página individual de produto a partir da bíblia. Aceita URL do painel (editor-produto.html?site=X&slug=Y) OU args canônicos `site/slug`. Stub precisa existir (criado no painel via "+ Nova página de produto"). Carrega chavões nicho-específicos de `docs/painel/_data/chavoes-por-nicho.json`. Aplica régua editorial: concordância PT-BR, ban "declarado pelo fabricante" como muleta, health absolutes YMYL, hard caps de tamanho (shortDescription ≤250, pros/cons ≤180 texto puro), shortDescription benefício-first, voz consultiva. Cria backup, commit, push, dispatch VPS pull.
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

- **DESTILAÇÃO CATEGORIA D (operação OBRIGATÓRIA pra cada claim da bíblia)**.
  Bíblia frequentemente traz claim com voz-comprador IMPLÍCITA dentro de
  `pontosFortes` / `pontosFracos`. Exemplos reais que sub-agents do Opus
  já caíram em armadilha (caso 2026-05-26, batch melhorpretreino):

  - Bíblia → "Sabor maçã verde divide opiniões nos reviews"
    - ❌ "Sabor divide: opiniões sobre o sabor são mistas" (voz-comprador literal)
    - ✅ "Sabor maçã verde é frutado, pode não agradar quem prefere perfis mais neutros"
  - Bíblia → "Um comprador relata que a fórmula não causou parestesia"
    - ❌ "Um comprador relata que não há formigamento" (voz-comprador)
    - ✅ "A fórmula em uso normal não induz formigamento marcante"
  - Bíblia → "Sabor elogiado de forma recorrente nas opiniões disponíveis"
    - ❌ "Bem avaliado pelos compradores"
    - ✅ "Sabor jabuticaba com romã, perfil cítrico-frutado"

  **AUTO-CHECK final antes de escrever**: se ALGUM campo do `.mdx` final contém "opiniões", "comentários", "um comprador", "elogios", "recepção", "avaliações", "reviews", "divide opiniões", "bem recebido [pelos/nos]" — está ERRADO. Reescreva como observação ANALÍTICA OBJETIVA.

- **Termos técnico-industriais proibidos** (régua específica do projeto): "contaminação cruzada", "linha de produção compartilhada" (sem contexto editorial). Não agregam ao leitor final; soam como ficha técnica. Para alérgenos, usar linguagem editorial:
  - ❌ "Risco de contaminação cruzada na linha de produção"
  - ✅ "Pode conter traços de leite — alérgicos severos devem ler a rotulagem antes do uso"
- **HTML allowlist no `fullReview`.** Permitido: `<p>`, `<strong>`, `<em>`, `<a>`. **Proibido**: `<h2>`, `<h3>`, `<ul>`, `<ol>`, `<table>`, `<img>`, `<script>`, `<iframe>`, `<style>`.

- **CAMPOS TEXTO-PURO — sem HTML inline.** A allowlist HTML acima é EXCLUSIVA do `fullReview`. Os demais campos editoriais são texto puro renderizado por Astro com `{var}` (escape automático XSS):
  - `subtitle`: texto puro (o template já envolve em `<strong class="pp-hero__subtitle">`, então `<strong>` literal aqui aninharia ou vazaria como texto)
  - `shortDescription`: texto puro (renderizado em `<p class="pp-hero__desc">{var}</p>` — qualquer `<strong>` vira `&lt;strong&gt;` no HTML, exibido como texto literal pro usuário)
  - `specs[].value`: strings simples (já documentado abaixo)
  - `pros[N]` / `cons[N]`: formato `<strong>Título</strong>: explicação` — o `<strong>` está PERMITIDO **apenas no Título inicial**, não no meio do texto após o `:`. Render via `set:html` em ProsCons component.
  
  **AUTO-CHECK obrigatório**: ANTES de gravar `.mdx`, faça uma busca por `<strong>`, `<em>`, `<a `, `<p>` em subtitle/shortDescription/specs.value. Se achar — ERRADO. Reescreva como texto puro destacando via vocabulário, não markup. Caso real 2026-05-26 Bárbara: sub-agent escreveu `<strong>energia com foco preservado</strong>` na shortDescription do Integralmédica Huger; Astro escapou → texto literal pro usuário (não negrito).
- **Tag-aware nos links Amazon.** Se `siteConfig.affiliateTag` está preenchida, usar `?tag={tag}&linkCode=ogi&th=1&psc=1`. Se está vazia (`''`, estado de construção), usar **URL crua** sem `?tag=...`.
- **Não listar concorrentes.** É função do artigo comparativo, não da página individual.
- **NÃO comparar nem "divergir o ângulo" contra outros sites nossos.** Mesmo que o mesmo produto exista num site irmão (estratégia SERP-monopoly), escreva a MELHOR página pela bíblia, sem tentar ser diferente de propósito — forçar divergência contorce e piora o texto. A comparação cross-site (e a reescrita do que de fato colar) é trabalho da `pagina-produto-auditar`, que mede a similaridade real. Regra: criação escreve livre, audit mede, fix corrige.
- **Português brasileiro editorial.** Sem gírias, sem anglicismos desnecessários.

## Fluxo

0.5. **Carregar chavões do nicho** (régua v1.18.0, expandida v1.19.0):
   - Identifique `niche` do site em `docs/painel/sites-meta.json`
   - Read `docs/painel/_data/chavoes-por-nicho.json`
   - Use `_genericos` + bloco do nicho (ex: `Pré Treino`, `Creatinas`, `Tablets`)
   - Limites aplicam como guard rail editorial:
     - `termos_banidos_absoluto` → 0 ocorrências (peers/claim/stack/SKU/ASIN/lineup)
     - `linguagem_artificial_max` → calibrar/empilhar/pico-e-queda = 0 (v1.19.0)
     - `corporativo_max` → "diferencial central" cap 2, "posicionamento" cap 3 (v1.19.0)
     - `health_absolutes_banidos` → "uso regular é seguro", "alternativa segura" = 0 (YMYL, v1.19.0)
     - `concordancia_quebrada_regex` → composiçãos/combinaçãos/"a produto"/"a formigamento" = 0 (v1.19.0)
     - `ingles_max`, `medico_tecnico_max`, `industrial_max`, `indicacao_medica_max` — não passar do número

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

Título **descritivo editorial** curto, **sem redundância com o nome do produto**. Aparece como meta-info abaixo do H1. É frase de venda/posicionamento, NÃO dump de specs técnicos.

Exemplos bons (descritivos, editoriais):
- Para "Epson EcoTank L3250": `"Multifuncional EcoTank com Wi-Fi, ideal para casa e home office"`
- Para "Kärcher VCL 2": `"Aspirador vertical 2 em 1 com filtro HEPA"`

Exemplos ruins:
- ❌ `"Epson EcoTank L3250"` (redundante com o nome)
- ❌ `"Impressora"` (genérico demais, < 10 chars)
- ❌ `"Cápsulas com 990 mg de EPA e 660 mg de DHA por porção e certificação IFOS de pureza"` (**spec dump** — vai pra tabela specs, não pro subtitle)
- ❌ `"Versão de 60 cápsulas com 1360 mg de ômega 3 por dose e selo IFOS"` (spec dump)

Regra prática: se subtitle parece "ficha técnica resumida", reescreva como posicionamento editorial. Specs vivem na tabela `specs`.

### 2. `shortDescription` (string, 50-250 chars, alvo 180-230) — padrão BENEFÍCIO-FIRST

1-2 frases que aparecem no hero, abaixo do nome. **HARD CAP 250 chars.** Apesar de a página individual ter mais "espaço editorial" que a tabela do artigo, o shortDescription fica num card hero — texto longo passa de 3-4 linhas e quebra escanabilidade. Canon `melhoraspirador`: 225 média.

**Padrão obrigatório (régua v1.17.0): benefício/posicionamento PRIMEIRO, técnico DEPOIS.**

Estrutura em 3 partes:
1. **Abertura**: posicionamento, perfil ou adjetivo posicional (engancha)
2. **Meio**: 2-3 specs essenciais (justifica)
3. **Fecho**: destaque, diferencial ou benefício (reforça)

**3 moldes (varie):**
- **Molde A**: "Ideal pra quem [perfil], entrega [spec]. Você ganha [benefício]."
- **Molde B**: "[Adjetivos] pra [perfil]. Combina [spec 1] e [spec 2]. Destaque para [diferencial]."
- **Molde C**: "[Posicionamento curto] pra [perfil]. [Fórmula/spec]. [Embalagem ou diferencial]."

**Exemplos ✅:**
- ✓ `"Custo-benefício forte e fórmula completa pra iniciantes ou rotina contínua. Combina creatina, beta-alanina, taurina e cafeína anidra em dose pequena de 5g, com pote de 300g que rende 60 doses por cerca de R$ 55."` (Molde C, 211ch)
- ✓ `"Impressora EcoTank pra uso doméstico ou escritório pequeno. Tanque de tinta recarregável e impressão duplex automática, com rendimento de até 4.500 páginas em preto por kit. Destaque para o custo por página baixo."` (Molde B, 218ch)

**Exemplo ❌ (técnico-first, REGRESSÃO):**
- ❌ `"Impressora multifuncional da Epson (linha EcoTank L3250) com tanque de tinta, Wi-Fi Direct, ADF e rendimento de até 4.500 páginas em preto por kit T544. Indicada para uso doméstico ou escritório pequeno com volume médio."` (começa com marca + listagem de specs — perde o leitor)

**Drop SEMPRE:**
- ❌ "[Tipo] brasileira/o da [marca]" — marca já no campo `name`
- ❌ "todos declarados pelo fabricante" — implícito
- ❌ "preço médio em torno de R$ X" — preço já está nas specs
- ❌ Público-alvo verboso ("Voltada para quem precisa de... e quer manter...")
- ❌ Listagem completa de ingredientes — pega só 2-3 chave

**Adicionar:**
- ✅ Adjetivos posicionais ("Versátil", "Premium", "Custo-benefício forte")
- ✅ Conexão emocional ("Ideal pra quem...", "Você ganha...")
- ✅ Destaque do diferencial ("Destaque para...")

**Régua de corte mental**: leia a 1ª frase. Começa com "[Tipo] brasileiro da X..." → ERRADO. Começa com adjetivo posicional ou "Ideal pra..." → CERTO.

### 3. `pros` (array de strings, 3-8 itens, cada 60-180 chars com alvo 80-130)

Formato: `<strong>Título</strong>: explicação`. A explicação **SEMPRE com dado concreto**, nunca genérico. Paridade com prompts de artigo (`formato_pros_cons_specs` shared).

**HARD CAP em 180 chars/item** (texto puro, descontando markup). Canon `melhoraspirador`: média 65 chars/item. Bullet > 180 chars vira parágrafo e quebra escanabilidade.

Exemplos bons:
- ✓ `"<strong>Rendimento elevado</strong>: 4.500 páginas em preto por kit T544."` *(spec factual afirmado direto, sem "segundo o fabricante"; ver Armadilha 7)*
- ✓ `"<strong>MicroPiezo Heat-Free</strong>: não aquece a tinta no processo, com consumo de cerca de 12W em operação."` *(descrição própria, sem citação)*
- ✓ `"<strong>Sistema sem cartuchos</strong>: tanque de tinta com abastecimento frontal por garrafas, sem dependência de cartuchos descartáveis."` *(descrição própria simples)*

Errados:
- ❌ `"<strong>Rendimento alto</strong>: a impressora rende muito"` (sem dado)
- ❌ `"Sistema EcoTank com rendimento de até <strong>4.500 páginas</strong>..."` (strong inline em vez de Título: explicação — esse era o padrão antigo, NÃO usar)
- ❌ `"Melhor opção do mercado"` (superlativo sem evidência)
- ❌ `"Mais barata que a HP Smart Tank 581"` (comparação com concorrente — função do artigo)

### 4. `cons` (array de strings, 1-5 itens, cada 60-180 chars com alvo 80-130)

Mesma formatação dos pros: `<strong>Título</strong>: explicação`. Mesmos limites de tamanho (180 chars texto puro). Pontos de atenção, trade-offs, contextos onde NÃO comprar. Se a bíblia tem `pontosFracos` populados, use como ponto de partida.

Exemplo: `"<strong>Duplex manual</strong>: imprimir frente e verso exige virar o papel à mão, sem mecanismo automático."` *(108 chars — OK)*

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

**A âncora é SEMPRE o nome do produto (ou parte dele) — NUNCA frase-CTA.**
A página individual já tem o botão "Ver Preço na Amazon" logo abaixo do review;
repetir CTA dentro do texto é redundante e vira spam. A âncora contextualiza no
nome ("a [Produto] mira quem..."), não vende de novo.

- ❌ `<a ...>Ver preço na Amazon</a>` · `<a ...>Conferir oferta</a>` · `<a ...>é só acessar aqui</a>` · `<a ...>verificar a disponibilidade</a>` · `<a ...>Comprar na Amazon</a>`
- ✅ `<a ...>Dux Creatina Monohidratada</a>` · `<a ...>Creatina Creapure</a>` (nome ou pedaço dele)

**AUTO-CHECK 1 (âncora = nome)** antes de escrever: cada `<a>…</a>` do fullReview
deve conter o nome do produto (ou parte). Se a âncora contém "ver / conferir /
comprar / acessar / oferta / aqui / disponibilidade / preço na Amazon" e NÃO o
nome → ERRADO, reescreva ancorando no nome.

**AUTO-CHECK 2 (prefixo em negrito)**: os 4 prefixos DEVEM sair exatamente como
`<p><strong>Para quem é:</strong>`, `<p><strong>Por que gostamos:</strong>`,
`<p><strong>Pontos de atenção:</strong>`, `<p><strong>Resumo:</strong>`. Se
algum sair `<p>Para quem é:` (sem `<strong>`) → ERRADO. Render é `set:html`
fiel: sem `<strong>` no source = sem negrito na tela.

> Caso real 2026-06-01 (creatinasaprovadas): 5 de 9 páginas geradas em batch
> falharam aqui — 2 com prefixo sem negrito + nome do produto ausente + âncoras
> "é só acessar aqui"; 3 com âncoras "Ver preço na Amazon" em vez do nome.

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

**NUNCA** cite **compradores, opiniões, avaliações, reviews, estrelas, posicionamento Amazon**. Frases proibidas:
- ❌ "Compradores recorrentemente citam..."
- ❌ "Um comprador relata..."
- ❌ "Bem avaliada por usuários"
- ❌ "Conforme reviews na Amazon"
- ❌ "Nº 1 mais vendido na Amazon"

**Reescreva** insights da bíblia em voz analítica:
- ✓ "O custo-benefício se destaca: {dado concreto}"
- ✓ "Um trade-off identificado é..."
- ✓ "O equipamento entrega {feature} em {condição}"

> **Sobre citar o fabricante**: regra diferente de citar comprador/Amazon. Spec factual (rendimento, velocidade, economia) vai afirmado direto, sem "segundo X". Atribuir só vale pra recomendação/calibração/política do fabricante (ex: "a HP recomenda 50-100 págs/mês"). Ver Armadilha 7 abaixo pra régua completa.

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

## Como usar a bíblia

- `pontosFortes` / `pontosFracos`: base dos pros/cons. NÃO invente. **DESTILE ao copiar** — ver "Operação de destilação" abaixo.
- `angulosConversao`: ângulos editoriais. Use pra estruturar parágrafos do `fullReview` ("para quem é", "por que gostamos").
- `sentimentoCompradores`: insights — **REESCREVA** como observação editorial, NÃO cite compradores. Ex: "compradores citam custo-benefício" → "O custo-benefício se destaca por {dado da bíblia}".
- `dicasAcionaveis`: incorpore se fizer sentido no `fullReview` ou como item em `cons` (quando for limitação contextual).
- `dadosInconsistentes` + `decisaoEditorial`: SE existir, **RESPEITE**. A decisão editorial diz qual valor usar e qual ignorar.
- `observacoesAgente`: notas internas pra você. Leia.
- `avisosAoAgente` / `observacoesAgente`: instruções/observações do humano. **Leia e respeite.**
- **Produto descontinuado** (régua canon): se `avisosAoAgente`/`observacoesAgente` indicarem que o produto **saiu de linha / foi descontinuado** com uma sucessora, **VOCÊ coloca o banner**: (1) **SETE o campo `descontinuado: { asin, nome }` no frontmatter do `.mdx`** — `nome` = nome completo da sucessora (com marca); `asin` = ASIN da sucessora. Se o aviso só trouxer o nome, **resolva o ASIN** na bíblia (`docs/biblias-v2/`) ou na página (`sites/{site}/src/content/products/`) da sucessora. Isso dispara o banner âmbar "produto descontinuado" + `schema.org/Discontinued` + link tag-aware da sucessora. (2) Escreva a review **honesta**: não venda como a compra atual; a sucessora é a recomendação corrente. Sem hedge de "confirmar disponibilidade" — descontinuado é descontinuado.
- `specsAmazon` + `doFabricante` + `conteudoBrutoFabricante`: fontes pra `specs` e claims numéricos no `fullReview`. Peso editorial varia por fonte — ver "Peso por fonte" abaixo.

## Operação de destilação bíblia → .mdx (CRÍTICO)

A bíblia carrega claims COM marcadores de procedência (`fonte: "specs"`, "conforme declarado pelo fabricante", "confirmado nos alérgenos"). É correto e útil internamente — rastreabilidade evita invenção. **O .mdx público é destilado**: droppa marcadores que viraram ruído burocrático.

**4 categorias de claim — como destilar cada:**

| Tipo | Bíblia (raw, OK) | .mdx destilado |
|---|---|---|
| **A) Fato verificável simples** | "Sem glúten confirmado nos alérgenos da Amazon" | "Sem glúten" |
| **B) Claim do fabricante repetível** | "Forma triglicerídeo, apontada pelo fabricante como mais absorvível" | "Forma triglicerídeo, considerada mais absorvível" |
| **C) Claim institucional / PR** | "Marca tradicional brasileira segundo o próprio fabricante" | "Marca brasileira" (ou omite se não agrega) |
| **D) Voz comprador implícita** | "Cápsulas sem sabor segundo relatos de compradores" | "Cápsulas sem sabor" |

**Exceção (raro, mas existe)**: recomendação/calibração/política do fabricante (ex: "a HP recomenda 50-100 págs/mês") pode manter "segundo X". Spec factual (rendimento, velocidade) NÃO — vai direto. Ver Armadilha 7 abaixo.

## Peso por fonte

Ao decidir QUAL claim vira pro central vs. spec, considere a fonte:

| Combinação de fontes | Confiança | Onde usar |
|---|---|---|
| Fabricante + Amazon coincidem | **FORTE** | Pode ser pro central, strong, ênfase no fullReview |
| Só fabricante | MÉDIO | OK em pros/specs, descrição própria (sem "segundo X") |
| Só Amazon (specsAmazon) | **FRACO** | Só na tabela specs, NÃO vira pro central |
| Só opiniões | FRACO | Inspira voz, não cita |

**Caso real (Vitafor B07L5W6GVC)**: "Composição cetogênica" vem de `Tipo de dieta: Cetogênica` nas specs Amazon — fonte fraca, classificação automática do marketplace. Vai na tabela specs, **não vira pro central**. Óleo de peixe é trivialmente keto (sem carboidrato); elevar isso a "diferencial" engana o leitor.

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

Se a página individual repete o `fullReview` do artigo, o SEO penaliza. Antes de gerar, leia o `fullReview` do produto no review (campo `apareceNosArtigos` da bíblia ajuda a localizar). Se ainda não há review citando o ASIN, ângulo é livre.

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

### 7. Voz de citação ("segundo X", "alérgenos confirmam", "atributos declaram") — viola diretrizes #1, #5 e #6

**Armadilha mais comum e fácil de cair.** Quando os dados da bíblia vêm de várias fontes (specsAmazon, doFabricante, conteudoBrutoFabricante), o modelo tende a citar a fonte pra justificar o claim: "segundo a Epson", "alérgenos da Amazon confirmam", "atributos de material declaram".

**A diretriz #5 da bíblia proíbe isso explicitamente**: *"Proibido dizer 'na ficha técnica', 'segundo as especificações' ou variantes: o review não pode parecer leitura de planilha."*
A #6 reforça: *"Integre os dados no texto como quem conhece o produto: não cite specs em bloco, costure no raciocínio."*

**Régua editorial — voz-citação OK SÓ quando atende AS DUAS condições:**

1. **(a) é recomendação/calibração/política do fabricante** (ex: "a HP recomenda 50-100 págs/mês", garantia estendida com registro) — NÃO spec factual: rendimento/economia/velocidade vão direto, sem atribuir
2. **(b) adiciona valor editorial ao leitor** (calibra expectativa, sinaliza honestidade, faz crítica útil)

Se NÃO atende as duas → drop. Régua editorial, não checklist mecânico.

**✓ EDITORIAL OK** (referência canônica: `sites/melhorimpressora/src/content/products/epson-ecotank-l3250.mdx`):
- "rende até 4.500 páginas em preto" → spec de fabricante afirmado DIRETO, sem "segundo a Epson" (atribuir rendimento/economia vira muleta)
- "número de marketing 33 ppm, mas a **velocidade ISO (padrão da indústria)** é mais realista" → crítica útil, separa marketing de fato
- "a HP recomenda volume de 50 a 100 páginas mensais" → claim só-fabricante + ajuda leitor calibrar uso

**❌ BUROCRÁTICA** (drop sempre):

Caso impressora (B0C1L2R4HH gerou 16 ocorrências numa única passada):
- "datasheet HP" / "no datasheet" *(jargão burocrático sem valor pro leitor)*
- "anúncio Amazon" / "apesar do anúncio Amazon listar"
- "conforme o fabricante" sem qualificar nada
- "na recomendação do fabricante" como muleta repetitiva

Caso suplemento (B07L5W6GVC + B09S3YDC6H + B081VQZ1YK, ômega 3):
- "alérgenos da Amazon confirmam ausência de glúten" → "sem glúten" *(fato trivial, marcação é só ruído)*
- "atributos de material declaram ausência de contaminantes" → "livre de contaminantes"
- "conforme tipo de dieta declarado" → "compatível com dieta X"
- "relato recorrente nas opiniões indica cápsulas sem sabor" → "cápsulas sem sabor"
- "apontada pelo fabricante como mais absorvível" → "considerada mais absorvível"
- "citada como motivo de preferência por um comprador" → drop ou reformula

**Reformulação correta** — afirmar como conhecimento próprio:

| ❌ Burocrática | ✓ Análise destilada |
|---|---|
| "alérgenos da Amazon confirmam ausência de glúten" | "sem glúten" |
| "atributos de material declaram ausência de contaminantes" | "livre de contaminantes" |
| "conforme tipo de dieta declarado" | "compatível com dieta X" |
| "apontada pelo fabricante como mais absorvível" | "considerada mais absorvível" |
| "relato recorrente nas opiniões indica cápsulas sem sabor" | "cápsulas sem sabor" |
| "apesar do anúncio Amazon listar duplex automático, o datasheet HP descreve manual" | "a impressão frente e verso é manual" *(toma o lado correto, ignora conflito interno)* |
| "volume mensal recomendado pela HP" | "volume mensal confortável" *(descrição editorial nossa)* |

**Tratamento de divergências internas** (dadosInconsistentes): a `decisaoEditorial` da bíblia já diz qual lado tomar. Aplica direto, sem mencionar o conflito (ex: duplex Amazon-diz-Auto vs HP-diz-Manual → escolhe Manual e afirma; o leitor não precisa saber da contradição interna, é problema nosso).

**Quando referenciar marca/fabricante É OK**:
- ✓ "cadastro no site da HP em até 60 dias" *(informação prática)*
- ✓ "app HP Smart centraliza configuração" *(nome do app)*
- ✓ "rende até 4.500 páginas" *(spec de fabricante afirmado direto, sem muleta de fonte)*
- ❌ "sem glúten confirmado nos alérgenos da Amazon" *(fato trivial + marcação burocrática)*

**Antes de gravar, faça grep mental**: se aparece "confirmado", "declarado", "apontada", "conforme X", "segundo Y", "relato recorrente", "atributos de material" — reescreva. Exceção: passou nos 2 critérios editoriais acima.

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

.claude/skills/pagina-produto-criar/SKILL.md      → segue
.claude/skills/pagina-produto-auditar/SKILL.md    → segue
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

Args canônico que invoco: `Skill(skill="pagina-produto-criar", args="melhorimpressora/epson-ecotank-l3250")`.

### Auto-check de concordância PT-BR (régua v1.19.0, canon 2026-05-28)

**Bug-class real** (batch melhorpretreino v1.17-1.18 — ChatGPT-Bárbara identificou 11+ casos): substituições mecânicas (BCAAs→aminoácidos, parestesia→formigamento, fórmula→composição) **NÃO reconcordaram** plural/gênero/artigo.

**Auto-check antes de gravar — grep regex**:

```python
import re

# Para cada campo (subtitle, shortDescription, pros, cons, specs.value, fullReview):

# 1) Plural errado em -ãos (deve ser -ões)
re.search(r'\b(composição|combinação|porção|injeção|reação|opção|posição)s\b', campo)
# composiçãos → composições, combinaçãos → combinações

# 2) Artigo errado antes de substantivo masculino
re.search(r'\b(a|na|da|esta|nessa|nesta|essa) (produto|formigamento|ingrediente|ativo|estímulo|composto)\b', campo, re.IGNORECASE)
# "a produto" → "o produto" / "a formigamento" → "o formigamento"

# 3) Artigo errado antes de substantivo feminino
re.search(r'\b(o|no|do|este|nesse|neste|esse) (fórmula|dose|porção|composição|tolerância)\b', campo, re.IGNORECASE)

# 4) Adjetivo concordância quebrada
re.search(r'produto[s]? elaborada[s]?\b|produto ampla|formula natural', campo, re.IGNORECASE)
# "produto ampla" → "fórmula ampla" / "formula natural" → "fórmula natural"

# 5) Duplicação preposicional "no em 20XX"
re.search(r'\b(?:disponíveis?|disponível) no em \d{4}', campo, re.IGNORECASE)
```

Se achar — corrija antes de gravar.

### Health absolutes YMYL banidos (régua v1.19.0, canon 2026-05-28)

**Bug-class** (ChatGPT ponto 7): absolutos de segurança/saúde violam diretrizes YMYL do Google.

**Banidos absolutos** (limite 0):
- "uso regular é seguro" → "Tolerado em uso regular pela maioria; consulte um profissional"
- "alternativa segura" → "alternativa mais leve"
- "não causa dano" → "Sem evidência de impacto em pessoas saudáveis em doses recomendadas"
- "totalmente seguro" / "100% seguro" / "sem riscos" → reescrever qualificando
- "sem efeitos colaterais" → "Efeitos colaterais raros e leves quando reportados"
- "cientificamente comprovado" / "clinicamente comprovado" (sem citar estudo)

### Voz-eximir-responsabilidade (régua v1.19.1, canon 2026-05-28)

**Bug-class**: "declarado pelo fabricante", "X mg declarados", "todas declaradas" viram muleta epistêmica — o site se eximindo de afirmar diretamente. Se o dado está na ficha técnica, é por definição declarado: redundância pura.

**3 sub-padrões proibidos**:

a) **"X mg declarados" parentético** (redundância):
- ❌ "(400 mg declarados)" → ✓ "(400 mg)"
- ❌ "valina (550 mg) declarados" → ✓ "valina (550 mg)"

b) **"declarado pelo fabricante" sobrando** (transfere responsabilidade):
- ❌ "doses todas declaradas pelo fabricante" → ✓ "doses transparentes" / "fórmula totalmente declarada"
- ❌ "restrição etária declarada pelo fabricante é 19 anos" → ✓ "restrição etária 19 anos"

c) **Alérgeno com "declarado"** (rotulagem é obrigatória por lei):
- ❌ "A fórmula contém glúten declarado pelo fabricante" → ✓ "Contém glúten"
- ❌ "Sem mg declarada de creatina" → ✓ "Sem creatina específica na fórmula"

**FLAG "segundo a [marca]" em spec factual** (régua v1.21.1): "rende 4.500 páginas, segundo a Epson" -> atribuir rendimento/economia/velocidade é muleta; o fix é afirmar direto ("rende até 4.500 páginas"). Atribuição só passa em recomendação/calibração do fabricante (ex: "a HP recomenda 50-100 págs/mês").

**Auto-check**: grep `\d+\s*(mg|g|µg|ml)\s+declarad`, `declarad\w+ pelo fabricante`, `(todos|todas|doses) declarad` antes de gravar. Achou → drop "declarad*" e verifique se a frase ainda faz sentido.

### Voz consultiva, não corporativa (régua v1.19.0)

Termos corporativos quebram voz especialista→amigo. Caps no JSON:
- `diferencial central`: 2 / `posicionamento`: 3 / `segmento`: 3 / `proposta de valor`: 0

**Substituições**:
| ❌ Corporativo | ✓ Conversacional |
|---|---|
| "O diferencial central é..." | "O grande ponto é..." |
| "Posicionamento de mercado premium" | "Categoria premium" / "Linha mais cara" |
| "Atende ao segmento de X" | "Funciona pra quem X" |

### Auto-check de capitalização + duplicação (régua v1.18.3, canon 2026-05-28)

**Bug-class real** (caso `melhorpretreino` commit `a72e7d9`): substituições mecânicas podem causar duplicação contígua, bullets minúsculos ou minúscula após ponto.

**Auto-check obrigatório ANTES de gravar**:

```python
import re

# Para cada campo gerado (shortDescription, fullReview, pros, cons, specs.value):

# a) Duplicação contígua (>=8 chars repetidos em sequência)
for m in re.finditer(r'([a-zA-ZÀ-ÿ\s]{8,40})\1', campo):
    print(f"⚠ duplicação: {m.group(0)}")
    # → Reescreve removendo a metade duplicada

# b) Bullet começa com minúscula (em pros/cons)
for bullet in pros + cons:
    if re.match(r'<strong>[a-záéíóúâêôãõàèìòùç]', bullet):
        print(f"⚠ bullet minúsculo: {bullet[:60]}")
        # → Capitalize primeira letra dentro de <strong>...</strong>

# c) Minúscula após ponto (texto editorial — excluir URLs)
for m in re.finditer(r'\. ([a-záéíóúâêôãõàèìòùç])', campo):
    ctx = campo[max(0,m.start()-30):m.end()+30]
    if 'http' in ctx or 'amazon.com.br' in ctx: continue
    if re.search(r'\d+\. \w', ctx[:50]): continue  # lista numerada
    print(f"⚠ minúsc após ponto: ...{ctx}...")
    # → Capitalize a letra (.+ espaço + Letra)
```

**Exemplos reais** (commit a72e7d9, melhorpretreino):
- a: `"sem empilhar suplementos sem empilhar suplementos"`
- b: `"<strong>aminoácidos essenciais na fórmula</strong>"` (era BCAAs → minúsculo)
- c: `"(maior dose declarada). pra emagrecer onde"` (era "em cutting" → minúsculo)

Se achar qualquer bug: corrija ANTES de gravar. Não bloqueia geração, mas evita commit com erro.

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), a validação fica editorial — eu (modelo) sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial (subtitle de 9 chars, fullReview de 290 chars, etc).

Mitigação: depois de gerar, conferir tamanhos antes de salvar. Se algum estiver no limite, expandir/encurtar com cuidado.
