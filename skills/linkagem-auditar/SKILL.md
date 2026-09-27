---
name: linkagem-auditar
description: "Audita e melhora a linkagem interna de um site inteiro: roda os scripts de grafo, validade e slug × histórico do GSC, julga o placement, propõe links novos para órfãos e sublinkados, aplica direto o conserto mecânico e pede aprovação para o julgamento. Use quando o pedido for auditar, consertar ou melhorar os links internos de um site (slug do site ou URL da página de linkagem do painel). Não é auditoria de um artigo só (artigo-auditar) nem escrita de guia (artigo-guia-escrever). Fecha com commit, push e painel-vps-pull."
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida — botão roxo "📋 Copiar skill" da página linkagem):
- `https://painel.melhorserum.com.br/linkagem-melhorimpressora.html`
- Extrai `site` via regex `linkagem-([a-z0-9-]+)\.html`

**B) Slug do site direto**:
- `melhorimpressora`

Detecção: começa com `https://` → caminho A. Senão → caminho B (valida `[a-z0-9-]+`).

# Auditar e melhorar a linkagem interna do site inteiro (propor → aprovar)

Você é o auditor-editor da **linkagem interna do site todo**. Diferente das skills por-artigo (`artigo-auditar`, `artigo-guia-auditar`), esta enxerga o **grafo cross-artigo** (quem linka quem, balanço, órfãos), roda a régua determinística em todos os artigos de uma vez, e **aplica fixes no estilo propor→aprovar** — igual `artigo-guia-auditar` faz pro guide de um artigo, mas aqui pro grafo do site inteiro.

## Divisão de trabalho (NÃO reimplementar o que os scripts já fazem)

| Camada | Quem faz | Esta skill |
|---|---|---|
| Régua SEO determinística (grafo, âncora, slug, Conclusão, home-errado, hub-and-spoke) | `scripts/audit-linkagem.ts --json` | **roda e lê** |
| Validade (tag Amazon, linkCode, 404 interno, redirect externo) | `scripts/audit-links.ts --json` | **roda e lê** |
| Slug × histórico do GSC (a URL do artigo é a que tem o histórico?) | `scripts/audit-slugs.ts --json` | **roda e lê** |
| Julgamento: placement *genuinamente* contextual? links NOVOS naturais? | **só LLM** | **agrega valor + propõe** |
| Aplicar os fixes aprovados (Edit cirúrgico no guideContent; no portado sem guia, no fullReview) | **a skill** | **aplica on-approval** |

Não reescreva extração de link nem grafo — os scripts já fazem. O valor da skill é (1) **consolidar** as duas saídas, (2) a **camada de julgamento** (placement + oportunidades), e (3) **aplicar** o que o user aprovar.

## Pré-requisitos

- Site existe em `sites/{site}/` com `src/content/reviews/*.mdx`.
- `scripts/audit-linkagem.ts`, `scripts/audit-links.ts` e `scripts/audit-slugs.ts` existem (núcleo determinístico).
- Pro `audit-slugs.ts`: `~/.gsc-token.json` + `.env.gsc` no `shared-scripts`. Sem credencial ele sai com `ok:false` e o motivo — **nunca com lista vazia**, que pareceria "está tudo certo".
- `bun` no PATH.
- Artigos a editar NÃO travados (`contentLocked: true` → pular esse artigo e avisar; nunca editar travado sem destrave explícito). **Exceção: artigo portado do WordPress (`portadoDe`) com a autorização do Marcelo nesta execução** — ver "Portados do WordPress".

## Invariantes

- **APLICA O ÓBVIO, PROPÕE O JULGAMENTO (canon Marcelo 2026-07-24, alinha com `biblia-auditar`).** Fix **determinístico de direção única** → **APLICA DIRETO** (sem esperar) e marca ✅ CORRIGIDO no relatório: `link-quebrado` (404 → slug REAL ou remover `<a>` mantendo texto), `link-home-errado` (`/{homeReviewSlug}/`→`/`), `anchor-nao-keyword` e `anchor-produto-sem-nome` (+ a reconciliação OBRIGATÓRIA de concordância artigo↔âncora, canon 2026-06-23), `anchor-frase-quebrada` **de level=error** (indefinido/qualificador + superlativo → artigo definido com contração; artigo no número errado → acertar o artigo, ou o plural da keyword no portado; "melhor" repetido fora do link → tirar o de fora: direção única, ver passo 10). **Julgamento** → **propor→aprovar** (imprime diffs e espera aprovação granular: "aplica tudo" / "aplica 1,3" / "aplica canon" / "rejeita 2"): **link NOVO** (adicionar), `peer-link-na-conclusao` (mover placement), `linkagem-excesso` (qual link cortar), `anchor-frase-quebrada` **de level=warn** (o "na/no/em", o "qual" e o "qualquer" pedem escolha editorial: nomear o destino, pôr o artigo, usar plural ou reescrever), **REMOVER link fora de contexto**. Na dúvida, trate como julgamento (proponha). O relatório com TODOS os fixes (óbvios já aplicados + julgamento proposto) sai sempre.
- **EDIÇÃO CIRÚRGICA, nunca rewrite.** Só toca no trecho do `guideContent` (ou do `fullReview`, no portado sem guia) com o fix aprovado (um `<a>`/`<p>` por vez). Resto do `.mdx` byte-a-byte intacto. Preserva o block scalar `|` (NUNCA parseYaml/stringify do frontmatter — sempre `Edit` no trecho-alvo).
- **NÃO inventa.** Findings determinísticos vêm dos scripts (verbatim). Os de julgamento (placement/oportunidade) citam o trecho real do guideContent. Link novo só com âncora = keyword real do destino + href = slug REAL (nunca derivado do keyword).
- **Escopo fechado.** CONSERTAR (404/home-errado/âncora/Conclusão/excesso>4) + ADICIONAR links novos contextuais (incl. reforçar órfão/sublinkado). `slug-vs-keyword` é só INFO (convenção, não se conserta — ver Critérios), mas `slug-sem-historico` do `audit-slugs.ts` é acionável e vai por propor→aprovar. **NÃO faz hub-and-spoke** (linkar produto órfão é decisão editorial à parte). **NÃO mexe em tag Amazon** (isso é `scripts/fill-affiliate-tag.ts`).
- **Régua de linkagem canônica** (igual artigo-guia-escrever/auditar): âncora de peer = keyword do destino (singular preferido); âncora de produto = nome completo COM marca; href = slug REAL; peer/home links contextuais e NUNCA na Conclusão (produto/Amazon na Conclusão = OK); home linkada via `href="/"` (nunca `/{homeReviewSlug}/`).
- **A FRASE em volta da âncora TEM que fechar (canon Marcelo 2026-07-31).** A keyword nomeia um **GUIA** ("melhor whey protein"), não um produto do mundo. Encaixá-la como se fosse coisa concreta produz frase que ninguém fala: *"combinar com **um melhor pré-treino**"*. Medição na rede: **64 ocorrências publicadas em 19 sites**, todas passando verde nos checks antigos — o defeito nasce de OBEDECER a régua de âncora=keyword sem olhar as palavras anteriores. O `audit-linkagem.ts` emite `anchor-frase-quebrada`.
  - **Por que o singular é o alvo (razão de SEO, não estética):** é a forma que as pessoas **buscam**, e a âncora do link interno reforça essa keyword. Trocar pro plural por conveniência gramatical joga fora esse sinal. Então, quando o singular não couber na frase, resolva **nesta ordem**:
    1. **Artigo definido** — `um melhor pré-treino` → `o melhor pré-treino`, **contraindo** a preposição que vier antes: `a um`→`ao`, `a uma`→`à`, `de um`→`do`, `em um`→`no`. Resolve a maioria e mantém o singular.
    2. **Moldura de destino** — `no guia de melhor pré-treino`, `o comparativo de melhor pré-treino`. Também mantém o singular, e é imune a concordância (a keyword vira complemento, sem artigo antes).
    3. **Plural** — `os melhores pré-treinos`. O script aceita (compara com `keyword` **ou** `keywordPlural`). Válvula de escape, não primeira opção (no portado com âncora que já estava no plural, é a primeira: ver "Portados do WordPress", item 3). ⚠ 9 artigos da rede não têm `keywordPlural` preenchido; nesses, não está disponível.
    4. **Reescrever a frase.** Último recurso.
  - **Nunca** deixar `um/uma/bom/boa/outro/outra/qualquer` + superlativo.
  - ⚠ **Só vale pra âncora com superlativo.** Em keyword sem "melhor" (`impressora barata`), o indefinido é CORRETO: *"vale ver uma impressora barata"*. O script já restringe.
