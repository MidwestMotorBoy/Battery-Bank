"""Monolith side tray: assembly in six steps, one render each (same model as monolith_side_renders.py).
Run: python monolith_assembly_steps.py   (mechanical venv)  -> monolith_side_assembly.png
The written procedure, with the checks at each step, is docs/production/p0-assembly.md."""
import numpy as np
import monolith_shell as S
from monolith_side_renders import Sheet, camera, proj, C, INK, MUTED, RULE, ACCENT, assembly

STEPS = [
    ('1  Cell module in its frame, on the bench',
     'Weld the 4S pack (series strips, PACK tabs on C1 / C4), mica cross,\n+ rings, liner. Slide it into the TPU top frame; solder the five sense\nleads to the strip and the two 18 AWG PACK leads to their tabs.',
     ('cell', 'mica', 'nickel', 'wire', 'lead', 'wrap', 'frame', 'strip'), {}),
    ('2  Prepare the tray',
     'Drop the TPU bottom holder into the floor zone: spring rings\nup, open over the C2 / C4 + caps.',
     ('shell', 'holder'), {}),
    ('3  Cell module in',
     'Slide the framed module in through the open side. The crush\nribs squeeze the liner, the rings preload the ends. PACK leads\ngo down into the gap below the board zone.',
     ('shell', 'holder', 'cell', 'mica', 'nickel', 'wire', 'lead', 'wrap', 'frame', 'strip'), {}),
    ('4  Board in, over the two PACK leads',
     'Lower the board 2.5 mm low, threading the PACK leads through\ntheir holes; the spring contacts land on the sense strip. Slide it\nup: the USB-C faces enter the top wall, the contacts wipe 2.5 mm.',
     ('shell', 'holder', 'cell', 'mica', 'nickel', 'wire', 'lead', 'wrap', 'frame', 'strip', 'insul', 'board', 'ble', 'stand', 'contacts'),
     {'board': (16, 0, -S.SB_SLIDE), 'ble': (16, 0, -S.SB_SLIDE), 'stand': (16, 0, -S.SB_SLIDE), 'contacts': (16, 0, -S.SB_SLIDE)}),
    ('5  Shim, solder, program, test',
     'Fit the shim under the board. Solder the two PACK leads on F.Cu,\nPACK- first, and trim. Check the five sense voltages, then\nprogram and test through the pogo pads / Tag-Connect.',
     ('shell', 'holder', 'cell', 'mica', 'nickel', 'wire', 'lead', 'wrap', 'frame', 'strip', 'insul', 'board', 'ble', 'stand', 'contacts', 'shim', 'hold'), {}),
    ('6  Close',
     'Gap pad on the tall parts, ePTFE vent patch, silicone bead in\nthe cover joint, cover under the top lip, 2 x M2 screws. Then\nthe caps snap on over the ends.',
     ('shell', 'cell', 'board', 'cover', 'capb_soft', 'capb_firm', 'capb_corner', 'capb_band', 'capt_soft', 'capt_firm', 'capt_corner', 'capt_band'), {}),
]

if __name__ == '__main__':
    A = assembly()
    sh = Sheet(2700, 1560)
    sh.header('Assembly: a framed cell module and the board',
              'The framed cell module is built and tested on the bench and goes in first. The board drops in over two PACK leads; '
              'five spring contacts on B.Cu pick up the sense strip. Only two joints are soldered inside the tray.')
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
