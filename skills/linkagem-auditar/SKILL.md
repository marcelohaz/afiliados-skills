---
name: linkagem-auditar
description: Audita E MELHORA a linkagem interna do SITE INTEIRO (cross-artigo), propor→aprovar. Roda os núcleos determinísticos (scripts/audit-linkagem.ts + audit-links.ts) + camada de julgamento LLM (placement contextual, links novos pra órfãos/sublinkados). Quantidade: 2 mín / ~3 ideal / 4 máx peers distintos por artigo; HUB (homeReviewSlug ou pillar:true) isento do teto. Conserta: link quebrado 404, /{homeReviewSlug}/→/, âncora≠keyword, âncora de produto sem marca, peer/home na Conclusão, excesso >4. contentLocked-aware (rerroteia a fonte). Aceita site OU URL do painel. Fecha com commit + push + painel-vps-pull + marcador .audits/linkagem/{site}-last.md.
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
| Julgamento: placement *genuinamente* contextual? links NOVOS naturais? | **só LLM** | **agrega valor + propõe** |
| Aplicar os fixes aprovados (Edit cirúrgico no guideContent) | **a skill** | **aplica on-approval** |

Não reescreva extração de link nem grafo — os scripts já fazem. O valor da skill é (1) **consolidar** as duas saídas, (2) a **camada de julgamento** (placement + oportunidades), e (3) **aplicar** o que o user aprovar.

## Pré-requisitos

- Site existe em `sites/{site}/` com `src/content/reviews/*.mdx`.
- `scripts/audit-linkagem.ts` e `scripts/audit-links.ts` existem (núcleo determinístico).
- `bun` no PATH.
- Artigos a editar NÃO travados (`contentLocked: true` → pular esse artigo e avisar; nunca editar travado sem destrave explícito).

## Invariantes

- **APLICA O ÓBVIO, PROPÕE O JULGAMENTO (canon Marcelo 2026-07-24, alinha com `biblia-auditar`).** Fix **determinístico de direção única** → **APLICA DIRETO** (sem esperar) e marca ✅ CORRIGIDO no relatório: `link-quebrado` (404 → slug REAL ou remover `<a>` mantendo texto), `link-home-errado` (`/{homeReviewSlug}/`→`/`), `anchor-nao-keyword` e `anchor-produto-sem-nome` (+ a reconciliação OBRIGATÓRIA de concordância artigo↔âncora, canon 2026-06-23), `anchor-frase-quebrada` **de level=error** (indefinido/qualificador + superlativo → artigo definido com contração: direção única, ver passo 10). **Julgamento** → **propor→aprovar** (imprime diffs e espera aprovação granular: "aplica tudo" / "aplica 1,3" / "aplica canon" / "rejeita 2"): **link NOVO** (adicionar), `peer-link-na-conclusao` (mover placement), `linkagem-excesso` (qual link cortar), `anchor-frase-quebrada` **de level=warn** (o "na/no" e o "qualquer" pedem escolha editorial: nomear o destino, usar plural ou reescrever), **REMOVER link fora de contexto**. Na dúvida, trate como julgamento (proponha). O relatório com TODOS os fixes (óbvios já aplicados + julgamento proposto) sai sempre.
- **EDIÇÃO CIRÚRGICA, nunca rewrite.** Só toca no trecho do `guideContent` com o fix aprovado (um `<a>`/`<p>` por vez). Resto do `.mdx` byte-a-byte intacto. Preserva o block scalar `|` (NUNCA parseYaml/stringify do frontmatter — sempre `Edit` no trecho-alvo).
- **NÃO inventa.** Findings determinísticos vêm dos scripts (verbatim). Os de julgamento (placement/oportunidade) citam o trecho real do guideContent. Link novo só com âncora = keyword real do destino + href = slug REAL (nunca derivado do keyword).
- **Escopo fechado.** CONSERTAR (404/home-errado/âncora/Conclusão/excesso>4) + ADICIONAR links novos contextuais (incl. reforçar órfão/sublinkado). `slug-vs-keyword` é só INFO (convenção, não se conserta — ver Critérios). **NÃO faz hub-and-spoke** (linkar produto órfão é decisão editorial à parte). **NÃO mexe em tag Amazon** (isso é `scripts/fill-affiliate-tag.ts`).
- **Régua de linkagem canônica** (igual artigo-guia-escrever/auditar): âncora de peer = keyword do destino (singular preferido); âncora de produto = nome completo COM marca; href = slug REAL; peer/home links contextuais e NUNCA na Conclusão (produto/Amazon na Conclusão = OK); home linkada via `href="/"` (nunca `/{homeReviewSlug}/`).
- **A FRASE em volta da âncora TEM que fechar (canon Marcelo 2026-07-31).** A keyword nomeia um **GUIA** ("melhor whey protein"), não um produto do mundo. Encaixá-la como se fosse coisa concreta produz frase que ninguém fala: *"combinar com **um melhor pré-treino**"*. Medição na rede: **64 ocorrências publicadas em 19 sites**, todas passando verde nos checks antigos — o defeito nasce de OBEDECER a régua de âncora=keyword sem olhar as palavras anteriores. O `audit-linkagem.ts` emite `anchor-frase-quebrada`.
  - **Por que o singular é o alvo (razão de SEO, não estética):** é a forma que as pessoas **buscam**, e a âncora do link interno reforça essa keyword. Trocar pro plural por conveniência gramatical joga fora esse sinal. Então, quando o singular não couber na frase, resolva **nesta ordem**:
    1. **Artigo definido** — `um melhor pré-treino` → `o melhor pré-treino`, **contraindo** a preposição que vier antes: `a um`→`ao`, `a uma`→`à`, `de um`→`do`, `em um`→`no`. Resolve a maioria e mantém o singular.
    2. **Moldura de destino** — `no guia de melhor pré-treino`, `o comparativo de melhor pré-treino`. Também mantém o singular, e é imune a concordância (a keyword vira complemento, sem artigo antes).
    3. **Plural** — `os melhores pré-treinos`. O script aceita (compara com `keyword` **ou** `keywordPlural`). Válvula de escape, não primeira opção. ⚠ 9 artigos da rede não têm `keywordPlural` preenchido; nesses, não está disponível.
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

  A moldura é o **padrão recomendado, não obrigatório**: link integrado ao texto continua válido quando passa nos checks de frase (ex.: *"vale olhar os melhores Kindles"*). O que não passa é a keyword enfiada como objeto de verbo no singular.
