# RAD3 繁體中文化

本資料夾放在上游 repo（dr3ams/RAD3-1.20.1）的 `zh_tw-translation` 分支，
不修改任何上游檔案，只在打包時產生語言鍵化的任務書與語言檔，方便持續跟上游合併。

## 翻譯範圍與來源

| 內容 | 處理方式 | 狀態 |
|---|---|---|
| 模組本體文字（387 個 jar） | jar 內建 zh_tw；只有簡中的由 `cn2tw.py` 自動轉繁；其餘建議 ModsTranslationPack | 見 `reports/mod_lang_status.md` |
| FTB Quests 任務書（約 3,750 條、4.5 萬字） | `tools/quests_i18n.py` 語言鍵化，譯文寫 `source/quests/zh_tw.json` | 完成 |
| KubeJS / Paxi 語言檔、Ponder、KubeJS 物品名 | `source/modpack/<命名空間>/zh_tw.json`，打包成資源包 | 完成 |
| 無中文的重要模組（`autopilot.py` 的 `MOD_TARGETS`） | `source/mods/<命名空間>/zh_tw.json`，打包進同一個資源包 | 進行中（`autopilot.py status`） |

目前**尚未處理**（需改動上游腳本或檔案，等主要內容完成後再評估）：

- KubeJS 腳本內寫死的英文（tooltip `Text.of`、`player.tell` 等約 2,200 條）
- GuideME 指南 `kubejs/assets/rad3/guides/**/*.md`（49 頁、約 1.25 萬字）
- 任務獎勵物品 NBT 名稱／Lore、任務內成書、地城彩蛋戰利品、技能樹節點 title、獎盃、稱號、里程碑進度
- FancyMenu 主選單按鈕（3 條）；主選單更新日誌是從網路讀取，無法翻譯

## 工作流程

**接續翻譯、分派、統一譯名、審查與上游更新的完整流程，請見 Claude Code skill `.claude/skills/rad3-zh-tw/`**
（在此 repo 開的對話輸入 `/rad3-zh-tw`）。以下是手動操作時的常用指令。

需要 Python 3.10+；自動轉繁需 `opencc`。所有指令在 repo 根目錄執行。
指令中的 `<實例>` 是你電腦上的模組包實例資料夾；個人路徑記錄在 `.claude/skills/rad3-zh-tw/local.md`（gitignore，範本見 `local.example.md`）。

```bash
# 1. 跟上游同步（main 有新提交時）
git fetch upstream && git merge upstream/main   # upstream = dr3ams/RAD3-1.20.1，沒有請先 git remote add upstream <網址>

# 2. 更新英文快照與進度報告
python -I translation/tools/sync_sources.py
git diff translation/source/        # 看哪些英文新增／變更，需要補翻

python -I translation/tools/autopilot.py invalidate   # 英文變了的鍵移除舊譯文，重新排入佇列

# 3. 翻譯：編輯 translation/source/**/zh_tw.json（只放已翻的鍵，沒翻的自動退回英文）
#    分工翻譯用佇列：autopilot.py status / next / merge（詳見 skill）
python -I translation/tools/autopilot.py status
#    檢查色碼、%% 與多餘鍵；譯名一致性；外部譯文檔可用 merge 檢查後合併
python -I translation/tools/term_check.py
python -I translation/tools/check_translations.py
python -I translation/tools/check_translations.py merge translation/source/quests 譯文.json

# 4. 打包給玩家
python -I translation/tools/build_pack.py 1.0     # → translation/dist/RAD3-zh_tw-1.0.zip
#    加 --mods 時，jar 內只有簡中的條目會用 OpenCC s2twp 自動轉繁中併入資源包
#    （需先 python -m pip install opencc；人工譯文優先，KubeJS/Paxi 覆寫的鍵不自動轉）
#    --skip-ns a,b 可略過指定命名空間（例如想完全交給 ModsTranslationPack 的模組）
python -I translation/tools/build_pack.py 1.0 --mods "<實例>/mods"

# （選用）重新掃描模組 jar 的繁中覆蓋率
python -I translation/tools/scan_mods.py "<實例>"
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
