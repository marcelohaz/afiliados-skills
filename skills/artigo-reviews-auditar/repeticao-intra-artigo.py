#!/usr/bin/env python3
"""Repetição de frase entre produtos do MESMO artigo (critério 1b da artigo-reviews-auditar).

Uso:
  python3 .claude/skills/artigo-reviews-auditar/repeticao-intra-artigo.py sites/{site}/src/content/reviews/{slug}.mdx [--min-words 6] [--json]

O que mede (só nos campos de produto: subtitle, shortDescription, pros, cons, fullReview):
  1. Sequências de N+ palavras iguais em 2+ produtos (default N=6), com contagem de produtos e de ocorrências.
     Fora do cálculo: os 4 rótulos do fullReview, nomes de produto (campo name), a keyword/keywordPlural do
     artigo, URLs. Sequências contidas numa maior repetida com a MESMA contagem são absorvidas (só a maior fica).
  2. Aberturas iguais: primeiras 4 palavras da shortDescription e do "Para quem é" em 3+ produtos.
     Número vira `#` antes de comparar (v1.128.0): "Monitor de 24 polegadas" e "Monitor de 23,8 polegadas"
     são o MESMO molde — 6 de 11 passaram como 3+2+1 enquanto o script comparava a string literal.
  3. Fecho de preço: shortDescriptions e Resumos que terminam com "preço … R$" (share sobre N produtos).
  4. Contador de verbos-curinga (resolve, dá conta, entrega, segura, pede, exige, aguenta, sustenta, encara,
     cobra, cobre, vira, brilha) — pra conferir que o CONSERTO não trocou repetição por frase estranha:
     rode antes e depois; o número não pode subir. (v1.128.0: `brilh\w*` virou `brilha[m]?` — contava o
     SUBSTANTIVO "brilho", spec central de monitor: 20 de 25 hits num artigo eram a palavra brilho.)
  5. Forma cross-produto (v1.128.0, canon Marcelo 2026-09-04): o que se repete um andar acima da frase e
     nenhum n-grama pega — TÍTULO de pró/contra igual em ≥4 produtos; Resumo ABRINDO com preço em mais
     da metade; claim "é o melhor {keyword}" no Para quem é em mais de 2 a cada 3. Medido: um agente
     escrevendo 11 reviews em sequência convergiu na própria forma (9/11 Resumos abrindo com preço; a
     rede tem mediana 0) e passou limpo em todos os checks lexicais.

Limiar canônico (canon Marcelo 2026-08-15): repetição ≤3 ocorrências = INFO (deixa); ≥4 = FIX (exceto spec pura — número/unidade/tecnologia — que é fato repetido e fica INFO) (reduzir a 3,
apagando a cópia quando o fato já está em pró/tabela/outra frase, ou reescrevendo SÓ por movimento literal:
número vira sujeito / fundir na vizinha / mover pra pró-contra). Abertura igual em ≥4 produtos = FIX (varia
as excedentes). Fecho de preço em >50% dos produtos = FIX (deixa em ≤ metade). 2-3 produtos = INFO.
"""
import re, sys, json, collections, yaml

ROTULOS = ['para quem é', 'por que gostamos', 'pontos de atenção', 'resumo']
# spec pura (número + unidade, nome de tecnologia): fato repetido, não frase-molde → INFO mesmo acima de 4
SPEC = re.compile(r"\d|\b(wi fi|bluetooth|hepa|usb|hdmi|ghz|mah|rpm|dpi|ppm|dual band)\b", re.I)
CURINGA = re.compile(r"\b(resolv\w*|d[áa]o? conta|entreg(?:a|am)|segur(?:a|am)|pede[m]?|exig(?:e|em)|aguent\w*|sustent\w*|encar\w*|cobra[m]?|cobre[m]?|vira[m]?|brilha[m]?)\b", re.I)

def strip(h): return re.sub(r'<[^>]+>', ' ', h or '')
def words(t): return re.findall(r"[a-zà-ú0-9º°]+(?:[,.]\d+)?", t.lower())
def molde(ws): return ' '.join('#' if re.search(r'\d', w) else w for w in ws)  # número vira # (molde, não string)

def load(path):
    raw = open(path).read()
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', raw, re.S)
    fm = yaml.safe_load(m.group(1))
    return fm

def product_text(p):
    parts = [p.get('subtitle') or '', p.get('shortDescription') or '']
    parts += [strip(x) for x in (p.get('pros') or [])] + [strip(x) for x in (p.get('cons') or [])]
    parts.append(strip(p.get('fullReview') or ''))
    t = ' . '.join(parts)
    t = re.sub(r'https?://\S+', ' ', t)
    return t

