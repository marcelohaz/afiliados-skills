---
name: pagina-produto-auditar
description: Audita página individual de produto (read-only para julgamento; aplica direto só o mecânico — travessão, `;`, concordância —, régua comum das auditoras), cruzando os 6 campos editoriais com a bíblia + diretrizes + tag de afiliado. 22 categorias (claim-vs-bible, tag-affiliate, tone-comprador, travessão, superlativo, html-inválido com 3 sub-checks, link-externo não-Amazon, tamanho-fora-de-faixa, redundância-com-artigo, voz-citação ficha-técnica, voz-comprador implícita, termos técnico-industriais, jargão-técnico-vazado, chavões-por-nicho, capitalização/duplicação, concordância PT-BR, health-absolutes-YMYL, voz-eximir-responsabilidade, fullReview-prefixo-e-ancoras, duplicata-cross-site, naturalidade (rótulo inventado/teste-da-Amazon, meta-SEO, palavra fora do sentido/verbo-curinga com sujeito-coisa, frase-sacada, jargão financeiro, tiques com teto — elipse de categoria LIBERADA)). Aceita URL do painel (editor-produto.html?site=X&slug=Y) OU args canônicos `site/slug`. Gera relatório em `docs/biblias-v2/.audits/products/<site>-<slug>-last.md`.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida):
- `https://painel.melhorserum.com.br/editor-produto.html?site=melhorimpressora&slug=hp-laser-107w`
- Extrai `site` e `slug` do query string

**B) Args canônicos**:
- `melhorimpressora/hp-laser-107w` (formato `site/slug`)

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B.

**Flag `EM_MASSA=yes`** (passada pela skill-mãe quando esta roda como sub-agent
de um lote — hoje `pagina-produto-criar-em-massa --audit` e
`pagina-produto-auditar-em-massa`). Efeito, nos 5 pontos que a citam: pular o
`git pull` (1.5), pular a camada mecânica (6.7), pular a guarda (19b), pular o
commit/push (9) — a mãe faz os quatro — e **habilitar** o conserto de fato que
passa no TESTE DA FRASE NOVA, que fora de lote é read-only.

⚠ **Genérica de propósito, não uma lista de nomes de mãe** (canon 2026-08-29).
Até então as 5 ressalvas nomeavam só a `criar-em-massa`; quando nasceu a segunda
mãe, o sub-agent dela ficaria entre duas ordens opostas em todos os 5 pontos —
que é exatamente o defeito já medido: **4 ambiguidades num lote de 10**
(cozinhaideal, 21/08) e **22 reincidências em `6.7`** no skill-log. Mãe nova NÃO
deve acrescentar o próprio nome aqui: basta passar `EM_MASSA=yes` no prompt.

# Auditar página individual de produto

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:audit_product_page`.
> Conteúdo duplicado abaixo pra autocontenção. **Esta SKILL.md é a fonte viva** desta execução (o `agent-prompts.json` é o espelho do path do painel/API e pode defasar — o projeto roda via Claude Code).

Você é o auditor da página individual de produto. O usuário passa `site/slug` (ou variantes). Sua função é **verificar** o conteúdo da página — não regerar, não reescrever, só encontrar e reportar problemas.

## Invariantes

- **Não edite julgamento no `.mdx`.** Seu output é um relatório em `.audits/products/`; o humano decide o que muda texto/sentido/fato.
  ⚠️ **Duas exceções:** (1) o **mecânico** (travessão, `;`, concordância PT-BR, capitalização/duplicação, `AFFILIATE_TAG_AQUI`) **aplica direto** com backup + Edit + commit, marcado ✅ CORRIGIDO — régua comum das auditoras (`docs/PADROES.md`, canon 2026-08-15); (2) rodando como **sub-agent de uma skill em-massa** (`EM_MASSA=yes` no prompt — hoje `pagina-produto-criar-em-massa --audit` e `pagina-produto-auditar-em-massa`), a skill-mãe pode autorizar o conserto de **fato** que passa no **TESTE DA FRASE NOVA** abaixo. Fora disso, e sempre para `warn` de julgamento, esta skill é read-only.
- **Nunca invente findings.** Se não encontrou problema numa categoria, diga "nenhum". Audit vazio é melhor que audit inventado.
- **Toda afirmação precisa de evidência.** Cite trecho literal do `.mdx` (blockquote < 15 palavras) ou da bíblia.
- **Respeite as diretrizes** do site e da bíblia.

## Fluxo

1. **Parse args**: aceita `{site}/{slug}` canônico ou nomes humanos (mesmo padrão do `pagina-produto-criar`).

1.5. **Git pull antes de ler arquivos locais** (CRÍTICO — evita estado stale):
   ```bash
   git stash push -m "skill-pagina-produto-auditar-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Painel VPS commita+pusha automaticamente quando user cria/edita conteúdo na UI; Mac local pode estar 5-30s atrás. Sem este pull, skill pode ler estado stale e abortar com falso "X não existe localmente". Se pull falhar (rede offline, conflito), seguir mesmo assim.

   ⚠ **Rodando como sub-agent de uma skill em-massa (`EM_MASSA=yes` no prompt),
   PULE este passo e NÃO registre desvio** (mesma ressalva do 6.7 e do 19b). A
   mãe proíbe git nos sub-agents porque N agentes paralelos dando `stash`/`pull`
   corrompem a árvore, e ela já puxou antes do pré-flight, então não há estado
   stale a corrigir. Sem esta linha o sub-agent fica entre duas ordens opostas e
   registra ambiguidade: aconteceu **4 vezes num único lote de 10** (cozinhaideal,
   2026-08-21), com um dos quatro usando `--alvo` diferente e escapando do
   detector de reincidência.

2. **Read .mdx**: `Read sites/{site}/src/content/products/{slug}.mdx`. Se 404, abortar com mensagem clara.

3. **Parsear frontmatter**: extrair os 6 campos editoriais (subtitle, shortDescription, pros, cons, specs, fullReview). Se algum vazio/ausente, registra como issue `tamanho-fora-de-faixa` (sub-tipo curto).

   ⚠ **`fullReview` ausente NÃO é `tamanho-fora-de-faixa`** — vai pra categoria 19b `texto-no-lugar-errado`, que é 🔴 Crítico. Rotular ausência como problema de tamanho é o que fez 7 páginas passarem meses sem ninguém olhar: um aviso de "conteúdo curto" convida a ignorar, enquanto o defeito real é página no ar sem resenha. E confira o **corpo do `.mdx`** no mesmo passo (a 19b explica por quê) — o parse de frontmatter sozinho é cego pra ele.

4. **Read bíblia**: `Read docs/biblias-v2/{asin}.json`. Sem bíblia, audit não tem como cruzar claims — abortar com mensagem.

5. **Read affiliateTag**: `Read sites/{site}/src/config.ts`. Determinar regra:
   - Serve só pra detectar tag **diferente** (`?tag=X` ≠ config, `AFFILIATE_TAG_AQUI`). URL crua `/dp/{ASIN}` é OK: o build injeta a tag (`injectAffiliateTag`).

