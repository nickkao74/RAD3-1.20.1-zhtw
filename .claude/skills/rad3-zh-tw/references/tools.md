# 工具一覽（`translation/tools/`）

全部用 `python -I translation/tools/<工具>.py ...` 在 repo 根目錄執行，輸出為繁體中文。

| 工具 | 指令 | 用途 |
|---|---|---|
| `autopilot.py` | `status` | 各來源剩餘條數／字數、工作塊狀態（未分派／翻譯中／逾時／待 merge） |
| | `next [塊數]` | 從佇列切下一批工作塊到 `translation/work/`；已有未完成塊時不切 |
| | `dispatched <塊名>...` | 標記已分派（寫時間戳，45 分鐘後視為逾時） |
| | `merge` | 檢查交回的 `chunkNNN.zh_tw.json`，通過才寫入各來源 `zh_tw.json`，並把塊移到 `work/done/` |
| | `invalidate` | 上游更新後，英文已變更的鍵從 `zh_tw.json` 移除（比對 git HEAD，commit 前執行） |
| | `mods <mods 資料夾>` | 依 `MOD_TARGETS` 從 jar 抽出無中文條目到 `source/mods/<ns>/en_us.json`（略過設定／指令類鍵） |
| `check_translations.py` | （無參數） | 檢查全部 `zh_tw.json`：多餘鍵、色碼、`%s`／`%%` 格式符號 |
| | `merge <來源資料夾> <譯文.json>...` | 檢查外部譯文檔（如審查修正）後合併進該來源 |
| `term_check.py` | `[--only <來源>] [--json <檔>]` | 譯名一致性：英文含 glossary 詞條但譯文未用該譯名的條目 |
| `sync_sources.py` | （無參數） | 從目前的 `config/ftbquests/quests` 與 kubejs/paxi 重抽英文快照，回報各來源進度 |
| `quests_i18n.py` | `extract` / `apply` / `status` | 任務書語言鍵化核心（通常由其他工具呼叫）；鍵格式 `rad3q.<物件ID>.title／subtitle／desc.<行>` |
| `prep_chunks.py` | `<輸出資料夾> <塊數> <章節>...` | 舊版：只切任務書指定章節（現已由 `autopilot.py next` 取代） |
| `cn2tw.py` | `<mods 資料夾> [輸出 json]` | jar 內只有簡中的條目以 OpenCC s2twp 轉繁並套用 `TERMS` 台灣用語替換 |
| `scan_mods.py` | `<實例資料夾> [輸出 md]` | 重算 387 個 jar 的 zh_tw 覆蓋率報告 `translation/reports/mod_lang_status.md` |
| `build_pack.py` | `[版本] [任務書資料夾] [--mods <mods>] [--skip-ns a,b]` | 打包 `translation/dist/RAD3-zh_tw-<版本>.zip`（語言鍵化任務書、kubejs 語言檔、資源包、安裝說明） |

## 調整參數

- 塊大小：`autopilot.py` 的 `WORDS_PER_CHUNK`（1300）、`ENTRIES_PER_CHUNK`（300）。
- 逾時：`STALE_SECONDS`（45 分鐘）。
- 要翻的模組與順序：`MOD_TARGETS`；改了之後執行 `autopilot.py mods <mods>` 重抽。
- 自動轉繁的用語替換：`cn2tw.py` 的 `TERMS`。
- 任務書語氣、模組語氣：`autopilot.py` 的 `TONE`（寫進每塊 `_meta.tone`）。

## 相依

- Python 3.10+；`opencc`（`python -m pip install opencc`，cn2tw 與譯者查遊戲內譯名用）。
- 打包、抽取都只讀實例資料夾，不會修改模組包。
