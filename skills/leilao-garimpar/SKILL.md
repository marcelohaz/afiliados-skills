---
name: leilao-garimpar
description: "Analisa a lista \"processo de liberação\" do Registro.br e devolve a shortlist de domínios bons para site afiliado de produto físico, mais o alerta de domínios nossos que estão sendo liberados. A lista é a mesma do Rank and Rent e fica guardada em shared-scripts/leiloes (uma rotina diária no GitHub guarda as listas e o desfecho de cada janela); a skill mostra o que ficou livre da lista anterior, confere quantas vezes cada candidato já apareceu, lê os achados que o R&R deixou para o afiliados e grava os de serviço local para o R&R. Use quando o Marcelo mandar a lista do leilão ou pedir o garimpo do leilão (sem arquivo, usa a lista guardada ou baixa e guarda). Só recomenda: registro e compra são do Marcelo. Não é o garimpo de keywords (garimpo-afiliados-loader)."
---

# Garimpo da lista de leilão afiliado (processo de liberação Registro.br)

**Entrada: a lista mora em `../shared-scripts/leiloes/`** (pasta irmã do repositório, repo `marcelohaz/shared-scripts`), UMA cópia para o afiliados e o Rank and Rent (decisão do Marcelo, 07/10/2026; ver `shared-scripts/leiloes/LEIA-ME.md`). O Registro.br publica uma lista por mês no mesmo endereço, que é sobrescrito: a lista que não foi guardada lá não se baixa mais. As funções são as de `shared-scripts/leiloes/lista.ts`; não mude nome nem parâmetro delas (o R&R usa as mesmas).

**Desde 13/10/2026 uma rotina diária no GitHub** (`shared-scripts/.github/workflows/leiloes-diario.yml`) guarda sozinha a lista principal e a competitiva e, depois de cada janela, grava o desfecho dos domínios acompanhados. Ela grava no GitHub, então o Mac só vê depois de puxar.

0. **Puxe a pasta comum antes de tudo** (sem `git stash`: as duas janelas e a rotina gravam lá):
   ```bash
   git -C ../shared-scripts pull --rebase -q && git -C ../shared-scripts log --oneline -1
   ```
   Se recusar por arquivo de outra janela em edição, veja se o GitHub tem commit que o disco não tem: `git -C ../shared-scripts fetch -q && git -C ../shared-scripts rev-list --count HEAD..origin/main`. Com 0, o disco já está atual e você segue. Com mais que 0, avise o Marcelo e siga com o que há no disco.
1. **O Marcelo mandou um arquivo** ($ARGUMENTS): guarde antes de analisar, com os bytes como vieram, e use o caminho impresso como `<CAMINHO>`:
   ```bash
   cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" && test -f docs/painel/sites-meta.json || { echo "⛔ cwd errado ($(pwd)): rode a partir da raiz do ProjetoAfiliados"; exit 1; }
   bun -e "import { guardarLista } from '../shared-scripts/leiloes/lista.ts'; const r = guardarLista('liberacao', new Uint8Array(await Bun.file('<ARQUIVO>').arrayBuffer())); console.log(r.jaExistia ? 'já estava guardada:' : 'guardada:', r.caminho, r.de, r.ate)"
   ```
   A lista **competitiva** (poucas centenas de domínios; o Registro.br chama de processo competitivo) vai com `'competitivo'` no lugar de `'liberacao'`, para `leiloes/competitivo/`. O cabeçalho das duas é igual: quem separa é o tamanho e o nome do arquivo. Ela é um pedaço da principal: os domínios disputados, que voltam à lista mês após mês (em 10/2026, 151 dos 152 já estavam nas de julho e setembro; o arcondicionados.com.br é um deles). A rotina diária guarda as duas; à mão, `baixarListaCompetitiva()`.
2. **Sem arquivo:** veja a lista mais recente guardada:
   ```bash
   cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" && test -f docs/painel/sites-meta.json || { echo "⛔ cwd errado ($(pwd)): rode a partir da raiz do ProjetoAfiliados"; exit 1; }
   bun -e "import { listaGuardada } from '../shared-scripts/leiloes/lista.ts'; const l = listaGuardada('liberacao'); console.log(l ? l.de + ' a ' + l.ate + ' ' + l.caminho : 'nenhuma')"
   ```
   - Período que começou há 25 dias ou menos é a lista do mês (a janela do R&R já baixou): use esse caminho e rode a Fase 2.
   - Senão, rode `bun scripts/refresh-leilao-afiliados.ts`: ele baixa a lista, guarda na pasta se o período for novo e já roda o processador (a Fase 2 fica feita). Use o caminho que ele imprime ("guardada em" ou "já estava guardada em").
   - **Período já encerrado (`<ATE>` antes de hoje), venha a lista da pasta ou do download:** a janela dessa lista acabou, e o Registro.br continua servindo a anterior até publicar a nova (o período novo começa na 2ª quarta-feira do mês; o arquivo sai uns 2 dias antes). Diga isso ao Marcelo, com a data provável da próxima, e não refaça a análise de uma lista encerrada, a não ser que ele peça. Caso de 07/10/2026: o endereço ainda servia a lista de 09 a 16/09.
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

