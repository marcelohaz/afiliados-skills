---
name: artigo-clonar-fila
description: Roda uma FILA de clones de artigo (N artigos, um após o outro), reusando a skill artigo-clonar-em-massa por item — nunca reimplementa o pipeline. Recebe uma lista de comandos /artigo-clonar-em-massa (a que o botão "▶ Copiar fila" do painel gera) OU uma lista de {targetSite, source, title}. Executa em SEQUÊNCIA, 1 artigo isolado por vez, com git-verdade pra pular os que já foram feitos, clone-log como gate por artigo (verify + verify-output), e relatório consolidado no fim. Timer opcional via ScheduleWakeup ("rode daqui a 3h"). NÃO faz deploy. NÃO trava artigos. Para em "todos commitados + buildados + relatório".
---

## O que esta skill É (e não é)

É a **camada FILA** acima da `artigo-clonar-em-massa`. Enquanto a `artigo-clonar-em-massa` clona **1 artigo** (com N produtos), esta roda **N artigos em sequência**.

- **REUSA `artigo-clonar-em-massa` por item — NUNCA reimplementa o pipeline.** Cada artigo passa pelas Etapas 0→6 daquela skill (pré-flight, reviews biblia-only, gates 1.2/1.3, HARD GATE 1.4, guide, intro+meta, HARD GATE 4 readyToLock, comparador, faq-shuffle, build, commit). Se a `artigo-clonar-em-massa` evoluir, a fila herda de graça (mesmo princípio anti-drift do resto da rede).
- **Se o Skill tool estiver disponível**: invoca `Skill(skill="afiliados-skills:artigo-clonar-em-massa", args="...")` por item. **Se não** (raro): fallback canônico — `Read .claude/skills/artigo-clonar-em-massa/SKILL.md` e executa o pipeline dela por item (ver CLAUDE.md #4 + regra anti-cache).
- **NÃO é a IA do painel.** O painel só GERA a fila (botão "▶ Copiar fila" na seção "Artigos recomendados" → um comando por linha). Quem EXECUTA com qualidade é o Claude Code (assinatura, Opus). O `clone-article` por API key do painel é o caminho vestigial/inferior — não é este.
- **NÃO faz deploy** (mesma régua da `artigo-clonar-em-massa`). Para em "commitado + buildado".

## Modelo

Opus 4.8 (ou mais novo). Sub-agents das etapas herdam o modelo da sessão. NUNCA Sonnet/Haiku.

## Parse de input

Aceita 2 formatos:

**A) Bloco de comandos** (o que o botão "▶ Copiar fila" do painel gera — um por linha):
```
/artigo-clonar-em-massa amelhorimpressora SOURCE=escritorioecasa/impressora-para-personalizados TITLE="As 5 Melhores Impressoras para Personalizados (Guia 2026)" HOME=no MODE=biblia-only
/artigo-clonar-em-massa amelhorimpressora SOURCE=escritorioecasa/impressora-sublimatica TITLE="..." HOME=no MODE=biblia-only
/artigo-clonar-em-massa amelhorimpressora SOURCE=escritorioecasa/melhor-impressora-epson TITLE="..." HOME=no MODE=biblia-only
```
Parse: cada linha começando com `/artigo-clonar-em-massa` vira 1 item da fila. Ignora linhas em branco/comentário.

**B) Token de agendamento** (opcional): a 1ª linha pode ser `/artigo-clonar-fila iniciar-em=Nmin` (N em minutos — é o que o modal "▶ Agendar fila" do painel emite, ex.: `iniciar-em=90min`). Parse determinístico do `iniciar-em=(\d+)min` → agenda com `ScheduleWakeup(N*60)` (ver Timer). Sem token, ou `iniciar-em=0min`, ou linguagem natural ("daqui a 3h") = roda já / interpreta o delay. Sempre prefira o token `iniciar-em=Nmin` (robusto; não parsear "2 horas e meia").

