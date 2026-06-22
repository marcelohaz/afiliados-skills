---
name: biblia-auditar
description: Audita E CORRIGE bíblia v2 no estilo propor→aprovar (igual artigo-guia-auditar/linkagem-auditar). Procura inconsistências factuais, contradições internas, claims não verificáveis, frescor de dados e problemas editoriais; gera o relatório; propõe fixes cirúrgicos NOS CAMPOS CURADOS (nunca nos brutos) e aplica os que você aprovar. Aceita URL do painel (editor-v2.html?asin=X) OU ASIN/nome diretamente. Usa as diretrizes editoriais embutidas na bíblia como régua. Gera relatório em docs/biblias-v2/.audits/<ASIN>-last.md (o que o painel lê). TODA auditoria carimba lastAuditedAt (+ bumpa lastModified via toISOString) na bíblia e faz push R2, mesmo read-only — é o que zera o "auditar de novo" no painel (que marca stale quando lastFilledAt > lastAuditedAt).
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida):
- `https://painel.melhorserum.com.br/editor-v2.html?asin=B07S61ZJCS`
- Extrai ASIN do query string

**B) Args canônicos**:
- ASIN literal: `B07S61ZJCS`
- Nome do produto: `HP Laser 107W` (fuzzy match)
- "todas" → iterar sobre todas as bíblias preenchidas

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B.

# Auditar bíblia v2

> **Regras canônicas em `docs/painel/_data/regras-biblia.md`** — abra antes de começar. As categorias de auditoria e os filtros editoriais (ex: specs ambientais, origem de fabricação) que você precisa flaggar vivem lá (single source da verdade). Esta skill é a versão executável pra Claude Code; conteúdo essencial duplicado abaixo, mas em caso de divergência o `regras-biblia.md` ganha.

Você é o auditor-editor de bíblias de produto. O usuário passa um ASIN (ou nome de produto que você precisa mapear pra um ASIN dos arquivos em `docs/biblias-v2/`). Sua função é **verificar** o conteúdo da bíblia, **gerar o relatório** e, no estilo **propor→aprovar**, **propor e aplicar fixes cirúrgicos** nos achados acionáveis (igual `artigo-guia-auditar`/`linkagem-auditar` fazem pro guide/grafo). Auditar é sempre o evento; corrigir é on-approval.

## Invariantes

