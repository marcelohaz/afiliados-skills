---
name: biblia-auditar
description: Audita e corrige a bíblia v2 de UM produto (docs/biblias-v2/<ASIN>.json) em contradições entre brutos e entre curado e bruto (inclusive o campo `fonte`), registro de inconsistência já extinto, claim sem lastro, frescor, imagem anexada não lida, naming e voz-comprador. Mexe só nos campos curados, carimba a auditoria e grava o relatório que o painel lê. Use quando pedirem para auditar, revisar ou conferir uma bíblia, por ASIN, nome do produto ou URL do editor-v2. Para várias de uma vez, use biblia-auditar-em-massa.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida):
- `https://painel.melhordrone.com.br/editor-v2.html?asin=B07S61ZJCS`
- Extrai ASIN do query string

**B) Args canônicos**:
- ASIN literal: `B07S61ZJCS`
- Nome do produto: `HP Laser 107W` (fuzzy match)
- "todas" ou mais de um ASIN → use a `biblia-auditar-em-massa` (um sub-agent isolado por bíblia)

Detecção: $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B.

# Auditar bíblia v2

> **Regras canônicas em `docs/painel/_data/regras-biblia.md`** — abra antes de começar. As categorias de auditoria e os filtros editoriais (ex: specs ambientais, origem de fabricação) que você precisa flaggar vivem lá (single source da verdade). Esta skill é a versão executável pra Claude Code; conteúdo essencial duplicado abaixo, mas em caso de divergência o `regras-biblia.md` ganha.

Você é o auditor-editor de bíblias de produto. O usuário passa um ASIN (ou nome de produto que você precisa mapear pra um ASIN dos arquivos em `docs/biblias-v2/`). Sua função é **verificar** o conteúdo da bíblia, **gerar o relatório** e, no estilo **propor→aprovar**, **propor e aplicar fixes cirúrgicos** nos achados acionáveis (igual `artigo-guia-auditar`/`linkagem-auditar` fazem pro guide/grafo). Auditar é sempre o evento; corrigir é on-approval.

## Invariantes

