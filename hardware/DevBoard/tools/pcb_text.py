"""Text-level board edits shared by the routing scripts (run before pcbnew.LoadBoard)."""
import re


def strip_items(path, uuids):
    """Remove (segment ...)/(via ...) blocks with these UUIDs from the board file as text: removing hundreds of
    items through pcbnew leaves dead SWIG wrappers for every later board call in the same process."""
    txt = open(path, encoding="utf-8").read()
    out, i, n = [], 0, 0
    while True:
        j = min([k for k in (txt.find("\n\t(segment", i), txt.find("\n\t(via", i)) if k >= 0] or [-1])
        if j < 0:
            out.append(txt[i:])
            break
        d, k = 0, j + 1
        while True:
            ch = txt[k]
            if ch == "(":
                d += 1
            elif ch == ")":
                d -= 1
                if d == 0:
                    break
            k += 1
        blk = txt[j:k + 1]
        u = re.search(r'\(uuid "([^"]+)"\)', blk)
        out.append(txt[i:j])
        if u and u.group(1) in uuids:
            n += 1
        else:
            out.append(blk)
        i = k + 1
    open(path, "w", encoding="utf-8", newline="\n").write("".join(out))
    return n

