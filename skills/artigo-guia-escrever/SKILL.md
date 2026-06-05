---
name: artigo-guia-escrever
description: Escreve o guideContent (HTML completo "Vale a pena / Como escolher / Melhor marca / FAQ / Conclusão") do artigo + análise de concorrentes reusável por keyword. Aceita URL do painel (editor-artigo.html?site=X&slug=Y) OU args canônicos `site/slug`. Quando user cola "Como escolher" de 1-3 concorrentes, skill ANALISA (tópicos, palavras-chave, gaps, clichês a evitar) + GERA guide com topical map paritário + SALVA análise em `docs/painel/_data/competitor-analyses/{keyword-slug}.md` pra reuso (qualquer site na mesma keyword auto-carrega). Régua: 5 H2 obrigatórios na ordem (Vale a pena / Como escolher / Melhor marca / FAQ / Conclusão) + 1 opcional (Por que confiar), 6000-25000 chars (alvo 12-18k), allowlist h2/h3/p/ul/ol/li/strong/em/a, links Amazon em FAQ/Marca/Conclusão (tag-aware), SEM travessão, linkagem interna 0-3 só pra peer articles reais. Carrega chavões nicho-específicos. Substitui só o campo guideContent. Backup + commit + push + sync VPS.
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

**Concorrentes (texto completo do "Como escolher") — OBRIGATÓRIOS pra gerar o guia.** O guia é a peça SEO que precisa BATER a SERP da keyword exata; sem os concorrentes reais dela, sai genérico e gera retrabalho. Há 2 formas de supri-los:

1. **Análise existente da keyword EXATA**: se já existe `docs/painel/_data/competitor-analyses/{keyword-slug}.md` (slug do `keyword` deste artigo, **match EXATO**), eu CARREGO automaticamente — você não precisa colar nada. O reuso só vale entre artigos que miram **a MESMA keyword** (mesma SERP, mesmos concorrentes), inclusive em sites diferentes. **NUNCA** reuso a análise de uma keyword vizinha/parecida: "melhor impressora" ≠ "melhor impressora custo benefício" ≠ "melhor impressora tanque de tinta" são keywords DIFERENTES (intenção de busca, SERP e concorrentes diferentes).

2. **Não existe análise da keyword exata**: você cola 1-3 textos completos de "Como escolher" dos concorrentes que aparecem ao buscar **essa keyword** no Google. Eu **analiso** (tópicos, palavras-chave, ângulos, gaps, o que evitar), **gero o guia**, e **salvo a análise** em `docs/painel/_data/competitor-analyses/{keyword-slug}.md` pra reuso futuro. **Sem os concorrentes eu PARO e peço — não gero genérico nem reuso de outra keyword** (ver Cenário C).

**Override**: se a análise existe mas você quer regenerar com concorrentes novos (SERP mudou), cole textos novos junto com o comando — eu sobrescrevo (backup antes).

# Escrever guia "Como escolher" do artigo

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:generate_guide`. O conteúdo essencial está duplicado abaixo pra autocontenção; em caso de divergência, o prompt canônico ganha.

Você é o curador editorial do **guide** do artigo — a seção "Como escolher {keyword}" que complementa o comparativo. O guide vive **dentro do frontmatter do `.mdx`**, no campo `guideContent` (block scalar YAML `|` com indent de 2 espaços, desde Etapa B/B.2).

Sua função é gerar **HTML educativo** que ajuda o leitor a entender CRITÉRIOS de escolha (não a comparar produtos específicos — isso é função da tabela e dos reviews). O guide é a peça SEO complementar: leitor educado converte melhor.

## Pré-requisitos

- O `.mdx` do artigo já existe em `sites/{site}/src/content/reviews/{slug}.mdx`. Se não, abortar com orientação pra criar via painel ("✨ Criar artigo" no site detail → `make-reviews-stub`).
- O artigo tem **pelo menos 1 produto** no lineup (`products: []` vazio = abortar — guide sem categoria concreta fica vago).
- Bíblias dos produtos do artigo estão em `docs/biblias-v2/{ASIN}.json`. Se alguma faltar, rodar `bun scripts/sync-biblias-r2.ts --apply` antes (skill avisa e aborta se faltar).
- `affiliateTag` em `sites/{site}/src/config.ts` é conhecida. Se vazia (site em construção), links Amazon do guide saem CRUS (`https://www.amazon.com.br/dp/{ASIN}`). Se preenchida, com tag (`?tag={tag}&linkCode=ogi&th=1&psc=1`). Guide TEM links Amazon em FAQ/Marca/Conclusão — então tag-aware importa.

## Invariantes

- **Nunca toque em nada além do campo `guideContent`** do frontmatter. Title, description, keyword, products, intro do body, tudo intacto. Só substitui o block scalar do `guideContent` (ou insere se ainda não existir).
- **HTML, não markdown.** Diferente da intro (que é markdown puro), o guide é HTML.
- **Allowlist de tags**: `<h2>`, `<h3>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<a>`. Tudo mais é proibido: `<h1>` (artigo já tem H1 no title), `<script>`, `<iframe>`, `<style>`, `<img>`, `<table>`, `<form>`, `<button>`, `<div>`, `<span>` (visual fica pro CSS).
- **6.000 a 25.000 chars** no total do HTML (alvo típico 8-18k — vide canônicos do projeto).
- **Estrutura: 5 H2 obrigatórios** + 1 opcional. Faltar qualquer obrigatório = ERRO. Ver "Régua editorial — ESTRUTURA OBRIGATÓRIA" abaixo.
- **Links Amazon: tag-aware.** PROIBIDOS em "Vale a pena" e "Como escolher" (educativas). PERMITIDOS em "Melhor marca" (link de busca da marca), "FAQ" e "Conclusão" (recomendações de produto). Formato: `?tag={tag}&linkCode=ogi&th=1&psc=1` se tag preenchida; URL crua se vazia.
- **Linkagem interna 0-3 links** pra **peer articles reais do mesmo site** (slug REAL do arquivo, NUNCA derivado do keyword). Âncora = **keyword do destino (singular preferido)**; link de produto = **nome completo COM marca**. Sem `target="_blank"`, sem `rel="nofollow"` (links internos passam autoridade). Ver "Linkagem interna".
- **Sem travessão (—).** Use vírgula, ponto, dois pontos ou parênteses.
- **Sem superlativos sem evidência** ("o melhor disponível", "incomparável", "imbatível"). "Excelente", "ótimo" OK se contextualizado.
- **Citação de produto específico: contextual.** PROIBIDA em "Como escolher" (linguagem GERAL — critérios, perfis). PERMITIDA em "Melhor marca" (1 H3 por marca), "FAQ" (recomendação direta), "Conclusão" (recomendação central) e como âncoras de preço em "Vale a pena" (P2). Ver matriz completa em "Como usar a bíblia".
- **NÃO inventar dados.** Se o guide precisar de número, vem de alguma bíblia.
- **NÃO citar compradores/reviews/avaliações** como entidade ("compradores avaliam X estrelas") — viola voz editorial do projeto. Link Amazon como destino de COMPRA está OK em FAQ/Marca/Conclusão.
- **Tom: educativo nas seções 1-2, recomendativo nas 3-6.** Vale a pena + Como escolher são puramente educativas. Melhor marca + FAQ + Conclusão são onde o leitor decide a compra.

