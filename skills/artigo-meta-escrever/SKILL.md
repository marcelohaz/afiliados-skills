---
name: artigo-meta-escrever
description: Escreve a meta description SEO de um artigo (campo `description` no frontmatter do .mdx). Aceita URL do painel (editor-artigo.html?site=X&slug=Y) OU args canônicos site/slug. 50-160 chars, single-line, sem travessão, sem aspas internas. Substitui só a linha `description: "..."` do frontmatter — todo o resto fica intacto. Backup + commit + push + sync VPS.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida — fluxo natural depois de abrir o editor do artigo):
- `https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio`
- Extrai `site` e `slug` do query string

**B) Args canônicos**:
- `melhorimpressora/melhor-impressora-custo-beneficio`

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B (split por `/`).

# Escrever meta description do artigo

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:rewrite_meta_description`. O conteúdo essencial está duplicado abaixo pra autocontenção. **Esta SKILL.md é a fonte viva** desta execução (o `agent-prompts.json` é o espelho do path do painel/API e pode defasar — o projeto roda via Claude Code).

Você é o curador editorial da meta description SEO. Sua função é **escrever uma meta description otimizada pra Google** (a tag `<meta name="description">` que aparece no snippet da busca), seguindo as regras de tamanho, voz e formato.

A meta description aparece no Google bem perto do `<title>` (H1). Ela influencia CTR (clique). Não precisa ser literária — precisa ser **clara, factual, com keyword nos primeiros 60 chars**, vendendo o ângulo do artigo sem prometer demais.

## Pré-requisitos

O `.mdx` do artigo já existe em `sites/{site}/src/content/reviews/{slug}.mdx` com campo `description` no frontmatter (mesmo que vazio ou com texto antigo). Se o campo não existir no frontmatter, abortar e orientar criar manualmente primeiro (não vou inventar campo que não existe).

## Invariantes

- **Nunca toque em nenhum outro campo do .mdx.** Só a linha `description: "..."` do frontmatter. Title, listHeading, intro, products, guideContent — tudo intacto.
- **50 a 160 chars.** Google trunca em ~155 chars, toleramos até 160 antes de cortar. Abaixo de 50 chars é texto preguiçoso. Hard limit.
- **1 sentença completa** — sem reticências, sem cortes meio do pensamento.
- **Keyword principal nos primeiros 60 chars.** Extrai do `title` (H1) ou do campo `keyword` se existir no frontmatter. Ex: title "Melhor Impressora Custo Benefício:" → keyword "melhor impressora custo benefício" → primeiros 60 chars da description devem incluir isso.
- **Linguagem direta, factual.** Sem superlativos sem evidência ("a melhor opção", "incomparável", "imbatível").
- **Sem travessão (—).** Use vírgula ou ponto.
- **Sem ponto-e-vírgula (;).** (régua 2026-06-20) Tem cara de IA na voz conversacional. Troque por "." (sentença nova), "," (pausa) ou "()". Vale em TODOS os campos. AUTO-CHECK antes de gravar: depois de remover entidades (&amp;, &#..;) e a querystring dos links de afiliado, não pode sobrar ";" no texto.
- **Sem aspas duplas internas.** Vai pra YAML single-line entre `"..."` — aspa dupla interna quebra o parse. Use aspas simples ou parafraseie.
- **Single line.** Sem `\n`. Frontmatter `description:` é single-line por convenção do repo.
- **Português brasileiro editorial.** Sem gírias, sem anglicismos desnecessários.
- **Divergir dos IRMÃOS (anti-dup SERP, 2026-06-13).** O mesmo artigo existe em vários sites da rede (SERP-monopoly) e o snippet aparece junto do `<title>` na busca. Antes de gravar, **leia a `description` dos artigos irmãos** (mesmo slug/keyword): `Grep -n "^description:" sites/*/src/content/reviews/{slug}.mdx`. A sua meta deve ter **ângulo/redação distinta** das irmãs (não copiar a frase) — mantém a keyword nos 1ºs 60 chars, mas varia o gancho (ex.: uma foca preço, outra custo-benefício, outra perfil de uso). Irmão `contentLocked` mantém a dele → você diverge. Pareia com a divergência de título da `artigo-intro-escrever` (título sozinho não fecha a SERP).

## Fluxo

1. **Parse args**: detecta URL vs canônico, extrai `site` e `slug`. Valida `site` em `slug` em `[a-z0-9-]+`. Se ambíguo, perguntar.

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   git stash push -m "skill-artigo-meta-escrever-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Painel VPS commita+pusha automaticamente quando user cria/edita conteúdo na UI; Mac local pode estar 5-30s atrás. Sem este pull, skill pode ler estado stale e abortar com falso "X não existe localmente". Se pull falhar (rede offline, conflito), seguir mesmo assim.

2. **Read `.mdx`**: `Read sites/{site}/src/content/reviews/{slug}.mdx`. Se 404, abortar com mensagem clara apontando o painel pra criar artigo primeiro.

3. **Parse frontmatter** mentalmente:
   - `title` — texto do H1 (obrigatório)
   - `description` — atual (pode estar vazia ou populada)
   - `keyword` — opcional; se ausente, derive de `title.split(':')[0].toLowerCase().trim()`
   - `products[]` — extrair nomes e ASINs pra contexto

4. **Extrair snippet da intro** (~600 chars do body após o `---` de fechamento):
   - Pega o body markdown
   - Strip de componentes MDX (linhas começando com `<` ou `{`)
   - Strip de headings (`^#{1,6}\s+`)
   - Strip de emphasis (`**`, `*`)
   - Normaliza whitespace
   - Trunca a 600 chars
   - Se body estiver com o placeholder `[a escrever: ...]`, considerar intro vazia (snippet = "")

5. **Validar `description` é editável**: se a linha `description: "..."` não existe no frontmatter, abortar com:
   > "Campo `description` ausente no frontmatter de {slug}.mdx. Adicione manualmente uma linha `description: \"\"` no frontmatter antes de rodar a skill."

6. **Detectar instrução opcional no prompt original do user** (não perguntar — paridade com outras skills):
   - Se a invocação foi inline tipo "escreve a meta description do X mais conciso" ou "... com foco em preço" → eu extraio "mais conciso" / "com foco em preço" como `instruction` e uso no prompt.
   - Se foi só "escreve a meta description do X" ou `/artigo-meta-escrever <URL>` → modo padrão sem instrução.
   - Em caso de dúvida ("isso é parte do slug ou é instrução?"), trata como sem instrução e gera no padrão. User pode re-invocar com instrução mais clara se não gostar.

7. **Gerar a nova description** seguindo as regras editoriais (ver seção "Régua de geração" abaixo). Use o contexto coletado: title, description atual (referência do que mudar), lista de produtos, snippet do intro, instrução opcional (se detectada no passo 6).

8. **Validar mentalmente** antes de salvar:
   - Tamanho dentro de 50-160 chars
   - Sem travessão `—` nem `–`
   - Sem aspa dupla interna `"` (escapa pra `\"` ou parafraseia)
   - Sem `\n` ou quebras de linha
   - Keyword aparece nos primeiros 60 chars
   - 1 sentença completa terminando em `.`

9. **Backup** ANTES de sobrescrever (paridade com pattern do painel):
   ```bash
   DAY=$(date +%Y-%m-%d); TIME=$(date +%H%M%S); SITE={site}; SLUG={slug}
   mkdir -p "docs/painel/.painel-backups/$DAY"
   cp "sites/$SITE/src/content/reviews/$SLUG.mdx" \
      "docs/painel/.painel-backups/$DAY/article-${SITE}-${SLUG}-${TIME}-metadesc.mdx"
   ```

10. **Aplicar via Edit tool**: substitui SÓ a linha `description: "..."` no frontmatter. Usa `old_string` = linha completa atual (com aspas internas escapadas se houver), `new_string` = linha completa nova.

    Padrão do frontmatter (sempre double-quoted single-line):
    ```yaml
    description: "Texto atual aqui."
    ```

    Cuidado: a linha do `description` no FRONTMATTER (entre os dois `---` do topo). Se houver outro `description:` no body por coincidência (raríssimo), garantir que o `old_string` é único o suficiente pra Edit tool não confundir. Em caso de dúvida, incluir contexto antes/depois (ex: linha do `title:` antes + linha em branco depois).

11. **Git add + commit + push** (do diretório raiz):
    ```bash
    git add sites/{site}/src/content/reviews/{slug}.mdx
    git commit --no-verify -m "feat({site}): meta description de {slug} escrita via skill" \
      -m "Co-Authored-By: {modelo da sessão} <noreply@anthropic.com>"
    git push origin main
    ```
    `--no-verify` é OBRIGATÓRIO: o pre-commit hook roda `audit-article.ts` no artigo staged e bloqueia se houver erros (ex.: productCount < 3, intro/guide pendentes em outro fluxo).

12. **Disparar git pull no painel da VPS**:
    ```bash
    bash scripts/painel-vps-pull.sh
    ```
    Script usa Basic Auth do painel (creds em `.env.painel-skills`). Falha graciosamente se `.env.painel-skills` não existir — commit+push já aconteceram, painel da VPS fica desatualizado até alguém clicar "Atualizar painel".

13. **Reportar no chat**: char count + description atual vs nova (preview do antes/depois) + path do arquivo.

## Régua de geração

Segue o template canônico (`rewrite_meta_description`):

```
## Tarefa
Reescreva a META DESCRIPTION (tag SEO que aparece na busca do Google) do artigo abaixo.

## Convenções
- 50 a 160 caracteres (Google trunca em ~155, toleramos 160)
- 1 a 2 sentenças completas, sem reticências nem cortes (pergunta + resposta funciona bem para CTR)
- BENEFÍCIO-FIRST, não ficha técnica: vende o ganho do leitor, não uma lista de specs (ver régua abaixo)
- Mencionar a keyword principal do title nos primeiros 60 chars
- Linguagem direta, factual; sem superlativos sem evidência
- Sem travessão (—); use vírgula ou ponto
- Sem aspas duplas internas (vai pra YAML single-line)
- Single line, sem quebras (\n)
```

### Benefício-first, NÃO ficha técnica (régua v1.20.0, canon 2026-06-03)

A meta vende o **GANHO do leitor** (o que ele economiza, resolve ou consegue), não a lista de critérios técnicos. O erro mais comum é virar **cabeçalho de planilha**: keyword + 3-4 specs encadeados por vírgula. Caso real (melhorimpressora, 2026-06-03): `"Melhor impressora tanque de tinta em 2026: comparativo com custo por página, rendimento por kit, velocidade ISO e frente e verso automático."` (4 specs em fila, zero gancho) — Marcelo flagou como "muito ficha técnica".

- ❌ **Ficha técnica (PROIBIDO)**: não encadeie 3 ou mais specs/critérios por vírgula ("custo por página, rendimento por kit, velocidade ISO e duplex").
- ✅ **Abra com 1**: a dúvida do leitor (pergunta), a dor (ex: cartucho caro), o objetivo (ex: imprimir muito gastando pouco) ou o resultado (ex: escolher sem erro).
- **No máximo 1-2 termos técnicos**, e sempre ancorados num benefício (`rende milhares de páginas` em vez de `rendimento por kit`).

**3 moldes que funcionam (varie entre eles):**

- Pergunta + resposta: `Qual a melhor {keyword} em {ano}? {benefício/ganho concreto}.`
- Dor → solução: `{Dor do leitor}? {Keyword}: {como resolve}.`
- Benefício + alcance: `As melhores {keywordPlural} de {ano} pra {objetivo}, de {X} a {Y}.`

Exemplos bons (benefício-first):

- ✓ `"Qual a melhor impressora tanque de tinta em 2026? Comparamos os modelos pra você imprimir muito gastando pouco com tinta, sem voltar ao cartucho."` (~146 chars)
- ✓ `"Cansou do cartucho caro? Veja as melhores impressoras de 2026 que rendem milhares de páginas com tinta barata, da básica à fotográfica."` (~134 chars)
- ✓ `"Qual a melhor creatina em 2026? Veja quais valem o preço pra ganho de força, com pureza Creapure e bom custo por dose."` (~116 chars)
- ✓ `"Tablet travando ou tela pequena? Os melhores tablets baratos de 2026 pra estudo, vídeo e leitura sem pesar no bolso."` (~114 chars)

Exemplos ruins:

- ❌ `"Melhor impressora tanque de tinta em 2026: comparativo com custo por página, rendimento por kit, velocidade ISO e frente e verso automático."` (ficha técnica: 4 specs encadeados, zero benefício)
- ❌ `"As melhores impressoras."` (24 chars, muito curto e vago)
- ❌ `"...com análise completa de tanque de tinta, velocidade ISO, rendimento por kit, conectividade Wi-Fi, capacidade de papel e duplex."` (passa de 160 + ficha técnica)
- ❌ `"Análise das melhores impressoras — a melhor seleção do mercado."` (travessão + superlativo)
- ❌ `"Análise das "melhores" impressoras..."` (aspa dupla interna)

## Voz editorial

- **Factual, não promocional**: não promete que o usuário vai encontrar a "perfeita". Promete análise/comparativo.
- **Verbos de análise**: "comparativo", "análise", "guia para escolher", "panorama das opções".
- **Concreto, mas não ficha técnica**: um benefício ou ganho concreto (economia, perfil, resultado) bate mais que "tudo o que você precisa saber". Não encadeie specs como lista.

## Tom conversacional (CRÍTICO)

Mesmo em 50-160 chars: pergunta-teste *"Um amigo entenderia?"*. Evite jargão corporativo (❌ "uma análise das melhores opções da categoria"). Linguagem direta (✓ "comparativo das X mais econômicas em 2026"). NÃO cite "Amazon", "fabricante", "ficha técnica" na meta.


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
## Armadilhas recorrentes

### 1. Aspa dupla interna
Bem fácil escapar usando aspa simples no lugar.
- ❌ `Análise das "melhores" impressoras` (quebra YAML)
- ✓ `Análise das melhores impressoras` (sem aspas)
- ✓ `Análise das 'melhores' impressoras` (aspa simples, se precisar)

### 2. Travessão por hábito
Travessão (`—` ou `–`) é proibido em todos os campos editoriais do projeto (regra `01-sem-travessao.md`). Vírgula faz o mesmo trabalho.

### 3. Keyword fora dos primeiros 60 chars
Se title é "Melhor Impressora Custo Benefício:", a description NÃO PODE começar com "Encontre opções..." — a keyword precisa entrar cedo pro Google rankear bem.

### 4. Cópia do title
Description = title é desperdício. Title já está no `<title>` da SERP. Description precisa AGREGAR informação (ângulo, critério, escopo).

### 5. Esquecer de substituir só a LINHA do description
Edit tool com `old_string` genérico tipo `description: ""` pode bater em outro lugar (raro mas possível). Inclua contexto suficiente pra unicidade — geralmente o texto da description atual já é único o bastante. Se atual estiver vazia (`description: ""`), incluir 1 linha de contexto antes (geralmente `title: "..."`).

### 6. Não reportar char count
O user precisa saber se ficou perto do limite (problemático em 155-160). Sempre reporta tamanho final.

## Quando NÃO usar essa skill

- **Artigo travado** (`contentLocked: true`): o servidor do painel recusaria save em /article/... endpoints (HTTP 423). Pra esta skill, o problema é o painel da VPS rejeitar o git pull resultante (não — git pull não passa pelo lock). Mas editorialmente: se o artigo está travado, há razão (SEO estável). Pergunta se realmente quer mudar antes de prosseguir.
- **Description já está perfeita**: rodar a skill 5x em 5 minutos não melhora muito (é determinístico-ish). Avalie primeiro com leitura humana.

## Sincronização painel ↔ skill ↔ prompt canônico

```
docs/painel/_data/agent-prompts.json:rewrite_meta_description  (SOURCE OF TRUTH editorial)
    ├── handler do painel (POST /agent/article/:site/:slug/rewrite-meta-description)
    └── esta SKILL.md (versão local executável)
```

Quando Marcelo edita régua editorial (via `agent-config.html` no painel), atualiza `agent-prompts.json` canônico. Esta SKILL.md pode ficar atrasada — atualizar manualmente quando notar drift.

## Exemplo de invocação

Exemplos válidos do user — modo padrão (sem instrução):
- "escreve a meta description do melhor-impressora-custo-beneficio do melhorimpressora"
- "meta description do artigo melhor-impressora-custo-beneficio"
- "https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio" (com hint "meta description")

Exemplos válidos com instrução inline:
- "escreve a meta description do melhor-impressora-custo-beneficio mais conciso"
- "meta description do melhor-impressora-custo-beneficio enfatizando preço"
- "escreve meta description do X mencionando que é guia 2026"

Args canônico que invoco: `Skill(skill="artigo-meta-escrever", args="melhorimpressora/melhor-impressora-custo-beneficio")` (instrução não vai pro args — ela vive no contexto do prompt natural do user)

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), a validação fica editorial — eu (modelo) sigo as regras. ~3% de chance de algum campo ficar levemente fora do limite editorial (ex: 162 chars em vez de 160). Mitigação: contar chars depois de gerar e ajustar antes de aplicar.
