"""Move everything inside a rectangle of a schematic sheet by (dx, dy).

    python tools/move_region.py sheet.kicad_sch x0 y0 x1 y1 dx dy [--dry]

An item moves when all of its anchor points lie inside the rectangle (schematic mm): a symbol's position, a
label's / junction's / no-connect's / text's position, both ends of a wire. Every coordinate in a moved item moves
with it (symbol fields too). A wire with only one end inside is reported, and stretched if it stays horizontal or
vertical; otherwise nothing is written. Run tools/junctions.py, tools/check_overlaps.py and an ERC afterwards.
"""
import re
import sys

KINDS = ("symbol", "wire", "label", "global_label", "hierarchical_label", "junction", "no_connect", "text",
         "bus_entry", "polyline", "netclass_flag", "text_box")
NUM = r"(-?\d+(?:\.\d+)?)"


def top_items(s):
    """(start, end, kind) of every item one level inside (kicad_sch ...)."""
    out, depth, i, start = [], 0, 0, None
    in_str = False
    while i < len(s):
        c = s[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
            if depth == 2:
                start = i
        elif c == ")":
            if depth == 2:
                kind = re.match(r"\((\w+)", s[start:start + 40]).group(1)
                out.append((start, i + 1, kind))
            depth -= 1
        i += 1
    return out


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


def main():
    a = [x for x in sys.argv[1:] if x != "--dry"]
    path = a[0]
    x0, y0, x1, y1, dx, dy = map(float, a[1:7])
    s = open(path, encoding="utf-8").read()

    def inside(x, y):
        return x0 <= x <= x1 and y0 <= y <= y1

    def shift_all(t):
        t = re.sub(r"\(at " + NUM + " " + NUM, lambda m: f"(at {fmt(float(m.group(1)) + dx)} {fmt(float(m.group(2)) + dy)}", t)
        return re.sub(r"\(xy " + NUM + " " + NUM, lambda m: f"(xy {fmt(float(m.group(1)) + dx)} {fmt(float(m.group(2)) + dy)}", t)

    out, last, moved, stretched, bad = [], 0, 0, 0, []
    for st, en, kind in top_items(s):
        if kind not in KINDS:
            continue
        t = s[st:en]
        if kind == "wire" or kind == "polyline":
            pts = [(float(x), float(y)) for x, y in re.findall(r"\(xy " + NUM + " " + NUM, t)]
            ins = [inside(*p) for p in pts]
            if all(ins):
                new = shift_all(t)
            elif any(ins) and kind == "wire" and len(pts) == 2:
                (ax, ay), (bx, by) = pts
                horiz, vert = abs(ay - by) < 1e-6, abs(ax - bx) < 1e-6
                if (horiz and dy == 0) or (vert and dx == 0):
                    k = 0

                    def one(m):
                        nonlocal k
                        x, y = float(m.group(1)), float(m.group(2))
                        r = f"(xy {fmt(x + dx)} {fmt(y + dy)}" if ins[k] else m.group(0)
                        k += 1
                        return r
                    new = re.sub(r"\(xy " + NUM + " " + NUM, one, t)
                    stretched += 1
                else:
                    bad.append(pts)
                    continue
            else:
                continue
        else:
            m = re.search(r"\(at " + NUM + " " + NUM, t)
            if not m or not inside(float(m.group(1)), float(m.group(2))):
                continue
            new = shift_all(t)
        out.append(s[last:st])
        out.append(new)
        last = en
        moved += 1
    out.append(s[last:])
    print(f"moved {moved} items, stretched {stretched} wires")
    if bad:
        print("wires crossing the rectangle edge that cannot stretch (nothing written):", bad)
        sys.exit(1)
    if "--dry" not in sys.argv:
        open(path, "w", encoding="utf-8", newline="\n").write("".join(out))


if __name__ == "__main__":
    main()
