# Confere no ar, artigo por artigo, que cada troca do dia saiu: o link novo está na página e o antigo não.
# uso (na raiz do repo): python3 conferir-no-ar.py <site> <dominio> [AAAA-MM-DD]   (sem data: hoje)
import json, urllib.request, collections, re, sys, datetime
site, dom = sys.argv[1], sys.argv[2]; dia = sys.argv[3] if len(sys.argv) > 3 else datetime.date.today().isoformat()
regs = [r for r in (json.loads(l) for l in open('docs/port-wordpress/disponibilidade/trocas.jsonl')) if r.get('em') == dia and r.get('site') == site]
# troca corrigida no mesmo dia: vale o 1º "de" (o original) e o último "para"
cadeia = {}
for r in regs:
    k = (r['artigo'], r.get('produto') or r['de'])
    if k in cadeia and cadeia[k][1] == r['de']: cadeia[k] = (cadeia[k][0], r['para'])
    elif k not in cadeia: cadeia[k] = (r['de'], r['para'])
por = collections.defaultdict(list)
for (art, _), par in cadeia.items(): por[art].append(par)
m = re.search(r"^\s*homeReviewSlug:\s*'([^']+)'", open(f'sites/{site}/src/config.ts').read(), re.M); home = m.group(1) if m else None
ok, ruim = 0, []
for art, pares in sorted(por.items()):
    url = f'https://{dom}/' if art == home else f'https://{dom}/{art}/'
    try: h = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=25).read().decode('utf-8', 'ignore')
    except Exception as e: ruim.append((art, str(e)[:50])); continue
    for de, para in pares:
        if para in h and f'/dp/{de}' not in h: ok += 1
        else: ruim.append((art, de, para))
print(site, '· artigos:', len(por), '· trocas certas no ar:', ok, '· com problema:', ruim)
