---
name: artigo-review-criar
description: Cria o review editorial de UM produto dentro de um artigo comparativo. Aceita URL do painel (editor-artigo.html?site=X&slug=Y) — detecta stubs vazios no lineup e pergunta qual preencher, 1 por vez (controle de qualidade) — OU args canônicos site/slug-artigo + ASIN. Cria backup, commit, push, dispatch VPS pull.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida — fluxo natural depois de adicionar produtos via "+ Adicionar produto"):
- `https://painel.melhorserum.com.br/editor-artigo.html?site=melhorimpressora&slug=melhor-impressora-custo-beneficio`
- Extrai `site` e `slug` do artigo

**Comportamento quando URL é fornecida:**
1. Read .mdx do artigo
2. Detecta produtos com **stub vazio** (`fullReview: |` seguido de nada antes do próximo campo, OU `fullReview: ""`)
3. **Cenários:**
   - **0 stubs vazios**: avisa "todos os produtos já têm review preenchido. Use `artigo-reviews-auditar` se quer revisar."
   - **1 stub vazio**: preenche aquele direto
   - **2+ stubs vazios**: **pergunta qual** preencher, listando posição + nome + ASIN. Padrão é **1 por vez** pra controle de qualidade. Exemplo:
     ```
     Encontrei 3 produtos com review vazio:
     1. HP Laser 107W (B07S61ZJCS) — posição 6 no lineup
     2. Canon Pixma MG3620 (B0XXXXXXXX) — posição 7
     3. Brother HL-L2350DW (B0YYYYYYYY) — posição 8

     Qual preencher? (responda com 1, 2 ou 3, ou ASIN direto)
     ```

**B) Args canônicos** (forma direta — power user já sabe ASIN):
- `melhorimpressora/melhor-impressora-custo-beneficio B07S61ZJCS`
- Skill preenche só o ASIN indicado, ignora outros stubs.

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B.

# Preencher review de um produto dentro de um artigo

> Versão executável local do prompt `docs/painel/_data/agent-prompts.json:rewrite_product` + (quando o artigo é stub) `make_reviews` pros campos top-level. O conteúdo essencial está duplicado abaixo; em caso de divergência, o prompt canônico ganha.

Você é o curador editorial que escreve o conteúdo do produto-no-artigo. O artigo existe como stub criado pelo endpoint `make-reviews-stub` ou `add-products-stub` do painel. Sua função é **preencher os 6 campos editoriais de um produto específico** seguindo a régua do `formato_full_review` (4 parágrafos marcados, comparativo), e quando o artigo é stub, **também os campos top-level** (title, description, excerpt, keywordPlural, listHeading, specLabels).

## Pré-requisitos

O `.mdx` do artigo já existe em `sites/{site}/src/content/reviews/{slug}.mdx` com lineup de produtos (criado pelo make-reviews-stub) ou recém-adicionado (add-products-stub). Se não existir, abortar com mensagem clara apontando o botão "✨ Criar artigo" no site detail.

A bíblia do ASIN está OK e a página individual existe (verificado pelo gate Fase 2 quando o stub foi criado).

## Invariantes

- **Nunca invente.** Cada claim numérico tem origem rastreável na bíblia (`specsAmazon`, `doFabricante`, `pontosFortes`, etc).
- **Conteúdo COMPARATIVO** (diferente da página individual): pode comparar com outros produtos do lineup, citar por nome, dizer "vs HP X" se houver dado na bíblia. Pode falar "nesta seleção", "comparado ao primeiro da lista".
- **Anti-duplicate vs página individual**: leia o `fullReview` da página individual antes (`sites/{site}/src/content/products/{slug-do-produto}.mdx`). O texto do produto-no-artigo deve ter ângulo DIFERENTE — comparativo, posicionamento na seleção, etc.
- **Sem travessão (—)** em nenhum campo.
- **Voz analítica**: NUNCA cite compradores/reviews/avaliações/estrelas/Amazon.
- **HTML allowlist no `fullReview`**: `<p>`, `<strong>`, `<em>`, `<a>`. Proibido: `<h2>`, `<h3>`, `<ul>`, `<ol>`, `<table>`, `<img>`, `<script>`.

