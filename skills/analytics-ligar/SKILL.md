---
name: analytics-ligar
description: "Liga o Google Analytics (GA4) nos sites, uma propriedade por site (desde 06/11/2026): cria pela API a propriedade de cada site na conta de quem recebe pelo ID da Amazon, grava o código no arquivo do site, confere o que cada publicação levaria junto, publica site a site pelo painel e confere no ar. Use quando pedirem para ligar, instalar ou configurar o Google Analytics nos sites, trocar o código de um site, ou conferir o Analytics já ligado (`conferir`)."
---

## Parse de input

- vazio: todos os sites da pessoa desta máquina que ainda não têm propriedade própria (Fases 0 a 6).
- lista de sites (`melhortech compraguia`): só esses.
- `conferir`: só a Fase 5, nos sites que já têm Analytics.

# Ligar o Google Analytics nos sites

Caso-origem: 19 e 20/10/2026, sessão do Marcelo. Só 2 dos 69 sites no ar tinham Analytics. Ele ligou nos dele (36 sites, numa propriedade só) e decidiu que os da Bárbara ficam com ela, no e-mail dela: *"sites da barbara, ela instala no email dela"*.

**Desde 06/11/2026, uma propriedade por site** (decisão do Marcelo de 05/11/2026): o mesmo código em todos os sites de uma pessoa ligava a rede a um dono só, para quem olha o código das páginas (concorrente, ferramentas que agrupam sites pelo código do Analytics). O Rank and Rent fez igual no mesmo dia, com 1.347 sites. Não esconde nada do próprio Google: a conta, o Search Console e o titular do domínio continuam ligando tudo. As regras moram em `scripts/lib/ga-propriedades.ts`.

**Por que vale a pena:** o Search Console mostra só a busca do Google e o relatório da Amazon mostra o total por site e por produto. O Analytics mostra de onde vem a visita fora do Google (Bing, redes, grupos, ChatGPT) e quantos leitores de cada artigo clicam na Amazon. O modelo já envia esse clique como o evento `amazon_click`. Caso real: o guiamelhores teve 6.030 cliques na Amazon em 12 meses e só 94 cliques no Google em 16 meses, sem explicação até ligar o Analytics.

## O que já está pronto no código (não refazer)

- Os 13 modelos (`packages/ui/src/layouts/BaseLayout.astro` e `templates/t2` a `t13`) carregam o Analytics sozinhos quando `sites/{site}/src/analytics.json` tem `ga4`. Site sem identificador não muda nada. O arquivo tem `{ ga4, propriedade, conta }`; o `aw` do Google Ads só no oguiacompra, como "AW-número/rótulo" (o rótulo liga a conversão no clique para a Amazon; até 06/11/2026 ele estava escrito no código comum do modelo 1 e ia a todos os sites desse modelo).
- **O publicador barra** (`scripts/cf-deploy-r2.ts`, desde 06/11/2026) a página que leva código que não é o do próprio site, os dois códigos de antes (o da Bárbara passou até a troca dela, na noite de 06/11/2026; `ANTIGOS_AINDA_PERMITIDOS` está vazio desde então), Analytics em site sem propriedade e o código do Google Ads em site que não o tem. O botão "Configurar GA4" do painel recusa os códigos de antes e o código de outro site.
- O trecho do Analytics que vai às páginas não tem comentário: o que está dentro do `<script>` sai igual em todas as páginas de todos os sites (até 06/11/2026 iam datas, números e o nome de um site). Comentário fica fora, em `{/* */}`; o teste `scripts/tests/ga-modelos.test.ts` confere.
- O script do Google não baixa no site montado neste computador (`localhost`), para as conferências antes de publicar não entrarem na propriedade (24/10/2026; teste em `scripts/tests/ga-modelos.test.ts`). Por isso o teste do envio (Fase 5) é sempre no site publicado.
- O script do Google (cerca de 190 quilobytes) só baixa depois que a página carregou (commit `d454b5b64`). Medido no PageSpeed, celular: o melhorhidratante foi de 78 (script junto da página) para 91 (script depois). Nos modelos Vidro (t9) e Pastel (t12) a simulação de celular lento do PageSpeed ainda pune o script. Mas nos tempos observados de verdade o script começa só depois do fim do carregamento (melhorairfryer.com: carregamento aos 0,52 segundo, script a partir daí, maior imagem aos 1,35 segundo).
- O clique num link da Amazon vira o evento `amazon_click`, com `link_url` e `link_text`. O link abre em outra aba, então o evento sai mesmo que o script do Google ainda esteja chegando.
- As 73 políticas de privacidade já dizem que o site usa o Google Analytics e cookies. Não há banner de cookies (decisão de sempre).

