---
name: artigo-intro-escrever
description: Escreve a introdução do artigo (body markdown que vai logo após o frontmatter do .mdx). Aceita URL do painel (editor-artigo.html?site=X&slug=Y) OU args canônicos site/slug. Régua dura — §1 abre com pergunta + keyword em bold, §final fecha com keywordPlural em bold + ✅, 2-3 parágrafos, 300-800 chars, tom conversacional (não consultor científico), sem critérios técnicos detalhados (isso é função do guideContent), sem travessão, sem mencionar marcas/modelos específicos. Substitui só o body — frontmatter e produtos ficam intactos. Backup + commit + push + sync VPS. Régua v1.18.0 (2026-05-28) — carrega `docs/painel/_data/chavoes-por-nicho.json` baseado em `niche` do site pra respeitar chavões nicho-específicos.
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

Sua função é gerar **2-3 parágrafos curtos** que estabeleçam o contexto do artigo, atendam a régua SEO (keyword bold §1, keywordPlural bold §final, ✅ no fim), e respeitem as restrições editoriais (sem travessão, sem marcas específicas, linguagem geral, tom conversacional alinhado com os reviews — NÃO registro científico-médico).

A intro **CONTEXTUALIZA + sinaliza o que esperar do artigo**. Não ensina critérios técnicos detalhados (isso é função do `guideContent` H2 "Como escolher" que vem depois). Não usa registro acadêmico nem cita instituições científicas (OMS, FAO, ANVISA, FDA). O leitor que chega aqui ainda está se orientando — a intro abre a porta, não dá aula.

## Pré-requisitos

- O `.mdx` do artigo já existe em `sites/{site}/src/content/reviews/{slug}.mdx`. Se não, abortar com orientação pra criar via painel ("✨ Criar artigo" no site detail → `make-reviews-stub`).
- O artigo tem **pelo menos 1 produto** no lineup (`products: []` vazio = abortar — intro sem ângulo concreto fica vaga).
- Bíblias dos produtos do artigo estão em `docs/biblias-v2/{ASIN}.json`. Se alguma faltar, rodar `bun scripts/sync-biblias-r2.ts --apply` antes (skill avisa e aborta se faltar).
- `affiliateTag` em `sites/{site}/src/config.ts` é conhecida (pode ser string vazia pra sites em construção — intros NÃO PRECISAM ter links Amazon, então tag vazia OK).

## Invariantes

- **Toca em até DOIS lugares: o body do .mdx (intro) E a linha `title:` do frontmatter.** O `title:` só é reescrito quando não está no padrão canônico (ver "## Régua do título do artigo" abaixo). Todo o resto (description, keyword, keywordPlural, listHeading, products, guideContent) fica intacto.
- **Body é puro markdown.** Verificado: zero artigos do monorepo têm componentes MDX no body — toda a estrutura (TabelaTop, ProductSection, ReviewLayout, etc) é montada pelo `<SlugPage>` via thin-wrapper em `pages/[slug].astro`. Skill nunca insere `<TabelaTop>` ou similar.
- **2 a 3 parágrafos** (obrigatório). Cada parágrafo separado por linha em branco. 4 parágrafos é EXCESSO — intro vira ensaio.
- **300 a 800 chars no total** (todo o body somado). Alvo: 500-700 chars. Antes era 300-1500 e sub-agents miravam 900-1400, tornando a intro cansativa — apertado em 2026-05-26 após feedback "muito longa, muito explicativa".
- **Tom conversacional alinhado com os reviews** (NOVA régua 2026-05-26). Escreva como amigo que pesquisou explicando, NÃO como consultor científico/médico ditando. Linguagem cotidiana, sem registro acadêmico. Os reviews do mesmo artigo são o padrão tonal — intro NÃO pode soar mais formal que eles.
- **NÃO citar instituições científicas** (OMS, FAO, ANVISA, FDA, INMETRO, IFOS). Esse tipo de menção quebra o tom de comparador editorial e vira página de saúde. Se a info importa, ela aparece nos reviews (como feature de produto certificado) ou no guide.
- **NÃO dar recomendações com número** ("X recomenda N mg/dia"). Números OK quando aparecem nos reviews depois (são features dos produtos comparados). Na intro, números viram recomendação acadêmica e quebram o tom.
- **NÃO entrar em critérios técnicos detalhados** que pertencem ao `guideContent` H2 "Como escolher". Listar "três fatores que diferenciam premium de entrada" é função do guia, não da intro. Intro fica em PERFIL DE USO e PANORAMA, sem ensinar a escolher.
- **Bold só em `**markdown**`**, nunca `<b>` ou `<strong>`.
- **Sem travessão (—).** Use vírgula ou ponto.
- **Sem superlativos sem evidência** — "o melhor disponível", "incomparável", "imbatível" são proibidos. "Excelente", "ótimo" são OK se contextualizado.
- **NÃO mencionar marcas, modelos ou ASINs específicos** na intro. Linguagem GERAL (perfil de uso, critério de decisão, panorama da categoria). Marcas vão na tabela e nos reviews — não na intro.
- **NÃO inventar dados** que não estejam nas bíblias dos produtos. Se a intro precisar de um número, ele veio de alguma bíblia.
- **NÃO usar heading de nenhum nível** (`#`, `##`, `###`, `<h1>`, `<h2>`, `<h3>`) na intro. Começa direto com prosa. O `title` do frontmatter cumpre o papel de H1; injetar outro heading no body criaria H1 duplicado ou hierarquia quebrada.

