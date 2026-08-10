---
name: artigo-lineup-montar
description: Escolhe QUAIS produtos entram num artigo comparativo, em que ORDEM e com que PAPEL — e opcionalmente cria o artigo no painel com eles. NÃO escreve conteúdo e NÃO põe badge, porque isso é das skills de review — mas AUDITA o próprio lineup antes de entregar, num sub-agent isolado que confere se toda exclusão tem prova citável no degrau certo (página para desqualificador, bíblia bruta para requisito) e se algum problema reportado some ao desfazer um corte. Só entram produtos que já têm página no site. A PRIMEIRA coisa que roda, antes de abrir qualquer produto, é uma consulta cega a um sub-agent Opus ISOLADO perguntando "como escolher {keyword}" — a resposta vira rubrica pré-registrada, e é contra ela que cada página é julgada. Depois lê a PÁGINA INTEIRA de todos os produtos da categoria (subtitle, shortDescription, pros, cons, specs, fullReview) pra classificar e julgar aderência à keyword, e só abre a bíblia de quem sobreviveu, pra pegar `comprasMesPassado`, marca, disponibilidade e `pontosFracos`. Ordena por venda, resolve gêmeo, sucessão e rebadge cross-marca antes de atribuir papel. Com `--aplicar`, chama os mesmos endpoints do painel (`make-reviews-stub` + `add-products-stub`) e devolve a URL do editor.
---

## Parse de input

- `melhordosom "melhor caixa de som jbl"` → site + keyword do artigo
- `melhordosom "melhor caixa de som jbl" --aplicar` → além de recomendar, cria o artigo no painel
- `melhordosom/melhor-caixa-de-som-jbl` → artigo que JÁ existe (recomenda produtos pra completar)

Detecção: se tem `/` seguido de kebab-case → artigo existente. Senão → keyword nova.

## O que esta skill É (e não é)

**É a etapa ANTES do painel, para artigo que AINDA NÃO EXISTE.** Ela chega no "+ Criar artigo" com o dever de casa feito: quais produtos, em que ordem, por quê.

⚠️ **Artigo que já existe é da `artigo-clonar-em-massa`, não desta skill** (canon Marcelo 2026-08-02). O modo `site/slug-do-artigo` daqui serve pra **completar** um artigo com produtos que faltam, nunca pra re-derivar o lineup de um artigo publicado. Recriar artigo existente é o trabalho da skill de clonar.

⚠️ **As 4 execuções de 2026-08-02 foram todas re-derivações de artigo publicado** (`melhor caixa de som jbl`, `melhor air fryer 12 litros`, `melhor impressora custo benefício`, `melhor impressora tanque de tinta`). Serviram pra calibrar a régua contra um resultado humano conhecido, e foi assim que vários defeitos apareceram — mas **não são o uso pretendido**. Não conclua daqui que comparar-se com o artigo publicado faz parte do fluxo: num artigo novo não há com o que comparar.

**NÃO escreve nada.** Nem review, nem intro, nem guia. Isso é da `artigo-review-criar` e família.

**NÃO põe badge.** O badge é atribuído na criação/auditoria do review, que tem visão do conjunto escrito.

**NÃO decide o que é apertado.** Onde duas opções empatam de verdade, ela **reporta o empate** em vez de arbitrar. Isso é desenho, não limitação: o mesmo princípio vale pro aviso de marca e pro teto de reuso, que informam e não travam.

## Invariantes

- **Só produto com página de produto no site.** É o universo de entrada, não uma preferência. Produto sem página não recebe link interno hub-and-spoke e o guia cai pro `/dp/` da Amazon.
- **Classificar tipo pela tabela `specs` da PÁGINA, nunca por regex no nome.** O campo `Tipo` responde direto. Ver Armadilha 1 — errei duas vezes no mesmo dia e a página tinha a resposta nas duas.
- **Página é fonte principal, bíblia é apoio.** Fato e classificação saem da página; vendas, marca, disponibilidade e `pontosFracos` saem da bíblia, porque a página não tem os três primeiros e **pode perder o quarto**.
- **`comprasMesPassado = 0` ORDENA, não elimina** (corrigido 2026-08-02). Não é "vendeu zero": é "a Amazon não exibe o widget", threshold estimado em **>50/mês** ([[afiliados.semantica.compras-mes-passado-0]]). É **ausência de sinal**, não sinal negativo — e a régua tratava como corte duro na linha seguinte à que citava essa memória. Agora o `0` manda o produto pro **fim da fila**, e quem corta é o teto de tamanho.
- **Todo item do relatório carrega o ASIN**, e nome/preço saem LIDOS do `.mdx`, nunca de memória. Ver Armadilha 4.
- **Não faz deploy, não escreve `.mdx` de review.** Com `--aplicar` ela só chama os endpoints do painel, que são os mesmos dos botões da UI.
- **Terminologia:** "lineup" é jargão técnico interno (o `products[]` do frontmatter). No texto editorial dos `.mdx` a palavra é BANIDA — a `artigo-reviews-auditar` flagra como crítico. Aqui é a régua descrevendo a si mesma, igual nos nomes de critério.

## Pipeline

### Etapa 1 — consulta cega "como escolher {keyword}" (PRIMEIRA COISA)

**Antes de abrir produto nenhum.** Não é ordem de conveniência: se você lê o catálogo primeiro e recebe os critérios depois, os critérios deixam de ser régua e viram racionalização do que você já viu. O valor inteiro desta etapa está em ela ser **pré-registrada**.

A restrição vale pro contexto principal também, não só pro sub-agent. Chegou aqui, ainda não leu `.mdx` de produto nenhum.

**Sub-agent Opus ISOLADO**, sem acesso ao catálogo nem a arquivo nenhum. Pergunta única: **como escolher {keyword}**, pedindo quatro coisas.

1. **Critérios ELIMINATÓRIOS e de QUALIDADE, separados.** Eliminatório tira o produto da conversa (não atende o recorte da keyword). Qualidade é o que faz um ser melhor que outro **entre os que passaram**.
2. **Quais formatos/linhas convivem sob esse rótulo** e como diferenciar na prática. É a pergunta que mais rende quando a keyword tem número (litros, polegadas, ppm), porque o número costuma cobrir coisas fisicamente diferentes.
3. **Perfis de uso** que a lista precisa cobrir pra não ficar incompleta.
4. **Armadilhas do comprador** — o que a categoria esconde e as listas não contam.

A resposta vira **RUBRICA**, registrada no relatório final. É contra ela que a Etapa 3 julga cada página.

⚠️ **Não peça "critérios em ordem de peso".** A pergunta 1 pedia isso até 2026-08-01 e **nenhuma etapa consumia o ranking**: a Etapa 3 usa a rubrica como binário, e na Etapa 5 quem ordena é venda, preço e papel. Pedir peso e ignorá-lo é gastar a consulta com o que não tem destino. O corte eliminatório/qualidade é o que a Etapa 3 sabe usar.

**Onde cada metade é consumida:**

| metade | quem usa | com que autoridade |
|---|---|---|
| eliminatórios | Etapa 2b e Etapa 3 | **apontam o que procurar, não eliminam sozinhos** — quem elimina é a página (ver Etapa 3) |
| qualidade · perfis · armadilhas | relatório da Etapa 7, e insumo pra `artigo-guia-escrever` | informativo |

Os de qualidade **não ordenam o lineup hoje**. Ordenar por eles exige resolver o conflito com os 71% da posição-1-mais-vendida, e isso é medição, não redação.

⚠️ **A rubrica é insumo, nunca autoridade.** Ela é memória de um modelo, sem acesso ao catálogo — acerta o que a categoria tem e erra o recorte do que "deveria" estar na mesma lista. Em 2026-08-02 ela me convenceu a cortar a `PartyBox Ultimate` de um artigo de caixa de som JBL porque "misturar caixa de festa com portátil é o erro mais comum". É juízo editorial sobre estrutura de artigo, e virou critério de admissão nas minhas mãos.

**Não pergunte QUAIS MODELOS.** Medido em 2 execuções: zero decisões aproveitadas e um erro ativo (marcou `JBL Go 4` com confiança ALTA sem saber que a Go 5 existia, e a regra de sucessão teve que desfazer). A LLM envelhece **nome de modelo** e não envelhece **critério de compra** — pergunte só a metade que não envelhece. Se um nome aparecer solto na resposta, trate como ruído, nunca como candidato.

**Voltar limpo é resultado válido.** Check que sempre acha algo é check mal calibrado.

**Aproveitamento duplo:** "Como escolher {keyword}" é o H2 obrigatório que a `artigo-guia-escrever` vai ter que produzir depois. Guarde a rubrica no relatório — ela serve as duas skills.

### Etapa 2 — universo e pré-flight, nesta ordem interna

**2a. Listar (barato).** O universo de entrada é a **lista de páginas de produto do `categorySlug` alvo**, não um filtro sobre bíblias. Só ASIN e nome por enquanto.

Essa direção é obrigatória e foi aprendida errando: na 3ª execução o escopo bíblia-first devolveu **13 de 23** produtos, porque exige adivinhar um filtro de busca. A lista de páginas é conjunto fechado e não depende de palpite.

⚠️ Um universo menor **não parece errado, parece um catálogo pequeno**. Por isso o erro é silencioso e por isso a direção importa.

