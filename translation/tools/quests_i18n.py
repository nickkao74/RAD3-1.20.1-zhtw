"""FTB Quests（2001.x）任務書語言鍵化工具。

FTB Quests 1.20.1 版沒有獨立的任務翻譯檔機制，文字直接寫在 snbt 內。
本工具把 title / subtitle / description 換成 `{語言鍵}`（JSON 文字元件則改成
`"translate"`），英文原文抽出成 en_us.json，翻譯則寫在 zh_tw.json，
兩者以資源（kubejs/assets）方式載入；沒翻到的鍵會自動退回英文。

用法:
  python -I translation/tools/quests_i18n.py extract <quests 資料夾> <en_us.json 輸出>
  python -I translation/tools/quests_i18n.py apply   <quests 資料夾> <輸出資料夾>
  python -I translation/tools/quests_i18n.py status  <en_us.json> <zh_tw.json>

語言鍵格式: rad3q.<物件ID>.title / .subtitle / .desc.<行號>
物件 ID 是 FTB Quests 的 16 位十六進位 ID，任務移動或改章節都不會變。
"""
import json
import os
import re
import sys

KEY_PREFIX = 'rad3q'
OBJ_ID_RE = re.compile(r'^\s*id:\s*"([0-9A-F]{16})"\s*$')
FIELD_RE = re.compile(r'^(\s*)(title|subtitle):\s*"((?:[^"\\]|\\.)*)"\s*$')
DESC_INLINE_RE = re.compile(r'^(\s*)description:\s*\[(.*)\]\s*$')
DESC_OPEN_RE = re.compile(r'^\s*description:\s*\[\s*$')
STR_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')
# chapter_groups.snbt 的單行物件: { id: "...", title: "..." }
INLINE_OBJ_RE = re.compile(r'^(\s*)\{\s*id:\s*"([0-9A-F]{16})",\s*title:\s*"((?:[^"\\]|\\.)*)"\s*\}(\s*)$')
KEY_ONLY_RE = re.compile(r'^\{[A-Za-z0-9_.\-]+\}$')
COLOR_RE = re.compile(r'&([0-9a-fk-orA-FK-OR])')


def unescape(s):
    return re.sub(r'\\(.)', r'\1', s)


def escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def to_lang(text):
    """snbt 文字 -> 語言檔值：& 色碼轉 §、% 轉義。"""
    return COLOR_RE.sub(r'§\1', text).replace('%', '%%')


def convert(text, key, out):
    """回傳替換後的 snbt 字串值；需翻譯的英文寫入 out[key]。不需翻譯則回傳 None。"""
    stripped = text.strip()
    if not stripped or KEY_ONLY_RE.match(stripped):
        return None
    if stripped.startswith('{image:') or stripped.startswith('{@'):
        return None
    if stripped[0] in '{[':
        try:
            comp = json.loads(stripped)
        except ValueError:
            comp = None
        if comp is not None:
            counter = [0]

            def walk(node):
                if isinstance(node, list):
                    return [walk(n) for n in node]
                if isinstance(node, dict):
                    node = {k: walk(v) if k in ('extra', 'hoverEvent', 'contents') else v
                            for k, v in node.items()}
                    if isinstance(node.get('text'), str) and node['text'].strip():
                        sub = key if counter[0] == 0 else f'{key}.{counter[0]}'
                        counter[0] += 1
                        out[sub] = to_lang(node.pop('text'))
                        node = {'translate': sub, **node}
                    return node
                return node

            new = walk(comp)
            return json.dumps(new, ensure_ascii=False) if counter[0] else None
    out[key] = to_lang(text)
    return '{' + key + '}'


