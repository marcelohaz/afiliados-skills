---
name: analytics-ligar
description: "Liga o Google Analytics (GA4) nos sites no ar de uma pessoa (Marcelo ou Bárbara): escolhe os sites dela sem Analytics, confere o que cada publicação levaria junto, cria a conta e a propriedade no Analytics pelo Chrome da pessoa (avisando antes e aceitando os termos só com o sim dela), grava o identificador, publica site a site pelo painel e confere no ar. Use quando pedirem para ligar, instalar ou configurar o Google Analytics nos sites, ou para conferir o Analytics já ligado (`conferir`)."
---

## Parse de input

- vazio: todos os sites no ar da pessoa desta máquina que ainda não têm Analytics (Fases 0 a 6).
- lista de sites (`melhortech compraguia`): só esses.
- `G-XXXXXXXXXX` junto: a propriedade já existe; pula a Fase 2 e usa esse identificador.
- `conferir`: só a Fase 5, nos sites que já têm Analytics.

# Ligar o Google Analytics nos sites

Caso-origem: 19 e 20/10/2026, sessão do Marcelo. Só 2 dos 69 sites no ar tinham Analytics. Ele ligou nos dele (36 sites, numa propriedade só) e decidiu que os da Bárbara ficam com ela, no e-mail dela: *"sites da barbara, ela instala no email dela"*. Esta skill é o mesmo caminho, para qualquer um dos dois rodar.

**Por que vale a pena:** o Search Console mostra só a busca do Google e o relatório da Amazon mostra o total por site e por produto. O Analytics mostra de onde vem a visita fora do Google (Bing, redes, grupos, ChatGPT) e quantos leitores de cada artigo clicam na Amazon. O modelo já envia esse clique como o evento `amazon_click`. Caso real: o guiamelhores teve 6.030 cliques na Amazon em 12 meses e só 94 cliques no Google em 16 meses, sem explicação até ligar o Analytics.

## O que já está pronto no código (não refazer)

- Os 12 modelos (`packages/ui/src/layouts/BaseLayout.astro` e `templates/t2` a `t12`) carregam o Analytics sozinhos quando `sites/{site}/src/analytics.json` tem `ga4`. Site sem identificador não muda nada.
- O script do Google (cerca de 190 quilobytes) só baixa depois que a página carregou (commit `d454b5b64`). Medido no PageSpeed, celular: o melhorhidratante foi de 78 (script junto da página) para 91 (script depois). Nos modelos Vidro (t9) e Pastel (t12) a simulação de celular lento do PageSpeed ainda pune o script. Mas nos tempos observados de verdade o script começa só depois do fim do carregamento (melhorairfryer.com: carregamento aos 0,52 segundo, script a partir daí, maior imagem aos 1,35 segundo).
- O clique num link da Amazon vira o evento `amazon_click`, com `link_url` e `link_text`. O link abre em outra aba, então o evento sai mesmo que o script do Google ainda esteja chegando.
- As 73 políticas de privacidade já dizem que o site usa o Google Analytics e cookies. Não há banner de cookies (decisão de sempre).

## Decisões já tomadas

- **Uma propriedade por pessoa**, com um identificador só para todos os sites dela. Os relatórios se separam pelo domínio (dimensão "Nome do host"). Uma por site seria o mesmo trabalho repetido, sem ganho para a análise.
- **Marcelo:** conta Google marcelo.ckx@gmail.com, conta do Analytics "Afiliados" (412569484), propriedade "Rede de afiliados (Marcelo)" (559669274), identificador **G-WJGPEJFWLS**. Sem administrador extra (*"nao precisas colocar escritorioecasa como administradora, nao vai mudar nada"*).
- **Bárbara:** no e-mail dela, numa propriedade dela. Os sites só dela vão para a propriedade dela.
- **Site de dono compartilhado** ("Marcelo e Bárbara", "Marcelo e Snizhana"): fica de fora até a pessoa dizer em qual propriedade entra.
- **Site que já tinha Analytics fica com o dele:** oguiacompra (G-BJSMLJCHF8, com o `aw` do Google Ads) e melhorcreatina (G-4KDVP5L4P6, da Bárbara).
- **Site travado** (`contentLocked` ou `deployBlocked` no sites-meta) fica de fora: publicar é o que liga o Analytics.