### 1.0 — Desfecho da janela anterior (vai no TOPO do relatório)
A rotina diária consulta no Registro.br, depois de cada janela, os domínios que os dois projetos acompanharam (os arquivos `candidatos/` e `achados/` daquele período) e grava em `leiloes/desfecho/{de}_a_{ate}.json`. Leia a última consulta da lista anterior:
```bash
bun -e "
import { listaGuardada, desfechoGuardado } from '../shared-scripts/leiloes/lista.ts';
import { readdirSync } from 'node:fs';
const nomes = readdirSync('../shared-scripts/leiloes/liberacao').filter(n => n.endsWith('.txt')).sort();
const ant = nomes.at(-2)?.match(/_(\d{4}-\d{2}-\d{2})_a_(\d{4}-\d{2}-\d{2})/);
const d = ant && desfechoGuardado(ant[1], ant[2]);
if (!d) { console.log('sem desfecho da lista anterior', ant?.slice(1)); process.exit(0); }
const c = d.consultas.at(-1)!; const por = {};
for (const [dom, r] of Object.entries(c.resultados)) (por[r.situacao] ??= []).push(dom + ' (' + r.origem.join(', ') + ')');
console.log('desfecho de', d.periodo.de, 'a', d.periodo.ate, 'consultado em', c.em); for (const [s, l] of Object.entries(por)) console.log(s + ':', l.join(' '));"
```
- **"livre" (código 0) é o que importa:** ninguém pegou e dá para registrar agora, pelo preço normal. Liste no topo, com a origem (afiliados, achado do R&R...). Registro é decisão do Marcelo.
- Código que não está em `SITUACAO_REGISTRO` vem gravado como "código N": diga qual apareceu e em quais domínios, para descobrir o que é.
- Sem arquivo de desfecho com a lista anterior já encerrada há mais de 1 dia: a rotina não rodou ou não havia o que consultar. Se `dominiosAcompanhados('<DE_ANT>', '<ATE_ANT>').size` for 0 (nenhum arquivo de candidatos nem de achados daquele período; vale para as listas de antes de 10/2026), não há desfecho a registrar: diga isso e siga. Senão, rode à mão `bun -e "import { registrarDesfecho } from '../shared-scripts/leiloes/lista.ts'; console.log(await registrarDesfecho('<DE_ANT>', '<ATE_ANT>'))"` (uns 2 segundos por domínio) e envie na Fase 8.

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
na lista e teriam passado batido.

**Domínio nosso na lista já foi cancelado e não renova mais.** O .br renova até uns 104 dias depois de
vencer (congelado); depois disso é cancelado e vai para a lista do mês. Nessa hora o antigo dono não tem
prioridade: o que resta é se candidatar na janela, como qualquer pessoa. O `domains.json` costuma trazer
`perdidoEm`. Até 20/10/2026 esta seção dizia "dá pra renovar até a liberação", e estava errado.

### 4.2 — Recorrência: pelas listas guardadas, não só pelo que foi curado
O flag `↩ recorrente` lê só o `historico-curado.json`, que não vê run não curada nem mês em que ninguém
analisou. A fonte é a lista original: `historicoDosDominios()` diz, para cada candidato, em quais listas
guardadas ele apareceu, na principal e na competitiva (uma chamada com todos os candidatos; ela lê as
listas inteiras):
```bash
bun -e "import { historicoDosDominios } from '../shared-scripts/leiloes/lista.ts';
const h = historicoDosDominios(process.argv.slice(1));
for (const [d, x] of Object.entries(h)) if (x.liberacao.length > 1 || x.competitivo.length) console.log(d, 'principal:', x.liberacao.join(' '), '| competitiva:', x.competitivo.join(' ') || '-');" <dominio> <dominio> ...
```
Repetição é rara (em 10/2026: dos 765 mil domínios diferentes de 6 listas, 99,4% apareceram uma vez só), então é sinal:
ninguém pegou o domínio. Na competitiva = disputado (há mais gente querendo). Guardadas: principais de
01, 02 e 04 a 10/2026 (a de 03/2026 não existe em lugar nenhum) e 70 competitivas de 09/2017 a
10/2026, com buracos (40 meses sem cópia, a maior parte de 2023 a 2025).

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
- **"Guia" + produto fica de fora** (`guiadegeladeiras`, `guiadasbicicletas`, `guiadofornoeletrico`): o Marcelo não compra mais (20/10/2026). O helper ainda acha essa família (Fase 3); a curadoria corta e mostra no fim, entre os descartados.
- **Onde o recall falha:** o exact-cru convergiu (varredura independente de 208 produtos em 09/2026 não achou nada novo). O que escapa é (a) a família `^(o|a|os|as)?(melhor|melhores|top)` com produto fora do dicionário, filtrando serviço e cidade por regex, e (b) `^produto+qualificador$` com lista fechada de qualificadores que formam termo real (eletrica, digital, inteligente, gamer, portatil, wifi, inox, vertical, embutir, externa, ip, kamado, passagem). `contains produto` sozinho é quase todo substring falsa.
- **Blocklist vence a memória:** o que o helper pulou por blocklist fica fora, mesmo que pareça bom.

