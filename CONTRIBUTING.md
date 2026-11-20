# 組員協作

公開儲存庫任何人可閱讀與下載。要直接推送需由擁有者另行加入協作者；未加入者可Fork後開Pull Request。此版不擅自邀請組員或傳訊息。

1. 先開Issue描述研究問題、資料期間與待驗證假說。
2. 從`main`建立自己的分支。新原文下載到`.local/`，保留實際發布日期、URL、頁碼與SHA-256。
3. 將自己的研究整理提交到`knowledge/`，附支持與反駁證據。使用`docs/finding-template.md`。
4. 要讓新文件參與檢索，將路徑、標題、類型、公司、可用日期、來源URL與SHA-256加入`catalog.json`的`documents`。可以用`python3 -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('檔案路徑').read_bytes()).hexdigest())"`計算。
5. 新研究晚於舊截止日，預設檢索不會納入。先用`--as-of`明確指定新範圍，討論後另建研究版本，保留舊快照。
6. 執行`python3 rag.py check`與`python3 -m unittest discover -s tests -v`，開Pull Request，寫清楚變更、來源與驗證。提交前檢查`git diff --cached --stat`，確認沒有`.local`或第三方全文。

原工作區擁有者可用`python3 tools/export_workspace.py "/原始研究資料夾"`重新匯出既定資料。匯出會覆寫同名研究文件與catalog，請先提交自己的工作並在分支檢查差異；它不是新資料的自動更新器。
