---
name: site-portar-wordpress
description: "Porta um site WordPress da rede (Hostinger) para Astro com o MESMO texto e os mesmos endereços, e vira os 301 de TODA a cadeia de domínios dele para um único herdeiro. Três cenários, em ordem de preferência — devolver o texto a um herdeiro Astro que já existe (cozinha), portar no mesmo domínio, ou domínio novo (só com decisão registrada do Marcelo: 9 de 10 domínios que receberam texto de outro domínio caíram em 05-06/2026). Fases com gates — decisão, levantamento, exportação na VPS (ou pelo Arquivo da Internet quando o WordPress já saiu do ar), conversão e conferência dos dados de produto (ASIN × nome × bíblia), site (institucionais, H1, categorias, estrela, páginas de produto), travas antes de publicar, virada (regras geradas da varredura, deploy, worker, zonas antigas, conferência pelo histórico do GSC a partir da VPS), Search Console, painel (coletas, linhagem, mapa) e medição semanal por 8 semanas com grupo de controle e plano B. Aceita `{dominio-wp} {site}` ou `medir {site...} --desde=AAAA-MM-DD`. NÃO é a site-migrar-dominio (site Astro que só troca de domínio). NÃO registra domínio, NÃO aponta NS, NÃO publica sem aprovação."
---

## Parse de input

- `{dominio-wp} {site}` — porta o WordPress `{dominio-wp}` para a pasta `sites/{site}` (que já existe, no cenário do herdeiro, ou vai ser criada).
- `medir {site...} --desde=AAAA-MM-DD` — só a Fase 8, para ports já feitos.

# Portar um WordPress para Astro

Casos de referência: seis ports de 19 a 21/09/2026 (analistadeprodutos → melhoreseletro, cadeirasconfortaveis → melhorcadeiradeescritorio, melhorwifi → melhoresparacasa, melhorbeleza → melhorestetica, melhoreseletronicos → melhortech, melhordacozinha → cozinhaideal). O que cada um ensinou, com números, está em `docs/port-wordpress/relatorio-analistadeprodutos-melhoreseletro.md`. Cada port novo acrescenta uma seção lá.

## O que esta skill É (e não é)

É levar o **texto** de um WordPress para um site Astro e fazer **todos** os domínios da cadeia apontarem direto para ele, sem passar por outro domínio antigo. O texto entra como está (`scripts/wp-portar.ts`, com `portadoDe` e `contentLocked: true`) e é reescrito aos poucos depois, se a medição mandar.

- **NÃO é a `site-migrar-dominio`**: aquela troca o domínio de um site Astro que já está no ar, sem mexer em conteúdo, de 1 domínio para 1. Ela mesma diz que não cobre consolidação nem go-live de site novo, e o port é as duas coisas. A Fase 5 daqui aponta para a Fase 2 dela (zona e DNS de domínio novo).
- **NÃO é clone** (`artigo-clonar-em-massa`): clone escreve do zero a partir das bíblias. Reescrever o portado é o plano B da Fase 8, e usa as skills de escrita.
- **NÃO registra domínio, NÃO aponta NS** (passo humano no Registro.br) e **NÃO publica sem o Marcelo pedir**.

## A evidência que pesa na decisão (medida em 22/09/2026)

O cânone da CLAUDE.md (19/09) diz que o texto igual em domínio novo trouxe o tráfego de volta maior. Medido depois, com a série semanal do GSC:

- **Trocas de domínio com o mesmo texto, de 11/2025 a 02/2026:** o domínio novo chegou a 11%–51% do pico do anterior em 5 de 7 casos. Só 2 passaram do pico anterior (o analistadeprodutos, no segundo salto, e a melhorbeleza, que partiu de base pequena).
- **Depois, todas caíram**, 3 a 6 meses após a troca. Foram três ondas: 18–25/05, 08–15/06 e 29/06/2026. Entre os sites com ≥10 cliques por semana no começo de maio, **9 de 10 domínios que tinham recebido texto de outro domínio perderam mais da metade até o fim de junho, contra 1 de 6 dos que nunca trocaram**. O melhorfonedeouvido, WordPress que nunca trocou, ficou estável.
- Hipóteses descartadas: "domínio com dono anterior" (os derrubados incluem domínios novos) e "a frota WordPress inteira caiu". A que sobra é "domínio jovem que recebeu texto e tráfego de outro", exatamente o que o cenário C cria.
- Reescrever do zero em Astro recuperou em 2 de 3 casos medidos (melhordaimpressora 99% do nível de maio, melhorestablets 192%; o compraguia não voltou). O produtosanalisados foi reescrito em 26/07 e ainda é cedo.
- É correlação com 16 sites, do mesmo período e da mesma família. Não é prova. É por isso que a Fase 8 mede com controle.

