"""수업 슬라이드 만들기: tools/decks/<과목>_<단원>.py 의 LESSONS 를 읽어 <과목>/<단원>/slidesN.html 을 씁니다.
사용: python3 tools/build_deck.py tools/decks/m1_ancient.py
장 종류(type):
  cover  photo, word, small, [tag]           표지: 사진 + 큰 낱말
  q      h2, lad                             관통 발문(따옴표) / 질문 사다리
  big    h2, [lad], [num], [size]            큰 낱말·질문 한 줄 (사진 없음)
  photoq photo, h2, [lad], [fit]             사진 + 오른쪽 위 질문
  photow photo, word, [small], [fit]         사진 + 왼쪽 아래 큰 낱말
  trio   items=[(낱말,작은글)...], [h2]       낱말 묶음(클릭마다 하나)
  pair   photos=[(사진,낱말)...], h2         두 사진 겨루기
  end    a, b                                한 문장 쓰기: a ___ b. 왜냐하면 ___.
모든 장: note(교사 메모 HTML). lad = [(꼬리표, 질문)...] 꼬리표가 ''이면 질문만.
사진 출처는 assets/photo/credits.json 의 credit 와 이용 조건으로 자동 표기합니다."""
import sys, json, html, pathlib, runpy
ROOT = pathlib.Path(__file__).resolve().parent.parent
CRED = json.loads((ROOT / 'assets/photo/credits.json').read_text(encoding='utf-8'))
E = lambda s: html.escape(s, quote=True)

def lic(l):
    if 'KOGL' in l: return '공공누리 제1유형'
    if 'CC0' in l and 'BY' not in l: return 'CC0'
    if 'Public domain' in l or 'PDM' in l or 'PD-' in l: return '퍼블릭 도메인'
    for x in l.split(', '):
        if x.startswith('CC'): return x
    return l

def credit(ph):
    c = CRED.get(ph + '.jpg') or CRED.get(ph + '.png')
    if not c: raise SystemExit('출처 없음: ' + ph)
    return f"{c.get('credit') or c['title']} · {lic(c['license'])}"

def img(ph, alt, fit):
    f = ph + ('.png' if (ROOT / 'assets/photo' / (ph + '.png')).exists() else '.jpg')
    return (f'<div class="ph{" cover" if fit == "cover" else ""}"><img data-src="../../assets/photo/{f}" alt="{E(alt)}">'
            f'<div class="miss">사진 · {E(alt)}</div></div>')

def lad(items, cls='lad'):
    if not items: return ''
    return f'<div class="{cls}">' + ''.join(f'<p class="f">{"<b>"+E(a)+"</b>" if a else ""}{E(b)}</p>' for a, b in items) + '</div>'

def h2(t): return E(t).replace('\n', '<br>')

