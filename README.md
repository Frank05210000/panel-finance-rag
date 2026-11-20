# 光電轉型財務研究 RAG

群創為主要個案、友達為比較對象。讓組員下載同一份研究，在自己的電腦用 AI 工具提問、查來源、提出可驗證的假說。

**研究資料截止：2026-11-15（Asia/Taipei）。** 既有研究的最新實績採 2026Q3／2026M9；2027 數字屬課堂情境，並非公司財測。近兩年法說會索引範圍為 **2024-11-15 至 2026-11-15**。公開專案整理日為 2026-11-20，沒有因此補入較新的研究資料。

## 組員開始使用

1. 在 GitHub 按 **Code → Download ZIP** 並解壓，或執行：

   ```bash
   git clone https://github.com/Frank05210000/panel-finance-rag.git
   cd panel-finance-rag
   ```

2. 用可讀取本機專案的 AI 工具開啟這個資料夾。Codex 可使用根目錄的 `AGENTS.md`；其他工具請把 [AI 研究指引](AGENTS.md) 貼到專案指令。純聊天工具則先執行下方 `context`，將輸出貼進對話。

3. 貼上這段開始：

   > 請先閱讀 AGENTS.md 與 README.md，執行 `python3 rag.py check`。接著針對我的問題執行 `python3 rag.py context "問題"`，閱讀引用片段與必要原始表格再回答。每個重要判斷附檔案與行號，區分實績、研究推論、情境假設與資料缺口。

4. 試問：「群創獲利改善中，哪些可能來自本業，哪些來自資產處分？請列出支持與反駁證據。」更多問題見 [研究問題](docs/questions.md)。

## 不裝套件即可檢索

需要 Python 3.10 以上。Windows 若沒有 `python3` 指令，可改用 `py -3`。

```bash
python3 rag.py check
python3 rag.py search "2027 EPS 基準情境有哪些假設？"
python3 rag.py context "群創營業現金流與資本支出有何變化？" --company 群創
python3 rag.py context "友達轉型與群創有哪些差別？" --top 8
```

`search` 回傳附行號的證據；`context` 將證據和研究規則組成可交給 AI 的提示。**生成答案由你使用的 AI 工具完成**，本程式本身不呼叫付費 API、不會自動連網。這是一個可實際使用的 RAG 檢索層與專案知識庫，沒有內建聊天模型或語意向量模型；檢索使用中英文字詞／中文字元雙連字的 BM25。對同義改寫較弱，必要時換用財報原詞。AI 工具自己的資料傳送與費用依其設定。

## 有哪些資料

| 位置 | 內容 |
|---|---|
| `knowledge/research.md` | 原詳細版完整研究報告與來源標記 |
| `knowledge/verification.md` | 原研究的驗證範圍、已知缺口 |
| `knowledge/ir-research.md` | 歷年法說會研究整理 |
| `knowledge/financials/` | 各公司各期間財務值、單位、來源、口徑 |
| `knowledge/workbook/` | 14 工作表的儲存格位置、公式、保存時數值 |
| `models/financial-analysis.xlsx` | 原詳細版 Excel，含 EPS 情境、敏感度、資本公積等 |
| `data/` | 財務表、長期營收表、來源清單、62 筆近兩年場次與 60 份 PDF 索引 |
| `catalog.json` | 文件類型、研究截止、來源及 SHA-256 |
| `.local/` | 自己下載／匯入的原文及未校對逐字稿，Git 忽略 |

Excel 是原研究快照；匯出的公式／值未在此次重新計算。工作簿中的第三方原文連結及封存路徑沿用當時記錄，後者不代表公開版包含該檔。修改工作簿後需自行重算及更新文字匯出，AI 不能把舊快取當作新模型結果。

## 增加原文及逐字稿

公開版收錄研究整理、財務事實與來源指引。第三方年報、簡報全文、影片、新聞全文與完整逐字稿保留原權利，不隨本專案重新散布。原始完整工作區的影音、轉錄模型、執行環境與暫存也不在版本庫內。

列出官方 PDF 來源（不連網）：

```bash
python3 tools/fetch_ir.py --limit 3
```

下載官方 PDF 到自己電腦，驗證保存時的 SHA-256；若已安裝 Poppler 的 `pdftotext`，可同時擷取有頁序的文字：

```bash
python3 tools/fetch_ir.py --download --extract --limit 3
python3 rag.py context "車用業務如何轉型？" --include-local
```

來源可能改版或拒絕下載；下載程式會報告失敗，不繞過限制。若有原始完整工作區，可匯入其已有的簡報文字與 15 場含時間戳逐字稿：

```bash
python3 tools/import_workspace.py "/你的原始研究資料夾"
```

一般文字也能逐份匯入：

```bash
python3 rag.py import "/你的資料/官方原文.txt" --title "群創某場官方法說簡報" --available-on 2026-08-18 --company 群創 --kind primary_text --source-url "https://www.innolux.com/"
```

請使用實際文件網址與確認的公開日期。語音逐字稿應改用 `--kind asr_unverified`。預設查詢不包含 `.local`；加 `--include-local` 才納入。新增日期晚於 2026-11-15 的資料會被預設截止日排除；欲研究較新期間，需明確提供 `--as-of YYYY-MM-DD` 並在研究結論說明新範圍。

本版 `available_on` 對公開研究文件採用研究快照的證據截止日，並非原文逐份首次發布日。`--as-of` 是文件日期篩選，不能當成完整的歷史時點回測。詳細資料規則見 [資料說明](docs/data.md)。

## 一起研究

以 Issue 記錄問題、假說及缺少資料，用分支與 Pull Request 提交新整理。可用 [發現紀錄範本](docs/finding-template.md)，附來源、公式、支持與反例。共同協作規則見 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
python3 -m unittest discover -s tests -v
```

程式與新寫的使用文件採 [MIT](LICENSE)；原研究成果與第三方資料的權利範圍見 [資料權利說明](DATA_RIGHTS.md)。

Codex 指令檔格式參考 [OpenAI 官方 AGENTS.md 文件](https://learn.chatgpt.com/docs/agent-configuration/agents-md#layer-project-instructions)。
