"""檢查譯文格式，並可把外部譯文檔合併進來源。

檢查項目（對照同資料夾的 en_us.json）:
  - 譯文鍵不存在於英文（多餘鍵）
  - § 色碼序列與英文不同
  - %% / %s 等格式符號數量不同
  - 譯文為空或與英文完全相同（僅提示）

用法:
  python -I translation/tools/check_translations.py                    檢查 translation/source 下全部
  python -I translation/tools/check_translations.py merge <來源資料夾> <譯文.json>...
      例: merge translation/source/quests a.json b.json   （檢查通過才寫入 zh_tw.json）
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'translation', 'source')
COLOR_RE = re.compile(r'§[0-9a-fk-or]', re.I)
FORMAT_RE = re.compile(r'%(?:\d+\$)?[sd%]')


def load(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def check(en, tw):
    """回傳 (錯誤列表, 提示列表)。"""
    errors, notes = [], []
    for k, v in tw.items():
        if k not in en:
            errors.append(f'{k}: 英文中沒有此鍵')
            continue
        if not isinstance(v, str):
            errors.append(f'{k}: 譯文不是字串')
            continue
        if not v.strip():
            notes.append(f'{k}: 譯文為空')
            continue
        src_colors = sorted(c.lower() for c in COLOR_RE.findall(en[k]))
        tw_colors = sorted(c.lower() for c in COLOR_RE.findall(v))
        if src_colors != tw_colors:
            errors.append(f'{k}: 色碼不一致 {"".join(src_colors)} → {"".join(tw_colors)}')
        if sorted(FORMAT_RE.findall(en[k])) != sorted(FORMAT_RE.findall(v)):
            errors.append(f'{k}: 格式符號不一致（% 需寫成 %%）')
        if v == en[k] and re.search(r'[A-Za-z]{4,}', v):
            notes.append(f'{k}: 與英文相同')
    return errors, notes


def write(path, data):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')


def main():
    sys.stdout.reconfigure(encoding='utf-8')  # Windows 主控台預設編碼無法輸出中文
    if len(sys.argv) > 1 and sys.argv[1] == 'merge':
        src_dir = sys.argv[2]
        en = load(os.path.join(src_dir, 'en_us.json'))
        incoming = {}
        for p in sys.argv[3:]:
            incoming.update(load(p))
        errors, notes = check(en, incoming)
        for e in errors + notes:
            print(('錯誤 ' if e in errors else '提示 ') + e)
        if errors:
            print(f'有 {len(errors)} 個錯誤，未寫入')
            sys.exit(1)
        tw_path = os.path.join(src_dir, 'zh_tw.json')
        tw = load(tw_path)
        tw.update(incoming)
        write(tw_path, tw)
        print(f'已合併 {len(incoming)} 條到 {tw_path}')
        return
    failed = 0
    for tw_path in sorted(glob.glob(os.path.join(SRC, '**', 'zh_tw.json'), recursive=True)):
        en = load(os.path.join(os.path.dirname(tw_path), 'en_us.json'))
        if not en:
            continue
        errors, _ = check(en, load(tw_path))
        for e in errors:
            print(f'{os.path.relpath(tw_path, SRC)}: {e}')
        failed += len(errors)
    print('全部通過' if not failed else f'共 {failed} 個錯誤')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
