---
name: linkagem-auditar
description: Audita E MELHORA a linkagem interna do SITE INTEIRO (cross-artigo), propor→aprovar. Roda os núcleos determinísticos (scripts/audit-linkagem.ts + audit-links.ts) + camada de julgamento LLM (placement contextual, links novos pra órfãos/sublinkados). Quantidade: 2 mín / ~3 ideal / 4 máx peers distintos por artigo; HUB (homeReviewSlug ou pillar:true) isento do teto. Conserta: link quebrado 404, /{homeReviewSlug}/→/, âncora≠keyword, âncora de produto sem marca, peer/home na Conclusão, excesso >4. Confere também SLUG × HISTÓRICO DO GSC (`scripts/audit-slugs.ts`): o artigo está na URL que o Google conhece, medindo os DOIS lados nos domínios da linhagem — renomear slug quebra link interno, então mora aqui. contentLocked-aware (rerroteia a fonte). Artigo PORTADO do WordPress (`portadoDe`): com a autorização do Marcelo na execução, edita os travados só no link e nas palavras coladas nele, com a trava ligada; âncora no plural vai para o `keywordPlural`; artigo sem guia recebe link no `fullReview`. ARTIGO QUE JÁ RANKEIA (clique em 28 dias, `rankeando[]` do audit-slugs): só conserto de defeito e 1 link novo com aprovação, o resto vai para o relatório; no site que recebeu portados, os links dos artigos antigos para os portados vêm 3 a 4 semanas depois do port. Link para outro site da rede (`link-rede`) é defeito. Aceita site OU URL do painel. Fecha com commit + push + painel-vps-pull + marcador .audits/linkagem/{site}-last.md.
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

⚠️ **O piso de 2 NÃO vence o "encaminhamento útil" (canon 2026-08-10) — vale sobretudo aqui, porque esta skill ADICIONA links.** Antes de propor um link novo pra resolver `linkagem-fraca`/`orfao`, aplique o teste da decisão: o link responde a uma **bifurcação** ("tablet ou Kindle?"), a uma **soma** ("whey + creatina?") ou a uma **ordem de prioridade** ("fecha a proteína antes da glutamina")? Se você precisa **construir o cenário** em que o leitor iria pro outro artigo, o cenário não existe e o link é protocolar. Nesse caso **NÃO proponha o link**: deixe o artigo em 0 peer e registre o `linkagem-fraca` como exceção justificada no relatório.

**PRÉ-CONDIÇÃO MECÂNICA — sem ela a exceção NÃO existe:** o artigo tem **ZERO peers da mesma `category`**. Conte antes de aceitar: `category` dos outros `.mdx` de `reviews/` do site. Havendo ao menos 1 irmão da mesma categoria, **o piso de 2 vale integral** e você DEVE propor o link. A exceção só cobre o artigo que é o primeiro da categoria dele num site que já tem outras. Isso é deliberado — exceção que é só julgamento vira atalho, e foi exatamente assim que a régua qualitativa perdeu pro piso numérico.

