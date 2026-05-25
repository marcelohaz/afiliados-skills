---
name: artigo-auditar
description: Audita artigo inteiro read-only. Combina 9 categorias editoriais (claim-vs-bible, tag-affiliate, travessao, superlativo, atribuicao-comprador, tone-clone, spec-ausente, dado-inconsistente, decisao-editorial) com 4 checks estruturais (hasIntro, hasGuide, productCount≥3, hasMetaDescription) e calcula readyToLock pra sinalizar se está pronto pra contentLocked:true. Output: relatório completo inline no chat + salva em docs/biblias-v2/.audits/articles/{site}-{slug}-audit-last.md (painel lê). NÃO modifica o .mdx. Aceita URL do painel OU args canônicos site/slug.
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

5. **Read `affiliateTag`**: `sites/{site}/src/config.ts` via regex. Define a regra de validação dos links Amazon:
   - Tag preenchida → links DEVEM ter `?tag={tag}&linkCode=ogi&th=1&psc=1`
   - Tag vazia → links DEVEM ser crus (sem `?tag=...`)

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

7. **Rodar auditoria IA** nas 9 categorias do `regras_auditoria_artigo` (seção "Critérios de auditoria" abaixo). Gerar:
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

## Critérios de auditoria (10 categorias do `regras_auditoria_artigo`)

Use exatamente esses valores em `rule`:

### `claim-vs-bible` (level=`error`)
Afirmação no review (subtitle, shortDescription, fullReview, pros, cons, specs) que NÃO tem origem rastreável na bíblia. Spec inventada, número errado, feature não confirmada. Inclui `evidence` com citação literal.

**Exemplo**: review diz "5.000 páginas por kit" mas bíblia diz "4.500 páginas".

### `tag-affiliate` (level=`error`)
Link Amazon com tag diferente da esperada.
- Tag preenchida no config: links DEVEM ter `?tag={tag}&linkCode=ogi&th=1&psc=1`
- Tag vazia: links DEVEM ser crus (sem `?tag=...`)

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