⚠️ **`categorySlug` VAZIO é o buraco do buraco — cheque SEMPRE.** A regra acima nasceu pra matar o universo silencioso e **tem a mesma falha** quando o site não preencheu categoria. Medido no oguiacompra (2026-08-02):

```
categorySlug = "impressoras"      17 páginas
categorySlug AUSENTE              13 páginas — TODAS impressoras
                                  ──
universo real                     30
```

Filtrar só pelo slug devolveria **17 de 30**, e dois produtos do lineup final (`L4360`, `Smart Tank 581`) vêm justamente do grupo sem categoria. **Depois de listar pelo slug, liste também as páginas com categoria vazia e inspecione cada uma** — é uma varredura barata e é a diferença entre ver o catálogo e ver metade dele.

**2b. Pré-flight (BLOQUEANTE).** Uma pergunta só: **existe bíblia que a rubrica admitiria e que não tem página no site?**

```
PRÉ-FLIGHT — artigo: {keyword} · site: {site}
páginas na categoria: N

⚠ BÍBLIA SEM PÁGINA que a rubrica admitiria:
   JBL PartyBox Ultimate      R$ 7.000   100+   ✅ RELEVANTE
   JBL PartyBox Wireless Mic  R$   620   500+   acessório, fora do escopo
```

**Classificar por relevância, não só por ausência.** Listar tudo que falta vira ruído: o microfone avulso "falta" e nunca vai entrar.

⚠️ **Aqui você julga com evidência mais fraca, e precisa saber disso.** Todo o desenho manda julgar pelo conteúdo da página, e estes produtos **não têm página** — sobra a bíblia. Eles são avaliados por material mais pobre que os concorrentes deles.

Aqui a única fonte é a bíblia, então você está no **2º degrau da escada da Etapa 3 sem ter passado pelo 1º**. Isso não impede eliminar — o bruto do fabricante é prova boa — mas cobra prudência, porque a decisão de 2b é **bloquear o fluxo**, não montar lineup. Some o custo assimétrico: listar demais é uma linha no relatório, listar de menos é um produto que nunca entra em artigo nenhum. Conduta: **erre pro lado de listar** — incerto vira `✅ RELEVANTE` e quem decide é o usuário. Só fica de fora o que é obviamente outra coisa (o microfone avulso, o cabo, a capa).

**Havendo relevante, PARA.** O usuário cria a página no painel e a skill roda de novo. Montar antes e reportar depois obriga a refazer — foi o que aconteceu na 1ª execução real (2026-08-01): montei 9, o Marcelo criou 2 páginas e o lineup teve que ser refeito com 13.

**Aproveite que é barato e rode aqui também a SOBREPOSIÇÃO com artigo existente**, lendo o `products[]` dos `reviews/*.mdx` do site. Não bloqueia, mas informa antes do gasto:

```
SOBREPOSIÇÃO — quanto deste universo já está publicado
   melhor-air-fryer-oven   10 produtos · 7 também candidatos aqui
   melhor-air-fryer        11 produtos · 2 também candidatos aqui
```

Detalhe e consequência editorial ficam na Etapa 7. **Aqui é só o número, cedo.** Se 7 de 8 já estão num artigo só, isso muda a decisão de escrever o artigo — e saber depois de montar o lineup inteiro é tarde.

⚠️ **O bloqueio e os avisos baratos vêm ANTES da leitura pesada de propósito.** Eles precisam só da rubrica, da lista de ASINs e do `products[]` dos artigos — nada do conteúdo das páginas. Rodar depois joga fora 176 KB toda vez que barra.

⚠️ **Cuidado com o medidor.** Ao varrer bíblia em massa, confira o TIPO do campo antes de concluir. `specsAmazon` é **string** em todas as bíblias medidas, não dicionário — um scan que assume `dict` devolve zero e parece um achado. Em 2026-08-01 isso quase virou uma acusação falsa contra esta própria régua.

**2c. Ler INTEIRO (caro), só depois de 2b passar** (canon Marcelo 2026-08-01): `subtitle` · `shortDescription` · `pros` · `cons` · `specs` · `fullReview`.

**Isso cabe, e o teto foi medido** — a maior categoria da rede em 2026-08-01:

```
cozinhaideal/aspiradores          35 produtos   176 KB   ← o teto
melhoraspirador/aspiradores       35 produtos   168 KB
melhorairfryer/air-fryers         23 produtos   176 KB
```

Sete categorias empatam em 34-35 produtos e nenhuma passa de **176 KB**. "Ler todas as páginas da categoria" soa ilimitado e não é: o pior caso da rede cabe com folga, então **não invente amostragem** — ler parte do universo reintroduz exatamente o erro silencioso que a 2a existe pra evitar. Se um dia aparecer categoria muito maior, o corte se decide medindo, não no susto.

⚠️ **Leia `pros`/`cons` pra JULGAR, nunca como placar comparativo.** Cada página foi escrita por um sub-agent isolado, um produto por vez, então "6 prós contra 2 contras" mede o texto e não o produto.

⚠️ **Modo artigo existente** (`site/slug-do-artigo`): o universo continua sendo a categoria, mas leia também o `products[]` do artigo. Quem já está lá **não é candidato**, é contexto — e o teste de LEAD da Etapa 5 tem que contar os qualificadores já tomados por eles, senão o produto novo repete um lead que já existe no artigo.

### Etapa 3 — julgamento contra a rubrica

Cada página responde duas coisas, e as duas vão pro relatório:

```
entra?              sim / não / limítrofe
qual spec prova     o campo lido que sustenta o julgamento
```

**A prova é o que torna o julgamento auditável.** Sem ela isto é só opinião com passos extras, e opinião sem lastro é como um produto fora de faixa entra "porque é bom".

⚠️ **NENHUM PRODUTO SAI SEM QUE A VENDA DELE TENHA SIDO OLHADA.** A Etapa 4 busca bíblia só dos sobreviventes, o que é barato — e cria uma cegueira: dá pra cortar um produto aqui sem nunca ver `comprasMesPassado`. Aconteceu em 2026-08-02: marquei a `HP DeskJet 2975` como limítrofe pelo insumo e **só depois** descobri que ela vende **1.000/mês**, empatada em segundo lugar do catálogo. **Antes de marcar `não` ou `limítrofe`, abra o `snapshot` daquele candidato.** É uma leitura por corte, e corte é decisão cara.

⚠️ **LEIA A RUBRICA INTEIRA, não só a lista de eliminatórios.** No mesmo caso, a rubrica dizia que cartucho é o eliminatório nº 1 da keyword **e**, três parágrafos abaixo, que cartucho *"faz sentido: volume muito baixo e esporádico, orçamento inicial travado, ou onde a cabeça integrada protege contra entupimento"*. Eu li a primeira metade. A seção "quando faz sentido" de cada tecnologia é **régua de admissão tanto quanto a lista de cortes** — ela diz para QUAL PERFIL aquele produto é a resposta certa, e perfil é papel no lineup.

⚠️ **A RUBRICA APONTA O QUE PROCURAR. QUEM ELIMINA É A PÁGINA.** Sem trecho da página que desqualifique, o produto **entra** — mesmo que a rubrica ache que ele é de outro segmento. A consulta cega é opinião de memória: ela sabe reconhecer o que existe na categoria, mas o recorte editorial de "isso não deveria estar na mesma lista" é juízo dela, não fato do produto.

⚠️ **MAS ELIMINATÓRIO TEM DUAS FORMAS, e a regra acima só cobre uma.** Descoberto em 2026-08-02 rodando `melhor tablet para desenho`: eu cortei 5 produtos por **silêncio** da página, que é justamente o que a linha acima proíbe — e cortar estava certo, porque tablet sem caneta ativa não pertence a um artigo de desenho. O defeito era da régua.

```
DESQUALIFICADOR   "é sublimação" · "é laser" · "uso restrito ao carro"
                  a página AFIRMA o defeito  →  silêncio NUNCA elimina

REQUISITO         "precisa ter caneta ativa com pressão"
                  a página CALA  →  silêncio é AMBÍGUO, não é prova
```

**No requisito, a ausência na página não decide nada**, porque a página é derivada da bíblia por um sub-agent e pode ter perdido o fato no caminho. É a mesma classe do *"a página perde negativo"* da Etapa 4, aplicada a spec em vez de defeito.

**Escada de três degraus, e você sobe só o necessário:**

```
1º  PÁGINA        tem o requisito? → entra.  Diz que NÃO tem? → sai, com a citação.
2º  BÍBLIA BRUTA  specsAmazon · sobreEsteItem · doFabricante · conteudoBrutoFabricante
                  resolveu 5 de 6 casos com evidência de FONTE
3º  LLM ISOLADA   só o que sobrou ambíguo E tem tração alta o bastante pra o corte doer
```

**O 2º degrau é o que mais rende.** Caso real: a página do `VAIO TL10` não dizia nada sobre caneta, e a bíblia dele **afirma** *"compatível com canetas modelo capacitivas passivas"* — silêncio virou prova positiva. E o `POCO Pad M1` tinha `Stylus support` no `conteudoBrutoFabricante`, confirmando a admissão.

⚠️ **No 3º degrau, PERGUNTE SOBRE INTERPRETAÇÃO, NUNCA SOBRE O MODELO.** A LLM envelhece em fato de SKU (Armadilha 2) e não envelhece em convenção. Medido no mesmo dia, a mesma consulta:

| pergunta | confiança | serviu? |
|---|---|---|
| "a Tab A11 suporta S Pen?" | **BAIXA** — *"trate como desconhecido"* | ela mesma se recusou |
| "*suporte para caneta Stylus* na Amazon indica caneta ativa?" | **ALTA** — template de categoria, zero evidência | decidiu |
| "a Samsung nomeia S Pen quando existe?" | **ALTA** — marca registrada, nunca usa termo genérico | decidiu |
| "capacitiva passiva serve pra desenho?" | **ALTA** — sem pressão, sem tilt, sem palm rejection | decidiu |

Convenção de ficha técnica, convenção de nomenclatura de marca e fato físico são estáveis. **"Esse SKU tem X?" não é.** E um `sim` dela **manda voltar ao bruto do fabricante procurar o fato — nunca admite o produto sozinha.**

Ganho concreto do exemplo: a frase *"a Samsung sempre nomeia S Pen, então a ausência importa"* era **inferência minha**; virou fato de confiança ALTA de uma fonte que não viu o catálogo. Foi o que sustentou cortar o `Galaxy Tab A11+`, que vende **2.000/mês** e estava empatado em primeiro do catálogo.

Caso real (melhordosom, 2026-08-02), os dois lados da linha:

```
JBL SW8A-MS         página, cons: "Uso restrito ao carro ... deixam a caixa fora
                                   de uso doméstico" · "Só entrada por cabo,
                                   sem opção sem fio pra conectar no celular"
                    → o produto se declara inelegível.  FORA, com prova.

PartyBox Ultimate   página, cons: porte grande · funciona na tomada · Dolby só no Wi-Fi
                    → nada desqualifica. Cabo de energia é característica,
                      não impedimento.  ENTRA.
```

Eu tinha cortado a Ultimate por "caixa de festa é outro segmento", frase que veio da rubrica e não da página, e o Marcelo repôs: **ter cabo de energia não exclui ser caixa de som**. Diferença de formato dentro da categoria é **estrutura editorial do artigo**, e o artigo resolve isso segmentando o texto — não é critério de admissão do lineup.

⚠️ Note que "só elimina por fato, não por opinião" **não** resolveria isto: "caixa de festa é uma categoria diferente" se apresenta como fato. O que resolve é exigir o **trecho da página**.

⚠️ **`limítrofe` tem regra, e é NÃO ENTRAR.** Ele sai do lineup e vira **bloco próprio no relatório**, com a prova e uma linha do que mudaria se entrasse. Sem isso a saída de três valores só tem tratamento pra dois, e o terceiro vira decisão minha no olho — foi o que aconteceu em 2026-08-01 com a `Britânia BAF11A` de **11 litros** num artigo de 12: eu escalei pro Marcelo por instinto, não por régua.

⚠️ **Seja honesto sobre o que isso é: um DEFAULT, não "reportar em vez de arbitrar".** Excluir o limítrofe é uma decisão, e a skill está tomando ela. A diferença pro empate entre dois candidatos (que ela realmente reporta sem arbitrar) é que ali não existe lado barato — aqui existe. Incluir um produto fora do recorte contamina a keyword do artigo inteiro, enquanto deixá-lo no bloco de limítrofes custa três linhas e o usuário repõe com uma palavra. **O default vai pro lado barato e diz que fez isso.**

**A tabela `specs` é onde a classificação mora**, e o motivo NÃO é cobertura. Medido no melhorairfryer, recorte "12 litros": a capacidade aparece em **23 de 23** páginas e é citada em **20 de 23** bíblias. Três produtos de diferença não sustentariam regra nenhuma.

O que sustenta é a página **qualificar o formato**, que é o que decide a categoria:

```
12 litros (formato forno)  ·  12 litros, com dois andares  ·  7,2L totais (4,7L útil)
```

O campo bruto entrega só o número. Sem a qualificação eu teria tratado como iguais produtos que a consulta cega identificou como coisas fisicamente diferentes vendidas sob o mesmo rótulo. **É a qualificação que decide, não a contagem** — se for citar a medição, cite as duas metades.

**Aderência à keyword é informativa, ainda NÃO ordena.** Quando a keyword tem número, o valor útil costuma divergir do nominal — nos 8 finalistas de "12 litros" o cesto real ia de 3,5 L a 5 L. **Reporte a divergência numa coluna**, não a use pra reordenar: a regra de posição 1 tem 71% de 307 artigos atrás dela e esta observação tem **uma** execução. Nesta mesma sessão inventei três regras de observação única e as três morreram na medição (`melhor escolha ≠ mais vendido` → coincidem em 71% · `artigo de 4 produtos é raso` → 42 existem, todos de recorte estreito · `escada decrescente é padrão` → 27%). Medir antes de promover.

### Etapa 4 — bíblia dos sobreviventes

Só de quem passou pela Etapa 3, e só o que a página não tem:

| campo | por que a página não serve |
|---|---|
| `snapshot.comprasMesPassado` | não existe na página, e é o eixo de ordenação |
| `snapshot.precoBRL` / `disponivel` | a página tem `schemaPrice` (arredondado editorial), não disponibilidade — **mas ver o aviso abaixo** |
| `identidade.marca` | a página não tem campo de marca |
| **`pontosFracos`** | ver abaixo — é o motivo mais importante |
| `angulosConversao` · `sentimentoCompradores` · `dadosInconsistentes` | não passam pra página |

⚠️ **A página PERDE negativo, e por isso o julgamento de qualidade continua vindo da bíblia.** Caso real (melhorairfryer, 2026-08-01):

```
Philco PFR2200P   bíblia: 3 pontosFracos, um deles ferrugem interna
                  página: 6 pros e 2 cons — a ferrugem sumiu
```

Na Britânia BFR2100P a mesma queixa sobreviveu à passagem. Não é regra, é risco — a página é escrita pra convencer, então o negativo é o primeiro a cair. Pra decidir posição 1 e pro aviso de qualidade, leia `pontosFracos` na bíblia.

⚠️ **PREÇO: a página e a bíblia divergem, e a régua não elegia uma fonte.** O invariante manda ler preço do `.mdx`, e esta tabela manda buscar `precoBRL` na bíblia — as duas coisas ao mesmo tempo. Medido no oguiacompra (2026-08-02):

```
Epson EcoTank L8050    página R$ 1.499   bíblia R$ 4.000    63%
HP LaserJet M107W      página R$   699   bíblia R$   950    26%
Canon Mega Tank G3110  página R$   699   bíblia R$   900    22%
Brother HL-L1232W      página R$   799   bíblia R$   990    19%
HP DeskJet 2975        página R$   450   bíblia R$   450     0%
```

**Regra: use `snapshot.precoBRL` da bíblia** — é o dado de captura datado, e o `schemaPrice` da página é arredondamento editorial que ninguém re-verifica quando o preço muda. **Mas reporte a divergência quando passar de 20%**, porque um dos dois está errado e você não sabe qual. Em artigo de custo-benefício isso pode inverter o top-3 sozinho.

**Nunca a bíblia inteira.** Medido: 19 KB por produto. Num catálogo de 35 são 665 KB e a skill morre de contexto antes de ordenar. Os 7 campos curados custam 5 KB, e a página inteira 4 KB.

### Etapa 5 — seleção

⚠️ **ORDEM DE APLICAÇÃO — não é lista de regras soltas, é sequência.** Aplicar fora de ordem dá resultado diferente. As seções abaixo seguem esta ordem.

```
entram aqui já filtrados pela rubrica + página (Etapa 3), com o tipo lido da PÁGINA

1. gêmeo / sucessão / rebadge   A e C REMOVEM · B só amarra ordem
2. DOMINAÇÃO             quem não acrescenta nada sai
   ▶ CHECKPOINT DE EXCLUSÕES — imprime o livro-razão antes do trabalho caro
3. posição 1             mais vendido entre os viáveis, preço de meio de faixa
4. top-3                 escada de preço a partir do #1
5. teste de LEAD         admissão das posições 4+, POR VENDA DECRESCENTE
                         quem tem comprasMesPassado = 0 entra no FIM da fila
6. tamanho               corta o excedente pela cauda, PRESERVANDO representante único
```

---

#### Passo 1 — gêmeo, sucessão, rebadge

```
A. variante do MESMO modelo (voltagem, cor, ASIN duplicado)  →  a MAIS VENDIDA ganha, a outra SAI
B. geração seguinte da MESMA linha (Go 4 → Go 5)             →  a MAIS NOVA fica ACIMA, as duas ficam
C. mesmo produto sob DUAS MARCAS irmãs (rebadge)             →  a MAIS VENDIDA ganha, a outra SAI
```

⚠️ **O passo 1 faz DUAS coisas, e só uma reduz a lista.** A e C tiram produto. B **não tira ninguém** — ele emite uma **restrição de ordem** que precisa sobreviver até o passo 5.

```
passo 1 emite:   Go 5 fica ACIMA da Go 4
passo 5 aplica:  entram por venda decrescente  →  Go 4 (3.000) viria antes da Go 5 (500)
                 ⚠ a restrição do passo 1 VENCE a venda
```

**Por que 1 vem antes de 5:** o teste de lead depende de quais qualificadores já foram tomados. A e C decidem QUEM está em jogo; B decide QUEM ESCOLHE PRIMEIRO entre duas gerações. Rodar o lead antes disso dá a uma geração um qualificador que pertence à outra.

