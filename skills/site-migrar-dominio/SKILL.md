---
name: site-migrar-dominio
description: Migra um site inteiro da rede de um domínio para outro, com 301 catch-all path-preserving no domínio antigo. Cobre as 5 fases (preparação no repo → zona/DNS → deploy no domínio novo → 301 no antigo → GSC), com gate entre a 3 e a 4 (o domínio novo TEM que servir antes da placa subir). Opcionalmente renomeia a pasta do site quando a identidade muda junto. Aceita `{site} {dominio-novo}` OU `{site} {dominio-novo} --sem-rename`. Trata as armadilhas medidas em casos reais: regras path-específicas com caminho relativo viram cadeia de 2 saltos, artigo `contentLocked` escapa da troca em massa de tag, pre-commit bloqueia migração (bypass documentado), rename orfana o prefixo do R2 e exige `pnpm install` na VPS, e a affiliateTag NUNCA pode ser inventada. NÃO registra domínio, NÃO aponta NS (passo humano no Registro.br) e NÃO decide o domínio de destino.
---

## Parse de input

- `{site} {dominio-novo}` (ex.: `escritoriocasa guiamelhor.com.br`, caso real de 08/08 — a pasta hoje é `oguiacompra`) → migra o site pro domínio novo, COM rename da pasta
- `{site} {dominio-novo} --sem-rename` → só troca o domínio, mantém o slug da pasta
- URL do painel (`site-{slug}.html`) também resolve o slug

O domínio de destino é **sempre** do usuário. A skill não escolhe e não sugere sozinha.

# Migrar um site de domínio

Caso de referência: **escritorioecasa.com → oguiacompra.com.br** (2026-07-31, 4 commits em 2h35) e
**escritoriocasa.com.br → guiamelhor.com.br** (2026-08-08). Toda régua abaixo foi medida num desses dois.

## O que esta skill É

O procedimento ponta a ponta de trocar o domínio de um site que **já existe e já está no ar**, deixando
o domínio antigo com 301 que preserva o caminho.

**NÃO é** consolidação de dois sites (fundir A dentro de B que já tem o mesmo conteúdo). Ali não há o que
mover — só a Fase 4. **NÃO é** go-live de site novo. **NÃO registra domínio nem aponta NS.**

## Invariantes

- **A ordem das fases é dura.** O domínio novo serve ANTES do 301 subir. No caso de referência foram 16
  minutos entre um e outro. Invertido, o Google segue o 301 e encontra porta fechada.
- **A `affiliateTag` NUNCA é inventada.** Tracking ID Amazon existe ou não existe na conta; a plataforma
  deixa criar e nunca apagar. Sem o id confirmado pelo usuário, a tag antiga FICA — ela é válida e a
  comissão continua entrando, só atribui pro bucket antigo. Ver [[afiliados.regras.affiliate-tag-naming-e-melhor-disponivel]].
- **O domínio ANTIGO tem que continuar registrado e apontado pra Cloudflare**, indefinidamente. É ele que
  sustenta o 301. Se vencer, todo backlink volta a bater em nada. Conferir a data de expiração na Fase 0
  e avisar.
- **`domains.json` não é fonte de verdade** sobre disponibilidade. Medido em 2026-08-08: 7 domínios
  marcados como livres tinham site no ar, e 10 tinham `expiresAt` vencido. O campo `site` ignora
  WordPress legado e alias Astro. Confirmar no Registro.br e por sonda HTTP.
- **NÃO faz deploy sem o usuário pedir** (régua da CLAUDE.md). A Fase 3 é a única que publica, e ela é
  o próprio pedido da migração — mas confirme antes de disparar se a conversa não deixou explícito.

## Fase 0 — pré-flight (BLOQUEANTE)

```bash
SITE={site}; NOVO={dominio-novo}
# 1. estado do site
python3 -c "import json;m=json.load(open('docs/painel/sites-meta.json'))['$SITE'];print(m)"
# contentLocked/deployBlocked True → PARAR e avisar
# 2. artigos travados (escapam da troca de tag)
grep -l "contentLocked: true" sites/$SITE/src/content/reviews/*.mdx
# 3. onde o domínio antigo está escrito na mão
ANTIGO=$(python3 -c "import re;print(re.search(r\"domain:\s*'([^']+)'\",open('sites/$SITE/src/config.ts').read()).group(1))")   # sem grep -P: BSD grep do macOS não tem
grep -rl "$ANTIGO" sites/$SITE/src/
# 4. regras que JÁ existem no worker pro host antigo
python3 -c "
import json;r=json.load(open('worker/redirects.json'))
rows=r if isinstance(r,list) else r.get('redirects',r)
print([x for x in rows if x.get('hostname','') in ('$ANTIGO','www.$ANTIGO','$NOVO','www.$NOVO')])"   # pelo DOMÍNIO lido do config, não pelo slug (slug sem hífen não casa 'melhoraspirador.com' e casa irmão)
# 5. o domínio novo resolve? tem zona?
curl -sS -o /dev/null -w "%{http_code}\n" --max-time 12 "https://$NOVO/"
```

