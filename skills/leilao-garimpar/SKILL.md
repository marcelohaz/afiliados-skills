---
name: leilao-garimpar
description: "Analisa a lista \"processo de liberação\" do Registro.br e devolve a shortlist de domínios bons para site afiliado de produto físico, mais o alerta de domínios nossos que estão sendo liberados. A lista é a mesma do Rank and Rent e fica guardada em shared-scripts/leiloes; a skill lê os achados que o R&R deixou para o afiliados e grava os de serviço local para o R&R. Use quando o Marcelo mandar a lista do leilão ou pedir o garimpo do leilão (sem arquivo, usa a lista guardada ou baixa e guarda). Só recomenda: registro e compra são do Marcelo. Não é o garimpo de keywords (garimpo-afiliados-loader)."
---

# Garimpo da lista de leilão afiliado (processo de liberação Registro.br)

**Entrada: a lista mora em `../shared-scripts/leiloes/`** (pasta irmã do repositório, repo `marcelohaz/shared-scripts`), UMA cópia para o afiliados e o Rank and Rent (decisão do Marcelo, 07/10/2026; ver `shared-scripts/leiloes/LEIA-ME.md`). O Registro.br publica uma lista por mês no mesmo endereço, que é sobrescrito: a lista que não foi guardada lá não se baixa mais. As funções são as de `shared-scripts/leiloes/lista.ts`; não mude nome nem parâmetro delas (o R&R usa as mesmas).

1. **O Marcelo mandou um arquivo** ($ARGUMENTS): guarde antes de analisar, com os bytes como vieram, e use o caminho impresso como `<CAMINHO>`:
   ```bash
   cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" && test -f docs/painel/sites-meta.json || { echo "⛔ cwd errado ($(pwd)): rode a partir da raiz do ProjetoAfiliados"; exit 1; }
   bun -e "import { guardarLista } from '../shared-scripts/leiloes/lista.ts'; const r = guardarLista('liberacao', new Uint8Array(await Bun.file('<ARQUIVO>').arrayBuffer())); console.log(r.jaExistia ? 'já estava guardada:' : 'guardada:', r.caminho, r.de, r.ate)"
   ```
   A lista **competitiva** (poucas centenas de domínios; o Registro.br chama de processo competitivo) vai com `'competitivo'` no lugar de `'liberacao'`, para `leiloes/competitivo/`. O cabeçalho das duas é igual: quem separa é o tamanho e o nome do arquivo.
2. **Sem arquivo:** veja a lista mais recente guardada:
   ```bash
   bun -e "import { listaGuardada } from '../shared-scripts/leiloes/lista.ts'; const l = listaGuardada('liberacao'); console.log(l ? l.de + ' a ' + l.ate + ' ' + l.caminho : 'nenhuma')"
   ```
   - Período que começou há 25 dias ou menos é a lista do mês (a janela do R&R já baixou): use esse caminho e rode a Fase 2.
   - Senão, rode `bun scripts/refresh-leilao-afiliados.ts`: ele baixa a lista, guarda na pasta se o período for novo e já roda o processador (a Fase 2 fica feita). Use o caminho que ele imprime ("guardada em" ou "já estava guardada em"). Se o período devolvido já tem run no `historico-curado.json`, a lista nova ainda não saiu (o período começa na 2ª quarta-feira do mês): diga isso ao Marcelo em vez de refazer a análise.
   - Não pare para pedir o arquivo (canon 2026-08-15).

Guarde `<DE>` e `<ATE>` (as datas do período, `AAAA-MM-DD`): os arquivos de achados usam as duas.

**Objetivo**: devolver a shortlist dos **bons domínios afiliado produto-físico** que estão sendo liberados — livres em breve, intenção comercial, alto ticket.

**Princípio**: o processador oficial é a espinha dorsal (consistência na aba Leilão do painel); as passadas complementares são a rede de segurança (o funil estrito só casa "exact" contra o catálogo, então bare-produto do dicionário expandido escapa). **NUNCA registrar/comprar — a compra é do Marcelo, sempre.**

## ⚠️ Não confundir com garimpo
Garimpo (`garimpo-afiliados-loader`) = você define keyword, sistema checa via WHOIS se `kw.com.br` está livre (proativo). **Leilão** (esta skill) = consome a lista pronta do Registro.br e filtra os afiliado-like (reativo). Já contaminei o pipeline uma vez cadastrando candidatos de leilão como keywords do garimpo — **não repetir**.

## Fase 1 — Sanidade + roteamento
- **Encoding Latin-1 (ISO-8859) + CRLF.** Ler em Python/bun com `latin1` e tirar `\r`. **NUNCA usar grep do macOS nesse arquivo** (BSD grep trata como binário e devolve vazio em SILÊNCIO — mordeu o R&R em 2026-06-10; aqui o CRLF também quebra `$` no grep). Os scripts já tratam isso; varredura ad-hoc = Python/bun.
- Confirmar header `# Processo de liberação` + período + contagem plausível (~110-130k).
- **Se NÃO tiver esse header** → é garimpo (lista de keywords), não leilão → PARA e avisa.

