---
name: artigo-auditar
description: Audita artigo inteiro read-only — cruza claims de intro/guide/reviews/frontmatter com bíblias dos produtos + PADROES + tag de afiliado. 9 categorias (claim-vs-bible, tag-affiliate, travessao, superlativo, atribuicao-comprador, tone-clone, spec-ausente, dado-inconsistente, decisao-editorial). NÃO modifica nada — gera relatório em docs/biblias-v2/.audits/articles/{site}-{slug}-audit-last.md. Sem decisão de lock (use artigo-analise-final pra isso). Aceita URL do painel OU args canônicos site/slug.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida):
- `https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio`
- Extrai `site` e `slug` do query string

**B) Args canônicos**:
- `melhorimpressora/melhor-impressora-custo-beneficio`

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B (split por `/`).

# Auditar artigo (read-only)

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:audit_article`. Conteúdo essencial duplicado abaixo pra autocontenção; em caso de divergência, o prompt canônico ganha.

Você é o auditor read-only do artigo. O usuário passa `{site}/{slug}` e quer **descobrir problemas** sem precisar de decisão de lock. Sua função é cruzar cada claim do artigo contra a bíblia do produto correspondente + PADROES + tag de afiliado, e reportar findings estruturados.

A skill é **read-only**: não toca no `.mdx`, não commita nada. Só relatório.

## Diferenças vs skills irmãs

| Skill | Escopo | Modifica? | Decide lock? |
|---|---|---|---|
| `artigo-reviews-auditar` | Só reviews (cross-produto, write op) | **Sim** (sugere diffs, user aprova) | Não |
| `artigo-analise-final` | Artigo todo + checks estruturais | Não | **Sim** (calcula `readyToLock`) |
| **`artigo-auditar`** | **Artigo todo, sem decisão de lock** | **Não** | **Não** |

Use **`artigo-auditar`** quando quer ver o estado do artigo num momento intermediário, sem ter que tomar decisão de fechar (lock). É o "audit puro" mais simples e barato.

Use **`artigo-analise-final`** quando achar que está pronto pra travar — vai rodar os mesmos checks editoriais + os 4 checks estruturais (intro/guide/produtos/meta) + calcular `readyToLock`.

## Pré-requisitos

- O `.mdx` do artigo já existe em `sites/{site}/src/content/reviews/{slug}.mdx`.
- O artigo tem **pelo menos 1 produto** no lineup (`products: []` vazio = abortar — nada pra auditar).
- Bíblias dos produtos do artigo estão em `docs/biblias-v2/{ASIN}.json`. Se alguma faltar, rodar `bun scripts/sync-biblias-r2.ts --apply` antes (skill avisa e aborta se faltar).
- `affiliateTag` em `sites/{site}/src/config.ts` é conhecida (pode ser vazia em sites em construção — a regra de auditoria muda: tag vazia → links Amazon devem ser CRUS sem `?tag=`).

## Invariantes

- **NÃO MODIFICA NADA.** Skill é puramente read-only. Output é arquivo markdown de relatório. Nenhum commit, nenhum push, nenhum write no `.mdx`.
- **NÃO inventa findings.** Se não encontrou problema numa categoria, não fabrica. Audit vazio em categoria = legítimo.
- **Toda issue precisa de evidência.** Cite trecho literal do `.mdx` (`evidence` ≤ 160 chars, idealmente < 15 palavras) OU da bíblia.
- **NÃO calcula readyToLock.** Esse é trabalho da `artigo-analise-final`. Aqui só report findings.
- **Português brasileiro editorial.** Tom analítico, factual.

## Fluxo

1. **Parse args**: detecta URL vs canônico, extrai `site` e `slug`. Valida `[a-z0-9-]+`.

2. **Read `.mdx`**: `Read sites/{site}/src/content/reviews/{slug}.mdx`. Se 404, abortar.

3. **Parse frontmatter** mentalmente:
   - `title` (H1)
   - `description` (meta description — vou checar placeholder)
   - `keyword` / `keywordPlural`
   - `products: []` — extrair ASINs + count
   - `guideContent` (block scalar) — pra auditar como parte do artigo

4. **Read bíblias** dos produtos. Se alguma faltar, abortar com instrução pra rodar sync R2.

5. **Read `affiliateTag`**: `sites/{site}/src/config.ts` via regex. Define a regra de validação dos links Amazon:
   - Tag preenchida → links DEVEM ter `?tag={tag}&linkCode=ogi&th=1&psc=1`
   - Tag vazia → links DEVEM ser crus (sem `?tag=...`)

6. **Rodar auditoria** nas 9 categorias do `regras_auditoria_artigo` (seção "Critérios de auditoria" abaixo). Gerar:
   - `issues`: array de `{level, rule, message, product?, fix?, evidence?}`
   - `summary`: 1-3 frases sobre estado geral
   - `passed`: bullets MUITO curtos (10-30 palavras) do que passou bem

7. **Detectar meta description placeholder específico** (paridade com `detectMetaDescPlaceholder` do painel — agent-edit.ts:1221-1235):
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

8. **Escrever relatório** em 2 locais (paridade com pattern de bíblias/produtos):
   ```
   docs/biblias-v2/.audits/articles/{site}-{slug}-audit-{YYYY-MM-DD-HHMM}.md  ← snapshot timestamped
   docs/biblias-v2/.audits/articles/{site}-{slug}-audit-last.md               ← caminho fixo
   ```
   Sufixo `-audit-` diferencia do relatório do `artigo-analise-final` (que usa `-finalreview-`).
   
   Criar `docs/biblias-v2/.audits/articles/` se não existir.

9. **Reportar no chat**: linha curta com count de issues por nível + path do relatório.

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

## Schema do output (`AuditArticleSchema`)

Paridade com `agent-edit.ts:1077-1084`:

```typescript
{
  issues: Array<{
    level: 'error' | 'warn' | 'info',
    rule: string (2-60 chars),
    message: string (10-800 chars),
    product?: string,    // ASIN se aplicável
    fix?: string (max 800 chars),
    evidence?: string (max 160 chars)
  }>,
  summary: string (20-800 chars),
  passed: string[] (max 20 items, 5-280 chars cada)
}
```

## Formato do relatório

Template do markdown a salvar em `.audits/articles/{site}-{slug}-audit-{date}.md`:

```markdown
# Auditoria: {site}/{slug}