- **Full-auto: aplica o conserto e reporta o de→para** (mesma régua da `biblia-auditar-em-massa`). Conserto de direção conhecida aplica sem perguntar, inclusive o de julgamento (voz-comprador→análise, `decisaoEditorial` atualizada, fato confirmado em fonte oficial com a URL no registro). Depois de aplicar, re-audite os campos tocados; conserto que não se sustenta volta do backup e vira report-only. Report-only fica só o indeterminável: valor sem fonte única, frescor que exige re-captura, verificação externa não feita, qualquer coisa nos brutos.
- **Toca nos CAMPOS CURADOS** (`sentimentoCompradores`, `angulosConversao`, `pontosFortes`, `pontosFracos`, `dicasAcionaveis`, `dadosInconsistentes`, `observacoesAgente`) **+ naming em `identidade` (`nome`/`marca`) quando o fix é óbvio** (derivável dos dados da própria bíblia). **NUNCA edita os campos BRUTOS** (`sobreEsteItem`, `doFabricante`, `descricaoProduto`, `specsAmazon`, `conteudoBrutoFabricante`) **nem `avisosAoAgente`** — os brutos são a fonte factual e o `avisosAoAgente` é o canal do HUMANO; achado neles é report-only (o humano corrige no editor). **NUNCA toca em `lastAuthor`.**
- **`lastAuditedAt`: TODA auditoria grava `lastAuditedAt = new Date().toISOString()` na bíblia (mesmo read-only, sem nenhum fix de curadoria).** É o carimbo que faz o painel saber que a bíblia foi auditada e parar de marcar "auditar de novo" (o painel compara `lastFilledAt > lastAuditedAt`; regra Marcelo 2026-06-15). Ver Etapa 4.5.
- **`lastModified`: bumpe via `new Date().toISOString()` (UTC correto) SEMPRE que gravar a bíblia** (e como a Etapa 4.5 sempre grava `lastAuditedAt`, isso vale pra toda auditoria, não só quando aplica fix). Sem isso, o push do R2 NÃO vence: o sync compara `lastModified` embutido (local) vs `uploadedAt` do objeto R2 (remoto), e um objeto R2 enviado depois do timestamp embutido faz o pull CLOBBERAR o seu edit (incidente real 2026-06-09 na B0D21JPCF9). **NUNCA hand-rolle o timestamp via getHours/pad** (bug de timezone: vira 2-3h no futuro e quebra o audit-stale). `toISOString()` é UTC real, sem esse bug. **NUNCA toque em `lastAuthor`.**
- **Escopo: FATO + DADO LIMPO + NAMING, não voz editorial** (ver categoria 5). NÃO flague/conserte travessão, muleta "declarado pelo fabricante", superlativo, concordância PT-BR na bíblia — é da criação do review/página (reescreve e tem auto-check próprio).
- **`auditFlags` gravado junto do `lastAuditedAt`** (Etapa 4.5): avisos semânticos `{type,label}` report-only. `'wrong-info'` e `'off-niche'` acendem o chip na coluna Observações; `'review'` é nota de auditoria (fica no relatório `-last.md` e no editor, não pinta a coluna nem tira a bíblia de "Prontos para clonar"), e é gravada sempre que o achado couber. É o que surfaça contaminação cross-produto que o detector mecânico não pega. Esvaziar (`[]`) quando limpo é obrigatório: chip preso é bug.
- **O que é auto-fixável**: lixo de dado nos campos curados (HTML/tags, caractere invisível/BOM, espaço duplo), naming (marca placeholder/vazia derivável dos dados, marca duplicada no nome), spec ambiental/origem que vazou pro curado, voz-comprador crua → observação analítica, `dadosInconsistentes.decisaoEditorial` quando a verificação resolveu o número, e adicionar aos curados um fato CONFIRMADO por fonte externa. Destes, o **óbvio/determinístico aplica direto** (naming derivável, HTML-strip, BOM, espaço duplo); o que tem **julgamento** (reescrita de voz, decisaoEditorial, fato externo) vai por **propor→aprovar** (ver 1º invariante). **Report-only** (nunca auto-fixar): contradição no raw sem valor certo conhecido, frescor (precisa re-captura), claim que exige verificação externa não feita, qualquer coisa nos campos brutos.
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
   ⚠️ **Leia `avisosAoAgente` ANTES de qualquer checagem.** É o único canal em que o humano manda na
   bíblia, e costuma explicar o que você está prestes a interpretar como defeito. Confira instrução por
   instrução se a bíblia obedece; cada uma não respeitada é achado com a instrução literal como evidência.
   Sem avisos, siga.
1.5. **Ler a fila de pendências vindas das páginas** (canon 2026-09-24):
   `bun scripts/biblia-pendencias.ts list <ASIN>`. Cada item é um problema que a auditoria de uma
   PÁGINA achou nesta bíblia, com o campo, o problema e a evidência do bruto. **Entrada obrigatória:**
   confira cada um contra os brutos e decida: consertar (entra nos achados), improcedente (diga por
   quê) ou indeterminável (vira `auditFlags` de revisão). A fila existe porque o relatório da página
   ninguém lia de volta: em 24/09 seis bíblias aprovadas tinham problema de fato que só as páginas viram.
2. **Rodar as 5 categorias de checagem** (abaixo). Anote achados em memória.
3. **Verificação externa opcional**: Se houver claims numéricos específicos (wattagem, dpi, capacidade) e dúvida, use `WebFetch` em `identidade.urlFabricante` pra cruzar. Não navegue em sites aleatórios; priorize fabricante oficial > Amazon ao vivo > nada.
3.5. **Auto-baixar imagem pendente** (a auditoria FECHA o gap, não só sugere): se `identidade.imagemAmazon` está preenchido **e** `docs/biblias-v2/<ASIN>.webp` NÃO existe, baixe agora antes de escrever o relatório:
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
   - **`b.auditFlags`** = `[{ type, label }]` com os achados report-only que sobram (o que a Etapa 9 conserta não entra). Princípio: chip é para quando a bíblia descreve outro produto ou afirma fato falso deste; ruído de captura do próprio produto não é chip.
     - `'wrong-info'`: (a) o ASIN escrito dentro do `specsAmazon` difere do `asin` da bíblia (único gatilho para esse campo, teste de igualdade e não julgamento de conteúdo); (b) fato falso sobre este produto num campo curado; (c) texto ou dado de produto genuinamente diferente (outra marca ou modelo, não variante-irmã) em qualquer campo.
     - Divergência de atributo entre `specsAmazon` e fabricante com o ASIN conferindo, atributo espúrio de listagem e material de variante-irmã com ASIN certo não acendem chip: registre em `dadosInconsistentes` (Etapa 9).
     - `'off-niche'`: o tipo de produto do bruto contradiz a `categoria`/`subcategoria` da própria bíblia (raro; não é "produto no site errado").
     - `'review'`: frescor que exige re-captura, verificação externa não feita que importa para o review, valor genuinamente incerto, fato de imagem anexada que não está em nenhum campo de texto. Estado com chip próprio (sem opiniões, sem preço, sem texto do fabricante, indisponível) não vira flag.
     - `label` até ~120 caracteres, motivo concreto, sem aspas duplas. Nada qualifica → `b.auditFlags = []`.
   - Write `JSON.stringify(b, null, 2) + '\n'`.
   (Se aplicar fixes na Etapa 9, re-bumpa o `lastModified` lá.)