O `TITLE=` de cada linha é HINT: a `artigo-clonar-em-massa` tem HARD GATE que DESCARTA e normaliza pro padrão-assinatura do DESTINO. A fila NÃO precisa tratar título.

## Invariantes

- **1 artigo por vez, em SEQUÊNCIA (não paralelo).** Clonar 2 artigos em paralelo mistura commits e disputa o git. A fila é serial; o paralelismo já existe DENTRO de cada artigo (os N sub-agents de review da Etapa 1.1).
- **git-verdade antes de cada item (idempotência):** `git log --oneline -- sites/{target}/src/content/reviews/{slug}.mdx`. Se já tem commit → **PULA** (marca "já feito" no relatório). Se existe `.mdx` não-commitado → regenera (trabalho interrompido). Re-rodar a fila é seguro.
- **clone-log como gate POR ARTIGO (obrigatório):** `bun scripts/clone-log.ts init {t} {slug} --source=...` no começo; `check` a cada etapa; `verify` (etapas rodaram, hard-gates 1.4+4) E `verify-output --source={sourceSite}` (o .mdx saiu certo **e** não duplica a fonte) ANTES de commitar. `verify` exit 1 = NÃO fechar aquele artigo.
- **Erro em 1 não derruba a fila.** Item que falha/não-converge vira "⚠ revisar" no relatório; a fila SEGUE pro próximo. Nada ruim é escondido.
- **NÃO faz deploy. NÃO trava** (`contentLocked` fica false). Commit direto em `main` (régua do projeto). Sub-agents NUNCA fazem git — a skill-mãe/loop controla.
- **Isolamento cross-nicho:** cada artigo é biblia-only e isolado; a fila nunca compartilha contexto entre artigos (evita vazar nicho de um pro outro).
- **Cap de segurança:** se a fila tiver > 10 itens, avise o custo (~10-15 sub-agents Opus por artigo) e confirme antes de começar. Abaixo disso, roda direto (o painel já é o ponto de seleção consciente).

## Pipeline

### Etapa F0 — Parse + plano
1. Parse do input (formato A ou B). Extrai a lista de itens `{target, source, slug, titleHint}` + delay do timer (se houver).
2. `git pull --rebase origin main` (evita estado stale; painel/Bárbara commitam em paralelo).
3. Para cada item: **git-verdade** (`git log -- .../{slug}.mdx`). Classifica: `FAZER` / `PULAR (já commitado)` / `REGERAR (.mdx órfão)`.
   - **RETOMADA POR ETAPA (não por artigo):** pra todo item que NÃO for `PULAR`, leia também `docs/biblias-v2/.audits/clone-runs/{target}-{slug}-last.md`. Se ele já tem etapas marcadas, **retome da primeira etapa NÃO marcada** em vez de recomeçar do zero. A git-verdade sozinha tem granularidade de ARTIGO: um item que morreu depois de 8 de 10 reviews volta a `FAZER` e joga fora 8 sub-agents Opus. O clone-log já registra etapa por etapa — só precisa ser lido. Marque no plano como `RETOMAR (etapa X)`.
     - ⚠️ Isso só funciona porque a `artigo-clonar-em-massa` grava os reviews em `<scratchpad>/rev-{slug}.json` na Etapa 2.5 dela, antes de marcar o `check 1.1`. Se o item estiver marcado em 1.1 mas o arquivo não existir (run antigo, anterior a essa régua), **trate como `FAZER`** e recomece o item — não tente retomar em cima de estado que não está no disco.
   - Isso também é o que torna o despertar do heartbeat seguro: sem ele, um despertar que caia no meio de um item provoca exatamente o restart que ele deveria evitar.
4. Mostra o plano (tabela item → status + estimativa). Se > 10 itens, confirma custo. **Informe o total em horas** (~1 artigo/hora medido) e que a sessão precisa ficar aberta.
5. **Se ZERO itens em `FAZER`/`REGERAR`/`RETOMAR`** → `ScheduleWakeup(stop: true)` e vá direto ao F2 (a fila acabou; sem isso o heartbeat reagenda pra sempre). Senão, arme o heartbeat (ver Timer) e siga F1.