Não é hipótese: em 2026-08-10 o `compraguia/melhor-caixa-de-som-jbl` (artigo de áudio num site de impressora/tablet/Kindle, **0 peers da mesma categoria**) ganhou 2 links de tablet só pra bater o piso, e eles foram removidos depois. **Esta skill é justamente a que os traria de volta.** E não adianta cortar por categoria: dos 942 links peer da rede, 229 são cross-categoria e **227 passam no teste da decisão** (34 E-reader↔Tablet, 174 entre suplementos, 17 de fitness). Ver "Desempate" na `artigo-guia-escrever`.
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

   ⚠ **`inconclusivo:true` + exit 2 (canon 2026-09-12).** Até aqui a guarda cobria só
   credencial ausente, e faltava o caso de ENTRADA vazia: no `melhoremcasa` a linhagem
   saiu com um domínio só (o novo, sem histórico), as duas janelas vieram zeradas e o
   relatório imprimiu **"✅ toda slug do site é a que tem o histórico"** sem ter medido
   nada. Aprovação sem medição é pior que erro — ela encerra a investigação. Agora sai
   `INCONCLUSIVO` com motivo e **exit 2**, que NÃO é falha do passo: leia o `motivo`,
   diga no relatório que esta classe não foi verificada, e siga.

   **Regra `orfa-mesma-busca` (disputas), canon 2026-09-12.** O casamento antigo exigia
   que a órfã fosse EXATAMENTE uma das três formas de keyword do artigo. Quando o clone
   copia keyword e slug da mesma fonte, as duas ficam coerentes entre si e nada liga o
   artigo ao passado do domínio de DESTINO — o caso mais comum, e o que deixava o aviso
   mudo. A regra nova liga pela CONSULTA real do Search Console (`dimensions:
   ['page','query']`), então a guarda 3 (nunca casar por semelhança de palavra) continua
   de pé: o elo é o termo que a pessoa digitou, não inferência de sinônimo.

   **Disputa é FATO, não conselho.** Ela diz "esta URL histórica e este artigo recebem a
   mesma busca", com as consultas e os números dos dois lados. As três saídas — mover a
   slug, emitir 301 pra cá, ou tratar como artigo separado — são decisão do dono do
   conteúdo (canon 2026-09-06: 301 pra artigo similar é válido). **Propor→aprovar**, e
   leia a fração com o denominador junto: ela é sobre as impressões com CONSULTA
   IDENTIFICADA, que no caso-origem eram 144 de 2.142 da página (o GSC anonimiza termo
   raro). "50%" ali é metade da parte identificada, não metade da página.

   As duas guardas da regra, as duas calibradas contra medição — se mexer nelas, meça de
   novo nos mesmos sites:
   - **Fração mínima (1%).** Sem ela saem 5 achados no `compraguia`, todos cauda: 859 de
     272.852 impressões (0,3%). Uma órfã grande sempre tem ALGUMA busca que contém a
     keyword de um artigo do site.
   - **Direção.** A slug órfã não pode ter token de conteúdo fora da forma do artigo. Sem
     ela, o piso de fração acusava `/melhor-air-fryer-custo-beneficio/` contra
     `/melhor-air-fryer/` com 29,7% — o par exato que a guarda 3 existe pra nunca fundir.
     Subtópico é **artigo a escrever**, não slug a corrigir, e por definição tem
     sobreposição alta com o tópico pai. Validado em 8 sites: 1 achado no total, zero
     falso positivo.

   **Todo achado vai por PROPOR→APROVAR, nunca auto-fix.** Mexer em URL pública errado
   custa o tráfego do artigo. E a decisão tem julgamentos que o script não faz sozinho
   (ver as 5 guardas no cabeçalho dele):
   - **Artigo NO AR não muda de slug (canon Marcelo 2026-09-12).** A ação padrão é **301
     da slug histórica PARA o artigo**, no domínio do site. O `audit-slugs.ts` mede se a
     URL do artigo responde 200 e já sai com `acao: '301'` (no ar), `'rename'` (fora do
     ar) ou `'medir'` (não conseguiu medir: confira antes). Por quê: renomear também cria
     um 301, só que no sentido contrário, e a única diferença é qual URL fica oficial. A
     que está no ar já tem indexação, sitemap e links internos; renomear joga isso fora e
     foi a operação dos 4 movimentos invertidos de 04/09 (ver o incidente abaixo). Que o
     301 consolida no destino a rede já mediu: o escritorioecasa.com passou a autoridade
     pro .com.br por um 301 longo. **Rename só vale pra artigo fora do ar** (existe no
     repo e nunca foi publicado, como o climatizador do compraguia em 12/09) **ou como
     exceção que o Marcelo aprovar caso a caso.** O caso em que a exceção pode valer é
     artigo no ar com histórico perto de zero contra slug histórica muito forte
     (amelhorimpressora, 28/08, renomeado antes desta regra). O que já foi renomeado
     fica: desfazer é mais uma troca de URL.
   - **`pareceCategoria: true` → quase sempre NÃO é rename.** A slug candidata coincide
     com um `categorySlug` do site, então provavelmente era a LISTAGEM antiga, não um
     artigo. Aí o certo é 301 pra `/categoria/`, e mover o artigo pra lá é erro.

   **O 301 (caso padrão) é uma regra só:** `{ from: "/{slug-historica}", to: "/{slug-do-artigo}/", status: 301, hostname: "{domínio do site}" }` no `worker/redirects.json`, seguida de `bun scripts/cf-deploy-worker.ts` e conferência com `curl -sL -o /dev/null -w "%{http_code} %{num_redirects}"` (200 em 1 salto). Não mexe em link interno nem no `.mdx`. **Antes de criar, confira que a origem não é a slug de um artigo vivo do site:** o worker responde o 301 antes de servir a página, e a regra deixaria o artigo inalcançável.

   **Se o rename for aprovado (artigo fora do ar, ou exceção), são 4 passos e a ordem importa:** renomear o `.mdx`,
   corrigir os links internos que apontam pra slug antiga (é o trabalho desta skill, e o
   motivo de a regra morar aqui), criar 301 da slug antiga pra nova no domínio do site, e
   **remover qualquer 301 cuja origem seja a slug NOVA** — o worker responde redirect
   antes de servir a página, então uma regra sobrando deixa o artigo inalcançável.

   ⚠ **`orfasSemArtigo` não é trabalho desta skill.** São URLs com histórico sem artigo
   nenhum do mesmo tópico no site: 199 das 209 órfãs da rede. Isso é artigo a escrever
   (seção "Artigos a recuperar" do painel), não slug a corrigir. Reporte a contagem e as
   maiores, e siga.

   ⚠ **Incidente que gerou este passo (2026-09-04):** movi 8 artigos pra "slug histórica"
   lendo só o `mapa-artigos-orfaos.json`. Quatro estavam invertidos — num deles o artigo
   saiu de uma URL com 275.770 impressões (51.085 nos últimos 28 dias) pra outra com 6. O
   mapa lista só URLs que NÃO existem em disco, então a slug forte nunca aparece nele,
   justamente por já ser o artigo. Ler ausência na lista como ausência de histórico é o
   erro que o `audit-slugs.ts` existe pra tornar impossível: ele mede os dois lados.

