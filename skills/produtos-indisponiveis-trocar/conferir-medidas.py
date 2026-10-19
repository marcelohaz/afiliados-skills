# Compara as medidas (litros, kg, ml, polegadas, BTUs, aro) do card e do produto original com as do substituto,
# para cada troca do dia. Saem os casos com medida diferente, para conferir à mão; diferença pequena de sucessor
# (310 → 320 L) é normal. Também acusa card cuja medida já não batia com o link antigo (link errado desde o
# WordPress): ali o substituto tem de seguir o card, não o link.
# uso (na raiz do repo, depois do `importar` das leituras dos substitutos): python3 conferir-medidas.py <site>... [--data=AAAA-MM-DD]
import json, re, sys, datetime
args = [a for a in sys.argv[1:] if not a.startswith('--')]
dia = next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--data=')), datetime.date.today().isoformat())
L = json.load(open('docs/port-wordpress/disponibilidade/leituras.json'))
regs = [r for r in (json.loads(l) for l in open('docs/port-wordpress/disponibilidade/trocas.jsonl')) if r.get('em') == dia and r.get('site') in args]
UN = {'litros': 'l', 'polegadas': '"', 'pol': '"', '″': '"'}
def medidas(s):
    s = re.sub(r'(\d)\.(\d{3})\b', r'\1\2', (s or '').lower()).replace(',', '.')  # 12.000 BTUs; 4,2 L
    out = {(float(n), UN.get(u, u)) for n, u in re.findall(r'(\d+(?:\.\d+)?)\s*(l\b|litros|kg|ml|"|″|pol|polegadas|btus)', s)}
    return out | {(float(n), 'aro') for n in re.findall(r'aro\s*(\d+)', s)}
tit = lambda a: ((L.get(a) or [{}])[-1].get('titulo') or '')
# troca corrigida no mesmo dia: vale o 1º "de" (o original) e o último "para"
cadeia = {}
for r in regs:
    k = (r['site'], r['artigo'], r.get('produto') or r['de'])
    if k in cadeia and cadeia[k]['para'] == r['de']: cadeia[k] = {**cadeia[k], 'para': r['para']}
    elif k not in cadeia: cadeia[k] = r
for r in cadeia.values():
    card, orig, novo = medidas(r.get('produto')), medidas(tit(r['de'])), medidas(tit(r['para']))
    uo, un = {u for _, u in orig}, {u for _, u in novo}
    errado = sorted(x for x in card if x[1] in uo and x not in orig)
    dif = sorted(x for x in card | orig if x[1] in un and x not in novo)
    if errado: print(f"LINK ANTIGO ERRADO {r['site']}/{r['artigo']}: card {r.get('produto')!r} × original {tit(r['de'])[:60]!r}")
    if dif: print(f"medida {r['site']}/{r['artigo']}: {r.get('produto')!r} → {tit(r['para'])[:70]!r} | card/original {dif} × substituto {sorted(novo)}")