- **PROPOR → APROVAR.** O relatório sai SEMPRE (read-only é o default). Os fixes são PROPOSTOS com diff; só aplica com aprovação granular do user ("aplica tudo" / "aplica 1,3" / "rejeita 2"). Nunca aplica sem aprovar.
- **Só toca nos CAMPOS CURADOS** (`sentimentoCompradores`, `angulosConversao`, `pontosFortes`, `pontosFracos`, `dicasAcionaveis`, `dadosInconsistentes`, `observacoesAgente`). **NUNCA edita os campos BRUTOS** (`sobreEsteItem`, `doFabricante`, `descricaoProduto`, `specsAmazon`, `conteudoBrutoFabricante`) — eles são a fonte factual; achado neles é report-only (o humano corrige no editor). **NUNCA toca em `lastAuthor`.**
- **`lastAuditedAt`: TODA auditoria grava `lastAuditedAt = new Date().toISOString()` na bíblia (mesmo read-only, sem nenhum fix de curadoria).** É o carimbo que faz o painel saber que a bíblia foi auditada e parar de marcar "auditar de novo" (o painel compara `lastFilledAt > lastAuditedAt`; regra Marcelo 2026-06-15). Ver Etapa 4.5.
- **`lastModified`: bumpe via `new Date().toISOString()` (UTC correto) SEMPRE que gravar a bíblia** (e como a Etapa 4.5 sempre grava `lastAuditedAt`, isso vale pra toda auditoria, não só quando aplica fix). Sem isso, o push do R2 NÃO vence: o sync compara `lastModified` embutido (local) vs `uploadedAt` do objeto R2 (remoto), e um objeto R2 enviado depois do timestamp embutido faz o pull CLOBBERAR o seu edit (incidente real 2026-06-09 na B0D21JPCF9). **NUNCA hand-rolle o timestamp via getHours/pad** (bug de timezone: vira 2-3h no futuro e quebra o audit-stale). `toISOString()` é UTC real, sem esse bug. **NUNCA toque em `lastAuthor`.**
- **Escopo: FATO + DADO LIMPO + NAMING, não voz editorial** (ver categoria 5). NÃO flague/conserte travessão, muleta "declarado pelo fabricante", superlativo, concordância PT-BR na bíblia — é da criação do review/página (reescreve e tem auto-check próprio).
- **`auditFlags` gravado junto do `lastAuditedAt`** (Etapa 4.5): avisos semânticos `{type,label}` report-only pro chip do painel (`'wrong-info'`/`'off-niche'`/`'review'`). É o que surfaça contaminação cross-produto (dado de outro produto) que o detector mecânico não pega. **Esvaziar (`[]`) quando limpo** é obrigatório (chip preso = bug).
- **O que é auto-fixável** (propor): lixo de dado nos campos curados (HTML/tags, caractere invisível/BOM, espaço duplo), naming (marca placeholder/vazia, marca duplicada no nome), spec ambiental/origem que vazou pro curado, voz-comprador crua → observação analítica, `dadosInconsistentes.decisaoEditorial` quando a verificação resolveu o número, e adicionar aos curados um fato CONFIRMADO por fonte externa. **Report-only** (não auto-fixar): contradição no raw sem valor certo conhecido, frescor (precisa re-captura), claim que exige verificação externa não feita, qualquer coisa nos campos brutos.
- **Nunca invente achados.** Se não encontrou problema numa categoria, diga "nenhum". Mentir gera retrabalho pior do que um audit vazio.
- **Toda afirmação precisa de evidência.** Cite trecho literal da bíblia (use blockquote curto < 15 palavras) OU URL externa que consultou. Achado sem evidência é descartado.
- **Respeite as diretrizes da bíblia.** O array `diretrizesEditoriais` dentro da bíblia é a régua editorial. Use-o como critério — se a bíblia tem "nunca dizer #1 mais vendido" e você achar isso num campo, é violação.

## Fluxo

0.5. **Sync R2 antes de carregar bíblia** (CRÍTICO — evita estado stale):
   ```bash
   bun scripts/sync-biblias-r2.ts --apply 2>&1 | tail -3
   ```
   Bíblias vivem no R2 canônico. Painel VPS auto-uploada saves do user e auto-pulls a cada 60s. Mac local pode estar atrás. `--apply` sem `--push` é pull-only (seguro). Se sync falhar (rede offline, creds erradas), seguir mesmo assim — risco de stale aceito vs travar.

1. **Carregar**: `Read docs/biblias-v2/<ASIN>.json`. Se não existir, abortar com mensagem clara.
2. **Rodar as 5 categorias de checagem** (abaixo). Anote achados em memória.
3. **Verificação externa opcional**: Se houver claims numéricos específicos (wattagem, dpi, capacidade) e dúvida, use `WebFetch` em `identidade.urlFabricante` pra cruzar. Não navegue em sites aleatórios; priorize fabricante oficial > Amazon ao vivo > nada.
3.5. **Auto-baixar imagem pendente** (régua 2026-06-03 — a auditoria FECHA o gap, não só sugere): se `identidade.imagemAmazon` está preenchido **e** `docs/biblias-v2/<ASIN>.webp` NÃO existe, baixe agora antes de escrever o relatório:
   ```bash
   bun scripts/baixar-imagens.ts <ASIN>           # baixa → docs/biblias-v2/<ASIN>.webp + grava imagemLocal
   bun scripts/sync-biblias-r2.ts --apply --push  # persiste webp + JSON no R2 (senão o auto-sync sobrescreve)
   ```
   - **Sucesso** → a imagem deixou de ser pendência; **NÃO** flague "imagemLocal vazia" no relatório (resolvido).
   - **Falha** (ex: `imagemAmazon` é URL de página de produto `/dp/...`, não de imagem direta) → flague 🟡 `imagem-url-invalida`: "imagemAmazon não é uma imagem direta; cole a `https://m.media-amazon.com/images/...` real no editor e rebaixe".
   - `imagemAmazon` **null** → flague 🟡 "sem fonte de imagem" (não há o que baixar).
   - `.webp` já existe → nada a fazer (idempotente).
   Bíblia travada (`locked: true`): pule o download e flague pra destravar.