## Invariantes

- **Uma linhagem vai para UM herdeiro** (canon Marcelo, 19/09/2026). Se já existe site Astro nosso herdeiro dessa linhagem, o texto vai para ele (cenário A), nunca para um segundo site.
- **Cenário C (domínio novo) só com decisão do Marcelo registrada na conversa**, mostrando a evidência acima. Não é escolha da skill.
- **Não mexer no melhorfonedeouvido.com.br** sem pedido explícito: é o único WordPress com tráfego que resistiu a maio e junho.
- **Texto do WordPress não é reescrito no port.** Correção permitida sem perguntar: dado errado com destino óbvio (href quebrado, ASIN trocado confirmado pela página, pela bíblia ou pelo título na Amazon, meta vazia com `og:description` do próprio post). Cada uma vai no commit e no relatório. Depois de publicado, o artigo portado está `contentLocked: true`: corrigir só com o sim do Marcelo, com backup em `.painel-backups/` e `--no-verify` (a Fase J barra `.mdx` fora do painel).
- **Ordem da virada é dura:** o site serve → worker com as regras → rotas nas zonas antigas. Rota antes da regra manda o domínio para o fallback de 404 da rede (a home).
- **Domínio antigo nunca recebe `cf-create-zone`** (derruba o WordPress que ainda está lá) e o **MX dele fica intocado** (o e-mail mora na Hostinger).
- **Site com `contentLocked` ou `deployBlocked` no sites-meta: parar e avisar.** Código compartilhado (`packages/ui`) só com prova de que os outros sites do template não mudam (build antes e depois).
- **Deploy e virada só com aprovação explícita do Marcelo**, e só de site dele (a regra de rollout da memória: nunca dos sites da Bárbara nem em massa).

## Cenários (a Fase 0 escolhe)

| | quando | o que muda |
|---|---|---|
| **A. herdeiro que já existe** | há site Astro nosso na linhagem (cozinhaideal) | sem domínio novo; conferir template, slugs que já existem, regras do site que escondem slug, estrela, página de produto |
| **B. no mesmo domínio** | o WordPress é o próprio fim da cadeia e não há herdeiro | sem troca de domínio (a hipótese que sobra da evidência não se aplica). **Ainda não testado na rede.** O site é criado com o domínio do WordPress e o deploy põe as rotas do worker na zona que já existe: o `A` fica com proxy e o MX da Hostinger fica. **Não rodar `cf-create-zone`** nesse domínio: ele troca o MX pelo e-mail da Cloudflare e derruba a caixa da Hostinger |
| **C. domínio novo** | só com decisão do Marcelo | tudo do B, mais domínio novo (RDAP, dono anterior, GSC, DNSSEC, lista da Amazon) |

## Fase 0 — decisão (BLOQUEANTE)

1. Montar a cadeia: o card da linhagem no mapa das cadeias do painel, a sonda (`docs/painel/_data/domains-status.json`) e o worker. Declarar o grupo em `docs/painel/_data/grupos-legado.json` já aqui (do mais antigo para o mais novo, com o domínio de destino no fim), porque os scripts das próximas fases leem de lá.
2. `bun scripts/port-linhagem.ts {site}` — vida de cada domínio no GSC, elos, quem faz o 301 hoje.
3. Escolher o cenário pela tabela acima e dizer ao Marcelo, com os números da cadeia (pico, mês da queda, nível de agora) e a evidência. **Cenário C: parar aqui até ele decidir.**
   Decidir junto a estrela no Google: os ports de domínio novo saíram sem estrela (`ratingStars: false`, "sem estrela inventada"), e o herdeiro pode dar nota automática aos portados (cozinhaideal). Uma política só por site, registrada no relatório.
4. Sobreposição com a rede: artigos com o mesmo slug em outros sites nossos. Texto diferente (menos de 10% de 8-gramas iguais) pode conviver; texto igual não.

