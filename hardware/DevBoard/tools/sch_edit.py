"""Text-level helpers for editing KiCad 10 schematics (shared by tools/review4_fixes.py and tools/review4_docs.py)."""
import re
import uuid


def U():
    return str(uuid.uuid4())


def g(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def block_end(s, start):
    d = 0
    k = start
    while True:
        c = s[k]
        if c == '"':
            k += 1
            while s[k] != '"':
                k += 2 if s[k] == "\\" else 1
        elif c == "(":
            d += 1
        elif c == ")":
            d -= 1
            if d == 0:
                return k + 1
        k += 1


def sym_span(s, ref):
    i = s.index(f'(property "Reference" "{ref}"')
    a = s.rindex("\n\t(symbol\n", 0, i)
    return a, block_end(s, a + 2)


def set_prop(blk, name, val):
    new, n = re.subn(r'(\(property "' + re.escape(name) + r'" )"[^"]*"', lambda m: m.group(1) + '"' + val + '"', blk,
                     count=1)
    assert n == 1, (name, blk[:120])
    return new


def edit(s, ref, **kv):
    a, b = sym_span(s, ref)
    blk = s[a:b]
    for k, v in kv.items():
        blk = set_prop(blk, k, v)
    return s[:a] + blk + s[b:]


def move_item(s, kind, name, x, y, nx, ny):
    """Move a label / global label / power symbol whose anchor is at (x, y)."""
    if kind == "symbol":
        pat = re.compile(r'(\n\t\(symbol\n\t\t\(lib_id "[^"]+"\)\n\t\t\(at )' + re.escape(g(x)) + " " + re.escape(g(y))
                         + r"( \d+\))")
    else:
        pat = re.compile(r'(\n\t\(' + kind + ' "' + re.escape(name) + r'"(?:\n\t\t\(shape \w+\))?\n\t\t\(at )'
                         + re.escape(g(x)) + " " + re.escape(g(y)) + r"( \d+\))")
    m = pat.search(s)
    assert m, (kind, name, x, y)
    a = m.start()
    b = block_end(s, a + 2)
    blk = s[a:b]
    dx, dy = nx - x, ny - y
    blk = re.sub(r"\(at ([-\d.]+) ([-\d.]+)( \d+)?\)",
                 lambda q: f"(at {g(float(q.group(1)) + dx)} {g(float(q.group(2)) + dy)}{q.group(3) or ''})", blk)
    return s[:a] + blk + s[b:]


def prop(name, val, x, y, hide):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return (f'\n\t\t(property "{name}" "{val}"\n\t\t\t(at {g(x)} {g(y)} 0){h}\n\t\t\t(show_name no)\n'
            f'\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)')


def new_symbol(lib_id, refs, value, x, y, pins, props, rot=0, dnp=False):
    """refs: [(sheet path, reference), ...] - one entry per instance of the sheet."""
    body = (f'\n\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {g(x)} {g(y)} {rot})\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            f'\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            f'\t\t(dnp {"yes" if dnp else "no"})\n\t\t(uuid "{U()}")')
    body += prop("Reference", refs[-1][1], x, y - 3, False) + prop("Value", value, x, y + 3, False)
    for k, v in props:
        body += prop(k, v, x, y, True)
    for p in pins:
        body += f'\n\t\t(pin "{p}"\n\t\t\t(uuid "{U()}")\n\t\t)'
    body += '\n\t\t(instances\n\t\t\t(project "MonolithDev"'
    for path, ref in refs:
        body += f'\n\t\t\t\t(path "{path}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)'
    return body + "\n\t\t\t)\n\t\t)\n\t)"


def clone(s, tref, refs, x, y, rot, props):
    """Copy symbol tref (same lib symbol) to (x, y, rot) with new references and properties."""
    a, b = sym_span(s, tref)
    blk = s[a:b]
    at = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+) (\d+)\)", blk)
    ox, oy = float(at.group(1)), float(at.group(2))
    blk = re.sub(r"\(at ([-\d.]+) ([-\d.]+) (\d+)\)",
                 lambda m: f"(at {g(float(m.group(1)) - ox + x)} {g(float(m.group(2)) - oy + y)} {m.group(3)})", blk)
    at = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+) (\d+)\)", blk)
    blk = blk[:at.start()] + f"\n\t\t(at {g(x)} {g(y)} {rot})" + blk[at.end():]
    blk = re.sub(r'\(uuid "[^"]+"\)', lambda m: f'(uuid "{U()}")', blk)
    blk = set_prop(blk, "Reference", refs[-1][1])
    for path, ref in refs:
        blk, n = re.subn(r'(\(path "' + re.escape(path) + r'"\s*\(reference )"[^"]+"', lambda m: m.group(1) + f'"{ref}"', blk)
        assert n == 1, (tref, path)
    for k, v in props:
        blk = set_prop(blk, k, v)
    return blk


def label(name, x, y, ang):
    just = "left bottom" if ang in (0, 90) else "right bottom"
    return (f'\n\t(label "{name}"\n\t\t(at {g(x)} {g(y)} {ang})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n\t)')


def wire(x0, y0, x1, y1):
    return (f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {g(x0)} {g(y0)}) (xy {g(x1)} {g(y1)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n'
            f'\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')


def junction(x, y):
    return f'\n\t(junction\n\t\t(at {g(x)} {g(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)'


def drop(s, pattern):
    """Delete the one top-level item whose text starts with the regex pattern."""
    m = list(re.finditer(pattern, s))
    assert len(m) == 1, (pattern, len(m))
    a = m[0].start()
    return s[:a] + s[block_end(s, a + 2):]


def insert_items(s, text):
    k = s.rindex("\n\t(sheet_instances")
    return s[:k] + text + s[k:]


def paths_of(s, ref):
    a, b = sym_span(s, ref)
    return re.findall(r'\(path "([^"]+)"\s*\(reference "([^"]+)"\)', s[a:b])


def note_replace(s, old, new):
    assert s.count(old) == 1, old
    return s.replace(old, new)
