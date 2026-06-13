---
name: artigo-clonar-em-massa
description: Clona um artigo comparativo de um site IRMÃO para outro, reescrevendo TODO o conteúdo do ZERO a partir das bíblias v2 (modo biblia-only) — usa o artigo fonte SÓ como molde estrutural (quantidade de produtos, keyword, badges, ordem, H2/H3 do guide). Pipeline 100% AUTOMATIZADO em etapas, cada uma com gate de auditoria + auto-fix em loop (sem parada humana no meio); o usuário só revisa o resultado final + relatório. Estratégia SERP-monopoly: site novo da rede clona artigo de um existente com texto divergente. Orquestra as skills-peça (review por produto biblia-only via sub-agents Opus paralelos, artigo-intro/guia/meta-escrever) + shuffle determinístico dos produtos do meio (top-3 fixo) + comparador de duplicata vs fonte no fim. NÃO faz deploy. NÃO trava o artigo (contentLocked fica false). Para em "commitado + buildado + preview pronto".
---

## Parse de input

Args canônico: `targetSite SOURCE=sourceSite/sourceSlug [TITLE="..."] [HOME=yes|no] [MODE=biblia-only|hybrid]`

Exemplo real:
```
melhorpretreino SOURCE=melhorpretreino-com/melhor-pre-treino TITLE="Os 11 melhores pré-treinos em 2026 (Atualizado)" HOME=yes MODE=biblia-only
```

- `targetSite` (obrigatório): site destino (ex: `melhorpretreino`).
- `SOURCE=` (obrigatório): `site/slug` do artigo fonte (ex: `melhorpretreino-com/melhor-pre-treino`).
- `TITLE=` (opcional): título do artigo destino. Se omitido, **NÃO reusar o título da fonte nem só "derivar da keyword"** (isso gera `<title>` idêntico ao irmão → dup na SERP). **OBRIGATÓRIO divergir**: aplicar a régua "Divergência cross-site" da `artigo-intro-escrever` — ler os títulos dos irmãos (mesmo slug/keyword nos outros sites), escolher o padrão de ASSINATURA deste site (pool P1-P4, mapa na memória `afiliados.seo.titulos-artigo-3-padroes-anti-dup.md`), lead = campo `keyword` (não forçar "Melhor"), número obrigatório, ≤60 chars. Causa-raiz dos 21 títulos idênticos (auditoria 2026-06-13): a clone reusava o título da fonte.
- `HOME=` (opcional, default `no`): se `yes`, configura o artigo como home do site (homeReviewSlug).
- `MODE=` (opcional, default `biblia-only`): `biblia-only` (texto 100% da bíblia, zero leakage do fonte) ou `hybrid` (top-3 da bíblia, 4+ pode considerar o fonte). **Default e recomendado: biblia-only.**

Slug do artigo destino = mesmo slug do fonte (ex: `melhor-pre-treino`), salvo override futuro.

## O que esta skill É (e não é)

É o **orquestrador full-auto** de clone de artigo. Análogo de `pagina-produto-criar-em-massa`, mas pra artigo inteiro.

- **Reusa** as skills-peça (`artigo-review-criar` régua, `artigo-intro-escrever`, `artigo-guia-escrever`, `artigo-meta-escrever`, `artigo-reviews-auditar`, `artigo-auditar`) — NÃO reimplementa régua editorial (evita drift; paridade com `agent-prompts.json`).
- **Conteúdo 100% do ZERO** a partir das bíblias. O artigo fonte serve SÓ de molde: nº de produtos, lineup, badges, keyword/keywordPlural/listHeading, e a estrutura de H2/H3 do guide. Em `biblia-only` os sub-agents NÃO veem o texto do fonte (sem leakage).
- **NÃO é a IA do painel.** Roda na assinatura (Claude Code), Opus 4.8. (A op `clone-article` do painel usa API key e está fora do fluxo.)

## Modelo

Opus 4.8 (ou mais novo). Sub-agents herdam o modelo da sessão (`settings.json: opus[1m]`) OU são fixados com `model: opus` no Agent tool. NUNCA Sonnet/Haiku (régua do projeto: skills sempre Opus).

## Ambiente (CRÍTICO)

