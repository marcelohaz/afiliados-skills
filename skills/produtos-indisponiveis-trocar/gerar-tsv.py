# Transforma as decisões em .tsv para o `disponibilidade-amazon.ts trocar` e acusa os conflitos.
# uso: python3 gerar-tsv.py <pasta-de-trabalho> <site> <decisoes.py>
# decisoes.py define D = {asin_original: (asin_novo | None, 'mesmo-modelo'|'sucessor'|'parecido'|'sem'|'pagina', motivo)}
# Conflito: o substituto já está no artigo, ou dois cards diferentes do mesmo artigo vão para o mesmo substituto.
# Link de texto para o mesmo produto de um card (sem card próprio) segue o card e não conta como conflito.
import json, sys, runpy
pasta, site, arq = sys.argv[1], sys.argv[2], sys.argv[3]
D = runpy.run_path(arq)['D']
T = json.load(open(f'{pasta}/{site}-trocar.json')); A = json.load(open(f'{pasta}/{site}-artigos.json'))
linhas, falta, sem, pag, conf, uso = [], [], [], [], [], {}
for c in T:
    o = c['asin']
    if o not in D: falta.append(o); continue
    n, tipo, mot = D[o]
    if tipo == 'pagina' or c['pagina']: pag.append(o); continue
    if not n: sem.append(o); continue
    for art in c['artigos']:
        if n in A.get(art, {}).get('todos', []): conf.append(f'{o}→{n}: o substituto já está em {art}')
        if o in A.get(art, {}).get('cards', []): uso.setdefault((art, n), []).append(o)
    linhas.append('\t'.join([o, n, tipo, mot]))
for (art, n), os_ in uso.items():
    if len(os_) > 1: conf.append(f'{art}: os cards {os_} vão para o mesmo {n}')
open(f'{pasta}/{site}-aplicar.tsv', 'w').write('asin_original\tasin_novo\ttipo\tmotivo\n' + '\n'.join(linhas) + '\n')
print(f'{site}: {len(linhas)} trocas, {len(sem)} sem substituto, {len(pag)} com página própria' + (f', SEM DECISÃO: {falta}' if falta else ''))
for x in conf: print('  CONFLITO', x)
