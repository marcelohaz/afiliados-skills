---
name: pagina-produto-auditar-em-massa
description: Audita E CORRIGE VÁRIAS páginas individuais de produto de uma vez, cada uma ISOLADA (sub-agents paralelos, ≤10 por leva). Régua = a canônica da `pagina-produto-auditar` (não reimplementa). Camada MECÂNICA na mãe primeiro (audit-editorial + guardas por slug), depois os sub-agents gastam contexto no JULGAMENTO. Auto-aplica o conserto de FATO que passa no TESTE DA FRASE NOVA; `warn` de julgamento é sempre report-only. Descobre sozinha as pendentes (conteúdo presente + sem relatório `.audits/products/{site}-{slug}-last.md` no DISCO). Aceita `site/slugs`, `site` (todas as pendentes) ou `todas` (rede). Dois commits separados (.mdx consertados / relatórios). NÃO faz deploy.
---

## Parse de input

Args no `$ARGUMENTS`:

- **`{site}/{slug1},{slug2}`** — subset explícito. Ex.: `guiamelhor/aoc-24b35hm2,lg-20u401a-b`
- **`{site}`** — todas as páginas pendentes de auditoria daquele site
- **`todas`** — todas as pendentes da rede (ordenadas por site)
- **`--limite N`** (default **10**) — quantas páginas por execução. É o tamanho da
  leva, não um teto do que existe: o relatório final sempre diz quantas sobraram
  e qual comando roda o próximo lote.
- **`--report-only`** (default desligado) — não aplica nada, só reporta. Vira a
  paridade literal com a skill individual, que fora de lote é read-only.
- **`RETOMAR=yes`** — invocação nascida do heartbeat (ver Invariantes → Turno vivo).

Detecção: contém `/` seguido de vírgulas ou de um slug → subset. É a string
`todas` → rede inteira. Senão → nome de site.

# Auditar + corrigir páginas de produto em massa (paralelo, isolado)

> Esta skill é **orquestrador**. A régua editorial (as 22 categorias de check, o
> TESTE DA FRASE NOVA, o que é `warn` e o que é `error`) é a canônica da
> **`pagina-produto-auditar`** — esta NÃO reimplementa nada disso. Ela faz
> pré-flight + camada mecânica + fan-out + reconciliação + guardas + commit.
> Mesma relação que a `biblia-auditar-em-massa` tem com a `biblia-auditar`.

## O que esta skill É (e não é)

- **É** o auditor-corretor em massa de páginas **já preenchidas**. Roda em N
  páginas, cada uma isolada, conserta o que tem direção conhecida e lista o resto.
- **NÃO cria página.** Página vazia (stub ou sem os 6 campos) é **excluída** do
  lote com aviso — o caminho dela é a `pagina-produto-criar-em-massa`.
- **NÃO é a etapa `--audit` da `criar-em-massa`.** Aquela audita só o que ela
  acabou de criar (ela **pula** página já preenchida por idempotência). Esta
  existe pra quitar a dívida de páginas criadas SEM a flag — que é o caso comum,
  porque `--audit` é opt-in e a própria skill orienta a pular em lote rotineiro.
- **NÃO faz deploy.** Para em "commitado + pushado + VPS sincronizada".

## Por que esta skill existe (a dívida que ela quita)

Medido em **2026-08-29**: **72 páginas** da rede com conteúdo e sem nenhuma
auditoria, **59 delas num site só** (`guiamelhor`), em categorias inteiras
(fones-de-ouvido 6/6, microfones 1/1, caixas-de-som 25/27). Causa: os lotes de
criação de jul-ago rodaram sem `--audit`, com a intenção de "auditar separado
depois" — e o *depois* não tinha ferramenta nem lembrete. O único sinal era um
chip cinza numa tabela de 171 linhas.