def slide(s, meta):
    t, note = s['type'], s.get('note', '')
    srcs, body = [], ''
    if t == 'cover':
        body = img(s['photo'], s.get('alt', s['word']), s.get('fit', 'cover')) + \
               f'<div class="tag">{E(s.get("tag", meta["tag"]))}</div><div class="word">{E(s["word"])}<small>{E(s.get("small", meta["title"]))}</small></div>'
        srcs = [s['photo']]
    elif t == 'q':
        body = f'<div class="q"><span class="mark">“</span><h2>{h2(s["h2"])}</h2>{lad(s.get("lad"))}</div>'
    elif t == 'big':
        size = s.get('size')
        st = f' style="font-size:min({size}vw,{int(size*12)}px);font-weight:900"' if size else ''
        num = f'<div class="num">{E(s["num"])}</div>' if s.get('num') else ''
        mt = ' style="margin-top:2vh"' if num and not size else st
        body = f'<div class="center"><div class="q">{num}<h2{mt}>{h2(s["h2"])}</h2>{lad(s.get("lad"))}</div></div>'
    elif t == 'photoq':
        body = img(s['photo'], s.get('alt', s['h2']), s.get('fit', 'cover')) + \
               f'<div class="onphoto"><h2>{h2(s["h2"])}</h2>{lad(s.get("lad"))}</div>'
        srcs = [s['photo']]
    elif t == 'photow':
        body = img(s['photo'], s.get('alt', s['word']), s.get('fit', 'cover')) + \
               f'<div class="word">{E(s["word"])}' + (f'<small>{E(s["small"])}</small>' if s.get('small') else '') + '</div>'
        srcs = [s['photo']]
    elif t == 'trio':
        size = s.get('size')
        bst = f' style="font-size:min({size}vw,{int(size*12)}px)"' if size else ''
        items = ''.join(f'<div class="f"><b{bst}>{E(a)}</b><span>{E(b)}</span></div>' for a, b in s['items'])
        if s.get('h2'):
            body = f'<div class="center"><div class="q"><h2>{h2(s["h2"])}</h2><div class="trio" style="margin-top:6vh">{items}</div></div></div>'
        else:
            body = f'<div class="trio">{items}</div>'
    elif t == 'pair':
        cells = ''.join(img(p, s.get('alts', [c, c])[i], 'cover').replace('</div></div>', f'</div><div class="cap">{E(c)}</div></div>', 1)
                        for i, (p, c) in enumerate(s['photos']))
        body = f'<div class="pair">{cells}</div><div class="center" style="pointer-events:none"><div class="onphoto" style="position:static;text-align:center;max-width:none"><h2>{h2(s["h2"])}</h2></div></div>'
        srcs = [p for p, _ in s['photos']]
    elif t == 'end':
        body = f'<div class="center"><div class="q"><span class="mark">“</span><h2>{E(s["a"])} <span class="fill">&nbsp;</span>{E(s["b"])}<br>왜냐하면 <span class="fill" style="min-width:7em">&nbsp;</span>.</h2></div></div>'
    else:
        raise SystemExit('모르는 장 종류: ' + t)
    src = f'<div class="src">{E(" / ".join(credit(p) for p in srcs))}</div>' if srcs else ''
    return f'<section class="s" data-note="{E(note)}">\n  {body}\n  {src}\n</section>\n'

def build(path):
    m = runpy.run_path(path)
    book, unit, uno, tag, back = m['BOOK'], m['UNIT'], m['UNO'], m['TAG'], m['BACK']
    out = ROOT / book / unit; out.mkdir(parents=True, exist_ok=True)
    for i, L in enumerate(m['LESSONS'], 1):
        meta = {'tag': tag, 'title': L['title']}
        n = len(L['slides'])
        if not 9 <= n <= 14: print(f'  주의: {i}차시 {n}장')
        if L['slides'][-1]['type'] != 'end': print(f'  주의: {i}차시 마지막 장이 한 문장 쓰기가 아님')
        doc = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(L["title"])} · {E(back)} {uno}단원 {i}차시</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700;900&family=IBM+Plex+Sans+KR:wght@400;500;700&display=swap">
<link rel="stylesheet" href="../../assets/deck.css">
</head>
<body>
<a class="home" href="../index.html#u{uno}">← {E(back)} 목록</a>
<div class="help"><button id="bN" type="button">발문 메모 (N)</button><button id="bF" type="button">전체 화면 (F)</button></div>
<main class="deck" id="deck">
''' + ''.join(slide(s, meta) for s in L['slides']) + '''</main>
<div class="bar" id="bar"></div><div class="hud" id="hud"></div>
<aside class="notes" id="notes"></aside>
<script src="../../assets/deck.js"></script>
</body>
</html>
'''
        (out / f'slides{i}.html').write_text(doc, encoding='utf-8')
        print(f'{book}/{unit}/slides{i}.html  {n}장')

if __name__ == '__main__':
    for p in sys.argv[1:]: build(p)
