---
name: rede-analisar
description: "Analisa o desempenho da rede de afiliados (Search Console, Analytics, vendas do Associados, quedas e atualizações do Google, nichos de época) com as regras e os erros já vistos, e grava a análise em docs/analises/ para o Marcelo, a Bárbara e os dois Claudes reverem. Use quando pedirem para analisar o desempenho, ver se os sites estão melhorando ou recuperando, explicar uma alta ou queda de cliques ou de vendas, ou conferir uma análise já feita (modo conferir, que o Claude da Bárbara usa sem os acessos do Mac)."
---

## Parse de input

- Pergunta livre ("analise o gsc e o analytics", "as vendas estão ruins?", "recuperou depois do update?"): análise nova.
- `conferir {pasta ou arquivo de docs/analises}`: confere uma análise já feita, só com os arquivos (é o modo do Claude da Bárbara, que não tem os acessos do Mac).

# Analisar a rede

Pedido do Marcelo (25/11/2026): uma pasta comum com a Bárbara, para as análises ficarem guardadas, serem revistas e conferidas pelo Claude dela, e para o método melhorar com o tempo. A pasta é `docs/analises/` (regras e formato no `LEIA-ME.md` de lá). Até 25/11/2026 cada análise refazia os programas de leitura e as regras viviam só na memória do Claude do Marcelo; os erros listados abaixo saíram dessas análises.

## Invariantes

- **Só leitura** nos sites, no Search Console, no Analytics e no Associados.
- **A pergunta é a base.** Pergunta sobre os últimos dias se responde com os últimos dias; o ano anterior entra só quando muda a conclusão (época do ano, Black Friday), em poucas linhas.
- **De quem são os sites:** "a rede do Marcelo" e "os meus sites" = os sites cujo Analytics é da conta dele (`sites/{site}/src/analytics.json`, campo `conta`; o `rede-ler.ts` separa por isso). Pergunta sobre o Associados de uma pessoa: só os sites dela.
- **Todo número da resposta é conferido na saída do programa** antes de escrever. Nada de conta de cabeça.
- **Fato separado de hipótese.** Causa é hipótese e diz o dado que a apoia. Análise é sinal, não regra.
- **Não sugerir mexer em artigo no ar** por causa de uma análise; decisão é do Marcelo.
- **Fica de fora da pasta comum:** Rank and Rent, finanças pessoais e dados de pessoas. Valor em reais da Amazon pode entrar (decisão do Marcelo, 25/11/2026).

## 0. Ler o que já existe

`docs/analises/LEIA-ME.md` (índice) e a análise anterior do mesmo tema. Parta dela: o que ela concluiu, o "reler em", as correções. Não reabra decisão já tomada (está no CLAUDE.md, nas skills e na memória).

## 1. Ler os dados (só no Mac do Marcelo)

```bash
P=~/Backups/afiliados/analises/{AAAA-MM-DD}-{tema}
bun scripts/rede-ler.ts ler $P --de={AAAA-MM-DD}      # padrão: os últimos 35 dias
bun scripts/rede-ler.ts resumo $P                     # resumo.csv por dono e dia
```
O `ler` grava em `$P/dados/`: Search Console por domínio e dia (Brasil e todos os países), por hora de Brasília nos últimos 9 dias, das páginas de calor; Analytics (só Brasil) de visitas e cliques na Amazon por dia, site, canal, país, hora e página. Programas próprios da análise vão em `$P/scripts/` (fora do repositório) e leem esses arquivos.

- **Vendas do Associados:** pela skill `amazon-relatorios-ler` (Chrome do Marcelo, o perfil que tem a conta logada; em 25/11/2026 era o "Browser 3" de três conectados: confira "Olá, Marcelo" na página inicial antes de ler). Por dia: agrupar por Data, "Últimos 30 dias" ou período personalizado (até 90 dias), digitando as datas nos campos De e Até (formato mês/dia/ano). Por site: agrupar por ID de rastreamento (cada site tem um ID).
- **Painel:** `docs/painel/_data/gsc-snapshot-{marcelo|barbara}.json` tem 28 dias por site (todos os países), já no repositório.

## 2. Regras de comparação (cada uma nasceu de um erro; a lista de erros está abaixo)

