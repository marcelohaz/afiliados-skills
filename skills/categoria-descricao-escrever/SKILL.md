---
name: categoria-descricao-escrever
description: Escreve a descrição HTML de uma categoria do site (`/categoria/{slug}/`). Aceita URL do painel (editor-categoria.html?site=X&slug=Y) OU args canônicos site/categorySlug. Régua dura — 2-3 parágrafos `<p>` (sem outras tags de bloco), 100-2000 chars, inline `<strong>`/`<em>`/`<a>`/`<br>` OK, PROIBIDO `<h1>`/`<h2>`/`<h3>`/`<ul>`/`<ol>`/`<table>`/listas/headings. Substitui só a entry da categoria no `categoryDescriptions` do config.ts — resto do config preservado. Backup + commit + push + sync VPS.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida — fluxo natural depois de abrir o editor):
- `https://painel.melhorserum.com.br/editor-categoria.html?site=escritoriocasa&slug=impressoras`
- Extrai `site` e `slug` (= categorySlug) do query string

**B) Args canônicos**:
- `escritoriocasa/impressoras`

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B (split por `/`).

**Instrução opcional**: se o prompt natural do user contém algo tipo "mais conciso", "enfatize ergonomia", "tom mais informal" → eu extraio como instrução adicional e uso no prompt. Se for só "escreve a descrição da categoria X" → modo padrão.

