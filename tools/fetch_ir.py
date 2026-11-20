#!/usr/bin/env python3
"""Download known public PDFs locally; verify hashes before optional extraction."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag import ROOT, import_document


def source_key(url):
    parsed = urllib.parse.urlsplit(url)
    params = urllib.parse.parse_qs(parsed.query)
    filename = next((values[0] for key, values in params.items() if key.lower() == 'filename'), None)
    return (filename or urllib.parse.unquote(parsed.path).rsplit('/', 1)[-1]).lower()


def source_rows():
    manifest = json.loads((ROOT / 'data/ir-pdf-manifest.json').read_text(encoding='utf-8'))
    with (ROOT / 'data/ir-events.csv').open(encoding='utf-8-sig') as handle:
        events = list(csv.DictReader(handle))
    by_url = {}
    for event in events:
        for field in ['中文簡報來源', '英文簡報來源']:
            if event[field]:
                by_url.setdefault(source_key(event[field]), []).append(event)
    for item in manifest:
        matches = sorted(by_url.get(source_key(item['url']), []), key=lambda e: e['日期'])
        company = '友達' if '友達' in item['path'] or '/2409/' in item['path'] else '群創'
        when = matches[0]['日期'] if matches else None
        yield {**item, 'company': company, 'available_on': when,
               'title': f"{company} {when or '日期待核'} 官方簡報 {Path(item['path']).name}"}


def main():
    parser = argparse.ArgumentParser(description='官方PDF下載至 .local，預設只列來源')
    parser.add_argument('--download', action='store_true', help='明確要求下載；未加此選項不連網')
    parser.add_argument('--extract', action='store_true', help='以已安裝的 pdftotext 擷取，並匯入本機')
    parser.add_argument('--limit', type=int, default=60)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit 必須為正整數')
    if args.extract and not args.download:
        parser.error('--extract 需搭配 --download')
    converter = shutil.which('pdftotext') if args.extract else None
    if args.extract and converter is None:
        parser.error('請先安裝 Poppler，確認 pdftotext 已在 PATH；或只下載後自行轉成含頁碼文字')
    failures = 0
    for item in list(source_rows())[:args.limit]:
        print(item['title'] + '\n' + item['url'])
        if not args.download:
            continue
        url = urllib.parse.urlsplit(item['url'])
        if url.scheme != 'https' or url.hostname not in ('mopsov.twse.com.tw', 'www.auo.com', 'www.innolux.com'):
            print('略過：未列入的官方下載網域', file=sys.stderr)
            failures += 1
            continue
        folder = ROOT / '.local/downloads' / item['sha256']
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / 'original.pdf'
        try:
            if not dest.exists():
                req = urllib.request.Request(item['url'], headers={'User-Agent': 'panel-finance-rag/1.0'})
                with urllib.request.urlopen(req, timeout=40) as response:
                    raw = response.read(50_000_001)
                if len(raw) > 50_000_000:
                    raise ValueError('來源超過 50 MB')
                if hashlib.sha256(raw).hexdigest() != item['sha256']:
                    raise ValueError('來源已變動或非原始PDF：SHA-256不符，未保存／匯入')
                dest.write_bytes(raw)
            elif hashlib.sha256(dest.read_bytes()).hexdigest() != item['sha256']:
                raise ValueError('本機PDF的SHA-256不符，未擷取')
            if converter and item['available_on']:
                text_file = folder / 'extracted.txt'
                subprocess.run([converter, '-layout', str(dest), str(text_file)], check=True, timeout=60)
                pages = text_file.read_text(encoding='utf-8').split('\f')
                text_file.write_text('\n\n'.join(f'## PDF頁序 {i+1}\n{page}' for i, page in enumerate(pages) if page.strip()), encoding='utf-8')
                import_document(text_file, item['title'], item['available_on'], item['company'], 'primary_text', item['url'])
            elif converter:
                print('發布日期待核，保留PDF但未匯入檢索。', file=sys.stderr)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            print(f'未完成：{exc}', file=sys.stderr)
            failures += 1
    if failures:
        parser.exit(1, f'{failures} 份未完成，請核對來源；工具不繞過存取限制。\n')


if __name__ == '__main__':
    main()