## Fluxo

0.5. **Carregar chavões do nicho** (régua v1.18.0):
   - Identifique `niche` em `docs/painel/sites-meta.json` (ex: Pré Treino, Creatinas, Tablets)
   - Read `docs/painel/_data/chavoes-por-nicho.json` — use `_genericos` + bloco do nicho
   - Aplique limites como guard rail: não passar de `ingles_max`, `medico_tecnico_max`, `industrial_max`, `indicacao_medica_max`
   - Banidos absolutos sempre: lineup, SKU, ASIN, datasheet, notificado, trade-off, hardcore

1. **Parse args**: detecta URL vs canônico, extrai `site` e `slug`. Valida `[a-z0-9-]+` em ambos.

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   git stash push -m "skill-artigo-intro-escrever-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Painel VPS commita+pusha automaticamente quando user cria/edita conteúdo na UI; Mac local pode estar 5-30s atrás. Sem este pull, skill pode ler estado stale e abortar com falso "X não existe localmente". Se pull falhar (rede offline, conflito), seguir mesmo assim.

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

8. **Gerar a intro** seguindo a régua editorial (ver seção abaixo). 2-3 parágrafos markdown.

8.5. **Avaliar/arrumar o título** (ver "## Régua do título do artigo" abaixo pra detalhe): se o `title:` NÃO estiver no padrão canônico `{Keyword Title Case}: {os|as} {N} melhores em {ano}` (ou no fallback sem contagem pra N<3), gere o título novo e marque pra aplicar no passo 11. Se já estiver no padrão, só atualiza a contagem N se o lineup mudou; senão deixa intacto. Respeita `contentLocked` (não mexe se travado).

9. **Validar mentalmente** antes de salvar:
   - 300-800 chars total (alvo 500-700)
   - 2-3 parágrafos (separados por linha em branco)
   - §1 contém `?` (pergunta) E `**{keyword}**` bold
   - §final contém `**{keywordPlural}**` bold E termina com `. ✅`
   - **Exatamente 2 bolds no body inteiro** (keyword no §1, keywordPlural no §final). NADA mais em bold — sem `**ano**`, sem `**marca**`, sem nenhum outro destaque.
   - Sem travessão `—` nem `–`
   - Sem `<b>` ou `<strong>` (só `**markdown**`)
   - Sem heading de nenhum nível: nem markdown (`# `, `## `, `### `) nem HTML (`<h1>`, `<h2>`, `<h3>`)
   - Sem menção a marca/modelo/ASIN específico (linguagem geral)
   - Se tag preenchida + intro tem links Amazon (raro mas possível): validar `?tag={tag}&linkCode=ogi&th=1&psc=1`
   - **Título** (só se foi reescrito no passo 8.5): 30-100 chars, contém a keyword (case-insensitive), gênero `os/as` correto, contagem N batendo com `products[]`, sem travessão, sem ponto final

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
    - **Se o título foi reescrito (passo 8.5)**: faça um Edit ADICIONAL na linha `title: "..."` do frontmatter (string única). NÃO toque em description/keyword/keywordPlural/listHeading/products. São 2 Edits no mesmo arquivo: 1 no body (intro), 1 na linha do title.

    Se body atual é muito curto (ex: só `[a escrever: ...]`), `old_string` é único na file. Edit funciona direto.
    Se body atual é a intro velha (300-800 chars), também é único.
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

