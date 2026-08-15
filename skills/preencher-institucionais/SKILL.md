---
name: preencher-institucionais
description: Escreve as DUAS páginas institucionais EDITORIAIS de um site por nicho — /sobre/ (voz do site/marca) E /author/ (voz da pessoa, 1ª pessoa) — mantendo-as DISTINTAS (sem duplicação) e com a mesma voz. Aceita `site` (slug) OU URL do painel. Molde de ouro melhoromega3. E-E-A-T fundamentado (autor/critérios do config+niche, nunca inventado); metodologia VAGA (avaliamos/analisamos, sem alegar teste físico nem expor pesquisa de mesa); disclosure Amazon + YMYL (saúde); anti-clone cross-site (personas reusadas) e cross-página (sobre≠autor). Alinha config.author.bio; cria a página /author/ se faltar. NÃO faz contato/termos/privacidade (template+config). Backup + commit + push + sync VPS. (Substitui a antiga preencher-sobre.)
---

# Escrever as páginas institucionais EDITORIAIS (/sobre/ + /author/) por nicho

Você é o curador editorial das duas páginas institucionais que têm CONTEÚDO
EDITORIAL: **/sobre/** (sobre o site) e **/author/** (sobre a pessoa). São peças
de **E-E-A-T** (Google). As outras institucionais (contato, termos, privacidade)
NÃO entram aqui — são template + config (mecânicas/legais).

Molde de ouro: **melhoromega3** (sobre + autor). Skill-only (sem botão no painel).

## Por que UMA skill pras DUAS

/sobre/ e /author/ **compartilham a identidade do autor** e hoje **duplicam
conteúdo** (ambas tinham "Como avaliamos os produtos" + "Independência
editorial"). Duas fontes separadas geram inconsistência (uma diz "analisamos",
a outra "testamos") e conteúdo duplicado (ruim pra SEO). Uma skill só:
1. mantém a MESMA voz nas duas;
2. dá PAPÉIS DISTINTOS (site vs pessoa) → mata a duplicação;
3. centraliza a persona (nome/credencial/bio).

## Parse de input

- Slug: `impressoraideal` — OU URL do painel `site-impressoraideal.html` → extrai slug. Valida `[a-z0-9-]+`.

## Pré-requisitos

- `sites/{site}/src/config.ts` com bloco `author` (name, role, href, bio) + `contactEmail`.
- `sites-meta.json[{site}].niche`.
- `sites/{site}/src/content/pages/sobre.html` existe (stub OK).
- `/author/{slug}.html`: se NÃO existir, a skill CRIA (alguns scaffolds antigos podem não ter a página de autor).

## Invariantes

- **Faz as DUAS páginas** (sobre + autor) numa execução, com papéis distintos.
- **NÃO inventa** credencial/empresa/processo. Autor/critérios/e-mail do config + niche.
- **Metodologia VAGA**: dá impressão de análise real SEM (a) alegar teste físico ["testamos/laboratório/bancada/presencial/medimos"] NEM (b) expor pesquisa de mesa ["partimos das especificações", "lendo a ficha linha por linha", "cruzamos com opiniões de compradores"]. Use "avaliamos a fundo", "indo além da ficha técnica", "comparamos os modelos de verdade", "o que faz diferença no dia a dia". Enquadramento anti-spec OK ("não de repetir a ficha que o fabricante divulga", "nunca de uma planilha decorada de specs").
- **Disclosure Amazon** obrigatória no /sobre/ (Independência editorial).
- **YMYL** (nicho saúde): disclaimer obrigatório — /sobre/ tem "Um lembrete importante"; /author/ embute no "Meu compromisso".
- **DISTINÇÃO sobre↔autor**: a /author/ NÃO repete "Independência editorial" nem "Como avaliamos os produtos" do /sobre/. /sobre/ = o que o SITE faz; /author/ = quem a PESSOA é + como ELA trabalha (1ª pessoa).
- **ANTI-CLONE cross-site = só VOZ, nunca cobertura**: personas são reusadas (Eduardo ×9, Gustavo ×16 — medido 15/08) E sites do mesmo nicho cobrem OS MESMOS tópicos (SERP-monopoly — ex: "melhor impressora sublimática" e "plotter de recorte" vão estar em TODOS os sites de impressora). Logo é PROIBIDO diferenciar por "este site cobre X, o outro Y" — todos cobrem tudo. A diferenciação é 100% redação/ângulo/tom. Antes de gerar, LER as /sobre/ e /author/ das sites-irmãs da MESMA persona e variar a prosa (zero sequência ≥6 palavras igual). Risco máximo: mesma persona + mesmo nicho (3 creatinas do Eduardo; impressoraideal+melhorimpressora do Gustavo).
- **VOZ NATURAL (canon 2026-07-05 + bloco transversal 2026-08-15)**: o tom especialista→amigo é cumprido com **simplicidade**, não com metáfora/personificação/hipérbole. Tem que soar como PESSOA REAL explicando, não prosa literária. Ver seção **"Voz natural"** abaixo — mesma família da régua de "Voz humana" da `artigo-review-criar` (antropomorfismo=0, máx 1 coloquialismo leve).
- **`contentLocked: false`** nas duas. PT-BR editorial, tom especialista→amigo, sem travessão. **NÃO faz deploy.**

## Fluxo

1. Parse → slug.
2. **Git pull** (`git stash push -u`/pull --rebase/pop, sem engolir erro). **Chave-mestra do site:** `sites-meta.json[site].contentLocked === true` → PARE e avise (páginas institucionais são `src/content/pages`, cobertas pelo lock e pelo `pre-push`).
3. **Coleta**: config (name, domain, contactEmail, author{name,role,href→slug,bio}); niche; **subtipos do NICHO** (campo `subtipos` em chavoes-por-nicho.json[niche], OU conhecimento do nicho — **NÃO derivar dos artigos atuais**: sites do mesmo nicho convergem pra cobertura COMPLETA, então o /sobre/ descreve o escopo do nicho, não a lista de artigos de hoje; ex Impressoras: tanque, laser, multifuncional, fotográfica, sublimática, plotter de recorte, impressora para personalizados, barata); chavões do nicho; authors.json (persona). **Sites-irmãs da persona**: listar outros sites cujo `config.author.name` == este autor; ler as /sobre/ + /author/ deles (anti-clone).
4. **Stub/overwrite**: se sobre.html ou autor.html já têm conteúdo real, PERGUNTAR antes de sobrescrever.
5. **Detecta saúde/YMYL**: niche casa `/creatina|whey|pré.?treino|pre.?treino|ô?mega|omega|vitamina|suplemento|colágeno|proteína/i`.
6. **Gera /sobre/** (régua abaixo) + **/author/** (régua abaixo), distintas e variadas vs irmãs.
7. **Valida** (checklist).
8. **Backup** ambas em `.painel-backups/{dia}/`.
9. **Escreve** sobre.html + author/{slug}.html (cria o dir `author/` se faltar). **A rota/dir da rede é `/author/` (com 'h'), NUNCA `/autor/`** — o `.mdx`/`.html` vive em `src/content/pages/author/{slug}.html`, a rota é `/author/{slug}/` e `config.author.href` aponta pra lá. Gravar em `autor/` = página órfã + link 404.
10. **Alinha `config.author.bio`** pra voz vaga (sem "Testo"); mantém variado vs irmãs. **IGNORA `evaluationText`** (campo morto, não renderiza).
11. **Commit** (`--no-verify`) + **push** + `bash scripts/painel-vps-pull.sh`.
12. **Reporta**: chars de cada página, autor citado, e lembrete de que vai ao ar no deploy.

## /sobre/ — ESTRUTURA (voz do SITE)

```
<!-- contentLocked: false -->
<h1>Sobre o {Site Name}</h1>
<p> boas-vindas + o que o site faz + ESCOPO do nicho de forma NATURAL: ~4-5 subtipos representativos numa frase fluida (NÃO catálogo exaustivo de todos os tipos — empilhar 7-8 vira lista de keyword e fica torto, caso real impressoras 06-12). Incluir um aceno aos segmentos especializados (ex: sublimática/plotter pra personalizados) sem reivindicar exclusividade. Negrito nos tipos. Cuidar da elisão: "a laser"/"a de tanque" são liberadas; "da tanque de tinta" NÃO. </p>
<h2>Nossa missão</h2>          → a dor do nicho que o site resolve
<h2>Quem está por trás</h2>    → 1 parágrafo: assinado por <a href="/author/{slug}/">{Autor}</a>, {role/credencial REAL}; encaminha pra /author/. SEM duplicar a metodologia.
<h2>Como avaliamos {os/as {nicho}}</h2>  → vago-evaluativo (sem método-de-mesa) + <ul> 4-6 critérios REAIS do nicho + fecho prós/contras honestos
<h2>Independência editorial</h2>  → Amazon: comissão sem custo, nunca influencia, sem produto grátis/pagamento
<h2>Um lembrete importante</h2>   → SÓ saúde (não substitui médico/nutricionista)
<h2>Fale conosco</h2>          → e-mail {contactEmail} + <a href="/contato/">
```

## /author/ — ESTRUTURA (voz da PESSOA, 1ª pessoa) — molde melhoromega3

```
<!-- contentLocked: false -->
<h2>Como eu trabalho</h2>      → 1ª pessoa: quem sou ({role/credencial REAL do config}), por que entendo do nicho, o que faço pelo leitor. Enquadramento anti-spec ("não de repetir a ficha"). NÃO repetir o disclosure.
<h2>Como eu avalio {o/a {nicho}}</h2>  → 1ª pessoa + <ul> com 3 PRIORIDADES PESSOAIS do autor (o que ELE mais olha), NÃO a lista completa de critérios do /sobre/; redação FRESCA + "quando dá pra ir além da ficha, olho..." (vago)
<h2>Meu compromisso com você</h2>  → honestidade (aponto forte e fraco) + (SAÚDE) YMYL embutido ("não substitui orientação de médico/nutricionista")
```

- A /author/ NÃO tem "Independência editorial" nem "Como avaliamos os produtos" (isso é do /sobre/). É sobre a PESSOA.
- Credencial REAL do config.author (role/bio). Se a persona não é especialista no nicho exato, descrever honesto (redator/analista que pesquisa o nicho), NUNCA título falso.
- A página é renderizada com o cabeçalho da persona (nome/foto/bio do config) por cima pelo `AutorPageEditable.astro` — o HTML aqui é só o corpo.

## Variação obrigatória por seção (anti-footprint) — POOLS

**Por que existe:** mesmo lendo as irmãs, a geração CONVERGE nas seções semanticamente presas (assinatura, disclosure, contato, abre do "Como avaliamos", boas-vindas) — elas "têm que dizer a mesma coisa", então saem com a MESMA redação em todos os sites da persona. Caso real (melhorairfryer vs cozinhaideal, 2026-06-27): mesmo com a régua anti-clone, colaram em 5 pontos — assinatura ("O conteúdo daqui é assinado por… É ela quem…"), abre do "Como avaliamos" ("avaliamos a fundo o que ele entrega…"), critério de custo ("o que você paga com o que…"), disclosure ("de graça em troca de elogio") e contato ("use a nossa página de contato"). A leitura não pegou; só o check de 6-gramas. A correção é **variar de propósito**, rotacionando um molde DIFERENTE por site nas 6 seções de risco.

**Regra:** pra CADA seção abaixo, escolha um molde da família que NENHUMA irmã da persona já usou (leia as irmãs no passo 3). É a ESTRUTURA da frase que varia, não só sinônimo solto. Os pools são sementes — gere fresco a partir deles, não copie verbatim.

- **Boas-vindas (§1 do /sobre/):** "Que bom ter você por aqui." / "Bem-vindo ao {Site}." / "Se você chegou até aqui, é porque…" / "{Site} existe por um motivo simples:" / (abre direto pela dor, sem saudação).
- **Assinatura ("Quem está por trás"):** "O conteúdo daqui é assinado por {Autor}…" / "Cada análise leva a assinatura de {Autor}…" / "Quem escreve por aqui é {Autor}…" / "Por trás das recomendações está {Autor}…". O 2º movimento ("é ela quem decide…") também rotaciona: "É dela a palavra final sobre…" / "É quem define o que entra na lista…" / "Cabe a ela escolher…". O encaminhamento para /author/ varia também: "vale dar uma passada na página dela" / "é só abrir a página da autora" / "conheça o método dela na página de autor".
- **Abre do "Como avaliamos":** "Antes de indicar qualquer modelo, avaliamos…" / "Cada recomendação passa por uma análise de…" / "Toda indicação aqui nasce de…" / "Para entrar na lista, o modelo é avaliado por…". (Mantém vago-evaluativo + anti-spec; só muda a estrutura.)
- **Critérios (a redação de cada `<li>`):** o CONCEITO repete entre sites (custo, capacidade, etc. são os mesmos), mas a FRASE de cada bullet varia. Ex. custo: "pesando o preço contra o uso real" / "equilibrando o valor com o que você de fato vai usar" / "se o preço compensa no uso do dia a dia".
- **Disclosure (parte NÃO-Amazon):** o nome "Programa de Associados da Amazon Brasil" é fixo (citação), mas a prosa ao redor varia: "podemos ganhar uma pequena comissão, sem custo a mais para você" / "recebemos uma porcentagem da compra, e o preço para você não muda" / "ganhamos uma comissão da loja, nunca do seu bolso". A parte do "não aceito brinde/pagamento" idem: "não aceito aparelho cortesia em troca de resenha boa" / "nenhum fabricante paga para subir na lista" / "produto grátis não garante elogio aqui".
- **Fecho ("Fale conosco"):** o e-mail é fixo, mas o convite e o link variam: "mande sua mensagem pela página de contato" / "fale com a gente pela página de contato" / "passe pela página de contato". NUNCA repetir "use a nossa página de contato" se uma irmã já usa.

## Voz natural (régua transversal, canon Marcelo 2026-08-15 — bloco IDÊNTICO nas 5 skills de criação e nos prompts canônicos do painel)

Especialista explicando a um amigo, cumprido com **simplicidade**, não com efeito. Pergunta-teste: *"um amigo que não entende disso entenderia e saberia o que fazer?"* Sem jargão corporativo, sem formalidade institucional, **sem sacada**.

O que faz texto soar como IA não é gíria nem termo técnico: é **palavra comum usada fora do sentido do dicionário** ("resolver a casa", "dar conta da poeira", "transformar a limpeza numa produção", "o aparelho pede tomada", "a conta da potência vem no peso"), quase sempre frase feita do inglês vertida (*make a production, handle, delivers, covers, calls for, the math*). Cada palavra é comum, então lista de termo não pega; a régua é uma **classe**:

1. **Sujeito concreto + verbo no sentido do dicionário.** Aspirador aspira, impressora imprime, bateria dura, produto custa/tem/funciona. Objeto, preço, peso ou potência NÃO "resolvem, dão conta, entregam, seguram, pedem, exigem, aguentam, sustentam, encaram, cobram, juntam, trabalham, cobrem, viram, brilham". Teste: é o sentido em que você usaria a palavra falando com um cliente?
2. **Substantivo literal.** Nada de "a conta", "degrau", "piso", "porta de entrada", "pacote", "proposta", "produção", "remanejo", "trunfo", "fôlego" como figura. Diga o que é (preço, faixa de preço, o mais barato, conjunto de recursos).
3. **Sem frase-sacada.** Nada de "não é X: é Y", "o que X é Y", "é aí que…", fecho com dois-pontos que "revela". Dois-pontos só para explicação ou lista.
4. **Repita a palavra certa.** "Aspira" 3× é normal. Chavão é frase-molde repetida, não palavra exata. **Nunca troque a palavra certa por sinônimo figurado para "variar"** (limpar → "resolver a casa" → "dar conta" é exatamente o defeito).
5. **"para", não "pra"**, no texto público.
6. **Frase de até ~30 palavras.** ", então" e ", o que" no máximo 1 por parágrafo.
7. **Fecho de parágrafo = frase curta de fato ou recomendação direta** ("é a melhor opção para casa pequena"), sem rótulo de público engatado ("é a escolha de quem", "faz sentido para quem", "é o que resolve").
8. **Ênfase só com dado.** Sem "de verdade", "bastante", "com folga", "de sobra", "justamente", "honesto/a" como muleta.
9. **Continuam valendo (v1.32):** rótulo de categoria só se existe no varejo (teste-da-Amazon: "máquina de trabalho"→"impressora de escritório", "preço de custo-benefício"→"preço justo"); elipse de categoria LIBERADA ("a barata", "a laser", "as de tanque"); sem meta-SEO (não comente a busca do leitor); sem jargão financeiro/burocrático ("desembolso"→"preço"); sem atribuição elíptica ("conta da Epson"→número direto); sem antropomorfismo ("não se cansa", "no batente"); no máximo 1 expressão coloquial leve, e só se for a forma mais direta.

10. **Teto mecânico da mesma régua**: `docs/painel/_data/chavoes-por-nicho.json` → `_genericos.naturalidade_max` (daqui 2, pede 3, resolve 3, entrega 3, de verdade 1, trunfo/fôlego 1…) e `naturalidade_banidos` (0). A auditoria conta por artigo (página = metade); escreva já dentro do teto.

**Antes de gravar, releia cada parágrafo: "uma pessoa escreveria assim?"** O trecho que soa esperto, simplifique.

| ❌ Como saiu (casos reais) | ✓ Como uma pessoa escreve |
|---|---|
| a impressora resolve o mês inteiro com um kit | um kit de tinta imprime cerca de 4.500 páginas |
| sem transformar a troca de tinta numa produção | sem muito esforço |
| a conta do rendimento vem no preço do kit | o rendimento alto tem um custo: o kit é caro |
| a creatina pede coqueteleira | a creatina dissolve melhor com coqueteleira |
| Se não tem, ela é a que resolve. | Se não tem, ela é a melhor opção. |
| O tanque não se cansa. | O tanque de tinta rende o mesmo até o fim. |

⚠️ **Os exemplos são de outra categoria de propósito e NÃO podem ser reusados.** Se a frase que você escreveu está nesta tabela (ou nos exemplos de shortDescription), reescreva com o fato do SEU produto. Caso real (melhoraspirador, 15/08): a linha "em casa grande você ainda troca de tomada algumas vezes", que era exemplo aqui, saiu copiada em 5 lugares do artigo — 11 sub-agents lendo o mesmo exemplo convergem nele.
**Caso que disparou a régua nesta skill (2026-07-05, /author/ do tabletparatrabalho, REJEITADO):** "esse aparelho só parece firme na vitrine", "o que muda quando o aparelho **encara** e-mail", "como se isso, sozinho, **resolvesse a sua vida**", "aquele conhecido que já **garimpou tudo antes de você abrir a carteira**", "**tenho birra** de ficha". Reescrita aprovada: *"o que quero saber é direto: ele funciona bem num expediente inteiro? Não me prendo só ao número do processador ou à quantidade de memória, porque uma ficha técnica cheia nem sempre significa um bom aparelho no uso."* Vale nas DUAS páginas, com risco maior na /author/ (1ª pessoa tenta "dar personalidade" e escorrega pro personagem).

⚠ **A reescrita naturalizadora RECOLA nas irmãs** (frase direta converge entre sites da mesma persona) — depois de naturalizar, RODE DE NOVO o gate de 6-gramas vs cada irmã (caso real 2026-07-05: 7 colisões novas que só o re-run pegou). Naturalizar e anti-clone são o MESMO loop.

## Régua de CONTEÚDO (as duas)

- Allowlist HTML: `h1`(só sobre), `h2`, `h3`, `p`, `ul`, `ol`, `li`, `strong`, `em`, `a`. Nada mais.
- Tamanho: /sobre/ 2800-4300 chars (alvo ~3200-3500); /author/ 1200-2400 chars (alvo ~1600).
- Sem travessão (—/–). Sem ponto-e-vírgula (;) (régua 2026-06-20: tem cara de IA; troque por "." ou ","). Sem superlativos/absolutos sem evidência.
- E-mail do config.contactEmail; link `/contato/` no fecho do sobre; link `/author/{slug}/` no "Quem está por trás" do sobre.

## Checklist de validação

- [ ] /sobre/: H1 + Missão + Quem está por trás + Como avaliamos + Independência (+ YMYL se saúde) + Fale conosco.
- [ ] /author/: Como eu trabalho + Como eu avalio + Meu compromisso (1ª pessoa).
- [ ] /author/ NÃO tem "Independência editorial" nem "Como avaliamos os produtos" (sem duplicar o sobre).
- [ ] Disclosure Amazon no /sobre/. YMYL nas duas se saúde.
- [ ] Autor = config.author (nome + /author/{slug}/ corretos). E-mail = config.contactEmail.
- [ ] SEM "testamos/laboratório/bancada/presencial/medimos".
- [ ] SEM método-de-mesa ("partimos das especificações", "linha por linha", "cruzamos com opiniões").
- [ ] **Voz natural** (canon 2026-07-05): sem metáfora rebuscada, personificação forçada ("o aparelho encara"), hipérbole ("resolvesse a sua vida") nem clichê-narrativo ("garimpou tudo antes de você abrir a carteira"). Leu em voz alta e soou pessoa real, não prosa literária. Ver seção "Voz natural".
- [ ] Variado vs irmãs da mesma persona (zero sequência ≥6 palavras igual). **GATE EM LOOP, não checagem única:** rode o check de 6-gramas vs CADA irmã; pra cada overlap que NÃO seja a citação Amazon ("Programa de Associados da Amazon Brasil") nem a credencial-fato do autor, **reescreva o trecho (rotacionando o pool da seção) e RODE DE NOVO**. Repita até sobrar só os grams permitidos. ⚠ Cuidado pra a reescrita não criar colisão NOVA com outra irmã (caso real 2026-06-27: reescrevi o contato e bati noutra irmã no "use a nossa página de contato"; só o re-run pegou) — por isso é loop, não passada única.
- [ ] sobre↔autor do MESMO site: zero frase verbatim copiada (overlap de TÓPICO ok; o /author/ usa 3 prioridades pessoais, NÃO espelha a lista de critérios do /sobre/). **VERIFICAR PROGRAMÁTICO** com check de 6-gramas (set de tuplas de 6 palavras de cada página; interseção deve ser 0) — fácil escapar na leitura manual (caso real 06-12: o fecho "se um modelo imprime devagar, tem tinta cara..." foi copiado do /sobre/ no "Meu compromisso" do /author/ e só o check de 6-gramas pegou).
- [ ] HTML só na allowlist; sem travessão; tamanhos OK.

## Armadilhas

1. **Duplicar sobre↔autor** (caso real: 12 sites tinham "Como avaliamos os produtos"+"Independência" iguais nas duas) — autor é PESSOA/1ª pessoa, sobre é SITE. Papéis distintos.
2. **Alegar teste físico** — proibido explícito.
3. **Expor método de mesa** (caso real impressoraideal 2026-06-12) — "lendo as especificações linha por linha", "cruzamos com opiniões" fazem parecer que não houve análise. Evaluativo-vago + anti-spec framing.
4. **Footprint cross-persona** — Eduardo ×9 (3 creatinas mesmo nicho), Gustavo ×16 (medido 15/08) (2 impressoras). Sites da mesma persona+nicho com autor/sobre colados = footprint. As bios já são variadas por site; estender a variação pra sobre+autor. LER as irmãs antes. **RODAR o check de 6-gramas TAMBÉM cross-site** (novo site vs cada irmã da mesma persona) — caso real melhorimpressora vs impressoraideal 06-12: escaparam "e para quem cada um compensa" (critério) e "mercado brasileiro, como Epson e HP" (intro), só o check pegou. PODEM repetir (não são footprint): o **nome "Programa de Associados da Amazon Brasil"** (citação obrigatória) e a **credencial real do autor** ("redator especialista em home office" — é fato, mesma pessoa). NÃO podem: prosa do disclosure (varie "comissão sobre as compras..."), critérios, missão, intro.
5. **Inventar credencial** — usar role/bio reais do config; honesto se não for especialista do nicho.
6. **Esquecer YMYL** em saúde (sobre "Um lembrete importante" + autor "Meu compromisso").
7. **/author/ inexistente** — criar o dir + arquivo (melhoraspirador, melhorcozinha).
8. **HTML fora da allowlist** / travessão.
9. **Voz de personagem / prosa literária** (caso real tabletparatrabalho 2026-07-05) — a /author/ saiu com "só parece firme na vitrine", "o aparelho encara e-mail", "como se isso resolvesse a sua vida", "garimpou tudo antes de você abrir a carteira". Rejeitada. Voz natural = frase direta e concreta (ver seção "Voz natural"). Risco maior na 1ª pessoa da /author/.

## Exemplo de invocação

- `Skill(skill="preencher-institucionais", args="impressoraideal")`

## Disciplina de release

Nasce no project repo. Marketplace só após validar num run real (sobre+autor de
1 site). Substitui a `preencher-sobre` (que era só metade).

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
