---
name: artigo-guia-escrever
description: Escreve o guideContent do artigo (HTML 'Vale a pena / Como escolher / Melhor marca / FAQ / Conclusão') + análise de concorrentes reusável por keyword. Aceita URL do painel OU site/slug. EXIGE concorrentes da keyword EXATA: carrega análise existente de _data/competitor-analyses/{keyword-slug}.md (match exato do slugify da KEYWORD — nunca keyword vizinha, nunca o slug do arquivo) ou o user cola 1-3 'Como escolher' da SERP; sem isso PARA e pede. Salva análise + texto cru pra reuso. 5 H2 base + extras dirigidos pela SERP, 6-25k chars, links Amazon só em Marca/FAQ/Conclusão (tag-aware), 2-4 links internos contextuais (âncora = keyword do destino, slug REAL, não na Conclusão). Substitui só o guideContent; backup + commit + push + sync VPS.
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

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:generate_guide`. O conteúdo essencial está duplicado abaixo pra autocontenção. **Esta SKILL.md é a fonte viva** desta execução (o `agent-prompts.json` é o espelho do path do painel/API e pode defasar — o projeto roda via Claude Code).

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
- **Estrutura: 5 H2 base obrigatórios + H2 extras dirigidos pela SERP.** Os 5 base (Vale a pena / Como escolher / Melhor marca / FAQ / Conclusão) são sempre obrigatórios; H2 informacionais extras (O que é / gasta energia / receitas / como limpar) entram quando a análise de concorrentes mostra intenção informacional. Faltar qualquer base = ERRO. Ver "Régua editorial — ESTRUTURA" abaixo.
- **Links Amazon: tag-aware.** PROIBIDOS em "Vale a pena" e "Como escolher" (educativas). PERMITIDOS em "Melhor marca" (link de busca da marca), "FAQ" e "Conclusão" (recomendações de produto). Formato: `?tag={tag}&linkCode=ogi&th=1&psc=1` se tag preenchida; URL crua se vazia.
- **Linkagem interna: 2 a 4 links (ideal ~3), contextuais e naturais** pra **peer articles reais do mesmo site** (slug REAL do arquivo, NUNCA derivado do keyword). Régua de quantidade canon (Marcelo 2026-06-09): 2 mín · ~3 ideal · 4 máx (ou o total de peers, se o site tiver menos de 2; 0 se for o 1º artigo do site **ou se nenhum peer passar no teste do "encaminhamento útil"** — ver "Desempate" em "Linkagem interna"). Âncora = **keyword do destino (singular preferido)**; link de produto = **nome completo COM marca**. Sem `target="_blank"`, sem `rel="nofollow"` (links internos passam autoridade). Ver "Linkagem interna".
- **Sem travessão (—).** Use vírgula, ponto, dois pontos ou parênteses.
- **Sem ponto-e-vírgula (;).** (régua 2026-06-20) Tem cara de IA na voz conversacional. Troque por "." (sentença nova), "," (pausa) ou "()". Vale em TODOS os campos. AUTO-CHECK antes de gravar: depois de remover entidades (&amp;, &#..;) e a querystring dos links de afiliado, não pode sobrar ";" no texto.
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
   - **⚠ `_sites_aplicaveis` é o gate do bloco de nicho (canon 2026-08-15):** se o slug do site não está na lista do bloco, **o bloco não vale** e sobra só o `_genericos`. Não force pelo `niche`. Reporte como sugestão de incluir o site no JSON, nunca como defeito do texto.
   - **O `_genericos` vale SEMPRE e é o que mais dispara:** `termos_banidos_absoluto`, `chavoes_estruturais_max` (as 4 variantes de "seleção" têm cap **0**) e `industrial_max` (`declarado` 3, `fabricante` 12). Conte ele antes de qualquer bloco de nicho.

1. **Parse args**: detecta URL vs canônico, extrai `site` e `slug`. Valida `[a-z0-9-]+` em ambos.

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   bash scripts/git-pull-seguro.sh "skill-artigo-guia-escrever-temp"
   ```
   Painel VPS commita+pusha automaticamente quando user cria/edita conteúdo na UI; Mac local pode estar 5-30s atrás. Sem este pull, skill pode ler estado stale e abortar com falso "X não existe localmente". Se pull falhar (rede offline, conflito), seguir mesmo assim.

2. **Read `.mdx`**: `Read sites/{site}/src/content/reviews/{slug}.mdx`. Se 404, abortar.

3. **Parse frontmatter** mentalmente:
   - `title` (vira o "Como escolher {keyword}" da abertura — extrair só a parte da keyword, sem o ":")
   - `keyword` — se ausente, fallback: `title.split(':')[0].toLowerCase().trim()`
   - **3.1 (canon 2026-08-15) Checagem BARATA dos concorrentes, aqui e não no passo 8:** com o `keyword` em mãos, `ls docs/painel/_data/competitor-analyses/{slugify(keyword)}.md`. Não existe E o usuário não colou textos → é o **Cenário C**: pare AGORA (mensagem do Cenário C) — antes de carregar bíblias e peers. Se `PIPELINE=yes` (invocada pela clone/fila), a clone já checou no pré-flight dela; se mesmo assim faltar, devolva "sem análise da keyword exata" como erro e não espere.
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
   - **Se existir `docs/painel/_data/competitor-sources/{keyword-slug}/` (texto cru, canon 2026-06-30), LEIA também** — é a fonte de fidelidade estrutural (headings reais) pra derivar os H2. Precedência: cru > ficha (a ficha vira só a síntese de gaps/clichês/ângulos). Keywords antigas sem cru → só a ficha topic-only, como antes.
   - Carrega como contexto rico (topical map, gaps, o que evitar, ângulos)
   - **NÃO regera a análise nem o cru** (preserva os existentes)
   - Reporta no chat: "📊 Análise de concorrentes carregada de `_data/competitor-analyses/{kw}.md` (gerada em DD/MM/YYYY)"

   ### Cenário B — análise NÃO existe + user colou textos de concorrentes
   - Cada texto truncado em 16k chars (mais generoso que os 8k antigos — análise rica)
   - **Salvo o texto cru colado VERBATIM** em `competitor-sources/{keyword-slug}/` (passo 10c) — fonte dos headings reais
   - Eu analiso os textos e produzo a análise estruturada (passo 10b)
   - Uso os **headings reais do cru** pra derivar a estrutura (H2/H3/FAQ) + a ficha como topical map
   - Crio o `.md` da análise (10b) E salvo o cru (10c)

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

