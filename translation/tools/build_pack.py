"""打包繁中化附加包，給一起玩的人解壓到模組包資料夾使用。

輸出 translation/dist/RAD3-zh_tw-<版本>.zip，內容:
  config/ftbquests/quests/            語言鍵化後的任務書（覆蓋原檔）
  kubejs/assets/rad3_i18n/lang/       任務書 en_us（英文退回用）與 zh_tw
  resourcepacks/RAD3-zh_tw.zip        模組包自帶文字與模組補充翻譯的資源包
  RAD3繁中化-安裝說明.txt

用法: python -I translation/tools/build_pack.py [版本字串] [任務書資料夾] [--mods <mods 資料夾>] [--skip-ns a,b]
  --mods     指定時把 jar 內只有簡中的條目以 OpenCC s2twp 轉繁中併入資源包（需 pip install opencc）
  --skip-ns  自動轉換時略過的命名空間（例如已由 ModsTranslationPack 涵蓋的模組）
  優先順序: source/mods 人工譯文 > source/modpack 人工譯文 > 自動轉換；
  source/modpack/<ns>/en_us.json 中的鍵（KubeJS/Paxi 覆寫）一律不用自動轉換。
  任務書資料夾預設為 repo 的 config/ftbquests/quests；玩家實際安裝的版本若與 repo 不同，
  請指向該版本的任務書（例如 CurseForge 實例的 config/ftbquests/quests），避免覆蓋成別版任務。
"""
import datetime
import glob
import importlib.util
import io
import json
import os
import shutil
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TR = os.path.join(ROOT, 'translation')
SRC = os.path.join(TR, 'source')
PACK_FORMAT = 15  # 1.20.1

_spec = importlib.util.spec_from_file_location('quests_i18n', os.path.join(TR, 'tools', 'quests_i18n.py'))
quests_i18n = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(quests_i18n)
_spec = importlib.util.spec_from_file_location('cn2tw', os.path.join(TR, 'tools', 'cn2tw.py'))
cn2tw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cn2tw)


def load(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def to_bytes(data):
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def translated(src_dir):
    """只取英文快照裡仍存在、且有譯文的鍵。"""
    en = load(os.path.join(src_dir, 'en_us.json'))
    tw = load(os.path.join(src_dir, 'zh_tw.json'))
    return {k: v for k, v in tw.items() if v and (not en or k in en)}


def build_resourcepack(auto=None):
    langs = {}
    for ns, data in (auto or {}).items():
        overridden = load(os.path.join(SRC, 'modpack', ns, 'en_us.json'))
        data = {k: v for k, v in data.items() if k not in overridden}
        if data:
            langs[ns] = dict(data)
    for kind in ('modpack', 'mods'):
        for d in sorted(glob.glob(os.path.join(SRC, kind, '*'))):
            data = translated(d)
            if data:
                langs.setdefault(os.path.basename(d), {}).update(data)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('pack.mcmeta', json.dumps(
            {'pack': {'pack_format': PACK_FORMAT, 'description': 'RAD3 繁體中文化'}},
            ensure_ascii=False, indent=2))
        icon = os.path.join(TR, 'pack.png')
        if os.path.exists(icon):
            z.write(icon, 'pack.png')
        for ns, data in sorted(langs.items()):
            z.writestr(f'assets/{ns}/lang/zh_tw.json', to_bytes(data))
    return buf.getvalue(), sum(len(v) for v in langs.values())


def main():
    sys.stdout.reconfigure(encoding='utf-8')  # Windows 主控台預設編碼無法輸出中文
    args, opts = [], {}
    it = iter(sys.argv[1:])
    for a in it:
        if a in ('--mods', '--skip-ns'):
            opts[a] = next(it)
        else:
            args.append(a)
    auto, skipped = {}, 0
    if '--mods' in opts:
        auto, skipped = cn2tw.convert(opts['--mods'])
        for ns in opts.get('--skip-ns', '').split(','):
            auto.pop(ns.strip(), None)
    version = args[0] if args else datetime.date.today().strftime('%Y%m%d')
    stage = os.path.join(TR, 'dist', 'stage')
    shutil.rmtree(stage, ignore_errors=True)
    quests_src = args[1] if len(args) > 1 else os.path.join(ROOT, 'config', 'ftbquests', 'quests')
    quests_out = os.path.join(stage, 'config', 'ftbquests', 'quests')
    quest_en = quests_i18n.run(quests_src, quests_out)
    quest_tw = {k: v for k, v in load(os.path.join(SRC, 'quests', 'zh_tw.json')).items() if v and k in quest_en}
    rp, rp_count = build_resourcepack(auto)

    out = os.path.join(TR, 'dist', f'RAD3-zh_tw-{version}.zip')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for d, _, files in os.walk(quests_out):
            for f in files:
                p = os.path.join(d, f)
                z.write(p, os.path.relpath(p, stage).replace(os.sep, '/'))
        z.writestr('kubejs/assets/rad3_i18n/lang/en_us.json', to_bytes(quest_en))
        z.writestr('kubejs/assets/rad3_i18n/lang/zh_tw.json', to_bytes(quest_tw))
        z.writestr('resourcepacks/RAD3-zh_tw.zip', rp)
        z.write(os.path.join(TR, 'INSTALL.txt'), 'RAD3繁中化-安裝說明.txt')
    shutil.rmtree(stage, ignore_errors=True)
    print(f'{out}\n  任務書譯文 {len(quest_tw)}/{len(quest_en)}；資源包譯文 {rp_count} 條（{len(rp) // 1024} KB）')
    if auto:
        print(f'  自動簡轉繁 {len(auto)} 個命名空間、{sum(map(len, auto.values()))} 條（格式不符略過 {skipped} 條；'
              f'與人工譯文重疊者以人工為準）')


if __name__ == '__main__':
    main()
