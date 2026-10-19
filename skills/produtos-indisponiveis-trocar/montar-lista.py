# Monta a lista de produtos a trocar de um site, a partir do relatório de disponibilidade.
# uso (na raiz do repo): python3 .claude/skills/produtos-indisponiveis-trocar/montar-lista.py <pasta-de-trabalho> <site>
# grava <pasta>/<site>-trocar.json (um item por produto) e <pasta>/<site>-artigos.json (cards e links de cada artigo)
# e imprime as buscas da Amazon em JSON ([asin, "tipo + nome do card"]), para o laço de busca da skill.
import json, sys, glob, re, subprocess, yaml
pasta, site = sys.argv[1], sys.argv[2]
r = json.loads(subprocess.run(['bun', 'scripts/disponibilidade-amazon.ts', 'relatorio', site, '--json'], capture_output=True, text=True).stdout)
alvo = [x for x in r if x['acao'].startswith('trocar')]
cards, desc, artigos = {}, {}, {}
for f in glob.glob(f'sites/{site}/src/content/reviews/*.mdx'):
    t = open(f, encoding='utf-8').read(); fm = yaml.safe_load(t.split('---')[1]) or {}; slug = f.split('/')[-1][:-4]
    cs = [p.get('asin') for p in fm.get('products') or [] if p.get('asin')]
    artigos[slug] = {'cards': cs, 'todos': sorted(set(re.findall(r'(?:/dp/|asin:\s*"?)([A-Z0-9]{10})', t)))}
    for p in fm.get('products') or []:
        a = p.get('asin')
        if a and a not in cards:
            cards[a] = p.get('name'); desc[a] = re.sub(r'\s+', ' ', str(p.get('shortDescription') or ''))[:170]
L = [{'asin': x['asin'], 'acao': x['acao'], 'titulo': x['titulo'], 'card': cards.get(x['asin']), 'artigos': x['artigos'],
      'pagina': x['pagina'], 'desc': desc.get(x['asin'], '')} for x in alvo]
json.dump(L, open(f'{pasta}/{site}-trocar.json', 'w'), ensure_ascii=False, indent=1)
json.dump(artigos, open(f'{pasta}/{site}-artigos.json', 'w'))
def busca(l):
    # o tipo vem do título da Amazon (as duas primeiras palavras): o nome do card sozinho já levou a busca
    # de um depurador para fornos e a de uma panela de pressão para assadeiras (19/10/2026)
    tipo = ' '.join(re.sub(r'[,(].*', '', l['titulo'] or '').split()[:2])
    return f"{tipo} {l['card'] or ''}".strip()[:70]
print(json.dumps([[l['asin'], busca(l)] for l in L], ensure_ascii=False))
