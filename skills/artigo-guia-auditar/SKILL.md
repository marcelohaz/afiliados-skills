---
name: artigo-guia-auditar
description: Audita o guideContent de um artigo E aplica correções CIRÚRGICAS por seção (nunca rewrite total) — contraparte da artigo-reviews-auditar pro guide. Aceita URL do painel OU site/slug. Critérios: produto do lineup fora do guide, claim stale, estrutura 5 H2, tamanho, HTML allowlist, links hub-and-spoke, link quebrado, peer na Conclusão, âncora≠keyword, travessão, voz-comprador, chavões por nicho, superlativo sem lastro, naturalidade (palavra fora do sentido/verbo-curinga, frase-sacada, molde de seção), concordância PT-BR, e faq-order-shuffle (anti-footprint determinístico — só reordena a FAQ, não muda redação). Relatório com diffs por seção; user aprova granular ('aplica 1,3' / 'aplica tudo'). Usa artigo-guia-escrever (rewrite total) só com guia ausente/stub ou 3+ H2 faltando.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**`PIPELINE=yes`** (opcional, canon 2026-08-15): passado pela clone/fila. Efeito: aplica óbvio E julgamento (auto-fix, máx 3 rodadas), não espera aprovação, não encerra o turno para perguntar. Sem a flag, propor→aprovar normal.

**A) URL do painel** (forma preferida):
- `https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=impressora-barata`
- Extrai `site` e `slug` do query string

**B) Args canônicos**:
- `melhorimpressora/impressora-barata`

Detecção: começa com `https://` → caminho A. Senão → caminho B (split por `/`).

# Auditar/corrigir o guia de um artigo (cirúrgico)

> Versão executável local. Op canônico correspondente: `agent-prompts.json:improve_guide` (prompt-espelho do painel/API, esta SKILL.md é a fonte viva; botão no painel é follow-up — ver "Sincronização" no fim). Compartilha a régua de guia com `artigo-guia-escrever` e os critérios de guia com `artigo-auditar`.

Você é o editor do **guide** no estilo cirúrgico. O usuário passa `{site}/{slug}` de um artigo cujo `guideContent` já existe (≥3 H2). Sua função é **auditar o guia** contra a régua canônica e **propor correções CIRÚRGICAS por seção** pra user aprovar — sem reescrever o guia do zero.

## Diferença vs as skills vizinhas

| Skill | O que faz no guide | Tipo |
|---|---|---|
| `artigo-auditar` | Diagnostica o guide (10 critérios: estrutura, tamanho, allowlist, links hub-and-spoke, peer na conclusão, link quebrado, slug-vs-keyword, linkagem fraca, peer não linkado, âncora) | Read-only |
| `artigo-guia-escrever` | Gera/reescreve o `guideContent` **inteiro** do zero | Write (rewrite total) |
| **`artigo-guia-auditar`** (esta) | Audita + **corrige cirúrgico por seção** (preserva o resto) | Write (cirúrgico) |

Esta skill é pra `artigo-guia-escrever` o que `artigo-reviews-auditar` é pra `artigo-review-criar`: o par "audita + conserta o que está errado" sem refazer tudo.

**Quando NÃO usar esta skill (usar `artigo-guia-escrever` em vez):**
- `guideContent` ausente ou stub (`''` ou < 100 chars) → não há o que consertar, gere do zero.
- Guia estruturalmente quebrado: **3+ H2 obrigatórios faltando** OU fora de tema → rewrite é mais barato que remendar.
- User quer reconteúdo afinado com concorrentes novos (SERP mudou) → `artigo-guia-escrever` com os textos colados.

Pra tudo mais (lineup mudou, 1 link quebrado, 1 FAQ faltando, 1 H2 ausente, travessão, anchor errado, claim stale, violação de allowlist), **esta skill é o caminho** — cirúrgica, barata, sem risco de estragar o que já rankeia.

## Pré-requisitos

- Artigo existe em `sites/{site}/src/content/reviews/{slug}.mdx`.
- `guideContent` no frontmatter, trim > 100 chars (senão → abortar orientando `artigo-guia-escrever`).
- Bíblias dos produtos do lineup em `docs/biblias-v2/{ASIN}.json` (pra checar claims). Se faltar, `bun scripts/sync-biblias-r2.ts --apply`.
- Artigo NÃO travado (`contentLocked: false` ou ausente). Se `true`, abortar com "destrave antes".
- `affiliateTag` em `sites/{site}/src/config.ts` (vazia OU preenchida — define a regra dos links Amazon).
- `homeReviewSlug` em `sites/{site}/src/config.ts` (pode ser undefined) — pra checar link-interno-quebrado.

## Invariantes