- **Padrão de frase de encaminhamento (canon Marcelo 2026-07-31).** As frases que o Marcelo aprovou têm quatro traços — use como molde ao ADICIONAR link ou ao reescrever um quebrado:
  1. **Nomeia o destino pelo que ele é**: a palavra `guia`/`artigo`/`comparativo` aparece. Não finge que a keyword é produto.
  2. **Diz pra quem o link é** — abre segmentando o leitor (recorte, perfil, objetivo, estágio da decisão), pra ele saber se aquilo é pra ele antes de clicar. É o que separa encaminhamento útil de link protocolar.
  3. **Verbo de leitura, não de compra**: veja, vale comparar, encontra mais, tem guia próprio.
  4. **A frase existe PRA fazer o encaminhamento** — não é uma frase sobre outro assunto que ganhou link enfiado no meio.

  Exemplos canônicos (reais, aprovados 2026-07-31):
  > "Pra ver só os isolados, veja o guia de **melhor whey protein isolado**."
  > "Esse cenário de produtividade tem guia próprio no **melhor tablet para trabalho**."
  > "Se o seu objetivo é o rendimento na academia, vale comparar com o nosso guia de **melhor pré-treino** antes de decidir."
  > "Quem já pensa na marca encontra mais no guia de **melhor impressora hp**."

  ⚠ **"tem guia próprio no {keyword}" só fecha com keyword masculina** ("no melhor tablet"). Com keyword feminina sai "no melhor cadeira presidente", erro que a régua de âncora não pega porque a âncora está certa (melhorcadeiradeescritorio, 26/09/2026). "Encontra mais no guia de {keyword}" e "veja o guia de {keyword}" não dependem de gênero: use uma delas quando a keyword for feminina.

  A moldura é o **padrão recomendado, não obrigatório**: link integrado ao texto continua válido quando passa nos checks de frase (ex.: *"vale olhar os melhores Kindles"*). O que não passa é a keyword enfiada como objeto de verbo no singular.
- **Régua de QUANTIDADE (canon Marcelo 2026-06-09): 2 mínimo · ~3 ideal · 4 máximo** peers DISTINTOS de saída, sempre **contextuais e naturais** (nunca decorativos). Não linkar o mesmo peer 2× no mesmo artigo. O **HUB** (artigo-cabeça: `homeReviewSlug` ou frontmatter `pillar: true`) é **isento do teto de 4** — ele linka todos os filhos (hub-and-spoke ideal). O script emite `linkagem-fraca` (<2) e `linkagem-excesso` (>4 não-hub); a régua "~3 ideal" é alvo de julgamento (mire 3 ao ADICIONAR), não um flag por-artigo.

⚠️ **O piso de 2 NÃO vence o "encaminhamento útil" (canon 2026-08-10) — vale sobretudo aqui, porque esta skill ADICIONA links.** Antes de propor um link novo pra resolver `linkagem-fraca`/`orfao`, aplique o **"Teste da decisão"** da `artigo-guia-escrever` (vale para todo link entre artigos, novo ou existente): **escolha entre dois**, com o parágrafo comparando as duas coisas; **compra conjunta** daquele par específico, nunca "quem combina com outros suplementos" ou "quem monta a rotina"; ou **um antes do outro**, só quando a ordem é verdadeira para o produto. E o link fica num parágrafo que trata do destino ou da decisão, não colado no fim de um parágrafo de outro assunto. Se você precisa **construir o cenário** em que o leitor iria pro outro artigo, o cenário não existe e o link é protocolar. Nesse caso **NÃO proponha o link**: deixe o artigo abaixo do piso e registre o `linkagem-fraca` como exceção justificada no relatório.

**PRÉ-CONDIÇÃO MECÂNICA — sem ela a exceção NÃO existe:** o artigo tem **ZERO peers da mesma `category`, ou já linka todos eles**. Conte antes de aceitar: `category` dos outros `.mdx` de `reviews/` do site, e quais deles o artigo já linka. Havendo irmão da mesma categoria **ainda não linkado**, **o piso de 2 vale integral** e você DEVE propor o link para ele. A exceção cobre o artigo que é o primeiro da categoria dele num site que já tem outras, e o artigo cuja categoria já está toda linkada (produtosanalisados, 27/09/2026: os 2 fones do site já se linkavam, e o piso levou o fone de academia a linkar a bicicleta ergométrica "onde o cabo incomoda menos"; na execução seguinte eu propus fone de corrida → esteira pelo mesmo motivo). Isso é deliberado — exceção que é só julgamento vira atalho, e foi exatamente assim que a régua qualitativa perdeu pro piso numérico.

Não é hipótese: em 2026-08-10 o `compraguia/melhor-caixa-de-som-jbl` (artigo de áudio num site de impressora/tablet/Kindle, **0 peers da mesma categoria**) ganhou 2 links de tablet só pra bater o piso, e eles foram removidos depois. **Esta skill é justamente a que os traria de volta.** E não adianta cortar por categoria: dos 942 links peer da rede em 08/2026, 229 eram cross-categoria e 227 passavam no teste da decisão como ele era lido então (34 E-reader↔Tablet, 174 entre suplementos, 17 de fitness). A leitura por destino de 27/09 mostrou que parte dos links entre suplementos é frase genérica, então o corte é pelo teste lido no parágrafo, não pela categoria. Ver "Desempate" na `artigo-guia-escrever`.
- **Sem travessão.** Português brasileiro editorial.

## Portados do WordPress (`portadoDe`, canon Marcelo 2026-09-22)

O port copia o texto do WordPress sem reescrever e grava `contentLocked: true` em todo artigo (skill `site-portar-wordpress`). Com a regra de sempre (travado → pular), esta skill não mudava nada nos 6 primeiros sites portados: os 112 artigos estavam travados, e no cozinhaideal os links novos iriam para os 3 únicos artigos sem trava (2 de air fryer e 1 de aspirador), escolhidos por estarem livres e não pelo assunto. Decisão do Marcelo: os sites têm backlinks, o link juice precisa fluir entre os artigos, e a hora de mudar é agora, antes de o artigo rankear.

1. **Autorização por execução.** Se o site tem artigo com `portadoDe` e `contentLocked: true`, pergunte **uma vez, no início** (antes do relatório): *"N artigos portados travados. Autoriza editar só os links e as palavras coladas neles, com a trava continuando ligada?"*. Vale também o pedido que já diz isso ("pode editar os portados"). Sem o sim, segue a regra de sempre: pular e rerrotear (régua D). Travado **sem** `portadoDe` segue a regra de sempre mesmo com a autorização.
2. **Com a autorização:**
   - A trava fica: não troque `contentLocked`. O CLAUDE.md manda destravar antes de editar travado e registra esta exceção: destravar e travar de novo no mesmo commit dá o mesmo arquivo, e esquecer de travar de novo é o risco. O que a regra exige de fato é a confirmação do item 1. O diff do commit mostra só o link e as palavras em volta.
   - A régua D (fonte travada → procurar outra) não vale para os portados: a fonte é a de melhor assunto.
   - **Mudança mínima.** Mexe só no `<a>` e nas palavras coladas nele (artigo, preposição, "melhor" repetido). O texto do WordPress fica como está: nada de reescrever o parágrafo para "melhorar".
