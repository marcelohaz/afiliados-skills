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
- `TITLE=` (opcional): título do artigo destino. **REGRA DURA: o título SEMPRE segue o padrão-assinatura do SITE-DESTINO, MESMO quando `TITLE=` é passado.** A clone NUNCA grava o `TITLE=` ao pé da letra (causa-raiz da reincidência 2026-06-14: passaram o `TITLE` do FONTE em P1 e a clone gravou idêntico no destino, que é P2). Fluxo obrigatório:
  1. **Inferir o padrão do destino**: ler 2-3 títulos de artigos JÁ EXISTENTES em `sites/{target}/src/content/reviews/*.mdx` → descobrir qual padrão-assinatura é o do site (P1 `{keyword}: as {N} melhores (Atualizado 2026)` · P2 `As {N} {keywordPlural} (Guia 2026)` · P3 `{keyword}: {N} opções para comprar (Guia Completo)` · P4 — mapa na memória `afiliados.seo.titulos-artigo-3-padroes-anti-dup.md`). NÃO chutar: o padrão é o que os irmãos do PRÓPRIO site usam.
  2. **Ler os títulos dos IRMÃOS cross-site** (mesmo slug nos outros sites) pra garantir divergência.
  3. **Gerar/normalizar**:
     - `TITLE` omitido → gera no padrão do destino (lead = campo `keyword`, sem forçar "Melhor", número N obrigatório, ≤60 chars, tag-assinatura do site).
     - `TITLE` passado → trata como **HINT, não literal**. Só usa se JÁ estiver no padrão do destino E divergir de todos os irmãos. Se for o título da FONTE/de um irmão ou estiver em outro padrão, **DESCARTA e regera** no padrão do destino, avisando no relatório.
  4. **HARD GATE** (rodado na **Etapa 0 passo 8**, ao decidir o título, ANTES do assembler; re-conferido na Etapa 6 antes do build): o título final (a) bate o regex do padrão-assinatura do destino E (b) é diferente do de TODOS os irmãos (normalizar caixa/acentos + comparar). Falhou qualquer um → regera. Causa-raiz dos 21 títulos idênticos (auditoria 2026-06-13) + reincidência via `TITLE` explícito (2026-06-14): a clone não validava o título contra o padrão do destino.
- `HOME=` (opcional, default `no`): se `yes`, configura o artigo como home do site (homeReviewSlug).
- `MODE=` (opcional, default `biblia-only`): `biblia-only` (texto 100% da bíblia, zero leakage do fonte) ou `hybrid` (top-3 da bíblia, 4+ pode considerar o fonte). **Default e recomendado: biblia-only.**

Slug do artigo destino = mesmo slug do fonte (ex: `melhor-pre-treino`), salvo override futuro.

## O que esta skill É (e não é)

É o **orquestrador full-auto** de clone de artigo. Análogo de `pagina-produto-criar-em-massa`, mas pra artigo inteiro.

- **Reusa** as skills-peça (`artigo-review-criar` régua, `artigo-intro-escrever`, `artigo-guia-escrever`, `artigo-meta-escrever`, `artigo-reviews-auditar`, `artigo-auditar`) — NÃO reimplementa régua editorial (evita drift; paridade com `agent-prompts.json`). **Princípio único (v1.54.0): a clone APONTA pra régua, nunca a RE-ESCREVE.** Guide/intro/meta/audits são INVOCADOS via Skill tool (loop principal, sequencial). Os reviews (Etapa 1.1) são N sub-agents PARALELOS e sub-agent não chama Skill tool → cada um LÊ `artigo-review-criar/SKILL.md` direto. Resumo inline de régua = proibido (era a fonte do drift: subtitle desatualizado, voz-comprador vazada, "Para quem é" repetitivo).
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
8. **Decide o TÍTULO do destino AGORA (antes do assembler da Etapa 1)** — aplica a regra `TITLE=` do topo: (a) lê 2-3 títulos de `sites/{target}/src/content/reviews/*.mdx` pra inferir o padrão-assinatura do PRÓPRIO site (P1/P2/P3/P4); (b) lê os títulos dos IRMÃOS cross-site (mesmo slug nos outros sites); (c) se `TITLE=` foi passado, só aceita se JÁ estiver no padrão do destino E divergir dos irmãos, senão DESCARTA; (d) gera/normaliza no padrão do destino (lead = campo `keyword`, sem forçar "Melhor", número N, ≤60 chars, tag-assinatura do site); (e) **HARD GATE**: o título escolhido bate o regex do padrão-assinatura do destino E é ≠ do de TODOS os irmãos (normaliza caixa/acentos antes de comparar). Falhou → regera. Guarda esse título pro assembler usar; a Etapa 6 só re-confere (backstop).

