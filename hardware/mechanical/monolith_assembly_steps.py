"""Monolith side tray: assembly in six steps, one render each (same model as monolith_side_renders.py).
Run: python monolith_assembly_steps.py   (mechanical venv)  -> monolith_side_assembly.png
The written procedure, with the checks at each step, is docs/production/p0-assembly.md."""
import numpy as np
import monolith_shell as S
from monolith_side_renders import Sheet, camera, proj, C, INK, MUTED, RULE, ACCENT, assembly

MOD = ('holder', 'cell', 'mica', 'nickel', 'tails', 'wrap', 'frame', 'insul', 'board', 'ble', 'stand')
CELLS = ('holder', 'cell', 'mica', 'nickel', 'tails', 'wrap')
BOARD = ('board', 'ble', 'stand')
def lift(dz, dx=0.0): return {k: (dx, 0, dz) for k in MOD}
DROP = S.SB_WEDGE_T - S.SB_AXIAL_PRELOAD      # how low the module sits on its ring carrier before the lift
STEPS = [
    ('1  Cells welded, on the bench',
     'Weld the 4S pack: series strips, the split PACK tabs on C1 / C4\nand the three sense tails, all cut long. Mica cross, + rings,\nkapton on the CELL2 tail, ring carrier under the cells, liner.',
     CELLS, {}),
    ('2  Frame and board on, on the bench',
     'Top frame over the cells, fish paper on their board side. Lower\nthe board onto the frame bars with the seven tails through their\nslots. Solder on F.Cu, PACK- first, then trim.',
     MOD, {k: (12, 0, 0) for k in BOARD}),
    ('3  Test the module, on the bench',
     'Check the seven voltages, flash the CC2340, gauge training on\nthe SMBus pads, charge and discharge on each port at 100 W.\nConformal coat and staking last. Fix anything here.',
     MOD, {}),
    ('4  Module into the tray',
     'In through the open side, resting on its ring carrier: the board\nsits about 2.1 mm low, so the USB-C faces pass under the top wall.',
     ('shell',) + MOD, lift(-DROP, 10.0)),
    ('5  Lift and wedge',
     'Lift the module 2.5 mm: the USB-C faces enter the top wall and the\nboard edge seats on the stops. Push the PA12 wedge in under it from\nthe open side; its nose takes up the 0.4 mm preload.',
     ('shell',) + MOD + ('wedge', 'hold'), {'wedge': (14, 0, 0)}),
    ('6  Close',
     'Gap pad on the tall parts, ePTFE vent patch, silicone bead in\nthe cover joint, cover under the top lip (it traps the wedge),\n2 x M2 screws. Then the caps snap on over the ends.',
     ('shell', 'cell', 'board', 'cover', 'capb_soft', 'capb_firm', 'capb_corner', 'capb_band', 'capt_soft', 'capt_firm', 'capt_corner', 'capt_band'), {}),
]

if __name__ == '__main__':
    A = assembly()
    sh = Sheet(2700, 1560)
    sh.header('Assembly: one power module, built and tested on the bench',
              'Cells, TPU frame and board are joined on the bench by seven nickel tails and fully tested there. In the tray the module '
              'drops in, lifts 2.5 mm into the ports, and a wedge locks it. Nothing is soldered in the tray.')
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
    sh.text(40, 1530, 'Procedure and checks: docs/production/p0-assembly.md. Fish-paper rings, kapton, gap pad and vent patch are not drawn.', 14, fill=MUTED)
    sh.save('monolith_side_assembly.png')
    print('wrote monolith_side_assembly.png')