## Fluxo

0.5. **Carregar chavões do nicho** (régua v1.18.0):
   - Identifique `niche` em `docs/painel/sites-meta.json` (ex: Pré Treino, Creatinas, Tablets)
   - Read `docs/painel/_data/chavoes-por-nicho.json` — use `_genericos` + bloco do nicho
   - Aplique limites como guard rail: não passar de `ingles_max`, `medico_tecnico_max`, `industrial_max`, `indicacao_medica_max`
   - Banidos absolutos sempre: lineup, SKU, ASIN, datasheet, notificado, trade-off, hardcore

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
   - Pra cada `.mdx` (excluindo o próprio): `Read` rápido pra extrair `title`, `keyword`, `keywordPlural` e `slug` (= filename sem `.mdx`)
   - Resultado: array `[{slug, title, keyword, keywordPlural}]` dos OUTROS artigos do site (a `keyword` vira a ÂNCORA do link interno — ver "Linkagem interna")
   - Se vazio (este é o 1º artigo do site): NÃO incluir links internos no guide gerado

7. **Detectar instrução opcional** no prompt do user (paridade com outras skills):
   - "mais conciso" / "enfatize tanque de tinta" / "sem subseções" / "com foco em iniciantes" → extrai como instrução
   - Sem instrução clara → modo padrão

8. **Análise de concorrentes** (3 cenários):

   ### Cenário A — análise da keyword EXATA existe E user NÃO colou novos concorrentes
   - **Match EXATO do slug é obrigatório.** `{keyword-slug}` = slugify do `keyword` do frontmatter DESTE artigo (ver função abaixo). Se o arquivo do slug exato NÃO existe, isto **NÃO é Cenário A** — vá pro **Cenário C** (pedir concorrentes). **NUNCA** carregar a análise de uma keyword vizinha/parecida (ex: usar `melhor-impressora-custo-beneficio.md` pra keyword "melhor impressora", ou `-epson`/`-tanque-de-tinta`): keywords diferentes têm intenção, SERP e concorrentes diferentes. "Mesma categoria" ≠ "mesma keyword".
   - `Read docs/painel/_data/competitor-analyses/{keyword-slug}.md` (slugify do `keyword` do frontmatter — ver função slugify abaixo)
   - Carrega como contexto rico (topical map, gaps, o que evitar, ângulos)
   - **NÃO regera a análise** (preserva a existente)
   - Reporta no chat: "📊 Análise de concorrentes carregada de `_data/competitor-analyses/{kw}.md` (gerada em DD/MM/YYYY)"

   ### Cenário B — análise NÃO existe + user colou textos de concorrentes
   - Cada texto truncado em 16k chars (mais generoso que os 8k antigos — análise rica)
   - Eu analiso os textos e produzo a análise estruturada (passo 10b)
   - Usa como topical map pra gerar o guide
   - Cria o `.md` da análise depois (passo 10b)

   ### Cenário C — não existe análise da keyword EXATA E user NÃO colou nada
   - **PARAR e PEDIR os concorrentes. OBRIGATÓRIO, sem exceção.** NÃO gerar o guia sem análise da keyword exata. Não há mais opção de "fallback genérico", e é **PROIBIDO reusar a análise de outra keyword** (mesmo do mesmo site/categoria — ver Cenário A). Mensagem ao user:
     > "Pra escrever o guia de **{keyword}** eu preciso dos concorrentes DESSA keyword. Não reuso a análise de keyword parecida (intenção/SERP/concorrentes diferentes) nem gero genérico. Cole 1-3 'Como escolher' dos resultados que aparecem ao buscar **'{keyword}'** no Google (Buscapé, Zoom, Canaltech, Mundo Conectado, TechTudo, etc). Eu analiso, gero o guia e salvo a análise pra reuso futuro nessa mesma keyword."
   - **AGUARDAR os textos colados.** Depois processa como Cenário B (analisa, gera, salva `{keyword-slug}.md`).
   - Se o user insistir em gerar SEM concorrentes: avisar explicitamente que o guia ficará fraco em SEO (não bate a SERP da keyword) e **exigir confirmação explícita** antes de prosseguir só com as bíblias. Nunca seguir sem concorrentes em silêncio.
   - **Razão**: experiência real (2026-06-05) mostrou que reusar a análise de uma keyword vizinha ("melhor impressora custo benefício" pra "melhor impressora") ou cair em fallback silencioso desperdiça a oportunidade de SEO e gera retrabalho. Pedir os concorrentes da keyword EXATA é o único caminho.

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
    - **6.000-25.000 chars** total (alvo 12-18k)
    - **5 H2 obrigatórios presentes na ordem**: `Vale a pena` → `Como escolher` → `Melhor marca` → `Perguntas Frequentes` → `Conclusão` (6º opcional: `Por que confiar` entre FAQ e Conclusão)
    - Primeiro tag = `<h2>` (NÃO `<h1>`, NÃO `<p>`)
    - HTML allowlist OK (Grep mental por tags fora da lista)
    - 0-3 links internos: cada `href="/{slug}/"` aponta pra slug REAL da peer articles list
    - Links Amazon: ZERO em "Vale a pena" e "Como escolher"; PERMITIDOS em "Melhor marca" (busca), "FAQ" e "Conclusão" (recomendação). Tag-aware do site.
    - Sem travessão `—` nem `–`
    - Sem `<h1>` (artigo já tem H1 no title)
    - Sem `<img>`, `<table>`, `<script>` etc
    - Citação de produto específico só em FAQ/Marca/Conclusão (+ âncoras de preço em "Vale a pena" P2)
    - Sem citação a "compradores"/"reviews"/"avaliações" como entidade

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