⚠ **Não foi bug de skill nem efeito do rename `escritoriocasa`→`guiamelhor`**
(esse moveu os 100 relatórios corretamente). Foi opção de invocação. Ver
[[afiliados.armadilha.paginas-produto-sem-auditoria]].

## Modelo

Opus 5 (ou o Opus mais novo disponível). Sub-agents fixados com `model: opus` no
Agent tool. NUNCA Sonnet/Haiku.

## Garantia de qualidade (= skill individual)

| | Individual (`pagina-produto-auditar`) | Em massa (esta) |
|---|---|---|
| Régua dos checks | 22 categorias canônicas | **as mesmas**, lidas do repo pelo sub-agent |
| Quem julga | sub-agent Opus, conversa fresh | **mesmo** sub-agent, conversa fresh |
| Camada mecânica | passo 6.7, dentro do sub-agent | **na mãe**, 1× por slug (Etapa 1) |
| Trava antes de "ficar" | read-only fora de lote | **re-rodar as 2 guardas** no que foi corrigido + reversão do backup |
| Conserto de fato | só com `EM_MASSA=yes` | habilitado (TESTE DA FRASE NOVA) |
| `warn` de julgamento | report-only | **report-only, sem exceção** |

Caveat honesto: o conserto entra sem aprovação prévia sua. A fiscalização é a
re-execução das guardas + o backup + o diff no relatório (pós-fato). Quem quer
paridade literal usa `--report-only`.

## Invariantes

- **Sub-agents NÃO fazem git.** Nem `pull`, nem `stash`, nem `commit`, nem
  `painel-vps-pull.sh`. A mãe controla 100% do git. Sub-agent recebe
  **`EM_MASSA=yes`**, que é a flag que a `pagina-produto-auditar` lê pra pular
  git/mecânica/guarda/commit e liberar o conserto de fato.
- **Isolamento estrito.** 1 sub-agent por página, conversa fresh, vê SÓ aquela
  página + a bíblia dela. NUNCA prompt com várias páginas, NUNCA contexto
  compartilhado. (A comparação cross-site é feita pelo `compare-cross-site.py`
  dentro do próprio sub-agent, que MEDE — não é passada comparativa da mãe.)
- **Trava de slug.** O sub-agent devolve `slug`; a mãe confere
  `slug_retornado == slug_pedido` antes de aceitar qualquer conserto. Sem isso um
  agente confuso pode reportar sobre a página do vizinho.
- **`warn` de julgamento NUNCA aplica** — nem parecendo óbvio. Frase colada na
  página irmã, coloquialismo acima do teto e redundância bullet↔parágrafo são
  report-only (canon 2026-07-10). Só o achado de **FATO** que passa no TESTE DA
  FRASE NOVA aplica.
- **Página que contradiz a `decisaoEditorial` mas obedece OUTRO campo da mesma
  bíblia: não toque.** O alvo é a bíblia; o relatório aponta pra lá.
- **Backup antes de qualquer escrita** (`.painel-backups/<dia>/`). Reversível.
- **Só audita PREENCHIDA.** Sem os 6 campos ou com marcador de stub → exclui do
  lote com aviso ("crie primeiro").
- **Respeita as duas travas.** `contentLocked` do SITE (`sites-meta.json`) aborta
  a skill; `contentLocked` da PÁGINA exclui aquela página do lote (auditar lê, mas
  o conserto escreveria). ⚠ Esta é uma diferença real em relação à
  `criar-em-massa`, que só olha o lock do site — lá as páginas são novas, aqui são
  existentes e podem estar travadas individualmente.
- **Cap de paralelismo: 10 sub-agents.** Acima → levas de 10.
- **Erro em 1 não quebra o lote.** Sub-agent que falha volta `{ok:false}`; a mãe
  agrega e reporta. Sub-agent que MORREU depois de escrever no `.mdx` é tratado
  na reconciliação (Etapa 3) — termine aquela página **inline**, não re-dispare
  (o `Edit` dele já está no disco e um agente novo re-audita um arquivo mudado
  sem saber disso).