⚠️ **Carregue a restrição, não confie na memória.** Quando o passo 5 ordena por venda e a diferença é grande (Go 4 vende 6× a Go 5), a tentação de "corrigir" a ordem é forte. Anote a restrição ao sair do passo 1 e **reporte a tensão**, com os dois números visíveis.

**A fronteira do caso A: pacote que HABILITA USO não é variante.** Voltagem e cor não mudam o que o comprador consegue fazer. Um acessório incluído pode mudar. O teste: **sem o pacote, o comprador precisaria de outra compra pra fazer aquilo?** Se sim, são produtos distintos e os dois podem entrar.

```
Encore Essential 2       R$ 1.400   500/mês   as DUAS têm entrada de microfone
Encore Essential 2 Mic   R$ 1.900   300/mês   só uma vem COM o microfone
```

Só uma responde "caixa de som JBL com karaokê" no primeiro dia. Canon Marcelo 2026-08-02, depois de eu cortar a versão Mic como se fosse variante de cor.

**O caso B ordena e não elimina** — e a versão anterior desta régua atribuía ao Marcelo uma decisão que era minha. O que é canon dele (2026-08-01) é **"venda é indicador atrasado"**: a geração que sai vende mais porque baixou de preço e acumulou avaliações, e o artigo é perene. Disso segue que **a mais nova merece a posição melhor**, e só isso. Eu traduzi "mais relevante" em "a anterior é cortada" e cortei um produto de 3.000/mês.

```
Go 4   R$ 230   3.000/mês      Go 5   R$ 280   500/mês
                               ↑ fica acima por ser a sucessora
                               ↓ a Go 4 continua, porque ainda tem tração
```

**A anterior fica enquanto tiver venda.** Sai quando a tração morrer, não quando a sucessora nascer. Canon Marcelo 2026-08-02.

**Detecção de B:** padrão de nome `{Linha} {N}` e `{Linha} {N+1}` no mesmo catálogo.

**O caso C escapa dos outros dois**, porque o nome não tem nada em comum. Caso real: `Britânia BFR2100P` e `Philco PFR2200P` são a mesma máquina, e os dois estavam no lineup com a Britânia na posição 2. Sinais, em ordem de força:

```
ASIN com prefixo compartilhado    B08R9341ZB · B08R93TVRG   ← cadastro conjunto, o mais forte
specs idênticas em ≥4 dimensões   1800 W · 80-200 °C · painel touch · 9 funções
mesmo defeito nos pontosFracos    ferrugem nos dois
marcas do mesmo grupo             Britânia e Philco
```

**Um sinal só = investigue; três ou mais = trate como gêmeo.** Desempata por venda: Philco 500/mês contra 100/mês.

⚠️ **"Specs iguais" só conta em campo que AS DUAS páginas declaram.** Rótulo ausente é **desconhecido, não igual** — as páginas são escritas por sub-agents independentes, que escolhem rótulos diferentes pro mesmo produto. Erro real: declarei `HP Smart Tank 581` e `584` gêmeas por baterem em 4 dimensões, mas a maioria dos campos **não existia nas duas** — comparei a sobreposição acidental e li o resto como igualdade. O Marcelo corrigiu: **são parecidas, não gêmeas.** Duas defesas: conte quantos campos as duas realmente compartilham antes de somar dimensões, e lembre que **sem sinal de ASIN a similaridade de specs sozinha não fecha o diagnóstico**.

---

#### Passo 2 — dominação

⚠️ **É o que faltava.** A régua tinha aviso de marca, de reuso e de sobreposição com outro artigo, e **nada que comparasse uma posição com as outras do próprio lineup**. Resultado (oguiacompra, tanque de tinta, 2026-08-02): montei 11 produtos com **três SKUs da mesma plataforma HP 580**, 27% da lista.

```
teste:  A é pior-ou-igual a B em TODO campo que AS DUAS páginas declaram
        E custa igual ou mais            →  A é DOMINADO

HP 583  R$880    6.000 preto  12/5 ppm  100 folhas  3 em 1   ← dominado
HP 584  R$820   12.000 preto  12/5 ppm  100 folhas  3 em 1
```

R$60 a mais por metade da tinta, todo o resto idêntico. Vale a mesma cautela do passo 1: campo que só UMA página declara é desconhecido, não empate.

**Quase-dominação vira relatório em vez de corte:** a `L5590` (R$1.700) contra a `L6270` (R$1.900) — R$200 compram duplex automático, bandeja de 250 contra 100 e rendimento de 7.500 contra 4.300.

**A pergunta que nenhum outro passo faz:** *esta vaga carrega algo que nenhuma outra vaga carrega?* Foi o que o Marcelo fez à mão no artigo publicado, que tem 7 posições e **um** Smart Tank contra as minhas 11 com três.

---

#### ▶ CHECKPOINT DE EXCLUSÕES — entre o passo 2 e o 3

⚠️ **Imprima o livro-razão de tudo que saiu, ANTES de escrever posição ou subtítulo** (canon Marcelo 2026-08-02). É o último momento barato de o usuário discordar: aqui já aconteceu tudo que tira produto **por um motivo**, e nada de caro foi produzido ainda.

**Por que aqui e não no pré-flight:** o pré-flight da Etapa 2b só enxerga bíblia sem página. As exclusões acontecem em quatro momentos (Etapa 3 · passo 1 · passo 2 · passo 6), e depois do passo 2 três dos quatro já rodaram. O passo 6 fica de fora porque depende da ordenação e é transparente por natureza — ele entra no relatório final.

**Motivo da regra:** em 2026-08-02, **todo** erro que o Marcelo e os audits pegaram foi uma **exclusão** — `PartyBox Ultimate`, `Encore Essential 2 Mic`, `Go 4`, `Galaxy Tab A11+` (2.000/mês), a única fotográfica, as duas únicas Brother, o `POCO Pad M1` admitido com a prova que reprovou outro. Exclusão é onde os erros se concentram e era a parte menos visível da entrega.

```
CHECKPOINT DE EXCLUSÕES — 30 no universo · 11 no lineup · 19 fora

ASIN            R$  vend   onde saiu   motivo
B09QSXYGSS    2600     —   Etapa 3     Tipo = "Impressora de sublimação (só impressão)"
B0G491Z8QR     450     —   Etapa 3     Tipo = "Multifuncional jato de tinta (cartucho)"
B07V3KSMFD    1200     0   passo 6     cauda · 0/mês · ÚNICA monocromática de tanque      ⛔
B0DK9ZQWPP     870     0   passo 6     cauda · 0/mês · ÚNICA Brother                      ⛔
B091JCMN73    5400     0   passo 6     cauda · 0/mês · ÚNICA fotográfica 6 tintas         ⛔

⛔ 5 dos 19 são ÚNICO representante de marca ou subtipo
```

**Colunas obrigatórias:** ASIN · preço · `comprasMesPassado` · em que etapa saiu · o motivo **com a citação**. Preço e venda de quem saiu são o que faz o erro gritar — foi assim que a `DeskJet 2975` de 1.000/mês e o `Tab A11+` de 2.000/mês teriam aparecido na tela em vez de num audit horas depois.

⚠️ **Marque `⛔` quem é ÚNICO representante de marca ou subtipo.** A regra de precedência da cauda (passo 6) já protege esses, mas ela opera em silêncio — o marcador faz o julgamento aparecer para quem lê.

**Quando parar e quando seguir:**

```
sem --aplicar   imprime e SEGUE montando. O usuário lê enquanto você trabalha
                e corta antes de você terminar. O relatório final repete o livro-razão.
com --aplicar   imprime e PARA. Criar artigo é escrita — não crie sobre exclusão
                que o usuário ainda não viu.
```

---

#### Passo 3 — posição 1

**O mais vendido entre os viáveis, em preço de meio de faixa.** Medido na rede: a posição 1 é o mais vendido do lineup em **71%** dos 307 artigos com bíblia completa, e **não é o extremo de preço em 79%**.

⚠️ **`comprasMesPassado` é degrau, não número.** A Amazon publica faixa, então `1000` pode ser 1.000 ou 9.000 e empate é comum. Quando empatar, **não invente desempate**: caia no critério seguinte (preço de meio de faixa) e **registre o empate**. Caso real: Mondial e Philips empataram em `1000`, e decidiu o preço — R$ 550 no meio da faixa contra R$ 850 no teto.

---

#### Passo 4 — top-3 e escada de preço

**Top-3 com preço decrescente** (preferência do Marcelo). A rede NÃO tem padrão aqui — medido: `#2 é o mais barato` 41%, `decrescente` 27%, `crescente` 16%, `#2 é o mais caro` 14%. É preferência declarada, não observação; não apresente como "o que a rede faz".

💡 **RECOMENDAÇÃO, não regra: evite duas marcas iguais SEGUIDAS no top-3** (canon Marcelo 2026-08-02). As três primeiras posições são a vitrine, e `Epson · Epson · HP` lê como preferência de marca antes de ler como recomendação. Não trava nada.

⚠️ **Isento quando a keyword nomeia a marca.** `melhor impressora HP`, `melhor caixa de som JBL` — ali a marca única é o recorte, e diversificar seria trair a keyword.

⚠️ **Briga com a escada de preço, e não há precedência.** Caso real: o top-3 saiu `L3250 R$1060 · L1250 R$850 · Smart Tank 581 R$820`, com duas Epson seguidas. Trocar #2 e #3 resolve a marca e **quebra a escada** (1060 → 820 → 850). Quando colidem, **reporte as duas ordens**.