6. **Read reviews que citam o ASIN** (anti-duplicate): `Grep` em `sites/{site}/src/content/reviews/*.mdx` por `asin:.*{asin}`. Se houver, leia o `fullReview` do produto-no-artigo pra comparar com o `fullReview` da página individual — flag se for muito parecido (parágrafo inteiro idêntico, frases-chave repetidas).

6.5. **Comparar duplicata cross-site** (mede, não adivinha): a criação escreve a página livremente pela bíblia, sem tentar "ser diferente" de outros sites. **É AQUI que a comparação acontece.** Rode o comparador (auto-descobre páginas do MESMO ASIN em outros sites nossos):
   ```bash
   python3 .claude/skills/pagina-produto-auditar/compare-cross-site.py sites/{site}/src/content/products/{slug}.mdx
   ```
   Lê o JSON. **`duplicata_acionavel` se baseia SÓ em colisão de PROSA** (subtitle/shortDescription/fullReview/pros/cons) — por par: `prosa_exatas`, `prosa_near_0.8`, `overlap_prosa_8gram_pct`. Se `duplicata_acionavel: true` (prosa idêntica > 0 OU prosa near-dup ≥ 0.8 contra algum irmão), abra a categoria `duplicata-cross-site` (abaixo) com os trechos de `prosa_exatas_lista` / `prosa_near_lista`. **Colisões de spec** (`specs_identicas`/`specs_identicas_lista`) NÃO são acionáveis — são dado bruto de ficha (dpi/ppm/rendimento) que repete entre sites por ser fato; no máximo registre como 🔵 info, NUNCA contorça spec pra fugir do match. Se `peers_encontrados: 0` (produto só existe neste site) ou prosa abaixo do limite, nada a flaggar. NÃO é erro ter o mesmo produto em 2 sites (estratégia SERP-monopoly) — o problema é a PROSA ser quase igual.

6.7. **Camada MECÂNICA determinística PRIMEIRO** (canon 2026-07-24 — não conta char de cabeça): rode o script antes de julgar. Ele decide 100% dos checks contáveis/estruturais (tamanho texto-puro, fence, travessão, `;` em prosa entity-aware, HTML em campo texto-puro, 4 rótulos do fullReview, termos banidos absolutos). Motivo: LLM erra ~1/3 desses (medido no gabarito: 6 de 19 shortDescriptions >250 vivas passaram batido na auditoria LLM; o script pega 100%).
   ```bash
   bun scripts/audit-editorial.ts {site}/{slug} --json
   ```
   ⚠ **Rodando como sub-agent de uma skill em-massa (`EM_MASSA=yes` no prompt),
   PULE este passo e NÃO registre desvio.** TODA mãe em-massa roda a camada
   mecânica por slug ANTES de disparar os sub-agents e diz explicitamente "NÃO
   re-rode": na `criar-em-massa` isso é o passo 9 (e o commit só aconteceu
   porque saiu sem `error`); na `pagina-produto-auditar-em-massa` é a Etapa 1,
   que existe justamente porque a página pode nunca ter passado pelo script. Re-rodar joga fora 1 tool call e
   uma leitura de arquivo por agente (medido 2026-07-31), e o contexto vale mais
   no julgamento. Se desconfiar de um achado mecânico específico, confira aquele
   campo à mão em vez de re-rodar tudo.

   Sem esta ressalva o sub-agent ficava entre duas ordens opostas e registrava
   desvio por obedecer a mãe: **22 reincidências em `6.7`** no `skill-log`, o
   ponto mais reincidente do log (canon 2026-08-20). Desvio é pra apontar
   contradição real — esta virou barulho previsível.

   Os findings retornados são **autoritativos** — inclua TODOS no relatório com a severidade que o script deu (`error`/`warn`), NÃO re-julgue tamanho/fence/`;`/travessão de cabeça. Se o script erra por ausência de `bun`/lib (raro), caia no check manual das mesmas categorias. **Escopo do script: só o mecânico.** Ele NÃO cobre `tag-affiliate` (a tag pode ser injetada no build — verificável só no HTML renderizado, não no `.mdx`), nem julgamento (claim-vs-bible, naturalidade, redundância, voz-comprador) — isso continua com você nos passos abaixo.

7. **Rodar as categorias de JULGAMENTO** (abaixo) — as que o script NÃO cobre: claim-vs-bible, tag-affiliate, tone/voz-comprador, superlativo, redundância, naturalidade, chavões-contexto, etc. As categorias puramente mecânicas (tamanho, travessão, `;`, html-invalido, fullReview-prefixo) já vieram do passo 6.7 — não duplicar.

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

   ⚠ **Rodando como sub-agent de uma skill em-massa (`EM_MASSA=yes` no prompt),
   PULE este passo e NÃO registre desvio.** Escreva o `-last.md` e pare aí: a mãe
   commita os relatórios num lote próprio (passo 12c da `criar-em-massa`, Etapa 4
   da `auditar-em-massa`), separado do commit dos `.mdx` consertados. Commitar aqui é a race condition que a REGRA ZERO da
   mãe existe pra evitar.

10. **Reportar no chat**: 3-5 linhas com total de findings por severidade + path do relatório. Não cole o relatório inteiro no chat.

## As categorias de check

### 1. `claim-vs-bible`
Afirmação em qualquer campo (subtitle, shortDescription, pros, cons, specs, fullReview) que não tem origem rastreável na bíblia (specs, números, certificações, marca).

Exemplo flag: `fullReview` diz "velocidade de 12 ppm" mas bíblia diz "10 ppm".

### 2. `tag-affiliate`
Links Amazon no `fullReview` com tag **diferente** da do config (canon 2026-08-15):
- URL crua `/dp/{ASIN}` = OK (o build injeta `siteConfig.affiliateTag` — `injectAffiliateTag`, ver passo 6.7 acima).
- Flag: `?tag=X` com X ≠ config, `AFFILIATE_TAG_AQUI`, tag de outro site.
- Config sem tag em site live: defeito do config, não do link.

### 3. `tone-comprador`
Texto cita 'compradores', 'reviews', 'avaliações', 'estrelas', 'usuários' (proibido — voz é analítica).

Procurar por: `comprador`, `compradores`, `usuário(s)`, `cliente(s)`, `avalia`, `review`, `estrela`, `nota`, `Amazon`.

### 4. `travessao`

**+ Ponto-e-vírgula (;)** (régua 2026-06-20): mesma família do travessão. Flag `;` em prosa como **warn** (auto-fixável: ;→"." ou ","). Detecção **entity-aware**: remova `&amp;`/`&#..;` e a querystring dos links de afiliado antes de checar, senão todo link falsa-positiva. Só prosa, nunca código.
Presença de `—` (U+2014) ou `–` (U+2013) em qualquer campo. Proibido por PADROES.

### 5. `superlativo-sem-evidencia`