- **Régua de QUANTIDADE (canon Marcelo 2026-06-09): 2 mínimo · ~3 ideal · 4 máximo** peers DISTINTOS de saída, sempre **contextuais e naturais** (nunca decorativos). Não linkar o mesmo peer 2× no mesmo artigo. O **HUB** (artigo-cabeça: `homeReviewSlug` ou frontmatter `pillar: true`) é **isento do teto de 4** — ele linka todos os filhos (hub-and-spoke ideal). O script emite `linkagem-fraca` (<2) e `linkagem-excesso` (>4 não-hub); a régua "~3 ideal" é alvo de julgamento (mire 3 ao ADICIONAR), não um flag por-artigo.

⚠️ **O piso de 2 NÃO vence o "encaminhamento útil" (canon 2026-08-10) — vale sobretudo aqui, porque esta skill ADICIONA links.** Antes de propor um link novo pra resolver `linkagem-fraca`/`orfao`, aplique o teste da decisão: o link responde a uma **bifurcação** ("tablet ou Kindle?"), a uma **soma** ("whey + creatina?") ou a uma **ordem de prioridade** ("fecha a proteína antes da glutamina")? Se você precisa **construir o cenário** em que o leitor iria pro outro artigo, o cenário não existe e o link é protocolar. Nesse caso **NÃO proponha o link**: deixe o artigo em 0 peer e registre o `linkagem-fraca` como exceção justificada no relatório.

**PRÉ-CONDIÇÃO MECÂNICA — sem ela a exceção NÃO existe:** o artigo tem **ZERO peers da mesma `category`**. Conte antes de aceitar: `category` dos outros `.mdx` de `reviews/` do site. Havendo ao menos 1 irmão da mesma categoria, **o piso de 2 vale integral** e você DEVE propor o link. A exceção só cobre o artigo que é o primeiro da categoria dele num site que já tem outras. Isso é deliberado — exceção que é só julgamento vira atalho, e foi exatamente assim que a régua qualitativa perdeu pro piso numérico.

