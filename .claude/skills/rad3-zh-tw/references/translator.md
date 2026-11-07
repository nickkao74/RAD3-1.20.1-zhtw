# 譯者規則（RAD3 繁中化）

你負責翻譯一個工作塊。repo 根目錄為目前工作目錄，本機路徑（`<實例>`、`<原版語言檔>`）見 `.claude/skills/rad3-zh-tw/local.md`。只能新增你的兩個輸出檔，**不要修改 repo 任何其他檔案**（包括 glossary、source、tools）。
暫存腳本放在你自己的子資料夾（例如 scratchpad 下 `chunkNNN/`），不要和其他平行譯者共用檔名。

## 輸入與輸出

- 輸入 `translation/work/chunkNNN.en.json`：
  - `_meta.kind`：`quests`（任務書）／`modpack`（模組包語言檔）／`mods`（模組語言檔）
  - `_meta.tone`：語氣說明
  - `_meta.sources`：每個鍵的來源資料夾（同來源已合併的譯文在該資料夾的 `zh_tw.json`）
  - 其餘為「鍵 → 英文」
- 輸出 `translation/work/chunkNNN.zh_tw.json`：同樣的鍵 → 繁體中文（台灣用語），**不含 `_meta`**。
- 輸出 `translation/work/chunkNNN.zh_tw.json.notes.md`：見文末「交付」。

## 硬性規則（程式會檢查，不符合整塊不會被合併）

1. 鍵集合與輸入（扣除 `_meta`）完全相同，不可增減或改名；每條都要有譯文，不可留空。
2. 色碼 `§x` 的數量與種類與原文相同，包住對應的中文詞語（`§6金幣§r`）。
3. 格式符號 `%s`、`%1$s`、`%d`、`%%` 的數量與寫法相同。任務書（kind=quests）裡的百分比一律寫 `%%`。
4. `\n`、物品 ID（`minecraft:emerald`）、標籤（`#rad3:artifact`）、指令（`/home`）、JEI 搜尋語法（`@modid`）、按鍵占位、數字不可改。
5. 用 Python 寫檔（`json.dump(..., ensure_ascii=False, indent=1)`），寫完用 `json.load` 讀回，逐條自檢以上各項。
   repo 內有現成檢查函式可用：
   ```python
   import importlib.util
   spec = importlib.util.spec_from_file_location('ct', 'translation/tools/check_translations.py')
   ct = importlib.util.module_from_spec(spec); spec.loader.exec_module(ct)
   errors, notes = ct.check(en_dict, zh_dict)   # errors 必須為空
   ```

## 查譯名（翻譯前先做）

依序查，越前面越優先：

1. **遊戲內譯名**：該模組 jar（在 `<實例>/mods/`，唯讀）
   的 `assets/<ns>/lang/zh_tw.json`；沒有則讀 `zh_cn.json`，用 `opencc`（`opencc.OpenCC('s2twp')`）轉繁，
   再替換台灣原版用語：下界→地獄、末地→終界、幽匿→伏聆、臺階→半磚、樓梯→階梯、刷怪蛋→生怪蛋、鍬→鏟、重灌→重裝。
   提到別的模組的物品時，去查那個模組的 jar。
2. **1.20.1 原版 zh_tw**：`<原版語言檔>`（JSON）。
   例：Slowness 緩速、Looting 掠奪、Netherite 獄髓、Shulker 界伏、Warden 伏守者、Biome 生態域、Villager 村民、Nether 地獄。
3. **譯名表**：`translation/glossary.md`（必須沿用）。
4. **既有譯文**：grep `translation/source/**/zh_tw.json`（英文在同資料夾 `en_us.json` 同鍵）找同一物品／機制的譯法，特別是同模組的 `zh_tw.json`。

建議先寫一個小查詢腳本：輸入英文詞 → 列出上述四個來源的命中，避免逐條手查。

## 翻譯風格

- 簡潔自然，不逐字硬譯；名稱短。全形標點（，。！？：「」）；英數與中文之間加半形空格。列表開頭「- 」保留。
- 同系列名稱用同一規則：材料前綴一致（「X劍／X斧」）、礦物照原版格式（「X原礦」「X原礦方塊」）、半磚／階梯／牆。
- 模組名稱無通行譯名可保留英文（如 Curios、JEI、ParCool）。
- **任務書**：說明清楚；劇情（日誌、信件、對白）用有文學感的敘事口吻，人名地名全篇一致。提到章節用「「章節中文名」章節」。
- **語言檔**：物品名短而一致；tooltip 一行一意，避免過長。進度標題的雙關可意譯成中文雙關。
- 原文明顯錯字依原意翻譯並記入 notes。
- 上下文：任務書可在 `config/ftbquests/quests/chapters/*.snbt` 以物件 ID（鍵的第二段）搜尋；模組條目可看 jar 內 en_us 的鄰近條目。

## 交付

`chunkNNN.zh_tw.json.notes.md` 內容：
1. **新定譯名**：「英文 → 中文（來源：遊戲內／原版／glossary／既有譯文／自訂）」清單。
2. **需跨塊統一**：你發現和既有譯文或 glossary 衝突的地方，寫出你的選擇與理由。
3. **沒把握的鍵**：鍵名與原因。

最後回報（100 字內）：條數、自檢結果、需協調者統一的譯名。