10c. **Salvar o TEXTO CRU dos concorrentes, além da ficha** (canon 2026-06-30). Sempre que o user colar concorrentes (Cenário B), salve o texto colado VERBATIM em `docs/painel/_data/competitor-sources/{keyword-slug}/` (um `.md` por concorrente, ou um só concatenado com separador `--- concorrente N ---`). Criar o diretório se não existir.
    - **Por quê:** a ficha (10b) é um resumo **lossy** — perde o NÍVEL de cada tópico (se o concorrente tratou como seção/H2, critério/H3 ou item de FAQ). O cru preserva os **headings reais**, que é o que a derivação de estrutura precisa pra decidir H2 vs H3 vs FAQ sem chutar. A ficha continua (síntese + reuso humano); o cru é a fonte de **fidelidade estrutural**. Custo-benefício: salvar o cru é ~de graça e elimina recolar no futuro.
    - **Precedência de leitura da estrutura (passo 8/9): cru > ficha.** Se existir `competitor-sources/{keyword-slug}/`, leia o cru pra extrair os headings e derivar os H2. Se só houver ficha (keywords antigas, pré-2026-06-30), use a ficha topic-only como antes. Nenhum dos dois → Cenário C (pedir concorrentes).
    - **Anti-cópia (DURO):** o cru é material de pesquisa, NUNCA renderizado. Proibido copiar/parafrasear óbvio dele — a prosa do guia é original (a régua "concorrente parafraseado óbvio" vale com mais força agora que o texto fica salvo ao lado).

11. **Validar mentalmente** antes de salvar:
    - **6.000-25.000 chars** total (alvo 12-18k)
    - **5 H2 base presentes na ordem relativa**: `Vale a pena` → `Como escolher` → `Melhor marca` → `Perguntas Frequentes` → `Conclusão`. **H2 extras informacionais permitidos** (O que é / gasta energia / receitas / como limpar) quando a SERP pedir, intercalados (+2 a +4, teto 9 H2 total); cada extra educacional = ZERO link Amazon; cada tópico em UM lugar só (regra anti-duplicação)
    - Primeiro tag = `<h2>` (NÃO `<h1>`, NÃO `<p>`)
    - HTML allowlist OK (Grep mental por tags fora da lista)
    - 2-4 links internos (ideal ~3; 0 só sem peers): cada `href="/{slug}/"` aponta pra slug REAL da peer articles list
    - Links Amazon: ZERO em "Vale a pena" e "Como escolher"; PERMITIDOS em "Melhor marca" (busca), "FAQ" e "Conclusão" (recomendação). Tag-aware do site.
    - Sem travessão `—` nem `–`
    - Sem `<h1>` (artigo já tem H1 no title)
    - Sem `<img>`, `<table>`, `<script>` etc
    - Citação de produto específico só em FAQ/Marca/Conclusão (+ âncoras de preço em "Vale a pena" P2)
    - Sem citação a "compradores"/"reviews"/"avaliações" como entidade

12. **Backup** ANTES de sobrescrever (paridade exata com pattern do painel, server.ts:4994):
    ```bash
    # raiz do repo — o cwd do Bash reseta pra ~/Documents/Claude em sessão continuada; sem isto o mkdir cria a árvore LÁ (medido 03/09/26)
    cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" && test -f docs/painel/sites-meta.json || { echo "⛔ cwd errado ($(pwd)): rode a partir da raiz do ProjetoAfiliados"; exit 1; }
    DAY=$(date +%Y-%m-%d); TIME=$(date +%H%M%S); SITE={site}; SLUG={slug}
    PROJ=$(pwd)  # raiz do repo — garantida pela guarda acima, não pelo cwd inicial da sessão
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
    git commit --only --no-verify -m "feat({site}): guia 'Como escolher' de {slug} escrito via skill (+ análise de concorrentes pra keyword '{keyword}')" \
      -m "Co-Authored-By: {modelo da sessão} <noreply@anthropic.com>" \
      -- sites/{site}/src/content/reviews/{slug}.mdx \
         docs/painel/_data/competitor-analyses/{keyword-slug}.md
    git push origin main
    ```
    `--no-verify` é OBRIGATÓRIO: o pre-commit hook roda `audit-article.ts` no artigo staged e bloqueia se houver erros — artigo ainda em construção sempre tem.

15. **Disparar git pull no painel da VPS**:
    ```bash
    bash scripts/painel-vps-pull.sh
    ```
    Falha graciosamente se `.env.painel-skills` não existir.

15.5. **CONFIRMAR QUE A ANÁLISE FOI GRAVADA** (canon 2026-08-20 — gate, não
    opcional). Nos cenários B/override, depois dos passos 10b e 10c:

    ```bash
    ls -la docs/painel/_data/competitor-analyses/{keyword-slug}.md
    ls -la docs/painel/_data/competitor-sources/{keyword-slug}/
    ```

    **Se algum não existir, GRAVE AGORA** e só então siga. E reporte o resultado
    no passo 16, em uma linha, dizendo se gravou ou não.

    **Por que virou gate:** os passos 10b e 10c não tinham confirmação nenhuma,
    então quando a sessão pulava a gravação o material colado sumia **sem
    ninguém perceber**. Medido em 2026-08-18: o cluster de creatina inteiro, 7
    keywords, estava sem ficha salva — e os concorrentes tinham sido colados em
    todas. A recuperação custou reconstruir 6 análises a partir dos guias da
    rede.

    O custo de não ter gravado aparece semanas depois e em outro lugar: a
    `artigo-clonar-em-massa` aborta no passo 4b concluindo que "a análise não foi
    feita". Ela foi — o repo é que perdeu. Perda silenciosa de insumo que o
    humano colou é a pior classe de falha desta skill, porque o trabalho de
    recolar é dele, não do agente.

16. **Reportar no chat**:
    - char count do HTML do guide + número de parágrafos + lista de links internos
    - path do `.mdx` salvo
    - **Coverage report** (se análise foi usada):
      - "Cobri N/M tópicos do concorrente"
      - "Adicionei K tópicos extras (das bíblias / gaps): X, Y, Z"
    - **Se análise foi criada/atualizada: diga explicitamente se a gravação foi
      CONFIRMADA no passo 15.5** (path + ficha e cru). "Salvei" sem ter olhado é
      exatamente o que fez 7 keywords sumirem.
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

### Estrutura: 5 H2 base obrigatórios + H2 extras dirigidos pela SERP

**Os 5 H2 base são SEMPRE obrigatórios, nesta ordem relativa:**

```html
<h2>Vale a pena comprar um/uma {keyword} em {ano}?</h2>
<h2>Como escolher o melhor/a melhor {keyword} em {ano}?</h2>
<h2>Qual a melhor marca de {keyword} em {ano}?</h2>
<h2>Perguntas Frequentes</h2>
<h2>Conclusão</h2>
```

