# Confere, depois do `trocar --gravar`, os .mdx alterados de cada site: frontmatter lido como YAML,
# nenhum card com o ASIN antigo e nenhum link /dp/ antigo no texto.
# uso: python3 validar.py <pasta-de-trabalho> <site>...
import sys, subprocess, yaml
pasta = sys.argv[1]
for site in sys.argv[2:]:
    tro = {l.split('\t')[0]: l.split('\t')[1] for l in open(f'{pasta}/{site}-aplicar.tsv').read().strip().split('\n')[1:]}
    fs = subprocess.run(['git', 'diff', '--name-only', '--', f'sites/{site}/src/content/reviews/'], capture_output=True, text=True).stdout.split()
    ruim, quebrado = [], 0
    for f in fs:
        t = open(f).read()
        try:
            fm = yaml.safe_load(t.split('---')[1]); assert isinstance(fm.get('products'), list)
        except Exception as e:
            quebrado += 1; print('  YAML QUEBRADO', f, e); continue
        ruim += [(f, 'card', p['asin']) for p in fm['products'] if p.get('asin') in tro]
        ruim += [(f, 'link', o) for o in tro if f'/dp/{o}' in t]
    print(f'{site}: {len(fs)} arquivos · YAML quebrado {quebrado} · sobrou {ruim[:5]}')
