---
name: pagina-produto-criar
description: Cria os 6 campos editoriais (subtitle, shortDescription, pros, cons, specs, fullReview) da página individual de produto a partir da bíblia. Aceita URL do painel (editor-produto.html?site=X&slug=Y) OU args canônicos `site/slug`. Stub precisa existir (criado no painel via "+ Nova página de produto"). Carrega chavões nicho-específicos de `docs/painel/_data/chavoes-por-nicho.json`. Aplica régua editorial: concordância PT-BR, ban "declarado pelo fabricante" como muleta, health absolutes YMYL, hard caps de tamanho (shortDescription ≤250, pros/cons ≤180 texto puro), shortDescription literal (para quem é + dados, sem molde), voz natural (verbo e substantivo no sentido do dicionário, sem frase-sacada, "para" no texto público, repetir a palavra certa é normal). Cria backup, commit, push, dispatch VPS pull.
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
> O conteúdo essencial está duplicado abaixo pra autocontenção. **Esta SKILL.md é a fonte viva** desta execução (o `agent-prompts.json` é o espelho do path do painel/API e pode defasar — o projeto roda via Claude Code).

Você é o curador editorial da página individual do produto. A página existe em `sites/{site}/src/content/products/{slug}.mdx`, criada como stub pelo endpoint `POST /product/:site/_actions/create-from-bible`. Sua função é **gerar os 6 campos editoriais** (subtitle, shortDescription, pros, cons, specs, fullReview) a partir da bíblia, com qualidade editorial alta e SEM duplicar conteúdo do produto-no-artigo (anti-duplicate-content SEO).

## Pré-requisitos

O `.mdx` da página já deve existir como **stub** com frontmatter mínimo (asin, name, image, imageAlt, category, categorySlug, publishDate). Se não existir, abortar com mensagem clara:

> "Página individual {slug} não existe ainda em {site}. Antes de preencher, crie o stub no painel: site detail → tabela 'Páginas de produto' → '+ Nova página de produto'."

## Invariantes