## Régua do título do artigo (v1.21.0, canon 2026-06-04)

Além da intro, a skill **arruma o `title` do frontmatter** quando ele não está no padrão canônico da rede. Motivo: o `make_reviews` cria o title só como "Keyword Capitalizado:" e o "as X melhores em ANO" sempre foi um passo manual que quase nunca era feito, deixando títulos fracos tipo "Melhor impressora epson". Como a intro roda no fim do artigo, é o momento natural de fechar o título com a contagem real de produtos.

### Padrão canônico (já usado em melhoraspirador/melhorestablets)

`{Keyword em Title Case}: {os|as} {N} melhores em {ano}`

Exemplos reais da rede:
- `Melhor Impressora Epson: as 9 melhores em 2026`
- `Melhor Aspirador de Pó Vertical: os 9 melhores em 2026`
- `Melhor iPad: os 5 Melhores em 2026`

Componentes:
- **Keyword em Title Case PT-BR**: capitaliza palavras de conteúdo; **preserva marca/sigla** (Epson, HP, iPad, A3, EcoTank); mantém **minúsculas** as preposições/artigos curtos (`de`, `e`, `para`, `com`, `da`, `do`, `em`, `a`, `o`). Ex: "melhor impressora tanque de tinta" → "Melhor Impressora Tanque de Tinta".
- **{os|as}**: concordância de gênero do substantivo-núcleo da keyword. impressora/creatina/mesa → **as**; tablet/aspirador/iPad/robô → **os**.
- **{N}**: número de produtos do lineup (`products[]`), em algarismo.
- **{ano}**: ano atual.
- **Sem ponto final.**

### Quando arrumar (conservador — decisão Marcelo 2026-06-04)

Só reescreve se o título **NÃO** já estiver no padrão. Detecção:
- **Já-no-padrão (NÃO toca)**: bate o regex `:\s*(os|as)\s+\d+\s+melhores\s+em\s+\d{4}` OU, no fallback sem contagem, termina com ` em \d{4}` sem placeholder.
- **Stub/fraco (arruma)**: minúsculo, sem ano, sem contagem, ou == keyword cru (ex: "Melhor impressora epson", "Melhor Impressora Custo Benefício").
- **Já-no-padrão mas N mudou**: se o lineup cresceu/encolheu, atualiza só o número (a contagem no título não pode envelhecer — mesmo cuidado da auditoria cross-produto).

### Fallback N<3 (decisão Marcelo)

Se o lineup tem menos de 3 produtos, "as 2 melhores" soa fraco. Use:
`{Keyword em Title Case} em {ano}` (sem contagem). Ex: "Melhor Impressora Epson em 2026".

### Limite de tamanho (auditor `title-qualidade`)

30-100 chars (alvo 40-70). O Zod do schema é só `z.string()` (não trava build), mas o `artigo-auditar` flagra <30 ou >100 como warn. Se a keyword for longa e o padrão estourar 100, caia no fallback sem contagem; se ainda assim passar de 100, mantenha só "{Keyword em Title Case}".

### Guard `contentLocked`

Se o artigo está `contentLocked: true`, **NÃO mexe no título** (título é H1 + `<title>` SEO; mudar artigo travado pode quebrar ranking). Avisa o user e segue só com a intro, se ele tiver destravado.

### O que NÃO confundir

- O `title` é DIFERENTE do `listHeading` (H2 da TabelaTop, ex "Quais as melhores impressoras Epson em 2026?"). A skill só mexe no `title`; `listHeading` tem régua própria e fica intacto.
- A keyword e a keywordPlural do frontmatter NÃO mudam — o título deriva da keyword, não a substitui.