Eles carregam a intenção comercial/comparativa + os links de afiliado (Marca/FAQ/Conclusão). Faltar qualquer um dos 5 base = ERRO.

⚠️ **Os 5 base são SLOTS, e coincidir com outro site da rede é ESPERADO — não é duplicação a corrigir.** `Perguntas Frequentes` e `Conclusão` já são obrigatoriamente idênticos em toda a rede; os outros três saem do mesmo template acima com a keyword trocada, então artigos da mesma keyword em sites irmãos vão convergir por construção. **NÃO invente variação ("Vale investir em…", "Compensa comprar…", "Que marca escolher?") para fugir de um comparador de duplicata** — isso quebra a consistência DO PRÓPRIO SITE, que é o que o leitor e o Google veem, e não compra nada em SEO. Mesma lógica de [[afiliados.regras.dedup-crosssite-nao-reescrever-por-jaccard]]: não reescrever por jaccard.
- **Nunca coloque nome de marca do lineup num H2 base** (ex.: "Epson ou Fujifilm: qual marca…"). O heading é estrutural e o lineup muda — o título passaria a mentir. Nome de marca vive nos H3 de "Melhor marca".
- Medido em 2026-07-30 (compraguia, 3 artigos): os **H3 divergem sozinhos** (1 idêntico em 49, e o único era a taxonomia "Cartucho, tanque de tinta ou laser"), incluindo as perguntas da FAQ. Diferenciação é trabalho dos H3 e da prosa, não dos slots.

**Além dos 5 base, ADICIONE H2 extras quando a análise de concorrentes mostrar que a SERP da keyword é informacional** (régua canon 2026-06-29). A estrutura é **dirigida pela SERP, não um molde fixo**:

- Se os concorrentes da keyword usam H2 informacionais em forma de pergunta ("O que é {keyword}?", "{keyword} gasta muita energia?", "Que receitas dá pra fazer?", "Como limpar {keyword}?"), **crie esses H2 no guide** — é o que o Google premia pra keyword com intenção how-to/informacional. Caso-origem: `melhorairfryer-com/melhor-air-fryer-oven` (2026-06-29), onde 3 de 3 guias completos concorrentes usavam só H2 informacionais e nenhum usava o frame comercial.
- **Critério pra incluir um H2 extra**: o tópico é **SEÇÃO (capítulo próprio) em 2+ concorrentes** OU é um gap real da SERP. **Derive do TEXTO CRU dos concorrentes** (`competitor-sources/`, passo 10c) olhando os **headings reais** deles: assunto a que eles dão SEÇÃO → vira H2; assunto que aparece só na FAQ deles → fica na FAQ; assunto que é critério dentro de "Como escolher" → vira H3. **Não chute o nível pela ficha topic-only** (ela achata seção/FAQ/critério — foi a causa-raiz do erro abaixo). Não invente seção que ninguém busca.
- **⚠ NUNCA espelhe a estrutura de um artigo de OUTRA keyword** (nem de um irmão de keyword diferente). Derive SÓ dos concorrentes DESTA keyword. Caso real (2026-06-30): espelhar os H2 do `melhor-air-fryer-oven` (categoria nova, SERP informacional, ganhou "O que é/energia/receitas/limpar") no `melhor-air-fryer` (keyword madura/comparativa, onde esses temas vivem na FAQ) inflou a estrutura indevidamente. Oven ≠ air fryer: mesma família, SERPs diferentes, estruturas diferentes.
- **Teto: +2 a +4 H2 extras** (guide com 7-9 H2 no total). Acima disso vira walls of text.
- **6º opcional clássico** ("Por que confiar neste conteúdo", entre FAQ e Conclusão) continua valendo e conta dentro do teto.
- Keyword **comparativa** (ex: "melhor tablet custo benefício", "melhor impressora") em geral NÃO pede extras — segue enxuta nos 5 base. Os extras são pra keyword **informacional** que a SERP pedir.

**Política de links dos H2 extras**: por padrão são **educacionais → ZERO link Amazon** (mesma regra de "Vale a pena" e "Como escolher"). Links de afiliado seguem concentrados em Marca/FAQ/Conclusão. Link interno (peer/produto) pode, se contextual.

**Posição/ordem dos extras:**
- Informacionais de definição/consumo ("O que é", "Gasta energia") → perto do topo (logo após "Vale a pena", ou até antes dele se a SERP abrir sempre com "O que é").
- De uso ("Que receitas", "Como limpar") → depois de "Como escolher", antes da FAQ.
- Os 5 base mantêm a ordem relativa ENTRE SI (Vale a pena → Como escolher → Marca → FAQ → Conclusão); os extras se intercalam.

**🚨 REGRA ANTI-DUPLICAÇÃO (a que faz os extras valerem a pena):** cada tópico mora em **UM lugar só, com profundidade total**. Quando você cria um H2 informacional, ele **ABSORVE** a menção rasa que iria pros 5 base — não soma por cima (senão dispara o check `redundancy` do audit). Exemplos:
- Criou "O que é {keyword}?" → o "Vale a pena" PARA de definir o produto e foca na DECISÃO de compra (compensa? pra quem? quando não vale).
- Criou "{keyword} gasta energia?" / "Que receitas?" / "Como limpar?" → essas perguntas SAEM da FAQ (viram H2 próprios). A FAQ fica com o que sobra (comparações, "X ou Y", tamanho/medida, "qual a melhor").
- Distinção legítima que NÃO é duplicação: "Facilidade de limpeza" dentro de "Como escolher" = **o que procurar na compra** (porta removível, antiaderente); "Como limpar" = **a rotina de limpeza**. São ângulos diferentes.

- **`em {ano}`** é padrão recomendado (atualidade SEO) mas pode ser omitido se a frase fica forçada (keyword já tem ano implícito, soa redundante, etc).
- **"Perguntas Frequentes"** e **"Conclusão"** ficam **sem** `em {ano}`.
- **NUNCA** `<h1>` (artigo já tem H1 no title). **NUNCA** começar com `<p>` antes do primeiro H2.

### Régua por seção