### Etapa 1 — Reviews (gerar + auditar + auto-fix)
1. **1.0 Lineup + shuffle**: ordem = top-3 do fonte FIXOS + posições 4+ embaralhadas com shuffle determinístico (seed = hash do target+source+slug; FNV-1a + xorshift32, igual `agent-edit.ts`). Badge **e `rating`** viajam COM o produto (mapeados por ASIN). Top-3 fixo garante "Melhor Escolha" na posição 1.
   - **GATE DE BADGE — TODO produto leva etiqueta (HARD GATE):** a convenção da rede é que **cada produto do comparativo tem badge** (ex.: melhor-impressora-hp e melhor-impressora-tanque-de-tinta = 7 produtos / 7 badges). Como o badge viaja por ASIN, **buraco no fonte vira buraco no destino** (causa-raiz 2026-06-14: o fonte sublimática tinha badge só nos 2 primeiros → o clone propagou L3250/L1250 SEM etiqueta nos 2 sites). Regra: os 2 primeiros mantêm os de ranking ("Melhor Escolha"/"Boa Alternativa"); **toda posição sem badge recebe um badge DESCRITIVO curto** derivado do ângulo/categoria do produto (ex.: "Multifuncional Adaptável", "Mais Barata", "Laser Monocromática", "Fotográfica", "Frente e Verso Automático", "Boa e Barata"). Badge é **texto livre**: renderiza com a cor padrão (`#1a56db`) via fallback de `getBadgeLabel`/`getBadgeColor`, **sem precisar registrar no `packages/ui/src/utils/amazon.ts`** (registro só pra cor custom, ex.: cinza de "Fora de Linha"). **AUTO-CHECK pós-lineup (OBRIGATÓRIO):** `nº de produtos com badge == nº de produtos`. Se faltar qualquer um, atribuir antes de seguir. Esse mesmo invariante é re-conferido na Etapa 4 (`artigo-auditar` critério `badge-ausente`).
2. **1.1 Geração**: N sub-agents Opus paralelos (levas de até 10). Cada um gera os campos do review-no-artigo (subtitle, shortDescription, pros, cons, specs, fullReview de 4 parágrafos) — **biblia-only** (vê só a bíblia do produto + a página individual do mesmo produto no destino como "ângulo a NÃO repetir" / anti-dup intra-site). NUNCA vê o texto do fonte (`biblia-only`).
   - **⚠️ RÉGUA = FONTE ÚNICA, NÃO RESUMO (régua v1.54.0).** O prompt de cada sub-agent **manda LER `.claude/skills/artigo-review-criar/SKILL.md` INTEIRA + `docs/painel/_data/chavoes-por-nicho.json` (bloco do nicho + `_genericos`) e APLICAR a régua dela na geração** — NÃO um resumo destilado inline. Sub-agent do Agent tool não consegue invocar a Skill tool (skills rodam no loop principal, e aqui são N agents PARALELOS), por isso ele LÊ o arquivo canônico em vez de invocar. Isso elimina o DRIFT: subtitle (híbrido fluindo crit.22), "Para quem é" (variar abertura + cap "ocupa o papel ≤2"), shortDescription benefício-first, voz-comprador (lista AMPLA categoria D), jargão dev (SKU/ASIN/datasheet), concordância PT-BR e capitalização passam a vir SEMPRE da skill viva, sem o resumo da clone ficar pra trás quando a `artigo-review-criar` evolui. A clone só acrescenta os **deltas dela** (ver "Prompt do sub-agent de review" abaixo): biblia-only, anti-dup vs página do destino, retornar JSON.
   - Os 4 parágrafos do fullReview usam os rótulos canônicos LITERAIS (`Para quem é:` / `Por que gostamos:` / `Pontos de atenção:` / `Resumo:`), NUNCA parafraseados — o audit (regra `review`) exige os literais e o anti-dup do clone já remove esses rótulos antes de medir overlap, então parafrasear só quebra (canon Marcelo 2026-06-14).
