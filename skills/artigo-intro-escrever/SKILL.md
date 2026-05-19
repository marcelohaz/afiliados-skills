---
name: artigo-intro-escrever
description: Escreve a introdução do artigo (body markdown que vai logo após o frontmatter do .mdx). Aceita URL do painel (editor-artigo.html?site=X&slug=Y) OU args canônicos site/slug. Régua dura — §1 abre com pergunta + keyword em bold, §final fecha com keywordPlural em bold + ✅, 2-4 parágrafos, 300-1500 chars, sem travessão, sem mencionar marcas/modelos específicos. Substitui só o body — frontmatter e produtos ficam intactos. Backup + commit + push + sync VPS.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida — fluxo natural depois de abrir o editor):
- `https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio`
- Extrai `site` e `slug` do query string

**B) Args canônicos**:
- `melhorimpressora/melhor-impressora-custo-beneficio`

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B (split por `/`).

**Instrução opcional**: se o prompt natural do user contém algo tipo "mais conciso", "enfatize Wi-Fi", "tom mais informal" → eu extraio como instrução adicional e uso no prompt. Se for só "escreve a intro do X" → modo padrão.

# Escrever introdução do artigo

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:generate_intro`. O conteúdo essencial está duplicado abaixo pra autocontenção; em caso de divergência, o prompt canônico ganha.

Você é o curador editorial da introdução do artigo. A introdução é o **body markdown que aparece logo depois do frontmatter** do `.mdx`, antes da tabela de produtos (que é renderizada pelo componente `<SlugPage>` do `@afiliados/ui`).

Sua função é gerar **2-4 parágrafos curtos** que estabeleçam o contexto do artigo, atendam a régua SEO (keyword bold §1, keywordPlural bold §final, ✅ no fim), e respeitem as restrições editoriais (sem travessão, sem marcas específicas, linguagem geral).

## Pré-requisitos

- O `.mdx` do artigo já existe em `sites/{site}/src/content/reviews/{slug}.mdx`. Se não, abortar com orientação pra criar via painel ("✨ Criar artigo" no site detail → `make-reviews-stub`).
- O artigo tem **pelo menos 1 produto** no lineup (`products: []` vazio = abortar — intro sem ângulo concreto fica vaga).
- Bíblias dos produtos do artigo estão em `docs/biblias-v2/{ASIN}.json`. Se alguma faltar, rodar `bun scripts/sync-biblias-r2.ts --apply` antes (skill avisa e aborta se faltar).
- `affiliateTag` em `sites/{site}/src/config.ts` é conhecida (pode ser string vazia pra sites em construção — intros NÃO PRECISAM ter links Amazon, então tag vazia OK).

## Invariantes

- **Nunca toque em nada além do body do .mdx.** Frontmatter (title, description, keyword, products, etc), guideContent, products[] — tudo intacto. Só substitui o conteúdo após o `---` final do frontmatter.
- **Body é puro markdown.** Verificado: zero artigos do monorepo têm componentes MDX no body — toda a estrutura (TabelaTop, ProductSection, ReviewLayout, etc) é montada pelo `<SlugPage>` via thin-wrapper em `pages/[slug].astro`. Skill nunca insere `<TabelaTop>` ou similar.
- **2 a 4 parágrafos.** Ideal: 2-3. Cada parágrafo separado por linha em branco.
- **300 a 1500 chars no total** (todo o body somado).
- **Bold só em `**markdown**`**, nunca `<b>` ou `<strong>`.
- **Sem travessão (—).** Use vírgula ou ponto.
- **Sem superlativos sem evidência** — "o melhor disponível", "incomparável", "imbatível" são proibidos. "Excelente", "ótimo" são OK se contextualizado.
- **NÃO mencionar marcas, modelos ou ASINs específicos** na intro. Linguagem GERAL (perfil de uso, critério de decisão, panorama da categoria). Marcas vão na tabela e nos reviews — não na intro.
- **NÃO inventar dados** que não estejam nas bíblias dos produtos. Se a intro precisar de um número, ele veio de alguma bíblia.
- **NÃO usar heading (H2/H3)** na intro. Começa direto com prosa. O `<title>` do artigo cumpre o papel de heading principal.

## Fluxo

1. **Parse args**: detecta URL vs canônico, extrai `site` e `slug`. Valida `[a-z0-9-]+` em ambos.

2. **Read `.mdx`**: `Read sites/{site}/src/content/reviews/{slug}.mdx`. Se 404, abortar.

3. **Parse frontmatter** mentalmente:
   - `title` (H1)
   - `description` (meta description — só pra entender contexto, não vou tocar)
   - `keyword` — obrigatório no frontmatter (formato canônico). Se ausente, fallback: `title.split(':')[0].toLowerCase().trim()`
   - `keywordPlural` — obrigatório. Se ausente, avisar user e abortar (não invento plural; user precisa preencher).
   - `products: []` — extrair ASINs pra carregar as bíblias

4. **Read bíblias** dos produtos:
   ```bash
   for ASIN in "${ASINS[@]}"; do
     Read docs/biblias-v2/${ASIN}.json
   done
   ```
   Se alguma faltar, abortar com mensagem orientando rodar `bun scripts/sync-biblias-r2.ts --apply`.

5. **Read `affiliateTag`**: `sites/{site}/src/config.ts` → extrair `affiliateTag` via regex `/affiliateTag:\s*['"]([^'"]*)['"]/`. Pode ser `''` (construção, OK) ou preenchida.

6. **Detectar body atual** do `.mdx`: tudo após o **segundo** `---` do arquivo (frontmatter fecha). Salvar pra usar como `old_string` no Edit tool. Pode ser:
   - `[a escrever: agente IA preenche via Gerar introdução]` (stub recém-criado)
   - Texto markdown de uma intro anterior (se já foi escrita antes e tá sendo reescrita)
   - Linhas em branco (raro)

7. **Compor contexto pra geração**:
   - Title + description do artigo
   - Keyword (singular, vai pro §1) + KeywordPlural (vai pro §final)
   - Ano atual (`new Date().getFullYear()`)
   - Lista de ASINs (só count + ASINs; NÃO listar nomes na intro)
   - Bíblias completas (pra entender categoria, perfis, ângulos comuns)
   - Instrução opcional (se detectada no prompt do user, passo 1)

8. **Gerar a intro** seguindo a régua editorial (ver seção abaixo). 2-4 parágrafos markdown.

9. **Validar mentalmente** antes de salvar:
   - 300-1500 chars total
   - 2-4 parágrafos (separados por linha em branco)
   - §1 contém `?` (pergunta) E `**{keyword}**` bold
   - §final contém `**{keywordPlural}**` bold E termina com `. ✅`
   - **Exatamente 2 bolds no body inteiro** (keyword no §1, keywordPlural no §final). NADA mais em bold — sem `**ano**`, sem `**marca**`, sem nenhum outro destaque.
   - Sem travessão `—` nem `–`
   - Sem `<b>` ou `<strong>` (só `**markdown**`)
   - Sem `<h2>`/`<h3>` ou markdown `## `/`### `
   - Sem menção a marca/modelo/ASIN específico (linguagem geral)
   - Se tag preenchida + intro tem links Amazon (raro mas possível): validar `?tag={tag}&linkCode=ogi&th=1&psc=1`