3. **Âncora que já está no plural → `keywordPlural`**, e não o singular (a ordem geral da régua põe o singular primeiro). O plural é aceito pelo script, mantém o artigo e a preposição do texto, e evita a troca que muda o sentido: "compatíveis com a maioria dos melhores roteadores" viraria "a maioria **do melhor roteador** WiFi". Os 112 têm `keywordPlural` preenchido.
4. **Artigo sem guia** (`guideContent` vazio; 5 dos 112 em 22/09/2026, 4 deles no melhoresparacasa). O texto é a análise de cada produto (`products[].fullReview`), onde o próprio WordPress já punha link entre artigos. Link novo que SAI desse artigo vai no `fullReview` do produto mais ligado ao destino, no fim de um parágrafo, com a mesma régua de frase. O extrator conta esses links no grafo; o `link-fora-do-guia` (info) que o script emite aqui é esperado, e a passada de placement do passo 5 vale para eles como vale para o guia. Backup do `.mdx` inteiro, não do guia. Não escreva guia para resolver linkagem: isso é a `artigo-guia-escrever`, decisão à parte.
5. **Artigo-cabeça da categoria com `linkagem-excesso`** (no melhortech, o "melhores celulares" com os 10 celulares do site): proponha `pillar: true` no frontmatter, numa linha nova logo depois de `categorySlug:`, em vez de cortar link. Cortar tira um link de entrada de outro artigo sem ganho. Artigo que não é cabeça segue a regra geral (cortar o menos contextual, com a guarda de grafo do passo 5).
6. **Categoria do WordPress é uma por artigo** (cozinhaideal: 20 categorias em 31 artigos, 15 sozinhos na sua). A pré-condição mecânica da exceção ao piso de 2 conta pela `category`, então libera esses 15. Não pare nela: o teste da decisão vale pelo assunto, e liquidificador, mixer e processador respondem à mesma bifurcação.
7. **Frase de encaminhamento sem link.** O texto do WordPress tem frases que já mandam para outro artigo e ficaram sem `<a>`: o WordPress linkava o próprio artigo por engano ("Quer conhecer o celular motorola com a melhor câmera?" apontava para o artigo do Motorola), linkava artigo que não existe e o port tirou o link mantendo o texto ("confira nosso artigo: melhor notebook custo benefício"), ou nunca teve link. Procure essas frases antes de escrever frase nova: são o lugar mais natural e a mudança fica no `<a>`. Quando o artigo citado não existe, trocar o nome dele pelo de um artigo que existe é julgamento; proponha. No compraguia (24/09/2026) foram 4 dos 28 links novos. Busca: frases com "confira/acesse/nosso artigo/nosso guia" que contêm a keyword de outro artigo do site e não têm `<a>`.

No relatório, a linha **Portados** diz quantos são e se a edição foi autorizada. Sem autorização, os consertos deles saem como "bloqueado (travado)".

## Artigo que já rankeia (`rankeando[]`, canon Marcelo 2026-09-24)

Pedido do Marcelo ao planejar o port do compraguia: melhorar a linkagem "com cuidado para não mudar muito os artigos que já estão rankeando bem". O critério é medido: o `audit-slugs.ts --json` (passo 4.6) devolve `rankeando[]`, os artigos com clique nos últimos 28 dias na própria slug, somando a linhagem. No compraguia, em 24/09/2026, eram os 24 artigos do site (de 1 a 131 cliques).

Num artigo de `rankeando[]`:

1. **Aplica direto, como sempre:** `link-quebrado`, `link-home-errado`, `link-rede` e `anchor-frase-quebrada` de level=error. São defeitos visíveis, e o conserto mexe só no link e nas palavras coladas nele.
2. **Com aprovação:** **1 link novo por execução** saindo do artigo, numa frase que já fala do assunto do destino, mexendo só no `<a>` e nas palavras coladas nele. Frase nova inteira só se nenhuma frase servir, e ela é a mudança da execução. Link novo que ENTRA no artigo não mexe nele (a edição é na fonte) e segue a régua de sempre.
3. **Só relata, não aplica:** `anchor-nao-keyword`, `anchor-produto-sem-nome`, `peer-link-na-conclusao`, `linkagem-excesso`, remoção de link fora de contexto e `anchor-frase-quebrada` de level=warn. Saem no relatório como "não aplicado: artigo rankeando (N cliques em 28 dias)". Aplica só se o Marcelo pedir para aquele artigo.
4. **Sem medição, todo artigo conta como rankeando.** `audit-slugs.ts` com `ok:false` ou `inconclusivo` → aplique esta seção ao site inteiro e diga no relatório. Mexer de menos por falta de dado é reversível; mexer demais num artigo posicionado pode custar a posição.

**Site que recebeu artigos portados** (herdeiro, cenário A da `site-portar-wordpress`): a linkagem vai em dois tempos.
- **No port:** só os portados. Links entre eles e deles para os artigos que o site já tinha. Os artigos do site não ganham link novo nesta execução.
- **3 a 4 semanas depois**, se os artigos do site seguirem estáveis no Search Console: os links dos artigos do site para os portados, com a regra acima (1 por artigo).

Motivo: se o site cair depois do port, dá para saber se foi o port ou a mudança nos artigos que já rankeavam. Com as duas mudanças juntas, não dá para separar.

No relatório, a linha **Rankeando** diz quantos artigos são (e de onde veio o número) e quantos consertos ficaram só no relatório por causa desta regra.

## Fluxo

1. **Parse args**: detecta URL vs slug, extrai `site`. Valida `[a-z0-9-]+`.

2. **Git pull antes de ler** (evita estado stale — o painel VPS commita writes):
   ```bash
   bash scripts/git-pull-seguro.sh "skill-linkagem-auditar-temp"
   ```

3. **Rodar a régua SEO determinística**:
   ```bash
   bun scripts/audit-linkagem.ts {site} --json
   ```
   Parse: `{ counts, findings:[{level,type,article,message}], homeReviewSlug, affiliateTag, totalArticles, lockedArticles, pillarArticles, portadoArticles, semGuiaArticles, inboundPeers, ancoraNaoVerificada:{links,destinos} }`. **`inboundPeers[slug]` = array dos OUTROS reviews que já linkam pra `slug` (grafo de entrada, peers distintos; hub/produto/home fora).** É a fonte pra calcular o delta de inbound de cada link novo — ver régua E no passo 5. NÃO recompute o grafo na mão.

   **Portões antes de qualquer proposta (canon 2026-09-22).** O script diz o que NÃO mediu; leia isso antes de ler os achados, porque "0 erros" com medição faltando parece site limpo:
   - **`extracao-incompleta` (error) em qualquer artigo → PARE.** O arquivo tem mais links do que o extrator leu, então o grafo do site não vale: não proponha link novo, remoção, nem conserto de órfão, sublinkado ou linkagem fraca. O relatório diz "grafo não confiável" com os artigos, e o conserto é no extrator (`docs/painel/_lib/internal-links.ts`), não no conteúdo. Caso real (22/09/2026, antes do controle existir): o texto do link em negrito vindo do WordPress sumia do grafo, e o melhorestetica aparecia com 16 órfãos que eram 6; no melhoresparacasa, links no `fullReview` deixavam 6 de 8 artigos com número errado. Propor link por esses números duplicaria link que já existe.
   - **`ancora-nao-verificada` (warn, 1 por site)** → os links para artigo sem `keyword` não tiveram a âncora comparada com nada. Escreva no relatório "âncora não verificada em N links (M destinos sem keyword)" e **não proponha link NOVO para destino sem keyword**: a régua é âncora = keyword do destino, e inventar a keyword pelo título ou pelo slug é decidir a busca-alvo do artigo, que não é trabalho desta skill. O caminho é preencher `keyword`/`keywordPlural` antes (nos 112 artigos portados do WordPress em 09/2026 o campo veio vazio). Placement e frase dos links que já existem continuam sendo avaliados normalmente.
   - **`portadoArticles` não vazio e travado** → faça a pergunta do item 1 de "Portados do WordPress" antes de montar as propostas. `semGuiaArticles` diz onde o link novo vai no `fullReview` (item 4).
   - **`link-fora-do-guia` (info)** → link entre artigos fora do `guideContent` (hoje só `products[].fullReview`, nos ports). Conta no grafo porque está na página. Liste na seção de placement e **não mova por conta própria**: o artigo pode nem ter guia, e mover é julgamento. No portado sem guia é o lugar certo (ver "Portados do WordPress", item 4).

