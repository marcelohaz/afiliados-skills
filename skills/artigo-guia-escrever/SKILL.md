---
name: artigo-guia-escrever
description: Escreve o guideContent (HTML "Como escolher") do artigo + análise de concorrentes reusável por keyword. Aceita URL do painel (editor-artigo.html?site=X&slug=Y) OU args canônicos site/slug. Quando user cola "Como escolher" de 1-3 concorrentes na mensagem, skill ANALISA (tópicos, palavras-chave, gaps, clichês a evitar) + GERA guide com topical map paritário + extras + SALVA análise em docs/painel/_data/competitor-analyses/{keyword-slug}.md pra reuso. Próximas execuções na mesma keyword (qualquer site) auto-carregam análise existente. Régua dura — HTML educativo (não comercial), abertura com H2 "Como escolher {keyword}", 3-6 parágrafos, 500-15000 chars, allowlist h2/h3/p/ul/ol/li/strong/em/a, SEM links Amazon, SEM travessão, linkagem interna 0-3 só pra peer articles reais do site. Substitui só o campo guideContent — frontmatter, produtos e body ficam intactos. Backup + commit + push + sync VPS.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida — fluxo natural depois de abrir o editor):
- `https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio`
- Extrai `site` e `slug` do query string

**B) Args canônicos**:
- `melhorimpressora/melhor-impressora-custo-beneficio`

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B (split por `/`).

**Instrução opcional**: se o prompt natural do user contém algo tipo "mais conciso", "enfatize tanque de tinta", "sem subseções" → eu extraio como instrução adicional e uso no prompt. Se for só "escreve o guia do X" → modo padrão.

**Concorrentes (texto completo do "Como escolher") opcionais**: 2 modos:

1. **Análise existente**: se já existe `docs/painel/_data/competitor-analyses/{keyword-slug}.md`, eu CARREGO automaticamente — você não precisa colar nada de novo. Isso permite reuso entre sites diferentes que miram a mesma keyword (a SERP é igual, os concorrentes são iguais).

2. **Primeira vez** (análise ainda não existe pra essa keyword): você cola 1-3 textos completos de "Como escolher" de concorrentes. Eu **analiso** (tópicos, palavras-chave, ângulos, gaps, o que evitar), **gero o guia**, e **salvo a análise** em `docs/painel/_data/competitor-analyses/{keyword-slug}.md` pra reuso futuro.

**Override**: se a análise existe mas você quer regenerar com concorrentes novos (SERP mudou), cole textos novos junto com o comando — eu sobrescrevo (backup antes).

