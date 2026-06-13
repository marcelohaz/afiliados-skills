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

PROSA vs SPEC: a colisão que importa é de PROSA (subtitle/shortDescription/fullReview/
pros/cons). Valores de `specs[].value` são dado bruto de ficha e repetem entre sites
por serem fato (rendimento/dpi/ppm) — NÃO contam como duplicata acionável (variá-los
à toa é contorção). Por isso `duplicata_acionavel` se baseia SÓ em prosa; colisões de
spec são reportadas à parte (`specs_identicas`) como informação.

Saída: JSON. Exit 1 se houver duplicata de PROSA acionável (prosa_exatas > 0 OU
prosa_near_0.8 > 0), pra a auditoria decidir flaggar 🟡.
"""
import sys, re, json, glob, os

try:
    import yaml
except ImportError:
    print("ERRO: pyyaml não instalado", file=sys.stderr); sys.exit(2)


def parse(path):
    """Lê frontmatter + body de uma página de produto .mdx.

    Robusto a arquivos SEM o '---' de fechamento (frontmatter-only, ou malformado
    com fullReview '>-'/'|' que corre até o EOF): nesse caso, tudo após o '---'
    inicial é tratado como frontmatter e o body fica vazio. NÃO depende de haver
    conteúdo após o 2º '---'. Loga warning explícito quando não consegue ler o
    asin, em vez de pular calado (falha silenciosa escondia duplicata cross-site
    em batches — caso guiaesportivo/black-skull-creatine-turbo, 2026-06-14).
    """
    raw = open(path, encoding="utf-8").read()
    m = re.search(r'^---\n(.*?)\n---\n?(.*)$', raw, re.S)
    if m:
        fm_text, body = m.group(1), m.group(2)
    else:
        m2 = re.match(r'^---\r?\n(.*)$', raw, re.S)   # '---' inicial sem fechamento
        if not m2:
            print(f"[compare-cross-site] WARN: {path} sem frontmatter (sem '---' inicial) — pulado", file=sys.stderr)
            return {}, ""
        fm_text, body = m2.group(1), ""
    try:
        fm = yaml.safe_load(fm_text) or {}
    except Exception as e:
        print(f"[compare-cross-site] WARN: {path} frontmatter YAML inválido ({e}) — pulado", file=sys.stderr)
        return {}, ""
    if not isinstance(fm, dict):
        print(f"[compare-cross-site] WARN: {path} frontmatter não é um mapa — pulado", file=sys.stderr)
        return {}, ""
    if not str(fm.get("asin") or "").strip():
        print(f"[compare-cross-site] WARN: {path} sem 'asin' no frontmatter — checagem de duplicata cross-site pode passar batido", file=sys.stderr)
    return fm, body


def clean(s):
    s = re.sub(r'<[^>]+>', ' ', str(s or ''))   # tags -> espaço (preserva fronteira)
    return re.sub(r'\s+', ' ', s).strip()


def prose_parts(fm):
    """Texto editorial AUTORAL (o que conta pra duplicata acionável)."""
    parts = [clean(fm.get("subtitle", "")), clean(fm.get("shortDescription", "")), clean(fm.get("fullReview", ""))]
    parts += [clean(x) for x in (fm.get("pros") or [])]
    parts += [clean(x) for x in (fm.get("cons") or [])]
    return [p for p in parts if p]


def spec_parts(fm):
    """Valores de specs[].value — dado bruto de ficha (colisão = info, não acionável)."""
    return [clean(s.get("value")) for s in (fm.get("specs") or []) if isinstance(s, dict) and clean(s.get("value"))]


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


def collisions(parts_t, parts_s):
    """Frases idênticas (>=6 palavras) e near-dup (jaccard>=0.6) entre dois conjuntos."""
    st, ss = sentences(parts_t), sentences(parts_s)
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
    return exatas, near


def compare(target_fm, peer_fm):
    pt_prose, ps_prose = prose_parts(target_fm), prose_parts(peer_fm)
    pt_spec, ps_spec = spec_parts(target_fm), spec_parts(peer_fm)

    prose_exatas, prose_near = collisions(pt_prose, ps_prose)
    spec_exatas, spec_near = collisions(pt_spec, ps_spec)

    # overlap n-grama só da PROSA (specs inflam artificialmente o overlap)
    ov = {}
    for n in (5, 8):
        A, B = shingles(pt_prose, n), shingles(ps_prose, n)
        ov[n] = round(len(A & B) / max(1, len(A | B)) * 100, 1)

    prose_near_08 = sum(1 for s, _, _ in prose_near if s >= 0.8)
    return {
        # PROSA — o que conta pra acionável
        "prosa_exatas": len(prose_exatas),
        "prosa_near_0.8": prose_near_08,
        "prosa_near_0.6": len(prose_near),
        "overlap_prosa_5gram_pct": ov[5],
        "overlap_prosa_8gram_pct": ov[8],
        "prosa_exatas_lista": prose_exatas[:30],
        "prosa_near_lista": [{"jaccard": s, "a": a[:160], "b": b[:160]} for s, a, b in prose_near[:30]],
        # SPECS — info, não acionável
        "specs_identicas": len(spec_exatas) + sum(1 for s, _, _ in spec_near if s >= 0.8),
        "specs_identicas_lista": (spec_exatas + [a for s, a, _ in spec_near if s >= 0.8])[:20],
        # acionável = SÓ prosa
        "acionavel": len(prose_exatas) > 0 or prose_near_08 > 0,
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
        if rep["acionavel"]:
            actionable = True

    out = {
        "target": target_path,
        "asin": str(target_fm.get("asin") or ""),
        "peers_encontrados": len(peers),
        "duplicata_acionavel": actionable,   # SÓ por colisão de PROSA
        "comparacoes": results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if actionable else 0)


if __name__ == "__main__":
    main()
