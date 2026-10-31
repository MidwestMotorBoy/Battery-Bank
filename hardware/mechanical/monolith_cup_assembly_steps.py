"""Monolith P0 assembly, step by step: one sheet per step of docs/production/p0-assembly.md (2026-10-24).
Run: python monolith_cup_assembly_steps.py [step ...]   -> assembly_steps/step0.png ... step6.png
Each panel draws what is already built in muted colours and the parts that step adds in full colour, moved out along the
way they go on, with an arrow. Same meshes as monolith_cup.py (no NTCs, gel bead or solder drawn: they are callouts)."""
import os, sys, numpy as np
from PIL import Image
import monolith_shell as S, monolith_cup as K, monolith_side_renders as RR
from monolith_render import camera

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'assembly_steps')
SS, INK, MUTED, RULE, ACCENT = RR.SS, RR.INK, RR.MUTED, RR.RULE, RR.ACCENT
PW, PH = 860, 660                     # panel size; render box is the left part, callouts on the right
RW = 500

def mute(c): return tuple(int(0.30*v + 0.70*232) for v in c)
def cen(V): return V.mean(1)
def pick(V, m): return V[m]

def split_parts():
    """the assembly, with the strips, tails and sense wires split the way they go on"""
    A = K.assembly(); P = {}
    for k, V, c in A: P.setdefault(k, []).append((V, c))
    out = {k: v for k, v in P.items()}
    zc = lambda V: cen(V)[:, 2]
    (Vn, cn), = P['nickel']; out['strip_bot'] = [(pick(Vn, zc(Vn) < 40), cn)]; out['strip_top'] = [(pick(Vn, zc(Vn) >= 40), cn)]
    (Vt, ct), = P['tails']; out['pads'] = [(pick(Vt, zc(Vt) < 40), ct)]; out['tongues'] = [(pick(Vt, zc(Vt) >= 40), ct)]
    (Vs, cs), = P['tails_sense']; z, y = zc(Vs), cen(Vs)[:, 1]
    out['w_top'] = [(pick(Vs, z >= 40), cs)]; out['w_cell2'] = [(pick(Vs, (z < 40) & (np.abs(y) < 3)), cs)]
    out['w_kelvin'] = [(pick(Vs, (z < 40) & (np.abs(y) >= 3)), cs)]
    (Vi, ci), = P['insul']; c = cen(Vi)
    near = np.argmin([np.hypot(c[:, 0] - x, c[:, 1] - y) for x, y in K.CELLS], axis=0)
    out['cells'] = [(V, cc) for V, cc in P['cell']]
    out['insul_by_cell'] = [(pick(Vi, near == i), ci) for i in range(4)]
    (Vc, cc), = P['carrier']; out['carrier_bot'] = [(pick(Vc, zc(Vc) < 9.0), cc)]
    return out