**Barreiras que param aqui:** site com `contentLocked` ou `deployBlocked`; domínio novo já servindo
conteúdo de terceiro; domínio antigo vencendo em menos de 60 dias sem plano de renovação.

**Reportar ao usuário antes de seguir:** artigos travados encontrados (vão precisar de destrave manual
pra troca de tag), quantidade de links com a tag antiga, e a data de expiração dos DOIS domínios.

## Fase 1 — preparação no repositório

Nada muda no ar. O site antigo segue servindo normal.

| # | ação | onde |
|---|---|---|
| 1.1 | `git mv sites/{antigo} sites/{novo}` | só se COM rename |
| 1.2 | `name`, `domain`, `siteUrl`, `contactEmail`, `contactMainTopic`, `hero.titleHighlight` | `src/config.ts` |
| 1.3 | `author.social.email` e `author.bio` (a bio cita o nome do site) | `src/config.ts` |
| 1.4 | domínio + marca | `content/pages/{sobre,privacidade,termos}.html` |
| 1.5 | `name` do pacote | `package.json` |
| 1.6 | renomear a chave do site **preservando a ordem** | `docs/painel/sites-meta.json` |
| 1.7 | `git mv` dos marcadores `{antigo}-*` → `{novo}-*` | `docs/biblias-v2/.audits/*/` |
| 1.8 | `pnpm install --lockfile-only` e conferir 0 ocorrências do nome antigo | `pnpm-lock.yaml` |
| 1.9 | atualizar `TEMPLATE_KNOWN_DIVERGENCES` e `KNOWN_DIVERGENCES` **se o slug estiver lá** | `server.ts` · `template-diff.ts` |

**O handle do Facebook MUDA** e segue o slug: `facebook.com/{slug-novo}`. Medido em 2026-08-09: **45 dos
49 sites** da rede usam `facebook.com/{slug}`, e **3 das 4 exceções são resíduo de rename** que ninguém
corrigiu (`oguiacompra`→escritoriocasa, `impressoracustobeneficio`→impressoraideal, e este caso antes do
conserto). O caso de referência manteve o handle antigo, mas isso foi **esquecimento, não decisão** —
canon Marcelo 2026-08-09: *"os facebooks de rodapé são gerados automaticamente, faça como se fosse um
site novo"*. O handle aparece no rodapé de TODAS as páginas, então deixar o antigo faz cada página da
marca nova apontar pra marca velha.

**O que NÃO muda:** o nome do autor e credenciais reais da persona.

**Tag de afiliado:** só troque com o id confirmado. `sed 's/tag={antiga}/tag={nova}/g'` nos `.mdx` de
`reviews/` e `products/`, MAIS o `affiliateTag` do config. Atenção: existe uma segunda camada — o
`injectAffiliateTag()` do `packages/ui/src/utils/amazon.ts` carimba a tag no BUILD em toda URL Amazon
**crua**. Links com tag hardcoded não são alcançados por ela. Ao auditar, **meça o build, não o source**.

**Gate da Fase 1:**
```bash
pnpm install && pnpm --filter {novo} build
grep -o 'rel="canonical" href="[^"]*"' sites/{novo}/dist/index.html | head -1   # domínio NOVO
grep -rl '{dominio-antigo}' sites/{novo}/dist | wc -l                           # tem que ser 0
```

**Commit:** o pre-commit **vai bloquear** (vê `.mdx` de `reviews/` staged, mesmo sendo rename puro). O
próprio hook documenta o bypass pra este caso — `git commit --no-verify`, "migrações grandes". Deixe
explícito na mensagem que **não foi deployado** e qual item ficou pendente.

**🚨 GATE PÓS-COMMIT — meça o HEAD, não a árvore de trabalho.** O gate acima lê `dist/`, que é
construído do **working tree**: ele passa mesmo quando as edições de conteúdo ficaram FORA do índice
e só o rename entrou no commit. Rode DEPOIS de commitar:

```bash
git show --stat HEAD | tail -1                      # ⛔ "0 insertions(+), 0 deletions(-)" = só o rename entrou
git grep -c '{dominio-antigo}' HEAD -- sites/{novo}/ | head   # domínio: tem que ser vazio
git grep -n '{Marca Antiga}' HEAD -- sites/{novo}/  | head    # MARCA com espaço: idem (case-SENSITIVE)
git show HEAD:sites/{novo}/src/config.ts | grep -E 'domain:|affiliateTag:'   # valores NOVOS
```

**⚠ Grepe as DUAS formas: o domínio E a marca com espaço.** `tabletideal` e `Tablet Ideal` são
strings diferentes, e a segunda sobrevive ao `sed` do domínio porque vive na PROSA (bio do autor,
página /sobre/, hero, descrição de categoria). Caso real 2026-08-13: `/author/gustavo-alves/` foi
pro ar dizendo *"redator por trás do Tablet Ideal"* e **passou por duas varreduras** que só grepavam
o domínio (achado da Bárbara, depois de já ter reportado a migração como concluída).

**Use `grep` case-SENSITIVE no Title Case da marca, nunca `-i`.** Marca de rede afiliada costuma ser
feita de palavras comuns, então `-i` casa com português legítimo e afoga o achado real em ruído:
medido em 2026-08-14 sobre 8 migrações da rede, `grep -i "Impressora Ideal"` deu **4 falsos
positivos** — todos em *"a impressora ideal para você"*, que é a frase, não a marca. No Title Case,
as mesmas 8 migrações dão **0**. Se a marca antiga for genérica demais pra separar por caixa
(ex.: "Melhor Guia"), grepe e classifique os hits à mão em vez de confiar na contagem.

**A assinatura do defeito é `0 insertions(+), 0 deletions(-)` num commit que deveria carregar rename
E edição.** `git mv` já deixa o rename staged; o `sed`/`Edit` que vem depois NÃO entra sozinho, e um
`git commit` sem `add` novo leva só a metade. Nada quebra na hora — o que está no ar continua certo,
porque o deploy saiu da árvore de trabalho — mas o HEAD fica com **pasta nova + config velho**, e o
próximo build pelo painel (ou por qualquer outra máquina) ressuscita a **tag de afiliado antiga**.
Reincidência medida: `guiamelhorcompra`→`escritoriocasa` (2026-08) e `tabletideal`→`omelhortablet`
(2026-08-13, pego pela própria Bárbara *depois* de reportar a migração como concluída). Ver
armadilhas 10-12 e [[afiliados.projeto.transferir-guiamelhorcompra-para-escritoriocasa]].

## Fase 2 — zona e DNS do domínio novo

1. Confirmar no **Registro.br** que o domínio está ativo (não confie no `domains.json`).
2. **Apontar o NS pra Cloudflare** — passo HUMANO, no painel do registrador. A skill não faz.
3. Criar a zona na conta do owner + CNAME `@` e `www` proxied.

Sem o NS propagado a Fase 3 falha em silêncio parcial: o `cf-deploy-r2` avisa
`⚠️ Zone não encontrada` e sobe o R2 mesmo assim, deixando KV e Worker Route pela metade.

## Fase 3 — publicar no domínio novo

```bash
bun scripts/cf-deploy-r2.ts {slug}
```

Sobe o build no R2 (prefixo = **slug da pasta**), mapeia `dominio → slug` no KV e cria as Worker Routes.
A partir daqui **os dois domínios servem o site em paralelo**.

⚠️ **Se renomeou a pasta, o R2 fica com DOIS prefixos — e o antigo NÃO é órfão ainda.** O prune do
deploy só varre o prefixo atual, então o antigo sobrevive. E ele **é o que serve o site vivo** enquanto
o domínio velho ainda responde, porque o KV segue mapeando `dominio-antigo → slug-antigo`.

**Podar o prefixo antigo antes da Fase 4 derruba o site no ar.** Ele só vira órfão de verdade depois
que o catch-all sobe e o domínio antigo para de servir conteúdo. Ordem: Fase 4 → conferir o 301 →
só então podar. Registre no relatório, senão em silêncio ninguém acha depois.

⚠️ **Compare a contagem dos dois prefixos.** Se o novo tem MAIS páginas que o antigo, existe conteúdo
no repo que nunca foi publicado — o deploy da migração vai publicá-lo de uma vez. Não é defeito, mas
mude o relatório: são páginas estreando, sem histórico de indexação. Caso real (guiamelhor, 2026-08-08):
129 páginas no ar contra 193 encenadas, porque 59 páginas transferidas de outro site em 06/08 nunca
tinham sido deployadas.