## Decisões já tomadas

- **Uma propriedade por site** (06/11/2026), com o nome do domínio, criada pela API (`scripts/ga-criar-propriedades.ts`): setor Compras, fuso de São Paulo, real, guarda de 14 meses, Google Signals desligado, medição otimizada ligada, um fluxo da web com o domínio e `amazon_click` como evento principal, os ajustes das propriedades de antes. Até 06/11/2026 era uma por pessoa ("uma por site seria o mesmo trabalho repetido"); a decisão mudou pelo motivo do topo.
- **A conta é a de quem recebe pelo ID da Amazon do site** (`affiliateTag` no config e `docs/painel/amazon-ids.json`), a mesma regra do dono do domínio. Site de dono compartilhado ("Marcelo e Bárbara", "Marcelo e Snizhana") segue o ID: melhoreletro, melhoressuplementos e melhorpretreino na da Bárbara; melhoremcasa, melhoreseletro, melhortech, guiamelhores e os 8 da Snizhana na do Marcelo. ID fora da lista: o dono do sites-meta quando é uma pessoa só.
- **Marcelo:** conta Google marcelo.ckx@gmail.com, conta do Analytics "Afiliados (Marcelo)" (412569484; renomeada de "Afiliados" em 06/11/2026, porque a da Bárbara tem o mesmo nome). Sem administrador extra (*"nao precisas colocar escritorioecasa como administradora, nao vai mudar nada"*).
- **Bárbara:** conta do Analytics "Afiliados (Bárbara)" (413295946), no e-mail dela; os dados dos sites dela ficam lá. O script cria lá com o token da marcelo.ckx, que tem o papel de **Editor** nessa conta desde 06/11/2026, dado por ela (antes tinha só leitura: no menu Criar, "Propriedade" aparecia apagada). Se um dia sair, ela dá de novo em Administrador, Gerenciamento de acesso à conta.
- **As propriedades de antes ficam, sem apagar**: "Rede de afiliados (Marcelo)" (559669274, G-WJGPEJFWLS) e "Rede de afiliados (Bárbara)" (560568520, G-PEXFL91T8Y) guardam o histórico de 19 a 23/10/2026 até a troca. O `ga-ler` e o relatório de quinta leem as de antes junto com as de cada site, somando pelo domínio. **No dia da publicação da troca de cada pessoa**, a de antes ganha o nome de histórico com o último dia: `bun scripts/ga-criar-propriedades.ts --historico=antiga-marcelo --ate=DD/MM/AAAA` ("Histórico: rede do Marcelo, de 19/10/2026 a DD/MM/AAAA"; `antiga-barbara` desde 23/10, com o papel de Editor e perguntando a ela antes, porque a conta é dela).
- **Nada se apaga** (decisão de 06/11/2026): os relatórios comuns ficam enquanto a propriedade existir (a guarda de 14 meses vale só para as explorações), e a apagada vai para a lixeira por 35 dias e some com o histórico. **Site que sai do ar ou é redirecionado inteiro**: a propriedade fica, renomeada com `--historico={site} --ate=DD/MM/AAAA` ("Histórico: {domínio}, até DD/MM/AAAA"); o `--conferir` não acusa como sobra a propriedade cujo nome começa com "Histórico: ". Site que troca de domínio não vira histórico: `--renomear`.
- **Propriedades de outra época:** antes de 19/10/2026, o oguiacompra tinha a G-BJSMLJCHF8 (conta escritorioecasa) e o melhorcreatina, da Bárbara, a G-4KDVP5L4P6. Em 23/10/2026 os dois passaram para a propriedade da pessoa (*"Todos deveriam ficar na mesma propriedade, exceto os da barbara"*, regra que valeu até 06/11/2026) e, desde 06/11/2026, cada um tem a sua, como os outros sites. O oguiacompra mantém o `aw` do Google Ads, com o rótulo da conversão. A tag do Google Ads dele continua mandando as visitas também para a G-BJSMLJCHF8 pela configuração no Google, sem estar no código do site; o histórico antigo segue lá.
- **Site travado** (`deployBlocked` no sites-meta) entra junto, como pede a regra do Marcelo de não deixar o travado para depois (18/10/2026): compare todas as páginas com o ar (`--todas` na Fase 1), libere só a publicação (`deployBlocked: false`, commit), publique e trave de novo no mesmo trabalho, contando no relatório. O `contentLocked` fica como está: o Analytics não mexe no conteúdo. A trava existe porque a publicação apaga do ar a página que não está no build; a comparação completa é o que mostra que nenhuma some. Em 20/10/2026 assim entraram o melhordaimpressora e o melhorimpressora.

