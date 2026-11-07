---
name: rad3-zh-tw
description: RAD3（Roguelike Adventures and Dungeons 3）模組包繁體中文化的協調流程——接續進度、切塊並分派子代理翻譯、合併檢查、統一譯名、品質審查、跟上游更新、打包給玩家。當使用者要繼續／接手 RAD3 翻譯、分派翻譯工作、統一或審查譯名、上游更新後補翻、或打包繁中化附加包時使用。
---

# RAD3 繁中化協調流程

你是**協調者**：不自己逐條翻譯，而是用 `translation/tools/` 的工具管理佇列、派子代理翻譯、合併、統一譯名、審查品質並 commit。
所有進度都存在檔案裡，任何對話都能從中斷處接手。

- Repo：`F:/AI-Project/RAD3-1.20.1`，分支 `zh_tw-translation`（上游 `origin/main` 是 dr3ams/RAD3-1.20.1）。
- 模組包實例（唯讀，取 jar 與原版語言檔用）：`F:/curseforge/minecraft/Instances/Roguelike Adventures and Dungeons 3`
- 所有指令在 repo 根目錄執行；Python 一律加 `-I`。回覆使用者用繁體中文（台灣用語）。

## 檔案地圖

| 路徑 | 用途 |
|---|---|
| `translation/source/quests/` | 任務書：`en_us.json`（由 snbt 抽出）＋ `zh_tw.json`（譯文） |
| `translation/source/modpack/<ns>/` | 模組包自帶語言檔（KubeJS、Paxi 覆寫、Ponder、KubeJS 物品名 `kubejs_registry`） |
| `translation/source/mods/<ns>/` | 需自己翻的模組（jar 內無繁中、無簡中）；清單在 `autopilot.py` 的 `MOD_TARGETS` |
| `translation/work/` | 進行中的工作塊（gitignore）；`done/` 保存已合併塊與譯者 notes |
| `translation/glossary.md` | 譯名表（唯一權威來源） |
| `references/translator.md`（本 skill） | 給翻譯子代理的規則 |
| `references/reviewer.md`（本 skill） | 給審查子代理的規則 |
| `references/tools.md`（本 skill） | 每個工具的用途與參數 |

只有 jar 內只有簡中的模組不用人工翻：`build_pack.py --mods` 會用 `cn2tw.py`（OpenCC s2twp + 台灣原版用語替換）自動轉繁。

## 每輪流程

### 0. 開場確認
```bash
git status --short && git log --oneline -3
python -I translation/tools/autopilot.py status
```
工作目錄有未 commit 的譯文先處理（通常是上一輪合併後沒 commit：跑第 5 步檢查後 commit）。

### 1. 合併已交回的譯文
```bash
python -I translation/tools/autopilot.py merge
```
檢查失敗的塊會列出錯誤且不合併：請原子代理修正（若還在這個對話中可用 SendMessage），否則刪掉該塊的 `.zh_tw.json` 重新分派。

### 2. 決定要不要切新塊
看 `status` 下半部的工作塊狀態：
- **翻譯中、未逾時**：已有子代理在跑，**不要重複分派**，本輪到此結束（或等通知）。
- **未分派／逾時**（逾時 45 分鐘，例如對話中斷或額度用完）：直接重新分派這些塊（第 3 步）。別的對話開的子代理無法接續，一律重派。
- **沒有任何未完成塊**：切下一批
  ```bash
  python -I translation/tools/autopilot.py next 8
  ```
  輸出「佇列已清空」→ 跳到第 7 步收尾。

佇列順序固定：任務書 → 模組包語言檔 → `MOD_TARGETS` 順序的模組（長篇的 araxers_bestiary、meed 最後）。
每塊 ≤1,300 英文字或 ≤300 條；任務書同一任務不會被拆開。

### 3. 分派翻譯子代理
先標記，再為**每塊開一個背景子代理**（general-purpose，同一則訊息平行發出，一批不超過 8 個）：
```bash
python -I translation/tools/autopilot.py dispatched chunk041 chunk042 ...
```
子代理提示（只換塊名）：
> 請先閱讀 F:/AI-Project/RAD3-1.20.1/.claude/skills/rad3-zh-tw/references/translator.md 並嚴格遵守。翻譯 F:/AI-Project/RAD3-1.20.1/translation/work/chunkNNN.en.json，輸出到同資料夾 chunkNNN.zh_tw.json（與 chunkNNN.zh_tw.json.notes.md）。不要修改 repo 其他檔案。用繁體中文回報。

子代理回報時，記下它提到「需要跨塊統一」的譯名，留到第 4 步一起處理。全部交回後回到第 1 步合併。

### 4. 統一譯名（每批合併後必做）
1. 讀本批的 `translation/work/done/chunkNNN.zh_tw.json.notes.md`，列出新譯名與跨塊衝突。
2. 跑一致性檢查：
   ```bash
   python -I translation/tools/term_check.py
   ```
