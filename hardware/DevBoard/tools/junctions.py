"""Add missing junction dots and optionally delete local labels by name.

A junction is needed wherever a wire end lands on the middle of another wire (KiCad does not join
them otherwise) and is added for readability wherever three or more wire ends / pin ends meet.

Usage (from DevBoard/): python tools/junctions.py sheet.kicad_sch [--drop-labels NAME,NAME,...]
"""
import os
import re
import sys
import uuid
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sch_geom as G  # noqa: E402

BS = chr(92)


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


def drop_labels(s, names):
    out, last, n = [], 0, 0
    for m in re.finditer(r'\t\(label "((?:[^"\\]|\\.)*)"\n', s):
        if m.group(1) in names:
            a = m.start()
            b = block_end(s, a + 1)
            out.append(s[last:a])
            last = b + 2 if s[b + 1:b + 2] == '\n' else b + 1
            n += 1
    out.append(s[last:])
    return ''.join(out), n


def pin_points(root):
    libs = {}
    for ls in G.kids(G.kid(root, 'lib_symbols') or [], 'symbol'):
        pins = set()
        for sub in G.kids(ls, 'symbol'):
            for p in G.kids(sub, 'pin'):
                at = G.kid(p, 'at')
                pins.add((float(at[1]), float(at[2])))
        libs[ls[1]] = pins
    out = []
    for sym in G.kids(root, 'symbol'):
        lib = G.kid(sym, 'lib_id')[1]
        at = G.kid(sym, 'at')
        sx, sy, rot = float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0
        mir = G.kid(sym, 'mirror')
        for px, py in libs.get(lib, ()):
            x, y = G.xform(px, py, sx, sy, rot, mir[1] if mir else None)
            out.append((round(x, 2), round(y, 2)))
    return out


def on_interior(p, a, b):
    (x, y), (x0, y0), (x1, y1) = p, a, b
    if x0 == x1 == x:
        return min(y0, y1) < y < max(y0, y1)
    if y0 == y1 == y:
        return min(x0, x1) < x < max(x0, x1)
    return False


path = sys.argv[1]
s = open(path, encoding='utf-8').read()
if '--drop-labels' in sys.argv:
    names = set(sys.argv[sys.argv.index('--drop-labels') + 1].split(','))
    s, n = drop_labels(s, names)
    print('dropped', n, 'labels')
    open(path, 'w', encoding='utf-8', newline='\n').write(s)
root, items, wires, syms = G.load(path)
wires = [((round(a[0], 2), round(a[1], 2)), (round(b[0], 2), round(b[1], 2))) for a, b in wires]
pins = set(pin_points(root))
ends = Counter(p for w in wires for p in w)
have = {(round(float(x), 2), round(float(y), 2)) for x, y in re.findall(r'\(junction\s*\(at ([-\d.]+) ([-\d.]+)', s)}
need = set()
for p, c in ends.items():
    if c + (1 if p in pins else 0) >= 3:
        need.add(p)
    if any(on_interior(p, a, b) for a, b in wires):
        need.add(p)
add = ''.join(f'\t(junction\n\t\t(at {x} {y})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n'
              for x, y in sorted(need - have))
i = s.rindex('\t(sheet_instances') if '\t(sheet_instances' in s else s.rstrip().rindex(')')
s = s[:i] + add + s[i:]
open(path, 'w', encoding='utf-8', newline='\n').write(s)
print(path, 'added', len(need - have), 'junctions')
