"""Interactive 3D viewer of the Monolith pack: one self-contained HTML page (three.js from a CDN, meshes embedded).
Built from the same meshes as monolith_cup.py (assembly(), the STLs) and the routed P0 board (board/monolith_board.npz),
with the wrap label art on the label. Re-run after any geometry change.
Needs the mechanical venv (numpy, pillow, manifold3d, matplotlib for the bumper text) + cairosvg for the label art.
Run: python monolith_viewer.py [--fragment OUT.html]
-> ../../docs/viewer/monolith_viewer.html (full page, open it in a browser; needs internet for three.js)
   --fragment writes the page body only (for publishing as a claude.ai artifact)."""
import os, sys, io, re, json, gzip, base64, subprocess, datetime, numpy as np
import manifold3d as M3
from PIL import Image
import monolith_cup as M, monolith_parts as P

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
TEMPLATE = os.path.join(ROOT, 'docs', 'viewer', 'template.html')
OUT = os.path.join(ROOT, 'docs', 'viewer', 'monolith_viewer.html')

# explode offsets (mm), as monolith_cup.sheet_exploded: the core drops out of the cup, the closure stack below it
EX = dict(cell=(0, 0, -75), carrier=(0, 0, -75), nickel=(0, 0, -75), tails=(0, 0, -75), board=(16, 0, -75), ble=(16, 0, -75),
          filler=(8, 0, -75), cup=(0, 0, 25), pad=(0, 0, -118), oring=(0, 0, -136), cap=(0, 0, -152), screw=(0, 0, -152),
          vent=(0, 0, -167), rails=(9, 0, -75), insul=(0, 0, -75), foam=(0, 0, -75), sleeve=(22, 0, -75), label=(0, 0, 25),
          bumpb=(0, 0, -182), bumpt=(0, 0, 50))

# (id, section, display name, part number in monolith_cup.PARTS, mesh keys in assembly())
UI = [('cup', 'Enclosure', 'Cup', 11, ['cup']),
      ('label', 'Enclosure', 'Wrap label', 18, ['label']),
      ('bumpt', 'Enclosure', 'Top bumper', 17, ['bumpt_band', 'bumpt_slab']),
      ('bumpb', 'Enclosure', 'Bottom bumper', 16, ['bumpb_band', 'bumpb_slab']),
      ('cap', 'Enclosure', 'Bottom cap', 14, ['cap']),
      ('oring', 'Enclosure', 'O-ring', 13, ['oring']),
      ('screw', 'Enclosure', 'M2 screws', 15, ['screw']),
      ('vent', 'Enclosure', 'Vent patch', 19, ['vent']),
      ('carrier', 'Core', 'Cell carrier', 1, ['carrier']),
      ('rails', 'Core', 'Board rails', 2, ['rails']),
      ('sleeve', 'Core', 'Post sleeves', 10, ['sleeve']),
      ('pad', 'Core', 'Cap pad', 12, ['pad']),
      ('foam', 'Core', 'Preload foam', 5, ['foam']),
      ('insul', 'Core', 'Insulator rings', 4, ['insul']),
      ('filler', 'Core', 'Gap filler', 8, ['filler']),
      ('cell', 'Cells and wiring', 'Cells C1-C4', 3, ['cell']),
      ('nickel', 'Cells and wiring', 'Nickel strips', 6, ['nickel']),
      ('tails', 'Cells and wiring', 'PACK pads and tongues', 7, ['tails']),
      ('wires', 'Cells and wiring', 'PACK and sense wires', 7, ['tails_wire', 'tails_sense']),
      ('pcb', 'Board', 'PCB', 9, None), ('parts', 'Board', 'Components', 9, None),
      ('usb', 'Board', 'USB-C receptacles', 9, None), ('ble', 'Board', 'BLE module U301', 9, None)]
NICE = dict(cup=(206, 208, 204), label=(255, 255, 255), cap=(160, 178, 196))   # label is textured; the rest keep monolith_cup.C


def comp_color(ref, model):
    """a plausible body colour for a board part (the KiCad STEP colours are not kept in the npz)"""
    p = re.match(r'[A-Z]+', ref).group(0)
    if model.startswith('Peg_'): return (118, 72, 50)
    if model.startswith('SolderWire'): return (200, 50, 50)
    if p in ('C',) and 'T593' not in model: return (186, 156, 112)
    if p == 'TH': return (160, 120, 80)
    if p in ('R', 'RS'): return (38, 38, 42)
    if p == 'L': return (78, 80, 86)
    if p == 'F': return (226, 222, 210)
    return (34, 34, 38)