- **EDIÇÃO MÍNIMA, NUNCA REWRITE.** Só toca nas seções/trechos com violação clara. O resto do `guideContent` fica byte-a-byte intacto. Se você está reescrevendo o guia inteiro, está usando a skill errada.
- **CONVERGÊNCIA.** Seção que já passa em todos os critérios não entra em `changes`. Re-run no mesmo guia não deve gerar mudança aleatória.
- **APLICA O ÓBVIO, PROPÕE O JULGAMENTO (canon Marcelo 2026-07-24, alinha com `biblia-auditar`).** Fix **determinístico de direção única** → **APLICA DIRETO** (sem esperar) e marca ✅ CORRIGIDO no relatório: `faq-order-shuffle` (reorder por seed idempotente, zero mudança de redação), `link-interno-quebrado` (href pro slug REAL / remover `<a>` mantendo texto), `link-home-errado` (`/{homeReviewSlug}/`→`/`), `anchor-nao-keyword` e `peer-article-nao-linkado` de âncora (+ a reconciliação de concordância artigo↔âncora), `travessao`, `;`, `concordancia-pt-br`. **Julgamento** → **propor→aprovar** (espera aprovação granular): `voz-comprador`, `superlativo-sem-evidencia`, `naturalidade`, `peer-link-na-conclusao` (mover placement), reescrita de texto, adicionar conteúdo. Na dúvida, trate como julgamento (proponha).
- **Preservar o block scalar `|`.** NUNCA parseYaml/stringifyYaml o frontmatter (bagunça o HTML multilinha). Sempre `Edit` cirúrgico no trecho-alvo do `guideContent`.
- **Preservar tudo fora do `guideContent`.** Não tocar em title, description, keyword, products, intro do body.
- **Sem travessão (—).**
- **Sem inventar.** Cada claim novo (ex: ao integrar um produto) tem origem rastreável na bíblia do ASIN.
- **Régua de guia canônica** (igual `artigo-guia-escrever`): 5 H2 na ordem, allowlist h2/h3/p/ul/ol/li/strong/em/a/br, links Amazon tag-aware em FAQ/Marca/Conclusão, hub-and-spoke pra peers, sem voz-comprador.
- **Português brasileiro editorial**, tom analítico.

## Fluxo

1. **Parse args**: detecta URL vs canônico, extrai `site` e `slug`. Valida `[a-z0-9-]+`.

1.5. **Git pull antes de ler** (CRÍTICO — evita estado stale):
   ```bash
   bash scripts/git-pull-seguro.sh "skill-artigo-guia-auditar-temp"
   ```
   Se pull falhar, seguir mesmo assim (documentar no relatório).

2. **Read `.mdx`**: `Read sites/{site}/src/content/reviews/{slug}.mdx`. Se 404, abortar. Se `contentLocked: true`, abortar ("destrave antes").

3. **Extrair do frontmatter**: `keyword`, `keywordPlural`, `products[]` (ASIN + name + slug derivado), `guideContent` (block scalar). Se `guideContent` trim < 100 chars → abortar ("guia ausente/stub — use `artigo-guia-escrever`").

4. **Read bíblias** dos produtos do lineup (pra checar claims do guia + ter dados ao integrar produto faltante).

5. **Read `affiliateTag` + `homeReviewSlug`** de `sites/{site}/src/config.ts`. Read `live` de `sites-meta.json[{site}].live`.

6. **Listar peers do site**: glob `sites/{site}/src/content/reviews/*.mdx` (peer articles) + `sites/{site}/src/content/products/*.mdx` (páginas de produto) — pra checar link-interno-quebrado, peer-article-nao-linkado e anchor-nao-keyword.

7. **Rodar os critérios** (seção abaixo). Gerar `changes` (issues com fix cirúrgico proposto) e `passed`.

8. **Decisão rewrite vs cirúrgico**: se 3+ H2 obrigatórios faltando OU guia fora de tema → NÃO propor remendos; recomendar `artigo-guia-escrever` e encerrar. Senão, seguir cirúrgico.

9. **Reportar em chat** (formato abaixo) + **aplicar o óbvio, esperar aprovação só do julgamento** (canon 2026-07-24): os fixes **determinísticos** (faq-shuffle, link quebrado/home-errado, âncora-keyword/produto-sem-nome + concordância, travessão, `;`, concordância PT-BR) **aplicam direto** no passo 11 sem esperar, marcados ✅ CORRIGIDO. Só os de **julgamento** (voz-comprador, superlativo, naturalidade, mover placement, reescrita) esperam aprovação granular ("aplica tudo" / "aplica 1,3" / "rejeita 2"). Se não houver nenhum de julgamento, pula a espera.