1. **Só Brasil** no Search Console. Confira antes os cliques de fora por site e dia (robô de Portugal em 06/11/2026).
2. **Dia incompleto:** o dia de hoje e, às vezes, o de ontem. Por hora, compare só as horas completas dos dois lados (a última hora do Search Console e do Analytics chega pela metade).
3. **Dia da semana:** compare com a média de segunda a sexta e com a proporção que aquele dia costuma ter (domingo 80% a 86% dos dias úteis nos cliques na Amazon antes de 10/11/2026), nunca com o dia anterior.
4. **Base "antes":** dias úteis antes do evento (na atualização de novembro: 02 a 11/11/2026). Promoção (11/11, Black Friday) puxa a base para cima: diga se ela entrou.
5. **Qual site fez a diferença** antes de dizer que um grupo sobe ou cai (um site sozinho já explicou um grupo inteiro: melhoreseletro em 06/11, produtosanalisados em 24/11).
6. **Nicho de época à parte:** calor de dezembro a fevereiro (`ehPaginaDeCalor` em `scripts/lib/rede-analise.ts`). Dê o número com e sem.
7. **Cliques de gente na Amazon = evento do Analytics.** O Associados conta mais (1,6 a 2 vezes) e, desde 22/11/2026, um robô que segue os links sem rodar o Analytics. Conversão de verdade = pedidos ÷ cliques do Analytics. Salto no Associados sem salto no Analytics: confira por ID de rastreamento e veja se o site teve visita.
8. **Vendas:** separe quantidade de pedidos por clique de gente e valor por pedido. Com menos de ~30 pedidos no período, um pedido caro muda a conta: diga isso.
9. **Search Console por busca ou por página perde cliques** (buscas anônimas; página com filtro de país perde mais da metade). Para separar um nicho, conte pelas páginas (filtro de página), não pelas buscas; para total, use o total do site por dia.
10. **Série semana a semana** quando a pergunta é tendência.

## 3. Escrever

`docs/analises/{AAAA-MM-DD}-{tema}/RELATORIO.md` no formato do `LEIA-ME.md` (pergunta com as palavras de quem perguntou, fontes e período, números, leitura, reler em), mais o `resumo.csv` e as tabelas pequenas que a análise usou (até umas dezenas de KB; o bruto fica no Mac). No chat: a análise inteira, em português simples, sem abreviação e sem metáfora.

Correção depois (inclusive na mesma conversa): no topo do relatório, com a data e o que mudou; na resposta, às claras, no começo. E uma nota no registro de erros (passo 5).

## 4. Guardar e avisar

```bash
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" && test -f docs/painel/sites-meta.json || { echo "cwd errado"; exit 1; }
bash scripts/git-pull-seguro.sh "rede-analisar"
bun scripts/analises-indice.ts
git add docs/analises/
git commit -m "análise: {tema} ({data})" -m "Co-Authored-By: {modelo da sessão} <noreply@anthropic.com>"
git push origin main
```
- **Recado à outra pessoa** só quando a análise muda o trabalho dela (queda nos sites dela, robô no Associados): `bun scripts/recados.ts postar novidade "..." --fonte=docs/analises/{pasta}` com a conclusão em poucas linhas e o caminho; no máximo 600 caracteres; nada de Rank and Rent nem finanças.
- **Memória:** só um ponteiro curto para o arquivo (a análise mora aqui, não na memória).

## 5. Registro de erros do método

Erro achado depois (por quem perguntou, por conferência, pelo Claude da Bárbara ou na releitura) vira nota, com o caso real:
```bash
bun scripts/skill-log.ts note rede-analisar <desvio|ambiguidade|bug|inventou-passo> "<o que foi dito, o que estava certo, a regra que faltou>" [--ctx=docs/analises/{pasta}]
```
Na leitura em lote do `skill-log`, a nota que se repete vira regra no passo 2 e entra na lista abaixo.

## Erros já vistos (casos reais)

| Data | Erro | Regra que saiu |
|---|---|---|
| 06/11/2026 | Comparação com 2025 com todos os países deu "metade" em vez de 40% | 1 |
| 06/11/2026 | Semana baixa atribuída à eleição sem olhar 2025 (caiu 11% nos dois anos) | invariante da pergunta |
| 06/11/2026 | "Seus sites caem devagar" era um site só (melhoreseletro) | 5 |
| 09/11/2026 | Soma por página com filtro de país perdeu mais da metade dos cliques | 9 |
| 23/11/2026 | Domingo comparado com o sábado e a rede toda somada numa pergunta só da parte dele | 3 e "de quem são os sites" |
| 24/11/2026 | Hoje somado até as 13h e os outros dias até as 13h, com hoje só até as 10h | 2 |
| 24/11/2026 | Conversão do Associados caiu para 1%: era robô (sites pequenos com 15 a 38 cliques e zero visita) | 7 |
| 24-25/11/2026 | "Quase tudo voltou" somava o calor, que triplicou; sem ele, ~80% | 6 |
| 25/11/2026 | Calor medido pelas buscas no Search Console perdia as buscas anônimas | 9 |

## Modo conferir (Claude da Bárbara, ou o do Marcelo numa análise dela)

Sem os acessos do Mac:
1. Leia o relatório inteiro e as correções do topo.
2. Refaça as contas com o `resumo.csv` e as tabelas da pasta (e o retrato do painel, `docs/painel/_data/gsc-snapshot-*.json`, para os últimos 28 dias).
3. Passe as regras do passo 2 uma por uma: base, dia incompleto, dia da semana, site que fez a diferença, época, robô.
4. Responda por recado (`pergunta` se algo não fecha, com o número e a linha; `novidade` se confirma) e, se achou erro, uma nota no registro (passo 5). Não edite o relatório de outro lado: quem fez corrige no topo.