5. **Camada de julgamento LLM** (o valor que script não dá). O JSON do `audit-linkagem.ts` traz `lockedArticles[]` (fontes travadas) e `pillarArticles[]` (hubs isentos do teto) — use os dois. Read os `.mdx` dos artigos com links peer/home + os com FAQ/seções relevantes. Avalie:
   - **Placement genuinamente contextual?** Para cada link peer/home existente, o parágrafo onde ele está fala MESMO do tema do destino? "Fora da Conclusão" é necessário mas não suficiente. Sinalize os fracos com spot melhor. **Régua de spot (canon Marcelo): o link cai na MELHOR posição do artigo pro tema** — ex: link pro "melhor impressora para fotos" entra no parágrafo/H3 que fala de fotografia, não num lugar genérico.
   - **REMOVER link que não faz sentido ali (canon Marcelo 2026-07-31).** Até 2026-07-31 a skill só sabia **consertar** (404/âncora/home) e **adicionar** — não havia NENHUM gatilho que produzisse "esse link não cabe aqui, tira". Consequência real: na 1ª passada do compraguia entreguei "0 erros · 0 avisos" com três links tablet→impressora vivos, porque nenhum check os questionava; só foram removidos quando o Marcelo apontou. Agora: link cujo parágrafo **não trata do tema do destino** é candidato a REMOÇÃO (não só a mover), **preservando a prosa** — tira o `<a>` e reescreve a frase pra ela continuar fazendo sentido sem o link.
     - **⚠ GUARDA DE GRAFO, obrigatória antes de propor remoção:** remover `A→B` derruba `inboundPeers[B]` de N pra N-1. Confira que **N-1 ≥ 2**; se não, proponha o link substituto (de preferência intra-cluster) **junto** com a remoção, no mesmo lote. Sem isso a remoção cria órfão/sublinkado e a régua E é violada pelo próprio fix. Caso real (compraguia 2026-07-31): removi 3 links e repus 1 intra-cluster pra não derrubar o inbound do destino.
     - Remoção é **julgamento** → propor→aprovar, nunca aplicar direto.
   - **Oportunidades de links NOVOS.** Há FAQ/H3/seção que toca no tema de um peer ainda não-linkado (ou pouco-linkado), onde um link cairia natural? Liste só as genuinamente naturais — NUNCA force link decorativo. Para cada: artigo origem, peer destino, **spot exato** (cite a frase âncora), **âncora sugerida** (= keyword singular do destino), e o **Edit proposto** (frase antes → depois).
   - **`contentLocked`-aware (régua D):** se a FONTE natural de um link novo está em `lockedArticles[]`, NÃO proponha editá-la (artigo travado = SEO estável). Em vez disso **rerroteie**: ache outra fonte NÃO-travada que cubra o mesmo tema do destino, ou registre a oportunidade como "bloqueada (fonte travada — destravar p/ aplicar)" sem aplicar. Nunca edite travado sem destrave explícito do user. **Portado com autorização: a régua D não vale** (ver "Portados do WordPress").
   - **Balanço do grafo — `sublinkado` é PADRÃO, não opcional (régua E, canon 2026-06-09).** Todo artigo deve receber **≥2 inbounds**. `orfao` (0 inbound) e `sublinkado` (1 inbound) são metas de QUALIDADE da skill, no mesmo nível dos consertos — não trate como "info ignorável". Para cada órfão/sublinkado, proponha 1-2 links contextuais de fontes que tocam o tema (respeitando contextualidade e o teto de 4 da fonte). Caso real: na 1ª passada do impressoraideal tratei sublinkado como opcional e só consertei defeitos — a barra de qualidade certa é reforçar autoridade de todo nó sublinkado.
     - **⚠ Delta de inbound via `inboundPeers` (canon 2026-07-04) — o link pra fixar sublinkado/órfão TEM que ser INBOUND ao nó.** Consumir `inboundPeers[slug]` do `--json` (passo 3) pra raciocinar sobre o grafo, NÃO recomputar na mão. Um link `A→B` proposto leva `inboundPeers[B]` de N pra N+1 (aumenta o inbound de **B**, o DESTINO). Logo: pra tirar `X` de sublinkado/órfão, a fonte é OUTRO artigo e o **destino é `X`** (`A→X`) — um link `X→A` (saindo de X) NÃO ajuda o inbound de X. Ao propor, confirme que `inboundPeers[X].length + (novos links inbound propostos pra X) ≥ 2`, e que a fonte `A` escolhida ainda NÃO está em `inboundPeers[X]` (senão é `peer-repetido`, não ganha inbound distinto). No relatório, anote pra cada nó tocado o inbound projetado (ex: `melhor-ipad: 1 → 2 ✓`). Causa-raiz (2026-07-04): sem esse delta explícito, rotulei um link OUTBOUND como se resolvesse o sublinkado do próprio artigo-fonte — só a re-auditoria do passo 12 pegou. O `inboundPeers` torna o delta verificável ANTES de aplicar.

