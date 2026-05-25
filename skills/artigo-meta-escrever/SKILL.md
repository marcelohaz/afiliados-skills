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

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:rewrite_meta_description`. O conteúdo essencial está duplicado abaixo pra autocontenção; em caso de divergência, o prompt canônico ganha.

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
- **Sem aspas duplas internas.** Vai pra YAML single-line entre `"..."` — aspa dupla interna quebra o parse. Use aspas simples ou parafraseie.
- **Single line.** Sem `\n`. Frontmatter `description:` é single-line por convenção do repo.
- **Português brasileiro editorial.** Sem gírias, sem anglicismos desnecessários.

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
    git commit -m "feat({site}): meta description de {slug} escrita via skill" \
      -m "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
    git push origin main
    ```

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
- 1 sentença completa, sem reticências, sem cortes
- Mencionar a keyword principal do title nos primeiros 60 chars
- Linguagem direta, factual; sem superlativos sem evidência
- Sem travessão (—); use vírgula ou ponto
- Sem aspas duplas internas (vai pra YAML single-line)
- Single line, sem quebras (\n)
```

**Estrutura típica que funciona** (não obrigatória, só pattern):

`{Keyword principal} para {perfil de uso}, com {ângulo concreto 1}, {ângulo concreto 2} e {ângulo concreto 3}.`

Exemplos bons:

- ✓ `"Análise das impressoras com melhor custo-benefício para uso doméstico e home office, com foco em tanque de tinta, velocidade ISO e rendimento por kit."` (155 chars)
- ✓ `"Comparativo das melhores creatinas em 2026, com análise de pureza Creapure, custo por dose e tempo de dissolução."` (113 chars)
- ✓ `"Guia para escolher tablet barato em 2026: tela, processador, RAM e bateria comparados em 8 modelos populares na Amazon."` (118 chars)

Exemplos ruins:

- ❌ `"As melhores impressoras."` (24 chars — muito curto)
- ❌ `"As melhores impressoras de custo benefício do mercado brasileiro em 2026, com análise completa de tanque de tinta, velocidade ISO, rendimento por kit, conectividade Wi-Fi, capacidade de papel e duplex."` (200 chars — passa do limite)
- ❌ `"Análise das melhores impressoras — a melhor seleção do mercado."` (tem travessão + superlativo sem evidência)
- ❌ `"Análise das "melhores" impressoras..."` (aspa dupla interna)

## Voz editorial

- **Factual, não promocional**: não promete que o usuário vai encontrar a "perfeita". Promete análise/comparativo.
- **Verbos de análise**: "comparativo", "análise", "guia para escolher", "panorama das opções".
- **Concreto, não vago**: dois ou três ângulos específicos (specs, perfis, critérios) batem mais que "tudo o que você precisa saber".

## Tom conversacional (CRÍTICO)

Mesmo em 50-160 chars: pergunta-teste *"Um amigo entenderia?"*. Evite jargão corporativo (❌ "uma análise das melhores opções da categoria"). Linguagem direta (✓ "comparativo das X mais econômicas em 2026"). NÃO cite "Amazon", "fabricante", "ficha técnica" na meta.

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
