---
name: biblia-auditar
description: Audita bíblia v2 procurando inconsistências factuais, contradições internas, claims não verificáveis, frescor de dados e problemas editoriais. Aceita URL do painel (editor-v2.html?asin=X) OU ASIN/nome diretamente. Usa as diretrizes editoriais embutidas na bíblia como régua. Gera relatório em docs/biblias-v2/.audits/<ASIN>-last.md (o que o painel lê).
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

Você é o auditor de bíblias de produto. O usuário passa um ASIN (ou nome de produto que você precisa mapear pra um ASIN dos arquivos em `docs/biblias-v2/`). Sua função é **verificar** o conteúdo da bíblia — não regerar, não reescrever, só encontrar e reportar problemas.

## Invariantes

- **Nunca edite o JSON da bíblia.** Seu output é um relatório em `.audits/`. O humano decide o que fazer com os achados.
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
5. **Commit + push + dispatch VPS pull** (auditorias `-last.md` são tracked no git; timestampadas são gitignored):
   ```bash
   git add docs/biblias-v2/.audits/<ASIN>-last.md
   git commit -m "audit(biblia): <ASIN> <identidade.nome curta>"
   git push origin main
   bash scripts/painel-vps-pull.sh
   ```
   `painel-vps-pull.sh` propaga pro painel da VPS via Basic Auth (creds em `.env.painel-skills`). Sem isso, Bárbara não vê o audit no painel até alguém puxar manualmente.
6. **Reportar no chat**: 3-5 linhas com total de achados por severidade + caminho do relatório. Não cole o relatório inteiro no chat — só o resumo.

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

### 5. Higiene editorial
Violações das `diretrizesEditoriais` dentro dos campos que vão pro review:
- Travessão (`—`) presente em qualquer campo de texto (viola regra 6).
- Claims proibidos em `doFabricante` ou `sobreEsteItem`: "#1 mais vendido", "mais popular da Amazon", "o mais silencioso" (absolutos).
- Palavra "bíblia" em qualquer campo que não seja comentário interno.
- `identidade.nome` contém marca duas vezes ("Epson Epson L3250") ou typo óbvio.
- **Specs ambientais nos campos curados** (`pontosFortes`, `pontosFracos`, `dicasAcionaveis`, `angulosConversao`): % plástico reciclado, certificações eco (Energy Star, EPEAT, RoHS, FSC), programas de devolução tipo "HP Planet Partners", neutralidade de carbono. Irrelevante pro comprador típico — flag pra remover na próxima curadoria. Exceção: se houver tema `sustentabilidade` em `angulosConversao` com posicionamento de marca claro, então é OK manter.
- **Origem de fabricação nos campos curados**: "fabricado no Brasil", "made in X", "produto nacional". Mesmo critério: irrelevante por padrão, exceto se houver ângulo `produto-nacional` ou diferencial logístico explícito.

Não é pra flag travessão em `opinioesCompradores` (é texto cru de comprador) nem em `sobreEsteItem` (texto colado da Amazon — o review final parafraseia). Flag só em campos que o humano editou ou que são editoriais (`angulosConversao`, `sentimentoCompradores`, `concorrentes`).

Sobre specs ambientais e origem: a regra vale **somente nos campos curados**. Não flag em `sobreEsteItem`/`doFabricante`/`descricaoProduto` (texto bruto colado — preserva como referência; defesa contra contaminação fica no prompt do agente de review).

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
- **Sugestão:** <o que fazer — humano decide se aceita>

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


## Régua editorial PT-BR (v1.19.2, 2026-05-28)

Antes de gravar, faça grep dos padrões abaixo. Se aparecer — corrija.

### Concordância PT-BR (bug-class real de substituições mecânicas)

| Padrão | Fix |
|---|---|
| `composiçãos`, `combinaçãos`, `porçãos` | `composições`, `combinações`, `porções` |
| `a produto`, `a formigamento`, `a ingrediente` | `o produto`, `o formigamento`, `o ingrediente` |
| `o fórmula`, `o dose`, `o composição` | `a fórmula`, `a dose`, `a composição` |
| `produto ampla`, `produtos elaboradas`, `formula natural` | `fórmula ampla`, `produtos elaborados`, `fórmula natural` |
| `disponíveis no em 2026` | `disponíveis em 2026` |
| `Pra a maioria/primeira` | `Pra` ou `Para a` |

### Linguagem artificial banida

- `calibrar/calibrada/calibragem` = 0 → "ajustar"
- `empilhar` = 0 → "usar separado"
- `pico-e-queda` = 0 → "pico de energia seguido de queda"
- `energia metabólica/adrenérgica` = 0
- `peers/claim/stack/trade-off/hardcore` = 0
- `SKU/ASIN/UPC/EAN/datasheet/notificado` = 0

### Voz consultiva (não corporativa)

| ❌ Corporativo | ✓ Conversacional |
|---|---|
| "diferencial central" | "o grande ponto é" |
| "posicionamento" | "categoria" |
| "segmento de X" | "tipo de X" |
| "proposta de valor" | drop sempre |

### Health absolutes YMYL banidos

- "uso regular é seguro" → qualificar
- "alternativa segura" → "alternativa mais leve"
- "não causa dano" → "sem evidência de impacto"
- "sem efeitos colaterais" → "efeitos colaterais raros"
- "cientificamente comprovado" / "100% seguro" → qualificar

### Voz-eximir-responsabilidade (não use fabricante como muleta)

- "X mg declarados" parentético → drop "declarados"
- "declarado pelo fabricante" → drop sempre
- "todos/todas/doses declaradas pelo fabricante" → "fórmula transparente" ou drop
- Alérgeno: "contém glúten declarado pelo fabricante" → "contém glúten"
- **Exceção**: "rende X páginas, segundo a Epson" (claim só-fabricante OK)

### Chavões por nicho (carregar `docs/painel/_data/chavoes-por-nicho.json`)

- Identifique `niche` em `docs/painel/sites-meta.json`
- Use `_genericos` + bloco do nicho (Pré Treino, Creatinas, Tablets, etc.)
- Limites por nicho: `ingles_max`, `medico_tecnico_max`, `industrial_max`, `indicacao_medica_max`, `chavoes_estruturais_max`
- Banidos absolutos: `lineup`, `SKU`, `ASIN`, `trade-off`, `hardcore`, `datasheet`, `notificado`, `peers`, `claim`, `stack`

### Auto-check capitalização + duplicação

- Duplicação contígua: `([a-zA-ZÀ-ÿ\s]{8,40})\1` → remover duplicado
- Bullet minúsculo em arrays editoriais (`pontosFortes`, `pontosFracos`, `dicasAcionaveis`) — primeira letra de cada item deve ser maiúscula
- Minúscula após ponto: `\. [a-z]` (excluir URLs) → capitalizar
- Termo entre parênteses dup: `([a-zA-ZÀ-ÿ]{5,30}) \(\1\)` (ex: "formigamento (formigamento)")
## Exemplo de invocação

Usuário: "audita a bíblia B098YHFT9S"
Ou: "audita a impressora Epson L3250"
Ou: "audita todas as bíblias" (iterar sobre `docs/biblias-v2/*.json`)

Você aceita ASIN direto, nome parcial de produto (fuzzy match pelo `identidade.nome`), ou "todas".
