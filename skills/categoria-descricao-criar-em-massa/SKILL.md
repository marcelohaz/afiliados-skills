---
name: categoria-descricao-criar-em-massa
description: Escreve descrições de VÁRIAS categorias de uma vez, agrupando por categorySlug (não por site). A régua viva é a categoria-descricao-escrever — não reimplementa nada. Só escreve em categoria com ≥1 artigo FINALIZADO (o texto ancora nos artigos; sem artigo prometeria o que não existe) — as demais viram fila de artigos no relatório. Grupos correm em paralelo; DENTRO do grupo é sequencial e cada item recebe o texto dos anteriores (senão saem N descrições irmãs duplicadas). Sub-agents devolvem HTML como DADO e não tocam em arquivo; a mãe grava 1x por site (config.ts é compartilhado), 1 commit. Aceita --site X. Pré-flight: bun scripts/categoria-desc-alvos.ts.
---

## Parse de input

- sem args → todos os alvos da rede
- `--site melhoresporte` → só aquele site
- `--dry` → roda o pré-flight, imprime o plano e PARA (não gera nada)

## O que esta skill É (e não é)

Orquestrador leve. **O trabalho editorial é da `categoria-descricao-escrever`** — os sub-agents LEEM aquela SKILL.md inteira e aplicam a régua dela. Esta aqui só coordena: pré-flight, agrupamento, ordem, escrita centralizada, commit e relatório.

**Nunca resumir a régua editorial aqui dentro.** É a mesma disciplina da `artigo-clonar-em-massa` (v1.54.0): resumo inline vira drift silencioso quando a skill individual evolui. Sub-agent do Agent tool não invoca Skill tool, então ele **lê o arquivo** `.claude/skills/categoria-descricao-escrever/SKILL.md`.

## Invariantes

- **Só categoria com ≥1 artigo FINALIZADO.** `complete` do `loaders.ts`, não "tem artigo". O pré-flight já filtra; a skill não recalcula.
- **Sub-agent NÃO escreve arquivo e NÃO faz git.** Devolve `{site, categorySlug, html}`. A mãe grava. Motivo técnico: as descrições de um site vivem TODAS no mesmo `config.ts` — N sub-agents escrevendo ali se sobrescrevem. Motivo de projeto: REGRA ZERO (sub-agent não faz git).
- **Paralelismo por GRUPO, sequencial dentro dele.** Ver "Por que agrupar" abaixo.
- **Não toca em categoria que já tem descrição.** Reescrever é trabalho da skill individual, sob pedido.
- **Não faz deploy.** Para em commitado + pushed + VPS pull.
- **Site com `contentLocked`** (chave-mestra) é pulado — o pré-flight já exclui.

## Por que agrupar por categoria, e não por site

A mesma categoria se repete em vários sites da rede:

```
glutamina     7 sites   ← 0 descrições existentes pra semear
termogenico   6 sites   ← 0
bicicletas    3 sites   ← 0
whey-protein  3 sites   ← 5 irmãs existentes
creatinas     3 sites   ← 6
```

Sete sub-agents gerando "glutamina" **ao mesmo tempo não veem o que os outros escreveram**. Todos leem o mesmo disco, todos aplicam o mesmo esqueleto, e saem sete textos irmãos — duplicate content fabricado em série, exatamente o que a régua anti-clone da skill individual existe pra impedir, e fatal pra estratégia SERP-monopoly (2+ sites do MESMO nicho).

Por isso: **grupos em paralelo entre si, sequencial dentro do grupo**, cada item recebendo o HTML que os anteriores acabaram de gerar, além das irmãs que já existem no disco.

Os grupos **sem semente** (glutamina, termogênico, bicicletas) são os mais arriscados: o 1º gera às cegas e cada seguinte só tem os anteriores. Não paralelizar ali de jeito nenhum.

## Pipeline

### Etapa 0 — pré-flight (aborta cedo)

```bash
git pull --rebase origin main
bun scripts/categoria-desc-alvos.ts --json
```

Devolve `{ total, grupos: [{categorySlug, alvos, irmasExistentes}], pulados }`.