## Fase 0: quem roda e quais sites

`bun scripts/ga-criar-propriedades.ts --seco` diz, por conta, quantos sites ainda não têm propriedade própria. O script roda só no Mac do Marcelo (o token de edição do Analytics, `~/.ga-token-admin.json`, mora lá); site da Bárbara se cria daqui, com o pedido dela ou do Marcelo. A lista abaixo serve para ver os sites no ar sem Analytics nenhum.

```bash
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" && test -f docs/painel/sites-meta.json || { echo "⛔ cwd errado"; exit 1; }
bash scripts/git-pull-seguro.sh "analytics-ligar"
DONO=$(bun -e "import { resolverDono } from './scripts/lib/dono.ts'; console.log(resolverDono(process.cwd()))")
python3 - "$DONO" <<'EOF'
import json, os, sys
dono = {'marcelo': 'Marcelo', 'barbara': 'Bárbara'}.get(sys.argv[1])
if not dono: sys.exit(f'dono não identificado ({sys.argv[1]}): pergunte à pessoa')
m = json.load(open('docs/painel/sites-meta.json'))
for s, v in sorted(m.items()):
    if not v.get('live') or dono not in (v.get('owner') or '') or not os.path.isdir(f'sites/{s}'): continue
    p = f'sites/{s}/src/analytics.json'
    ga4 = (json.load(open(p)).get('ga4') or '').strip() if os.path.exists(p) else ''
    trava = 'publicação travada: comparar com --todas' if v.get('deployBlocked') else ''
    junto = f"dono {v['owner']}: conferir de quem é a tag" if v.get('owner') != dono else ''
    print(s, ga4 or 'sem Analytics', trava, junto)
EOF
```

O pull vem antes de tudo: a comparação da Fase 1 constrói o site nesta máquina, e o painel publica o que está na VPS. Com o repositório daqui atrasado, a comparação não mostra o que a publicação leva. O script acha o repositório principal pelo endereço (na Bárbara, o `upstream`).

Mostre a lista à pessoa: quantos sites, quais ficam de fora e por quê.

## Fase 1: o que cada publicação levaria junto (antes de tudo)

Ligar o Analytics é publicar o site de novo, e a publicação leva junto tudo o que mudou no código desde a última vez. Em 19/10/2026, 13 dos 35 sites do Marcelo tinham código comum ainda não publicado. Construa e compare cada site com o que está no ar:

```bash
TZ=UTC pnpm --filter {site} build   # um por site; sem node_modules: pnpm install --frozen-lockfile --filter "./sites/{site}..."
bun scripts/site-comparar-no-ar.ts {site} [{site}...]
```

**Monte com `TZ=UTC`**, o horário do servidor que monta o que vai ao ar. A data dos artigos ("2026-10-20") é lida como meia-noite em Londres, e num computador com o horário de Brasília vira o dia anterior ("19 de outubro"): em 23/10/2026, no Mac da Bárbara, o comparador acusou diferença em quase todas as páginas por isso, sem nada mudado.

O comparador olha a lista de endereços dos sitemaps e, numa amostra de páginas (início, artigos, produto, Sobre, autor e categoria), o título, a descrição, o canonical, o texto, os links e os dados estruturados. Em site com a publicação travada, use `--todas`, que compara todas as páginas. Endereço que saiu do sitemap mas continua no build (as páginas legais, que os modelos tiram do sitemap) aparece como "fora do sitemap novo" e não conta como diferença.

- **Igual ao que está no ar:** a publicação leva só o Analytics. Pode seguir.
- **Diferença só na página de categoria** (por exemplo, a descrição montada pelos artigos): pode seguir. Página de categoria pode mudar (regra do Marcelo).
- **Diferença que vem de um conserto comum já publicado nos outros sites** (o cargo do autor do `f9ec15efe`, a data "Atualizado em" da página de produto): pode seguir, dizendo no relatório. Confira o commit que causou antes (`git log -S "{texto antigo}"`).
- **Diferença em artigo, página de produto, Sobre ou na lista de endereços:** pare naquele site e mostre a diferença à pessoa. Página que existe só no ar seria apagada pela poda do deploy. Artigo no ar não muda sem o pedido dela.