10. **Backup** ANTES de sobrescrever:
    ```bash
    DAY=$(date +%Y-%m-%d); TIME=$(date +%H%M%S); SITE={site}; SLUG={slug}
    mkdir -p "docs/painel/.painel-backups/$DAY"
    cp "sites/$SITE/src/content/reviews/$SLUG.mdx" \
       "docs/painel/.painel-backups/$DAY/article-${SITE}-${SLUG}-${TIME}-intro.mdx"
    ```

11. **Substituir body via Edit tool**:
    - `old_string` = body atual (texto exato após o segundo `---`, incluindo placeholder ou intro velha)
    - `new_string` = nova intro gerada (sem `---` na frente — Edit substitui APÓS o último `---` do frontmatter)

    Se body atual é muito curto (ex: só `[a escrever: ...]`), `old_string` é único na file. Edit funciona direto.
    Se body atual é a intro velha (300-1500 chars), também é único.
    Risco: se a intro velha tem alguma frase EXATA que aparece também no frontmatter (ex: title repetido literal), Edit pode confundir. Mitigação: incluir 1-2 linhas de contexto antes (ex: `---\n\n[body]`) — força match no body especificamente.

12. **Git add + commit + push**:
    ```bash
    git add sites/{site}/src/content/reviews/{slug}.mdx
    git commit -m "feat({site}): intro de {slug} escrita via skill" \
      -m "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
    git push origin main
    ```

