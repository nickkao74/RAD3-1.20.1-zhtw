"""翻譯工作佇列：把所有待翻內容切成小塊，分派給多人（或多個 AI 子代理）平行翻譯，可隨時中斷續跑。

進度全部存在檔案裡：
  translation/source/**/zh_tw.json    已合併的譯文（git 追蹤）
  translation/work/                   進行中的工作塊（gitignore）
    chunkNNN.en.json                  待翻原文（含 _meta：來源資料夾、語氣說明）
    chunkNNN.dispatched               已分派的時間戳（避免重複分派）
    chunkNNN.zh_tw.json               譯者交回的譯文（merge 時檢查並合併）

用法:
  python -I translation/tools/autopilot.py mods <mods 資料夾>   依 MOD_TARGETS 抽出模組待翻原文到 source/mods/
  python -I translation/tools/autopilot.py status               各來源進度與進行中的工作塊
  python -I translation/tools/autopilot.py next [塊數]           佇列中下一批切塊（已有未完成塊則不切）
  python -I translation/tools/autopilot.py dispatched <塊名>...  標記為已分派
  python -I translation/tools/autopilot.py merge                 檢查並合併已交回的譯文
"""
import glob
import importlib.util
import json
import os
import re
import sys
import time
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TR = os.path.join(ROOT, 'translation')
SRC = os.path.join(TR, 'source')
WORK = os.path.join(TR, 'work')
WORDS_PER_CHUNK = 1300
ENTRIES_PER_CHUNK = 300
STALE_SECONDS = 45 * 60


