"""掃描模組包 mods/ 內所有 jar 的語言檔，輸出繁中覆蓋率報告。

用法: python -I translation/tools/scan_mods.py <模組包實例資料夾> [輸出 md 路徑]
"""
import json
import os
import re
import sys
import zipfile

LANGS = ('en_us', 'zh_tw', 'zh_cn')
LANG_RE = re.compile(r'assets/([^/]+)/lang/([a-z_]+)\.json$')
BOOK_RE = re.compile(r'(?:assets|data)/[^/]+/patchouli_books/([^/]+)/([a-z_]+)/')


def load_keys(z, name):
    try:
        return set(json.loads(z.read(name).decode('utf-8-sig')))
    except Exception:
        return set()


def scan_jar(path):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    keys = {lg: set() for lg in LANGS}
    books = {}
    for n in names:
        m = LANG_RE.match(n)
        if m and m.group(2) in LANGS:
            keys[m.group(2)] |= {f'{m.group(1)}:{k}' for k in load_keys(z, n)}
        b = BOOK_RE.match(n)
        if b:
            books.setdefault(b.group(1), set()).add(b.group(2))
    modid = None
    if 'META-INF/mods.toml' in names:
        t = z.read('META-INF/mods.toml').decode('utf-8', 'ignore')
        m = re.search(r'modId\s*=\s*"([^"]+)"', t)
        modid = m.group(1) if m else None
    en = keys['en_us']
    return {
        'modid': modid,
        'en': len(en),
        'tw': len(en & keys['zh_tw']),
        'cn': len(en & keys['zh_cn']),
        'books': {k: sorted(v) for k, v in books.items()},
    }


def status(r):
    if r['en'] == 0:
        return '無文字'
    if r['tw'] >= r['en'] * 0.95:
        return '繁中完整'
    if r['tw'] > 0:
        return '繁中部分'
    if r['cn'] > 0:
        return '僅簡中'
    return '無中文'


def main():
    sys.stdout.reconfigure(encoding='utf-8')  # Windows 主控台預設編碼無法輸出中文
    inst = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else 'translation/reports/mod_lang_status.md'
    rows = []
    mods = os.path.join(inst, 'mods')
    for fn in sorted(os.listdir(mods), key=str.lower):
        if fn.endswith('.jar'):
            r = scan_jar(os.path.join(mods, fn))
            r['jar'] = fn
            r['status'] = status(r)
            rows.append(r)
    order = ['無中文', '僅簡中', '繁中部分', '繁中完整', '無文字']
    rows.sort(key=lambda r: (order.index(r['status']), -(r['en'] - r['tw'])))
    counts = {s: sum(1 for r in rows if r['status'] == s) for s in order}
    total_en = sum(r['en'] for r in rows)
    missing = sum(r['en'] - r['tw'] for r in rows)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 模組語言檔繁中覆蓋率（jar 內建）\n\n')
        f.write('> 由 `translation/tools/scan_mods.py` 自動產生，請勿手動編輯。\n')
        f.write('> 只統計 jar 內建語言檔；外部資源包（如 CFPA 簡中包）的覆蓋另計。\n\n')
        f.write(f'共 {len(rows)} 個 jar；英文條目 {total_en}，缺繁中 {missing}。\n\n')
        for s in order:
            f.write(f'- {s}：{counts[s]}\n')
        f.write('\n| 狀態 | jar | modid | en_us | zh_tw | zh_cn | 缺繁中 | Patchouli 書（語言資料夾） |\n')
        f.write('|---|---|---|---:|---:|---:|---:|---|\n')
        for r in rows:
            books = '; '.join(f"{k}({','.join(v)})" for k, v in r['books'].items())
            f.write(f"| {r['status']} | {r['jar']} | {r['modid'] or ''} | {r['en']} | {r['tw']} | "
                    f"{r['cn']} | {r['en'] - r['tw']} | {books} |\n")
    print(f'{len(rows)} jars -> {out}; ' + ', '.join(f'{s}={counts[s]}' for s in order))


if __name__ == '__main__':
    main()
