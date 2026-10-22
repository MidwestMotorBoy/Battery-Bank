"""Hybrid weight-saving variants: pocketed lid, 1.2 mm tub wall, narrow flange with 4 end screws, thinner lid.
Run: python monolith_hybrid_variants.py CURRENT_MECH_DIR   (next to monolith_hybrid.py; prints a mass table)"""
import sys, os, numpy as np
CUR = sys.argv[1]; sys.argv = ['x', CUR, os.path.dirname(os.path.abspath(__file__)) + '/out', 'none']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import monolith_hybrid as H
from monolith_render import vol
M3 = H.M3
def recompute():
    H.cs_body = H.hull(*[H.circ(x, y, H.CR + 0.2 + H.TW) for x, y in H.CELLS], H.rect(0, H.X_FL0 + 0.01, -H.YI - H.TW, H.YI + H.TW))
    H.cs_flange = H.rrect(H.X_FL0 - 1.5, H.X_RIM, -H.Y_FL, H.Y_FL, 2.0)
    H.cs_pack = H.CS.batch_boolean([H.cs_body, H.cs_flange, H.rrect(H.X_FL0, H.X_RIM + H.LID_T, -H.Y_FL, H.Y_FL, 2.0)], M3.OpType.Add)
base_lid = H.lid
def pocketed_lid(keep):
    def f():
        m = base_lid()
        inner = H.groove_loop(-H.GROOVE_W/2 - 1.0)                     # 1 mm inside the groove's inner edge
        hot = H.rect(-13.0, 13.0, 26.0, 56.0)                            # pedestal over the hot parts (y, z)
        pocket = H.CS.batch_boolean([inner, hot], M3.OpType.Subtract)
        return m - H.px_(pocket, H.X_RIM - 0.1, H.X_RIM + H.LID_T - keep)
    return f
def run(name, **kw):
    saved = {k: getattr(H, k) for k in ('TW', 'Y_FL', 'LID_T', 'lid', 'SCREW_Z')}
    for k, v in kw.items(): setattr(H, k, v)
    recompute(); A = H.assembly(); m = H.masses(A)
    m['filler'] = 26*30*0.5/1000*2.5                                     # 0.5 mm real filler, not the 1.8 mm stand-in
    for k, v in saved.items(): setattr(H, k, v)
    recompute()
    return name, m
rows = [run('baseline (as rendered, filler corrected)'),
        run('lid pocketed to 1.5 mm inside the groove', lid=pocketed_lid(1.5)),
        run('+ tub wall 1.2 (as current)', lid=pocketed_lid(1.5), TW=1.2),
        run('+ narrow flange, 4 end screws (Y_FL 26.9)', lid=pocketed_lid(1.5), TW=1.2, Y_FL=26.9, SCREW_Z=(8.0, H.H - 8.0)),
        run('+ lid 2.5 mm, pocketed to 1.2', lid=pocketed_lid(1.2), TW=1.2, Y_FL=26.9, SCREW_Z=(8.0, H.H - 8.0), LID_T=2.5)]
keys = ['tub', 'lid', 'bumpb', 'bumpt', 'carrier', 'pad', 'screw', 'lim', 'oring', 'filler']
print(f"{'variant':46s}" + ''.join(f'{k:>8s}' for k in keys) + f"{'total':>8s}")
for n, m in rows: print(f'{n:46s}' + ''.join(f'{m.get(k,0):8.1f}' for k in keys) + f'{sum(m.values()):8.1f}')
