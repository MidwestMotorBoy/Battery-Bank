"""USB-C retention sheet: a cut through port 1, the load path of a plug push, and how much of each seal ring stays in
the full bore (2026-10-31). Run from hardware/mechanical: python monolith_usb_retention.py -> usb_port_retention.png"""
import sys, os; sys.path.insert(0, os.getcwd())
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import monolith_cup as K, monolith_shell as S, monolith_side_renders as RR
A = [(k, V, c) for k, V, c in K.assembly() if k not in ('label', 'tails_sense', 'foam', 'insul')]
F = lambda b, n: ImageFont.truetype('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf', n)
INK, MUT, ACC, RED, GRN = RR.INK, (110, 112, 120), RR.ACCENT, (196, 52, 52), (40, 140, 70)
W, H = 2760, 1060
img = Image.new('RGB', (W, H), (250, 249, 246)); d = ImageDraw.Draw(img)
d.text((40, 24), 'What holds the USB-C ports in their seal bores', fill=INK, font=F(1, 34))
d.text((40, 72), 'The seal is radial (the ring squeezes inside the bore), so the port has to stay deep enough in the bore. Pulling a plug has a hard stop; pushing one in only has the TPU pad behind it.', fill=MUT, font=F(0, 18))
def panel(x0, y0, w, h, title):
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], 8, outline=(214, 214, 210), width=1); d.text((x0 + 18, y0 + 14), title, fill=INK, font=F(1, 20))
def cut(y, box, px, x0, y0, maxw, maxh):
    u0, u1, w0, w1 = box; Wc, Hc = int((u1 - u0) * px) + 40, int((w1 - w0) * px) + 40
    sh = RR.Sheet(Wc, Hc); sh.section(A, 1, y, 0, 2, (20 - px*u0, 20 + px*w1), px)
    im = sh.img.resize((Wc, Hc), Image.LANCZOS); s = min(maxw / Wc, maxh / Hc); im = im.resize((int(Wc*s), int(Hc*s)), Image.LANCZOS)
    img.paste(im, (x0, y0)); return lambda u, w: (x0 + s*(20 + px*(u - u0)), y0 + s*(20 + px*(w1 - w))), im.size
def note(p, t, tx, ty, col=MUT):
    d.line([p, (tx - 6, ty + 9)], fill=col, width=1); d.ellipse([p[0]-3, p[1]-3, p[0]+3, p[1]+3], fill=INK); d.multiline_text((tx, ty), t, fill=INK, font=F(0, 15), spacing=3)
def arrow(p0, p1, col=ACC, w=4):
    d.line([p0, p1], fill=col, width=w); v = np.subtract(p1, p0); v = v / np.hypot(*v); n = np.array([-v[1], v[0]])
    b = np.array(p1) - v*16; d.polygon([tuple(p1), tuple(b + n*8), tuple(b - n*8)], fill=col)
# panel 1: close-up through port 1
panel(40, 120, 900, 900, f'1  Cut through USB port 1 (y = {S.SB_PORT_Y})')
P1, (pw, ph) = cut(S.SB_PORT_Y, (13.0, 33.5, 76.0, 82.6), 60, 60, 170, 860, 420)
zr0, zr1 = K.Z_TOP1 - S.USB_RING_D[1], K.Z_TOP1 - S.USB_RING_D[0]; zb = K.Z_POCKET + K.POCKET_LEAD
rx = K.PORT_X + S.USB_RING_H/2
marks = [((K.PORT_X, K.Z_TOP1 - 0.1), 'Mating face, flush with the top of the cup'),
         ((rx, (zr0 + zr1)/2), f'Silicone ring band, z {zr0:.1f} to {zr1:.1f}: squeezes ~0.12 mm a side in the bore'),
         ((rx + 0.15, (zb + K.Z_TOP1)/2 + 0.2), f'Full-size bore: only the top {zr1 - zb:.2f} mm of the ring band is in it'),
         ((rx + 0.15, K.Z_POCKET - 0.2), 'Housing pocket + 0.25 mm lead-in under the bore (the ring is loose here)'),
         ((16.0, K.FR_T1 - 0.4), 'Carrier top frame resting on the top wall (the pad pushes the core up)')]
for i, (pt, t) in enumerate(marks, 1):
    x, y = P1(*pt); d.ellipse([x-13, y-13, x+13, y+13], fill=ACC); d.text((x, y), str(i), fill=(255, 255, 255), font=F(1, 15), anchor='mm')
    d.ellipse([70-13, 640 + 34*i - 13, 70+13, 640 + 34*i + 13], fill=ACC); d.text((70, 640 + 34*i), str(i), fill=(255, 255, 255), font=F(1, 15), anchor='mm')
    d.text((95, 640 + 34*i - 9), t, fill=INK, font=F(0, 16))