> **Padrão consolidado em 2026-05** com `docs/PADROES.md` + canônicos do projeto (ex: `sites/melhorestablets/src/content/reviews/melhor-tablet-custo-beneficio.mdx`).

### 5 H2 obrigatórios (na ordem) + 1 opcional

```html
<h2>Vale a pena comprar um/uma {keyword} em {ano}?</h2>
<h2>Como escolher o melhor/a melhor {keyword} em {ano}?</h2>
<h2>Qual a melhor marca de {keyword} em {ano}?</h2>
<h2>Perguntas Frequentes</h2>
<!-- [OPCIONAL] <h2>Por que confiar neste conteúdo</h2> -->
<h2>Conclusão</h2>
```

- **`em {ano}`** é padrão recomendado (atualidade SEO) mas pode ser omitido se a frase fica forçada (keyword já tem ano implícito, soa redundante, etc).
- **"Perguntas Frequentes"** e **"Conclusão"** ficam **sem** `em {ano}`.
- **NUNCA** `<h1>` (artigo já tem H1 no title). **NUNCA** começar com `<p>` antes do primeiro H2.
- A 6ª seção opcional ("Por que confiar neste conteúdo") fica entre FAQ e Conclusão. Use só quando agrega (transparência editorial específica, metodologia explicada).

### Régua por seção

#### 1. Vale a pena comprar...?
**3 parágrafos:**
- **P1**: argumento central da categoria + critérios estruturais (ex: tanque vs cartucho, ecossistema, perfis de uso).
- **P2**: âncoras de preço REAIS do lineup (ex: *"Os preços desta seleção vão de R$ X (Modelo Y) a R$ Z (Modelo W)"*). Cita 2-3 modelos como referência de preço (esta é a EXCEÇÃO à régua "geral").
- **P3**: quando **NÃO** vale a pena comprar (perfil errado, alternativas melhores). Importante editorialmente — protege credibilidade.

#### 2. Como escolher o melhor...?
**Intro (1 parágrafo curto) + 4-7 subseções `<h3>`** — cada H3 é um critério.

Régua de cada H3:
- Texto explica **o que o critério significa** e **o que procurar** — não qual produto tem o quê
- **Dar números de referência concretos** (ex: *"4.096 níveis é o padrão profissional atual"*, *"8 GB é o ponto ideal para a maioria"*)
- Evitar linguagem vaga (*"quanto maior melhor"*, *"HD ou superior"* sem contexto)
- **Produtos específicos só de forma pontual** quando agrega valor educativo (ex: *"Procreate é exclusivo do iPadOS"*)

Exemplos do que diferencia bom vs ruim (de `docs/PADROES.md`):

| Ruim (genérico) | Bom (educativo) |
|---|---|
| "quanto maior o número de níveis de pressão, melhor" | "4.096 níveis é o padrão profissional atual; abaixo disso o traço perde variação" |
| "telas de 10 a 15 polegadas com HD ou superior" | "10 a 11 polegadas é o equilíbrio entre canvas e portabilidade; 13 polegadas ou mais para quem trabalha apoiado sobre mesa" |

#### 3. Qual a melhor marca?
**Intro (1 parágrafo curto) + 1 `<h3>` por marca relevante** (tipicamente 3-5 H3).

Régua de cada H3:
- Título: `<h3>{Marca}: {posicionamento curto editorial}</h3>` (ex: *"Samsung: a marca mais completa para Android no Brasil"*)
- 1 parágrafo: foco em **diferencial editorial real** (linha principal, ecossistema, suporte, característica única)
- **Sem ranking absoluto** entre marcas — cada uma cobre um cenário diferente
- **Pode incluir link Amazon de busca da marca** (formato `<a href="https://www.amazon.com.br/s?k={termo}&tag={affiliateTag}" rel="nofollow" target="_blank">{Marca}</a>`)
- Manter **objetivo** e baseado em fatos da bíblia/categoria (NÃO inventar "história da empresa")

#### 4. Perguntas Frequentes
**5-8 subseções `<h3>`** cada uma com a pergunta como título + 1-3 frases de resposta concreta.

Régua de cada FAQ:
- Pergunta como leitor digitaria no Google (ex: *"Qual o melhor X em 2026?"*, *"Vale a pena Y?"*, *"X ou Z?"*)
- Resposta direta e concreta (não rodeio)
- **PODE citar produtos específicos do lineup com link Amazon** (ex: *"Para a maioria das pessoas, o Samsung Galaxy Tab S10 Lite é a melhor compra..."* com link Amazon do ASIN)
- Distribuir 1-2 links Amazon por FAQ que justifique recomendação
- Pergunta-teste: *"Esta FAQ responde algo que o leitor REALMENTE perguntaria?"*

#### 5. [OPCIONAL] Por que confiar neste conteúdo
1-3 parágrafos sobre metodologia editorial (sem citar Amazon/avaliações — viola memória do projeto). Use só quando há diferencial real a comunicar.

#### 6. Conclusão
**2 parágrafos:**
- **P1**: recomendação central do guide (1-2 modelos top com link Amazon)
- **P2**: alternativas por perfil (modelos específicos por nicho ou redireciona pra artigos peer relacionados)
- **Tom resolutivo** — leitor sai com decisão tomada

### Tamanho típico

**Alvo: 8.000-18.000 chars.** Range válido: 6.000-25.000.

