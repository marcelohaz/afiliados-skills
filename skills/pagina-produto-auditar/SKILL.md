---
name: pagina-produto-auditar
description: Audita página individual de produto read-only, cruzando os 6 campos editoriais com a bíblia + diretrizes editoriais + tag de afiliado. 16 categorias de check (claim-vs-bible, tag-affiliate, tone-comprador, travessao, superlativo, html-invalido com 3 sub-checks, link-externo, tamanho-fora-de-faixa, redundancia-com-artigo, voz-citacao-ficha-tecnica, voz-comprador-implicita, termos-tecnico-industriais, chavoes-por-nicho, capitalizacao-duplicacao, concordancia-quebrada-pt-br, health-absolutes-ymyl). Régua v1.19.0 (ChatGPT-Bárbara 2026-05-28) — critérios novos: concordancia-quebrada-pt-br (composiçãos/combinaçãos/"a produto"/"a formigamento"/"no em 20XX"), health-absolutes-ymyl ("uso regular é seguro"/"alternativa segura"/"não causa dano" — Google YMYL). Régua v1.18.0 — critério 13 chavoes-por-nicho. v1.16.0 — tamanho-fora-de-faixa cobre curto E LONGO demais (shortDescription >250 chars, pros/cons >180 chars texto puro). Aceita URL do painel (editor-produto.html?site=X&slug=Y) OU args canônicos site/slug. Gera relatório em docs/biblias-v2/.audits/products/<site>-<slug>-last.md.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida):
- `https://painel.melhorserum.com.br/editor-produto.html?site=melhorimpressora&slug=hp-laser-107w`
- Extrai `site` e `slug` do query string

**B) Args canônicos**:
- `melhorimpressora/hp-laser-107w` (formato `site/slug`)

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B.

