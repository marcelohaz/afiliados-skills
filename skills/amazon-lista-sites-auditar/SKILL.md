---
name: amazon-lista-sites-auditar
description: >-
  Audita a Lista de Sites do Associados Amazon (teto de 50 por conta) e RECOMENDA quem entra e quem sai. Lê a lista no Chrome da pessoa (ou recebe colada), mede o que está no ar por sonda HTTP, puxa tráfego do GSC das contas com token, confere a conta de cada tag e devolve dois rankings lado a lado: declarados do pior pro melhor (candidatos a sair) e não declarados do melhor pro pior (candidatos a entrar). Só aplica a troca na Amazon com o sim da pessoa para aquela troca. No fim sincroniza o espelho do painel (sites-amazon.html) via /admin/amazon-sites/import.
---

# Auditar a Lista de Sites da Amazon

> Skill de **recomendação**. Ela mede, ordena e explica. **Na Amazon, só lê**,
> até a pessoa dizer sim para a troca recomendada: mudar a lista é mudar a
> conta, e isso pede o sim dela, a cada vez. Com o sim, a troca é feita no
> Chrome dela (Etapa 6). O outro write é o espelho do painel, no fim, com a
> lista que ficou gravada na Amazon.

## Parse de input

- **Sem argumento** → audita a conta do Marcelo (owner default).
- **`owner=Bárbara`** → audita a conta dela. O teto de 50 é **por conta**, e a
  conta se resolve pela TAG do site, não pelo dono editorial.
- **`--dias=N`** → janela do GSC (default 28).

## O que a skill NÃO faz, declarado

**Não lê a conta da Amazon sem o Chrome da pessoa.** A conta exige login, e o
Claude nunca digita senha: lê pelo Claude in Chrome, na conta já logada,
avisando antes o quê, o site (`associados.amazon.com.br`) e a conta. Sem o
Chrome, a lista vem colada pela pessoa.

**Não vê clique de afiliado por tag**, que é o sinal mais forte de risco: um
site não declarado só manda referência pra Amazon quando alguém clica no link.
Esse número está no relatório do Associados. A skill usa **tráfego de busca**
como aproximação e precisa dizer isso no relatório.

**Não altera a Amazon sem o sim.** A recomendação sai primeiro; a troca, só
depois do sim da pessoa para ela.

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
6. **Ser genérico não é critério.** Site genérico com muitas páginas costuma ir bem nos itens 2 e 3, mas quem decide são cliques e posição, não o tipo: há genérico com zero clique.

**Regra de conta, sempre:** site cuja tag pertence a OUTRA conta vai na lista
DELA. Declarar na sua gasta sua vaga com comissão que entra na conta alheia.

**Custo de sair:** tirar da lista NÃO remove os links. Enquanto o site estiver
no ar monetizando, ele vira site não declarado, que é o problema que a skill
existe pra resolver. Toda recomendação de saída sai acompanhada de "e o que
fazer com os links".

## Pipeline

### Etapa 1 — Receber a lista atual

Ler a lista em `https://associados.amazon.com.br/home/account/profile/sitelist`,
no Chrome da pessoa (avisar antes, ver acima), ou pedir que ela cole. Conferir o
StoreID no topo da página (a do Marcelo é `escritorioeca-20`): a lista é por
conta. Cada site é um elemento `.ac-site-name`; leia todos por JavaScript e
normalize URL → domínio (a resposta da ferramenta corta perto de 1.000
caracteres: leia em duas metades). Compare com o espelho do painel
(`GET /admin/amazon-sites`, campo `declared`): diferença entre os dois é a
primeira coisa a relatar. **Sem a lista a skill não roda**: não há de onde
inferir o estado.

### Etapa 2 — O que está no ar

```bash
bun scripts/domains-status-snapshot.ts     # ~23s, 307 domínios
```
Se o snapshot em `docs/painel/_data/domains-status.json` tiver menos de 24h, reusar.

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

⚠️ **Se a tag não constar no espelho, não invente.** O `docs/painel/amazon-ids.json` é preenchido à mão
e não tem os sites mais novos que ele. Nesse caso: reportar como
"conta indeterminada", cair no `sites-meta` para dizer de QUEM é o site, e
avisar que o espelho está velho. Duas fontes resolvem a conta de verdade: a
página `https://associados.amazon.com.br/home/account/tag/manage` (os IDs de
rastreamento da conta logada, lidos por JavaScript no Chrome) e os
`tracking-id.csv` da `amazon-relatorios-analisar` (só os IDs com movimento).
Em 19/10/2026, 5 tags ausentes do espelho estavam na conta do Marcelo.

