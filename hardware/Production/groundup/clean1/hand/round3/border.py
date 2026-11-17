#!/usr/bin/env python3
"""Lead's own round-3 fixes: the four 90 degree corners that sit on the north/south border (y = 103), on top of the merged
north + south result (m2/ns_geo.json)."""
import sys, os
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, S + '/tools'); from fixlib import Fix
f = Fix(S + '/m2/ns_geo.json')
def nm(x, y): return (int(round(x * 1e6)), int(round(y * 1e6)))
# 1 ACP_F port 2, In2, corner (81.325, 100.0745): 0.4 mm chamfer
f.replace(['53a91661', '31ec657e'], [nm(80.175, 100.0745), nm(80.925, 100.0745), nm(81.325, 100.4745), nm(81.325, 108.4245)])
# 2 CELL3, In2, diagonal + 0.6 flat + corner (98.925, 101.1245): one diagonal
d = [t for t in f.near(98.15, 100.95, 'In2', r=0.05) if t['net'].endswith('CELL3')]
assert len(d) == 1, d
f.replace([d[0]['id'], '607c4df6', '13c5ba8f'], [nm(98.025, 100.8245), nm(98.925, 101.7245), nm(98.925, 112.5245)])
# 3 EN_5V1, In2, corner (115.325, 103.2): 0.3 mm chamfer
f.replace(['6c6eac45', 'fcc4c296'], [nm(115.325, 101.3245), nm(115.325, 102.9), nm(115.025, 103.2), nm(112.95, 103.2)])
# 4 I2CC_SCL port 1, In2, corner (94.975, 103.9745): 0.3 mm chamfer
f.replace(['3f6ae487', '25849627'], [nm(94.975, 97.2745), nm(94.975, 103.6745), nm(94.675, 103.9745), nm(93.975, 103.9745)])
ok = f.check(S + '/m2/spec_border.json', maxexc=0.8, out=S + '/m2/final_geo.json'); sys.exit(0 if ok else 1)