**Gate — não seguir sem isso:**
```bash
curl -sS -o /dev/null -w "%{http_code}\n" https://{novo}/            # 200
curl -sS -o /dev/null -w "%{http_code}\n" https://{novo}/{um-artigo}/ # 200
```

## Fase 4 — 301 no domínio antigo

**4.1 — reescrever as regras que já existem** pro host antigo em `worker/redirects.json`, trocando
caminho relativo por **URL absoluta no domínio novo**:

```
antes:  { "from": "/plotter-de-recorte", "to": "/impressora-para-personalizados/" }
depois: { "from": "/plotter-de-recorte", "to": "https://NOVO/impressora-para-personalizados/" }
```

**Por que:** o worker resolve com `new URL(r.to, url)`, relativo ao host **atual**. Com um catch-all
ativo, cada uma dessas viraria `antigo/destino` → `novo/destino` = **cadeia de 2 saltos**. O caso de
referência tinha 11 regras e todas foram reescritas pra absoluto. Se você não reescrever, funciona e
dilui — o defeito é invisível no navegador.

**4.2 — acrescentar o catch-all como ÚLTIMA entrada do host:**

```json
{ "from": "/*", "to": "https://NOVO", "status": 301,
  "hostname": "ANTIGO", "catchAll": true }
```

A ordem no arquivo não importa pro worker (ele varre path-específicos num loop e catch-all noutro,
`afiliados-router.ts:73-89`), mas manter por último deixa a intenção legível.

**4.3 — ativar:**
```bash
bun scripts/cf-deploy-worker.ts
```

O `redirects.json` entra no **bundle** do worker. Editar o arquivo sem rodar isso **não surte efeito
nenhum**. É o erro mais fácil de cometer aqui.

⚠️ **A partir deste comando o conteúdo próprio do domínio antigo para de ser servido** — o catch-all
dispara antes da resolução no KV (`afiliados-router.ts:91`). Não precisa despublicar nem podar nada
pro redirect valer.

**4.4 — PURGAR o cache das duas zonas.** Sem isso a borda serve as respostas anteriores e o teste
mente. Medido em 2026-08-09, logo após o deploy do worker: uma URL ainda 301 pra home do domínio
ANTIGO, uma regra path-específica ainda com destino relativo, e um artigo ainda entregando **200 no
domínio antigo**. `POST /zones/{id}/purge_cache {"purge_everything":true}` nas duas zonas, esperar
~20s, e só então testar.

**Gate — use `-L` com contagem de saltos, não `curl -I`:**
```bash
curl -sSL -o /dev/null -w 'saltos=%{num_redirects} · %{http_code} · %{url_effective}\n' \
  https://{antigo}/{um-artigo}/
# esperado: saltos=1 · 200 · https://{novo}/{um-artigo}/
```
⚠️ **`curl -I` sozinho não serve de gate.** No caso real acima ele mostrava 301 pro destino certo e
parecia sucesso, enquanto o `-L` revelava que a cadeia terminava em 200 no domínio ANTIGO. Testar:
um artigo, uma página de produto, uma das regras path-específicas, e uma URL inexistente
(essa vai dar 2 saltos — catch-all + fallback — e está correto, assim como `www.`).

## Fase 5 — Search Console

1. Adicionar e **verificar** a property do domínio novo.
2. Submeter os sitemaps do domínio novo.

**NÃO usar a Mudança de Endereço do GSC.** Canon Marcelo 2026-08-09, aplicado nas duas migrações da
rede: *"não vou avisar o GSC a mudança de endereço. No oguiacompra também não foi feito isso."*
Não propor, não listar como pendência, não chamar de "passo que faltou" — é escolha, não esquecimento.
O Google recebe o 301 catch-all e os sitemaps do domínio novo, e processa a partir daí.
Ver [[afiliados.decisao.nao-usar-mudanca-de-endereco-gsc]].

## Reversão

Remover a entrada `catchAll` do `redirects.json` + `cf-deploy-worker.ts`. O domínio antigo volta a
servir na hora. As Fases 1 a 3 não precisam ser desfeitas: o domínio novo apenas fica servindo junto.

## Pós-migração na VPS (COM rename)

`node_modules` é gitignored, então o dir novo nasce sem ele na VPS e o "Atualizar Site" do painel quebra
com `astro: not found`:

```bash
ssh melhorserum-painel@91.108.125.248
cd ~/afiliados && pnpm install --frozen-lockfile
rm -rf sites/{antigo}       # o órfão gitignored bloqueia recriar o slug depois
```

Ver [[afiliados.armadilha.rename-site-vps-pnpm-install]].

## Armadilhas