## Fase 1 — levantamento

- **Domínio de destino** (só C): RDAP (titular, **vencimento**: avise se vence em menos de 60 dias), sem pasta, sem sites-meta, sem regra no worker, não serve nada (controle positivo num WordPress de verdade). Dono anterior: Arquivo da Internet e sitemaps antigos no GSC.
- **Exportação, NA VPS** (a Hostinger bloqueia o Mac):
  `sudo -u melhorserum-painel bash -lc 'cd /home/melhorserum-painel/afiliados && bun scripts/wp-exportar.ts {dominio-wp} /home/melhorserum-painel/wp-export/{dominio-wp}-{data}'`
  e copiar para `~/Backups/afiliados/wp-export/`. Conferir: posts, páginas, categorias, autores, imagens com 0 falha.
- **WordPress que já saiu do ar** (a Hostinger só devolve 301, sem API; caso do compraguia, 24/09/2026): o texto vem das cópias do Arquivo da Internet, no Mac:
  `bun scripts/wp-exportar-arquivo.ts ~/Backups/afiliados/wp-export/{site}-arquivo-{data} --dominios {todos os domínios onde o texto esteve} --origem {herdeiro} --site {site} --amazon --slugs-de {lista}`.
  Vence a cópia mais nova com o artigo inteiro, em qualquer domínio da cadeia (no compraguia, o próprio compraguia teve os textos como WordPress até 06/2026, mais novos que os do guiacompra). O script desfaz o carregamento preguiçoso das imagens, tira a caixa do autor e troca os domínios da cadeia pelo `--origem`.
  **A foto do produto quase nunca está no Arquivo** (3 de 157 no compraguia): o robô dele não pede a imagem que carrega com a rolagem. Ela vem, nesta ordem, do mesmo arquivo trazido por outro port, da página de produto do mesmo ASIN no herdeiro e da foto principal da Amazon (`--amazon`, para no primeiro captcha; rode de novo depois). A fonte de cada uma fica em `imagens.json` da pasta. ⚠ As duas últimas vão pelo ASIN do card: se o item 3 da Fase 2 trocar o ASIN de um card, apague a foto dele da pasta e rode o exportador de novo antes do `--gravar`.
- **Cenário A:** slugs do WordPress que já existem no herdeiro. Reescrito do zero e no ar fica como está (artigo no ar não muda: canon 12/09); só entram os que faltam.

## Fase 2 — conversão e dados

1. `bun scripts/wp-portar.ts {export} sites/{site} --tag {tag} [--cadeia dominios-anteriores] [--irmaos dominios] [--so slugs] [--ano AAAA]` sem `--gravar`: todo post no formato, texto ≥99%, imagens 0 faltando, 0 link para outro site da rede. Depois com `--gravar`.
   - **Link para outro site da rede impede o `--gravar`** (Marcelo, 24/09/2026: site da rede não linka outro site da rede). Quase sempre é domínio da cadeia que faltou no `--irmaos`: o texto antigo linka os domínios anteriores em endereço absoluto (543 links no compraguia).
   - `--ano 2026` troca o ano velho do título e da descrição (o texto fica). Decisão do Marcelo para o compraguia (24/09/2026). Confira os avisos: o `listHeading` e a introdução continuam com o ano do texto, e um ano que é nome de modelo ("iPad 2025") também seria trocado.
   - `--tag`: a do próprio WordPress (conferir a mais usada nos posts) ou a do herdeiro. Nunca inventar tag.
   - `--so` regrava o `port-plano.json` só com esses posts: rode de novo sem `--gravar` e sem `--so` para refazer o plano inteiro.
   - Cenário A: categorias do WordPress genéricas ("melhores") saem; cada artigo vai para a categoria do seu produto que o herdeiro já tem.