- **CAMPOS TEXTO-PURO — sem HTML inline** (régua v1.11.5, canon 2026-05-26). A allowlist HTML acima é EXCLUSIVA do `fullReview`. Os demais campos do produto-no-artigo são texto puro renderizado por Astro com `{var}` (escape XSS automático):
  - `subtitle`: texto puro
  - `shortDescription`: texto puro (renderizado em `<p>{var}</p>` no card — `<strong>` literal vira texto pro usuário)
  - `specs[].value`: strings simples sem HTML
  - `pros[N]` / `cons[N]`: formato `<strong>Título</strong>: explicação` — `<strong>` está PERMITIDO **apenas no Título inicial** (template usa `set:html` ali), **NÃO** no meio do texto após o `:`.

  **AUTO-CHECK obrigatório**: antes de gravar o `.mdx`, grep `<strong>`, `<em>`, `<a `, `<p>` em subtitle/shortDescription/specs.value. Se achar — ERRADO. Reescreva como texto puro. Caso real 2026-05-26: `Integralmédica Huger` (página individual) vazou `<strong>energia...</strong>` na shortDescription, apareceu literal no card pro usuário. Mesmo bug-class é vulnerável em produto-no-artigo.
- **Tag-aware**: leia `siteConfig.affiliateTag`. Vazia (sites em construção) → URL crua `https://www.amazon.com.br/dp/{ASIN}`. Preenchida → `?tag={tag}&linkCode=ogi&th=1&psc=1`.
- **Português brasileiro editorial** sem gírias.

## Fluxo

1. **Parse args**: aceita `{site}/{slug-do-artigo} {ASIN-ou-slug-do-produto}` ou variantes humanas. Eu (Claude) interpreto e formato args canônicos antes.