### Etapa F1 — Loop sequencial (por artigo)
Para cada item `FAZER`/`REGERAR`/`RETOMAR`, EM ORDEM:
0. **Arme o heartbeat**: `ScheduleWakeup(1800)` com o bloco da fila como `prompt` (ver Timer). É o passo 0 porque tudo depois dele depende do turno continuar vivo.
1. `bun scripts/clone-log.ts init {target} {slug} --source={source}` (pule se estiver RETOMANDO — o log já existe e apagá-lo perde o progresso).
2. Roda a `artigo-clonar-em-massa` para o item (Skill tool OU fallback lendo a SKILL.md). Marca cada etapa com `clone-log.ts check {target} {slug} {etapa} "{detalhe}"` conforme conclui (**0, 1.0, 1.1, 1.2, 1.3, 1.4, 2, 2.2, 3, 3.2, 4, 5, 5.4, 6.3.5, 6**). ⚠ A lista ganhou **1.0** (lineup+shuffle), **5.4** (re-gate) e **6.3.5** (FAQ-shuffle) em 2026-08-10 — elas existiam no pipeline e não no checklist. **As três são `soft`: registram, mas NÃO reprovam o `verify`.** É de propósito: o script viaja por `git pull` e as skills por marketplace, então quem puxar o script novo sem atualizar o plugin não pode travar no meio de uma fila. A proteção do badge continua onde sempre esteve (auto-check do assembler + `badge-ausente` como `error` na `artigo-auditar`). `6.3.5` aceita `N/A` quando não há irmão na keyword.
   - Os HARD GATES (1.4 artigo-reviews-auditar, 4 artigo-auditar → readyToLock) são obrigatórios — a `artigo-clonar-em-massa` já os roda; a fila só confirma via clone-log.
3. ANTES do commit do item (Etapa 6 da clone): `bun scripts/clone-log.ts verify-output {target} {slug} --source={sourceSite}` **PRIMEIRO** (ele grava a verificação mecânica no log) **e depois** `bun scripts/clone-log.ts verify {target} {slug}`, que agora **reprova se essa seção estiver vazia** — sem ela o log seria só autorrelato (artefato ok **e** zero frase exata fora dos H2-slot vs a fonte?). Qualquer um exit 1 → NÃO commita; tenta resolver (auto-fix da etapa faltante) ou marca "⚠ revisar" e segue.
4. Commit/push/gen/VPS do item (a própria `artigo-clonar-em-massa` faz isso na Etapa 6). VPS git-jam → retry (armadilha conhecida).
5. Cross-check pós-item (memória `afiliados.fluxo.crosscheck-obrigatorio-pos-batch-paralelo`): confirma que o `.mdx` está no `git log` e o build passou.
6. Próximo item.

### Etapa F2 — Relatório consolidado
Tabela por artigo: `commit | readyToLock (via clone-log) | verify-output | comparador (exatas/near≥.8) | título`. Lista os PULADOS (já feitos) e os "⚠ revisar" (não-convergidos), com o porquê. Aponta que NADA foi deployado (aguarda aprovação humana).

## Timer + HEARTBEAT (ScheduleWakeup) — obrigatório, não opcional

**Atraso de início** (opcional): se a 1ª linha trouxer `iniciar-em=Nmin` (N>0), agende com `ScheduleWakeup(N*60)` passando de volta a MESMA instrução (o bloco inteiro). Teto de 3600s por salto: pra N>60, encadeie saltos até o alvo. NUNCA agende deploy.

**Heartbeat durante a execução** (SEMPRE, mesmo sem `iniciar-em`): ⚠️ **a fila só avança enquanto o turno do agente está vivo. Nada roda entre turnos.** Se o turno acabar por qualquer motivo — compactação de contexto, erro de ferramenta, cota, ou decisão de parar pra relatar — a fila **morre em silêncio e nunca mais volta**, a não ser que exista um despertar pendente. Por isso:

1. **Arme `ScheduleWakeup(1800)` no topo de CADA item**, com o bloco da fila como `prompt`.
2. **Arme de novo como PRIMEIRO ATO de todo turno nascido de um despertar**, antes de qualquer outra coisa. Comportamento observado (3 disparos encadeados, 2026-07-30): há **um único** despertar pendente por vez e cada chamada substitui a anterior — a resposta da ferramenta diz "Next wakeup scheduled", no singular. Ou seja, um despertar consumido no meio de um item deixa a janela aberta até você re-armar. Acordar sem re-armar = voltar ao estado sem rede.
3. **Encerre explicitamente** em QUALQUER uma destas três saídas, sempre com `ScheduleWakeup(stop: true)`:
   - **Fila terminou**: a F0 classificou **ZERO** itens como `FAZER`/`REGERAR`/`RETOMAR`. Chame o `stop` **antes** do relatório F2. Sem isso o despertar pendente dispara depois do fim, acha tudo commitado e reagenda pra sempre.
   - **⚠️ O usuário pediu pra parar, pausar, ou interrompeu a fila.** Com heartbeat armado a fila volta sozinha no próximo fim de turno — inclusive depois de você só responder uma pergunta dele. Se ele mandou parar, `stop: true` **na hora**, e diga que a fila está parada e como retomar (re-colar o bloco). Sem isso você ressuscita um trabalho que ele acabou de interromper.
   - **Aborto do pré-flight** (site inexistente, bíblia incompleta, zero itens válidos): `stop: true` junto com a mensagem de aborto.

Por que 1800s e não o teto de 3600: com o resume por etapa (F0 passo 3), despertar espúrio é barato — ele só relê o clone-log e continua de onde parou. Metade do intervalo = metade do tempo morto máximo quando a queda é real.

### ⚠️ CIRCUIT BREAKER — o heartbeat não pode virar loop infinito de tentativa

Heartbeat sem freio é pior que sem heartbeat: se a causa da queda for **persistente** (cota estourada às 3h, git-jam, bíblia corrompida), ele te acorda a cada 30 min pra falhar de novo, a noite inteira, queimando ciclo e sem ninguém pra ver. Obrigatório:

1. **Meça progresso entre despertares.** Guarde em `<scratchpad>/fila-{target}-heartbeat.json` a assinatura de progresso: `{itensCommitados, etapasMarcadasNoItemEmCurso, streakSemProgresso}`. A cada despertar, recalcule e compare com a gravada.
2. **Sem progresso = streak++.** Progresso (um commit novo OU uma etapa nova no clone-log) zera o streak.
3. **`streakSemProgresso >= 3`** (≈1h30 sem sair do lugar) → **`ScheduleWakeup(stop: true)`** e escreva o F2 dizendo em que item travou, qual o erro observado e que a fila está PARADA aguardando decisão humana. Não tente pra sempre.
4. **Falha de cota dentro do turno**: se os sub-agents morrerem com erro de limite de sessão, **PARE de disparar sub-agents nesse turno** na hora (não gaste os que faltam falhando um a um), registre no clone-log e deixe o heartbeat tentar mais tarde — a cota volta sozinha, o turno não. Isso conta como "sem progresso" pro streak.

Caso real que motiva: em 2026-07-30, de madrugada, o limite de sessão matou 10 sub-agents de uma vez num batch. Uma fila de 7 artigos dispara ~70-105 sub-agents Opus — bater o teto no meio da noite é cenário provável, não exótico.