2. **Keyword.** O `wp-portar` propõe `keyword` e `keywordPlural` de cada artigo (`scripts/lib/keyword-do-port.ts`): o 1º negrito da introdução, que é a keyword que o texto do WordPress já usa, e o plural pelo último negrito ou pelo `listHeading` quando o negrito repete o singular. A lista sai no relatório ("keywords propostas") e no `port-plano.json`. **É proposta:** confira toda linha marcada com ⚠ antes do `--gravar`, com esta régua (Marcelo, 22/09/2026):
   - keyword é **"melhor X" por padrão**. A forma sem "melhor" costuma ter SERP transacional (loja, fabricante, Shopping) e só vale quando a SERP dela é de conteúdo: faixa de preço ("celular até 1000 reais"), uso ("notebook para trabalhar"). **Não é regra:** abra a SERP do Google BR e conte conteúdo × loja nos orgânicos;
   - Search Console da linhagem (buscas da página, com posição e CTR): título e busca concordando contra o negrito, vence o título. CTR baixo em posição boa mostra que o clique vai para outro lugar (Shopping, anúncio, loja), mas **não diz se o orgânico é de loja ou de conteúdo**: em 22/09/2026, "celular até 1000" tinha 0,2% na posição 4,6 (contra 1,3% de "melhores celulares até 1000 reais" na 4,3) e o orgânico era de blogs, com o clique indo para um bloco de ~20 produtos. Compare CTR só entre posições parecidas, porque ele cai com a posição. **Quem decide é a SERP;**
   - artigo que rankeia bem na forma ampla sem "melhor" é **artigo forte**, não motivo para mirar nela ("pressurizador de água" na posição 3,5, com os 4 primeiros orgânicos todos lojas);
   - keyword no singular e sem ano; plural com concordância ("melhores cadeiras gamer", não "melhores cadeira gamers").

   Por que importa: a `artigo-guia-escrever` analisa os concorrentes da SERP da keyword EXATA (numa SERP transacional, os "concorrentes" são lojas) e a `linkagem-auditar` compara a âncora com ela. Os 6 primeiros ports saíram **sem keyword** nos 112 artigos e ela foi preenchida depois (commit `49e29cfe6`); a proposta automática acerta 104 keywords e 102 plurais desses 112, e o resto foi decisão por Search Console e SERP.
3. `bun scripts/port-dados-produto.ts {site} --amazon` (no Mac). Sai 1 enquanto sobrar achado:
   - **marca** do nome contra a página ou a bíblia do mesmo ASIN, e **ASIN repetido** no artigo;
   - **card × texto** (`scripts/lib/card-texto.ts`): o texto do produto, ou o guia, linka com o nome do produto um ASIN diferente do card. É o erro mais comum: no WordPress o autor copiava o card do produto vizinho e esquecia de trocar o ASIN, e o texto ficava com o certo. A dica diz o provável (card errado, texto errado ou dois ASINs com o mesmo nome);
   - `--amazon` lê título e estoque dos dois ASINs pelo curl. Funciona no Mac; a Amazon bloqueia a VPS, e a PA-API foi desligada.

   O `wp-portar` já avisa o card × texto na conversão. Decida cada achado pelo título na Amazon:

   | o que a Amazon mostra | o que fazer |
   |---|---|
   | o ASIN do texto é o produto do nome, e o do card é outro | trocar o `asin` do card (ele gera 7 links na página: tabela do topo, foto, nome, botões) e os links com o nome que ainda levem ao errado |
   | o ASIN do link é o card de outro produto da lista | trocar o link do texto |
   | o certo saiu da Amazon (404) ou está indisponível, e o card leva a outro produto | **sucessor** (ver abaixo): o card do WordPress costuma já ser o sucessor, porque essa era a prática do Marcelo; confira se é da mesma linha. Não serve: sucessor novo ou, sem sucessor claro, o certo mesmo fora de estoque |
   | o certo saiu da Amazon, mas o mesmo modelo está à venda em outro anúncio | o anúncio atual (é o mesmo produto, não é sucessor) |
   | nenhum dos dois é o produto (o WordPress nunca teve o certo) | achar na Amazon o anúncio que bate com o texto (modelo, memória, 4G ou 5G) e anotar no commit |
   | variante (cor, memória, voltagem), modelo vizinho à venda com o do nome esgotado, ou os dois esgotados | não mexer; registrar em `docs/port-wordpress/card-texto-conferidos.tsv` com o veredito |
   | produto listado duas vezes (o título diz N e a lista tem N+1) | tirar a repetição |

   **Produto que saiu de linha: link para o sucessor, sem aviso** (Marcelo, 24/09/2026; era a prática dele no WordPress, e vale para qualquer artigo, não só no port):
   - **Só o link muda.** O `asin` do card vai para o sucessor (gera os 7 links do card) e todo link do texto que ia ao original vai também. Nome, review, foto (a do original, que combina com o nome) e texto ficam. Sem foto do original em lugar nenhum, a do sucessor.
   - **Marcação interna, obrigatória:** `sucessorDe: { asin: <original>, motivo: "fora da Amazon (404)" | "indisponível", em: AAAA-MM-DD }` no produto. Não aparece na página (a página de produto tem o `descontinuado`, que mostra banner; o artigo não mostra nada). `bun scripts/sucessores.ts` lista a rede; o `port-dados-produto` deixa de acusar card × texto entre sucessor e original.
   - **Sucessor de verdade:** mesma marca e linha, mesma faixa de preço e de uso (Redmi 13C → 15C, POCO C65 → C85). No compraguia o WordPress tinha trocado o Galaxy M55 pelo A07 (faixa mais barata) e o Xiaomi 13C pelo POCO M7 Pro (mais cara): isso não é sucessor. Sem sucessor claro, o original fica e o artigo entra na lista da reescrita.
   - **Escopo no port:** os que saíram da Amazon e os que o WordPress já tinha trocado. Os só indisponíveis, que ainda têm página, ficam para uma passada da rede com o mapa pronto: ler todos custa várias rodadas por causa do captcha (257 produtos em 34 artigos).

   Medido nos 6 primeiros ports, que foram ao ar sem este passo (22/09/2026):
   - **24 correções em 19 artigos**, feitas depois de no ar;
   - marca e repetido achavam 15 delas;
   - card × texto achou as outras 9, 2 delas no guia;
   - 14 casos ficaram como variante ou esgotado.
