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

⚠ FICHA DENTRO DE PROSA (corrigido 2026-08-06): a separação acima era derrotada por
ONDE o redator põe a enumeração. A mesma frase — "woofer de 80 x 45 mm, tweeter de
cúpula de 16 mm da Peerless e dois radiadores passivos" — era classificada como spec
(não acionável) quando morava em `specs[].value` e como prosa AUTORAL (acionável)
quando morava num bullet de `pros`.

⚠ **Dimensione a expectativa: isto é conserto de classificação, não faxina de ruído.**
No lote de áudio de 06/08 o sintoma parecia epidêmico (o `acionavel` acendia em quase
todo par e o top hit era sempre enumeração de driver), mas medido na rede o efeito é
mínimo: **425 pares em 70 páginas, 42% acionável antes e 42% depois — 1 par silenciado**.
Nos outros 41% o `acionavel` aponta prosa autoral de verdade e deve mesmo acender.
Nichos que recitam ficha em bullet (áudio, suplemento) concentram o caso; o resto da
rede quase não é afetado. Não conte com esta mudança pra baixar volume de warn.

Agora frases com >=3 medidas (número + unidade) entram no balde `prosa_ficha_*` e
NÃO acionam. Elas continuam no JSON, com lista própria: o objetivo é tirá-las do
gate, não escondê-las. Duas pessoas destilando a mesma ficha convergem na mesma
enumeração porque ela é fato, exatamente como acontece em `specs[].value`.

Saída: JSON. Exit 1 se houver duplicata de PROSA AUTORAL acionável
(prosa_exatas > 0 OU prosa_near_0.8 > 0), pra a auditoria decidir flaggar 🟡.

⚠ ILEGÍVEL NÃO É LIMPO (corrigido 2026-09-01): frontmatter que o YAML não parseia
(target ou irmão) antes virava só um WARN no stderr e o JSON saía "0 peers /
acionavel: false" — a auditoria, que só lê o JSON, tratava como limpo. Agora:
  - target ilegível → `target_ilegivel: true` + `erro`, exit 2 (a skill flaga
    🔴 `html-invalido`/yaml, não "sem duplicata");
  - irmão ilegível → ainda entra em `comparacoes` (asin lido por regex no texto
    cru) com `peer_ilegivel: true`, e `peers_ilegiveis` conta no topo.
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
        # não some: devolve o asin por regex pra a página seguir contando como irmã/target
        asin_m = re.search(r'^asin:\s*["\']?([A-Z0-9]{10})', fm_text, re.M)
        print(f"[compare-cross-site] WARN: {path} frontmatter YAML inválido ({str(e).splitlines()[0]}) — marcado ilegível", file=sys.stderr)
        return {"asin": asin_m.group(1) if asin_m else "", "_ilegivel": True, "_erro": str(e).splitlines()[0][:160]}, ""
    if not isinstance(fm, dict):
        print(f"[compare-cross-site] WARN: {path} frontmatter não é um mapa — marcado ilegível", file=sys.stderr)
        return {"_ilegivel": True, "_erro": "frontmatter não é um mapa"}, ""
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


# número + unidade: "80 x 45 mm", "16 mm", "20 W", "4.500 mAh", "1,37 kg", "12 h", "50%", '6,5"'
# ⚠ `%` e `"` ficam FORA do grupo com `\b`: são não-palavra, então um `\b` depois deles
# falha sempre que vier vírgula/ponto/fim ("50%," não casava). Bug pego no teste de
# calibração — mantenha os dois blocos separados.
MEDIDA_RE = re.compile(
    r'\d+(?:[.,]\d+)?\s*'
    r'(?:(?:mm|cm|m|km|kg|g|mah|wh|w|khz|hz|db|ms|min|h|horas?|pol(?:egadas?)?|v|gb|tb|mb|dpi|ppm|rpm)\b'
    r'|[%"])',
    re.I,
)


def is_ficha(s):
    """Enumeração de ficha técnica: >=3 medidas na mesma frase.

    Corta a recitação de spec que mora em bullet de pros/cons sem cortar prosa
    autoral. Calibrado no lote 06/08 do lg-xboom-grab:
      ficha    "woofer de 80 x 45 mm, tweeter ... 16 mm ... saída de 20 W"      (3+)
      autoral  "Resistente e fácil de carregar pra quem ouve música fora"       (0)
      autoral  "não existe estéreo numa unidade só"                             (0)
      autoral  "IP67 cobre poeira e imersão de até 1 metro por 30 minutos"      (2)
    O limiar 3 é o que separa enumerar ficha de citar um número dentro de uma frase.
    """
    return len(MEDIDA_RE.findall(s)) >= 3


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

    # separa recitação de ficha da prosa autoral — só a autoral aciona (ver docstring)
    aut_exatas = [s for s in prose_exatas if not is_ficha(s)]
    fic_exatas = [s for s in prose_exatas if is_ficha(s)]
    aut_near = [(s, a, b) for s, a, b in prose_near if not is_ficha(a)]
    fic_near = [(s, a, b) for s, a, b in prose_near if is_ficha(a)]

    aut_near_08 = sum(1 for s, _, _ in aut_near if s >= 0.8)
    fic_near_08 = sum(1 for s, _, _ in fic_near if s >= 0.8)
    return {
        # PROSA AUTORAL — o que conta pra acionável
        "prosa_exatas": len(aut_exatas),
        "prosa_near_0.8": aut_near_08,
        "prosa_near_0.6": len(aut_near),
        "overlap_prosa_5gram_pct": ov[5],
        "overlap_prosa_8gram_pct": ov[8],
        "prosa_exatas_lista": aut_exatas[:30],
        "prosa_near_lista": [{"jaccard": s, "a": a[:160], "b": b[:160]} for s, a, b in aut_near[:30]],
        # FICHA dentro de pros/cons — reportada, NÃO aciona (não é escondida)
        "prosa_ficha_exatas": len(fic_exatas),
        "prosa_ficha_near_0.8": fic_near_08,
        "prosa_ficha_lista": (fic_exatas + [a for s, a, _ in fic_near if s >= 0.8])[:20],
        # SPECS — info, não acionável
        "specs_identicas": len(spec_exatas) + sum(1 for s, _, _ in spec_near if s >= 0.8),
        "specs_identicas_lista": (spec_exatas + [a for s, a, _ in spec_near if s >= 0.8])[:20],
        # acionável = SÓ prosa AUTORAL
        "acionavel": len(aut_exatas) > 0 or aut_near_08 > 0,
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
    peers_ilegiveis = 0
    for peer_path, peer_fm in peers:
        rep = compare(target_fm, peer_fm)
        rep["peer"] = peer_path
        if peer_fm.get("_ilegivel"):
            rep["peer_ilegivel"] = True
            rep["erro"] = peer_fm.get("_erro", "")
            peers_ilegiveis += 1
        results.append(rep)
        if rep["acionavel"]:
            actionable = True

    target_ilegivel = bool(target_fm.get("_ilegivel"))
    out = {
        "target": target_path,
        "asin": str(target_fm.get("asin") or ""),
        "target_ilegivel": target_ilegivel,          # True = NÃO tratar como limpo
        "erro": target_fm.get("_erro", "") if target_ilegivel else "",
        "peers_encontrados": len(peers),
        "peers_ilegiveis": peers_ilegiveis,          # irmãos que não deu pra comparar
        "duplicata_acionavel": actionable,   # SÓ por colisão de PROSA
        "comparacoes": results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(2 if target_ilegivel else (1 if actionable else 0))


if __name__ == "__main__":
    main()
