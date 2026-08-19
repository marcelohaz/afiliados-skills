---
name: amazon-lista-sites-auditar
description: >-
  Audita a Lista de Sites do Associados Amazon (teto de 50 por conta) e RECOMENDA quem entra e quem sai. Recebe a lista colada do console da Amazon, mede o que está no ar por sonda HTTP, puxa tráfego do GSC das contas com token, cruza com sites-meta/tag/DR e devolve dois rankings lado a lado: declarados do pior pro melhor (candidatos a sair) e não declarados do melhor pro pior (candidatos a entrar). READ-ONLY na Amazon — quem aplica é o humano. No fim pede a lista já aplicada e sincroniza o espelho do painel (sites-amazon.html) via /admin/amazon-sites/import.
---

# Auditar a Lista de Sites da Amazon

> Skill de **recomendação**. Ela mede, ordena e explica. **Não altera nada na
> Amazon** — não tem como, e não deveria. Quem aplica é o humano, no console.
> O único write dela é o espelho do painel, no fim, e só com a lista que o
> humano confirmar que aplicou.

## Parse de input

- **Sem argumento** → audita a conta do Marcelo (owner default).
- **`owner=Bárbara`** → audita a conta dela. O teto de 50 é **por conta**, e a
  conta se resolve pela TAG do site, não pelo dono editorial.
- **`--dias=N`** → janela do GSC (default 28).

## Modelo

Opus 5 (ou o Opus mais novo disponível). Nunca Sonnet/Haiku.

## O que a skill NÃO faz, declarado

**Não lê a conta da Amazon.** Exige login. A lista vem colada pelo humano, nas
duas pontas.

**Não vê clique de afiliado por tag**, que é o sinal mais forte de risco: um
site não declarado só manda referência pra Amazon quando alguém clica no link.
Esse número está no relatório do Associados. A skill usa **tráfego de busca**
como aproximação e precisa dizer isso no relatório.

**Não altera a Amazon.** Só o espelho local.

## Os critérios, na ordem certa

Há **duas perguntas diferentes**, e misturá-las foi o erro que originou esta
skill.

**Pergunta A, obrigatória: o site exibe link de afiliado?** Se exibe, tem que
estar declarado. Tráfego, DR e ticket são irrelevantes aqui. É binário.

⚠️ Na prática **quase todos exibem** — medido em 2026-08-19: dos 94 no ar, 0
sem link e 3 confirmados vazios por nunca terem sido preenchidos. Um teste que
dá positivo em ~96% quase não informa, então isto é **varredura ocasional**,
não passo de toda execução.

**Pergunta B, de prioridade: quem fica com a vaga escassa?** Só existe porque o
teto força escolher, e **toda escolha aqui é concessão na pergunta A**. Nesta
ordem:

1. **Está no ar e não é redirect.** Redirect e domínio morto são vaga
   desperdiçada — devolvem 4 vagas de graça na medição de 19/08.
2. **Cliques e impressões** (GSC, janela do input).
3. **Posição média**, que separa o que os cliques não separam: no grupo de zero
   clique, posição 10 é topo da 2ª página e posição 75 é 8ª página. `melhorpurificador`
   e `arcondicionado.org` são idênticos por cliques e opostos por posição.
4. **Trajetória, não nível.** Site novo tem tráfego zero por IDADE, não por
   fraqueza. Astro recém-publicado com mil impressões e DR 0 não é candidato a
   corte — é candidato a esperar.
5. **Ticket × comissão.** A tabela da Amazon paga **13% em Beleza/Saúde**, a
   faixa mais alta, e 8% em eletrônicos. Mas ticket domina: R$40 a 13% dá
   R$5,20 e R$1.025 a 8% dá R$82. Ticket alto sozinho também não basta — só
   define o teto do ganho.
6. **Genérico com muitas páginas** costuma render (`analistadeprodutos` 690
   cliques, `compraguia` 217), mas não por ser genérico: `guiamelhores` é
   genérico e fez zero.

**Regra de conta, sempre:** site cuja tag pertence a OUTRA conta vai na lista
DELA. Declarar na sua gasta sua vaga com comissão que entra na conta alheia.

**Custo de sair:** tirar da lista NÃO remove os links. Enquanto o site estiver
no ar monetizando, ele vira site não declarado, que é o problema que a skill
existe pra resolver. Toda recomendação de saída sai acompanhada de "e o que
fazer com os links".

## Pipeline

### Etapa 1 — Receber a lista atual

Pedir a lista colada do console (`/home/account/profile/sitelist`). Normalizar
URL → domínio. **Sem ela a skill não roda**: não há de onde inferir o estado.

### Etapa 2 — O que está no ar