Canônicos atuais (referência):
- `melhor-tablet-custo-beneficio` — 17.847 chars
- `melhor-aspirador-de-po-vertical` — 18.923 chars
- `melhor-tablet-samsung` — 20.073 chars
- `kindle-qual-o-melhor` — 15.518 chars

Guide bem feito tem ~12-18k chars. Menos que 6k provavelmente faltou cobertura; mais que 25k vira walls of text.

### Listas (opcionais, dentro das seções)

`<ul>` ou `<ol>` quando faz sentido enumerar critérios discretos. **Mínimo 3 itens**:

```html
<p>Antes de comprar, verifique:</p>
<ul>
  <li>Voltagem (bivolt ou específica)</li>
  <li>Tipo de filtro (HEPA, lavável, descartável)</li>
  <li>Garantia oficial Brasil</li>
</ul>
```

Lista de 1-2 itens vira prosa.

### Densidade visual: negrito e links Amazon

**Régua descoberta em 2026-05** comparando 35 guides do monorepo.

A rede tem 2 padrões coexistindo:

- **Padrão NOVO (canon atual — usar SEMPRE em guides novos)**: melhoraspirador (5,3 strongs/1k), melhorestablets (2,8–5,6), qualamelhorcreatina (2,6–3,6), melhorimpressora. Pattern: **"negrito denso + links Amazon concentrados em Marca/FAQ/Conclusão"**.

- **Padrão LEGADO (NÃO REPLICAR — herança histórica)**: escritoriocasa (8 guides, 0,15–2,7 strongs/1k), melhorcozinha (0,0–0,8), guides antigos de melhorcreatina (0,4–2,2). Pattern: **"poucos negritos + muitos links Amazon espalhados em todas as seções"**.

Quando escrever guide novo ou refazer guide existente, seguir o padrão NOVO. Guides legados ficam onde estão até dor real (refazer compete com features); auditoria pode flaggar como info, mas migração é manual e caso a caso.

#### Negrito (`<strong>`) — alvo: 4-5 por 1.000 chars

Pra um guide de 18k chars, isso significa ~70-90 tags `<strong>` distribuídas. Menos que 3/1k = guide visualmente fraco (parece muro de texto). Mais que 6/1k = inflação de destaque (perde efeito).

**O que SEMPRE negritar:**
- Specs numéricos: `<strong>1.000W a 2.000W</strong>`, `<strong>4.500 páginas</strong>`, `<strong>R$ 60</strong>`
- Termos técnicos da categoria: `<strong>filtro HEPA</strong>`, `<strong>tanque de tinta</strong>`, `<strong>Wi-Fi Direct</strong>`, `<strong>escova rotativa motorizada</strong>`
- Frases-chave conceituais (insight editorial): `<strong>onde o peso se concentra</strong>`, `<strong>preço inicial somado ao custo por página</strong>`, `<strong>não resseca quando a impressora fica sem uso</strong>`
- Perfis de uso destacados: `<strong>uso doméstico médio</strong>`, `<strong>escritório com fluxo alto</strong>`, `<strong>pets e tapetes grossos</strong>`
- Diferenciais reais entre produtos/marcas: `<strong>tinta preta pigmento</strong>`, `<strong>duplex automático</strong>`

**O que NÃO negritar:**
- Conectivos e palavras de transição ("portanto", "além disso", "também")
- Palavras isoladas sem contexto editorial ("rápido", "bom", "fácil")
- Frases inteiras (>10 palavras) — destaque perde efeito
- Marcas no texto corrido fora da seção "Quais as melhores marcas" (a marca aparece como nome próprio, não como destaque)

**Pergunta-teste**: *"Se eu escanear o guide só lendo o que está em negrito, capto os pontos-chave?"* Se sim, densidade está OK. Se vejo só números sem contexto, falta negritar conceitos.

#### Links no guide — estratégia hub-and-spoke (2026-05)

**Decisão editorial (2026-05)**: quando o site tem páginas individuais dos produtos do lineup em `sites/{site}/src/content/products/{slug}.mdx`, **prefira link INTERNO** (`/{slug}/`) sobre link Amazon `/dp/{ASIN}` no guide. Motivos:

1. **SEO interno**: distribui link juice do artigo principal pras páginas de produto → elas rankeiam melhor no Google
2. **UX no guide**: leitor que aprofunda no guide chega numa página com info concentrada do produto (mais reflexiva que ir direto pra Amazon)
3. **Conversão preservada**: a página individual TEM CTA Amazon próprio (botão "Comprar"), então a conversão acontece com 1 clique extra
4. **Links Amazon abundantes nos reviews-em-artigo** (parte de cima do artigo) já capturam quem decide direto

**Distribuição esperada por seção (atualizada):**

| Seção | Links | Tipo | Por quê |
|---|---|---|---|
| Vale a pena | **0** | — | Educativa-introdutória, sem CTA. Citações de modelo como âncora de preço (P2) em texto SIMPLES |
| Como escolher (H3s) | **0** | — | 100% educativa sobre critérios |
| Quais as melhores marcas (H3s) | **1 por marca** | Amazon search `/s?k=...` | Não há páginas internas de "marca" — usa search Amazon mesmo |
| Perguntas Frequentes | **2-4** | **Internos `/slug/`** (se peer page existe) ou Amazon `/dp/` (fallback) | FAQs comparativas/recomendativas |
| Conclusão | **5-8** | **Internos `/slug/`** (se peer pages existem) ou Amazon `/dp/` (fallback) | Lista por nicho |
| **Total alvo** | **~10-15** | majoritariamente internos, com 3-5 search Amazon nas Marcas | |

**Como decidir entre interno vs Amazon `/dp/`:**

```
Antes de inserir <a> pra produto no guide (FAQ/Conclusão):
  1. Existe sites/{site}/src/content/products/{slug-do-produto}.mdx?
     SIM → use <a href="/{slug}/">Nome</a>  (SEM rel, SEM target — link interno)
     NÃO → use <a href="https://www.amazon.com.br/dp/{ASIN}?tag={tag}&..." rel="nofollow" target="_blank">Nome</a>
  2. Sites em construção (affiliateTag vazia) podem trabalhar mesmo se peer page faltar:
     usa link Amazon CRU sem tag pra esperar peer page ser criada
```