d.multiline_text((60, 640 + 34*6), f'Not in this cut (the board is cut away under the connector): beside it the board top\nedge sits {K.BOARD_ZFLOAT} mm under the top wall. That edge is the hard stop when you PULL a plug.\nPushing a plug in has no hard stop near the port: see 2 and 3.', fill=INK, font=F(1, 16), spacing=5)
p = P1(K.PORT_X, K.Z_TOP1 + 0.6); arrow((p[0] + 40, p[1] - 30), (p[0] + 40, p[1] + 40), RED)
d.text((p[0] + 60, p[1] - 30), 'plug push 5-20 N', fill=RED, font=F(1, 16))
# panel 2: load path, cut through the pegs
panel(960, 120, 900, 900, f'2  Load path when you push a plug in (cut at the pegs, y = {S.CUP_PEGS[2][0]})')
P2, (pw2, ph2) = cut(S.CUP_PEGS[2][0], (-27.0, 35.0, -14.0, 88.0), 6, 980, 170, 520, 830)
tx2 = 980 + pw2 + 30
steps = [((K.PORT_X - 2, 84), 'USB plug pushes the receptacle\nand the board toward the cap', RED),
         ((S.sb_xb0 + 1, 68), 'Board rides on 4 pegs in slots:\n0.2 mm of z play (2.2 slot, 2.0 peg)', MUT),
         ((24.5, 72), 'Pegs belong to the 4 clip-on\nrails, keyed into the carrier', MUT),
         ((0, 40), 'Carrier + cells (the whole core)\nslide as one block', MUT),
         ((0, 0), f'TPU pad, {K.PAD_FILL:.0%} gyroid, printed\n{K.PAD_PROUD} mm proud: ~15-80 N preload.\nThe only thing resisting the push', RED),
         ((0, K.Z_MOUTH - 0.8), f'Cap. Overtravel posts (at y = 0, not\nin this cut) catch the core after {K.OT_GAP} mm', MUT)]
ty = 200
for (u, w), t, col in steps:
    note(P2(u, w), t, tx2, ty, col); ty += 120
# panel 3: engagement
x3, y3 = 1880, 120; panel(x3, y3, 840, 900, '3  How much ring stays in the full bore')
cases = [('Nominal', 0.0), ('Before (0.6 gap), worst', 0.6 + 0.1), (f'Now ({K.OT_GAP} gap), worst', K.OT_GAP + 0.1)]
z_hi, z_lo = K.Z_TOP1 + 0.3, K.Z_HOUSING0 - 0.3; sc = 230; top = y3 + 120
Z = lambda z: top + (z_hi - z) * sc
for i, (name, dz) in enumerate(cases):
    cx = x3 + 60 + i * 260
    d.rectangle([cx, Z(K.Z_TOP1), cx + 60, Z(zb)], fill=(214, 214, 208), outline=INK)          # full bore wall
    d.rectangle([cx, Z(zb), cx + 60, Z(K.Z_POCKET)], fill=(236, 236, 230), outline=INK)       # lead-in
    d.rectangle([cx, Z(K.Z_POCKET), cx + 60, Z(K.Z_TOP1 - K.TOP_T)], fill=(246, 246, 242), outline=MUT)  # pocket
    r0, r1 = zr0 - dz, zr1 - dz; ov = max(0, min(r1, K.Z_TOP1) - zb)
    col = GRN if ov >= 0.3 else (RED if ov <= 0.05 else (214, 140, 40))
    d.rectangle([cx + 66, Z(r1), cx + 100, Z(r0)], fill=col, outline=INK)
    d.text((cx - 10, y3 + 60), name, fill=INK, font=F(1, 17))
    d.text((cx - 10, Z(z_lo) + 20), f'core moved {dz:.1f} mm\nring in full bore: {ov:.2f} mm', fill=col, font=F(1, 16))
lx = x3 + 40; ly = Z(z_lo) + 110
for c, t in [((214, 214, 208), 'full-size seal bore (the ring seals here)'), ((236, 236, 230), '0.25 mm lead-in'), ((246, 246, 242), 'housing pocket (no seal)')]:
    d.rectangle([lx, ly, lx + 26, ly + 18], fill=c, outline=INK); d.text((lx + 36, ly), t, fill=INK, font=F(0, 15)); ly += 28
d.multiline_text((lx, ly + 10), 'Worst push = pad preload lower than the plug force, so\nthe core slides until the overtravel posts catch it,\nplus 0.1 mm of peg-slot play. Since 2026-10-31: 15 % pad\n(~15-80 N, above a normal plug-in) and a 0.3 mm post gap.', fill=MUT, font=F(0, 15), spacing=4)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'usb_port_retention.png'); img.save(out, optimize=True); print(out)
