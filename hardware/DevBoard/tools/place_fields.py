"""Place Reference/Value text of every symbol where it collides with nothing (graphics only).

For each symbol, candidate spots around its body are scored against bodies, pin lines, labels,
notes, wires and already-placed fields; the first collision-free candidate wins (else the least bad).
Text is always written horizontal and centre-justified, so symbol rotation can't flip it.

Also moves long value annotations "X (note)" into a hidden Notes property (value keeps "X").

Usage (from DevBoard/): python tools/place_fields.py [sheet ...]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sch_geom as G  # noqa: E402

SHEETS = ['MonolithDev.kicad_sch', 'gauge.kicad_sch', 'power.kicad_sch', 'mcu.kicad_sch', 'usb_port.kicad_sch']
GAP = 0.8


def blocks(s, head='symbol'):
    root = s.index('(kicad_sch')
    end = G_block_end(s, root)
    k = root + 1
    while k < end:
        c = s[k]
        if c == '"':
            k = skip(s, k)
        elif c == '(':
            m = G_block_end(s, k)
            if re.match(r'\((\w+)', s[k:k + 40]).group(1) == head:
                yield k, m
            k = m
        k += 1


def skip(s, k):
    k += 1
    while s[k] != '"':
        if s[k] == G.BS:
            k += 1
        k += 1
    return k


def G_block_end(s, start):
    d, m = 0, start
    while True:
        ch = s[m]
        if ch == '"':
            m = skip(s, m)
        elif ch == '(':
            d += 1
        elif ch == ')':
            d -= 1
            if d == 0:
                return m
        m += 1


def prop_span(blk, name):
    m = re.search(r'\(property "' + re.escape(name) + r'" "', blk)
    if not m:
        return None
    return m.start(), G_block_end(blk, m.start())


def set_prop(blk, name, x=None, y=None, value=None, hide=None, add_after=None):
    sp = prop_span(blk, name)
    if sp is None:
        if add_after is None:
            return blk
        a, b = prop_span(blk, add_after)
        new = (f'\n\t\t(property "{name}" "{value}"\n\t\t\t(at 0 0 0)\n\t\t\t(hide yes)\n'
               f'\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n'
               f'\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)')
        return blk[:b + 1] + new + blk[b + 1:]
    a, b = sp
    p = blk[a:b + 1]
    if value is not None:
        p = re.sub(r'^\(property "' + re.escape(name) + r'" "(?:[^"\\]|\\.)*"', f'(property "{name}" "{value}"', p)
    if x is not None:
        p = re.sub(r'\(at [-\d.]+ [-\d.]+(?: [-\d.]+)?\)', f'(at {x:.2f} {y:.2f} {ANG})', p, count=1)
        es = p.find('(effects')
        if es >= 0:
            ee = G_block_end(p, es)
            eff = p[es:ee + 1]
            size = re.search(r'\(size ([\d.]+) ([\d.]+)\)', eff)
            sz = '1.27'
            p = p[:es] + f'(effects\n\t\t\t\t(font\n\t\t\t\t\t(size {sz} {sz})\n\t\t\t\t)\n\t\t\t)' + p[ee + 1:]
    if hide is not None:
        p = re.sub(r'\n\s*\(hide yes\)', '', p)
        if hide:
            p = re.sub(r'(\(at [^)]*\))', r'\1\n\t\t\t(hide yes)', p, count=1)
    return blk[:a] + p + blk[b + 1:]


ANG = 0


def shorten_values(s):
    out, last = [], 0
    for a, b in list(blocks(s)):
        blk = s[a:b + 1]
        lib = re.search(r'\(lib_id "([^"]+)"\)', blk).group(1)
        m = re.search(r'\(property "Value" "((?:[^"\\]|\\.)*)"', blk)
        if m and not lib.startswith('power:'):
            v = m.group(1)
            mm = re.match(r'^(.*?)\s*\((.+)\)\s*$', v)
            if mm and len(v) > 12 and mm.group(1):
                blk = set_prop(blk, 'Value', value=mm.group(1).strip())
                if prop_span(blk, 'Notes'):
                    blk = set_prop(blk, 'Notes', value=mm.group(2))
                else:
                    blk = set_prop(blk, 'Notes', value=mm.group(2), add_after='Value')
        out.append(s[last:a])
        out.append(blk)
        last = b + 1
    out.append(s[last:])
    return ''.join(out)


LABEL_KINDS = ('label', 'global_label', 'hierarchical_label')


def orient_labels(path):
    """Rotate each label about its fixed anchor to the orientation with the fewest collisions."""
    s = open(path, encoding='utf-8').read()
    root, items, wires, syms = G.load(path)
    obstacles = [b for b in items if b.kind in ('body', 'pinline', 'note')]
    wire_boxes = [G.Box(w[0][0] - 0.05, w[0][1] - 0.05, w[1][0] + 0.05, w[1][1] + 0.05, 'wire') for w in wires]
    placed = []
    edits = []
    for kind in LABEL_KINDS:
        for a, b in list(blocks(s, kind)):
            blk = s[a:b + 1]
            txt = re.search(r'\(' + kind + r' "((?:[^"\\]|\\.)*)"', blk).group(1)
            at = re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', blk)
            x, y, cur = float(at.group(1)), float(at.group(2)), int(float(at.group(3)))
            size = 1.27
            best = None
            for ang in [cur] + [o for o in (0, 90, 180, 270) if o != cur]:
                box = label_box(kind, txt, x, y, ang, size)
                sc = 0
                for o in obstacles:
                    if o.kind == 'pinline':
                        if box.overlaps(o, 0.6):
                            sc += 10
                    elif box.overlaps(o, 0.05):
                        sc += 10
                for o in placed:
                    if box.overlaps(o, 0.05):
                        sc += 10
                for w in wire_boxes:
                    # a wire ending at the anchor is the label's own wire; others must not cross the text
                    if box.overlaps(w, 0.05):
                        sc += 3
                sc += 0 if ang == cur else 0.5
                if best is None or sc < best[0]:
                    best = (sc, ang, box)
            placed.append(best[2])
            if best[1] != cur:
                edits.append((a, b, cur, best[1]))
    for a, b, cur, new in sorted(edits, reverse=True):
        blk = s[a:b + 1]
        blk = re.sub(r'\(at ([-\d.]+) ([-\d.]+) [-\d.]+\)', lambda m: f'(at {m.group(1)} {m.group(2)} {new})', blk, count=1)
        just = 'right' if new in (180, 270) else 'left'
        blk = re.sub(r'\(justify (left|right)( bottom)?\)', lambda m: f'(justify {just}{m.group(2) or ""})', blk, count=1)
        s = s[:a] + blk + s[b + 1:]
    open(path, 'w', encoding='utf-8', newline='\n').write(s)
    return len(edits)


def label_box(kind, txt, x, y, a, size):
    if kind == 'label':
        L = len(txt) * size * G.CHAR_W + 0.4
        H = size * 1.2
        if a == 0:
            return G.Box(x + 0.2, y - H, x + 0.2 + L, y - 0.15, 'label')
        if a == 180:
            return G.Box(x - 0.2 - L, y - H, x - 0.2, y - 0.15, 'label')
        if a == 90:
            return G.Box(x - H, y - 0.2 - L, x - 0.15, y - 0.2, 'label')
        return G.Box(x - H, y + 0.2, x - 0.15, y + 0.2 + L, 'label')
    L = len(txt) * size * G.CHAR_W + size * 2.2 + 0.4
    H = size * 1.9
    if a == 0:
        return G.Box(x, y - H / 2, x + L, y + H / 2, 'glabel')
    if a == 180:
        return G.Box(x - L, y - H / 2, x, y + H / 2, 'glabel')
    if a == 90:
        return G.Box(x - H / 2, y - L, x + H / 2, y, 'glabel')
    return G.Box(x - H / 2, y, x + H / 2, y + L, 'glabel')


def place(path):
    global ANG
    s = open(path, encoding='utf-8').read()
    s = shorten_values(s)
    open(path, 'w', encoding='utf-8', newline='\n').write(s)
    print(path, 'labels re-oriented', orient_labels(path))
    s = open(path, encoding='utf-8').read()
    root, items, wires, syms = G.load(path)
    static = [b for b in items if b.kind != 'field']
    wire_boxes = [G.Box(w[0][0] - 0.1, w[0][1] - 0.1, w[1][0] + 0.1, w[1][1] + 0.1, 'wire') for w in wires]
    placed = []

    # per-symbol field text and body box
    sym_nodes = G.kids(root, 'symbol')
    info = []
    for node, (ref, lib, sx, sy, rot, mir) in zip(sym_nodes, syms):
        bodies = [b for b in static if b.owner == ref and b.kind in ('body', 'pinline')]
        if bodies:
            bx0 = min(b.x0 for b in bodies if b.kind == 'body') if any(b.kind == 'body' for b in bodies) else sx
            # reference extent = graphics + pin lines (without pin-number allowance)
            ext = [b for b in bodies]
            body = G.Box(min(b.x0 for b in ext), min(b.y0 for b in ext) + (1.5 if False else 0),
                         max(b.x1 for b in ext), max(b.y1 for b in ext), 'body', ref)
            gfx = [b for b in bodies if b.kind == 'body']
            if gfx and not lib.startswith('Device:'):
                body = gfx[0]
        else:
            body = G.Box(sx - 1, sy - 1, sx + 1, sy + 1, 'body', ref)
        fields = []
        for p in G.kids(node, 'property'):
            if p[1] in ('Reference', 'Value'):
                size, _, _, hidden = G.effects_of(p)
                if not hidden and p[2]:
                    fields.append((p[1], p[2], size))
        info.append((ref, lib, sx, sy, rot, body, fields))

    two_pin = [(r, x, y) for r, l, x, y, rt, _, _ in info if l.startswith('Device:') and rt % 180 == 0]

    def in_row(ref, x, y, lib, rot):
        if not lib.startswith('Device:') or rot % 180:
            return False
        return any(r != ref and abs(yy - y) < 0.5 and 0 < abs(xx - x) <= 12.8 for r, xx, yy in two_pin)

    # order: big parts first so small parts work around them
    info.sort(key=lambda t: -((t[5].x1 - t[5].x0) * (t[5].y1 - t[5].y0)))
    moves = {}
    for ref, lib, sx, sy, rot, body, fields in info:
        if not fields:
            continue
        lines = [f for f in fields]
        w = max(len(t) for _, t, _ in lines) * max(sz for *_, sz in lines) * G.CHAR_W
        lh = max(sz for *_, sz in lines) * G.LINE_H
        h = lh * len(lines)
        cx, cy = (body.x0 + body.x1) / 2, (body.y0 + body.y1) / 2
        cands = [
            (body.x1 + GAP + w / 2, cy),                 # right
            (body.x0 - GAP - w / 2, cy),                 # left
            (cx, body.y0 - GAP - h / 2),                 # above
            (cx, body.y1 + GAP + h / 2),                 # below
            (body.x1 + GAP + w / 2, body.y0 - GAP - h / 2),
            (body.x1 + GAP + w / 2, body.y1 + GAP + h / 2),
            (body.x0 - GAP - w / 2, body.y0 - GAP - h / 2),
            (body.x0 - GAP - w / 2, body.y1 + GAP + h / 2),
        ]
        if lib.startswith('power:') or lib in ('power:PWR_FLAG',):
            cands = [cands[3], cands[2], cands[0], cands[1]] + cands[4:]
        elif in_row(ref, sx, sy, lib, rot):
            # parts in a horizontal row (cap banks): label above, so each label sits over its own part
            cands = [cands[2], cands[3], cands[0], cands[1]] + cands[4:]
        # widen the search ring
        for d in (1.27, 2.54, 3.81):
            cands += [(c[0] + dx, c[1] + dy) for c in cands[:4] for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d))]
        best, best_score = None, None
        for (fx, fy) in cands:
            box = G.Box(fx - w / 2, fy - h / 2, fx + w / 2, fy + h / 2, 'field', ref)
            score = 0
            for o in static:
                if o.owner == ref and o.kind in ('body', 'pinline'):
                    if box.overlaps(o, -0.4 if o.kind == 'pinline' else -0.2):
                        score += 50
                    continue
                if box.overlaps(o, -0.3):
                    score += 10
            for o in placed + wire_boxes:
                if box.overlaps(o, -0.3):
                    score += 10
            dist = abs(fx - cx) + abs(fy - cy)
            score += dist * 0.4
            if best_score is None or score < best_score:
                best, best_score = (fx, fy, box), score
            if score < 1:
                break
        fx, fy, box = best
        placed.append(box)
        top = fy - h / 2 + lh / 2
        moves[(ref, round(sx, 2), round(sy, 2))] = [(name, fx, top + i * lh) for i, (name, _, _) in enumerate(lines)]

    out, last = [], 0
    for a, b in list(blocks(s)):
        blk = s[a:b + 1]
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', blk)
        sx, sy, rot = float(at.group(1)), float(at.group(2)), int(float(at.group(3)))
        key = (ref, round(sx, 2), round(sy, 2))
        if key in moves:
            ANG = (360 - rot) % 180 if rot % 180 else 0
            ANG = 90 if rot % 180 == 90 else 0
            for name, fx, fy in moves[key]:
                blk = set_prop(blk, name, fx, fy)
        out.append(s[last:a])
        out.append(blk)
        last = b + 1
    out.append(s[last:])
    open(path, 'w', encoding='utf-8', newline='\n').write(''.join(out))
    print(path, 'placed', len(moves))


for p in [a for a in sys.argv[1:]] or SHEETS:
    place(p)
