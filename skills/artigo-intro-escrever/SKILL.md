---
name: artigo-intro-escrever
description: Escreve a introdução do artigo (body markdown pós-frontmatter). Aceita URL do painel OU site/slug. Régua: §1 = pergunta com a keyword em bold nas ~5 primeiras palavras; §final = keywordPlural em bold + '. ✅'; 2-3 parágrafos, 300-800 chars; exatos 2 bolds; tom natural (máx 1 coloquialismo); sem critérios técnicos (função do guide), sem travessão, sem marcas/modelos. ANTI-CLONE intra-site: lê as intros irmãs do site antes de gerar (famílias rotativas de abertura/miolo/CTA, zero sequências ≥6 palavras). Também conserta o title quando está stub, sem contagem (N≥3) ou colidindo com irmão cross-site (pool P1-P4, lead=keyword, ≤60 chars). Backup + commit + push + sync VPS.
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

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:generate_intro`. O conteúdo essencial está duplicado abaixo pra autocontenção. **Esta SKILL.md é a fonte viva** desta execução (o `agent-prompts.json` é o espelho do path do painel/API e pode defasar — o projeto roda via Claude Code).

Você é o curador editorial da introdução do artigo. A introdução é o **body markdown que aparece logo depois do frontmatter** do `.mdx`, antes da tabela de produtos (que é renderizada pelo componente `<SlugPage>` do `@afiliados/ui`).

Sua função é gerar **2-3 parágrafos curtos** que estabeleçam o contexto do artigo, atendam a régua SEO (keyword bold §1, keywordPlural bold §final, ✅ no fim), e respeitem as restrições editoriais (sem travessão, sem marcas específicas, linguagem geral, tom conversacional alinhado com os reviews — NÃO registro científico-médico).

A intro **CONTEXTUALIZA + sinaliza o que esperar do artigo**. Não ensina critérios técnicos detalhados (isso é função do `guideContent` H2 "Como escolher" que vem depois). Não usa registro acadêmico nem cita instituições científicas (OMS, FAO, ANVISA, FDA). O leitor que chega aqui ainda está se orientando — a intro abre a porta, não dá aula.

## Pré-requisitos

- O `.mdx` do artigo já existe em `sites/{site}/src/content/reviews/{slug}.mdx`. Se não, abortar com orientação pra criar via painel ("✨ Criar artigo" no site detail → `make-reviews-stub`).
- O artigo tem **pelo menos 1 produto** no lineup (`products: []` vazio = abortar — intro sem ângulo concreto fica vaga).
- Bíblias dos produtos do artigo estão em `docs/biblias-v2/{ASIN}.json`. Se alguma faltar, rodar `bun scripts/sync-biblias-r2.ts --apply` antes (skill avisa e aborta se faltar).
- `affiliateTag` em `sites/{site}/src/config.ts` é conhecida (pode ser string vazia pra sites em construção — intros NÃO PRECISAM ter links Amazon, então tag vazia OK).

## Invariantes

- **Toca em até DOIS lugares: o body do .mdx (intro) E a linha `title:` do frontmatter.** O `title:` é reescrito quando está stub/fora do padrão **OU colide com um irmão** da rede (ver "## Régua do título do artigo" → "Divergência cross-site" abaixo). Todo o resto (description, keyword, keywordPlural, listHeading, products, guideContent) fica intacto.
- **Body é puro markdown.** Verificado: zero artigos do monorepo têm componentes MDX no body — toda a estrutura (TabelaTop, ProductSection, ReviewLayout, etc) é montada pelo `<SlugPage>` via thin-wrapper em `pages/[slug].astro`. Skill nunca insere `<TabelaTop>` ou similar.
- **2 a 3 parágrafos** (obrigatório). Cada parágrafo separado por linha em branco. 4 parágrafos é EXCESSO — intro vira ensaio.
- **300 a 800 chars no total** (todo o body somado). Alvo: 500-700 chars. Antes era 300-1500 e sub-agents miravam 900-1400, tornando a intro cansativa — apertado em 2026-05-26 após feedback "muito longa, muito explicativa".
- **KEYWORD CEDO (v1.31.0, canon Marcelo 2026-06-10)**: o `**{keyword}**` começa dentro das **primeiras ~5 palavras** do §1. A abertura é um verbo de busca curto ("Procurando a", "Precisa de uma", "Quer saber qual a"); TODO o enriquecimento da pergunta (cenário, dor, benefício) vem DEPOIS da keyword, na mesma frase.
- **ANTI-CLONE INTRA-SITE (v1.31.0)**: gerar SÓ depois de ler as intros dos outros artigos do site (passo 6.5). Proibido: qualquer sequência de ≥6 palavras igual a uma intro irmã; repetir a família de abertura/arremate/miolo/CTA já usada no site. Incidente-origem: 3 intros idênticas no melhorimpressora (2026-06-10) porque a skill copiava o exemplo canônico.
- **VOZ NATURAL (canon 2026-08-15, substitui "tom natural v1.31" + "tom conversacional 2026-05-26")**: ver bloco "## Voz natural" abaixo. Em resumo: verbo e substantivo no sentido do dicionário, sem frase-sacada, "para" no texto público, sem molde de abertura/arremate/CTA, no máximo 1 expressão coloquial leve. A intro não pode soar mais formal que os reviews, nem mais "esperta" que eles.
- **NÃO citar instituições científicas** (OMS, FAO, ANVISA, FDA, INMETRO, IFOS). Esse tipo de menção quebra o tom de comparador editorial e vira página de saúde. Se a info importa, ela aparece nos reviews (como feature de produto certificado) ou no guide.
- **NÃO dar recomendações com número** ("X recomenda N mg/dia"). Números OK quando aparecem nos reviews depois (são features dos produtos comparados). Na intro, números viram recomendação acadêmica e quebram o tom.
- **NÃO entrar em critérios técnicos detalhados** que pertencem ao `guideContent` H2 "Como escolher". Listar "três fatores que diferenciam premium de entrada" é função do guia, não da intro. Intro fica em PERFIL DE USO e PANORAMA, sem ensinar a escolher.
- **SEM aviso de saúde na intro** (régua v1.57.0). Mesmo em nicho de suplemento/saúde, a intro NÃO leva "consulte um médico/nutricionista" nem disclaimer YMYL — isso fica 1× no guia (ver `artigo-guia-escrever`). Repetir o aviso na intro + guia + reviews é a ladainha que a `artigo-auditar` (`disclaimer-saude-repetido`) flagra.
- **Bold só em `**markdown**`**, nunca `<b>` ou `<strong>`.
- **Sem travessão (—).** Use vírgula ou ponto.
- **Sem ponto-e-vírgula (;).** (régua 2026-06-20) Tem cara de IA na voz conversacional. Troque por "." (sentença nova), "," (pausa) ou "()". Vale em TODOS os campos. AUTO-CHECK antes de gravar: depois de remover entidades (&amp;, &#..;) e a querystring dos links de afiliado, não pode sobrar ";" no texto.
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
   - **⚠ `_sites_aplicaveis` é o gate do bloco de nicho (canon 2026-08-15):** se o slug do site não está na lista do bloco, **o bloco não vale** e sobra só o `_genericos`. Não force pelo `niche`. Reporte como sugestão de incluir o site no JSON, nunca como defeito do texto.
   - **O `_genericos` vale SEMPRE e é o que mais dispara:** `termos_banidos_absoluto`, `chavoes_estruturais_max` (as 4 variantes de "seleção" têm cap **0**) e `industrial_max` (`declarado` 3, `fabricante` 12). Conte ele antes de qualquer bloco de nicho.

1. **Parse args**: detecta URL vs canônico, extrai `site` e `slug`. Valida `[a-z0-9-]+` em ambos.

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   bash scripts/git-pull-seguro.sh "skill-artigo-intro-escrever-temp"
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

6.5. **Ler as intros IRMÃS do site (ANTI-CLONE — v1.31.0, OBRIGATÓRIO)**: extrair o body de TODOS os outros artigos do site:
   ```bash
   for f in sites/{site}/src/content/reviews/*.mdx; do
     echo "── $(basename $f)"; awk 'BEGIN{c=0} /^---$/{c++; next} c>=2{print}' "$f"
   done
   ```
   Anotar de cada irmã: a ABERTURA (primeiras palavras), a família do MIOLO e o CTA do fecho. A intro nova não pode repetir nenhuma dessas famílias nem qualquer sequência de ≥6 palavras. Foi a ausência deste passo que produziu 3 intros idênticas no melhorimpressora.

7. **Compor contexto pra geração**:
   - Title + description do artigo
   - Keyword (singular, vai pro §1) + KeywordPlural (vai pro §final)
   - Ano atual (`new Date().getFullYear()`)
   - Lista de ASINs (só count + ASINs; NÃO listar nomes na intro)
   - Bíblias completas (pra entender categoria, perfis, ângulos comuns)
   - Instrução opcional (se detectada no prompt do user, passo 1)

8. **Gerar a intro** seguindo a régua editorial (ver seção abaixo). 2-3 parágrafos markdown.

8.5. **Avaliar/arrumar o título** (ver "## Régua do título do artigo" abaixo): primeiro rode a **checagem cross-site** (passo da "Divergência cross-site") — leia os títulos dos artigos IRMÃOS (mesmo slug/keyword em outros sites). Reescreve o `title:` se: (a) está stub/fraco (fora de qualquer padrão), OU (b) **colide com um irmão** (título igual/quase-igual), OU (c) a contagem N envelheceu. Ao reescrever, use o padrão de ASSINATURA deste site (pool P1-P4), lead = campo `keyword` (não forçar "Melhor"), número obrigatório, ≤60 chars. Se já está no padrão do site E não colide com irmão, só atualiza N se mudou. Respeita `contentLocked` (não mexe se travado).

9. **Validar mentalmente** antes de salvar:
   - 300-800 chars total (alvo 500-700)
   - 2-3 parágrafos (separados por linha em branco)
   - §1 contém `?` (pergunta) E `**{keyword}**` bold — e a keyword COMEÇA dentro das primeiras ~5 palavras do §1 (v1.31.0)
   - §final contém `**{keywordPlural}**` bold E termina com `. ✅` ou `! ✅`
   - ANTI-CLONE: zero sequências de ≥6 palavras iguais a qualquer intro irmã (passo 6.5); famílias de abertura/arremate/miolo/CTA inéditas no site
   - VOZ NATURAL: verbo/substantivo no sentido literal, sem frase-sacada, "para" (não "pra"), sem arremate/CTA-molde, máx 1 expressão coloquial leve
   - **Exatamente 2 bolds no body inteiro** (keyword no §1, keywordPlural no §final). NADA mais em bold — sem `**ano**`, sem `**marca**`, sem nenhum outro destaque.
   - Sem travessão `—` nem `–`
   - Sem `<b>` ou `<strong>` (só `**markdown**`)
   - Sem heading de nenhum nível: nem markdown (`# `, `## `, `### `) nem HTML (`<h1>`, `<h2>`, `<h3>`)
   - Sem menção a marca/modelo/ASIN específico (linguagem geral)
   - Se tag preenchida + intro tem links Amazon (raro mas possível): validar `?tag={tag}&linkCode=ogi&th=1&psc=1`
   - **Título** (só se foi reescrito no passo 8.5): **≤60 chars** (corte Google), contém a keyword (case-insensitive) no lead, número N batendo com `products[]`, não colide com irmão, sem travessão, sem ponto final

10. **Backup** ANTES de sobrescrever:
    ```bash
    # raiz do repo — o cwd do Bash reseta pra ~/Documents/Claude em sessão continuada; sem isto o mkdir cria a árvore LÁ (medido 03/09/26)
    cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" && test -f docs/painel/sites-meta.json || { echo "⛔ cwd errado ($(pwd)): rode a partir da raiz do ProjetoAfiliados"; exit 1; }
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
    git commit --only --no-verify -m "feat({site}): intro de {slug} escrita via skill" \
      -m "Co-Authored-By: {modelo da sessão} <noreply@anthropic.com>" \
      -- sites/{site}/src/content/reviews/{slug}.mdx
    git push origin main
    ```
    `--no-verify` é OBRIGATÓRIO: o pre-commit hook roda `audit-article.ts` no artigo staged e bloqueia se houver erros — artigo ainda em construção sempre tem.

13. **Disparar git pull no painel da VPS**:
    ```bash
    bash scripts/painel-vps-pull.sh
    ```
    Falha graciosamente se `.env.painel-skills` não existir.

14. **Reportar no chat**: char count + número de parágrafos + preview da intro inteira (curta o suficiente pra colar) + path do arquivo.

## Régua do título do artigo (v1.21.0, canon 2026-06-04)

Além da intro, a skill **arruma o `title` do frontmatter** quando ele está stub/fora do padrão **ou quando colide com um título irmão** da rede (divergência cross-site — ver subseção abaixo). Motivo: o `make_reviews` cria o title só como "Keyword Capitalizado:" e o "as X melhores em ANO" sempre foi um passo manual que quase nunca era feito, deixando títulos fracos tipo "Melhor impressora epson". Como a intro roda no fim do artigo, é o momento natural de fechar o título com a contagem real de produtos.

### Divergência cross-site (v1.35.0, canon Marcelo 2026-06-13) — ANTI-DUP SERP

**Problema:** a mesma keyword existe em vários sites da rede (SERP-monopoly). Se todos usam o padrão único, saem com `<title>` IDÊNTICO na SERP → Google colapsa duplicados, CTR repetido. Auditoria 2026-06-13: 21 artigos compartilhados, 100% título idêntico.

**Regra (gatilho = COLISÃO, não "fora do padrão"):** antes de gravar o título, **leia os títulos dos artigos IRMÃOS** — mesmo `slug` em outros sites E mesma `keyword`: `Grep -n "^title:|^keyword:" sites/*/src/content/reviews/{slug}.mdx` (se o slug variar entre sites, procure pelo mesmo valor de `keyword`). Se o seu título sair igual a um irmão, **escolha um padrão/tag diferente**. Irmão `contentLocked` mantém o dele → você diverge dele. Na dúvida, mantenha o site estabelecido/forte e diverja o novo.

**Pool de padrões** (todos: lead = campo `keyword`, número N obrigatório, **≤60 chars**):
- **P1** `{Keyword}: as {N} melhores (Atualizado 2026)` — fallback `(2026)` se passar de 60
- **P2** `As {N} {KeywordPlural Title Case} (Guia 2026)`
- **P3** `{Keyword}: {N} opções para comprar` — ` (Guia Completo)` só se couber ≤60
- **P4** `{Keyword}: as {N} melhores de 2026`

Tags (encaixe a que couber, **sem dobrar o ano** — título com "em/de 2026" NÃO leva "(2026)/(Atualizado 2026)" junto): `(Atualizado 2026)`, `(Guia 2026)`, `(Guia Completo)`, `(2026)`, `de 2026`, `em 2026`.

**Lead = campo `keyword`, NÃO forçar "Melhor":** se a keyword é "impressora barata" / "impressora para fotos" (sem "melhor"), o título começa "Impressora Barata" / "Impressora para Fotos", NUNCA "Melhor Impressora Barata". Conferir o campo `keyword` do frontmatter, jamais chutar pelo slug.

**Casos especiais:** keyword de pergunta/marca ("creatina black skull", "qual a melhor creatina") mantém a forma de pergunta ("Creatina Black Skull é Boa?", "Qual a Melhor Creatina?") + tail divergente por site.

**Assinatura por site:** cada site usa um padrão fixo, atribuído pra divergir dos irmãos que dividem a keyword. Mapa vivo na memória `afiliados.seo.titulos-artigo-3-padroes-anti-dup.md` (ex.: melhorimpressora=P1, escritorioecasa=P2, impressoraideal=P3; creatinasaprovadas=P1, melhorcreatina=P2, qualamelhorcreatina=P3, melhoressuplementos=P4). Site novo: pegue um padrão livre no cluster.

### Padrão canônico (P1 = default; ver pool de divergência acima)

O padrão de cada site é o do **pool P1-P4 acima** (P1 `{Keyword}: as {N} melhores (Atualizado 2026)`; a forma `{Keyword}: {os|as} {N} melhores em {ano}` é o **P4**, não o default). Use o padrão-assinatura do SITE (inferido dos títulos já existentes nele); os exemplos abaixo mostram a forma geral, não o P1.

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

### Quando arrumar (gatilho = stub OU colisão — v1.39.0)

Reescreve se: (a) o título está **stub/fraco**, OU (b) **colide com um irmão** (mesmo slug/keyword em outro site com título igual/quase-igual — ver "Divergência cross-site"), OU (c) a **contagem N envelheceu**. Detecção:
- **Stub/fraco (arruma)**: minúsculo, sem ano, sem contagem, ou == keyword cru (ex: "Melhor impressora epson", "Melhor Impressora Custo Benefício").
- **⚠ "Sem contagem" com N≥3 é SEMPRE stub — gatilho OBJETIVO, não inferência (v1.39.0):** se o lineup tem 3+ produtos e **o número N não aparece no título** (teste: `\bN\b`, a contagem real do lineup — NÃO uma lista de substantivos; ver auto-check #6 e o porquê da mudança na v1.103.0), é stub a corrigir **mesmo que o título esteja bem-formado** (Title Case + ano, ex: "Melhor Tablet para Estudar em 2026") **e mesmo que artigos IRMÃOS do site estejam iguais sem contagem**. Irmão sem contagem com N≥3 é **straggler não-corrigido, NÃO assinatura do site** — NUNCA inferir "padrão" a partir de stubs. Contagem só é dispensável com **N<3** (ver Fallback). Caso real (2026-06-22, escritorioecasa/melhor-tablet-para-estudar, N=8): a intro deixou o título sem contagem inferindo que o cluster "para X" (desenho N=7, trabalho N=7, ambos também stubs) era a assinatura. Era armadilha: o gatilho "sem contagem com N≥3" vence qualquer aparência de consistência.
- **Colide com irmão (arruma p/ divergir)**: título idêntico/quase-igual a um irmão → aplica o padrão de assinatura deste site (pool P1-P4). Mesmo que já esteja "no padrão", se colide, troca.
- **N mudou (atualiza)**: se o lineup cresceu/encolheu, atualiza o número (a contagem não pode envelhecer).
- **OK (NÃO toca)**: já no padrão de assinatura do site **com contagem presente** (ou N<3), não colide com irmão, e N certo. "N certo" pressupõe que **a contagem EXISTE** — título sem contagem com N≥3 nunca cai no "OK".

### Fallback N<3 (decisão Marcelo)

Se o lineup tem menos de 3 produtos, "as 2 melhores" soa fraco. Use:
`{Keyword em Title Case} em {ano}` (sem contagem). Ex: "Melhor Impressora Epson em 2026".

### Limite de tamanho — **≤60 chars (corte do Google na SERP)**

Canon Marcelo 2026-06-13: **título não pode passar de ~60 chars** ou o Google corta na SERP. Régua: número SEMPRE presente; depois encaixe a tag que couber (`(Atualizado 2026)` > `(Guia 2026)` > `de 2026` > `(2026)`); se a keyword for longa, use número terso ("10 melhores", "10 opções") e/ou solte a tag. Mínimo ~30 (`artigo-auditar` flagra <30). Contar os chars ANTES de gravar.

### Guard `contentLocked`

Se o artigo está `contentLocked: true`, **NÃO mexe no título** (título é H1 + `<title>` SEO; mudar artigo travado pode quebrar ranking). Avisa o user e segue só com a intro, se ele tiver destravado.

### O que NÃO confundir

- O `title` é DIFERENTE do `listHeading` (H2 da TabelaTop, ex "Quais as melhores impressoras Epson em 2026?"). A skill só mexe no `title`; `listHeading` tem régua própria e fica intacto.
- A keyword e a keywordPlural do frontmatter NÃO mudam — o título deriva da keyword, não a substitui.

### Exemplo antes/depois (melhor-impressora-epson, 9 produtos)

- ❌ `title: "Melhor impressora epson"` (minúsculo, sem contagem, sem ano)
- ✅ `title: "Melhor Impressora Epson: as 9 melhores em 2026"`

## Régua editorial — ESTRUTURA OBRIGATÓRIA

A fórmula é fixa; o RECHEIO de cada slot RODA entre os artigos do site. **Slots: [pergunta com keyword cedo] → [arremate de acolhimento] → [miolo] → [fechamento + CTA]**. A mesma família de recheio NÃO repete em outra intro do mesmo site (por isso o passo 6.5 lê as irmãs antes de gerar).

### §1 — pergunta com a keyword CEDO + arremate opcional (literal)

**Regra dura (v1.31.0, canon Marcelo 2026-06-10): o `**{keyword}**` começa dentro das primeiras ~5 palavras.** Molde:

`[abertura curta de busca] + **{keyword}** + [enriquecimento com intenção de uso]?`

**Aberturas curtas (pool — NÃO repetir a mesma em duas intros do site):**
- `Procurando a **{keyword}**...`
- `Quer saber qual a **{keyword}**...` / `Quer acertar na **{keyword}**...`
- `Precisa de uma **{keyword}**...`
- `Está buscando a **{keyword}**...`
- `Em busca da **{keyword}**...`
- `Cansou de procurar a **{keyword}**...`

**Enriquecimento (DEPOIS da keyword — é ele que diferencia artigos vizinhos):**
- intenção de uso: "...para imprimir, copiar e digitalizar com um aparelho só?"
- cenário concreto: "...para imprimir o trabalho da escola, o boleto e uns documentos de vez em quando?"
- dor da categoria: "...para imprimir à vontade sem medo da conta de cartucho?"
- objeção/custo: "...sem pagar por função que você nunca vai usar?"
- intenção de marca (keyword com marca): "...agora que a marca já está decidida e só falta o modelo?"

❌ **Pergunta SECA proibida como padrão**: "Está em dúvida sobre qual a **{keyword}** em {ano}?" sem enriquecimento — foi este template que clonou 3 intros do melhorimpressora (incidente 2026-06-10).

**Arremate após a pergunta: OPCIONAL, 1 frase curta e literal, sem exclamação obrigatória.** Ex.: "Este comparativo reúne os modelos que valem a pena em {ano}." / "Abaixo estão os modelos que comparamos." Medido em 2026-08-15: 64% das intros da rede fechavam o §1 com "!" e frases-molde ("A gente fez essa conta pra você!" 11×, "Então este comparativo é pra você!" 10×, "Esse comparativo nasceu pra resolver…" 7×) — viraram assinatura. Não use essas nem variações delas.

**SEM mencionar marcas/modelos/ASINs específicos** (exceto marca que faz parte da keyword, ex: "melhor impressora Epson").

### §2 (miolo) — substância concreta, UMA família por site

Escolha uma família AINDA NÃO usada nas intros irmãs (passo 6.5):

1. **Contexto-da-categoria** — o que a categoria mudou/resolve: "o tanque de tinta mudou o custo de imprimir em casa: em vez de trocar cartucho toda hora, você reabastece com garrafas que custam pouco e rendem milhares de páginas."
2. **Cenário-que-não-basta** — o improviso atual falha em situações concretas: "fotografar documento com o celular até resolve, mas tem hora que não basta: uma cópia legível do RG, um contrato digitalizado em boa qualidade, dez páginas pra entregar amanhã."
3. **Quebra-de-objeção** — valida o orçamento/receio do leitor: "mesmo com um orçamento limitado, ainda é possível encontrar modelos eficientes..." / "tem modelo barato que sai caro em um ano de tinta, e modelo mais caro que compensa em poucos meses."
4. **Panorama-da-linha** (keywords de marca) — os modelos parecem iguais e se separam no uso: "um foi pensado pra documento todo dia, outro pra quem copia e digitaliza, outro pra foto."
5. **Tricolon de perfis** — "quem A...; quem B...; e quem C...": PERMITIDO, mas no máximo 1 artigo por site (era o esqueleto repetido em 3+ intros antes da v1.31.0).
6. **Cenário-dor** (estilo impressora-para-fotos) — a cena ruim que motiva a compra. Pode até abrir o §1, DESDE que a pergunta com a keyword cedo venha logo em seguida no mesmo parágrafo.

Regras do miolo: **concreto > genérico** ("rendem milhares de páginas" informa; "são muito econômicas" não). SEM bold. SEM critérios técnicos detalhados, recomendações com número, siglas de instituição (OMS/FAO/ANVISA/FDA), jargão médico ou distinções acadêmicas — isso é função do `guideContent`. Intro **abre a porta**, guide **ensina a escolher**, reviews **comparam**.

### §final — keywordPlural + critérios + CTA

`[ponte] + **{keywordPlural}** de {ano} + [2-3 critérios de comparação] + [CTA convidando]`

**Pontes (varie, sem repetir irmã):** "Para facilitar sua escolha, reunimos..." / "Para ajudar, comparamos..." / "Por isso, colocamos as ... lado a lado" / "Separamos as ..." / "No comparativo abaixo você encontra as ..."

**Critérios**: 2-3, concretos da categoria ("rendimento da tinta, qualidade do scanner e facilidade de uso" / "preço de compra, gasto com tinta e funções extras").

**CTA final: OPCIONAL, 1 frase curta e literal.** Ex.: "Veja abaixo qual serve para o seu uso." Medido em 2026-08-15: 52% das intros da rede terminavam com "Veja/Confira/Descubra qual (combina/encaixa/cabe) no seu…" — virou molde; não use essa forma nem "Dá uma olhada". Se o §final já convida ("reunimos as X de {ano}, comparando A, B e C"), não precisa de CTA.

Termina **OBRIGATORIAMENTE** com `. ✅` ou `! ✅` (pontuação, espaço, emoji, nada depois).

## Exemplos bons — famílias DIFERENTES (régua de FORMA, não texto-fonte)

> ⚠️ **PROIBIDO reusar frases destes exemplos verbatim.** Eles mostram forma e tom; cada intro nova nasce do zero com recheios próprios e família inédita no site. Copiar o "exemplo canônico" antigo foi o que gerou 3 intros idênticas no melhorimpressora (incidente 2026-06-10).

### Exemplo A — multifuncional (CANON DE TOM, aprovado Marcelo 2026-06-10 · família "cenário-que-não-basta")

```
Procurando a **melhor impressora multifuncional** para imprimir, copiar e digitalizar com um aparelho só? Este comparativo reúne os modelos que valem a pena em 2026.