4. Links internos quebrados que já eram quebrados no WordPress: apontar para o artigo que a âncora nomeia (só o `href`).

## Fase 3 — o site

**Cenário C ou B (site novo):** persona pelo painel (`bun scripts/painel-api.ts POST /authors` e a foto), `POST /sites/create` (template6, `ratingStars` decidido na Fase 0) e a `site-criar-workflow` para o resto do scaffold. Se o `gitSync` voltar `commit-failed`, commitar na VPS com `PAINEL_AUTO_COMMIT=1` (aconteceu em 3 de 5 criações; o `detail` diz o motivo).
- `productPages: false`, o `[slug].astro` só com artigos (copiar de um site portado t6) e a divergência em `docs/painel/_lib/template-divergences.ts`.
- `config.ts`: H1 da home (o scaffold monta "O melhor {nome}" e quebra quando o nome não é substantivo simples), `contactMainTopic`, `knowsAbout`, e-mail do autor, bio sem "Testo" nem frase-sacada.
- `/sobre/` do WordPress adaptado (marca e domínio novos, sem alegar teste, com o escopo real) e `/author/` pela `preencher-institucionais` (ela tem a exceção de site portado).
- Descrição de categoria pela `categoria-descricao-escrever` (ou `-criar-em-massa`): as do WordPress repetem o mesmo molde entre sites.

**Cenário A (herdeiro):**
- Template do herdeiro precisa aceitar produto sem página: t6 com `productPages: false`; t5 e t7 com `productPagesOnlyWithMdx: true` (link pela página do mesmo ASIN, âncora quando não há página; no t7 desde 24/09/2026, para o compraguia) e o bloco do `[slug].astro` do cozinhaideal ou do compraguia. Outro template: código novo, com build antes e depois de outro site do mesmo template provando que nada muda.
- Estrela: decidir e registrar (o herdeiro pode dar nota automática aos portados; os ports de domínio novo saíram sem estrela).
- Regras do herdeiro que escondem slug: o `port-regras.ts` acusa na Fase 6; elas saem junto com a virada.

**Todos os cenários:** linkagem entre os artigos pela `linkagem-auditar {site}`, autorizando a edição dos portados (seção "Portados do WordPress" dela: com a regra de sempre ela pula todo artigo travado e não muda nada). O texto chega com os órfãos e as âncoras do WordPress, e a hora de mudar é antes de o artigo rankear (Marcelo, 22/09/2026). Precisa da keyword da Fase 2 preenchida. No herdeiro (A) entram também os links entre os portados e os artigos que o site já tinha, **em dois tempos** (combinado com o Marcelo em 24/09/2026): no port, só os portados (links entre eles e deles para os artigos do site); os links dos artigos do site para os portados, 3 a 4 semanas depois, se eles seguirem estáveis, com a regra "Artigo que já rankeia" da `linkagem-auditar` (1 link por artigo, sem mexer no resto). Separar no tempo é o que permite saber, se o site cair, qual das duas mudanças causou.

