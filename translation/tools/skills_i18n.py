"""Passive Skill Tree 技能資料包語言鍵化工具。

RAD3 的技能定義在 config/paxi/datapacks/rad3-compat/data/skilltree/skills/*.json，
其中 "title" 是寫死的英文（模組用 Component.literal 顯示，不讀語言檔），
"description" 是文字元件，"text" 也是寫死的英文。

本工具：
  - 移除 "title"，讓模組改用語言鍵 skill.<命名空間>.<路徑>.name 顯示標題；
  - description 中含英文的 "text" 改成 {"translate": 鍵, "fallback": 原文}；
  - 英文原文抽成 en_us.json（打包到 kubejs/assets/rad3_i18n/lang，英文退回用），
    譯文寫在 translation/source/skills/zh_tw.json。

用法:
  python -I translation/tools/skills_i18n.py extract [skills 資料夾] [en_us.json 輸出]
  python -I translation/tools/skills_i18n.py apply   <skills 資料夾> <輸出資料夾>

語言鍵格式: skill.<ns>.<路徑>.name（標題，模組固定格式）、rad3s.<路徑>.desc.<序號>（說明）
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SKILLS_DIR = os.path.join(ROOT, 'config', 'paxi', 'datapacks', 'rad3-compat', 'data', 'skilltree', 'skills')
EN_OUT = os.path.join(ROOT, 'translation', 'source', 'skills', 'en_us.json')
# 資料包內的相對路徑（打包時放回同一位置覆蓋原檔）
DATAPACK_REL = 'config/paxi/datapacks/rad3-compat/data/skilltree/skills'
LETTER_RE = re.compile(r'[A-Za-z]')


def to_lang(text):
    return text.replace('%', '%%')


def convert(skill, path):
    """回傳 (轉換後的技能 dict, {鍵: 英文})；不需轉換時 dict 為 None。"""
    out = {}
    ns = skill.get('id', '').partition(':')[0] or 'skilltree'
    changed = False
    title = skill.get('title')
    if isinstance(title, str) and title.strip():
        out[f'skill.{ns}.{path}.name'] = to_lang(title)
        changed = True
    counter = [0]

    def walk(node):
        if isinstance(node, list):
            return [walk(n) for n in node]
        if not isinstance(node, dict):
            return node
        node = {k: walk(v) if k in ('extra', 'with') else v for k, v in node.items()}
        text = node.get('text')
        if isinstance(text, str) and LETTER_RE.search(text):
            key = f'rad3s.{path}.desc.{counter[0]}'
            counter[0] += 1
            out[key] = to_lang(text)
            node = {'translate': key, 'fallback': to_lang(text),
                    **{k: v for k, v in node.items() if k != 'text'}}
        return node

    new = dict(skill)
    if changed:
        del new['title']
    if isinstance(skill.get('description'), list):
        new['description'] = walk(skill['description'])
    return (new if changed or counter[0] else None), out


def iter_skills(skills_dir):
    for p in sorted(glob.glob(os.path.join(skills_dir, '*.json'))):
        with open(p, encoding='utf-8-sig') as f:
            yield os.path.splitext(os.path.basename(p))[0], json.load(f)


def extract(skills_dir):
    en = {}
    for path, skill in iter_skills(skills_dir):
        en.update(convert(skill, path)[1])
    return en


def apply(skills_dir, out_dir):
    """把轉換後的技能檔寫到 out_dir，回傳 en_us 字典。"""
    en = {}
    os.makedirs(out_dir, exist_ok=True)
    for path, skill in iter_skills(skills_dir):
        new, keys = convert(skill, path)
        en.update(keys)
        if new is not None:
            with open(os.path.join(out_dir, path + '.json'), 'w', encoding='utf-8', newline='\n') as f:
                json.dump(new, f, ensure_ascii=False, indent=2)
                f.write('\n')
    return en


def dump(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    args = sys.argv[1:]
    if not args or args[0] not in ('extract', 'apply'):
        print(__doc__)
        sys.exit(1)
    if args[0] == 'extract':
        skills_dir = args[1] if len(args) > 1 else SKILLS_DIR
        out = args[2] if len(args) > 2 else EN_OUT
        en = extract(skills_dir)
        dump(out, en)
        print(f'技能資料包：抽出 {len(en)} 條 -> {os.path.relpath(out, ROOT)}')
    else:
        en = apply(args[1], args[2])
        print(f'技能資料包：語言鍵化 {len(en)} 條 -> {args[2]}')


if __name__ == '__main__':
    main()