### Exemplo antes/depois (melhor-impressora-epson, 9 produtos)

- ❌ `title: "Melhor impressora epson"` (minúsculo, sem contagem, sem ano)
- ✅ `title: "Melhor Impressora Epson: as 9 melhores em 2026"`

## Régua editorial — ESTRUTURA OBRIGATÓRIA

### §1 — abertura com pergunta + keyword bold

Começa com uma **pergunta** contendo `**{keyword}**` em bold markdown. Variantes aceitas — TOM padrão é EMPÁTICO (estilo blog afiliados brasileiro), não consultor frio:

**Empáticas (preferidas — canon 2026-05-26)**:
- `Está em dúvida sobre qual a **{keyword}**?`
- `Cansou de procurar a **{keyword}** sem decidir?`
- `Procurando a **{keyword}** sem complicação?`
- `Quer saber qual a **{keyword}** em {ano}?`

**Neutras (OK quando o site tem tom mais sóbrio)**:
- `Qual a **{keyword}**?` / `Qual é a **{keyword}**?` / `Qual o **{keyword}**?`
- `Procurando a **{keyword}**?`
- `Quer comprar a **{keyword}**?`

Após a pergunta, **1-2 frases curtas** com **promessa de ajuda** (canon 2026-05-26):
- "Preparamos uma seleção pra ajudar você a {benefício}"
- "Te ajudamos a comparar e decidir sem perder tempo"
- "Reunimos os melhores modelos pra você {investir bem | economizar | escolher com segurança}"

A promessa não deve ser vaga ("vamos te ajudar") — sempre amarrada a um benefício concreto pro leitor (economizar, investir bem, decidir rápido, escolher com confiança).

**SEM mencionar marcas/modelos/ASINs específicos.** Linguagem geral.

### §s do meio (opcional — só se for 3 parágrafos)

Aprofundamento PANORÂMICO, NÃO técnico. Estrutura canônica (canon 2026-05-26): **CONJUGAR aplicações de uso + perfis concretos** — começa abrindo onde a categoria se aplica (acolhedor) e termina com perfis de decisão concretos (informativo).

**Estrutura ideal**:
```
Para {aplicação 1}, {aplicação 2} ou {aplicação 3}, a decisão começa pelo
perfil de uso: quem {perfil A} se dá bem com {opção X}; quem {perfil B}
recupera o investimento de {opção Y}; e quem {perfil C} economiza mais
com {opção Z}.
```

**Exemplos válidos**:
- **Aplicações** (acolhe o leitor): "Para uso em casa, home office ou pequenas empresas" / "Pra treino, estudos ou rotina corrida" / "Em quartos, salas ou ambientes pequenos"
- **Perfis técnicos** (informa decisão): "quem imprime pouco vs todo dia", "quem treina pesado vs casual", "quem tem alergia a X"
- **Panorama da categoria** (alternativa): "o mercado oferece duas tecnologias principais (cartucho e tanque)"
- **Tecnologias específicas OK quando informam decisão** (cartucho/tanque/laser, monohydrate/HCl, óleo de peixe/krill) — esses termos comprador busca e diferenciam decisão. NÃO confundir com critérios técnicos detalhados de guide (forma química, certificações, mg específicos).

**NÃO entrar em**:
- ❌ Critérios técnicos detalhados ("três fatores: concentração, certificação, forma química")
- ❌ Recomendações com números ("OMS recomenda 250-500mg/dia")
- ❌ Siglas de instituições científicas (OMS, FAO, ANVISA, FDA, IFOS, etc — termos certificadores OK quando aparecem nos reviews como feature)
- ❌ Jargão médico/científico ("manutenção cardiovascular", "posologia", "forma química do óleo")
- ❌ Distinções acadêmicas ("triglicerídeo é considerado mais próximo do natural que éster etílico")

Isso tudo é função do `guideContent` H2 "Como escolher" que vem depois. Intro **abre a porta**, guide **ensina a escolher**, reviews **comparam os produtos específicos**.

**SEM bold em nenhuma palavra** — bold é EXCLUSIVO de §1 e §final.

### §final — fechamento com keywordPlural bold + ✅

