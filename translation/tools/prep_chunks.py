"""把指定任務章節中尚未翻譯的條目抽出，依字數切成數塊，方便分工翻譯。

同一個任務（物件 ID）的條目一定在同一塊，保留上下文。
輸出 <輸出資料夾>/chunkN.en.json，翻完的譯文用 check_translations.py merge 合併。

用法: python -I translation/tools/prep_chunks.py <輸出資料夾> <塊數> <章節檔名>...
  例: python -I translation/tools/prep_chunks.py work 4 adventure_begins
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
QUESTS = os.path.join(ROOT, 'config', 'ftbquests', 'quests', 'chapters')

_spec = importlib.util.spec_from_file_location('quests_i18n', os.path.join(os.path.dirname(__file__), 'quests_i18n.py'))
quests_i18n = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(quests_i18n)


def words(d):
    return sum(len(v.split()) for v in d.values())


def main():
    sys.stdout.reconfigure(encoding='utf-8')  # Windows 主控台預設編碼無法輸出中文
    out_dir, n, chapters = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    with open(os.path.join(ROOT, 'translation', 'source', 'quests', 'zh_tw.json'), encoding='utf-8') as f:
        done = json.load(f)
    groups = {}
    for ch in chapters:
        out = {}
        path = os.path.join(QUESTS, ch + '.snbt')
        with open(path, encoding='utf-8', newline='') as f:
            quests_i18n.process_text(f.read(), out, 'f_' + ch)
        for k, v in out.items():
            if k not in done:
                groups.setdefault(k.split('.')[1], {})[k] = v
    total = sum(words(g) for g in groups.values())
    target = total / n
    chunks = [{}]
    for g in groups.values():
        if words(chunks[-1]) >= target and len(chunks) < n:
            chunks.append({})
        chunks[-1].update(g)
    os.makedirs(out_dir, exist_ok=True)
    for i, c in enumerate(chunks, 1):
        with open(os.path.join(out_dir, f'chunk{i}.en.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(c, f, ensure_ascii=False, indent=1)
        print(f'chunk{i}: {len(c)} 條、{words(c)} 字')
    print(f'合計 {sum(len(c) for c in chunks)} 條、{total} 字')


if __name__ == '__main__':
    main()