13. **Disparar git pull no painel da VPS**:
    ```bash
    bash scripts/painel-vps-pull.sh
    ```
    Falha graciosamente se `.env.painel-skills` não existir.

14. **Reportar no chat**: char count + número de parágrafos + preview da intro inteira (curta o suficiente pra colar) + path do arquivo.

## Régua editorial — ESTRUTURA OBRIGATÓRIA

### §1 — abertura com pergunta + keyword bold

Começa com uma **pergunta** contendo `**{keyword}**` em bold markdown. Variantes aceitas (escolha uma, varia entre artigos do mesmo site pra não ficar repetitivo):

- `Procurando a **{keyword}**?`
- `Quer comprar a **{keyword}**?`
- `Qual a **{keyword}**?` / `Qual é a **{keyword}**?` / `Qual o **{keyword}**?`
- `Está procurando a **{keyword}**?`
- `Está em dúvida sobre qual a **{keyword}**?`
- `Quer saber qual a **{keyword}** em {ano}?`
- ...ou variantes próximas no mesmo espírito

Após a pergunta, **2-5 frases** dando contexto:
- Critério de decisão (o que importa pra escolher)
- Perfil de comprador (quem usa, em que contexto)
- O que vale verificar antes de comprar

**SEM mencionar marcas/modelos/ASINs específicos.** Linguagem geral.

### §s do meio (opcional — só se for 3 ou 4 parágrafos)

Aprofundamento:
- Panorama da categoria (ex: "o mercado oferece duas tecnologias principais: cartucho e tanque de tinta")
- Perfis de uso (ex: "quem imprime raramente paga menos com cartucho; quem imprime muito recupera o tanque em poucos meses")
- O que verificar antes de comprar (rendimento, conectividade, etc — critérios objetivos)

**SEM bold em nenhuma palavra** — bold é EXCLUSIVO de §1 e §final.

### §final — fechamento com keywordPlural bold + ✅

Use `**{keywordPlural}**` em bold markdown. Variantes de abertura aceitas:

- `Esta seleção reúne as **{keywordPlural}**...`
- `Para te ajudar na escolha, reunimos as **{keywordPlural}**...`
- `Neste guia, reunimos as **{keywordPlural}**...`
- `Confira agora nossa seleção exclusiva das **{keywordPlural}**...`
- `Por isso, reunimos uma lista com as **{keywordPlural}**...`
- `A seguir, reunimos as **{keywordPlural}**...`

Termina **OBRIGATORIAMENTE** com `. ✅` (ponto, espaço, emoji, sem nada depois).

## Exemplos bons (do prompt canônico)

### Exemplo 1 — impressora multifuncional (2 parágrafos)

```
Qual a **melhor impressora multifuncional** em 2026 para casa e home office? A decisão começa por uma pergunta simples: com que frequência você imprime? Quem imprime raramente paga menos com uma multifuncional de cartucho: menor custo de entrada e cabe em qualquer bancada. Quem imprime centenas de páginas por mês recupera o investimento de uma tanque de tinta em poucos meses, com custo por página muito menor.

Esta seleção reúne as **melhores impressoras multifuncionais** para uso doméstico e home office disponíveis no Brasil em 2026, comparadas por tecnologia de consumível, rendimento, duplex e Wi-Fi. ✅
```