6. **Montar o relatório** (formato abaixo) com TODOS os fixes numerados (consertos + links novos), cada um com o diff `ANTES → DEPOIS`, marcando quais são **óbvios/determinísticos** (aplicam direto) e quais são **julgamento** (esperam aprovação). **Imprime inline.**

   **⚠ A seção `## 🔗 Placement avaliado` é OBRIGATÓRIA (canon Marcelo 2026-07-31)** — sem ela o relatório está INCOMPLETO, mesmo que tudo mais esteja verde. Motivo: a avaliação de placement (passo 5) era a única camada da skill sem nenhum artefato de saída, então dava pra pular em silêncio e o relatório saía "completo" do mesmo jeito. Foi exatamente o que aconteceu no compraguia (2026-07-31).
   - **Uma passada por ARTIGO, não por link.** Pergunta: *"algum link deste guide está num parágrafo que não trata do tema do destino?"*. São ~N perguntas (N = artigos) em vez de uma por link — dá pra fazer de verdade, e o output é curto. Exigir veredito link a link geraria 60+ linhas de "✓ ok" por site, que vira carimbo, não análise.
   - **O que imprimir:** os artigos onde algo falhou (com o parágrafo citado e o encaminhamento: remover / mover / reescrever a frase). Se nada falhou, uma linha só: `N artigos avaliados, nenhum link fora de contexto`. **O que não pode é a seção não existir.**