5. **Commit + push + dispatch VPS pull** (auditorias `-last.md` são tracked no git; timestampadas são gitignored):
   ```bash
   git add docs/biblias-v2/.audits/<ASIN>-last.md
   git commit --only -m "audit(biblia): <ASIN> <identidade.nome curta>" \
     -- docs/biblias-v2/.audits/<ASIN>-last.md
   git push origin main
   bash scripts/painel-vps-pull.sh
   ```
   `painel-vps-pull.sh` propaga pro painel da VPS via Basic Auth (creds em `.env.painel-skills`). Sem isso, Bárbara não vê o audit no painel até alguém puxar manualmente.
6. **Reportar no chat**: 3-5 linhas com total de achados por severidade + caminho do relatório. Não cole o relatório inteiro no chat — só o resumo.

7. **Aplicar os consertos**: backup → Edit → bump `lastModified`, marcando ✅ CORRIGIDO no relatório com o diff `ANTES → DEPOIS`. Re-audite os campos tocados antes de seguir. Achados report-only ficam só no relatório. Sem conserto nenhum, siga para a Etapa 10 (o push leva o carimbo da 4.5).

9. **Aplicar** (backup → Edit cirúrgico):
   - Backup: `cp docs/biblias-v2/<ASIN>.json docs/painel/.painel-backups/$(date +%Y-%m-%d)/<ASIN>-v2-$(date +%H%M%S).json`.
   - Editar os campos curados (óbvios + aprovados) **e o naming em `identidade` (`nome`/`marca`) quando o fix é óbvio** (script que lê o JSON, muta os campos, escreve `JSON.stringify(b, null, 2) + '\n'`). NUNCA tocar nos campos brutos.
   - **Bumpar `b.lastModified = new Date().toISOString()`** (ver invariante — sem isso o push é clobberado). Manter `lastAuthor`.
   - **Dê baixa em cada pendência do passo 1.5**, com o resultado:
     `bun scripts/biblia-pendencias.ts baixa <ASIN> <id> "consertado: ... | improcedente: ... | virou chip de revisão: ..."`.
     O arquivo `docs/biblias-v2/.audits/pendencias-biblia-{owner}.jsonl` vai no commit do passo 9.5.
     A baixa é o que faz as páginas da rede escritas antes do conserto aparecerem em
     `bun scripts/biblia-pendencias.ts reauditar` (cite o comando no relatório final).

9.5. **Reescrever o `-last.md` e recommitar depois do apply** (canon 2026-08-15): o relatório do passo 4 foi escrito ANTES dos consertos; sem este passo o `-last.md` no git (o que o painel exibe) não tem os "✅ CORRIGIDO" nem os diffs aplicados. Regrave os dois arquivos do passo 4 com o estado final e repita o commit do passo 5.
10. **Sync R2 + confirmar (SEMPRE roda)**: `bun scripts/sync-biblias-r2.ts --apply --push`. Roda mesmo em audit read-only — a Etapa 4.5 sempre grava `lastAuditedAt` no JSON, então há sempre algo pra subir. Conferir que a linha do ASIN é `enviado` (local mais novo) e não `recebido` (clobber). Re-rodar o sync: deve dar `0 enviadas, 0 recebidas` (steady-state = local==R2). Reportar o que foi aplicado + status do push.

## As 5 categorias

### 1. Consistência interna

**Duas direções. A primeira sempre esteve aqui; a segunda é a que escapa.**