## Fase 4 — travas antes de publicar

`port-dados-produto` com saída 0 · keyword em todo artigo (`audit-linkagem {site}` sem `ancora-nao-verificada` nem `extracao-incompleta`) · Build · `check-dist-links` (0 quebrado) · `check-broken-images` · `audit-article` (portado: só erro técnico conta) · checklist do painel (`GET /site/{site}/audit-checklist`) · pré-checagem de publicação (`GET /deploy-precheck/{site}`) · no HTML gerado: canonical no domínio certo, 0 menção ao domínio antigo, uma tag só, sitemaps certos · **cenário A: toda URL do sitemap no ar tem que estar no build novo** (o deploy faz prune) · home, artigo, categoria e autor vistos no navegador.

## Fase 5 — zona e DNS (só C)

Seguir a **Fase 2 da `site-migrar-dominio`**: `cf-create-zone {site} --so-checar` e depois sem a flag, `conferir-delegacao.ts` antes e depois de trocar o NS (DS órfão do DNSSEC), `activation_check` se a zona ficar `pending`, e `cf-create-zone` de novo para ligar o e-mail.

## Fase 6 — publicar e virar (com aprovação)

1. `bun scripts/port-regras.ts {dominio-wp} {site} --incluir-hostinger --extra={arquivo.tsv}` — mostra as regras da cadeia inteira, os endereços que vão para a home e as regras do site que escondem artigo. O que tiver destino óbvio vai para o `--extra` (erro de digitação, home que era o próprio artigo no Arquivo da Internet, categoria renomeada). **Nunca a página inicial para slug de artigo:** sem regra própria, a regra geral leva o endereço ao mesmo caminho no site novo, que chega à home em 2 saltos enquanto não há artigo, e ao artigo quando ele for criado (recuperação de órfãs). Regra para a home vale antes da regra geral e segura o slug. Regra para a home só em listagem do WordPress (`page/2`, `category/…`, `melhores`). Depois `--gravar` (e `--tirar-escondidas` no cenário A) e commit. **Não publique o worker ainda.**
   - `--incluir-hostinger` sempre: todo 301 de domínio antigo mora no worker, inclusive o que a Hostinger já levava direto ao site (decisão do Marcelo, 22/09/2026). Na Hostinger ele fica fora do painel e não aceita regra por endereço.
   - Depois de `--gravar`, rode o mesmo comando sem `--gravar`: tem que sair **0 regra nova**. Se sair, é regra de um domínio que ainda não foi para os outros da cadeia (o `port-regras` leva a regra a todos os domínios dela); grave de novo. Caso real (22/09/2026): 84 regras ficaram de fora na primeira gravação do compraguia (quase todas de slug para a home, que depois saíram pela armadilha 14: o que conta é a regra ter destino).
   - Domínio da cadeia sem propriedade no Search Console (a varredura avisa "GSC 403"): liste os endereços dele no Arquivo da Internet (`https://web.archive.org/cdx/search/cdx?url={dominio}/*&output=json&fl=original,timestamp,statuscode&collapse=urlkey`) e ponha no `--extra` os que não têm equivalente no site, para irem à home em 1 salto.
   - **Herdeiro cuja cadeia já foi virada antes** (compraguia, 24/09/2026: "o domínio continua o mesmo, só adicionar os artigos"): o port-regras sai com 0 regra nova e o `--gravar` recusa por causa dos conflitos, que aqui são sugestões de destino melhor para regras que já existem (categoria da cadeia que ia para a home e agora existe no site). Mudar essas regras não é o pedido. Tire só as regras que escondem os portados direto no `worker/redirects.json`, filtrando pelo host do site: a mesma slug tem regra em outros domínios da rede (no compraguia, escritorioecasa e guiamelhor). Confira que o arquivo resultante é a lista original menos elas, e rode o port-regras de novo sem `--gravar`: não pode sobrar nenhuma escondida. Os conflitos e os endereços com destino óbvio vão para o relatório, para decisão do Marcelo.
