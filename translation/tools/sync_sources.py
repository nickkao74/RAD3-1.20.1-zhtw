"""從模組包目前內容更新翻譯來源（英文快照），並回報各來源翻譯進度。

上游更新後執行一次，git diff translation/source/ 就能看出哪些英文改了、要補翻哪些。

用法: python -I translation/tools/sync_sources.py
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'translation', 'source')

# 模組包自帶、會被玩家看到的語言檔（en_us）
MODPACK_LANG_GLOBS = [
    'kubejs/assets/*/lang/en_us.json',
    'config/paxi/resourcepacks/RAD3-Resources/assets/*/lang/en_us.json',
]


def load(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def dump(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')


def report(name, en, tw_path):
    if not os.path.exists(tw_path):
        dump(tw_path, {})
    tw = load(tw_path)
    done = sum(1 for k in en if tw.get(k))
    stale = [k for k in tw if k not in en]
    pct = done * 100 // len(en) if en else 100
    extra = f'，多餘鍵 {len(stale)}' if stale else ''
    print(f'  {name:<40} {done:>5}/{len(en):<5} {pct:>3}%{extra}')


REGISTRY_RE = re.compile(r"StartupEvents\.registry\(\s*['\"](\w+)['\"]")
CREATE_RE = re.compile(r"\.create\(\s*(['\"])([^'\"]+)\1[^)]*\)(.*)")
DISPLAY_RE = re.compile(r"\.displayName\(\s*(['\"])((?:(?!\1)[^\\]|\\.)*)\1\s*\)")


def registry_names():
    """KubeJS startup 腳本中 .displayName('...') 註冊的名稱 -> 語言鍵（item.kubejs.<id> 等）。"""
    out = {}
    for path in sorted(glob.glob(os.path.join(ROOT, 'kubejs', 'startup_scripts', '*.js'))):
        with open(path, encoding='utf-8') as f:
            text = re.sub(r'/\*.*?\*/', '', f.read(), flags=re.S)
        kind = None
        for line in text.splitlines():
            line = line.split('//')[0] if line.lstrip().startswith('//') else line
            m = REGISTRY_RE.search(line)
            if m:
                kind = m.group(1)
            c = CREATE_RE.search(line)
            d = DISPLAY_RE.search(c.group(3)) if c else None
            if c and d and kind:
                ns, _, name = c.group(2).rpartition(':')
                out[f"{kind}.{ns or 'kubejs'}.{name}"] = d.group(2).replace("\\'", "'")
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')  # Windows 主控台預設編碼無法輸出中文
    print('任務書:')
    quests_en = os.path.join(SRC, 'quests', 'en_us.json')
    subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'translation', 'tools', 'quests_i18n.py'),
                    'extract', os.path.join(ROOT, 'config', 'ftbquests', 'quests'), quests_en], check=True)
    report('quests', load(quests_en), os.path.join(SRC, 'quests', 'zh_tw.json'))

    print('模組包語言檔:')
    merged = {}
    for pattern in MODPACK_LANG_GLOBS:
        for path in sorted(glob.glob(os.path.join(ROOT, pattern))):
            ns = os.path.basename(os.path.dirname(os.path.dirname(path)))
            merged.setdefault(ns, {}).update(load(path))
    # 資料夾名只決定資源包內的路徑，語言鍵是全域的
    merged['kubejs_registry'] = registry_names()
    for ns, en in sorted(merged.items()):
        dump(os.path.join(SRC, 'modpack', ns, 'en_us.json'), en)
        report(ns, en, os.path.join(SRC, 'modpack', ns, 'zh_tw.json'))

    mods = sorted(glob.glob(os.path.join(SRC, 'mods', '*', 'zh_tw.json')))
    if mods:
        print('模組補充翻譯:')
        for path in mods:
            print(f'  {os.path.basename(os.path.dirname(path)):<40} {len(load(path)):>5} 條')


if __name__ == '__main__':
    main()