- **Nunca invente dados.** Tudo que você escrever precisa ter origem rastreável na bíblia (`pontosFortes`, `pontosFracos`, `angulosConversao`, `sentimentoCompradores`, `specsAmazon`, `doFabricante`, etc).
- **Conteúdo INDEPENDENTE do produto-no-artigo.** A página individual tem ângulo editorial próprio. Não copie/parafraseie do `fullReview` do review — usa estrutura, voz e ângulo diferentes (anti-duplicate-content). Se o produto aparece em algum review (campo `apareceNosArtigos` da bíblia ou via Grep nos `.mdx` de `sites/{site}/src/content/reviews/`), leia pra saber o que NÃO repetir.
- **Sem travessão (—).** Em nenhum campo. Use vírgula, ponto, parênteses ou dois pontos.
- **Sem ponto-e-vírgula (;).** (régua 2026-06-20) Tem cara de IA na voz conversacional. Troque por "." (sentença nova), "," (pausa) ou "()". Vale em TODOS os campos. AUTO-CHECK antes de gravar: depois de remover entidades (&amp;, &#..;) e a querystring dos links de afiliado, não pode sobrar ";" no texto.
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
- **SEM confirmação — prossiga direto** (canon Marcelo 2026-07-24). Chegou ao passo de gerar = os pré-requisitos foram lidos (`.mdx` existe, bíblia existe, tag resolvida). NÃO pergunte "posso criar?/confirma?" — os aborts do fluxo (404 do `.mdx`, bíblia ausente) são a única barreira. Perguntar antes de escrever é atrito. (Exceção estrita: input de args genuinamente ambíguo no passo 1 — aí sim esclareça o mapeamento antes; não é confirmação de "pode criar".)

## Fluxo

0.5. **Carregar chavões do nicho** (régua v1.18.0, expandida v1.19.0):
   - Identifique `niche` do site em `docs/painel/sites-meta.json`
   - Read `docs/painel/_data/chavoes-por-nicho.json`
   - Use `_genericos` + bloco do nicho (ex: `Pré Treino`, `Creatinas`, `Tablets`)
   - **⚠ `_sites_aplicaveis` é o gate (canon 2026-08-15):** site fora da lista do bloco de nicho → **só o `_genericos` vale**. Não force pelo `niche`. E conte o `_genericos` SEMPRE: `chavoes_estruturais_max` tem as 4 variantes de "seleção" em cap **0**, e `industrial_max` tem `declarado` em 3.
   - Durante a geração:
     - `termos_banidos_absoluto` e tetos **0** → regra DURA, 0 ocorrências.
     - **Todo teto NUMÉRICO é referência, não limite (canon Marcelo 2026-09-05).** Serve pra você notar
       que está martelando a mesma palavra. **NUNCA troque a palavra certa, apague um fato ou reescreva
       uma spec pra fazer um número baixar** — isso contradiz a régua de voz natural desta mesma skill
       ("repetir a palavra certa é normal") e já produziu dano medido (ver `_meta.por_que_informativo`
       no JSON). Passou do teto e não há como reduzir sem piorar o texto? Deixa como está.
   - Detalhe das chaves:
     - `termos_banidos_absoluto` → 0 ocorrências (peers/claim/stack/SKU/ASIN/lineup)
     - `linguagem_artificial_max` (vive no bloco do NICHO, ex. Pré Treino — NÃO é genérico; v1.32.0) → aplicar quando o bloco do nicho listar; em nichos sem o bloco, evite mesmo assim o uso figurado ("calibrada pra rotina" → "feita pra")
     - `corporativo_max` → "diferencial central" cap 2, "posicionamento" cap 3 (v1.19.0)
     - `health_absolutes_banidos` → "uso regular é seguro", "alternativa segura" = 0 (YMYL, v1.19.0)
     - `concordancia_quebrada_regex` → composiçãos/combinaçãos/"a produto"/"a formigamento" = 0 (v1.19.0)
     - `ingles_max`, `medico_tecnico_max`, `industrial_max`, `indicacao_medica_max` — referência, não limite (não troque a palavra certa pra baixar contagem)

1. **Parse args**: aceita formatos `{site}/{slug}` (canônico) ou nomes humanos. Exemplos válidos:
   - `melhorimpressora/epson-ecotank-l3250` ✓
   - `melhorimpressora epson-ecotank-l3250` ✓
   - `L3250 melhorimpressora` (descobrir slug via ASIN da bíblia + procurar em `sites/{site}/src/content/products/`)
   - `B098YHFT9S melhorimpressora` (idem)
   - Se ambíguo, perguntar antes de prosseguir.

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   bash scripts/git-pull-seguro.sh "skill-pagina-produto-criar-temp"
   ```
   O script escolhe a estratégia: árvore de conteúdo **limpa** → stash + rebase + pop;
   **suja** → `fetch` + `merge --ff-only`, sem stash (outra janela do Claude Code pode
   estar gravando, e stash é global — canon 2026-09-02). Ele imprime a linha de controle
   `local · remote` e avisa com ⛔ se o remote tiver commit que você não tem: aí o disco
   está velho, decida se para ou segue sabendo disso. Nunca engula a saída dele.

   **Chave-mestra do site (CLAUDE.md):** antes de escrever em `sites/{site}/src/content/**`, `python3 -c "import json;print(json.load(open('docs/painel/sites-meta.json'))['{site}'].get('contentLocked'))"` — `True` → PARE e avise (o site está com edição travada; destravar no painel → Proteção). Sem isso o `pre-push` barra no fim, depois de todo o trabalho.

   Painel VPS commita+pusha automaticamente quando user cria/edita conteúdo na UI; Mac local pode estar 5-30s atrás. Sem este pull, skill pode ler estado stale e abortar com falso "X não existe localmente". Caso real Bárbara 2026-05-24: ela criou site melhoromega3 + stub vitafor-omegafor-plus pelo painel VPS; sub-agent rodou git fetch (sem novidades), assumiu que site não existia. Pull antes evita esse falso-negativo.

2. **Read .mdx atual**: `Read sites/{site}/src/content/products/{slug}.mdx`. Se 404, abortar com mensagem do pré-requisito.

3. **Parsear frontmatter**: extrair `asin`, `name`, `image`, `imageAlt`, `category`, `categorySlug`. Validar que `asin` está no formato `[A-Z0-9]{10}`.

4. **Read bíblia**: `Read docs/biblias-v2/{asin}.json`. Se não existir, abortar (bíblia foi deletada após criação do stub — raro mas possível).
   - **Defesa em profundidade (canon 2026-07-26):** se a bíblia tem imagem em `conteudoBrutoFabricanteImagens`/`doFabricanteImagens` **e** o `conteudoBrutoFabricante` está fino ou é só um recado ("o texto está na imagem em anexo"), **avise no relatório e não finja que a base está completa** — a bíblia provavelmente ainda não teve as imagens lidas (`imagensVerificadasEm` ausente confirma). O certo é rodar `biblia-preencher` (ou `--enriquecer`) antes, em vez de escrever a página com base incompleta. Depois que a régua nova das skills de bíblia rodar, isso vira raro; a linha existe pro caso residual.

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
    # raiz do repo — o cwd do Bash reseta pra ~/Documents/Claude em sessão continuada; sem isto o mkdir cria a árvore LÁ (medido 03/09/26)
    cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" && test -f docs/painel/sites-meta.json || { echo "⛔ cwd errado ($(pwd)): rode a partir da raiz do ProjetoAfiliados"; exit 1; }
    DAY=$(date +%Y-%m-%d); TIME=$(date +%H%M%S); SITE={site}; SLUG={slug}
    mkdir -p "docs/painel/.painel-backups/$DAY"
    cp "sites/$SITE/src/content/products/$SLUG.mdx" "docs/painel/.painel-backups/$DAY/product-${SITE}-${SLUG}-${TIME}.mdx"
    ```

11. **Write `.mdx`**: monta o novo conteúdo:
    - **Frontmatter**: preserva todos os campos base existentes (asin, name, image, imageAlt, category, categorySlug, publishDate, contentLocked se existir). **Adiciona** os 6 campos editoriais (subtitle, shortDescription, pros, cons, specs, fullReview).
    - **Body**: remove o marker de stub (`{/* STUB GERADO POR ... [TODO: preencher] */}`). Body fica vazio ou com 1 linha em branco.

      🚨 **O TEXTO VAI NO CAMPO `fullReview:` DO FRONTMATTER, NUNCA NO CORPO DO `.mdx`.** Corpo de página de produto **não renderiza**: o `SlugPage` só monta `<Content />` quando `type === 'review'`. Escrever a resenha no corpo produz uma página que vai pro ar **sem resenha nenhuma**, e nada reclama — build passa, painel não acusa, a página abre bonita e vazia. **Caso real 2026-08-14:** 7 páginas em 3 sites ficaram **meses** assim; o texto existia, completo e bom, no lugar que ninguém lê. Foram consertadas MOVENDO o texto pro campo (não regerando — o texto já era original por site). Na mesma varredura apareceu a variante: `guiaesportivo/vitafor-vita-d3-2000ui-gotas` com a resenha NOVA no campo e 2.222 chars da resenha VELHA esquecidos no corpo, resíduo de uma reescrita que gravou no frontmatter e não limpou o corpo. **Ao reescrever uma página que já existe, apague o corpo — não basta preencher o campo.**

    - **AUTO-CHECK DE CORPO E CAMPO (OBRIGATÓRIO pós-Write, canon 2026-08-14)**:
      ```bash
      bun scripts/pagina-produto-guardas.ts {site} {slug}
      ```
      Reprova `fullReview-ausente` (campo não existe → página sem resenha), `fullReview-duplicado` (>1 ocorrência) e `corpo-nao-vazio` (texto no corpo, comentário MDX não conta). **Por que o check nasceu:** a guarda anterior fazia `findIndex` do campo e saía em silêncio quando ele não existia — ausência passava como "nada a conferir", que é exatamente o buraco por onde as 7 páginas caíram. Zero é defeito, não isenção.

    - **AUTO-CHECK DE FENCE (OBRIGATÓRIO pós-Write)**: rode `grep -c '^---$'` no `.mdx` — tem que dar **exatamente 2** (abre+fecha o frontmatter). Se der **1**, faltou a fence de fechamento (o block scalar `>-` do `fullReview`, último campo, correu até o EOF) → **anexe `\n---\n` no fim do arquivo** e re-confira. Sem isso o build quebra com `asin: Required / name: Required` (caso real Bárbara 2026-06-15).

    - **AUTO-CHECK MECÂNICO DETERMINÍSTICO (OBRIGATÓRIO pós-Write, canon 2026-07-24)** — NÃO conte char de cabeça:
      ```bash
      bun scripts/audit-editorial.ts {site}/{slug} --json
      ```
      Cobre 100% dos checks contáveis/estruturais: tamanho texto-puro (shortDescription ≤250, pros/cons ≤180), fence, travessão, `;` em prosa (entity+url-aware, exclui specs.value), HTML em campo texto-puro, 4 rótulos do fullReview, termos banidos absolutos. **É AUTORITATIVO** — se ele apontar `error`, conserte SÓ o campo apontado e re-rode (máx 2×). **Por quê:** LLM erra ~1/3 desses (medido: 6 de 19 shortDescriptions >250 vivas passaram batido na auditoria). Este passo substitui o "eyeball" dos hard caps de tamanho/`;`/travessão — não confie na sua contagem, confie no script. Se `bun`/lib faltar (raro), caia nos auto-checks manuais das mesmas categorias. **Escopo: só o mecânico** — ele NÃO cobre tag-affiliate (tag pode ser injetada no build) nem julgamento (claim-vs-bible etc.), que seguem sendo seus nos passos da régua.
      **⚠ Modo batch:** se você é um sub-agent da `pagina-produto-criar-em-massa` (REGRA ZERO), **PULE este passo** — a skill-mãe roda **este mesmo script**, 1× por slug, no commit-lote (passo 9 dela). Rodar aqui = N spawns paralelos redundantes. ⚠ Até 2026-07-31 esta nota dizia que a mãe rodava "a guarda equivalente": era falso, a `pagina-produto-guardas` não cobre travessão, `;` nem HTML em texto-puro, e o batch sem `--audit` ficava sem esses três. Corrigido na mãe.

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
    git commit --only -m "feat({site}): preenche página individual {slug} via skill" \
      -m "Co-Authored-By: {modelo da sessão} <noreply@anthropic.com>" \
      -- sites/{site}/src/content/products/{slug}.mdx
    git push origin main
    ```

    Sem `--no-verify` de propósito: o hook pre-commit só bloqueia `.mdx` de `reviews/` — `products/` passa limpo. Não "conserte" adicionando a flag.

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