**BRUTO × BRUTO** — mesmo fato afirmado em blocos diferentes com valores contraditórios:
- `sobreEsteItem` × `doFabricante` × `descricaoProduto` × `specsAmazon` × `conteudoBrutoFornecedor`
- Exemplos: "120Hz" num bloco e "60Hz" noutro; "4.500 páginas" vs "3.000 páginas"; `identidade.modelo` diferente do nome que aparece dentro de `doFabricante`.

**CURADO × BRUTO** — três checagens:

**(a) `fonte` é uma AFIRMAÇÃO DE PROCEDÊNCIA — confira-a.** Cada item de `pontosFortes`/`pontosFracos`
declara de onde veio, e o vocabulário mapeia direto nos brutos:

```
fabricante  →  doFabricante + conteudoBrutoFabricante
specs       →  specsAmazon
bullets     →  sobreEsteItem
opiniões    →  opinioesCompradores
```

**Valor que não está no campo que a `fonte` nomeia é 🔴.** A exceção é o item vindo de verificação
externa (Categoria 2), e aí o registro tem que carregar a URL: sem ela, "fonte: fabricante" num dado
que o fabricante não declara é claim sem lastro com carimbo de lastro, que é pior que claim solto.

⚠️ **NÃO é claim sem lastro: valor DERIVADO do bruto** por conversão de unidade ou arredondamento
("2,7 polegadas (6,9 cm)", "1 g (1000 mg)", "2,92 kg" virando "cerca de 3 kg"). O que a checagem procura é
**métrica diferente** ou número que não sai de nada do campo. No caso que originou a régua, a curadoria dizia
"129,3% de sRGB" e o fabricante declarava "NTSC 85%" — não é conversão de coisa nenhuma. **Calibração:** um
matcher cru marca **214 de 1954** itens conferíveis da rede (10%), e a amostra é dominada por conversão
legítima. Se a sua taxa de achado passar muito disso, você está flagrando derivação, não defeito. ⚠️ **`angulosConversao` não tem `fonte` em item nenhum
(0 de todos)** — lá o cruzamento é manual, e foi justamente onde metade do claim da B0FGDJNXPP morava.

**(b) Registro de inconsistência que descreve conflito EXTINTO.** Um `dadosInconsistentes` afirma "o
campo X informa V" e V não está mais em X. Acontece quando o bruto é **re-capturado depois da
curadoria**: o conserto some do bruto e o registro morto continua lá, fazendo o review a jusante
hedgear contra um fantasma. **Confira cada registro contra o campo que ele nomeia.** Na B0FGDJNXPP
eram 5 de 6.

**(c) Curadoria órfã em geral.** O mesmo evento (bruto trocado) deixa claims curados sem âncora mesmo
onde não há `fonte` pra conferir. Sinal barato de que vale olhar: `avisosAoAgente` mencionando
re-captura, troca de página do fabricante ou variante errada.

Não há detector mecânico confiável para (b) e (c): `lastModified > lastAuditedAt` dispara em lote, `capturedAt` não muda em edição manual e o heurístico de valor ausente erra por unidade. Quem pega é a leitura. O chip "auditar de novo" do painel também não avisa, porque é keyado em `lastFilledAt`.

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
  - `imagemLocal` em `docs/biblias-v2/<ASIN>.webp` (padrão) ou em `sites/{site}/public/images/products/<slug>.webp` (bíblias antigas) está certo; não flague nenhum dos dois.
- `specsAmazon === null && conteudoBrutoFornecedor === null` → agente não tem ficha técnica pra trabalhar.
- `opinioesCompradores === null && sentimentoCompradores.length === 0` → review sem voz de comprador.
- `doFabricanteImagens.length === 0` mas `doFabricante` é longo → provavelmente há imagens de infográfico não cadastradas.
- **🔴 IMAGEM ANEXADA COM CONTEÚDO AUSENTE DA BÍBLIA (canon 2026-07-26).** Se `conteudoBrutoFabricanteImagens` ou `doFabricanteImagens` tiverem **qualquer item, ABRA e leia cada uma** (mesmo procedimento da etapa 2.5 da `biblia-preencher`: `curl` → `sips -Z 1400` → `Read`). Se a imagem traz **dado factual** (tabela nutricional, dose, ficha técnica) que **não aparece em nenhum campo de texto**, é achado 🟡 e vira `auditFlags` tipo `review`.
  - **Pule só se** `imagensVerificadasEm` existe E a lista de imagens não mudou desde então. Qualquer imagem nova → lê tudo.
  - **Conflito entre imagem e `specsAmazon` sem valor único (alérgeno, potência, capacidade, qualquer campo) é achado 🔴, e não se escolhe lado**: traga para decisão humana.
  - ⚠️ **Não confundir com o passo 3.5**, que cuida da FOTO do produto (`imagemAmazon` → `.webp`). Lá a imagem é arquivo a baixar; **aqui é conteúdo a ler**.