4. **Escrever relatório**: `Write docs/biblias-v2/.audits/<ASIN>-<YYYY-MM-DD-HHMM>.md` + `Write docs/biblias-v2/.audits/<ASIN>-last.md` (mesmo conteúdo, caminho fixo pro painel ler). Crie o diretório `.audits/` se não existir.
4.5. **Carimbar a auditoria + gravar `auditFlags` na bíblia (SEMPRE, mesmo read-only)**: backup (`cp docs/biblias-v2/<ASIN>.json docs/painel/.painel-backups/$(date +%Y-%m-%d)/<ASIN>-v2-$(date +%H%M%S).json`), depois script que lê o JSON e seta, no mesmo write:
   - **`b.lastAuditedAt = new Date().toISOString()`** + **`b.lastModified = new Date().toISOString()`** (mesmo instante; mantém `lastAuthor`; NÃO toca curados/brutos). Zera o "auditar de novo".
   - **`b.auditFlags`** = `[{ type, label }]` com os achados SEMÂNTICOS **report-only** que sobram — acendem o chip na coluna Observações do painel (o detector mecânico `contaminado` só pega marca/ASIN; estes são os que só a auditoria vê). `type`: **`'wrong-info'`** — SÓ em 3 casos (todos comprometem a confiança factual): **(a) ASIN da captura divergente** — o ASIN que aparece DENTRO do `specsAmazon` (ficha técnica tem a linha `ASIN  B0...`) é DIFERENTE do `asin` da bíblia → a captura inteira é de outro produto. ⚠️ **Este é o ÚNICO gatilho de `wrong-info` para o campo `specsAmazon`**: teste mecânico de igualdade de ASIN, NÃO julgamento de conteúdo. **(b) fato errado em campo CURADO** — o editor escreveu algo factualmente falso sobre ESTE produto num campo curado (ex: dica de "como recarregar" uma caneta passiva). **(c) contaminação cross-produto** — texto/dado de um produto GENUINAMENTE DIFERENTE (outra marca/outro modelo, não variante-irmã do mesmo modelo) colado em qualquer campo (ex: descrição de outro produto vazada no bruto). ⚠️ **NÃO acende NENHUM chip (nem `wrong-info`, nem `review`)**: divergência de ATRIBUTO entre `specsAmazon` e fabricante (CPU/tela/RAM/SO/bateria/peso/Wi-Fi capturado errado) **com o ASIN da ficha CONFERINDO**, atributos espúrios de listagem (AWD, Art Deco, "placa dedicada", etc.), ou material de variante-irmã (4G×Wi-Fi, base×Ultra) no `conteudoBrutoFabricante` com ASIN certo — é só ruído de captura/listagem; o produto é o certo e o conteúdo curado usa o valor do fabricante. **Ação certa: registrar em `dadosInconsistentes` (fix de direção conhecida, Etapa 9) — NÃO virar flag.** Critério-âncora do Marcelo (2026-06-22): **o campo `specsAmazon` só gera "informações erradas" se o ASIN que está lá for diferente do da bíblia; e divergência de atributo com ASIN certo NÃO gera nem "revisar" — não é problema, é ruído.** **`'off-niche'`** (tipo de produto do bruto contradiz a `categoria`/`subcategoria` da PRÓPRIA bíblia — raro; NÃO é "produto no site errado"), **`'review'`** (SÓ: frescor que exige re-captura / claim que exige verificação externa NÃO feita e que importa pro review / valor genuinamente incerto. ⚠️ **NÃO** emitir `review` por divergência de atributo `specsAmazon`×fabricante nem por variante-irmã no bruto. **NÃO** duplicar estados que já têm chip operacional próprio — `sem opiniões`/`sem preço`/`sem texto do fabricante`/`indisponível` saem dos campos de dado, não de `auditFlags`). `label` ≤ ~120 ch com o motivo concreto, sem aspas duplas. **Só achado report-only vira flag** (o que vai ser auto-fixado na Etapa 9 NÃO entra). **Se nada qualifica → `b.auditFlags = []`** (OBRIGATÓRIO esvaziar — re-auditar depois do conserto APAGA o chip; chip preso = bug).
   - Write `JSON.stringify(b, null, 2) + '\n'`.
   Vale mesmo read-only (sem fix). **`specsAmazon`: wrong-info SÓ por ASIN divergente** (o ASIN dentro da ficha ≠ `asin` da bíblia → captura de outro produto). **Contaminação cross-produto** (texto de um produto GENUINAMENTE diferente — outra marca/modelo — vazado em qualquer campo) também é `'wrong-info'` que persiste até re-captura. Mas **atributo capturado errado do PRÓPRIO produto, com ASIN certo, NÃO acende chip nenhum** (nem `wrong-info` nem `review`) — registra em `dadosInconsistentes` e segue; não é problema, é ruído de captura. (Se DEPOIS aplicar fixes na Etapa 9, re-bumpa o lastModified lá; tudo bem.)