### ⚠ Regra que vale para `subtitle` e `shortDescription`: número curto carrega o qualificador

**Se a bíblia condiciona um número, o condicionante viaja com ele para TODO campo onde
o número aparecer — inclusive os curtos.** Quando não couber, **corte o número, nunca o
qualificador**.

Isso existe porque o erro tem uma direção só e ela é sempre a mesma: o `fullReview`
qualifica certo, e o aperto de espaço do `subtitle`/`shortDescription` derruba a condição.
E são justamente esses dois campos que circulam **sozinhos**, no card e no snippet da
SERP, longe do parágrafo que consertaria.

Medido em 4 batches de 10 páginas (2026-08-06), sempre o mesmo desenho:

```
"180 Hz"            sem "pela DisplayPort"    ← a HDMI do mesmo monitor faz 144
"120 Hz"            sem "por overclock"       ← o nativo é 100
"15 horas"          sem "até"                 ← a bíblia marca condição ideal
"0,3 ms"            sem "MPRT"                ← métrica diferente de GtG
"Sem som próprio"   afirmando a ausência      ← a bíblia mandou não afirmar
```

Em todos, o corpo do texto estava certo. O defeito nasceu no encurtamento.

**Teste antes de gravar:** leia o `subtitle` e a `shortDescription` isolados, como se o
resto da página não existisse. Algum número promete mais do que a bíblia sustenta?

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