9.5. **Gravar marcador de auditoria** (registra QUANDO o guia foi auditado — alimenta a pill "Guia auditado", o chip "Auditar Guia" da barra FALTAM e o log de atividade do editor-artigo). Roda **SEMPRE**, logo após o relatório, mesmo que o user depois rejeite todas as correções (auditar é o evento; aplicar é outro):
   - `Write` em `docs/biblias-v2/.audits/guide/{site}-{slug}-last.md` com: título (`# Auditoria do guia: {site}/{slug}`), `- Critérios checados: {N}`, `- Achados: {M}` (+ lista curta dos critérios disparados, ou "nenhum"). A data é só pra leitura humana — **NÃO** invente timestamp pra sort (a fonte de tempo é o commit do git; `Date().toISOString()` cai no bug de timezone). Crie o diretório se não existir.
   - Commit + push + VPS pull:
     ```bash
     git add docs/biblias-v2/.audits/guide/{site}-{slug}-last.md
     git commit --only --no-verify -m "audit-guia({site}): {slug} ({M} achados)" \
       -- docs/biblias-v2/.audits/guide/{site}-{slug}-last.md
     git push origin main
     bash scripts/painel-vps-pull.sh
     ```
   - **Por quê:** o nome `-last.md` (sem dígitos de data) NÃO cai no `.gitignore` de audits timestampados → fica TRACKED e sincroniza. O editor lê via `git log` (`/article/:site/:slug/activity`), então o evento aparece em qualquer máquina. O prefixo `audit-guia(` faz o editor classificar como auditoria de guia (chip "Auditar Guia" some, pill "Guia auditado" registra). Sem este passo, "Guia auditado" fica "sem registro" pra sempre.

10. **Backup** antes de aplicar: `docs/painel/.painel-backups/{YYYY-MM-DD}/article-{site}-{slug}-{HHMMSS}-guide.mdx`.

11. **Aplicar** os fixes óbvios + os aprovados via `Edit` cirúrgico no `guideContent` (preservar indentação de 2 espaços do block scalar; um bloco por linha).

12. **Build**: `pnpm --filter {site} build`. Se Zod falhar, reverter do backup e reportar.

13. **Git add + commit (`--no-verify`) + push + VPS pull**:
   ```bash
   git add sites/{site}/src/content/reviews/{slug}.mdx
   git commit --only --no-verify -m "fix({site}): auditoria cirúrgica do guia de {slug} via skill" \
     -- sites/{site}/src/content/reviews/{slug}.mdx
   git push origin main
   bash scripts/painel-vps-pull.sh
   ```
   `--no-verify` necessário (hook Fase J bloqueia commit direto de `reviews/*.mdx`; a skill é o caminho oficial).

14. **Reportar resultado**: seções aplicadas + path do backup.

## Critérios da auditoria do guia

### `ymyl-aviso-repetido` — poda do excedente (🟡, canon 2026-06-25 + 2026-07-30)

A régua limita o aviso "procure um médico/nutricionista" a **1 por ARTIGO**. Quem
CONTA é a `artigo-auditar` (única com escopo de artigo inteiro); esta skill **poda a fatia do `guideContent`**.

Rode o mesmo script que ela usa, para não inventar regex próprio:

```bash
python3 .claude/skills/artigo-auditar/ymyl-avisos.py sites/{site}/src/content/reviews/{slug}.mdx --json
```

Ele já marca cada ocorrência como `KEEP` ou `PODA` e diz em que seção está. **Você aplica só as `PODA` cujo `secao` é `guide`** — as dos reviews são da
`artigo-reviews-auditar`, e o `KEEP` fica.

⚠ O `KEEP` quase sempre É do guide (a regra elege o guide como sobrevivente), então
na prática você poda o 2º aviso do guide em diante, não todos.