7. **Gravar o marcador de auditoria** (registra QUANDO auditou — roda SEMPRE, logo após o relatório, mesmo que o user rejeite tudo depois; auditar é o evento):
   ```bash
   # raiz do repo — o cwd do Bash reseta pra ~/Documents/Claude em sessão continuada; sem isto o mkdir cria a árvore LÁ (medido 03/09/26)
   cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" && test -f docs/painel/sites-meta.json || { echo "⛔ cwd errado ($(pwd)): rode a partir da raiz do ProjetoAfiliados"; exit 1; }
   mkdir -p docs/biblias-v2/.audits/linkagem
   ```
   `Write` em `docs/biblias-v2/.audits/linkagem/{site}-last.md`: título (`# Auditoria de linkagem: {site}`), contagens (`- Erros: N · Avisos: M · Infos: K · Oportunidades: O`), a mesma linha "Não medido" do relatório (quem abrir o marcador depois precisa saber se o "0 erros" foi medido), lista curta dos tipos disparados (ou "nenhum"). **NÃO** invente timestamp (a fonte de tempo é o commit git).

8. **Aplicar o óbvio + esperar aprovação só do julgamento** (canon 2026-07-24): os fixes **determinísticos** (link-quebrado, link-home-errado, anchor-nao-keyword, anchor-produto-sem-nome + reconciliação de concordância, `anchor-frase-quebrada` de level=error) **aplicam direto** no passo 10 sem esperar, marcados ✅ CORRIGIDO. Só os de **julgamento** (link NOVO, mover peer-link-na-conclusao, linkagem-excesso) esperam aprovação granular: "aplica tudo" / "aplica 1,3" / "aplica canon" (por tema) / "rejeita 2" / "refaz 1". Se não houver nenhum de julgamento, pula a espera e vai pro build/commit. **Artigo de `rankeando[]` segue a seção "Artigo que já rankeia"**: dos determinísticos, só os do item 1 dela aplicam direto; os outros ficam no relatório.

9. **Backup** antes de aplicar (1 por artigo tocado):
   `docs/painel/.painel-backups/{YYYY-MM-DD}/article-{site}-{slug}-{HHMMSS}-guide.mdx` (via helper `readGuideContent` do painel, mesmo formato dos outros). Portado sem guia, com edição no `fullReview`: cópia do `.mdx` inteiro em `article-{site}-{slug}-{HHMMSS}.mdx`.