### 2. `shortDescription` (string, 50-250 chars) — o que o produto é e para quem, em linguagem literal

1-2 frases que aparecem no hero, abaixo do nome. **HARD CAP 250 chars** (card hero: texto longo passa de 3-4 linhas e quebra escanabilidade). **Não é ficha técnica** (não começa com marca nem com lista de specs), mas também **não é frase de efeito**.

Estrutura (sem molde fixo de palavras — a estrutura é a mesma, o fraseado nasce do produto):
1. **1ª frase: para quem serve ou o que faz de melhor**, dita de forma literal ("Impressora com tanque de tinta para casa e escritório pequeno" / "Creatina pura, sem aditivo, para uso contínuo").
2. **2-3 dados essenciais** que justificam.
3. **Fecho: um fato** (rendimento, embalagem, diferencial concreto, acessório na caixa). O preço já está na página: **não use preço como fecho padrão** (teto: metade das páginas do site). Sem "Você ganha…", sem sacada.

⚠️ **Sem fecho-molde.** Medido em 2026-08-06: **1.043 de 3.003 páginas da rede (35%)** fechavam com "Destaque para", e "Ideal pra quem" abria 18% (2026-08-15) — assinatura textual que liga os sites entre si. O fecho é uma frase de fato ("São 4.500 páginas em preto por kit."), não um molde e não uma frase esperta ("o custo por página é o que segura a conta", "quem esquece a impressora ligada agradece" eram sugestões desta skill até 2026-08-15 e saíram: verbo fora do sentido).

**Exemplos ✓:**
- ✓ `"Impressora com tanque de tinta para casa e escritório pequeno. Imprime, copia e digitaliza, com Wi-Fi e rendimento de até 4.500 páginas em preto por kit."` (≈150ch) — exemplo de outra categoria de propósito: NÃO reuse a abertura literal
- ✓ `"Creatina pura para uso contínuo, sem aditivo nem sabor. São 5 g por dose, pote de 300 g que rende 60 doses e laudo de pureza de laboratório independente."` (≈160ch)

**Exemplos ❌:**
- ❌ `"Impressora multifuncional da Epson (linha EcoTank L3250) com tanque de tinta, Wi-Fi Direct, ADF e rendimento de até 4.500 páginas em preto por kit T544. Indicada para uso doméstico..."` (começa com marca + listagem de specs)
- ❌ `"Ideal pra quem imprime em casa, entrega 4.500 páginas por kit. Você ganha meses sem trocar tinta. Destaque para o Wi-Fi."` (molde + "entrega/ganha" fora do sentido literal)

**Drop SEMPRE:**
- ❌ "[Tipo] brasileira/o da [marca]" — marca já no campo `name`
- ❌ "todos declarados pelo fabricante" — implícito
- ❌ "preço médio em torno de R$ X" como abertura — preço pode fechar, não abrir
- ❌ Público-alvo verboso ("Voltada para quem precisa de... e quer manter...")
- ❌ Listagem completa de ingredientes — pega só 2-3 chave
- ❌ Moldes de abertura/fecho ("Ideal pra quem", "Feito pra quem", "Você ganha", "Destaque para", "Custo-benefício forte pra")

**Régua de corte mental**: releia a 1ª frase: diz para quem é ou o que faz, com verbo no sentido literal? Começa com marca ou lista → inverta. Começa com "Ideal pra quem… entrega…" → reescreva literal.

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

Mesma formatação dos pros: `<strong>Título</strong>: explicação`. Mesmos limites de tamanho (180 chars texto puro). Pontos de atenção, contrapartidas, contextos onde NÃO comprar. Se a bíblia tem `pontosFracos` populados, use como ponto de partida.

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

### 6. `fullReview` (string HTML, 800-3000 chars de **texto puro**)