2. `bun scripts/cf-deploy-r2.ts {site}` e conferir **pela VPS** (200, `www` com 301, canonical). `live: true` no sites-meta.
3. `bun scripts/cf-deploy-worker.ts`. Espere uns 30 segundos antes de testar: a versão nova leva esse tempo para chegar a todos os pontos da Cloudflare, e um teste logo depois pode pegar a versão anterior (22/09/2026).
4. `bun scripts/port-zonas-antigas.ts {todos os domínios antigos da cadeia}` e, conferido, `--aplicar` (rotas, proxy, purge, MX igual). O script recusa domínio sem catch-all no worker. Endereço com `www` chega em 2 saltos (o worker tira o `www` antes da regra), como em todo domínio antigo do worker.
5. `bun scripts/port-conferir.ts --montar {dominio-wp} {site} --extra={arquivo.tsv} [--com-site] > lista.tsv` no Mac, copiar a lista para a VPS e lá, com o commit dos scripts já puxado, `sudo -u melhorserum-painel bash -lc 'cd /home/melhorserum-painel/afiliados && bun scripts/port-conferir.ts --testar /tmp/lista.tsv'`. Todo endereço com clique tem que cair no destino esperado: em 1 salto quando tem regra própria; em 2, pela regra geral, quando não tem artigo no site novo ou quando o próprio site já redireciona o caminho (a 5ª coluna da lista diz quantos, e o resumo conta os que passaram em 2). O que ficar fora volta ao passo 1. `--com-site` no cenário A: o histórico do próprio herdeiro também muda com a virada.

## Fase 7 — Search Console e painel

- C: `bun scripts/gsc-registrar-dominio.ts {dominio-novo}`.
- Depois da virada: `bun scripts/gsc-apagar-sitemaps-wordpress.ts {todos os domínios, inclusive o novo} --aplicar` (a propriedade nova pode trazer sitemaps do dono anterior).
- As quatro coletas:
  - **na VPS**, do mesmo jeito que acima (`sudo -u melhorserum-painel bash -lc 'cd /home/melhorserum-painel/afiliados && …'`): `bun docs/painel/scripts/cf-accounts-snapshot.ts` (commit à mão) e `bash scripts/cron-domains-status.sh`. O retrato das contas **só na VPS**: no Mac há credencial de uma conta só, e o arquivo sai com `accounts_checked: 1` e as zonas da outra conta sem dado (22/09/2026). Confira `accounts_checked: 2` antes do commit;
  - **no Mac**: `bun docs/painel/scripts/linhagens-snapshot.ts` (é dele a data "na Cloudflare desde" das caixas do mapa) e `bun scripts/mapa-artigos-orfaos.ts`. Confira antes que o Mac resolve o domínio novo.
- Linhagem: `bun scripts/port-linhagem.ts {site}` sugere os elos da Hostinger que faltam declarar (régua da inclusão, ou "visto" pela primeira coleta da sonda) e os declarados que o worker encerrou. Gravar em `linhagens-declaradas.json` com nota.
- Gerar o painel e **olhar o mapa na tela** (prévia com o `main.css` embutido, sem scripts nem tabelas, abaixo de 512 KB, apagada depois): um card, domínios em laranja ou roxo, nenhum ponto vermelho, o domínio portado fora de "Sem site no painel", cadeia original na ordem do tempo.
- C: conferir no console da Amazon se o domínio novo está na lista de sites (`amazon-lista-sites-auditar`).

## Fase 8 — medir e decidir

- No dia da virada e toda semana, por 8 semanas:
  `bun scripts/port-medir.ts {site} --desde={virada} --controle={3 ou 4 sites não portados} --gravar=docs/port-wordpress/medicao/{site}-{data}.json`
  Controle: sites Astro feitos do zero em domínio com histórico e publicados perto da mesma data (em 09/2026: oguiacompra, guiamelhor, melhorescustobeneficio; e o melhorimpressora como referência de site que cresceu).
- **Critério, escrito antes de ver o resultado:** o port vale se, na semana 8, a soma (novo + cadeia) estiver acima da média das 4 semanas antes da virada **e** crescendo mais que o controle em cliques por artigo. Abaixo da média de antes na semana 8: plano B.
- **Plano B:** reescrever pelas skills de escrita (lineup, reviews, guia, intro, meta) nos MESMOS endereços, começando pelos artigos de maior histórico. Em site com muitos artigos, reescrever metade e manter metade portada: mesmo domínio e mesmo período dão a única comparação limpa entre "mesmo texto" e "reescrita".