**Padrões errados a evitar:**
- ❌ Link Amazon `/dp/` no guide quando a peer page existe (oportunidade perdida de SEO interno)
- ❌ Link interno `/slug/` SEM verificar se a peer page existe (gera 404 em produção)
- ❌ Misturar `rel="nofollow" target="_blank"` em link interno (esses atributos são pra externo apenas)
- ❌ 24+ links no guide inteiro espalhados em todas seções, incluindo educativas

**Implementação canônica (referência):** `melhorimpressora/melhor-impressora-custo-beneficio.mdx` aplica esse padrão desde 2026-05 — 0 Amazon `/dp/` no guide, 13 internos pras 9 páginas individuais, 6 Amazon search (4 marcas + 2 FAQ específica), Amazon `/dp/` continuam nos reviews-em-artigo (parte de cima) sem mudança.

#### Links internos (peer articles)

- **0-3 links totais** no guide inteiro (já documentado em "Linkagem interna")
- Distribuir ao longo do texto (não concentrar no fim)
- Bom encaixe: dentro de H3 de "Como escolher" pra cross-linkar critério com outro artigo do site (ex: H3 "Com fio ou sem fio" linka pra "/melhor-aspirador-sem-fio-vertical/")

## Linkagem interna — contextual, estratégica, âncora = keyword (v1.22.0)

A skill carrega `[{slug, title, keyword, keywordPlural}]` dos OUTROS artigos do site (passo 6) + a lista de páginas de produto (`products/*.mdx`). Linkar é **contextual e estratégico**, não decorativo.

### Regra de OURO da âncora

- **Link pra ARTIGO peer**: a âncora é a **keyword do artigo de destino**, com **preferência pela forma SINGULAR** (plural só quando a frase exige). NUNCA âncora descritiva/genérica.
  - ✅ `<a href="/melhor-impressora-tanque-de-tinta/">melhor impressora tanque de tinta</a>`
  - ❌ `<a href="/melhor-impressora-tanque-de-tinta/">opções de tanque de tinta</a>` (âncora ≠ keyword)
- **Link pra PÁGINA DE PRODUTO** (hub-and-spoke): a âncora é o **nome COMPLETO do produto, COM a marca** (nunca só o modelo).
  - ✅ `<a href="/epson-ecotank-l4360/">Epson EcoTank L4360</a>`
  - ❌ `<a href="/epson-ecotank-l4360/">L4360</a>` ou `<a ...>EcoTank L4360</a>` (sem marca)

### Slug REAL — NUNCA derivar do keyword

O `href` é o **slug REAL do arquivo de destino** (da peer-list / pasta `products/`), copiado verbatim. **NUNCA derive o slug do keyword** (slugify do título). Foi exatamente assim que nasceu `/impressora-boa-e-barata/` (keyword "impressora boa e barata") quando o arquivo real é `impressora-barata.mdx` → 404 em produção. Se o destino é o `homeReviewSlug` do site, o href é `/` (a home), **não** `/{homeReviewSlug}/` (esse é filtrado do getStaticPaths → 404).

### Estratégia (contextual + sem órfão)

- Distribua os links ao longo do texto (não concentrar no fim), cada um num contexto que justifique a visita.
- Pense no grafo do site: linke os **irmãos mais relevantes** (ex: o guia do termo-head linka custo-benefício + tanque + barata; cada sub-artigo aponta de volta pra home via `/`). Evita artigo órfão/sub-linkado.
- Atributos: SEM `target="_blank"`, SEM `rel="nofollow"` (interno passa autoridade).
- Quantidade: **mínimo 2 peer ARTICLES DISTINTOS** (NUNCA repita o mesmo destino 2×), até 3, + os links de PRODUTO (hub-and-spoke, quantos forem naturais).
- **Só no guia**: todos os links internos (peer + produto) vivem **só no `guideContent`** (Como escolher / FAQ / Conclusão). **NUNCA** na introdução nem nos reviews dos produtos (lá só vai link Amazon).

### Hard-validation (antes de salvar)

1. Cada `href="/{slug}/"` existe em `reviews/` OU `products/`? Se não → 404, **regenerar com o slug real**. Nenhum aponta pro `homeReviewSlug` (esse vira `/`).
2. Âncora de peer == keyword do destino (singular preferido)? Âncora de produto contém a marca + é o nome completo?
Se algo falhar, **corrijo o trecho antes de aplicar**. Não passa link inventado nem âncora fora da régua.

Se peer list está vazia (1º artigo do site), **ZERO links de peer**.

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

**Citação de produto específico varia por seção:**

| Seção do guide | Cita produto específico? |
|---|---|
| Vale a pena | SOMENTE como âncoras de preço ("R$ X do Modelo Y a R$ Z do Modelo W") |
| Como escolher | NÃO (exceto exceções editoriais pontuais como *"Procreate é exclusivo do iPadOS"*) |
| Melhor marca | SIM (1 H3 por marca, cita linha principal e diferencial editorial) |
| Perguntas Frequentes | SIM (recomendação direta com link Amazon) |
| Conclusão | SIM (recomendação central + alternativas por perfil) |

**Padrão bom em "Como escolher"** (generaliza):
- Bíblia 1 (Epson L3250): tanque, 4.500 páginas, doméstico
- Bíblia 2 (HP Smart Tank 581): tanque, 6.000 páginas, escritório pequeno
- Bíblia 3 (HP DeskJet 2975): cartucho, 200 páginas, uso raro

→ Guide fala sobre "rendimento por kit", "tanque vs cartucho", "perfis de uso (doméstico/profissional)" — generaliza o que as bíblias revelam, sem citar Epson, HP, modelos.

**Padrão bom em FAQ/Conclusão** (cita):
- ✅ *"Para a maioria das pessoas, o `<a href='{amazonUrl}'>Epson EcoTank L3250</a>` é a melhor compra: tanque de tinta, 4.500 páginas por kit, Wi-Fi por cerca de R$ 1.060"* (FAQ)
- ✅ *"Quem quer mais rendimento por kit pode considerar o `<a href='{amazonUrl}'>HP Smart Tank 581</a>` (12.000 páginas) por preço similar"* (Conclusão)

