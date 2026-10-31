"""Rebuild the tracker tables in ordering/README.md from ordering/parts-tracker.csv.

parts-tracker.csv is the source of truth (edit it in Excel or any text editor). GitHub shows a CSV as a table but
doesn't make its links clickable, so this script writes a Markdown copy, grouped the same way, into README.md
between the tracker markers. Standard library only.

Run: python ordering/update_readme.py
"""
import csv, os, re
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CSV, README = os.path.join(HERE, 'parts-tracker.csv'), os.path.join(HERE, 'README.md')
START, END = '<!-- tracker:start -->', '<!-- tracker:end -->'
STATUS_ORDER = ['To order', 'Decide', 'Hold', 'Check', 'Ordered', 'Received', 'Have', 'Dropped']


def money(s):
    try:
        return float(s.replace('$', '').replace(',', ''))
    except ValueError:
        return None


def cell(s):
    return (s or '').replace('|', '\\|').replace('\n', ' ').strip()


def table(rows):
    out = ['| ID | Item | Qty | Vendor | Cost (USD) | Status | Ordered | Notes |',
           '|---|---|---|---|---|---|---|---|']
    for r in rows:
        vendor = f"[{cell(r['Vendor'])}]({r['Link'].strip()})" if r['Link'].strip() else cell(r['Vendor'])
        unit, total = money(r['Unit cost (USD)']), money(r['Total (USD)'])
        cost = f'{total:,.2f}' if total is not None else (f'{unit:,.2f} ea' if unit is not None else '')
        ordered = ' '.join(x for x in (cell(r['Order date']), cell(r['Order #'])) if x)
        if r['Received'].strip():
            ordered += f" (in {cell(r['Received'])})"
        status = cell(r['Status'])
        status = f'**{status}**' if status in ('To order', 'Decide') else status
        item = cell(r['Item']) + (f"<br><sub>{cell(r['Part / spec'])}</sub>" if r['Part / spec'].strip() else '')
        out.append(f"| {r['ID']} | {item} | {cell(r['Qty to buy'])} | {vendor} | {cost} | {status} | {ordered} | {cell(r['Notes'])} |")
    return out


def main():
    rows = list(csv.DictReader(open(CSV, newline='', encoding='utf-8-sig')))
    groups = OrderedDict()
    for r in rows:
        groups.setdefault(r['Group'], []).append(r)
    counts = Counter(r['Status'].strip() for r in rows)
    order = [s for s in STATUS_ORDER if counts[s]] + sorted(s for s in counts if s not in STATUS_ORDER)
    known = sum(money(r['Total (USD)']) or 0 for r in rows if r['Status'].strip() not in ('Have', 'Dropped'))
    spent = sum(money(r['Total (USD)']) or 0 for r in rows if r['Status'].strip() in ('Ordered', 'Received'))
    lines = [START, '', '_Generated from `parts-tracker.csv` by `update_readme.py`; edit the CSV, not this table._', '',
             '**Status:** ' + ' · '.join(f'{s} {counts[s]}' for s in order) + '  ',
             f'**Known prices:** ${known:,.2f} listed so far (most lines have no price yet), ${spent:,.2f} ordered.', '']
    for g, rs in groups.items():
        lines += [f'### {g}', ''] + table(rs) + ['']
    lines.append(END)
    text = open(README, encoding='utf-8').read()
    new = re.sub(re.escape(START) + '.*?' + re.escape(END), lambda _: '\n'.join(lines), text, flags=re.S)
    if START not in text:
        new = text.rstrip() + '\n\n' + '\n'.join(lines) + '\n'
    open(README, 'w', encoding='utf-8', newline='\n').write(new)
    print(f'{len(rows)} lines, {len(groups)} groups -> {README}')


if __name__ == '__main__':
    main()
