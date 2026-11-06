"""把模組 jar 內只有簡中的語言條目用 OpenCC s2twp 轉成繁中（台灣用語）。

對每個 jar 的 assets/<ns>/lang/：取「en_us 有、zh_tw 沒有、zh_cn 有」的鍵轉換，
jar 內繁中不完整的模組只補缺的鍵。轉換後的 § 色碼與 %s 等格式符號須與英文一致，
不一致的條目略過（多半是簡中本身就過時或翻錯）。

用法: python -I translation/tools/cn2tw.py <mods 資料夾> [輸出 json]
  單獨執行時輸出 {命名空間: {鍵: 譯文}} 供檢查；build_pack.py --mods 會直接呼叫 convert()。
"""
import importlib.util
import json
import os
import re
import sys
import zipfile

LANG_RE = re.compile(r'assets/([^/]+)/lang/(en_us|zh_tw|zh_cn)\.json$')
# OpenCC 轉換後再換成 Minecraft 台灣官方用語（與任務書譯文一致）
TERMS = {'下界': '地獄', '末地': '終界', '幽匿': '伏聆', '蜡': '蠟'}

_spec = importlib.util.spec_from_file_location(
    'check_translations', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'check_translations.py'))
check_translations = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_translations)


def converter():
    try:
        import opencc
    except ImportError:
        sys.exit('缺少 OpenCC 套件，請先安裝:\n  python -m pip install opencc\n'
                 '（若安裝失敗可改用純 Python 版: python -m pip install opencc-python-reimplemented）')
    try:
        return opencc.OpenCC('s2twp')
    except Exception:
        return opencc.OpenCC('s2twp.json')


def to_tw(cc, text):
    text = cc.convert(text)
    for a, b in TERMS.items():
        text = text.replace(a, b)
    return text


def load_json(z, name):
    try:
        data = json.loads(z.read(name).decode('utf-8-sig'))
    except Exception:
        return {}
    return {k: v for k, v in data.items() if isinstance(v, str)} if isinstance(data, dict) else {}


def convert(mods_dir):
    """回傳 ({ns: {鍵: 繁中}}, 略過條數)。"""
    cc = converter()
    langs = {}  # ns -> lang -> dict
    for fn in sorted(os.listdir(mods_dir), key=str.lower):
        if not fn.endswith('.jar'):
            continue
        try:
            z = zipfile.ZipFile(os.path.join(mods_dir, fn))
        except zipfile.BadZipFile:
            continue
        with z:
            for n in z.namelist():
                m = LANG_RE.match(n)
                if m:
                    langs.setdefault(m.group(1), {}).setdefault(m.group(2), {}).update(load_json(z, n))
    out, skipped = {}, 0
    for ns, d in sorted(langs.items()):
        en, tw, cn = d.get('en_us', {}), d.get('zh_tw', {}), d.get('zh_cn', {})
        todo = {k: to_tw(cc, cn[k]) for k in en if k not in tw and cn.get(k, '').strip()}
        errors, _ = check_translations.check(en, todo)
        bad = {e.split(': ', 1)[0] for e in errors}
        skipped += len(bad)
        todo = {k: v for k, v in todo.items() if k not in bad}
        if todo:
            out[ns] = todo
    return out, skipped


def main():
    sys.stdout.reconfigure(encoding='utf-8')  # Windows 主控台預設編碼無法輸出中文
    data, skipped = convert(sys.argv[1])
    path = sys.argv[2] if len(sys.argv) > 2 else 'cn2tw.json'
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f'{len(data)} 個命名空間、{sum(map(len, data.values()))} 條；格式不符略過 {skipped} 條 -> {path}')


if __name__ == '__main__':
    main()