## Fase 2: criar a propriedade de cada site (pela API)

```bash
bun scripts/ga-criar-propriedades.ts --site={site}[,{site}]     # ou --dono=marcelo / --dono=barbara para todos os que faltam
bun scripts/ga-criar-propriedades.ts --conferir [--dono=...]    # só lê: confere uma a uma
```

O script cria na conta de quem recebe, com os ajustes da seção "Decisões", e grava `{ ga4, propriedade, conta }` no `analytics.json` do site assim que ele fica pronto. Parou no meio: rode de novo, ele continua e completa a propriedade que ficou sem fluxo (acha pelo nome). O Google às vezes responde 503 ou 403 logo depois de criar: o script espera e tenta de novo, e relê a conta antes de criar outra, para não repetir (06/11/2026: um 503 no ajuste da guarda da primeira). Leva uns 4 a 10 segundos por site. O `--conferir` diz se há propriedade repetida ou sobrando na conta, site sem propriedade, e confere em cada uma o nome, a conta, o fuso, a moeda, a guarda, o evento principal, o fluxo e o código do arquivo.

Troca de domínio de um site: `--renomear={site}` depois de o `siteUrl` do config ter o domínio novo. Renomeia a propriedade e o endereço do fluxo e mantém o código.

**Sem a API (conta nova da pessoa, ou a Bárbara sem dar o papel de Editor à marcelo.ckx):** o caminho antigo pelo Chrome da pessoa, abaixo, uma propriedade por site com o nome do domínio. Antes de abrir, avise numa linha: o quê (criar a propriedade do Analytics), o site (analytics.google.com) e a conta Google (a logada no Chrome). Carregue a skill `chrome-browser`. O Claude nunca digita senha. Se pedir login, a pessoa entra.

1. Confira a conta logada: `accounts.google.com/AccountChooser?continue=https://analytics.google.com/` mostra as contas do perfil. Conta sem nenhum Analytics cai na tela "Começar a usar".
2. **Conta:** nome "Afiliados". Nas "Configurações de compartilhamento de dados", desmarque as quatro caixas, que é a opção mais reservada. Clique em Próximo.
3. **Propriedade:** nome igual ao domínio do site, fuso Brasil e Horário de São Paulo, moeda Real brasileiro. Os seletores têm busca: digite "Brasil", "Paulo" e "Real".
4. **Empresa:** setor Compras, tamanho Pequena. **Objetivos:** "Entender o tráfego da Web" e "Ver o engajamento". Clique em Criar.
5. **Termos:** escolha o país Brasil. **Aceite só com o sim da pessoa nesta conversa.** Para quem está na Europa, o Google só libera o botão com a caixa dos Termos de Tratamento de Dados marcada (aconteceu com o Marcelo). Explique isso no pedido do sim.
6. **Fluxo de dados:** Web, com a URL do site e o nome igual ao domínio. A medição otimizada fica ligada, como vem. O identificador G-... aparece no trecho de código da tela "Configurar uma tag do Google". Ele não está no texto da página: leia pela imagem (zoom).
7. Se aparecer "Meus comunicados por e-mail", use "Desmarcar tudo e salvar".
8. **Guarda dos dados:** Administrador > Coleta e modificação de dados > Retenção de dados. Ponha 14 meses (o padrão do Google é 2 meses) e salve. Recarregue a página para conferir.
9. **Clique na Amazon como evento principal, já na criação:** Administrador > Exibição de dados > Eventos > Criar evento. Nome `amazon_click`, ligue "Marcar como evento principal", escolha "Não definir um valor de evento principal padrão" (o formulário vem com 1 dólar por clique, número inventado) e "Uma vez por evento", e no fim "Criar com código" (o site já envia o evento). Clique em Criar e confira a estrela cheia na aba "Eventos principais". Assim não é preciso esperar o evento aparecer na lista, o que leva até 24 horas (Marcelo, 20/10/2026).

## Fase 3: gravar o identificador

**Pelo script (Fase 2):** ele já gravou os arquivos. Commit só dos `analytics.json` e o painel atualizado:

```bash
git add sites/*/src/analytics.json && git commit -m "analytics: uma propriedade por site (N sites)" && git push origin main
bash scripts/painel-vps-pull.sh
```