- **Nunca inventa achado.** Categoria sem problema = "nenhum". Toda flag precisa
  de evidência (trecho literal < 15 palavras).
- **Turno vivo (canon Marcelo 2026-08-15).** Sub-agents SEMPRE com
  `run_in_background: false`, a leva inteira num só bloco de chamadas. **O plano e
  a primeira leva vão na MESMA mensagem.** Heartbeat como passo 0:
  `ScheduleWakeup(1800, prompt="/pagina-produto-auditar-em-massa {os MESMOS args} RETOMAR=yes")`
  — exceto se invocada dentro de outra em-massa (o despertar é da mãe).
  `ScheduleWakeup(stop:true)` antes do relatório final e no aborto do pré-flight.
  Circuit breaker: 3 despertares sem página nova → `stop` + relatório.
- **NÃO faz deploy.**

## Pipeline

### Etapa 0 — Pré-flight

0. **Arma o heartbeat** (pule se `ANINHADA=yes`/`EM_MASSA=yes`: o despertar é da mãe).
   Se `RETOMAR=yes`, re-arme e siga — o pré-flight é idempotente (só entra o que
   ainda não tem relatório).

1. **Git pull com linha de controle** (o estado vem do painel VPS por git):
   ```bash
   git stash push -u -m "skill-pagina-produto-auditar-em-massa-temp" 2>&1 | tail -1
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>&1 | tail -1
   echo "local: $(git rev-parse --short=12 HEAD) · remote: $(git ls-remote origin main | cut -c1-12)"
   ```
   ⚠ Use `-u` e **não engula o erro do pull**. Sem a linha de controle não dá pra
   distinguir "puxei e não tem" de "não puxei" (caso real 2026-08-13).

2. **Chave-mestra do site**: pra cada site do lote,
   `python3 -c "import json;print(json.load(open('docs/painel/sites-meta.json'))['{site}'].get('contentLocked'))"`.
   `True` → **PARE e avise** (destravar no painel → Proteção).

### Etapa 0.5 — Descobrir as pendentes (o pré-flight próprio desta skill)

Uma página está **pendente de auditoria** quando as duas coisas valem:

1. tem conteúdo: o frontmatter casa `^(subtitle|shortDescription|pros|cons|specs|fullReview):`
   **e** o corpo não tem `{/* STUB GERADO POR `;
2. **NÃO existe** `docs/biblias-v2/.audits/products/{site}-{slug}-last.md` **no disco**.

```bash
python3 - <<'PY'
import os, re, glob, json, sys
alvo = sys.argv[1] if len(sys.argv) > 1 else 'todas'   # 'todas' | '{site}' | '{site}/{slugs}'
pend = {}
padrao = 'sites/*/src/content/products/*.mdx' if alvo == 'todas' else f'sites/{alvo.split("/")[0]}/src/content/products/*.mdx'
for f in sorted(glob.glob(padrao)):
    site, slug = f.split('/')[1], os.path.basename(f)[:-4]
    raw = open(f, encoding='utf-8').read()
    fm = (re.match(r'^---\n([\s\S]*?)\n---', raw) or [None, raw])[1]
    if '{/* STUB GERADO POR ' in raw: continue
    if not re.search(r'^(?:subtitle|shortDescription|pros|cons|specs|fullReview):', fm, re.M): continue
    if os.path.exists(f'docs/biblias-v2/.audits/products/{site}-{slug}-last.md'): continue
    pend.setdefault(site, []).append(slug)
print(json.dumps(pend, ensure_ascii=False, indent=1))
PY
```