Edição roda onde os arquivos do projeto estão acessíveis. Se a sessão é VPS-only (Mac local EPERM-blocked), TODO I/O de arquivo é via SSH na VPS (`/home/melhorserum-painel/afiliados`), e os sub-agents geram conteúdo retornando dados estruturados; a skill-mãe centraliza a escrita via SSH (ownership `melhorserum-painel`, 1 commit). Caso contrário, opera direto no repo local. Detecte no início.

## Invariantes

- **⚠️ GATES DE AUDITORIA OBRIGATÓRIOS — NUNCA PULAR**: Etapa 1.4 (`artigo-reviews-auditar`, cross-produto) E Etapa 4 (`artigo-auditar`) são TRAVAS DURAS. O pipeline NÃO pode reportar "pronto/concluído" sem ter RODADO as duas e obtido `readyToLock: SIM`. Pular = execução INVÁLIDA. **Caso real (1º run, melhorpretreino 2026-05-29): os audits foram pulados e o artigo carregava 8 erros factuais críticos** (4 claims de cafeína falsos: "único sem cafeína"/"no topo"/"no teto"/"sem pico" com 400mg; + 3 brand-swaps no guide: Dux descrito com specs do True Source, 3VS como "contém glúten"). **Build + gates mecânicos NÃO pegam isso — só os audits editoriais.** Os audits são o que separa "lê bonito" de "está correto".
- **NÃO faz deploy.** Para em "commitado + buildado + preview pronto". Deploy exige aprovação humana explícita (régua do projeto).
- **NÃO trava** (`contentLocked` fica false/ausente) — editável após revisão.
- **Full-auto, sem checkpoint humano no meio.** Cada etapa: gera → audita (auto) → auto-fix loop → segue. Humano só vê o final + relatório.
- **Auto-fix com limite + não-bloqueia.** Cada gate que falha dispara correção e re-valida (máx 3 tentativas). Se não convergir, NÃO trava o pipeline — registra "⚠ não convergiu, revisar" no relatório final e segue. Nada ruim é escondido.
- **Commit/push do conteúdo: sim** (fluxo de criação). Deploy: não.
- **Português brasileiro editorial**, voz analítica.
- **Idempotência defensiva:** se o artigo destino já existe e está `contentLocked: true`, ABORTAR (não sobrescrever trabalho travado). Se existe sem lock, perguntar/abortar conforme contexto.

## Pipeline (full-auto, etapa por etapa)

### Etapa 0 — Pré-flight (auto; aborta cedo se faltar)
1. Git pull no repo de trabalho (evita estado stale; painel/Bárbara commitam em paralelo).
2. Parse args. Valida `targetSite`/`sourceSite` (`[a-z0-9-]+`).
3. Lê o `.mdx` fonte → extrai: produtos (ASIN, name, image, imageAlt, badge, **rating**, schemaPrice, store), keyword, keywordPlural, listHeading, category, e a estrutura de H2/H3 do `guideContent`. **`rating` é a nota editorial do fonte e DEVE ser preservada — o clone biblia-only NÃO regenera nota, e sem ela o artigo/página perde a fonte de estrela (caso real escritoriocasa 2026-06-11: clones saíram com 0 rating).**
4. Valida bíblias de TODOS os ASINs: existem em `docs/biblias-v2/{ASIN}.json` + `pontosFortes` não-vazio + `angulosConversao` não-vazio. Falta qualquer → ABORTA listando.
5. Valida páginas de produto no destino (`sites/{target}/src/content/products/{slug}.mdx`): se existem, links hub-and-spoke do guide resolvem + servem de anti-dup intra-site. Se faltam, AVISA (guide cai pra Amazon /dp/ no fallback) — não bloqueia.
6. Lê `affiliateTag` do destino (`sites/{target}/src/config.ts`). Vazia = links crus; preenchida = `?tag=...`.
7. Confere que o artigo destino NÃO existe travado.