3. **1.2 Gate mecânico** (auto): por review — travessão (0), **ponto-e-vírgula `;` (0 na prosa, detecção entity-aware: ignora `&amp;`/`&#..;` e a querystring de href; régua 2026-06-20)**, links Amazon (formato + contagem 2-3, tag-aware), texto-puro (subtitle/shortDescription/specs.value sem HTML), 4 parágrafos com prefixos, tamanhos, **voz-comprador com LISTA AMPLA** (incluir "de forma recorrente", bare "recorrente", "aparece como", "parte das opiniões/observações", "citado/citados de forma"; caso real: "de forma recorrente" escapou de uma lista curta). Falha → auto-fix (sub-agent corrige só o campo) → re-valida (máx 3x).
4. **1.3 Anti-dup intra-site** (auto): cada review ≠ página individual do mesmo produto (jaccard de sentenças). Acima do limite → auto-fix (reescreve trecho divergindo) → re-valida.
5. **1.4 Audit cross-produto** (`artigo-reviews-auditar`): tone-clone, redundância, incoerência, claim-vs-lineup, buyer-refs, etc. → AUTO-APLICA as correções propostas → re-audita (máx 3x). Não-convergido → flag no relatório.

### Etapa 2 — Guide (gerar + auditar + auto-fix)
1. **2.1 INVOCAR DE VERDADE** `artigo-guia-escrever` **via Skill tool** (`Skill(skill="afiliados-skills:artigo-guia-escrever", args="{target}/{slug}")`), passando a estrutura de H2/H3 do guide do fonte como **mapa de tópicos** (referência estrutural, NÃO copia frases). Prosa do zero.
   - **⚠️ INVOCAR ≠ INLINE (régua v1.54.0).** "Invoca" significa CHAMAR a Skill tool, NÃO escrever um sub-agent/Python que re-implementa o guia. A skill viva já carrega a régua COMPLETA dela (health-YMYL, voz-eximir, Amazon-zero nas seções educativas, âncora=keyword + slug REAL + home via `/`, FAQ H2 literal "Perguntas Frequentes", densidade de negrito, chavões por nicho). Re-implementar inline = re-introduzir o drift que esta skill existe pra evitar. Incidente real 2026-06-24: o clone inlinou guide/intro/meta e perdeu o anti-clone intra-site da intro + checks YMYL do guide.
   - **OBRIGATÓRIO: passar uma TABELA CANÔNICA de specs por marca/produto** (cafeína/dose, glúten, ativos-chave, preço) extraída das bíblias, e instruir "use SÓ esta tabela pras seções de marca/cafeína". **Caso real: sem a tabela o sub-agent FEZ BRAND-SWAP** (descreveu o Dux com specs do True Source: 200mg/L-teanina; e o 3VS como "contém glúten" quando é sem glúten). Auto-check pós-geração: nenhuma spec de uma marca aparece em outra; produto X "para iniciantes" não é o de maior cafeína.
2. **2.2 Confirmar que a skill rodou** (NÃO re-listar a régua dela): a `artigo-guia-escrever` já aplicou + auto-validou a régua completa dela ao gravar. Aqui o gate só confirma o ESSENCIAL ESTRUTURAL que a clone tem que garantir: (a) `guideContent` não-vazio e gravado, (b) 5 H2 obrigatórios presentes, (c) **2-5 links internos hub-and-spoke** resolvendo pras páginas reais do destino (caso real: regen ZEROU os links por ler "opcional"). Os demais critérios editoriais (YMYL, voz, âncoras, FAQ literal, negrito, chavões) são responsabilidade da skill invocada — se ela rodou de verdade, já passaram. Se a clone tiver inlinado em vez de invocar, RE-INVOQUE a skill. Algum essencial falhar → re-rodar a skill ou auto-fix dirigido → re-valida (máx 3x).