Fotografar documento com o celular funciona em muitos casos, mas não em todos: uma cópia legível do RG, um contrato digitalizado em boa qualidade, dez páginas de apostila para entregar amanhã. A multifuncional faz essas três coisas em um único aparelho e ocupa pouco espaço na mesa.

Para facilitar sua escolha, reunimos as **melhores impressoras multifuncionais** de 2026, comparando rendimento da tinta, qualidade do scanner e facilidade de uso. ✅
```

**Por quê funciona**: keyword na 3ª palavra; o enriquecimento da pergunta ecoa o produto (imprimir/copiar/digitalizar = o 3-em-1); miolo com 3 situações CONCRETAS (RG, contrato, apostila) em frases literais ("faz", "ocupa"), sem exclamação nem CTA-molde. ~600 chars, 3 §, 2 bolds. (Versão revisada em 2026-08-15: a anterior tinha "Então você está no lugar certo!", "até resolve, mas tem hora que não basta", "cobre essas três situações" e "Confira qual faz mais sentido pra sua casa!" — o registro que virou molde na rede.)

### Exemplo B — barata (família "cenário concreto + quebra de objeção")

```
Precisa de uma **impressora barata** para imprimir o trabalho da escola, o boleto e uns documentos de vez em quando? Existem modelos bons por menos de R$ 500, e é isso que comparamos aqui.

