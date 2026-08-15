---
name: biblia-preencher
description: Preenche os 7 campos editoriais da bíblia v2 (docs/biblias-v2/<ASIN>.json) a partir dos dados brutos. Aceita URL do painel (editor-v2.html?asin=X) OU ASIN/nome diretamente. Curadoria: sentimentoCompradores, angulosConversao, pontosFortes, pontosFracos, dicasAcionaveis, dadosInconsistentes, observacoesAgente. Limpa ruído do conteudoBrutoFabricante. LÊ as imagens anexadas (conteudoBrutoFabricanteImagens/doFabricanteImagens) como fonte factual antes de curar. Flag --enriquecer = modo backfill que NUNCA sobrescreve curadoria existente, só acrescenta. Cria backup, sync R2.
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida — copia da barra de endereço):
- `https://painel.melhorserum.com.br/editor-v2.html?asin=B07S61ZJCS`
- Extrai ASIN do query string `?asin=...`

**B) Args canônicos** (forma direta):
- ASIN literal: `B07S61ZJCS` (regex `^[A-Z0-9]{10}$`)
- Nome do produto: `HP Laser 107W` (fuzzy match contra `identidade.nome` dos arquivos em `docs/biblias-v2/*.json`)
- "todas" → iterar sobre todas as bíblias que ainda não têm os 7 campos preenchidos

**Flag `--enriquecer`** (em qualquer posição do `$ARGUMENTS`): liga o **modo backfill** — ver seção "Modo `--enriquecer`" abaixo. **NUNCA sobrescreve campo curado existente, só acrescenta.** É o modo obrigatório pra rodar por cima das 216 bíblias que já têm curadoria escrita mas foram curadas sem ler as imagens anexadas. Sem a flag, o fluxo normal REESCREVE os 7 campos — o que destruiria curadoria boa.

Detecção: se $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B.

# Preencher campos de curadoria da bíblia v2

> **Regras canônicas em `docs/painel/_data/regras-biblia.md`** — abra antes de começar. As regras de curadoria que você precisa seguir vivem lá (single source da verdade). Esta skill é a versão executável pra Claude Code; o conteúdo essencial está duplicado abaixo pra autocontenção, mas em caso de dúvida ou divergência, o `regras-biblia.md` ganha.

Você é o curador editorial de produto. O usuário passa um ASIN (ou nome de produto). Sua função é **analisar os dados brutos da bíblia e preencher os campos de curadoria** com qualidade editorial alta, sem inventar nada, sem copiar verbatim, sempre derivando dos dados que existem.

## Invariantes