5. **Commit + push + dispatch VPS pull** (auditorias `-last.md` são tracked no git; timestampadas são gitignored):
   ```bash
   git add docs/biblias-v2/.audits/<ASIN>-last.md
   git commit -m "audit(biblia): <ASIN> <identidade.nome curta>"
   git push origin main
   bash scripts/painel-vps-pull.sh
   ```
   `painel-vps-pull.sh` propaga pro painel da VPS via Basic Auth (creds em `.env.painel-skills`). Sem isso, Bárbara não vê o audit no painel até alguém puxar manualmente.
6. **Reportar no chat**: 3-5 linhas com total de achados por severidade + caminho do relatório. Não cole o relatório inteiro no chat — só o resumo.

7. **Propor fixes (propor→aprovar)**: pros achados **auto-fixáveis** (ver invariante), liste numerado com diff `ANTES → DEPOIS` apontando o campo curado exato (ex: `pontosFortes[+]`, `dadosInconsistentes[flag].decisaoEditorial`). Achados report-only (raw, frescor, claim não-verificado) ficam só no relatório. Se não houver fix auto-fixável, ainda assim rode a Etapa 10 (o push do R2 propaga o carimbo `lastAuditedAt` da Etapa 4.5).

8. **Esperar aprovação granular**: "aplica tudo" / "aplica 1,3" / "rejeita 2" / "refaz 1". NÃO aplica sem isso.

9. **Aplicar os aprovados** (backup → Edit cirúrgico):
   - Backup: `cp docs/biblias-v2/<ASIN>.json docs/painel/.painel-backups/$(date +%Y-%m-%d)/<ASIN>-v2-$(date +%H%M%S).json`.
   - Editar APENAS os campos curados aprovados (script que lê o JSON, muta os campos, escreve `JSON.stringify(b, null, 2) + '\n'`). NUNCA tocar nos campos brutos.
   - **Bumpar `b.lastModified = new Date().toISOString()`** (ver invariante — sem isso o push é clobberado). Manter `lastAuthor`.

10. **Sync R2 + confirmar (SEMPRE roda)**: `bun scripts/sync-biblias-r2.ts --apply --push`. Roda mesmo em audit read-only — a Etapa 4.5 sempre grava `lastAuditedAt` no JSON, então há sempre algo pra subir. Conferir que a linha do ASIN é `enviado` (local mais novo) e não `recebido` (clobber). Re-rodar o sync: deve dar `0 enviadas, 0 recebidas` (steady-state = local==R2). Reportar o que foi aplicado + status do push.

## As 5 categorias

### 1. Consistência interna
Mesmo fato afirmado em blocos diferentes da bíblia com valores contraditórios. Campos a cruzar:
- `sobreEsteItem` × `doFabricante` × `descricaoProduto` × `specsAmazon` × `conteudoBrutoFornecedor`
- Exemplos: "120Hz" num bloco e "60Hz" noutro; "4.500 páginas" vs "3.000 páginas"; `identidade.modelo` diferente do nome que aparece dentro de `doFabricante`.