**Propriedade criada pelo Chrome (caminho antigo), Marcelo:** direto nos arquivos, com o número da propriedade e a conta (sem eles a leitura não acha o site), mantendo os outros campos (o `aw` do oguiacompra), e um commit só:

```bash
python3 - {site} [{site}...] <<'EOF'
import json, sys
for s in sys.argv[1:]:
    p = f'sites/{s}/src/analytics.json'
    raw = open(p).read(); d = json.loads(raw); d['ga4'] = 'G-XXXXXXXXXX'; d['propriedade'] = 'NNNNNNNNN'; d['conta'] = 'NNNNNNNNN'
    open(p, 'w').write(json.dumps(d, indent=2, ensure_ascii=False) + ('\n' if raw.endswith('\n') else ''))
EOF
git add sites/*/src/analytics.json && git commit -m "analytics: Google Analytics (G-...) em N sites" && git push origin main
bash scripts/painel-vps-pull.sh
```

**Propriedade criada pelo Chrome, Bárbara:** pelo painel, site a site. A rota mantém os outros campos e faz o commit na VPS desde 20/10/2026 (antes ela regravava só o `ga4` e não commitava). Ela recusa os códigos de antes e o código de outro site, e tira o número da propriedade quando o código muda: depois, peça ao Claude do Marcelo para pôr o número (a leitura do Analytics acha o site por ele).

```bash
echo '{"code": "G-XXXXXXXXXX"}' > /tmp/ga4.json
bun scripts/painel-api.ts POST /admin/site/{site}/analytics /tmp/ga4.json   # 200, com "gitSync"
```

## Fase 4: publicar, um site por vez

```bash
bun scripts/painel-publicar-sites.ts {site} [{site}...] --confirmar-erro-antigo
```

O script faz build, deploy e limpeza do cache pelo painel, um site por vez. O painel escolhe a conta Cloudflare pela zona, então vale para os sites dos dois. Leva cerca de um minuto e meio por site. Para muitos sites, rode em segundo plano e avise a pessoa quanto deve levar.

- `--confirmar-erro-antigo`: o painel recusa publicar quando um artigo tem erro de auditoria. O script só confirma quando nenhum arquivo de conteúdo do site mudou desde a última publicação, ou seja, quando o erro já estava no ar. Caso real: oguiacompra, 19/10/2026, com a pergunta da introdução de um artigo de 31/07 sem a palavra-chave. A comparação é feita no commit que o painel construiu. Com conteúdo mudado, ou com o repositório desta máquina atrás do painel, o site é pulado e o motivo sai no resumo (no segundo caso, rode o pull e publique de novo só aquele site).
- Publique primeiro um site e confira (Fase 5) antes de mandar o resto.
- **Nunca edite o roteiro de publicação enquanto ele roda.** O terminal lê o arquivo durante a execução e pode rodar um pedaço errado.

## Fase 5: conferir no ar

1. **Nas páginas:** só o código do próprio site (o do `analytics.json`, nenhum outro e nenhum dos de antes) e o carregamento leve (`carregarGtag`) na página inicial e num artigo de cada site, e nada do script antigo (`<script async src="https://www.googletagmanager`). O publicador já barra o código errado; esta conferência pega a página que ficou no cache. Peça sem cache (`?cb=...`) e repita se um ponto da Cloudflare ainda mostrar a versão anterior: isso acontece por alguns segundos depois da limpeza. Site que já tinha Analytics e não foi publicado depois de 19/10/2026 ainda carrega o script do jeito antigo, junto da página (o melhorcreatina, conferido em 20/10/2026). O identificador está lá e a coleta funciona; publicar de novo passa para o carregamento leve.
2. **No navegador do app**, abra um artigo e confira o envio:
   ```js
   performance.getEntriesByType('resource').filter(r => /\/g\/collect/.test(r.name)).map(r => decodeURIComponent(r.name).match(/tid=([^&]+)|en=([a-z_]+)/g))
   ```
   Para testar o clique na Amazon sem gerar clique falso lá, impeça a navegação (`document.addEventListener('click', e => e.preventDefault())`) e dispare um clique num link da Amazon. Tem que sair `en=amazon_click`. Em site com `aw` (oguiacompra), esse clique também conta uma conversão no Google Ads (`en=conversion`, 23/10/2026): teste o clique num site sem `aw` e, no oguiacompra, confira só o envio da página.