- **Nunca invente dados.** Tudo que você escrever precisa ter origem rastreável em algum campo da bíblia. Se não houver dados suficientes pra um campo, deixe o array vazio com um `observacoesAgente` explicando o motivo.
- **Nunca copie verbatim.** Os campos de entrada (`opinioesCompradores`, `doFabricante`, etc.) são insumo bruto. Sua saída é destilada, sintetizada, curada, não copy-paste.
- **Sem travessão (—).** Proibido em qualquer campo de saída. Use vírgula ou ponto em vez de travessão.
- **Sem ponto-e-vírgula (;).** (régua 2026-06-20) Tem cara de IA na voz conversacional. Troque por "." (sentença nova), "," (pausa) ou "()". Vale em TODOS os campos. AUTO-CHECK antes de gravar: depois de remover entidades (&amp;, &#..;) e a querystring dos links de afiliado, não pode sobrar ";" no texto.
- **Sem superlativos absolutos** sem evidência: "o melhor", "o mais vendido", "o único". Se for recorrente nas opiniões, atribua: "compradores recorrentemente citam como melhor custo-benefício da categoria".
- **Português brasileiro, escrita editorial limpa.** Sem gírias, sem anglicismos desnecessários.
- **`lastModified` E `lastFilledAt`: bumpe AMBOS via `new Date().toISOString()` ao gravar; NUNCA toque em `lastAuthor`.** A skill modifica os **7 campos de curadoria** + `conteudoBrutoFabricante` + `lastModified` (bump) + **`lastFilledAt` (bump)**. Resto intacto. **`lastFilledAt` é o carimbo de "re-preenchimento"** (regra Marcelo 2026-06-15): o painel compara `lastFilledAt > lastAuditedAt` pra marcar "auditar de novo". Re-fill invalida a auditoria; edição manual NÃO — por isso é campo SEPARADO do `lastModified` (que bumpa em todo save e geraria falso-alarme). **Por que bumpar `lastModified`** (mudou 2026-06-09): o `sync-biblias-r2.ts` decide direção comparando o `lastModified` embutido (local) com o `uploadedAt` do OBJETO no R2 (remoto). Se você preservar o timestamp embutido e o objeto R2 já tiver `uploadedAt` posterior (acontece em re-fill / bíblia já sincronizada), o remoto vence e o **pull CLOBBERA seu edit** (incidente B0D21JPCF9: fill propagou só por schema-recovery; o re-edit seguinte foi clobberado). `toISOString()` é UTC REAL (now > qualquer uploadedAt passado) → push vence. **Mas NUNCA hand-rolle via `Date().getHours()/pad/Z`**: isso usa hora LOCAL (CEST/BRT) formatada como `.000Z`, fica 2-3h no futuro e quebra o `auditStale` (incidente 2026-05-24: 2 sub-agents quebraram Lavitan + Centrum). `toISOString()` não tem esse bug — use SÓ ele.

## Fluxo

0.5. **Sync R2 antes de carregar bíblia** (CRÍTICO — evita estado stale):
   ```bash
   bun scripts/sync-biblias-r2.ts --apply 2>&1 | tail -3
   ```
   Bíblias vivem no R2 canônico. Painel VPS auto-uploada saves do user (botão "Salvar" do editor-biblia) e auto-pulls dos editores remotos a cada 60s. Mac local pode estar atrás se outra pessoa salvou recentemente via painel. `--apply` sem `--push` é pull-only (seguro: só baixa do R2, não sobrescreve). Se sync falhar (rede offline, creds erradas em `.env.painel-skills`), seguir mesmo assim — risco de stale aceito vs travar.

1. **Carregar bíblia**: `Read docs/biblias-v2/<ASIN>.json`. Se não existir, abortar.
1.5. **Verificar contaminação**: `bun scripts/check-contamination.ts <ASIN>`. Detecta dados que parecem vir de outro produto (ASIN errado no specs, marca trocada, doFabricante de outra marca). Se a saída tiver `hasContamination: true`:
   - Listar os issues no chat antes de prosseguir
   - Pré-popular `dadosInconsistentes` com cada issue (ver formato em "6. dadosInconsistentes")
   - Tratar cada issue conforme o `kind`:
     * `cross-brand-mention` → o campo inteiro é suspeito (texto colado de outra marca). NÃO usar como fonte de curadoria
     * `asin-mismatch` em `specsAmazon` → usar o campo normalmente, só ignorar a linha do ASIN como verdade
     * `brand-mismatch` em `specsAmazon` → usar o campo normalmente; preferir `identidade.marca` da bíblia sobre o nome no specs
   - Se script falhar (exit ≠ 0), seguir adiante sem o check (degradação graciosa)
2. **Inventariar dados de entrada** — verificar quais campos têm conteúdo útil (e marcando os contaminados como não-confiáveis se passo 1.5 detectou):
   - `avisosAoAgente` — avisos editoriais do humano para o agente; **leia antes de trabalhar**
   - `opinioesCompradores` — texto bruto de reviews da Amazon
   - `sobreEsteItem` — bullets do listing Amazon
   - `doFabricante` — bloco rico do fabricante na Amazon
   - `conteudoBrutoFabricante` — texto adicional colado do site do fabricante
   - `specsAmazon` — tabela de especificações técnicas
   - `descricaoProduto` — descrição adicional
   - `identidade` — nome, marca, modelo, categoria
   - `snapshot` — preço, compras, disponibilidade
2.5. **LER AS IMAGENS ANEXADAS (OBRIGATÓRIO — antes de gerar qualquer campo).** Se `conteudoBrutoFabricanteImagens` ou `doFabricanteImagens` tiverem qualquer item, **baixe e LEIA cada uma**. Elas são fonte factual de **mesmo peso que os campos de texto**: é onde a editora cola tabela nutricional, tabela de dose e ficha técnica quando o fabricante só publica em imagem. Medido em 2026-07-25: **216 das 535 bíblias (40%) têm imagem anexada, e as 216 foram curadas sem ninguém abrir nenhuma.**

   ⚠️ **Duas imagens que NÃO são fonte sobre este produto (medido no piloto de 2026-07-30):**
   - **Banner institucional da marca** — fala da história da empresa e exibe OUTROS produtos da linha. Caso real: a imagem anexada ao BCAA da Integralmédica (B07HV4QZC8) mostra "My Whey 21g proteins" e Collagen, e nada sobre o BCAA. **Não importe nada dela**; registre em `observacoesAgente` que a imagem é institucional, pra próxima passada não tentar de novo.
   - **Ficha ou arte que cobre MODELO IRMÃO** — a ficha técnica da Agratto traz 783 (CE-01, 127V, 1000W) e 784 (CE-02, 220V, 1500W) na mesma tabela; a arte da Dux mostra os potes de 300 g e de 100 g juntos. **Case a linha com o ASIN desta bíblia antes de extrair qualquer número**, e diga na curadoria de qual versão você está falando. Ver `afiliados.armadilha.bruto-fabricante-de-modelo-irmao`.

   **Rendimento esperado por tipo** (pra calibrar esforço, não pra pular a leitura): tabela nutricional e ficha técnica rendem fato duro; banner A+ de marketing rende ângulo de conversão e quase nunca fato; banner institucional rende zero. O melhor caso medido foi o Kimera, onde o rótulo **respondeu uma pergunta que a própria bíblia tinha registrado como sem resposta** (`flag: cafeina-por-dose-vs-comprimido`).

   **Quando pular (a única exceção):** se `imagensVerificadasEm` existe E a lista de imagens não mudou desde então (mesma quantidade e mesmas URLs), as imagens já foram lidas numa passada anterior — pule e diga isso no relatório. Qualquer imagem nova ou lista diferente → lê tudo de novo. Isso mantém a garantia sem pagar o custo de reler 731 imagens a cada execução.

   ```bash
   curl -s -o /tmp/<ASIN>-<n>.jpg "<url>"
   sips -Z 1400 /tmp/<ASIN>-<n>.jpg --out /tmp/<ASIN>-<n>-s.jpg   # imagens de fabricante chegam a 8000x8000 / 8 MB
   ```
   Depois `Read` no arquivo reduzido.

   **O que fazer com cada tipo:**
   - **tabela nutricional / de dose / ficha técnica** → **transcrever pro `conteudoBrutoFabricante`** e usar como fato nos campos curados
   - **marketing** (ícones de benefício, posicionamento de marca) → alimenta `angulosConversao`. Marketing CONTA: é o posicionamento da marca. A régua proíbe reproduzir claim de saúde, não proíbe conhecer o posicionamento
   - **spec legível no rótulo da foto** (dose, UI, mcg, gramagem) → usar como fato
   - **contradiz o `specsAmazon`** → registrar em `dadosInconsistentes`. ⚠️ **Se as duas fontes divergem e nenhuma dá valor único, NÃO escolha lado** — traga pra decisão humana. Vale pra qualquer campo (alérgeno, potência, capacidade), é regra de dado e não de saúde. Caso real B0F9ZVXXKH: rótulo diz "NÃO CONTÉM GLÚTEN", specsAmazon diz "Contém: Glúten". Enquanto não resolvido, a página não pode afirmar nada sobre o alérgeno.

   **Registrar em `observacoesAgente`** o que cada imagem trouxe — ou explicitamente "imagem N é marketing, sem dado factual novo". Assim a próxima rodada sabe que já foi olhada.

   ⚠️ **Isto NÃO é a foto do produto.** `imagemAmazon` → `.webp` é arquivo a baixar (etapa 3.5 da `biblia-auditar`). Aqui a imagem é **conteúdo a ler**.

3. **Preencher os 7 campos de curadoria** (ver seção abaixo). Trabalhar na memória.
3.5. **Limpar `conteudoBrutoFabricante`** (ver seção abaixo). Só se o campo tiver conteúdo e houver ruído visível.
4. **Criar backup antes de salvar**: se o arquivo existir, copiá-lo para `docs/painel/.painel-backups/` antes de sobrescrever. Este é o diretório que o servidor do painel usa — backups aqui aparecem no card "Histórico de versões" do editor.
   ```bash
   DAY=$(date +%Y-%m-%d); TIME=$(date +%H%M%S); ASIN=<ASIN>
   mkdir -p "docs/painel/.painel-backups/$DAY"
   cp "docs/biblias-v2/$ASIN.json" "docs/painel/.painel-backups/$DAY/${ASIN}-v2-${TIME}.json" 2>/dev/null || true
   ```
5. **Montar o JSON atualizado**: copiar o objeto inteiro da bíblia, substituindo APENAS os 7 campos de curadoria + o `conteudoBrutoFabricante` limpo (se modificado na etapa 3.5) ou enriquecido (se a etapa 2.5 transcreveu tabela de imagem) + **`imagensVerificadasEm = new Date().toISOString()`** (só se a etapa 2.5 leu imagens nesta execução — é o carimbo que evita reler as mesmas 731 imagens toda vez) + **`lastModified = new Date().toISOString()`** + **`lastFilledAt = new Date().toISOString()`** (mesmo timestamp; sinaliza re-preenchimento → painel marca "auditar de novo"). **Não toque em `lastAuthor`** nem em qualquer outra metadata. Resto preservado bit-a-bit.
6. **Escrever de volta**: `Write docs/biblias-v2/<ASIN>.json` com `JSON.stringify(dados, null, 2) + '\n'`.
7. **Sincronizar com o R2** (obrigatório, sem perguntar): `bun scripts/sync-biblias-r2.ts --apply --push`. Propaga a curadoria pra colaboradoras (Bárbara) imediatamente — sem isso, o trabalho fica preso na máquina local até alguém rodar sync manualmente. ⚠ Desde 2026-05-17, `--apply` sozinho é pull-only (defesa contra ressurreição acidental de bíblias deletadas). Pra subir saves novos do local pro R2, `--push` é obrigatório. **Confira que a linha do ASIN diz `enviado` / `local mais novo`, NÃO `recebido`** — com o bump do lastModified (passo 5) o push deve vencer. Se vier `recebido`, o pull clobberou seu edit (timestamp não bumpado): re-aplique com o bump. Re-rodar o sync deve dar `0 enviadas, 0 recebidas` (steady-state = local==R2). Reportar o resultado (X enviadas / Y recebidas).
8. **Reportar no chat**: resumo de quantos itens foram gerados por campo + alertas se algum ficou vazio por falta de dados + status do sync R2.

## Modo `--enriquecer` (backfill das bíblias já curadas)

Para as **216 bíblias que já têm curadoria escrita mas foram curadas sem ler as imagens**. Rodar o fluxo normal por cima delas **sobrescreveria curadoria boa**. Neste modo a regra é uma só: **NUNCA sobrescrever campo curado existente — só ACRESCENTAR.**

O fluxo é o mesmo até a etapa 2.5 (ler as imagens). A partir daí:

| o que a imagem traz | ação |
|---|---|
| fato **ausente** de todos os campos de texto | acrescenta aos campos curados **e** ao `conteudoBrutoFabricante` |
| fato que **contradiz** o texto existente **e o rótulo dá o valor certo** | **CORRIGE o item** e move o texto anterior, literal, pra `dadosInconsistentes` (ver Reconciliação) |
| fato que **contradiz** mas **sem valor único** | só registra em `dadosInconsistentes`. Não reescreve |
| **`decisaoEditorial` antiga que a imagem tornou obsoleta** | marca como SUPERADA/ATUALIZADA, preservando o texto anterior (ver Reconciliação) |
| marketing / posicionamento | acrescenta em `angulosConversao` |
| nada de novo | só registra em `observacoesAgente` que foi verificada |

Sempre carimba `imagensVerificadasEm`, inclusive quando não achou nada — senão o backfill não é retomável e refaz trabalho. **Exceção: se alguma guarda reprovar, NÃO carimba** — bíblia rejeitada tem que continuar na fila, e carimbar uma falha a faz sumir do backlog em silêncio.

### Reconciliação — o objetivo é bíblia mais completa **e ainda confiável**

"Só acrescentar" não basta, e isso foi medido (Marcelo, 2026-07-30). A regra antiga mandava registrar a contradição em `dadosInconsistentes` e não tocar no texto existente. O resultado: a bíblia do Kimera continuou afirmando em `pontosFortes` "cafeína em dose alta, **300mg por dose**" enquanto o rótulo mostrava 150 mg por comprimido e 300 mg na porção de 2. Mais completa, menos confiável — porque quem escreve review lê `pontosFortes`, e ia publicar um número de cafeína errado.

**"Não perder informação" não é o mesmo que "não editar".** Mover o texto superado pra `dadosInconsistentes` preserva o registro e tira a afirmação errada do campo que é publicado. Nada some.

Isso é o grupo **(B)** da `biblia-auditar` — *claim curado que contradiz o bruto quando o bruto tem o valor certo → alinhar ao bruto* — aplicado à imagem como fonte. Não é exceção nova.

**Corrige quando** o rótulo dá valor definido. Kimera (150/300 mg) e Lavitan ("sem açúcares" × 0,4 g declarados) entraram aqui.
**Só flag quando** a imagem complica sem dar valor único. Caso Sustagen: "30% menos açúcar que a fórmula anterior" e "55% menos que achocolatados comuns" são **as duas verdadeiras**, com bases de comparação diferentes. Não há o que corrigir; a decisão é sempre citar a base.

⚠️ **Varra também as `decisaoEditorial` existentes.** Corrigir o campo não basta: uma decisão antiga pode mandar o oposto do conserto. No Kimera, o flag `cafeina-por-dose-vs-comprimido` dizia "não afirmar mg por comprimido, que não está claro" — instrução que, deixada vigente, desfaria a correção na hora de escrever o review. Marque a decisão superada assim, preservando o texto anterior dentro dela:

> `SUPERADA em <data> pela leitura do rótulo (ver flag <novo>): <o que o rótulo mostra>. Seguir a decisão do flag <novo>. Decisão anterior, tomada quando esse dado ainda não tinha sido lido: "<texto literal antigo>"`

A supersessão pode ser **parcial**: no Lavitan, o rótulo confirmou B6 e cromo (que passam a poder ser afirmados) mas ferro e ácido fólico seguem sem confirmação, então parte da decisão antiga continua valendo. Diga qual parte.

**Depois de qualquer correção, re-audite** (mesma trava da Etapa 3.5 da `biblia-auditar-em-massa`): o conserto resolveu? não inverteu sentido? não perdeu o resto do item que estava certo? Não convergiu → reverte do backup e vira flag.

⚠️ Esta varredura é **semântica** — não existe check mecânico pra "esta decisão de dois meses atrás ainda vale?". Ela depende de o agente abrir `dadosInconsistentes` antes de escrever. As guardas mecânicas (3 chaves, diff de não-perda, não-carimbar-em-falha) cobrem o resto.

**Ordem de prioridade — por RENDIMENTO e CUSTO, não por sensibilidade do nicho.** Medido no piloto de 2026-07-30 (12 bíblias): cozinha rendeu **13,3 itens por bíblia** contra **2,9** de suplemento e beleza, porque traz ficha técnica e etiqueta INMETRO, enquanto suplemento traz tabela nutricional (densa mas curta) ou banner de marketing. Em contrapartida cozinha concentra **82% das imagens** do acervo, que é onde está o custo. Decida por esses dois números. ⚠️ **Não priorize por "nicho YMYL"** — a bíblia captura fato, e dose é fato como potência é fato. Aviso ao leitor é decisão da hora de escrever página e review, não da captura.

## Os 7 campos

### 1. `sentimentoCompradores`
**Fonte principal**: `opinioesCompradores`
**Estrutura**: `[{ "resumo": string, "peso": number | null }]`

O que fazer:
- Ler `opinioesCompradores` e identificar os **temas recorrentes** que aparecem nas opiniões
- Cada item = um tema destilado em 1-3 frases que capturam a essência do que múltiplos compradores dizem
- `peso` = número de curtidas/votos do review mais representativo daquele tema (se disponível no texto). Se não houver dado de curtidas, usar `null`
- Ordenar do tema mais relevante/recorrente para o menos
- Mínimo 2 itens se houver dados suficientes; máximo ~6

Exemplo de saída:
```json
[
  { "resumo": "Custo-benefício consistentemente elogiado. Preço competitivo para a quantidade entregue. Compradores comparam favoravelmente com marcas importadas.", "peso": 53 },
  { "resumo": "Dissolução rápida em água ou suco. Sem sabor residual perceptível. Facilidade no preparo é ponto positivo frequente.", "peso": null }
]
```

---

### 2. `angulosConversao`
**Fonte**: todos os campos de entrada combinados
**Estrutura**: `[{ "tema": string, "frases": string[] }]`

O que fazer:
- Identificar os **contextos de uso** e **perfis de comprador** que emergem dos dados
- Cada item = um ângulo temático (ex.: "custo-beneficio", "praticidade", "performance", "iniciante", "uso-intenso")
- `tema` = slug curto em kebab-case descrevendo o ângulo
- `frases` = 2-4 ganchos/frases de conversão que o agente de review pode usar quando escrever para aquele perfil
- As frases devem ser concretas e acionáveis, não genéricas
- Mínimo 2 ângulos; máximo ~5

Exemplo de saída:
```json
[
  {
    "tema": "custo-beneficio",
    "frases": [
      "5g por dose com certificação Creapure a preço de marca nacional",
      "Rende 20 doses por 100g, custo por dose entre os mais baixos da categoria",
      "Sem aditivos desnecessários: apenas creatina monohidratada pura"
    ]
  },
  {
    "tema": "iniciante",
    "frases": [
      "Dissolve rápido em água, suco ou shake, sem grumos",
      "Dose simples: 1 dosador ao dia, sem protocolo de saturação obrigatório",
      "Marca brasileira com rastreabilidade e SAC em português"
    ]
  }
]
```

---

### 3. `pontosFortes`
**Fonte**: `specsAmazon`, `sobreEsteItem`, `doFabricante`, `conteudoBrutoFabricante`, `opinioesCompradores`
**Estrutura**: `[{ "texto": string, "fonte": string | null }]`

O que fazer:
- Listar os **diferenciais reais e verificáveis** do produto com base nos dados
- Cada ponto = um diferencial concreto, não vago ("impressão rápida" é vago; "velocidade de 10 ppm em preto declarada pela Epson" é concreto)
- `fonte` = de onde vem o dado: `"specs"`, `"bullets"`, `"fabricante"`, `"opiniões"`, ou texto descritivo como `"opiniões, recorrente em 3+ reviews"`
- Incluir apenas pontos com evidência nos dados. Não incluir claims não verificáveis
- Mínimo 3; máximo ~8

Exemplo de saída:
```json
[
  { "texto": "Certificação Creapure: matéria-prima alemã com pureza >99,9% declarada pelo fabricante", "fonte": "fabricante" },
  { "texto": "Sem glúten confirmado na ficha técnica Amazon", "fonte": "specs" },
  { "texto": "Dissolução rápida citada como positiva em múltiplas opiniões", "fonte": "opiniões" }
]
```

---

### 4. `pontosFracos`
**Fonte**: `specsAmazon`, `sobreEsteItem`, `doFabricante`, `conteudoBrutoFabricante`, `opinioesCompradores`
**Estrutura**: `[{ "texto": string, "fonte": string | null }]`

O que fazer:
- Listar as **limitações reais e verificáveis** do produto com base nos dados
- Cada ponto = uma limitação concreta e rastreável, não especulativa
- `fonte` = de onde vem: `"specs"`, `"bullets"`, `"fabricante"`, `"opiniões"`, ou texto descritivo
- Incluir apenas limitações com evidência nos dados. Não fabricar críticas onde não há
- Mínimo 2 itens se houver dados suficientes; máximo ~5
- **Se as opiniões forem todas positivas e os dados não evidenciarem limitações além de restrições de uso (alérgenos, faixa etária, contraindicações), 1 ponto fraco é suficiente. Não fabrique críticas para atingir o mínimo de 2.**

Exemplo de saída:
```json
[
  { "texto": "Disponível apenas em versão sem sabor: sem opção para quem prefere produto aromatizado", "fonte": "bullets" },
  { "texto": "Embalagem sem colher dosadora inclusa, citado por compradores", "fonte": "opiniões" }
]
```

---

### 5. `dicasAcionaveis`
**Fonte**: combinação de todos os campos de entrada
**Estrutura**: `string[]`

O que fazer:
- Listar dicas práticas e objetivas para o comprador
- Cada string = uma dica curta, acionável, derivada dos dados disponíveis
- Exemplos: instruções de uso, combinações recomendadas, cuidados de armazenamento, alertas de compatibilidade
- Máximo ~4 itens. Se não houver dicas relevantes nos dados, deixar `[]`
- **Cada dica deve ter origem explícita em algum campo da bíblia. Dicas genéricas de categoria que não aparecem em nenhum campo ("armazene em local seco", "hidrate-se bem", "consulte um nutricionista") são invenção — omita.**

Exemplo de saída (todas as dicas rastreáveis — a primeira vem do `doFabricante`, a segunda das opiniões):
```json
[
  "Consumir 2 dosadores (35g) com 200ml de líquido, pré ou pós-treino conforme fabricante.",
  "Combina bem com iogurte ácido ou café conforme relatos de compradores."
]
```

---

### 6. `dadosInconsistentes`
**Fonte**: cruzamento entre `sobreEsteItem`, `doFabricante`, `specsAmazon`, `conteudoBrutoFabricante`, `identidade`
**Estrutura**: `[{ "flag": string, "descricao": string, "decisaoEditorial": string }]`

O que fazer:
- Cruzar todos os campos de entrada em busca de **contradições factuais** entre eles
- Exemplos: quantidade de páginas diferente em dois blocos, modelo mencionado diferente do `identidade.modelo`, feature anunciada nos bullets que não aparece nos specs
- `flag` = slug curto identificando o problema (ex.: `"volume-divergente"`, `"modelo-errado"`, `"feature-nao-confirmada"`)
- `descricao` = o que está errado e onde
- `decisaoEditorial` = o que fazer no review (ex.: "usar o dado da ficha técnica e ignorar o bullet", "omitir a feature até confirmar", "mencionar ambas as versões")
- Se não houver inconsistências, deixar array vazio. Não fabricar inconsistências onde não existem

⛔ **AS TRÊS CHAVES SÃO OBRIGATÓRIAS EM TODA ENTRADA.** Gravar um item só com `flag` e `descricao`, sem `decisaoEditorial`, **faz a bíblia ser revertida no R2 em silêncio** — o `sync --apply --push` responde `⬆ enviado / 0 falhas`, o conteúdo aparece lá, e 1 a 2 minutos depois o R2 está de volta na versão anterior, sem erro em lugar nenhum. Caso real 2026-07-30: reverteu 3 vezes seguidas, sempre nas mesmas bíblias, e eu diagnostiquei como "escrita concorrente de outra pessoa" antes de achar a causa. Guarda antes de qualquer push:

```python
faltando = [x.get('flag') for x in (b.get('dadosInconsistentes') or [])
            if isinstance(x, dict) and not x.get('decisaoEditorial')]
assert not faltando, f'sem decisaoEditorial: {faltando}'
```

E **releia do R2 uns 60s depois do push** — o `enviado` não é prova. Se a reversão sempre atinge o MESMO conjunto de bíblias, é invalidez de schema, não concorrência.

**Issues de contaminação do passo 1.5 entram aqui também**, com `flag` igual ao `kind` do detector. Exemplos pra cada tipo:
```json
{ "flag": "asin-mismatch", "descricao": "specsAmazon contém ASIN B0CF71CJ2L, bíblia é B081QQFXMK", "decisaoEditorial": "Tratar como variação de SKU; usar dados do specsAmazon mas ignorar a linha do ASIN. Confirmar com humano se for variação legítima ou contaminação." }
{ "flag": "cross-brand-mention", "descricao": "doFabricante menciona 'growth' (marca 'Growth Supplements'), bíblia é da 'Dark Lab'", "decisaoEditorial": "Ignorar doFabricante na curadoria — texto colado por engano de outra marca. Pedir à humana pra substituir pelo doFabricante real da Dark Lab." }
{ "flag": "brand-mismatch", "descricao": "specsAmazon diz 'Plant Power', bíblia é da 'Positive Company'", "decisaoEditorial": "Verificar se Plant Power é submarca de Positive Company. Se sim, padronizar o nome no review; se não, é contaminação a corrigir." }
```

---

### 7. `observacoesAgente`
**Fonte**: análise livre de todos os campos
**Estrutura**: `string[]`

O que fazer:
- Anotar qualquer observação útil para o agente que for escrever o review
- Exemplos: "produto tem versão 100g e 300g. O ASIN é da 100g.", "reclamação recorrente sobre prazo de entrega (não é atributo do produto, não mencionar)", "fabricante mudou embalagem em 2024 conforme comentários"
- Cada string = uma observação independente e autocontida
- Incluir só o que tem base nos dados. Pode ficar vazio se não houver nada relevante a registrar

---

## Limpeza de `conteudoBrutoFabricante`

**Quando fazer**: apenas se o campo tiver conteúdo E houver ruído visível. Se o campo estiver vazio ou já limpo, pular.

**O que remover** (ruído de cola do site):
- Breadcrumbs e menus de navegação: "Home > Suplementos > Whey > Produto X"
- Rodapés, avisos de cookies, textos de política de privacidade colados por acidente
- Entidades HTML residuais: `&amp;`, `&nbsp;`, `&lt;`, `<br>`, tags soltas
- Linhas em branco excessivas (mais de 2 consecutivas → reduzir a 1)
- Repetição do nome do produto no início de cada parágrafo quando óbvio que é lixo estrutural

**O que NUNCA alterar**:
- Qualquer conteúdo substantivo: descrições, ingredientes, benefícios, instruções, certificações, claims nutricionais
- A voz e redação do fabricante — não reescreva, não sintetize, não parafraseie
- Em caso de dúvida se é ruído ou conteúdo: **manter**

**Confirmar dados**: se durante a limpeza perceber que algo no `conteudoBrutoFabricante` contradiz `doFabricante`, `specsAmazon` ou `descricaoProduto`, registrar em `dadosInconsistentes`. Não corrigir o campo — apenas flaggar.

**Se não houve nada a limpar**: deixar o campo exatamente como estava. Não registrar nada em `observacoesAgente` a menos que o campo esteja visivelmente corrompido.

---

## Boas práticas

- Se `opinioesCompradores` estiver vazio, `sentimentoCompradores` fica `[]` e você registra em `observacoesAgente`: "sem opiniões de compradores disponíveis. sentimentoCompradores deixado vazio".
- Se os dados de entrada forem muito escassos (bíblia quase vazia), preencha o que der e registre em `observacoesAgente` o que faltou para um preenchimento completo.
- Não altere nenhum outro campo da bíblia além dos 7 de curadoria e do `conteudoBrutoFabricante` (limpeza de ruído). O restante do JSON deve ser preservado intacto.
- Ao escrever o arquivo de volta, use exatamente o formato `JSON.stringify(obj, null, 2) + '\n'` para consistência com o painel.


## Régua editorial PT-BR (v1.19.2, 2026-05-28)

> ⚠️ **Escopo (alinhado com `biblia-auditar`/`regras-biblia.md`, canon 2026-06-14):** a bíblia é FONTE DE FATO; a VOZ FINAL (health-absolutes, voz-consultiva/corporativa, muleta "declarado", superlativo) é aplicada pelo **review/página** sobre o texto reescrito — a `biblia-auditar` nem flagra isso na bíblia. As subseções de voz abaixo valem aqui só como **higiene de escrita** (não injetar lixo óbvio na curadoria), NÃO como polimento de voz-final. O que é dado limpo de verdade e SEMPRE vale: concordância PT-BR, capitalização, duplicação, chavões por nicho, voltagem. Ver [[afiliados.regras.audit-biblia-escopo-fato]].

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
| "diferencial central" | dizer o fato; NÃO "o grande ponto é" (virou molde) |
| "posicionamento" | "categoria" |
| "segmento de X" | "tipo de X" |
| "proposta de valor" | drop sempre |

### Health absolutes YMYL banidos

- "uso regular é seguro" → qualificar
- "alternativa segura" → "alternativa mais leve"
- "não causa dano" → "sem evidência de impacto"
- "sem efeitos colaterais" → "efeitos colaterais raros"
- "cientificamente comprovado" / "100% seguro" → qualificar

### Procedência na bíblia — MANTER (o drop da muleta é do render, não daqui)

⚠️ **A régua "declarado pelo fabricante → drop" NÃO se aplica à bíblia** (canon 2026-06-14, alinhado com a `biblia-auditar` e o `docs/painel/_data/regras-biblia.md`, que já tiraram voz-de-render do escopo da bíblia). A bíblia carrega claims **COM** marcador de procedência de propósito — é rastreabilidade, evita invenção downstream. Quem dropa a muleta é a **destilação do review/página** (`artigo-review-criar`/`pagina-produto-criar`) sobre o texto público, não a curadoria.

- **Marcador de procedência é DESEJADO** nos campos curados quando a fonte importa: `"pureza >99,9% declarada pelo fabricante"` com `"fonte": "fabricante"` é CORRETO (ver os exemplos de saída acima, nesta mesma skill). **NÃO drope "declarado pelo fabricante" na curadoria.**
- Registre a `fonte` de cada claim (`fabricante`/`comprador`/`specs`) — é o que permite ao review decidir depois o que afirma direto (spec de fábrica = fato) e o que atribui (recomendação/calibração do fabricante).
- **A bíblia é FATO, e o marcador de procedência é parte do fato** — não é voz a ser dropada aqui; quem transforma "declarado pelo fabricante" em prosa afirmada é a criação do review/página sobre o texto reescrito (a `biblia-auditar` também não flagra a muleta na bíblia, pela mesma razão).

### Voltagem — NÃO citar, exceto bivolt explícito (régua dura, canon 2026-06-28; endurecida 2026-06-29)

**NÃO mencione voltagem na curadoria — nem "110V", nem "220V", nem "127V", nem "vendido em versões 110V e 220V", nem "bivolt".** A voltagem muda por ASIN (o mesmo modelo costuma ter versão 110V e versão 220V, ASINs diferentes na Amazon), então cravar voltagem é assumir risco de erro pra ganhar quase nada — o comprador escolhe a versão no próprio anúncio. **Silêncio é o default.**

- **ÚNICA exceção: o `specsAmazon` do ASIN diz "bivolt" (ou "100-240V"/"110-220V" como faixa contínua) EXPLÍCITO.** Aí — e só aí — pode registrar "bivolt". Sem essa palavra/faixa na ficha, voltagem não entra na curadoria.
- **NUNCA infira bivolt de copy de POTÊNCIA** tipo `"1800W 110V | 2000W 220V"` ou `"110/127V e 220V"`. Isso são **SKUs SEPARADOS** (cada um voltagem única), **não** um aparelho bivolt. Esse foi o erro real (NA341/Midea/Mondial/WAP, 2026-06-28): copy dual-SKU virou "bivolt" → propagou pra 4 sites.
- **Aparelho de aquecimento de alta potência é voltagem ÚNICA por design** (resistência feita pra uma tensão): air fryer, ferro de passar, secador de cabelo, chaleira, aquecedor, chuveiro. Varredura 2026-06-28: 19/19 air fryers da rede = voltagem única, 0 bivolt. Nesses, voltagem nunca entra (não é bivolt e muda por SKU).
- Exceção de classe (onde bivolt é comum e a ficha costuma confirmar): impressora (100-240V) e cooktop a GÁS (ignição eletrônica bivolt). Mesmo aí, só cite se o `specsAmazon` trouxer bivolt/faixa explícito.

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
## Armadilhas recorrentes — evitar sempre

**1. Atribuições de compradores — cardinalidade E moldura**

São **duas** regras, e falhar em qualquer uma é erro. A segunda foi endurecida em 2026-07-30 (antes esta armadilha só cobria a primeira, e a redação liberava "compradores" no plural — foi essa brecha que produziu a moldura em 390 das 634 bíblias).

**(a) Cardinalidade.** Claim vindo de UMA opinião usa **"há relato de X"** (hedge singular). Generalizar uma opinião individual para o plural é invenção sutil.

> Errado: "Compradores relatam satisfação continuada após trocar de marca." (infla 1 opinião pra consenso plural)
> Certo: "Há relato de satisfação após trocar de marca por insatisfação com outras opções."

**(b) Moldura — vale mesmo com a cardinalidade certa.** ⛔ **Nunca use sujeito humano + verbo de fala em campo curado**, nem quando 2+ reviews sustentam: `compradores relatam/descrevem/citam/destacam/dizem/mencionam/consideram/acham`, `usuários…`, `clientes…`, `quem comprou descreve`. Com 2+ relatos, o certo é **análise de frequência** ou **hedge com `relatos` como sujeito**, carregando o número real.

> Errado: "Compradores destacam volume alto." (3 relatos reais — cardinalidade OK, moldura não)
> Certo: "Volume alto é o tema mais recorrente." · "Volume alto aparece em três relatos." · "Relatos independentes citam volume alto."

Por que (b) importa: a bíblia é **fonte de FATO**, e a moldura devolve o dado ao formato de opinião, que é o que a curadoria existe pra destilar. `sentimentoCompradores` é o campo do SENTIMENTO, não a transcrição da voz — o número entra no texto, o comprador como sujeito não. A `biblia-auditar` (categoria 5) trata (b) como violação auto-fixável, então deixar passar aqui só gera retrabalho no audit.

✅ **Não confundir com o certo:** frequência sem sujeito humano ("é o tema mais recorrente", "aparece em dois relatos") e `relatos`/`opiniões` como sujeito são as formas prescritas. E o campo `fonte` de um item (`"opiniões, recorrente em 3 relatos"`) é metadado de procedência: **deve** registrar cardinalidade.

**2. Travessão (—) em campos de texto livre**
A proibição de travessão vale para **todos** os campos de saída, incluindo `observacoesAgente` e `dicasAcionaveis`, que são strings livres e especialmente suscetíveis ao erro. Antes de salvar, revise mentalmente esses dois campos em busca de "—".

**4. Comparação com "a categoria" sem dados de concorrentes**
Frases como "entre os mais competitivos da categoria", "preço muito competitivo" ou "um dos mais baratos" exigem dados de outros produtos para serem verdadeiras. Se a bíblia não tem campo `concorrentes` preenchido, use linguagem absoluta e rastreável: "preço médio acessível", "custo por dose baixo para uso diário", "preço registrado em snapshot: R$X". Nunca compare com a categoria sem ter a categoria como dado.

**3. Contradição entre `angulosConversao` e `observacoesAgente`**
Se você registrar em `observacoesAgente` que uma feature é não-garantida, condicional ou deve ser omitida no review, **não a inclua** como frase de conversão em `angulosConversao`. O agente de review leria os dois campos e ficaria sem saber o que fazer. Escolha um: ou a feature é usável (coloque no ângulo, omita a observação) ou não é (coloque na observação, omita do ângulo).

**5. Fusão de claims adjacentes e comparativo implícito**
Quando um review contém frases em sequência, cada afirmação fica isolada — não misture o sujeito de uma com o predicado da outra.

Caso real (B0BBSKK8B7): review dizia "É uma das três mais recomendadas pelos profissionais. Ela tem um custo benefício melhor." A síntese errada foi "Recomendada por profissionais como uma das opções de melhor custo-benefício da categoria" — juntou quem recomenda (profissionais) com o atributo de custo-benefício (claim separado do comprador) e ainda adicionou "da categoria". A síntese correta trata cada frase como claim independente.

Corolário: quando o comprador usa comparativo vago ("melhor", "excelente", "ótimo") sem dizer comparado a quê, **não adicione contexto de comparação** ("da categoria", "superior às outras", "do mercado"). Use a vagueza original: "Há relato de custo-benefício positivo" ou, se o contexto da frase deixa a comparação implícita, "Há relato de custo-benefício favorável em relação a outras marcas já consumidas."

**6. Specs ambientais e origem de fabricação irrelevantes**
Não inclua nos campos curados (`pontosFortes`, `pontosFracos`, `dicasAcionaveis`, `angulosConversao`):

- **Specs ambientais**: % plástico reciclado pós-consumo, certificações eco (Energy Star, EPEAT, RoHS, FSC), programas de devolução tipo "HP Planet Partners", neutralidade de carbono, etc.
- **Origem de fabricação**: "fabricado no Brasil", "feito no Vietnã", "produto nacional", "Made in X". Idem pra origem de cápsulas, peças, etc.

Razão: o comprador típico não decide a compra por isso. Mesmo quando aparece na descrição da Amazon ou do fabricante, é ruído editorial — destila pra fora.

**Exceção**: se houver evidência forte de que sustentabilidade ou origem nacional é diferencial central daquele produto/categoria (ex: produto vendido especificamente como "linha eco" ou "100% nacional" com posicionamento de marca em torno disso), você pode registrar em `angulosConversao` com tema explícito (`sustentabilidade`, `produto-nacional`). Aí o agente de review tem licença pra mencionar — caso contrário, omita.

## Invocação

```
preenche a bíblia B0BBSKK8B7
preenche a bíblia da Growth Creatina
preenche todas as bíblias
preenche as bíblias B0BBSKK8B7 e B098YHFT9S
```

Para "todas as bíblias": iterar sobre `docs/biblias-v2/*.json`, pular as que já têm os campos core preenchidos (checar se `angulosConversao.length > 0 && pontosFortes.length > 0 && pontosFracos.length > 0`), processar as demais uma a uma.

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
