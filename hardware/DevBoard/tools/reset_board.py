"""Reset MonolithDev.kicad_pcb to parts + outline for a fresh layout, and bring its footprints in line with the
schematic.

Step 1 (text, no pcbnew): delete every track, arc, via, zone (pours and rule areas), group and board graphic except
the Edge.Cuts outline; delete footprints that are no longer in the schematic and footprints whose library footprint
changed (their position, rotation and side are kept in reset_board.json).
Step 2 (pcbnew, `--load`): load the changed footprints from their libraries at the old positions, and add footprints
for new schematic parts in a staging area below the board, grouped by sheet.
Then run netlist_to_board.py for nets, fields and symbol links.

    kicad-cli sch export netlist --format kicadsexpr -o net.sexp MonolithDev.kicad_sch
    python tools/reset_board.py net.sexp [REF,...]  # step 1; listed refs are reloaded even if the name is unchanged
    python tools/reset_board.py net.sexp --load     # step 2 (KiCad's python)
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PCB = os.path.join(ROOT, "MonolithDev.kicad_pcb")
STATE = os.path.join(HERE, "reset_board.json")
KICAD_FP = r"C:/Program Files/KiCad/10.0/share/kicad/footprints"
BOARD_ONLY = re.compile(r"^H\d+$")                     # mounting holes live only on the board


def parse(t):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', t)
    st = [[]]
    for k in toks:
        if k == "(":
            st.append([])
        elif k == ")":
            x = st.pop()
            st[-1].append(x)
        else:
            st[-1].append(k[1:-1] if k[0] == '"' else k)
    return st[0][0]


def schematic_parts(netfile):
    tree = parse(open(netfile, encoding="utf-8").read())
    comps = [c for c in tree if isinstance(c, list) and c and c[0] == "components"][0]
    out = {}
    for c in comps[1:]:
        if not (isinstance(c, list) and c[0] == "comp"):
            continue
        ref = fp = sheet = ""
        for f in c[1:]:
            if isinstance(f, list) and f[0] == "ref":
                ref = f[1]
            if isinstance(f, list) and f[0] == "footprint":
                fp = f[1]
            if isinstance(f, list) and f[0] == "sheetpath":
                sheet = [g for g in f if isinstance(g, list) and g[0] == "names"][0][1]
        out[ref] = dict(fp=fp, sheet=sheet)
    return out


def top_blocks(s):
    """(kind, start, end) of every top-level item, end exclusive, start at the newline before it."""
    for m in re.finditer(r"\n\t\(([a-z_]+)", s):
        a = m.start()
        d, i = 0, a + 2
        while True:
            c = s[i]
            if c == '"':
                i += 1
                while s[i] != '"':
                    i += 2 if s[i] == "\\" else 1
            elif c == "(":
                d += 1
            elif c == ")":
                d -= 1
                if d == 0:
                    break
            i += 1
        yield m.group(1), a, i + 1


def step1(netfile, force=()):
    sch = schematic_parts(netfile)
    s = open(PCB, encoding="utf-8").read()
    shutil.copy(PCB, PCB + ".before_reset")
    cut, counts, keep_fp, swaps = [], {}, set(), []
    for kind, a, b in top_blocks(s):
        blk = s[a:b]
        drop = False
        if kind in ("segment", "arc", "via", "zone", "group", "dimension", "target", "image", "table"):
            drop = True
        elif kind.startswith("gr_"):
            drop = '(layer "Edge.Cuts")' not in blk
        elif kind == "footprint":
            ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
            lib_id = re.match(r'\n\t\(footprint "([^"]+)"', blk).group(1)
            if BOARD_ONLY.match(ref):
                keep_fp.add(ref)
            elif ref not in sch:
                drop = True
                kind = "footprint (not in schematic)"
            elif sch[ref]["fp"] and (sch[ref]["fp"] != lib_id or ref in force):
                at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
                layer = re.search(r'\n\t\t\(layer "([^"]+)"\)', blk).group(1)
                swaps.append(dict(ref=ref, fp=sch[ref]["fp"], x=float(at.group(1)), y=float(at.group(2)),
                                  rot=float(at.group(3) or 0), back=layer == "B.Cu"))
                drop = True
                kind = "footprint (library footprint changed)"
            else:
                keep_fp.add(ref)
        if drop:
            cut.append((a, b))
            counts[kind] = counts.get(kind, 0) + 1
    for a, b in sorted(cut, reverse=True):
        s = s[:a] + s[b:]
    open(PCB, "w", encoding="utf-8", newline="\n").write(s)
    swapped = {w["ref"] for w in swaps}
    new = sorted(r for r, v in sch.items() if r not in keep_fp and r not in swapped and v["fp"])
    json.dump(dict(swaps=swaps, new=[dict(ref=r, fp=sch[r]["fp"], sheet=sch[r]["sheet"]) for r in new]),
              open(STATE, "w"), indent=1)
    for k, v in sorted(counts.items()):
        print(f"removed {v:4d} {k}")
    print(f"kept {len(keep_fp)} footprints; {len(swaps)} to reload, {len(new)} new -> {STATE}")


def step2():
    import pcbnew
    st = json.load(open(STATE))
    pro = os.path.join(ROOT, "MonolithDev.kicad_pro")
    pro_txt = open(pro, encoding="utf-8").read()
    board = pcbnew.LoadBoard(PCB)

    def load(fp_id):
        lib, name = fp_id.split(":", 1)
        path = os.path.join(ROOT, lib + ".pretty") if lib == "MonolithDev" else os.path.join(KICAD_FP, lib + ".pretty")
        f = pcbnew.FootprintLoad(path, name)
        assert f is not None, fp_id
        f.SetFPID(pcbnew.LIB_ID(lib, name))
        return f

    for w in st["swaps"]:
        f = load(w["fp"])
        f.SetReference(w["ref"])
        board.Add(f)
        f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(w["x"]), pcbnew.FromMM(w["y"])))
        if w["back"]:
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(w["rot"])

    box = board.GetBoardEdgesBoundingBox()
    x0, y = pcbnew.ToMM(box.GetLeft()), pcbnew.ToMM(box.GetBottom()) + 8.0
    by_sheet = {}
    for n in st["new"]:
        by_sheet.setdefault(n["sheet"], []).append(n)
    for sheet, parts in by_sheet.items():
        x, row_h = x0, 0.0
        for n in sorted(parts, key=lambda n: (re.match(r"[A-Z]+", n["ref"]).group(), int(re.search(r"\d+", n["ref"]).group()))):
            f = load(n["fp"])
            f.SetReference(n["ref"])
            board.Add(f)
            bb = f.GetBoundingBox(False)
            w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
            if x + w > x0 + pcbnew.ToMM(box.GetWidth()):
                x, y, row_h = x0, y + row_h + 2.0, 0.0
            dx = pcbnew.ToMM(f.GetPosition().x - bb.GetLeft())
            dy = pcbnew.ToMM(f.GetPosition().y - bb.GetTop())
            f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x + dx), pcbnew.FromMM(y + dy)))
            x += w + 2.0
            row_h = max(row_h, h)
        y += row_h + 5.0
    board.Save(PCB)
    open(pro, "w", encoding="utf-8", newline="").write(pro_txt)
    print(f"reloaded {len(st['swaps'])}, added {len(st['new'])} below the board")


if __name__ == "__main__":
    if "--load" in sys.argv:
        step2()
    else:
        step1(sys.argv[1], set(sys.argv[2].split(",")) if len(sys.argv) > 2 else ())