⚠ **A verdade é a EXISTÊNCIA DO ARQUIVO NO DISCO, nunca o `git log`.** O painel
usa `gitLastCommitMs` no relatório, e isso devolve a data do commit de
**DELEÇÃO** quando o arquivo foi apagado — a página aparece "Auditado" sem nunca
ter sido auditada. Medido 2026-08-29:
`qualamelhorcreatina/atlhetica-creatina-100-pure`, relatório apagado em 18/06 no
commit "remove audit órfão do slug antigo", página seguiu no ar. Se a skill
herdasse esse critério, pularia exatamente as páginas que mais precisam.

Zero pendentes = **fim legítimo**, relatório de 3 linhas + `stop`. Não é uma lista
de opções esperando resposta.

### Etapa 1 — Camada MECÂNICA (na mãe, determinística, sem IA)

Roda ANTES de gastar sub-agent. Motivo: a LLM erra ~1/3 dos checks contáveis
(medido no gabarito da individual: 6 de 19 `shortDescription` >250 passaram
batido), e defeito puramente mecânico não precisa de Opus.

```bash
SITE={site}; FAIL=0        # ⚠ {site} é o site do lote, não um valor fixo
set -- {slug-1} {slug-2} ...          # ⚠ zsh NÃO faz word-split em $VAR
echo "CONTROLE \$# = $#  (esperado N)"
for S in "$@"; do
  bun scripts/audit-editorial.ts "$SITE/$S" --json 2>/dev/null | python3 -c "
import json,sys
raw=sys.stdin.read().strip()
if not raw.startswith('{'):
    print('  ⛔ $S: audit-editorial não retornou JSON →', raw[:80]); sys.exit(1)
d=json.loads(raw); bad=[f for f in (d.get('findings') or []) if f.get('sev') in ('error','warn')]
if bad:
    print('  ⛔ '+d['slug'])
    for f in bad: print(f\"       {f['sev']:5} {f['rule']:22} {f.get('field','')} · {str(f.get('detail',''))[:60]}\")
    sys.exit(1)
" || FAIL=1
done
[ "$FAIL" = "0" ] && echo "  ✅ audit-editorial limpo"
bun scripts/pagina-produto-guardas.ts {site} {slug-1} {slug-2} ...
```

⚠ **`audit-editorial.ts` SEMPRE sai com exit 0**, mesmo com achado — o gate tem
que ler o JSON, não o exit code.

⚠ **A linha `$#` não é decoração.** Em zsh, `for S in $SLUGS` passa a string
inteira como um argumento só e a guarda imprime "0 página(s) conferida(s)" — uma
execução vazia parecendo sucesso. Aconteceu de verdade (cozinhaideal, 2026-08-21).

**Achado mecânico:** conserte determinístico aqui (travessão→vírgula, `;`→`.`/`,`,
parágrafo órfão fundido no "Por que gostamos", trim da última frase pra caber no
cap) e re-rode. Só depois disso os sub-agents entram — e o prompt deles diz
"a mecânica já passou, NÃO re-rode, gaste o contexto no julgamento".

### Etapa 2 — Fan-out do JULGAMENTO (sub-agents isolados, ≤10)

Imprime o plano e dispara **na mesma mensagem** (Turno vivo). Cada sub-agent:

```
Audite `{site}/{slug}`.  EM_MASSA=yes

Leia `.claude/skills/pagina-produto-auditar/SKILL.md` e execute a régua à risca.
A flag EM_MASSA=yes acima já diz o que muda: sem git (1.5), sem camada mecânica
(6.7), sem guarda (19b), sem commit (9) — a mãe fez os quatro — e o conserto de
FATO que passa no TESTE DA FRASE NOVA está habilitado.

Contexto deste lote:
- A camada mecânica passou limpa na mãe (`audit-editorial.ts` + `pagina-produto-guardas.ts`).
- ⚠ `warn` de julgamento NUNCA aplica.
- ⚠ Página contradiz `decisaoEditorial` mas obedece outro campo da mesma bíblia
  → NÃO toque; o alvo é a bíblia e o relatório aponta pra lá.
- Chavões: `{site}` {está/NÃO está} em `_sites_aplicaveis` — {bloco X vale / só o `_genericos`}.
- Site {live/em construção}. {avisos por bíblia, se houver — dadosInconsistentes/auditFlags}
- Relatório em `docs/biblias-v2/.audits/products/{site}-{slug}-last.md`,
  separando **CORRIGIDO** (com diff) de **REPORTADO**.

Retorne: {ok, slug, severity, corrigidos:[{campo,de,para}], issues:[...]}
```

