---
name: pagina-produto-auditar
description: Audita página individual de produto read-only, cruzando os 6 campos editoriais com a bíblia + diretrizes editoriais + tag de afiliado. Aceita URL do painel (editor-produto.html?site=X&slug=Y) OU args canônicos site/slug. Gera relatório em docs/biblias-v2/.audits/products/<site>-<slug>-last.md.
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

1. **Parse args**: aceita `{site}/{slug}` canônico ou nomes humanos (mesmo padrão do `preencher-pagina-produto`).

2. **Read .mdx**: `Read sites/{site}/src/content/products/{slug}.mdx`. Se 404, abortar com mensagem clara.

3. **Parsear frontmatter**: extrair os 6 campos editoriais (subtitle, shortDescription, pros, cons, specs, fullReview). Se algum vazio/ausente, registra como issue `conteudo-curto`.

4. **Read bíblia**: `Read docs/biblias-v2/{asin}.json`. Sem bíblia, audit não tem como cruzar claims — abortar com mensagem.

5. **Read affiliateTag**: `Read sites/{site}/src/config.ts`. Determinar regra:
   - Tag preenchida: links Amazon devem ter `?tag={tag}&linkCode=ogi&th=1&psc=1`
   - Tag vazia: links Amazon devem ser **crus** sem `?tag=...`

6. **Read reviews que citam o ASIN** (anti-duplicate): `Grep` em `sites/{site}/src/content/reviews/*.mdx` por `asin:.*{asin}`. Se houver, leia o `fullReview` do produto-no-artigo pra comparar com o `fullReview` da página individual — flag se for muito parecido (parágrafo inteiro idêntico, frases-chave repetidas).

7. **Rodar as 9 categorias de checagem** (abaixo).

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

## As 9 categorias de check

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
Tag não permitida em `fullReview`: `<h2>`, `<h3>`, `<ul>`, `<ol>`, `<li>`, `<table>`, `<img>`, `<script>`, `<iframe>`, `<style>`. Permitido apenas: `<p>`, `<strong>`, `<em>`, `<a>`.

### 7. `link-externo-nao-amazon`
Links em `fullReview` que NÃO apontam pra `amazon.com.br/dp/...`. Página individual não deve ter links externos pra outras lojas/sites.

### 8. `conteudo-curto`
Campo crítico vazio ou muito curto:
- `subtitle` ausente ou < 10 chars
- `shortDescription` ausente ou < 40 chars
- `fullReview` ausente ou < 300 chars
- `pros` < 3 itens
- `cons` ausente ou 0 itens
- `specs` < 3 pares

### 9. `redundancia-com-artigo`
Se conseguir detectar: pontos no `fullReview` da página individual que parecem copiados/parafraseados do `fullReview` do produto-no-artigo (anti-duplicate-content SEO).

Heurística: frases-chave repetidas, mesma sequência argumentativa, conclusões iguais. Não precisa ser idêntico — paráfrase próxima conta como redundância.

Se nenhum review cita o ASIN, essa categoria sai vazia automaticamente (não há com que comparar).

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

- **🔴 Crítico**: claim factualmente errado vs bíblia, tag affiliate violada, HTML proibido, tone-comprador.
- **🟡 Aviso**: superlativo sem evidência, conteúdo curto em campo opcional, specs ambientais sem ângulo, suspeita de duplicate content.
- **🔵 Info**: nota que vale registrar mas não exige ação (ex: "subtitle no limite mínimo de 10 chars, considere expandir").

## Boas práticas

- Se a página está quase vazia (stub recém-criado, antes de rodar `preencher-pagina-produto`), resuma em 1 bullet "página em estágio inicial; checagens de conteúdo adiadas até preenchimento" e termine.
- Prefira 5 findings bem evidenciados a 20 vagos. Assine valor, não volume.
- Se errou na auditoria (ex: confundiu campo X com Y), o humano vê no diff do markdown na próxima rodada. Não há vergonha em revisar o próprio relatório.

## Exemplo de invocação

```
audita a página individual da L3250 no melhorimpressora
audita o produto epson-ecotank-l3250 do melhorimpressora
audita melhorimpressora/epson-ecotank-l3250
```

Args canônico: `Skill(skill="auditar-pagina-produto", args="melhorimpressora/epson-ecotank-l3250")`.
