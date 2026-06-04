---
name: biblia-preencher
description: Preenche os 7 campos editoriais da bíblia v2 (docs/biblias-v2/<ASIN>.json) a partir dos dados brutos. Aceita URL do painel (editor-v2.html?asin=X) OU ASIN/nome diretamente. Curadoria: sentimentoCompradores, angulosConversao, pontosFortes, pontosFracos, dicasAcionaveis, dadosInconsistentes, observacoesAgente. Limpa ruído do conteudoBrutoFabricante. Cria backup, sync R2.
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

Detecção: se $ARGUMENTS começa com `https://` → caminho A. Senão → caminho B.

# Preencher campos de curadoria da bíblia v2

> **Regras canônicas em `docs/painel/_data/regras-biblia.md`** — abra antes de começar. As regras de curadoria que você precisa seguir vivem lá (single source da verdade). Esta skill é a versão executável pra Claude Code; o conteúdo essencial está duplicado abaixo pra autocontenção, mas em caso de dúvida ou divergência, o `regras-biblia.md` ganha.

Você é o curador editorial de produto. O usuário passa um ASIN (ou nome de produto). Sua função é **analisar os dados brutos da bíblia e preencher os campos de curadoria** com qualidade editorial alta, sem inventar nada, sem copiar verbatim, sempre derivando dos dados que existem.

## Invariantes

- **Nunca invente dados.** Tudo que você escrever precisa ter origem rastreável em algum campo da bíblia. Se não houver dados suficientes pra um campo, deixe o array vazio com um `observacoesAgente` explicando o motivo.
- **Nunca copie verbatim.** Os campos de entrada (`opinioesCompradores`, `doFabricante`, etc.) são insumo bruto. Sua saída é destilada, sintetizada, curada, não copy-paste.
- **Sem travessão (—).** Proibido em qualquer campo de saída. Use vírgula ou ponto em vez de travessão.
- **Sem superlativos absolutos** sem evidência: "o melhor", "o mais vendido", "o único". Se for recorrente nas opiniões, atribua: "compradores recorrentemente citam como melhor custo-benefício da categoria".
- **Português brasileiro, escrita editorial limpa.** Sem gírias, sem anglicismos desnecessários.
- **NUNCA mexa em `lastModified` ou `lastAuthor`.** Esses campos são metadata de save gerenciada pelo painel (UI) e pelo sync R2 — não são estado editorial. A skill só modifica os **7 campos de curadoria** + `conteudoBrutoFabricante`. Resto do objeto fica intacto. Mesmo que você sinta tentação de "atualizar o timestamp" porque você acabou de editar, NÃO faça — qualquer string que você gerar via `Date().getHours()/pad/Z` cai num bug de timezone (hora local CEST/BRT do Mac formatada como `.000Z` parece UTC mas é local, fica 2-3h no futuro e o painel marca audit como "desatualizado" mesmo quando audit é mais novo). Caso real 2026-05-24: 2 sub-agents em 23 sucumbiram a essa tentação e quebraram o `auditStale` de Lavitan + Centrum. Preserve os campos.

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
3. **Preencher os 7 campos de curadoria** (ver seção abaixo). Trabalhar na memória.
3.5. **Limpar `conteudoBrutoFabricante`** (ver seção abaixo). Só se o campo tiver conteúdo e houver ruído visível.
4. **Criar backup antes de salvar**: se o arquivo existir, copiá-lo para `docs/painel/.painel-backups/` antes de sobrescrever. Este é o diretório que o servidor do painel usa — backups aqui aparecem no card "Histórico de versões" do editor.
   ```bash
   DAY=$(date +%Y-%m-%d); TIME=$(date +%H%M%S); ASIN=<ASIN>
   mkdir -p "docs/painel/.painel-backups/$DAY"
   cp "docs/biblias-v2/$ASIN.json" "docs/painel/.painel-backups/$DAY/${ASIN}-v2-${TIME}.json" 2>/dev/null || true
   ```