# Escrever guia "Como escolher" do artigo

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:generate_guide`. O conteúdo essencial está duplicado abaixo pra autocontenção; em caso de divergência, o prompt canônico ganha.

Você é o curador editorial do **guide** do artigo — a seção "Como escolher {keyword}" que complementa o comparativo. O guide vive **dentro do frontmatter do `.mdx`**, no campo `guideContent` (block scalar YAML `|` com indent de 2 espaços, desde Etapa B/B.2).

Sua função é gerar **HTML educativo** que ajuda o leitor a entender CRITÉRIOS de escolha (não a comparar produtos específicos — isso é função da tabela e dos reviews). O guide é a peça SEO complementar: leitor educado converte melhor.

## Pré-requisitos

- O `.mdx` do artigo já existe em `sites/{site}/src/content/reviews/{slug}.mdx`. Se não, abortar com orientação pra criar via painel ("✨ Criar artigo" no site detail → `make-reviews-stub`).
- O artigo tem **pelo menos 1 produto** no lineup (`products: []` vazio = abortar — guide sem categoria concreta fica vago).
- Bíblias dos produtos do artigo estão em `docs/biblias-v2/{ASIN}.json`. Se alguma faltar, rodar `bun scripts/sync-biblias-r2.ts --apply` antes (skill avisa e aborta se faltar).
- `affiliateTag` em `sites/{site}/src/config.ts` é conhecida (pode ser vazia — guide NÃO PRECISA ter links Amazon, então tag vazia OK).

## Invariantes

- **Nunca toque em nada além do campo `guideContent`** do frontmatter. Title, description, keyword, products, intro do body, tudo intacto. Só substitui o block scalar do `guideContent` (ou insere se ainda não existir).
- **HTML, não markdown.** Diferente da intro (que é markdown puro), o guide é HTML.
- **Allowlist de tags**: `<h2>`, `<h3>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<a>`. Tudo mais é proibido: `<h1>` (artigo já tem H1 no title), `<script>`, `<iframe>`, `<style>`, `<img>`, `<table>`, `<form>`, `<button>`, `<div>`, `<span>` (visual fica pro CSS).
- **500 a 15000 chars** no total do HTML.
- **SEM links Amazon.** Afiliados ficam só nos cards do `.mdx` (subtitle, fullReview, pros, cons). Guide é educativo, sem CTA de compra.
- **Linkagem interna 0-3 links** pra **peer articles reais do mesmo site** — slugs verificados antes. Formato: `<a href="/{slug}/">texto descritivo</a>`. Sem `target="_blank"`, sem `rel="nofollow"` (links internos passam autoridade).
- **Sem travessão (—).** Use vírgula, ponto, dois pontos ou parênteses.
- **Sem superlativos sem evidência** ("o melhor disponível", "incomparável", "imbatível"). "Excelente", "ótimo" OK se contextualizado.
- **NÃO mencionar marcas/modelos/ASINs específicos.** Linguagem GERAL (critérios, perfis, panorama). Marcas vão na tabela e nos reviews.
- **NÃO inventar dados.** Se o guide precisar de número, vem de alguma bíblia.
- **NÃO citar compradores/reviews/avaliações/Amazon** como entidade (mesma regra de toda voz editorial do projeto, `02-estilo-editorial.md`).
- **Tom EDUCATIVO, não comercial.** Guide explica COMO decidir, não vende produto.

## Fluxo

1. **Parse args**: detecta URL vs canônico, extrai `site` e `slug`. Valida `[a-z0-9-]+` em ambos.

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   git stash push -m "skill-artigo-guia-escrever-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Painel VPS commita+pusha automaticamente quando user cria/edita conteúdo na UI; Mac local pode estar 5-30s atrás. Sem este pull, skill pode ler estado stale e abortar com falso "X não existe localmente". Se pull falhar (rede offline, conflito), seguir mesmo assim.

2. **Read `.mdx`**: `Read sites/{site}/src/content/reviews/{slug}.mdx`. Se 404, abortar.

3. **Parse frontmatter** mentalmente:
   - `title` (vira o "Como escolher {keyword}" da abertura — extrair só a parte da keyword, sem o ":")
   - `keyword` — se ausente, fallback: `title.split(':')[0].toLowerCase().trim()`
   - `products: []` — extrair ASINs pra carregar as bíblias + contar quantos pro contexto
   - `guideContent` atual — pode ser:
     - Ausente (campo nunca foi escrito; vou inserir)
     - `guideContent: ''` (inline vazio; vou substituir pelo block scalar)
     - `guideContent: |\n  <h2>...` (block scalar com conteúdo; vou substituir TODO o range)

4. **Read bíblias** dos produtos: `Read docs/biblias-v2/{ASIN}.json` pra cada ASIN. Se alguma faltar, abortar com mensagem orientando rodar `bun scripts/sync-biblias-r2.ts --apply`.

5. **Read `affiliateTag`**: `sites/{site}/src/config.ts` → regex `/affiliateTag:\s*['"]([^'"]*)['"]/`. Pode ser vazia (OK pra guide).

6. **Listar peer articles** do site (pra linkagem interna):
   - `ls sites/{site}/src/content/reviews/*.mdx` (ou Glob)
   - Pra cada `.mdx` (excluindo o próprio): `Read` rápido pra extrair `title` e `slug` (= filename sem `.mdx`)
   - Resultado: array `[{slug, title}]` dos OUTROS artigos do site
   - Se vazio (este é o 1º artigo do site): NÃO incluir links internos no guide gerado

7. **Detectar instrução opcional** no prompt do user (paridade com outras skills):
   - "mais conciso" / "enfatize tanque de tinta" / "sem subseções" / "com foco em iniciantes" → extrai como instrução
   - Sem instrução clara → modo padrão

8. **Análise de concorrentes** (3 cenários):

   ### Cenário A — análise existe E user NÃO colou novos concorrentes
   - `Read docs/painel/_data/competitor-analyses/{keyword-slug}.md` (slugify do `keyword` do frontmatter — ver função slugify abaixo)
   - Carrega como contexto rico (topical map, gaps, o que evitar, ângulos)
   - **NÃO regera a análise** (preserva a existente)
   - Reporta no chat: "📊 Análise de concorrentes carregada de `_data/competitor-analyses/{kw}.md` (gerada em DD/MM/YYYY)"

   ### Cenário B — análise NÃO existe + user colou textos de concorrentes
   - Cada texto truncado em 16k chars (mais generoso que os 8k antigos — análise rica)
   - Eu analiso os textos e produzo a análise estruturada (passo 10b)
   - Usa como topical map pra gerar o guide
   - Cria o `.md` da análise depois (passo 10b)

   ### Cenário C — análise NÃO existe E user NÃO colou nada
   - Fallback: gera só com bíblias + título (comportamento original sem concorrentes)
   - Avisa no chat: "⚠ Sem análise de concorrentes pra essa keyword. Pra otimizar SEO, rode novamente colando textos do 'Como escolher' de 1-3 concorrentes (Buscapé/Zoom/etc)."

   ### Slugify do keyword
   ```js
   // Espelha agent-validators.ts:128
   function slugifyKeyword(s) {
     return s
       .normalize('NFD').replace(/[\u0300-\u036F]/g, '') // remove acentos
       .replace(/\+/g, '-plus')
       .toLowerCase()
       .replace(/[^a-z0-9]+/g, '-')
       .replace(/^-+|-+$/g, '');
   }
   // "Melhor Impressora Custo Benefício" → "melhor-impressora-custo-beneficio"
   ```

9. **Compor contexto pra geração**:
   - Title do artigo + keyword
   - Lista de ASINs (count + identidade.nome de cada bíblia pra entender categoria)
   - Bíblias completas (pra entender critérios técnicos da categoria)
   - Peer articles list (slug + título de cada um — formato pro prompt)
   - **Análise de concorrentes** (passo 8) — topical map + gaps + ângulos
   - Instrução opcional

10. **Gerar o guide HTML** seguindo a régua editorial (ver seção abaixo). Foco em CRITÉRIOS, não em produtos. Cobertura paritária com tópicos do concorrente + extras dos gaps identificados.

10b. **Gerar/atualizar análise de concorrentes** (só nos cenários B e overrides):

    Conteúdo da análise (estrutura obrigatória — ver seção "Formato da análise" abaixo):
    - Tópicos cobertos por cada concorrente (tabela check/cross)
    - Ângulos editoriais identificados (preço-first, técnico, perfil-first, etc)
    - Palavras-chave/jargão recorrente (com nota: usar / evitar)
    - **Clichês ou claims fracos a EVITAR** (assertivas vagas, superlativos sem dado)
    - **Gaps**: o que NINGUÉM cobriu — sua oportunidade
    - Recomendações editoriais pra próximos artigos com mesma keyword

    Backup se já existe: `docs/painel/.painel-backups/{day}/competitor-analysis-{keyword-slug}-{HHMMSS}.md`

    Salvar: `docs/painel/_data/competitor-analyses/{keyword-slug}.md`.

    Criar `_data/competitor-analyses/` se não existir.

11. **Validar mentalmente** antes de salvar:
    - 500-15000 chars
    - Abertura: `<h2>Como escolher {keyword}</h2>` (ou variante natural com a keyword na frase)
    - HTML allowlist OK (Grep mental por tags fora da lista)
    - 0-3 links internos: cada `href="/{slug}/"` aponta pra slug REAL da peer articles list
    - ZERO links Amazon: nenhum `href` contém `amazon.com` ou `amzn.to`
    - Sem travessão `—` nem `–`
    - Sem `<h1>` (artigo já tem H1 no title)
    - Sem `<img>`, `<table>`, `<script>` etc
    - Sem citação a marca/modelo/ASIN específico
    - Sem citação a "compradores"/"reviews"/"avaliações"

12. **Backup** ANTES de sobrescrever (paridade exata com pattern do painel, server.ts:4994):
    ```bash
    DAY=$(date +%Y-%m-%d); TIME=$(date +%H%M%S); SITE={site}; SLUG={slug}
    PROJ=$(pwd)  # raiz do projeto — sempre cwd inicial do Claude Code nesta sessão
    mkdir -p "$PROJ/docs/painel/.painel-backups/$DAY"
    # Extrai HTML atual do guideContent (se existir) pra salvar como .html.
    # Reusa o helper canônico do painel pra extrair sem indent — mesmo formato
    # que o painel produz em /guide-save, então restore via UI funciona igual.
    bun -e "import { readGuideContent } from '$PROJ/docs/painel/_lib/article-guide.ts'; const r = readGuideContent('$PROJ/sites/$SITE/src/content/reviews/$SLUG.mdx'); if (r.exists && r.content.length > 0) { Bun.write('$PROJ/docs/painel/.painel-backups/$DAY/guide-$SITE-$SLUG-$TIME.html', r.content); }"
    ```
    **Pattern do nome obrigatório**: `guide-{site}-{slug}-{HHMMSS}.html`. Sem isso, o card "Histórico de versões" no editor-artigo não reconhece o backup (regex em `backups.ts:99`).
    
    Se `guideContent` atual está vazio ou ausente, **NÃO criar backup vazio** — o `if (r.exists && r.content.length > 0)` no script já cuida disso (não escreve nada se vazio).

13. **Aplicar via Edit tool** no `.mdx` (escolha um caminho):
    
    **Caso A — `guideContent` já existe** (block scalar com conteúdo):
    - `old_string` = bloco YAML inteiro:
      ```
      guideContent: |
        <h2>...</h2>
        <p>...</p>
        ...
      ```
      (header + todas as linhas indentadas com 2 espaços; até a próxima linha não-indentada que NÃO seja vazia)
    - `new_string` = novo bloco com mesma estrutura (`guideContent: |\n  <html-line>\n  <html-line>...`)
    
    **Caso B — `guideContent` ausente OU `guideContent: ''` inline**:
    - `old_string` = a linha imediatamente antes do `---` de fechamento do frontmatter (ex: linha do `products:` com seus items, ou alguma outra última linha do YAML) + `\n---`. Inclui contexto suficiente pra match único.
    - `new_string` = mesma linha de contexto + `\nguideContent: |\n  <html-line>\n  <html-line>...\n---`
    
    **CRÍTICO sobre indent**: cada linha do HTML dentro do block scalar precisa começar com **exatamente 2 espaços**. Linhas em branco entre parágrafos HTML ficam sem indent (string vazia). Sem indent = YAML inválido = build do Astro quebra.
    
    Exemplo de bloco bem formatado:
    ```yaml
    guideContent: |
      <h2>Como escolher impressora multifuncional</h2>
      <p>A decisão começa pela frequência de uso...</p>
      <h3>Tanque de tinta vs cartucho</h3>
      <p>...</p>
    ```

14. **Git add + commit + push**:
    ```bash
    # .mdx do artigo SEMPRE entra. Análise .md entra SE foi criada/atualizada.
    git add sites/{site}/src/content/reviews/{slug}.mdx
    if [ -f docs/painel/_data/competitor-analyses/{keyword-slug}.md ] && \
       git diff --quiet HEAD -- docs/painel/_data/competitor-analyses/{keyword-slug}.md; then
      :  # análise não mudou, não precisa commitar
    else
      git add docs/painel/_data/competitor-analyses/{keyword-slug}.md 2>/dev/null || true
    fi
    git commit -m "feat({site}): guia 'Como escolher' de {slug} escrito via skill (+ análise de concorrentes pra keyword '{keyword}')" \
      -m "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
    git push origin main
    ```

15. **Disparar git pull no painel da VPS**:
    ```bash
    bash scripts/painel-vps-pull.sh
    ```
    Falha graciosamente se `.env.painel-skills` não existir.

16. **Reportar no chat**:
    - char count do HTML do guide + número de parágrafos + lista de links internos
    - path do `.mdx` salvo
    - **Coverage report** (se análise foi usada):
      - "Cobri N/M tópicos do concorrente"
      - "Adicionei K tópicos extras (das bíblias / gaps): X, Y, Z"
    - Se análise foi criada/atualizada: path do `_data/competitor-analyses/{kw}.md` salvo
    - Se análise foi carregada de existente: lembrete "essa análise reusa em outros sites com mesma keyword"

## Formato da análise de concorrentes

Estrutura obrigatória do `_data/competitor-analyses/{keyword-slug}.md`:

```markdown
# Análise de concorrentes: {keyword}

- **Última atualização:** {YYYY-MM-DD HH:MM}
- **Gerada via skill:** /artigo-guia-escrever
- **Artigo origem:** {site}/{slug}
- **Concorrentes analisados:** {nome1}, {nome2}, {nome3}

## 📋 Tópicos cobertos por concorrentes

| Tópico | {Concorrente1} | {Concorrente2} | {Concorrente3} |
|---|---|---|---|
| {Tópico A} | ✓ | ✓ | ✓ |
| {Tópico B} | ✓ | ✗ | ✓ |
| ...

## 🎯 Ângulos editoriais identificados

- {Concorrente1}: {ângulo principal, 1 frase}
- {Concorrente2}: {ângulo principal, 1 frase}
- {Concorrente3}: {ângulo principal, 1 frase}

## 🔑 Palavras-chave / jargão da categoria

**Usar** (relevantes pro SEO da keyword):
- "{termo X}" — usado por 3/3 concorrentes
- "{termo Y}" — técnico mas claro
- ...

**Evitar** (vagos, clichês, ou comprometem voz analítica):
- "{termo Z}" — superlativo sem dado
- "{termo W}" — comercial demais
- ...

## 🚫 Clichês / claims fracos pra EVITAR no guide

- {Claim 1 que aparece em 2+ concorrentes mas é vago/inútil}
- {Claim 2}
- ...

## 💡 Gaps — o que NINGUÉM cobriu

(Sua oportunidade SEO — incluir esses tópicos no guide pra superar a SERP)

- {Gap 1: tópico relevante que está nas bíblias mas concorrentes ignoraram}
- {Gap 2}
- ...

## 📌 Recomendações pra próximos artigos com mesma keyword

- Cobrir os {N} tópicos comuns (paridade)
- Adicionar gaps: {lista resumida}
- Tom recomendado: {síntese editorial 1-2 frases}
- Evitar: {síntese de armadilhas}
```

**Tamanho**: livre — 500-5000 chars típico. Não há limite duro, mas mantenha legível pra revisar manualmente no painel.

**Validações antes de salvar**:
- Encoding UTF-8 (acentos)
- Sem links Amazon (não é review, é análise editorial)
- Sem travessão `—` (consistência com outras escritas)
- Tabela markdown válida (colunas batem com header)

## Régua editorial — ESTRUTURA OBRIGATÓRIA

### Abertura: H2 com a keyword

Primeira tag SEMPRE é `<h2>` contendo a keyword principal. Padrão canônico:

- `<h2>Como escolher {keyword}</h2>`

Variante natural OK se a frase fica forçada (ex: keyword muito longa ou já no infinitivo). Quando em dúvida, use o padrão canônico — paridade com o que o painel gera.

**NUNCA** `<h1>` (artigo já tem H1 no title). **NUNCA** começar com `<p>` antes do H2.

### Corpo: 3-6 parágrafos `<p>`

Cobrem **critérios objetivos de decisão**. Exemplos do que vai aqui:

- Tecnologias da categoria (ex: tanque de tinta vs cartucho, hidrolisada vs concentrada, OLED vs LCD)
- Perfis de uso (ex: doméstico leve vs profissional, iniciante vs avançado, uso ocasional vs intenso)
- Specs técnicos que realmente importam (ex: rendimento, velocidade, conectividade — generalizando o que aparece nas bíblias)
- Pegadinhas comuns (ex: "atenção ao kit de cartuchos, não ao preço do equipamento sozinho")
- O que verificar antes de comprar (ex: voltagem, garantia, compatibilidade)

**Cada parágrafo 2-5 frases.** Sem walls of text. Sem 1-frase-parágrafo (vira lista disfarçada).

### Subseções H3 (opcionais)

Use `<h3>` se faz sentido segmentar o tópico. Bom uso:

```html
<h3>Tanque de tinta vs cartucho</h3>
<p>...</p>

<h3>Conectividade e Wi-Fi</h3>
<p>...</p>
```

Mau uso (subseção redundante):

```html
<h2>Como escolher impressora</h2>
<h3>Introdução</h3>  <!-- ❌ redundante, o H2 já abre o tópico -->
```

**Máximo 4 subseções H3.** Mais que isso vira índice, não guide.

### Listas (opcionais)

`<ul>` ou `<ol>` quando faz sentido enumerar critérios discretos:

```html
<p>Antes de comprar, verifique:</p>
<ul>
  <li>Voltagem (bivolt ou específica)</li>
  <li>Tipo de filtro (HEPA, lavável, descartável)</li>
  <li>Garantia oficial Brasil</li>
</ul>
```

**Itens objetivos e curtos**, não frases longas. Se vai ter 1-2 itens só, é melhor virar prosa.

### Fechamento (opcional, 1 parágrafo)

Pode ter um parágrafo final que conecta o guide ao comparativo, tipo:

```html
<p>Com esses critérios em mente, fica mais fácil avaliar a tabela acima e escolher o modelo que melhor encaixa no seu perfil.</p>
```

**Sem CTA de compra** ("compre agora", "clique aqui pra comprar"). Sem links Amazon.

## Linkagem interna — peer articles do site

A skill carrega `[{slug, title}]` dos OUTROS artigos do mesmo site (passo 6). **0-3 links** no guide inteiro, distribuídos ao longo do texto (não concentrar no fim).

### Formato exato

```html
<a href="/{slug}/">texto âncora descritivo</a>
```

- Slug entre barras (`/` no início, `/` no fim) — path absoluto
- Texto âncora descritivo, NÃO "clique aqui" / "veja aqui" / "saiba mais"
- SEM `target="_blank"` (links internos abrem no mesmo tab)
- SEM `rel="nofollow"` (queremos passar autoridade SEO)

### Exemplos bons

```html
<p>Para uso doméstico leve, o foco muda pra cartucho — veja nossa análise das <a href="/melhor-impressora-multifuncional/">multifuncionais</a>.</p>

<p>Quem busca rendimento extremo deve considerar também as <a href="/melhor-impressora-laser/">impressoras laser</a>, que cobrimos em separado.</p>
```

### Exemplos ruins

❌ `<a href="/melhor-aspirador-robo/">veja aqui</a>` (âncora não-descritiva)

❌ `<p>Veja também: <a>X</a>, <a>Y</a>, <a>Z</a>.</p>` (concentração no fim)

❌ `<a href="/melhor-impressora-laser-barata/">laser barata</a>` quando esse slug NÃO está na peer list (link inventado — IA "alucinando" artigo que não existe)

### Hard-validation (eu faço antes de salvar)

Extraio todos os `href="/..."` do HTML e confiro contra a lista de peer articles. Se algum slug não bate, **regenero** o trecho antes de aplicar. Não passa link inventado.

Se peer list está vazia (este é o 1º artigo do site), **ZERO links internos**. Não tenta linkar pra fora do site, não inventa slug.

## Concorrentes (opcional)

Se o user colou textos de páginas concorrentes (ex: "olha o guia da Buscapé sobre creatina"), uso como **inspiração editorial** (tópicos cobertos, estrutura, ângulos), **NÃO como cópia**.

Máximo 3 textos, cada um até 8k chars (truncamento se vier maior). Cada texto passa por strip básico de tags HTML antes de virar contexto.

**REGRA DURA**: nada do guide pode ser frase parafraseada ÓBVIA de concorrente. Se aparece "A creatina monohidratada é a forma mais estudada" e o concorrente tem isso literal, eu reescrevo com ângulo próprio.

## Como usar as bíblias (contexto, não citação)

Carrego TODAS as bíblias dos produtos do artigo pra ENTENDER:

- Categoria editorial (tipo de produto, nicho)
- Critérios técnicos que diferenciam os produtos do lineup
- Specs e features comuns vs raras
- Perfis de uso que aparecem em `angulosConversao`
- Filtros editoriais (ver bíblia → `diretrizesEditoriais`)

**NÃO cito produtos por nome no guide.** Uso a info das bíblias pra escrever sobre a CATEGORIA, generalizando.

**Padrão bom**:
- Bíblia 1 (Epson L3250): tanque, 4.500 páginas, doméstico
- Bíblia 2 (HP Smart Tank 581): tanque, 6.000 páginas, escritório pequeno
- Bíblia 3 (HP DeskJet 2975): cartucho, 200 páginas, uso raro

→ Guide fala sobre "rendimento por kit", "tanque vs cartucho", "perfis de uso (doméstico/profissional)" — generaliza o que as bíblias revelam, sem citar Epson, HP, modelos.

**Padrão ruim**:
- ❌ "A Epson L3250 oferece 4.500 páginas..." (cita produto específico — função da tabela/review)
- ❌ "Recomendamos a HP Smart Tank para escritório" (recomenda produto — função do review)

## Voz editorial

- **Educativa, factual, neutra.** Tom de quem explica critérios pra alguém aprendendo a comprar.
- **Não comercial.** Não promete que a pessoa vai encontrar o produto "perfeito". Promete entender critérios.
- **Sem "nós" exagerado.** "A decisão começa por X" > "Nós recomendamos X" (mais educativo, menos prescritivo).
- **Português brasileiro editorial.** Sem gírias, sem anglicismos desnecessários.
- **NUNCA cite compradores/reviews/avaliações/Amazon** (padrão do projeto).

## Tom conversacional (CRÍTICO)

Pergunta-teste antes de salvar: *"Um amigo que não entende disso entenderia?"* Se não → simplifica.

Guide é educativo mas não acadêmico. Evite jargão corporativo (❌ "alinhado à narrativa", "perfil favorável", "estrutura química mais próxima do natural"). Use linguagem direta (✓ "vale procurar dose alta", "molécula mais parecida com o óleo natural"). NUNCA cite procedência burocrática ("conforme tipo de dieta declarado", "alérgenos confirmam") — destila o critério direto.

Referência canônica pra calibrar tom: `sites/melhorimpressora/src/content/reviews/melhor-impressora-custo-beneficio.mdx` (campo `guideContent` é exemplo).

## Filtros editoriais

- **Specs ambientais** (% reciclado, Energy Star, EPEAT, RoHS, "Planet Partners") → omitir no guide, salvo se tema `sustentabilidade` em `angulosConversao` de alguma bíblia.
- **Origem de fabricação** ("fabricado no Brasil", "made in X") → idem, salvo ângulo `produto-nacional`.
- **Variantes Amazon** (tamanhos de embalagem, voltagens específicas, cores) → omitir (não é critério de categoria, é variante).

## Regras duras (bloqueiam audit)

- Abertura é `<h2>` (NÃO `<h1>`, NÃO começa com `<p>`).
- 500-15000 chars total no HTML.
- HTML allowlist: `<h2>`, `<h3>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<a>`. Nada mais.
- ZERO links Amazon. Nenhum `href` contém `amazon.com` ou `amzn.to`.
- Linkagem interna: 0-3 links totais, todos pra slugs reais de peer articles. Formato `<a href="/{slug}/">texto descritivo</a>` sem `target`/`rel`.
- Sem travessão `—` nem `–`.
- Sem superlativos sem evidência ("o melhor disponível", "incomparável").
- Sem citação a marca/modelo/ASIN específico.
- Sem citação a compradores/reviews/avaliações/Amazon como entidade.
- Sem `<h1>`, `<img>`, `<table>`, `<script>`, `<iframe>`, `<style>`, `<div>`, `<span>`, `<form>`.

## Armadilhas recorrentes

### 1. H1 em vez de H2 na abertura
Hábito de modelos LLM começar HTML com `<h1>`. Proibido aqui — o artigo já tem H1 no title do frontmatter. Sempre `<h2>`.

### 2. Mencionar produto específico
"A Epson L3250 lidera o segmento..." → NÃO. Generaliza: "as marcas brasileiras dominam o segmento". Produtos vão na tabela e nos reviews.

### 3. Slug inventado pra linkagem
IA frequentemente inventa `/melhor-impressora-laser-barata/` quando esse artigo NÃO existe. Antes de salvar, eu Grep mentalmente todos os `href` e confiro contra peer list. Se inventar → regenero o trecho.

### 4. Link Amazon no guide
Por hábito de outras skills (reviews têm 2-3 links Amazon), modelo pode tentar incluir `https://www.amazon.com.br/...`. PROIBIDO no guide. Afiliados ficam só nos cards do `.mdx`.

### 5. UL/OL com 1-2 itens só
Lista de 1-2 items é "lista de mentira" — sempre vira prosa melhor. Reserve UL/OL pra 3+ critérios discretos.

### 6. Subseção H3 redundante
`<h3>Introdução</h3>`, `<h3>Conclusão</h3>` — redundantes (o H2 abre, o último parágrafo fecha). H3 é pra TÓPICOS específicos (ex: `<h3>Tanque de tinta vs cartucho</h3>`).

### 7. Travessão por hábito
Travessão (`—` ou `–`) é proibido em todos os campos editoriais do projeto. Vírgula, dois pontos ou parênteses fazem o mesmo trabalho.

### 8. Indent errado no block scalar
Se o `guideContent: |` tem linha com 4 spaces ou 0 spaces ou tab, YAML quebra → build Astro falha → erro de produção. Cada linha do HTML dentro do block scalar precisa de **exatamente 2 espaços** de indent. Linhas em branco entre parágrafos HTML ficam sem indent (string vazia OK).

### 9. Edit tool com bloco old_string ambíguo
Se o `guideContent` atual tem alguma frase EXATA que aparece também em outro lugar do `.mdx` (ex: title repetido literal), Edit pode confundir. Mitigação: incluir 1-2 linhas de contexto antes (ex: a linha do `products:` ou similar) no `old_string` pra forçar match único.

### 10. Texto âncora não-descritivo
`<a href="/X/">clique aqui</a>` — SEO ruim. Texto âncora deve descrever DESTINO: `<a href="/melhor-impressora-multifuncional/">multifuncionais</a>`.

### 11. Concorrente parafraseado óbvio
Se user colou texto da Buscapé e o guide reusa frase quase literal, é cópia (mesmo sem aspas). Reescrever com ângulo próprio.

### 12. Citar comprador no guide
"Compradores recorrentemente preferem..." → PROIBIDO. Substituir por linguagem analítica: "Para uso doméstico, o critério principal é..." ou "Quem imprime muito tende a recuperar...".

## Sincronização painel ↔ skill ↔ prompt canônico

```
docs/painel/_data/agent-prompts.json:generate_guide  (SOURCE OF TRUTH editorial)
    ├── handler do painel (POST /agent/article/:site/:slug/generate-guide)
    └── esta SKILL.md (versão local executável)
```

Quando Marcelo edita régua editorial (via `agent-config.html` no painel), atualiza `agent-prompts.json` canônico. Esta SKILL.md pode ficar atrasada — atualizar manualmente quando notar drift.

Helpers do painel pra leitura/escrita do `guideContent`:
- `docs/painel/_lib/article-guide.ts:readGuideContent(mdxPath)` — extrai HTML sem indent
- `docs/painel/_lib/article-guide.ts:writeGuideContent(mdxPath, html)` — escreve com indent + atomic
- Skill local não importa esses helpers (não roda no contexto Bun), mas a lógica equivalente está documentada no passo 13 do fluxo.

## Quando NÃO usar essa skill

- **Artigo travado** (`contentLocked: true`): o painel rejeita save em /guide endpoints (HTTP 423). Skill grava direto via Edit tool (não passa pelo painel) — funciona tecnicamente, mas editorialmente: se o artigo tá travado, há razão (SEO estável). Pergunta antes de prosseguir.
- **Artigo sem produtos** (`products: []` vazio): guide sem categoria concreta fica vago. Abortar e orientar adicionar produtos primeiro.
- **Falta de bíblia** dos produtos: rodar `bun scripts/sync-biblias-r2.ts --apply` primeiro. Sem as bíblias, o guide fica genérico demais (não consegue inferir critérios da categoria).
- **Site recém-criado com 1 artigo só**: skill funciona mas peer list vai estar vazia → ZERO links internos. OK, é o estado natural.

## Exemplo de invocação

Exemplos válidos do user — modo padrão:
- "escreve o guia do melhor-impressora-custo-beneficio do melhorimpressora"
- "gera o guideContent do artigo X do site Y"
- "https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio" (com hint "guia")

Exemplos com instrução inline:
- "escreve o guia do X mais conciso"
- "guia do Y com foco em iniciantes"
- "escreve o guia do Z sem subseções H3"

Exemplos com concorrentes:
- "escreve o guia do X, usa esse texto da Buscapé como referência: [colou texto]"

Args canônico que invoco: `Skill(skill="artigo-guia-escrever", args="melhorimpressora/melhor-impressora-custo-beneficio")` (instrução + concorrentes vão pelo contexto do prompt natural)

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), validação fica editorial — eu (modelo) sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial (link interno inventado, char count em 15100, tag fora da allowlist). Mitigação principal: hard-validation manual de links internos contra peer list antes de aplicar; se falhar, regenero o trecho.