### Exemplo 2 — creatina (3 parágrafos)

```
Qual é a **melhor creatina** para comprar em 2026? O mercado oferece dezenas de opções com pureza, qualidade e preços muito diferentes entre si, e nem todo produto entrega o que promete.

Neste guia, analisamos as principais creatinas disponíveis por tipo, custo-benefício e solubilidade, para diferentes perfis de uso.

Se você quer encontrar as **melhores creatinas** do mercado sem perder tempo com pesquisa, está no lugar certo. Confira o ranking completo abaixo. ✅
```

## Regras duras (bloqueiam audit)

- §1 contém `?` (pergunta) E `**{keyword}**` em bold markdown
- §final contém `**{keywordPlural}**` em bold markdown E termina com `✅`
- **Apenas 2 bolds totais no body**: keyword no §1 + keywordPlural no §final. NADA mais em bold.
- Bold em markdown `**texto**`. NUNCA `<b>` ou `<strong>`.
- Começa direto com prosa, SEM heading. NÃO use `## Introdução` nem qualquer h2/h3.
- 2-4 parágrafos (separar com linha em branco). Ideal: 2-3.
- 300-1500 chars no total.
- Sem travessão (—). Vírgula ou ponto.
- Sem superlativos sem evidência (`o melhor disponível`, `incomparável`).
- NÃO mencionar marcas, modelos ou ASINs específicos. Linguagem geral.
- NÃO inventar dados que não estejam nas bíblias dos produtos.

## Como usar as bíblias (contexto, não citação)

Carrega TODAS as bíblias dos produtos do lineup pra ENTENDER:
- Que tipo de comprador compra esses produtos (público-alvo)
- Quais critérios técnicos diferenciam os produtos (tanque vs cartucho, monohydrate vs hcl, etc)
- Quais ângulos de conversão são recorrentes (custo-benefício, durabilidade, praticidade)
- Quais perfis de uso aparecem (doméstico, profissional, intensivo)

**NÃO cite produtos por nome na intro.** Use a info das bíblias pra escrever sobre a CATEGORIA, não sobre os produtos específicos.

**Padrão bom**:
- Bíblia 1 (Epson L3250): tanque, 4.500 páginas, doméstico
- Bíblia 2 (HP Smart Tank 581): tanque, 6.000 páginas, escritório pequeno
- Bíblia 3 (HP DeskJet 2975): cartucho, 200 páginas, uso raro

→ Intro fala sobre "tanque de tinta vs cartucho", "rendimento por kit", "perfis de uso doméstico vs uso intenso" — generalizando o que as bíblias revelam, sem citar a Epson, a HP ou modelos.

**Padrão ruim**:
- ❌ "Quem precisa de muito rendimento prefere a Epson EcoTank L3250..." (cita produto específico)
- ❌ "Esta seleção tem 6 modelos: L3250, L4360, ..." (lista produtos — função da tabela, não da intro)

## Voz editorial

- **Tom de quem testou/analisou**: "a decisão depende de", "quem imprime muito recupera", "o mercado oferece"
- **Factual, não promocional**: não promete que a pessoa vai encontrar o produto "perfeito". Promete análise/comparativo.
- **Português brasileiro editorial** — sem gírias, sem anglicismos desnecessários.
- **NUNCA cite compradores/reviews/avaliações/estrelas/Amazon** como entidade. Padrão de toda a voz editorial do projeto (`02-estilo-editorial.md`).

## Armadilhas recorrentes

### 1. Mais de 2 bolds
Hábito de bold em "2026", "tanque de tinta", "Wi-Fi" — TODOS proibidos. Exatos 2 bolds: keyword no §1, keywordPlural no §final. Confere antes de salvar contando os `**` (devem ser 4 — abrindo e fechando de cada bold).

### 2. Heading H2/H3 por hábito
"## Introdução", "### Por que esse guia" — proibido. A intro começa direto com a pergunta do §1.

