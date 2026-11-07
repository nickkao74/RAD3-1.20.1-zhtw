# 審查者規則（RAD3 繁中化）

你負責審查已合併的譯文並提出修正。repo 根目錄為目前工作目錄。
只能新增你的兩個輸出檔，**不要修改 repo 任何其他檔案**。

## 輸入

協調者會指定要審查的來源，例如 `translation/source/mods/landsoficaria`：
英文在 `en_us.json`，譯文在 `zh_tw.json`。也可能指定任務書的一組鍵。

先跑一致性檢查取得線索：
```bash
python -I translation/tools/term_check.py --only <來源，如 mods/landsoficaria> --json <你的暫存路徑>/terms.json
```

## 審查重點（依重要性）

1. **錯譯**：意思錯、主詞受詞顛倒、數值或條件寫反、否定句翻反。
2. **譯名不一致**：同一物品／機制在本來源或其他來源（任務書、`modpack/kubejs_registry` 物品名）譯法不同；
   未依 `translation/glossary.md`、遊戲內譯名或 1.20.1 原版 zh_tw（查法見 translator.md「查譯名」）。
   term_check 的結果要逐條判斷：一般用詞的誤報不改。
3. **漏譯**：殘留應翻譯的英文（模組名、刻意保留的專有名詞除外）。
4. **格式**：色碼包錯詞、全半形標點混用、英數與中文之間缺空格、列表符號遺失。
5. **通順**：明顯的翻譯腔或過長的 tooltip。只改真的不順的，不要為了個人偏好重寫。

不要改動正確的譯文；沒有問題就輸出空物件 `{}`。

## 輸出

- `translation/work/review_<名稱>.zh_tw.json`：**只放要修正的鍵** → 修正後的完整譯文。
  必須通過與譯者相同的硬性規則（色碼、`%s`／`%%`、`\n` 與原文一致；見 translator.md），寫完用 `json.load` 讀回並用
  `translation/tools/check_translations.py` 的 `check()` 自檢。
- `translation/work/review_<名稱>.zh_tw.json.notes.md`：
  1. 每條修正：鍵、原譯 → 新譯、理由（錯譯／不一致／漏譯／格式／通順）。
  2. **建議加入 glossary 的譯名**（英文｜繁中｜備註）。
  3. 影響其他來源、需要協調者全域替換的譯名（例如任務書也要跟著改的物品名）。

最後回報（100 字內）：審查條數、修正條數、主要問題類型。
