#!/usr/bin/env python3
"""
Comparador de duplicata cross-site entre dois artigos .mdx (destino vs fonte).
Uso: python3 compare-cross-site.py <target.mdx> <source.mdx>
Saída: relatório de frases idênticas, near-dup (jaccard), overlap n-grama e specs.
Companheiro da skill artigo-clonar-em-massa (Etapa 5 — QA de duplicata).
"""
import sys, re, json

try:
    import yaml
except ImportError:
    print("ERRO: pyyaml não instalado", file=sys.stderr); sys.exit(2)


def parse(path):
    raw = open(path, encoding="utf-8").read()
    m = re.search(r'^---\n(.*?)\n---\n?(.*)$', raw, re.S)
    if not m:
        return {}, ""
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    return fm, body


def clean(s):
    s = re.sub(r'<[^>]+>', ' ', str(s or ''))   # tags -> espaço (preserva fronteira)
    return re.sub(r'\s+', ' ', s).strip()


def article_text_parts(fm, body):
    """Retorna lista de blocos de texto do artigo (reviews + guide + intro)."""
    parts = []
    for p in (fm.get("products") or []):
        parts.append(clean(p.get("subtitle", "")))
        parts.append(clean(p.get("shortDescription", "")))
        parts.append(clean(p.get("fullReview", "")))
        parts += [clean(x) for x in (p.get("pros") or [])]
        parts += [clean(x) for x in (p.get("cons") or [])]
    parts.append(clean(fm.get("guideContent", "")))
    parts.append(clean(body))
    return [p for p in parts if p]


def sentences(parts):
    out = []
    for txt in parts:
        for s in re.split(r'(?<=[.!?:])\s+', txt):
            s = s.strip()
            if len(s.split()) >= 6:
                out.append(s)
    return out


def wset(s):
    return set(re.findall(r'\w+', s.lower()))


def jac(a, b):
    A, B = wset(a), wset(b)
    return len(A & B) / max(1, len(A | B))


def shingles(parts, n):
    w = re.findall(r'\w+', ' '.join(parts).lower())
    return set(tuple(w[i:i+n]) for i in range(len(w) - n + 1))


def specs_map(fm):
    """asin -> {label: value} agregado dos produtos."""
    out = {}
    for p in (fm.get("products") or []):
        asin = p.get("asin")
        out[asin] = {s.get("label"): s.get("value") for s in (p.get("specs") or [])}
    return out


def main():
    if len(sys.argv) != 3:
        print("uso: compare-cross-site.py <target.mdx> <source.mdx>", file=sys.stderr); sys.exit(2)
    ft, bt = parse(sys.argv[1])
    fs, bs = parse(sys.argv[2])
    pt, ps = article_text_parts(ft, bt), article_text_parts(fs, bs)
    st, ss = sentences(pt), sentences(ps)
    sset_t, sset_s = set(st), set(ss)

    exatas = sorted(sset_t & sset_s)
    near = []
    for a in st:
        if a in sset_s:
            continue
        best = max(((jac(a, b), b) for b in ss), default=(0, ""))
        if best[0] >= 0.6:
            near.append((round(best[0], 2), a, best[1]))
    near.sort(reverse=True)

    ov = {}
    for n in (5, 8):
        A, B = shingles(pt, n), shingles(ps, n)
        ov[n] = round(len(A & B) / max(1, len(A | B)) * 100, 1)

    spt, sps = specs_map(ft), specs_map(fs)
    spec_diffs = []
    for asin in spt:
        if asin in sps:
            for k, v in spt[asin].items():
                if k in sps[asin] and str(v).strip() == str(sps[asin][k]).strip():
                    spec_diffs.append((asin, k, v))

    report = {
        "frases_exatas": len(exatas),
        "near_dup_0.8": sum(1 for s, _, _ in near if s >= 0.8),
        "near_dup_0.6": len(near),
        "overlap_5gram_pct": ov[5],
        "overlap_8gram_pct": ov[8],
        "specs_identicas": len(spec_diffs),
        "exatas_lista": exatas[:40],
        "near_lista": [{"jaccard": s, "target": a[:160], "source": b[:160]} for s, a, b in near[:40]],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # exit 1 se houver duplicata acionável (exatas > 0 ou near>=0.8) — pra a skill decidir loop
    sys.exit(1 if (report["frases_exatas"] > 0 or report["near_dup_0.8"] > 0) else 0)


if __name__ == "__main__":
    main()
