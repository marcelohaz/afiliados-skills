---
name: artigo-auditar
description: Audita artigo inteiro read-only. Combina 22 categorias editoriais (claim-vs-bible, tag-affiliate-contextual, travessao, superlativo, atribuicao-comprador, tone-clone, spec-ausente, dado-inconsistente, decisao-editorial, voz-citacao-ficha-tecnica, html-invalido, voz-comprador-implicita, termos-tecnico-industriais, intro-qualidade, title-qualidade, meta-description-qualidade, list-heading-qualidade, guide-estrutura, guide-tamanho, guide-html-allowlist, guide-links-hub-and-spoke, tamanho-escannavel-produto) com 4 checks estruturais (hasIntro, hasGuide, productCount≥3, hasMetaDescription) e calcula readyToLock pra sinalizar se está pronto pra contentLocked:true. Tag-affiliate é severity contextual: error crítico se site live=true, warn se em construção. Fase 2 (2026-05-27): qualidade editorial de intro/title/meta/listHeading. Fase 3 (2026-05-27): audit do guideContent. Fase 4 (2026-05-28 v1.16.0): tamanho-escannavel-produto (hard caps shortDescription ≤250, pros/cons ≤180 texto puro + ban "lineup"). Fase 5 (2026-05-28 v1.17.0): sub-check shortDescription-tecnico-first (detecta abertura "[Tipo] brasileiro/a da [marca]..." que viola padrão benefício-first). Output: relatório completo inline no chat + salva em docs/biblias-v2/.audits/articles/{site}-{slug}-audit-last.md (painel lê). NÃO modifica o .mdx. Aceita URL do painel OU args canônicos site/slug.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida):
- `https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio`
- Extrai `site` e `slug` do query string

**B) Args canônicos**:
- `melhorimpressora/melhor-impressora-custo-beneficio`

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B (split por `/`).

# Auditar artigo (skill única, read-only)

> Versão executável local do prompt canônico em `docs/painel/_data/agent-prompts.json:audit_article` enriquecido com structural checks + readyToLock (antes esses 2 elementos viviam em `final_review`, hoje consolidados aqui).

Você é o auditor read-only do artigo. O usuário passa `{site}/{slug}` e quer um diagnóstico completo: claims cruzados com bíblia, tag de afiliado correta, travessão, voz analítica, **mais checks estruturais** (intro/guide/produtos/meta) **mais veredito readyToLock**.

A skill é **read-only**: não toca no `.mdx`, não commita o `.mdx`. Só gera relatório + commita o `.md` da auditoria.

**Histórico**: até 2026-05-24 existiam 2 skills separadas (`artigo-auditar` puro + `artigo-analise-final` com structural+lock). Foram consolidadas — separação era artificial (custo extra de $0.02, mesmas 9 categorias). Quem quiser audit "leve" no meio do dev pode simplesmente ignorar o campo `readyToLock` no output.

## Pré-requisitos

- O `.mdx` do artigo já existe em `sites/{site}/src/content/reviews/{slug}.mdx`.
- O artigo tem **pelo menos 1 produto** no lineup (`products: []` vazio = abortar — nada pra auditar).
- Bíblias dos produtos do artigo estão em `docs/biblias-v2/{ASIN}.json`. Se alguma faltar, rodar `bun scripts/sync-biblias-r2.ts --apply` antes (skill avisa e aborta se faltar).
- `affiliateTag` em `sites/{site}/src/config.ts` é conhecida (pode ser vazia em sites em construção — a regra de auditoria muda: tag vazia → links Amazon devem ser CRUS sem `?tag=`).

## Invariantes

- **NÃO MODIFICA O `.mdx`.** Skill é read-only no conteúdo editorial. Só escreve o relatório de audit + commita ele.
- **NÃO inventa findings.** Se não encontrou problema numa categoria, não fabrica. Audit vazio em categoria = legítimo.
- **Toda issue precisa de evidência.** Cite trecho literal do `.mdx` (`evidence` ≤ 160 chars, idealmente < 15 palavras) OU da bíblia.
- **Código manda no readyToLock.** Override determinístico: IA pode dizer `true`, mas se estruturalmente falta peça obrigatória OU tem issue level=error, readyToLock final é `false`. IA só pode AFROUXAR, nunca APERTAR.
- **Português brasileiro editorial.** Tom analítico, factual.

## Fluxo

1. **Parse args**: detecta URL vs canônico, extrai `site` e `slug`. Valida `[a-z0-9-]+`.