# Auditar página individual de produto

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:audit_product_page`.
> Conteúdo duplicado abaixo pra autocontenção; em caso de divergência, o prompt canônico ganha.

Você é o auditor da página individual de produto. O usuário passa `site/slug` (ou variantes). Sua função é **verificar** o conteúdo da página — não regerar, não reescrever, só encontrar e reportar problemas.

## Invariantes

- **Nunca edite o `.mdx`.** Seu output é um relatório em `.audits/products/`. O humano decide o que fazer.
- **Nunca invente findings.** Se não encontrou problema numa categoria, diga "nenhum". Audit vazio é melhor que audit inventado.
- **Toda afirmação precisa de evidência.** Cite trecho literal do `.mdx` (blockquote < 15 palavras) ou da bíblia.
- **Respeite as diretrizes** do site e da bíblia.

## Fluxo

1. **Parse args**: aceita `{site}/{slug}` canônico ou nomes humanos (mesmo padrão do `pagina-produto-criar`).

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   git stash push -m "skill-pagina-produto-auditar-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Painel VPS commita+pusha automaticamente quando user cria/edita conteúdo na UI; Mac local pode estar 5-30s atrás. Sem este pull, skill pode ler estado stale e abortar com falso "X não existe localmente". Se pull falhar (rede offline, conflito), seguir mesmo assim.

2. **Read .mdx**: `Read sites/{site}/src/content/products/{slug}.mdx`. Se 404, abortar com mensagem clara.

3. **Parsear frontmatter**: extrair os 6 campos editoriais (subtitle, shortDescription, pros, cons, specs, fullReview). Se algum vazio/ausente, registra como issue `tamanho-fora-de-faixa` (sub-tipo curto).

4. **Read bíblia**: `Read docs/biblias-v2/{asin}.json`. Sem bíblia, audit não tem como cruzar claims — abortar com mensagem.

5. **Read affiliateTag**: `Read sites/{site}/src/config.ts`. Determinar regra:
   - Tag preenchida: links Amazon devem ter `?tag={tag}&linkCode=ogi&th=1&psc=1`
   - Tag vazia: links Amazon devem ser **crus** sem `?tag=...`

6. **Read reviews que citam o ASIN** (anti-duplicate): `Grep` em `sites/{site}/src/content/reviews/*.mdx` por `asin:.*{asin}`. Se houver, leia o `fullReview` do produto-no-artigo pra comparar com o `fullReview` da página individual — flag se for muito parecido (parágrafo inteiro idêntico, frases-chave repetidas).

7. **Rodar as 12 categorias de checagem** (abaixo).

8. **Escrever relatório**:
   - `docs/biblias-v2/.audits/products/{site}-{slug}-{YYYY-MM-DD-HHMM}.md` (histórico)
   - `docs/biblias-v2/.audits/products/{site}-{slug}-last.md` (path fixo, painel pode ler)
   - Crie o diretório `docs/biblias-v2/.audits/products/` se não existir.

9. **Commit + push + dispatch VPS pull** (auditorias são tracked no git, igual `.audits/` de bíblia; só commitar o `-last.md` — o timestampado é gitignored):
   ```bash
   git add docs/biblias-v2/.audits/products/{site}-{slug}-last.md
   git commit -m "audit({site}): página individual {slug}"
   git push origin main
   bash scripts/painel-vps-pull.sh
   ```
   `painel-vps-pull.sh` propaga pro painel da VPS via Basic Auth (creds em `.env.painel-skills`).

10. **Reportar no chat**: 3-5 linhas com total de findings por severidade + path do relatório. Não cole o relatório inteiro no chat.

## As 12 categorias de check

### 1. `claim-vs-bible`
Afirmação em qualquer campo (subtitle, shortDescription, pros, cons, specs, fullReview) que não tem origem rastreável na bíblia (specs, números, certificações, marca).

Exemplo flag: `fullReview` diz "velocidade de 12 ppm" mas bíblia diz "10 ppm".

### 2. `tag-affiliate`
Links Amazon no `fullReview` que violam a regra do site:
- Config com tag → links devem ter `?tag={tag}&linkCode=ogi&th=1&psc=1`
- Config vazia → links devem ser **crus** sem `?tag=...`

### 3. `tone-comprador`
Texto cita 'compradores', 'reviews', 'avaliações', 'estrelas', 'usuários' (proibido — voz é analítica).

Procurar por: `comprador`, `compradores`, `usuário(s)`, `cliente(s)`, `avalia`, `review`, `estrela`, `nota`, `Amazon`.

### 4. `travessao`
Presença de `—` (U+2014) ou `–` (U+2013) em qualquer campo. Proibido por PADROES.

### 5. `superlativo-sem-evidencia`

**Proibido**: superlativos ABSOLUTOS sem dado verificável que justifique:
- ❌ "o melhor"
- ❌ "o mais X" (sem dado de comparação contra todo o lineup)
- ❌ "o único"
- ❌ "incomparável"
- ❌ "imbatível"

**Permitido** (qualificadores positivos simples — alinhado com diretriz editorial #2 da bíblia: "review honesto mas inclinado ao positivo pra aumentar conversão"):
- ✓ "excelente"
- ✓ "ótimo"
- ✓ "muito bom"
- ✓ "boa fidelidade"
- ✓ "destaque prático"

A diferença: adjetivo aprobativo simples vs. claim absoluto que exige verificação. Reviews em sites de afiliado são **levemente inclinados ao positivo por design** — qualificadores positivos NÃO são violação editorial.

Use `superlativas qualificadas` quando houver dado de comparação na bíblia:
- ✓ "entre os mais econômicos da categoria EcoTank" (se bíblia tem `concorrentes` populado)
- ✓ "um dos mais leves" (se bíblia tem comparação de peso)

### 6. `html-invalido`

**6a. Tags proibidas em `fullReview`** (`<h2>`, `<h3>`, `<ul>`, `<ol>`, `<li>`, `<table>`, `<img>`, `<script>`, `<iframe>`, `<style>`). Permitido apenas: `<p>`, `<strong>`, `<em>`, `<a>`.

**6b. HTML em campos TEXTO-PURO** (sub-tipo da mesma categoria, severity crítica): `subtitle`, `shortDescription` e `specs[].value` são strings TEXTO PURO renderizadas por Astro com `{var}` (escape XSS automático). Qualquer tag HTML literal nesses campos (`<strong>`, `<em>`, `<a>`, `<p>`) aparece como TEXTO LITERAL pro usuário (não-renderizada). Verificar via regex `<\w+[^>]*>` em cada um dos 3 campos. Caso real 2026-05-26: shortDescription do Integralmédica Huger vazou `<strong>energia...</strong>` → exibido literal no card da página individual.

**6c. HTML no meio do texto de `pros[N]` ou `cons[N]`** (após o `:` que separa título de explicação). O `<strong>Título</strong>` no início está PERMITIDO (template usa `set:html` ali); mas `<strong>` aninhado no texto da explicação **vira texto literal** (mesmo bug). Regex de detecção: depois do primeiro `</strong>:`, qualquer `<\w+` é violação.

### 7. `link-externo-nao-amazon`
Links em `fullReview` que NÃO apontam pra `amazon.com.br/dp/...`. Página individual não deve ter links externos pra outras lojas/sites.

### 8. `tamanho-fora-de-faixa` (régua v1.16.0 — antes era só `conteudo-curto`)

Campo fora dos limites editoriais — pode estar **curto demais** (vazio/incompleto) ou **longo demais** (regressão de escanabilidade, similar ao caso `melhorpretreino`).

**Curto demais** (severidade: depende do campo):
- `subtitle` ausente ou < 10 chars
- `shortDescription` ausente ou < 50 chars (era 40 antes da v1.16.0)
- `fullReview` ausente ou < 300 chars
- `pros` < 3 itens
- `cons` ausente ou 0 itens
- `specs` < 3 pares

**Longo demais** (severidade: Crítico — quebra escanabilidade do card):
- `subtitle` > 150 chars
- `shortDescription` > 250 chars (HARD CAP régua v1.16.0; alvo 180-230)
- `pros[i]` item > 180 chars texto puro (descontando markup `<strong>`/`<a>`)
- `cons[i]` item > 180 chars texto puro
- `fullReview` > 3000 chars

**Padrão técnico-first** (sub-check `tamanho-fora-de-faixa-padrao`, régua v1.17.0):
- Detecta `shortDescription` que abre com técnico em vez de benefício-first
- **Antipadrões na 1ª frase** (flag):
  - "[Tipo] brasileiro/a da [marca]..." (ex: "Impressora multifuncional da Epson...")
  - "[Tipo] com X mg de Y..." / "[Tipo] com [spec técnica]..."
- **Padrões OK na 1ª frase**: adjetivo posicional, "Ideal pra quem...", "Você ganha...", posicionamento direto
- Fix: inverter ordem — posicionamento/benefício na 1ª frase, técnico justifica depois. Ver moldes A/B/C em `pagina-produto-criar` v1.17.0.

**Como contar pros/cons sem HTML**: olhe o bullet sem `<strong>...</strong>` e sem `<a href="...">...</a>` mantendo só o texto interno. Se passa de 180 = flag.

Canon vivo `melhoraspirador` (referência): shortDescription média 225 chars, pros/cons média 65 chars/item, máx 93.

### 9. `redundancia-com-artigo`
Se conseguir detectar: pontos no `fullReview` da página individual que parecem copiados/parafraseados do `fullReview` do produto-no-artigo (anti-duplicate-content SEO).

Heurística: frases-chave repetidas, mesma sequência argumentativa, conclusões iguais. Não precisa ser idêntico — paráfrase próxima conta como redundância.

Se nenhum review cita o ASIN, essa categoria sai vazia automaticamente (não há com que comparar).

### 10. `voz-citacao-ficha-tecnica`

Detecta marcadores de procedência **burocráticos** no .mdx — quando o modelo copiou da bíblia sem destilar. Diretrizes #5 e #6 da bíblia proíbem isso ("não pode parecer leitura de planilha").

**Padrões pra grep**:
- "alérgenos da Amazon confirmam"
- "atributos de material declaram"
- "conforme tipo de dieta"
- "conforme declarado pelo fabricante" / "conforme o fabricante" (sem qualificar)
- "apontada pelo fabricante como" / "apontado pelo fabricante como"
- "relato recorrente nas opiniões" / "segundo relatos de compradores"
- "citada como motivo de preferência por um comprador"
- "datasheet" / "no datasheet"
- "anúncio Amazon" / "apesar do anúncio Amazon listar"

**Severidade: 🟡 Aviso** (não crítico) — porque "segundo X" pode ser **editorial OK** em casos específicos. Verificar contra a régua:

Voz-citação OK SÓ quando atende AS DUAS condições:
1. **(a)** qualifica claim que SÓ o fabricante pode fazer (rendimento, garantia interna, certificação proprietária)
2. **(b)** adiciona valor editorial ao leitor (calibra expectativa, sinaliza honestidade, faz crítica útil)

**✓ Exemplos editorial OK** (não flagar, ou flagar como info):
- "rende até 4.500 páginas em preto, segundo a Epson" *(rendimento é claim só-fabricante + qualifica)*
- "número de marketing 33 ppm, mas a velocidade ISO é mais realista" *(crítica útil)*
- "a HP recomenda volume de 50 a 100 páginas mensais" *(claim só-fabricante)*

**❌ Exemplos burocráticos** (flagar aviso):
- "alérgenos da Amazon confirmam ausência de glúten" → reformula pra "sem glúten"
- "atributos de material declaram ausência de contaminantes" → "livre de contaminantes"
- "apontada pelo fabricante como mais absorvível" → "considerada mais absorvível"

Reportar no relatório com sugestão de reformulação destilada. Humano decide se aceita.

### 11. `voz-comprador-implicita` (severidade: 🔴 Crítico)

Diferente da categoria 3 (`tone-comprador`) que pega menções EXPLÍCITAS de "compradores"/"reviews"/"avaliações", esta pega **voz-comprador SUTIL** que o sub-agent não destilou da bíblia. Régua "destilação categoria D" canonizada 2026-05-26 (v1.11.4).

**Padrões pra grep em qualquer campo (subtitle, shortDescription, pros, cons, specs.value, fullReview)**:
- "opiniões" (no sentido de opiniões de compradores)
- "comentários" (no sentido de comentários de quem comprou)
- "um comprador relata" / "um comprador descreve"
- "divide opiniões" / "opiniões divididas" / "opiniões mistas"
- "elogios recorrentes" / "elogiado nas opiniões"
- "recepção [mista/dividida/positiva]"
- "avaliações" (no sentido Amazon, não avaliação técnica)
- "bem recebido [pelos/nos]"
- "ponto positivo recorrente nas opiniões"
- "queixa recorrente"

**Caso real 2026-05-26** (batch melhorpretreino, 3 produtos via `pagina-produto-criar-em-massa` v1.11.3):
- `dux-energy-kick` pros[4]: "paladar bem recebido pelos comentários disponíveis"
- `dux-energy-kick` fullReview: "Um comprador inclusive descreve uso durante o treino"
- `dux-pre-workout` cons[0]: "Sabor divide: opiniões sobre o sabor são mistas"
- `dux-pre-workout` fullReview: "O sabor maçã verde divide opiniões"

Sub-agent v1.11.3 reconhecia voz-comprador EXPLÍCITA na bíblia mas CAÍA em SUTIL ("um comprador relata", "divide opiniões"). v1.11.4 adicionou auto-check na skill de criação — esta audit cobre defesa em camadas.

**Exemplo flag (errado vs certo)**:
- ❌ "Sabor divide opiniões" → ✅ "Sabor maçã verde é frutado, pode não agradar quem prefere perfis mais neutros"

### 12b. `jargao-tecnico-vazado` (régua v1.17.3, severidade: 🔴 Crítico)

Termos de dev/estoque/regulatório que NUNCA devem aparecer no texto público. Gap real descoberto no melhorpretreino: bullets de produto continham "SKU avaliado" / "ASIN aqui só vem em...".

**Termos PROIBIDOS** (em subtitle, shortDescription, fullReview, pros, cons, specs.value):
- `\bSKU\b`, `\bASIN\b`, `\bUPC\b`, `\bEAN\b`, `\bGTIN\b` — identificadores técnicos
- `\bdatasheet\b`, `\bdataset\b`, `\bfrontmatter\b`, `\bmetadata\b` — jargão dev
- `\bnotificado\b` (regulatório) — soa bula

**IGNORAR** matches no frontmatter YAML (`asin:`, `image:` são campos técnicos por design, não renderizam).

**Fix**: substitua por linguagem editorial — "SKU avaliado" → "versão avaliada"; "ASIN aqui" → "produto avaliado"; "alimento notificado sob N°..." → "produto registrado na ANVISA".

### 13. `chavoes-por-nicho` (régua v1.18.0, severidade: 🔴 Crítico)

Lê `docs/painel/_data/chavoes-por-nicho.json` baseado em `niche` do site (`docs/painel/sites-meta.json`). Conta termos em texto público (subtitle, shortDescription, fullReview, pros, cons, specs.value), excluindo frontmatter YAML técnico (campos `asin:`, `image:`, etc).

Aplica limites de `_genericos` + bloco do nicho específico (`Pré Treino`, `Creatinas`, `Tablets`, etc.). Banidos absolutos (`lineup`, `SKU`, `ASIN`, `trade-off`, `hardcore`, `datasheet`) flagam imediatamente; demais flagam quando passam do `_max` definido.

Fix: variação léxica (alternativas PT-BR documentadas) + destilação cirúrgica.

### 12. `termos-tecnico-industriais` (severidade: 🔴 Crítico)

Termos técnico-industriais proibidos pela régua editorial (canonizada 2026-05-26 v1.11.4). Soam como rotulagem técnica/ANVISA — quebram a voz editorial.

**Padrões pra grep em qualquer campo**:
- "contaminação cruzada"
- "linha de produção compartilhada" (sem contexto editorial)
- "sujeito a contaminação"
- "risco de contaminação por proteínas"

**Caso real 2026-05-26**: `essential-nutrition-beta-action` cons[3] usou "considerar o risco de contaminação cruzada na linha de produção". Audit pegou — sugerido fix:

- ❌ "Risco de contaminação cruzada na linha de produção"
- ✅ "Pode conter traços de leite — alérgicos severos devem ler a rotulagem antes do uso"

Linguagem editorial em vez de técnica. Aviso é crítico porque quebra a voz, não é um qualificador a debater.


### 14. `capitalizacao-duplicacao` (régua v1.18.3, severidade: 🔴 Crítico)

Detecta bugs de substituição mecânica que vazam pro output:

**Sub-checks:**
- **14a — duplicação contígua**: regex `([a-zA-ZÀ-ÿ\s]{8,40})\1` em qualquer campo. Ex real (`a72e7d9`): "sem empilhar suplementos sem empilhar suplementos"
- **14b — bullet minúsculo**: bullet de pros/cons começa com `<strong>[a-z]`. Ex real: `<strong>aminoácidos essenciais na fórmula</strong>` (era `<strong>BCAAs na fórmula</strong>` antes da substituição)
- **14c — minúscula após ponto**: padrão `\. [a-z]` em texto editorial (excluir URLs amazon.com.br). Ex real: "(maior dose declarada). pra emagrecer onde"

**Causa raiz**: substituições mecânicas com palavras minúsculas viram bug em posição de início de frase/bullet, ou colidem com cauda já existente.

**Fix proposto**: capitalizar primeira letra ou destilar duplicação. Bug-class encontrado pela 1ª vez em commit a72e7d9 (melhorpretreino).

### 15. `concordancia-quebrada-pt-br` (régua v1.19.0, severidade: 🔴 Crítico)

**Bug-class** (ChatGPT-Bárbara 2026-05-28): substituições mecânicas v1.17-1.18 não reconcordaram plural/gênero/artigo.

**Sub-checks (regex em todos os 6 campos editoriais)**:

| Sub | Regex | Exemplo |
|---|---|---|
| 15a `plural-aos-errado` | `\b(composição\|combinação\|porção\|injeção\|reação\|opção)s\b` | `composiçãos` → composições |
| 15b `artigo-fem-antes-masc` | `\b(a\|na\|da\|esta) (produto\|formigamento\|ingrediente\|ativo)\b` | `a produto` → o produto |
| 15c `artigo-masc-antes-fem` | `\b(o\|no\|do\|este) (fórmula\|dose\|porção\|composição)\b` | `o fórmula` → a fórmula |
| 15d `adjetivo-quebrado` | `produto[s]? elaborada[s]?\b\|produto ampla\|formula natural` | `produto ampla` → fórmula ampla |
| 15e `duplicacao-prep` | `\b(?:disponíveis?\|disponível) no em \d{4}\|Pra a (maioria\|primeira)` | `disponíveis no em 2026` → disponíveis em 2026 |
| 15f `genero-errado` | `\b(as produtos\|os fórmulas)\b` | `as produtos em geral` → os produtos em geral |
| 15g `termo-duplicado-parens` | `([a-zA-ZÀ-ÿ]{5,30}) \(\1\)` | `formigamento (formigamento)` |

**Fix proposto**: regex find-and-replace direto, sem ambiguidade semântica.

### 16. `health-absolutes-ymyl` (régua v1.19.0, severidade: 🔴 Crítico)

**Bug-class** (ChatGPT-Bárbara ponto 7): absolutos de segurança/saúde violam diretrizes YMYL do Google ("Your Money Your Life") — Google penaliza páginas afiliadas que afirmam segurança absoluta sem fonte.

**Termos banidos absolutos** (limite 0 em qualquer dos 6 campos):
- `uso regular é seguro`
- `alternativa segura` (sem qualificar contra o quê)
- `não causa dano`
- `totalmente seguro` / `100% seguro` / `sem riscos`
- `sem efeitos colaterais`
- `cientificamente comprovado` / `clinicamente comprovado` (sem citar estudo)

**Fix proposto**: qualificar sempre — "Tolerado pela maioria; consulte um profissional se tem comorbidade" em vez de "uso regular é seguro".

## Filtros editoriais — flag se aparecer nos campos curados

Também sinalizar (severidade `aviso`):

- **Specs ambientais** (% plástico reciclado, certificações eco como Energy Star/EPEAT/RoHS/FSC, programas de devolução tipo "HP Planet Partners", neutralidade de carbono) em qualquer dos 6 campos. Exceto se a bíblia tem `angulosConversao` com tema `sustentabilidade` marcado.
- **Origem de fabricação** ("fabricado no Brasil", "made in X", "produto nacional") em qualquer dos 6 campos. Exceto se a bíblia tem `angulosConversao` com tema `produto-nacional`.

## Formato do relatório

Template exato — use blocos idênticos pro painel parsear visualmente:

```markdown
# Auditoria: {productName} — {site}/{slug}

- **Data:** {YYYY-MM-DD HH:MM}
- **ASIN:** {ASIN}
- **Status:** {N críticos, M avisos, K info}

## 🔴 Crítico ({N})

<lista ou "nenhum">

### {título curto do achado}
- **Campo:** `{campo.path}` (ex: `pros[2]`, `fullReview`, `specs[0].value`)
- **Categoria:** `{categoria do check}` (ex: `claim-vs-bible`, `tag-affiliate`)
- **Evidência:** "{trecho literal < 15 palavras}"
- **Problema:** {descrição em 1-2 frases}
- **Sugestão:** {o que fazer — humano decide se aceita}

## 🟡 Avisos ({M})

<mesma estrutura>

## 🔵 Info ({K})

<mesma estrutura — achados menores>

## ✅ Passou

- <lista bullet curta das categorias sem problemas>
```

## Classificação de severidade

- **🔴 Crítico**: claim factualmente errado vs bíblia, tag affiliate violada, HTML proibido (inclui sub-checks 6a/6b/6c), tone-comprador EXPLÍCITO, voz-comprador-implicita (categoria D, régua v1.11.4), termos-tecnico-industriais (régua v1.11.4), **tamanho-fora-de-faixa LONGO demais** (régua v1.16.0 — shortDescription >250, pros/cons >180 texto puro; cards viram parágrafos).
- **🟡 Aviso**: superlativo sem evidência, conteúdo curto em campo opcional, specs ambientais sem ângulo, suspeita de duplicate content, voz-citação ficha-técnica burocrática.
- **🔵 Info**: nota que vale registrar mas não exige ação (ex: "subtitle no limite mínimo de 10 chars, considere expandir").

## Boas práticas

- Se a página está quase vazia (stub recém-criado, antes de rodar `pagina-produto-criar`), resuma em 1 bullet "página em estágio inicial; checagens de conteúdo adiadas até preenchimento" e termine.
- Prefira 5 findings bem evidenciados a 20 vagos. Assine valor, não volume.
- Se errou na auditoria (ex: confundiu campo X com Y), o humano vê no diff do markdown na próxima rodada. Não há vergonha em revisar o próprio relatório.

## Exemplo de invocação

```
audita a página individual da L3250 no melhorimpressora
audita o produto epson-ecotank-l3250 do melhorimpressora
audita melhorimpressora/epson-ecotank-l3250
```

Args canônico: `Skill(skill="pagina-produto-auditar", args="melhorimpressora/epson-ecotank-l3250")`.