Imprimir fora de casa parece barato até a semana em que aparecem dez folhas de uma vez. Quem imprime pouco não precisa de uma impressora cheia de recursos: um modelo simples, que conecta no celular e imprime sem configuração complicada, já atende.

Separamos as **impressoras baratas** de 2026 que valem o que custam, comparando preço, facilidade de instalação e impressão direto do celular. ✅
```

### Exemplo C — Epson (família "intenção de marca + panorama da linha")

```
Quer saber qual a **melhor impressora Epson** agora que a marca já está decidida e só falta o modelo? Comparamos os principais modelos da linha para responder isso.

Dentro da mesma marca, os modelos parecem iguais e servem a usos diferentes: um foi pensado para documento todo dia, outro para quem copia e digitaliza com frequência, outro para foto com cores fiéis. A diferença que mais afeta o gasto, quanto rende cada recarga de tinta, não aparece na etiqueta de preço.

No comparativo abaixo você encontra as **melhores impressoras Epson** de 2026, separadas por uso, rendimento e custo da recarga. ✅
```

### Exemplo D — ômega 3 (BAD vs GOOD pareado, caso real 2026-05-26)

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

**✅ GOOD** (~500c, voz natural, contextual):

```
Qual o **melhor ômega 3** para escolher em 2026? Para quem não come peixe gordo com frequência, o suplemento virou prática comum, especialmente entre quem busca apoio cardiovascular ou cognitivo. Mas o mercado tem opções bem diferentes em concentração, certificação e preço, e nem todo pote vale o que custa.

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