def process_file(lines, out, file_id):
    """逐行處理單一 snbt；回傳新行列表。"""
    result = list(lines)
    # 以 { } 行追蹤物件層級。有 ID 的物件（章節、任務、子任務、獎勵…）用自身 ID 當鍵；
    # 沒有 ID 的物件（如戰利品表條目）以「上層 ID + .e<序號>」當鍵。
    # 每層: {'id': str|None, 'fields': [(行號, 種類, 描述行序, 子路徑)], 'anon': 匿名子物件數}
    stack = []
    in_desc = None
    for i, line in enumerate(lines):
        s = line.strip()
        if in_desc is not None:
            if s == ']':
                in_desc = None
            elif STR_RE.fullmatch(s) and stack:
                stack[-1]['fields'].append((i, 'desc', in_desc, ''))
                in_desc += 1
            continue
        m = INLINE_OBJ_RE.match(line)
        if m:
            ind, oid, val, eol = m.groups()
            new = convert(unescape(val), f'{KEY_PREFIX}.{oid}.title', out)
            if new is not None:
                result[i] = f'{ind}{{ id: "{oid}", title: "{escape(new)}" }}{eol}'
            continue
        if s.endswith('{'):
            stack.append({'id': None, 'fields': [], 'anon': 0})
            continue
        if s.startswith('}'):
            if not stack:
                continue
            frame = stack.pop()
            if not stack and not frame['id']:
                frame['id'] = file_id
            if frame['id']:
                apply_frame(result, frame, out)
            elif frame['fields']:
                parent = stack[-1]
                tag = f"e{parent['anon']}."
                parent['anon'] += 1
                parent['fields'] += [(li, k, sub, tag + path) for li, k, sub, path in frame['fields']]
            continue
        if not stack:
            continue
        m = OBJ_ID_RE.match(line)
        if m:
            stack[-1]['id'] = m.group(1)
        elif FIELD_RE.match(line):
            stack[-1]['fields'].append((i, 'field', None, ''))
        elif DESC_OPEN_RE.match(line):
            in_desc = 0
        elif DESC_INLINE_RE.match(line):
            stack[-1]['fields'].append((i, 'desc_inline', None, ''))
    return result


def apply_frame(result, frame, out):
    for i, kind, sub, path in frame['fields']:
        base = f"{KEY_PREFIX}.{frame['id']}.{path}"
        line = result[i]
        eol = line[len(line.rstrip('\r\n')):]
        if kind == 'field':
            ind, name, val = FIELD_RE.match(line).groups()
            new = convert(unescape(val), f'{base}{name}', out)
            if new is not None:
                result[i] = f'{ind}{name}: "{escape(new)}"' + eol
        elif kind == 'desc':
            ind = line[:len(line) - len(line.lstrip())]
            val = STR_RE.search(line).group(1)
            new = convert(unescape(val), f'{base}desc.{sub}', out)
            if new is not None:
                result[i] = f'{ind}"{escape(new)}"' + eol
        else:
            ind, body = DESC_INLINE_RE.match(line).groups()
            vals = []
            for n, m in enumerate(STR_RE.finditer(body)):
                v = unescape(m.group(1))
                new = convert(v, f'{base}desc.{n}', out)
                vals.append('"' + escape(new if new is not None else v) + '"')
            result[i] = f'{ind}description: [{", ".join(vals)}]' + eol


def process_text(text, out, file_id):
    return '\n'.join(process_file(text.split('\n'), out, file_id))


def iter_snbt(root):
    for d, _, files in os.walk(root):
        if os.sep + 'lang' in d[len(root):]:
            continue
        for f in sorted(files):
            if f.endswith('.snbt'):
                yield os.path.join(d, f)


def run(root, out_dir=None):
    out = {}
    for path in sorted(iter_snbt(root)):
        with open(path, encoding='utf-8', newline='') as f:
            text = f.read()
        new = process_text(text, out, 'f_' + os.path.splitext(os.path.basename(path))[0])
        if out_dir:
            dest = os.path.join(out_dir, os.path.relpath(path, root))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'w', encoding='utf-8', newline='') as f:
                f.write(new)
    return out


def write_json(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')


def main():
    sys.stdout.reconfigure(encoding='utf-8')  # Windows 主控台預設編碼無法輸出中文
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'extract':
        old = {}
        if os.path.exists(sys.argv[3]):
            with open(sys.argv[3], encoding='utf-8') as f:
                old = json.load(f)
        data = run(sys.argv[2])
        write_json(sys.argv[3], data)
        added = [k for k in data if k not in old]
        changed = [k for k in data if k in old and old[k] != data[k]]
        removed = [k for k in old if k not in data]
        print(f'{len(data)} 條；新增 {len(added)}、變更 {len(changed)}、移除 {len(removed)}')
        for k in changed:
            print('  變更', k)
    elif cmd == 'apply':
        data = run(sys.argv[2], sys.argv[3])
        print(f'已輸出語言鍵化任務書到 {sys.argv[3]}（{len(data)} 條）')
    elif cmd == 'status':
        with open(sys.argv[2], encoding='utf-8') as f:
            en = json.load(f)
        tw = {}
        if os.path.exists(sys.argv[3]):
            with open(sys.argv[3], encoding='utf-8') as f:
                tw = json.load(f)
        done = sum(1 for k in en if tw.get(k))
        print(f'已翻譯 {done}/{len(en)}（{done * 100 // max(len(en), 1)}%）；多餘鍵 {len([k for k in tw if k not in en])}')
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
