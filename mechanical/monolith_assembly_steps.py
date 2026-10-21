"""Monolith side tray: assembly in six steps, one render each (same model as monolith_side_renders.py).
Run: python monolith_assembly_steps.py   (mechanical venv)  -> monolith_side_assembly.png
The written procedure, with the checks at each step, is docs/production/p0-assembly.md."""
import numpy as np
import monolith_shell as S
from monolith_side_renders import Sheet, camera, proj, C, INK, MUTED, RULE, ACCENT, assembly

STEPS = [
    ('1  Cell module, on the bench',
     'Weld the 4S pack: series strips, PACK tabs on C1 and C4.\nSolder the five leads to the nickel before welding near the cans.\nMica cross, + end rings, fish-paper liner, top EVA pad.',
     ('cell', 'mica', 'nickel', 'wire', 'lead', 'wrap', 'pad_top'), {}),
    ('2  Prepare the tray',
     'Floor spacer (TPU) and the 1 mm EVA floor pad in the\nfloor zone, cut-outs over the C2 / C4 + caps.',
     ('shell', 'pad_floor', 'eva_floor'), {}),
    ('3  Cell module in',
     'Slide the module in through the open side. The crush ribs\nsqueeze the liner. Route the leads: taps up the groove,\nPACK leads down into the gap below the board zone.',
     ('shell', 'pad_floor', 'eva_floor', 'cell', 'mica', 'nickel', 'wire', 'lead', 'wrap', 'pad_top'), {}),
    ('4  Board in, over the leads',
     'Fish paper and EVA lanes on the cells. Lower the board 2.5 mm\nlow, threading the five leads through their holes from B.Cu,\nthen slide it up so the USB-C faces enter the top wall.',
     ('shell', 'pad_floor', 'eva_floor', 'cell', 'mica', 'nickel', 'wire', 'lead', 'wrap', 'pad_top', 'insul', 'lanes', 'board', 'ble', 'stand'),
     {'board': (16, 0, -S.SB_SLIDE), 'ble': (16, 0, -S.SB_SLIDE), 'stand': (16, 0, -S.SB_SLIDE)}),
    ('5  Shim, solder, program, test',
     'Fit the shim under the board. Solder the leads on F.Cu in the\ndatasheet order (see the doc), trim. Program and test through\nthe pogo pads / Tag-Connect while it is open.',
     ('shell', 'pad_floor', 'eva_floor', 'cell', 'mica', 'nickel', 'wire', 'lead', 'wrap', 'pad_top', 'insul', 'lanes', 'board', 'ble', 'stand', 'shim', 'hold'), {}),
    ('6  Close',
     'Gap pad on the tall parts, ePTFE vent patch, silicone bead in\nthe cover joint, cover under the top lip, 2 x M2 screws. Then\nthe caps snap on over the ends.',
     ('shell', 'cell', 'board', 'cover', 'capb_soft', 'capb_firm', 'capb_corner', 'capb_band', 'capt_soft', 'capt_firm', 'capt_corner', 'capt_band'), {}),
]

if __name__ == '__main__':
    A = assembly()
    sh = Sheet(2700, 1560)
    sh.header('Assembly: two subassemblies joined by five leads',
              'The cell module is built and tested on the bench, goes into the tray first, and the board drops in over its leads. '
              'All soldering happens on F.Cu from the open side, away from the cells.')
    R = camera((1.0, -0.8, 0.5))
    for i, (title, text, keys, moves) in enumerate(STEPS):
        col, row = i % 3, i // 3
        x0, y0 = 40 + col * 890, 130 + row * 690
        sh.panel_title(x0, y0, title, 840)
        parts = [(V + np.array(moves.get(k, (0, 0, 0))), c) for k, V, c in A if k in keys]
        pxi = 3.5 if i == 5 else 3.9
        o = (x0 + 330, y0 + (500 if i == 5 else 480))
        sh.render(parts, R, o, pxi)
        sh.text(x0, y0 + 575, text, 14, fill=INK, spacing=5)
    sh.line([(40, 1520), (2660, 1520)], RULE, 1.5)
    sh.text(40, 1530, 'Procedure and checks: docs/production/p0-assembly.md. Rings, gap pad and vent patch are not drawn.', 14, fill=MUTED)
    sh.save('monolith_side_assembly.png')
    print('wrote monolith_side_assembly.png')