⚠ **Fato de rótulo NÃO entra na poda** (achado da Bárbara, 2026-08-30). Aviso que
  cita fabricante, embalagem ou bula, ou que amarra idade e dose — "o fabricante
  orienta que crianças até 3 anos só consumam sob orientação de pediatra", "o
  próprio rótulo avisa que dose acima de 2 comprimidos só com indicação médica" —
  é **informação de produto**, da mesma classe de dose e alérgeno, e é exatamente
  o caso que a régua manda MANTER ("só quando o ponto é genuinamente sensível,
  ex.: contraindicação real de um produto específico"). O `KEEP`/`PODA` do script
  é POSICIONAL e não distingue: já marcou PODA no fato de rótulo e KEEP no
  disclaimer genérico, invertendo o valor. **Quando isso acontecer, ignore o
  script.** Não há classificador de propósito — a fronteira não é nítida e ler
  2 ou 3 trechos custa menos que errar no automático.

⚠ **Só APAGA quando o aviso é frase inteira ou oração removível deixando o texto
válido.** Se tirar exigir reescrever a frase em volta, é prosa nova: vai pro
relatório, não aplica. Exemplos reais do pior caso da rede:
- `"Por ser suplemento infantil, o uso pede acompanhamento do pediatra."` → frase
  inteira, APAGA.
- `"...praticidade na nutrição infantil, sempre com a orientação de um profissional
  de saúde."` → a oração final sai e a frase fica de pé, APAGA a oração.
- `"...a partir dos 4 anos com orientação do pediatra."` dentro de uma
  `shortDescription` que só tem essa frase → apagar deixaria o campo sem fecho:
  REPORTA.

**Severidade 🟡 e não 🔴:** aviso a mais não é erro de fato nem risco ao leitor,
é repetição que cansa. Não bloqueia nada.

### 1. `produto-no-lineup-fora-do-guide` (level=`warn`) — O CRITÉRIO-CHAVE

O motivo nº1 desta skill existir. Quando o `products[]` do artigo cresce (produto adicionado depois do guia ser escrito), o guia fica **stale**: não menciona nem linka o produto novo.

**Como detectar**:
1. Pra cada produto do `products[]`: derivar `name` + `slug` (slugify do name) + `marca`.
2. Conferir se o guia menciona o `name` (ou marca, se a seção "Melhor marca" for por-marca) OU linka `/{slug}/`.
3. Se um produto do lineup **não aparece em lugar nenhum** do guia → flag.

**Fix cirúrgico proposto** (NÃO rewrite): integrar o produto na **seção mais natural**, com 1 frase + link interno + 1 diferencial da bíblia:
- Laser/mono → FAQ "Impressora laser vale a pena em casa?" ou similar.
- Tanque colorido → FAQ "imprimir muito e gastar pouco?" ou seção de marca.
- Cartucho entrada → FAQ "imprime pouco?".
- Se não houver FAQ temático, adicionar 1 frase no "resumo por perfil" da seção "Melhor marca" ou na Conclusão.

**Caso real (2026-06-05, impressora-barata)**: Brother HL-L1232W entrou como 5º produto (2º laser) depois do guia; o guia linkava 4 de 5 e tratava laser como "a impressora laser da HP". Fix: 1 frase no FAQ laser + link `/brother-hl-l1232w/` + diferencial (toner inicial 1.500 págs). 1 Edit, sem rewrite.

### 2. `claim-vs-lineup-stale` (level=`error` se factualmente errado)

Claim no guia que era verdade mas ficou **falso** porque o lineup mudou:
- "a única laser desta lista" → agora há 2 lasers.
- "o mais barato é o X" → produto novo é mais barato.
- "as três opções" → agora são 5.

Cruzar claims numéricos/contagem/exclusividade contra o `products[]` atual + `schemaPrice`. Fix: reescrever o trecho pro escopo verdadeiro ("uma das mais rápidas", "entre as opções") — mesmo padrão do `claim-vs-lineup-fato` do `artigo-reviews-auditar`.

### 3. `guide-estrutura` (level=`warn`; `error` se 1 H2 obrigatório faltando)

5 H2 **base** obrigatórios na ordem: **Vale a pena → Como escolher → Melhor marca → FAQ → Conclusão** (+ opcional "Por que confiar" entre FAQ e Conclusão, igual `artigo-auditar`/`artigo-guia-escrever`). **H2 extras informacionais dirigidos pela SERP são permitidos** (canon 2026-06-29; teto 9 H2 total; sem link Amazon; não são "desordem") — não flagrar. Sem H1. Faltar 1 dos 5 base = error (paridade com a régua comum em `docs/PADROES.md`).
- 1-2 H2 faltando → propor **inserir** a(s) seção(ões) faltante(s) cirurgicamente (com conteúdo derivado das bíblias/peers), na posição canônica.
- 3+ faltando OU fora de ordem grave → recomendar `artigo-guia-escrever` (rewrite).

### 4. `guide-tamanho` (level=`info`)
6000-25000 chars (alvo 12-18k). < 6000 → "aprofundar" (info). > 25000 → "condensar" (info). Não bloqueia.

### 5. `guide-html-allowlist` (level=`error`)
Permitidas: `<h2> <h3> <p> <ul> <ol> <li> <strong> <em> <a href rel target> <br>`. Proibidas: `<h1> <h4>-<h6> <table>/<tr>/<td> <img> <picture> <video> <iframe> <script> <style> <div> <span>`. Fix cirúrgico: converter `<table>` → `<ul>`/`<p>`, desembrulhar `<div>`/`<span>`, remover mídia.

### 6. `guide-links-hub-and-spoke` (tag errada: `error` se live / `warn` em construção; posição: `info`)
- Links Amazon (`/dp/`): flag só tag **diferente** da do config (ou `AFFILIATE_TAG_AQUI`); URL crua é OK (o build injeta a tag — canon 2026-08-15). Severity da tag errada igual `artigo-auditar` (live=true → error; live=false → warn).
- "Vale a pena" e "Como escolher" devem ter **0 links AMAZON** (seções educativas, sem CTA de compra). Link Amazon nelas → warn (paridade com `artigo-auditar`; é violação de régua dura, não polimento). (Link interno peer/home contextual nessas seções É permitido — é navegação, não CTA.)
- FAQ/Marca/Conclusão: links de produto/Amazon OK; preferir link interno pra peer sobre Amazon (info).

### 6b. `peer-link-na-conclusao` (level=`info`, v1.24.0)
Links de **navegação peer-article/home** concentrados na **Conclusão** → flag info. Régua (Marcelo, 2026-06-05): "evitar colocar na conclusão (ou não colocar mesmo). tem que ser contextual." Link de navegação no fecho é decorativo. Fix: **mover** o link peer/home pro spot onde o tema do irmão aparece naturalmente (FAQ que toca no assunto, H3 de "Como escolher", H3 de marca, ou "Vale a pena" pra apontar a categoria-mãe/home). Se não há encaixe natural fora da Conclusão, **remover** o link em vez de mantê-lo no fecho.
- **Detecção**: na seção `<h2>Conclusão</h2>`, qualquer `<a href="/{slug}/">` onde `{slug}` é um peer ARTICLE (existe em `reviews/`), OU `<a href="/">` (home). 
- **NÃO flag**: links de PRODUTO na Conclusão (`<a href="/{slug}/">` onde `{slug}` existe em `products/`) nem Amazon `/dp/` — esses são recomendação de compra, função legítima do fecho.
- Não bloqueia readyToLock.

### 7. `link-interno-quebrado` (level=`error`)
Pra cada `<a href="/{slug}/">` interno:
- Se `slug === homeReviewSlug` → error (o correto é `href="/"`, pois o `[slug].astro` filtra o homeReviewSlug do `getStaticPaths` → 404 em produção).
- Se não existe `reviews/{slug}.mdx` NEM `products/{slug}.mdx` → error (404). Fix: corrigir o slug (slugify canon: lowercase, sem acento, ponto entre dígitos → hífen, demais pontos removidos) ou apontar pro arquivo real.

### 8. `peer-article-nao-linkado` (level=`warn`)
Peer article = outro `.mdx` em `reviews/` que compartilha 2+ palavras iniciais do `keyword`. Se existe peer e o guia não o linka → propor 1 link interno **contextual** (FAQ que toca no tema, H3 de "Como escolher", H3 de marca, ou "Vale a pena"), anchor = `peer.keyword` (singular preferido). **NÃO propor na Conclusão** (v1.24.0 — navegação peer/home é contextual, não vai no fecho). Não bloqueia.

### 9. `anchor-nao-keyword` (level=`warn`, v1.22.0)
Âncora de link interno fora da régua. Dois sub-casos:
- **peer (artigo)**: âncora ≠ `keyword` do destino. Régua: âncora = **keyword do destino, preferência SINGULAR** (`keywordPlural` só se a frase exigir). Fix: trocar o anchor pela keyword (qualificadores ficam FORA do `<a>`).
- **produto**: âncora não contém a **marca** OU não é o **nome completo** (ex: `L4360`/`EcoTank L4360` em vez de `Epson EcoTank L4360`). Fix: usar o `name` completo do produto.
Era `info`; subiu pra `warn` porque âncora errada é perda de SEO real e foi recorrente (melhorimpressora, 2026-06-05). Não bloqueia readyToLock.
**⚠ Ao APLICAR o fix, reconciliar a concordância do artigo/preposição ANTES do `<a>` (canon 2026-06-23):** se a âncora nova muda NÚMERO/GÊNERO em relação à antiga, o artigo que a rege acompanha (`das→da`, `dos→do`, `nas→na`, `nos→no`, `pelas→pela`, `essas→essa`). Caso real (escritoriocasa sublimatica): âncora `melhores impressoras de tanque de tinta`→`melhor impressora tanque de tinta` deixou "no guia **das** melhor impressora" quebrado. Reler a FRASE INTEIRA do `<a>` tocado. Auto-check pós-aplicação: `grep -nE '\b(das|dos|nas|nos|aos|pelas|pelos) +<a [^>]*>\s*(melhor|impressora|tablet|opção)\b'` no `.mdx` — match = corrigir o artigo. O `\b` é obrigatório (senão `melhor` casa `melhores` e "das melhores creatinas" falsa-positiva).

### 9b. `linkagem-fraca` (level=`warn`, v1.22.0)
O artigo deve linkar peer articles DISTINTOS (outros `.mdx` de `reviews/`) seguindo a **régua de quantidade canon (Marcelo 2026-06-09): 2 mínimo · ~3 ideal · 4 máximo**, **sem repetir** o mesmo destino, e SÓ no `guideContent` (nunca na intro/reviews). O **HUB** (artigo-cabeça: `homeReviewSlug` ou frontmatter `pillar: true`) é **isento do teto de 4** (linka todos os filhos). **A home é peer**: `href="/"` conta como link pro `homeReviewSlug`, e a própria home NÃO pode ficar órfã (deve receber ≥2 entradas dos outros artigos). Flag se: <2 peers distintos no guia, OU >4 peers distintos num artigo NÃO-hub, OU o mesmo peer linkado 2+ vezes, OU algum link interno na intro/review, OU a home órfã.

⚠️ **Exceção de `<2 peers` (canon 2026-08-10):** site que TEM peers mas **nenhum que responda a uma decisão do leitor deste artigo** (bifurcação / soma / ordem de prioridade) fica em **0 peer de propósito** — a régua qualitativa da `artigo-guia-escrever` ("encaminhamento útil × link protocolar") vence o piso. **NÃO proponha adicionar link nesse caso**, classifique como exceção justificada. Se pra justificar o link você precisa construir o cenário em que o leitor iria pro outro artigo, o cenário não existe.

**PRÉ-CONDIÇÃO MECÂNICA:** a exceção só vale com **ZERO peers da mesma `category`** no site. Com ao menos 1 irmão de mesma categoria, o piso de 2 vale integral e o fix normal se aplica. Caso-origem: `compraguia/melhor-caixa-de-som-jbl` (0 peers de áudio num site de impressora/tablet). Ver "Desempate" na `artigo-guia-escrever`.

Fix (quando NÃO for a exceção acima): adicionar/enxugar peer(s) em spot **contextual** (FAQ/Marca/Vale a pena/Como escolher — **NÃO na Conclusão**, v1.24.0), âncora = keyword do destino (singular), ou remover a repetição. Não bloqueia readyToLock.

### 10. `travessao` (level=`warn`)

**+ Ponto-e-vírgula (;)** (régua 2026-06-20): mesma família do travessão. Flag `;` em prosa como **warn** (auto-fixável: ;→"." ou ","). Detecção **entity-aware**: remova `&amp;`/`&#..;` e a querystring dos links de afiliado antes de checar, senão todo link falsa-positiva. Só prosa, nunca código.
`—` ou `–` em qualquer lugar do guia. Fix: trocar por `:`, `,`, `()` ou `.`.

### 11. `voz-comprador` (level=`error`)
Voz-comprador explícita ("compradores citam", "avaliações") OU implícita ("divide opiniões", "um comprador relata", "bem recebido", "elogios recorrentes") no guia. Fix: reescrever como observação analítica (régua "destilação categoria D").

### 12. `chavoes-por-nicho` (banido absoluto level=`error` · teto numérico level=`info` — paridade com as outras 3 auditoras, régua v1.21.0)
Carregar `docs/painel/_data/chavoes-por-nicho.json`: `_genericos` SEMPRE + bloco do nicho **só se o slug do site está em `_sites_aplicaveis`** (gate canon 2026-08-15). `termos_banidos_absoluto` (lineup, SKU, ASIN, etc.) e tetos **0** > 0 → flag `error`. **Teto NUMÉRICO ultrapassado → `info`, não reprova** (canon 2026-09-05: o teto cai sobre a palavra que É o produto e não há script que o compute igual; ver `_meta.por_que_informativo` do JSON). NUNCA proponha trocar a palavra certa pra baixar contagem. Fix: encurtar ou omitir a frase repetida, NUNCA trocar a palavra exata por sinônimo figurado (é o defeito do critério 12c).

### 12b. `superlativo-sem-evidencia` (level=`warn`, v1.69.0 — 2026-07-02)

Absoluto de VITRINE sem lastro na prosa do guia. **Faltava esta checagem aqui** (a `chavoes-por-nicho` só pega palavra banida tipo lineup/SKU, não superlativo) — caso real 2026-07-02: "imbatível", "o mais forte do mercado" e "melhor do mercado" passaram batido pela guia-auditar em 3 guias de tablet e só o `artigo-auditar` pegou. Este critério fecha o buraco.

**FLAG** (absoluto de mercado/mundo, sem escopo nem dado):
- Bare-boasts: "imbatível", "incomparável", "insuperável", "imperdível", "sem igual", "não tem concorrente", "campeão absoluto", "nada se compara", "o número 1".
- Claim de mercado ilimitado: "o melhor do mercado" / "melhor do mercado", "o mais {forte/potente/rápido/completo} do mercado".

**NÃO FLAG** (legítimo — a régua da rede é levemente positiva por design):
- **A keyword em si.** A keyword da rede quase sempre é "melhor/melhores + algo" ("melhor tablet para estudar", "melhores air fryers"). Usá-la no H2/prosa é correto e esperado. "o melhor tablet para desenho" = uso da keyword, OK. "melhor {produto} para {uso}" quando faz sentido = OK.
- **Superlativo ESCOPADO ao comparativo:** "o mais completo deste comparativo", "a maior autonomia entre os analisados", "o melhor custo-benefício da lista", "o mais barato aqui". O escopo local tira o caráter de claim de mercado.
- **Superlativo ANCORADO em fato na mesma frase:** "o maior suporte de software da categoria, com 7 anos de atualização", "a maior tela daqui, de 14,6 polegadas". Colado ao número/fato que o sustenta = análise, não boast.
- Qualificadores positivos simples: "excelente", "ótimo", "muito bom".

Regra mental: **absoluto de MERCADO/MUNDO sem lastro = flag; keyword, escopo local, ou ancorado em fato = OK.** Fix cirúrgico: escopar ("...deste comparativo"), ancorar no fato, ou trocar por qualificador simples.

### 12c. `naturalidade` (level=`warn`; `error` se ≥3 na mesma seção H2 ou ≥8 no guia — régua comum 2026-08-15, JULGAMENTO → propor→aprovar)

O guia é 50-60% do texto do artigo e até 2026-08-15 não tinha nenhum critério de tom. A classe a flagrar é **palavra comum fora do sentido do dicionário** (quase sempre colocação inglesa vertida), não gíria nem termo técnico:
- objeto/preço/peso como agente com verbo humano: "resolve, dá conta, entrega, segura, pede, exige, aguenta, sustenta, encara, cobra, cobre, trabalha, vira, brilha" ("O de tomada não se cansa", "casa grande pede remanejo", "o sem fio se paga", "reorganiza a categoria inteira");
- substantivo-figura: "a conta", "degrau", "piso", "porta de entrada", "pacote", "produção", "cenário", "posicionamento", "ressalva honesta", "trunfo", "fôlego";
- frase-sacada / aforismo: "não é X: é Y", "não é X, e sim Y", "é aí que mora", "e é justamente", "Marca que só divulga watt está divulgando a conta de luz", "Modelo sem reposição no mercado tem prazo de validade";
- moldes de seção repetidos na rede: "Os preços desta seleção vão de", "Quando não vale a pena:", "Não existe marca que ganhe em tudo", "A escolha gira em torno de", "Escolher bem é menos sobre X e mais sobre Y", "Para a maioria das pessoas, o X é a escolha mais equilibrada", "Seja qual for o perfil";
- "pra" no texto público; ", então" e ", o que" em mais de 1 frase por parágrafo; frase >35 palavras.
Teste: a palavra está no sentido em que você a usaria falando com um cliente? Fix cirúrgico por frase: sujeito concreto + verbo literal ("o modelo com fio não perde força", "você troca de tomada algumas vezes"), "para", quebrar frase longa em duas, trocar o molde pela frase literal. Repetir a palavra exata ("aspira" 3×) NÃO é defeito. NÃO reescrever seção inteira: é a `artigo-guia-escrever` que faz rewrite, esta skill conserta frase a frase.

### 13. `concordancia-quebrada-pt-br` (level=`error`)
Bugs de substituição mecânica (composiçãos, "a produto", "no em 20XX", termo duplicado entre parênteses). Regex igual `artigo-reviews-auditar` critério 15. Fix: corrigir concordância.

### 14. `faq-order-shuffle` (level=`info`, anti-footprint cross-site, v1.x)
**Por quê:** artigos da MESMA keyword em sites irmãos convergem nas MESMAS perguntas de FAQ (a `artigo-guia-escrever` reusa a mesma análise de concorrentes por keyword + os moldes "Qual o melhor X / Vale a pena Y / X ou Z"). Conferido (2026-06-23): as **respostas** já divergem (escritas independente, jaccard 0.25-0.45, ~zero exatas), então o footprint é só a **ordem/identidade das perguntas** — perguntas verbatim iguais e, nos piores casos (4 tablets antigos), na MESMA ordem. Reordenar a FAQ por site disfarça o "template clonado" no FAPage schema + DOM, sem reescrever conteúdo. NÃO mexe na redação das perguntas (bater a PAA literal tem valor SEO), só na ordem.

**Como:** roda o núcleo determinístico `bun scripts/faq-shuffle.ts {site}/{slug}` (dry-run mostra antes→depois; `--apply` grava). A ordem-alvo é função PURA de (conjunto de perguntas, seed=site+slug) — NÃO da ordem atual: ordena canônico (texto da pergunta) → fixa a "money question" (1ª que casa `qual o melhor|qual a melhor|vale a pena`) no topo → embaralha o resto com Fisher-Yates seedado (FNV-1a/xorshift32, igual ao shuffle de produtos da clone). Cada site irmão recebe ordem diferente; re-rodar dá a MESMA ordem → **idempotente, sem churn** (compatível com a CONVERGÊNCIA desta skill). A resposta viaja junto com a pergunta (move o bloco `<h3>+resposta` inteiro). Precisa de ≥3 itens de FAQ; <3 não faz nada. Respeita `contentLocked` (o script aborta).

**Aplicação:** é fix DETERMINÍSTICO → **aplica direto** (canon 24/06 e 24/07; não espera aprovação): rode `bun scripts/faq-shuffle.ts {site}/{slug} --apply` (preserva block-scalar + indentação sozinho) e marque ✅ CORRIGIDO no relatório. Determinístico e seguro → pode auto-aplicar junto dos demais fixes aprovados. **level=info** (não bloqueia readyToLock; é polimento anti-footprint, não erro).

ℹ️ A clone (`artigo-clonar-em-massa`) roda o `faq-shuffle.ts` direto na Etapa 6.3.5 dela (obrigatório desde 2026-06-24 quando há irmão na keyword) — artigo novo de clone já sai embaralhado. Esta skill/o script seguem sendo o caminho pra artigos ANTIGOS (pré-shuffle) ou pra reembaralhar um cluster inteiro (determinístico, pode rodar a qualquer momento).

## Formato do relatório

```markdown
# Auditoria do guia: {site}/{slug}

**Guide**: {N} H2, {chars} chars · **affiliateTag**: {tag} (live: {bool})
**Lineup**: {N} produtos · **Resultado**: {X} seções com mudança proposta, {Y} critérios passaram

> Se 3+ H2 faltando: "⚠ Guia estruturalmente incompleto (N H2 faltando) — recomendo `artigo-guia-escrever` (rewrite) em vez de remendo. Encerrando."

## ✅ Passaram
- {critério}: {nota curta}

## 🟡 Mudanças propostas

### 1. {seção / critério} `[rule]`
- **Problema**: ...
- **Fix proposto** (cirúrgico, só este trecho):
```html
ANTES: <p>...</p>
DEPOIS: <p>...</p>
```

## Como aplicar
- **"aplica tudo"** · **"aplica 1, 3"** (por número) · **"aplica laser"** (por seção/tema)
- **"rejeita 2"** · **"rejeita tudo"** · **"refaz 1"** (repensar uma proposta)
```

Imprimir o relatório inline no chat. Aplicar direto só o mecânico/determinístico (travessão, `;`, concordância, faq-shuffle, link quebrado, âncora); o de julgamento espera aprovação (ou `PIPELINE=yes`).

## Apply: como editar o guideContent

**Estratégia**: `Edit` cirúrgico no trecho-alvo. NUNCA parseYaml/stringify.

1. Localizar o `<p>`/`<h3>`/`<li>` exato dentro do `guideContent` (indentação 2 espaços no block scalar).
2. Substituir SÓ aquele bloco pela versão corrigida. Manter indentação.
3. Inserir seção/H3 nova: `Edit` ancorado no fim da seção-pai (ex: última `<p>` antes do próximo `<h2>`), preservando a ordem canônica.
4. NÃO tocar em outros trechos do guia nem em campos fora do `guideContent`.

## Validar antes de salvar

- Allowlist HTML do guia respeitada.
- Sem travessão.
- Links Amazon tag-aware (ou crus se config vazia); links internos resolvem.
- Sem voz-comprador.
- `pnpm --filter {site} build` passa (gate final). Se falhar → reverter do backup.

## Armadilhas recorrentes

1. **Reescrever o guia inteiro.** É o anti-padrão que esta skill existe pra evitar. Toque só no trecho flagado.
2. **parseYaml/stringify no frontmatter.** Bagunça o block scalar `|` do `guideContent`. Sempre `Edit` cirúrgico.
3. **Shoehornar produto na seção errada.** "Melhor marca: HP ou Epson?" é SEO-binária — não enfie um 3º produto/marca lá; use o FAQ temático ou a Conclusão.
4. **Inventar dado ao integrar produto.** O diferencial citado tem que estar na bíblia do ASIN.
5. **Remendar guia fundamentalmente quebrado.** 3+ H2 faltando = caso de `artigo-guia-escrever`, não de remendo.
6. **Esquecer `--no-verify`.** `guideContent` mora em `reviews/*.mdx` → hook Fase J bloqueia commit normal.
7. **Link interno pro homeReviewSlug.** Vira 404 (filtrado do getStaticPaths) — o correto é `href="/"`.

## Sincronização painel ↔ skill ↔ prompt canônico

```
docs/painel/_data/agent-prompts.json:improve_guide  (espelho do painel/API — pode defasar)
    └── esta SKILL.md (versão local executável)
```

O op `improve_guide` foi adicionado ao `agent-prompts.json` como espelho do prompt no painel (esta SKILL.md é a fonte viva). **O BOTÃO no painel é follow-up**: precisa de handler em `agent-edit.ts` (renderTemplate + chamada) + rota em `server.ts` + UI no `editor-artigo.html`, espelhando o que `improve_reviews` já tem. Enquanto o botão não existe, a capacidade roda via Skill tool (Marcelo/Bárbara no Claude Code) — paridade idêntica à `pagina-produto-criar-em-massa` (skill sem botão).

## Invocação

```
audita o guia do artigo impressora-barata do melhorimpressora
audita melhorimpressora/impressora-barata (só o guia)
```

Args canônico: `Skill(skill="afiliados-skills:artigo-guia-auditar", args="melhorimpressora/impressora-barata")`.

## Limitação intrínseca

O `guideContent` é um bloco único (≠ `products[]` que são N blocos), então o diff cirúrgico é por **seção/trecho** (mais fino que por-produto). Sem schema Zod no output — validação editorial + build como gate final. Pra inserir seção H2 inteira faltante, o Edit é maior, mas ainda localizado (não rewrite).

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