- ⚠️ **É in-session**: a sessão do Claude Code precisa ficar ABERTA — o `ScheduleWakeup` dorme e acorda DENTRO da sessão. O painel só GEROU o comando agendado; ele não executa nada. Se o usuário fechar tudo esperando rodar sozinho, NÃO roda (deixe isso claro se ele perguntar).
- **Dimensione a expectativa antes de prometer:** throughput medido em run real (compraguia, 2026-07-30) foi de **41 a 55 min por artigo** (4 a 10 produtos), ou seja **~1 artigo/hora**. Fila de 10 = corrida de **~9 horas** com a sessão aberta o tempo todo. Isso NÃO cabe num turno só — é justamente por isso que o heartbeat é obrigatório, e não uma preferência. Diga o número de horas ao usuário ao imprimir o plano.
- **NÃO** existe (por ora) execução headless disparada pelo painel (cron na VPS → `claude`). Se um dia existir, é projeto separado com os riscos de rodar sem supervisão (custo, gate travado/git-jam às 3h). Ver a análise em memória.

### Caso real que originou esta régua (2026-07-30)
Fila de 10 artigos pro compraguia. A régua antiga dizia "rode a fila inteira num disparo só (ou re-arme por item **se quiser** heartbeat)". Rodei num disparo só: itens 1 e 2 commitados às 11:15 e 12:10, e aí o turno terminou (parei pra dar um checkpoint). **A cadeia de saltos já tinha sido inteiramente consumida no início**, nenhum despertar ficou pendente, e a fila ficou parada 1h09 até o usuário perguntar. Nada falhou — não houve erro, cota nem sub-agent morto. O default documentado simplesmente não sobrevive a um fim de turno, e num tamanho de fila que a própria skill autoriza sem confirmação (10) o fim de turno é **certo**.

## Armadilhas (embutir)

1. **Paralelizar artigos** — NÃO. Serial. O paralelismo é intra-artigo (reviews da Etapa 1.1).
2. **Pular git-verdade** — re-rodar a fila re-clona o que já existe e duplica trabalho/commits. Sempre checar `git log` por item.
3. **Fechar sem os 2 gates** — `verify` (etapas) E `verify-output` (artefato) ANTES do commit. Um sem o outro deixa passar (etapas marcadas mas .mdx quebrado, ou .mdx ok mas hard-gate pulado).
4. **TITLE do painel** — ⚠️ **é SEMPRE o título de um site IRMÃO, nunca da fonte.** O painel embute `data-title = g.title` (o título do gap, vindo de um peer qualquer) em `_pages/site-detail.ts`, enquanto o `pickSource` escolhe a fonte por outro critério (canônica do nicho → live-first → alfabético). Os dois são **decoupled**, então o HARD GATE da `artigo-clonar-em-massa` é obrigado a descartar o TITLE em 100% dos casos. Trate como ruído: **não grave o literal e não perca tempo avaliando**. (Caso real 2026-07-30: os 10 TITLE= da fila do compraguia eram os títulos do `escritorioecasa` verbatim, com `SOURCE=escritoriocasa`.)
5. **Deploy** — NUNCA na fila/timer. Para em commitado+buildado.
6. **VPS git-jam** (ref lock) — retry; não é erro fatal (o commit em `main` é a fonte da verdade).
7. **Achar que a fila "roda sozinha"** — não roda. Entre turnos NADA acontece. Sem o heartbeat re-armado (Timer), qualquer fim de turno mata a fila em silêncio, sem erro nenhum no log. Foi assim que a fila do compraguia parou 1h09 no item 2.
8. **Encerrar sem `ScheduleWakeup(stop: true)`** — deixa despertar pendente reagendando pra sempre depois que a fila acabou.
9. **Retomar por artigo em vez de por etapa** — joga fora até 10 sub-agents Opus de trabalho. O clone-log tem o estado por etapa; leia-o na F0.

## Disciplina de release

Nasce no project repo. Vai pro marketplace (`marcelohaz/afiliados-skills`) junto da próxima release relevante (ver `feedback_skill_regua_release_junto`). Validar num run real antes.

## Invocação

```
/artigo-clonar-fila
<cola aqui o bloco de comandos do botão "▶ Copiar fila" do painel>
```
Ou com timer: "daqui a 3 horas: {bloco}".