⚠ **Passe os avisos por bíblia quando ela tiver `dadosInconsistentes`/`auditFlags`.**
Medido nos lotes de 28/08: avisar caso a caso o que a bíblia decidiu (ex.: "a
reclinação não tem valor certo — fique neutro") **impediu a reincidência** de
erros que apareceram em páginas irmãs criadas sem o aviso.

### Etapa 3 — Agregar + reconciliar (nos DOIS sentidos)

```bash
git status --short sites/{site}/src/content/products/
```

- **modificado E reportado** → normal, segue pro 3.5.
- **reportado E não modificado** → sub-agent alucinou o conserto. Investigue.
- **modificado E NÃO reportado** → ⛔ **edição órfã**. O agente editou e não
  chegou a validar (caso real 2026-08-06, `somprofissional/lg-xboom-grab`: morreu
  por erro de API depois do `Edit` e antes de re-auditar; a edição estava certa,
  mas por **sorte**). Rode as guardas nela E confira contra a bíblia à mão.
  Termine aquela página **inline**, não re-dispare.

Confira também a **trava de slug** (`slug_retornado == slug_pedido`).

### Etapa 3.5 — Re-rodar as DUAS guardas no que foi corrigido

O conserto entra depois da Etapa 1, ou seja, fora de qualquer guarda. Sem isto um
`Edit` pode estourar o cap, quebrar o fence ou deixar o `fullReview` fora da forma
canônica e ir pro commit sem ninguém olhar.

```bash
SITE={site}; set -- {slugs-corrigidos}; echo "CONTROLE \$# = $#"
for S in "$@"; do bun scripts/audit-editorial.ts "$SITE/$S" --json 2>/dev/null | python3 -c "..."; done
bun scripts/pagina-produto-guardas.ts {site} {slugs-corrigidos}
```

Reprovou? **Reverta aquela página do backup** e mova o achado pra REPORTADO.
Conserto que não passa na guarda não vale o risco.

### Etapa 4 — Dois commits separados, push, VPS

Nesta ordem, com lista explícita em cada `git add` (nunca glob):

1. os `.mdx` consertados (se houver) — mensagem dizendo o que foi trocado
2. os `.md` de auditoria

```bash
git add sites/{site}/src/content/products/{slug}.mdx ...
git commit -m "fix({site}): auditoria em massa corrige N páginas individuais"
git add docs/biblias-v2/.audits/products/{site}-{slug}-last.md ...
git commit --no-verify -m "audit-produto({site}): N páginas auditadas em massa"
git pull --rebase origin main && git push origin main
echo "local=$(git rev-parse --short=9 HEAD) remote=$(git ls-remote origin main | cut -c1-9)"
bash scripts/painel-vps-pull.sh
```

Separar importa: o commit de conteúdo tem que ser legível sozinho no histórico e
revertível sem levar os relatórios junto.

⚠ **`painel-vps-pull.sh` respondendo "já estava atualizado" SEM "(painel
regenerado)" é sinal de que o gen não rodou** (o `/admin/update` pula o gen quando
`behind=0`). Chame de novo antes de afirmar que o painel está em dia.

### Etapa 5 — Relatório