### Etapa 3 — Intro + Meta (gerar + auditar + auto-fix)
1. **3.1 INVOCAR DE VERDADE** `artigo-intro-escrever` + `artigo-meta-escrever` **via Skill tool** (`Skill(skill="afiliados-skills:artigo-intro-escrever", ...)` e idem meta), NÃO inline.
   - **⚠️ A intro carrega o ANTI-CLONE INTRA-SITE** (a skill lê as intros IRMÃS do mesmo site e garante zero sequências de ≥6 palavras iguais). Esse check só acontece se a skill for INVOCADA — inline o clone não vê as intros irmãs e gera abertura colada (incidente das 3 intros idênticas no melhorimpressora). A meta carrega benefício-first + divergência cross-site. Invocar de verdade herda os dois.
2. **3.2 Confirmar que as skills rodaram** (NÃO re-listar a régua): só o ESSENCIAL ESTRUTURAL — intro gravada (2-3 parágrafos, §1 com keyword bold + §final com keywordPlural bold `. ✅`, exatos 2 bolds, sem heading/travessão/marca) e meta gravada (50-160 chars, single-line). Anti-clone intra-site da intro e benefício-first da meta são da skill invocada. Inlinou em vez de invocar → RE-INVOQUE. Falha → re-rodar a skill ou auto-fix → re-valida.

### Etapa 4 — Audit do artigo inteiro (auto-fix)
1. **4.1** Invoca `artigo-auditar` (30 categorias editoriais + 4 estruturais hasIntro/hasGuide/productCount≥3/hasMeta + `readyToLock`). Issues críticos → auto-fix dirigido → re-audita (máx 3x). Não-convergido → flag.

### Etapa 5 — Duplicata vs fonte (comparar + reescrever + re-scan em loop)
1. **5.1** Roda o comparador `compare-cross-site.py` (nesta pasta) entre o artigo destino e o fonte: frases idênticas (≥6 palavras, HTML→espaço), near-dup (jaccard ≥0.8 e ≥0.6), overlap 5-grama e 8-grama, specs label↔value.
2. **5.2** Trechos acima do limite (exatas > 0 OU jaccard ≥0.8) → sub-agent reescreve SÓ aqueles trechos divergindo (sem mudar fato) → **5.3 re-scan** → loop até limpo OU máx 3 rodadas. Sobra → flag no relatório.
   - Nota honesta: frases factuais rígidas (contraindicação/dose/alérgeno) convergem por serem boilerplate de indústria; o foco da reescrita é o conteúdo AUTORAL (subtitles, prosa), não bula que aparece igual no mundo todo.
3. **5.4 RE-GATE mecânico dos campos reescritos (OBRIGATÓRIO, régua v1.54.0):** a reescrita anti-dup é o ponto de MAIOR risco de re-introduzir defeito mecânico (concordância PT-BR quebrada, capitalização errada, travessão/`;` que voltou, voz-comprador que vazou na nova frase, rótulo canônico do fullReview alterado). Após CADA rodada de reescrita que tocou um campo, re-rodar o **gate mecânico da Etapa 1.2** SÓ nos campos mexidos (travessão=0, `;`=0 entity-aware, links Amazon 2-3 tag-aware, texto-puro, 4 parágrafos com rótulos LITERAIS, voz-comprador lista ampla, concordância/capitalização). Falhou → corrigir antes de fechar o loop. NÃO fechar a Etapa 5 com campo reescrito que regrediu no gate 1.2.