class Step:
    def __init__(self, n, title, sub, panels):
        cols = min(3, panels); rows = (panels + cols - 1) // cols
        self.sh = RR.Sheet(40 + cols * (PW + 30), 130 + rows * (PH + 30)); self.n = n; self.k = 0; self.cols = cols
        self.sh.header(title, sub)

    def panel(self, title, done, new, view, arrows=(), notes=(), side_notes=None, fit_extra=(), holes=()):
        """done / new: [(V, colour, offset)]; arrows: [(3D from, 3D to)]; notes: [(3D point, text)]"""
        sh = self.sh; i = self.k; self.k += 1
        x0 = 40 + (i % self.cols) * (PW + 30); y0 = 128 + (i // self.cols) * (PH + 30)
        sh.rect(x0, y0, x0 + PW, y0 + PH, outline=RULE, r=8, width=1.2)
        sh.text(x0 + 18, y0 + 14, title, 19, True)
        R = camera(view)
        parts = [(K.mv(V, o), mute(c)) for V, c, o in done] + [(K.mv(V, o), c) for V, c, o in new]
        Q = np.vstack([p[0].reshape(-1, 3) for p in parts] + [np.asarray(fit_extra, float).reshape(-1, 3)]) @ R.T
        nh = 21 * len(side_notes or ()) + (12 if side_notes else 0)
        bx0, by0, bw, bh = x0 + 14, y0 + 56, RW, PH - 76 - nh
        px = 0.94 * min(bw / np.ptp(Q[:, 0]), bh / np.ptp(Q[:, 1]))
        org = (bx0 + bw/2 - px*(Q[:, 0].min() + Q[:, 0].max())/2, by0 + bh/2 + px*(Q[:, 1].min() + Q[:, 1].max())/2)
        sh.render(parts, R, org, px); pj = RR.proj(R, org, px)
        for p, r in holes: self.hole(pj(p), r * px)
        for a, b in arrows: self.arrow(pj(a), pj(b))
        if notes: self.callouts([(pj(p), t) for p, t in notes], x0 + RW + 50, y0 + 56, y0 + PH - 16)
        if side_notes:
            yy = y0 + PH - 14 - 21 * len(side_notes)
            for s in side_notes: sh.text(x0 + 24, yy, s, 14, fill=MUTED); yy += 21
        return pj

    def hole(self, p, r):
        x, y = p; r = max(r, 3.0)
        self.sh.g.ellipse([(x - r)*SS, (y - r)*SS, (x + r)*SS, (y + r)*SS], fill=(214, 182, 96), outline=INK, width=SS)

    def callouts(self, items, x, y_min, y_max, size=14, gap=10):
        """like Sheet.callouts, but the column is shifted up if it would run off the panel"""
        sh = self.sh; lh = size * 1.45; items = sorted(items, key=lambda it: it[0][1]); ys, y_prev = [], y_min
        for (ax, ay), s in items:
            h = lh * (s.count('\n') + 1); ty = max(ay - h/2, y_prev); ys.append(ty); y_prev = ty + h + gap
        over = y_prev - gap - y_max
        if over > 0:                                   # push up from the bottom, keeping the order and the gaps
            y_next = y_max
            for i in range(len(items) - 1, -1, -1):
                h = lh * (items[i][1].count('\n') + 1); ys[i] = min(ys[i], y_next - h); y_next = ys[i] - gap
        for ((ax, ay), s), ty in zip(items, ys):
            ym = ty + lh/2
            sh.line([(ax, ay), (x - 28, ym), (x - 10, ym)], (96, 98, 106), 1.2); sh.dot(ax, ay, 3.2)
            sh.text(x, ty, s, size, spacing=3)

    def arrow(self, p0, p1, w=3.0):
        sh = self.sh; (x0, y0), (x1, y1) = p0, p1
        d = np.array([x1 - x0, y1 - y0]); L = np.linalg.norm(d)
        if L < 1: return
        d /= L; n = np.array([-d[1], d[0]]); tip = np.array([x1, y1]); base = tip - d * 16
        sh.line([(x0, y0), tuple(base)], ACCENT, w)
        sh.g.polygon([tuple(v * SS) for v in (tip, base + n * 7, base - n * 7)], fill=ACCENT)

    def save(self):
        os.makedirs(OUT, exist_ok=True)
        p = os.path.join(OUT, f'step{self.n}.png')
        self.sh.img.resize((self.sh.W, self.sh.H), Image.LANCZOS).save(p, optimize=True); print('wrote', os.path.relpath(p, HERE))

def L(P, *keys, o=(0, 0, 0)): return [(V, c, o) for k in keys for V, c in P[k]]

# views: shell x = board normal (F.Cu faces +x), y across, z along the pack (port end up, cap down)
ISO = (1.0, -1.1, 0.65); LOW = (1.0, -1.1, -0.6); SIDE = (0.35, -1.0, 0.45); FACE = (1.0, 0.0, 0.0); BACK = (-1.0, 0.0, 0.0)
def hole_xyz(y, z): return (S.sb_xb1, y, z)

def step0(P):
    st = Step(0, '0   The bare board, before it meets the cells',
              'Power it from the cell simulator through the seven pack holes, flash it and set it up. Fix anything now: once it is on the pack, '
              'it comes off only by desoldering seven wires out of the gel.', 2)
    sl, ph = S.sb_slots(), S.sb_pack_holes()
    sim = [(ph['PACK-'], 'PACK-  (supply -)'), (sl['1N'], '1N  (supply -)'), (sl['CELL1'], 'CELL1  (ladder tap 1)'),
           (sl['CELL2'], 'CELL2  (ladder tap 2)'), (sl['CELL3'], 'CELL3  (ladder tap 3)'), (sl['4P'], '4P  (supply +)'), (ph['PACK+'], 'PACK+  (supply +)')]
    st.panel('0.2  Cell simulator into the seven holes (F.Cu)', [], L(P, 'board'), FACE,
             notes=[(hole_xyz(p[0], p[1]), t) for p, t in sim], holes=[(hole_xyz(p[0], p[1]), p[2] / 2 + 0.3) for p, _ in sim],
             side_notes=['Supply 14.0-14.8 V, 100 mA limit;', 'four 1 kOhm resistors make the taps.',
                         'Check the current, then 3V3 at TP301.'])
    st.panel('0.1 / 0.3  Inspect B.Cu, then flash and set up', [], L(P, 'board', 'ble'), BACK,
             notes=[((23.0, 16.6, 59.6), 'CC2340 module and the other\nhand-fitted B.Cu parts: loupe'),
                    ((25.3, -11.5, 40.0), 'Gap-filler zone: bare copper,\nno parts (|y| 7-16, z 27-53)')],
             side_notes=['Check R124 / R126 are NOT fitted (gauge note 16).', 'Flash the CC2340 (XDS110, Tag-Connect), load the',
                         'BQ25756 + TPS25751 config, gauge on the pogo pads.'])
    st.save()

def step1(P):
    st = Step(1, '1   Cells into the carrier and welded, on the bench',
              'Bottom strip and foam go in first, then the cells sideways, then the top strips and PACK pads are welded in place. '
              'From the first weld the pack is live: no metal bench, caps on the wire ends.', 5)
    st.panel('1.2 / 1.4  Foam rings, then the bottom strip', L(P, 'carrier_bot'), L(P, 'foam') + L(P, 'strip_bot', 'w_cell2', o=(0, 0, 14)), ISO,
             arrows=[((0, 0, 20), (0, 0, 7))],
             notes=[((-11.6, 11.6, 5.6), 'Foam ring in each pocket\n(C1 / C4: half ring, away\nfrom the PACK pads)'),
                    ((-5.0, 0.0, 20.0), 'Bottom strip C2+ to C3-,\nCELL2 wire soldered under\nits middle on the bench'),
                    ((14.0, 0.0, 19.6), 'Press the CELL2 wire into\nthe channel along y = 0')],
             side_notes=['Carrier drawn cut just above', 'the bottom frame.'])
    cells = P['cells']; done = L(P, 'carrier', 'foam', 'strip_bot', 'w_cell2'); new = []
    for i, ((V, c), (x, y)) in enumerate(zip(cells, K.CELLS)):
        o = (30 if x > 0 else -30, 0, 0)
        Vi, ci = P['insul_by_cell'][i]
        up = S.SB_CELLS[(int(np.sign(x)), int(np.sign(y)))][1] == 'top'
        new += [(V, c, o), (Vi, ci, (o[0], 0, 4 if up else -4))]
    st.panel('1.2 / 1.5  Insulator rings on, cells in sideways', done, new, SIDE,
             arrows=[((x + (42 if x > 0 else -42), y, 90), (x + (14 if x > 0 else -14), y, 90)) for x, y in K.CELLS[:2]],
             notes=[((11.6 + 30, -11.6, 81.4), 'Fish-paper ring on every + end\n(C1 / C3 top, C2 / C4 bottom)'),
                    ((-11.6 - 30, -11.6, 30), 'Back pair (C2, C3)\nfrom the back'),
                    ((11.6 + 30, -11.6, 30), 'Front pair (C1, C4) from the\nboard side, rails still off')],
             side_notes=['C1 and C3 + up, C2 and C4 + down.', 'Check the CELL2 wire is still in its channel.'])
    done = L(P, 'carrier', 'foam', 'strip_bot', 'w_cell2', 'cells', 'insul')
    st.panel('1.7  Weld the top strips (tongues to the board side)', done, L(P, 'strip_top', 'tongues', 'w_top'), (0.8, -0.9, 1.1),
             notes=[((-11.6, -11.6, 77.8), 'C1+ to C2- through the windows'),
                    ((-11.6, 11.6, 77.8), 'C3+ to C4-'),
                    ((22.0, -13.9, 77.5), 'CELL1 wire under the tongue end\n(soldered on the bench, before welding)'),
                    ((22.0, 13.9, 77.5), 'CELL3 wire, mirrored')],
             side_notes=['Slide each strip into the gap between the', 'cell ends and the top frame; push the cells',
                         'up against the top frame while welding.'])
    st.panel('1.7  Weld the PACK pads (bottom, wires already on)', done, L(P, 'pads', 'tails_wire', 'w_kelvin'), LOW,
             notes=[((11.6, -11.6, 6.0), 'PACK- pad on the C1 bottom:\n18 AWG power + 28 AWG Kelvin (1N)'),
                    ((11.6, 11.6, 6.0), 'PACK+ pad on the C4 bottom (+ cap):\npower + Kelvin (4P)'),
                    ((22.5, -13.0, 5.0), 'Both wires in the frame notch')],
             side_notes=['Weld spots >= 3 mm from the solder,', 'joints inside the weld window.',
                         'Cap the wire ends until soldered.'])
    done = L(P, 'carrier', 'foam', 'strip_bot', 'w_cell2', 'cells', 'insul', 'strip_top', 'tongues', 'w_top', 'pads', 'tails_wire', 'w_kelvin')
    st.panel('1.8  Rail blocks on', done, L(P, 'rails', o=(14, 0, 0)), ISO,
             arrows=[((48, -9, 72), (36, -9, 72)), ((48, -9, 12), (36, -9, 12))],
             notes=[((14 + 30.3, 9.0, 68.0), 'Peg posts point +x\n(toward the board)'),
                    ((14 + 20.5, -9.0, 60.0), 'Tongue presses into the key\nslot; crush ribs hold it'),
                    ((14 + 25.0, -9.0, 35.0), 'No rail over the gap-filler\nzone (z 25-55)')])
    st.save()

def step2(P):
    mod = L(P, 'carrier', 'foam', 'strip_bot', 'w_cell2', 'cells', 'insul', 'strip_top', 'tongues', 'w_top', 'pads', 'tails_wire', 'w_kelvin', 'rails')
    st = Step(2, '2   Gap filler and board on, on the bench',
              'About 4.5 g of GEL 30 on the two front cells, then the board down onto the posts with every '
              'wire through its hole, sleeves on, and the seven wires soldered from F.Cu in order.', 3)
    st.panel('2.1 / 2.2  Gap filler on the front cells', mod, L(P, 'filler'), (1.0, -0.55, 0.35),
             notes=[((24.0, -11.5, 40.0), 'About 2.3 g GEL 30 per zone,\na little proud (|y| 7-16, z 27-53)'),
                    ((24.0, -15.5, 29.0), 'Cover the zone\'s bottom corner too:\nthe C1 / C4 NTCs (TH101 / TH104)\nsit there on B.Cu')],
             side_notes=['Weigh it: tare the module on the scale.', 'No cure. Rework: peel, IPA, fresh gel.'])
    sl, ph = S.sb_slots(), S.sb_pack_holes()
    st.panel('2.3  Board onto the posts, then the sleeves', mod + L(P, 'filler'),
             L(P, 'board', 'ble', o=(22, 0, 0)) + L(P, 'sleeve', o=(40, 0, 0)), ISO,
             arrows=[((62, 0, 80), (50, 0, 80)), ((70, 8.6, 14), (60, 8.6, 14))],
             notes=[((22 + 26.9, -8.6, 68.0), 'Peg slots 2.6 x 2.2: the board\nfloats across, located along'),
                    ((40 + 27.4, 8.6, 14.0), 'TPU sleeve down each post\nuntil it touches F.Cu (no clamp)'),
                    ((22 + 26.9, -13.0, 6.0), 'Guide the seven pack wires\ninto their holes')])
    order = [(ph['PACK-'], '1  PACK-'), (sl['1N'], '2  1N'), (sl['CELL1'], '3  CELL1'), (sl['CELL2'], '4  CELL2'),
             (sl['CELL3'], '5  CELL3'), (sl['4P'], '6  4P'), (ph['PACK+'], '7  PACK+')]
    st.panel('2.4  Solder on F.Cu, in this order', mod + L(P, 'filler', 'ble'), L(P, 'board', 'sleeve'), FACE,
             notes=[(hole_xyz(p[0], p[1]), t) for p, t in order],
             side_notes=['USB unplugged. Trim each wire', 'about 0.5 mm proud.'])
    st.save()

def step3(P):
    mod = L(P, 'carrier', 'foam', 'strip_bot', 'w_cell2', 'cells', 'insul', 'strip_top', 'tongues', 'w_top', 'pads', 'tails_wire',
            'w_kelvin', 'rails', 'filler', 'ble')
    st = Step(3, '3   Test the module, on the bench',
              'Everything is still open: check the voltages, fit R124 / R126, program, run the function and 100 W thermal tests, then coat.', 2)
    sl, ph = S.sb_slots(), S.sb_pack_holes()
    st.panel('3.1  Seven voltages, then fit R124 / R126', mod, L(P, 'board', 'sleeve'), FACE,
             notes=[(hole_xyz(*ph['PACK-'][:2]), 'Reference: PACK-'),
                    (hole_xyz(*sl['CELL1'][:2]), 'CELL1: one cell up'),
                    (hole_xyz(*sl['CELL2'][:2]), 'CELL2: two cells'),
                    (hole_xyz(*sl['CELL3'][:2]), 'CELL3: three cells'),
                    (hole_xyz(*ph['PACK+'][:2]), 'PACK+ and 4P: four cells')],
             side_notes=['Each step 2.5-4.2 V. Only then fit', 'R124 and R126 (5.1 kOhm 0402, F.Cu).'])
    st.panel('3.3 / 3.4  Function test, then conformal coat', mod, L(P, 'board', 'sleeve'), ISO,
             notes=[((S.sb_port_x, -S.SB_PORT_Y, 78.6), 'Mask the USB-C seal rings'),
                    ((25.3, 16.6, 60.0), 'Keep coat off the antenna end'),
                    ((18.8, -19.8, 45.0), 'Thermocouple on a front cell\n(and one on a back cell)'),
                    ((26.9, 0.0, 40.0), 'No coat over the pogo pads\nor the gap-filler zone')],
             side_notes=['Charge and discharge on each port,', '100 W thermal run, gauge, BLE.'])
    st.save()

def step4(P):
    mod = L(P, 'carrier', 'foam', 'strip_bot', 'w_cell2', 'cells', 'insul', 'strip_top', 'tongues', 'w_top', 'pads', 'tails_wire',
            'w_kelvin', 'rails', 'filler', 'board', 'ble', 'sleeve')
    st = Step(4, '4   Module into the cup',
              'Port end first, from the bottom. The carrier frames guide it; the bores\' lead-ins take the USB-C rings in.', 1)
    st.panel('4.1 / 4.2  Push it home, square', L(P, 'cup'), [(V, c, (0, 0, -112)) for V, c, _ in mod], (1.0, -1.1, 0.35),
             arrows=[((0, 0, -32), (0, 0, -8))],
             notes=[((S.sb_port_x, S.SB_PORT_Y, K.Z_TOP1), 'USB-C seal bores in the closed top wall:\nboth rings go in together'),
                    ((K.X_OUT, -10, 40), 'Board face: 2.0 mm wall,\nposts stop 0.3 under it'),
                    ((-6.0, -17.0, 78.8 - 112), 'Push until the carrier top frame\nbears on the top wall')])
    st.save()

def step5(P):
    built = L(P, 'cup')
    st = Step(5, '5   Cap',
              'Check the pad height, grease the O-ring into the skirt groove, push the cap in to its hard stop, then two M2 screws through the cup wall.', 2)
    st.panel('5.1-5.3  Pad and O-ring on the cap, cap in', built,
             L(P, 'pad', o=(0, 0, -22)) + L(P, 'oring', o=(0, 0, -40)) + L(P, 'cap', o=(0, 0, -40)), LOW,
             arrows=[((5, -30, -60), (5, -30, -14))],
             notes=[((22.1, 0, -22 - 2), 'TPU pad: ~1.2 mm proud,\npreloads the core'),
                    ((30.6, 0, -40 + 1), 'O-ring in the skirt groove,\nsilicone-safe grease'),
                    ((34.2, -20, -40 - 5), 'Push until the plate lands on\nthe rim')])
    st.panel('5.4  Two M2 screws through the cup wall', built + L(P, 'pad', 'oring', 'cap'),
             [(V, c, (0, -12 if cen(V)[:, 1].mean() < 0 else 12, 0)) for V, c in [(pick(V, cen(V)[:, 1] < 0), c) for V, c in P['screw']]
              + [(pick(V, cen(V)[:, 1] >= 0), c) for V, c in P['screw']]], LOW,
             arrows=[((16, -44, -2), (16, -30, -2))],
             notes=[((16, -38.9, -2), 'M2 x 6 thread-forming, into\nthe blind skirt boss'),
                    ((16, 26.9 + 12, -2), 'Same on the other side')],
             side_notes=['Snug, not tight: they sit below the', 'O-ring and the pilots stop 1.2 mm short.'])
    st.save()

def step6(P):
    built = L(P, 'cup', 'cap', 'screw')
    st = Step(6, '6   Leak test, bumpers',
              'No vent: the pack is sealed for good. Soap the joints, pull a vacuum round the pack in a jar, then press the bumpers on.', 2)
    st.panel('6.1  Vacuum-jar bubble test', L(P, 'cup'), L(P, 'cap', 'screw'), (1.0, -0.7, 0.3),
             notes=[((K.X_OUT, -K.YI, K.Z_MOUTH + 3), 'Soap film on the cap seam\nand the two screw heads'),
                    ((S.sb_port_x, S.SB_PORT_Y, K.Z_TOP1), 'Soap film on both USB-C ports'),
                    ((K.X_OUT, 0, 40), 'Pull -20 kPa, watch 5 min:\ngrowing bubbles = a leak')],
             side_notes=['Fit print first, to -50 kPa (a warm pack at 4300 m):', 'side flats measured before and after.'])
    st.panel('6.2  Bumpers on', built,
             L(P, 'bumpt_band', 'bumpt_slab', o=(0, 0, 22)) + L(P, 'bumpb_band', 'bumpb_slab', o=(0, 0, -22)), (1.0, -1.1, 0.35),
             arrows=[((0, -30, 115), (0, -30, 100)), ((0, -30, -40), (0, -30, -25))],
             notes=[((S.sb_port_x, S.SB_PORT_Y, 88.6 + 22), 'Top bumper: port well\nover the USB-C'),
                    ((0, -26.6, -9.9 - 22), 'Bottom bumper over the mouth,\npockets over the screw heads')])
    st.save()

STEPS = [step0, step1, step2, step3, step4, step5, step6]
if __name__ == '__main__':
    P = split_parts()
    for i in (map(int, sys.argv[1:]) if len(sys.argv) > 1 else range(len(STEPS))): STEPS[i](P)
