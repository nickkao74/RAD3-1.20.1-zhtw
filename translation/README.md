# RAD3 繁體中文化

本資料夾放在上游 repo（dr3ams/RAD3-1.20.1）的 `zh_tw-translation` 分支，
不修改任何上游檔案，只在打包時產生語言鍵化的任務書與語言檔，方便持續跟上游合併。

## 翻譯範圍與來源

| 內容 | 處理方式 | 狀態 |
|---|---|---|
| 模組本體文字（387 個 jar） | 不自己翻：jar 內建 zh_tw ＋ 外部資源包（建議 ModsTranslationPack） | 見 `reports/mod_lang_status.md` |
| FTB Quests 任務書（約 3,750 條、4.5 萬字） | `tools/quests_i18n.py` 語言鍵化，譯文寫 `source/quests/zh_tw.json` | 進行中 |
| KubeJS / Paxi 語言檔（ponder、gearupgrades、endrem 覆寫等約 560 條） | 譯文寫 `source/modpack/<命名空間>/zh_tw.json`，打包成資源包 | 待翻 |
| KubeJS 註冊物品名稱（`.displayName()`，約 180 條） | 同上，`source/modpack/kubejs_registry/` | 待翻 |
| 模組缺漏補翻（選用） | `source/mods/<命名空間>/zh_tw.json`，打包進同一個資源包 | 未開始 |

目前**尚未處理**（需改動上游腳本或檔案，等主要內容完成後再評估）：

- KubeJS 腳本內寫死的英文（tooltip `Text.of`、`player.tell` 等約 2,200 條）
- GuideME 指南 `kubejs/assets/rad3/guides/**/*.md`（49 頁、約 1.25 萬字）
- 任務獎勵物品 NBT 名稱／Lore、任務內成書、地城彩蛋戰利品、技能樹節點 title、獎盃、稱號、里程碑進度
- FancyMenu 主選單按鈕（3 條）；主選單更新日誌是從網路讀取，無法翻譯

## 工作流程

需要 Python 3.10+，不需安裝套件。所有指令在 repo 根目錄執行。

```bash
# 1. 跟上游同步（main 有新提交時）
git fetch origin && git merge origin/main

# 2. 更新英文快照與進度報告
python -I translation/tools/sync_sources.py
git diff translation/source/        # 看哪些英文新增／變更，需要補翻

# 3. 翻譯：編輯 translation/source/**/zh_tw.json（只放已翻的鍵，沒翻的自動退回英文）
#    分工翻譯時，可把章節未翻條目切塊（同一任務不會被拆開）
python -I translation/tools/prep_chunks.py work 4 adventure_begins
#    檢查色碼、%% 與多餘鍵；外部譯文檔可用 merge 檢查後合併
python -I translation/tools/check_translations.py
python -I translation/tools/check_translations.py merge translation/source/quests 譯文.json

# 4. 打包給玩家
python -I translation/tools/build_pack.py 1.0     # → translation/dist/RAD3-zh_tw-1.0.zip
#    加 --mods 時，jar 內只有簡中的條目會用 OpenCC s2twp 自動轉繁中併入資源包
#    （需先 python -m pip install opencc；人工譯文優先，KubeJS/Paxi 覆寫的鍵不自動轉）
#    --skip-ns a,b 可略過指定命名空間（例如想完全交給 ModsTranslationPack 的模組）
python -I translation/tools/build_pack.py 1.0 --mods "F:/curseforge/minecraft/Instances/Roguelike Adventures and Dungeons 3/mods"

# （選用）重新掃描模組 jar 的繁中覆蓋率
python -I translation/tools/scan_mods.py "F:/curseforge/minecraft/Instances/Roguelike Adventures and Dungeons 3"
```

## 任務書語言鍵規則

- 鍵名：`rad3q.<物件ID>.title`、`.subtitle`、`.desc.<行號>`；戰利品表條目無 ID，用 `rad3q.<表ID>.e<序號>.title`。
- 物件 ID 是 FTB Quests 的固定 ID，任務移動不會變；但上游若在描述中**插入或刪除行**，後面行號會位移，
  `sync_sources.py` 會列出「變更」的鍵，請對照英文確認譯文。
- 英文中的 `&` 色碼已轉為 `§`；`%` 已轉為 `%%`（語言檔格式需要），翻譯時請保留這兩種寫法。
- 可點擊跳頁的 JSON 文字元件只抽出 `text`，`clickEvent` 原樣保留。

## 翻譯慣例

- 繁體中文（台灣用語）。保留原文色碼 `§x` 與結尾 `§r`，位置對應譯文中相同詞語。
- 模組／維度等專有名詞優先沿用 ModsTranslationPack 與遊戲內已有譯名，避免任務書與物品名不一致。
- 譯名對照表請記在 `glossary.md`。