Use `**{keywordPlural}**` em bold markdown. Variantes de abertura aceitas:

- `Esta seleção reúne as **{keywordPlural}**...`
- `Para te ajudar na escolha, reunimos as **{keywordPlural}**...`
- `Neste guia, reunimos as **{keywordPlural}**...`
- `Confira agora nossa seleção exclusiva das **{keywordPlural}**...`
- `Por isso, reunimos uma lista com as **{keywordPlural}**...`
- `A seguir, reunimos as **{keywordPlural}**...`

**2 estilos de fechamento** (escolher conforme ângulo do artigo):

**a) Valores qualificativos (canon 2026-05-26 — preferido pra produtos "decisão por benefício")**:
> "...destacando as que realmente entregam {valor 1}, {valor 2} e {valor 3} no dia a dia."

Exemplos: "qualidade, economia e praticidade", "potência, autonomia e custo-benefício", "pureza, concentração e absorção". 2-3 valores no máximo. Adjetivo "realmente" OK (qualificador conforme régua dos qualificadores positivos).

**b) Critérios de comparação técnicos (OK pra produtos "decisão por specs")**:
> "...comparadas por {critério 1}, {critério 2} e {critério 3}."

Exemplos: "tecnologia, rendimento e custo por página", "concentração, certificação e custo por dose", "tela, processador e duração de bateria".

Termina **OBRIGATORIAMENTE** com `. ✅` (ponto, espaço, emoji, sem nada depois).

## Exemplos bons (do prompt canônico)

### Exemplo 1 — impressora custo benefício (3 parágrafos, **CANON MEIO-TERMO**)

Este é o **canon visual de referência** desde 2026-05-26. Padrão do "blog afiliados brasileiro" — empático + perfis concretos + promessa enfática. Cobre os 3 padrões aprovados em sessão: §1 empático com promessa de ajuda, §2 aplicações de uso conjugadas com perfis técnicos de decisão, §final com 3 valores qualificativos.

```
Está em dúvida sobre qual a **melhor impressora custo benefício** em 2026? Preparamos uma seleção pra ajudar você a investir bem e economizar nas suas impressões.

Para uso em casa, home office ou pequenas empresas, a decisão começa pelo perfil de uso: quem imprime pouco se dá bem com modelos a cartucho; quem imprime todo dia recupera o investimento de uma tanque de tinta em poucos meses; e quem precisa de volume alto em preto e branco economiza mais com a laser monocromática.

Esta seleção reúne as **melhores impressoras custo benefício** disponíveis em 2026, destacando as que realmente entregam qualidade, economia e praticidade no dia a dia. ✅
```

**Por que este é o canon**:
- §1: pergunta empática ("Está em dúvida sobre...") + promessa concreta de ajuda ("investir bem e economizar")
- §2: aplicações de uso ("em casa, home office ou pequenas empresas") + 3 perfis CONCRETOS com tecnologias ("cartucho/tanque/laser") — informa decisão sem invadir o guideContent
- §3: fechamento com 3 valores qualificativos ("qualidade, economia, praticidade") em vez de critérios de comparação fria
- ~610 chars, 3 §, 2 bolds, ✅

### Exemplo 2 — creatina (3 parágrafos)

```
Qual é a **melhor creatina** para comprar em 2026? O mercado oferece dezenas de opções com pureza, qualidade e preços muito diferentes entre si, e nem todo produto entrega o que promete.

Neste guia, analisamos as principais creatinas disponíveis por tipo, custo-benefício e solubilidade, para diferentes perfis de uso.

Se você quer encontrar as **melhores creatinas** do mercado sem perder tempo com pesquisa, está no lugar certo. Confira o ranking completo abaixo. ✅
```

### Exemplo 3 — ômega 3 (BAD vs GOOD pareado, caso real 2026-05-26)

**❌ BAD** (924c, registro científico-médico, invade conteúdo de guia):

