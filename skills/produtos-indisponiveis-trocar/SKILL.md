---
name: produtos-indisponiveis-trocar
description: "Troca o link dos produtos que não se compram mais na Amazon (página inexistente ou \"Não disponível\") nos artigos de um ou mais sites, mantendo o texto, o nome e a foto do card: lê a disponibilidade, busca o substituto (mesmo modelo, sucessor ou parecido da mesma marca), confere a página de cada um, aplica, registra, publica os sites do Marcelo e confere no ar. Use na leitura mensal dos sites no ar, depois de um port, ou quando o Marcelo pedir para trocar produtos indisponíveis (`{site...}`)."
---

## Parse de input

- `{site...}`: as pastas em `sites/` a tratar.
- Sem site: pergunte quais (a leitura de um site grande leva perto de 10 minutos no navegador).

# Trocar produtos indisponíveis

Regra do Marcelo (24/09, 02/10, 03/10 e 19/10/2026): produto que não dá para comprar ganha outro link, e o nome, o review e a foto do card ficam. O Google não avalia o link da Amazon (todo link tem nofollow e nenhum está nos dados estruturados), então a posição do artigo não muda. *"Enviar cliente pra produto inválido é ruim, ele vai achar que o artigo é ruim e sair"* (19/10/2026).

A regra completa (o que troca, a ordem dos substitutos, qual anúncio escolher) está em `site-portar-wordpress`, item "Produtos da Amazon"; a ferramenta é `scripts/disponibilidade-amazon.ts` (o cabeçalho dela tem o laço de leitura). Esta skill é o procedimento de ponta a ponta, montado em 19/10/2026 quando 17 sites portados passaram pela troca (205 cards em 109 artigos).

Caso-origem (19/10/2026): nos ports antigos, "Não disponível" esperava uma 2ª leitura que atrasou; 535 dos 2.322 produtos estavam indisponíveis, 130 de 311 no compraguia. Desde então "Não disponível" troca já, na 1ª leitura.

## Invariantes

- **Só o link muda.** Nada de texto, nome, foto, ordem ou produto novo no card. Troca de produto com texto novo é reescrita e é decisão do Marcelo.
- **Ordem dos substitutos:** o mesmo modelo em outro anúncio; o sucessor da mesma marca e linha, na mesma faixa de preço; um parecido da mesma marca e do mesmo tipo, com a ficha e o preço que o card descreve. **Outra marca nunca.** Sem nenhum dos três, o produto fica e vai para `sem-substituto.json` com o motivo.
- **Confira a página de cada substituto antes de gravar,** não o título da busca: à venda, não é seminovo (nem "Amazon Seminovos"), voltagem, tamanho, cor e gênero do card, quem vende. Mesmo modelo só em loja de terceiro e com preço alto indica que saiu de linha.
- **Faixa de preço:** sucessor que custa o dobro ou mais do card não é sucessor (JBL Pulse 5 → Pulse 6 a R$ 3.434, 19/10/2026); procure o parecido no preço ou deixe sem troca.
- **Artigo com teto de preço no título** (`notebook-ate-2500-reais`): substituto acima do teto é decisão do Marcelo. No compraguia, em 19/10/2026, ele escolheu trocar mesmo assim; liste os casos no relatório.
- **Conflitos:** o substituto não pode já estar no artigo, e dois cards diferentes do mesmo artigo não vão para o mesmo produto. Link de texto do mesmo produto de um card segue o card.
- **Produto com página própria no site não troca** (a ferramenta recusa): o artigo acha a página pelo ASIN do card. Fica para o ajuste do modelo.
- **Artigo travado (`contentLocked`)**: a troca de link entra com o sim do Marcelo, sem destravar.
- **Publicar:** sites do Marcelo, quando ele pediu a troca; site da Bárbara (`owner` no `sites-meta.json`) fica aplicado e só publica com o sim dele.
- **Verificação de robô da Amazon** ("Clique no botão abaixo para continuar comprando"): nunca clicar. Pare o laço e retome mais tarde.

## Fase 1 — o que trocar

Pasta de trabalho no scratchpad (`$W` abaixo). Para cada site:

```bash
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" && test -f docs/painel/sites-meta.json || exit 1
bun scripts/disponibilidade-amazon.ts lista {site}        # ASINs a ler
```

Leia na Amazon com o laço do cabeçalho do `disponibilidade-amazon.ts`, numa aba da amazon.com.br no navegador do app, e grave com `importar <arquivo.json> --data=AAAA-MM-DD`. Depois:

```bash
python3 .claude/skills/produtos-indisponiveis-trocar/montar-lista.py $W {site}
```

Grava `$W/{site}-trocar.json` (produto, título da Amazon, nome do card, artigos, página própria) e imprime as buscas. Confira as buscas antes de rodar: o tipo vem do título da Amazon; se a busca não descreve o produto, corrija à mão.

## Fase 2 — buscar

No navegador do app, na aba da amazon.com.br. Com o painel escondido o Chrome desacelera os timers: rode dois ou três laços de cada vez, sem espera entre as consultas.

```js
window.__bus={}; window.__st={};
window.__buscar=async(nome,parte)=>{ window.__st[nome]='lendo'; for(const [a,k] of parte){ try{
  const t=await (await fetch('/s?k='+encodeURIComponent(k))).text(); const d=new DOMParser().parseFromString(t,'text/html');
  const itens=[...d.querySelectorAll('[data-asin][data-component-type="s-search-result"]')];
  if(!itens.length && /captcha|validateCaptcha/i.test(t)){ window.__st[nome]='captcha'; return }
  window.__bus[a]=itens.filter(x=>!x.querySelector('.puis-sponsored-label-text, .s-sponsored-label-text')).slice(0,6)
    .map(x=>[x.dataset.asin,((x.querySelector('.a-price .a-offscreen')||{}).textContent||'').trim(),((x.querySelector('h2')||{}).textContent||'').replace(/\s+/g,' ').trim().slice(0,85)]);
  }catch(e){ window.__bus[a]=[['erro','',String(e).slice(0,40)]] } } window.__st[nome]='fim' };
// const Q = <buscas da Fase 1>; const m=Math.ceil(Q.length/2); __buscar('a',Q.slice(0,m)); __buscar('b',Q.slice(m));
```

Resultado grande não cabe na resposta da ferramenta: devolva `JSON.stringify(window.__bus)` com uns 90 mil caracteres de enchimento depois de uma quebra de linha. A resposta vai para um arquivo, e o Python lê com `json.JSONDecoder().raw_decode`.

## Fase 3 — escolher e conferir

Para cada produto, escolha pela ordem das Invariantes e escreva em `$W/decisoes.py`:

```python
D = {
 'B07493523N': ('B0GZWXJ372','parecido','parecido: depurador Electrolux 80 cm DE8SB 110V, preto (o DE80X inox 127V saiu)'),
 'B089329JYS': (None,'sem','o depurador Mondial DP60 à venda é só de 220V, e o card é de 110V'),
 'B09HL9FF16': ('B0FTR8SV9T','pagina','tem página própria, espera o ajuste do modelo'),
}
```

O motivo é a frase que o Marcelo lê no painel ("Trocas de link"): marca e modelo de antes → depois, ou "parecido: …", ou por que ficou.

Confira a página de cada substituto e do original (a voltagem do card vem do título do original):

```js
window.__conf={};
window.__ler=async(nome,parte)=>{ window.__st[nome]='lendo'; for(const a of parte){ try{
  const r=await fetch('/dp/'+a); const t=await r.text(); const d=new DOMParser().parseFromString(t,'text/html');
  const ti=d.querySelector('#productTitle'); if(!ti && r.status!==404 && /captcha|validateCaptcha/i.test(t)){ window.__st[nome]='captcha'; return }
  const bb=(d.querySelector('#desktop_buybox,#buybox,#rightCol')||{}).textContent||''; const av=(d.querySelector('#availability')||{}).textContent||'';
  const e=r.status===404?'404':(d.querySelector('#add-to-cart-button')||/em estoque/i.test(av))?'venda':(d.querySelector('#outOfStock')||/Não disponível/.test(bb))?'indisp':/opções de compra/.test(bb)?'outros':'?';
  const tx=s=>((d.querySelector(s)||{}).textContent||'').replace(/\s+/g,' ').trim();
  const vend=tx('#merchantInfoFeature_feature_div')+tx('#sellerProfileTriggerId'), env=tx('#fulfillerInfoFeature_feature_div'), marca=tx('#bylineInfo');
  const all=d.body?d.body.textContent.replace(/\s+/g,' '):'';
  window.__conf[a]={e, amz:e==='404'?null:/Amazon/.test(vend)?'vende':/Amazon/.test(env)?'entrega':'não',
    semi:/seminovo|renovado|recondicionado/i.test(d.title)||/Seminovos/.test(marca), alto:/Preço mais alto do que o habitual/.test(bb),
    preco:(tx('#corePrice_feature_div .a-offscreen')||tx('.a-price .a-offscreen')).slice(0,14), marca:marca.slice(0,40),
    volt:(all.match(/Voltagem[^A-Za-z]{0,6}[^|]{0,25}/)||[''])[0], t:ti?ti.textContent.trim().slice(0,170):''};
  }catch(err){ window.__conf[a]={e:'erro'} } } window.__st[nome]='fim' };
```