3. 衝突時擇一，優先順序：**遊戲內譯名**（jar 內 zh_tw，或 zh_cn 經 cn2tw 轉繁）＞ **1.20.1 原版 zh_tw** ＞ **glossary 既有譯名** ＞ 多數用法。
   原版語言檔：`F:/curseforge/minecraft/Install/assets/objects/ea/ea26c1cee4ef2006eb3ac010b8489399ff6e5639`（JSON）。
4. 用小 Python 腳本對 `translation/source/**/zh_tw.json` 做替換。**只在英文原文含該詞的鍵上替換**（以 `en_us.json` 同鍵判斷），避免誤傷一般用詞。
   寫回格式：`json.dump(..., ensure_ascii=False, indent=2, sort_keys=True)` 加結尾換行。
5. 把新定案的譯名加進 `translation/glossary.md`（表格三欄：英文｜繁中｜備註；按英文排序）。
   一般字也會出現的詞（如 Clues、Forgotten）在備註寫「不檢查」，避免 term_check 誤報。
6. 若是自動轉繁產生的系統性用詞問題（如「下界」→「地獄」），加到 `translation/tools/cn2tw.py` 的 `TERMS`。

### 5. 檢查與 commit
```bash
python -I translation/tools/check_translations.py      # 必須「全部通過」
git add translation .claude/skills/rad3-zh-tw
git commit -m "Translate <內容> to zh_tw" -m "Co-Authored-By: ..."
```
只加 `translation/` 與本 skill；不要動上游檔案（config/、kubejs/ 等）。

### 6. 品質審查（每 2～3 批，或使用者要求時）
挑最近合併的來源，開 1～2 個審查子代理：
> 請先閱讀 F:/AI-Project/RAD3-1.20.1/.claude/skills/rad3-zh-tw/references/reviewer.md 並嚴格遵守。審查來源 `<translation/source/mods/xxx>`（或任務書鍵前綴清單），輸出修正檔 F:/AI-Project/RAD3-1.20.1/translation/work/review_<名稱>.zh_tw.json 與 .notes.md。不要修改 repo 其他檔案。

審查交回後：
```bash
python -I translation/tools/check_translations.py merge translation/source/<來源> translation/work/review_<名稱>.zh_tw.json
```
再跑第 4、5 步。

### 7. 收尾與打包
```bash
python -I translation/tools/build_pack.py <版本> "<實例>/config/ftbquests/quests" --mods "<實例>/mods"
```
- 任務書資料夾要用**玩家實際安裝的版本**，否則會蓋成別版任務。
- 產物在 `translation/dist/RAD3-zh_tw-<版本>.zip`；把安裝方式（`translation/INSTALL.txt`）一起告訴使用者。
- 若有設排程（CronCreate），佇列清空後刪除。

## 跟上游更新

```bash
git fetch origin && git merge origin/main
python -I translation/tools/sync_sources.py                          # 重抽任務書與模組包英文
python -I translation/tools/autopilot.py mods "<實例>/mods"           # 模組更新時重抽模組英文
python -I translation/tools/autopilot.py invalidate                  # 英文變了的鍵移除舊譯文 → 重新排入佇列
python -I translation/tools/scan_mods.py "<實例>"                     # （選用）重算 jar 繁中覆蓋率報告
git diff --stat translation/source/
```
`invalidate` 比對工作目錄與 git HEAD 的 `en_us.json`，必須在 commit 這些英文快照**之前**執行。之後照「每輪流程」補翻。
任務書描述若有插入／刪除行，後續行號鍵會位移，`invalidate` 會把位移後內容不同的鍵都排回重翻。

## 長時間自動執行

使用者要求「自動繼續到完成」時：
- 可用 CronCreate 設每 30 分鐘一次的喚醒（避開整點與半點，如 `17,47 * * * *`），提示內容：「依 rad3-zh-tw skill 執行一輪協調流程」。排程只存在於目前對話、7 天失效。
- 額度用完時子代理會失敗；恢復後在**同一個對話**可用 SendMessage 讓原子代理接續，否則重派該塊。
- 使用者說「停止並保存」：CronDelete 排程 → TaskStop 所有翻譯子代理 → `merge` 已交回的塊 → `rm translation/work/chunk*.dispatched`（未完成塊改回「未分派」）→ 檢查並 commit。

## 品質原則（協調者把關）

- 譯名一致比文采重要：同一物品在任務書、物品名、tooltip 必須同名。
- 模組物品先查遊戲內譯名；沒有才自訂，並寫進 glossary。
- 子代理說「沒把握」的條目，合併後抽查；明顯錯譯就直接改 `zh_tw.json`。
- 不要為了通過檢查刪除色碼或格式符號；`check_translations.py` 擋下的一律修正後再合併。