**Padrão sempre ruim:**
- ❌ "A Epson L3250 oferece 4.500 páginas..." em "Como escolher" (cita produto específico fora das seções permitidas)
- ❌ "FAQ: Qual a melhor? Resposta: depende..." (FAQ genérica sem produto/link, conteúdo vazio)

## Voz editorial

- **Educativa, factual, neutra.** Tom de quem explica critérios pra alguém aprendendo a comprar.
- **Não comercial.** Não promete que a pessoa vai encontrar o produto "perfeito". Promete entender critérios.
- **Sem "nós" exagerado.** "A decisão começa por X" > "Nós recomendamos X" (mais educativo, menos prescritivo).
- **Português brasileiro editorial.** Sem gírias, sem anglicismos desnecessários.
- **NUNCA cite compradores/reviews/avaliações/Amazon** (padrão do projeto).

## Tom conversacional (CRÍTICO)

Pergunta-teste antes de salvar: *"Um amigo que não entende disso entenderia?"* Se não → simplifica.

Guide é educativo mas não acadêmico. Evite jargão corporativo (❌ "alinhado à narrativa", "perfil favorável", "estrutura química mais próxima do natural"). Use linguagem direta (✓ "vale procurar dose alta", "molécula mais parecida com o óleo natural"). NUNCA cite procedência burocrática ("conforme tipo de dieta declarado", "alérgenos confirmam") — destila o critério direto.

Referência canônica pra calibrar tom + densidade visual: `sites/melhoraspirador/src/content/reviews/melhor-aspirador-de-po-vertical.mdx` (campo `guideContent`). Esse é o padrão atual de qualidade — 5,3 `<strong>` por 1k chars + links Amazon concentrados em Marca/FAQ/Conclusão (0 Amazon em Vale a pena/Como escolher). Outros bons exemplos: `sites/melhorestablets/src/content/reviews/melhor-tablet-custo-beneficio.mdx`, `sites/qualamelhorcreatina/src/content/reviews/qual-a-melhor-creatina.mdx`.

## Filtros editoriais

- **Specs ambientais** (% reciclado, Energy Star, EPEAT, RoHS, "Planet Partners") → omitir no guide, salvo se tema `sustentabilidade` em `angulosConversao` de alguma bíblia.
- **Origem de fabricação** ("fabricado no Brasil", "made in X") → idem, salvo ângulo `produto-nacional`.
- **Variantes Amazon** (tamanhos de embalagem, voltagens específicas, cores) → omitir (não é critério de categoria, é variante).

## Regras duras (bloqueiam audit)

- **Estrutura: 5 H2 obrigatórios + 1 opcional** (Vale a pena / Como escolher / Melhor marca / FAQ / [Por que confiar] / Conclusão). Faltar qualquer um dos 5 obrigatórios = ERRO.
- Primeira tag é `<h2>` (NÃO `<h1>`, NÃO começa com `<p>`).
- **6.000-25.000 chars** total no HTML (alvo típico 8-18k).
- HTML allowlist: `<h2>`, `<h3>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<a>`. Nada mais.
- **Links Amazon**: PROIBIDOS em "Vale a pena" e "Como escolher" (educativas). PERMITIDOS em "Melhor marca", "FAQ" e "Conclusão" (formato `?tag={tag}&...` tag-aware do site; também pode ser link de busca de marca `/s?k=...`).
- **Linkagem interna**: 0-3 links pra peer articles reais (slug REAL, NUNCA derivado do keyword), âncora = keyword do destino (singular preferido); link de produto = nome completo COM marca. Sem `target`/`rel`.
- Sem travessão `—` nem `–`.
- Sem superlativos sem evidência ("o melhor disponível", "incomparável", "imbatível").
- **Citação de produto específico**: PROIBIDA em "Vale a pena" (exceto âncoras de preço — *"R$ X do Modelo Y a R$ Z do Modelo W"*) e "Como escolher" (exceto exceções editoriais pontuais, ex: *"Procreate é exclusivo do iPadOS"*). PERMITIDA em "Melhor marca" (1 H3 por marca), "FAQ" (recomendação direta) e "Conclusão" (recomendação central).
- Sem citação a compradores/reviews/avaliações/Amazon **como entidade** ("compradores avaliam", "X estrelas"). Link Amazon como destino de compra está OK em FAQ/Marca/Conclusão.
- Sem `<h1>`, `<img>`, `<table>`, `<script>`, `<iframe>`, `<style>`, `<div>`, `<span>`, `<form>`.


## Régua editorial PT-BR (v1.19.2, 2026-05-28)

Antes de gravar, faça grep dos padrões abaixo. Se aparecer — corrija.

### Concordância PT-BR (bug-class real de substituições mecânicas)

| Padrão | Fix |
|---|---|
| `composiçãos`, `combinaçãos`, `porçãos` | `composições`, `combinações`, `porções` |
| `a produto`, `a formigamento`, `a ingrediente` | `o produto`, `o formigamento`, `o ingrediente` |
| `o fórmula`, `o dose`, `o composição` | `a fórmula`, `a dose`, `a composição` |
| `produto ampla`, `produtos elaboradas`, `formula natural` | `fórmula ampla`, `produtos elaborados`, `fórmula natural` |
| `disponíveis no em 2026` | `disponíveis em 2026` |
| `Pra a maioria/primeira` | `Pra` ou `Para a` |

### Linguagem artificial banida

- `calibrar/calibrada/calibragem` = 0 → "ajustar"
- `empilhar` = 0 → "usar separado"
- `pico-e-queda` = 0 → "pico de energia seguido de queda"
- `energia metabólica/adrenérgica` = 0
- `peers/claim/stack/trade-off/hardcore` = 0
- `SKU/ASIN/UPC/EAN/datasheet/notificado` = 0

### Voz consultiva (não corporativa)