def main():
    args = sys.argv[1:]
    n = 6
    if '--min-words' in args:
        n = int(args[args.index('--min-words') + 1])
    as_json = '--json' in args
    path = [a for a in args if a.endswith('.mdx')][0]
    fm = load(path)
    prods = fm.get('products') or []
    kw = [(fm.get('keyword') or '').lower(), (fm.get('keywordPlural') or '').lower()]
    names = [(p.get('name') or '').lower() for p in prods]
    stop = set()
    for s in ROTULOS + kw + names:
        for w in words(s): stop.add(w)  # palavras de rótulo/keyword/nome não iniciam nem terminam n-grama

    # 1) n-gramas repetidos entre produtos
    # n-gramas por FRASE (não atravessam ". ", ":", ";", "!" ou "?") — evita falso positivo de fronteira
    gram_prod = collections.defaultdict(set); gram_occ = collections.Counter()
    per_prod = []
    for p in prods:
        low = product_text(p).lower()
        for s_ in ROTULOS + [k for k in kw if k] + [x for x in names if x]:
            low = low.replace(s_, ' ')
        sents = re.split(r'(?<=[.!?:;])\s+|\s\.\s', low)
        per_prod.append([words(x) for x in sents])
    for i, sents in enumerate(per_prod):
        for w in sents:
            for j in range(len(w) - n + 1):
                g = tuple(w[j:j+n])
                gram_prod[g].add(i); gram_occ[g] += 1
    rep = {g: (len(ps), gram_occ[g]) for g, ps in gram_prod.items() if len(ps) >= 2}
    # funde n-gramas deslocados (g[1:] == h[:-1]) com a MESMA contagem numa frase máxima
    merged = []
    used = set()
    by_start = collections.defaultdict(list)
    for g in rep: by_start[g[:-1]].append(g)
    for g in sorted(rep, key=lambda x: (-rep[x][0], -rep[x][1], x)):
        if g in used: continue
        chain = list(g); cur = g; used.add(g)
        while True:
            nxts = [h for h in by_start.get(cur[1:], []) if h not in used and rep[h] == rep[g]]
            if not nxts: break
            h = nxts[0]; used.add(h); chain.append(h[-1]); cur = h
        merged.append((' '.join(chain), rep[g][0], rep[g][1]))
    # remove frases contidas em outra maior com a mesma contagem
    merged.sort(key=lambda x: -len(x[0]))
    final = []
    for s_, np_, no in merged:
        if any(s_ in m_s and (mp, mo) == (np_, no) for m_s, mp, mo in final): continue
        final.append((s_, np_, no))
    merged = sorted(final, key=lambda x: (-x[2], -x[1]))
    # 2) aberturas
    open_sd = collections.Counter(); open_pq = collections.Counter()
    for p in prods:
        sd = words(p.get('shortDescription') or '')
        if len(sd) >= 4: open_sd[molde(sd[:4])] += 1
        fr = strip(p.get('fullReview') or '')
        m = re.search(r'Para quem é:\s*(.*?)(?:\.|$)', fr)
        if m:
            w = words(m.group(1))
            if len(w) >= 4: open_pq[molde(w[:4])] += 1
    # 3) fecho de preço
    price_sd = sum(1 for p in prods if re.search(r'pre[çc]o[^.]{0,30}R\$[^.]*\.?\s*$', (p.get('shortDescription') or '').strip(), re.I))
    price_res = 0
    for p in prods:
        fr = strip(p.get('fullReview') or '')
        m = re.search(r'Resumo:\s*(.*)$', fr, re.S)
        if m:
            last = re.split(r'(?<=[.!?])\s+', m.group(1).strip())[-1]
            if re.search(r'pre[çc]o[^.]{0,30}R\$', last, re.I): price_res += 1
    # 4) curinga
    curinga = sum(len(CURINGA.findall(product_text(p))) for p in prods)
    # 5) forma cross-produto (v1.128.0): título de pró/contra, abertura do Resumo, claim de keyword
    tit_prod = collections.defaultdict(set)
    for i, p in enumerate(prods):
        for x in (p.get('pros') or []) + (p.get('cons') or []):
            m = re.match(r'\s*<strong>(.*?)</strong>', str(x))
            if m: tit_prod[re.sub(r'\s+', ' ', m.group(1).strip().lower())].add(i)
    titulos = sorted(((k, len(v)) for k, v in tit_prod.items() if len(v) >= 3), key=lambda kv: -kv[1])
    res_preco = 0; claim = 0
    kwcore = re.sub(r'^(melhor(es)?|o melhor|a melhor)\s+', '', kw[0]).split()  # melhor(es)?, não melhores? (que nunca casa 'melhor')
    claim_rx = re.compile(r'é [oa] melhor ' + re.escape(' '.join(kwcore[:2])), re.I) if kwcore else None
    for p in prods:
        fr = strip(p.get('fullReview') or '')
        m = re.search(r'Resumo:\s*(.*)$', fr, re.S)
        if m:
            first = re.split(r'(?<=[.!?])\s+', m.group(1).strip())[0]
            if re.match(r'.{0,25}(pre[çc]o|cerca de|em torno de|por volta de|R\$)', first, re.I): res_preco += 1
        m = re.search(r'Para quem é:\s*(.*?)(?=Por que gostamos:|$)', fr, re.S)
        if m and claim_rx and claim_rx.search(m.group(1)): claim += 1

    N = len(prods)
    out = {
        'produtos': N,
        'min_words': n,
        'repeticoes': [{'frase': s, 'produtos': np_, 'ocorrencias': no, 'nivel': ('INFO' if (no < 4 or SPEC.search(s)) else 'FIX'), 'spec': bool(SPEC.search(s))} for s, np_, no in merged],
        'aberturas_shortDescription': [{'abertura': k, 'produtos': v, 'nivel': 'FIX' if v >= 4 else 'INFO'} for k, v in open_sd.items() if v >= 3],
        'aberturas_para_quem_e': [{'abertura': k, 'produtos': v, 'nivel': 'FIX' if v >= 4 else 'INFO'} for k, v in open_pq.items() if v >= 3],
        'fecho_preco': {'shortDescription': price_sd, 'resumo': price_res, 'nivel': 'FIX' if (price_sd > N/2 or price_res > N/2) else 'INFO'},
        'verbos_curinga_total': curinga,
        'forma': {
            'titulos_repetidos': [{'titulo': k, 'produtos': v, 'nivel': 'FIX' if v >= 4 else 'INFO'} for k, v in titulos],
            'resumo_abre_com_preco': res_preco, 'resumo_nivel': 'FIX' if res_preco > N/2 else 'INFO',
            'claim_keyword': claim, 'claim_nivel': 'FIX' if claim > 2*N/3 else 'INFO',
        },
    }
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=1)); return
    print(f"# Repetição intra-artigo — {path}\n{N} produtos · n-grama={n} · verbos-curinga={curinga}\n")
    fix = [r for r in out['repeticoes'] if r['nivel'] == 'FIX']; info = [r for r in out['repeticoes'] if r['nivel'] == 'INFO']
    print(f"## FIX (≥4 ocorrências): {len(fix)}")
    for r in fix: print(f"  {r['ocorrencias']}× em {r['produtos']} produtos: “{r['frase']}”")
    spec_info = [r for r in info if r.get('spec')]
    if spec_info: print(f"  (+{len(spec_info)} sequências com número/spec ficaram INFO mesmo ≥4: fato repetido não é frase-molde)")
    print(f"\n## INFO (2-3 ocorrências, deixa): {len(info)}")
    for r in info[:25]: print(f"  {r['ocorrencias']}× em {r['produtos']} produtos: “{r['frase']}”")
    if len(info) > 25: print(f"  … +{len(info)-25}")
    print("\n## Aberturas iguais")
    for r in out['aberturas_shortDescription']: print(f"  shortDescription “{r['abertura']}…” em {r['produtos']} produtos [{r['nivel']}]")
    for r in out['aberturas_para_quem_e']: print(f"  Para quem é “{r['abertura']}…” em {r['produtos']} produtos [{r['nivel']}]")
    fp = out['fecho_preco']
    print(f"\n## Fecho de preço: shortDescription {fp['shortDescription']}/{N} · Resumo {fp['resumo']}/{N} [{fp['nivel']}]")
    fo = out['forma']
    print(f"\n## Forma cross-produto (v1.128.0)")
    for r in fo['titulos_repetidos']: print(f"  título de pró/contra “{r['titulo']}” em {r['produtos']} produtos [{r['nivel']}]")
    if not fo['titulos_repetidos']: print("  nenhum título de pró/contra em 3+ produtos")
    print(f"  Resumo ABRE com preço: {fo['resumo_abre_com_preco']}/{N} [{fo['resumo_nivel']}] (teto: metade)")
    print(f"  claim “é o melhor {{keyword}}” no Para quem é: {fo['claim_keyword']}/{N} [{fo['claim_nivel']}] (teto: 2 a cada 3)")

if __name__ == '__main__':
    main()