- **Data:** {YYYY-MM-DD HH:MM}
- **affiliateTag:** {tag ou "(vazia — site em construção)"}
- **Produtos auditados:** {count} ({asins list})

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

Também salvar versão `.audits/articles/{site}-{slug}-audit-last.md` (mesmo conteúdo) — caminho fixo pra leitura programática se precisar.

## Voz analítica (CRÍTICO)

Igual a todas as auditorias do projeto:

- **Tom analítico.** "O review do produto 2 cita 5.000 páginas; bíblia confirma 4.500."
- **NÃO comente preferências.** "Acho que ficaria melhor com Y" → "Y pode ser uma alternativa que cita {dado da bíblia}".
- **Cite evidência.** Cada issue com `evidence` (do `.mdx`) ou referência a campo da bíblia. Sem evidência, descarta.

## Quando NÃO usar essa skill

- **Artigo sem produtos** (`products: []` vazio): nada pra auditar. Aborta orientando completar lineup primeiro.
- **Falta de bíblia** de produtos: rodar `bun scripts/sync-biblias-r2.ts --apply` primeiro. Sem bíblias, a auditoria de `claim-vs-bible` é inútil (não consegue cruzar).
- **Quer decidir lock**: use `artigo-analise-final` em vez disso — ela faz tudo isso + checks estruturais + `readyToLock`.
- **Quer reescrever reviews**: use `artigo-reviews-auditar` em vez disso — ela é write op que propõe diffs cross-produto.

