---
name: leilao-garimpar
description: "Analisa a lista \"processo de liberação\" do Registro.br e devolve a shortlist de domínios bons para site afiliado de produto físico, mais o alerta de domínios nossos que estão sendo liberados. Use quando o Marcelo mandar a lista do leilão ou pedir o garimpo do leilão (sem arquivo, a skill baixa a lista). Só recomenda: registro e compra são do Marcelo. Não é o garimpo de keywords (garimpo-afiliados-loader)."
---

# Garimpo da lista de leilão afiliado (processo de liberação Registro.br)

**Input** ($ARGUMENTS): caminho do `lista-processo-liberacao.txt` (header `# Processo de liberação no período de X a Y`, ~110-130k domínios). **Sem argumento = baixe você mesmo** com `bun scripts/refresh-leilao-afiliados.ts` (baixa a lista do Registro.br e roda o mesmo processador) — não pare para pedir o arquivo (canon 2026-08-15).

**Objetivo**: devolver a shortlist dos **bons domínios afiliado produto-físico** que estão sendo liberados — livres em breve, intenção comercial, alto ticket.

**Princípio**: o processador oficial é a espinha dorsal (consistência na aba Leilão do painel); as passadas complementares são a rede de segurança (o funil estrito só casa "exact" contra o catálogo, então bare-produto do dicionário expandido escapa). **NUNCA registrar/comprar — a compra é do Marcelo, sempre.**

## ⚠️ Não confundir com garimpo
Garimpo (`garimpo-afiliados-loader`) = você define keyword, sistema checa via WHOIS se `kw.com.br` está livre (proativo). **Leilão** (esta skill) = consome a lista pronta do Registro.br e filtra os afiliado-like (reativo). Já contaminei o pipeline uma vez cadastrando candidatos de leilão como keywords do garimpo — **não repetir**.

## Fase 1 — Sanidade + roteamento
- **Encoding Latin-1 (ISO-8859) + CRLF.** Ler em Python/bun com `latin1` e tirar `\r`. **NUNCA usar grep do macOS nesse arquivo** (BSD grep trata como binário e devolve vazio em SILÊNCIO — mordeu o R&R em 2026-06-10; aqui o CRLF também quebra `$` no grep). Os scripts já tratam isso; varredura ad-hoc = Python/bun.
- Confirmar header `# Processo de liberação` + período + contagem plausível (~110-130k).
- **Se NÃO tiver esse header** → é garimpo (lista de keywords), não leilão → PARA e avisa.

## Fase 2 — Pipeline oficial (sempre primeiro)
```bash
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" && test -f docs/painel/sites-meta.json || { echo "⛔ cwd errado ($(pwd)): rode a partir da raiz do ProjetoAfiliados"; exit 1; }
bun -e "import { processarLeilaoAfiliadosTexto } from './docs/painel/_lib/leilao-afiliados-processor.ts';
const raw = Buffer.from(await Bun.file('<CAMINHO>').arrayBuffer()).toString('latin1');
const { snap, outPath } = await processarLeilaoAfiliadosTexto(raw, { fonte: 'upload' });
console.log(snap.periodo, snap.totalLista, '→ afiliado', snap.totalAfiliado, '| exact', snap.totalExact, 'melhor-top', snap.totalMelhorTop, 'produto-qualif', snap.totalProdutoQualif);"
```
Gera `_data/leiloes-afiliados/leilao-{periodo}.json` + `latest.json` (alimenta a aba Leilão). Funil: TLD `.com.br` → exact/melhor-top (catálogo) / produto-qualif (catálogo+`PRODUTOS_EXTRA`) → exclui cidade/nicho-rr/infoproduto/evento/ano/blacklist → score.

## Fase 3 — Passadas complementares (rede de segurança)
```bash
bun scripts/leilao-afiliados-passadas.ts <CAMINHO>
```
Faz, sobre a lista crua: **exact-match-cru** (produto=domínio sem prefixo, ex: `webcam`/`mousegamer`/`celularxiaomi` — o que o Marcelo mais valoriza), **prefixo afiliado** (melhor/melhores/top/os-as), **decomposição** (produto+spec `camerawifi`, marca+produto, plural de composto `garrafastermicas`). Já cruza com domains.json/catálogo/blocklist/histórico. Grava `candidatos-{periodo}.json`. Dicionário = `PRODUTOS_EXTRA` do processador + catálogo garimpo (fonte única).

