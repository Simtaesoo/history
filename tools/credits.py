"""assets/photo/credits.json → assets/photo/CREDITS.md 의 '전체 목록' 부분을 다시 만듭니다."""
import json, pathlib
P = pathlib.Path(__file__).resolve().parent.parent / 'assets' / 'photo'
md = (P / 'CREDITS.md').read_text(encoding='utf-8').split('\n## 전체 목록')[0].rstrip() + '\n'
cred = json.loads((P / 'credits.json').read_text(encoding='utf-8'))
rows = ['', '## 전체 목록 (Wikimedia Commons에서 받은 사진, tools/credits.py로 자동 생성)', '',
        '| 파일 | 이용 조건 | 출처 표기 | 원본 페이지 |', '|---|---|---|---|']
for k in sorted(cred):
    c = cred[k]
    rows.append(f"| {k} | {c.get('license','')} | {(c.get('credit') or c.get('author','')).replace('|','/')[:80]} | [{c['title'][5:60]}]({c['page']}) |")
(P / 'CREDITS.md').write_text(md + '\n'.join(rows) + '\n', encoding='utf-8')
print(len(cred), 'entries')