### Etapa 1 — Reviews (gerar + auditar + auto-fix)
1. **1.0 Lineup + shuffle**: ordem = top-3 do fonte FIXOS + posições 4+ embaralhadas com shuffle determinístico (seed = hash do target+source+slug; FNV-1a + xorshift32, igual `agent-edit.ts`). Badge **e `rating`** viajam COM o produto (mapeados por ASIN). Top-3 fixo garante "Melhor Escolha" na posição 1.
2. **1.1 Geração**: N sub-agents Opus paralelos (levas de até 10). Cada um gera os campos do review-no-artigo (subtitle, shortDescription, pros, cons, specs, fullReview de 4 parágrafos) — **biblia-only** (vê só a bíblia do produto + a página individual do mesmo produto no destino como "ângulo a NÃO repetir" / anti-dup intra-site). NUNCA vê o texto do fonte (`biblia-only`). Régua = `artigo-review-criar` (destilação categoria D, voz analítica, sem travessão, texto-puro, links tag-aware, chavões por nicho, health YMYL, hard caps). H2 labels dos 4 parágrafos parafraseados.
3. **1.2 Gate mecânico** (auto): por review — travessão (0), links Amazon (formato + contagem 2-3, tag-aware), texto-puro (subtitle/shortDescription/specs.value sem HTML), 4 parágrafos com prefixos, tamanhos, **voz-comprador com LISTA AMPLA** (incluir "de forma recorrente", bare "recorrente", "aparece como", "parte das opiniões/observações", "citado/citados de forma"; caso real: "de forma recorrente" escapou de uma lista curta). Falha → auto-fix (sub-agent corrige só o campo) → re-valida (máx 3x).
4. **1.3 Anti-dup intra-site** (auto): cada review ≠ página individual do mesmo produto (jaccard de sentenças). Acima do limite → auto-fix (reescreve trecho divergindo) → re-valida.
5. **1.4 Audit cross-produto** (`artigo-reviews-auditar`): tone-clone, redundância, incoerência, claim-vs-lineup, buyer-refs, etc. → AUTO-APLICA as correções propostas → re-audita (máx 3x). Não-convergido → flag no relatório.

### Etapa 2 — Guide (gerar + auditar + auto-fix)
1. **2.1** Invoca `artigo-guia-escrever` passando a estrutura de H2/H3 do guide do fonte como **mapa de tópicos** (referência estrutural, NÃO copia frases). Prosa do zero.
   - **OBRIGATÓRIO: passar uma TABELA CANÔNICA de specs por marca/produto** (cafeína/dose, glúten, ativos-chave, preço) extraída das bíblias, e instruir "use SÓ esta tabela pras seções de marca/cafeína". **Caso real: sem a tabela o sub-agent FEZ BRAND-SWAP** (descreveu o Dux com specs do True Source: 200mg/L-teanina; e o 3VS como "contém glúten" quando é sem glúten). Auto-check pós-geração: nenhuma spec de uma marca aparece em outra; produto X "para iniciantes" não é o de maior cafeína.
2. **2.2 Audit guide** (auto): 5 H2 obrigatórios na ordem, 6000-25000 chars, allowlist HTML, **2-5 links internos hub-and-spoke OBRIGATÓRIOS** (resolvem pras páginas reais; caso real: o regen do guide ZEROU os links por ler "opcional" — exigir 2-5), sem travessão, densidade de negrito, chavões por nicho. Falha → auto-fix → re-valida (máx 3x).

### Etapa 3 — Intro + Meta (gerar + auditar + auto-fix)
1. **3.1** Invoca `artigo-intro-escrever` + `artigo-meta-escrever`.
2. **3.2 Audit** (auto): intro (§1 pergunta + keyword bold, §final keywordPlural bold + `. ✅`, 2-3 parágrafos, 300-800 chars, sem heading, sem travessão, sem marca específica, exatos 2 bolds) + meta (50-160 chars, single-line, sem travessão, sem aspas internas). Falha → auto-fix → re-valida.

### Etapa 4 — Audit do artigo inteiro (auto-fix)
1. **4.1** Invoca `artigo-auditar` (30 categorias editoriais + 4 estruturais hasIntro/hasGuide/productCount≥3/hasMeta + `readyToLock`). Issues críticos → auto-fix dirigido → re-audita (máx 3x). Não-convergido → flag.