5. **Montar o JSON atualizado**: copiar o objeto inteiro da bíblia, substituindo APENAS os 7 campos de curadoria e o `conteudoBrutoFabricante` limpo (se foi modificado na etapa 3.5). **Não toque em `lastModified`, `lastAuthor`** ou qualquer outra metadata — preservar bit-a-bit. Ver invariante específico acima.
6. **Escrever de volta**: `Write docs/biblias-v2/<ASIN>.json` com `JSON.stringify(dados, null, 2) + '\n'`.
7. **Sincronizar com o R2** (obrigatório, sem perguntar): `bun scripts/sync-biblias-r2.ts --apply --push`. Propaga a curadoria pra colaboradoras (Bárbara) imediatamente — sem isso, o trabalho fica preso na máquina local até alguém rodar sync manualmente. ⚠ Desde 2026-05-17, `--apply` sozinho é pull-only (defesa contra ressurreição acidental de bíblias deletadas). Pra subir saves novos do local pro R2, `--push` é obrigatório. Se o sync detectar que o R2 está mais novo (algum auto-uploader do painel já enviou) e fizer pull "no-op", tudo bem: o conteúdo é o mesmo. Reportar no chat o resultado (X enviadas / Y recebidas).
8. **Reportar no chat**: resumo de quantos itens foram gerados por campo + alertas se algum ficou vazio por falta de dados + status do sync R2.

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
- **Spec de fabricante = fato, afirme direto** (régua v1.21.1): rendimento, economia e velocidade da ficha (ex: "rende até 4.500 páginas") vão SEM "segundo a Epson"/"segundo o fabricante" (atribuir a cada spec vira muleta repetitiva, igual "declarado pelo fabricante"). Atribuição só vale pra recomendação/calibração do fabricante (ex: "a HP recomenda 50 a 100 páginas/mês").

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

**1. Singular → plural em atribuições de compradores**
Quando um claim vem de uma única opinião, escreva "um comprador" ou "um comprador relata". Use "compradores" (plural sem qualificação) **apenas** quando o mesmo tema aparece de forma independente em 2 ou mais reviews. Generalizar uma opinião individual para "compradores" é invenção sutil.

Errado: "Compradores relatam satisfação continuada após trocar de marca."
Certo: "Um comprador relata satisfação após trocar de marca por insatisfação com outras opções."

**2. Travessão (—) em campos de texto livre**
A proibição de travessão vale para **todos** os campos de saída, incluindo `observacoesAgente` e `dicasAcionaveis`, que são strings livres e especialmente suscetíveis ao erro. Antes de salvar, revise mentalmente esses dois campos em busca de "—".

**4. Comparação com "a categoria" sem dados de concorrentes**
Frases como "entre os mais competitivos da categoria", "preço muito competitivo" ou "um dos mais baratos" exigem dados de outros produtos para serem verdadeiras. Se a bíblia não tem campo `concorrentes` preenchido, use linguagem absoluta e rastreável: "preço médio acessível", "custo por dose baixo para uso diário", "preço registrado em snapshot: R$X". Nunca compare com a categoria sem ter a categoria como dado.

**3. Contradição entre `angulosConversao` e `observacoesAgente`**
Se você registrar em `observacoesAgente` que uma feature é não-garantida, condicional ou deve ser omitida no review, **não a inclua** como frase de conversão em `angulosConversao`. O agente de review leria os dois campos e ficaria sem saber o que fazer. Escolha um: ou a feature é usável (coloque no ângulo, omita a observação) ou não é (coloque na observação, omita do ângulo).

**5. Fusão de claims adjacentes e comparativo implícito**
Quando um review contém frases em sequência, cada afirmação fica isolada — não misture o sujeito de uma com o predicado da outra.

Caso real (B0BBSKK8B7): review dizia "É uma das três mais recomendadas pelos profissionais. Ela tem um custo benefício melhor." A síntese errada foi "Recomendada por profissionais como uma das opções de melhor custo-benefício da categoria" — juntou quem recomenda (profissionais) com o atributo de custo-benefício (claim separado do comprador) e ainda adicionou "da categoria". A síntese correta trata cada frase como claim independente.

Corolário: quando o comprador usa comparativo vago ("melhor", "excelente", "ótimo") sem dizer comparado a quê, **não adicione contexto de comparação** ("da categoria", "superior às outras", "do mercado"). Use a vagueza original: "Um comprador avalia o custo-benefício positivamente" ou, se o contexto da frase deixa a comparação implícita, "Um comprador relata custo-benefício favorável em relação a outras marcas que já consumiu."

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
