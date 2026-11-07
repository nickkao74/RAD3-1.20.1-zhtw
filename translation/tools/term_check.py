"""譯名一致性檢查：英文含 glossary 詞條、但譯文沒用對應譯名的條目。

只檢查單一詞條（英文與繁中都不含「/」「～」「X」等變體寫法的列），備註含「不檢查」的列略過；
英文欄的全形括號註記（如「Trait（L2Hostility）」）會被忽略。比對英文時區分大小寫，
以免一般單字（end、scrap）被當成專有名詞。

用法:
  python -I translation/tools/term_check.py                全部來源
  python -I translation/tools/term_check.py --json <檔案>  另把結果寫成 JSON（供審查子代理使用）
  python -I translation/tools/term_check.py --only <來源>  只查某來源，如 mods/ancient_aether
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'translation', 'source')
GLOSSARY = os.path.join(ROOT, 'translation', 'glossary.md')
# 已知會誤報的組合：英文詞在這些語境下不該套 glossary 譯名
ALLOW = {
    'Trait': re.compile(r'personality|trait of', re.I),
}


def load(path):
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def glossary_terms():
    terms = []
    with open(GLOSSARY, encoding='utf-8') as f:
        for line in f:
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cells) < 2 or cells[0] in ('英文', '') or set(cells[0]) <= set('-'):
                continue
            en = re.sub(r'（.*?）', '', cells[0]).strip()
            zh = cells[1]
            if len(cells) > 2 and '不檢查' in cells[2]:
                continue
            if not en or not zh or re.search(r'[/～]|\bX\b|\.\.\.', en) or re.search(r'[／～X]', zh):
                continue
            terms.append((en, zh))
    # 長詞優先，避免「Coin」蓋過「Diamond Coin」
    return sorted(terms, key=lambda t: -len(t[0]))


def main():
    sys.stdout.reconfigure(encoding='utf-8')  # Windows 主控台預設編碼無法輸出中文
    args = sys.argv[1:]
    out_json = args[args.index('--json') + 1] if '--json' in args else None
    only = args[args.index('--only') + 1] if '--only' in args else None
    terms = glossary_terms()
    issues = []
    for tw_path in sorted(glob.glob(os.path.join(SRC, '**', 'zh_tw.json'), recursive=True)):
        rel = os.path.relpath(os.path.dirname(tw_path), SRC).replace(os.sep, '/')
        if only and rel != only:
            continue
        en_path = os.path.join(os.path.dirname(tw_path), 'en_us.json')
        if not os.path.exists(en_path):
            continue
        en, tw = load(en_path), load(tw_path)
        for k, v in tw.items():
            src = re.sub(r'§.', '', en.get(k, ''))
            covered = ''
            for term, zh in terms:
                if not re.search(r'\b' + re.escape(term) + r's?\b', src, re.I):
                    continue
                if any(term.lower() in c.lower() for c in covered.split('\0') if c):
                    continue  # 已被更長的詞條涵蓋
                covered += '\0' + term
                if term in ALLOW and ALLOW[term].search(src):
                    continue
                if zh not in v and term not in v:  # 刻意保留英文（如模組名）不算
                    issues.append({'source': rel, 'key': k, 'term': term, 'expected': zh, 'en': en[k], 'zh_tw': v})
    by_term = {}
    for i in issues:
        by_term.setdefault((i['term'], i['expected']), []).append(i)
    for (term, zh), items in sorted(by_term.items(), key=lambda x: -len(x[1])):
        print(f'{term} → {zh}：{len(items)} 條未使用')
        for i in items[:3]:
            print(f'    {i["source"]} {i["key"]}: {i["zh_tw"][:50]}')
    print(f'共 {len(issues)} 條可能不一致（{len(terms)} 個詞條）')
    if out_json:
        with open(out_json, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(issues, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