### 1. Deployar o 301 antes do domínio novo servir
A mais cara e a mais fácil. O gate da Fase 3 existe só pra isso.

### 2. Editar o redirects.json e achar que valeu
Ele é importado no bundle do worker. Sem `cf-deploy-worker.ts`, nada muda. Sempre feche a Fase 4 com o
`curl` do gate, nunca com "editei o arquivo".

### 3. Regras antigas com caminho relativo
Viram cadeia de 2 saltos assim que o catch-all sobe. Ver 4.1. **Conte as regras existentes na Fase 0** —
se você não olhou, elas estão lá.

### 4. Artigo `contentLocked` escapa da troca de tag
Caso real (oguiacompra, 2026-07-31): o `melhor-ipad` estava travado, ficou com a tag antiga em 14 links,
e precisou de um commit extra. **Liste os travados na Fase 0** e trate antes, não depois.

### 5. Inventar a affiliateTag
Se o id não existir na conta Amazon, os links passam a não creditar ninguém. Sem confirmação do usuário,
a tag antiga fica — ela é válida.

### 6. Confiar no domains.json
Ver invariantes. Sonda HTTP + Registro.br.

### 7. Rename que não é necessário
Trocar só o domínio **não quebra nada** — o domínio não é derivado em runtime, vive no `config.ts`, e
todo o SEO deriva de `siteConfig.siteUrl` ([[afiliados.convencao.slug-por-tld-multidominio]]). O rename
serve quando a IDENTIDADE muda junto e o slug passaria a mentir. Ele custa: prefixo órfão no R2,
`pnpm install` na VPS, dir órfão no disco e as duas listas `KNOWN_DIVERGENCES`
([[afiliados.armadilha.rename-site-quebra-known-divergences]]). Pergunte antes de assumir.

### 8. Podar o prefixo antigo do R2 antes da Fase 4
Enquanto o domínio velho responde, é ELE que serve o site — o KV ainda mapeia `antigo → slug-antigo`.
Podar ali derruba o site no ar. Só vira órfão depois do catch-all. Ver Fase 3.

### 9. Achar que o 404.astro redireciona
Não redireciona. Ele devolve **HTTP 404** com meta-refresh no corpo; o Googlebot lê o status e descarta
a URL ([[afiliados.armadilha.404-meta-refresh-nao-e-redirect]]). Redirect de verdade só pelo
`worker/redirects.json`.

### 10. Grepar só o domínio e achar que varreu a marca
`tabletideal` e `Tablet Ideal` são strings diferentes. O `sed` do domínio não toca a marca escrita
por extenso na PROSA (bio do autor, /sobre/, hero, descrição de categoria), e ela vai pro ar
contradizendo a marca nova. Duas varreduras da Bárbara passaram batido nisso em 2026-08-13. O gate
pós-commit da Fase 1 grepa as duas formas — e **case-sensitive**, porque `-i` afoga o achado em
português legítimo ("a impressora ideal para você").

### 11. `git mv` + `sed`: o commit leva só o rename
A armadilha mais reincidente desta skill, e a mais silenciosa — **o site no ar continua certo**, então
nada denuncia. `git mv` já entra staged; a edição que vem depois (`sed`, `Edit`) fica unstaged, e um
`git commit` sem `git add` novo grava pasta nova com config velho. Assinatura: `0 insertions(+),
0 deletions(-)` num commit que deveria ter as duas coisas. Confirmado 2× na rede (guiamelhorcompra
2026-08, tabletideal 2026-08-13). O gate pós-commit da Fase 1 existe só pra isso: **medir o HEAD**,
porque todo gate que lê a árvore de trabalho ou o `dist/` passa limpo com o defeito presente.

### 12. Reportar a migração antes de conferir o HEAD
Corolário da 10, e o motivo de ela sobreviver: as duas reincidências foram **reportadas como
concluídas** e o erro apareceu depois, na conferência. O relatório final só sai depois do gate
pós-commit — "testei com `curl` e deu 200" prova o que está no ar, não o que está commitado.

## Relatório final

Sempre incluir: commit(s), o que ficou **pendente** (tag, NS, VPS, poda do R2), a data de expiração dos
dois domínios, e o comando exato de reversão. **Pré-condição: o gate pós-commit da Fase 1 passou** (o
HEAD, não a árvore) — sem isso o relatório afirma o que não foi medido.

## Exemplo de invocação

```
Skill(skill="afiliados-skills:site-migrar-dominio", args="escritoriocasa guiamelhor.com.br")
Skill(skill="afiliados-skills:site-migrar-dominio", args="melhorguia melhortech.com.br --sem-rename")
```

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