# Escrever descrição de categoria

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:category_description`. O conteúdo essencial está duplicado abaixo pra autocontenção; em caso de divergência, o prompt canônico ganha.

Você é o curador editorial das descrições de categoria. Cada site afiliado tem um objeto `categoryDescriptions: Record<string, string>` no `sites/{site}/src/config.ts`, onde cada chave é o slug da categoria (ex: `'impressoras'`) e o valor é HTML em template literal (backtick).

A descrição aparece no **topo da página `/categoria/{slug}/`** do site — função SEO + editorial — apresentando o nicho e orientando o leitor pra navegar pelos artigos da categoria. **NÃO é guide** ("Como escolher") nem **review** (comparativo de produtos). É uma **prosa curta** sobre a categoria em si.

## Pré-requisitos

- O site existe em `sites/{site}/src/config.ts`.
- O site tem objeto `categoryDescriptions: { ... } as Record<string, string>` no config (todos os 8 sites têm).
- A categoria tem ≥1 artigo no site (`category` ou `categorySlug` nos `.mdx` de `sites/{site}/src/content/reviews/`) OU é entry "órfã" no `categoryDescriptions` existente.

Se ambos faltam (categoria não existe nos reviews E não tem entry no config), abortar com aviso "Categoria X não tem nenhum artigo nem entry no config. Cria categorias adicionando artigos com `categorySlug: 'X'` primeiro."

## Invariantes

- **Nunca toque em nada além da entry específica do `categoryDescriptions`** no config.ts. Outros campos do siteConfig (name, slug, domain, navItems, etc.) ficam intactos.
- **HTML em template literal** (backtick `` ` ``) — formato canônico do projeto.
- **Allowlist de tags**: bloco `<p>` apenas. Inline OK: `<strong>`, `<em>`, `<a>`, `<br>`. (O sanitize do painel tecnicamente também aceita `<b>` e `<i>` como fallback, mas o prompt canônico só permite `<strong>` e `<em>` — uso a allowlist editorial restrita.)
- **PROIBIDO** tags de bloco: `<h1>`, `<h2>`, `<h3>`, `<ul>`, `<ol>`, `<li>`, `<table>`, `<div>`, `<section>`, `<aside>`, `<img>`, `<script>`, `<iframe>`, `<style>`, `<form>`.
- **Sem listas de qualquer tipo** (`<ul>`/`<ol>`/`<li>`) — listagem vira frase em prosa.
- **2 a 3 parágrafos `<p>`.** Ideal: 3 (estrutura canônica). 2 aceitável se o nicho é simples.
- **100 a 2000 chars** total no HTML.
- **CRÍTICO — sem backtick `` ` `` literal no HTML.** Quebraria o template literal do config.ts. Se precisar de citação, usar aspas ou itálico.
- **CRÍTICO — sem `${` literal no HTML.** Seria interpretado como interpolação JS no template literal (corrompe config OU pior, executa código). Sanity-check obrigatório: se a IA gerar `${...}`, regenero.
- **Sem travessão (—).** Use vírgula ou ponto.
- **Sem superlativos sem evidência** ("o melhor disponível", "incomparável", "imbatível"). "Excelente", "ótimo" são OK contextualizados.
- **Sem comentários HTML, sem placeholders `[TODO:...]`.**
- **Português brasileiro editorial.** Sem gírias, sem anglicismos desnecessários.

## Fluxo

1. **Parse args**: detecta URL vs canônico, extrai `site` e `categorySlug`. Valida `[a-z0-9-]+` em ambos.

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   git stash push -m "skill-categoria-descricao-escrever-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Painel VPS commita+pusha automaticamente quando user cria/edita conteúdo na UI; Mac local pode estar 5-30s atrás. Sem este pull, skill pode ler estado stale e abortar com falso "X não existe localmente". Se pull falhar (rede offline, conflito), seguir mesmo assim.

2. **Read `config.ts`**: `Read sites/{site}/src/config.ts`. Se 404, abortar.

3. **Extrair `siteName`**: regex `/^\s*name:\s*['"]([^'"]+)['"]/m` no config. Se não achar, fallback pro `site` (slug). Mesmo padrão do handler (`category-desc.ts:426`).

4. **Extrair `categoryDescriptions` atual**: capturar o objeto `categoryDescriptions: { ... } as Record<string, string>` (regex `BLOCK_RE` em `_lib/category-desc.ts:20`). Detectar:
   - Entry já existe pra esse `categorySlug` (vai substituir) — capturar HTML antigo pra contexto e backup mental.
   - Entry não existe (vai adicionar nova).

5. **Detectar `categoryName`** (nome bonito da categoria):
   - Listar `sites/{site}/src/content/reviews/*.mdx`
   - Pra cada `.mdx`, ler frontmatter e extrair `category` e `categorySlug` (se houver ambos)
   - Buscar artigo com `categorySlug === {param categorySlug}`; se achar, `categoryName = category`
   - Se nenhum artigo tem esse `categorySlug` (categoria órfã), fallback: `categoryName = categorySlug` (slug cru, sem capitalizar — paridade com `category-desc.ts:420`: `fromReviews.get(slug)?.name ?? slug`)

5.1. **GUARD de slug acentuado/malformado (canon 2026-06-19) — OBRIGATÓRIO antes de gravar:**
   - Ao listar os `categorySlug` dos artigos, **normalize acento pra comparar** (`s.normalize('NFD').replace(/[̀-ͯ]/g,'')`).
   - **Se algum artigo tem `categorySlug` com acento/maiúscula/espaço** (ex: `pré-treino`, `Tablets`, `whey protein`) → é **slug malformado**: gera `/categoria/{slug}/` 404 E faz a descrição (que fica na chave sem-acento do config) virar **órfã** (bug real: melhorpretreino-com `pré-treino` vs config `pre-treino`, 2026-06-19). **NÃO escreva a descrição** nesse caso — **ABORTE com aviso**: "categorySlug malformado nos artigos [arquivos]: `{slug-cru}`. Conserte o slug nos `.mdx` pra `{slug-normalizado}` ANTES (mesma normalização do `article-builder.slugify`), senão a descrição nasce órfã. (Se o artigo está `contentLocked`, destrave via painel primeiro.)"
   - **Se o `categorySlug` PARAM passado tem acento** → normalize-o (sem-acento) e use a versão limpa como chave da descrição (a chave do `categoryDescriptions` é SEMPRE sem-acento).
   - Só prossiga quando o slug-param normalizado **bater** com o `categorySlug` (já normalizado) de ≥1 artigo, OU for órfã legítima do config. Mismatch acento ≠ órfã legítima.

6. **Detectar instrução opcional** no prompt do user (paridade com outras skills):
   - "mais conciso" / "enfatize X" / "sem chamada pra ação" → extrai como instrução
   - Sem instrução clara → modo padrão

7. **Compor contexto pra geração**:
   - `siteName` (ex: "Escritório Casa")
   - `categoryName` (ex: "Impressoras")
   - `categorySlug` (ex: "impressoras")
   - URL pública: `/categoria/{categorySlug}/`
   - Instrução opcional

8. **Gerar o HTML** seguindo a régua editorial (ver seção abaixo). 2-3 parágrafos `<p>` apenas.

9. **Validar mentalmente** antes de salvar:
   - 100-2000 chars
   - 2-3 `<p>...</p>` (count das tags de bloco)
   - ZERO tags proibidas (`<h1>`/`<h2>`/`<ul>`/etc.) — Grep mental
   - ZERO `` ` `` (backtick) literal
   - ZERO `${` literal
   - Sem travessão
   - Sem comentários HTML `<!-- ... -->`
   - Sem placeholders `[TODO:...]`
   - Não começa nem termina com whitespace estranho

10. **Backup** ANTES de sobrescrever (paridade com handler `category-desc.ts:139-147`):
    ```bash
    DAY=$(date +%Y-%m-%d); TIME=$(date +%H%M%S); SITE={site}; SLUG={categorySlug}
    PROJ=$(pwd)
    mkdir -p "$PROJ/docs/painel/.painel-backups/$DAY"
    cp "$PROJ/sites/$SITE/src/config.ts" \
       "$PROJ/docs/painel/.painel-backups/$DAY/config-${SITE}-${TIME}-cat-${SLUG}.ts"
    ```
    **Pattern do nome**: `config-{site}-{HHMMSS}-cat-{categorySlug}.ts`. Note que esse nome **NÃO bate** com o regex do `backups.ts:99` (que só aceita `article|guide|page|product` como prefix e `.mdx|.html` como ext), então não aparece no card "Histórico de versões" do painel. Backup é só recovery manual.

11. **Substituir entry via Edit tool** no `config.ts`:
    
    **Caso A — entry já existe** (`'{categorySlug}': \`...\`,` OU `"{categorySlug}": \`...\`,`):
    - `old_string` = entry completa, formato: `<aspa>{categorySlug}<aspa>: \`...HTML antigo completo...\`,` — note que a chave pode estar entre aspas simples OU duplas (ENTRY_RE em `category-desc.ts:43` aceita ambas; verificar o config real antes de montar o `old_string`)
    - `new_string` = nova entry sempre com aspas simples: `'{categorySlug}': \`{NOVO HTML}\`,` (paridade com `category-desc.ts:89`)
    
    **Caso B — entry ainda não existe** (categoria órfã ou nova):
    - Achar o fim do bloco `categoryDescriptions: { ... }` — geralmente vem fechado com `\n  } as Record<string, string>,`
    - **Caso B1 — bloco vazio** (`categoryDescriptions: {}`):
      - `old_string` = `categoryDescriptions: {} as Record<string, string>,`
      - `new_string` = `categoryDescriptions: {\n    '{categorySlug}': \`{HTML}\`,\n  } as Record<string, string>,`
    - **Caso B2 — bloco tem entries** (adicionar ao final):
      - Detectar a última entry (`'{outroSlug}': \`...\`,` ou `'{outroSlug}': \`...\``)
      - Garantir vírgula final na entry anterior
      - Adicionar nova linha indentada com 4 espaços: `    '{categorySlug}': \`{HTML}\`,`
      - Risco: a linha do `as Record<string, string>` precisa ficar intacta
    
    **CRÍTICO**: ao colar o HTML novo dentro do template literal, garantir que:
    - Não tem backtick `` ` `` no HTML (quebra o template)
    - Não tem `${...}` no HTML (interpola JS)
    - Indent do template é preservado (4 espaços antes da chave da entry)
    
    Em caso de dúvida sobre o `old_string` ambíguo (ex: 2 entries têm HTML quase idêntico), incluir 1-2 linhas de contexto antes/depois.

12. **Git add + commit + push**:
    ```bash
    git add sites/{site}/src/config.ts
    git commit -m "chore({site}): atualiza descrição categoria {categorySlug} via skill" \
      -m "Co-Authored-By: {modelo da sessão} <noreply@anthropic.com>"
    git push origin main
    ```
    Mensagem é `chore` (não `feat`) — paridade com o handler do painel (`category-desc.ts:288`).

13. **Disparar git pull no painel da VPS**:
    ```bash
    bash scripts/painel-vps-pull.sh
    ```
    Falha graciosamente se `.env.painel-skills` não existir.

14. **Reportar no chat**: char count do HTML + número de parágrafos + indicação se foi substituição ou inserção nova + path do arquivo.

## Régua editorial — ESTRUTURA SUGERIDA (3 parágrafos)

Não é estrita, mas é o pattern dos exemplos canônicos:

### §1 — Introdução: o desafio + critérios em `<strong>`

Apresenta o nicho e o desafio de escolher na categoria. Lista 3-6 critérios técnicos em `<strong>...</strong>`. Tom de "vou te ajudar a entender".

**Exemplo** (categoria "creatinas"):
> `<p>Escolher a creatina certa pode parecer simples, mas o mercado brasileiro oferece dezenas de opções com propostas muito diferentes entre si. Aqui você encontra comparativos e guias organizados para facilitar sua decisão, considerando critérios como <strong>tipo de creatina</strong>, <strong>pureza</strong>, <strong>quantidade por dose</strong>, <strong>sabor</strong>, <strong>custo-benefício</strong> e <strong>certificações de qualidade</strong>: os fatores que realmente fazem diferença nos seus resultados.</p>`

### §2 — Perfis de uso: tipos/nichos cobertos pelos artigos

Lista os perfis de comprador/uso que aparecem nos artigos da categoria. Cada perfil em `<strong>...</strong>` (3-5 perfis). Tom de "cobrimos isso".

**Exemplo**:
> `<p>Cobrimos os principais perfis de uso: desde creatinas para <strong>ganho de massa muscular</strong> e <strong>performance atlética</strong>, até opções voltadas para <strong>veganismo</strong>, <strong>dietas específicas</strong> e <strong>praticantes iniciantes</strong>. Cada perfil tem pontos fortes específicos, e nossas análises ajudam você a entender qual se encaixa melhor na sua rotina de treino.</p>`

### §3 — Convite ao leitor (opcional)

Chama pra navegar pelos artigos. Pode ser omitido se a descrição fica grande demais.

**Exemplo**:
> `<p>Navegue pelos artigos, leia os prós e contras reais de cada produto e chegue à sua próxima compra com confiança, sabendo exatamente o que esperar antes de o produto chegar na sua casa.</p>`

## Régua ANTI-CLONE (CRÍTICO — v1.20.0, canon 2026-06-12)

Os exemplos acima são **UM** preenchimento possível do esqueleto, **NÃO um template pra copiar verbatim**. Sem variação, categorias diferentes (e pior, sites de **MESMO nicho**) saem com descrição quase idêntica = **duplicate content** — fatal pra estratégia SERP-monopoly (2+ sites no mesmo nicho: impressoras = melhorimpressora+impressoraideal, pré-treino = melhorpretreino+melhorpretreino-com, creatina ×3) e pro guarda-chuva **melhoressuplementos** (que sobrepõe TODOS os nichos: creatinas, whey, ômega-3, pré-treino, suplementos). O `§3` "...antes de o produto chegar na sua casa" é o pior ofensor: niche-agnostic, o modelo copia verbatim em todo lugar.

**Passo OBRIGATÓRIO antes de gerar** — leia as descrições de categoria JÁ existentes de **(a)** outras categorias do mesmo site e **(b)** sites de MESMO nicho (ex: gerando `impressoras` no impressoraideal → leia o `impressoras` do melhorimpressora). Anote a abertura (§1) e o fecho (§3) de cada uma, pra divergir.

**Regras de divergência (hard):**
1. **Zero sequências de ≥8 palavras** iguais a uma descrição irmã (mesmo site) ou de mesmo nicho (site irmão).
2. **NÃO reusar a família de abertura** "Escolher [o/a] {X} certo/a pode parecer simples, mas o mercado brasileiro oferece dezenas..." se já usada numa irmã/mesmo-nicho. Rotacione (pool abaixo).
3. **NUNCA repetir o §3 verbatim** ("...antes de o produto chegar na sua casa"). Varie o fecho ou omita o §3.
4. Critérios (§1) e perfis (§2) **específicos do nicho** — não a lista genérica reaproveitável.

**Pool de aberturas §1** (rotacione; não repita no site nem entre sites do mesmo nicho):
- "Escolher [a/o] {X} certo/a pode parecer simples, mas..."
- "Procurando [a/o] {X} ideal? ..."
- "O mercado de {X} no Brasil..."
- "{X} deixaram de ser [coisa rara] e viraram..."
- "Se o seu objetivo é {benefício do nicho}, ..."
- "Reunimos aqui os comparativos de {X}..."

**Pool de fechos §3** (rotacione; ou omita — 2 parágrafos bastam):
- "Navegue pelos artigos e compare os modelos lado a lado..."
- "Explore os comparativos e decida com base no que mais importa pra você."
- "Veja as análises completas e escolha com segurança."
- "Compare as opções e encontre [a/o] {X} ideal pra {contexto}."

**Teste final:** abra a descrição da categoria irmã / mesmo-nicho lado a lado. Se a abertura OU o fecho são da mesma família → reescreva.

## Restrições críticas (NÃO QUEBRE)

### 1. Sem tags de bloco além de `<p>`

PROIBIDO: `<h1>`, `<h2>`, `<h3>`, `<ul>`, `<ol>`, `<li>`, `<table>`, `<div>`, `<section>`, `<aside>`, `<img>`, `<script>`, `<iframe>`, `<style>`, `<form>`, `<button>`.

**Por quê**: a página `/categoria/{slug}/` já tem H1/H2 estruturais (do layout Astro). Adicionar mais headings quebra hierarquia. Listas (`<ul>`/`<ol>`) viram prosa com vírgulas.

PERMITIDO inline: `<strong>`, `<em>`, `<a href="...">`, `<br>` (este último com moderação).

### 2. Sem backtick literal `` ` ``

O HTML vai pra dentro de um template literal JavaScript no `config.ts`. Backtick interno quebra o parser. Se precisar destacar texto, usar `<strong>` ou `<em>`.

### 3. Sem `${` literal

Padrão `${expr}` em template literal = interpolação JavaScript. Se o HTML tiver `${algumaCoisa}`, o JS vai tentar avaliar. Em runtime, isso vira `undefined` (corrompe a descrição) ou pior — execução de código se `algumaCoisa` for um nome válido no escopo. Defesa crítica: validar antes de salvar.

**Exemplo problemático**: `<p>Combina com bebidas como suco, água ou shakes do tipo ${ingrediente principal}.</p>` — o `${...}` é interpretado. Reescrever sem `${`.

### 4. Sem listas de qualquer tipo

`<ul>` e `<ol>` são proibidos. Listagem vira prosa com vírgulas + `<strong>`. Padrão dos exemplos canônicos.

### 5. Sem comentários HTML, sem placeholders

Nada de `<!-- TODO -->` ou `[TODO: preencher]`. HTML é o conteúdo final que vai pra produção.

### 6. Sem travessão (—)

Mesma regra editorial de todo o projeto. Vírgula, ponto, dois pontos.

## Voz editorial

- **Tom de "estamos aqui pra ajudar".** Não vende produto específico — apresenta o nicho e orienta navegação.
- **Linguagem editorial.** Sem gírias, sem anglicismos desnecessários, sem "expert" / "best" / "top".
- **NÃO mencione produtos/marcas específicas.** Linguagem geral da categoria. Marcas vão nos artigos.
- **NÃO cite compradores/reviews/avaliações/Amazon.** Padrão da voz editorial do projeto.
- **Tom de conhecimento, não de vendedor.** "Cobrimos os principais perfis" > "Encontre o melhor X aqui!".

## Tom conversacional (CRÍTICO)

Pergunta-teste antes de salvar: *"Um amigo que não entende disso entenderia?"* Se não → simplifica.

Evite jargão corporativo (❌ "alinhado à narrativa de categoria", "posicionamento de mercado"). Use linguagem direta de quem orienta (✓ "se você procura X, considere Y"). NÃO cite procedência burocrática ("conforme dados", "segundo Amazon") — descrição de categoria não precisa justificar fonte.

Referência canônica: leia outras descrições de categoria já travadas em `sites/*/src/config.ts` (`categoryDescriptions`).

## Filtros editoriais (paridade com outras skills)

- **Specs ambientais** (% reciclado, Energy Star, EPEAT, etc.) → omitir, salvo se for tese central da categoria.
- **Origem de fabricação** ("fabricado no Brasil") → idem.


## Régua editorial PT-BR (v1.19.2, 2026-05-28)

Antes de gravar, faça grep dos padrões abaixo. Se aparecer — corrija.

### Concordância PT-BR (bug-class real de substituições mecânicas)

| Padrão | Fix |
|---|---|
| `composiçãos`, `combinaçãos`, `porçãos` | `composições`, `combinações`, `porções` (plural correto em -ões) |
| `a produto`, `a formigamento`, `a ingrediente` | `o produto`, `o formigamento`, `o ingrediente` |
| `o fórmula`, `o dose`, `o composição` | `a fórmula`, `a dose`, `a composição` |
| `produto ampla`, `produtos elaboradas`, `formula natural` | `fórmula ampla`, `produtos elaborados`, `fórmula natural` |
| `disponíveis no em 2026` | `disponíveis em 2026` |
| `Pra a maioria/primeira` | `Pra` ou `Para a` |

### Linguagem artificial banida (calques de inglês, jargão pseudo-técnico)

- `calibrar/calibrada/calibragem` = 0 → use "ajustar"
- `empilhar` = 0 → use "usar separado"
- `pico-e-queda` = 0 → "pico de energia seguido de queda"
- `energia metabólica/adrenérgica` = 0
- `peers/claim/stack/trade-off/hardcore` = 0
- `SKU/ASIN/UPC/EAN/datasheet/notificado` = 0 (banidos no público)

### Voz consultiva (não corporativa)

| ❌ Corporativo | ✓ Conversacional |
|---|---|
| "diferencial central" | "o grande ponto é" |
| "posicionamento" | "categoria" |
| "segmento de X" | "tipo de X" |
| "proposta de valor" | drop sempre |

### Health absolutes YMYL banidos (Google penaliza páginas afiliadas)

- "uso regular é seguro" → "tolerado pela maioria; consulte profissional se tem comorbidade"
- "alternativa segura" → "alternativa mais leve"
- "não causa dano" → "sem evidência de impacto em pessoas saudáveis em doses recomendadas"
- "sem efeitos colaterais" → "efeitos colaterais raros quando reportados"
- "cientificamente comprovado" / "100% seguro" / "sem riscos" → qualificar

### Voz-eximir-responsabilidade (não use fabricante como muleta)

- "X mg declarados" parentético → drop "declarados" (info do mg já é declarada por definição)
- "declarado pelo fabricante" → drop sempre
- "todos/todas/doses declaradas pelo fabricante" → "fórmula totalmente transparente" ou drop
- Alérgeno "contém X declarado pelo fabricante" → "contém X" direto
- **Spec de fabricante = fato, afirme direto** (régua v1.21.1): rendimento, economia e velocidade da ficha (ex: "rende até 4.500 páginas") vão SEM "segundo a Epson"/"segundo o fabricante" (atribuir a cada spec vira muleta repetitiva, igual "declarado pelo fabricante"). Atribuição só vale pra recomendação/calibração do fabricante (ex: "a HP recomenda 50 a 100 páginas/mês").
## Sincronização painel ↔ skill ↔ prompt canônico

```
docs/painel/_data/agent-prompts.json:category_description  (SOURCE OF TRUTH editorial)
    ├── handler do painel (POST /agent/category-desc/:site/:slug/create)
    └── esta SKILL.md (versão local executável)
```

Helpers do painel pra leitura/escrita da entry:
- `docs/painel/_lib/category-desc.ts:parseCategoryDescriptions(configTs)` — parsa o bloco
- `docs/painel/_lib/category-desc.ts:writeCategoryDescription(configTs, slug, html)` — substitui/adiciona entry preservando o resto

Skill local não importa esses helpers; a lógica equivalente está documentada no passo 11 do fluxo (Edit tool com caso A/B1/B2).

Quando Marcelo edita régua editorial (via `agent-config.html` no painel), atualiza `agent-prompts.json` canônico. Esta SKILL.md pode ficar atrasada — atualizar manualmente quando notar drift.

## Quando NÃO usar essa skill

- **Categoria sem artigos** E **sem entry no config**: skill aborta. Cria categoria adicionando artigos primeiro.
- **Categoria travada** (`<!-- contentLocked: true -->` no início do HTML atual): o painel rejeita save em HTTP 423 (`category-desc.ts:250-254`). Skill grava direto via Edit tool (não passa pelo painel) — funciona, mas pergunta antes (há razão pra trava).
- **Quer reescrita iterativa rápida**: skill custa ~$0.01-0.03 cada chamada. Mais barato dos prompts, mas ainda não é zero — não rodar 5x sequencialmente sem ler o output anterior.

## Armadilhas recorrentes

### 1. Tags de bloco proibidas por hábito
LLMs frequentemente abrem com `<h2>` ou usam `<ul>` pra listar critérios. PROIBIDO. Use só `<p>` como bloco; destacar com `<strong>` inline.

### 2. Backtick `` ` `` no HTML
Se o conteúdo cita um termo entre backticks ou um exemplo de código, NÃO USE backtick literal. Reescreva com aspas ou itálico.

### 3. `${variavel}` literal no HTML
Frase tipo "combina com ${produto}" → ${...} vira interpolação JS no template literal do config.ts. Detecta antes de salvar; reescrever sem `${`.

### 4. Listar com `<ul>` por hábito
"Cobrimos: <ul><li>X</li><li>Y</li></ul>" → quebra a régua. Reescreva como "Cobrimos X, Y e Z" com `<strong>` nos termos.

### 5. Edit tool com `old_string` ambíguo
Se 2 entries têm HTML quase idêntico (raro mas possível em sites com nichos próximos), incluir 1-2 linhas de contexto antes/depois pra forçar match único. Ex: incluir a linha `categoryDescriptions: {` ou a linha da entry anterior.

### 6. Esquecer indent canônico (4 espaços)
A entry deve ter 4 espaços antes da chave (`    'slug': \`html\`,`). Sem indent ou com indent errado quebra a estética + futuro diff/audit.

### 7. Mencionar marca específica
"Cobrimos creatinas da Growth, Max Titanium e Integralmédica." → NÃO. Generaliza: "Cobrimos as principais marcas brasileiras de creatina." Marcas vão nos artigos.

### 8. Mencionar Amazon como entidade
"Os melhores produtos da Amazon" → quebra a voz analítica. Omitir referência a Amazon na descrição de categoria.

### 9. Não incluir vírgula no fim da entry
Convenção do projeto: cada entry termina com vírgula. `'X': \`Y\`,` ✓ vs `'X': \`Y\`` ❌. Sem vírgula, próximas inserções confundem.

### 10. HTML muito curto (< 100 chars)
Schema do painel rejeita < 30 chars na sanitização, mas o canônico exige 100-2000 chars. Categoria com 1 frase só fica fraca editorialmente.

## Exemplo de invocação

Exemplos válidos do user — modo padrão:
- "escreve a descrição da categoria impressoras do escritoriocasa"
- "categoria impressoras do escritoriocasa"
- "https://painel.melhorserum.com.br/editor-categoria.html?site=escritoriocasa&slug=impressoras" (com hint "descrição")

Exemplos com instrução inline:
- "escreve a descrição da categoria impressoras mais conciso"
- "categoria creatinas enfatizando custo-benefício"
- "escreve a descrição de cadeiras com foco em home office"

Args canônico que invoco: `Skill(skill="categoria-descricao-escrever", args="escritoriocasa/impressoras")` (instrução vai pelo contexto do prompt natural)

## Limitação intrínseca conhecida

Sem schema Zod programático no output, validação fica editorial. ~3% de chance de algum campo ficar levemente fora do limite editorial (HTML em 2050 chars, 4 parágrafos em vez de 3, alguma tag inline rara). Mitigação principal: validar mentalmente a tag list e os caracteres proibidos (`` ` `` e `${`) antes de aplicar.