## Fase 0: quem roda e quais sites

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
    if not v.get('live') or v.get('owner') != dono or not os.path.isdir(f'sites/{s}'): continue
    p = f'sites/{s}/src/analytics.json'
    ga4 = (json.load(open(p)).get('ga4') or '').strip() if os.path.exists(p) else ''
    trava = 'TRAVADO' if v.get('contentLocked') or v.get('deployBlocked') else ''
    print(s, ga4 or 'sem Analytics', trava)
EOF
```

O pull vem antes de tudo: a comparação da Fase 1 constrói o site nesta máquina, e o painel publica o que está na VPS. Com o repositório daqui atrasado, a comparação não mostra o que a publicação leva. O script acha o repositório principal pelo endereço (na Bárbara, o `upstream`).

Mostre a lista à pessoa: quantos sites, quais ficam de fora e por quê.

## Fase 1: o que cada publicação levaria junto (antes de tudo)

Ligar o Analytics é publicar o site de novo, e a publicação leva junto tudo o que mudou no código desde a última vez. Em 19/10/2026, 13 dos 35 sites do Marcelo tinham código comum ainda não publicado. Construa e compare cada site com o que está no ar:

```bash
pnpm --filter {site} build          # um por site; sem node_modules: pnpm install --frozen-lockfile --filter "./sites/{site}..."
bun scripts/site-comparar-no-ar.ts {site} [{site}...]
```

O comparador olha a lista de endereços dos sitemaps e, numa amostra de páginas (início, artigos, produto, Sobre, autor e categoria), o título, a descrição, o canonical, o texto, os links e os dados estruturados.

- **Igual ao que está no ar:** a publicação leva só o Analytics. Pode seguir.
- **Diferença só na página de categoria** (por exemplo, a descrição montada pelos artigos): pode seguir. Página de categoria pode mudar (regra do Marcelo).
- **Diferença em artigo, página de produto, Sobre ou na lista de endereços:** pare naquele site e mostre a diferença à pessoa. Página que existe só no ar seria apagada pela poda do deploy. Artigo no ar não muda sem o pedido dela.

## Fase 2: criar a conta e a propriedade no Analytics (Chrome da pessoa)

Pule esta fase se a pessoa já tem a propriedade e deu o identificador. Antes de abrir, avise numa linha: o quê (criar a conta e a propriedade do Analytics), o site (analytics.google.com) e a conta Google (a logada no Chrome). Carregue a skill `chrome-browser`. O Claude nunca digita senha. Se pedir login, a pessoa entra.

1. Confira a conta logada: `accounts.google.com/AccountChooser?continue=https://analytics.google.com/` mostra as contas do perfil. Conta sem nenhum Analytics cai na tela "Começar a usar".
2. **Conta:** nome "Afiliados". Nas "Configurações de compartilhamento de dados", desmarque as quatro caixas, que é a opção mais reservada. Clique em Próximo.
3. **Propriedade:** nome "Rede de afiliados ({pessoa})", fuso Brasil e Horário de São Paulo, moeda Real brasileiro. Os seletores têm busca: digite "Brasil", "Paulo" e "Real".
4. **Empresa:** setor Compras, tamanho Pequena. **Objetivos:** "Entender o tráfego da Web" e "Ver o engajamento". Clique em Criar.
5. **Termos:** escolha o país Brasil. **Aceite só com o sim da pessoa nesta conversa.** Para quem está na Europa, o Google só libera o botão com a caixa dos Termos de Tratamento de Dados marcada (aconteceu com o Marcelo). Explique isso no pedido do sim.
6. **Fluxo de dados:** Web, com a URL de um dos sites e o nome "Sites de {pessoa}". A medição otimizada fica ligada, como vem. O identificador G-... aparece no trecho de código da tela "Configurar uma tag do Google". Ele não está no texto da página: leia pela imagem (zoom).
7. Se aparecer "Meus comunicados por e-mail", use "Desmarcar tudo e salvar".
8. **Guarda dos dados:** Administrador > Coleta e modificação de dados > Retenção de dados. Ponha 14 meses (o padrão do Google é 2 meses) e salve. Recarregue a página para conferir.