Não é hipótese: em 2026-08-10 o `compraguia/melhor-caixa-de-som-jbl` (artigo de áudio num site de impressora/tablet/Kindle, **0 peers da mesma categoria**) ganhou 2 links de tablet só pra bater o piso, e eles foram removidos depois. **Esta skill é justamente a que os traria de volta.** E não adianta cortar por categoria: dos 942 links peer da rede, 229 são cross-categoria e **227 passam no teste da decisão** (34 E-reader↔Tablet, 174 entre suplementos, 17 de fitness). Ver "Desempate" na `artigo-guia-escrever`.
- **Sem travessão.** Português brasileiro editorial.

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
   Parse: `{ counts, findings:[{level,type,article,message}], homeReviewSlug, affiliateTag, totalArticles, inboundPeers }`. **`inboundPeers[slug]` = array dos OUTROS reviews que já linkam pra `slug` (grafo de entrada, peers distintos; hub/produto/home fora).** É a fonte pra calcular o delta de inbound de cada link novo — ver régua E no passo 5. NÃO recompute o grafo na mão.

4. **Rodar a validade de links** (estrutural por padrão; só Amazon/internos, sem fetch):
   ```bash
   bun scripts/audit-links.ts {site} --no-fetch --json
   ```
   Use SÓ pra contexto (tag/404 interno). **Não conserte tag aqui** — só reporte que `fill-affiliate-tag.ts` resolve.

4.5. **Links nascidos no TEMPLATE (canon 2026-09-02).** Tabela de specs, "Produtos testados", cards de categoria e o `sitemap-produtos.xml` montam `href` que não estão em campo nenhum do `.mdx`, então os passos 3 e 4 **não os veem** — foi assim que esta skill disse "limpo" com 12 links 404 no ar (creatina, ago/2026). Se `sites/{site}/dist/` existe e é mais novo que o último commit que tocou o site, rode:
   ```bash
   bun scripts/check-dist-links.ts {site} --json
   ```
   Cada destino 404 vira **conserto proposto** no relatório. A causa quase sempre é **produto citado em artigo sem página individual**: o fix é criar a página (`pagina-produto-criar`), **nunca remover o link** (decisão Marcelo 2026-09-01: o template linka sem condicional; a página é que tem que existir). O `audit-article.ts` (rule `produto`) já acusa isso por artigo. Sem dist fresco: **diga no relatório que essa classe não foi verificada** — a pré-checagem de deploy do painel e o `cf-deploy-r2.ts` rodam o mesmo check antes de subir.