- **Recado no lugar do conteúdo.** `conteudoBrutoFabricante` curto (< 200 chars) casando com padrão de bilhete (`/est[áa] na imagem|em anexo|ver anexo|texto na imagem/i`) **não é conteúdo do fabricante** — é a editora avisando que o dado está na imagem. Achado 🟡: a bíblia está sem a voz do fabricante apesar do campo parecer preenchido. O detector do painel já trata isso (`server.ts`, `cbFabEhRecado`).

### 5. Higiene de dado + naming (NÃO voz editorial)

> **Escopo (canonizado 2026-06-14):** a bíblia é fonte de FATO e nunca é renderizada direto; o review/página reescreve tudo e aplica a régua de VOZ no texto final. Então este audit cuida de **dado limpo + naming + relevância de info**, **NÃO** de estilo. **FORA do escopo (é da criação, NÃO flague na bíblia):** travessão, "declarado pelo fabricante"/muleta, superlativo/claim absoluto, concordância PT-BR, jargão/voz corporativa, health-YMYL. Esses são reescritos pelas skills `artigo-review-criar`/`pagina-produto-criar`, que têm régua + auto-check próprios.

Flag SÓ nos campos curados (`sentimentoCompradores`, `angulosConversao`, `pontosFortes`, `pontosFracos`, `dicasAcionaveis`, `dadosInconsistentes`, `observacoesAgente`) — nunca nos brutos:
- **HTML/lixo de marcação**: `<strong>`/`<em>`/qualquer tag em campo curado. Não é estilo, é ruído de preenchimento (curadoria é texto puro; tag literal corrompe). Auto-fixável: strip da tag.
- **Duplicação de texto** (ruído de dado): duplicação contígua `([a-zA-ZÀ-ÿ\s]{8,40})\1` ou termo entre parênteses repetido `([a-zA-ZÀ-ÿ]{5,30}) \(\1\)` (ex: "formigamento (formigamento)"). Auto-fixável: remover a cópia.
- **Naming** (em `identidade.nome`/`identidade.marca`): `nome` vazio/incompleto (só marca sem modelo, ou modelo sem marca); `marca` vazia ou placeholder (`—`); marca duplicada no nome ("Epson Epson L3250"); espaço duplo; caractere invisível (BOM/U+FEFF) no nome/marca; typo óbvio. **Quando o valor certo é derivável dos próprios dados da bíblia (ex.: `marca` vazia e o `nome`/`specsAmazon` dizem "Philco"), CORRIGE DIRETO, sem pedir** (régua Marcelo 2026-06-27). Naming ambíguo (marca real incerta, nome linha-vs-fabricante) fica report-only.
- **Palavra "bíblia"** em campo de output (jargão interno vazado).
- **Specs ambientais nos campos curados**: % plástico reciclado, certificações eco (Energy Star, EPEAT, RoHS, FSC), "HP Planet Partners", neutralidade de carbono. Info irrelevante ao comprador — flag pra remover. Exceção: tema `sustentabilidade` em `angulosConversao` com posicionamento claro.
- **Origem de fabricação nos campos curados**: "fabricado no Brasil", "made in X". Mesmo critério; exceto ângulo `produto-nacional`/logístico explícito.
- **Voz-comprador crua** ("um comprador relata"/"divide opiniões") em campo curado → destilar pra observação analítica. **Fica no escopo** porque é virar opinião em FATO usável (não é polimento de estilo). São DUAS regras independentes — cheque as duas, a segunda é a que mais escapa:
  - ⚠️ **(1) Preserve a cardinalidade epistêmica** (Armadilha 1 da `biblia-preencher`): se a base é 1 review, a observação NÃO pode virar consenso plural. "Um comprador relata dificuldade de montagem" → "há relato de dificuldade de montagem" (mantém o hedge singular), **nunca** "a montagem é difícil" cru (inventa consenso). Destilar a MOLDURA burocrática, não a incerteza.
  - ⚠️ **(2) A moldura sai MESMO com a cardinalidade certa** (canon 2026-07-30). **Sujeito humano + verbo de fala é violação por si só**, não importa quantos relatos sustentam: `compradores relatam/descrevem/citam/destacam/dizem/mencionam/consideram/acham`, `usuários…`, `clientes…`, `quem comprou descreve`. Vale no PLURAL HONESTO: `"Compradores destacam volume alto"` com 3 relatos reais **é violação** — o número está certo, a moldura não. Conserto: análise de frequência ou hedge, preservando o número real → `"Volume alto é o tema mais recorrente"` / `"aparece em três relatos"` / `"há relato de"`.
  - 🎯 **Escopo por campo — as duas regras NÃO cobrem os mesmos campos:** **(1) cardinalidade vale em TODOS os curados**, inclusive `observacoesAgente`/`dadosInconsistentes` (contagem errada é erro de FATO em qualquer campo). **(2) moldura vale só nos que ALIMENTAM o review** (`sentimentoCompradores`, `angulosConversao`, `pontosFortes`, `pontosFracos`, `dicasAcionaveis`) — nos internos a moldura é inofensiva, são recado pro agente e nunca viram texto renderizado. **Não flague moldura em `observacoesAgente`/`dadosInconsistentes`.**
  - ✅ **NÃO flague** (falso-positivo clássico): frequência sem sujeito humano ("qualidade sonora é o tema mais recorrente", "aparece em dois relatos") = a destilação CERTA; `relatos`/`opiniões` como sujeito ("relatos independentes citam X") = o hedge que a régua prescreve; e `pontosFortes[N].fonte = "opiniões, recorrente em 3 relatos"`, que é metadado de procedência e **deve** registrar cardinalidade.
  - **Por que é FATO e não estilo** (a objeção é "o review reescreve mesmo"): a moldura plural **funde claims de contagens diferentes e apaga o número**. Caso real: `"Compradores destacam som honesto e valor justo"` — 1 relato pro primeiro, 2 pro segundo. Fundido, o número some da bíblia e o review a jusante não tem como hedgear certo. É perda factual irreversível — por isso entra aqui, enquanto travessão/superlativo não entram.