⚠️ **A faixa é de TEXTO PURO, descontando o markup** — igual a `shortDescription`,
`pros` e `cons`, que já diziam isso. Não conte `<p>`, `<strong>` nem as três URLs
da Amazon com `?tag=...&linkCode=ogi&th=1&psc=1`.

Isto era ambíguo até 2026-08-06 e a ambiguidade custava caro. Medido na rede:
**o markup come 23% a 27% do campo**, e 8 páginas estouravam os 3.000 sem ter
2.600 chars de texto em nenhuma delas. Pior, o aperto caía justo em quem tinha
o que dizer: o p99 dos nichos complexos ficava colado em 2.998 — sub-agents
parando na linha — enquanto o mesmo p99 em texto puro era ~2.380.

```
                      p99 bruto   p99 texto puro
Eletrônicos              2.998           2.383
Caixas de Som            2.998           2.358
Impressoras              2.974           2.330
Creatinas                2.385           1.816   ← nunca chega perto
```

**A faixa não força ninguém a encher.** Produto simples para onde o conteúdo
acaba: creatina fica em 1.816 no p99, com o mesmo teto que monitor usa até o
limite. Se a bíblia não sustenta mais texto, o campo termina antes — o teto é
proteção contra prolixidade, nunca meta a atingir.

**Quando houver muito o que cobrir**, o caminho é a divisão autorizada do
"Por que gostamos" (features-chave num parágrafo, specs gerais no seguinte),
descrita logo abaixo, e não esticar cada parágrafo.

**Estrutura obrigatória — 4 parágrafos marcados, paridade com `formato_full_review` dos prompts de artigo**:

```html
<p><strong>Para quem é:</strong> perfil de uso, ambiente, tipo de comprador. Inclua 1 link Amazon no nome do produto neste parágrafo.</p>

<p><strong>Por que gostamos:</strong> features-chave com dados concretos. Inclua 1 link Amazon na primeira menção do produto. Se houver muito o que cobrir (>5-6 frases), divida em 2 parágrafos: primeiro features-chave, segundo specs gerais (peso, dimensões, conectividade, garantia).</p>

<p><strong>Pontos de atenção:</strong> contrapartidas reais, limitações, contextos onde NÃO comprar. SEM link de afiliado neste parágrafo (não tenta vender no parágrafo de objeções).</p>

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
- ✓ "Custa cerca de R$ X e rende Y páginas por kit" (o dado concreto no lugar de "custo-benefício se destaca")
- ✓ "Uma limitação a considerar é..."
- ✓ "O aparelho tem {feature} / faz {ação} em {condição}" (verbo literal, não "entrega")

> **Sobre citar o fabricante**: regra diferente de citar comprador/Amazon. Spec factual (rendimento, velocidade, economia) vai afirmado direto, sem "segundo X". Atribuir só vale pra recomendação/calibração/política do fabricante (ex: "a HP recomenda 50-100 págs/mês"). Ver Armadilha 7 abaixo pra régua completa.

## Voz natural (régua transversal, canon Marcelo 2026-08-15 — bloco IDÊNTICO nas 5 skills de criação e nos prompts canônicos do painel)

Especialista explicando a um amigo, cumprido com **simplicidade**, não com efeito. Pergunta-teste: *"um amigo que não entende disso entenderia e saberia o que fazer?"* Sem jargão corporativo, sem formalidade institucional, **sem sacada**.

O que faz texto soar como IA não é gíria nem termo técnico: é **palavra comum usada fora do sentido do dicionário** ("resolver a casa", "dar conta da poeira", "transformar a limpeza numa produção", "o aparelho pede tomada", "a conta da potência vem no peso"), quase sempre frase feita do inglês vertida (*make a production, handle, delivers, covers, calls for, the math*). Cada palavra é comum, então lista de termo não pega; a régua é uma **classe**:

1. **Sujeito concreto + verbo no sentido do dicionário.** Aspirador aspira, impressora imprime, bateria dura, produto custa/tem/funciona. Objeto, preço, peso ou potência NÃO "resolvem, dão conta, entregam, seguram, pedem, exigem, aguentam, sustentam, encaram, cobram, juntam, trabalham, cobrem, viram, brilham". Teste: é o sentido em que você usaria a palavra falando com um cliente?
2. **Substantivo literal.** Nada de "a conta", "degrau", "piso", "porta de entrada", "pacote", "proposta", "produção", "remanejo", "trunfo", "fôlego" como figura. Diga o que é (preço, faixa de preço, o mais barato, conjunto de recursos).
3. **Sem frase-sacada.** Nada de "não é X: é Y", "o que X é Y", "é aí que…", fecho com dois-pontos que "revela". Dois-pontos só para explicação ou lista.
4. **Repita a palavra certa.** "Aspira" 3× é normal. Chavão é frase-molde repetida, não palavra exata. **Nunca troque a palavra certa por sinônimo figurado para "variar"** (limpar → "resolver a casa" → "dar conta" é exatamente o defeito).
5. **"para", não "pra"**, no texto público.
6. **Frase de até ~30 palavras.** ", então" e ", o que" no máximo 1 por parágrafo.
7. **Fecho de parágrafo = frase curta de fato ou recomendação direta** ("é a melhor opção para casa pequena"), sem rótulo de público engatado ("é a escolha de quem", "faz sentido para quem", "é o que resolve").
8. **Ênfase só com dado.** Sem "de verdade", "bastante", "com folga", "de sobra", "justamente", "honesto/a" como muleta.
9. **Continuam valendo (v1.32):** rótulo de categoria só se existe no varejo (teste-da-Amazon: "máquina de trabalho"→"impressora de escritório", "preço de custo-benefício"→"preço justo"); elipse de categoria LIBERADA ("a barata", "a laser", "as de tanque"); sem meta-SEO (não comente a busca do leitor); sem jargão financeiro/burocrático ("desembolso"→"preço"); sem atribuição elíptica ("conta da Epson"→número direto); sem antropomorfismo ("não se cansa", "no batente"); no máximo 1 expressão coloquial leve, e só se for a forma mais direta.

10. **Teto mecânico da mesma régua**: `docs/painel/_data/chavoes-por-nicho.json` → `_genericos.naturalidade_max` (daqui 2, pede 3, resolve 3, entrega 3, de verdade 1, trunfo/fôlego 1…) e `naturalidade_banidos` (0). A auditoria CONTA e reporta, mas desde 2026-09-05 teto numérico **não reprova**: use como sinal de que você está martelando a mesma palavra, nunca como motivo pra trocar a palavra certa por outra (`naturalidade_banidos` e tetos **0** seguem duros). Ver `_meta.regra_de_ouro` do JSON.

**Antes de gravar, releia cada parágrafo: "uma pessoa escreveria assim?"** O trecho que soa esperto, simplifique.

| ❌ Como saiu (casos reais) | ✓ Como uma pessoa escreve |
|---|---|
| a impressora resolve o mês inteiro com um kit | um kit de tinta imprime cerca de 4.500 páginas |
| sem transformar a troca de tinta numa produção | sem muito esforço |
| a conta do rendimento vem no preço do kit | o rendimento alto tem um custo: o kit é caro |
| a creatina pede coqueteleira | a creatina dissolve melhor com coqueteleira |
| Se não tem, ela é a que resolve. | Se não tem, ela é a melhor opção. |
| O tanque não se cansa. | O tanque de tinta rende o mesmo até o fim. |

⚠️ **Os exemplos são de outra categoria de propósito e NÃO podem ser reusados.** Se a frase que você escreveu está nesta tabela (ou nos exemplos de shortDescription), reescreva com o fato do SEU produto. Caso real (melhoraspirador, 15/08): a linha "em casa grande você ainda troca de tomada algumas vezes", que era exemplo aqui, saiu copiada em 5 lugares do artigo — 11 sub-agents lendo o mesmo exemplo convergem nele.

## Como usar a bíblia

- `pontosFortes` / `pontosFracos`: base dos pros/cons. NÃO invente. **DESTILE ao copiar** — ver "Operação de destilação" abaixo.
- `angulosConversao`: ângulos editoriais = **matéria-prima, NÃO texto pronto**. Use o `tema` pra estruturar parágrafos do `fullReview` ("para quem é", "por que gostamos") e as `frases` como **fonte do FATO**, nunca como fraseado a colar. **DESTILE o registro** — ver categoria E em "Operação de destilação". As frases de ângulo são escritas em registro de venda e frequentemente vêm coloquiais ("no tempo do café passar", "sem precisar ficar de olho", "fininho"); colar verbatim importa a gíria direto pra página. A bíblia é fonte de **fato**, não de **voz**.
- `sentimentoCompradores`: insights — **REESCREVA** como observação editorial, NÃO cite compradores. Ex: "compradores citam custo-benefício" → "O custo-benefício se destaca por {dado da bíblia}".
- `dicasAcionaveis`: incorpore se fizer sentido no `fullReview` ou como item em `cons` (quando for limitação contextual).
- `dadosInconsistentes` + `decisaoEditorial`: SE existir, **RESPEITE**. A decisão editorial diz qual valor usar e qual ignorar.
- `observacoesAgente`: notas internas pra você. Leia.
- `avisosAoAgente` / `observacoesAgente`: instruções/observações do humano. **Leia e respeite.**
- **Produto descontinuado** (régua canon): se `avisosAoAgente`/`observacoesAgente` indicarem que o produto **saiu de linha / foi descontinuado** com uma sucessora, **VOCÊ coloca o banner**: (1) **SETE o campo `descontinuado: { asin, nome }` no frontmatter do `.mdx`** — `nome` = nome completo da sucessora (com marca); `asin` = ASIN da sucessora. Se o aviso só trouxer o nome, **resolva o ASIN** na bíblia (`docs/biblias-v2/`) ou na página (`sites/{site}/src/content/products/`) da sucessora. Isso dispara o banner âmbar "produto descontinuado" + `schema.org/Discontinued` + link tag-aware da sucessora. (2) Escreva a review **honesta**: não venda como a compra atual; a sucessora é a recomendação corrente. Sem hedge de "confirmar disponibilidade" — descontinuado é descontinuado.
- `specsAmazon` + `doFabricante` + `conteudoBrutoFabricante`: fontes pra `specs` e claims numéricos no `fullReview`. Peso editorial varia por fonte — ver "Peso por fonte" abaixo.

## Subtitle humano = ângulo do review (v1.34.0, canon Marcelo 2026-06-10)

Quando o stub já vem com `subtitle` (e/ou `badge`) preenchido pelo editor humano (modal "+ Adicionar produto" do painel), isso NÃO é placeholder: **é a direção editorial** — "normalmente é o ângulo que queremos que você aborde o produto" (Marcelo).

1. **Ângulo VINCULANTE**: o review inteiro aborda o produto por esse ângulo — o "Para quem é" deriva dele (reforça a régua v1.20.1, que já manda derivar o claim do subtitle), os pros priorizam o que o sustenta.
2. **Texto MELHORÁVEL**: você tem liberdade de polir o subtitle (concisão, clareza, régua 10-150 chars, title case) — mas o SENTIDO não muda. Trocar "tanque pra alto volume" por "multifuncional compacta" = violação; polir "boa pra muito volume" → "Tanque de alto volume pra rotina pesada" = ok.
3. **Subtitle vazio** = comportamento atual (criar do zero a partir da bíblia + badge).
4. **NUNCA descartar silenciosamente** o ângulo humano. Se a bíblia CONTRADIZ o ângulo (ex: subtitle diz "a mais rápida" e a bíblia mostra que não é), NÃO grave nada conflitante: pare e pergunte ao usuário.

Histórico: até v1.33 a skill regenerava o subtitle sem ler o existente (~80% dos subtitles humanos sobrescritos; os ~20% "mantidos" eram convergência por acaso). O badge sempre teve esse tratamento (var + hint editorial) — esta régua espelha pro subtitle.

## Operação de destilação bíblia → .mdx (CRÍTICO)

A bíblia carrega claims COM marcadores de procedência (`fonte: "specs"`, "conforme declarado pelo fabricante", "confirmado nos alérgenos"). É correto e útil internamente — rastreabilidade evita invenção. **O .mdx público é destilado**: droppa marcadores que viraram ruído burocrático.

⚠ Destilar é DUAS coisas, não uma: (1) dropar o marcador de procedência (A-D) **e** (2) reescrever o REGISTRO quando a bíblia vier coloquial (E). As categorias A-D só cobrem (1) — um trecho pode não ter marcador nenhum e ainda assim estar impróprio pro público por causa do fraseado. Sem (2), a gíria da bíblia entra na página sem disparar nenhum check.

**5 categorias de claim — como destilar cada:**

| Tipo | Bíblia (raw, OK) | .mdx destilado |
|---|---|---|
| **A) Fato verificável simples** | "Sem glúten confirmado nos alérgenos da Amazon" | "Sem glúten" |
| **B) Claim do fabricante repetível** | "Forma triglicerídeo, apontada pelo fabricante como mais absorvível" | "Forma triglicerídeo, considerada mais absorvível" |
| **C) Claim institucional / PR** | "Marca tradicional brasileira segundo o próprio fabricante" | "Marca brasileira" (ou omite se não agrega) |
| **D) Voz comprador implícita** | "Cápsulas sem sabor segundo relatos de compradores" | "Cápsulas sem sabor" |
| **E) Registro coloquial da bíblia** | "700W pra tostar as fatias no tempo do café passar" · "as fatias sobem sozinhas, sem precisar ficar de olho" · "não só pão de forma fininho" | "700W nas duas fatias" · "elevação automática ao fim do ciclo" · "aceita fatias de espessuras diferentes" (NÃO "potência que dá conta das fatias": trocar a gíria da bíblia por verbo figurado é o mesmo defeito em outra roupa) |

**Categoria E — por que existe** (canon 2026-07-16): `angulosConversao` (e às vezes `sentimentoCompradores`) vêm em **registro de venda**, coloquial de propósito, porque servem de matéria-prima pra copy. Colar verbatim importa a gíria: no lote cozinhaideal de 9 páginas, 8 saíram com 6 a 9 coloquialismos contra o teto de 1 — e dois auditores independentes rastrearam a origem pra frases **literais** da bíblia ("no tempo do café passar", "sem precisar ficar de olho", "fininho"). O sub-agent não estava improvisando: a régua mandava "usar" o ângulo e ele usou. **Pegue o FATO da frase de ângulo e reescreva em voz analítica.** Se você copiou ≥5 palavras seguidas de uma `frase` de `angulosConversao`, você NÃO destilou.

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
- **Voltagem — não citar (régua dura, canon 2026-06-28; endurecida 2026-06-29)**: **NÃO cite voltagem — nem na spec nem na prosa.** Sem "110V", "220V", "127V", "vendido em versões 110V e 220V", nem "bivolt". A voltagem muda por ASIN (o mesmo modelo tem versão 110 e 220), o comprador escolhe no anúncio → **default é omitir** (inclusive não criar a row "Voltagem" no specs). ÚNICA exceção: o `specsAmazon` do ASIN diz "bivolt" (ou faixa contínua "100-240V"/"110-220V") EXPLÍCITO → aí pode afirmar bivolt. NUNCA infira bivolt de copy de potência "1800W 110V \| 2000W 220V" / "110/127V e 220V" = SKUs SEPARADOS, não bivolt. **Aparelho de aquecimento de alta potência (air fryer, ferro, secador, chaleira) é voltagem única por design** — nunca cita voltagem. Exceção de classe (bivolt comum, citar só se a ficha confirmar): impressora e cooktop a gás. Caso real: air fryers afirmados bivolt erradamente (2026-06-28).

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

**Fonte da verdade é ESTA `SKILL.md`** (canon 2026-08-15, ver "Régua comum das auditoras" em `docs/PADROES.md`). O `docs/painel/_data/agent-prompts.json` → `ops.create_product_page / rewrite_product` é **espelho** usado pelos botões do painel (pode defasar; ao mudar régua aqui, refletir lá no mesmo commit quando a mudança afeta o output). Os endpoints legados `generate-*/rewrite-*/create` do painel foram removidos em 2026-05-27; `agent-config.html` virou `editorial.html`. Listas, regex e tetos vivem em `chavoes-por-nicho.json` — cite a chave, não copie a tabela.


## Exemplo de invocação

```
preenche a página individual da L3250 no melhorimpressora
preenche o produto epson-ecotank-l3250 do melhorimpressora
preenche melhorimpressora/epson-ecotank-l3250
preenche B098YHFT9S no melhorimpressora
```

Args canônico que invoco: `Skill(skill="pagina-produto-criar", args="melhorimpressora/epson-ecotank-l3250")`.

### Auto-check de concordância PT-BR (régua v1.19.0, canon 2026-05-28)

**Bug-class real** (batch melhorpretreino v1.17-1.18): substituições mecânicas (BCAAs→aminoácidos, parestesia→formigamento, fórmula→composição) **NÃO reconcordaram** plural/gênero/artigo (11+ casos em 2 artigos). Antes de gravar, grep dos padrões abaixo em cada campo; achou → corrija antes de gravar.

| Padrão | Fix |
|---|---|
| `composiçãos`, `combinaçãos`, `porçãos`, `opçãos` | `composições`, `combinações`, `porções`, `opções` |
| `a produto`, `a formigamento`, `a ingrediente`, `esta ativo` | `o produto`, `o formigamento`, `o ingrediente`, `este ativo` |
| `o fórmula`, `o dose`, `o composição`, `este tolerância` | `a fórmula`, `a dose`, `a composição`, `esta tolerância` |
| `produto ampla`, `produtos elaboradas`, `formula natural` | `fórmula ampla`, `produtos elaborados`, `fórmula natural` |
| `disponíveis no em 2026` | `disponíveis em 2026` |
| `Pra a maioria/primeira/melhor` | `Para a maioria/primeira/melhor` |
| `as produtos`, `os fórmulas`, `as ingredientes` | gênero certo |

Regex de referência (se quiser rodar): `\b(composição|combinação|porção|opção|posição)s\b` · `\b(a|na|da|esta|nesta|essa) (produto|formigamento|ingrediente|ativo|estímulo|composto|atleta)\b` · `\b(o|no|do|este|neste|esse) (fórmula|dose|porção|composição|combinação|tolerância)\b` · `\bPra a \w+`.

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
| ❌ Corporativo | ✓ Direto (literal, sem molde) |
|---|---|
| "O diferencial central é a fórmula sem aditivos" | "A fórmula não tem aditivos" (NÃO "o grande ponto é…": virou molde em 289 páginas) |
| "Posicionamento de mercado premium" | "Linha mais cara" |
| "Atende ao segmento de X" | "Serve para quem X" |

### Auto-check de capitalização + duplicação (régua v1.18.3, canon 2026-05-28)

Substituições mecânicas causam (caso real melhorpretreino `a72e7d9`): **14a** duplicação contígua (`sem empilhar suplementos sem empilhar suplementos`; regex `([a-zA-ZÀ-ÿ\s]{8,40})\1`) · **14b** bullet começando com minúscula dentro de `<strong>` (`<strong>aminoácidos…`) · **14c** minúscula após ponto em texto editorial (`(maior dose). pra emagrecer`; ignorar URLs e listas numeradas). Rodar em shortDescription, fullReview, pros, cons, specs.value antes de gravar; achou → corrija.


## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), a validação fica editorial — eu (modelo) sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial (subtitle de 9 chars, fullReview de 780 chars, etc).

Mitigação: depois de gerar, conferir tamanhos antes de salvar. Se algum estiver no limite, expandir/encurtar com cuidado.

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
