"""사진 찾기·내려받기 도구 (Wikimedia Commons).
  python3 tools/photo.py search "검색어"            → 파일 이름 · 이용 조건 · 크기
  python3 tools/photo.py get "File:이름.jpg" 저장이름  → assets/photo/저장이름.jpg 로 저장, credits.json 에 출처 기록
  python3 tools/photo.py sheet 저장이름...           → 확인용 모아 보기 (scratch 경로에 PNG)
Commons 로봇 정책에 맞는 User-Agent를 쓰고, 요청 사이에 쉬며, 표준 썸네일 크기만 요청합니다."""
import sys, re, json, html, time, pathlib, urllib.parse as up, urllib.request as ur, urllib.error as ue, os

ROOT = pathlib.Path(__file__).resolve().parent.parent
PHOTO = ROOT / 'assets' / 'photo'
CRED = PHOTO / 'credits.json'
UA = 'HistoryClassMaterials/1.0 (https://github.com/Simtaesoo/history)'
SIZES = [1280, 960, 1920, 500]

def fetch(url, tries=4):
    for t in range(tries):
        try:
            with ur.urlopen(ur.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                return r.read(), r.headers.get('Content-Type', '')
        except ue.HTTPError as e:
            if e.code in (429, 503) and t < tries - 1:
                time.sleep(20 * (t + 1)); continue
            raise
    raise RuntimeError('fetch failed')

def text(fragment):
    f = re.sub(r'<style.*?</style>|<span[^>]*class="[^"]*(?:wikidata|plainlinks)[^"]*".*?</span>', ' ', fragment or '', flags=re.S)
    f = re.sub(r'\.mw-parser-output[^}]*}', ' ', f)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(f))).strip()

def field(s, label):
    m = re.search(r'id="fileinfotpl_' + label + r'"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>', s, re.S)
    return text(m.group(1)) if m else ''

def wikiclean(v):
    v = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', v)          # [[a|b]] → b
    v = re.sub(r'\[https?://\S+ ([^\]]*)\]', r'\1', v)                 # [url 글] → 글
    v = re.sub(r'\{\{(?:creator|Creator):([^}|]*)[^}]*\}\}', r'\1', v)
    v = re.sub(r'\{\{[^{}]*\|([^{}|=]*)\}\}', r'\1', v)               # {{틀|값}} → 값
    v = re.sub(r'\{\{[^{}]*\}\}|<[^>]+>|\'\'+', '', v)
    return re.sub(r'\s+', ' ', v).strip(' |')

def rawfield(raw, names):
    for n in names:
        m = re.search(r'^\s*\|\s*' + n + r'\s*=\s*(.+)$', raw, re.M | re.I)
        if m and wikiclean(m.group(1)):
            return wikiclean(m.group(1))[:200]
    return ''

def info(title):
    raw = fetch('https://commons.wikimedia.org/w/index.php?' + up.urlencode({'title': title, 'action': 'raw'}))[0].decode('utf-8')
    time.sleep(1)
    s = fetch('https://commons.wikimedia.org/wiki/' + up.quote(title.replace(' ', '_')))[0].decode('utf-8')
    lic = sorted(set(text(x) for x in re.findall(r'class="licensetpl_short"[^>]*>(.*?)</span>', s)))
    if not lic:
        lic = sorted(set(re.findall(r'(Public domain|CC0|CC BY(?:-SA)? [0-9.]+|KOGL Type \d)', s)))[:3]
    m = re.search(r'upload\.wikimedia\.org/wikipedia/commons/([0-9a-f]/[0-9a-f]{2})/([^"?/]+)', s)
    return {
        'title': title, 'page': 'https://commons.wikimedia.org/wiki/' + up.quote(title.replace(' ', '_')),
        'license': ', '.join(lic), 'author': rawfield(raw, ['author', 'artist', 'photographer', 'creator']) or field(s, 'aut')[:200], 'date': field(s, 'date')[:80],
        'source': rawfield(raw, ['source', 'institution']) or field(s, 'src')[:300], 'desc': field(s, 'desc')[:600],
        'hash': m.group(1) if m else None, 'name': m.group(2) if m else None,
    }

