#!/usr/bin/env python3
"""Export an explicit allowlist from the original workspace. Never copy raw media."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = '2026-11-15'
LABELS = dict(revenue='營收', cost='營業成本', gross='毛利', opex='營業費用', op='營業利益',
              nonop='業外收支', pretax='稅前淨利', tax='所得稅費用', net='合併淨利',
              parent='歸屬母公司淨利', eps='每股盈餘EPS', cash='現金', ca='流動資產', ppe='不動產廠房設備',
              intangibles='無形資產', goodwill='商譽', assets='總資產', shortdebt='短期借款',
              currentlongdebt='一年內到期長期借款', longdebt='長期借款', cl='流動負債',
              liabilities='總負債', equity='總權益', parent_equity='歸母權益', cfo='營業活動現金流',
              cfi='投資活動現金流', cff='籌資活動現金流', capex='取得PPE支出',
              ppe_proceeds='出售PPE收現', held_proceeds='待出售資產收現', held_advance='出售資產預收款',
              acquisition_net='併購淨支出', intangible_capex='無形資產支出',
              cash_interest_received='收取利息', cash_dividends_received='收取股利',
              cash_interest_paid='支付利息', cfo_ex_interest_dividends='排除利息股利的營業現金流', da='折舊攤銷')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace', type=Path, help='原始研究資料夾，含 outputs/v3 與 research')
    args = parser.parse_args()
    src = args.workspace.resolve()
    docs, assets = [], []

    def record(path, title, kind, companies=None, urls=None, original=None, document=True):
        raw = path.read_bytes()
        item = dict(path=path.relative_to(ROOT).as_posix(), title=title, kind=kind,
                    companies=companies if companies is not None else ['群創', '友達'],
                    available_on=CUTOFF, sha256=hashlib.sha256(raw).hexdigest(),
                    source_urls=urls or [], original_workspace_path=original)
        (docs if document else assets).append(item)

    def copy(relative, dest, title, kind='team_analysis', document=True):
        out = ROOT / dest
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.suffix in ('.md', '.csv', '.json'):
            # Match .gitattributes so hashes remain valid after a fresh clone on Windows.
            text = (src / relative).read_bytes().decode('utf-8')
            out.write_bytes(text.replace('\r\n', '\n').replace('\r', '\n').encode('utf-8'))
        else:
            shutil.copyfile(src / relative, out)
        record(out, title, kind, original=relative, document=document)
        return out

    copy('outputs/v3/A_完整研究報告_詳細版.md', 'knowledge/research.md', '完整研究報告')
    copy('outputs/v3/F_來源與驗證報告_詳細版.md', 'knowledge/verification.md', '驗證範圍與研究限制')
    copy('outputs/v3/G_歷年法說會研究.md', 'knowledge/ir-research.md', '歷年法說會研究')
    copy('outputs/v3/財務原始資料.csv', 'data/financials.csv', '標準化財務原始資料', 'financial_facts', False)
    copy('outputs/v3/長期營收原始資料.csv', 'data/revenue-history.csv', '長期營收原始資料', 'financial_facts', False)
    copy('outputs/v3/原始財務與產業來源清單.csv', 'data/sources.csv', '財務與產業來源索引', 'source_index', False)
    copy('research/法說會近兩年/完整場次清單.csv', 'data/ir-events.csv', '近兩年62筆法說會場次索引', 'source_index', False)
    copy('research/法說會近兩年/pdf_manifest.json', 'data/ir-pdf-manifest.json', '60份原始PDF下載及雜湊索引', 'source_index', False)
    book = copy('outputs/v3/B_財務分析工作簿_詳細版.xlsx', 'models/financial-analysis.xlsx', '原14工作表財務分析工作簿', 'mixed_actuals_and_scenarios', False)

    # Each company-period has its own document so retrieval retains context.
    with (ROOT / 'data/financials.csv').open(encoding='utf-8-sig') as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        company, period = row['company'], row['period']
        out = ROOT / f'knowledge/financials/{company}_{period}.md'
        out.parent.mkdir(parents=True, exist_ok=True)
        body = [f'# {company} {period} 財務實績', '',
                f'公司：{company}；期間：{period}；涵蓋月數：{row["months"]}。',
                '金額：新台幣仟元；EPS：新台幣元／股。空白欄位代表未提供，不能當作零。',
                f'來源：{row["url"]}', f'原財報定位：{row["source"]}', f'口徑與限制：{row["note"]}', '',
                '| 指標 | 數值 |', '|---|---:|']
        body.extend(f'| {LABELS.get(key, key)} ({key}) | {value} |' for key, value in row.items()
                    if key not in ('company', 'period', 'months', 'url', 'source', 'note') and value != '')
        out.write_text('\n'.join(body)+'\n', encoding='utf-8')
        record(out, f'{company} {period} 財務實績', 'financial_facts', [company], [row['url']] if row['url'] else [], 'outputs/v3/財務原始資料.csv')

    # Source IDs from the research report stay searchable; keep archival paths explicitly labeled.
    for filename, title in [('sources.csv', '原始來源索引'), ('ir-events.csv', '近兩年法說會場次'), ('revenue-history.csv', '長期營收與會計口徑')]:
        with (ROOT / 'data' / filename).open(encoding='utf-8-sig') as handle:
            records = list(csv.DictReader(handle))
        out = ROOT / f'knowledge/{filename[:-4]}.md'
        body = [f'# {title}', '', '資料截止2026-11-15。下列本地檔／影音資料夾為原工作區封存位置，公開版未附原文；請使用原始網址取得。', '']
        for item in records:
            body.append('## ' + '／'.join(str(x) for x in list(item.values())[:3]))
            body.extend(f'- {key}：{value}' for key, value in item.items() if value)
            body.append('')
        out.write_text('\n'.join(body)+'\n', encoding='utf-8')
        record(out, title, 'source_index', original='data/'+filename)

    # Extract stored cell values AND formulas using OOXML; do not recalculate or modify the workbook.
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    rel_ns = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    with zipfile.ZipFile(book) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        relationships = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        for sheet in ET.fromstring(z.read('xl/workbook.xml')).find('m:sheets', ns):
            name = sheet.attrib['name']
            target = relationships[sheet.attrib[rel_ns]]
            archive_path = target.lstrip('/') if target.startswith('/') else 'xl/'+target
            tree = ET.fromstring(z.read(archive_path))
            body = [f'# 工作簿：{name}', '', '來源：models/financial-analysis.xlsx。以下是研究快照的儲存格值及原公式；公式沒有在本次匯出重新計算。',
                    '實績／假設依工作表原標籤判讀，EPS模型及敏感度為2027課堂情境。金額單位以原儲存格說明為準。', '']
            for row in tree.findall('.//m:sheetData/m:row', ns):
                parts = []
                for cell in row.findall('m:c', ns):
                    val = cell.find('m:v', ns)
                    value = val.text if val is not None else ''
                    if cell.attrib.get('t') == 's' and value:
                        value = strings[int(value)]
                    elif cell.attrib.get('t') == 'inlineStr':
                        value = ''.join(cell.find('m:is', ns).itertext())
                    formula = cell.find('m:f', ns)
                    text = f'{cell.attrib["r"]}：{value or "（未存值）"}'
                    if formula is not None:
                        text += f'；原公式 ={formula.text or "（共用公式，請查原工作簿）"}'
                    if value or formula is not None:
                        parts.append(text.replace('\n', ' '))
                if parts:
                    body.append('- ' + ' ｜ '.join(parts))
            out = ROOT / f'knowledge/workbook/{name}.md'
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text('\n'.join(body)+'\n', encoding='utf-8')
            record(out, f'工作簿{name}公式與快取值', 'scenario_assumptions' if name in ('EPS模型', '敏感度') else 'workbook_snapshot', original='outputs/v3/B_財務分析工作簿_詳細版.xlsx')

    catalog = dict(schema_version=1, research_cutoff=CUTOFF, timezone='Asia/Taipei',
                   latest_actual_periods=['2026Q3', '2026M9'], ir_window_start='2024-11-15',
                   packaged_on='2026-11-20',
                   date_semantics='available_on 是此快照採用的證據截止日，並非逐份原文首次發布日；不支援歷史時點回測。',
                   documents=docs, assets=assets)
    (ROOT / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Exported {len(docs)} documents and {len(assets)} assets.')


if __name__ == '__main__':
    main()