#### 1. Vale a pena comprar...?
**3 parágrafos:**
- **P1**: argumento central da categoria + critérios estruturais (ex: tanque vs cartucho, ecossistema, perfis de uso).
- **P2**: âncoras de preço REAIS do lineup, citando 2-3 modelos como referência (esta é a EXCEÇÃO à régua "geral"). Frase literal e variada: "O mais barato do comparativo é o Modelo Y, por cerca de R$ X, e o mais caro é o Modelo W, por volta de R$ Z." — NÃO a mesma abertura em todo artigo ("Os preços desta seleção vão de…" apareceu em ~45 guias e virou assinatura).
- **P3**: quando **NÃO** vale a pena comprar (perfil errado, alternativas melhores). Importante editorialmente — protege credibilidade. Sem o rótulo-molde "Quando não vale a pena:" (43 guias): escreva a frase ("Não compensa para quem…").

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

Régua de cada H3 (profundidade por completude, **não cota** — régua canon 2026-06-29):
- Título: `<h3>{Marca}: {posicionamento curto editorial}</h3>` (ex: *"Samsung: a marca mais completa para Android no Brasil"*)
- **1 a 2 parágrafos, o que a marca pedir** (não trave em 1 parágrafo raso). Cada marca deve cobrir, **quando o dado existe na bíblia/categoria**: posicionamento + **linha/modelos principais na categoria** + **diferencial técnico real** + **pra qual perfil serve** + (opcional) **uma ressalva honesta** (onde a marca peca). Fôlego de referência ~60-110 palavras — orientação, NÃO meta a bater.
- **Sem ranking absoluto** entre marcas — cada uma cobre um cenário diferente
- **Pode incluir link Amazon de busca da marca** (formato `<a href="https://www.amazon.com.br/s?k={termo}&tag={affiliateTag}" rel="nofollow" target="_blank">{Marca}</a>`)
- Manter **objetivo** e baseado em fatos da bíblia/categoria (NÃO inventar "história da empresa" nem encher de adjetivo). Profundidade vem de cobrir mais ângulos REAIS, não de prosa decorativa.
- ⚠ **Anti-padding**: se a marca só tem 1 diferencial honesto, 1 parágrafo basta. Não invente segundo parágrafo só pra "engordar". Completo ≠ comprido.

#### 4. Perguntas Frequentes
**5-8 subseções `<h3>`** cada uma com a pergunta como título + resposta **completa** (não resumida).

Régua de cada FAQ (profundidade por completude, **não cota** — régua canon 2026-06-29):
- Pergunta como leitor digitaria no Google (ex: *"Qual o melhor X em 2026?"*, *"Vale a pena Y?"*, *"X ou Z?"*)
- **Resposta que ganharia o featured snippet / People Also Ask**: completa o suficiente pra ser a melhor resposta da SERP. Tipicamente **2-4 frases (~40-80 palavras)**, e **use lista curta (`<ul>`/`<ol>`, 3+ itens) quando o formato ajudar** (passo a passo de limpeza, "o que NÃO colocar", checklist). Resposta de 1 frase raramente vence a caixa de destaque.
- Direta e concreta (sem rodeio), mas **cobre a dúvida inteira** — antecipa o "e se...", dá o número/critério, fecha com a recomendação prática.
- **PODE citar produtos específicos do lineup com link Amazon** (ex: *"Para a maioria das pessoas, o Samsung Galaxy Tab S10 Lite é a melhor compra..."* com link Amazon do ASIN)
- Distribuir 1-2 links Amazon por FAQ que justifique recomendação
- Pergunta-teste: *"Esta FAQ responde algo que o leitor REALMENTE perguntaria?"*
- ⚠ **Anti-padding**: se a pergunta se resolve em 2 frases, PARE em 2 frases. Não enrole pra atingir tamanho. Completo é responder a dúvida toda, não escrever muito.

#### 5. [OPCIONAL] Por que confiar neste conteúdo
1-3 parágrafos sobre metodologia editorial (sem citar Amazon/avaliações — viola memória do projeto). Use só quando há diferencial real a comunicar.

#### 6. Conclusão
**2 parágrafos:**
- **P1**: recomendação central do guide (1-2 modelos top com link Amazon)
- **P2**: alternativas por perfil (modelos específicos por nicho ou redireciona pra artigos peer relacionados)
- **Tom resolutivo** — leitor sai com decisão tomada

### Tamanho típico

**Range válido: 6.000-25.000 chars.** Guia comparativo (5 H2 base) costuma ficar em 8-18k; keyword informacional com H2 extras, em 16-22k. **Isso é medida do que sai quando os tópicos são cobertos, não meta**: não escreva para chegar num número (o enchimento vira cauda ", então… / o que…" e é onde a prosa perde naturalidade).

Canônicos atuais (referência):
- `melhor-tablet-custo-beneficio` — 17.847 chars
- `melhor-aspirador-de-po-vertical` — 18.923 chars
- `melhor-tablet-samsung` — 20.073 chars
- `kindle-qual-o-melhor` — 15.518 chars

Menos que 6k provavelmente faltou cobertura; mais que 25k vira walls of text. **Profundidade vem de cobrir mais tópicos REAIS (H2 informacionais, marca/FAQ completas), nunca de encher parágrafo (ver anti-padding nas seções 3 e 4).**

### Listas (opcionais, dentro das seções)

`<ul>` ou `<ol>` quando faz sentido enumerar critérios discretos. **Mínimo 3 itens**:

```html
<p>Antes de comprar, verifique:</p>
<ul>
  <li>Potência de sucção (em Pa ou W)</li>
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
- Marcas no texto corrido fora da seção "Qual a melhor marca" (a marca aparece como nome próprio, não como destaque)

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
| Vale a pena | **0 Amazon** (pode ter peer/home interno) | Peer/home `/slug/` ou `/` | Sem CTA Amazon. Bom spot pra ligar a categoria-mãe/home contextualmente. Citações de modelo como âncora de preço (P2) em texto SIMPLES |
| Como escolher (H3s) | **0 Amazon** (pode ter peer interno) | Peer `/slug/` | Sem CTA Amazon. Pode cross-linkar critério com artigo-irmão (ex: H3 "tanque vs cartucho" → guia de tanque) |
| Qual a melhor marca (H3s) | **1 por marca** + peer | Amazon search `/s?k=...` ou peer `/slug/` da marca | Search Amazon por marca; ou link pro guia-da-marca se existir como peer |
| Perguntas Frequentes | **2-4** | Peer `/slug/`, produto `/slug/` ou Amazon `/dp/` | FAQs comparativas/recomendativas — spot natural pra link peer contextual |
| Conclusão | **PRODUTO: 5-8** · **peer/home: evitar** | Produto `/slug/` ou Amazon `/dp/` (recomendação) | Recomendação de compra por nicho. **Links de navegação peer/home NÃO entram aqui** (decorativo) — eles vão nos spots contextuais acima |
| **Total alvo** | **~10-15** | majoritariamente internos, com 3-5 search Amazon nas Marcas | peer/home distribuídos contextualmente (NÃO na Conclusão); produto concentrado em FAQ/Conclusão |

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

- **2-4 links totais (ideal ~3)** no guide inteiro — régua de quantidade canon (Marcelo 2026-06-09): 2 mín · ~3 ideal · 4 máx (0 se o site não tiver peers ainda, **ou se nenhum peer passar no teste do "encaminhamento útil"** — ver "Desempate" em "Linkagem interna"). Já documentado em "Linkagem interna".
- **Contextual, NÃO na Conclusão (v1.24.0):** distribuir ao longo do texto, cada um no spot onde o tema do artigo-irmão aparece naturalmente. **Evite a Conclusão** pra links peer/home — fecho com link de navegação é decorativo. Melhor não forçar do que enfiar no fim.
- Bons encaixes: dentro de H3 de "Como escolher" pra cross-linkar critério com outro artigo (ex: H3 "Com fio ou sem fio" → "/melhor-aspirador-sem-fio-vertical/"); resposta de FAQ que toca no tema do irmão; "Vale a pena" pra apontar a categoria-mãe/home; H3 de marca pra apontar o guia daquela marca.

## Linkagem interna — contextual, estratégica, âncora = keyword (v1.22.0)

A skill carrega `[{slug, title, keyword, keywordPlural}]` dos OUTROS artigos do site (passo 6) + a lista de páginas de produto (`products/*.mdx`). Linkar é **contextual e estratégico**, não decorativo.

### Regra de OURO da âncora

- **Link pra ARTIGO peer**: a âncora é a **keyword do artigo de destino**, com **preferência pela forma SINGULAR** (plural só quando a frase exige). NUNCA âncora descritiva/genérica.
  - ✅ `<a href="/melhor-impressora-tanque-de-tinta/">melhor impressora tanque de tinta</a>`
  - ❌ `<a href="/melhor-impressora-tanque-de-tinta/">opções de tanque de tinta</a>` (âncora ≠ keyword)
- **Link pra PÁGINA DE PRODUTO** (hub-and-spoke): a âncora é o **nome COMPLETO do produto, COM a marca** (nunca só o modelo).
  - ✅ `<a href="/epson-ecotank-l4360/">Epson EcoTank L4360</a>`
  - ❌ `<a href="/epson-ecotank-l4360/">L4360</a>` ou `<a ...>EcoTank L4360</a>` (sem marca)

### ⚠ A FRASE em volta da âncora tem que fechar (canon Marcelo 2026-07-31)

A keyword nomeia um **GUIA** ("melhor whey protein"), não um produto do mundo. Encaixá-la como se fosse coisa concreta produz frase que ninguém fala. Medição na rede em 2026-07-31: **64 ocorrências publicadas em 19 sites** — todas nasceram AQUI, na criação, de obedecer "âncora = keyword" sem olhar as palavras anteriores. O `audit-linkagem.ts` agora emite `anchor-frase-quebrada`, mas o certo é não produzir.

- ❌ `combinar com um melhor pré-treino` · `a creatina rende mais somada a um bom melhor whey protein` · `o caminho é um melhor tablet para estudar`
- **Superlativo não aceita artigo indefinido em PT-BR.** Nunca `um/uma/bom/boa/outro/outra/qualquer` + `melhor…`.

**O singular é o alvo por razão de SEO**, não estética: é a forma que as pessoas **buscam**, e a âncora reforça essa keyword. Quando não couber, nesta ordem:
1. **Artigo definido** — `um melhor pré-treino` → `o melhor pré-treino`, **contraindo** a preposição: `a um`→`ao`, `a uma`→`à`, `de um`→`do`, `em um`→`no`.
2. **Moldura de destino** — `no guia de melhor pré-treino`. Imune a concordância (a keyword vira complemento, sem artigo antes).
3. **Plural** (`os melhores pré-treinos`) — aceito pelo script, mas é válvula de escape, não primeira opção. ⚠ exige `keywordPlural` preenchida.
4. Reescrever a frase.

⚠ **Só vale pra âncora com superlativo.** Em keyword sem "melhor" (`impressora barata`), o indefinido é CORRETO: *"vale ver uma impressora barata"*.

**`na/no` só se retomar um substantivo de destino na mesma frase:**
- ✅ `tem **guia** próprio **no** melhor tablet para trabalho` (o "no" retoma *guia*)
- ❌ `encontra as opções **na** melhor glutamina` (lê-se lugar físico)

### Padrão de frase de encaminhamento (canon Marcelo 2026-07-31)

Molde aprovado, com quatro traços:
1. **Nomeia o destino pelo que ele é** — `guia`/`artigo`/`comparativo` aparece na frase.
2. **Diz pra quem o link é** — abre segmentando o leitor (recorte, perfil, objetivo, estágio da decisão), pra ele saber se aquilo é pra ele antes de clicar. É o que separa encaminhamento útil de link protocolar.
3. **Verbo de leitura, não de compra** — veja, vale comparar, encontra mais, tem guia próprio.
4. **A frase existe PRA encaminhar** — não é frase sobre outro assunto com link enfiado no meio.

> "Pra ver só os isolados, veja o guia de **melhor whey protein isolado**."
> "Esse cenário de produtividade tem guia próprio no **melhor tablet para trabalho**."
> "Se o seu objetivo é o rendimento na academia, vale comparar com o nosso guia de **melhor pré-treino** antes de decidir."
> "Quem já pensa na marca encontra mais no guia de **melhor impressora hp**."

Recomendado, não obrigatório: link integrado ao texto vale quando a frase fecha (ex. *"vale olhar os melhores Kindles"*). O que não vale é a keyword enfiada como objeto de verbo no singular.

### Slug REAL — NUNCA derivar do keyword

O `href` é o **slug REAL do arquivo de destino** (da peer-list / pasta `products/`), copiado verbatim. **NUNCA derive o slug do keyword** (slugify do título). Foi exatamente assim que nasceu `/impressora-boa-e-barata/` (keyword "impressora boa e barata") quando o arquivo real é `impressora-barata.mdx` → 404 em produção. Se o destino é o `homeReviewSlug` do site, o href é `/` (a home), **não** `/{homeReviewSlug}/` (esse é filtrado do getStaticPaths → 404).

### Estratégia (contextual + sem órfão)

- Distribua os links ao longo do texto (não concentrar no fim), cada um num contexto que justifique a visita.
- Pense no grafo do site: linke os **irmãos mais relevantes** (ex: o guia do termo-head linka custo-benefício + tanque + barata; cada sub-artigo aponta de volta pra home via `/`). Evita artigo órfão/sub-linkado.
- **A home é um peer como qualquer artigo.** Ela é o `homeReviewSlug`, servida na raiz (`/` = dominio.com.br), âncora = a keyword dela (ex: "melhor impressora"). Os outros artigos DEVEM linká-la via `<a href="/">{keyword da home}</a>` (NUNCA `/{homeReviewSlug}/`, que é 404) — **não deixe a home órfã**. O `href="/"` CONTA como peer link (vale pros ≥2 distintos).
- Atributos: SEM `target="_blank"`, SEM `rel="nofollow"` (interno passa autoridade).
- Quantidade: **mínimo 2 peer ARTICLES DISTINTOS** (NUNCA repita o mesmo destino 2×), até 4 (ideal ~3), + os links de PRODUTO (hub-and-spoke, quantos forem naturais).
- **Só no guia**: todos os links internos (peer + produto) vivem **só no `guideContent`** (Como escolher / FAQ / Marca / Vale a pena / Conclusão). **NUNCA** na introdução nem nos reviews dos produtos (lá só vai link Amazon).
- **Onde colocar o link peer/home — contextual, EVITAR a Conclusão (v1.24.0):** cada link pra artigo-irmão ou pra home entra no spot onde o assunto aparece **naturalmente no meio do texto** — uma resposta de FAQ que toca no tema do artigo-irmão, a seção "Qual a melhor marca" (pra apontar o guia daquela marca), ou "Vale a pena" / "Como escolher" (pra ligar a categoria-mãe/home). **NÃO concentre links de navegação peer/home na Conclusão.** Link de navegação jogado no fecho é decorativo, não contextual; o ideal é evitar a Conclusão de vez pra esses links. Se não houver encaixe natural fora da Conclusão, **melhor não forçar o link** do que enfiá-lo no fecho.
  - ⚠ **Distinção importante:** essa régua é pra links **peer-article + home** (navegação entre artigos). Links de **PRODUTO** (hub-and-spoke `/{slug-produto}/` ou Amazon `/dp/`) **continuam OK na Conclusão** — ali são recomendação direta de compra, que é a função do fecho. O que sai da Conclusão é só a navegação inter-artigo.

### Hard-validation (antes de salvar)

1. Cada `href="/{slug}/"` existe em `reviews/` OU `products/`? Se não → 404, **regenerar com o slug real**. Nenhum aponta pro `homeReviewSlug` (esse vira `/`).
2. Âncora de peer == keyword do destino (singular preferido)? Âncora de produto contém a marca + é o nome completo?
3. **A FRASE de cada link fecha?** Reler a frase INTEIRA de cada `<a>` (não só a âncora): zero `um/uma/bom/boa/outro/outra/qualquer` antes de âncora com superlativo; `na/no` só se retomar guia/artigo; o artigo concorda em gênero com o núcleo REAL da keyword. Este é o passo que faltava até 2026-07-31 e que deixou 64 frases quebradas irem pro ar.
Se algo falhar, **corrijo o trecho antes de aplicar**. Não passa link inventado nem âncora fora da régua.

Se peer list está vazia (1º artigo do site), **ZERO links de peer**.

### ⚖️ Desempate: o piso de 2 NÃO vence o "encaminhamento útil" (canon 2026-08-10)

O piso de 2 e o molde de encaminhamento acima podem se contradizer num caso só: **o site TEM peers, mas nenhum responde a uma decisão que o leitor deste artigo está tomando.** Quando isso acontece, **a régua qualitativa ganha e o artigo vai a ZERO peer**, declarando o motivo no relatório. Não invente ponte pra bater o número.

**PRÉ-CONDIÇÃO MECÂNICA — sem ela a exceção NÃO está disponível:** o artigo tem **ZERO peers da mesma `category`**. Confira contando: `category` dos outros `.mdx` de `reviews/` do site. Se existe pelo menos 1 irmão da mesma categoria, **o piso de 2 vale integralmente** e não há discussão — linke. A exceção existe só pro caso em que o artigo é o primeiro da categoria dele num site que já tem outras categorias. Isso é deliberado: a exceção é julgamento, e julgamento sem porta de entrada verificável vira atalho (foi assim que a régua qualitativa perdeu pro piso numérico em primeiro lugar).

**Passada a pré-condição, o teste é a decisão, não a categoria.** Link peer bom responde a uma bifurcação ("tablet ou Kindle?"), a uma soma ("whey + creatina?") ou a uma ordem de prioridade ("fecha a proteína antes da glutamina"). Se você precisa construir o cenário em que o leitor iria pro outro artigo, o cenário não existe. Note que a pré-condição NÃO decide sozinha: os 34 links E-reader↔Tablet da rede passam por artigos que também têm 0 peer da própria categoria, e são links bons — o que os salva é o teste da decisão, não a contagem.

**Por que não basta "só linkar dentro da mesma categoria":** medido na rede em 2026-08-10, dos 942 links peer, 229 são cross-categoria — e 227 deles passam no teste da decisão (34 E-reader↔Tablet, 174 entre suplementos, 17 de fitness). Cortar por categoria mataria os 227 pra pegar os 2 ruins, e ilharia 31 artigos de suplemento que hoje se conversam legitimamente. A taxonomia também não ajuda: `Caixas de Som`, `Tablets` e `Impressoras` são todas subs de `Eletrônicos`, igualzinho a `Creatinas` e `Glutamina` sob `Suplementos`.

**Consequência aceita:** o `audit-linkagem.ts` e o critério `linkagem-fraca` vão emitir `warn` nesse artigo (o script conta peer bruto e não sabe avaliar decisão). É `warn`, não bloqueia `readyToLock`, e é o custo certo — melhor um warn conhecido do que um link que não serve ao leitor. Registre no relatório como exceção justificada.

**Caso-origem:** `compraguia/melhor-caixa-de-som-jbl` (2026-08-10). Site generalista com 19 peers de impressora, tablet e Kindle, nenhum de áudio. Pra cumprir o piso saíram 2 links protocolares ("quem monta a mesa de trabalho encontra mais no guia de melhor tablet"), removidos depois. Quando o site ganhar o 2º artigo de som, ele vira peer de mesma categoria e a linkagem acontece sozinha.

## Como usar as bíblias (contexto, não citação)

Carrego TODAS as bíblias dos produtos do artigo pra ENTENDER:

- Categoria editorial (tipo de produto, nicho)
- Critérios técnicos que diferenciam os produtos do lineup
- Specs e features comuns vs raras
- Perfis de uso que aparecem em `angulosConversao` — **filtrados pela keyword DESTE artigo** (canon Marcelo
  2026-09-04). A bíblia ordena os ângulos pelo produto, não pelo artigo, e perfil fora do recorte arrisca o
  guia ranquear pra outra busca. Esta skill já tem essa disciplina pra escolher a análise de concorrente
  ("keywords diferentes têm intenção, SERP e concorrentes diferentes"); ela vale igual aqui. Caso real: a
  bíblia de um monitor abre com `gamer-competitivo` como tema 1 de 5, e o artigo era de monitor **pra
  trabalho**. Régua irmã na `artigo-review-criar`, invariante do ângulo.
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
- **Português brasileiro editorial.** Sem gírias, sem anglicismos (inclusive os de sentido: "entrega", "cobre", "pede", "a conta"), "para" e não "pra". Ver "## Voz natural" abaixo.
- **NUNCA cite compradores/reviews/avaliações/Amazon** (padrão do projeto).

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

10. **Teto mecânico da mesma régua**: `docs/painel/_data/chavoes-por-nicho.json` → `_genericos.naturalidade_max` (daqui 2, pede 3, resolve 3, entrega 3, de verdade 1, trunfo/fôlego 1…) e `naturalidade_banidos` (0). A auditoria conta por artigo (página = metade); escreva já dentro do teto.

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

**Referência de DENSIDADE VISUAL (negrito por 1k chars, links Amazon só em Marca/FAQ/Conclusão)**: `sites/melhoraspirador/src/content/reviews/melhor-aspirador-de-po-vertical.mdx` (campo `guideContent`). ⚠ É referência de estrutura e densidade, **não de tom**: o texto dele tem o registro que a régua de 2026-08-15 corrige ("o de tomada não se cansa", "marca que só divulga watt está divulgando a conta de luz"). Para tom, siga o bloco acima.

## Filtros editoriais

- **Specs ambientais** (% reciclado, Energy Star, EPEAT, RoHS, "Planet Partners") → omitir no guide, salvo se tema `sustentabilidade` em `angulosConversao` de alguma bíblia.
- **Origem de fabricação** ("fabricado no Brasil", "made in X") → idem, salvo ângulo `produto-nacional`.
- **Variantes Amazon** (tamanhos de embalagem, voltagens específicas, cores) → omitir (não é critério de categoria, é variante).

## Regras duras (bloqueiam audit)

- **Estrutura: 5 H2 base obrigatórios** (Vale a pena / Como escolher / Melhor marca / FAQ / Conclusão). Faltar qualquer um dos 5 = ERRO. **H2 extras informacionais permitidos** (dirigidos pela SERP/análise de concorrentes, +2 a +4, teto 9 H2 total, educacionais = ZERO link Amazon, sem duplicar tópico dos 5 base). 6º opcional "Por que confiar" segue valendo.
- Primeira tag é `<h2>` (NÃO `<h1>`, NÃO começa com `<p>`).
- **6.000-25.000 chars** total no HTML (alvo típico 8-18k).
- HTML allowlist: `<h2>`, `<h3>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<a>`. Nada mais.
- **Links Amazon**: PROIBIDOS em "Vale a pena" e "Como escolher" (educativas). PERMITIDOS em "Melhor marca", "FAQ" e "Conclusão" (formato `?tag={tag}&...` tag-aware do site; também pode ser link de busca de marca `/s?k=...`).
- **Linkagem interna**: 2-4 links (ideal ~3) pra peer articles reais (slug REAL, NUNCA derivado do keyword), âncora = keyword do destino (singular preferido); link de produto = nome completo COM marca. Sem `target`/`rel`. **Links peer/home são contextuais e NÃO entram na Conclusão** (v1.24.0) — vão no spot onde o tema aparece (FAQ/Marca/Vale a pena/Como escolher). Links de PRODUTO podem ficar na Conclusão (recomendação).
- Sem travessão `—` nem `–`.
- Sem superlativos sem evidência ("o melhor disponível", "incomparável", "imbatível").
- **Voz natural** (canon 2026-08-15): verbo e substantivo no sentido do dicionário (produto não "resolve/entrega/pede/segura/cobre"), sem frase-sacada ("não é X: é Y", "é aí que…"), "para" no texto público, sem molde repetido de abertura de seção ("Não existe marca que ganhe em tudo", "Seja qual for o perfil", "Escolher bem é menos sobre X e mais sobre Y", "Quando não vale a pena:").
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
| `Pra a maioria/primeira` | `Para a maioria/primeira` |

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
| "diferencial central" | dizer o fato ("a fórmula não tem aditivos"); NÃO "o grande ponto é" (virou molde) |
| "posicionamento" | "categoria" |
| "segmento de X" | "tipo de X" |
| "proposta de valor" | drop sempre |

### Health absolutes YMYL banidos

- "uso regular é seguro" → qualificar
- "alternativa segura" → "alternativa mais leve"
- "não causa dano" → "sem evidência de impacto"
- "sem efeitos colaterais" → "efeitos colaterais raros"
- "cientificamente comprovado" / "100% seguro" → qualificar

**Aviso "consultar profissional" — o guia é a CASA dele (só nicho suplemento/saúde, régua v1.57.0):** em nicho de suplemento/saúde (creatina, whey, pré-treino, ômega, vitamina, suplementos, colágeno, beleza), o aviso geral de "conteúdo informativo, não substitui orientação de médico/nutricionista" vai AQUI no guia, **1 vez** (natural em "Vale a pena comprar…?" ou numa pergunta da FAQ), conciso. É o lugar canônico — os reviews dos produtos NÃO repetem esse encaminhamento genérico (vira ladainha, ~14×/artigo; ver régua na `artigo-review-criar` §13 e o check `disclaimer-saude-repetido` da `artigo-auditar`). Em nicho não-saúde (eletrônico/cozinha/tablet), não há esse aviso.

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
Links Amazon em "Vale a pena" ou "Como escolher" = ERRO (essas 2 seções são educativas, sem CTA). Em "Melhor marca", "FAQ" e "Conclusão" são PERMITIDOS: prefira link INTERNO (página de produto do site) quando ela existe; Amazon `/dp/` só quando não há página, e busca de marca `/s?k=` na seção de marca. Não há cota de links Amazon (a frase "canônico tem ~10-20" era de antes do hub-and-spoke; o canônico atual tem 0 `/dp/` no guia e 13 internos).

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
Versão da skill pré-1.8.2 induzia "abertura com 1 H2 + H3 dentro". Estrutura atual é **5 H2 base obrigatórios** (Vale a pena / Como escolher / Melhor marca / FAQ / Conclusão) + **H2 extras informacionais quando a SERP pedir** (régua canon 2026-06-29). Conferir que os 5 base existem na ordem relativa antes de salvar; os extras (O que é / energia / receitas / limpeza) são bem-vindos pra keyword informacional, sem duplicar tópico dos base.

### 14. Faltar FAQ ou Conclusão
Modelo tende a parar em "Melhor marca" achando que cobriu o tema. Mas FAQ e Conclusão são obrigatórios pelo PADROES.md + são onde leitor decide a compra (FAQ responde dúvidas pré-compra; Conclusão dá recomendação clara). Sem essas 2 seções, guide fica fraco em SEO + UX.

### 15. Inflar "Vale a pena" sem ancorar preço
P2 da seção "Vale a pena" pede âncoras de preço reais do lineup. Modelo tende a generalizar ("os preços variam") — VAI BUSCAR números reais nas bíblias (`snapshot.precoBRL`) ou no frontmatter do `.mdx` (`schemaPrice` dos produtos) e citar 2-3 modelos pra ancorar a faixa.

### 16. FAQ genérica sem produto específico
"FAQ: Qual a melhor X? Resposta: depende das suas necessidades..." — FAQ inútil. Régua: cada FAQ deve ter resposta CONCRETA, geralmente com 1-2 links Amazon de produtos específicos do lineup que cobrem a resposta. Sem link Amazon ≠ FAQ ruim, mas sem CONCRETUDE = ruim.

### 17. Parágrafos densos com 3+ conceitos
Cada parágrafo deve cobrir **1 ideia principal** (com 1-2 conceitos relacionados, no máximo). Quando um parágrafo lista 3+ conceitos distintos com `<strong>` dedicado pra cada (ex: "Wi-Fi Direct, AirPrint, Mopria e Bivolt automático" tudo junto), divide em 2 ou 3 parágrafos menores. **Regra prática**: se você usa 3+ tags `<strong>` no mesmo parágrafo pra introduzir conceitos diferentes, considere dividir.

Ex.: "Wi-Fi Direct / AirPrint / Mopria / Bivolt automático" com `<strong>` em cada um num parágrafo só → separe: os 3 padrões de impressão pelo celular num parágrafo, o bivolt em outro.

Mesma regra aplica em listas tipo "tipos de impressora" (cartucho/tanque/laser) — cada tipo merece parágrafo próprio pra leitor escanear. Leitor cansa em parágrafos densos; SEO também premia conteúdo escaneável.

### 18. Negrito esparso (frases conceituais sem destaque)
Inverso da armadilha 17. Modelo tende a negritar SÓ specs numéricos (R$ 450, 12W, 4.500 páginas) e deixar frases-chave conceituais em texto normal. Resultado: guide com 2 strongs/1k chars (visualmente fraco) em vez do alvo 4-5/1k dos canônicos.

Antes de salvar, escaneie cada parágrafo procurando **frases-chave conceituais sem negrito**: o critério que decide a compra, a limitação real, o perfil de uso, o valor de referência ("8 GB é o suficiente para a maioria"). Negrite o **termo**, não a frase inteira. ⚠ Isso não é licença para escrever em molde ("o ponto que define X é Y", "o que importa de verdade é A", "o porém real:") — esses clefts eram sugeridos aqui até 2026-08-15 e viraram assinatura; a frase é literal, o negrito é o que a torna escaneável.

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
Régua dura: links Amazon SÓ em "Qual a melhor marca" + FAQ + Conclusão. Modelo violou várias vezes na prática (2026-05) colocando links de "Modelo Y" como âncora em Vale a pena P2 quando a régua é texto SIMPLES sem link. Fix: em Vale a pena, citar modelos como referência de preço *"Os preços vão de R$ X (Modelo Y) a R$ Z (Modelo W)"* mas com **Modelo Y / Modelo W em texto puro, sem `<a>`**. Em Como escolher, mesmo critério: produto se for citado vira texto simples.

Verificação antes de salvar: `grep -c 'amazon\.com\.br' nas seções 1-2 do guide` deve retornar **0**.

### 20. Links peer/home concentrados na Conclusão (v1.24.0)
Tentação: jogar todos os links de navegação inter-artigo ("veja também o guia de X") na Conclusão, como um rodapé de "leia mais". É **decorativo, não contextual** — o leitor no fecho já decidiu, e link de navegação genérico ali não ajuda. Régua (Marcelo, 2026-06-05): "o ideal é evitar colocar na conclusão (ou não colocar mesmo). tem que ser contextual." Fix: cada link peer/home vai no spot onde o tema do irmão aparece naturalmente — FAQ que toca no assunto, H3 de "Como escolher", H3 de marca, ou "Vale a pena" pra apontar a categoria-mãe/home. Se não há encaixe natural fora da Conclusão, **não force** o link.

Distinção: links de **PRODUTO** (hub-and-spoke `/{slug-produto}/` ou Amazon `/dp/`) continuam OK na Conclusão (recomendação de compra é a função do fecho). Só a **navegação peer/home** sai.

Verificação antes de salvar: na seção Conclusão, nenhum `<a href="/{slug}/">` aponta pra peer ARTICLE (`reviews/`) nem `<a href="/">` pra home. Links de produto (`products/`) e Amazon ali são OK.

## Sincronização painel ↔ skill ↔ prompt canônico

**Fonte da verdade é ESTA `SKILL.md`** (canon 2026-08-15, ver "Régua comum das auditoras" em `docs/PADROES.md`). O `docs/painel/_data/agent-prompts.json` → `ops.generate_guide` é **espelho** usado pelos botões do painel (pode defasar; ao mudar régua aqui, refletir lá no mesmo commit quando a mudança afeta o output). Os endpoints legados `generate-*/rewrite-*/create` do painel foram removidos em 2026-05-27; `agent-config.html` virou `editorial.html`. Listas, regex e tetos vivem em `chavoes-por-nicho.json` — cite a chave, não copie a tabela.


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

Substituições mecânicas causam (caso real melhorpretreino `a72e7d9`): **14a** duplicação contígua (`sem empilhar suplementos sem empilhar suplementos`; regex `([a-zA-ZÀ-ÿ\s]{8,40})\1`) · **14b** bullet começando com minúscula dentro de `<strong>` (`<strong>aminoácidos…`) · **14c** minúscula após ponto em texto editorial (`(maior dose). pra emagrecer`; ignorar URLs e listas numeradas). Rodar no guideContent inteiro antes de gravar; achou → corrija.


## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), validação fica editorial — eu (modelo) sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial (link interno inventado, char count em 15100, tag fora da allowlist). Mitigação principal: hard-validation manual de links internos contra peer list antes de aplicar; se falhar, regenero o trecho.

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