- **Voltagem citada sem bivolt explícito** (FATO — wrong-info, canon 2026-06-28; endurecida 2026-06-29): campo curado menciona voltagem ("110V"/"220V"/"127V"/"vendido em versões 110V e 220V"/"bivolt"/"funciona em qualquer tomada"/"sem transformador") MAS o `specsAmazon`, a `descricaoProduto` e o `sobreEsteItem` do ASIN **não** trazem "bivolt" (nem faixa contínua "100-240V"/"110-220V") explícito. A régua nova é **não citar voltagem na curadoria** (muda por ASIN, o comprador escolhe a versão no anúncio) — a ÚNICA exceção é um desses três campos dizer "bivolt"/faixa explícito. **Auto-fixável: REMOVER a menção de voltagem do campo curado** (não trocar por "vendido em versões..." — isso ainda é citar voltagem). O erro raiz é ler copy de potência dual-SKU (`"1800W 110V | 2000W 220V"`, `"110/127V e 220V"`) como bivolt — são SKUs separados. **Aparelho de aquecimento de alta potência é voltagem única por design** (air fryer, ferro, secador, chaleira). Exceção de classe (bivolt comum, citar só se a ficha confirmar): impressora e cooktop a GÁS. Caso real: NA341/Midea/Mondial/WAP (air fryers) afirmados bivolt → propagou pra 4 sites (2026-06-28).

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
- **Sugestão:** <o que fazer — se for auto-fixável num campo curado, é aplicado no passo 7; senão fica report-only>

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


## Exemplo de invocação

Usuário: "audita a bíblia B098YHFT9S"
Ou: "audita a impressora Epson L3250"
Ou: "audita todas as bíblias" → `biblia-auditar-em-massa todas`

Você aceita ASIN direto, nome parcial de produto (fuzzy match pelo `identidade.nome`), ou "todas".

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