O script usa o `loadSite` REAL do painel pra decidir "artigo finalizado". **Não reimplementar por regex** — tentei e deu 0 alvos onde havia 31 (2026-07-31).

Se `total === 0`, encerra dizendo que não há o que fazer e imprime os `pulados`.

### Etapa 1 — imprimir o plano

Grupos, alvos por grupo, quantas irmãs de semente cada um tem. Marcar os de semente zero. **Dispara direto, sem confirmação S/N** (paridade com as outras skills em massa). Com `--dry`, para aqui.

### Etapa 2 — gerar (paralelo por grupo, sequencial dentro)

Um "runner" por grupo, todos em paralelo (cap 10 grupos simultâneos). Dentro do runner, um sub-agent por vez.

O prompt de cada sub-agent leva **só os deltas** — a régua vem da skill individual, que ele lê:

1. **Leia `.claude/skills/categoria-descricao-escrever/SKILL.md` INTEIRA e aplique a régua dela.** Especialmente a seção "Régua ANTI-CLONE".
2. Alvo: `{site}` / `{categorySlug}` ("{categoryName}").
3. **Não escreva em arquivo nenhum. Não rode git.** Devolva só o HTML.
4. Contexto de leitura: `sites/{site}/src/config.ts` (nome do site, voz), e os `.mdx` de `content/reviews/` cujo `categorySlug` bate — são os artigos que o §2 tem que refletir.
4.5. **Se o nicho do site for saúde/suplemento, incluir SEMPRE a nota YMYL no prompt** (não improvisar por categoria): sem absoluto de saúde ("seguro", "sem efeitos colaterais", "cientificamente comprovado", "emagrece", "garantido"), e o §3 fecha sugerindo orientação profissional sem prometer resultado. A régua individual já cobre, mas na 1ª execução real eu escrevi a nota só em 3 dos 7 prompts e o resultado saiu **inconsistente dentro do mesmo site**: 4 categorias com ressalva, 2 sem, todas de suplemento. Nenhuma estava errada, mas régua desigual num site inteiro é defeito. **A nota é do NICHO, não da categoria.** Categoria de equipamento (bicicletas, esteiras) dentro de site de suplemento NÃO leva ressalva de saúde.
5. **Anti-clone — divergir de TODAS estas** (colar o HTML inteiro de cada):
   - irmãs já existentes no disco (`irmasExistentes` do pré-flight)
   - **as que os itens anteriores DESTE grupo acabaram de gerar** (colar o HTML)
   - as outras categorias do MESMO site
6. Retorne JSON: `{ "site": "...", "categorySlug": "...", "html": "<p>…</p>" }` — **tags LITERAIS**, não escapadas.

⚠ Mesmo pedindo, o sub-agent costuma devolver o HTML **escapado** (`&lt;p&gt;`). A mãe tem que desescapar na coleta (`html.unescape` se contiver `&lt;p&gt;` e não `<p>`), senão o gate reprova por "0 parágrafos" — ou pior, gravaria entidade literal no config. Aconteceu nos 7 itens da 1ª execução real. Alguns também vêm com prosa antes do JSON: extrair com regex `\{"site".*\}`.

### Etapa 3 — gate mecânico (por item, antes de escrever)

Reprova e manda o sub-agent refazer (máx 3 tentativas):

- 100-2000 chars · 2-3 `<p>` · zero tag de bloco fora da allowlist
- **zero backtick** e **zero `${`** — o helper joga exceção, e `${` dentro do template literal é interpolação JS que corrompe o `config.ts`
- sem travessão, sem `<!--`, sem `[TODO`
- **zero sequência de ≥8 palavras** igual a qualquer irmã (existente ou gerada no grupo)

Não convergiu em 3 → registra no relatório e segue. Nunca grava item reprovado.

### Etapa 3.5 — colisão INTRA-SITE (obrigatória, achada rodando)

O agrupamento por categoria resolve o eixo **cross-site** (mesma categoria em sites diferentes). Ele **não** resolve o eixo **intra-site**: as N categorias de um mesmo site rodam em grupos DIFERENTES, portanto em paralelo, e não veem umas às outras. Num site sem descrição nenhuma, todas geram às cegas entre si.