### Etapa 6 — Home + infra + build + commit
1. **6.1 Frontmatter final**: (a) **categorySlug** força sem acento (`pré-treino` → `pre-treino`, bug conhecido do `/categoria/`); (b) **backstop do título** — re-confere que o `title` gravado bate o regex do padrão-assinatura do destino E diverge de TODOS os irmãos cross-site (a Etapa 0 passo 8 já decidiu/validou; aqui é só a rede de segurança caso algo tenha sobrescrito o título no meio do pipeline). Falhou → regera no padrão do destino antes de buildar.
2. **6.2 Home (se HOME=yes)**: configura homeReviewSlug:
   - `sites/{target}/src/config.ts`: adiciona/ajusta `homeReviewSlug: '{slug}'`.
   - `sites/{target}/src/pages/index.astro`: troca `IndexPage` → `HomeAsReviewPage`.
   - (`[slug].astro` do template1 já filtra o home-slug via siteConfig.homeReviewSlug — confirmar.)
   - Registra `melhorpretreino`/target em `TEMPLATE_KNOWN_DIVERGENCES` (index.astro) no server.ts + scripts/template-diff.ts se o site virar homeReviewSlug e ainda não estiver lá (senão o chip "Template" acusa falso drift).
3. **6.3 Build** (`pnpm --filter {target} build`): gate Zod/YAML. Falha → conserta (YAML do .mdx) → rebuild.
3.5. **6.3.5 FAQ-shuffle anti-footprint (OBRIGATÓRIO se há irmão na keyword)**: se o artigo clonado tem irmão(s) na MESMA keyword em outro(s) site(s) da rede (quase sempre o caso num clone, já que a fonte é um irmão), rodar `bun scripts/faq-shuffle.ts {target}/{slug} --apply` ANTES do commit. Determinístico/idempotente (função pura por seed), só reordena a FAQ, não muda redação. NÃO é opcional nem "deixa pro batch depois" — faz parte do fechamento do clone (canon Marcelo 2026-06-24: "já era pra ter feito, nem precisa perguntar"). Rebuildar após o shuffle. Ver [[feedback_aplicar_fix_deterministico_seguro_sem_pedir]].
4. **6.4 Commit + push** (`--no-verify`, hook bloqueia .mdx direto) + **regen `gen.ts`** (senão painel mostra "0 artigos") + **restart do dev server** do target (senão getStaticPaths fica stale e a rota nova dá 404 — armadilha conhecida).
5. **6.5 Verifica infra** (auto): build OK + dev serve a home + `/{slug}/` 200 + painel lista o artigo.

### Relatório final (o que o humano lê)
- Artigo criado: site/slug, título, N produtos (ordem final + badges), home sim/não.
- Por etapa: o que cada audit pegou, o que foi auto-corrigido, **o que NÃO convergiu** (⚠ revisar).
- Comparação vs fonte: frases idênticas, near-dup, overlap, specs — antes e depois da reescrita.
- Build/infra: status. Commit hash. FAQ-shuffle aplicada (Etapa 6.3.5).
- Próximo passo: revisar a home renderizada; se aprovar, travar (contentLocked) + deploy (ambos manuais).

## Prompt do sub-agent de review (Etapa 1.1) — LÊ a régua canônica, não resume

**A régua NÃO é re-escrita aqui — o sub-agent LÊ a skill `artigo-review-criar` viva.** Resumo inline drifta toda vez que a `artigo-review-criar` evolui (era a causa-raiz de o clone gerar subtitle desatualizado, voz-comprador vazada, "Para quem é" repetitivo, jargão dev). Em vez disso, o prompt do sub-agent é:

```
Você vai gerar os 6 campos do review-no-artigo de UM produto, em modo biblia-only.

PASSO 1 — LEIA a régua canônica (NÃO improvise, NÃO use resumo de memória):
- Read `.claude/skills/artigo-review-criar/SKILL.md` (régua INTEIRA: subtitle híbrido fluindo,
  "Para quem é" variar-abertura + cap "ocupa o papel ≤2", shortDescription benefício-first,
  pros/cons formato, fullReview 4 parágrafos com rótulos LITERAIS, voz analítica categoria D,
  sem travessão, sem ";", texto-puro, links tag-aware, health YMYL, hard caps, jargão dev banido).
- Read `docs/painel/_data/chavoes-por-nicho.json` → use `_genericos` + bloco do nicho deste site
  como guard rail (limites ingles/medico/industrial; banidos absolutos: lineup/SKU/ASIN/datasheet).
Aplique ESSA régua na íntegra. Onde este prompt e a SKILL.md divergirem, a SKILL.md ganha
(exceto os DELTAS DO CLONE abaixo, que são adições, não conflitos).

PASSO 2 — Inputs deste produto:
- target, slug-artigo, ASIN, badge, affiliateTag (crua se vazia)
- bíblia (conteúdo de docs/biblias-v2/{ASIN}.json)
- página individual do produto NO DESTINO (texto) — só pra anti-dup intra-site

DELTAS DO CLONE (adições à régua da skill):
- biblia-only: a ÚNICA fonte factual é a bíblia. NUNCA citar nem ver o artigo fonte.
- anti-dup intra-site: o review no artigo deve divergir do texto da página individual do mesmo
  produto no destino (não repetir frases/ângulo).
- subtitle: NÃO inventar ângulo novo; segue a régua de subtitle da skill (a normalização
  keyword-first cross-produto fica pra Etapa 1.4). O ângulo editorial do review é o BADGE.

SAÍDA: retorne SÓ um JSON com os 6 campos (subtitle, shortDescription, pros[], cons[], specs[],
fullReview). A skill-mãe monta o .mdx — não escreva arquivo nem rode git.
```

Se o sub-agent não tiver acesso de leitura à `artigo-review-criar/SKILL.md` (ambiente VPS-only raro), a skill-mãe lê o arquivo e COLA o conteúdo dela no prompt — nunca cair num resumo de memória.

## Shuffle determinístico (Etapa 1.0)

```
top3 = sourceAsins[0:3]   # fixos
resto = seededShuffle(sourceAsins[3:], seed=FNV1a(target+source+slug))
finalOrder = top3 + resto
```
Badge **e `rating`** seguem o ASIN (cada produto mantém seu badge e sua nota editorial do fonte → preserva a estrela). Top-3 fixo mantém "Melhor Escolha" na posição 1 (régua do projeto).

## Montagem do .mdx (Etapa 1 fim)

Assembler determinístico (Python: json.dumps para campos single-line — subtitle/shortDescription/specs; **block scalar `|` para fullReview e guideContent**). Frontmatter: title (SEMPRE no padrão-assinatura do destino — ver regra `TITLE=`; passou o HARD GATE de padrão + divergência cross-site; NUNCA o literal do `TITLE=`/fonte), description (placeholder até a meta), keyword, keywordPlural, listHeading, category, categorySlug (sem acento), homeReviewSlug (se HOME), **publishDate (OBRIGATÓRIO — o schema Zod exige; sem ele o build falha com `publishDate: Invalid date`)**, **featuredImage (og:image/hero do artigo — use uma imagem que EXISTE no destino, ex.: a `image` do 1º produto; sem isso vira 404 social/hero, caso real escritorioecasa sublimatica 2026-06-17)**, + products[] na ordem final (base do fonte + 6 campos gerados). guideContent vazio nesse momento (Etapa 2 preenche via skill).

**⚠️ ORDEM DOS CAMPOS DO PRODUTO — `name` PRIMEIRO (HARD GATE).** Cada item de `products[]` DEVE começar por `- name:` (depois asin, image, ...). O parser do painel (`docs/painel/_lib/loaders.ts`) conta produtos com a regex `^\s*-\s*name:` — se o 1º campo for `asin` (`- asin:`), o painel conta **0 produtos** e mostra `PRODUTOS —` + `STATUS Vazio` mesmo com o artigo perfeito (Astro ignora ordem de campo YAML, então buildava normal e nada parecia errado). Caso real escritoriocasa/melhor-impressora-epson 2026-06-17. Convenção da rede toda = `name` 1º.