3. **No Analytics, o tempo real**: as visitas chegando. Pela API, sem Chrome: `runRealtimeReport` da propriedade do site (Data API, `properties/{número}:runRealtimeReport`, com o token de leitura do `scripts/lib/ga-auth.ts`), depois de abrir o site; ou em Relatórios > Tempo real. A tela do fluxo de dados mostra "A coleta de dados não está ativa" por até 48 horas mesmo com dados chegando. Quem prova é o tempo real. Com uma propriedade por site (desde 06/11/2026), a propriedade nova não recebe de nenhum outro site: confira o tempo real pela API numa amostra, um site de cada modelo, logo depois de publicar; nos outros, o envio conferido no passo 2 basta. Até 06/11/2026, com a propriedade comum (a G-WJGPEJFWLS recebia dos 38 em 22/10/2026), o passo 2 bastava para todos.
4. **Na conferência de sites que já estão no Analytics (`conferir`), pela API, sem Chrome** (27/10/2026: foi o que achou os defeitos que o passo 2 não via):
   - visitas de busca do Analytics contra os cliques do Google de cada site, em dias inteiros desde a entrada do Analytics (`bun scripts/ga-ler.ts` e o snapshot do Search Console): site com clique no Google e sem visita no Analytics é defeito;
   - `amazon_click` contra o clique de saída para a Amazon da medição otimizada (`click`), por site: muito menos `amazon_click` que `click` quer dizer evento que não sai;
   - visitas com host `localhost`, por dia: tem de ser zero (o script não baixa no site montado neste computador desde 24/10/2026).
   O `ga-ler` lê todas juntas (as de cada site e as duas de antes); `GA_PROPRIEDADE=<número>[,<número>]` lê só essas, e `--site=` lê só as que podem ter dado do site.
   - na semana da troca, o total do `ga-ler` contra os mesmos dias da semana anterior: a soma é pelo domínio, então o site que passou da propriedade de antes para a dele no meio da semana conta inteiro.

## Fase 6: depois de 24 horas

- **Clique na Amazon como evento principal**, se o passo 9 da Fase 2 ficou para trás: o mesmo caminho daquele passo, ou a estrela no `amazon_click` na aba "Eventos recentes", que só lista o evento até 24 horas depois da primeira coleta.
- O Google conta o clique na Amazon duas vezes, como `click` (clique de saída da medição otimizada) e como `amazon_click`. Para a análise vale o `amazon_click`.

## Armadilhas (aconteceram)

1. **O PageSpeed sem chave da API recusa por limite diário.** Pela página pagespeed.web.dev funciona. No navegador do app com o painel escondido, a página não desenha o resultado: rode no Chrome da pessoa (só leitura, sem conta, avisando antes).
2. **Uma rodada do PageSpeed varia alguns pontos.** Compare com duas rodadas, ou com um site do mesmo modelo sem Analytics.
3. **O checklist do painel mostra o retrato do Search Console**, que a VPS tira às segundas. Até 20/10/2026 o painel só relia o arquivo ao reiniciar; agora relê quando o arquivo muda.
4. **Lista mostrada à pessoa sem conferir:** em 19/10/2026 entrou na "primeira leva" um site que levava 17 arquivos de código pendente (melhorsecador). Monte a lista a partir da comparação da Fase 1, não de memória.
5. **Fila longa com `--confirmar-erro-antigo` pula sites com "este repositório está atrás do painel"** (06/11/2026: 4 de 30 e depois 6 de 31 sites da Bárbara, e o oguiacompra). O painel grava um commit a cada site publicado, então este repositório fica atrás no meio da fila, e o script, que só confirma o erro antigo de auditoria quando o repositório daqui tem o commit do painel, pula o site. No fim da fila, publique os pulados um por vez, com `bash scripts/git-pull-seguro.sh` antes de cada um (e uns 20 segundos de espera, para o commit do site anterior chegar).
6. **Disco cheio no meio da publicação:** um comando falhou com "no space left on device". Confira o espaço (`df -h /System/Volumes/Data`) antes de construir muitos sites.

## Registrar desvio de execução (obrigatório quando houver)

SE você (a) executou diferente do que esta skill manda, (b) **criou um passo que ela não tem**, (c) achou a régua ambígua ou contraditória, ou (d) topou com bug numa ferramenta dela, ENTÃO registre antes de fechar:

```bash
bun scripts/skill-log.ts note analytics-ligar <desvio|ambiguidade|bug|inventou-passo> "<o que fugiu e por quê>" [--alvo=<fase>]
```

Execução limpa **não gera linha**: vazio é dado.