Não é hipótese. Na 1ª execução real (melhoresporte, 7 categorias, 2026-07-31) deu **2 colisões**:

```
creatinas × whey-protein   mesma família de abertura "Se o seu objetivo é…"
bcaa × pre-treino          8 palavras iguais: "o que realmente muda de um pote para"
```

Então, DEPOIS de gerar e ANTES de escrever, cruzar **todos os itens do mesmo site entre si**:

- zero sequência de ≥8 palavras compartilhada
- famílias de abertura §1 distintas entre todas

Colidiu → regerar **um** dos dois, passando as OUTRAS do site como material anti-clone explícito (além das irmãs cross-site). Repetir até zerar. A régua individual já manda divergir de "(a) outras categorias do mesmo site" — o que faltava era a mãe **ter o material**, que só existe depois da geração.

Sequenciar o site inteiro resolveria na origem, mas custa o paralelismo todo. Gerar em paralelo e consertar a colisão é mais barato e converge: nas 2 ocorrências reais, uma regeração resolveu cada.

### Etapa 4 — escrever (centralizado, 1x por site)

Grava os resultados num `.json` e chama o aplicador. **Não escrever à mão** — é o passo que corrompe `config.ts` se errar, e o script é o mesmo toda vez:

```bash
bun scripts/categoria-desc-aplicar.ts <resultados.json> --dry   # confere
bun scripts/categoria-desc-aplicar.ts <resultados.json>         # grava
```

Formato: `[{ "site": "...", "categorySlug": "...", "html": "<p>…</p>" }]`

O aplicador faz, por conta própria: **o gate mecânico da Etapa 3** (é o último ponto antes do disco, então roda de novo aqui), **backup** por site, encadeia `writeCategoryDescription` em memória e grava **1x por site**, e um **sanity pós-transformação** — se alguma descrição antiga sumiu ou alguma nova não entrou, aquele site é pulado inteiro em vez de gravar pela metade.

Item reprovado não derruba os outros: sai no relatório e o resto grava. Exit 1 se algum site falhou.

### Etapa 5 — validar e commitar

```bash
pnpm --filter {site} build     # por site tocado; Zod + template literal do config
git add sites/*/src/config.ts
git commit --no-verify -m "feat(categorias): descrição de N categorias em M sites via skill"
git push origin main
bash scripts/painel-vps-pull.sh
```

Build falhou → reverte aquele site do backup e reporta. `--no-verify` porque o pre-commit bloqueia edição direta de conteúdo.

### Etapa 6 — relatório

- escritas por site/categoria
- reprovadas no gate (com o motivo)
- **`pulados` do pré-flight, agrupado por motivo** — é a fila de artigos a escrever, sai de graça

## Armadilhas

**Não reimplementar "artigo finalizado".** É `complete` do `loaders.ts` (3+ produtos ∧ guide ∧ intro ∧ meta, ou `contentLocked`). O pré-flight importa a função de verdade.

**Slug malformado é abortar o ITEM, não o lote.** `categorySlug` com acento/maiúscula (ex: `pré-treino`) gera `/categoria/{slug}/` 404 **e** deixa a descrição órfã, porque a chave do config é sempre sem acento (bug real 2026-06-19). O pré-flight já manda esses pra `pulados`.

**Categoria só com página de produto NÃO recebe descrição.** A página existe e está no sitemap desde 2026-07-31, mas o texto é ancorado nos artigos — sem eles ele promete o que não existe. Melhor ausente que mentindo, e a página degrada bem (o bloco não renderiza e a linha abaixo já diz "N produtos analisados"). Canon Marcelo 2026-07-31.

**O `§3` é o pior ofensor de clone.** "...antes de o produto chegar na sua casa" é niche-agnostic e o modelo copia verbatim em todo lugar. A régua individual manda variar ou omitir — respeitar.

**Nomes de categoria divergem entre sites** ("Pré Treino" vs "Pré-Treino"). Usar o `categoryName` do pré-flight, que vem do `.mdx` daquele site, e não normalizar por conta própria.

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