- §1 contém `?` (pergunta) E `**{keyword}**` em bold markdown, com a keyword começando dentro das primeiras ~5 palavras (v1.31.0)
- §final contém `**{keywordPlural}**` em bold markdown E termina com `. ✅` ou `! ✅`
- ANTI-CLONE intra-site: zero sequências de ≥6 palavras iguais a intro irmã; família de abertura/arremate/miolo/CTA inédita no site (v1.31.0)
- Voz natural (canon 2026-08-15): verbo/substantivo no sentido do dicionário, sem frase-sacada, "para" no texto público, sem arremate/CTA-molde, máx 1 expressão coloquial leve, analogia só quando explica
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
- **Nem científico-médico, nem "esperto"**. Escreve como uma pessoa que pesquisou explicando, não como consultor nem como redator tentando ser criativo. A intro não pode soar mais formal que os reviews, nem mais figurada.

### Título (quando reescrito)
- Padrão = o **padrão-assinatura do site** no pool P1-P4 da "Régua do título" (P1 `{Keyword}: as {N} melhores (Atualizado {ano})` é o default; `{Keyword}: {os|as} {N} melhores em {ano}` é o **P4**, não o default; esta linha dizia o contrário até 2026-09-01 e desfazia a divergência entre irmãos). N≥3 obrigatório; com N<3, fallback `{Keyword Title Case} em {ano}`. **Sem ponto final.**
- **≤60 chars** (corte Google); keyword no lead; número N = `products[]`; não colide com título irmão; sem travessão.
- **Reescreve pelos gatilhos de "Quando arrumar"** (stub/fora de qualquer padrão, OU colisão com irmão, OU N envelheceu; sem contagem com N≥3 é sempre stub). Já-no-padrão do site e sem colisão → só atualiza N se o lineup mudou.
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