1.5. **Git pull antes de ler o `.mdx`** (CRÍTICO — evita falso-negativo "produto stale"):
   ```bash
   git stash push -m "skill-artigo-auditar-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Se pull falhar (offline/conflito), seguir mesmo assim — documentar no relatório se for o caso.

2. **Read `.mdx`**: `Read sites/{site}/src/content/reviews/{slug}.mdx`. Se 404, abortar.

3. **Parse frontmatter** mentalmente:
   - `title` (H1)
   - `description` (meta description — checa placeholder)
   - `keyword` / `keywordPlural`
   - `products: []` — extrair ASINs + count
   - `contentLocked` — se `true`, avisa mas não bloqueia (útil pra reauditar pós-trava)
   - `guideContent` (block scalar) — extrai pra check estrutural + audit

4. **Read bíblias** dos produtos. Se alguma faltar, abortar com instrução pra rodar sync R2.

5. **Read `affiliateTag` + `live` status** (canon 2026-05-26):
   - `affiliateTag` de `sites/{site}/src/config.ts` via regex (pode ser `''`).
   - `live` de `docs/painel/sites-meta.json[{site}].live` (boolean).
   - Regra de validação dos links Amazon:
     - Tag preenchida → links DEVEM ter `?tag={tag}&linkCode=ogi&th=1&psc=1`
     - Tag vazia → links DEVEM ser crus (sem `?tag=...`)
   - Severity contextual da `tag-affiliate`:
     - `live: true` → divergência é 🔴 error crítico (bloqueia readyToLock)
     - `live: false` → divergência é 🟡 warn (site em construção, tag preenche pré-deploy)
     - `live: true` + tag vazia → SEMPRE 🔴 error crítico (sem afiliação no ar = perda direta)
     - **Fallback se `live` não definido em sites-meta**: tratar como `false` (default leniente — site recém-criado pode não ter o campo populado ainda).

6. **Rodar 4 checks estruturais determinísticos** (não-IA, código mental):

   ### a) `hasIntro`
   Body markdown do `.mdx` (tudo após o segundo `---` do frontmatter).
   - Calcular `totalBodyChars` (count de chars do body, ignorando frontmatter)
   - Quebrar body em "segmentos" (linhas separadas por blank lines)
   - Detectar placeholder: algum segmento inclui `[a escrever` OU `— agente IA preenche`
   - `hasIntro = totalBodyChars > 200 && !isPlaceholder`

   ### b) `hasGuide`
   - Extrair `guideContent` do frontmatter (block scalar `|` ou inline vazio)
   - `hasGuide = guideContent.exists && guideContent.trim().length > 100`

   ### c) `productCount >= 3`
   - `parsed.products.length` (quantos itens no array `products[]`)

   ### d) `hasMetaDescription`
   - `description` é placeholder se inclui `[descrição a definir`
   - `hasMetaDescription = description.length >= 50 && !isPlaceholder`

7. **Rodar auditoria IA** nas 22 categorias (10 do `regras_auditoria_artigo` + 3 adicionadas 2026-05-26: html-invalido, voz-comprador-implicita, termos-tecnico-industriais + 4 adicionadas 2026-05-27 Fase 2: intro-qualidade, title-qualidade, meta-description-qualidade, list-heading-qualidade + 4 adicionadas 2026-05-27 Fase 3: guide-estrutura, guide-tamanho, guide-html-allowlist, guide-links-hub-and-spoke + 1 adicionada 2026-05-28 Fase 4: tamanho-escannavel-produto — ver "Critérios de auditoria" abaixo). Gerar:
   - `issues`: array de `{level, rule, message, product?, fix?, evidence?}`
   - `summary`: 1-3 frases sobre estado geral
   - `passed`: bullets MUITO curtos (10-30 palavras) do que passou bem

8. **Detectar meta description placeholder específico** (paridade com `detectMetaDescPlaceholder` do painel — agent-edit.ts:1221-1235):
   ```js
   if (description.includes('[descrição a definir')) {
     issues.unshift({
       level: 'error',
       rule: 'meta-description-placeholder',
       message: 'Meta description ainda é placeholder. Não pode ser publicado assim — Google indexaria o snippet placeholder.',
       fix: 'Execute /artigo-meta-escrever pra gerar uma meta description real antes de publicar.'
     });
   }
   ```

9. **Calcular `readyToLock`** com override determinístico:
   ```
   structuralOk = hasIntro && hasGuide && productCount >= 3 && hasMetaDescription
   errorIssueCount = issues.filter(i => i.level === 'error').length
   errorsOk = errorIssueCount === 0
   readyToLock = structuralOk && errorsOk
   ```

   `lockReasoning` (1-2 frases) listando blockers se readyToLock=false:
   - "introdução vazia ou placeholder (execute /artigo-intro-escrever)"
   - "guide ausente — campo guideContent vazio no frontmatter (execute /artigo-guia-escrever)"
   - "apenas N produto(s) (mínimo 3) — adicione mais produtos via painel + execute /artigo-review-criar"
   - "meta description ainda é placeholder (execute /artigo-meta-escrever)"
   - "N issue(s) crítico(s) — veja seção 🔴 do relatório"

   Se readyToLock=true: `lockReasoning = "Tudo OK — pronto pra travar com contentLocked: true."`

10. **Montar markdown do relatório** (formato em "Formato do relatório" abaixo).

11. **Escrever relatório** em 2 locais:
    ```
    docs/biblias-v2/.audits/articles/{site}-{slug}-audit-{YYYY-MM-DD-HHMM}.md  ← snapshot timestamped
    docs/biblias-v2/.audits/articles/{site}-{slug}-audit-last.md               ← caminho fixo, painel lê esse
    ```
    Criar `docs/biblias-v2/.audits/articles/` se não existir.

12. **Commit + push + dispatch VPS pull** (auditorias `-last.md` são tracked no git; timestampadas são gitignored):
    ```bash
    git add docs/biblias-v2/.audits/articles/{site}-{slug}-audit-last.md
    git commit -m "audit({site}): artigo {slug} (readyToLock={true|false})"
    git push origin main
    bash scripts/painel-vps-pull.sh
    ```

13. **Imprimir relatório COMPLETO inline no chat** (não só summary). Mesmo conteúdo que vai pro `.md`. User vê tudo sem precisar abrir arquivo. Path do `.md` é mencionado no final pra quem quiser linkar.

## Critérios de auditoria (13 categorias — 10 do `regras_auditoria_artigo` + 3 adicionadas 2026-05-26)

Use exatamente esses valores em `rule`:

### `claim-vs-bible` (level=`error`)
Afirmação no review (subtitle, shortDescription, fullReview, pros, cons, specs) que NÃO tem origem rastreável na bíblia. Spec inventada, número errado, feature não confirmada. Inclui `evidence` com citação literal.

**Exemplo**: review diz "5.000 páginas por kit" mas bíblia diz "4.500 páginas".

### `tag-affiliate` (level=`error` se site live, `warn` se em construção)
Link Amazon com tag diferente da esperada.
- Tag preenchida no config: links DEVEM ter `?tag={tag}&linkCode=ogi&th=1&psc=1`
- Tag vazia: links DEVEM ser crus (sem `?tag=...`)

**Severity contextual** (canon 2026-05-26): a skill lê `sites-meta.json[site].live`.
- `live: true` (site no ar): divergência de tag é **🔴 error** crítico — bloqueia readyToLock (não pode publicar sem afiliação correta).
- `live: false` (em construção): divergência vira **🟡 warn** — site ainda não foi pro ar, tag pode ser preenchida pré-deploy. Não bloqueia readyToLock.
- `live: true` + tag vazia: 🔴 error crítico **sempre** — site no ar sem afiliação é grave (perda direta de comissão).

### `travessao` (level=`warn`)
Travessão (`—` ou `–`) detectado em qualquer campo editorial: title, description, subtitle, shortDescription, fullReview, pros, cons, intro (body markdown), guideContent.

### `superlativo-sem-evidencia` (level=`warn`)
Absolutos sem evidência: "o melhor disponível", "o mais X", "incomparável", "único", "imbatível".

**Não flag**: qualificadores positivos simples ("excelente", "ótimo", "muito bom") — review afiliado é levemente inclinado ao positivo por design.

### `atribuicao-comprador` (level=`warn`)
Usa "compradores" (plural) sem ter múltiplas opiniões na bíblia; OU cita "1 comprador" como se fosse consenso. Voz analítica é o padrão — citações explícitas de comprador/Amazon/reviews devem ser reescritas.

### `tone-clone` (level=`info`)
Produtos com voz/estrutura idêntica. Aberturas todas começando igual ("A {X} é para quem..."), mesma fórmula, mesmo número de frases por bloco.

**Não flag** se o pattern é o template editorial canônico (`Para quem é:` / `Por que gostamos:` / `Pontos de atenção:` / `Resumo:`) — isso é INTENCIONAL.

Só flag tone-clone se houver:
- Frase concreta repetida em 2+ reviews (claim copiado)
- Parágrafo quase idêntico com nome trocado
- Explicação de conceito repetida (ex: o que é "EcoTank" explicado em todos os reviews em vez de uma vez)

### `spec-ausente` (level=`info`)
Produto sem campo de spec que outros do artigo têm (incompletude). Ex: 3 produtos com "Conectividade: Wi-Fi" no specs e 1 sem.

### `dado-inconsistente-ignorado` (level=`warn`)
Bíblia tem `dadosInconsistentes` com `decisaoEditorial`; review não respeita a decisão.

**Exemplo**: bíblia tem flag "ppm-divergente" com decisão "usar 10ppm da ficha técnica, ignorar bullet de 12ppm" — mas review diz "12 ppm".

### `decisao-editorial-violada` (level=`warn`)
Review contradiz `decisaoEditorial` registrada na bíblia (caso geral).

### `voz-citacao-ficha-tecnica` (level=`warn`)
Marcadores de procedência **burocráticos** no .mdx — quando o modelo copiou da bíblia sem destilar. Diferente de `atribuicao-comprador` (cita comprador) — esta cobre **cita fonte burocrática** ("alérgenos confirmam", "atributos declaram", "conforme tipo de dieta").

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

**Régua editorial — voz-citação OK SÓ quando atende AS DUAS condições:**
1. **(a)** qualifica claim que SÓ o fabricante pode fazer (rendimento, garantia interna, certificação proprietária)
2. **(b)** adiciona valor editorial ao leitor (calibra expectativa, sinaliza honestidade, faz crítica útil)

**✓ Editorial OK** (não flag): "rende até 4.500 páginas em preto, segundo a Epson" — claim só-fabricante + qualifica rendimento.

**❌ Burocrática** (flag warn): "alérgenos da Amazon confirmam ausência de glúten" → sugerir "sem glúten".

### `html-invalido` (level=`error`)

Tags HTML em campos do `.mdx` que **violam allowlist do campo** ou **viram texto literal** ao renderizar. Astro escapa `{var}` com proteção XSS — qualquer HTML literal em campo texto-puro aparece como TEXTO ao usuário (não-renderizado).

Sub-checks:

**a. Tags fora da allowlist em `fullReview` (produto-no-artigo) ou `guideContent`**:
- `fullReview` (campo dentro de `products[N]` no `.mdx` do artigo): allowlist `<p>`, `<strong>`, `<em>`, `<a>`. Tags proibidas: `<h2>`, `<h3>`, `<ul>`, `<ol>`, `<li>`, `<table>`, `<img>`, `<script>`, `<iframe>`, `<style>`.
- `guideContent` (frontmatter): allowlist mais permissiva — `<h2>`, `<h3>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<a>`. Mesmas proibições no resto.

**b. HTML em campos TEXTO-PURO do produto-no-artigo** — `subtitle`, `shortDescription`, `specs[].value`. Esses campos são renderizados por Astro com `{var}` (escape XSS automático). Qualquer tag HTML literal (`<strong>`, `<em>`, `<a>`, `<p>`) aparece como TEXTO LITERAL pro usuário (não-renderizada). Verificar via regex `<\w+[^>]*>` em cada um.

**c. HTML no meio do texto de `pros[N]` ou `cons[N]` do produto-no-artigo** (após o `:` que separa título de explicação). O `<strong>Título</strong>` no início está PERMITIDO (template usa `set:html` ali); mas `<strong>` aninhado no texto da explicação **vira texto literal**. Regex de detecção: depois do primeiro `</strong>:`, qualquer `<\w+` é violação.

**d. HTML no body markdown da intro** (tudo após o segundo `---` do frontmatter, até o primeiro `## ` ou fim). Régua da `artigo-intro-escrever`: "body é puro markdown, sem HTML inline. Bold só em `**markdown**`, nunca `<b>` ou `<strong>`." Verificar via regex `<\w+[^>]*>` no body da intro — qualquer tag HTML é violação.

**Caso real 2026-05-26**: `Integralmédica Huger` (página individual) vazou `<strong>energia com foco preservado</strong>` na shortDescription, apareceu literal no card. **Mesmo bug-class é vulnerável em campos de artigo** — qualquer `products[N].shortDescription`, `products[N].subtitle`, `products[N].specs.value` ou body markdown da intro pode ter o mesmo problema. Audit precisa pegar em todos esses lugares.

### `voz-comprador-implicita` (level=`error`)

Diferente de `atribuicao-comprador` que pega menções explícitas ("compradores", "Amazon", "reviews"), esta categoria pega **voz-comprador SUTIL** que sub-agent não destilou da bíblia. Régua "destilação categoria D" canonizada 2026-05-26 (v1.11.4).

**Padrões a flagar (regex em qualquer campo: subtitle, shortDescription, fullReview, pros, cons, intro, guideContent)**:
- "opiniões" (no sentido de opiniões de compradores)
- "comentários" (no sentido de comentários de quem comprou)
- "um comprador relata"
- "divide opiniões" / "opiniões divididas" / "opiniões mistas"
- "elogios recorrentes" / "elogiado nas opiniões"
- "recepção [mista/dividida/positiva]"
- "avaliações" (no sentido de avaliações Amazon, não avaliação técnica)
- "bem recebido [pelos/nos]"
- "ponto positivo recorrente nas opiniões"
- "queixa recorrente"

**Caso real 2026-05-26** (batch melhorpretreino): 5 ocorrências em 3 produtos. Sub-agent Opus reconhecia voz-comprador EXPLÍCITA na bíblia ("elogiado de forma recorrente nas opiniões") e destilava. Mas CAÍA quando era SUTIL ("um comprador relata", "divide opiniões"). Régua "destilação categoria D" exige sub-agent REESCREVER como observação analítica antes de usar.

**Exemplo flag (errado vs certo)**:
- ❌ bíblia: "Sabor maçã verde divide opiniões nos reviews" → review: "Sabor divide opiniões"
- ✅ destilado: "Sabor maçã verde é frutado, pode não agradar quem prefere perfis mais neutros"

### `termos-tecnico-industriais` (level=`error`)

Termos técnico-industriais proibidos pela régua editorial (canonizada 2026-05-26 v1.11.4). Soam como rotulagem técnica/ANVISA — quebram a voz editorial.

**Padrões a flagar (regex em qualquer campo)**:
- "contaminação cruzada"
- "linha de produção compartilhada" (sem contexto editorial)
- "sujeito a contaminação"
- "risco de contaminação por proteínas"

**Caso real 2026-05-26** (batch melhorpretreino): `essential-nutrition-beta-action` cons[3] usou "considerar o risco de contaminação cruzada na linha de produção". Audit da página individual pegou. Pra produto-no-artigo, audit (esta) precisa pegar também.

**Fix sugerido pelo audit**: linguagem editorial pra alérgenos:
- ❌ "Risco de contaminação cruzada na linha de produção"
- ✅ "Pode conter traços de leite — alérgicos severos devem ler a rotulagem antes do uso"

### `intro-qualidade` (level=`warn`)

Audit da qualidade EDITORIAL do body markdown da intro (não só "tem chars > 200" do check estrutural). Régua canon v1.11.6 (canon 2026-05-26).

**Checklist obrigatório** — falhar QUALQUER um vira issue:
- **Chars 300-800** (alvo 500-700). >1500 chars = ensaio cansativo, <300 = vaga.
- **2-3 parágrafos** (separados por linha em branco). 4+ parágrafos quebra régua.
- **§1 inclui pergunta** (`?`) + `**{keyword}**` em bold markdown.
- **§final inclui** `**{keywordPlural}**` em bold E **termina com `. ✅`** (ponto + espaço + emoji, nada depois).
- **Exatamente 2 bolds totais** no body inteiro (keyword no §1, keywordPlural no §final). Nada mais em bold.
- **Sem travessão** (`—` ou `–`).
- **Sem heading** (`#`, `##`, `<h1>`, `<h2>`, `<h3>`).
- **Sem mencionar marcas/modelos/ASINs específicos** (linguagem geral).
- **Sem instituições científicas** (OMS, FAO, ANVISA, FDA, IFOS).
- **Sem registro acadêmico/médico** (tom conversacional especialista→amigo).

**Exemplo flag**:
- ❌ "A OMS recomenda 250mg de EPA+DHA diários" → cita instituição
- ❌ "**Excelente** ômega 3 com **dose alta**" → bolds extras
- ✅ "Procurando a **melhor impressora**? A decisão começa por..."

Fix sugerido: rodar skill `artigo-intro-escrever` (passa por régua canon completa).

### `title-qualidade` (level=`warn`)

Audit do campo `title` do frontmatter.

**Checklist**:
- **30-100 chars** (alvo 40-70). <30 = SEO fraco, >100 = truncado no Google.
- **Inclui `{keyword}` (case-insensitive)** — keyword principal do artigo precisa estar no title.
- **Não tem placeholder** (`[TITLE TODO`, `Title aqui`, etc).
- **Não termina com travessão**.

Fix sugerido: editar via painel (editor-artigo.html → campo Título).

### `meta-description-qualidade` (level=`warn`)

Audit do campo `description` do frontmatter (meta description SEO).

**Checklist**:
- **50-160 chars** (alvo 120-155). <50 = pobre, >160 = truncado no Google.
- **Single-line** (sem quebras de linha).
- **Sem aspas duplas internas** (quebra o YAML do frontmatter).
- **Sem travessão** (`—` ou `–`).
- **Inclui `{keyword}` ou variante próxima** (case-insensitive).
- **Não tem placeholder** (`[descrição a definir`, `Meta description aqui`).

Fix sugerido: rodar skill `artigo-meta-escrever`.

### `list-heading-qualidade` (level=`warn`)

Audit do campo `listHeading` do frontmatter (H2 que abre a TabelaTop dos produtos).

**Checklist**:
- **Existe e não-vazio** (campo obrigatório no schema do .mdx).
- **10-200 chars** (alvo 30-80).
- **Não tem placeholder** (`[listHeading TODO`, `Heading aqui`).
- **Idealmente inclui `{keyword}` ou pergunta**: "Qual a **melhor impressora** em 2026?", "Quais são as **melhores creatinas**?"
- **Sem travessão**.

Fix sugerido: editar via painel (editor-artigo.html → campo "Heading da tabela").

### `guide-estrutura` (level=`warn`)

Audit da estrutura do `guideContent` HTML (Fase 3, canon 2026-05-27). Régua canon da skill `artigo-guia-escrever`.

**Checklist**:
- **5 H2 obrigatórios na ordem**:
  1. "Vale a pena" (ou variante: "Vale a pena comprar")
  2. "Como escolher"
  3. "Melhor marca" (ou variante: "Qual a melhor marca")
  4. "FAQ" (ou variante: "Perguntas frequentes")
  5. "Conclusão"
- **1 H2 opcional permitido**: "Por que confiar" (geralmente no início, antes de "Vale a pena")
- **Ordem importa**: H2s fora de ordem viram issue (ex: "Conclusão" antes de "FAQ").
- **Sem H1 no guide** — H1 já é o `title` do artigo, duplicar quebra hierarquia SEO.
- **Sem placeholder** (`[GUIDE TODO`, `Conteúdo do guia aqui`).

**Exemplo flag**:
- ❌ Guide só tem 3 H2 (faltando "Melhor marca" e "FAQ") → warn "guide-estrutura: faltam 2 H2 obrigatórios"
- ❌ H2s na ordem "Vale a pena / FAQ / Como escolher" → warn "ordem invertida"

Fix sugerido: rodar skill `artigo-guia-escrever` (gera os 5 H2 na ordem canônica).

### `guide-tamanho` (level=`info`)

Audit do tamanho do `guideContent` (chars). Régua canon: 6000-25000 chars, alvo 12000-18000.

**Checklist**:
- **<6000 chars**: info "guide-tamanho: muito curto ({N} chars), abaixo do mínimo 6000. Aprofundar análise."
- **>25000 chars**: info "guide-tamanho: muito longo ({N} chars), acima do máximo 25000. Considerar dividir ou condensar."
- **6000-25000**: passa silenciosamente (não flag).

Fix sugerido: ajustar via skill `artigo-guia-escrever` ou editar via painel.

### `guide-html-allowlist` (level=`error`)

Audit do HTML do `guideContent`. Régua canon: allowlist estrita.

**Tags PERMITIDAS**:
- `<h2>`, `<h3>` (h3 pode aninhar dentro de h2)
- `<p>`, `<ul>`, `<ol>`, `<li>`
- `<strong>`, `<em>`
- `<a href="..." rel="nofollow" target="_blank">` (Amazon ou interno)
- `<br>` (linha em branco — uso pontual)

**Tags PROIBIDAS** (flag como error):
- `<h1>` (duplica o title do artigo)
- `<h4>`, `<h5>`, `<h6>` (hierarquia além de h3 não-canônica)
- `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>` (não usar tabela no guide — usar listas)
- `<img>`, `<picture>`, `<video>`, `<iframe>` (sem mídia inline no guide)
- `<script>`, `<style>` (segurança)
- `<div>`, `<span>` (HTML estrutural — não-canônico)

**Sub-check obrigatório**:
- **Sem travessão** (`—` ou `–`) — proibido em todo o guide.

Fix sugerido: rodar skill `artigo-guia-escrever` (allowlist enforced no output).

### `guide-links-hub-and-spoke` (level=`info`)

Audit dos links no `guideContent`. Régua hub-and-spoke (canon v1.10.0 da skill `artigo-guia-escrever`, 2026-05-25).

**Checklist**:
- **Links Amazon (`amazon.com.br/dp/`) em FAQ/Marca/Conclusão**: tag-aware (com `?tag={tag}&linkCode=ogi&th=1&psc=1` se site live). Sem tag = warn.
- **Preferir link interno sobre Amazon em FAQ/Conclusão** (info): se há peer-article no site (em `content/reviews/`) que cobre o tópico, link interno (`/{slug}/`) é preferido. Ex: FAQ sobre "creatina monohidratada" — link pra `/melhor-creatina-monohidratada/` (peer article do site) em vez de produto Amazon.
- **Vale a pena / Como escolher**: 0 links (essas 2 seções são EDUCATIVAS, sem links pra não distrair).
- **Marca**: links Amazon de busca por marca permitidos (`amazon.com.br/s?k=marca-X`).
- **Sem travessão** (também coberto em guide-html-allowlist, mas reforço aqui).

**Exemplo flag**:
- ❌ Link `<a href="https://amazon.com.br/dp/X">` SEM tag em site live → warn
- ℹ️ Conclusão linka `/dp/B123` mas há peer article `/melhor-creatina-monohidratada/` no site → info "considere link interno hub-and-spoke"

Fix sugerido: rodar skill `artigo-guia-escrever` (aplica hub-and-spoke automaticamente).

### `tamanho-escannavel-produto` (level=`error`, régua v1.16.0)

Audit dos limites editoriais de tamanho nos campos do produto-no-artigo. Bullets/cards inchados quebram a escanabilidade visual (cards viram parágrafos, parágrafos viram wall-of-text → usuário pula a decisão).

**Hard caps** (canon `melhoraspirador` validado live):

| Campo | Limite | Alvo |
|---|---|---|
| `products[N].shortDescription` | 250 chars | 150-220 |
| `products[N].pros[i]` item | 180 chars texto puro | 80-130 |
| `products[N].cons[i]` item | 180 chars texto puro | 80-130 |

**Como contar pros/cons**: descontar markup `<strong>`/`<a>`/`<em>` — conta só o texto visível ao leitor.

**Sub-checks (sub-tipos do mesmo critério, todos level=`error`)**:
- `shortDescription-longa`: campo > 250 chars
- `shortDescription-tecnico-first` (régua v1.17.0): 1ª frase abre com técnico em vez de benefício/posicionamento. Antipadrões detectáveis na abertura: "[Tipo] brasileiro/a da [marca]..." (ex: "Pré-treino brasileiro da X..."), "[Tipo] com X mg de Y...", "[Tipo] multifuncional/premium da [marca]...". Padrões OK: adjetivo posicional ("Custo-benefício forte", "Vegano"), "Ideal pra quem...", "Você ganha...". Fix: inverter ordem — posicionamento na 1ª frase, técnico justifica depois. Ver moldes A/B/C em `artigo-review-criar` v1.17.0.
- `bullet-longo`: pros[i] ou cons[i] texto puro > 180 chars
- `listagem-peers-exaustiva`: bullet/parágrafo cita 4+ peers (lista virou tabela em texto)
- `palavra-chavao-banida`: ocorrência de "lineup", "do lineup", "do nosso lineup", "desta seleção", "do nosso comparativo" em qualquer campo do produto
- `palavra-chavao-alta-freq` (level=`warn`): "fórmula" > 60, "ativo"/"ativos" > 50, "preço médio" > 15, "parestesia"+"formigamento" > 20 combinados — chavões que precisam variação léxica

**Caso real `melhorpretreino`** (regressão pré-v1.16.0): shortDescription média 329-414 chars (canon vivo: 225); bullets média 175-182 chars (canon: 65); 50 ocorrências de "lineup" + 114 de "seleção" num único artigo.

**Bloqueia readyToLock?** Sim — categoria `error`, conta como blocker.

Fix sugerido: rodar skill `artigo-review-criar` (v1.16.0+) com hard caps embutidos, ou destilar manualmente.

## Critérios estruturais (4 checks determinísticos)

| Check | Critério | Bloqueia readyToLock? |
|---|---|---|
| `hasIntro` | body chars > 200 + sem placeholder `[a escrever:` ou `— agente IA preenche` | Sim |
| `hasGuide` | `guideContent` no frontmatter, trim > 100 chars | Sim |
| `productCount >= 3` | array `products[]` tem ≥3 items | Sim |
| `hasMetaDescription` | `description` >= 50 chars + sem placeholder `[descrição a definir` | Sim |

## Formato do relatório

Template do markdown (gravado em arquivo E impresso inline no chat):

```markdown
# Auditoria: {site}/{slug}

- **Data:** {YYYY-MM-DD HH:MM}
- **affiliateTag:** {tag ou "(vazia — site em construção)"}
- **Produtos auditados:** {count} ({asins list})
- **readyToLock:** {true|false}
- **lockReasoning:** {1-2 frases}

## Structural checks

| Check | Status | Valor |
|---|---|---|
| Introdução escrita | {✓|✗} | {chars do body} chars |
| Guide presente | {✓|✗} | {chars do guideContent} chars |
| ≥3 produtos | {✓|✗} | {productCount} produtos |
| Meta description | {✓|✗} | {chars da description} chars |

## Summary

{1-3 frases sobre o estado geral, do campo summary da IA}

## 🔴 Errors ({N})

{lista com format abaixo, ou "Nenhum" se vazio}

### {rule}: {message curta}
- **Produto:** {ASIN ou nome — opcional, só se aplicável}
- **Evidência:** "{citação literal < 15 palavras}"
- **Fix sugerido:** {1 frase}

## 🟡 Warnings ({M})

{mesma estrutura}

## 🔵 Info ({K})

{mesma estrutura}

## ✅ Passed ({P})

- {bullet curto, 10-30 palavras}
- {bullet curto, 10-30 palavras}
```

## Voz analítica (CRÍTICO)

- **Tom analítico.** "O review do produto 2 cita 5.000 páginas; bíblia confirma 4.500."
- **NÃO comente preferências.** "Acho que ficaria melhor com Y" → "Y pode ser uma alternativa que cita {dado da bíblia}".
- **Cite evidência.** Cada issue com `evidence` (do `.mdx`) ou referência a campo da bíblia. Sem evidência, descarta.

## Quando NÃO usar essa skill

- **Artigo sem produtos** (`products: []` vazio): nada pra auditar. Aborta orientando completar lineup primeiro.
- **Falta de bíblia** de produtos: rodar `bun scripts/sync-biblias-r2.ts --apply` primeiro.
- **Quer REESCREVER reviews** (write op): use `artigo-reviews-auditar` em vez disso — ela propõe diffs cross-produto pra você aprovar.

## Output no chat

Diferente de outras skills que só reportam "audit OK, ver path/X.md", essa skill **imprime o relatório markdown completo inline no chat**. Usuário não precisa abrir o `.md` pra ver o resultado — ele aparece direto na resposta da skill.

Path do `.md` salvo é mencionado no rodapé do output pra referência (painel lê esse arquivo pra mostrar UI).

## Sincronização painel ↔ skill ↔ prompt canônico

```
docs/painel/_data/agent-prompts.json:audit_article  (SOURCE OF TRUTH editorial)
    └── esta SKILL.md (versão local executável, enriquecida com structural+readyToLock)
```

Pré-consolidação (até 2026-05-24), existiam 2 prompts canônicos: `audit_article` (puro) e `final_review` (com structural+readyToLock). Hoje a skill local consome só `audit_article` e implementa structural+readyToLock como código em volta. Compartilha o `regras_auditoria_artigo` shared.

## Armadilhas recorrentes

### 1. Tentar editar o `.mdx`
Skill é read-only no conteúdo editorial. Mesmo que veja problema fácil de consertar, NÃO edita o `.mdx`. O user roda skills específicas (`artigo-intro-escrever`, `artigo-review-criar`, etc.) pra corrigir.

### 2. Confundir com `artigo-reviews-auditar`
Aquela é WRITE op cross-produto (sugere mudanças, user aprova granular). Esta é READ-only de TODO o artigo + structural + readyToLock.

### 3. IA forçar readyToLock=true sem checks estruturais
Override determinístico (passo 9) cobre isso. Se IA disse `true` mas falta intro/guide/produtos/meta, reescrevo o `lockReasoning` listando blockers e força `readyToLock = false`.

### 4. Citar comprador no audit
"Compradores reclamam de X" → quebra a voz analítica. Sempre reescreva: "Bíblia registra trade-off X (campo Y)".

### 5. Não criar diretório `.audits/articles/`
Primeiro run do skill no projeto, o diretório não existe. Sempre fazer `mkdir -p docs/biblias-v2/.audits/articles/` antes de escrever.

### 6. Achar tone-clone onde é template intencional
A estrutura dos 4 parágrafos com prefixos exatos (`Para quem é:` / `Por que gostamos:` / `Pontos de atenção:` / `Resumo:`) é o template canônico — **não é tone-clone**.

### 7. Tag vazia esperando link com tag
Site em construção tem `affiliateTag: ''`. Nesse caso, links Amazon devem ser CRUS (`https://amazon.com.br/dp/X`). Se a IA assume tag preenchida e flagga "tag-affiliate", está errado.

### 8. Não considerar `contentLocked` no input
Se artigo já é `contentLocked: true`, a skill ainda roda (útil pra reauditar pós-trava), mas o relatório deve mencionar no header. UI do painel oferece "Destravar" se houver issue crítica achada.

### 9. Inventar issues pra ter "achados"
Audit vazio é válido. Se artigo está bom, `issues: []` + `passed: [...]` + `readyToLock: true` é o output correto. Prefira 5 findings bem evidenciados a 20 vagos.

### 10. Esquecer de imprimir inline no chat
A diferença chave dessa skill é o output FULL inline (não apenas summary + path). Sempre imprimir o markdown completo do relatório como resposta no chat.

## Exemplo de invocação

Exemplos válidos do user:
- "audita o artigo melhor-impressora-custo-beneficio do melhorimpressora"
- "audita pra travar o melhor-impressora-custo-beneficio"
- "https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio" (com hint "audita")

Args canônico: `Skill(skill="artigo-auditar", args="melhorimpressora/melhor-impressora-custo-beneficio")`

## Limitação intrínseca conhecida

Sem schema Zod programático no output, validação fica editorial. ~5% de chance de algum issue ter `evidence` levemente fora do limite. Mitigação: conferir mentalmente antes de salvar o `.md`.