## Fase 4 — Merge + cruzamentos
- Unir candidatos do processador (Fase 2) + do helper (Fase 3), dedup por domínio.
- Flags do helper: `já-kw` (já é keyword nossa — relevância alta), `↩ recorrente` (apareceu em período anterior do histórico curado), categoria.
- Blocklist (deletados) já foi pulada.

### 🚨 4.1 — Domínio NOSSO na lista é ALERTA, não ruído (canon 2026-09-07)
O helper conta os "já-meus" como pulados e **some com eles**. Mas a lista é de **processo de
liberação**: domínio nosso ali dentro significa que ele **vai ser liberado nesta janela** — ou seja,
expirou e não foi renovado. Isso é mais urgente que a shortlist inteira (a shortlist é oportunidade,
isso tem prazo). **Sempre extrair e reportar no TOPO:**
```bash
python3 -c "
import json;lista={l.strip().lower() for l in open('<CAMINHO>','rb').read().decode('latin1').split(chr(10)) if l.strip() and not l.startswith('#')}
d=json.load(open('docs/painel/domains.json'));rows=d['domains'] if isinstance(d,dict) else d
for r in rows:
    if r['domain'].lower() in lista: print(r['domain'], r.get('expiresAt'), r.get('conta'), r.get('site'))"
```
Confirme por **sinal vivo** antes de afirmar (o `expiresAt` do `domains.json` vem de CSV e envelhece —
ver [[feedback_dominio_expirado_csv_e_foto_nao_estado_atual]]): no RDAP do Registro.br, domínio em
liberação volta **sem campo `status`**, enquanto domínio ativo volta `status=['active']`. Use um
controle positivo conhecido na mesma rodada — o `remarks: truncated` aparece nos DOIS e não separa nada.
Medido em 07/09/2026: **8 domínios nossos** (conta Ozéia, todos expirados em abril, sem site) estavam
na lista e teriam passado batido. Dá pra renovar no Registro.br até a liberação.

### 4.2 — Recorrência: cruzar também com run NÃO curada
O flag `↩ recorrente` lê só o `historico-curado.json`. Run processada e **não curada** (havia uma de
agosto/2026) fica invisível, e repetição vira "novo" no relatório. Antes de comparar, cruze também os
`candidatos-{periodo}.json` de períodos anteriores — recorrência é sinal (ninguém pegou o domínio).

## Fase 5 — Curadoria (o julgamento — é seu, não do script)
O helper dá recall; aqui entra a precisão. Para cada candidato:
- **MANTER**: produto físico de **alto ticket / intenção comercial** — eletrônicos, eletrodomésticos, cozinha eletroportátil, suplementos, móveis, ferramentas, devices de beleza (chapinha/depilador/aparador), segurança (câmera/fechadura).
- **CORTAR**: bebê (carrinho/chupeta/banheira/cadeirinha — exceto se alto-ticket claro), esporte/bola, commodity/consumível baixa-margem (mop, amaciante, maquiagem genérica), serviço, infoproduto, conteúdo, carro/veículo.
- **FALSO-POSITIVO a barrar** (caso real): `fonteoficial`/`fontepremium` (o processador casa "fonte"=fonte de PC, mas aqui é "fonte/origem" genérico) — `fonteatx`/`fontedealimentacao` SIM (inequívoco). `celularprofissional`/`mouseautomatico`/`controleindustrial` = não são termos de busca reais → cortar. Termo ambíguo (`ferroplus`: ferro-suplemento × ferro-de-passar) → cortar ou marcar dúvida.
- **Tiers de saída** (ordem fixa):
  1. 🎯 **Exact-match cru** (produto=domínio, sem prefixo) — prioridade nº 1 do Marcelo.
  2. 🟢 **"melhor/melhores X"** de produto forte (intenção de review).
  3. 🟡 **Tier 2** — produto+qualificador / marca+produto / ticket médio / domínio fraco.
  4. ⚪ **Descartados com motivo** (mostrar pra provar que conferiu).
