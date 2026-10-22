"""Approximate geometry of a KiCad 10 .kicad_sch for readability checks.

Builds boxes for symbol bodies, visible fields, labels, notes and wire segments,
using a small S-expression parser and an estimate of KiCad's stroke-font text size.
Coordinates are schematic millimetres, y down.
"""
import math
import re

BS = chr(92)
CHAR_W = 0.95      # glyph advance as a fraction of font size (KiCad stroke font, average)
LINE_H = 1.55      # line pitch as a fraction of font size


# ---------------------------------------------------------------- S-expressions
def parse(s):
    tok = re.compile(r'"(?:[^"' + BS + BS + r']|' + BS + BS + r'.)*"|\(|\)|[^\s()"]+')
    stack, cur = [], []
    for m in tok.finditer(s):
        t = m.group(0)
        if t == '(':
            stack.append(cur)
            cur = []
        elif t == ')':
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            if t[0] == '"':
                t = t[1:-1].replace(BS + 'n', '\n').replace(BS + '"', '"')
            cur.append(t)
    return cur[0]


def kids(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def kid(node, name):
    k = kids(node, name)
    return k[0] if k else None


def num(x):
    return float(x)


# ---------------------------------------------------------------- boxes
class Box:
    __slots__ = ('x0', 'y0', 'x1', 'y1', 'kind', 'owner', 'text')

    def __init__(self, x0, y0, x1, y1, kind, owner='', text=''):
        self.x0, self.x1 = min(x0, x1), max(x0, x1)
        self.y0, self.y1 = min(y0, y1), max(y0, y1)
        self.kind, self.owner, self.text = kind, owner, text

    def overlaps(self, o, pad=0.0):
        return (self.x0 < o.x1 - pad and o.x0 < self.x1 - pad and
                self.y0 < o.y1 - pad and o.y0 < self.y1 - pad)

    def __repr__(self):
        return f'{self.kind}:{self.owner}:{self.text!r}@({self.x0:.1f},{self.y0:.1f})-({self.x1:.1f},{self.y1:.1f})'


def text_box(text, x, y, ang, size, hjust='center', vjust='center', kind='text', owner=''):
    lines = text.split('\n')
    w = max(len(l) for l in lines) * size * CHAR_W
    h = (len(lines) - 1) * size * LINE_H + size * 1.1
    if hjust == 'left':
        a0, a1 = 0, w
    elif hjust == 'right':
        a0, a1 = -w, 0
    else:
        a0, a1 = -w / 2, w / 2
    if vjust == 'top':
        b0, b1 = 0, h
    elif vjust == 'bottom':
        b0, b1 = -h, 0
    else:
        b0, b1 = -h / 2, h / 2
    if ang % 180 == 90:
        # vertical text reads bottom-to-top: along-text axis is -y
        return Box(x + b0, y - a1, x + b1, y - a0, kind, owner, text)
    return Box(x + a0, y + b0, x + a1, y + b1, kind, owner, text)


def effects_of(node):
    eff = kid(node, 'effects')
    size, hj, vj, hidden = 1.27, 'center', 'center', False
    if eff:
        f = kid(eff, 'font')
        if f and kid(f, 'size'):
            size = num(kid(f, 'size')[1])
        j = kid(eff, 'justify')
        if j:
            for t in j[1:]:
                if t in ('left', 'right'):
                    hj = t
                if t in ('top', 'bottom'):
                    vj = t
        if kid(eff, 'hide') or 'hide' in eff:
            hidden = True
    h = kid(node, 'hide')
    if h and (len(h) == 1 or h[1] == 'yes'):
        hidden = True
    return size, hj, vj, hidden


# ---------------------------------------------------------------- library symbols
def lib_body(libsym):
    """Bounding box (lib coords, y up) of graphics + pins, per unit (unit 0 = common)."""
    pts = []
    pins = []
    pn = kid(libsym, 'pin_numbers')
    shows_numbers = not (pn and (kid(pn, 'hide') or 'hide' in pn))
    for sub in kids(libsym, 'symbol'):
        for g in sub[1:]:
            if not isinstance(g, list):
                continue
            if g[0] == 'rectangle':
                for k in ('start', 'end'):
                    p = kid(g, k)
                    pts.append((num(p[1]), num(p[2])))
            elif g[0] == 'polyline':
                for p in kids(kid(g, 'pts'), 'xy'):
                    pts.append((num(p[1]), num(p[2])))
            elif g[0] == 'circle':
                c = kid(g, 'center')
                r = num(kid(g, 'radius')[1])
                pts += [(num(c[1]) - r, num(c[2]) - r), (num(c[1]) + r, num(c[2]) + r)]
            elif g[0] == 'arc':
                for k in ('start', 'mid', 'end'):
                    p = kid(g, k)
                    if p:
                        pts.append((num(p[1]), num(p[2])))
            elif g[0] == 'pin':
                at = kid(g, 'at')
                ln = num(kid(g, 'length')[1]) if kid(g, 'length') else 2.54
                x, y, a = num(at[1]), num(at[2]), num(at[3]) if len(at) > 3 else 0
                ex = x + ln * math.cos(math.radians(a))
                ey = y + ln * math.sin(math.radians(a))
                if not kid(g, 'hide') and 'hide' not in g:
                    pins.append(((x, y), (ex, ey), shows_numbers))
    return pts, pins


def xform(px, py, sx, sy, rot, mirror):
    # lib coords (y up) -> schematic (y down)
    if mirror == 'y':
        px = -px
    elif mirror == 'x':
        py = -py
    vx, vy = px, -py
    t = math.radians(rot)
    rx = vx * math.cos(t) + vy * math.sin(t)
    ry = -vx * math.sin(t) + vy * math.cos(t)
    return sx + rx, sy + ry


# ---------------------------------------------------------------- sheet
def load(path):
    s = open(path, encoding='utf-8').read()
    root = parse(s)
    libs = {}
    for ls in kids(kid(root, 'lib_symbols') or [], 'symbol'):
        libs[ls[1]] = lib_body(ls)
    items = []      # Boxes
    wires = []      # ((x0,y0),(x1,y1))
    syms = []
    for sym in kids(root, 'symbol'):
        lib = kid(sym, 'lib_id')[1]
        at = kid(sym, 'at')
        sx, sy, rot = num(at[1]), num(at[2]), int(num(at[3])) if len(at) > 3 else 0
        mir = kid(sym, 'mirror')
        mirror = mir[1] if mir else None
        ref = ''
        for p in kids(sym, 'property'):
            if p[1] == 'Reference':
                ref = p[2]
        pts, pins = libs.get(lib, ([], []))
        allp = [xform(x, y, sx, sy, rot, mirror) for x, y in pts]
        # body = graphics only (pins are thin lines; include them as 'pinline' boxes)
        if allp:
            xs, ys = zip(*allp)
            body = Box(min(xs), min(ys), max(xs), max(ys), 'body', ref, lib)
            items.append(body)
        for (a, b, nums) in pins:
            p0 = xform(*a, sx, sy, rot, mirror)
            p1 = xform(*b, sx, sy, rot, mirror)
            bx = Box(p0[0] - 0.15, p0[1] - 0.15, p1[0] + 0.15, p1[1] + 0.15, 'pinline', ref, lib)
            if nums:
                # pin number text sits above a horizontal pin / left of a vertical pin
                if abs(p0[1] - p1[1]) < 0.01:
                    bx.y0 -= 1.5
                else:
                    bx.x0 -= 1.5
            items.append(bx)
        syms.append((ref, lib, sx, sy, rot, mirror))
        for p in kids(sym, 'property'):
            name, val = p[1], p[2]
            if not val or name not in ('Reference', 'Value') and not (lib.startswith('power:') and name == 'Value'):
                if name not in ('Reference', 'Value'):
                    continue
            size, hj, vj, hidden = effects_of(p)
            if hidden or not val:
                continue
            pat = kid(p, 'at')
            fx, fy, fa = num(pat[1]), num(pat[2]), int(num(pat[3])) if len(pat) > 3 else 0
            disp = (fa + rot) % 180
            if rot in (180, 270) and hj in ('left', 'right'):
                hj = 'right' if hj == 'left' else 'left'
            items.append(text_box(val, fx, fy, disp, size, hj, vj, 'field', ref))
    for w in kids(root, 'wire'):
        p = kids(kid(w, 'pts'), 'xy')
        wires.append(((num(p[0][1]), num(p[0][2])), (num(p[1][1]), num(p[1][2]))))
    for kind in ('label', 'global_label', 'hierarchical_label'):
        for l in kids(root, kind):
            txt = l[1]
            at = kid(l, 'at')
            x, y, a = num(at[1]), num(at[2]), int(num(at[3])) if len(at) > 3 else 0
            size, hj, vj, _ = effects_of(l)
            extra = 0 if kind == 'label' else size * 2.2
            L = len(txt) * size * CHAR_W + extra + 0.4
            H = size * (1.2 if kind == 'label' else 1.9)
            if kind == 'label':
                # local label text sits just above (or left of, if vertical) its anchor line
                if a == 0:
                    b = Box(x + 0.2, y - H, x + 0.2 + L, y - 0.15, 'label', txt, txt)
                elif a == 180:
                    b = Box(x - 0.2 - L, y - H, x - 0.2, y - 0.15, 'label', txt, txt)
                elif a == 90:
                    b = Box(x - H, y - 0.2 - L, x - 0.15, y - 0.2, 'label', txt, txt)
                else:
                    b = Box(x - H, y + 0.2, x - 0.15, y + 0.2 + L, 'label', txt, txt)
            else:
                if a == 0:
                    b = Box(x, y - H / 2, x + L, y + H / 2, 'glabel', txt, txt)
                elif a == 180:
                    b = Box(x - L, y - H / 2, x, y + H / 2, 'glabel', txt, txt)
                elif a == 90:
                    b = Box(x - H / 2, y - L, x + H / 2, y, 'glabel', txt, txt)
                else:
                    b = Box(x - H / 2, y, x + H / 2, y + L, 'glabel', txt, txt)
            items.append(b)
    for t in kids(root, 'text'):
        at = kid(t, 'at')
        x, y, a = num(at[1]), num(at[2]), int(num(at[3])) if len(at) > 3 else 0
        size, hj, vj, _ = effects_of(t)
        if hj == 'center' and kid(kid(t, 'effects') or [], 'justify') is None:
            hj = 'left'
        b = text_box(t[1], x, y, a, size, hj, 'top' if vj == 'center' else vj, 'note', 'note')
        # KiCad anchors text at the first baseline
        b.y0 -= size * 0.9
        b.y1 -= size * 0.9
        items.append(b)
    return root, items, wires, syms


def seg_hits_box(seg, b, pad=0.1):
    (x0, y0), (x1, y1) = seg
    if x0 == x1:
        return b.x0 + pad < x0 < b.x1 - pad and min(y0, y1) < b.y1 - pad and max(y0, y1) > b.y0 + pad
    if y0 == y1:
        return b.y0 + pad < y0 < b.y1 - pad and min(x0, x1) < b.x1 - pad and max(x0, x1) > b.x0 + pad
    return False


def problems(items, wires):
    """Return list of (a, b) overlapping pairs that hurt readability."""
    out = []
    texty = ('field', 'label', 'glabel', 'note')
    n = len(items)
    for i in range(n):
        a = items[i]
        for j in range(i + 1, n):
            b = items[j]
            if a.kind not in texty and b.kind not in texty:
                if a.kind == 'body' and b.kind == 'body' and a.owner != b.owner and a.overlaps(b, 0.3):
                    out.append((a, b))
                continue
            # a field may touch its own symbol's pin lines/body edge only if it is outside the body
            if a.owner == b.owner and {a.kind, b.kind} <= {'field', 'body', 'pinline'}:
                if 'field' in (a.kind, b.kind) and ('body' in (a.kind, b.kind)):
                    f, bd = (a, b) if a.kind == 'field' else (b, a)
                    if f.overlaps(bd, 0.25) and bd.text.split(':')[0] in ('Device', 'Jumper', 'Connector'):
                        out.append((a, b))
                if 'field' in (a.kind, b.kind) and 'pinline' in (a.kind, b.kind) and a.overlaps(b, -0.2):
                    out.append((a, b))
                continue
            if 'pinline' in (a.kind, b.kind):
                if a.overlaps(b, 0.6):
                    out.append((a, b))
                continue
            clear = -0.3 if (a.kind in texty and b.kind in texty and not (a.kind == b.kind == 'glabel')) else 0.05
            if a.overlaps(b, clear):
                out.append((a, b))
    for it in items:
        if it.kind in ('field', 'note'):
            for w in wires:
                if seg_hits_box(w, it):
                    out.append((it, Box(*w[0], *w[1], 'wire')))
                    break
    return out