## Fase 6 — Output
- Shortlist em tiers (tabela: domínio · produto · flag). **Lembrete**: são domínios **expirando na janela do header** — entram pra registro quando liberados, não estão livres agora. Os que vieram do R&R levam a marca "veio do R&R".
- **Pedidos, com a janela aberta:** consulte no Registro.br cada domínio da shortlist, os nossos da 4.1 e os achados para o R&R que passam nas regras da Fase 8, um por vez e com pausa (o Registro.br já bloqueou o Mac por excesso):
  ```bash
  bun -e "import { consultarRegistro } from '../shared-scripts/leiloes/lista.ts';
  for (const d of process.argv.slice(1)) { const r = await consultarRegistro(d); console.log(d, r.status, r.situacao, 'pedidos=' + (r.pedidos ?? 0) + (r.pedidosCortado ? ' ou mais' : '')); await new Promise(z => setTimeout(z, 1500)); }" <dominio> <dominio> ...
  ```
  Códigos: 6 sem pedido, 7 já pedido, 9 na lista competitiva (disputa). O Registro.br devolve no máximo 10 números de pedido, por isso "10 ou mais". Ponha os pedidos na tabela. O titular de cada pedido só aparece com login no Registro.br.
- **População da cidade em todo domínio de serviço mostrado ao Marcelo** (pedido dele, 20/10/2026), em toda lista e toda resposta, não só no relatório: cidade, UF e população pela estimativa mais recente do IBGE. A cidade é leitura sua (`bhz` é Belo Horizonte, `riopreto` é São José do Rio Preto, `floripa` é Florianópolis, `poa` é Porto Alegre, `bsb` e `df` são Brasília); nome que existe em mais de um estado pede a UF certa. Domínio sem cidade (sub-nicho, "perto de mim") leva "sem cidade". O comando pega o ano mais recente sozinho (em 20/10/2026 já era a estimativa de 2026):
  ```bash
  bun -e "
  const per = (await fetch('https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos').then(r => r.json())).at(-1).id;
  const r = await fetch('https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/' + per + '/variaveis/9324?localidades=N6[all]').then(r => r.json());
  const tira = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
  const pop = new Map(r[0].resultados[0].series.map((x) => [tira(x.localidade.nome), Number(x.serie[per])]));
  console.log('estimativa do IBGE de', per);
  for (const c of process.argv.slice(1)) console.log(c + ':', pop.get(tira(c))?.toLocaleString('pt-BR') ?? 'não achei');" 'Joinville - SC' 'Florianópolis - SC'
  ```
  "Não achei" é nome escrito diferente do IBGE (o acento não importa; hífen e apóstrofo importam): corrija o nome, não deixe o domínio sem número.