def pack(V, extra=None):
    """triangles (n, 3, 3) -> deduplicated uint16-quantized vertices + indices; extra = per-corner (n, 3, k) data kept per vertex"""
    V = np.asarray(V, float).reshape(-1, 3)
    lo, hi = V.min(0), V.max(0); sc = np.maximum(hi - lo, 1e-6)
    q = np.round((V - lo) / sc * 65535).astype(np.uint16)
    key = q if extra is None else np.hstack([q, np.round(np.asarray(extra, float).reshape(len(V), -1) * 4096).astype(np.int64)])
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    idx = inv.reshape(-1).astype(np.uint32)
    return dict(q=q[first], idx=idx, lo=lo, sc=sc, first=first)


class Blob:
    def __init__(self): self.b = bytearray()
    def add(self, a):
        a = np.ascontiguousarray(a); off = len(self.b); self.b += a.tobytes()
        while len(self.b) % 4: self.b.append(0)
        return off


def mesh_entry(blob, V, color, extra=None, vcol=None):
    pk = pack(V, extra)
    nv = len(pk['q']); it = 'u16' if nv < 65536 else 'u32'
    e = dict(pos=blob.add(pk['q']), nv=nv, idx=blob.add(pk['idx'].astype(np.uint16 if it == 'u16' else np.uint32)),
             ni=len(pk['idx']), it=it, lo=[round(float(x), 5) for x in pk['lo']], sc=[round(float(x), 6) for x in pk['sc']],
             color='#%02x%02x%02x' % tuple(int(c) for c in color))
    if extra is not None:
        e['uv'] = blob.add(np.asarray(extra, np.float32).reshape(-1, 2)[pk['first']])
    if vcol is not None:
        e['vcol'] = blob.add(np.asarray(vcol, np.uint8).reshape(-1, 3)[pk['first']])
    return e


def label_mesh():
    """the label shell, split at the seam (middle of the back flat, as hardware/label/monolith_label.py lays it out) and
    mapped to the print art: u = perimeter position from the seam, v = down from the top edge"""
    from monolith_cup import cs_out, LABEL_T, LABEL_Z, ROUND, label
    Pl = np.array(cs_out.offset(LABEL_T / 2, ROUND, circular_segments=720).to_polygons()[0], float)
    Ql = np.roll(Pl, -1, 0); seg = np.linalg.norm(Ql - Pl, axis=1); s0 = np.concatenate([[0], np.cumsum(seg)[:-1]]); per = seg.sum()
    back = [i for i in range(len(Pl)) if seg[i] > 2 and abs(Pl[i, 0] - Ql[i, 0]) < 1e-4 and Pl[i, 0] < 0][0]
    seam = s0[back] + seg[back] / 2; ys = (Pl[back, 1] + Ql[back, 1]) / 2
    a, b = label().split_by_plane((0, 1, 0), ys)
    T = np.vstack([M.tris(a), M.tris(b)])
    p = T.reshape(-1, 3); d = Ql - Pl; u = np.empty(len(p))
    for k in range(0, len(p), 2000):
        q = p[k:k + 2000, None, :2]
        t = np.clip(((q - Pl[None]) * d[None]).sum(-1) / (seg ** 2)[None], 0, 1)
        j = np.argmin(np.linalg.norm(q - (Pl[None] + t[..., None] * d[None]), axis=-1), axis=1)
        u[k:k + 2000] = (s0[j] + t[np.arange(len(j)), j] * seg[j] - seam) % per
    u = u.reshape(-1, 3)
    for r in u:                                          # triangles touching the seam: keep all three corners on one side
        if r.max() - r.min() > per / 2: r[r < per / 2] += per
    v = LABEL_Z[1] - T[..., 2]
    art = os.path.join(HERE, '..', 'label', 'out', 'monolith_label_bl_print.svg'); bleed, dpmm = 2.0, 9
    try:
        import cairosvg
        png = cairosvg.svg2png(url=art, scale=dpmm / (96 / 25.4), background_color='white')
        im = Image.open(io.BytesIO(png)).convert('RGB')
        wmm, hmm = im.size[0] / dpmm, im.size[1] / dpmm
        buf = io.BytesIO(); im.save(buf, 'JPEG', quality=84, optimize=True)
        tex = 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        print('label art not embedded:', e); tex, wmm, hmm = None, per + 2 * bleed, v.max() + 2 * bleed
    uv = np.stack([(u + bleed) / wmm, 1 - (v + bleed) / hmm], -1)
    return T, uv, tex