Recuse e escolha outro quando: não está `venda`; `semi`; `alto` com só loja de terceiro; a voltagem (do título ou de `volt`) não bate com a do original; a cor, o tamanho (aro, litros, polegadas) ou o gênero não batem com o card; a marca é outra; o preço passa do dobro do original. O preço que a página indisponível ainda mostra pode estar velho ou ser de outro anúncio (o do Edifier G2000 dizia R$ 96): use como sinal, não como prova.

Armadilhas de 19/10/2026, todas pegas só na conferência da página:
- o título da busca não traz a voltagem; a ficha (`volt`) traz: o Panasonic NR-BB71GVFB era de 127V, e a escolha certa mudou;
- o anúncio com o mesmo código pode custar várias vezes mais e ser outro produto ou um importado (LG 26WQ500 a R$ 2.603);
- a marca no anúncio pode não ser a do card (a "Munique Big" do card era Conforsit; o anúncio, Qualiflex; o substituto, outra loja).

## Fase 4 — conflitos, ensaio e gravação

```bash
python3 .claude/skills/produtos-indisponiveis-trocar/gerar-tsv.py $W {site} $W/decisoes.py
bun scripts/disponibilidade-amazon.ts trocar {site} $W/{site}-aplicar.tsv            # ensaio
bash scripts/git-pull-seguro.sh "trocas de link {site}"
bun scripts/disponibilidade-amazon.ts trocar {site} $W/{site}-aplicar.tsv --gravar
python3 .claude/skills/produtos-indisponiveis-trocar/validar.py $W {site}
```

Todo CONFLITO do `gerar-tsv` se resolve antes de gravar (outro substituto ou "sem"). O `validar` tem de dizer `YAML quebrado 0` e `sobrou []`: em 19/10/2026 um motivo com aspas de polegada quebrou o frontmatter de 15 artigos antes do conserto do `trocar`.

## Fase 5 — registro, commit e publicação

1. Grave as leituras dos substitutos conferidos: o `__conf` salvo num `.json` serve direto para o `importar <arquivo> --data=AAAA-MM-DD` (ele usa `e`, `amz`, `semi`, `alto` e `t` e ignora o resto).
2. `python3 .claude/skills/produtos-indisponiveis-trocar/registro.py $W $W/decisoes.py {site}...`: grava `trocas-{site}-{data}.md` e `.tsv` em `docs/port-wordpress/disponibilidade/` e acrescenta os "sem" ao `sem-substituto.json`.
3. Commit só dos seus arquivos. No zsh, lista de arquivos numa variável não se divide em palavras: grave a lista num arquivo e use `git add --pathspec-from-file=`. O `.mdx` pede `git commit --no-verify`. Depois `git push origin main` e `bash scripts/painel-vps-pull.sh`.
4. Publique os sites do Marcelo pelo painel da VPS, um por vez: `GET /deploy-precheck/{site}`, `POST /build/{site}` e `POST /deploy/{site}` com `bun scripts/painel-api.ts`, esperando cada job (`GET /job/{id} --completo` até `running` falso). A resposta do POST traz o id em `id` ou em `job.id`; um 409 diz que já há um build do site rodando e traz o id dele. Bloqueio anterior à troca (por exemplo "Falta shortDescription" em card que veio do WordPress) não é da troca: `POST /deploy/{site}?force=1`, dizendo no relatório.
5. Confira no ar: `python3 .claude/skills/produtos-indisponiveis-trocar/conferir-no-ar.py {site} {dominio}` tem de dizer `com problema: []`.

## Relatório

Em linguagem simples, por site: quantos cards trocados (mesmo modelo, sucessor, parecido) e em quantos artigos; os que ficaram sem troca, com o motivo; os que esperam o ajuste do modelo (página própria); os substitutos acima do teto de preço de um artigo; os sites da Bárbara aplicados e esperando o sim para publicar; e os achados de passagem (link que já abria outro produto, artigo que precisa de reescrita porque quase todos os produtos saíram).