```
Qual o **melhor ômega 3** pra escolher em 2026? A decisão depende do que você quer com a suplementação: pra manutenção cardiovascular e cognitiva, a OMS e a FAO recomendam 250 a 500 mg de EPA e DHA por dia pra adulto saudável. Quem não come peixe gordo 2 a 3 vezes por semana pode usar suplemento pra fechar essa conta sem complicar a rotina.

O que diferencia produtos premium de opções de entrada é a soma de três fatores: concentração total de ômega 3 na porção (não no peso da cápsula), selo internacional de pureza que ateste ausência de metais pesados, e a forma química do óleo (triglicerídeo é considerado mais próximo do natural que éster etílico). Posologia e tamanho do pote também pesam no custo por dia de uso contínuo.

Para te ajudar na escolha, reunimos as **melhores ômega 3** disponíveis no Brasil em 2026, comparadas por concentração de EPA e DHA, certificação de pureza, forma química e custo por dose. ✅
```

Por que está errado:
- Cita "OMS e FAO" (instituições científicas) e dose acadêmica "250-500mg" — registro médico
- Lista "três fatores" técnicos (concentração, selo, forma química) — é CONTEÚDO DO GUIA "Como escolher"
- "Triglicerídeo é mais próximo do natural que éster etílico" — distinção acadêmica
- "Posologia", "manutenção cardiovascular e cognitiva" — jargão médico
- 924 chars — acima do range 300-800

**✅ GOOD** (~500c, tom conversacional, contextual):

```
Qual o **melhor ômega 3** pra escolher em 2026? Pra quem não come peixe gordo na rotina, o suplemento virou prática comum, especialmente entre quem busca apoio cardiovascular ou cognitivo. Mas o mercado tem opções bem diferentes em concentração, certificação e preço, e nem todo pote entrega o que promete pelo valor.

Para te ajudar, reunimos as **melhores ômega 3** disponíveis no Brasil em 2026, comparadas por concentração de EPA e DHA, certificação de pureza e custo por dose. ✅
```

Por que está OK:
- Sem siglas de instituição (OMS/FAO sumiram)
- Sem dose acadêmica (250-500mg sumiu)
- Cita "EPA e DHA" SÓ no fechamento como sinalização (não como recomendação)
- Sem lista de "três fatores" — esse trabalho é do guia
- "Pra quem não come peixe gordo na rotina" — perfil de uso conversacional
- Termo "concentração / certificação / preço" genérico, sem ensinar a diferença
- ~500 chars, 2 §

## Regras duras (bloqueiam audit)

- §1 contém `?` (pergunta) E `**{keyword}**` em bold markdown
- §final contém `**{keywordPlural}**` em bold markdown E termina com `✅`
- **Apenas 2 bolds totais no body**: keyword no §1 + keywordPlural no §final. NADA mais em bold.
- Bold em markdown `**texto**`. NUNCA `<b>` ou `<strong>`.
- Começa direto com prosa, SEM heading. NÃO use `## Introdução` nem qualquer h2/h3.
- 2-3 parágrafos (separar com linha em branco). 4 parágrafos é EXCESSO.
- 300-800 chars no total. Alvo: 500-700.
- Sem travessão (—). Vírgula ou ponto.
- Sem superlativos sem evidência (`o melhor disponível`, `incomparável`).
- NÃO mencionar marcas, modelos ou ASINs específicos. Linguagem geral.
- NÃO inventar dados que não estejam nas bíblias dos produtos.
- **NÃO citar instituições científicas/regulatórias** (OMS, FAO, ANVISA, FDA, INMETRO, IFOS). Registro acadêmico quebra o tom de comparador editorial.
- **NÃO dar recomendações com número** ("X recomenda N mg/dia"). Números só nos reviews (são features dos produtos comparados, não recomendações).
- **NÃO entrar em critérios técnicos detalhados** (forma química, distinções acadêmicas, listas tipo "três fatores"). Esse trabalho é do `guideContent` H2 "Como escolher". Intro fica em PERFIL DE USO + PANORAMA.
- **Tom conversacional, NÃO científico-médico**. Escreve como amigo que pesquisou, não como consultor. Use os reviews do mesmo artigo como referência tonal — intro NÃO pode soar mais formal que eles.