O `GET /admin/amazon-sites` já cruza tudo isso por site (campos `account`,
`state`, `http`, `stack`, `declared`): comece por ele. Site fora do repositório
(WordPress antigo) não aparece ali: liste os domínios que respondem em
`docs/painel/_data/domains-status.json` (`estado` `wordpress` ou `astro`) e
leia a tag nos posts pelo `wp-json` (`/wp-json/wp/v2/posts?per_page=5`; site
de listagem costuma ter o conteúdo em `/pages`).

### Etapa 5 — Os dois rankings

**SAIR** — declarados, do pior pro melhor: cliques, impressões, posição,
plataforma, links, e o que fazer com eles.
**ENTRAR** — não declarados, do melhor pro pior, mesmos campos.

Mais três avisos: quem está **fora do GSC** (zero ali é ausência de dado), quem
tem **tag de outra conta**, e quem é **redirect ou está fora do ar**.

### Etapa 6 — Aplicar (só com o sim) e sincronizar o espelho

**Aplicar, se a pessoa disser sim para a troca recomendada** (19/10/2026, 9
trocas na conta do Marcelo), na mesma página da Etapa 1:
- Remover: cada site tem um X (`.ac-site-icon-close`, dentro do mesmo bloco do
  `.ac-site-name`); o `click()` por JavaScript funciona.
- Pôr: preencher a caixa "Insira seu site" (placeholder
  `https://www.example.com/myblog`) com `https://dominio`, disparando `input` e
  `change`, e clicar no botão "Adicionar" ao lado. Tire antes de pôr: o teto é 50.
- Remover e pôr só mudam a tela. **Nada fica gravado até o botão "Confirmar"**,
  que aparece depois da primeira mudança. Antes de clicar nele, compare a lista
  da tela, inteira, com a esperada (zero faltando, zero sobrando). Clique de
  verdade em "Confirmar"; a página responde "Sites e Apps atualizados".
- Recarregue a página e leia a lista de novo: é ela que vale.

Sem o sim, a pessoa aplica no console e cola a lista final. Nos dois casos, a
lista que ficou gravada vai para o painel:

```
POST /admin/amazon-sites/import   { owner, text, replace: true }
```

O endpoint preserva `status`/`nota` de quem continua, faz backup em
`.painel-backups/{dia}/` e barra encolhimento suspeito (`force: true` libera).
Ele devolve `removidos[]` com a anotação de quem saiu — **mostrar antes de
descartar**: anotação humana não se reconstrói por medição.

⚠️ **O import não faz commit** (19/10/2026): o handler grava
`docs/painel/amazon-sites.json` na VPS, mas o arquivo não está na whitelist do
commit automático. Até isso ser consertado, confira na VPS
(`git status --short docs/painel/amazon-sites.json`) e, se estiver sujo, faça o
commit lá mesmo e envie. Se o gancho de envio da VPS barrar por testes de
outras rotas, confira que o commit só tem esse arquivo antes de usar
`PULAR_TESTES_PAINEL=1`.

⚠️ **Se a lista final não foi lida nem colada, diga com todas as letras que o
espelho NÃO foi atualizado**, e desde quando está parado. Sem isso, a próxima
execução apresenta inferência sobre dado velho como se fosse medição.

E conferir se a lista final bate com a recomendação. Aplicação parcial ou
diferente é informação, não ruído.

## Armadilhas

1. **Home não representa o site.** Site de listagem não tem link na home; eles
   vivem nos artigos (`amelhorpanela`: 68 links nos artigos). Julgue pelos artigos.
2. **O caminho do sitemap muda por plataforma.** Astro usa
   `sitemap-artigos.xml`; WordPress usa `sitemap_index.xml` (Yoast). Usar o do
   WordPress num Astro deu 12 falsos "sem link" seguidos.
3. **Rótulo de painel externo não descreve realidade** (ver Etapa 2).
4. **`cfAccount: nenhum` significa fora da Cloudflare**, não conta divergente.
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