---

#### Passo 5 — teste de LEAD e ordem das posições 4+

**As posições 4+ entram por VENDA DECRESCENTE**, e quem tem `comprasMesPassado = 0` entra no fim da fila. Quem vende mais **escolhe qualificador primeiro** — a ordem de entrada decide quem fica com o lead livre e quem sobra sem papel.

**Teste de LEAD distinto.** Cada produto precisa suportar um LEAD de subtitle próprio, sem repetir o qualificador de outro.

⚠️ **Separe o que é regra do crit. 22 do que é heurística DESTA skill.** Em 2026-08-01 esta seção citava o crit. 22 como fonte de um portão de exclusão, e a fonte não diz isso:

| | status no crit. 22 |
|---|---|
| **LEADs distintos entre produtos** | **regra** — está na lista FLAGRAR |
| a sequência abaixo | "sequência **típica**" |
| o vocabulário de qualificadores | "**SUGESTÃO, não regra**" |
| **excluir produto do artigo** | **não existe.** O output do crit. 22 é `newSubtitle` |

Cortar produto por aí é heurística própria, defensável (se não dá pra articular papel distinto, talvez o produto não pertença) mas **sem respaldo no crit. 22**. Por isso o resultado é sinal, não veredito: **produto sem lead disponível é candidato a ficar de fora — reporte em vez de cortar calado.**

Sequência típica, não canônica:

```
pos 0   Melhor {Categoria} em Geral ...      ← "Melhor" obrigatório SÓ aqui
pos 1   {Categoria} Custo Benefício ...
pos 2   {Categoria} Boa e Barata ...
pos 3+  perfil / marca / feature
```

⚠️ **Concordância de gênero pelo núcleo da keyword** (crit. 22, regra dura): `impressora → Boa e Barata` · `tablet → Bom e Barato` · `aspirador → Bom e Barato`. Nunca trocar.

⚠️ **O GANCHO É ORAÇÃO COM VERBO, NÃO FICHA TÉCNICA** (canon Marcelo 2026-08-02). Empilhar spec responde *o que é* e não responde *e daí*:

```
ficha   Impressora de Tanque 4 em 1 com ADF de 30 folhas e Ethernet
frase   Impressora de Tanque 4 em 1 que digitaliza um maço de uma vez
```

**O molde:** LEAD capitalizado + emenda (`que` · `com` · vírgula) + **o DIFERENCIAL deste produto dentro deste lineup**. O número entra dentro da oração, não como lista. Padrão pescado dos artigos publicados do oguiacompra — `"que vira a folha sozinha"`, `"que dispensa o scanner sem uso"`.

⚠️ **DIFERENCIAL, não "o que o produto faz pelo leitor"** (canon Marcelo 2026-08-10, corrigindo a redação anterior desta seção). A régua dizia "oração que diz o que o produto FAZ pelo leitor", e isso empurra pro genérico: num comparativo, **quase todos fazem a mesma coisa**. Todo aspirador vertical aspira o chão, todo 2 em 1 vira de mão, toda impressora imprime. Quando o molde pede benefício e o benefício é comum, a saída vira frase de efeito pra soar distinta sem dizer nada.

```
❌ que encosta no armário e some          cena, não fato · vale pra qualquer compacto
❌ para quem limpa com gente dormindo      cena · e o produto NÃO era o mais silencioso
❌ que vira de mão sem trocar de aparelho  todo 2 em 1 do lineup faz isso
❌ com 1,65 kg e filtro HEPA removível     ⚠ PARECE spec, e mesmo assim não diferencia
✅ com 2000 W para carpete e tapete grosso a maior potência DA LISTA
✅ o mais barato do comparativo            superlativo verdadeiro dentro do lineup
✅ com 1,1 kg no modo de mão               o mais leve, com o qualificador que o torna verdadeiro
```

⚠️ **O 4º ❌ é o erro mais fácil de não ver, e eu cometi ele escrevendo esta própria seção.** "com 1,65 kg e filtro HEPA removível" passa no teste de "não é frase de efeito" — é spec, é factual, tem lastro. E não diferencia nada: no lineup em que foi escrito, três produtos eram MAIS leves (1,1 · 1,5 · 1,6) e **8 dos 11 declaravam HEPA**. Spec verdadeira não é o mesmo que spec distintiva. **O teste não é "isso é fato?", é "ordenando os 11 por esse atributo, este fica em primeiro?"**

⚠️ **Se nenhum atributo coloca o produto em primeiro, ele pode não ter lead.** Isso não é falha de redação, é sinal do passo 5: *produto sem lead disponível é candidato a ficar de fora* — reporte, não force um gancho morno.

**O gancho responde: por que ESTE e não os outros dez?** O vocabulário natural disso é comparativo — mais leve, mais potente, mais barato, menos barulho, maior autonomia — ou de recorte de uso quando o produto é o único que atende: passa pano, para apartamento, com saco, sem fio.

⚠️ **Consequência direta: o gancho não pode citar número em que o produto PERDE pra outro do mesmo lineup.** Deixou de ser aviso separado e virou o mesmo princípio — se o gancho é o diferencial, citar um número onde você perde é uma contradição, não um descuido. A `EcoTank L3250` estava no slot "Melhor em Geral" com o gancho *"até 4.500 páginas"*, e três produtos da mesma lista rendem **12.000 por R$ 240 a menos**. **Antes de fechar, ordene o lineup por cada número citado nos ganchos.**

⚠️ **E o diferencial precisa de LASTRO, não do nome do produto.** Caso real (2026-08-10, melhoraspirador-com): ia dar ao `WAP Silent Speed Max` o lead "Silencioso", que é o nome comercial dele. A bíblia declara **85 dB**, e o `Electrolux STK15` da posição 1 declara **84 dB** — o "silencioso" era o mais barulhento dos dois. Marca batiza produto por marketing; o diferencial se prova na ficha ou não existe.

⚠️ **O resultado depende do que já foi atribuído**, por isso este teste é o passo 5 e não o 1. Caso real: a `Go 4` vende **3.000/mês** e a `Go 5` vende **500**. Por venda pura a Go 4 entraria primeiro e levaria o qualificador melhor; a restrição do passo 1 inverte, e a Go 5 fica em #3 com `Boa e Barata` enquanto a Go 4 entra em #4 com `Ultraportátil`.

⚠️ **O teste é lexical, não semântico.** Ele checa se o qualificador repete, não se os produtos são parecidos. Três caixas de bolso podem passar com "Custo Benefício", "Boa e Barata" e "Compacta". Se o lineup ficar com 3+ produtos do mesmo formato, olhe à mão.

---

#### Passo 6 — tamanho

**TETO 11, PISO 4** (canon Marcelo 2026-08-02). Não é faixa sugerida, é limite.

```
> 11   corta o excedente pela cauda, e REPORTE quem saiu
< 4    o recorte não sustenta artigo — pare e diga isso, não complete com produto fraco
```

O piso de 4 é mais apertado que o gate da rede, que é 3 (`artigo-auditar`, `productCount >= 3`) — vale o mais apertado. A rede tem 42 artigos com exatamente 4 produtos, todos de recorte estreito.

⚠️ **A CAUDA NÃO É SÓ ORDEM DE VENDA — REPRESENTANTE ÚNICO TEM PRECEDÊNCIA.** Corte primeiro quem **duplica** um eixo já coberto, mesmo que venda mais que outro da cauda.

```
ordem de corte, da cauda pra cima:
  1º  dominado ou quase-dominado (passo 2)
  2º  duplica eixo já coberto por outro do lineup
  3º  menor comprasMesPassado  ·  quem tem 0 (sem widget) cai aqui
  ⛔  representante ÚNICO de marca, subtipo OU PERFIL sai por último
```

⚠️ **"Perfil" entrou nesse ⛔ em 2026-08-11 e é a adição que mais muda resultado.** Marca e subtipo saltam à vista na tabela; perfil só aparece se você levantar a cobertura (Etapa 7). Foi por não estar aqui que o `WAP High Speed Plus` — 1,25 kg, o mais leve do catálogo, e a única resposta do perfil "força reduzida" — foi cortado por "duplica eixo" sem que ninguém notasse o que ia junto.

Caso real (oguiacompra, tanque de tinta): meu lineup cortou a **única fotográfica** e a **única Brother** do catálogo e ficou com três SKUs da plataforma HP 580. O artigo publicado, com 7 posições, mantém as duas e usa um Smart Tank.

Isso só funciona porque `comprasMesPassado = 0` deixou de eliminar (ver Invariantes) — enquanto ele filtrava, os representantes únicos saíam do pool **antes** de qualquer regra poder preferi-los.

⚠️ **O TETO 11 É LIMITE, NÃO META** (canon Marcelo 2026-08-11). Preencher até 11 porque cabe é o erro. **O tamanho sai da COBERTURA**, e a pergunta por posição é: *este produto tem eixo próprio, OU cobre um perfil que ninguém mais cobre?* Uma das duas basta. Nenhuma das duas = ele não está sustentando a vaga.

```
tem eixo próprio (vence algum atributo no lineup)   →  fica
sem eixo, mas é o ÚNICO que atende um perfil        →  fica, e o perfil é o motivo declarado
sem eixo e sem perfil exclusivo                     →  candidato a sair, com o motivo no relatório
```