### Título (quando reescrito)
- Padrão `{Keyword Title Case}: {os|as} {N} melhores em {ano}` (N≥3) ou fallback `{Keyword Title Case} em {ano}` (N<3). **Sem ponto final.**
- 30-100 chars; contém a keyword (case-insensitive); gênero `os/as` correto; N = `products[]`; sem travessão.
- **Só reescreve se fora do padrão** (conservador). Já-no-padrão só atualiza N se o lineup mudou.
- **Nunca** mexe no título de artigo `contentLocked: true`.

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

## Tom conversacional (CRÍTICO)

Pergunta-teste antes de salvar: *"Um amigo que não entende disso entenderia?"* Se não → simplifica.

Evite jargão corporativo (❌ "alinhado à narrativa", "perfil favorável", "posicionamento de mercado", "uma rotina X séria"). Use linguagem direta (✓ "se você imprime em casa", "boa dose pra rotina contínua"). NUNCA cite procedência burocrática ("alérgenos da Amazon confirmam", "atributos declaram") — destila o claim direto.

Referência canônica pra calibrar tom:
- `sites/melhorimpressora/src/content/reviews/melhor-impressora-custo-beneficio.mdx` (intro do artigo é bom exemplo)


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
- **Exceção**: "rende X páginas, segundo a Epson" (claim só-fabricante que qualifica expectativa) OK
## Armadilhas recorrentes

### 1. Mais de 2 bolds
Hábito de bold em "2026", "tanque de tinta", "Wi-Fi" — TODOS proibidos. Exatos 2 bolds: keyword no §1, keywordPlural no §final. Confere antes de salvar contando os marcadores `**` no body: devem ser exatamente 4 (1 abre + 1 fecha por bold × 2 bolds = 4 marcadores `**`, ou 8 caracteres `*` se for contar asterisco a asterisco).

### 2. Heading de qualquer nível por hábito
"# Título", "## Introdução", "### Por que esse guia", `<h1>`, `<h2>` — todos proibidos. A intro começa direto com a pergunta do §1. O H1 já é o `title` do frontmatter; injetar outro no body quebra a hierarquia.

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

### Auto-check de capitalização + duplicação (régua v1.18.3, canon 2026-05-28)

**Bug-class real** (caso `melhorpretreino` commit `a72e7d9`): substituições mecânicas podem causar duplicação contígua, bullets minúsculos ou minúscula após ponto.

**Auto-check obrigatório ANTES de gravar**:

```python
import re

# Para cada campo gerado (shortDescription, fullReview, pros, cons, specs.value):

# 14a) Duplicação contígua (>=8 chars repetidos em sequência)
for m in re.finditer(r'([a-zA-ZÀ-ÿ\s]{8,40})\1', campo):
    print(f"⚠ duplicação: {m.group(0)}")
    # → Reescreve removendo a metade duplicada

# 14b) Bullet começa com minúscula (em pros/cons)
for bullet in pros + cons:
    if re.match(r'<strong>[a-záéíóúâêôãõàèìòùç]', bullet):
        print(f"⚠ bullet minúsculo: {bullet[:60]}")
        # → Capitalize primeira letra dentro de <strong>...</strong>

# 14c) Minúscula após ponto (texto editorial — excluir URLs)
for m in re.finditer(r'\. ([a-záéíóúâêôãõàèìòùç])', campo):
    ctx = campo[max(0,m.start()-30):m.end()+30]
    if 'http' in ctx or 'amazon.com.br' in ctx: continue
    if re.search(r'\d+\. \w', ctx[:50]): continue  # lista numerada
    print(f"⚠ minúsc após ponto: ...{ctx}...")
    # → Capitalize a letra (.+ espaço + Letra)
```

**Exemplos reais** (commit a72e7d9, melhorpretreino):
- 14a: `"sem empilhar suplementos sem empilhar suplementos"`
- 14b: `"<strong>aminoácidos essenciais na fórmula</strong>"` (era BCAAs → minúsculo)
- 14c: `"(maior dose declarada). pra emagrecer onde"` (era "em cutting" → minúsculo)

Se achar qualquer bug: corrija ANTES de gravar. Não bloqueia geração, mas evita commit com erro.

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), validação fica editorial — eu (modelo) sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial (3 bolds em vez de 2, char count em 1510, etc). Mitigação: contar bolds (`**`) e chars depois de gerar e ajustar antes de aplicar.