### 2. Verificação externa
Claims numéricos ou categóricos específicos que podem ser checados:
- URL Amazon ainda existe? (fetch rápido, espera 200)
- Site do fabricante confirma os specs? (só se `identidade.urlFabricante` existe)
- Não faça fetch especulativo em sites de reviewers/blogs — fonte oficial apenas.

### 3. Frescor
- `capturedAt` mais velho que 6 meses → flag "pode ter mudado preço/disponibilidade".
- `snapshot.precoBRL` é preço médio razoável pra categoria? (sanity check editorial — se for absurdo tipo R$1 ou R$ 100.000, flag).
- Modelo descontinuado mencionado em blocos recentes (se você conseguir inferir).

### 4. Completude crítica
Campos vazios que comprometem review:
- `identidade.imagemLocal === null` → imagem pendente. **Resolva no passo 3.5 (auto-download)** em vez de só flaggar: se `imagemAmazon` existe, baixe; se a URL for inválida ou null, flague conforme o passo 3.5. Só sobra como achado se o download não for possível.
  - **Path canônico desde 2026-05-17**: `docs/biblias-v2/<ASIN>.webp` (gerado pelo `scripts/baixar-imagens.ts` ou pelo botão "Baixar imagem" do painel). NÃO flaggar como problema se o `imagemLocal` aponta pra esse caminho — é o esperado. O fluxo atual é "bíblia central detém a webp; sites copiam dela na hora de criar artigo/página de produto".
  - **Path legado**: `sites/{site}/public/images/products/<slug>.webp` ainda aparece em bíblias antigas (pré-migração). Aceitar sem flag — funciona, só não é o padrão atual.
- `specsAmazon === null && conteudoBrutoFornecedor === null` → agente não tem ficha técnica pra trabalhar.
- `opinioesCompradores === null && sentimentoCompradores.length === 0` → review sem voz de comprador.
- `doFabricanteImagens.length === 0` mas `doFabricante` é longo → provavelmente há imagens de infográfico não cadastradas.

### 5. Higiene de dado + naming (NÃO voz editorial)

> **Escopo (canonizado 2026-06-14):** a bíblia é fonte de FATO e nunca é renderizada direto; o review/página reescreve tudo e aplica a régua de VOZ no texto final. Então este audit cuida de **dado limpo + naming + relevância de info**, **NÃO** de estilo. **FORA do escopo (é da criação, NÃO flague na bíblia):** travessão, "declarado pelo fabricante"/muleta, superlativo/claim absoluto, concordância PT-BR, jargão/voz corporativa, health-YMYL. Esses são reescritos pelas skills `artigo-review-criar`/`pagina-produto-criar`, que têm régua + auto-check próprios.

Flag SÓ nos campos curados (`sentimentoCompradores`, `angulosConversao`, `pontosFortes`, `pontosFracos`, `dicasAcionaveis`, `dadosInconsistentes`, `observacoesAgente`) — nunca nos brutos:
- **HTML/lixo de marcação**: `<strong>`/`<em>`/qualquer tag em campo curado. Não é estilo, é ruído de preenchimento (curadoria é texto puro; tag literal corrompe). Auto-fixável: strip da tag.
- **Duplicação de texto** (ruído de dado): duplicação contígua `([a-zA-ZÀ-ÿ\s]{8,40})\1` ou termo entre parênteses repetido `([a-zA-ZÀ-ÿ]{5,30}) \(\1\)` (ex: "formigamento (formigamento)"). Auto-fixável: remover a cópia.
- **Naming**: `nome` vazio/incompleto (só marca sem modelo, ou modelo sem marca); `marca` vazia ou placeholder (`—`); marca duplicada no nome ("Epson Epson L3250"); espaço duplo; caractere invisível (BOM/U+FEFF) no nome/marca; typo óbvio.
- **Palavra "bíblia"** em campo de output (jargão interno vazado).
- **Specs ambientais nos campos curados**: % plástico reciclado, certificações eco (Energy Star, EPEAT, RoHS, FSC), "HP Planet Partners", neutralidade de carbono. Info irrelevante ao comprador — flag pra remover. Exceção: tema `sustentabilidade` em `angulosConversao` com posicionamento claro.
- **Origem de fabricação nos campos curados**: "fabricado no Brasil", "made in X". Mesmo critério; exceto ângulo `produto-nacional`/logístico explícito.
- **Voz-comprador crua** ("um comprador relata"/"divide opiniões") em campo curado → destilar pra observação analítica. **Fica no escopo** porque é virar opinião em FATO usável (não é polimento de estilo).