def git_rev():
    try: return subprocess.check_output(['git', '-C', ROOT, 'log', '-1', '--format=%h %cs'], text=True).strip()
    except Exception: return ''


def build():
    A = M.assembly(); m = M.masses(A)
    names = {n: (name, mat) for n, name, mat, _ in M.PARTS}
    blob = Blob(); parts = []
    B = P.real_board()
    lab_T, lab_uv, lab_tex = label_mesh()
    for pid, sec, title, num, keys in UI:
        meshes, picks = [], None
        if keys is None:                                  # board pieces, straight from the KiCad mesh
            refs = [k for k in B if not k.startswith('_') and k not in ('PCB', 'U301') + P.BENCH_ONLY]
            usb = ['J401', 'J501']
            if pid == 'pcb': meshes.append(mesh_entry(blob, B['PCB'], M.C['board']))
            elif pid == 'ble': meshes.append(mesh_entry(blob, B['U301'], M.C['ble']))
            elif pid == 'usb': meshes.append(mesh_entry(blob, np.vstack([B[k] for k in usb]), M.C['usb']))
            else:
                refs = sorted([k for k in refs if k not in usb], key=lambda r: (re.match(r'[A-Z]+', r).group(0), int(re.sub(r'\D', '', r) or 0)))
                Ts, cols, picks, t0 = [], [], [], 0
                for r in refs:
                    T = np.asarray(B[r], float); model = str(B['_model_' + r])
                    Ts.append(T); cols.append(np.tile(comp_color(r, model), (len(T) * 3, 1)))
                    picks.append([r, model, t0, len(T)]); t0 += len(T)
                # dedupe per part (part index as an extra key) so neighbouring parts never share, and recolour, a vertex
                partid = np.concatenate([np.full((len(T), 3, 2), [i, 0], float) for i, T in enumerate(Ts)]) / 4096
                pk = pack(np.vstack(Ts), partid)
                nv = len(pk['q']); it = 'u16' if nv < 65536 else 'u32'
                ent = dict(pos=blob.add(pk['q']), nv=nv, idx=blob.add(pk['idx'].astype(np.uint16 if it == 'u16' else np.uint32)),
                           ni=len(pk['idx']), it=it, lo=[round(float(x), 5) for x in pk['lo']],
                           sc=[round(float(x), 6) for x in pk['sc']], color='#ffffff',
                           vcol=blob.add(np.vstack(cols)[pk['first']].astype(np.uint8)))
                meshes.append(ent)
            explode = EX['board']
        elif pid == 'label':
            e = mesh_entry(blob, lab_T, NICE['label'], extra=lab_uv); e['tex'] = lab_tex
            meshes.append(e); explode = EX['label']
        else:
            for k, V, c in A:
                if k in keys:
                    col = NICE.get(pid, c)
                    meshes.append(mesh_entry(blob, V, col))
            explode = EX[M.group(keys[0])]
        name, mat = names[num]
        g = 'tails' if pid == 'wires' else pid if pid in m else None
        mass = round(m[g], 1) if g in m and pid not in ('wires',) else None
        if pid in ('pcb', 'parts', 'usb', 'ble'): mass = None
        parts.append(dict(id=pid, section=sec, title=title, num=num, name=name, material=mat, mass=mass,
                          explode=list(explode), meshes=meshes, **({'picks': picks} if picks else {})))
    V = np.vstack([V for _, V, _ in A]).reshape(-1, 3)
    meta = dict(parts=parts, bbox=[V.min(0).round(2).tolist(), V.max(0).round(2).tolist()],
                total=round(sum(m.values()), 1), board_mass=round(m['board'], 1), rev=git_rev(),
                built=datetime.date.today().isoformat(), size=(V.max(0) - V.min(0)).round(1).tolist())
    raw = bytes(blob.b); gz = gzip.compress(raw, 9)
    print(f'meshes {len(raw) / 1e6:.2f} MB raw, {len(gz) / 1e6:.2f} MB gzip; total {meta["total"]} g, size {meta["size"]}')
    return meta, base64.b64encode(gz).decode()


def main():
    frag = '--fragment' in sys.argv
    out = sys.argv[sys.argv.index('--fragment') + 1] if frag else OUT
    meta, b64 = build()
    html = open(TEMPLATE, encoding='utf-8').read()
    html = html.replace('/*__META__*/null', json.dumps(meta, separators=(',', ':'))).replace('__BLOB__', b64)
    if not frag:
        html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                '</head>\n<body>\n' + html + '\n</body>\n</html>\n')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(html)
    print('wrote', out, f'{len(html) / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
