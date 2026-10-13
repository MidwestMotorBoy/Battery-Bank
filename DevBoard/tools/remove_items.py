"""Remove specific wires / labels from a sheet by exact coordinates.

Usage: python tools/remove_items.py sheet.kicad_sch spec.txt
spec lines:  wire x0 y0 x1 y1   |   label NAME x y
"""
import re
import sys

BS = chr(92)


def blocks(s, head):
    for m in re.finditer(r'\n\t\(' + head + r'\b', s):
        a = m.start() + 1
        d, i = 0, a
        while True:
            c = s[i]
            if c == '"':
                i += 1
                while s[i] != '"':
                    i += 2 if s[i] == BS else 1
            elif c == '(':
                d += 1
            elif c == ')':
                d -= 1
                if d == 0:
                    break
            i += 1
        yield a, i


path, spec = sys.argv[1], sys.argv[2]
kill_w, kill_l = set(), set()
for line in open(spec):
    t = line.split()
    if not t:
        continue
    if t[0] == 'wire':
        a = tuple(float(v) for v in t[1:5])
        kill_w.add(a)
        kill_w.add((a[2], a[3], a[0], a[1]))
    elif t[0] == 'label':
        kill_l.add((t[1], float(t[2]), float(t[3])))
s = open(path, encoding='utf-8').read()
cut = []
for a, b in blocks(s, 'wire'):
    m = re.search(r'\(xy ([-\d.]+) ([-\d.]+)\) \(xy ([-\d.]+) ([-\d.]+)\)', s[a:b])
    if tuple(map(float, m.groups())) in kill_w:
        cut.append((a, b))
for a, b in blocks(s, 'label'):
    m = re.search(r'\(label "([^"]+)"\s*\(at ([-\d.]+) ([-\d.]+)', s[a:b])
    if m and (m.group(1), float(m.group(2)), float(m.group(3))) in kill_l:
        cut.append((a, b))
for a, b in sorted(cut, reverse=True):
    s = s[:a - 1] + s[b + 1:]
open(path, 'w', encoding='utf-8', newline='\n').write(s)
print('removed', len(cut))
