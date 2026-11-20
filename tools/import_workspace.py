#!/usr/bin/env python3
"""Add archived third-party text to .local only, using known event metadata."""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag import ROOT, import_document


def main():
    parser = argparse.ArgumentParser(description='將已保存的法說會文字匯入本機，不加入公開資料')
    parser.add_argument('workspace', type=Path)
    args = parser.parse_args()
    base = args.workspace.resolve() / 'research/法說會近兩年'
    with (ROOT / 'data/ir-events.csv').open(encoding='utf-8-sig') as handle:
        rows = list(csv.DictReader(handle))
    paths = set()
    for row in rows:
        folder = row.get('本地影音資料夾')
        if not folder:
            continue
        path = base / folder / '逐字稿_含時間戳.md'
        if path.is_file():
            paths.add(import_document(path, f"{row['公司']} {row['日期']} 法說會含時間戳逐字稿（未校對）",
                                      row['日期'], row['公司'], 'asr_unverified', row['公開錄影網址']))
    # The PDF text filenames share the basename of the archived PDF.
    from fetch_ir import source_rows
    for row in source_rows():
        path = base / Path(row['path']).with_suffix('.txt')
        if path.is_file() and row['available_on']:
            paths.add(import_document(path, row['title'], row['available_on'], row['company'], 'primary_text', row['url']))
    print(f'已匯入 {len(paths)} 份本機文字（依內容及出處去重）；查詢時加 --include-local。匯入不會改變研究截止日。')


if __name__ == '__main__':
    main()