| ❌ Corporativo | ✓ Conversacional |
|---|---|
| "diferencial central" | "o grande ponto é" |
| "posicionamento" | "categoria" |
| "segmento de X" | "tipo de X" |
| "proposta de valor" | drop sempre |

### Health absolutes YMYL banidos

- "uso regular é seguro" → qualificar
- "alternativa segura" → "alternativa mais leve"
- "não causa dano" → "sem evidência de impacto"
- "sem efeitos colaterais" → "efeitos colaterais raros"
- "cientificamente comprovado" / "100% seguro" → qualificar

### Voz-eximir-responsabilidade (não use fabricante como muleta)

- "X mg declarados" parentético → drop "declarados"
- "declarado pelo fabricante" → drop sempre
- "todos/todas/doses declaradas pelo fabricante" → "fórmula transparente" ou drop
- Alérgeno: "contém glúten declarado pelo fabricante" → "contém glúten"
- **Spec de fabricante = fato, afirme direto** (régua v1.21.1): rendimento, economia e velocidade da ficha (ex: "rende até 4.500 páginas") vão SEM "segundo a Epson"/"segundo o fabricante" (atribuir a cada spec vira muleta repetitiva, igual "declarado pelo fabricante"). Atribuição só vale pra recomendação/calibração do fabricante (ex: "a HP recomenda 50 a 100 páginas/mês").

### Qualificadores de procedência redundantes (régua v1.19.2, canon 2026-05-29)

Quando um valor numérico concreto já está citado, qualificadores como "declarado", "informado", "detalhado", "especificado" são redundância pura — soam burocráticos.

| ❌ Antes | ✓ Depois |
|---|---|
| "1 g de leucina declarados" | "1 g de leucina" |
| "400 mg de cafeína declarados" | "400 mg de cafeína" |
| "aminoácidos essenciais declarados (1 g de leucina...)" | "aminoácidos essenciais (1 g de leucina...)" |
| "doses totalmente declaradas em mg" | "doses em mg" |
| "transparência das doses" como elogio vago | citar as doses reais |
| "fórmula com doses detalhadas" | "fórmula com 9 ativos em mg específicos" |

**Exceção legítima**: quando descrevendo AUSÊNCIA — "mg não consta no rótulo", "fabricante não detalha as mg". "não declarado" / "não informado" são OK quando descrevem falta de dado real.

Auto-check: grep por `declarad|informado|detalhado|especificado` logo após número concreto (`\d+\s*(?:mg|g)\s+(?:declarad|informad|detalhad|especificad)`). Se achar — drop o qualificador.

### Chavões por nicho (carregar `docs/painel/_data/chavoes-por-nicho.json`)

- Identifique `niche` em `docs/painel/sites-meta.json`
- Use `_genericos` + bloco do nicho (Pré Treino, Creatinas, Tablets, etc.)
- Limites por nicho: `ingles_max`, `medico_tecnico_max`, `industrial_max`, `indicacao_medica_max`, `chavoes_estruturais_max`
- Banidos absolutos: `lineup`, `SKU`, `ASIN`, `trade-off`, `hardcore`, `datasheet`, `notificado`, `peers`, `claim`, `stack`

### Auto-check capitalização + duplicação

- Duplicação contígua: `([a-zA-ZÀ-ÿ\s]{8,40})\1` → remover duplicado
- Bullet minúsculo: `<strong>[a-z]` em pros/cons → capitalizar
- Minúscula após ponto: `\. [a-z]` (excluir URLs) → capitalizar
- Termo entre parênteses dup: `([a-zA-ZÀ-ÿ]{5,30}) \(\1\)` (ex: "formigamento (formigamento)")
## Armadilhas recorrentes

### 1. H1 em vez de H2 na abertura
Hábito de modelos LLM começar HTML com `<h1>`. Proibido aqui — o artigo já tem H1 no title do frontmatter. Sempre `<h2>`.

### 2. Mencionar produto específico FORA das seções permitidas
"A Epson L3250 lidera o segmento" em "Como escolher" → NÃO. Generaliza: "marcas brasileiras com sistema EcoTank dominam o segmento de tanque". Produtos específicos podem ser citados em FAQ, Conclusão, Melhor Marca e como âncoras de preço em "Vale a pena" (ex: *"de R$ X (Modelo Y) a R$ Z (Modelo W)"*).

### 3. Slug inventado pra linkagem
IA frequentemente inventa `/melhor-impressora-laser-barata/` quando esse artigo NÃO existe. Antes de salvar, eu Grep mentalmente todos os `href` e confiro contra peer list. Se inventar → regenero o trecho.

### 4. Link Amazon FORA das seções permitidas
Links Amazon em "Vale a pena" ou "Como escolher" = ERRO (essas 2 seções são educativas, sem CTA). Em "Melhor marca", "FAQ" e "Conclusão" são PERMITIDOS e até esperados (canônico tem ~10-20 links Amazon distribuídos nessas seções).

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

### 10. Âncora ≠ keyword / slug derivado do keyword
Três erros: (1) âncora descritiva em vez da keyword do destino (`<a href="/melhor-impressora-tanque-de-tinta/">opções de tanque</a>` → use `melhor impressora tanque de tinta`, singular); (2) âncora de produto sem marca (`<a>L4360</a>` → `Epson EcoTank L4360`); (3) derivar o slug do keyword → 404 (`/impressora-boa-e-barata/` quando o arquivo é `impressora-barata.mdx`). Use sempre o slug REAL e a keyword/nome completo como âncora.

### 11. Concorrente parafraseado óbvio
Se user colou texto da Buscapé e o guide reusa frase quase literal, é cópia (mesmo sem aspas). Reescrever com ângulo próprio.

### 12. Citar comprador no guide
"Compradores recorrentemente preferem..." → PROIBIDO. Substituir por linguagem analítica: "Para uso doméstico, o critério principal é..." ou "Quem imprime muito tende a recuperar...".

### 13. Gerar só 1 H2 (estrutura antiga)
Versão da skill pré-1.8.2 induzia "abertura com 1 H2 + H3 dentro". Estrutura atual é **5 H2 obrigatórios** (Vale a pena / Como escolher / Melhor marca / FAQ / Conclusão). Faltar qualquer um = ERRO. Conferir contagem de H2 antes de salvar.

