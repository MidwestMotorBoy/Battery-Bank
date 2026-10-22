"""Remove local net labels that duplicate a wired connection (MacroFab: don't label direct same-page links).

A label is a candidate only if a wire ends at its anchor. Each removal is kept only if the
kicad-cli netlist (net names and members) is unchanged. Also hides TestPoint values, which
repeat the net label next to them.

Usage (from DevBoard/): python tools/prune_labels.py
"""
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
SHEETS = ['gauge.kicad_sch', 'power.kicad_sch', 'mcu.kicad_sch', 'usb_port.kicad_sch', 'MonolithDev.kicad_sch']
BS = chr(92)


def netlist():
    out = os.path.join(tempfile.gettempdir(), 'prune_net.xml')
    subprocess.run([CLI, 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', out, 'MonolithDev.kicad_sch'],
                   check=True, capture_output=True)
    r = ET.parse(out).getroot()
    return {(n.get('name'), frozenset((x.get('ref'), x.get('pin')) for x in n.iter('node'))) for n in r.iter('net')}


def block_end(s, start):
    d, m = 0, start
    while True:
        ch = s[m]
        if ch == '"':
            m += 1
            while s[m] != '"':
                if s[m] == BS:
                    m += 1
                m += 1
        elif ch == '(':
            d += 1
        elif ch == ')':
            d -= 1
            if d == 0:
                return m
        m += 1


def top(s, head):
    root = s.index('(kicad_sch')
    end = block_end(s, root)
    k = root + 1
    res = []
    while k < end:
        if s[k] == '"':
            k += 1
            while s[k] != '"':
                if s[k] == BS:
                    k += 1
                k += 1
        elif s[k] == '(':
            m = block_end(s, k)
            if re.match(r'\((\w+)', s[k:k + 40]).group(1) == head:
                res.append((k, m))
            k = m
        k += 1
    return res


def wire_ends(s):
    ends = set()
    for a, b in top(s, 'wire'):
        for x, y in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', s[a:b]):
            ends.add((round(float(x), 2), round(float(y), 2)))
    return ends


def hide_tp_values(s):
    out, last = [], 0
    for a, b in top(s, 'symbol'):
        blk = s[a:b + 1]
        if '(lib_id "Connector:TestPoint")' in blk:
            m = re.search(r'\(property "Value" "', blk)
            pe = block_end(blk, m.start())
            p = blk[m.start():pe + 1]
            if '(hide yes)' not in p:
                p = re.sub(r'(\(at [^)]*\))', r'\1\n\t\t\t(hide yes)', p, count=1)
            blk = blk[:m.start()] + p + blk[pe + 1:]
        out.append(s[last:a])
        out.append(blk)
        last = b + 1
    out.append(s[last:])
    return ''.join(out)


base = netlist()
removed = 0
for sheet in SHEETS:
    s = open(sheet, encoding='utf-8').read()
    s = hide_tp_values(s)
    open(sheet, 'w', encoding='utf-8', newline='\n').write(s)
    i = 0
    while True:
        labels = top(s, 'label')
        ends = wire_ends(s)
        cands = []
        for a, b in labels:
            m = re.search(r'\(at ([-\d.]+) ([-\d.]+)', s[a:b])
            if (round(float(m.group(1)), 2), round(float(m.group(2)), 2)) in ends:
                cands.append((a, b))
        if i >= len(cands):
            break
        a, b = cands[i]
        ls = s.rfind('\n', 0, a) + 1
        trial = s[:ls] + s[b + 2:] if s[b + 1:b + 2] == '\n' else s[:ls] + s[b + 1:]
        open(sheet, 'w', encoding='utf-8', newline='\n').write(trial)
        if netlist() == base:
            s = trial
            removed += 1
        else:
            open(sheet, 'w', encoding='utf-8', newline='\n').write(s)
            i += 1
    print(sheet, 'done')
print('removed', removed, 'redundant labels')