## Voz natural (régua transversal, canon Marcelo 2026-08-15 — bloco IDÊNTICO nas 5 skills de criação e nos prompts canônicos do painel)

Especialista explicando a um amigo, cumprido com **simplicidade**, não com efeito. Pergunta-teste: *"um amigo que não entende disso entenderia e saberia o que fazer?"* Sem jargão corporativo, sem formalidade institucional, **sem sacada**.

O que faz texto soar como IA não é gíria nem termo técnico: é **palavra comum usada fora do sentido do dicionário** ("resolver a casa", "dar conta da poeira", "transformar a limpeza numa produção", "o aparelho pede tomada", "a conta da potência vem no peso"), quase sempre frase feita do inglês vertida (*make a production, handle, delivers, covers, calls for, the math*). Cada palavra é comum, então lista de termo não pega; a régua é uma **classe**:

1. **Sujeito concreto + verbo no sentido do dicionário.** Aspirador aspira, impressora imprime, bateria dura, produto custa/tem/funciona. Objeto, preço, peso ou potência NÃO "resolvem, dão conta, entregam, seguram, pedem, exigem, aguentam, sustentam, encaram, cobram, juntam, trabalham, cobrem, viram, brilham". Teste: é o sentido em que você usaria a palavra falando com um cliente?
2. **Substantivo literal.** Nada de "a conta", "degrau", "piso", "porta de entrada", "pacote", "proposta", "produção", "remanejo", "trunfo", "fôlego" como figura. Diga o que é (preço, faixa de preço, o mais barato, conjunto de recursos).
3. **Sem frase-sacada.** Nada de "não é X: é Y", "o que X é Y", "é aí que…", fecho com dois-pontos que "revela". Dois-pontos só para explicação ou lista.
4. **Repita a palavra certa.** "Aspira" 3× é normal. Chavão é frase-molde repetida, não palavra exata. **Nunca troque a palavra certa por sinônimo figurado para "variar"** (limpar → "resolver a casa" → "dar conta" é exatamente o defeito).
5. **"para", não "pra"**, no texto público.
6. **Frase de até ~30 palavras.** ", então" e ", o que" no máximo 1 por parágrafo.
7. **Fecho de parágrafo = frase curta de fato ou recomendação direta** ("é a melhor opção para casa pequena"), sem rótulo de público engatado ("é a escolha de quem", "faz sentido para quem", "é o que resolve").
8. **Ênfase só com dado.** Sem "de verdade", "bastante", "com folga", "de sobra", "justamente", "honesto/a" como muleta.
9. **Continuam valendo (v1.32):** rótulo de categoria só se existe no varejo (teste-da-Amazon: "máquina de trabalho"→"impressora de escritório", "preço de custo-benefício"→"preço justo"); elipse de categoria LIBERADA ("a barata", "a laser", "as de tanque"); sem meta-SEO (não comente a busca do leitor); sem jargão financeiro/burocrático ("desembolso"→"preço"); sem atribuição elíptica ("conta da Epson"→número direto); sem antropomorfismo ("não se cansa", "no batente"); no máximo 1 expressão coloquial leve, e só se for a forma mais direta.

