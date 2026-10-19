# Grava o registro das trocas de cada site (docs/port-wordpress/disponibilidade/trocas-<site>-<data>.md e .tsv)
# e acrescenta os produtos sem substituto ao sem-substituto.json, com o motivo.
# uso (na raiz do repo): python3 registro.py <pasta-de-trabalho> <decisoes.py> <site>...
import json, sys, runpy, datetime
pasta, arq, sites = sys.argv[1], sys.argv[2], sys.argv[3:]
R = 'docs/port-wordpress/disponibilidade'; HOJE = datetime.date.today().isoformat()
D = runpy.run_path(arq)['D']; SEM = json.load(open(f'{R}/sem-substituto.json'))
NOME = {'mesmo-modelo': 'Mesmo modelo em outro anúncio', 'sucessor': 'Sucessor da mesma linha', 'parecido': 'Parecido, da mesma marca e do mesmo tipo'}
for site in sites:
    T = json.load(open(f'{pasta}/{site}-trocar.json')); tsv = open(f'{pasta}/{site}-aplicar.tsv').read()
    feitos = {l.split('\t')[0] for l in tsv.strip().split('\n')[1:]}
    grupos = {k: [] for k in NOME}; sem, pag = [], []
    for c in T:
        o = c['asin']; n, tipo, mot = D[o]; card = c['card'] or (c['titulo'] or o)[:50]; linha = f"| {card} | {mot} | {', '.join(c['artigos'])} |"
        if o in feitos: grupos[tipo].append(linha)
        elif tipo == 'pagina' or c['pagina']: pag.append(linha)
        else: sem.append(linha); SEM[o] = {'motivo': f'{site}: {mot}', 'em': HOJE}
    d = datetime.date.fromisoformat(HOJE).strftime('%d/%m/%Y')
    L = [f'# Trocas de link no {site} ({d})', '', f'Só o link muda; texto, nome e foto do card ficam. Conferido na Amazon em {d}: todo substituto está à venda, não é seminovo, tem a voltagem e o gênero que o card descreve, e o tamanho mais próximo à venda (quando é outro, o motivo diz).', '']
    for k, v in grupos.items():
        if v: L += [f'## {NOME[k]} ({len(v)})', '', '| Produto no artigo | Vai para | Artigos |', '|---|---|---|'] + sorted(v) + ['']
    if sem: L += [f'## Ficam sem troca ({len(sem)})', '', 'Não há produto da mesma marca e do mesmo tipo à venda que sirva. O card continua com o link antigo.', '', '| Produto no artigo | Por quê | Artigos |', '|---|---|---|'] + sorted(sem) + ['']
    if pag: L += [f'## Esperam o ajuste do modelo ({len(pag)})', '', 'Têm página própria no site; trocar só o ASIN tiraria o link do artigo para a página.', '', '| Produto no artigo | Substituto quando der | Artigos |', '|---|---|---|'] + sorted(pag) + ['']
    open(f'{R}/trocas-{site}-{HOJE}.md', 'w').write('\n'.join(L)); open(f'{R}/trocas-{site}-{HOJE}.tsv', 'w').write(tsv)
    print(site, {k: len(v) for k, v in grupos.items()}, 'sem', len(sem), 'página própria', len(pag))
json.dump(SEM, open(f'{R}/sem-substituto.json', 'w'), ensure_ascii=False, indent=1)