5. **Camada de julgamento LLM** (o valor que script não dá). O JSON do `audit-linkagem.ts` traz `lockedArticles[]` (fontes travadas) e `pillarArticles[]` (hubs isentos do teto) — use os dois. Read os `.mdx` dos artigos com links peer/home + os com FAQ/seções relevantes. Avalie:
   - **Placement genuinamente contextual?** Para cada link peer/home existente, o parágrafo onde ele está fala MESMO do tema do destino? "Fora da Conclusão" é necessário mas não suficiente. Sinalize os fracos com spot melhor. **Régua de spot (canon Marcelo): o link cai na MELHOR posição do artigo pro tema** — ex: link pro "melhor impressora para fotos" entra no parágrafo/H3 que fala de fotografia, não num lugar genérico.
   - **REMOVER link que não faz sentido ali (canon Marcelo 2026-07-31).** Até 2026-07-31 a skill só sabia **consertar** (404/âncora/home) e **adicionar** — não havia NENHUM gatilho que produzisse "esse link não cabe aqui, tira". Consequência real: na 1ª passada do compraguia entreguei "0 erros · 0 avisos" com três links tablet→impressora vivos, porque nenhum check os questionava; só foram removidos quando o Marcelo apontou. Agora: link cujo parágrafo **não trata do tema do destino** é candidato a REMOÇÃO (não só a mover), **preservando a prosa** — tira o `<a>` e reescreve a frase pra ela continuar fazendo sentido sem o link.
     - **⚠ GUARDA DE GRAFO, obrigatória antes de propor remoção:** remover `A→B` derruba `inboundPeers[B]` de N pra N-1. Confira que **N-1 ≥ 2**; se não, proponha o link substituto (de preferência intra-cluster) **junto** com a remoção, no mesmo lote. Sem isso a remoção cria órfão/sublinkado e a régua E é violada pelo próprio fix. Caso real (compraguia 2026-07-31): removi 3 links e repus 1 intra-cluster pra não derrubar o inbound do destino.
     - Remoção é **julgamento** → propor→aprovar, nunca aplicar direto.
   - **Oportunidades de links NOVOS.** Há FAQ/H3/seção que toca no tema de um peer ainda não-linkado (ou pouco-linkado), onde um link cairia natural? Liste só as genuinamente naturais — NUNCA force link decorativo. Para cada: artigo origem, peer destino, **spot exato** (cite a frase âncora), **âncora sugerida** (= keyword singular do destino), e o **Edit proposto** (frase antes → depois).
   - **`contentLocked`-aware (régua D):** se a FONTE natural de um link novo está em `lockedArticles[]`, NÃO proponha editá-la (artigo travado = SEO estável). Em vez disso **rerroteie**: ache outra fonte NÃO-travada que cubra o mesmo tema do destino, ou registre a oportunidade como "bloqueada (fonte travada — destravar p/ aplicar)" sem aplicar. Nunca edite travado sem destrave explícito do user.
   - **Balanço do grafo — `sublinkado` é PADRÃO, não opcional (régua E, canon 2026-06-09).** Todo artigo deve receber **≥2 inbounds**. `orfao` (0 inbound) e `sublinkado` (1 inbound) são metas de QUALIDADE da skill, no mesmo nível dos consertos — não trate como "info ignorável". Para cada órfão/sublinkado, proponha 1-2 links contextuais de fontes que tocam o tema (respeitando contextualidade e o teto de 4 da fonte). Caso real: na 1ª passada do impressoraideal tratei sublinkado como opcional e só consertei defeitos — a barra de qualidade certa é reforçar autoridade de todo nó sublinkado.
     - **⚠ Delta de inbound via `inboundPeers` (canon 2026-07-04) — o link pra fixar sublinkado/órfão TEM que ser INBOUND ao nó.** Consumir `inboundPeers[slug]` do `--json` (passo 3) pra raciocinar sobre o grafo, NÃO recomputar na mão. Um link `A→B` proposto leva `inboundPeers[B]` de N pra N+1 (aumenta o inbound de **B**, o DESTINO). Logo: pra tirar `X` de sublinkado/órfão, a fonte é OUTRO artigo e o **destino é `X`** (`A→X`) — um link `X→A` (saindo de X) NÃO ajuda o inbound de X. Ao propor, confirme que `inboundPeers[X].length + (novos links inbound propostos pra X) ≥ 2`, e que a fonte `A` escolhida ainda NÃO está em `inboundPeers[X]` (senão é `peer-repetido`, não ganha inbound distinto). No relatório, anote pra cada nó tocado o inbound projetado (ex: `melhor-ipad: 1 → 2 ✓`). Causa-raiz (2026-07-04): sem esse delta explícito, rotulei um link OUTBOUND como se resolvesse o sublinkado do próprio artigo-fonte — só a re-auditoria do passo 12 pegou. O `inboundPeers` torna o delta verificável ANTES de aplicar.

6. **Montar o relatório** (formato abaixo) com TODOS os fixes numerados (consertos + links novos), cada um com o diff `ANTES → DEPOIS`, marcando quais são **óbvios/determinísticos** (aplicam direto) e quais são **julgamento** (esperam aprovação). **Imprime inline.**

   **⚠ A seção `## 🔗 Placement avaliado` é OBRIGATÓRIA (canon Marcelo 2026-07-31)** — sem ela o relatório está INCOMPLETO, mesmo que tudo mais esteja verde. Motivo: a avaliação de placement (passo 5) era a única camada da skill sem nenhum artefato de saída, então dava pra pular em silêncio e o relatório saía "completo" do mesmo jeito. Foi exatamente o que aconteceu no compraguia (2026-07-31).
   - **Uma passada por ARTIGO, não por link.** Pergunta: *"algum link deste guide está num parágrafo que não trata do tema do destino?"*. São ~N perguntas (N = artigos) em vez de uma por link — dá pra fazer de verdade, e o output é curto. Exigir veredito link a link geraria 60+ linhas de "✓ ok" por site, que vira carimbo, não análise.
   - **O que imprimir:** os artigos onde algo falhou (com o parágrafo citado e o encaminhamento: remover / mover / reescrever a frase). Se nada falhou, uma linha só: `N artigos avaliados, nenhum link fora de contexto`. **O que não pode é a seção não existir.**