10. **Teto mecânico da mesma régua**: `docs/painel/_data/chavoes-por-nicho.json` → `_genericos.naturalidade_max` (daqui 2, pede 3, resolve 3, entrega 3, de verdade 1, trunfo/fôlego 1…) e `naturalidade_banidos` (0). A auditoria conta por artigo (página = metade); escreva já dentro do teto.

**Antes de gravar, releia cada parágrafo: "uma pessoa escreveria assim?"** O trecho que soa esperto, simplifique.

| ❌ Como saiu (casos reais) | ✓ Como uma pessoa escreve |
|---|---|
| a impressora resolve o mês inteiro com um kit | um kit de tinta imprime cerca de 4.500 páginas |
| sem transformar a troca de tinta numa produção | sem muito esforço |
| a conta do rendimento vem no preço do kit | o rendimento alto tem um custo: o kit é caro |
| a creatina pede coqueteleira | a creatina dissolve melhor com coqueteleira |
| Se não tem, ela é a que resolve. | Se não tem, ela é a melhor opção. |
| O tanque não se cansa. | O tanque de tinta rende o mesmo até o fim. |

⚠️ **Os exemplos são de outra categoria de propósito e NÃO podem ser reusados.** Se a frase que você escreveu está nesta tabela (ou nos exemplos de shortDescription), reescreva com o fato do SEU produto. Caso real (melhoraspirador, 15/08): a linha "em casa grande você ainda troca de tomada algumas vezes", que era exemplo aqui, saiu copiada em 5 lugares do artigo — 11 sub-agents lendo o mesmo exemplo convergem nele.

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
| `Pra a maioria/primeira` | `Para a maioria/primeira` |

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
| "diferencial central" | dizer o fato ("a fórmula não tem aditivos"); NÃO "o grande ponto é" (virou molde) |
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

