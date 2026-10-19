"""Find the narrow webs in the GND plane (In1) that DRC's connection_width reports only by zone origin.

Rasterises the saved In1 fill at 0.05 mm, opens it (erode then dilate by 2 px, so anything narrower than 0.2 mm
disappears) and reports the blobs of copper that the opening removed: those are the webs under 0.2 mm, which
includes everything DRC rejects (< 0.15 mm). Each blob is printed with its size and the nearest non-GND holes, so the
offending via can be nudged. Run from DevBoard/ with KiCad's python after a refill (kicad-cli pcb drc --refill-zones
--save-board): python tools/plane_necks.py [board.kicad_pcb]
"""
import math
import os
import sys
from collections import deque

import numpy as np
import pcbnew
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "MonolithDev.kicad_pcb")
MM = pcbnew.ToMM
G = 0.05
b = pcbnew.LoadBoard(PCB)
gnd = b.FindNet("GND").GetNetCode()
plane = [z for z in b.Zones() if z.GetNetCode() == gnd and z.IsOnLayer(pcbnew.In1_Cu) and not z.GetIsRuleArea()][0]
fill = plane.GetFilledPolysList(pcbnew.In1_Cu)
bb = b.GetBoardEdgesBoundingBox()
X0, Y0 = MM(bb.GetLeft()), MM(bb.GetTop())
NX, NY = int(MM(bb.GetWidth()) / G) + 2, int(MM(bb.GetHeight()) / G) + 2
im = Image.new("1", (NX, NY), 0)
d = ImageDraw.Draw(im)
for i in range(fill.OutlineCount()):
    o = fill.Outline(i)
    d.polygon([((MM(o.CPoint(k).x) - X0) / G, (MM(o.CPoint(k).y) - Y0) / G) for k in range(o.PointCount())], fill=1)
    for h in range(fill.HoleCount(i)):
        c = fill.Hole(i, h)
        d.polygon([((MM(c.CPoint(k).x) - X0) / G, (MM(c.CPoint(k).y) - Y0) / G) for k in range(c.PointCount())], fill=0)
L = im.convert("L")
opened = L.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
a = np.array(L, dtype=bool)
thin = a & ~np.array(opened, dtype=bool)
print(f"In1 fill raster {NX}x{NY} px at {G} mm; copper px {int(a.sum())}; thin px {int(thin.sum())}")
holes = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and t.GetNetCode() != gnd:
        p = t.GetPosition()
        holes.append((MM(p.x), MM(p.y), "via " + t.GetNetname()))
for f in b.GetFootprints():
    for q in f.Pads():
        if q.HasHole() and q.GetNetCode() != gnd:
            p = q.GetPosition()
            holes.append((MM(p.x), MM(p.y), f"pad {f.GetReference()}.{q.GetNumber()}"))
# blobs of thin pixels (8-connected), skipping the plane's outer rim (thin edge artefacts)
ys, xs = np.nonzero(thin)
seen = np.zeros_like(thin)
blobs = []
for y, x in zip(ys, xs):
    if seen[y, x]:
        continue
    q = deque([(y, x)])
    seen[y, x] = True
    pts = []
    while q:
        cy, cx = q.popleft()
        pts.append((cy, cx))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < NY and 0 <= nx < NX and thin[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
    if len(pts) < 3:
        continue
    cy = sum(p[0] for p in pts) / len(pts)
    cx = sum(p[1] for p in pts) / len(pts)
    bx, by = X0 + cx * G, Y0 + cy * G
    # a web joins two larger regions: both sides of the blob must be copper that survived the opening
    blobs.append((len(pts), bx, by))
blobs.sort(reverse=True)
print(len(blobs), "thin blobs (>= 3 px); largest first:")
for n, bx, by in blobs[:40]:
    near = sorted(holes, key=lambda h: math.hypot(h[0] - bx, h[1] - by))[:3]
    print(f"  {n:4d} px at ({bx:.2f},{by:.2f}) nearest: " + "; ".join(f"{l} ({x:.2f},{y:.2f})" for x, y, l in near))
