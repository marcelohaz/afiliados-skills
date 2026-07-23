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
- **clone-log como gate POR ARTIGO (obrigatório):** `bun scripts/clone-log.ts init {t} {slug} --source=...` no começo; `check` a cada etapa; `verify` (etapas rodaram, hard-gates 1.4+4) E `verify-output` (o .mdx saiu certo) ANTES de commitar. `verify` exit 1 = NÃO fechar aquele artigo.
- **Erro em 1 não derruba a fila.** Item que falha/não-converge vira "⚠ revisar" no relatório; a fila SEGUE pro próximo. Nada ruim é escondido.
- **NÃO faz deploy. NÃO trava** (`contentLocked` fica false). Commit direto em `main` (régua do projeto). Sub-agents NUNCA fazem git — a skill-mãe/loop controla.
- **Isolamento cross-nicho:** cada artigo é biblia-only e isolado; a fila nunca compartilha contexto entre artigos (evita vazar nicho de um pro outro).
- **Cap de segurança:** se a fila tiver > 10 itens, avise o custo (~10-15 sub-agents Opus por artigo) e confirme antes de começar. Abaixo disso, roda direto (o painel já é o ponto de seleção consciente).

## Pipeline

### Etapa F0 — Parse + plano
1. Parse do input (formato A ou B). Extrai a lista de itens `{target, source, slug, titleHint}` + delay do timer (se houver).
2. `git pull --rebase origin main` (evita estado stale; painel/Bárbara commitam em paralelo).
3. Para cada item: **git-verdade** (`git log -- .../{slug}.mdx`). Classifica: `FAZER` / `PULAR (já commitado)` / `REGERAR (.mdx órfão)`.
4. Mostra o plano (tabela item → status + estimativa). Se > 10 itens, confirma custo.
5. Se veio timer → `ScheduleWakeup` com o delay e re-entra nesta skill no disparo (ver Timer). Senão segue F1.

### Etapa F1 — Loop sequencial (por artigo)
Para cada item `FAZER`/`REGERAR`, EM ORDEM:
1. `bun scripts/clone-log.ts init {target} {slug} --source={source}`.
2. Roda a `artigo-clonar-em-massa` para o item (Skill tool OU fallback lendo a SKILL.md). Marca cada etapa com `clone-log.ts check {target} {slug} {etapa} "{detalhe}"` conforme conclui (0, 1.1, 1.2, 1.3, 1.4, 2, 2.2, 3, 3.2, 4, 5, 6).
   - Os HARD GATES (1.4 artigo-reviews-auditar, 4 artigo-auditar → readyToLock) são obrigatórios — a `artigo-clonar-em-massa` já os roda; a fila só confirma via clone-log.
3. ANTES do commit do item (Etapa 6 da clone): `bun scripts/clone-log.ts verify {target} {slug}` (etapas ok?) **E** `bun scripts/clone-log.ts verify-output {target} {slug}` (artefato ok?). Qualquer um exit 1 → NÃO commita; tenta resolver (auto-fix da etapa faltante) ou marca "⚠ revisar" e segue.
4. Commit/push/gen/VPS do item (a própria `artigo-clonar-em-massa` faz isso na Etapa 6). VPS git-jam → retry (armadilha conhecida).
5. Cross-check pós-item (memória `afiliados.fluxo.crosscheck-obrigatorio-pos-batch-paralelo`): confirma que o `.mdx` está no `git log` e o build passou.
6. Próximo item.

### Etapa F2 — Relatório consolidado
Tabela por artigo: `commit | readyToLock (via clone-log) | verify-output | comparador (exatas/near≥.8) | título`. Lista os PULADOS (já feitos) e os "⚠ revisar" (não-convergidos), com o porquê. Aponta que NADA foi deployado (aguarda aprovação humana).

## Timer (ScheduleWakeup)

Se a 1ª linha trouxer `iniciar-em=Nmin` (N>0): use `ScheduleWakeup(N*60)`, passando de volta a MESMA instrução (o bloco inteiro) pra re-entrar nesta skill no disparo. No disparo, a Etapa F0 roda de novo — e a **git-verdade pula automaticamente** o que já foi feito (idempotente). Rode a fila inteira num disparo só (ou re-arme por item se quiser heartbeat). NUNCA agende deploy.

- ⚠️ **É in-session**: a sessão do Claude Code precisa ficar ABERTA durante a espera — o `ScheduleWakeup` dorme e acorda DENTRO da sessão. O painel só GEROU o comando agendado; ele não executa nada. Se o usuário fechar tudo esperando rodar sozinho, NÃO roda (deixe isso claro se ele perguntar).
- Este é o caminho recomendado: reusa tudo, mantém relatório revisável, zero infra nova.
- **NÃO** existe (por ora) execução headless disparada pelo painel (cron na VPS → `claude`). Se um dia existir, é projeto separado com os riscos de rodar sem supervisão (custo, gate travado/git-jam às 3h). Ver a análise em memória.

## Armadilhas (embutir)

1. **Paralelizar artigos** — NÃO. Serial. O paralelismo é intra-artigo (reviews da Etapa 1.1).
2. **Pular git-verdade** — re-rodar a fila re-clona o que já existe e duplica trabalho/commits. Sempre checar `git log` por item.
3. **Fechar sem os 2 gates** — `verify` (etapas) E `verify-output` (artefato) ANTES do commit. Um sem o outro deixa passar (etapas marcadas mas .mdx quebrado, ou .mdx ok mas hard-gate pulado).
4. **TITLE do painel** — vem no padrão do FONTE; a `artigo-clonar-em-massa` normaliza pro destino. NÃO gravar o TITLE literal.
5. **Deploy** — NUNCA na fila/timer. Para em commitado+buildado.
6. **VPS git-jam** (ref lock) — retry; não é erro fatal (o commit em `main` é a fonte da verdade).

## Disciplina de release

Nasce no project repo. Vai pro marketplace (`marcelohaz/afiliados-skills`) junto da próxima release relevante (ver `feedback_skill_regua_release_junto`). Validar num run real antes.

## Invocação

```
/artigo-clonar-fila
<cola aqui o bloco de comandos do botão "▶ Copiar fila" do painel>
```
Ou com timer: "daqui a 3 horas: {bloco}".