### 7. Não terminar com `. ✅` ou `! ✅`
Padrão: pontuação (ponto ou exclamação) + espaço + emoji. `...pra sua casa ou trabalho! ✅` ✓ · `...selecionadas abaixo. ✅` ✓ · `...abaixo ✅` ❌ (sem pontuação).

### 8. Esquecer de gerar keywordPlural se ausente no frontmatter
Se o frontmatter não tem `keywordPlural`, abortar e avisar — NÃO inventar plural (gera erro). User precisa preencher manualmente (ou rodar `artigo-review-criar` que gera keywordPlural junto).

### 9. Body markdown com componente MDX
Por hábito de outras frameworks, IA pode tentar emitir `<TabelaTop products={data.products} />`. Proibido. Verificado: zero artigos do repo têm componente MDX no body. Toda a estrutura é montada pelo `<SlugPage>` do `@afiliados/ui`.

### 10. Edit tool com old_string ambíguo
Se a intro velha for muito curta (ex: `[a escrever: ...]`), o `old_string` é único. Mas se for uma intro velha de 1500 chars, partes dela podem repetir outros trechos do .mdx (raro mas possível). Mitigação: incluir 1-2 linhas de contexto antes (ex: `---\n\n[body]`) no `old_string` pra forçar match no body especificamente.

### 11. Clonar o exemplo da skill (incidente 2026-06-10)
O maior bug histórico desta skill: o "exemplo canônico" único virou texto-fonte e 3 intros do melhorimpressora saíram idênticas (só a keyword trocada). Exemplo é régua de FORMA. Se a intro gerada compartilha qualquer frase de ≥6 palavras com um exemplo desta skill OU com uma intro irmã do site — reescreva antes de gravar.

### 12. Keyword tarde no §1
"Cansou de gastar com cartucho e está procurando a **{keyword}**..." enterra a keyword na 8ª palavra. Inverta: abertura curta + keyword + enriquecimento ("Procurando a **{keyword}** para imprimir sem medo da conta de cartucho?").