4. **Rodar a validade de links** (estrutural por padrão; só Amazon/internos, sem fetch):
   ```bash
   bun scripts/audit-links.ts {site} --no-fetch --json
   ```
   Use SÓ pra contexto (tag/404 interno). **Não conserte tag aqui** — só reporte que `fill-affiliate-tag.ts` resolve.
   **Exceção: `link-rede` (error) se conserta aqui.** Site da rede não linka outro site da rede (Marcelo, 24/09/2026: "se achar, tem algo errado"). Aplica direto: tira o `<a>` e mantém o texto. Se o próprio site tem artigo do mesmo assunto, propõe (julgamento) o link interno no lugar. Em 24/09/2026 eram 0 na rede; um achado novo quase sempre é texto portado com link para um domínio antigo da cadeia que faltou no `--irmaos` do `wp-portar`.

4.5. **Links nascidos no TEMPLATE (canon 2026-09-02).** Tabela de specs, "Produtos testados", cards de categoria e o `sitemap-produtos.xml` montam `href` que não estão em campo nenhum do `.mdx`, então os passos 3 e 4 **não os veem** — foi assim que esta skill disse "limpo" com 12 links 404 no ar (creatina, ago/2026). Se `sites/{site}/dist/` existe e é mais novo que o último commit que tocou o site, rode:
   ```bash
   bun scripts/check-dist-links.ts {site} --json
   ```
   Cada destino 404 vira **conserto proposto** no relatório. A causa quase sempre é **produto citado em artigo sem página individual**: o fix é criar a página (`pagina-produto-criar`), **nunca remover o link** (decisão Marcelo 2026-09-01: o template linka sem condicional; a página é que tem que existir). O `audit-article.ts` (rule `produto`) já acusa isso por artigo. Sem dist fresco: **diga no relatório que essa classe não foi verificada** — a pré-checagem de deploy do painel e o `cf-deploy-r2.ts` rodam o mesmo check antes de subir.