```
✅ Lote concluído — {N} páginas auditadas em {site}

CORRIGIDO NA HORA ({F}) — passou no teste da frase nova:
  {slug} · specs[3]  "0,5ms MPRT (1ms GtG)" → "0,5ms MPRT"
                     (o GtG só existe no bloco do modelo irmão)

REPORTADO ({R}) — exige decisão sua:
  {slug} · {categoria} · {evidência curta}

RAIZ NA BÍBLIA ({B}) — o alvo não é a página:
  {ASIN} · {campo} · {o que contradiz}

📦 Commit (fixes): {hash}   📦 Commit (audits): {hash}
🔄 VPS: {OK | bloqueado}

⏭️  Faltam {X} páginas pendentes. Próximo lote:
    /pagina-produto-auditar-em-massa {mesmos args}
```

**Todo conserto vai no relatório com o de→para**, não só a contagem — você precisa
poder discordar de uma troca sem abrir o diff do git.

## Armadilhas (todas medidas)

1. **`git log` como critério de "já auditou"** → falso "Auditado" em página com
   relatório deletado. Use existência no disco (Etapa 0.5).
2. **zsh não faz word-split** em `for S in $VAR` → guarda roda vazia e imprime
   sucesso. Use `set --` + a linha de controle `$#`.
3. **`audit-editorial.ts` sai com exit 0 mesmo com achado** → o gate lê o JSON.
4. **Sub-agent que morre depois do `Edit`** → edição órfã no `git status`. Termine
   inline; re-disparar faz o novo agente auditar um arquivo já mudado.
5. **Não re-rodar as guardas no que foi corrigido** → o conserto entra sem
   verificação nenhuma, que é exatamente o buraco que as guardas fecham.
6. **Prompt sem `EM_MASSA=yes`** → o sub-agent fica entre duas ordens opostas e
   registra ambiguidade. Foi o defeito medido antes da flag existir: 4 num lote de
   10 e 22 reincidências em `6.7` no skill-log.

## Limites de segurança (NUNCA faz)

- Não cria página, não preenche campo vazio, não regera conteúdo.
- Não aplica `warn` de julgamento, nem "óbvio".
- Não edita a BÍBLIA (o alvo é a página; achado de raiz vai pro relatório).
- Não faz deploy nem `cf-deploy-*`.
- Não toca em site/página com `contentLocked`.

## Disciplina de release

Skill nova → **vai pro marketplace** (tabela do CLAUDE.md: feature nova = ✓ Sim).
Checklist: copiar a SKILL.md, **registrar em `plugins[].skills` do
`.claude-plugin/marketplace.json`** (arquivo sem entrada no manifesto NÃO carrega
— foi assim que a v1.85.0 falhou), bumpar `metadata.version` + changelog na
`metadata.description`, conferir a contagem de skills na `plugins[].description`,
confirmar com `git ls-remote origin HEAD` (nunca pelo log local) e avisar que a
Bárbara precisa rodar `/plugin marketplace update`.

## Invocação

```
/pagina-produto-auditar-em-massa guiamelhor                    ← 10 pendentes do site
/pagina-produto-auditar-em-massa guiamelhor --limite 5
/pagina-produto-auditar-em-massa guiamelhor/aoc-24b35hm2,lg-20u401a-b
/pagina-produto-auditar-em-massa todas                         ← 10 pendentes da rede
/pagina-produto-auditar-em-massa guiamelhor --report-only
```

## Registrar desvio de execução (obrigatório quando houver)

SE você (a) executou diferente do que esta skill manda, (b) **criou um passo que
ela não tem**, (c) achou a régua ambígua/contraditória, ou (d) topou com bug numa
ferramenta dela — registre antes de fechar:

```bash
bun scripts/skill-log.ts note pagina-produto-auditar-em-massa <desvio|ambiguidade|bug|inventou-passo> "<o que fugiu e por quê>" [--ctx=site/slug] [--alvo=<etapa>]
```

Execução limpa **não gera linha** — vazio é dado. Sem `--alvo` a nota cai em
`geral` e sai do detector de reincidência, então **nomeie a etapa**.
