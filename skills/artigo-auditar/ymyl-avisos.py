#!/usr/bin/env python3
"""Avisos de "procure um profissional de saúde" repetidos no MESMO artigo.

Uso:
  python3 .claude/skills/artigo-auditar/ymyl-avisos.py sites/{site}/src/content/reviews/{slug}.mdx [--json]

Régua (canon Marcelo 2026-06-25, extensão 2026-07-30): em nicho de saúde o aviso
"procure médico/nutricionista" entra NO MÁXIMO UMA VEZ por artigo, e só quando o
ponto é genuinamente sensível. O texto é comparativo de compra, não bula.

POR QUE UM SCRIPT, e não leitura (a lição que originou este arquivo, 2026-08-30):
o artigo é montado por skills diferentes em momentos diferentes — os reviews pela
`artigo-review-criar`, o guide pela `artigo-guia-escrever`, a intro pela
`artigo-intro-escrever`. Cada uma conhece a régua "no máximo um" e escreve o SEU.
Nenhuma vê o que a outra escreveu. Medido na rede: dos avisos em artigos com
excesso, 54% estão nos reviews e 46% no guide, e só 4 blocos `fullReview` da rede
inteira tinham 2+ avisos DENTRO do mesmo review. Ou seja, a repetição é ENTRE as
seções, e nenhuma skill de criação tem como enxergar isso sozinha.

E por que a contagem não pode ser improvisada na hora: um regex frouxo infla o
número em ~80%. Medido no mesmo dia — um detector escrito às pressas acusou 79
artigos com excesso; a definição estrita dá 44. O que ele contava errado:
  · "60 comprimidos na orientação de dois ao dia"     → posologia
  · "a orientação de uso começa nessa idade"          → instrução de rótulo
  · label: "Orientação de uso" value: "1 a 2 gomas"   → linha da tabela de specs
  · "Complementa, não substitui"                      → sobre alimentação, não médico
A definição estrita exige um PROFISSIONAL DE SAÚDE citado. Sem isso não é aviso.
"""
import re, sys, json

PROF = r'(?:m[ée]dic[oa]|pediatra|nutricionista|profissional de sa[úu]de|especialista de sa[úu]de)'
# Aviso = manda/condiciona a procurar profissional, OU nega substituir profissional.
AVISO = re.compile(
    rf'(?:consulte|procure|converse com|fale com|orienta[çc][ãa]o d[eo]|acompanhamento d[eo]|'
    rf'sob orienta[çc][ãa]o d[eo]|indica[çc][ãa]o d[eo]|supervis[ãa]o d[eo])\s+'
    rf'(?:um |uma |seu |sua )?{PROF}'
    rf'|n[ãa]o substitui[^.<>]{{0,45}}{PROF}', re.I)


def secoes(raw: str):
    """Divide o .mdx em (reviews, guide, intro). O guideContent e o products[]
    vivem os DOIS no frontmatter, então o corte é por posição da chave."""
    m = re.match(r'^---\n([\s\S]*?)\n---\n([\s\S]*)$', raw)
    fm, body = (m.group(1), m.group(2)) if m else (raw, '')
    gi, pi = fm.find('guideContent:'), fm.find('products:')
    guide = fm[gi:] if gi >= 0 else ''
    if pi >= 0:
        prods = fm[pi:gi] if gi > pi else fm[pi:]
    else:
        prods = ''
    return {'reviews': prods, 'guide': guide, 'intro': body}


def trecho(texto: str, m) -> str:
    """Janela em volta do match. NÃO corta por ".": URL de afiliado e YAML têm
    ponto e não têm frase, e cortar ali devolve lixo (bug medido 2026-08-30)."""
    ini, fim = max(0, m.start() - 85), min(len(texto), m.end() + 85)
    s = re.sub(r'https?://\S+', '[url]', texto[ini:fim])
    s = re.sub(r'<[^>]+>', ' ', s)
    return ('…' if ini else '') + ' '.join(s.split())[:175] + ('…' if fim < len(texto) else '')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print('uso: ymyl-avisos.py <path do .mdx> [--json]', file=sys.stderr); sys.exit(2)
    path = args[0]
    raw = open(path, encoding='utf-8').read()
    sec = secoes(raw)

    achados = []
    for nome, texto in sec.items():
        for m in AVISO.finditer(texto):
            achados.append({'secao': nome, 'trecho': trecho(texto, m)})

    total = len(achados)
    por = {k: sum(1 for a in achados if a['secao'] == k) for k in sec}
    # SOBREVIVENTE: o do guide se houver (seção educativa, é onde o aviso cabe);
    # senão o primeiro dos reviews. Regra posicional de propósito — "manter o mais
    # ancorado num fato" não opera: no pior caso da rede os avisos ancorados eram
    # justamente os repetidos (idade mínima do rótulo, citada em 4 lugares).
    manter = 'guide' if por.get('guide') else ('reviews' if por.get('reviews') else 'intro')
    nivel = 'OK' if total <= 1 else 'FIX'

    if '--json' in sys.argv:
        vis = False
        for a in achados:
            a['acao'] = 'KEEP' if (a['secao'] == manter and not vis) else 'PODA'
            vis = vis or a['acao'] == 'KEEP'
        print(json.dumps({'path': path, 'total': total, 'por_secao': por,
                          'nivel': nivel, 'manter_em': manter if total > 1 else None,
                          'podar': sum(1 for a in achados if a['acao'] == 'PODA'),
                          'achados': achados}, ensure_ascii=False, indent=1))
        return

    print(f'# Avisos YMYL — {path}')
    print(f'{total} aviso(s) · reviews={por.get("reviews",0)} guide={por.get("guide",0)} intro={por.get("intro",0)} · [{nivel}]\n')
    if total <= 1:
        print('Dentro da régua (máximo 1 por artigo). Nada a podar.')
        return
    print(f'Régua: máximo 1 por artigo. SOBREVIVENTE = o do `{manter}`; os demais são excedente.\n')
    keep_usado = False
    for a in achados:
        eh_keep = (a['secao'] == manter) and not keep_usado
        if eh_keep:
            keep_usado = True
        print(f'{"  KEEP" if eh_keep else "  PODA"} [{a["secao"]}] {a["trecho"]}')
    print('\n⚠ Só pode APAGAR o excedente quando ele é frase inteira ou oração removível')
    print('  deixando o texto válido. Se a remoção exigir reescrever a frase em volta,')
    print('  é prosa nova: REPORTA, não aplica.')
    if manter != 'guide' and por.get('guide'):
        print('⚠ Guide tem aviso e não foi eleito sobrevivente: revise a regra.')


if __name__ == '__main__':
    main()