- **Convergência**: quando ampliar dicionário/passadas não traz nada novo = poço seco, pode fechar. Sinalizar isso.
- **Falso-positivo tem forma fixa: `{produto}{qualificador-vazio}`** (celularcerto, geladeiracerta, mesaspremium, dronedigital, alarmesmart, fonteoficial). Se o par produto+adjetivo não é como alguém digita no Google, corta. Casar na regex não basta: confira se o par existe no mundo (`climatizadorultrasonico` casa, mas climatizador é evaporativo).
- **Beleza/saúde consumível ou cosmético** (perfume, maquiagem, batom, sérum, protetor solar) fica fora: ROI baixo para comprar domínio novo (Marcelo, 23/07/2026). Devices de grooming ficam. Vale só para o garimpo, não para sites de beleza que já existem.
- **Cortes recorrentes:** conteúdo (`receitasairfryer`), usados (`notebookusados`), B2B (`tabletindustrial`), prefixo não brasileiro (`reviewcadeiras`).
- **Onde o recall falha:** o exact-cru convergiu (varredura independente de 208 produtos em 09/2026 não achou nada novo). O que escapa é (a) a família `^(o|a|os|as)?(melhor|melhores|top)` com produto fora do dicionário, filtrando serviço e cidade por regex, e (b) `^produto+qualificador$` com lista fechada de qualificadores que formam termo real (eletrica, digital, inteligente, gamer, portatil, wifi, inox, vertical, embutir, externa, ip, kamado, passagem). `contains produto` sozinho é quase todo substring falsa.
- **Blocklist vence a memória:** o que o helper pulou por blocklist fica fora, mesmo que pareça bom.

## Fase 6 — Output
- Shortlist em tiers (tabela: domínio · produto · flag). **Lembrete**: são domínios **expirando na janela do header** — entram pra registro quando liberados, não estão livres agora.
- **READ-ONLY. Registro é decisão do Marcelo.** Não commitar/publicar sem "pode subir".

## Fase 7 — Histórico + pós-compra
- **Histórico curado** (`_data/leiloes-afiliados/historico-curado.json`, schema `{runs:[{periodo,curadoEm,totalLista,candidatos,exactCru[],melhorX[],tier2[],registrados[]}]}`): ao fechar a curadoria, **anexar a run deste período** (substituir se o período já existe). É o que dá o "novos × recorrentes" no próximo mês e o histórico dos leilões passados. (Os snapshots crus por período já ficam em `leilao-{periodo}.json`; este arquivo é a camada CURADA.)
- **Pós-compra**: quando o Marcelo disser o que registrou, preencher `registrados[]` da run + cadastrar em `domains.json` (form normal, com expiresAt real) → o helper passa a ocultar automaticamente.
- **Publicar (só se pedido)**: a Fase 2 já escreveu `latest.json` (aba Leilão local). Pra subir no painel VPS: commit dos JSONs + `bun docs/painel/gen.ts` + `bash scripts/painel-vps-pull.sh`.

## Regras invioláveis
- **NUNCA registrar/comprar** — só recomendar. Janela é curta: entregar no mesmo dia.
- **NÃO cadastrar candidato de leilão como keyword do garimpo** (a contaminação que já aconteceu).
- **NÃO tocar** em `garimpo-snapshot-afiliados.json` nem no WHOIS do garimpo (outro processo).
- READ-ONLY por default; commit/deploy só com pedido explícito.
- Crescer o dicionário = editar `PRODUTOS_EXTRA` no `leilao-afiliados-processor.ts` (fonte única; a aba Leilão também melhora). Nunca duplicar dicionário no helper.

---

## Aprendizados

Ao fim de cada run, o que mudar a curadoria vira regra na Fase 5 ou produto no `PRODUTOS_EXTRA`; o registro da run vai na mensagem do commit, não nesta skill.

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