## Armadilhas (cada uma aconteceu)

1. **Varrer só o domínio pedido.** Os domínios de cima da cadeia, que redirecionam pela Hostinger, ficaram passando por outro domínio antigo (2 saltos entre domínios) no wi-fi e na beleza. `port-regras.ts` usa a cadeia inteira. Não confundir com os 2 saltos aceitos da armadilha 14, que são dentro do site novo (caminho sem artigo → página inicial).
2. **Conferir a regra contra ela mesma.** A lista de teste tem que vir do histórico do GSC (`port-conferir.ts`), não das regras.
3. **Home que era o artigo.** A home do melhoresnotebooks2025 (2.383 cliques) era o próprio artigo "Melhores Notebooks"; o catch-all mandaria para a home do site novo.
4. **Regra do herdeiro que esconde o artigo portado.** 20 no cozinhaideal; no worker, a regra vale antes da página.
5. **Dados de produto do WordPress.** O card levava a outro produto em 24 lugares de 19 artigos nos 6 primeiros ports, publicados assim. A checagem de marca não vê erro dentro da mesma marca (Deco M5 com o ASIN do M4) nem ASIN sem bíblia. Card × texto e leitura na Amazon, na Fase 2.
6. **Scaffold com texto de template:** `/sobre/` provisório, autor alegando teste presencial, H1 quebrado, e-mail `@dominio`, `knowsAbout` de outro nicho.
7. **Descrição de categoria do WordPress** repete o mesmo molde entre os sites portados.
8. **Sitemap de dono anterior** na propriedade nova do GSC (melhoreseletro, melhorestetica, melhortech).
9. **DNSSEC:** domínio que usava o DNS do Registro.br tem DS; trocar o NS sem tirar o DS derruba a resolução.
10. **Commit do scaffold falhando na VPS** (`index.lock`, rebase): o `detail` do `gitSync` diz o motivo; commitar à mão com `PAINEL_AUTO_COMMIT=1`.
11. **Página de produto casada pelo nome** (t5): produto com página de outro nome quebrava o build; o flag casa pelo ASIN.
12. **Número de memória no relatório.** Todo número do relatório sai de um arquivo ou de uma medição feita na hora.
13. **`sudo -u melhorserum-painel bun` na VPS dá "command not found":** o `sudo` não carrega o PATH do usuário. Use `sudo -u melhorserum-painel bash -lc 'cd /home/melhorserum-painel/afiliados && bun …'`.
14. **Regra para a home em slug de artigo.** Para cumprir "1 salto", criei 218 regras de slug de artigo e endereço malformado para a home nos domínios antigos do compraguia e da cozinha, e 24 cópias das regras do próprio compraguia (22/09/2026). As duas seguravam o endereço: a do artigo, quando ele fosse criado; a cópia, quando o site mudasse a regra dele. Foram apagadas; o critério de saltos agora aceita 2 pela regra geral.
15. **Port sem keyword.** Os 112 artigos dos 6 primeiros ports saíram sem `keyword`, e a linkagem passou "0 erros de âncora" com 195 links sem medição. Preenchida em 22/09/2026 pela régua da Fase 2; em 3 artigos a proposta saiu sem "melhor" — no pressurizador e no robô que passa pano porque a forma sem "melhor" tinha mais clique, no robô com mapeamento porque era o negrito do texto. Nos três, a SERP da forma sem "melhor" era de loja, e a keyword ficou com "melhor".

## Registrar desvio de execução (obrigatório quando houver)

SE você (a) executou diferente do que esta skill manda, (b) **criou um passo que ela
não tem**, (c) achou a régua ambígua/contraditória, ou (d) topou com bug numa
ferramenta dela — ENTÃO registre antes de fechar:

```bash
bun scripts/skill-log.ts note site-portar-wordpress <desvio|ambiguidade|bug|inventou-passo> "<o que fugiu e por quê>" [--ctx=site/slug] [--alvo=<fase>]
```

Execução limpa **não gera linha** — vazio é dado. O que se lê depois é
`bun scripts/skill-log.ts report`, que conta por skill e destaca o que já bateu
mais de uma vez. Sem `--alvo` a nota cai em `geral` e sai do detector de
reincidência, então **nomeie a fase** quando ela existir.