def _load_module(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TR, 'tools', name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


check_translations = _load_module('check_translations')

# 需要自己翻的模組（jar 內無繁中、也無可轉換的簡中），依優先順序。
# 長篇說明可延後：araxers_bestiary（怪物圖鑑）、meed（附魔說明，與 EnchantmentDescriptions 重疊）。
MOD_TARGETS = [
    # 高優先：玩法內容
    'radweaponry', 'skilltree', 'landsoficaria', 'additional_attributes', 'ancient_aether',
    'nameless_trinkets', 'knavesneeds', 'collectorsalbum', 'sorcerousnether', 'ntrials',
    'radenchants', 'fallen_traits_relics', 'red_exp',
    # 中優先：介面、裝飾、附加說明
    'titles', 'vinery', 'ars_nouveau', 'friendsandfoes',
    # 長篇說明
    'araxers_bestiary', 'meed',
]
# 玩家幾乎看不到的設定／指令類條目不翻
SKIP_KEY_RE = re.compile(r'(^|[._])(config|configuration|command|commands|cmd|option|options|gui\.config)([._]|$)', re.I)

# 佇列順序：任務書 → 模組包語言檔 → 模組
TONE = {
    'quests': 'FTB Quests 任務書文字（標題、副標題、描述）；說明清楚、劇情用敘事口吻。',
    'modpack': '模組包自帶的語言檔（物品名、tooltip、Ponder 教學、屬性名）；物品名簡短，說明清楚。',
    'mods': '模組語言檔（物品／方塊／生物名稱、tooltip、說明）；名稱簡短一致，同系列物品命名規則要統一。',
}


def load(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def dump(path, data, indent=2, sort=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent, sort_keys=sort)
        f.write('\n')


def words(d):
    return sum(len(str(v).split()) for v in d.values())


def extract_mods(mods_dir):
    """從 jar 抽出 MOD_TARGETS 中無繁中、無簡中的條目，寫到 source/mods/<ns>/en_us.json。"""
    langs = {}
    for fn in sorted(os.listdir(mods_dir), key=str.lower):
        if not fn.endswith('.jar'):
            continue
        try:
            z = zipfile.ZipFile(os.path.join(mods_dir, fn))
        except zipfile.BadZipFile:
            continue
        with z:
            for n in z.namelist():
                m = re.match(r'assets/([^/]+)/lang/(en_us|zh_tw|zh_cn)\.json$', n)
                if m and m.group(1) in MOD_TARGETS:
                    try:
                        data = json.loads(z.read(n).decode('utf-8-sig'))
                    except ValueError:
                        continue
                    langs.setdefault(m.group(1), {}).setdefault(m.group(2), {}).update(
                        {k: v for k, v in data.items() if isinstance(v, str)})
    for ns in MOD_TARGETS:
        d = langs.get(ns, {})
        have = set(d.get('zh_tw', {})) | {k for k, v in d.get('zh_cn', {}).items() if v.strip()}
        en = {k: v for k, v in d.get('en_us', {}).items()
              if k not in have and v.strip() and not SKIP_KEY_RE.search(k)}
        dump(os.path.join(SRC, 'mods', ns, 'en_us.json'), en)
        tw_path = os.path.join(SRC, 'mods', ns, 'zh_tw.json')
        if not os.path.exists(tw_path):
            dump(tw_path, {})
        print(f'  {ns:<24} {len(en):>5} 條 {words(en):>6} 字')


def targets():
    """依佇列順序回傳 [(來源資料夾, 種類)]。"""
    out = [(os.path.join(SRC, 'quests'), 'quests')]
    out += [(d, 'modpack') for d in sorted(glob.glob(os.path.join(SRC, 'modpack', '*')))]
    out += [(os.path.join(SRC, 'mods', ns), 'mods') for ns in MOD_TARGETS
            if os.path.isdir(os.path.join(SRC, 'mods', ns))]
    return out


def pending_keys():
    """所有已在工作塊中（尚未合併）的鍵。"""
    keys = set()
    for p in glob.glob(os.path.join(WORK, 'chunk*.en.json')):
        keys |= {k for k in load(p) if k != '_meta'}
    return keys


def untranslated(src_dir):
    en = load(os.path.join(src_dir, 'en_us.json'))
    tw = load(os.path.join(src_dir, 'zh_tw.json'))
    return {k: v for k, v in en.items() if not tw.get(k)}


def group_key(kind, key):
    # 任務書以物件 ID 分組，同一任務不拆開；語言檔不分組
    return key.split('.')[1] if kind == 'quests' else key


def cmd_next(n):
    os.makedirs(WORK, exist_ok=True)
    open_chunks = [p for p in glob.glob(os.path.join(WORK, 'chunk*.en.json'))
                   if not os.path.exists(p.replace('.en.json', '.zh_tw.json'))]
    if open_chunks:
        print(f'尚有 {len(open_chunks)} 個未完成工作塊，不切新塊')
        return
    busy = pending_keys()
    existing = [int(re.search(r'chunk(\d+)', p).group(1))
                for p in glob.glob(os.path.join(WORK, '**', 'chunk*.en.json'), recursive=True)]
    seq = max(existing, default=0)
    # 同一種類（quests / modpack / mods）的多個來源可合在同一塊，_meta.sources 記錄每個鍵的來源
    made, cur, cur_kind, cur_src = [], {}, None, {}

    def flush():
        nonlocal cur, cur_src
        if cur:
            made.append((cur_kind, cur, cur_src))
        cur, cur_src = {}, {}

    for src_dir, kind in targets():
        if len(made) >= n:
            break
        todo = {k: v for k, v in untranslated(src_dir).items() if k not in busy}
        busy |= set(todo)
        if not todo:
            continue
        if kind != cur_kind:
            flush()
            cur_kind = kind
        groups = {}
        for k, v in todo.items():
            groups.setdefault(group_key(kind, k), {})[k] = v
        rel = os.path.relpath(src_dir, ROOT).replace(os.sep, '/')
        for g in groups.values():
            if cur and (words(cur) + words(g) > WORDS_PER_CHUNK or len(cur) + len(g) > ENTRIES_PER_CHUNK):
                flush()
                if len(made) >= n:
                    break
            cur.update(g)
            cur_src.update({k: rel for k in g})
    if len(made) < n:
        flush()
    for kind, data, srcs in made:
        seq += 1
        name = f'chunk{seq:03d}'
        sources = sorted(set(srcs.values()))
        meta = {'kind': kind, 'tone': TONE[kind], 'sources': srcs}
        dump(os.path.join(WORK, name + '.en.json'), {'_meta': meta, **data}, indent=1, sort=False)
        print(f'{name}: {", ".join(s.split("/")[-1] for s in sources)} {len(data)} 條 {words(data)} 字')
    if not made:
        print('佇列已清空：所有目標都已翻譯或已在工作塊中')


def cmd_dispatched(names):
    for n in names:
        with open(os.path.join(WORK, n + '.dispatched'), 'w') as f:
            f.write(str(int(time.time())))


def cmd_merge():
    for p in sorted(glob.glob(os.path.join(WORK, 'chunk*.zh_tw.json'))):
        name = os.path.basename(p).split('.')[0]
        en_path = os.path.join(WORK, name + '.en.json')
        src = load(en_path)
        meta = src.pop('_meta', {})
        try:
            tw = load(p)
        except ValueError as e:
            print(f'{name}: JSON 錯誤 {e}')
            continue
        tw.pop('_meta', None)
        srcs = meta.get('sources') or {k: meta['source'] for k in src}
        # 同一個鍵可能出現在多個來源（如 kubejs 與 kubejs_registry），全部寫入
        rels = sorted(set(srcs.values()) | {os.path.relpath(d, ROOT).replace(os.sep, '/')
                                            for d, kind in targets() if kind == meta.get('kind')})
        by_src = {}
        for rel in rels:
            en_keys = load(os.path.join(ROOT, rel, 'en_us.json'))
            part = {k: v for k, v in tw.items() if k in en_keys}
            if part:
                by_src[rel] = part
        missing = [k for k in src if k not in tw]
        errors = []
        for rel, part in by_src.items():
            en = load(os.path.join(ROOT, rel, 'en_us.json')) if rel else {}
            errors += check_translations.check(en, part)[0]
        if errors or missing:
            print(f'{name}: 錯誤 {len(errors)}、缺鍵 {len(missing)}，未合併')
            for e in errors[:10]:
                print('   ', e)
            continue
        for rel, part in by_src.items():
            tw_path = os.path.join(ROOT, rel, 'zh_tw.json')
            merged = load(tw_path)
            merged.update(part)
            dump(tw_path, merged)
        done = os.path.join(WORK, 'done')
        os.makedirs(done, exist_ok=True)
        for suffix in ('.en.json', '.zh_tw.json', '.zh_tw.json.notes.md', '.dispatched'):
            f = os.path.join(WORK, name + suffix)
            if os.path.exists(f):
                os.replace(f, os.path.join(done, name + suffix))
        print(f'{name}: 已合併 {len(tw)} 條 → {", ".join(r.split("/")[-1] for r in by_src)}')


def cmd_status():
    total_en = total_tw = 0
    for src_dir, kind in targets():
        en = load(os.path.join(src_dir, 'en_us.json'))
        left = untranslated(src_dir)
        total_en += words(en)
        total_tw += words(en) - words(left)
        if left:
            print(f'  {os.path.relpath(src_dir, SRC):<36} 剩 {len(left):>5} 條 {words(left):>6} 字')
    print(f'整體（英文字數）: {total_tw}/{total_en}')
    now = time.time()
    for p in sorted(glob.glob(os.path.join(WORK, 'chunk*.en.json'))):
        name = os.path.basename(p).split('.')[0]
        if os.path.exists(os.path.join(WORK, name + '.zh_tw.json')):
            state = '已交回，待 merge'
        else:
            d = os.path.join(WORK, name + '.dispatched')
            if not os.path.exists(d):
                state = '未分派'
            else:
                age = now - int(open(d).read().strip() or 0)
                state = f'翻譯中 {int(age // 60)} 分鐘' + ('（逾時，可重新分派）' if age > STALE_SECONDS else '')
        print(f'  {name}: {state}')


def main():
    sys.stdout.reconfigure(encoding='utf-8')  # Windows 主控台預設編碼無法輸出中文
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if cmd == 'mods':
        extract_mods(sys.argv[2])
    elif cmd == 'next':
        cmd_next(int(sys.argv[2]) if len(sys.argv) > 2 else 6)
    elif cmd == 'dispatched':
        cmd_dispatched(sys.argv[2:])
    elif cmd == 'merge':
        cmd_merge()
    elif cmd == 'status':
        cmd_status()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