### Etapa 5 — Duplicata vs fonte (comparar + reescrever + re-scan em loop)
1. **5.1** Roda o comparador `compare-cross-site.py` (nesta pasta) entre o artigo destino e o fonte: frases idênticas (≥6 palavras, HTML→espaço), near-dup (jaccard ≥0.8 e ≥0.6), overlap 5-grama e 8-grama, specs label↔value.
2. **5.2** Trechos acima do limite (exatas > 0 OU jaccard ≥0.8) → sub-agent reescreve SÓ aqueles trechos divergindo (sem mudar fato) → **5.3 re-scan** → loop até limpo OU máx 3 rodadas. Sobra → flag no relatório.
   - Nota honesta: frases factuais rígidas (contraindicação/dose/alérgeno) convergem por serem boilerplate de indústria; o foco da reescrita é o conteúdo AUTORAL (subtitles, prosa), não bula que aparece igual no mundo todo.

### Etapa 6 — Home + infra + build + commit
1. **6.1 categorySlug**: força sem acento (`pré-treino` → `pre-treino`) no frontmatter (bug conhecido do `/categoria/`).
2. **6.2 Home (se HOME=yes)**: configura homeReviewSlug:
   - `sites/{target}/src/config.ts`: adiciona/ajusta `homeReviewSlug: '{slug}'`.
   - `sites/{target}/src/pages/index.astro`: troca `IndexPage` → `HomeAsReviewPage`.
   - (`[slug].astro` do template1 já filtra o home-slug via siteConfig.homeReviewSlug — confirmar.)
   - Registra `melhorpretreino`/target em `TEMPLATE_KNOWN_DIVERGENCES` (index.astro) no server.ts + scripts/template-diff.ts se o site virar homeReviewSlug e ainda não estiver lá (senão o chip "Template" acusa falso drift).
3. **6.3 Build** (`pnpm --filter {target} build`): gate Zod/YAML. Falha → conserta (YAML do .mdx) → rebuild.
4. **6.4 Commit + push** (`--no-verify`, hook bloqueia .mdx direto) + **regen `gen.ts`** (senão painel mostra "0 artigos") + **restart do dev server** do target (senão getStaticPaths fica stale e a rota nova dá 404 — armadilha conhecida).
5. **6.5 Verifica infra** (auto): build OK + dev serve a home + `/{slug}/` 200 + painel lista o artigo.

### Relatório final (o que o humano lê)
- Artigo criado: site/slug, título, N produtos (ordem final + badges), home sim/não.
- Por etapa: o que cada audit pegou, o que foi auto-corrigido, **o que NÃO convergiu** (⚠ revisar).
- Comparação vs fonte: frases idênticas, near-dup, overlap, specs — antes e depois da reescrita.
- Build/infra: status. Commit hash.
- Próximo passo: revisar a home renderizada; se aprovar, travar (contentLocked) + deploy (ambos manuais).

## Prompt do sub-agent de review (Etapa 1.1) — resumo

Inline, ~mesma régua de `artigo-review-criar`, com:
- Inputs: target, slug-artigo, ASIN, badge, affiliateTag (crua se vazia), bíblia (conteúdo), página individual do produto no destino (texto, p/ anti-dup intra-site).
- Gera os 6 campos do review-no-artigo. `biblia-only`: fonte factual = SÓ a bíblia. NUNCA citar/ver o artigo fonte.
- Régua dura: sem travessão; voz analítica (zero comprador/opiniões/relatos/elogiado/quem comprou); destilação categoria D; campos texto-puro sem HTML; pros/cons `<strong>Título</strong>: texto`; fullReview 4 parágrafos com prefixos parafraseados + 2-3 links Amazon tag-aware; sem termos técnico-industriais; sem "declarado/conforme/segundo o fabricante" como muleta; health YMYL; hard caps.
- Retorna SÓ JSON com os 6 campos (a skill-mãe monta o .mdx).

## Shuffle determinístico (Etapa 1.0)

```
top3 = sourceAsins[0:3]   # fixos
resto = seededShuffle(sourceAsins[3:], seed=FNV1a(target+source+slug))
finalOrder = top3 + resto
```
Badge **e `rating`** seguem o ASIN (cada produto mantém seu badge e sua nota editorial do fonte → preserva a estrela). Top-3 fixo mantém "Melhor Escolha" na posição 1 (régua do projeto).

## Montagem do .mdx (Etapa 1 fim)