⚠️ **"Sem eixo próprio" NÃO é motivo suficiente pra cortar** — e essa distinção nasceu de um erro medido. Em 2026-08-11 (melhoraspirador-com, `melhor aspirador de pó vertical`) duas execuções da mesma keyword produziram 11 e 9 posições. A de 9 cortou tudo que não vencia um superlativo, e junto foi o **WAP High Speed Plus, 1,25 kg — o mais leve do catálogo inteiro em configuração completa**. O lineup ficou com 1,5 kg como piso e **o perfil "força reduzida" da rubrica descoberto**. Ele não vencia eixo nenhum e era a única resposta de um perfil.

**Por isso a cobertura de perfil é bloco obrigatório do relatório (Etapa 7):** sem esse dado, esta regra não tem como ser aplicada — você não sabe qual perfil ficou descoberto se ninguém for obrigado a olhar.

---

#### Transversal — onde a sequência briga

**Onde a sequência empata, REPORTE.** Os passos 5 e 6 podem colidir. Caso real: o lineup fechou com 12 produtos e o ideal é 9 ou 11; cortar pelo tamanho tiraria a `PartyBox Ultimate` (100/mês), justamente o topo de linha e o único eixo "evento grande" da lista. Não existe precedência entre "tamanho ideal" e "eixo distinto", e inventar uma seria pior que reportar.

**Sobre o `comprasMesPassado = 0`, dois argumentos distintos e só um caiu:**

```
FRESCOR      "a bíblia é velha, o número não vale"   →  REJEITADO. Medido: os ZEROS eram as
                                                        capturas MAIS NOVAS do lote, e produtos
                                                        do MESMO DIA deram 0, 50 e 200.
SEMÂNTICA    "0 = sem widget, não = zero venda"      →  ACEITO. Por isso ordena, não elimina.
```

O número continua válido como referência **relativa** dentro do mesmo catálogo. Não reabra o eixo frescor.

### Etapa 6 — audit do lineup (SEMPRE, sub-agent ISOLADO)

**Roda ANTES do relatório, não depois.** Sem `--aplicar`, o relatório **é** a entrega — auditar depois dele é te mostrar algo que eu já sei que pode estar torto.

⚠️ **Não pode ser você mesmo.** Quem acabou de montar o lineup passou a etapa inteira se convencendo de cada escolha e vai carimbar. É o mesmo motivo pelo qual a Etapa 1 é isolada.

**O sub-agent RECEBE:** site · keyword · o lineup final (ASIN, ordem, subtítulo) · a lista de **excluídos com motivo e prova alegada** · a rubrica · acesso aos arquivos.
**NÃO recebe:** o seu raciocínio, a sua narrativa, nem o relatório escrito. Lendo como você chegou ali, ele concorda com você.

**As seis checagens:**

```
1  toda exclusão tem trecho CITÁVEL — e no degrau CERTO da escada?
   DESQUALIFICADOR ("é sublimação")  → a prova tem que estar na PÁGINA. Não achou = achado.
   REQUISITO ("precisa ter caneta")  → a página PODE calar. A prova vem da BÍBLIA BRUTA.
                                       Exclusão por silêncio, sem ninguém ter aberto a
                                       bíblia daquele produto = achado.
   ⚠ não flagre exclusão de requisito só porque o .mdx não diz nada — é esperado.

2  todo gancho tem lastro E não contradiz o próprio lead?
   "12 Litros ... com cesto de 5 litros" é contradição interna, não falta de lastro.

3  nome e preço batem com o .mdx, caractere a caractere?

4  sobrou par de gêmeo / sucessão / rebadge não resolvido?
   prefixo de ASIN compartilhado · specs iguais em ≥4 dimensões · mesmo defeito.

5  a restrição de sucessão do passo 2 chegou no passo 5?
   havendo par de geração, a mais nova está acima?

6  algum problema reportado SOME se desfizer uma exclusão?
```

⚠️ **A checagem 6 é a razão de o audit existir**, e o método é mecânico: **pegue cada problema que o lineup declara e teste re-inserindo os excluídos.**

```
"a escada quebrou, não existe nada entre R$ 270 e R$ 550"
   → algum excluído cai na faixa?   Britânia BAF11A, R$ 380     ⛔ o problema é seu, não do catálogo

"a posição 1 é extremo de preço"
   → re-inserindo os excluídos, continua extremo?   Ultimate R$ 7.000   ⛔ idem
```

Os dois são casos reais de 2026-08-02, e os dois eu reportei como buraco da régua antes de descobrir que eram consequência de um corte meu. É a única checagem que nenhuma skill downstream consegue fazer, porque exige comparar o lineup com o universo **antes** do corte — informação que só existe neste momento.

**Duas severidades** (mesmo canon da `artigo-reviews-auditar`, "aplica o óbvio, propõe o julgamento"):

| tipo | exemplos | conduta |
|---|---|---|
| **erro objetivo** | nome/preço divergente do `.mdx` · >13 palavras · dois-pontos · gêmeo não resolvido · gancho sem lastro | **conserte antes de mostrar** |
| **julgamento** | exclusão sem prova citável · problema que some ao desfazer exclusão · gancho que contradiz o lead | **vai pro relatório, o usuário decide** |

⚠️ **Não abafe.** Os achados de julgamento entram no relatório **com o texto do sub-agent**, não com a sua paráfrase. Você é parte interessada.

⚠️ **Não flagre o que já está declarado.** Se o relatório já diz "as posições 2 e 3 vendem 100/mês, o piso do lote", isso não é achado. Audit que repete o que já foi reconhecido vira ruído, e ruído treina você a ignorar.

**Por que SEMPRE e não opt-in** (o `--audit` da `pagina-produto-criar-em-massa` é opt-in): medido em 2026-08-02, as **4 execuções reais tiveram pelo menos uma falha de julgamento cada** — atribuição errada da sucessão · escada quebrada falsa · três exclusões por opinião da rubrica mais o conflito falso da posição 1 · gancho contradizendo o lead. Taxa de 4 em 4. Um sub-agent é barato perto de nove reviews escritos sobre lineup torto.

**Escopo: só o que ninguém mais checa.** O crit. 22 da `artigo-reviews-auditar` já valida formato de subtitle e a `artigo-auditar` valida o artigo. Não repita. O que é exclusivo deste momento é a relação entre o lineup e o **universo que ele descartou**.

### Etapa 7 — relatório

Abre com a **rubrica da Etapa 1**, resumida. Ela vem primeiro porque é o critério que o resto do relatório aplica, e mostrá-la depois da tabela transforma régua em justificativa.

**O que da rubrica aparece aqui:** os critérios de **qualidade**, os **perfis de uso** e as **armadilhas**. Os eliminatórios já fizeram o trabalho deles na 2b e na 3, e repeti-los é ruído — o que interessa ao leitor do relatório é contra o que os sobreviventes foram medidos, e o que a categoria esconde.

**Blocos obrigatórios além da tabela:**

```
EXCLUSÕES         o livro-razão do CHECKPOINT, agora completo — inclui o passo 6
                  (tamanho), que não existia quando o checkpoint imprimiu
LIMÍTROFES        quem a Etapa 3 marcou assim, com a prova e o que mudaria se entrasse
SEM PÁGINA        o que a 2b listou, se algo foi criado no meio do caminho
```

⚠️ **O livro-razão aparece DUAS vezes de propósito**, e não é redundância: no checkpoint ele é parcial e serve pra você discordar cedo; no relatório é completo e serve de registro do que foi decidido. Se o usuário mandou repor algo no checkpoint, o relatório mostra o produto **dentro** do lineup, não na lista de fora.

Colunas obrigatórias, nesta ordem:

```
#  ASIN         Produto              R$      Compras/mês   Subtítulo sugerido
```

- **ASIN é a chave.** Nome é ambíguo (abreviação, variante com uma palavra de diferença), preço muda, posição muda.
- **Nome e preço LIDOS do `.mdx`**, nunca digitados de memória — inclusive ao montar a tabela.
- ⚠️ **A célula "Subtítulo sugerido" leva SUBTÍTULO, nunca rótulo de diagnóstico.** `sem eixo próprio`, `a definir`, `eixo fraco` não são subtítulos — são anotação sua, e quem lê a tabela não tem o que fazer com elas. Se o produto não tem diferencial, as saídas legítimas são duas: **tirá-lo do lineup** dizendo por quê, ou **mantê-lo com o melhor subtítulo possível** e sinalizar o eixo fraco **em nota à parte**. Caso real 2026-08-11: entreguei 5 de 11 células com "sem eixo próprio" e o Marcelo respondeu *"cadê o subtítulo, não entendi nada"* — com razão, porque a entrega não era utilizável.
- **`comprasMesPassado` sempre visível.** É o que deixa você discordar da ordem olhando o dado.
- **Data de captura da bíblia junto.** Preço e venda envelhecem; quem lê precisa saber de quando é o retrato.