7. **Gravar o marcador de auditoria** (registra QUANDO auditou — roda SEMPRE, logo após o relatório, mesmo que o user rejeite tudo depois; auditar é o evento):
   ```bash
   mkdir -p docs/biblias-v2/.audits/linkagem
   ```
   `Write` em `docs/biblias-v2/.audits/linkagem/{site}-last.md`: título (`# Auditoria de linkagem: {site}`), contagens (`- Erros: N · Avisos: M · Infos: K · Oportunidades: O`), lista curta dos tipos disparados (ou "nenhum"). **NÃO** invente timestamp (a fonte de tempo é o commit git).

8. **Aplicar o óbvio + esperar aprovação só do julgamento** (canon 2026-07-24): os fixes **determinísticos** (link-quebrado, link-home-errado, anchor-nao-keyword, anchor-produto-sem-nome + reconciliação de concordância) **aplicam direto** no passo 10 sem esperar, marcados ✅ CORRIGIDO. Só os de **julgamento** (link NOVO, mover peer-link-na-conclusao, linkagem-excesso) esperam aprovação granular: "aplica tudo" / "aplica 1,3" / "aplica canon" (por tema) / "rejeita 2" / "refaz 1". Se não houver nenhum de julgamento, pula a espera e vai pro build/commit.

9. **Backup** antes de aplicar (1 por artigo tocado):
   `docs/painel/.painel-backups/{YYYY-MM-DD}/article-{site}-{slug}-{HHMMSS}-guide.mdx` (via helper `readGuideContent` do painel, mesmo formato dos outros).

10. **Aplicar os óbvios + os aprovados** via `Edit` cirúrgico no `guideContent` do `.mdx` (preservar indent 2 espaços do block scalar; um trecho por vez). Regras:
    - **anchor-nao-keyword**: trocar SÓ o texto entre `<a>...</a>` pela keyword (qualificadores ficam FORA do `<a>`). **⚠ RECONCILIAR a concordância do artigo/preposição que vem ANTES do `<a>` (canon 2026-06-23):** se a âncora nova muda NÚMERO ou GÊNERO em relação à antiga, o artigo/contração que a rege precisa acompanhar. Caso real: âncora `melhores impressoras de tanque de tinta` (plural) virou `melhor impressora tanque de tinta` (singular) mas o "no guia **das**" ficou → "no guia das melhor impressora" (quebrado). Ajustes típicos: `das→da`, `dos→do`, `nas→na`, `nos→no`, `aos→ao`, `pelas→pela`, `essas→essa`, `umas→uma`. **Reler a FRASE INTEIRA do `<a>` tocado (não só o trecho da âncora) antes de salvar.**
    - **anchor-produto-sem-nome**: trocar o texto pelo nome completo do produto (com marca). **Mesma reconciliação de concordância do item acima** (ex: âncora que era plural genérico vira nome próprio singular → ajustar artigo antes).
    - **anchor-frase-quebrada (error)**: NÃO toca na âncora (ela já está certa = keyword). Troca o **artigo indefinido que vem ANTES** pelo definido, **contraindo** a preposição anterior: `um`→`o`, `uma`→`a`, `a um`→`ao`, `a uma`→`à`, `de um`→`do`, `em um`→`no`. Se havia qualificador (`um bom melhor whey` → `o melhor whey`), ele sai junto (era redundante com o superlativo). ⚠ **Reler a frase inteira depois**, incluindo o gênero do artigo — o gênero NÃO é validado pelo script (ver 11.5) e é você quem confere contra o núcleo real da keyword.
    - **anchor-frase-quebrada (warn)**: é julgamento, espera aprovação. `na/no` que não retoma nada → nomear o destino (`no guia de {keyword}`) ou usar o plural. `qualquer` + superlativo → reescrever a frase.
    - **REMOVER link fora de contexto** (aprovado no julgamento): tira o `<a>` mantendo/reescrevendo a prosa pra frase seguir fazendo sentido sem ele. Aplicar **junto** com o link substituto quando a guarda de inbound exigir (ver passo 5).
    - **link-home-errado**: trocar `href="/{homeReviewSlug}/"` por `href="/"` (manter a âncora = keyword da home).
    - **link-quebrado**: corrigir o href pro slug REAL (confirmar o arquivo existe) OU, se não há destino, remover o `<a>` mantendo o texto.
    - **peer-link-na-conclusao**: MOVER o link pro spot contextual aprovado (remover da Conclusão + inserir no parágrafo-alvo). Produto/Amazon na Conclusão ficam.
    - **link novo**: inserir o `<a>` no spot exato aprovado, âncora = keyword singular do destino, href = slug REAL (`/slug/` ou `/` pra home), sem `rel`/`target` (interno passa autoridade).

