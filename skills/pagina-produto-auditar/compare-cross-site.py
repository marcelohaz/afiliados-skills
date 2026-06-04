#!/usr/bin/env python3
"""
Comparador de duplicata cross-site entre PÁGINAS INDIVIDUAIS de produto (.mdx flat).

Diferente do compare-cross-site.py da artigo-clonar-em-massa (que lê products[] +
guideContent de um ARTIGO), este lê o frontmatter FLAT de uma página de produto
(subtitle / shortDescription / fullReview / pros / cons / specs no topo).

Usos:
  python3 compare-cross-site.py <target.mdx>            # auto-descobre irmãos pelo ASIN
  python3 compare-cross-site.py <target.mdx> <peer.mdx> # par explícito

Auto-descoberta: lê o asin do target e varre sites/*/src/content/products/*.mdx
por outras páginas (sites diferentes) com o MESMO asin. Roda a partir da raiz do repo.

Saída: JSON com frases idênticas (>=6 palavras), near-dup (jaccard), overlap n-grama
por par comparado. Exit 1 se houver duplicata acionável (exatas > 0 OU near>=0.8),
pra a auditoria decidir flaggar.
"""
import sys, re, json, glob, os

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
    return fm, m.group(2)


def clean(s):
    s = re.sub(r'<[^>]+>', ' ', str(s or ''))   # tags -> espaço (preserva fronteira)
    return re.sub(r'\s+', ' ', s).strip()


def product_text_parts(fm):
    """Blocos de texto editorial de uma página de produto (frontmatter flat)."""
    parts = [
        clean(fm.get("subtitle", "")),
        clean(fm.get("shortDescription", "")),
        clean(fm.get("fullReview", "")),
    ]
    parts += [clean(x) for x in (fm.get("pros") or [])]
    parts += [clean(x) for x in (fm.get("cons") or [])]
    parts += [clean(s.get("value")) for s in (fm.get("specs") or []) if isinstance(s, dict)]
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


def compare(target_fm, peer_fm):
    pt, ps = product_text_parts(target_fm), product_text_parts(peer_fm)
    st, ss = sentences(pt), sentences(ps)
    sset_s = set(ss)
    exatas = sorted(set(st) & sset_s)
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
    return {
        "frases_exatas": len(exatas),
        "near_dup_0.8": sum(1 for s, _, _ in near if s >= 0.8),
        "near_dup_0.6": len(near),
        "overlap_5gram_pct": ov[5],
        "overlap_8gram_pct": ov[8],
        "exatas_lista": exatas[:30],
        "near_lista": [{"jaccard": s, "a": a[:160], "b": b[:160]} for s, a, b in near[:30]],
    }


def discover_peers(target_path, target_fm):
    asin = str(target_fm.get("asin") or "").strip()
    if not asin:
        return []
    tgt_abs = os.path.abspath(target_path)
    peers = []
    for p in glob.glob("sites/*/src/content/products/*.mdx"):
        if os.path.abspath(p) == tgt_abs:
            continue
        try:
            fm, _ = parse(p)
        except Exception:
            continue
        if str(fm.get("asin") or "").strip() == asin:
            peers.append((p, fm))
    return peers


def main():
    args = sys.argv[1:]
    if len(args) not in (1, 2):
        print("uso: compare-cross-site.py <target.mdx> [<peer.mdx>]", file=sys.stderr); sys.exit(2)
    target_path = args[0]
    target_fm, _ = parse(target_path)

    if len(args) == 2:
        peers = [(args[1], parse(args[1])[0])]
    else:
        peers = discover_peers(target_path, target_fm)

    results = []
    actionable = False
    for peer_path, peer_fm in peers:
        rep = compare(target_fm, peer_fm)
        rep["peer"] = peer_path
        results.append(rep)
        if rep["frases_exatas"] > 0 or rep["near_dup_0.8"] > 0:
            actionable = True

    out = {
        "target": target_path,
        "asin": str(target_fm.get("asin") or ""),
        "peers_encontrados": len(peers),
        "duplicata_acionavel": actionable,
        "comparacoes": results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if actionable else 0)


if __name__ == "__main__":
    main()
