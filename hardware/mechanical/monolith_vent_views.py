"""Vent close-up sheet: pack from below, bottom bumper off, and a cut through the vent (2026-10-31).
Run from hardware/mechanical: python monolith_vent_views.py -> vent_views.png"""
import sys, os; sys.path.insert(0, os.getcwd())
import numpy as np
from PIL import Image
import monolith_cup as K, monolith_side_renders as RR, monolith_cup_assembly_steps as AS
P = AS.split_parts(); L = AS.L
vx, vy = K.VENT_XY; zc = K.Z_MOUTH - K.CAP_T; zb = zc - K.BUMP_T_BOT
st = AS.Step(7, 'Pressure vent on the cap, under the bottom bumper',
             f'12 mm ePTFE patch over a 3 mm hole in the cap; bumper pocket {2*K.VENT_POCKET_R:.1f} mm with a cross-hatch grille and a breather groove to the board-face edge. No label hole.', 3)
allp = L(P, 'cup', 'label', 'screw', 'bumpt_band', 'bumpt_slab')
st.panel('Pack from below', [], allp + L(P, 'cap', 'vent', 'bumpb_band', 'bumpb_slab'), (0.55, -0.75, -0.9),
         notes=[((vx, vy, zb), f'45 deg TPU grille over the\n{2*K.VENT_POCKET_R:.1f} mm vent pocket ({K.VENT_GRILLE[1]} mm bars,\n{K.VENT_GRILLE[2] - K.VENT_GRILLE[1]:.1f} mm openings)'),
                ((K.X_OUT + 1, 0, zb + 0.4), 'Breather groove 1.2 x 0.8 mm:\nbreathes on a flat table'),
                ((-3, 0, zb), '"91 Wh" moved 2.5 mm\naway from the vent')])
st.panel('Bottom bumper off', allp + L(P, 'cap'), L(P, 'vent') + L(P, 'bumpb_band', 'bumpb_slab', o=(0, 0, -34)), (0.55, -0.75, -0.9),
         notes=[((vx, vy, zc - 0.5), '12 mm patch stuck on the\ncap plate, over the 3 mm hole'),
                ((vx, vy, zb - 34), 'Pocket through the 3 mm slab,\ngrille printed in its base')])
st.save()
img = Image.open(os.path.join(AS.OUT, 'step7.png')); os.remove(os.path.join(AS.OUT, 'step7.png'))
# section through y = vy, zoomed on the vent
px = 30.0; u0, u1, w0, w1 = 15.0, 35.0, -10.5, 6.0
W, H = int((u1 - u0) * px) + 40, int((w1 - w0) * px) + 40
sh = RR.Sheet(W, H)
A = [(k, V, c) for k, V, c in K.assembly() if k in ('cup', 'cap', 'pad', 'bumpb_band', 'bumpb_slab', 'vent', 'board', 'carrier', 'cell', 'oring', 'label', 'tails_wire', 'nickel')]
to_px = sh.section(A, 1, vy + 0.01, 0, 2, (20 - px*u0, 20 + px*w1), px)
sec = sh.img.resize((W, H), Image.LANCZOS)
pw, ph = AS.PW, AS.PH
x0 = 40 + 2 * (pw + 30); y0 = 128
from PIL import ImageDraw
d = ImageDraw.Draw(img)
s = min(520 / W, (ph - 80) / H); sec = sec.resize((int(W*s), int(H*s)), Image.LANCZOS)
img.paste(sec, (x0 + 20, y0 + 50))
d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], 8, outline=RR.RULE, width=1)
try:
    from PIL import ImageFont; f = ImageFont.truetype('DejaVuSans-Bold.ttf', 19); f2 = ImageFont.truetype('DejaVuSans.ttf', 14)
except Exception: f = f2 = None
d.text((x0 + 18, y0 + 14), f'Cut through the vent (y = {vy:g}), board face on the right', fill=RR.INK, font=f)
P_ = lambda u, w: (x0 + 20 + s*(20 + px*(u - u0)), y0 + 50 + s*(20 + px*(w1 - w)))
notes = [((vx, zc + 4), '~8 mm of air up to\nthe board edge'),
         ((vx, zc + K.CAP_T/2), '3 mm hole in the\n1.6 mm cap plate'),
         ((vx - 4.5, zc - K.VENT_T/2), 'Vent patch\n(1 mm drawn)'),
         ((vx + K.VENT_POCKET_R - 0.3, zb + 1.8), 'Pocket through the\n3 mm bumper slab'),
         ((vx - 1.2, zb + 0.5), 'Grille bars, 1 mm thick,\nflush with the base')]
tx = x0 + 20 + int(W*s) + 30; last = 0
for (u, w), t in notes:
    ax, ay = P_(u, w); ty = max(ay - 10, last); last = ty + 42
    d.line([(ax, ay), (tx - 8, ty + 9)], fill=(96, 98, 106), width=1); d.ellipse([ax-3, ay-3, ax+3, ay+3], fill=RR.INK)
    d.multiline_text((tx, ty), t, fill=RR.INK, font=f2, spacing=3)
img.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vent_views.png'), optimize=True); print(img.size)