## Cooldown / dedup

O painel tem cooldown de 20s por artigo (server.ts:2575). A skill local não tem cooldown automático — rodar 2x em sequência custa $0.05-0.08 cada. Recomendo rodar com intervalo razoável.

## Sincronização painel ↔ skill ↔ prompt canônico

```
docs/painel/_data/agent-prompts.json:audit_article  (SOURCE OF TRUTH editorial)
    ├── handler do painel (POST /agent/article/:site/:slug/audit)
    └── esta SKILL.md (versão local executável)
```

Compartilha o `regras_auditoria_artigo` com `final_review` (via `_shared`). Logo, manter sincronia entre essa skill e a `artigo-analise-final` (mesmas 9 categorias, mesma definição).

## Armadilhas recorrentes

### 1. Tentar editar o `.mdx`
Skill é PURAMENTE read-only. Mesmo que veja problema fácil de consertar, NÃO edita. O user roda skills específicas (`artigo-intro-escrever`, `artigo-review-criar`, etc.) pra corrigir.

### 2. Confundir com `artigo-analise-final`
`artigo-analise-final` faz tudo isso AINDA + checks estruturais + readyToLock. Se o user quer saber "está pronto pra travar?", direcionar pra `artigo-analise-final`. Se quer só "audita o que tem", esta skill é a correta.

### 3. Confundir com `artigo-reviews-auditar`
Aquela é WRITE op (sugere mudanças, user aprova granular). Esta é READ-only (só relatório). Esta cobre artigo INTEIRO (intro, guide, reviews, frontmatter); aquela cobre só reviews cross-produto.

### 4. Citar comprador no audit
"Compradores reclamam de X" → quebra a voz analítica. Sempre reescreva: "Bíblia registra trade-off X (campo Y)".

### 5. Não criar diretório `.audits/articles/`
Primeiro run do skill no projeto, o diretório não existe. Sempre fazer `mkdir -p docs/biblias-v2/.audits/articles/` antes de escrever.

### 6. Achar tone-clone onde é template intencional
A estrutura dos 4 parágrafos com prefixos exatos (`Para quem é:` / `Por que gostamos:` / `Pontos de atenção:` / `Resumo:`) é o template canônico — **não é tone-clone**. Só flag tone-clone se houver frase concreta repetida em 2+ reviews ou parágrafo quase idêntico com nome trocado.

### 7. Tag vazia esperando link com tag
Site em construção tem `affiliateTag: ''`. Nesse caso, links Amazon devem ser CRUS (`https://amazon.com.br/dp/X`). Se a IA assume tag preenchida e flagga "tag-affiliate", está errado. Sempre cruzar com o config real.

### 8. Sobrescrever audit antigo sem perceber
O arquivo `-audit-last.md` é sobrescrito a cada run. Se precisar comparar com run anterior, olhe o snapshot timestamped `{site}-{slug}-audit-{date}.md`.

### 9. Inventar issues pra ter "achados"
Audit vazio é válido. Se artigo está bom, `issues: []` + `passed: [...]` é o output correto. Prefira 5 findings bem evidenciados a 20 vagos.

## Exemplo de invocação

Exemplos válidos do user — modo padrão:
- "audita o artigo melhor-impressora-custo-beneficio do melhorimpressora"
- "audita o artigo X"
- "https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio" (com hint "audita")

Args canônico que invoco: `Skill(skill="artigo-auditar", args="melhorimpressora/melhor-impressora-custo-beneficio")`

## Limitação intrínseca conhecida

Sem schema Zod programático no output, validação fica editorial. ~5% de chance de algum issue ter `evidence` ligeiramente longa (>160 chars) ou estrutura do markdown levemente quebrada. Mitigação: conferir mentalmente antes de salvar o `.md`. Em caso de dúvida, optar por menos issues e mais evidência forte.