**Proibido** (absoluto de mercado/mundo sem lastro):
- ❌ "imbatível", "incomparável", "insuperável", "sem igual"
- ❌ "o melhor do mercado" / "melhor do mercado", "o mais {forte/potente/completo} do mercado"
- ❌ "o único" (sem qualificar em quê)

**Permitido** (NÃO flagar):
- ✓ **A keyword**: "melhor {produto} para {uso}" quando faz sentido — a keyword da rede é "melhor/melhores + algo".
- ✓ **Escopado**: "o mais completo deste comparativo", "o mais barato da lista" (dado de comparação contra o lineup).
- ✓ **Ancorado em fato**: "a maior tela daqui, de 14,6 polegadas".
- ✓ Qualificadores simples (diretriz editorial #2 da bíblia: "review honesto mas inclinado ao positivo pra aumentar conversão"): "excelente", "ótimo"
- ✓ "muito bom"
- ✓ "boa fidelidade"
- ✓ "destaque prático"

A diferença: adjetivo aprobativo simples vs. claim absoluto que exige verificação. Reviews em sites de afiliado são **levemente inclinados ao positivo por design** — qualificadores positivos NÃO são violação editorial.

Use `superlativas qualificadas` quando houver dado de comparação na bíblia:
- ✓ "entre os mais econômicos da categoria EcoTank" (se bíblia tem `concorrentes` populado)
- ✓ "um dos mais leves" (se bíblia tem comparação de peso)

### 6. `html-invalido`

**6a. Tags proibidas em `fullReview`** (`<h2>`, `<h3>`, `<ul>`, `<ol>`, `<li>`, `<table>`, `<img>`, `<script>`, `<iframe>`, `<style>`). Permitido apenas: `<p>`, `<strong>`, `<em>`, `<a>`.

**6b. HTML em campos TEXTO-PURO** (sub-tipo da mesma categoria, severity crítica): `subtitle`, `shortDescription` e `specs[].value` são strings TEXTO PURO renderizadas por Astro com `{var}` (escape XSS automático). Qualquer tag HTML literal nesses campos (`<strong>`, `<em>`, `<a>`, `<p>`) aparece como TEXTO LITERAL pro usuário (não-renderizada). Verificar via regex `<\w+[^>]*>` em cada um dos 3 campos. Caso real 2026-05-26: shortDescription do Integralmédica Huger vazou `<strong>energia...</strong>` → exibido literal no card da página individual.

**6c. HTML no meio do texto de `pros[N]` ou `cons[N]`** (após o `:` que separa título de explicação). O `<strong>Título</strong>` no início está PERMITIDO (template usa `set:html` ali); mas `<strong>` aninhado no texto da explicação **vira texto literal** (mesmo bug). Regex de detecção: depois do primeiro `</strong>:`, qualquer `<\w+` é violação.

### 7. `link-externo-nao-amazon`
Links em `fullReview` que NÃO apontam pra `amazon.com.br/dp/...`. Página individual não deve ter links externos pra outras lojas/sites.

### 8. `tamanho-fora-de-faixa` (régua v1.16.0 — antes era só `conteudo-curto`)

Campo fora dos limites editoriais — pode estar **curto demais** (vazio/incompleto) ou **longo demais** (regressão de escanabilidade, similar ao caso `melhorpretreino`).

**Curto demais** (severidade: depende do campo):
- `subtitle` ausente ou < 10 chars
- `shortDescription` ausente ou < 50 chars (era 40 antes da v1.16.0)
- `fullReview` ausente ou < 300 chars **texto puro** (🔴 incompleto); 300-800 chars (🟡 abaixo do alvo — os 4 parágrafos rotulados + 3 links não cabem em <800; alvo 800-3000, paridade com a criação)
- `pros` < 3 itens
- `cons` ausente ou 0 itens
- `specs` < 3 pares

**Longo demais** (severidade: Crítico — quebra escanabilidade do card):
- `subtitle` > 150 chars
- `shortDescription` > 250 chars (HARD CAP régua v1.16.0)
- `pros[i]` item > 180 chars texto puro (descontando markup `<strong>`/`<a>`)
- `cons[i]` item > 180 chars texto puro
- `fullReview` > 3000 chars **texto puro** (descontando `<p>`/`<strong>`/`<a>` e as URLs da Amazon)

⚠️ **Meça texto puro, não a string HTML.** Isto era ambíguo até 2026-08-06 e
gerava falso positivo sistemático: o markup é 23-27% do campo, então uma página
com 2.400 chars de texto aparecia como "2.998 de 3.000, colada no teto". Oito
páginas da rede constavam como violação sem que nenhuma tivesse 2.600 chars de
texto. Ao reportar, cite o número em texto puro.

**Padrão técnico-first** (sub-check `tamanho-fora-de-faixa-padrao`, régua v1.17.0):
- Detecta `shortDescription` que abre com técnico em vez de benefício-first
- **Antipadrões na 1ª frase** (flag):
  - "[Tipo] brasileiro/a da [marca]..." (ex: "Impressora multifuncional da Epson...")
  - "[Tipo] com X mg de Y..." / "[Tipo] com [spec técnica]..."
- **Padrões OK na 1ª frase**: para quem serve ou o que faz de melhor, dito de forma literal ("Impressora com tanque de tinta para casa e escritório pequeno", "Creatina pura para uso contínuo").
- **Também flagrar (canon 2026-08-15, ver 20c/20e)**: molde "Ideal pra quem…", "Feito pra quem…", "Você ganha…", "Destaque para…" — eram "padrões OK" até 2026-08-15 e viraram assinatura da rede (18% e 35% das páginas).
- Fix: 1ª frase literal (para quem é / o que faz), técnico na 2ª, fecho de fato. Ver seção shortDescription em `pagina-produto-criar`.

**Como contar pros/cons sem HTML**: olhe o bullet sem `<strong>...</strong>` e sem `<a href="...">...</a>` mantendo só o texto interno. Se passa de 180 = flag.

Canon vivo `melhoraspirador` (referência): shortDescription média 225 chars, pros/cons média 65 chars/item, máx 93.

### 9. `redundancia-com-artigo`
Se conseguir detectar: pontos no `fullReview` da página individual que parecem copiados/parafraseados do `fullReview` do produto-no-artigo (anti-duplicate-content SEO).

Heurística: frases-chave repetidas, mesma sequência argumentativa, conclusões iguais. Não precisa ser idêntico — paráfrase próxima conta como redundância.

Se nenhum review cita o ASIN, essa categoria sai vazia automaticamente (não há com que comparar).

### 10. `voz-citacao-ficha-tecnica`

Detecta marcadores de procedência **burocráticos** no .mdx — quando o modelo copiou da bíblia sem destilar. Diretrizes #5 e #6 da bíblia proíbem isso ("não pode parecer leitura de planilha").

**Padrões pra grep**:
- "alérgenos da Amazon confirmam"
- "atributos de material declaram"
- "conforme tipo de dieta"
- "conforme declarado pelo fabricante" / "conforme o fabricante" (sem qualificar)
- "apontada pelo fabricante como" / "apontado pelo fabricante como"
- "relato recorrente nas opiniões" / "segundo relatos de compradores"
- "citada como motivo de preferência por um comprador"
- "datasheet" / "no datasheet"
- "anúncio Amazon" / "apesar do anúncio Amazon listar"

**Severidade: 🟡 Aviso** (não crítico) — porque "segundo X" pode ser **editorial OK** em casos específicos. Verificar contra a régua:

Voz-citação OK SÓ quando atende AS DUAS condições:
1. **(a)** é recomendação/calibração/política do fabricante (ex: "a HP recomenda 50-100 págs/mês"), NÃO spec factual — rendimento/economia/velocidade vão direto, sem atribuir
2. **(b)** adiciona valor editorial ao leitor (calibra expectativa, sinaliza honestidade, faz crítica útil)

**✓ Exemplos editorial OK** (não flagar, ou flagar como info):
- "rende até 4.500 páginas em preto, segundo a Epson" *(agora FLAG: atribuir spec de fabricante é muleta; afirmar direto)*
- "número de marketing 33 ppm, mas a velocidade ISO é mais realista" *(crítica útil)*
- "a HP recomenda volume de 50 a 100 páginas mensais" *(claim só-fabricante)*

**❌ Exemplos burocráticos** (flagar aviso):
- "alérgenos da Amazon confirmam ausência de glúten" → reformula pra "sem glúten"
- "atributos de material declaram ausência de contaminantes" → "livre de contaminantes"
- "apontada pelo fabricante como mais absorvível" → "considerada mais absorvível"

Reportar no relatório com sugestão de reformulação destilada. Humano decide se aceita.

### 11. `voz-comprador-implicita` (severidade: 🔴 Crítico)

Diferente da categoria 3 (`tone-comprador`) que pega menções EXPLÍCITAS de "compradores"/"reviews"/"avaliações", esta pega **voz-comprador SUTIL** que o sub-agent não destilou da bíblia. Régua "destilação categoria D" canonizada 2026-05-26 (v1.11.4).

**Padrões pra grep em qualquer campo (subtitle, shortDescription, pros, cons, specs.value, fullReview)**:
- "opiniões" (no sentido de opiniões de compradores)
- "comentários" (no sentido de comentários de quem comprou)
- "um comprador relata" / "um comprador descreve"
- "divide opiniões" / "opiniões divididas" / "opiniões mistas"
- "elogios recorrentes" / "elogiado nas opiniões"
- "recepção [mista/dividida/positiva]"
- "avaliações" (no sentido Amazon, não avaliação técnica)
- "bem recebido [pelos/nos]"
- "ponto positivo recorrente nas opiniões"
- "queixa recorrente"

**Caso real 2026-05-26** (batch melhorpretreino, 3 produtos via `pagina-produto-criar-em-massa` v1.11.3):
- `dux-energy-kick` pros[4]: "paladar bem recebido pelos comentários disponíveis"
- `dux-energy-kick` fullReview: "Um comprador inclusive descreve uso durante o treino"
- `dux-pre-workout` cons[0]: "Sabor divide: opiniões sobre o sabor são mistas"
- `dux-pre-workout` fullReview: "O sabor maçã verde divide opiniões"

Sub-agent v1.11.3 reconhecia voz-comprador EXPLÍCITA na bíblia mas CAÍA em SUTIL ("um comprador relata", "divide opiniões"). v1.11.4 adicionou auto-check na skill de criação — esta audit cobre defesa em camadas.

**Exemplo flag (errado vs certo)**:
- ❌ "Sabor divide opiniões" → ✅ "Sabor maçã verde é frutado, pode não agradar quem prefere perfis mais neutros"

### 12. `termos-tecnico-industriais` (severidade: 🔴 Crítico)

Termos técnico-industriais proibidos pela régua editorial (canonizada 2026-05-26 v1.11.4). Soam como rotulagem técnica/ANVISA — quebram a voz editorial.

**Padrões pra grep em qualquer campo**:
- "contaminação cruzada"
- "linha de produção compartilhada" (sem contexto editorial)
- "sujeito a contaminação"
- "risco de contaminação por proteínas"

**Caso real 2026-05-26**: `essential-nutrition-beta-action` cons[3] usou "considerar o risco de contaminação cruzada na linha de produção". Audit pegou — sugerido fix:

- ❌ "Risco de contaminação cruzada na linha de produção"
- ✅ "Pode conter traços de leite — alérgicos severos devem ler a rotulagem antes do uso"

Linguagem editorial em vez de técnica. Aviso é crítico porque quebra a voz, não é um qualificador a debater.

### 12b. `jargao-tecnico-vazado` (régua v1.17.3, severidade: 🔴 Crítico)

Termos de dev/estoque/regulatório que NUNCA devem aparecer no texto público. Gap real descoberto no melhorpretreino: bullets de produto continham "SKU avaliado" / "ASIN aqui só vem em...".

**Termos PROIBIDOS** (em subtitle, shortDescription, fullReview, pros, cons, specs.value):
- `\bSKU\b`, `\bASIN\b`, `\bUPC\b`, `\bEAN\b`, `\bGTIN\b` — identificadores técnicos
- `\bdatasheet\b`, `\bdataset\b`, `\bfrontmatter\b`, `\bmetadata\b` — jargão dev
- `\bnotificado\b` (regulatório) — soa bula

**IGNORAR** matches no frontmatter YAML (`asin:`, `image:` são campos técnicos por design, não renderizam).

**Fix**: substitua por linguagem editorial — "SKU avaliado" → "versão avaliada"; "ASIN aqui" → "produto avaliado"; "alimento notificado sob N°..." → "produto registrado na ANVISA".

### 13. `chavoes-por-nicho` (régua v1.18.0, severidade: 🔴 Crítico)

Lê `docs/painel/_data/chavoes-por-nicho.json` baseado em `niche` do site (`docs/painel/sites-meta.json`). Conta termos em texto público (subtitle, shortDescription, fullReview, pros, cons, specs.value), excluindo frontmatter YAML técnico (campos `asin:`, `image:`, etc).

Aplica limites de `_genericos` + bloco do nicho específico (`Pré Treino`, `Creatinas`, `Tablets`, etc.). Banidos absolutos (`lineup`, `SKU`, `ASIN`, `trade-off`, `hardcore`, `datasheet`) flagam imediatamente; demais flagam quando passam do `_max` definido.

Fix: encurtar/omitir a frase repetida + destilação cirúrgica. NÃO "variação léxica" por sinônimo figurado (é o defeito do 20c).
**⚠ TETO POR PÁGINA = ~1/10 do teto por ARTIGO (canonizado 2026-08-28).** Os tetos do JSON são POR ARTIGO (medidos no p90 de artigos comparativos); esta skill audita UMA página individual. A conversão está nos próprios `_doc` do JSON (Eletrônicos e Suplementos): "numa página individual o equivalente é ~1/10 do valor". Regra: `teto_pagina = max(1, round(teto_artigo/10))` — exceto os **banidos absolutos**, que continuam **0** em qualquer superfície. Era a ambiguidade mais registrada do skill-log neste critério (3 notas em 17-20/08: sem o divisor, cada auditor inventava um).

**⚠ `_sites_aplicaveis` é o GATE do bloco de nicho, e o `_genericos` é obrigatório (canon 2026-08-15).**

1. **Bloco de nicho só vale se o slug do site estiver em `_sites_aplicaveis`.** Não force o bloco pelo `niche` do `sites-meta.json`. Caso real: `melhoraspirador-com` tem `niche: "Aspiradores"`, mas o bloco `Aspiradores` lista `_sites_aplicaveis: ["melhoraspirador"]`, que é OUTRO site — o bloco não se aplica. Precedente consistente na rede (`.audits/products/oguiacompra-wap-high-speed-plus-last.md`, `guiaesportivo-vitafor-v-fort`, `compraguia-melhor-impressora-epson`): site fora da lista → **vale só o `_genericos`**. Se o bloco DEVERIA cobrir o site, reporte como sugestão de incluí-lo em `_sites_aplicaveis` — é descalibração do JSON, **não achado contra o texto**.
2. **CONTE O `_genericos` SEMPRE, e conte PRIMEIRO.** Ele não tem gate, vale em qualquer site, e é o que costuma disparar de verdade: `termos_banidos_absoluto`, `chavoes_estruturais_max` (as 4 variantes de "seleção" têm cap **0**, são banidas — salvo as `frases_excecao_canon`) e `industrial_max` (`declarado` 3, `fabricante` 12, `rótulo` 20, `preço médio` 15).

**Incidente-origem (2026-08-15, `melhoraspirador-com/melhor-aspirador-de-po-vertical`):** três auditorias seguidas contaram só o bloco de nicho. Erro duplo — reprovaram o artigo por 4 termos de um bloco que nem se aplicava, e deixaram passar o achado real: 8 ocorrências de "nesta/desta/da seleção" (cap 0 no `_genericos`) no `guideContent`.


### 14. `capitalizacao-duplicacao` (régua v1.18.3, severidade: 🔴 Crítico)

Detecta bugs de substituição mecânica que vazam pro output:

**Sub-checks:**
- **14a — duplicação contígua**: regex `([a-zA-ZÀ-ÿ\s]{8,40})\1` em qualquer campo. Ex real (`a72e7d9`): "sem empilhar suplementos sem empilhar suplementos"
- **14b — bullet minúsculo**: bullet de pros/cons começa com `<strong>[a-z]`. Ex real: `<strong>aminoácidos essenciais na fórmula</strong>` (era `<strong>BCAAs na fórmula</strong>` antes da substituição)
- **14c — minúscula após ponto**: padrão `\. [a-z]` em texto editorial (excluir URLs amazon.com.br). Ex real: "(maior dose declarada). pra emagrecer onde"

**Causa raiz**: substituições mecânicas com palavras minúsculas viram bug em posição de início de frase/bullet, ou colidem com cauda já existente.

**Fix proposto**: capitalizar primeira letra ou destilar duplicação. Bug-class encontrado pela 1ª vez em commit a72e7d9 (melhorpretreino).

### 15. `concordancia-quebrada-pt-br` (régua v1.19.0, severidade: 🔴 Crítico)

**Bug-class** (ChatGPT-Bárbara 2026-05-28): substituições mecânicas v1.17-1.18 não reconcordaram plural/gênero/artigo.

**Sub-checks (regex em todos os 6 campos editoriais)**:

| Sub | Regex | Exemplo |
|---|---|---|
| 15a `plural-aos-errado` | `\b(composição\|combinação\|porção\|injeção\|reação\|opção)s\b` | `composiçãos` → composições |
| 15b `artigo-fem-antes-masc` | `\b(a\|na\|da\|esta) (produto\|formigamento\|ingrediente\|ativo)\b` | `a produto` → o produto |
| 15c `artigo-masc-antes-fem` | `\b(o\|no\|do\|este) (fórmula\|dose\|porção\|composição)\b` | `o fórmula` → a fórmula |
| 15d `adjetivo-quebrado` | `produto[s]? elaborada[s]?\b\|produto ampla\|formula natural` | `produto ampla` → fórmula ampla |
| 15e `duplicacao-prep` | `\b(?:disponíveis?\|disponível) no em \d{4}\|Pra a (maioria\|primeira)` | `disponíveis no em 2026` → disponíveis em 2026 |
| 15f `genero-errado` | `\b(as produtos\|os fórmulas)\b` | `as produtos em geral` → os produtos em geral |
| 15g `termo-duplicado-parens` | `([a-zA-ZÀ-ÿ]{5,30}) \(\1\)` | `formigamento (formigamento)` |

**Fix proposto**: regex find-and-replace direto, sem ambiguidade semântica.

### 16. `health-absolutes-ymyl` (régua v1.19.0, severidade: 🔴 Crítico)

**Bug-class** (ChatGPT-Bárbara ponto 7): absolutos de segurança/saúde violam diretrizes YMYL do Google ("Your Money Your Life") — Google penaliza páginas afiliadas que afirmam segurança absoluta sem fonte.

**Termos banidos absolutos** (limite 0 em qualquer dos 6 campos):
- `uso regular é seguro`
- `alternativa segura` (sem qualificar contra o quê)
- `não causa dano`
- `totalmente seguro` / `100% seguro` / `sem riscos`
- `sem efeitos colaterais`
- `cientificamente comprovado` / `clinicamente comprovado` (sem citar estudo)

**Fix proposto**: qualificar sempre — "Tolerado pela maioria; consulte um profissional se tem comorbidade" em vez de "uso regular é seguro".

### 17. `voz-eximir-responsabilidade` (régua v1.19.1, severidade: 🔴 Crítico)

**Bug-class** (canon 2026-05-28, Marcelo): "declarado pelo fabricante", "X mg declarados", "todas declaradas" viraram muleta epistêmica — site se eximindo de afirmar diretamente. Se o dado está na ficha técnica, é por definição declarado: redundância pura.

**Sub-checks (regex em todos os 6 campos editoriais)**:

| Sub | Padrão | Caso real |
|---|---|---|
| 17a `mg-declarados-parentetico` | `\\d+\\s*(?:mg\|g\|µg\|ml)\\s+declarad[oas]+` | "(400 mg declarados)" |
| 17b `declarado-pelo-fabricante` | `declarad[oas]+ pelo fabricante` | "declarado pelo fabricante" sobrando |
| 17c `todas-doses-declaradas` | `(?:todos\|todas\|doses) declarad[oas]+` | "doses todas declaradas" |
| 17d `alergeno-declarado` | `contém [\\w\\s]+ declarad[oas]+ pelo fabricante` | "Contém glúten declarado pelo fabricante" |
| 17e `sem-mg-declarado` | `sem mg declarad[ao]` | "Sem mg declarada de creatina" |
| 17f `conforme-declaracao` | `conforme (?:declaração\|declarado\|declarada)` | "Pode conter lactose conforme declaração" |

**Fix proposto**: drop "declarad*" e verifique se a frase ainda faz sentido — se sim, era redundância. Para alérgenos: "Contém X" direto (rotulagem é obrigatória por lei).

**FLAG "segundo a [marca]" em spec factual** (régua v1.21.1): "rende 4.500 páginas, segundo a Epson" -> atribuir rendimento/economia/velocidade é muleta; o fix é afirmar direto ("rende até 4.500 páginas"). Atribuição só passa em recomendação/calibração do fabricante (ex: "a HP recomenda 50-100 págs/mês").

### 18. `fullReview-prefixo-e-ancoras` (régua v1.20.3, severidade: 🔴 Crítico)

Três sub-checks no `fullReview` da página individual. **Caso real 2026-06-01**
(creatinasaprovadas): 5 de 9 páginas geradas em batch falharam aqui e o audit
**não pegou** — o check 6a só confere allowlist (vê `<strong>` presente nas
ênfases inline e aprova), sem nunca verificar prefixo nem âncora. Estes 3
sub-checks fecham esse furo.

**18a `prefixo-sem-negrito`**: cada um dos 4 prefixos DEVE estar em `<strong>`.
Flag se aparecer `<p>Para quem é:` / `<p>Por que gostamos:` / `<p>Pontos de
atenção:` / `<p>Resumo:` SEM o `<strong>` (regex: `<p>\s*(Para quem é|Por que
gostamos|Pontos de atenção|Resumo):` que NÃO seja precedido de `<strong>`).
Render é `set:html` fiel — sem `<strong>` no source = sem negrito na tela.

**18b `ancora-cta-em-vez-de-nome`**: a página já tem o botão "Ver Preço na
Amazon"; âncora-CTA no texto é redundante/spam. Flag qualquer `<a>…</a>` cujo
texto contenha "ver / conferir / comprar / acessar / oferta / aqui /
disponibilidade / preço na amazon" E **não** contenha o nome do produto. Ex
reais: `<a>é só acessar aqui</a>`, `<a>Ver preço na Amazon</a>`, `<a>Comprar na
Amazon</a>`. Âncora certa = nome do produto (ou pedaço dele).

**18c `nome-produto-nao-linkado`**: o nome do produto (ou parte ≥2 palavras
significativas) DEVE aparecer como texto de pelo menos 1 `<a>` do `fullReview`.
Flag se nenhuma âncora contém o nome — sinal de que os links viraram CTA
genérico em vez de linkar o produto (igual nos reviews de artigo).

**Fix proposto pros 3**: reescrever os 3 links pra ancorar no nome do produto
em Para quem é / Por que gostamos / Resumo, e garantir os 4 prefixos em
`<strong>`. Não adicionar link no parágrafo "Pontos de atenção".

### 19. `duplicata-cross-site` (régua v1.17.0, severidade: 🟡 Aviso)

Página individual deste produto com texto quase idêntico ao de OUTRO site nosso
que vende o mesmo ASIN. Múltiplos sites no mesmo nicho são estratégia deliberada
(SERP-monopoly); o problema NÃO é existir o mesmo produto em 2 sites, é o **texto
ser duplicado** (canibaliza ranqueamento por conteúdo duplicado).

**Como detectar** (passo 6.5 do fluxo, medição objetiva, não palpite): rodar
`python3 .claude/skills/pagina-produto-auditar/compare-cross-site.py sites/{site}/src/content/products/{slug}.mdx`.
O tool auto-descobre irmãos pelo ASIN e separa PROSA de SPEC. Flag quando, contra
algum irmão, houver colisão de **PROSA**:
- `prosa_exatas > 0` (frase autoral de ≥6 palavras idêntica), OU
- `prosa_near_0.8 > 0` (frase autoral com jaccard ≥ 0.8), OU
- `overlap_prosa_8gram_pct` alto (ex: > 25%).

**`duplicata_acionavel` do tool já reflete isso** (só prosa). **Colisão de spec
NÃO conta** — `specs_identicas`/`specs_identicas_lista` (dpi, ppm, rendimento) é
dado bruto de ficha que repete entre sites por ser fato; no máximo 🔵 info,
**nunca reescreva spec só pra fugir do match** (isso é a contorção que queremos
evitar).

**Evidência**: citar o `peer` (site/slug do irmão) + os trechos de
`prosa_exatas_lista` / `prosa_near_lista` que colaram.

**Fix proposto**: reescrever SÓ os trechos de prosa sobrepostos divergindo o
fraseado (mesmos fatos, redação distinta) — não a página inteira. A reescrita é a
hora certa de "ficar diferente"; a criação escreve livre, o audit mede, o fix
corrige só a prosa que de fato colou.

**Não flag** se `peers_encontrados: 0` (produto só existe neste site), se só
houver `specs_identicas`, ou se a prosa ficou abaixo dos limites.

### 19b. `texto-no-lugar-errado` (régua 2026-08-14, severidade: 🔴 Crítico)

O texto existe e é bom, mas está onde ninguém lê. **Não é falta de conteúdo, é
endereço errado** — e por isso escapa de toda auditoria que só olha os campos
que existem.

**Mecânica:** o `SlugPage` só monta `<Content />` quando `type === 'review'`.
Numa página de produto, **o corpo do `.mdx` nunca renderiza**. Resenha gravada
ali produz página no ar sem resenha, com build passando e painel sem acusar.

**Dois sub-checks, ambos determinísticos:**

| sub | condição | o que significa |
|---|---|---|
| `fullReview-ausente` | `grep -c '^fullReview:'` == 0 | página vai pro ar sem resenha |
| `fullReview-duplicado` | `grep -c '^fullReview:'` > 1 | YAML ambíguo, o último vence em silêncio |
| `corpo-nao-vazio` | corpo após a 2ª fence, descontando `{/* … */}`, tem qualquer char | texto morto no arquivo |

Rode a guarda em vez de conferir a olho — ela é a implementação canônica:

```bash
bun scripts/pagina-produto-guardas.ts {site} {slug}
```

⚠ **Como sub-agent de uma skill em-massa (`EM_MASSA=yes` no prompt), PULE a
guarda e NÃO registre desvio** — mesma razão do passo 6.7: a mãe já a rodou por
slug antes de disparar os sub-agents. Continue julgando a categoria (o `fullReview` no lugar errado é
🔴 Crítico e é leitura, não script); o que se pula é só re-executar a guarda.

**Casos reais (2026-08-14, os dois achados na mesma varredura):**
- **7 páginas em 3 sites** com a resenha inteira no corpo e o campo ausente.
  Ficaram **meses** assim. O conserto certo foi **MOVER** o texto pro campo, não
  regerar: o texto já era original por site (jaccard 6-grama 0,00-0,02 contra o
  irmão) e regerar jogaria isso fora, recriando um risco de duplicata cross-site
  que media zero. **Regra: quando o defeito é de endereço, mude o endereço.**
- **1 página** (`guiaesportivo/vitafor-vita-d3-2000ui-gotas`) com a resenha NOVA
  no campo e 2.222 chars da VELHA esquecidos no corpo — resíduo de reescrita que
  gravou no frontmatter e não limpou o corpo. Uma varredura que procura só
  "campo ausente" **não acha esta**: o campo está lá. Procurar pelo sintoma não
  encontra a causa. Ver [[feedback_controle_positivo_antes_de_afirmar_ausencia]].

**Fix:** corpo com texto e campo ausente → mover. Corpo com texto e campo
preenchido → conferir se o corpo é versão velha (quase sempre é) e apagar o
corpo. Comentário MDX no corpo é intencional e não se toca.

### 20. `naturalidade` (régua v1.33.0, canon Marcelo 2026-06-10, severidade: 🔴 a/b · 🟡 c/d/e, c vira 🔴 com ≥3)

Sub-checks QUALITATIVOS de tom natural — complementam o critério 13 (que já aplica
`naturalidade_banidos` e `naturalidade_max` quando o bloco do nicho os define, ex.
`Impressoras`). Estes pegam o que lista nenhuma cobre:

- **20a — rótulo de categoria inventado** (🔴): teste-da-Amazon — o rótulo usado
  existe no varejo (alguém digitaria na busca)? ❌ "máquina de trabalho" → ✓
  "impressora de escritório" · ❌ "impressora para imagem" → ✓ "impressora
  fotográfica" · ❌ "preço de custo-benefício" → ✓ "preço justo".
- **20b — meta-SEO** (🔴): NUNCA comentar a busca/intenção do leitor no texto
  ("tem gente que digita X na busca", "quem pesquisa por Y quer..."). O texto
  fala do produto, não do Google.
- **20c — palavra fora do sentido / verbo-curinga com sujeito-coisa** (🟡; 🔴 com
  ≥3 na mesma página — canon Marcelo 2026-08-15, substitui "antropomorfismo com
  gíria"): a **classe** que mais dá "cara de IA" e passa em toda lista de termo.
  Palavra comum usada fora do sentido do dicionário, quase sempre colocação inglesa
  vertida: objeto/preço/peso que "resolve, dá conta, entrega, segura, pede, exige,
  aguenta, sustenta, encara, cobra, junta, trabalha, cobre, vira, brilha" ("resolver
  a casa", "o aparelho pede espaço", "a conta da potência vem no peso", "sem
  transformar a limpeza numa produção"); substantivo-figura ("a conta", "degrau",
  "porta de entrada", "pacote", "produção", "trunfo", "fôlego"); frase-sacada
  ("não é X: é Y", "o que X é Y", "é aí que…"); fecho com rótulo de público ("é a
  escolha de quem", "faz sentido pra quem", "ele é o que resolve"); "pra" no texto
  público. Teste: a palavra está no sentido em que você a usaria falando com um
  cliente? Fix: sujeito concreto + verbo literal, "para". Repetir a palavra exata
  NÃO é defeito. Verbo inventado/gíria ("se reconserta", "no batente") continua
  aqui. Máximo 1 coloquialismo leve por página.
- **20e — tiques com teto por PÁGINA** (🟡, vale em todo nicho): tetos = **metade** dos de
  `_genericos.naturalidade_max` do `chavoes-por-nicho.json` (regra escrita no `_doc` da chave:
  "página de produto: metade"), pela fórmula **`teto_pagina = max(1, floor(teto_artigo/2))`**
  (ex.: resolve 3 → floor(1,5) = 1; daqui 2 → 1; **de verdade 1 → floor(0,5) = 0 → max(1,0) = 1**), e
  `_genericos.naturalidade_banidos` = 0 ("Ideal pra quem", "Destaque para", "preço médio
  acessível"…). Some com o bloco do nicho se o site está em `_sites_aplicaveis`. Não copie a
  lista pra cá: cite a chave (a lista que vivia aqui já divergia do JSON).

  ⚠ **O divisor /2 é EXCEÇÃO DE UMA CHAVE SÓ: `_genericos.naturalidade_max`.**
  **Todo o resto do JSON converte por /10** pela fórmula do critério 13 — os blocos
  de nicho **e as demais chaves do próprio `_genericos`** (`industrial_max`,
  `chavoes_estruturais_max`, `ingles_max`, `corporativo_max`…). Não é "genéricos
  contra nicho": é uma chave contra todas as outras. O que decide é o `_doc`, e
  `naturalidade_max` é a **única** do JSON inteiro que declara divisor próprio
  ("página de produto: metade"); onde o `_doc` não declara, vale o /10 do 13.

  São escopos diferentes, não réguas concorrentes — e errar isso muda o veredito por
  ordem de grandeza. Medido em 2026-08-29 na chave `Creatinas.medico_tecnico_max.monohidratada`
  (teto 30 por artigo): dois auditores varreram a MESMA rede e acharam **1** e **270**
  páginas acima do teto, porque um aplicou /2 (teto 15) e o outro /10 (teto 3). O certo
  ali é **/10**. Antes de converter, olhe o NOME da chave, não o bloco:
  `_genericos.naturalidade_max` → /2; **qualquer outra chave, em qualquer bloco** → /10.

  ⚠ **`max(1, ...)` não chega a zero de propósito.** Teto 0 é função do
  `_genericos.naturalidade_banidos`, que é lista separada. Deixar um tique de
  `naturalidade_max` cair a zero por arredondamento seria banir por divisão uma
  palavra que a régua escolheu apenas limitar.
- **20d — jargão financeiro/burocrático** (🟡): "desembolso" → "preço" ·
  "reprografia" → "cópia e digitalização" · "aquisição" → "compra".

**LIBERADAS (NÃO flagrar — falso-positivo já cometido e corrigido 1x)**:
- **Elipse de categoria com adjetivo real**: "a barata da lista", "a doméstica",
  "a laser" são português natural (teste: o leitor tropeça NO contexto? não).
- "calibrada/calibrado" só é banida se o bloco do NICHO listar (hoje: Pré Treino).
  Não é regra genérica.

## Filtros editoriais — flag se aparecer nos campos curados

Também sinalizar (severidade `aviso`):

- **Specs ambientais** (% plástico reciclado, certificações eco como Energy Star/EPEAT/RoHS/FSC, programas de devolução tipo "HP Planet Partners", neutralidade de carbono) em qualquer dos 6 campos. Exceto se a bíblia tem `angulosConversao` com tema `sustentabilidade` marcado.
- **Origem de fabricação** ("fabricado no Brasil", "made in X", "produto nacional") em qualquer dos 6 campos. Exceto se a bíblia tem `angulosConversao` com tema `produto-nacional`.

## Formato do relatório

Template exato — use blocos idênticos pro painel parsear visualmente:

```markdown
# Auditoria: {productName} ({site}/{slug})

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

- **🔴 Crítico**: claim factualmente errado vs bíblia, tag affiliate violada, HTML proibido (inclui sub-checks 6a/6b/6c), tone-comprador EXPLÍCITO, voz-comprador-implicita (categoria D, régua v1.11.4), termos-tecnico-industriais (régua v1.11.4), **tamanho-fora-de-faixa LONGO demais** (régua v1.16.0 — shortDescription >250, pros/cons >180 texto puro; cards viram parágrafos), **fullReview-prefixo-e-ancoras** (régua v1.20.3 — 18a prefixo sem negrito, 18b âncora-CTA em vez do nome, 18c nome do produto não linkado).
- **🟡 Aviso**: superlativo sem evidência, conteúdo curto em campo opcional, specs ambientais sem ângulo, suspeita de duplicate content, voz-citação ficha-técnica burocrática.
- **🔵 Info**: nota que vale registrar mas não exige ação (ex: "subtitle no limite mínimo de 10 chars, considere expandir").

## TESTE DA FRASE NOVA — o que pode ser consertado sem aprovação

**Canon Marcelo 2026-08-06:** *"se for erro de fato (informações erradas), já poderia fixar na
hora. Agora se for só warning (frases parecidas com fontes ou páginas irmãs), só reportar."*

Isso **refina** a régua de report-only de 2026-07-10, não a reverte. O que foi barrado lá foi
auto-consertar **warn** (estilo). Fato é outra coisa.

A linha não é "erro vs aviso" — é uma pergunta única, e ela é verificável:

> ### Dá pra consertar sem escrever nenhuma frase nova?

Se sim, **aplique**. Se não, **reporte com o fix sugerido**. O critério de saída: depois do
conserto, toda palavra que sobrou vem da bíblia ou já estava na página. **Zero prosa inventada.**

**As três formas que passam:**

```
APAGAR       a página afirma X, X aparece 0× na bíblia,
             e a frase continua de pé sem X
SUBSTITUIR   a página diz "A", a bíblia diz "B" para o mesmo referente
RESTAURAR    a bíblia diz "número + condição" e a página tem só o número
```

Medido nos 4 batches de 2026-08-06 (23 achados factuais), a linha separou 9 de 14:

```
APLICA                                      REPORTA
"0,5ms MPRT (1ms GtG)"  apaga o parêntese   "Sem som próprio"   apagar não deixa título
"Rádio FM"              apaga "FM"          "no próprio painel" a frase quebra sem ele
"água, poeira e tombo"  apaga 2 palavras    "beira da piscina"  buraco na enumeração
"6 a 7 bandas"          apaga a contagem    "o remoto resolve os 10 m"  o raciocínio
"alça embutida"         apaga "embutida"                        inteiro está errado
"prioridade de voz"   → "do microfone"      "app da Philips"    atribuir = frase nova
"pontos por polegada" → "pixels por"
"180 Hz"              + "pela DisplayPort"
"reset sob a tampa"     restaura o hedge
```

Os cinco da direita são exatamente aqueles em que a redação do substituto foi **escolha
editorial**, e é isso que precisa de olho humano.

⚠️ **Warn de JULGAMENTO nunca aplica** (frase parecida com a página irmã, coloquialismo acima do
teto, redundância entre bullet e parágrafo: só relatório). **Warn MECÂNICO aplica direto** — travessão,
`;`, concordância PT-BR, capitalização/duplicação, `AFFILIATE_TAG_AQUI` (régua comum das auditoras,
`docs/PADROES.md`, canon 2026-08-15; antes esta skill era a única que deixava até o mecânico só no relatório).

### Quando a raiz é a BÍBLIA, não a página

**Se a página contradiz a `decisaoEditorial` MAS obedece outro campo da mesma bíblia, o alvo do
conserto é a bíblia.** Reporte apontando para lá e **não toque na página**.

Caso real 2026-08-06: `philips-tax4000-78` prometeu o ajuste pelo app da Philips em **três sites**.
A flag `aplicativo-e-bass-plus-ausentes-do-anuncio` proíbe a promessa, e o `pontosFortes[5]` da
mesma bíblia endossa o recurso — o redator seguiu o campo que endossa, três vezes. Consertar as
três páginas calaria o sintoma e garantiria a quarta.

#### Ao reportar (ou consertar) a bíblia, aponte o CLAIM, não o campo

**Um claim mora em vários campos curados.** O audit só enxerga o campo que a página copiou,
então reportar "conserte `pontosFortes[5]`" entrega um conserto pela metade.

Ainda no mesmo 2026-08-06, a bíblia `B0FK1JG2TT` foi corrigida no `pontosFortes[5]` e a página
seguinte saiu limpa. Mas a promessa do app continuava viva em `angulosConversao[2].frases[2]` e
em duas `dicasAcionaveis` — o vetor seguia armado para o 6º site.

Ao apontar a raiz, **varra os campos curados atrás do mesmo claim** e liste todos no relatório:

```
pontosFortes · pontosFracos · angulosConversao[].frases[] · dicasAcionaveis
sentimentoCompradores[].resumo · observacoesAgente
```

⚠ **Busca por termo produz falso positivo e falso negativo.** No caso acima, um grep por
`aplicativo|ajust|control` marcou o próprio conserto já aplicado (por conter "controlar"), marcou
o texto da flag que **proíbe** o claim, e deixou passar uma `dicasAcionaveis` que dizia
"desligue … pelo aplicativo" (o grep procurava "desligar"). Use a busca para **estreitar**, depois
leia os campos. O que conta é o campo afirmar o claim, não conter a palavra.

### Como aplicar, quando aplicar

Copie a mecânica da `biblia-auditar-em-massa`, não invente outra:

1. **Backup antes de escrever**, em `docs/painel/.painel-backups/<dia>/`.
2. Aplique **só** o que passou no teste, com `Edit` cirúrgico. Nunca reescreva o campo inteiro.
3. **Re-audite o que você tocou**: resolveu? não quebrou outra coisa? não mudou o sentido?
4. Não convergiu em ≤3 tentativas → **reverte do backup** e vira item de relatório.
5. O relatório distingue **CORRIGIDO** de **REPORTADO**, com o diff de cada conserto.
6. ⛔ **Nada de git.** A skill-mãe commita.

## Boas práticas

- Se a página está quase vazia (stub recém-criado, antes de rodar `pagina-produto-criar`), resuma em 1 bullet "página em estágio inicial; checagens de conteúdo adiadas até preenchimento" e termine.
- Prefira 5 findings bem evidenciados a 20 vagos. Assine valor, não volume.
- Se errou na auditoria (ex: confundiu campo X com Y), o humano vê no diff do markdown na próxima rodada. Não há vergonha em revisar o próprio relatório.

## Exemplo de invocação

```
audita a página individual da L3250 no melhorimpressora
audita o produto epson-ecotank-l3250 do melhorimpressora
audita melhorimpressora/epson-ecotank-l3250
```

Args canônico: `Skill(skill="pagina-produto-auditar", args="melhorimpressora/epson-ecotank-l3250")`.

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