- **No Mac do Marcelo, diga também o que o R&R tem no mesmo serviço e na mesma cidade** (pergunta dele, 20/10/2026: "algum em nicho e cidade com prestador?"): prestador ativo (pagante ou não) e site do R&R, com os leads de 30 dias. É o que separa o domínio que já tem para quem vender do que ainda espera prestador. Os dados são do painel do R&R, só leitura.
- **Backlinks, só do que o Marcelo for pegar:** página pública `https://ahrefs.com/backlink-checker/?input=<dominio>&mode=subdomains` no Chrome dele (Claude in Chrome; avise antes: ahrefs.com, sem conta). No navegador do app, o "confirme que é humano" não passa. Vá de 2 a 3 por vez, espere uns 8 segundos depois de abrir e leia a tabela por JavaScript (`tr` com DR, página e âncora). O ruído automático ("SEO Express", "Directory Pages Index", listas de domínio à venda, páginas de estatística de domínio como "Website Stats" e "Domain Report", e o Subdomain Finder do c99.nl nos domínios de cidade) aparece em todo domínio. O que conta são os links de verdade: guia local, notícia, fórum do assunto. A página grátis mostra no máximo 20 links, e o quadro de cima dá o total de sites que linkam: quando os 20 são ruído, diga que o resto não aparece. "No backlinks for" é zero de verdade (em 20/10/2026, o guinchoemmaringa.com.br). A `ahrefs-backlinks` não serve aqui: ela lê o Ahrefs Webmaster Tools, que só abre domínio nosso e verificado.
- No fim do relatório: **a lista** dos achados para o R&R (Fase 8), com os pedidos e a população de cada cidade, e quantos achados do R&R foram avaliados (1.1). Leia o arquivo de achados inteiro antes de resumir (`grep -c '^- '` dá o total): em 20/10/2026 só as 30 primeiras de 66 linhas foram mostradas ao Marcelo, e 3 dos domínios que ele reservou estavam na parte não lida.
- **READ-ONLY no afiliados. Registro é decisão do Marcelo.** Commit e publicação do painel (JSONs, gen, VPS) só com "pode subir". A exceção é a pasta compartilhada de leilões (Fase 8): a lista e os achados vão sempre para o git, porque a janela do R&R lê de lá.

## Fase 7 — Histórico + pós-compra
- **Histórico curado** (`_data/leiloes-afiliados/historico-curado.json`, schema `{runs:[{periodo,curadoEm,totalLista,candidatos,exactCru[],melhorX[],tier2[],registrados[]}]}`): ao fechar a curadoria, **anexar a run deste período** (substituir se o período já existe). É o que dá o "novos × recorrentes" no próximo mês e o histórico dos leilões passados. (Os snapshots crus por período já ficam em `leilao-{periodo}.json`; este arquivo é a camada CURADA.)
- **Pós-compra**: quando o Marcelo disser o que registrou, preencher `registrados[]` da run + cadastrar em `domains.json` (form normal, com expiresAt real) → o helper passa a ocultar automaticamente.
- **Publicar (só se pedido)**: a Fase 2 já escreveu `latest.json` (aba Leilão local). Pra subir no painel VPS: commit dos JSONs + `bun docs/painel/gen.ts` + `bash scripts/painel-vps-pull.sh`.

## Fase 8 — Achados para o R&R e estado ao terminar