### 1.1 — Achados que o R&R deixou para o afiliados
```bash
bun -e "import { caminhoDosAchados } from '../shared-scripts/leiloes/lista.ts'; console.log(caminhoDosAchados('<DE>', '<ATE>', 'rr'))"
```
Se o arquivo existir (`achados/<DE>_a_<ATE>-do-rr-para-o-afiliados.md`, uma linha por domínio: `- dominio.com.br — por quê`), esses domínios entram como candidatos na Fase 4, marcados **"veio do R&R"**, e passam pela mesma curadoria da Fase 5. Não existir é normal: a janela do R&R pode não ter rodado ainda.

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
- Unir candidatos do processador (Fase 2) + do helper (Fase 3) + os achados do R&R (1.1, com a marca "veio do R&R"), dedup por domínio.
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
- Shortlist em tiers (tabela: domínio · produto · flag). **Lembrete**: são domínios **expirando na janela do header** — entram pra registro quando liberados, não estão livres agora. Os que vieram do R&R levam a marca "veio do R&R".
- No fim do relatório: quantos domínios ficaram para o R&R (Fase 8) e quantos achados do R&R foram avaliados (1.1).
- **READ-ONLY no afiliados. Registro é decisão do Marcelo.** Commit e publicação do painel (JSONs, gen, VPS) só com "pode subir". A exceção é a pasta compartilhada de leilões (Fase 8): a lista e os achados vão sempre para o git, porque a janela do R&R lê de lá.

## Fase 7 — Histórico + pós-compra
- **Histórico curado** (`_data/leiloes-afiliados/historico-curado.json`, schema `{runs:[{periodo,curadoEm,totalLista,candidatos,exactCru[],melhorX[],tier2[],registrados[]}]}`): ao fechar a curadoria, **anexar a run deste período** (substituir se o período já existe). É o que dá o "novos × recorrentes" no próximo mês e o histórico dos leilões passados. (Os snapshots crus por período já ficam em `leilao-{periodo}.json`; este arquivo é a camada CURADA.)
- **Pós-compra**: quando o Marcelo disser o que registrou, preencher `registrados[]` da run + cadastrar em `domains.json` (form normal, com expiresAt real) → o helper passa a ocultar automaticamente.
- **Publicar (só se pedido)**: a Fase 2 já escreveu `latest.json` (aba Leilão local). Pra subir no painel VPS: commit dos JSONs + `bun docs/painel/gen.ts` + `bash scripts/painel-vps-pull.sh`.

## Fase 8 — Achados para o R&R e estado ao terminar

1. **Grave os achados para o R&R** em `caminhoDosAchados('<DE>', '<ATE>', 'afiliados')` (`../shared-scripts/leiloes/achados/<DE>_a_<ATE>-do-afiliados-para-o-rr.md`; crie a pasta `achados/` se faltar): os domínios de **serviço local** que apareceram na análise e parecem bons para rank and rent, ou seja, serviço + cidade (chaveiro, guincho, encanador, vidraçaria, desentupidora, dedetização, eletricista, ar-condicionado, conserto de eletrodoméstico e parecidos). Uma linha cada: `- dominio.com.br — por quê`. **Sem análise a fundo:** o funil do R&R já cobre os nichos dele; anote o que chamar atenção (serviço e cidade claros, curto, sem número nem hífen). Nome de empresa (`chaveirogomes`) não entra. Sem nenhum, não grave o arquivo.
   Passada rápida para achar o que olhar (não é funil; em 09/2026 deu 204 domínios, a maioria nome de empresa):
   ```bash
   python3 - <<'EOF'
   import re
   C='<CAMINHO>'
   doms=[l.strip().lower() for l in open(C,'rb').read().decode('latin1').replace('\r','').split('\n') if l.strip() and not l.startswith('#')]
   servicos=['chaveiro','guincho','reboque','encanador','desentupidora','desentupimento','vidracaria','vidraceiro','dedetizadora','dedetizacao','eletricista','arcondicionado','refrigeracao','conserto','assistenciatecnica','maridodealuguel','serralheria','cacamba']
   achados=sorted((len(d),d) for d in doms if d.endswith('.com.br') and re.fullmatch(r'[a-z]+',d[:-7]) and len(d)<=35 and any(d.startswith(s) and len(d)-7-len(s)>=4 for s in servicos))
   print(len(achados)); [print(d) for _,d in achados]
   EOF
   ```
2. **Commit e push da `shared-scripts` só com os arquivos de `leiloes/`** (lista nova, lista competitiva guardada, achados), com `git pull --rebase` antes do push, porque as duas janelas gravam lá:
   ```bash
   git -C ../shared-scripts add leiloes/ && git -C ../shared-scripts commit -m "leiloes: <o que entrou> (<DE> a <ATE>)" -- leiloes/
   git -C ../shared-scripts pull --rebase && git -C ../shared-scripts push
   ```
   Se o `pull --rebase` recusar por arquivo de outra janela em edição, não use `git stash`: espere a outra janela ou avise o Marcelo. Confira com `git -C ../shared-scripts log --oneline -1` e `git -C ../shared-scripts ls-remote origin HEAD`.

## Regras invioláveis
- **NUNCA registrar/comprar** — só recomendar. Janela é curta: entregar no mesmo dia.
- **NÃO cadastrar candidato de leilão como keyword do garimpo** (a contaminação que já aconteceu).
- **NÃO tocar** em `garimpo-snapshot-afiliados.json` nem no WHOIS do garimpo (outro processo).
- READ-ONLY no afiliados por default; commit/deploy do painel só com pedido explícito. A pasta compartilhada de leilões é a exceção (Fase 8).
- A lista fica UMA vez, em `shared-scripts/leiloes/`: não guarde cópia no afiliados nem baixe por fora do `lista.ts`.
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