### 14. Faltar FAQ ou Conclusão
Modelo tende a parar em "Melhor marca" achando que cobriu o tema. Mas FAQ e Conclusão são obrigatórios pelo PADROES.md + são onde leitor decide a compra (FAQ responde dúvidas pré-compra; Conclusão dá recomendação clara). Sem essas 2 seções, guide fica fraco em SEO + UX.

### 15. Inflar "Vale a pena" sem ancorar preço
P2 da seção "Vale a pena" pede âncoras de preço reais do lineup. Modelo tende a generalizar ("os preços variam") — VAI BUSCAR números reais nas bíblias (`snapshot.precoBRL`) ou no frontmatter do `.mdx` (`schemaPrice` dos produtos) e citar 2-3 modelos pra ancorar a faixa.

### 16. FAQ genérica sem produto específico
"FAQ: Qual a melhor X? Resposta: depende das suas necessidades..." — FAQ inútil. Régua: cada FAQ deve ter resposta CONCRETA, geralmente com 1-2 links Amazon de produtos específicos do lineup que cobrem a resposta. Sem link Amazon ≠ FAQ ruim, mas sem CONCRETUDE = ruim.

### 17. Parágrafos densos com 3+ conceitos
Cada parágrafo deve cobrir **1 ideia principal** (com 1-2 conceitos relacionados, no máximo). Quando um parágrafo lista 3+ conceitos distintos com `<strong>` dedicado pra cada (ex: "Wi-Fi Direct, AirPrint, Mopria e Bivolt automático" tudo junto), divide em 2 ou 3 parágrafos menores. **Regra prática**: se você usa 3+ tags `<strong>` no mesmo parágrafo pra introduzir conceitos diferentes, considere dividir.

Exemplos de divisão (corrigindo padrão denso):

❌ **Denso (1 parágrafo, 4 conceitos)**:
```html
<p><strong>Wi-Fi Direct</strong> permite imprimir sem roteador. <strong>AirPrint</strong>
é o padrão Apple. <strong>Mopria</strong> é o equivalente Android. <strong>Bivolt
automático</strong> é diferencial brasileiro: liga em 110V ou 220V sem configuração.</p>
```

✅ **Dividido (2 parágrafos, 1 ideia cada)**:
```html
<p>Pra impressão pelo celular, três padrões cobrem os principais cenários: <strong>Wi-Fi
Direct</strong> permite imprimir sem roteador (útil em redes instáveis), <strong>AirPrint</strong>
é o padrão Apple (iPhone/iPad imprimem sem app), <strong>Mopria</strong> é o equivalente
Android.</p>

<p><strong>Bivolt automático</strong> é diferencial brasileiro: a impressora liga em 110V ou
220V sem configuração, prático pra quem muda de casa ou cidade.</p>
```

Mesma regra aplica em listas tipo "tipos de impressora" (cartucho/tanque/laser) — cada tipo merece parágrafo próprio pra leitor escanear. Leitor cansa em parágrafos densos; SEO também premia conteúdo escaneável.

### 18. Negrito esparso (frases conceituais sem destaque)
Inverso da armadilha 17. Modelo tende a negritar SÓ specs numéricos (R$ 450, 12W, 4.500 páginas) e deixar frases-chave conceituais em texto normal. Resultado: guide com 2 strongs/1k chars (visualmente fraco) em vez do alvo 4-5/1k dos canônicos.

Antes de salvar, escaneie cada parágrafo procurando **frases-chave conceituais sem negrito**. Padrões típicos a negritar:
- *"o ponto que define X é Y"* → negritar Y
- *"diferente das outras opções, esta tem Z"* → negritar Z
- *"o trade-off real: ..."* → negritar a coisa que é o trade-off
- *"o que importa de verdade é A"* → negritar A
- *"perfil de quem imprime B"* → negritar B (perfil)

**Exemplo real do canon melhoraspirador** (`<h3>Peso e ergonomia</h3>`):

```html
<p>O peso varia bastante: de <strong>1,43 kg</strong> nos modelos mais
compactos até cerca de <strong>5 kg</strong> nos mais potentes. Para
quem limpa escadas, sofás ou usa o aspirador no modo portátil com
frequência, cada grama extra pesa no braço.</p>

<p>Além do peso total, vale observar <strong>onde o peso se concentra</strong>.
Modelos com motor no topo da haste ficam mais leves na base e entram
embaixo de móveis com facilidade, enquanto modelos com motor na base
oferecem mais estabilidade no piso. Bocais com <strong>rotação 180° ou 360°</strong>
também ajudam: acompanham o movimento da mão e reduzem o esforço em
manobras.</p>
```

5 strongs em ~50 palavras de conteúdo: 2 specs numéricos (1,43 kg, 5 kg) + 1 frase conceitual destacada (onde o peso se concentra) + 1 spec técnico (rotação 180°/360°). É o ritmo visual que diferencia bom de mediano.

### 19. Links Amazon nas seções "educativas" (Vale a pena / Como escolher)
Régua dura: links Amazon SÓ em Quais as melhores marcas + FAQ + Conclusão. Modelo violou várias vezes na prática (2026-05) colocando links de "Modelo Y" como âncora em Vale a pena P2 quando a régua é texto SIMPLES sem link. Fix: em Vale a pena, citar modelos como referência de preço *"Os preços vão de R$ X (Modelo Y) a R$ Z (Modelo W)"* mas com **Modelo Y / Modelo W em texto puro, sem `<a>`**. Em Como escolher, mesmo critério: produto se for citado vira texto simples.

Verificação antes de salvar: `grep -c 'amazon\.com\.br' nas seções 1-2 do guide` deve retornar **0**.

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

### Auto-check de capitalização + duplicação (régua v1.18.3, canon 2026-05-28)

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

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), validação fica editorial — eu (modelo) sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial (link interno inventado, char count em 15100, tag fora da allowlist). Mitigação principal: hard-validation manual de links internos contra peer list antes de aplicar; se falhar, regenero o trecho.