Assembler determinístico (Python: json.dumps para campos single-line — subtitle/shortDescription/specs; **block scalar `|` para fullReview e guideContent**). Frontmatter: title (override ou derivado), description (placeholder até a meta), keyword, keywordPlural, listHeading, category, categorySlug (sem acento), homeReviewSlug (se HOME), **publishDate (OBRIGATÓRIO — o schema Zod exige; sem ele o build falha com `publishDate: Invalid date`)**, + products[] na ordem final (base do fonte + 6 campos gerados). guideContent vazio nesse momento (Etapa 2 preenche via skill). **guideContent E cada `fullReview` de produto DEVEM ser gravados como YAML BLOCK SCALAR (`|`), NUNCA json.dumps/aspas** — guideContent com corpo indentado 2 espaços; cada `fullReview` indentado 6 espaços (um `<p>` por linha). O `parseArticle` (article-parser.ts) que alimenta o editor de artigo SÓ reconhece `fullReview` em block scalar `|`: em aspas o campo fica INVISÍVEL no editor (loga "campo será invisível no editor") e o painel reporta "FALTAM N reviews" mesmo com o conteúdo presente — o site renderiza normal (Astro yaml-parseia os dois). Caso real 2026-05-29: gravei os 11 fullReviews via json.dumps → painel mostrou "FALTAM 11 REVIEWS"; corrigido convertendo pra block scalar. (subtitle/shortDescription seguem single-line quoted; pros/cons/specs como listas — esses o parseArticle aceita.) **AUTO-CHECK pós-assembler (OBRIGATÓRIO, antes da Etapa 2)**: `grep -c '^    fullReview: |' {target}.mdx` deve == nº de produtos E `grep -c '^    fullReview: "' {target}.mdx` deve == 0. Se houver fullReview em aspas, o assembler errou — converter pra block scalar (um `<p>` por linha, indent 6) antes de prosseguir. Body intro vazio (Etapa 3). SEM contentLocked.

## Comparador cross-site

`compare-cross-site.py` (nesta pasta): recebe dois `.mdx` de artigo (destino + fonte), extrai texto (products[].subtitle/shortDescription/pros/cons/fullReview + guideContent + body intro), strip HTML→espaço, e reporta: frases idênticas (≥6 palavras), pares near-dup (jaccard ≥0.8 e ≥0.6), overlap 5/8-grama, specs label↔value divergentes. Saída estruturada pra a Etapa 5 decidir o que reescrever.

## Armadilhas (todas já mordidas neste projeto — embutir)

1. **Dev server stale**: criar conteúdo com o dev rodando deixa `getStaticPaths` stale → rota nova dá 404 no preview. SEMPRE restart do dev do target no fim (Etapa 6.4). HMR/touch NÃO resolve (data-store cache).
2. **gen.ts não auto-regenera** em commit cru de .mdx → painel mostra "0 artigos/páginas". SEMPRE `bun docs/painel/gen.ts` no fim.
3. **categorySlug com acento** (`pré-treino`) → `/categoria/` 404. Forçar sem acento.
4. **Astro data-store cache** (`node_modules/.astro`): se mudar schema, `rm -rf` antes do build. Pro dev, restart re-scaneia content.
5. **tar do macOS** inclui AppleDouble `._*` → quebra parsing. Usar `COPYFILE_DISABLE=1` + ignorar `._` no consumidor.
6. **Ownership na VPS**: I/O como `melhorserum-painel` (git como root quebra). cp/edit via `sudo -u melhorserum-painel` ou `chown -R` no fim.
7. **Pre-commit hook** bloqueia `.mdx` direto em content/reviews → commit com `--no-verify` (caminho oficial das skills).
8. **homeReviewSlug + chip Template**: site homeReviewSlug precisa estar em `TEMPLATE_KNOWN_DIVERGENCES` (index.astro) do server.ts E do template-diff.ts, senão o chip acusa falso drift.
9. **Voz-comprador residual**: geração biblia-only ainda vaza "opiniões/relatos/elogiado/quem comprou/segundo o fabricante" — o gate 1.2 + 1.4 pegam; auto-fix destila.

## Limites de segurança (a skill NUNCA faz)

- Deploy (`cf-deploy*`) — aprovação humana explícita.
- `contentLocked: true` — fica editável.
- Preencher `affiliateTag` — fica como está (regra: tag é das últimas coisas).
- Tocar em outros sites ou no template1.

## Disciplina de release

Skill nasce no project repo. Só vai pro marketplace (`marcelohaz/afiliados-skills`) DEPOIS de validada num run real (1º artigo). Padrão: fazer + validar → release.
