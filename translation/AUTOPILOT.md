# 自動翻譯作業說明

本檔有兩部分：**A. 協調者流程**（分派與合併，給主對話或排程使用）、**B. 譯者規則**（給每個翻譯子代理）。
所有進度都在檔案裡，任何時候中斷都能從 `autopilot.py status` 接續。

## A. 協調者流程（每次喚醒執行一輪）

在 repo 根目錄 `F:/AI-Project/RAD3-1.20.1`，分支 `zh_tw-translation`。

1. `python -I translation/tools/autopilot.py merge` — 合併已交回的譯文（檢查失敗的會列出，請該塊譯者修正或重新分派）。
2. `python -I translation/tools/autopilot.py status` — 看進度與進行中的塊。
   - 「翻譯中」且未逾時：子代理還在跑，**不要重複分派**，本輪結束。
   - 「未分派」或「逾時」：分派（見第 4 步）。
3. 沒有未完成塊時：`python -I translation/tools/autopilot.py next 8` 切下一批（約 8 塊、每塊 ≤1,300 字）。
   輸出「佇列已清空」→ 全部完成，執行第 6 步收尾。
4. 對每個要分派的塊，先 `autopilot.py dispatched chunkNNN ...` 標記，再為每塊開一個背景子代理（general-purpose），提示：
   > 請先閱讀 F:/AI-Project/RAD3-1.20.1/translation/AUTOPILOT.md 的「B. 譯者規則」並嚴格遵守。翻譯 F:/AI-Project/RAD3-1.20.1/translation/work/chunkNNN.en.json，輸出到同資料夾 chunkNNN.zh_tw.json（與 .notes.md）。不要修改 repo 其他檔案。用繁體中文回報。
5. 一批全部合併後：
   - 統一譯名：讀 `translation/work/done/*.notes.md` 中本批新譯名，跨塊衝突時擇一（優先：遊戲內譯名 > 已有譯文 > 多數），
     用小腳本替換 `source/**/zh_tw.json` 中的舊譯名，更新 `translation/glossary.md`。
   - `python -I translation/tools/check_translations.py` 必須「全部通過」。
   - commit（只加 `translation/` 下的檔案），訊息如 `Translate <內容> to zh_tw`，結尾附 Co-Authored-By 行。
6. 收尾：`build_pack.py` 依玩家安裝版本打包驗證；刪除排程（CronList / CronDelete）；向使用者報告。

## B. 譯者規則

輸入 `chunkNNN.en.json`：`_meta` 說明來源與語氣，其餘為「鍵 → 英文」。輸出 `chunkNNN.zh_tw.json`：同樣的鍵 → 繁體中文（台灣用語），**不含 `_meta`**。

### 硬性規則（程式會檢查，不符合不會被合併）
1. 鍵集合與輸入（扣除 `_meta`）完全相同，不可增減或改名。
2. 色碼 `§x` 數量與種類與原文相同，包住對應的中文詞語。
3. 格式符號 `%s`、`%1$s`、`%d`、`%%` 數量與寫法相同；任務書中的百分比寫成 `%%`。
4. `\n`、物品 ID（`minecraft:emerald`）、指令（`/home`）、JEI 搜尋語法（`@modid`）、按鍵、數字不可改。
5. 用 Python 寫檔（`ensure_ascii=False`），寫完用 `json.load` 讀回並自檢以上各項。

### 翻譯風格
- 簡潔自然、不逐字硬譯；名稱短。全形標點；英數與中文之間加半形空格。列表開頭「- 」保留。
- 原版 Minecraft 名詞用官方台灣譯名（Villager 村民、Nether 地獄、End 終界、Sculk 伏聆、Illager 窳民、Enchanting Table 附魔台）。
- **譯名一致**：必須沿用 `F:/AI-Project/RAD3-1.20.1/translation/glossary.md`；遇到物品／機制名稱先 grep
  `translation/source/**/zh_tw.json` 找既有譯名。模組物品若在 `F:/curseforge/minecraft/Instances/Roguelike Adventures and Dungeons 3/mods/`
  的 jar 內有 zh_tw 或 zh_cn（zh_cn 用 `opencc` 的 s2twp 轉繁，再把 下界→地獄、末地→終界、幽匿→伏聆），以遊戲內譯名為準（只讀 jar，不修改）。
- 同系列名稱統一規則（如 X Sword／X Axe → X劍／X斧；材料前綴一致）。
- 模組名稱無通行譯名可保留英文。原文明顯錯字依原意翻譯並記入 notes。
- 上下文：任務書可讀 `config/ftbquests/quests/chapters/*.snbt`（以物件 ID 搜尋）；模組條目可讀該模組 jar 的 en_us 看鄰近條目。

### 交付
- `chunkNNN.zh_tw.json` 與 `chunkNNN.zh_tw.json.notes.md`（新定譯名「英文 → 中文」清單、沒把握的鍵與原因）。
- 回報 100 字內：條數、自檢結果、需與其他塊統一的譯名。