**⚠️ `name`, `image` e `imageAlt` VÊM DA PÁGINA DE PRODUTO DO DESTINO, não do fonte (régua v1.54.0).** O filename de imagem é POR-SITE (uns sites usam slug `epson-ecotank-l3250.webp`, outros prefixo legado `impressora-epson-...webp`). Copiar do fonte propaga o caminho/nome do site errado. Regra: pra cada produto, leia `sites/{target}/src/content/products/{slug-destino}.mdx` e use o `name`, `image` E `imageAlt` DELE. `badge`/`rating`/`schemaPrice`/`store` seguem do fonte (são editoriais/comerciais); `name`/`image`/`imageAlt` são re-derivados do destino.
- **`image`**: garante que o arquivo existe no `public/` do destino (senão imagem 404; casos reais escritoriocasa epson + escritorioecasa sublimatica 2026-06-17).
- **`name` (HARD GATE — build-breaker):** o link hub-and-spoke do guide e a resolução `products/{slug}.mdx` usam `slugify(name)`. Se o `name` vier do fonte e slugificar pra um slug que NÃO existe como página no destino, o **build quebra** (`Entry products → {slug} was not found`; caso real guiaesportivo-com 2026-06-24: `Dux Creatina`→`dux-creatina` vs página real `dux-creatina-monohidratada`, 5 produtos quebrados). Usar o `name` EXATO da página de produto do destino garante `slugify(name)` == slug-da-página. Se o produto NÃO tem página no destino (Etapa 0 passo 5 avisou), manter o `name` do fonte mas REGISTRAR no relatório que o link cairá no fallback Amazon /dp/.

**guideContent E cada `fullReview` de produto DEVEM ser gravados como YAML BLOCK SCALAR (`|`), NUNCA json.dumps/aspas** — guideContent: chave `guideContent: |` na coluna 0, corpo indentado 2 espaços; cada `fullReview`: **chave `fullReview: |` indentada 4 espaços (mesmo nível de subtitle/specs/pros/cons), conteúdo (`<p>`) indentado 6 espaços, um `<p>` por linha**. NÃO ponha a chave a 6 espaços (cai no nível dos itens de `cons`/`pros`) → quebra o YAML (`expected <block end>`, build falha); caso real epson 2026-06-17. O `parseArticle` (article-parser.ts) que alimenta o editor de artigo SÓ reconhece `fullReview` em block scalar `|`: em aspas o campo fica INVISÍVEL no editor (loga "campo será invisível no editor") e o painel reporta "FALTAM N reviews" mesmo com o conteúdo presente — o site renderiza normal (Astro yaml-parseia os dois). Caso real 2026-05-29: gravei os 11 fullReviews via json.dumps → painel mostrou "FALTAM 11 REVIEWS"; corrigido convertendo pra block scalar. (subtitle/shortDescription seguem single-line quoted; pros/cons/specs como listas — esses o parseArticle aceita.) **AUTO-CHECK pós-assembler (OBRIGATÓRIO, antes da Etapa 2)** — TODOS devem passar:
- `grep -c '^    fullReview: |' {target}.mdx` == nº de produtos E `grep -c '^    fullReview: "' {target}.mdx` == 0 (block scalar, não aspas; indent 4).
- `grep -c '^  - name:' {target}.mdx` == nº de produtos E `grep -c '^  - asin:' {target}.mdx` == 0 (name-first; senão painel mostra "Vazio").
- YAML parseia + nº de `products` no parse == nº esperado, E a regex do painel bate: `len(re.findall(r'^\s*-\s*name:', products_block, re.M))` == nº de produtos.
- **`name`↔slug do destino (anti build-breaker):** pra CADA produto, `slugify(name)` (com a regra `+`→`-plus`) tem que existir como `sites/{target}/src/content/products/{slug}.mdx` OU o produto está na lista de "sem página no destino" registrada na Etapa 0. Senão o build quebra com `Entry products → {slug} was not found`. Confira: pra cada `name`, `test -f sites/{target}/src/content/products/$(slugify name).mdx`. Falhou e o produto TEM página com outro slug → o `name` ficou do fonte; troque pelo `name` exato da página do destino.
- TODO `image:` e o `featuredImage:` apontam pra arquivo que EXISTE em `sites/{target}/public{path}` (rode `bun scripts/check-broken-images.ts --site {target}` → 0 quebradas). Imagem é do destino, não do fonte.
Qualquer um falhar = assembler errou; conserte antes de prosseguir. Body intro vazio (Etapa 3). SEM contentLocked.

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