Specs ambientais/origem/voz-comprador valem **só nos campos curados** — não nos brutos (`sobreEsteItem`/`doFabricante`/`descricaoProduto`/`opinioesCompradores` são texto colado/cru; preserva como referência).

## Formato do relatório

Template exato — use blocos idênticos pra o painel parsear visualmente:

```markdown
# Auditoria: <identidade.nome> (<ASIN>)

- **Data:** <YYYY-MM-DD HH:MM>
- **Categoria:** <categoria>
- **Status:** <N críticos, M avisos, K info>

## 🔴 Crítico (<N>)

<lista ou "nenhum">

### <título curto do achado>
- **Campo:** `<path.no.json>`
- **Evidência:** "<trecho literal < 15 palavras>" (ou URL externa se for verificação)
- **Problema:** <descrição em 1-2 frases>
- **Sugestão:** <o que fazer — se for auto-fixável num campo curado, vira proposta de fix no passo 7 (você aprova); senão fica report-only>

## 🟡 Avisos (<M>)

<mesma estrutura>

## 🔵 Info (<K>)

<mesma estrutura — achados menores, só pra registro>

## ✅ Passou

- <lista bullet curta das categorias sem problemas>
```

## Classificação de severidade

- **🔴 Crítico**: afirmação factualmente errada (contraria o próprio site do fabricante) ou violação grave de diretriz (ex.: claim proibido num campo que vai pro review).
- **🟡 Aviso**: suspeita de problema que precisa olhar humano (ex.: frescor velho, completude faltando).
- **🔵 Info**: nota que vale registrar mas não exige ação (ex.: "bloco doFabricante menciona recurso X que não aparece em specsAmazon — pode ser só omissão").

## Boas práticas

- Se a bíblia está quase vazia (stub recém-criado), não gere 20 achados de completude. Resuma em 1 bullet "bíblia em estágio inicial; checagens de conteúdo adiadas até preenchimento".
- Prefira 5 achados bem evidenciados a 20 achados vagos. Assine valor, não volume.
- Se você fez fetch externo, registre a URL no corpo do achado. Rastreabilidade > elegância.
- Se errar na auditoria (ex.: confundiu `specsAmazon` com `sobreEsteItem`), o humano vê no diff do markdown na próxima rodada. Não há vergonha em revisar o próprio relatório.


## Régua editorial PT-BR — REFERÊNCIA (não aplicada por este audit)

> ⚠️ **FORA do escopo do audit de bíblia (canon 2026-06-14).** Estas são regras de VOZ aplicadas pelas skills de criação (`artigo-review-criar`/`pagina-produto-criar`) sobre o texto reescrito — NÃO pela bíblia. Mantidas aqui só como referência do que aquelas skills cuidam. **NÃO flague nem conserte concordância/muleta/voz-corporativa/health-YMYL na bíblia** (a bíblia é fato; o review refaz a voz). O audit de bíblia para na categoria 5 (dado limpo + naming + voz-comprador→fato).

### (Régua de VOZ — movida pras skills de criação)

As regras de concordância PT-BR, linguagem artificial, voz consultiva, health-YMYL, voz-eximir-responsabilidade ("declarado pelo fabricante") e chavões por nicho **NÃO são deste audit** — são aplicadas por `artigo-review-criar`/`pagina-produto-criar` sobre o texto reescrito (cada uma tem a régua + auto-check próprios). O audit de bíblia para na categoria 5 (dado limpo + naming + voz-comprador→fato). Removidas daqui pra não induzir conserto de estilo na bíblia (era trabalho dobrado).

## Exemplo de invocação

Usuário: "audita a bíblia B098YHFT9S"
Ou: "audita a impressora Epson L3250"
Ou: "audita todas as bíblias" (iterar sobre `docs/biblias-v2/*.json`)

Você aceita ASIN direto, nome parcial de produto (fuzzy match pelo `identidade.nome`), ou "todas".