```bash
bun scripts/domains-status-snapshot.ts     # ~23s, 307 domínios
```
Se o snapshot em `_data/domains-status.json` tiver menos de 24h, reusar.

⚠️ **Nunca derive "está no ar" de campo guardado.** O `live` do sites-meta é
setado no deploy e defasa. E rótulo de painel externo mente nas duas direções:
"O domínio não está funcionando" e "Redirecionado" da Hostinger aparecem em
sites que respondem 200 normalmente (7 casos medidos em 19/08).

### Etapa 3 — Tráfego

```bash
bun scripts/gsc-trafego-lote.ts <arquivo-de-dominios> --dias=28 --json
```

Cobre declarados + não declarados de uma vez. O script prefere propriedade
`sc-domain` quando existe, e separa **sem medição** de **zero medido**.

⚠️ **Zero e ausente não são a mesma coisa.** Domínio fora do GSC sai como
`erro`, nunca como 0 cliques. Tratar os dois igual gera recomendação de corte
para site que ninguém mediu.

### Etapa 4 — Atribuir conta e dono

Conta pela **tag** (`config.ts` → `amazon-ids.json`). Dono pelo
`sites-meta.json`, que é o que a coluna Responsável do `sites.html` mostra.

⚠️ **Se a tag não constar no espelho, não invente.** Em 19/08, 10 das 50 tags
em uso não estavam no `amazon-ids.json` (parado em 24/07) porque os sites
nasceram depois. Isso cegou 20% da rede. Nesse caso: reportar como
"conta indeterminada", cair no `sites-meta` para dizer de QUEM é o site, e
avisar que o espelho está velho.

### Etapa 5 — Os dois rankings

**SAIR** — declarados, do pior pro melhor: cliques, impressões, posição,
plataforma, links, e o que fazer com eles.
**ENTRAR** — não declarados, do melhor pro pior, mesmos campos.

Mais três avisos: quem está **fora do GSC** (zero ali é ausência de dado), quem
tem **tag de outra conta**, e quem é **redirect ou está fora do ar**.

### Etapa 6 — Pedir a lista aplicada e sincronizar o espelho

Depois que o humano aplicar no console, pedir a lista final e mandar pro painel:

```
POST /admin/amazon-sites/import   { owner, text, replace: true }
```

O endpoint preserva `status`/`nota` de quem continua, faz backup em
`.painel-backups/{dia}/` e barra encolhimento suspeito (`force: true` libera).
Ele devolve `removidos[]` com a anotação de quem saiu — **mostrar antes de
descartar**: anotação humana não se reconstrói por medição.

⚠️ **Se o humano NÃO colar a lista final, dizer com todas as letras que o
espelho NÃO foi atualizado**, e desde quando está parado. Silêncio aqui recria
o problema que a Etapa 6 existe pra resolver: em 19/08 o espelho estava 25 dias
atrasado e eu apresentei "30 sites não declarados" como medição quando era
inferência sobre dado velho.

E conferir se a lista final bate com a recomendação. Aplicação parcial ou
diferente é informação, não ruído.

## Armadilhas (todas com caso real de 2026-08-19)

1. **Home não representa o site.** Site de listagem não tem link na home; eles
   vivem nos artigos. Julguei 5 sites pela home e errei os 5 — `amelhorpanela`
   tinha 68 links, `whiskyideal` 32, `melhorshampoo` 45.
2. **O caminho do sitemap muda por plataforma.** Astro usa
   `sitemap-artigos.xml`; WordPress usa `sitemap_index.xml` (Yoast). Usar o do
   WordPress num Astro deu 12 falsos "sem link" seguidos.
3. **Rótulo de painel externo não descreve realidade** (ver Etapa 2).
4. **`cfAccount: nenhum` significa fora da Cloudflare**, não conta divergente.
   Contei 25 "divergências de conta" que eram ausência de zona; o número real
   era zero.
5. **Dono editorial ≠ conta.** São eixos diferentes e divergem por desenho: 24
   dos 92 domínios têm responsável compartilhado, que o `cfAccount` sequer
   consegue representar.
6. **Espelho manual envelhece em silêncio.** `amazon-ids.json` e
   `amazon-sites.json` são preenchidos à mão. Checar a data antes de tratar
   qualquer um dos dois como verdade.

## Registrar desvio de execução (obrigatório quando houver)

SE você (a) executou diferente do que esta skill manda, (b) **criou um passo que
ela não tem**, (c) achou a régua ambígua/contraditória, ou (d) topou com bug
numa ferramenta dela — ENTÃO registre antes de fechar:

```bash
bun scripts/skill-log.ts note amazon-lista-sites-auditar <desvio|ambiguidade|bug|inventou-passo> "<o que fugiu e por quê>" [--alvo=<etapa>]
```

Execução limpa **não gera linha** — vazio é dado.