4.6. **Slug × histórico do GSC (canon Marcelo 2026-09-04)**:
   ```bash
   bun scripts/audit-slugs.ts {site} --json
   ```
   Parse: `{ ok, inconclusivo, motivo, linhagem, propriedadesSemAcesso, achados:[{nivel,regra,artigo,sugerida,atual,candidata,pareceCategoria,msg}], disputas, rankeando:[{slug,cliques28d,impressoes28d}], orfasSemArtigo }`. O `rankeando` decide o que se aplica em cada artigo (seção "Artigo que já rankeia").

   O script **grava** `docs/painel/_data/slugs-historicas.json` (merge por site, só
   quando mediu) e o painel lê dali pro chip da coluna Slug. Commite esse arquivo junto
   com o resto da auditoria: sem ele, o site fica marcado como "nunca medido" na tela, que
   é o estado correto mas some assim que alguém roda — e a medição custa uma rodada de GSC
   por domínio da linhagem.

   **A pergunta é outra que a do `slug-vs-keyword`.** Aquela é convenção e dispara em
   32% da rede (127 de 390 artigos), por isso é INFO. Esta é histórico e dispara em 7
   casos na rede inteira: o artigo está na URL que o Google conhece?

   **`ok:false` NÃO é "limpo"** — é medição que não aconteceu. Reporte o motivo e siga
   com o resto da auditoria, sem afirmar nada sobre slug. Mesma régua pra
   `propriedadesSemAcesso`: propriedade sem permissão soma zero, então o achado daquele
   site pode estar incompleto e o relatório diz isso.

   **`inconclusivo:true` + exit 2** não é falha do passo e não é aprovação: a medição não aconteceu (ex.: linhagem com um domínio só, sem histórico nas duas janelas). Leia o `motivo`, diga no relatório que esta classe não foi verificada, e siga.

   **Regra `orfa-mesma-busca` (disputas).** Liga a órfã ao artigo pela consulta real do Search Console (`dimensions: ['page','query']`), nunca por semelhança de palavra.

   **Disputa é FATO, não conselho.** Ela diz "esta URL histórica e este artigo recebem a
   mesma busca", com as consultas e os números dos dois lados. As três saídas — mover a
   slug, emitir 301 pra cá, ou tratar como artigo separado — são decisão do dono do
   conteúdo (canon 2026-09-06: 301 pra artigo similar é válido). **Propor→aprovar**, e
   leia a fração com o denominador junto: ela é sobre as impressões com CONSULTA
   IDENTIFICADA, que no caso-origem eram 144 de 2.142 da página (o GSC anonimiza termo
   raro). "50%" ali é metade da parte identificada, não metade da página.

   **Todo achado vai por PROPOR→APROVAR, nunca auto-fix.** Mexer em URL pública errado
   custa o tráfego do artigo. E a decisão tem julgamentos que o script não faz sozinho
   (ver as 5 guardas no cabeçalho dele):
   - **Fica a URL mais forte, medida nos dois lados (canon Marcelo 2026-09-12, revisto
     em 26/09).** O `audit-slugs.ts` mede se a URL do artigo responde 200 e sai com:
     - `acao: '301'`: artigo no ar COM histórico próprio (1.000 impressões ou mais em 16
       meses). A slug histórica ganha **301 PARA o artigo**, sem renomear. Por quê:
       renomear também cria um 301, só que no sentido contrário; a URL no ar já tem
       indexação, sitemap e links internos; e tirar o artigo da URL forte foi a operação
       dos 4 movimentos invertidos de 04/09 (ver o incidente abaixo). Que o 301
       consolida no destino a rede já mediu: o escritorioecasa.com passou a autoridade
       pro .com.br por um 301 longo.
     - `acao: 'rename'`: artigo fora do ar (existe no repo e nunca foi publicado, como o
       climatizador do compraguia em 12/09) OU **artigo no ar SEM histórico próprio**
       contra histórica que vence o piso e o fator. Medido em 26/09: nos 7 casos da rede
       o artigo no ar tinha de 0 a 944 impressões em 16 meses contra 13 mil a 1,9 milhão
       da histórica (a do WordPress antigo), quase sempre porque o clone nasceu na slug
       do site de origem. Os 7 foram para a histórica pelo rename do painel, e a Bárbara
       fez o mesmo com 3 artigos do melhoresporte. Com o artigo na URL que o Google já
       conhecia, os backlinks dela chegam direto nele.
     - `acao: 'medir'`: não conseguiu medir se o artigo está no ar. Confira antes.

     As `disputas` (casamento por consulta) saem sempre com 301 quando o artigo está no
     ar: o elo delas é mais fraco (no melhoreletro a disputa apontava o subtópico "frio
     silencioso", não o artigo geral). Slug histórica que já tem 301 para o próprio
     artigo sai em `resolvidos` e não é achado. O que já foi renomeado fica: desfazer é
     mais uma troca de URL.
   - **`pareceCategoria: true` → quase sempre NÃO é rename.** A slug candidata coincide
     com um `categorySlug` do site, então provavelmente era a LISTAGEM antiga, não um
     artigo. Aí o certo é 301 pra `/categoria/`, e mover o artigo pra lá é erro.

   **O 301 (caso padrão) é uma regra só:** `{ from: "/{slug-historica}", to: "/{slug-do-artigo}/", status: 301, hostname: "{domínio do site}" }` no `worker/redirects.json`, seguida de `bun scripts/cf-deploy-worker.ts` e conferência com `curl -sL -o /dev/null -w "%{http_code} %{num_redirects}"` (200 em 1 salto). Não mexe em link interno nem no `.mdx`. **Antes de criar, confira que a origem não é a slug de um artigo vivo do site:** o worker responde o 301 antes de servir a página, e a regra deixaria o artigo inalcançável.

   **Se o rename for aprovado, faça pelo rename do painel** (`bun scripts/painel-api.ts POST /article/{site}/{slug}/rename corpo.json`, com `{"newSlug": "{slug-historica}"}`, ou o botão do editor). Ele faz, num commit só e na ordem certa: renomeia o `.mdx`, corrige os links internos que apontam pra slug antiga, cria o 301 da slug antiga pra nova, leva os relatórios de auditoria e de clonagem para o nome novo (desde 26/09) e **recusa com 409 quando a slug NOVA já é origem de um 301** — o worker responde redirect antes de servir a página, então uma regra sobrando deixaria o artigo inalcançável. Se a histórica já tinha 301 para o artigo (produtosanalisados, 26/09), tire essa regra do `worker/redirects.json` antes, num commit seu, e sincronize a VPS. Depois: build + deploy do site e deploy do worker da conta da zona, um logo depois do outro (entre os dois, a slug que saiu cai na home), e `curl -L` contando saltos: histórica 200 em 0, slug que saiu 200 em 1.

   ⚠ **`orfasSemArtigo` não é trabalho desta skill.** São URLs com histórico sem artigo
   nenhum do mesmo tópico no site: 199 das 209 órfãs da rede. Isso é artigo a escrever
   (seção "Artigos a recuperar" do painel), não slug a corrigir. Reporte a contagem e as
   maiores, e siga.

5. **Camada de julgamento LLM** (o valor que script não dá). O JSON do `audit-linkagem.ts` traz `lockedArticles[]` (fontes travadas) e `pillarArticles[]` (hubs isentos do teto) — use os dois. Read os `.mdx` dos artigos com links peer/home + os com FAQ/seções relevantes. Avalie:
   - **Placement genuinamente contextual?** Para cada link peer/home existente, o parágrafo onde ele está fala MESMO do tema do destino? "Fora da Conclusão" é necessário mas não suficiente. Sinalize os fracos com spot melhor. **Régua de spot (canon Marcelo): o link cai na MELHOR posição do artigo pro tema** — ex: link pro "melhor impressora para fotos" entra no parágrafo/H3 que fala de fotografia, não num lugar genérico.
   - **REMOVER link que não faz sentido ali (decisão do Marcelo).** Link cujo parágrafo **não trata do tema do destino** é candidato a REMOÇÃO (não só a mover), **preservando a prosa**: tira o `<a>` e reescreve a frase para ela continuar fazendo sentido sem o link.
     - **⚠ GUARDA DE GRAFO, obrigatória antes de propor remoção:** remover `A→B` derruba `inboundPeers[B]` de N pra N-1. Confira que **N-1 ≥ 2**; se não, proponha o link substituto (de preferência intra-cluster) **junto** com a remoção, no mesmo lote. Sem isso a remoção cria órfão/sublinkado e a régua E é violada pelo próprio fix. Caso real (compraguia 2026-07-31): removi 3 links e repus 1 intra-cluster pra não derrubar o inbound do destino.
     - **Guarda sem substituto natural:** se não existe fonte que passe no "Teste da decisão" para repor a entrada, o link fica. Ele sai no relatório como "sem decisão, mantido pela guarda (destino ficaria com N-1)", para ser trocado quando surgir a fonte. Caso real (produtosanalisados, 27/09/2026): os 3 links que a glutamina recebia eram genéricos, e a fonte natural (o whey isolado, que já fala de "BCAA e glutamina na fórmula") estava no teto de 4.
     - Remoção é **julgamento** → propor→aprovar, nunca aplicar direto.
   - **Leitura por destino (canon Marcelo 2026-09-27).** A passada por artigo pergunta "este link cabe aqui?" um de cada vez, e assim aprova link genérico, que só aparece como padrão quando as frases são lidas juntas. Para os **3 destinos com mais entradas** em `inboundPeers`, leia lado a lado TODAS as frases que apontam para cada um, com o parágrafo de cada uma, e aplique o "Teste da decisão". Frase que cabe em qualquer artigo, prioridade que não é verdadeira para o produto ou frase colada em parágrafo de outro assunto vira proposta de remoção, com a guarda de grafo acima. Caso-origem: produtosanalisados, 27/09/2026. O whey recebia 16 links; a auditoria de 24/09, lendo artigo por artigo, aprovou todos pela "ponte rotina de treino", e lidos juntos 5 não passavam ("quem combina com outros suplementos", "feche a proteína antes de somar vitaminas", em parágrafos sobre dose de creatina, alérgeno e tempo de pedalada).
   - **Oportunidades de links NOVOS.** Há FAQ/H3/seção que toca no tema de um peer ainda não-linkado (ou pouco-linkado), onde um link cairia natural? Liste só as genuinamente naturais — NUNCA force link decorativo. Para cada: artigo origem, peer destino, **spot exato** (cite a frase âncora), **âncora sugerida** (= keyword singular do destino), e o **Edit proposto** (frase antes → depois).
   - **`contentLocked`-aware (régua D):** se a FONTE natural de um link novo está em `lockedArticles[]`, NÃO proponha editá-la (artigo travado = SEO estável). Em vez disso **rerroteie**: ache outra fonte NÃO-travada que cubra o mesmo tema do destino, ou registre a oportunidade como "bloqueada (fonte travada — destravar p/ aplicar)" sem aplicar. Nunca edite travado sem destrave explícito do user. **Portado com autorização: a régua D não vale** (ver "Portados do WordPress").
   - **Balanço do grafo — `sublinkado` é PADRÃO, não opcional (régua E, canon 2026-06-09).** Todo artigo deve receber **≥2 inbounds**. `orfao` (0 inbound) e `sublinkado` (1 inbound) são metas de QUALIDADE da skill, no mesmo nível dos consertos — não trate como "info ignorável". Para cada órfão/sublinkado, proponha 1-2 links contextuais de fontes que tocam o tema (respeitando contextualidade e o teto de 4 da fonte). Caso real: na 1ª passada do impressoraideal tratei sublinkado como opcional e só consertei defeitos — a barra de qualidade certa é reforçar autoridade de todo nó sublinkado.
     - **⚠ Delta de inbound via `inboundPeers` (canon 2026-07-04) — o link pra fixar sublinkado/órfão TEM que ser INBOUND ao nó.** Consumir `inboundPeers[slug]` do `--json` (passo 3) pra raciocinar sobre o grafo, NÃO recomputar na mão. Um link `A→B` proposto leva `inboundPeers[B]` de N pra N+1 (aumenta o inbound de **B**, o DESTINO). Logo: pra tirar `X` de sublinkado/órfão, a fonte é OUTRO artigo e o **destino é `X`** (`A→X`) — um link `X→A` (saindo de X) NÃO ajuda o inbound de X. Ao propor, confirme que `inboundPeers[X].length + (novos links inbound propostos pra X) ≥ 2`, e que a fonte `A` escolhida ainda NÃO está em `inboundPeers[X]` (senão é `peer-repetido`, não ganha inbound distinto). No relatório, anote pra cada nó tocado o inbound projetado (ex: `melhor-ipad: 1 → 2 ✓`). Causa-raiz (2026-07-04): sem esse delta explícito, rotulei um link OUTBOUND como se resolvesse o sublinkado do próprio artigo-fonte — só a re-auditoria do passo 12 pegou. O `inboundPeers` torna o delta verificável ANTES de aplicar.

6. **Montar o relatório** (formato abaixo) com TODOS os fixes numerados (consertos + links novos), cada um com o diff `ANTES → DEPOIS`, marcando quais são **óbvios/determinísticos** (aplicam direto) e quais são **julgamento** (esperam aprovação). **Imprime inline.**

   **⚠ A seção `## 🔗 Placement avaliado` é OBRIGATÓRIA (canon Marcelo 2026-07-31)** — sem ela o relatório está INCOMPLETO, mesmo que tudo mais esteja verde. Motivo: a avaliação de placement (passo 5) era a única camada da skill sem nenhum artefato de saída, então dava pra pular em silêncio e o relatório saía "completo" do mesmo jeito. Foi exatamente o que aconteceu no compraguia (2026-07-31).
   - **Uma passada por ARTIGO, não por link.** Pergunta: *"algum link deste guide está num parágrafo que não trata do tema do destino?"*. São ~N perguntas (N = artigos) em vez de uma por link — dá pra fazer de verdade, e o output é curto. Exigir veredito link a link geraria 60+ linhas de "✓ ok" por site, que vira carimbo, não análise.
   - **O que imprimir:** os artigos onde algo falhou (com o parágrafo citado e o encaminhamento: remover / mover / reescrever a frase). Se nada falhou, uma linha só: `N artigos avaliados, nenhum link fora de contexto`. **O que não pode é a seção não existir.**
   - **Mais uma linha obrigatória, da leitura por destino (passo 5):** os 3 destinos lidos, com as entradas de cada um e quantas não passaram. Sem ela, a leitura por destino pode ser pulada em silêncio, como a de placement era até 31/07.

7. **Gravar o marcador de auditoria** (registra QUANDO auditou — roda SEMPRE, logo após o relatório, mesmo que o user rejeite tudo depois; auditar é o evento):
   ```bash
   # raiz do repo — o cwd do Bash reseta pra ~/Documents/Claude em sessão continuada; sem isto o mkdir cria a árvore LÁ (medido 03/09/26)
   cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" && test -f docs/painel/sites-meta.json || { echo "⛔ cwd errado ($(pwd)): rode a partir da raiz do ProjetoAfiliados"; exit 1; }
   mkdir -p docs/biblias-v2/.audits/linkagem
   ```
   `Write` em `docs/biblias-v2/.audits/linkagem/{site}-last.md`: título (`# Auditoria de linkagem: {site}`), contagens (`- Erros: N · Avisos: M · Infos: K · Oportunidades: O`), a mesma linha "Não medido" do relatório (quem abrir o marcador depois precisa saber se o "0 erros" foi medido), lista curta dos tipos disparados (ou "nenhum"). **NÃO** invente timestamp (a fonte de tempo é o commit git).
   Depois do passo 12, atualize o marcador com o estado final e, se algum artigo ficou **órfão de propósito**, registre-o nestas linhas fixas, com os slugs separados por vírgula: `- Exceções justificadas: slug-a, slug-b (motivo curto)` para a exceção do "encaminhamento útil", e `- Segundo tempo a partir de AAAA-MM-DD: slug-c` para o que fica para a segunda leva de links. O painel lê só essas duas linhas: órfão que não está nelas acende "Linkagem com pendências" no site, e o segundo tempo volta a acender na data.

8. **Aplicar o óbvio + esperar aprovação do julgamento**: aplica direto no passo 10, marcado ✅ CORRIGIDO, só o que o Invariante "APLICA O ÓBVIO" e o passo 4 classificam como determinístico (link-quebrado, link-home-errado, link-rede, anchor-nao-keyword, anchor-produto-sem-nome com a reconciliação de concordância, `anchor-frase-quebrada` de level=error). Todo o resto espera aprovação granular ("aplica tudo" / "aplica 1,3" / "aplica canon" / "rejeita 2" / "refaz 1"), inclusive remoção de link, `anchor-frase-quebrada` de level=warn, proposta de `pillar: true` e os achados do `audit-slugs.ts`. Sem nada de julgamento, pula a espera e vai para o build/commit. **Artigo de `rankeando[]` segue a seção "Artigo que já rankeia"**: dos determinísticos, só os do item 1 dela aplicam direto.

9. **Backup** antes de aplicar (1 por artigo tocado):
   `docs/painel/.painel-backups/{YYYY-MM-DD}/article-{site}-{slug}-{HHMMSS}-guide.mdx` (via helper `readGuideContent` do painel, mesmo formato dos outros). Portado sem guia, com edição no `fullReview`: cópia do `.mdx` inteiro em `article-{site}-{slug}-{HHMMSS}.mdx`.

10. **Aplicar os óbvios + os aprovados** via `Edit` cirúrgico no `guideContent` do `.mdx` (ou no `fullReview`, no portado sem guia; preservar indent 2 espaços do block scalar; um trecho por vez). Regras:
    - **anchor-nao-keyword**: trocar SÓ o texto entre `<a>...</a>` pela keyword (qualificadores ficam FORA do `<a>`). **⚠ RECONCILIAR a concordância do artigo/preposição que vem ANTES do `<a>` (canon 2026-06-23):** se a âncora nova muda NÚMERO ou GÊNERO em relação à antiga, o artigo/contração que a rege precisa acompanhar. Caso real: âncora `melhores impressoras de tanque de tinta` (plural) virou `melhor impressora tanque de tinta` (singular) mas o "no guia **das**" ficou → "no guia das melhor impressora" (quebrado). Ajustes típicos: `das→da`, `dos→do`, `nas→na`, `nos→no`, `aos→ao`, `pelas→pela`, `essas→essa`, `umas→uma`. **Depois de cada troca, releia a frase inteira como leitor.** Artigo, preposição, número e gênero antes do `<a>` têm que fechar com a âncora nova, e nenhuma palavra pode ficar duplicada ("o melhor <a>melhor robô…</a>": tire o de fora). Se a troca exige mexer em algo além da palavra colada ("em <a>…</a>", "qual <a>…</a>"), ou se a frase passou a dizer outra coisa ("quem utiliza o notebook para trabalho" virando "quem utiliza o melhor notebook para trabalho"), é julgamento: proponha, não aplique. No portado, âncora que já estava no plural vai para o `keywordPlural` ("Portados do WordPress", item 3).
    - **anchor-produto-sem-nome**: trocar o texto pelo nome completo do produto (com marca). **Mesma reconciliação de concordância do item acima** (ex: âncora que era plural genérico vira nome próprio singular → ajustar artigo antes).
    - **anchor-frase-quebrada (error)**: NÃO toca na âncora (ela já está certa = keyword). Troca o **artigo indefinido que vem ANTES** pelo definido, **contraindo** a preposição anterior: `um`→`o`, `uma`→`a`, `a um`→`ao`, `a uma`→`à`, `de um`→`do`, `em um`→`no`. Se havia qualificador (`um bom melhor whey` → `o melhor whey`), ele sai junto (era redundante com o superlativo). **Artigo no número errado** ("das melhor impressora", "o melhores roteadores"): acertar o artigo (`das`→`da`, `o`→`os`); no portado cuja âncora era plural, usar o `keywordPlural` e manter o artigo do texto. **"melhor" repetido** ("o melhor <a>melhor robô…</a>"): tirar o de fora. ⚠ **Reler a frase inteira depois**, incluindo o gênero do artigo — o gênero NÃO é validado pelo script (ver 11.5) e é você quem confere contra o núcleo real da keyword.
    - **anchor-frase-quebrada (warn)**: é julgamento, espera aprovação. `na/no` que não retoma nada → nomear o destino (`no guia de {keyword}`) ou usar o plural. `em` que não retoma nada → nomear o destino (o plural não resolve: "em melhores celulares" também não fecha). `qual` + superlativo → pôr o artigo (`qual o melhor robô…`, conferindo o gênero). `qualquer` + superlativo → reescrever a frase.
    - **REMOVER link fora de contexto** (aprovado no julgamento): tira o `<a>` mantendo/reescrevendo a prosa pra frase seguir fazendo sentido sem ele. Aplicar **junto** com o link substituto quando a guarda de inbound exigir (ver passo 5).
    - **link-home-errado**: trocar `href="/{homeReviewSlug}/"` por `href="/"` (manter a âncora = keyword da home).
    - **link-quebrado**: corrigir o href pro slug REAL (confirmar o arquivo existe) OU, se não há destino, remover o `<a>` mantendo o texto.
    - **link-rede**: remover o `<a>` mantendo o texto (outro site da rede nunca é destino). Link interno no lugar só com aprovação.
    - **peer-link-na-conclusao**: MOVER o link pro spot contextual aprovado (remover da Conclusão + inserir no parágrafo-alvo). Produto/Amazon na Conclusão ficam.
    - **link novo**: inserir o `<a>` no spot exato aprovado, âncora = keyword singular do destino, href = slug REAL (`/slug/` ou `/` pra home), sem `rel`/`target` (interno passa autoridade).

11. **Build** (gate): `pnpm --filter {site} build`. Se Zod/Astro falhar, reverter do backup e reportar.

11.5. **Concordância artigo↔âncora.** O `audit-linkagem.ts` do passo 12 acusa artigo no número errado antes da âncora ("das melhor", "o melhores", inclusive com negrito dentro do link), "melhor" repetido fora do link e "em"/"qual" + superlativo. Keyword sem "melhor" que já é plural ("creatinas", "micro-ondas") ele não confere: fica para a sua releitura do passo 10.

    **Concordância de GÊNERO (`o melhor impressora`, `a melhor tablet`) fica FORA do determinístico — de propósito (canon 2026-07-31).** Tentei derivar o gênero do `title` do destino ("as N melhores" = feminino) e **medi 17% de acerto**: os títulos da rede usam `As 11 Melhores Whey Protein` e `As N Melhores Ômega 3` concordando com substantivo ELÍPTICO ("as melhores [opções]"), não com o núcleo da keyword. Resultado: `o melhor whey protein` e `o melhor ômega 3`, que estão **CORRETOS**, vinham como erro. Como esta skill aplica fix determinístico **sem aprovação**, um check assim viraria edição errada automática. Então: gênero é **julgamento** — ao reler a frase inteira do `<a>` tocado (passo 10), confira o artigo com o núcleo REAL da keyword, não com o título.

12. **Re-rodar `bun scripts/audit-linkagem.ts {site}`** pós-fix para confirmar que os achados aplicados sumiram e nada regrediu (0 broken, 0 home-errado, 0 peer na Conclusão entre os aplicados). O que ficou de fora de propósito continua aparecendo e vai para o relatório com o motivo: exceção justificada ao piso de 2, artigo de `rankeando[]`, destino sem keyword, fonte travada ou proposta rejeitada.

13. **Git add + commit (`--no-verify`) + push + VPS pull**:
    ```bash
    git add sites/{site}/src/content/reviews/{slugs-tocados}.mdx
    git add docs/biblias-v2/.audits/linkagem/{site}-last.md
    git commit --only --no-verify -m "fix({site}): linkagem interna via skill (N consertos + M links novos)" \
      -- sites/{site}/src/content/reviews/{slugs-tocados}.mdx docs/biblias-v2/.audits/linkagem/{site}-last.md
    git push origin main
    bash scripts/painel-vps-pull.sh
    ```
    `--no-verify` necessário (hook Fase J bloqueia `reviews/*.mdx`). **O `painel-vps-pull.sh` dispara `/admin/update`, que roda `gen.ts` full → regenera `linkagem-{site}.html` = o painel mostra o resultado final ("sincroniza lá").**

14. **Reportar** o resultado: o que foi aplicado, o grafo pós-fix, o path do backup, e o link da página de linkagem no painel.

## Formato do relatório de propostas

```markdown
# Linkagem: {site}

**{N} artigos · tag: {affiliateTag} · home: {homeReviewSlug ou "grid"}**
**Determinístico:** {errors} erros · {warnings} avisos · {infos} infos
**Não medido:** {extração incompleta: N artigos (grafo não confiável) · âncora não verificada: N links, M destinos sem keyword · slug: ok:false ou propriedades sem acesso} — ou "nada"  ← LINHA OBRIGATÓRIA
**Portados:** {N artigos com `portadoDe` (M sem guia) · edição autorizada: sim/não} — ou "nenhum"

## 🔴 Consertos propostos
### 1. [{type}] {article} `{slug}`
- **Problema**: {message do script}
- **Fix** (cirúrgico):
  ```
  ANTES:  <p>... <a href="/x/">y</a> ...</p>
  DEPOIS: <p>... <a href="/x/">{keyword}</a> ...</p>
  ```

## 💡 Links novos propostos
### N. {article} → {peer} (na {seção/FAQ "..."})
- **Por quê natural**: {1 frase}
- **Fix**:
  ```
  ANTES:  <p>...frase-alvo.</p>
  DEPOIS: <p>...frase-alvo. {nova frase com <a href="/peer/">keyword</a>}.</p>
  ```

## 🔗 Placement avaliado  ← SEÇÃO OBRIGATÓRIA, nunca omitir
{N} artigos avaliados. Links fora de contexto: {M}
Leitura por destino: {destino-1} ({E} entradas, {X} sem decisão) · {destino-2} (…) · {destino-3} (…)
### N. {article}: link → {peer} no parágrafo "{primeiras palavras do <p>}"
- **Por quê não cabe**: {1 frase — o parágrafo fala de X, o destino é sobre Y}
- **Encaminhamento**: remover (inbound de {peer}: {N}→{N-1} {✓ ou ⚠ repor}) · mover pra {seção} · reescrever a frase
{ou, se nada falhou: "{N} artigos avaliados, nenhum link fora de contexto."}

## Como aplicar
- **"aplica tudo"** · **"aplica 1,3"** (por número) · **"aplica consertos"** (só os 🔴) · **"rejeita 2"** · **"refaz 1"**
```

## Critérios (referência — vêm dos scripts)

- `link-rede` (error, do `audit-links.ts`: link para outro site da rede), `link-quebrado` (error), `link-home-errado` (error), `linkagem-fraca` (warn, <2 peers distintos de saída), `linkagem-excesso` (warn, >4 peers distintos num artigo NÃO-hub — enxugar pros 3-4 contextuais ou marcar `pillar:true`), `peer-repetido` (warn), `anchor-nao-keyword` (warn; compara sem acento, hífen nem espaço, então "micro-ondas" = "microondas" e "Wi-Fi" = "wifi"; keyword sem "melhor" aceita "melhor " + keyword), `anchor-frase-quebrada` (**error** = indefinido/qualificador antes de âncora com superlativo, ex. "um melhor pré-treino" — fix: artigo definido contraindo a preposição, ver Invariantes; artigo no número errado, ex. "das melhor impressora"; "melhor" repetido fora do link; **warn** = "na/no/em" que não retoma guia/artigo, "qual" sem artigo, ou "qualquer" + superlativo, que pedem reescrita), `anchor-produto-sem-nome` (warn), `slug-vs-keyword` (**info** — convenção comum na rede, 32% dos artigos medidos em 2026-09-04; o 404 real já é coberto por link-quebrado/link-home-errado; NÃO é defeito a consertar), `slug-sem-historico` (**warn**, do `audit-slugs.ts` — pergunta DIFERENTE da anterior: não é "segue a convenção?" e sim "é a URL que o Google conhece?", medindo os dois lados nos domínios da linhagem; dispara em 7 casos na rede contra os 127 da `slug-vs-keyword`; **sempre propor→aprovar**, e `pareceCategoria:true` quase sempre significa 301 pra `/categoria/`, não rename), `peer-link-na-conclusao` (info), `hub-and-spoke-incompleto` (info, **1 linha-resumo colapsada** — **fora de escopo desta skill**), `orfao` (warn)/`sublinkado` (info, mas **acionável** — ver régua E no passo 5), `extracao-incompleta` (**error** — o grafo do site não vale; a skill para, ver os portões do passo 3), `ancora-nao-verificada` (warn, 1 por site — âncora não medida por falta de keyword no destino; sem link novo para esses destinos), `link-fora-do-guia` (info — link entre artigos no `fullReview`; listar, não mover).

## Armadilhas

1. **Reimplementar grafo/extração.** Os scripts já fazem — rode e leia o JSON.
2. **Rewrite do guide.** É cirúrgico por trecho; nunca reescreva o guide inteiro (isso é `artigo-guia-escrever`).
3. **parseYaml/stringify no frontmatter.** Bagunça o block scalar `|`. Sempre `Edit` no trecho.
4. **Forçar link novo decorativo.** Só proponha se o spot REALMENTE toca no tema do destino. Melhor 0 honestas que 5 forçadas.
5. **Aplicar JULGAMENTO sem aprovar.** O mecânico (âncora=keyword, link quebrado, `/{homeReviewSlug}/`→`/`) aplica direto (canon 24/07); links novos e placement (julgamento) imprimem os diffs e esperam.
6. **Esquecer `--no-verify`.** O hook Fase J bloqueia `reviews/*.mdx`.
7. **Editar artigo travado.** `contentLocked: true` → pular + avisar. A exceção é o portado com autorização na execução (ver "Portados do WordPress"); e o erro inverso também existe: com a regra de sempre, os 6 primeiros sites portados saíam sem mudança nenhuma, e ninguém percebia que a skill não tinha feito nada.
8. **Ler `ok:false` do `audit-slugs.ts` como "limpo".** Sem credencial do GSC o script não mede, e não medir não é aprovar. Mesma coisa pra `propriedadesSemAcesso`: propriedade sem permissão soma zero e o achado do site fica incompleto — diga isso no relatório.
9. **Renomear slug olhando um lado só.** O `mapa-artigos-orfaos.json` lista apenas URLs que NÃO existem em disco, então a slug forte nunca aparece nele. Em 2026-09-04 isso me fez tirar um artigo de uma URL com 275.770 impressões e pôr numa com 6. O `audit-slugs.ts` mede as duas pontas — use o número dele, não a presença na lista de órfãs.
10. **Renomear e esquecer o 301 da slug NOVA.** O worker responde redirect antes de servir a página: se sobrar uma regra com origem na slug nova, o artigo fica inalcançável. Aconteceu com os monitores do compraguia no mesmo dia.
11. **Casar tópico por UM campo só.** O artigo declara o tópico em três lugares — `keyword`, `keywordPlural` e `keywordAlternativas` — e a órfã que interessa costuma estar no PLURAL (82 de 82 artigos de slug plural da rede têm `keyword` singular). Quem compara a órfã só com `slugify(keyword)` fica cego justamente no caso comum, e o silêncio parece aprovação. Aconteceu 3× em 04/09/2026: duas no `slugDivergentes` do painel e uma no próprio `audit-slugs.ts`, que **não pegava** o caso dos monitores (281.519 imp) que originou a régua. Pior que não achar: a órfã no plural caía NAS DUAS listas ao mesmo tempo, como "slug a corrigir" e como "artigo a escrever". **Ao mexer em qualquer comparação de tópico, use os três campos e teste com um caso conhecido, invertendo o estado.**
12. **Achar que o painel não atualiza.** Atualiza: `/admin/update` roda `gen.ts` full → `linkagem-{site}.html` regenera. Não precisa de passo extra.
13. **Ler "0 erros de âncora" como âncora certa.** Até 22/09/2026 o check de âncora pulava em silêncio todo link para artigo sem `keyword`, e o relatório saía verde nos 6 sites portados do WordPress com 195 links sem medição (todos os que apontam para artigo portado, que veio sem keyword). O controle positivo é outro site com keyword: o `oguiacompra` acusava 10 achados de âncora no mesmo dia. Hoje o script emite `ancora-nao-verificada`; se ela vier, a linha "Não medido" do relatório diz quantos.
14. **Confiar no grafo sem o controle do extrator.** O extrator lia só o `guideContent` e só link com texto sem tag. Três implementações de "links deste site" conviviam (extrator do painel, chip `linkagem-health.ts` que conta `href` no arquivo inteiro, e a régua de frase da auditoria) e só o chip estava certo. O `extracao-incompleta` compara o arquivo inteiro com o que o extrator leu; se ele aparecer, o conserto é no extrator.
15. **Trocar a âncora sem olhar a palavra colada antes do link.** Lidas uma a uma, as 43 âncoras dos 6 portados (22/09/2026) davam 6 frases quebradas se trocadas pela keyword ao pé da letra, e nenhuma conferência da época pegava: "o melhor melhor robô…" e "a melhor melhor máquina de lavar 12kg", "qual melhor robô… combina", "comparar alternativas em melhor celular…" (2) e "a maioria do melhor roteador WiFi" (a âncora era "melhores roteadores"). Hoje o script acusa as cinco primeiras; a última se evita com o item 3 de "Portados".
16. **Ler diferença de grafia como âncora errada.** Das mesmas 43, 13 diferiam só em acento, hífen ou espaço ("ar condicionado" × "ar-condicionado", "micro-ondas" × "microondas"). Para a busca é a mesma palavra, e trocar pela keyword piorava a grafia em 4 ("micro-ondas" virava "microondas", "Wi-Fi" virava "wifi"). O script compara sem essas diferenças desde então; não "conserte" à mão o que ele não acusa.

## Invocação

```
audita e melhora a linkagem do melhorimpressora
/linkagem-auditar impressoraideal
```

Args canônico: `Skill(skill="afiliados-skills:linkagem-auditar", args="melhorimpressora")`.

## Sincronização painel ↔ skill

A skill grava `.audits/linkagem/{site}-last.md` (1º marcador por-SITE; os outros audits são por-artigo/ASIN). A página `linkagem-{site}.html` (gerada por `gen.ts:linkagemContent`) reflete o grafo pós-fix automaticamente no `painel-vps-pull` (gen full). O botão roxo "📋 Copiar skill" dessa página copia `/linkagem-auditar {site}` pro clipboard. A pill "Linkagem auditada" no site-detail é follow-up (`/activity` lê o commit `audit-linkagem(`).

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