def search(q):
    s = fetch('https://commons.wikimedia.org/w/index.php?' + up.urlencode(
        {'search': q, 'title': 'Special:Search', 'ns6': 1, 'fulltext': 1, 'limit': 20}))[0].decode('utf-8')
    seen = []
    for m in re.findall(r'href="/wiki/(File:[^"]+)"', s):
        t = up.unquote(html.unescape(m))
        if t not in seen:
            seen.append(t)
    for i, block in enumerate(re.findall(r'<li class="mw-search-result.*?</li>', s, re.S)):
        t = re.search(r'href="/wiki/(File:[^"]+)"', block)
        d = re.search(r'class="mw-search-result-data"[^>]*>(.*?)</div>', block, re.S)
        if t:
            print(up.unquote(html.unescape(t.group(1))), '|', text(d.group(1)) if d else '')

def get(title, save):
    if not title.startswith('File:'):
        title = 'File:' + title
    meta = info(title)
    if not meta['hash']:
        sys.exit('이미지 주소를 찾지 못함: ' + title)
    ext = '.png' if meta['name'].lower().endswith(('.png', '.gif', '.svg', '.tif', '.tiff')) else '.jpg'
    data = None
    for size in SIZES:
        url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{meta['hash']}/{meta['name']}/{size}px-{meta['name']}"
        if meta['name'].lower().endswith(('.tif', '.tiff')):
            url += '.jpg'; ext = '.jpg'
        try:
            body, ctype = fetch(url, tries=3)
            if ctype.startswith('image/'):
                data = body; break
        except ue.HTTPError as e:
            if e.code in (400, 404, 500):  # 원본보다 큰 썸네일 등
                continue
            time.sleep(15)
        time.sleep(3)
    if data is None:  # 작은 원본은 그대로
        body, ctype = fetch(f"https://upload.wikimedia.org/wikipedia/commons/{meta['hash']}/{meta['name']}")
        data = body
    out = PHOTO / (save + ext)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    from PIL import Image
    im = Image.open(out)
    if im.mode not in ('RGB', 'L'):
        im = im.convert('RGB')
    im.thumbnail((1600, 1600))
    im.save(out, quality=84, optimize=True) if ext == '.jpg' else im.save(out, optimize=True)
    cred = json.loads(CRED.read_text(encoding='utf-8')) if CRED.exists() else {}
    meta.pop('hash'); meta.pop('name')
    rel = str(out.relative_to(PHOTO)); meta['file'] = rel; meta['size'] = Image.open(out).size
    cred[rel] = meta
    CRED.write_text(json.dumps(cred, ensure_ascii=False, indent=1), encoding='utf-8')
    print(rel, meta['size'], '|', meta['license'], '|', meta['author'][:60], '|', meta['date'])
    time.sleep(3)

def sheet(names):
    from PIL import Image
    ims = []
    for n in names:
        p = next(PHOTO.glob(n + '.*'))
        im = Image.open(p).convert('RGB'); im.thumbnail((10000, 300)); ims.append(im)
    W = sum(i.width for i in ims) + 8 * len(ims); o = Image.new('RGB', (W, 300), 'white'); x = 0
    for i in ims:
        o.paste(i, (x, 0)); x += i.width + 8
    dst = pathlib.Path(os.environ.get('SHEET', '/tmp/sheet.png')); o.save(dst); print(dst)

if __name__ == '__main__':
    cmd = sys.argv[1]
    {'search': lambda: search(sys.argv[2]), 'get': lambda: get(sys.argv[2], sys.argv[3]), 'sheet': lambda: sheet(sys.argv[2:]), 'refresh': lambda: None}[cmd]()

def refresh(keys):
    """credits.json 의 출처 정보만 다시 읽기 (파일은 그대로)."""
    cred = json.loads(CRED.read_text(encoding='utf-8'))
    for k in keys:
        m = info(cred[k]['title']); m.pop('hash'); m.pop('name')
        m['file'] = k; m['size'] = cred[k].get('size'); cred[k] = m
        print(k, '|', m['license'], '|', m['author'][:70]); time.sleep(3)
    CRED.write_text(json.dumps(cred, ensure_ascii=False, indent=1), encoding='utf-8')

if __name__ == '__main__' and sys.argv[1] == 'refresh':
    refresh(sys.argv[2:])