## Fase 3: gravar o identificador

**Marcelo:** direto nos arquivos, mantendo os outros campos (o `aw` do oguiacompra), e um commit só:

```bash
python3 - {site} [{site}...] <<'EOF'
import json, sys
for s in sys.argv[1:]:
    p = f'sites/{s}/src/analytics.json'
    raw = open(p).read(); d = json.loads(raw); d['ga4'] = 'G-XXXXXXXXXX'
    open(p, 'w').write(json.dumps(d, indent=2, ensure_ascii=False) + ('\n' if raw.endswith('\n') else ''))
EOF
git add sites/*/src/analytics.json && git commit -m "analytics: Google Analytics (G-...) em N sites" && git push origin main
bash scripts/painel-vps-pull.sh
```

**Bárbara:** pelo painel, site a site. A rota mantém os outros campos e faz o commit na VPS desde 20/10/2026 (antes ela regravava só o `ga4` e não commitava):

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

1. **Nas páginas:** o identificador e o carregamento leve (`carregarGtag`) na página inicial e num artigo de cada site, e nada do script antigo (`<script async src="https://www.googletagmanager`). Peça sem cache (`?cb=...`) e repita se um ponto da Cloudflare ainda mostrar a versão anterior: isso acontece por alguns segundos depois da limpeza. Site que já tinha Analytics e não foi publicado depois de 19/10/2026 ainda carrega o script do jeito antigo, junto da página (o melhorcreatina, conferido em 20/10/2026). O identificador está lá e a coleta funciona; publicar de novo passa para o carregamento leve.
2. **No navegador do app**, abra um artigo e confira o envio:
   ```js
   performance.getEntriesByType('resource').filter(r => /\/g\/collect/.test(r.name)).map(r => decodeURIComponent(r.name).match(/tid=([^&]+)|en=([a-z_]+)/g))
   ```
   Para testar o clique na Amazon sem gerar clique falso lá, impeça a navegação (`document.addEventListener('click', e => e.preventDefault())`) e dispare um clique num link da Amazon. Tem que sair `en=amazon_click`.
3. **No Analytics**, em Relatórios > Tempo real: as visitas chegando. A tela do fluxo de dados mostra "A coleta de dados não está ativa" por até 48 horas mesmo com dados chegando. Quem prova é o tempo real.

## Fase 6: depois de 24 horas

- **Clique na Amazon como evento principal:** Administrador > Exibição de dados > Eventos, aba "Eventos recentes", estrela no `amazon_click`. O Analytics só lista o evento até 24 horas depois da primeira coleta.
- O Google conta o clique na Amazon duas vezes, como `click` (clique de saída da medição otimizada) e como `amazon_click`. Para a análise vale o `amazon_click`.

## Armadilhas (aconteceram)

1. **O PageSpeed sem chave da API recusa por limite diário.** Pela página pagespeed.web.dev funciona. No navegador do app com o painel escondido, a página não desenha o resultado: rode no Chrome da pessoa (só leitura, sem conta, avisando antes).
2. **Uma rodada do PageSpeed varia alguns pontos.** Compare com duas rodadas, ou com um site do mesmo modelo sem Analytics.
3. **O checklist do painel mostra o retrato do Search Console guardado na memória** e só relê quando o painel reinicia.
4. **Lista mostrada à pessoa sem conferir:** em 19/10/2026 entrou na "primeira leva" um site que levava 17 arquivos de código pendente (melhorsecador). Monte a lista a partir da comparação da Fase 1, não de memória.
5. **Disco cheio no meio da publicação:** um comando falhou com "no space left on device". Confira o espaço (`df -h /System/Volumes/Data`) antes de construir muitos sites.

## Registrar desvio de execução (obrigatório quando houver)

SE você (a) executou diferente do que esta skill manda, (b) **criou um passo que ela não tem**, (c) achou a régua ambígua ou contraditória, ou (d) topou com bug numa ferramenta dela, ENTÃO registre antes de fechar:

```bash
bun scripts/skill-log.ts note analytics-ligar <desvio|ambiguidade|bug|inventou-passo> "<o que fugiu e por quê>" [--alvo=<fase>]
```

Execução limpa **não gera linha**: vazio é dado.
