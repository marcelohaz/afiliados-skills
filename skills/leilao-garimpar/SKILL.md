---
name: leilao-garimpar
description: Analisa a lista "processo de liberação" do Registro.br pra garimpar domínios afiliado de PRODUTO FÍSICO. Roda o pipeline oficial do painel (leilao-afiliados-processor) E as passadas complementares (scripts/leilao-afiliados-passadas.ts) que pegam o que o funil estrito deixa escapar — exact-match-cru (produto=domínio), prefixo melhor/top, decomposição produto+spec/marca+produto/plural-de-composto. Cruza com domains.json (já meus), catálogo garimpo (já é kw) e blocklist (deletados). Cura por margem/intenção (mantém alto-ticket; corta bebê/esporte/commodity/serviço/infoproduto/falso-positivo) e entrega shortlist em tiers com exact-cru no topo. READ-ONLY: registro é decisão do Marcelo. Mantém histórico curado por período. Termina ATUALIZANDO a seção Aprendizados. Input: caminho do .txt (Marcelo baixa e manda).
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
cd /Users/marcelo/Documents/Claude/Projects/ProjetoAfiliados
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
- Já-meus (domains.json) e blocklist (deletados) já foram ocultados/pulados.

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

## Aprendizados (apêndice vivo — ATUALIZAR a cada run)

> Ao final de CADA run: anexar o que escapou, termo/padrão novo, produto a adicionar no `PRODUTOS_EXTRA`, e decisão do Marcelo que vire regra.

**v1 — 2026-06-11 (lista 10-17/06, 112.691 dom → 19 oficiais + 29 complementares)**
- **Gap estrutural do processador**: "exact" só casa contra o CATÁLOGO (512 kw), não contra `PRODUTOS_EXTRA` — por isso `webcam.com.br` (estava em PRODUTOS_EXTRA) NÃO foi pego pelo oficial. A Passada exact-cru cobre. Fix possível no processador (exact também olhar prodSet) é arriscado (floda produto-qualif na aba) → manter a passada como rede.
- **Marcelo valoriza muito o exact-match-cru** (produto=domínio limpo, sem "melhor"): webcam, mousegamer, camerawifi, celularxiaomi. É o tier de topo.
- Produtos adicionados ao `PRODUTOS_EXTRA` neste run: magnesio, colageno, copotermico, cafeteiraespresso, headphone(s), perfume, armario, aquecedor(agas/eletrico), fonteatx, smartwatch, relogiointeligente, nobreak, mesagamer, poltrona, videoporteiro, scanner, irrigadororal, frigobar, lavalouca, circulador, caixadesombluetooth.
- Falsos-positivos recorrentes: `fonteoficial`/`fontepremium` (fonte=origem), `celularprofissional`/`mouseautomatico`/`controleindustrial` (não-termo). Barrar sempre.
- A sweep de marca veio quase toda ruído (ninja*=infoproduto, stanley*/arno*/bosch* não são a marca) — marca+produto rende pouco; foco em exact-cru + prefixo + produto+spec.

**v1.1 — 2026-06-11 (QA pós-build + amostragem ampla pra filtragem humana)**
- **Bug do teto de SLD**: o helper cortava em 24 chars, e `asmelhoresgarrafastermicas` (26) escapava. Corrigido pra 40 — domínio de leilão JÁ EXISTE (é válido por definição); o processador oficial não tem teto máx, só mín 4. Lição: não inventar teto máximo de SLD pra leilão.
- **Cross-ref de blocklist pegou um erro MEU**: recomendei à mão `melhorperfumefeminino`/`masculino`, mas estão na blocklist (faxina beleza-saúde de 2026-05-08). O helper corretamente pulou. **A curadoria manual não tem a memória que o cross-ref tem — sempre confiar na blocklist.** Removidos do histórico.
- **RESOLVIDO — política beleza-saúde (Marcelo 2026-07-23)**: beleza-saúde **CONSUMÍVEL/cosmético** (perfume, perfumefeminino, perfumemasculino, maquiagem, batom, rímel, sérum, protetor solar) é **OUT do garimpo** — nicho de ROI baixo pra ADQUIRIR domínio novo. Removidos do `PRODUTOS_EXTRA` (o dicionário que faz o garimpo surfaçar candidatos), então não aparecem mais na shortlist. **Devices de grooming high-ticket ficam** (chapinha/secador/modelador/babyliss/depilador/barbeador/aparador — Fase 5 já mandava MANTER). ⚠️ **A regra é escopada só ao GARIMPO**: não afeta domínios/sites de beleza que o Marcelo já tem — esses se trabalham normal (conteúdo/páginas/etc.).
- **Amostragem ampla** (controle de recall humano): gerar TSV com `alta` (recomendados) + `revisar` (melhor/melhores/os-as-melhores X fora do dict, com flag `[blocklist]`) e o Marcelo filtra. Net amplo demais (`qual`/`guia`/`comprar`/`top`/sufixo) = 95% ruído (colisão "qualidade", "guia de cidade", nome de empresa) — ficar no **melhor-family**. Restam baixo-valor não-pegos: make/amaciante (consumível), applewatchstore (sufixo "store" no JUNK).

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