10. **Aplicar os óbvios + os aprovados** via `Edit` cirúrgico no `guideContent` do `.mdx` (ou no `fullReview`, no portado sem guia; preservar indent 2 espaços do block scalar; um trecho por vez). Regras:
    - **anchor-nao-keyword**: trocar SÓ o texto entre `<a>...</a>` pela keyword (qualificadores ficam FORA do `<a>`). **⚠ RECONCILIAR a concordância do artigo/preposição que vem ANTES do `<a>` (canon 2026-06-23):** se a âncora nova muda NÚMERO ou GÊNERO em relação à antiga, o artigo/contração que a rege precisa acompanhar. Caso real: âncora `melhores impressoras de tanque de tinta` (plural) virou `melhor impressora tanque de tinta` (singular) mas o "no guia **das**" ficou → "no guia das melhor impressora" (quebrado). Ajustes típicos: `das→da`, `dos→do`, `nas→na`, `nos→no`, `aos→ao`, `pelas→pela`, `essas→essa`, `umas→uma`. **Reler a FRASE INTEIRA do `<a>` tocado (não só o trecho da âncora) antes de salvar.** Quatro casos que a troca cria, medidos nos portados (22 e 24/09/2026): (a) **"melhor" já antes do link** ("sobre o melhor <a>robô aspirador com mapeamento</a>"): ele sai, porque a âncora nova já começa com "melhor"; (b) **"em" ou "qual" antes do link** ("comparar alternativas em <a>celular até 1300 reais</a>", "saber qual <a>robô…</a> combina"): a âncora antiga fechava a frase e a keyword não; é julgamento ("no guia de…", "qual o…"), então não aplique direto, proponha; (c) **âncora que já estava no plural, no portado:** vai para o `keywordPlural` (ver "Portados do WordPress", item 3); (d) **âncora que era um substantivo comum no meio da frase**: com "melhor", a frase continua gramatical e o sentido muda, e o script não acusa. No compraguia (24/09/2026), "quem utiliza o notebook para trabalho" virou "quem utiliza o melhor notebook para trabalho", e "um modem ou um roteador wifi tradicional" virou "o melhor roteador Wi-Fi tradicional"; as duas foram desfeitas na revisão. Leia a frase como leitor: se ela passou a dizer outra coisa, é julgamento. Proponha a troca da palavra colada ("quem procura o…") ou deixe a âncora do texto e anote no relatório. O script acusa (a) como error e (b) como warn ao rodar de novo no passo 12; (d) só aparece na leitura.
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

11.5. **Concordância artigo↔âncora: quem confere é o script (desde 22/09/2026), no passo 12.** Um conserto de âncora pode passar verde no `anchor-nao-keyword` e deixar "no guia **das** melhor impressora". O `audit-linkagem.ts` emite `anchor-frase-quebrada` para: artigo no número errado antes de âncora com "melhor"/"melhores" ("das melhor", "os melhor", "o melhores", inclusive com negrito dentro do link), "melhor" repetido fora do link, e "em"/"qual" + superlativo. O grep que ficava aqui pegou 1 de 7 casos de teste (não via "os/as" nem o negrito do WordPress).

    **Âncora sem "melhor"** ("impressora barata", "celular até 1000 reais"): o script tira o número da keyword do destino (âncora igual à keyword = singular), mas só quando a 1ª palavra dela não termina em "s". Sem esse recorte deu 11 falsos em 11 na rede: "creatinas" é keyword sem "melhor" que já é plural, e "das creatinas" está certo ("micro-ondas" e "tênis" são o mesmo caso). Então "das impressora barata" é pego, e keyword como "creatinas" fica para a releitura do passo 10.

    **Concordância de GÊNERO (`o melhor impressora`, `a melhor tablet`) fica FORA do determinístico — de propósito (canon 2026-07-31).** Tentei derivar o gênero do `title` do destino ("as N melhores" = feminino) e **medi 17% de acerto**: os títulos da rede usam `As 11 Melhores Whey Protein` e `As N Melhores Ômega 3` concordando com substantivo ELÍPTICO ("as melhores [opções]"), não com o núcleo da keyword. Resultado: `o melhor whey protein` e `o melhor ômega 3`, que estão **CORRETOS**, vinham como erro. Como esta skill aplica fix determinístico **sem aprovação**, um check assim viraria edição errada automática. Então: gênero é **julgamento** — ao reler a frase inteira do `<a>` tocado (passo 10), confira o artigo com o núcleo REAL da keyword, não com o título.

12. **Re-rodar `bun scripts/audit-linkagem.ts {site}`** pós-fix pra confirmar que os findings aprovados sumiram e nada regrediu (cada artigo 2-4 peers — hub isento; 0 `linkagem-excesso`; 0 órfãos e idealmente 0 sublinkados; 0 na Conclusão; 0 broken/home-errado).

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