1.5. **Git pull antes de ler o .mdx** (CRÍTICO — evita falso "produto não está no lineup"):
   ```bash
   git stash push -m "skill-artigo-review-criar-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Pattern de falha resolvida em 2026-05-24: user adiciona produto no painel da VPS (botão "+ Adicionar produto"), painel commita + push pro GitHub. Mac local fica desatualizado (sem auto-pull). Skill lê o .mdx local STALE, não encontra o ASIN, aborta dizendo "produto não está no lineup" — mas o user JÁ ADICIONOU. Pull antes elimina esse falso-negativo.

   Se pull falhar (rede offline, conflito), seguir mesmo assim — o stash pop pode pegar stale. Documentar no relatório.

2. **Read artigo**: `Read sites/{site}/src/content/reviews/{slug}.mdx`. Se 404, abortar.

3. **Localizar o produto** no `products[]` do frontmatter pelo ASIN. Se não encontrado APÓS o pull, abortar com mensagem "Produto X não está no lineup do artigo; use '+ Adicionar produto' antes" — agora sim com confiança que o local está sincronizado.

4. **Read bíblia**: `Read docs/biblias-v2/{ASIN}.json`. Se não existir, abortar.

5. **Read página individual**: tenta `Read sites/{site}/src/content/products/{slugify(bíblia.identidade.nome)}.mdx`. Lê o `fullReview` pra **NÃO REPETIR** ângulo no artigo. Se a página individual não tiver `fullReview` (stub puro), tudo bem — só toma cuidado com o conceito.

6. **Read `affiliateTag`**: `sites/{site}/src/config.ts`. Pode ser `''` (construção, links crus) ou preenchida.

7. **Detectar se o artigo é stub** (`title`/`description`/`excerpt` vazios): se sim, gerar também os campos top-level (passo 8a). Se não, só os campos do produto (passo 8b).

8a. **Gerar campos top-level do artigo** (só se stub):
   - `title`: 30-100 chars. Formato: keyword capitalizado + ":" (o resto user completa). Ex: keyword "melhor impressora custo benefício" → title "Melhor Impressora Custo Benefício:"
   - `description`: 50-160 chars, meta-description SEO
   - `keywordPlural`: forma plural do keyword. Ex: keyword "melhor impressora custo benefício" → keywordPlural "melhores impressoras custo benefício"
   - `listHeading`: SEMPRE derivado do `keywordPlural` gerado acima — nunca do keyword singular. Formato: "Quais os/as melhores {keywordPlural} em {ano}?" — use o artigo correto pelo gênero do substantivo plural (impressoras → "as", pré-treinos → "os", creatinas → "as", robôs → "os"). Ex: keywordPlural "melhores impressoras custo benefício" → listHeading "Quais as melhores impressoras custo benefício em 2026?"
   - `excerpt`: 50-300 chars. Teaser do topo
   - `specLabels`: array de 3-10 labels (intersecção dos specs.label dos produtos no lineup). Pra primeiro produto, deriva direto. Pra produtos adicionados depois, deixa como está e atualiza só se o novo produto tiver labels diferentes.

8b. **Gerar os 6 campos editoriais do produto** seguindo a régua do `formato_full_review` (4 parágrafos marcados):

```html
<p><strong>Para quem é:</strong> perfil de uso. Inclua 1 link Amazon no nome do produto.</p>
<p><strong>Por que gostamos:</strong> features-chave com dados concretos. Inclua 1 link Amazon na primeira menção. Pode dividir em 2 parágrafos se >5-6 frases (primeiro features-chave, segundo specs gerais).</p>
<p><strong>Pontos de atenção:</strong> trade-offs, limitações. SEM link de afiliado neste parágrafo.</p>
<p><strong>Resumo:</strong> fechamento conciso. Inclua 1 link Amazon na última menção.</p>
```

- **3 links de afiliado** total (Para quem é + Por que gostamos + Resumo). SEM link em "Pontos de atenção".
- Formato dos links: `<a href="{amazonUrl}" rel="nofollow" target="_blank">Nome do Produto</a>` onde `amazonUrl` é crua quando tag vazia, com tag quando preenchida.

- **pros** (3-8 itens): formato `<strong>Título</strong>: explicação com dado concreto`.
  - ✓ "<strong>Rendimento elevado</strong>: 4.500 páginas em preto por kit T544 segundo o fabricante"
  - ❌ "<strong>Rendimento alto</strong>: a impressora rende muito" (sem dado)

- **cons** (1-5 itens): mesma formatação.

- **specs** (3-10 pares label/value): strings simples sem HTML. Reuso labels comuns do lineup pra alinhar com `specLabels`.

- **subtitle** (10-70 chars): rótulo de posicionamento SEO — espelha buscas reais no Google. NÃO é descrição de specs.

  **Formato**: `"Melhor {tipo-produto} {diferenciador}"` — ou sem "Melhor" quando mais natural.
  Extrai o **tipo-produto** do `keyword` do artigo: `"melhor pré-treino"` → `"Pré-treino"`, `"melhor impressora custo-benefício"` → `"Impressora"`, `"melhor tablet"` → `"Tablet"`.

  **Sequência posicional default** (guia inteligente — ajuste pela bíblia se não calçar):
  - Posição 0: `"Melhor {tipo} em Geral"` — campeão da seleção, reflete badge "Melhor Escolha"
  - Posição 1: `"Melhor {tipo} Custo-Benefício"` — melhor relação qualidade/preço
  - Posição 2: `"Melhor {tipo} Bom e Barato"` — mais acessível que ainda entrega resultado
  - Posição 3+: derivado da bíblia — público (`"para Iniciantes"`, `"para Idosos"`, `"para Mulheres"`), feature (`"sem Cafeína"`, `"com Creatina"`), combinação (`"sem Cafeína para Iniciantes"`)

  **Coerência com badge**: se badge preenchido, subtitle deve refletir. Badge `"Custo-Benefício"` → subtitle contém "Custo-Benefício". Badge `"Bom e Barato"` → subtitle contém "Bom e Barato". Badge `"Melhor Escolha"` → subtitle contém "em Geral".

  **O subtitle define o ângulo do review**: a lente escolhida guia o `Para quem é` e o `Resumo`. Ex: subtitle `"para Iniciantes"` → enfatizar facilidade, fórmula mais leve, segurança para quem começa.

  ✅ `"Melhor Pré-treino em Geral"` · `"Melhor Impressora Custo-Benefício"` · `"Melhor Tablet para Desenhar"` · `"Melhor Pré-treino sem Cafeína para Iniciantes"` · `"Melhor Tablet Bom e Barato"`
  ❌ `"Pré-treino com 400mg de cafeína, creatina e beta-alanina..."` (specs, não posicionamento) · `"Compacta de Orçamento"` (sem keyword âncora)

  > **Se já preenchido no stub (valor não-vazio)**: usar como está — não regenerar.

- **shortDescription** (50-800 chars): 1-2 frases que resumem o produto pra TabelaProdutos e TopPickCard.

9. **Validar mentalmente** antes de salvar:
   - Tamanhos dentro dos ranges
   - HTML allowlist OK no fullReview
   - Sem travessão
   - Tag correta nos links (ou cruas se config vazia)
   - Voz analítica (zero "compradores", "reviews", "avaliações", "posicionamento Amazon")
   - Voz-citação ficha-técnica (zero "alérgenos confirmam", "atributos declaram", "conforme tipo de dieta", "apontada pelo fabricante como") — exceção: claim só-fabricante que adiciona valor editorial, ver Armadilha 4
   - Anti-duplicate vs página individual (frases não-repetidas)
   - `"lineup"`: deve ser 0 no produto gerado (proibido — substituir por "desta lista", "desta seleção", etc.)
   - Âncoras comparativas: se > 2× neste produto, substituir excedente por variante ou elide
   - Pros de preço: verificar se listou 3+ concorrentes com preços — simplificar pra 1 referência ou afirmação geral
   - Termos técnicos de nicho: se apareceu pela primeira vez no artigo sem gloss, adicionar explicação breve entre parênteses

10. **Backup**: `docs/painel/.painel-backups/{YYYY-MM-DD}/article-{site}-{slug}-{HHMMSS}-prod-{ASIN}.mdx`. Pattern paralelo ao do painel pra aparecer no card "Histórico de versões".

11. **Write `.mdx`**: usa parseYaml + stringifyYaml lib pra reconstruir, OU editar cirurgicamente o trecho do produto-alvo. Cuidado pra:
    - Preservar produtos não-alvo intactos (não tocar)
    - Preservar `fullReview` block scalar (`|`) — re-parsear+stringificar pode bagunçar HTML multi-linha. Recomendo edição cirúrgica via Edit tool quando possível.
    - Atualizar campos top-level só se foram detectados como stub

12. **Git add + commit + push**:
    ```bash
    git add sites/{site}/src/content/reviews/{slug}.mdx
    git commit -m "feat({site}): preenche review de {ASIN} em {slug} via skill" \
      -m "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
    git push origin main
    ```

13. **Disparar git pull no painel da VPS**:
    ```bash
    bash scripts/painel-vps-pull.sh
    ```
    Script usa Basic Auth do painel (creds em `.env.painel-skills`).
    Substituiu SSH direto — funciona pra Marcelo e Bárbara.

14. **Reportar no chat**: counts por campo + se gerou campos top-level + path do arquivo.

## Os 6 campos do produto-no-artigo

### subtitle (10-150 chars)
Título descritivo curto, sem redundância com nome. Ex: para "Epson EcoTank L3250": "Multifuncional EcoTank com Wi-Fi, ideal para casa e home office".

### shortDescription (50-800 chars)
1-2 frases que resumem o produto. Aparece na TabelaProdutos e no TopPickCard. Ex: "Multifuncional 3 em 1 com tanque de tinta, Wi-Fi Direct e rendimento de até 4.500 páginas em preto por kit. Indicada para uso doméstico ou escritório pequeno com volume médio."

### fullReview (HTML, ~800-3000 chars)
**Estrutura obrigatória — 4 parágrafos marcados** (idêntico ao `formato_full_review` shared):

```html
<p><strong>Para quem é:</strong> ... <a href="{amazonUrl}">{nome}</a> ...</p>
<p><strong>Por que gostamos:</strong> ... <a href="{amazonUrl}">{nome ou variante}</a> ...</p>
<p><strong>Pontos de atenção:</strong> ...</p>
<p><strong>Resumo:</strong> ... <a href="{amazonUrl}">{nome}</a> ...</p>
```

**Ângulo COMPARATIVO** (diferente da página individual que é autônoma):
- Usar âncoras comparativas com moderação — variar obrigatoriamente entre:
  `"nesta seleção"` · `"desta lista"` · `"neste artigo"` · `"neste comparativo"` ·
  `"entre os produtos que analisamos"` · `"entre os modelos analisados"` · `"aqui"` (quando contexto já é claro) · ou **elide** completamente quando o contexto é óbvio
- **Máx. 2× âncora comparativa por produto.** No artigo inteiro, variar — não repetir a mesma frase produto após produto; o efeito acumula
- ❌ **`"lineup"` proibido** em conteúdo gerado — jargão em inglês sem equivalente natural; substituir sempre por uma das variantes acima
- Pode comparar com outros produtos da lista pelo nome
- Pode dizer "diferente do produto anterior" se houver fluxo narrativo

### pros (3-8 itens)
`<strong>Título</strong>: explicação com dado concreto`. Sempre dado verificável.

**Regra de comparação de preço em pros**: mencionar o próprio preço + afirmar posição ("o mais acessível desta lista") + **no máximo 1 referência comparativa**. A tabela do artigo já mostra todos os preços — listar todos os concorrentes no bullet é redundante.
- ✅ `<strong>Preço mais acessível desta lista</strong>: cerca de R$ 40, o menor entre os modelos analisados.`
- ✅ `<strong>Melhor custo por dose</strong>: R$ 40 por pote, abaixo das opções com fórmula similar (R$ 78-90).`
- ❌ `<strong>Preço mais acessível do lineup</strong>: cerca de R$ 40, abaixo do Produto A (R$ 55), Produto B (R$ 78), Produto C (R$ 80), Produto D e E (R$ 90 cada)... desta seleção.`

### cons (1-5 itens)
Mesma formatação dos pros. Trade-offs reais.

### specs (3-10 pares label/value)
Specs técnicas derivadas de `specsAmazon`/`doFabricante`/`conteudoBrutoFabricante`. Strings simples. Reuso labels do lineup quando possível.

## Voz editorial

Idêntica à da página individual (mesma régua):
- Tom de quem testou/analisou
- NUNCA cite **compradores, reviews, avaliações, estrelas, posicionamento Amazon**
- Reescreva insights de `sentimentoCompradores` como observação editorial direta

> **Sobre citar o fabricante**: regra diferente. Citar fabricante pode ser editorial OK em casos específicos (rendimento, garantia interna, certificação proprietária). Ver Armadilha 4 abaixo pra régua completa.

## Tom conversacional (CRÍTICO)

A pergunta-teste antes de salvar qualquer campo:
> *"Um amigo que não entende disso entenderia e saberia o que fazer?"*

Se não → simplifica.

Reviews afiliados são **especialista explicando pra amigo ou vizinho**: claro, direto, fluido. Sem jargão corporativo, sem formalidade institucional. Use 2ª pessoa quando faz sentido ("se você imprime em casa..."), descreva uso real ("você abre uma tampa, derrama a garrafa direto, e pronto"), conecte com a situação do leitor ("está cansado de gastar com cartucho").

**Padrões de tom — antes/depois:**

| ❌ Formal/corporativo | ✓ Conversacional |
|---|---|
| "atende quem busca dose alta de EPA e DHA" | "se você quer dose cheia de EPA e DHA em poucas cápsulas" |
| "O posicionamento da X em suplementação esportiva" | "se você treina e quer um da linha esportiva" |
| "alinhado à narrativa de procedência" | "isso encaixa com a história de pureza do produto" |
| "estrutura química mais próxima do óleo de peixe in natura" | "molécula mais parecida com o óleo natural" |
| "perfil de absorção favorável" | "absorve melhor" |
| "uma rotina de suplementação séria" | "uma rotina contínua" |
| "números compatíveis com" | "boa dose pra" |
| "tradicionalmente associada a" | "conhecida por" |

**Referências canônicas do projeto pra calibrar tom** (leia se desconfia que o output está formal demais):
- `sites/melhorimpressora/src/content/products/epson-ecotank-l3250.mdx`
- `sites/melhorimpressora/src/content/reviews/melhor-impressora-custo-beneficio.mdx`

## Operação de destilação bíblia → .mdx (CRÍTICO)

A bíblia carrega claims COM marcadores de procedência (`fonte: "specs"`, "conforme declarado pelo fabricante", "confirmado nos alérgenos"). É correto e útil internamente — rastreabilidade evita invenção. **O .mdx público é destilado**: droppa marcadores que viraram ruído burocrático.

**4 categorias de claim — como destilar cada:**

| Tipo | Bíblia (raw, OK) | .mdx destilado |
|---|---|---|
| **A) Fato verificável simples** | "Sem glúten confirmado nos alérgenos da Amazon" | "Sem glúten" |
| **B) Claim do fabricante repetível** | "Forma triglicerídeo, apontada pelo fabricante como mais absorvível" | "Forma triglicerídeo, considerada mais absorvível" |
| **C) Claim institucional / PR** | "Marca tradicional brasileira segundo o próprio fabricante" | "Marca brasileira" (ou omite se não agrega) |
| **D) Voz comprador implícita** | "Cápsulas sem sabor segundo relatos de compradores" | "Cápsulas sem sabor" |

**Exceção (raro, mas existe)**: claim do fabricante VERIFICÁVEL SÓ por ele (rendimento, garantia interna, certificação proprietária) pode manter "segundo X" se adiciona valor editorial — ver Armadilha 4 abaixo.

### AUTO-CHECK categoria D — voz-comprador IMPLÍCITA (régua v1.11.4, canon 2026-05-26)

**Categoria D é a mais traiçoeira** porque a voz-comprador vem SUTIL — não tem palavra-flag óbvia ("compradores destacam"), tem fraseado conversacional que parece análise editorial mas é relato disfarçado.

**Bíblias com voz EXPLÍCITA** ("elogiado nas opiniões", "relato recorrente"): você reconhece e destila. Fácil.
**Bíblias com voz IMPLÍCITA** ("um comprador relata", "divide opiniões", "vista por alguns como"): você COPIA LITERAL achando que é análise. Erro.

**Exemplos pareados (errado vs certo)** — TODOS de casos reais 2026-05-26 (batch melhorpretreino: dux-energy-kick, dux-pre-workout):

| ❌ Voz-comprador implícita (copiado da bíblia) | ✓ Destilado pra voz editorial |
|---|---|
| "um comprador relata sentir energia em 15 minutos" | "início rápido percebido em ~15 minutos" |
| "divide opiniões pelo sabor adocicado" | "sabor adocicado, agrada perfis específicos" |
| "vista por alguns como queda de energia depois de 2h" | "duração efetiva ~2h, requer dose espaçada em treinos longos" |
| "elogiada pela facilidade de dissolução" | "dissolve facilmente" |
| "relatada como menos potente que a versão anterior" | "potência reduzida vs versão anterior" |
| "considerada cara por parte dos compradores" | drop (preço já tem qualificador objetivo em outro lugar) |

**Auto-check obrigatório antes de gravar — grep por palavras-flag**:
- "um comprador", "alguns compradores", "parte dos compradores"
- "relata", "relatos", "relatado", "relatada"
- "divide opiniões", "vista por alguns", "considerada por", "elogiada por"
- "queixas", "elogios", "feedback dos"

Se aparecer QUALQUER ocorrência → reescreva como observação editorial direta. Sem citar quem fala. Categoria D bem destilada vira **observação técnica curta sem sujeito-comprador**.

### TERMOS TÉCNICO-INDUSTRIAIS PROIBIDOS (régua v1.11.4 formalizada, canon 2026-05-26)

Termos de **rotulagem industrial** soam burocráticos e quebram voz editorial. Régua existia em audits desde 2026-05-17 mas só foi formalizada em 2026-05-26.

**Proibidos em todo o conteúdo do produto-no-artigo**:
- "contaminação cruzada"
- "linha de produção compartilhada" (sem contexto editorial)
- "padrões de fabricação ISO XXXX" (sem agregar valor ao leitor)
- "boas práticas de fabricação" (BPF — só técnico)
- "lote de fabricação", "rastreabilidade do lote" (técnico-regulatório)

**Substituições editoriais**:
- ❌ "Pode ter contaminação cruzada com glúten" → ✓ "Pode conter traços de glúten. Leia a rotulagem antes do uso."
- ❌ "Linha de produção compartilhada com produtos com lactose" → ✓ "Pode conter traços de lactose. Confira a rotulagem se você é sensível."
- ❌ "Atende padrões ISO 22000 de segurança alimentar" → drop ou "produto seguindo padrões reconhecidos da categoria" (se agregar)

**Por quê proibido**: reviews afiliados são especialista→amigo, não bula técnica. Termo técnico-industrial sinaliza copy-paste de ficha técnica ou ChatGPT genérico — quebra confiança editorial.

## Peso por fonte

Ao decidir QUAL claim vira pro central no artigo vs. spec:

| Combinação de fontes | Confiança | Onde usar |
|---|---|---|
| Fabricante + Amazon coincidem | **FORTE** | Pode ser pro central, strong, ênfase no fullReview |
| Só fabricante | MÉDIO | OK em pros/specs, descrição própria (sem "segundo X") |
| Só Amazon (specsAmazon) | **FRACO** | Só na tabela specs, NÃO vira pro central |
| Só opiniões | FRACO | Inspira voz, não cita |

**Caso real (Vitafor B07L5W6GVC)**: "Composição cetogênica" vem de `Tipo de dieta: Cetogênica` nas specs Amazon — fonte fraca, classificação automática do marketplace. Vai na tabela specs, **não vira pro central**. Óleo de peixe é trivialmente keto; elevar isso a "diferencial" engana o leitor.

## Filtros editoriais

- Specs ambientais (Energy Star, EPEAT, RoHS, % reciclado) → omitir
- Origem de fabricação (Brasil, Made in X) → omitir
- Exceção: se bíblia tem ângulo explícito (sustentabilidade, produto-nacional) em `angulosConversao`

## Restrições finais

- Sem travessão (—)
- Sem superlativos ABSOLUTOS sem evidência ("o melhor", "o mais X", "incomparável", "único", "imbatível")
- ✓ Qualificadores positivos simples ("excelente", "ótimo", "muito bom") são OK — reviews são levemente inclinados ao positivo por design (diretriz #2 da bíblia)
- ✓ Superlativas qualificadas com dado: "entre as mais econômicas da categoria" (se houver concorrentes na bíblia)
- Densidade ~5-7 dados quantitativos no fullReview
- ❌ `"lineup"` proibido em conteúdo gerado — substituir por "desta lista", "desta seleção", "neste comparativo", "entre os modelos analisados"
- Âncoras comparativas ("desta seleção", "nesta seleção", "desta lista", etc.): máx. 2× por produto; variar ao longo do artigo (ver Ângulo COMPARATIVO acima)
- Termos técnicos de nicho (ingredientes, processos, farmacologia) → glossar na **primeira ocorrência** do artigo com explicação breve entre parênteses; nas seguintes, usar livremente. Ex: "parestesia (formigamento na pele)", "BCAAs (aminoácidos essenciais)", "cafeína anidra (cafeína seca, a forma padrão)"

## Anti-duplicate vs página individual

**Antes de gerar**, leia a página individual do produto (`content/products/{slug}.mdx`) e identifique frases-chave do `fullReview`. **Não repita** essas frases no artigo. Use ângulo comparativo (vs autônomo da página individual):

| Página individual (autônoma) | Produto no artigo (comparativo) |
|---|---|
| "A L3250 é uma multifuncional pensada para uso doméstico" | "Na seleção, a L3250 cobre o perfil doméstico" |
| "O diferencial central é o sistema EcoTank" | "Comparada às outras impressoras desta lista, a L3250 destaca-se pelo sistema EcoTank" |

## Armadilhas recorrentes

### 1. Repetir frase exata da página individual
Confere antes de salvar. Se uma frase específica está na página individual, reescreva.

### 2. HTML proibido por hábito
`<ul>` é tentador pra listar features. Use parágrafos.

### 3. Comparações sem dado
"Uma das mais econômicas" sem `concorrentes` na bíblia é especulação. Use linguagem absoluta com dado: "rende 4.500 páginas por kit" em vez de "rende mais que a maioria".

### 4. Voz de citação — comprador, fabricante, Amazon ("segundo X", "alérgenos confirmam", "atributos declaram")

**Armadilha mais comum e fácil de cair.** Quando os dados da bíblia vêm de várias fontes, o modelo tende a citar a fonte pra justificar o claim. Há 3 tipos de citação com tratamentos diferentes:

**A) Citar comprador → SEMPRE proibido**
- ❌ "Compradores destacam X" → "X destaca-se por {dado da bíblia}"
- ❌ "Relato recorrente nas opiniões indica cápsulas sem sabor" → "cápsulas sem sabor"
- ❌ "Citada como motivo de preferência por um comprador" → drop ou reformula

**B) Citar Amazon/specs → SEMPRE proibido (burocrático)**
- ❌ "alérgenos da Amazon confirmam ausência de glúten" → "sem glúten"
- ❌ "atributos de material declaram ausência de contaminantes" → "livre de contaminantes"
- ❌ "conforme tipo de dieta declarado" → "compatível com dieta X"

**C) Citar fabricante → CONDICIONAL (editorial OK em casos específicos)**

Régua: voz-citação do fabricante OK SÓ quando atende AS DUAS condições:
1. **(a)** qualifica claim que SÓ o fabricante pode fazer (rendimento, garantia interna, certificação proprietária)
2. **(b)** adiciona valor editorial ao leitor (calibra expectativa, sinaliza honestidade, faz crítica)

**✓ EDITORIAL OK** (referência: `sites/melhorimpressora/src/content/products/epson-ecotank-l3250.mdx`):
- "rende até 4.500 páginas em preto, **segundo a Epson**" → claim só-fabricante + qualifica rendimento
- "número de marketing 33 ppm, mas a **velocidade ISO (padrão da indústria)** é mais realista" → crítica útil
- "a HP recomenda volume de 50 a 100 páginas mensais" → claim só-fabricante + ajuda leitor calibrar

**❌ BUROCRÁTICA** (drop sempre):
- "apontada pelo fabricante como mais absorvível" → "considerada mais absorvível"
- "segundo o próprio fabricante" como muleta repetitiva → drop
- "conforme o fabricante" sem qualificar nada → drop

**Tratamento de divergências internas** (dadosInconsistentes): a `decisaoEditorial` da bíblia já diz qual lado tomar. Aplica direto, sem mencionar o conflito.

**Antes de gravar, faça grep mental**: se aparece "confirmado", "declarado", "apontada", "conforme X", "segundo Y", "relato recorrente", "atributos de material" — reescreva. Exceção: passou nos 2 critérios editoriais (C) acima.

### 5. Atualizar campos top-level quando não-stub
Se o artigo já tem `title`, `description`, `excerpt` populados, NÃO sobrescreva (preserva trabalho do user). Só preenche se estão vazios.

### 6. Block scalar `|` no fullReview
Se reusar a abordagem yaml.parseYaml + stringify, fullReview pode mudar de `|` pra string quoted, bagunçando HTML. Recomendado: edição cirúrgica com Edit tool no trecho do produto-alvo, preservando o resto do arquivo intacto.

## Invocação

Exemplos válidos do user:
- "preenche o review da L3250 no artigo melhor-impressora-custo-beneficio do melhorimpressora"
- "preenche o produto B098YHFT9S no artigo X de Y"
- "preenche melhorimpressora/melhor-impressora-custo-beneficio B098YHFT9S"

Args canônicos que invoco:
- `Skill(skill="artigo-review-criar", args="melhorimpressora/melhor-impressora-custo-beneficio B098YHFT9S")`

## Limitação intrínseca conhecida

Sem schema Zod programático no output (diferente do painel), validação fica editorial — eu sigo as regras. ~5% de chance de algum campo ficar levemente fora do limite editorial. Build do Astro é gate final.