### 3. Mencionar marca específica
"A Epson lidera o segmento de tanque" — NÃO. Generaliza: "as marcas brasileiras dominam o segmento". Marcas vão na tabela e nos reviews.

### 4. Listar produtos na intro
"Esta seleção tem L3250, L4360, Smart Tank 581 e..." — função da tabela, não da intro. Intro fala sobre CATEGORIA.

### 5. Travessão por hábito
Travessão (`—` ou `–`) é proibido em todos os campos editoriais. Usa vírgula ou ponto.

### 6. `<b>` em vez de `**`
Editores antigos usavam `<b>` (verificável em alguns artigos legados do repo). Skill SEMPRE usa `**markdown**`. Audit do painel pega isso.

### 7. Não terminar com `. ✅`
Padrão: ponto + espaço + emoji. `...selecionadas abaixo. ✅` ✓. `...abaixo ✅` ❌ (sem ponto).

### 8. Esquecer de gerar keywordPlural se ausente no frontmatter
Se o frontmatter não tem `keywordPlural`, abortar e avisar — NÃO inventar plural (gera erro). User precisa preencher manualmente (ou rodar `artigo-review-criar` que gera keywordPlural junto).

### 9. Body markdown com componente MDX
Por hábito de outras frameworks, IA pode tentar emitir `<TabelaTop products={data.products} />`. Proibido. Verificado: zero artigos do repo têm componente MDX no body. Toda a estrutura é montada pelo `<SlugPage>` do `@afiliados/ui`.

### 10. Edit tool com old_string ambíguo
Se a intro velha for muito curta (ex: `[a escrever: ...]`), o `old_string` é único. Mas se for uma intro velha de 1500 chars, partes dela podem repetir outros trechos do .mdx (raro mas possível). Mitigação: incluir 1-2 linhas de contexto antes (ex: `---\n\n[body]`) no `old_string` pra forçar match no body especificamente.

## Sincronização painel ↔ skill ↔ prompt canônico

```
docs/painel/_data/agent-prompts.json:generate_intro  (SOURCE OF TRUTH editorial)
    ├── handler do painel (POST /agent/article/:site/:slug/generate-intro)
    └── esta SKILL.md (versão local executável)
```

Quando Marcelo edita régua editorial (via `agent-config.html` no painel), atualiza `agent-prompts.json` canônico. Esta SKILL.md pode ficar atrasada — atualizar manualmente quando notar drift.

## Quando NÃO usar essa skill

- **Artigo travado** (`contentLocked: true`): o painel rejeita save em /article endpoints (HTTP 423). Skill em si grava direto via Edit tool (não passa pelo painel) — funciona, mas editorialmente: se o artigo tá travado, há razão (SEO estável). Pergunta antes de prosseguir.
- **Artigo sem produtos** (`products: []` vazio): intro sem ângulo concreto fica vaga. Abortar e orientar adicionar produtos primeiro.
- **Falta de bíblia** dos produtos: rodar `bun scripts/sync-biblias-r2.ts --apply` primeiro. Sem as bíblias, a intro fica genérica demais (não consegue inferir categoria/perfis).

## Exemplo de invocação

Exemplos válidos do user — modo padrão:
- "escreve a intro do artigo melhor-impressora-custo-beneficio do melhorimpressora"
- "intro do artigo melhor-impressora-custo-beneficio"
- "https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio" (com hint "intro")

Exemplos com instrução inline:
- "escreve a intro do melhor-impressora-custo-beneficio mais conciso"
- "intro do X enfatizando o aspecto custo-benefício"
- "escreve intro do Y tom mais informal"

Args canônico que invoco: `Skill(skill="artigo-intro-escrever", args="melhorimpressora/melhor-impressora-custo-beneficio")` (instrução vai pelo contexto do prompt natural)

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), validação fica editorial — eu (modelo) sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial (3 bolds em vez de 2, char count em 1510, etc). Mitigação: contar bolds (`**`) e chars depois de gerar e ajustar antes de aplicar.