11. **Build** (gate): `pnpm --filter {site} build`. Se Zod/Astro falhar, reverter do backup e reportar.

11.5. **AUTO-CHECK de concordância artigo↔âncora (OBRIGATÓRIO, canon 2026-06-23):** o `audit-linkagem.ts` valida âncora=keyword mas NÃO olha a gramática da frase em volta — então um conserto de âncora pode passar verde e mesmo assim deixar "no guia **das** melhor impressora". Pra cada artigo tocado, grep:
    ```bash
    grep -nE '\b(das|dos|nas|nos|aos|pelas|pelos) +<a [^>]*>\s*(melhor|impressora|tablet|opção)\b' sites/{site}/src/content/reviews/*.mdx
    ```
    Qualquer match = artigo plural regendo âncora singular → corrigir o artigo (`das→da` etc). **O `\b` é OBRIGATÓRIO:** sem ele, `melhor` casa `melhores` e `tablet` casa `tablets`, e "das melhores creatinas"/"nos tablets Lenovo" (plural+plural, CORRETO) viram falso-positivo. Com `\b`, só pega `das melhor` / `nos tablet` singular. Esse check pega a regressão clássica do anchor-fix isolado. Sem matches → ok.

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

- `link-quebrado` (error), `link-home-errado` (error), `linkagem-fraca` (warn, <2 peers distintos de saída), `linkagem-excesso` (warn, >4 peers distintos num artigo NÃO-hub — enxugar pros 3-4 contextuais ou marcar `pillar:true`), `peer-repetido` (warn), `anchor-nao-keyword` (warn), `anchor-frase-quebrada` (**error** = indefinido/qualificador antes de âncora com superlativo, ex. "um melhor pré-treino" — fix: artigo definido contraindo a preposição, ver Invariantes; **warn** = "na/no" que não retoma guia/artigo, ou "qualquer" + superlativo, que pedem reescrita), `anchor-produto-sem-nome` (warn), `slug-vs-keyword` (**info** — convenção comum na rede, ~23% dos artigos; o 404 real já é coberto por link-quebrado/link-home-errado; NÃO é defeito a consertar), `peer-link-na-conclusao` (info), `hub-and-spoke-incompleto` (info, **1 linha-resumo colapsada** — **fora de escopo desta skill**), `orfao` (warn)/`sublinkado` (info, mas **acionável** — ver régua E no passo 5).

## Armadilhas

1. **Reimplementar grafo/extração.** Os scripts já fazem — rode e leia o JSON.
2. **Rewrite do guide.** É cirúrgico por trecho; nunca reescreva o guide inteiro (isso é `artigo-guia-escrever`).
3. **parseYaml/stringify no frontmatter.** Bagunça o block scalar `|`. Sempre `Edit` no trecho.
4. **Forçar link novo decorativo.** Só proponha se o spot REALMENTE toca no tema do destino. Melhor 0 honestas que 5 forçadas.
5. **Aplicar JULGAMENTO sem aprovar.** O mecânico (âncora=keyword, link quebrado, `/{homeReviewSlug}/`→`/`) aplica direto (canon 24/07); links novos e placement (julgamento) imprimem os diffs e esperam.
6. **Esquecer `--no-verify`.** O hook Fase J bloqueia `reviews/*.mdx`.
7. **Editar artigo travado.** `contentLocked: true` → pular + avisar.
8. **Achar que o painel não atualiza.** Atualiza: `/admin/update` roda `gen.ts` full → `linkagem-{site}.html` regenera. Não precisa de passo extra.

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