### 13. Empilhar coloquialismos e palavras fora do sentido (feedback Marcelo 2026-06-10 e 2026-08-15)
"Quebra um galho", "pra ontem", "gambiarra", "faz-tudo" na MESMA intro = personagem forçado. E o defeito mais comum não é gíria: é palavra comum em sentido figurado ("dar conta da poeira", "sem transformar a limpeza numa produção", "resolver a casa"). Ver "## Voz natural". Trocas: "quebra um galho"→"funciona" · "pra ontem"→"para amanhã" · "máquina parruda"→"modelo mais avançado" · "sem drama"→"sem complicação" · "dar conta da poeira"→"aspirar a poeira" · "numa produção"→"em muito esforço".

## Sincronização painel ↔ skill ↔ prompt canônico

**Fonte da verdade é ESTA `SKILL.md`** (canon 2026-08-15, ver "Régua comum das auditoras" em `docs/PADROES.md`). O `docs/painel/_data/agent-prompts.json` → `ops.generate_intro` é **espelho** usado pelos botões do painel (pode defasar; ao mudar régua aqui, refletir lá no mesmo commit quando a mudança afeta o output). Os endpoints legados `generate-*/rewrite-*/create` do painel foram removidos em 2026-05-27; `agent-config.html` virou `editorial.html`. Listas, regex e tetos vivem em `chavoes-por-nicho.json` — cite a chave, não copie a tabela.


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

### Auto-check final antes de gravar (v1.31.0 — específico de INTRO)

```python
import re, glob

novo = BODY_NOVO        # intro gerada (texto após o 2º ---)
TITLE = TITLE_FINAL     # título que vai ser gravado (reescrito ou o atual)
PRODUCTS = FRONTMATTER_PRODUCTS  # lista products[] do frontmatter

# 1) KEYWORD CEDO: o primeiro ** começa nas primeiras ~5 palavras
prefixo = novo.strip().split('**')[0].strip()
assert len(prefixo.split()) <= 5, f"keyword tarde; abertura: '{prefixo}'"

# 2) Exatos 2 bolds (= 4 marcadores **)
assert novo.count('**') == 4, f"{novo.count('**')//2} bolds (régua: exatos 2)"

# 3) Fecho: pontuação + espaço + ✅
assert re.search(r'[.!] ✅\s*$', novo.strip()), "fecho deve ser '. ✅' ou '! ✅'"

# 4) ANTI-CLONE: nenhuma sequência de 6 palavras igual a intro irmã
def frases6(t):
    t = re.sub(r'\*\*|<[^>]+>', ' ', t).lower()
    p = re.findall(r'[a-zà-ÿ0-9]+', t)
    return {' '.join(p[i:i+6]) for i in range(max(0, len(p)-5))}
minhas = frases6(novo)
for f in glob.glob(f'sites/{SITE}/src/content/reviews/*.mdx'):
    if f.endswith(f'{SLUG}.mdx'): continue
    corpo = open(f).read().split('---', 2)[2]
    rep = minhas & frases6(corpo)
    assert not rep, f"CLONE com {f}: {sorted(rep)[:3]}"

# 5) Duplicação contígua (bug-class a72e7d9) + minúscula após ponto
assert not re.search(r'([a-zA-ZÀ-ÿ\s]{8,40})\1', novo), "duplicação contígua"
# '\. [a-z]' fora de URL → capitalizar

# 6) TÍTULO: sem contagem com N≥3 é stub (v1.39.0). v1.103.0: o teste é "o Nº DE PRODUTOS aparece
# no título" (regex antigo r'\d+\s+([Mm]elhores|opções)' era mais estreito que a regra e reprovava
# 8 formas legítimas + tinha bug de caixa; passavam 258/333, agora 331). Falso-negativo aceito:
# keyword com o mesmo dígito de N ("Ômega 3", "iPad 11") passa sem contagem — erra pro lado de NÃO mexer.
N = len(PRODUCTS)  # produtos do lineup
if N >= 3 and not re.search(rf'\b{N}\b', TITLE):
    raise AssertionError(f"título sem a contagem N={N} (>=3) = stub; reescreva com a contagem. "
                         f"NÃO tratar irmão sem contagem como assinatura: {TITLE!r}")
```

Checagem de olho (não-greppável): família de abertura/arremate/miolo/CTA inédita vs as irmãs lidas no passo 6.5 · voz natural (verbo/substantivo no sentido literal, sem sacada, "para", sem molde de arremate/CTA) · nenhuma frase reusada dos Exemplos A-D · 300-800 chars · 2-3 §.

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), validação fica editorial — eu (modelo) sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial (3 bolds em vez de 2, char count em 810, etc). Mitigação: contar bolds (`**`) e chars depois de gerar e ajustar antes de aplicar.

## Registrar desvio de execução (obrigatório quando houver)

SE você (a) executou diferente do que esta skill manda, (b) **criou um passo que ela
não tem**, (c) achou a régua ambígua/contraditória, ou (d) topou com bug numa
ferramenta dela — ENTÃO registre antes de fechar:

```bash
bun scripts/skill-log.ts note <skill> <desvio|ambiguidade|bug|inventou-passo> "<o que fugiu e por quê>" [--ctx=site/slug] [--alvo=<etapa>]
```

Execução limpa **não gera linha** — vazio é dado. O que se lê depois é
`bun scripts/skill-log.ts report`, que conta por skill e destaca o que já bateu
mais de uma vez. Sem `--alvo` a nota cai em `geral` e sai do detector de
reincidência, então **nomeie a etapa** quando ela existir.
