---
name: artigo-analise-final
description: Análise final pré-lock de artigo (read-only). Combina checks estruturais determinísticos (intro existe, guide existe, ≥3 produtos, meta description preenchida) com auditoria IA cross-conteúdo (claim-vs-bíblia, tag, travessão, tone-clone, buyer-ref). Calcula readyToLock boolean — IA pode AFROUXAR (true→false), nunca APERTAR (false→true). Aceita URL do painel (editor-artigo.html?site=X&slug=Y) OU args canônicos site/slug. NÃO modifica nada — gera relatório em docs/biblias-v2/.audits/articles/{site}-{slug}-finalreview-last.md. Use antes de marcar contentLocked: true.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida — fluxo natural depois de abrir o editor):
- `https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio`
- Extrai `site` e `slug` do query string

**B) Args canônicos**:
- `melhorimpressora/melhor-impressora-custo-beneficio`

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B (split por `/`).

# Análise final do artigo (pré-lock)

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:final_review`. Conteúdo essencial duplicado abaixo pra autocontenção; em caso de divergência, o prompt canônico ganha.

Você é o **gatekeeper pré-lock** do artigo. O usuário roda essa skill quando achou que o artigo está pronto pra ser travado (`contentLocked: true`) — SEO estável, conteúdo finalizado. Sua função é:

1. **Rodar checks estruturais determinísticos** (não-IA) pra garantir que peças obrigatórias existem (intro, guide, ≥3 produtos, meta description).
2. **Rodar auditoria IA cross-conteúdo** nas 9 categorias do `regras_auditoria_artigo`.
3. **Calcular `readyToLock`** combinando IA + checks estruturais. Código pode VETAR (`false`), nunca FORÇAR (`true`).
4. **Gerar relatório markdown** em `docs/biblias-v2/.audits/articles/` (padrão paralelo às outras auditorias).

A skill é **read-only**: não toca no `.mdx`, não commita nada. Só relatório.

## Pré-requisitos

- O `.mdx` do artigo já existe em `sites/{site}/src/content/reviews/{slug}.mdx`.
- O artigo tem **pelo menos 1 produto** no lineup (`products: []` vazio = abortar — nada pra analisar).
- Bíblias dos produtos do artigo estão em `docs/biblias-v2/{ASIN}.json`. Se alguma faltar, rodar `bun scripts/sync-biblias-r2.ts --apply` antes (skill avisa e aborta se faltar).
- `affiliateTag` em `sites/{site}/src/config.ts` é conhecida (pode ser vazia em sites em construção — a regra de auditoria muda: tag vazia → links Amazon devem ser CRUS sem `?tag=`).

## Invariantes

- **NÃO MODIFICA NADA.** Skill é puramente read-only. Output é arquivo markdown de relatório. Nenhum commit, nenhum push, nenhum write no `.mdx`.
- **NÃO inventa findings.** Se não encontrou problema numa categoria, não fabrica. Audit vazio em categoria = legítimo.
- **Toda issue precisa de evidência.** Cite trecho literal do `.mdx` (blockquote curto < 15 palavras) OU da bíblia.
- **Código manda no readyToLock.** Override determinístico: IA pode dizer `true`, mas se estruturalmente falta peça obrigatória, readyToLock final é `false`. IA só pode AFROUXAR a decisão, nunca APERTAR.
- **Português brasileiro editorial.** Tom analítico, factual.

## Fluxo

1. **Parse args**: detecta URL vs canônico, extrai `site` e `slug`. Valida `[a-z0-9-]+` em ambos.

2. **Read `.mdx`**: `Read sites/{site}/src/content/reviews/{slug}.mdx`. Se 404, abortar.

3. **Parse frontmatter** mentalmente:
   - `title` (H1)
   - `description` (meta description — vou checar se é placeholder)
   - `keyword` / `keywordPlural`
   - `products: []` — extrair ASINs + count
   - `contentLocked` — se já é `true`, **avisar mas não bloquear** (user pode querer reauditar mesmo travado)
   - `guideContent` (block scalar) — preciso extrair pra check estrutural

4. **Read bíblias** dos produtos. Se alguma faltar, abortar com instrução pra rodar sync R2.

5. **Read `affiliateTag`**: `sites/{site}/src/config.ts` via regex. Define a regra de validação dos links Amazon.

6. **Listar peer articles** (apenas pra contexto de tom-clone — não pra linkagem). Não é estritamente necessário, mas ajuda a IA a entender se este artigo tem voz coerente com os irmãos.

7. **Rodar checks estruturais determinísticos** (não-IA, código mental):

   ### a) `hasIntro`
   Body markdown do `.mdx` (tudo após o segundo `---` do frontmatter).
   - Calcular `totalBodyChars` (count de chars do body, ignorando frontmatter)
   - Quebrar body em "segmentos" (linhas separadas por blank lines)
   - Detectar placeholder: `bodySegments.length <= 2` **AND** algum segmento inclui `[a escrever` OU `— agente IA preenche` (AND, não OR — paridade com `agent-edit.ts:1917-1918`)
   - `hasIntro = totalBodyChars > 200 && !isPlaceholder`

   ### b) `hasGuide`
   - Extrair `guideContent` do frontmatter (block scalar `|` ou inline vazio)
   - `hasGuide = guideContent.exists && guideContent.trim().length > 100`

   ### c) `productCount`
   - `parsed.products.length` (quantos itens no array `products[]`)

   ### d) `hasMetaDescription`
   - `description` é placeholder se inclui `[descrição a definir` (texto que `agentMakeReviews` seta na criação do stub)
   - `hasMetaDescription = description.length >= 50 && !isPlaceholder`

8. **Rodar auditoria IA** nas 9 categorias (seção "Critérios de auditoria" abaixo). Gerar:
   - `issues`: array de `{level, rule, message, product?, fix?, evidence?}`
   - `summary`: 1-3 frases sobre estado geral
   - `passed`: bullets MUITO curtos (10-30 palavras) do que passou bem
   - `readyToLock` (estimativa IA): true/false
   - `lockReasoning` (justificativa IA): 1-2 frases

9. **Calcular `readyToLock` FINAL** com override determinístico:
   ```
   structuralOk = hasIntro && hasGuide && productCount >= 3 && hasMetaDescription
   errorIssueCount = issues.filter(i => i.level === 'error').length
   errorsOk = errorIssueCount === 0
   codeReadyToLock = structuralOk && errorsOk
   readyToLock = (estimativa_IA) && codeReadyToLock
   ```

   **Importante**: se IA aprovou (`true`) mas código vetou (`codeReadyToLock = false`), eu **reescrevo o `lockReasoning`** listando os blockers estruturais. Mensagens adaptadas pra fluxo de skill local (vs UI do painel):
   - "introdução vazia ou placeholder (execute /artigo-intro-escrever)"
   - "guide ausente — campo guideContent vazio no frontmatter (execute /artigo-guia-escrever)"
   - "apenas N produto(s) (mínimo 3) — adicione mais produtos via painel + execute /artigo-review-criar"
   - "meta description ainda é placeholder (execute /artigo-meta-escrever)"
   - "N issue(s) crítico(s) — veja seção 🔴 do relatório pra detalhe"

10. **Detectar meta description placeholder específico**: se `description` inclui `[descrição a definir`, **prepend** um issue crítico no início do array. Paridade com `detectMetaDescPlaceholder` do painel (agent-edit.ts:1221-1235):
    ```js
    {
      level: 'error',
      rule: 'meta-description-placeholder',
      message: 'Meta description ainda é placeholder. Não pode ser publicado assim — Google indexaria o snippet placeholder.',
      fix: 'Execute /artigo-meta-escrever pra gerar uma meta description real antes de travar.'
    }
    ```
    A `message` preserva a justificativa SEO; o `fix` aponta pra skill local (vs UI do painel).

11. **Escrever relatório** em 2 locais (paridade com pattern de bíblias/produtos):
    ```
    docs/biblias-v2/.audits/articles/{site}-{slug}-finalreview-{YYYY-MM-DD-HHMM}.md  ← snapshot timestamped
    docs/biblias-v2/.audits/articles/{site}-{slug}-finalreview-last.md               ← caminho fixo, painel lê esse
    ```
    Criar `docs/biblias-v2/.audits/articles/` se não existir. Conteúdo do relatório: ver seção "Formato do relatório" abaixo.

12. **Reportar no chat**: linha curta com:
    - `readyToLock: true/false`
    - `lockReasoning`
    - count de issues por nível
    - path do relatório

## Critérios de auditoria (9 categorias do `regras_auditoria_artigo`)

Use exatamente esses valores em `rule`:

### `claim-vs-bible` (level=`error`)
Afirmação no review (subtitle, shortDescription, fullReview, pros, cons, specs) que NÃO tem origem rastreável na bíblia. Spec inventada, número errado, feature não confirmada. Inclui `evidence` com citação literal.

**Exemplo**: review diz "5.000 páginas por kit" mas bíblia diz "4.500 páginas".

### `tag-affiliate` (level=`error`)
Link Amazon com tag diferente da esperada.
- Tag preenchida no config: links DEVEM ter `?tag={tag}&linkCode=ogi&th=1&psc=1`
- Tag vazia: links DEVEM ser crus (sem `?tag=...`)

**Exemplo**: config tem `melhorimpressora-20` mas review tem `https://amazon.com.br/dp/X?tag=outratag-20`.

### `travessao` (level=`warn`)
Travessão (`—` ou `–`) detectado em qualquer campo editorial: title, description, subtitle, shortDescription, fullReview, pros, cons, intro (body markdown), guideContent.

### `superlativo-sem-evidencia` (level=`warn`)
Absolutos sem evidência: "o melhor disponível", "o mais X", "incomparável", "único", "imbatível".

**Não flag**: qualificadores positivos simples ("excelente", "ótimo", "muito bom") — review afiliado é levemente inclinado ao positivo por design.

### `atribuicao-comprador` (level=`warn`)
Usa "compradores" (plural) sem ter múltiplas opiniões na bíblia; OU cita "1 comprador" como se fosse consenso. Voz analítica é o padrão — citações explícitas de comprador/Amazon/reviews devem ser reescritas.

### `tone-clone` (level=`info`)
Produtos com voz/estrutura idêntica. Aberturas todas começando igual ("A {X} é para quem..."), mesma fórmula, mesmo número de frases por bloco. **Não flag** se o pattern é o template editorial canônico (`Para quem é:` / `Por que gostamos:` / `Pontos de atenção:` / `Resumo:`) — isso é INTENCIONAL.

### `spec-ausente` (level=`info`)
Produto sem campo de spec que outros do artigo têm (incompletude). Ex: 3 produtos com "Conectividade: Wi-Fi" no specs e 1 sem.

### `dado-inconsistente-ignorado` (level=`warn`)
Bíblia tem `dadosInconsistentes` com `decisaoEditorial`; review não respeita a decisão.

**Exemplo**: bíblia tem flag "ppm-divergente" com decisão "usar 10ppm da ficha técnica, ignorar bullet de 12ppm" — mas review diz "12 ppm".

### `decisao-editorial-violada` (level=`warn`)
Review contradiz `decisaoEditorial` registrada na bíblia (caso geral).

## Critérios estruturais (determinísticos, não-IA)

Estes 4 checks são feitos **em código mental** antes da auditoria IA. Resultado entra no relatório como bloco `Structural` e influencia o `readyToLock` final.

| Check | Critério | Bloqueia lock? |
|---|---|---|
| `hasIntro` | body chars > 200 + sem placeholder `[a escrever:` ou `— agente IA preenche` | Sim |
| `hasGuide` | `guideContent` no frontmatter, trim > 100 chars | Sim |
| `productCount >= 3` | array `products[]` tem ≥3 items | Sim |
| `hasMetaDescription` | `description` >= 50 chars + sem placeholder `[descrição a definir` | Sim |

Se QUALQUER um falha, `codeReadyToLock = false` → `readyToLock = false`.

## Override determinístico do readyToLock

A lógica final é:

```
readyToLock = (IA disse true) AND (todos os 4 checks estruturais OK) AND (zero issues level=error)
```

Cenários possíveis:

| IA | Estrutural OK | Errors=0 | `readyToLock` final | Quem decidiu |
|---|---|---|---|---|
| true | true | true | **true** | Consenso ✓ |
| true | false | * | **false** | Código vetou (override) |
| true | true | false | **false** | Código vetou (override) |
| false | * | * | **false** | IA recusou |

**Regra**: IA NUNCA pode forçar `true` se código vetou. Se IA disse `true` mas código vetou, eu **reescrevo o `lockReasoning`** explicando os blockers (não mantenho o lockReasoning da IA, que estaria errado).

## Formato do relatório

Template do markdown a salvar em `.audits/articles/{site}-{slug}-{date}.md`:

```markdown
# Análise final: {site}/{slug}

- **Data:** {YYYY-MM-DD HH:MM}
- **readyToLock:** {true|false}
- **lockReasoning:** {1-2 frases}

## Structural checks

| Check | Status | Valor |
|---|---|---|
| Introdução escrita | {✓|✗} | {chars do body} chars |
| Guide presente | {✓|✗} | {chars do guideContent} chars |
| ≥3 produtos | {✓|✗} | {productCount} produtos |
| Meta description | {✓|✗} | {chars da description} chars |

## Summary IA

{1-3 frases sobre o estado geral}

## 🔴 Errors ({N})

{lista com format abaixo, ou "Nenhum" se vazio}

### {rule}: {message}
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

Também salvar versão `.audits/articles/{site}-{slug}-finalreview-last.md` (mesmo conteúdo) — o painel lê esse path fixo pra mostrar UI.

## Voz analítica (CRÍTICO)

Igual a todas as auditorias do projeto:

- **Tom analítico.** "O review do produto 2 cita 5.000 páginas; bíblia confirma 4.500."
- **NÃO comente preferências.** "Acho que ficaria melhor com Y" → "Y pode ser uma alternativa que cita {dado da bíblia}".
- **Cite evidência.** Cada issue com `evidence` (do `.mdx`) ou referência a campo da bíblia. Sem evidência, descarta.

## Quando NÃO usar essa skill

- **Artigo vazio** (`products: []` vazio): nada pra analisar. Aborta orientando completar lineup primeiro.
- **Falta de bíblia** de produtos: rodar `bun scripts/sync-biblias-r2.ts --apply` primeiro. Sem bíblias, a auditoria de `claim-vs-bible` é inútil (não consegue cruzar).
- **Artigo já travado** (`contentLocked: true`): avisa que já está travado, mas roda análise mesmo (útil pra reauditar pós-trava).

## Cooldown / dedup

O painel tem cooldown de 30s por artigo (server.ts:3204). A skill local não tem cooldown automático — rodar 2x em sequência custa $0.06-0.10 cada. Recomendo rodar só quando achar que está pronto, não preventivamente.

## Sincronização painel ↔ skill ↔ prompt canônico

```
docs/painel/_data/agent-prompts.json:final_review  (SOURCE OF TRUTH editorial)
    ├── handler do painel (POST /agent/article/:site/:slug/final-review)
    └── esta SKILL.md (versão local executável)
```

A lógica de override determinístico do `readyToLock` está em `_lib/agent-edit.ts:1986-2004`. Esta SKILL.md replica essa lógica mentalmente (passo 9 do fluxo).

Quando Marcelo edita régua editorial (via `agent-config.html` no painel), atualiza `agent-prompts.json` canônico. Esta SKILL.md pode ficar atrasada — atualizar manualmente quando notar drift.

## Armadilhas recorrentes

### 1. Tentar editar o `.mdx`
Skill é PURAMENTE read-only. Mesmo que veja problema fácil de consertar, NÃO edita. O user roda skills específicas (`artigo-intro-escrever`, `artigo-review-criar`, etc.) pra corrigir.

### 2. IA forçar readyToLock=true sem checks estruturais
Override determinístico no passo 9 cobre isso. Se IA disse `true` mas falta intro ou guide, reescrevo `lockReasoning` listando blockers e força `readyToLock = false`.

### 3. Esquecer de detectar meta description placeholder
`description: "[descrição a definir]"` é placeholder do `make-reviews-stub`. Não bloquearia structural check direto (>= 50 chars), mas é placeholder VISUAL — vai pro Google como meta. **Prepend** issue crítico `meta-description-placeholder` no array de issues.

### 4. Citar comprador no audit
"Compradores reclamam de X" → quebra a voz analítica. Sempre reescreva: "Bíblia registra trade-off X (campo Y)".

### 5. Não criar diretório `.audits/articles/`
Primeiro run do skill no projeto, o diretório não existe. Sempre fazer `mkdir -p docs/biblias-v2/.audits/articles/` antes de escrever.

### 6. Sobrescrever `-last.md` com data errada
O snapshot timestamped E o `-last.md` recebem o MESMO conteúdo, gerado uma vez. Não calcular 2 timestamps diferentes.

### 7. Achar tone-clone onde é template intencional
A estrutura dos 4 parágrafos com prefixos exatos (`Para quem é:` / `Por que gostamos:` / `Pontos de atenção:` / `Resumo:`) é o template canônico — **não é tone-clone**. Só flag tone-clone se houver frase concreta repetida em 2+ reviews ou parágrafo quase idêntico com nome trocado.

### 8. Tag vazia esperando link com tag
Site em construção tem `affiliateTag: ''`. Nesse caso, links Amazon devem ser CRUS (`https://amazon.com.br/dp/X`). Se a IA assume tag preenchida e flagga "tag-affiliate", está errado. Sempre cruzar com o config real.

### 9. Confundir com `artigo-reviews-auditar`
Skill `artigo-reviews-auditar` é WRITE op cross-produto (sugere mudanças, user aprova granular). Esta skill (`artigo-analise-final`) é READ-only e cobre TODO o artigo (intro, guide, reviews, frontmatter, meta) + decide se está pronto pra travar. Escopos diferentes.

### 10. Não considerar `contentLocked` no input
Se artigo já é `contentLocked: true`, a skill ainda roda (útil pra reauditar pós-trava), mas o relatório deve mencionar no header. UI do painel oferece "Destravar" se houver issue crítica achada.

## Exemplo de invocação

Exemplos válidos do user — modo padrão:
- "análise final do artigo melhor-impressora-custo-beneficio do melhorimpressora"
- "audita pra travar o melhor-impressora-custo-beneficio"
- "https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio" (com hint "análise final" ou "pré-lock")

Args canônico que invoco: `Skill(skill="artigo-analise-final", args="melhorimpressora/melhor-impressora-custo-beneficio")`

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), validação fica editorial. ~5% de chance de algum issue ter `evidence` levemente fora do limite (ex: 17 palavras em vez de 15) ou estrutura do markdown levemente quebrada. Mitigação: conferir mentalmente antes de salvar o `.md`. Em caso de dúvida, optar por menos categorias e mais evidência.

A única validação **automatizável** é o override determinístico do `readyToLock`, que é a parte mais crítica.