1. **Grave os achados para o R&R** em `caminhoDosAchados('<DE>', '<ATE>', 'afiliados')` (`../shared-scripts/leiloes/achados/<DE>_a_<ATE>-do-afiliados-para-o-rr.md`; crie a pasta `achados/` se faltar): os domínios de **serviço local** que apareceram na análise e parecem bons para rank and rent (chaveiro, guincho, encanador, vidraçaria, desentupidora, dedetização, eletricista, ar-condicionado, conserto de eletrodoméstico e parecidos). Uma linha cada: `- dominio.com.br — por quê`. **Sem análise a fundo:** quem garimpa serviço é a skill do R&R (`leilao-garimpar-rr`); anote o que chamar atenção, curto e sem hífen. Sem nenhum, não grave o arquivo. O que o Marcelo costuma comprar (20/10/2026):
   - **nicho + cidade** (`chaveiromaringa`) e **nicho + em + cidade** (`chaveiroemcuiaba`);
   - **nicho no domínio da cidade** (`encanador.floripa.br`, `guincho.joinville.br`): o Registro.br tem 56 terminações de cidade (categoria "Localidades" em registro.br/dominio/categorias);
   - **plural** das formas acima (`chaveiroscuritiba`, `chaveiros.curitiba.br`);
   - **nicho + "perto de mim"**, normalmente no singular (`encanadorpertodemim`);
   - **sub-nicho de serviço, sem cidade** (`fechaduradigital`, `boxparabanheiro`);
   - **vidraçaria**, sempre que tiver cidade: é nicho bom e tem pagantes no R&R.

   Ele dificilmente compra, e por isso **fica de fora**:
   - "24h" ou "24horas" no nome;
   - bairro (`encanadormooca`, `chaveirobarratijuca`);
   - nome com ruído, ou seja, com um pedaço que não é nicho, cidade nem "perto de mim": letras soltas (`guinchopertodemimjl`), nome ou sigla de empresa (`chaveirogomes`, `desentupidorajatex`) e palavra de marca (`chaveiroexpress...`, `telechaveiro...`).

   Passada rápida para achar o que olhar (não é funil). Os nichos vêm do `detectNicho` de `shared-scripts/domains/nicho-detect.ts`, a fonte única do R&R: a passada acompanha sozinha quando o R&R abre nicho novo. Não escreva lista de serviços à mão. Em 09/2026 deu 268 domínios em 27 nichos, a maioria nome de empresa. Ela lê o `.com.br` e as terminações de cidade, e aceita o nicho sozinho (sub-nicho, ou nicho no domínio da cidade). Em 20/10/2026 o `detectNicho` não conhecia `fechaduradigital` nem `boxdebanheiro` (conhecia `boxparabanheiro`): sub-nicho que ele não conhece só aparece olhando a lista. Avise a janela do R&R para incluir.
   ```bash
   bun -e "
   import { detectNicho } from '../shared-scripts/domains/nicho-detect.ts';
   const doms = Buffer.from(await Bun.file('<CAMINHO>').arrayBuffer()).toString('latin1').replace(/\r/g, '').split('\n').map(l => l.trim().toLowerCase()).filter(l => l && !l.startsWith('#'));
   // Terminações de cidade do Registro.br (categoria Localidades, lida em 20/10/2026).
   const CIDADES = new Set('9guacu abc aju anani aparecida barueri belem bhz boavista bsb campinagrande campinas caxias contagem cuiaba curitiba feira floripa fortal foz goiania gru jab jampa jdf joinville londrina macapa maceio manaus maringa morena natal niteroi osasco palmas poa pvh recife ribeirao rio riobranco riopreto salvador sampa santamaria santoandre saobernardo saogonca sjc slz sorocaba the udi vix'.split(' '));
   const porNicho = new Map<string, string[]>();
   for (const d of doms) {
     const p = d.split('.');
     if (!(p.length === 3 && p[2] === 'br' && (p[1] === 'com' || CIDADES.has(p[1])))) continue;
     const sld = p[0];
     if (!/^[a-z]+$/.test(sld) || sld.length > 30) continue;   // sem número: 24h ele quase não compra
     const n = detectNicho(sld);
     const resto = sld.length - n.slug.length;   // 0 = o nicho sozinho (sub-nicho, ou nicho no domínio da cidade)
     if (n.slug === 'outros' || (resto > 0 && resto < 4)) continue;
     porNicho.set(n.label, [...(porNicho.get(n.label) ?? []), d]);
   }
   for (const [l, ds] of [...porNicho].sort((a, b) => b[1].length - a[1].length)) console.log(ds.length, l + ':', ds.sort((a, b) => a.length - b.length).join(' '));
   "
   ```
   Ruído conhecido: começo curto (`gas`, `grama`, `gesso`) pega palavra que não é o serviço (gastronomia, a cidade de Gramado); começo que também é produto (`geladeira`, `arcondicionado`, `maquinadelavar`) traz domínio de afiliado, como `geladeirasamsung`, que é candidato deste garimpo e não vai para o R&R.
2. **Grave os candidatos do afiliados para o desfecho** em `caminhoDosCandidatos('<DE>', '<ATE>', 'afiliados')` (`../shared-scripts/leiloes/candidatos/<DE>_a_<ATE>-afiliados.txt`): um domínio por linha, os três tiers da shortlist e os domínios nossos da 4.1, com linhas `#` separando os grupos. Só os domínios: a escolha, os tiers e o porquê ficam no `historico-curado.json` do afiliados. É desta lista (mais os achados) que a rotina diária consulta o desfecho depois da janela.
3. **Commit e push da `shared-scripts` só com os arquivos de `leiloes/`** (lista nova, lista competitiva guardada, achados, candidatos), com `git pull --rebase` antes do push, porque as duas janelas e a rotina diária gravam lá:
   ```bash
   git -C ../shared-scripts add leiloes/ && git -C ../shared-scripts commit -m "leiloes: <o que entrou> (<DE> a <ATE>)" -- leiloes/
   git -C ../shared-scripts pull --rebase && git -C ../shared-scripts push
   ```
   Sem nada novo em `leiloes/` (lista que já estava guardada e nenhum achado), o git responde que não há o que commitar, e está certo. Se o `pull --rebase` recusar por arquivo de outra janela em edição, não use `git stash`: veja se o GitHub tem commit que o disco não tem (`fetch` e `rev-list --count HEAD..origin/main`, como no passo 0). Com 0, o `push` passa direto; com mais que 0, espere a outra janela ou avise o Marcelo. Confira com `git -C ../shared-scripts log --oneline -1` e `git -C ../shared-scripts ls-remote origin HEAD`.

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