Mais os **avisos** (não travas):
- **Concentração de marca**, com a proporção dela no catálogo pra comparar. ⚠️ **Isento quando a keyword nomeia a marca** — `melhor-impressora-epson` tem 9/9 Epson por design. O risco real não é parecer patrocinado, é o artigo derivar pra "melhor {categoria} {marca}" em vez da keyword alvo (canon Marcelo).
- **Reuso intra-site**: em quantos artigos do site o produto já aparece. A `artigo-clonar-em-massa` avisa que 3-4 esgota o espaço de ângulos honestos, mas o oguiacompra tem produto em 7 de 19 artigos — então informe, não bloqueie.
- **Sobreposição com artigo EXISTENTE do site** — o número já saiu na Etapa 2b; **aqui entra a consequência editorial**. Diferente do reuso, que conta por produto: a pergunta é *quanto deste lineup já é um artigo que existe*. Nenhum contador por produto mostra isso, e é o sinal de canibalização. Caso real (melhorairfryer, 2026-08-01): o recorte "12 litros" saiu com **7 dos 8 produtos já no `melhor-air-fryer-oven`** — inevitável no nicho, porque uma air fryer de 12 litros É uma air fryer oven. Não trava: avisa que a separação vai ter que vir do ângulo editorial, não do lineup.
- **Cobertura de subtipo** — obrigatório quando a rubrica listou subtipos. Diga quais o lineup cobre, quais ficaram de fora e **quem carregava cada um dos que saíram**. Formato:

```
COBERTURA DE SUBTIPO (da rubrica da Etapa 1)
   ✅ multifuncional colorida   L3250 · 581 · 584 · 583 · G3110
   ✅ só-impressão              L1250
   ✅ escritório duplex+ADF     L6270 · L5590
   ✅ A3+                       L14150
   ❌ monocromática             M1120 ficou fora do teto de 11
   ❌ fotográfica 5-6 tintas    L8050 · L8180 · L18050 ficaram fora do teto
```

Sem isso o buraco de cobertura só aparece quando alguém procura. Caso real (oguiacompra, 2026-08-02): o lineup cobria 1 de 4 subtipos que a rubrica pedia, e quem achou foi o audit da Etapa 6 — a rubrica listava a monocromática como *"o subtipo mais mal divulgado do segmento"* e ela estava entre os cortados.

- **Cobertura de PERFIL** — obrigatório, mesmo peso do subtipo (canon Marcelo 2026-08-11). A rubrica da Etapa 1 lista subtipos **e** perfis de uso, e só o primeiro tinha bloco. Mesmo formato: quais perfis o lineup cobre, quais ficaram descobertos e **quem carregava cada um dos que saíram**.

```
COBERTURA DE PERFIL (da rubrica da Etapa 1)
   ✅ apartamento pequeno    Mondial AP-36 · PAS1600P
   ✅ casa grande            Philips Aqua 3000 (60 min)
   ✅ carpete                PAS4000V (2000 W, página cita carpete)
   ✅ lavar o chão           Liectroux i7 Pro · Philips Aqua 3000
   ✅ orçamento de entrada   Mondial AP-36 (R$ 130)
   ❌ força reduzida         WAP High Speed Plus (1,25 kg, o mais leve do catálogo) ficou fora
   ❌ pet                    nenhuma página declara escova anti-enrolamento — buraco do CATÁLOGO
```

⚠️ **Separe buraco DE CORTE de buraco DE CATÁLOGO**, porque a ação é oposta. Descoberto por corte = candidato a repor (é o motivo válido de manter produto sem eixo, ver passo 6). Descoberto porque nenhum produto do catálogo atende = informação pro guia e pra próxima compra de bíblia, não erro do lineup.

Este bloco é o que **alimenta a regra de tamanho do passo 6**. Sem ele, "sem eixo mas cobre perfil exclusivo" é inaplicável, porque ninguém levantou os perfis.

- **Empate na posição 1**, quando dois candidatos ficam próximos em preço, tipo e prós/contras, ou quando empatam no degrau de `comprasMesPassado`.
- **Aderência à keyword** quando a keyword tem número — valor nominal contra valor útil, como coluna informativa. Não reordena (ver Etapa 3).
- **Escada de preço quebrada.** Se o catálogo não tem produto na faixa que o top-3 pede, diga isso em vez de forçar. Caso real: entre R$ 270 e R$ 550 não existia nada em 12 litros, e o #1 e o #2 empataram em preço.

**Sinal de mercado é só `comprasMesPassado`.** Nota média e contagem de avaliações da Amazon ficam de fora: a média não discrimina (quase tudo entre 4,3 e 4,8), a contagem exigiria campo novo no schema (hoje só existe como texto solto em ~10% das bíblias) e resolveria um empate raro. ⚠️ Não confundir com o `rating` da rede, que é número fabricado por hash pro schema da SERP ([[afiliados.schema.rating-seed-por-site-antifootprint]]).

### Etapa 8 — criação (só com `--aplicar`)

⚠️ **Pré-condição: o CHECKPOINT DE EXCLUSÕES do passo 2 foi aprovado.** Com `--aplicar` ele **para e espera** — criar artigo é escrita, e escrever sobre uma exclusão que o usuário ainda não viu é o erro caro desta skill. Sem aprovação do checkpoint, não chame endpoint nenhum.

Mesmos endpoints dos botões do painel — `site-detail.js:3239` e `editor-artigo.html:4167`. O resultado é indistinguível de ter feito na mão.

```bash
POST /agent/site/{site}/make-reviews-stub
     { keyword, slug, products: [{asin, subtitle}] }     # 1-3 produtos

POST /agent/article/{site}/{slug}/add-products-stub
     { products: [{asin, subtitle}] }                    # 1-3 por chamada
```

`subtitle` é aceito pelos DOIS, apesar do comentário do código só documentar `{asin, badge?}` — conferido na implementação.

⚠️ **Espere entre levas e valide o campo `added` da resposta.** O `add-products-stub` tem rate-limit por artigo — `checkCooldown({ cooldownMs: 5_000 })`, ou seja **5 segundos** entre chamadas no mesmo artigo. Quando estoura, devolve `ok:false` e **a leva some em silêncio**. Se a próxima entrar, a ordem quebra. Ver Armadilha 3.

**A skill NÃO consegue gravar o título.** O endpoint recebe só `{keyword, slug, products}`, e o `buildArticleSkeleton` monta `capitalize(keyword)` — sai "Melhor Caixa De Som Jbl", sem o número e com caixa errada. Proponha um no padrão-assinatura do site (lead = campo `keyword`, número N obrigatório, ≤60 chars, tag do site) e **destaque no relatório que precisa ser colado no editor**. Em site sem artigo nenhum não há padrão pra inferir, e a escolha define a assinatura dali em diante ([[afiliados.seo.titulos-artigo-3-padroes-anti-dup]]).

Barreiras que vêm de graça do endpoint: **423** em site com edição travada, **409** se o `.mdx` já existir, e o `gateRequiresOkBibles` barrando produto sem bíblia pronta.

## O subtítulo sugerido é vinculante na prática

A `artigo-review-criar` trata subtitle vindo do stub como **direção editorial**, não placeholder (v1.34.0):

> **Ângulo VINCULANTE**: o review inteiro aborda o produto por esse ângulo. **Texto MELHORÁVEL**: liberdade de polir, mas o SENTIDO não muda.

**O papel chega no texto, e a linha do tempo é o que garante isso:**

```
CRIAÇÃO  artigo-review-criar v1.34   subtitle do stub = ângulo VINCULANTE
                                     badge só entra se o subtitle vier vazio (item 3)
              ↓  review escrito, ângulo já cumprido
AUDIT    crit. 22                    normaliza o subtitle pro keyword-first,
                                     "depois do review pronto, com visão do conjunto"
```

Então "Custo Benefício" no subtitle faz o review inteiro argumentar custo-benefício, porque a criação lê antes de o audit existir.

⚠️ **Não se assuste com a linha 599 do crit. 22**, que diz *"o ângulo que guia o REVIEW é o `badge`, não o subtitle"*. Ela contradiz a `artigo-review-criar:454` na letra, mas é justificativa mal escrita pra um comportamento correto: quando o audit roda, o review já existe, então mexer no subtitle ali é edição de SEO no heading do card, não redirecionamento editorial. Em 2026-08-01 essa linha me fez levantar um alarme falso de que o papel do lineup não chegaria no review.

Duas consequências práticas:

1. **Escreva já no formato do crit. 22** (híbrido fluindo, ≤13 palavras, sem dois-pontos, lead capitalizado emendado num gancho concreto em caixa natural). **Não porque o audit não conserta** — ele conserta, e flagra exatamente os 7 casos do checklist (lead não keyword-first · dois-pontos · repete LEAD de outro · >13 palavras · vazio · rótulo sem gancho · "em Geral" sem "Melhor"). Escreva certo porque acertar poupa uma rodada de proposta-e-aprovação, não porque errar é permanente.
2. **Todo gancho tem que sair de fato da página ou da bíblia.** Claim sem lastro faz a `artigo-review-criar` **parar e perguntar** (regra 4 dela), travando o batch. A skill escreve só o que leu.

## Armadilhas

### 1. Classificar tipo por regex no nome
**Dois erros no mesmo dia (2026-08-01).** `Liectroux i7 Pro` virou "robô" porque o nome parece de robô — é aspirador **vertical** sem fio que lava. `Kärcher VCL 1 Stick` virou "automotivo" por falso positivo de regex.

**A resposta estava na página o tempo todo**, no campo `Tipo` da tabela `specs`:

```
liectroux-i7-pro      Tipo = "Vertical sem fio"
karcher-vcl-1-stick   Tipo = "Vertical 2 em 1"  ·  Alimentação = "Elétrico com fio, cabo de 5 m"
wap-robot-w90         Tipo = "Robô aspirador 3 em 1 (varre, aspira, passa pano)"
```

⚠️ **MAS O `Tipo` É UMA AFIRMAÇÃO DA PÁGINA, NÃO UM FATO — e ele erra** (2026-08-11). A regra acima resolve o falso positivo do nome e cria um novo ponto cego: confiar cegamente no rótulo. Caso real: `britania-bas1430` declara `Tipo = "Aspirador de pó vertical com saco"` e o produto é **de arrasto**, o eliminatório literal da rubrica. Duas execuções independentes da keyword tiveram que subir pro 2º degrau pra pegar.

**Quando outro campo da MESMA página contradiz o `Tipo`, a contradição vence o rótulo.** O que denunciou, nas duas runs:

```
dimensão de corpo   32 cm · os 19 verticais reais do catálogo declaram 104-116 cm (a haste)
mangueira           "mangueira de sucção", "trava de encaixe da mangueira" (6× nas opiniões)
arquitetura         rodinhas · 2 tubos prolongadores · corpo puxado, não conduzido pela haste
tanque em litros    é a fronteira de pó-e-água, não de vertical
```

**A dimensão foi o controle mais barato** — uma linha por produto, e o outlier salta. Isso é ilustração do método, não regra de categoria: em impressora ou tablet os campos denunciadores são outros. O que transfere é **procurar contradição dentro da própria página antes de aceitar o rótulo**, e o corolário: se o `Tipo` errou aqui, ele está errado no `.mdx` e vai contaminar todo artigo futuro que confiar nele — reporte pra correção na fonte.

Os dois erros seriam evitados lendo `specs`. **Leia a tabela da página; regex no nome e no texto bruto é o que produz falso positivo.** Se o `Tipo` faltar em alguma página, aí sim caia pro `Fonte de alimentação` do `specsAmazon` da bíblia como reserva.

**O caso que mais dói:** no melhordosom, `JBL Wave Beam 2` (4.000/mês) e `JBL C50HI` (2.000/mês) são a **5ª e a 8ª** mais vendidas das 19 páginas do site, e as duas mais vendidas **entre as JBL** — e são **fones de ouvido**. Um lineup ordenado por venda sem ler a página poria um fone na primeira posição de um artigo de caixa de som. Medido de novo em 2026-08-01: os **4 primeiros do site inteiro** são fones de Philips e Samsung, todos a 5.000/mês. Ordenar por venda sem classificar tipo não erra às vezes, erra por padrão.

### 2. Confiar na consulta cega além do que ela sabe
Ela tem **duas** formas de te enganar, e a segunda só apareceu depois que eu tapei a primeira.

**2a. O MODELO.** A pergunta de modelo **saiu da Etapa 1** em 2026-08-01 justamente por isto — mas a armadilha fica registrada porque nome de modelo ainda pode aparecer solto na resposta, e a tentação de usar continua.

**2b. A FRONTEIRA DE CATEGORIA.** Em 2026-08-02, com a pergunta de modelo já removida, ela me pegou de novo por outro lado: disse que "misturar caixa de festa com portátil é o erro mais comum" dessas listas, e eu cortei a `PartyBox Ultimate` de um artigo de **caixa de som JBL**. O Marcelo repôs — cabo de energia não exclui ser caixa de som. Aposentei confiar nos nomes que ela devolve e comecei a confiar nos recortes editoriais dela, que é a mesma armadilha com roupa nova.

**A defesa é estrutural, não de atenção:** quem elimina é a **fonte**, nunca a rubrica (Etapa 3). Enquanto a eliminação exigir trecho citável do `.mdx` **ou da bíblia bruta**, nenhum juízo da rubrica corta produto sozinho — não importa quantas formas novas ela invente de soar autoritativa. A escada de degraus **amplia** essa defesa em vez de afrouxá-la: ela dá um caminho legítimo pro corte por requisito, que antes eu fazia por silêncio e sem prova nenhuma.

Ela acerta **critério** e envelhece **modelo**. Comprovado na 1ª execução: marcou `JBL Go 4` com confiança **ALTA** e **não sabia que a Go 5 existe** — uma geração atrás, exatamente onde a regra de sucessão manda o contrário. Também recomendaria "Dyson V11" e "Roomba i3", que já rodaram de geração. Nome que aparecer na rubrica é **ruído, nunca candidato**.

### 3. Assumir que a leva entrou
`add-products-stub` rate-limita por artigo. Na 1ª execução real, a leva 2 voltou `{"ok":false,"code":"rate-limited"}` e **não adicionou nada**; a leva 3 entrou normal. Reenviei a 2 depois e ela foi pro fim — os blocos 7-9 e 10-12 ficaram trocados. Espere entre chamadas e confira `added`.

### 4. Localizar o array de produtos por regex ao reordenar
**Corrompi um `.mdx` assim (2026-08-01).** Usei regex pra achar o fim do `products:` e ele parou no lugar errado: o fence `---` e o corpo do artigo foram parar no meio da lista, com 3 produtos caindo **fora do frontmatter**. O YAML continuou parseando, com 9 produtos em vez de 12.

Os limites são a **linha `products:`** e a **linha do fence `---` de fechamento**, achadas por comparação exata de linha.

E o mais importante: **validar contando o array do YAML, nunca por grep de campo.** O arquivo corrompido tinha 12 `- name:` e 12 `asin:` no grep — passava limpo — e falhava no parse. Grep mede texto; o que importa é estrutura.

### 5. Montar a tabela de memória
Abreviei "JBL PartyBox Encore Essential 2 Mic" pra "Encore Essential 2 Mic" no relatório e o Marcelo pegou. Os itens 7 e 9 do lineup eram `B0FL2QF7YJ` e `B0GT6LW2VN` — mesmo modelo com e sem microfone, nomes que diferem por uma palavra, ASINs sem nada em comum. **Sem o ASIN, uma abreviação troca um pelo outro e ninguém percebe.**

## Régua ainda NÃO exercitada

Três execuções reais até aqui, todas em 2026-08-01: `melhor caixa de som JBL` (melhordosom, marca única, site sem artigo) e `melhor air fryer 12 litros` (melhorairfryer, duas passadas).

**Já exercitadas depois da v1:**
- **Teto de reuso intra-site** — o melhorairfryer tinha 2 artigos, e o cruzamento devolveu 7 de 8 produtos já usados. Foi o que fez nascer o aviso de sobreposição.
- **Rebadge cross-marca** — nasceu do par Britânia/Philco na 3ª execução.

**Exercitado na 4ª execução** (`melhor caixa de som jbl`, melhordosom, 2026-08-02 — o pipeline de 7 etapas rodando inteiro pela 1ª vez):
- **Rubrica × catálogo** — o choque aconteceu e a rubrica **perdeu**, três vezes. Foi o que produziu a regra "quem elimina é a página".
- **Universo pelo `categorySlug`** — funcionou melhor que o previsto: excluiu os 6 fones do site sem regra nenhuma, resolvendo estruturalmente a Armadilha 1.
- **Posição 1 com dois critérios em conflito** — reportei "mais vendida × não é extremo de preço" como buraco da régua, e era **artefato do meu corte indevido**: readmitida a `PartyBox Ultimate` a R$ 7.000, a `Boombox 4` a R$ 2.400 saiu da borda e os dois critérios voltaram a concordar. Lição: antes de declarar conflito de régua, cheque se o conflito não vem de uma exclusão sua.

**Ainda sem teste:**
- **Aviso de concentração de marca** — nas quatro execuções o caso foi brand-keyword (isento) ou catálogo já diverso.
- **Cobertura multi-tipo** — nenhum dos casos exigiu um representante por tipo com link pro spoke.
- **Pré-registro de verdade** — na 4ª execução eu **já conhecia o catálogo** (era re-run da mesma keyword), então a propriedade central da Etapa 1 não foi testada. Ela vale pro sub-agent, que é isolado; não valeu pra mim.
- **Sucessão que ordena sem eliminar** — a regra nova (`Go 5 acima, Go 4 fica`) nasceu nesta execução mas não foi rodada por ela.

O caso que exercita os que faltam é o **`melhor aspirador de pó` do melhoraspirador**: 35 produtos, 5 tipos (vertical, robô, pó e água, carro, sem fio), 7 artigos planejados dividindo o mesmo catálogo.

## Buracos conhecidos, sem regra

Declarados de propósito — hoje são resolvidos por julgamento e reportados, o que é ruim de escala mas não produz erro silencioso.

- **Tamanho não tem critério de decisão.** "Mínimo 3, ideal 5/9/11, média ~9" descreve a rede, não escolhe. Na 3ª execução parei em 8 porque foi quem sobrou.
- **Catálogo pobre não tem tratamento.** Escada de preço quebrada é reportada, mas nada diz se o lineup sai assim ou se aquilo é sinal de garimpar mais produto antes.
- **Rubrica × catálogo** (acima).

## Exemplo de invocação

```
monta o lineup de melhor caixa de som jbl no melhordosom
artigo-lineup-montar melhordosom "melhor caixa de som jbl"
artigo-lineup-montar melhordosom "melhor caixa de som jbl" --aplicar
```

Args canônico: `Skill(skill="afiliados-skills:artigo-lineup-montar", args="melhordosom \"melhor caixa de som jbl\"")`
