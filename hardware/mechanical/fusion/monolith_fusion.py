"""Monolith pack as a parametric Autodesk Fusion model, built by the Fusion Python API from the numbers in
hardware/mechanical/monolith_cup.py (pack frame: z along the cells, +x toward the board, y across; mm).

Each part is its own component ('Cup (parametric)', 'Cap (parametric)', ...) driven by shared User Parameters, with
offset construction planes, fully constrained sketches and ordinary features, so a wall or a clearance can be changed in
Modify > Change Parameters and the parts rebuild. Positions that come from the KiCad board (the wall pockets over
L401 / L501) are fixed sketch geometry, not parameters.

Run inside Fusion (Utilities > Scripts and Add-ins, or through the Fusion MCP with a shim that exec()s this file and
calls run()). PARTS selects what to (re)build; a part that exists is deleted and rebuilt. Fusion 2705+: the active
design must be a Hybrid or Assembly design (the script switches a Part design to Hybrid).
Reference check: import the STEPs from hardware/mechanical/step/ (monolith_step.py) and compare volumes; the cup came
out 32496.5 mm3 against the mesh model's 32484.6 (true arcs vs 48-gon facets, <= 0.03 mm everywhere)."""
import adsk.core, adsk.fusion

PARTS = ['cup', 'cap']

PARAMS = [  # name, expression, comment (order matters: a parameter may use the ones above it)
    # cells and the cup section
    ('CellPitch', '11.625 mm', 'cell centre offset from the pack axis (x and y)'),
    ('CellR', '10.925 mm', 'cell radius (FEB 21700G, 21.85 dia)'),
    ('CellClr', '0.2 mm', 'cup inside to the cells'),
    ('YI', 'CellPitch + CellR + CellClr', 'inside half-width'),
    ('RBack', 'CellR + CellClr', 'inside back corner radius'),
    ('XIn', '30.6 mm', 'inside face over the board (sb_xb1 + SB_OUT_H + 0.5)'),
    ('RFront', '4 mm', 'inside front corner radius (>= 2 x O-ring cord)'),
    ('Wall', '1.6 mm', 'side and back wall, MJF PA12'),
    ('WallBF', '2.0 mm', 'board-face wall'),
    ('TopT', '1.85 mm', 'top wall'),
    ('ZTop', '80.6 mm', 'top of the cup (SB_H)'),
    ('ZMouth', '-4.35 mm', 'open bottom end'),
    ('SkirtL', '7.5 mm', 'cap skirt length = cup mouth to skirt top'),
    ('MouthT', '2.4 mm', 'wall thickness over the mouth band'),
    ('MouthH', 'SkirtL', 'mouth band height'),
    ('MouthTaper', '0.8 mm', 'taper back to Wall at the top of the band'),
    ('MouthLead', '0.8 mm', 'O-ring lead-in step height at the mouth'),
    ('MouthLeadD', '0.3 mm', 'O-ring lead-in step depth'),
    # USB-C ports
    ('PortX', '26.927 mm', 'USB-C port centre (x)'),
    ('PortY', '6.5 mm', 'USB-C port centre offset (+-y)'),
    ('RingW', '10.35 mm', 'USB-C seal ring outside width (rev A4)'),
    ('RingH', '4.57 mm', 'USB-C seal ring outside height'),
    ('RingR', '1.97 mm', 'USB-C seal ring corner radius'),
    ('RingD', '1.5 mm', 'ring back edge below the top face'),
    ('UsbSq', '0.15 mm', 'seal squeeze per side (bore = ring - 2 x UsbSq)'),
    ('HousW', '10.05 mm', 'USB-C front housing width'),
    ('HousH', '3.868 mm', 'USB-C front housing height'),
    ('HousR', '0.51 mm', 'USB-C front housing corner radius'),
    ('HousClr', '0.15 mm', 'pocket clearance round the housing'),
    ('BoardZFloat', '0.1 mm', 'board top edge float under the top wall'),
    ('PocketLead', '0.25 mm', 'loft from the ring outline to the seal bore'),
    # radial M2 screws through the mouth band into the cap skirt bosses
    ('ScrewX', '16 mm', 'M2 cap screws: x'),
    ('ScrewDZ', '2.4 mm', 'M2 cap screws: height above the mouth'),
    ('ScrewHoleR', '1.1 mm', 'M2 clearance hole radius (cup)'),
    ('CboreR', '2.1 mm', 'counterbore radius (cup)'),
    ('CboreD', '0.8 mm', 'counterbore depth (cup)'),
    ('WallPocketD', '0.5 mm', 'pockets over L401 / L501 in the board-face wall'),
    # cap
    ('CapT', '1.6 mm', 'cap plate below the mouth (lands on the cup rim)'),
    ('CapClr', '0.1 mm', 'cap skirt to the cup bore, radial'),
    ('SkirtT', '2.6 mm', 'radial skirt wall'),
    ('GrooveD', '1.4 mm', 'O-ring groove depth (2.0 mm cord, ~25 % squeeze)'),
    ('GrooveZ0', '3.9 mm', 'groove bottom above the mouth'),
    ('GrooveW', '2.6 mm', 'groove width (z)'),
    ('BossR', '2.6 mm', 'screw boss radius'),
    ('BossDepth', '5 mm', 'screw boss depth (y)'),
    ('PilotR', '0.8 mm', 'M2 thread-forming pilot radius'),
    ('PilotSolid', '1.2 mm', 'solid behind each blind pilot'),
    ('FrB0', '4.25 mm', 'carrier bottom frame underside (z)'),
    ('OTR', '1.5 mm', 'overtravel post radius'),
    ('OTGap', '0.3 mm', 'overtravel post to the frame underside at nominal'),
    ('OTInset', '2.6 mm', 'side posts: in from the cell envelope'),
    ('VentX', '25.6 mm', 'ePTFE vent hole x (y = 0)'),
    ('VentHoleR', '1.5 mm', 'vent hole radius'),
    # carrier (one-piece PA12: two frames, spines, front-back webs)
    ('ZCell0', '6.3 mm', 'cell bottom ends'),
    ('ZCell1', '77.4 mm', 'cell top ends'),
    ('TabT', '0.4 mm', 'nickel strip thickness over the top ends'),
    ('FrameT', '1.6 mm', 'bottom frame thickness'),
    ('WinR', '7 mm', 'weld / + cap windows in the frames'),
    ('SpineHW', '1.5 mm', 'spine half-width'),
    ('SpineL', '5.2 mm', 'spine depth in from the cell envelope'),
    ('WebX', '2 mm', 'front-back web half-width (x)'),
    ('WebIn', '4.5 mm', 'web half-length about the cell row (y)'),
    ('WebClr', '0.05 mm', 'web to the cells'),
    ('WebLink', '0.6 mm', 'web link out to the side spine, half-width'),
    ('KeyDepth', '2 mm', 'rail tongue length into the frame'),
    ('KeyClr', '0.1 mm', 'key slot clearance all round'),
    ('KeyB0', '5.4 mm', 'bottom tongue |y| from'),
    ('KeyB1', '7.4 mm', 'bottom tongue |y| to'),
    ('KeyT0', '7.5 mm', 'top tongue |y| from'),
    ('KeyT1', '10.5 mm', 'top tongue |y| to'),
    ('RailX0', 'CellPitch + CellR + 0.15 mm', 'rails stand 0.15 off the front cans'),
    ('BoardB', '25.3 mm', 'board B.Cu face (sb_xb0)'),
    ('NotchX0', 'CellPitch + 3 mm', 'PACK wire notch starts (x)'),
    ('PackY', '13.025 mm', 'PACK+/- pad hole |y|'),
    ('KSlotY', '8.725 mm', 'Kelvin slot |y| (1N / 4P)'),
    ('PWireOD', '1.8 mm', '18 AWG pack wire OD'),
    ('KWireOD', '0.75 mm', '28 AWG Kelvin wire OD'),
    ('NotchClr', '0.2 mm', 'wire notch clearance each side'),
    ('FoamPocket', '0.6 mm', 'foam ring pocket depth in the bottom frame'),
    ('FoamR0', 'WinR - 0.3 mm', 'foam pocket inner radius'),
    ('FoamR1', 'CellR - 1.0 mm', 'foam pocket outer radius'),
    ('FoamTrim', '0.8 mm', 'C1 / C4 pockets stop this far short of the cell centre (board side)'),
    ('ChW', '1 mm', 'CELL2 sense channel width'),
    ('ChD', '0.95 mm', 'CELL2 sense channel depth'),
    ('ChPocket', '2 mm', 'solder pocket half-width at the channel start'),
    # board rails (four clip-on PA12 blocks) and the TPU retaining sleeves
    ('BoardT', '1.6 mm', 'board thickness'),
    ('BarY0', '6.5 mm', 'rail block |y| from'),
    ('BarY1', '11.3 mm', 'rail block |y| to'),
    ('BarZ0', '7.3 mm', 'bottom block full width from (z)'),
    ('RailGap0', '25 mm', 'bottom blocks stop here (gap filler zone)'),
    ('RailGap1', '55 mm', 'top blocks start here'),
    ('RailReliefY', '7.6 mm', 'below BarZ0 the bottom blocks keep only |y| <= this (PACK / Kelvin wires pass)'),
    ('PegY', '8.6 mm', 'board peg |y|'),
    ('PegZ0', '14 mm', 'lower pegs z'),
    ('PegZ1', '68 mm', 'upper pegs z'),
    ('PegD', '2 mm', 'peg post diameter'),
    ('PostGap', '0.3 mm', 'post tips to the board-face wall'),
    ('HousD', '2.5 mm', 'USB-C front housing depth behind the port face'),
    ('RibH', '0.25 mm', 'tongue crush rib height'),
    ('RibW', '0.5 mm', 'tongue crush rib width (z)'),
    ('RibLead', '0.4 mm', 'crush rib ramp length from the tongue tip'),
    ('SleeveR', '1.9 mm', 'TPU retaining sleeve outer radius'),
    ('SleeveBore', '0.85 mm', 'sleeve bore radius (grips the post)'),
    ('SleeveH', '1 mm', 'sleeve height above F.Cu'),
]
WALL_POCKETS = [(7.9608, 15.6608, 44.9671, 52.7671), (-15.0650, -7.3650, 44.9607, 52.7607)]   # L401, L501 (y0, y1, z0, z1)
POCKET_MARGIN, POCKET_R = 0.5, 1.0

cm = lambda v: v / 10.0
VI = adsk.core.ValueInput.createByString
OP = adsk.fusion.FeatureOperations
NEW, JOIN, CUT = OP.NewBodyFeatureOperation, OP.JoinFeatureOperation, OP.CutFeatureOperation
DO = adsk.fusion.DimensionOrientations
HOR, VER = DO.HorizontalDimensionOrientation, DO.VerticalDimensionOrientation


def P3(x, y, z=0.0):
    return adsk.core.Point3D.create(cm(x), cm(y), cm(z))


class Part:
    """one component plus the sketch / feature helpers"""

    def __init__(self, des, name):
        self.des, self.um = des, des.unitsManager
        root = des.rootComponent
        for o in [o for o in root.occurrences if o.component.name == name]:
            o.deleteMe()
        self.occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        self.comp = self.occ.component
        self.comp.name = name
        self.ext = self.comp.features.extrudeFeatures
        self.body = None

    def ev(self, e):
        return self.um.evaluateExpression(e, 'mm') * 10.0

    def plane(self, base, expr, name):
        pi = self.comp.constructionPlanes.createInput()
        pi.setByOffset(base, VI(expr))
        pl = self.comp.constructionPlanes.add(pi)
        pl.name = name
        return pl

    def zplane(self, expr, name):
        return self.plane(self.comp.xYConstructionPlane, expr, name)

    def yplane(self, expr, name):
        return self.plane(self.comp.xZConstructionPlane, expr, name)

    def sketch(self, pl, name):
        sk = self.comp.sketches.add(pl)
        sk.name = name
        return sk

    # ---- sketch geometry ----
    def rrect(self, sk, x0, x1, y0, y1, r, e):
        """rounded rectangle in an XY-offset sketch (sketch coords = world x, y), radii r = (x0y0, x1y0, x1y1, x0y1);
        e = expressions: distance from the sketch origin to each edge (left, right, bottom, top), then the 4 radii"""
        L = sk.sketchCurves.sketchLines.addTwoPointRectangle(P3(x0, y0), P3(x1, y1))

        def edge(test):
            for i in range(L.count):
                l = L.item(i)
                if test(l.startSketchPoint.geometry, l.endSketchPoint.geometry):
                    return l
        left = edge(lambda a, b: abs(a.x - cm(x0)) < 1e-6 and abs(b.x - cm(x0)) < 1e-6)
        right = edge(lambda a, b: abs(a.x - cm(x1)) < 1e-6 and abs(b.x - cm(x1)) < 1e-6)
        bot = edge(lambda a, b: abs(a.y - cm(y0)) < 1e-6 and abs(b.y - cm(y0)) < 1e-6)
        top = edge(lambda a, b: abs(a.y - cm(y1)) < 1e-6 and abs(b.y - cm(y1)) < 1e-6)
        gc = sk.geometricConstraints
        for l, horiz in ((left, False), (right, False), (bot, True), (top, True)):
            try:
                gc.addHorizontal(l) if horiz else gc.addVertical(l)
            except Exception:
                pass                                                  # already constrained
        d = 0.01
        corners = [(left, bot, x0, y0, 1, 1), (right, bot, x1, y0, -1, 1), (right, top, x1, y1, -1, -1), (left, top, x0, y1, 1, -1)]
        A = [sk.sketchCurves.sketchArcs.addFillet(l1, P3(x, y + sy * d), l2, P3(x + sx * d, y), cm(rr))
             for (l1, l2, x, y, sx, sy), rr in zip(corners, r)]
        D, o = sk.sketchDimensions, sk.originPoint
        for line, orient, ex, tp in ((left, HOR, e[0], P3(x0 - 3, 0)), (right, HOR, e[1], P3(x1 + 3, 0)),
                                     (bot, VER, e[2], P3(0, y0 - 3)), (top, VER, e[3], P3(0, y1 + 3))):
            D.addDistanceDimension(o, line.startSketchPoint, orient, tp).parameter.expression = ex
        for a, ex in zip(A, e[4:]):
            dm = None
            for i in range(D.count):
                x = D.item(i)
                if isinstance(x, adsk.fusion.SketchRadialDimension) and x.entity == a:
                    dm = x
            if dm is None:
                c, m = a.centerSketchPoint.geometry, a.geometry.startPoint
                dm = D.addRadialDimension(a, adsk.core.Point3D.create(c.x + (m.x - c.x) * 1.5, c.y + (m.y - c.y) * 1.5, 0))
            dm.parameter.expression = ex
        return sk

    def rect(self, sk, ex0, ex1, ey0, ey1):
        """plain rectangle in an XY-offset sketch from signed edge expressions (x0, x1, y0, y1), each edge dimensioned
        to the sketch origin"""
        x0, x1, y0, y1 = (self.ev(e) for e in (ex0, ex1, ey0, ey1))
        L = sk.sketchCurves.sketchLines.addTwoPointRectangle(P3(x0, y0), P3(x1, y1))
        gc, D, o = sk.geometricConstraints, sk.sketchDimensions, sk.originPoint
        for i in range(L.count):
            l = L.item(i)
            a, b = l.startSketchPoint.geometry, l.endSketchPoint.geometry
            vert = abs(a.x - b.x) < 1e-9
            try:
                gc.addVertical(l) if vert else gc.addHorizontal(l)
            except Exception:
                pass
            v = a.x if vert else a.y
            ex = None
            for val, e in ((x0, ex0), (x1, ex1)) if vert else ((y0, ey0), (y1, ey1)):
                if abs(cm(val) - v) < 1e-9:
                    ex = e
            tp = P3(v * 10 + 1, 0) if vert else P3(0, v * 10 + 1)
            dm = D.addDistanceDimension(o, l.startSketchPoint, HOR if vert else VER, tp)
            dm.parameter.expression = 'abs(%s)' % ex
        return L

    def circle_s(self, sk, exx, exy, er):
        """circle in an XY-offset sketch at signed expressions (x, y), radius er; centre dimensioned to the origin, or
        put on an axis when a coordinate is 0"""
        x, y = self.ev(exx), self.ev(exy)
        # drawn slightly off and then driven onto place by the dims: a centre drawn exactly in line with another
        # circle's centre makes the solver call the second dimension over-constraining
        dx = 0.0 if abs(x) < 1e-9 else 0.31
        dy = 0.0 if abs(y) < 1e-9 else 0.17
        ci = sk.sketchCurves.sketchCircles.addByCenterRadius(P3(x + dx, y + dy), cm(self.ev(er) * 1.01))
        D, o, cp, gc = sk.sketchDimensions, sk.originPoint, ci.centerSketchPoint, sk.geometricConstraints
        D.addDiameterDimension(ci, P3(x + 2, y + 2)).parameter.expression = '2 * (%s)' % er
        if abs(x) > 1e-9:
            D.addDistanceDimension(o, cp, HOR, P3(x, y - 2)).parameter.expression = 'abs(%s)' % exx
        else:
            gc.addVerticalPoints(o, cp)
        if abs(y) > 1e-9:
            D.addDistanceDimension(o, cp, VER, P3(x + 2, y)).parameter.expression = 'abs(%s)' % exy
        else:
            gc.addHorizontalPoints(o, cp)
        return ci

    def outline(self, sk, gx0, gx1, gy, grb, grf):
        """the cup section family grown by expressions: x from -(YI + gx0) to XIn + gx1, y +-(YI + gy),
        back corner radius RBack + grb, front RFront + grf ('0' = no growth; negative growth as '(-expr)')"""
        g = lambda base, s: base if s == '0' else '(%s + %s)' % (base, s)
        ev = self.ev
        x0, x1, h = -ev(g('YI', gx0)), ev(g('XIn', gx1)), ev(g('YI', gy))
        rb, rf = ev(g('RBack', grb)), ev(g('RFront', grf))
        return self.rrect(sk, x0, x1, -h, h, (rb, rf, rf, rb),
                          [g('YI', gx0), g('XIn', gx1), g('YI', gy), g('YI', gy),
                           g('RBack', grb), g('RFront', grf), g('RFront', grf), g('RBack', grb)])

    def outline_off(self, sk, off):
        """the inside section offset by one expression all round (rounded-offset: radii grow with it)"""
        return self.outline(sk, off, off, off, off, off)

    def circle(self, sk, wpt, rexpr, ex_h=None, ex_v=None, on_h_axis=False, on_v_axis=False):
        """circle at world point wpt (mm, 3-tuple) with a diameter dim; its centre is dimensioned to the sketch origin
        along the sketch's horizontal / vertical (ex_h / ex_v), or put on that axis (on_*_axis), else fixed"""
        c = sk.modelToSketchSpace(P3(*wpt))
        ci = sk.sketchCurves.sketchCircles.addByCenterRadius(c, cm(self.ev(rexpr)))
        D, o, cp = sk.sketchDimensions, sk.originPoint, ci.centerSketchPoint
        D.addDiameterDimension(ci, adsk.core.Point3D.create(c.x + 0.4, c.y + 0.4, 0)).parameter.expression = '2 * (%s)' % rexpr
        gc = sk.geometricConstraints
        if ex_h:
            D.addDistanceDimension(o, cp, HOR, adsk.core.Point3D.create(c.x, c.y - 0.5, 0)).parameter.expression = ex_h
        if ex_v:
            D.addDistanceDimension(o, cp, VER, adsk.core.Point3D.create(c.x + 0.5, c.y, 0)).parameter.expression = ex_v
        if on_h_axis:
            gc.addHorizontalPoints(o, cp)
        if on_v_axis:
            gc.addVerticalPoints(o, cp)
        if not (ex_h or on_v_axis) or not (ex_v or on_h_axis):
            if not (ex_h or ex_v or on_h_axis or on_v_axis):
                cp.isFixed = True
        return ci

    def axes(self, sk):
        """which sketch axis world x and z run along: returns (x_is_sketch_h, sign_x, sign_z) for an XZ-family sketch"""
        s0, sx, sz = (sk.modelToSketchSpace(P3(*p)) for p in ((0, 0, 0), (1, 0, 0), (0, 0, 1)))
        x_h = abs(sx.x - s0.x) > abs(sx.y - s0.y)
        return x_h

    # ---- features ----
    @staticmethod
    def biggest(sk):
        return max(sk.profiles, key=lambda p: p.areaProperties().area)

    @staticmethod
    def smallest(sk):
        return min(sk.profiles, key=lambda p: p.areaProperties().area)

    @staticmethod
    def ring(sk):
        """the profile with two loops (the region between two nested outlines)"""
        for p in sk.profiles:
            if p.profileLoops.count == 2:
                return p

    def extrude(self, prof, dist, op, name, symmetric=False):
        ei = self.ext.createInput(prof, op)
        if symmetric:
            ei.setSymmetricExtent(VI(dist), False)
        else:
            ei.setDistanceExtent(False, VI(dist))
        if op != NEW and self.comp.bRepBodies.count:          # only this component's bodies
            ei.participantBodies = list(self.comp.bRepBodies)
        f = self.ext.add(ei)
        f.name = name
        if op == NEW:
            self.body = f.bodies.item(0)
        return f

    def loft(self, p0, p1, op, name):
        li = self.comp.features.loftFeatures.createInput(op)
        li.loftSections.add(p0)
        li.loftSections.add(p1)
        li.isSolid = True
        if op != NEW and self.comp.bRepBodies.count:          # only this component's bodies
            li.participantBodies = list(self.comp.bRepBodies)
        f = self.comp.features.loftFeatures.add(li)
        f.name = name
        return f

    def report(self, ref=None):
        b = self.body
        bb = b.boundingBox
        print('%s: %.1f mm3%s, bbox %s %s' % (self.comp.name, b.volume * 1000, '' if ref is None else ' (mesh model %.1f)' % ref,
              [round(v * 10, 3) for v in bb.minPoint.asArray()], [round(v * 10, 3) for v in bb.maxPoint.asArray()]))


# =============================================== parts ===============================================
def cup(des):
    p = Part(des, 'Cup (parametric)')
    pl_mouth = p.zplane('ZMouth', 'Mouth plane')
    # outer shell, mouth band and its taper (loft), cavity, O-ring lead-in step
    sk = p.sketch(pl_mouth, 'Outer section'); p.outline(sk, 'Wall', 'WallBF', 'Wall', 'Wall', 'Wall')
    p.extrude(p.biggest(sk), 'ZTop - ZMouth', NEW, 'Outer'); p.body.name = 'Cup'
    sk = p.sketch(pl_mouth, 'Mouth band section'); p.outline_off(sk, 'MouthT')
    p.extrude(p.biggest(sk), 'MouthH - MouthTaper', JOIN, 'Mouth band')
    s0 = p.sketch(p.zplane('ZMouth + MouthH - MouthTaper', 'Mouth taper start'), 'Taper start'); p.outline_off(s0, 'MouthT')
    s1 = p.sketch(p.zplane('ZMouth + MouthH', 'Mouth taper end'), 'Taper end'); p.outline(s1, 'Wall', 'WallBF', 'Wall', 'Wall', 'Wall')
    p.loft(p.biggest(s0), p.biggest(s1), JOIN, 'Mouth taper')
    sk = p.sketch(pl_mouth, 'Inside section'); p.outline_off(sk, '0')
    p.extrude(p.biggest(sk), 'ZTop - TopT - ZMouth', CUT, 'Cavity')
    sk = p.sketch(pl_mouth, 'Lead-in section'); p.outline_off(sk, 'MouthLeadD')
    p.extrude(p.biggest(sk), 'MouthLead', CUT, 'O-ring lead-in')
    # USB-C seal bores, housing pockets (ring outline + housing, union), lead from the ring outline to the bore
    pl_top0 = p.zplane('ZTop - TopT', 'Top wall inside')
    pl_pk = p.zplane('ZTop - RingD + BoardZFloat + 0.02 mm', 'Housing pocket top')
    pl_le = p.zplane('ZTop - RingD + BoardZFloat + 0.02 mm + PocketLead', 'Ring lead end')

    def port(sk, s, w, h, r):
        py, px = p.ev('PortY') * s, p.ev('PortX')
        W, H, R = p.ev(w), p.ev(h), p.ev(r)
        ey = ['PortY - (%s)/2' % w, 'PortY + (%s)/2' % w] if s > 0 else ['PortY + (%s)/2' % w, 'PortY - (%s)/2' % w]
        return p.rrect(sk, px - H / 2, px + H / 2, py - W / 2, py + W / 2, (R,) * 4,
                       ['PortX - (%s)/2' % h, 'PortX + (%s)/2' % h] + ey + [r] * 4)
    BORE = ('RingW - 2*UsbSq', 'RingH - 2*UsbSq', 'RingR - UsbSq')
    RING = ('RingW', 'RingH', 'RingR')
    HOUS = ('HousW + 2*HousClr', 'HousH + 2*HousClr', 'HousR + HousClr')
    for s, tag in ((1, 'USB1'), (-1, 'USB2')):
        sk = p.sketch(pl_top0, tag + ' seal bore'); port(sk, s, *BORE)
        p.extrude(p.biggest(sk), 'TopT', CUT, tag + ' seal bore')
        for nm, sec in (('ring', RING), ('housing', HOUS)):
            sk = p.sketch(pl_top0, '%s pocket (%s)' % (tag, nm)); port(sk, s, *sec)
            p.extrude(p.biggest(sk), 'TopT - RingD + BoardZFloat + 0.02 mm', CUT, '%s pocket (%s)' % (tag, nm))
        s0 = p.sketch(pl_pk, tag + ' lead start'); port(s0, s, *RING)
        s1 = p.sketch(pl_le, tag + ' lead end'); port(s1, s, *BORE)
        p.loft(p.biggest(s0), p.biggest(s1), CUT, tag + ' ring lead')
    # wall pockets over L401 / L501 (positions from the KiCad board: fixed geometry)
    sk = p.sketch(p.plane(p.comp.yZConstructionPlane, 'XIn', 'Board-face wall inside'), 'Wall pockets (L401, L501)')
    for (y0, y1, z0, z1) in WALL_POCKETS:
        a = sk.modelToSketchSpace(P3(p.ev('XIn'), y0 - POCKET_MARGIN, z0 - POCKET_MARGIN))
        b = sk.modelToSketchSpace(P3(p.ev('XIn'), y1 + POCKET_MARGIN, z1 + POCKET_MARGIN + p.ev('BoardZFloat')))
        L = sk.sketchCurves.sketchLines.addTwoPointRectangle(a, b)
        for i in range(4):
            l1, l2 = L.item(i), L.item((i + 1) % 4)
            c, a1, b2 = l1.endSketchPoint.geometry, l1.startSketchPoint.geometry, l2.endSketchPoint.geometry
            sk.sketchCurves.sketchArcs.addFillet(l1, adsk.core.Point3D.create(c.x + (a1.x - c.x) * 0.1, c.y + (a1.y - c.y) * 0.1, 0),
                                                  l2, adsk.core.Point3D.create(c.x + (b2.x - c.x) * 0.1, c.y + (b2.y - c.y) * 0.1, 0), cm(POCKET_R))
    for cv in sk.sketchCurves:
        cv.isFixed = True
    profs = adsk.core.ObjectCollection.create()
    for pr in sk.profiles:
        profs.add(pr)
    p.extrude(profs, 'WallPocketD', CUT, 'Wall pockets')
    # radial M2 holes and counterbores
    sk = p.sketch(p.comp.xZConstructionPlane, 'Screw holes')
    screw_circle(p, sk, 0.0, 'ScrewHoleR')
    p.extrude(p.biggest(sk), 'YI + MouthT + 1 mm', CUT, 'Screw holes', symmetric=True)
    for s in (1, -1):
        side = '+y' if s > 0 else '-y'
        sk = p.sketch(p.yplane(('' if s > 0 else '-') + '(YI + MouthT)', 'Mouth band face ' + side), 'Counterbore ' + side)
        screw_circle(p, sk, s * p.ev('YI + MouthT'), 'CboreR')
        p.extrude(p.smallest(sk), 'CboreD', CUT, 'Counterbore ' + side, symmetric=True)
    p.report(32484.6)
    return p


def screw_circle(p, sk, y, rexpr):
    """a circle on the screw axis (ScrewX, ZMouth + ScrewDZ) in an XZ-family sketch at world y"""
    x_h = p.axes(sk)
    ex_x, ex_z = 'ScrewX', 'abs(ZMouth + ScrewDZ)'
    return p.circle(sk, (p.ev('ScrewX'), y, p.ev('ZMouth + ScrewDZ')), rexpr,
                    ex_h=ex_x if x_h else ex_z, ex_v=ex_z if x_h else ex_x)


def cap(des):
    p = Part(des, 'Cap (parametric)')
    pl_plate = p.zplane('ZMouth - CapT', 'Cap plate underside')
    pl_mouth = p.zplane('ZMouth', 'Cap plate top (cup mouth)')
    # plate: the cup's mouth-band section
    sk = p.sketch(pl_plate, 'Plate section'); p.outline_off(sk, 'MouthT')
    p.extrude(p.biggest(sk), 'CapT', NEW, 'Plate'); p.body.name = 'Cap'
    # skirt: inside section less CapClr, SkirtT thick
    sk = p.sketch(pl_mouth, 'Skirt section')
    p.outline_off(sk, '(-CapClr)')
    p.outline_off(sk, '(-CapClr - SkirtT)')
    p.extrude(p.ring(sk), 'SkirtL', JOIN, 'Skirt')
    # screw bosses (y), each BossDepth in from the skirt's outside
    for s in (1, -1):
        side = '+y' if s > 0 else '-y'
        mid = '(YI - CapClr - BossDepth / 2)'
        sk = p.sketch(p.yplane(mid if s > 0 else '-' + mid, 'Boss mid ' + side), 'Boss ' + side)
        screw_circle(p, sk, s * p.ev(mid), 'BossR')
        p.extrude(p.biggest(sk), 'BossDepth / 2', JOIN, 'Boss ' + side, symmetric=True)
    # overtravel posts: centre, and in from the cell envelope on -x, -y, +y
    sk = p.sketch(pl_mouth, 'Overtravel posts')
    e = 'CellPitch + CellR - OTInset'
    E = p.ev(e)
    p.circle(sk, (0, 0, p.ev('ZMouth')), 'OTR', on_h_axis=True, on_v_axis=True)
    p.circle(sk, (-E, 0, p.ev('ZMouth')), 'OTR', ex_h=e, on_h_axis=True)
    p.circle(sk, (0, -E, p.ev('ZMouth')), 'OTR', ex_v=e, on_v_axis=True)
    p.circle(sk, (0, E, p.ev('ZMouth')), 'OTR', ex_v=e, on_v_axis=True)
    profs = adsk.core.ObjectCollection.create()
    for pr in sk.profiles:
        profs.add(pr)
    p.extrude(profs, 'FrB0 - OTGap - ZMouth', JOIN, 'Overtravel posts')
    # O-ring groove: from 0.5 outside the bore in to GrooveD + CapClr inside it
    sk = p.sketch(p.zplane('ZMouth + GrooveZ0', 'Groove bottom'), 'Groove section')
    p.outline_off(sk, '0.5 mm')
    p.outline_off(sk, '(-CapClr - GrooveD)')
    p.extrude(p.ring(sk), 'GrooveW', CUT, 'O-ring groove')
    # vent hole
    sk = p.sketch(pl_plate, 'Vent hole')
    p.circle(sk, (p.ev('VentX'), 0, p.ev('ZMouth - CapT')), 'VentHoleR', ex_h='VentX', on_h_axis=True)
    p.extrude(p.biggest(sk), 'CapT + 1 mm', CUT, 'Vent hole', symmetric=True)
    # blind pilots: from outside the skirt in to PilotSolid short of each boss's inner end
    for s in (1, -1):
        side = '+y' if s > 0 else '-y'
        inner = '(YI - CapClr - BossDepth + PilotSolid)'
        mid = '((%s + YI + 1 mm) / 2)' % inner
        sk = p.sketch(p.yplane(mid if s > 0 else '-' + mid, 'Pilot mid ' + side), 'Pilot ' + side)
        screw_circle(p, sk, s * p.ev(mid), 'PilotR')
        p.extrude(p.biggest(sk), '(YI + 1 mm - %s) / 2' % inner, CUT, 'Pilot ' + side, symmetric=True)
    p.report(7527.5)
    return p


CELL_XY = [(sx, sy) for sx in (1, -1) for sy in (1, -1)]            # cell centres as signs of CellPitch


def cell_envelope(p, sk):
    e = 'CellPitch + CellR'
    E, R = p.ev(e), p.ev('CellR')
    return p.rrect(sk, -E, E, -E, E, (R,) * 4, [e] * 4 + ['CellR'] * 4)


def all_profiles(sk, keep=lambda pr: True):
    c = adsk.core.ObjectCollection.create()
    for pr in sk.profiles:
        if keep(pr):
            c.add(pr)
    return c


def carrier(des):
    p = Part(des, 'Carrier (parametric)')
    pl_b0 = p.zplane('FrB0', 'Bottom frame underside')
    pl_t0 = p.zplane('ZCell1 + TabT', 'Top frame underside')
    # frames (cell envelope less the four windows) and the spines between them: back (-x) and the two sides (+-y)
    def frame(pl, nm, t, op):
        sk = p.sketch(pl, nm + ' section')
        cell_envelope(p, sk)
        for sx, sy in CELL_XY:
            p.circle_s(sk, '%sCellPitch' % ('' if sx > 0 else '-'), '%sCellPitch' % ('' if sy > 0 else '-'), 'WinR')
        p.extrude(p.biggest(sk), t, op, nm)
    frame(pl_b0, 'Bottom frame', 'FrameT', NEW)
    p.body.name = 'Carrier'
    sk = p.sketch(pl_b0, 'Spines')
    e = 'CellPitch + CellR'
    p.rect(sk, '-(%s)' % e, '-(%s - SpineL)' % e, '-SpineHW', 'SpineHW')
    p.rect(sk, '-SpineHW', 'SpineHW', '%s - SpineL' % e, e)
    p.rect(sk, '-SpineHW', 'SpineHW', '-(%s)' % e, '-(%s - SpineL)' % e)
    p.extrude(all_profiles(sk), 'ZTop - TopT - FrB0', JOIN, 'Spines')
    frame(pl_t0, 'Top frame', 'ZTop - TopT - (ZCell1 + TabT)', JOIN)
    # webs in the front-back gaps, with their links to the side spines, then the cells cut out of them
    pl_c0 = p.zplane('ZCell0', 'Cell bottom ends')
    sk = p.sketch(pl_c0, 'Webs')
    for s in ('', '-'):
        p.rect(sk, '-WebX', 'WebX', '%s(CellPitch - WebIn)' % s, '%s(CellPitch + WebIn)' % s)
        p.rect(sk, '-WebLink', 'WebLink', '%s(CellPitch + WebIn - 0.5 mm)' % s, '%s(CellPitch + CellR)' % s)
    p.extrude(all_profiles(sk), 'ZCell1 - ZCell0', JOIN, 'Webs')
    sk = p.sketch(pl_c0, 'Cells (web clearance)')
    for sx, sy in CELL_XY:
        p.circle_s(sk, '%sCellPitch' % ('' if sx > 0 else '-'), '%sCellPitch' % ('' if sy > 0 else '-'), 'CellR + WebClr')
    p.extrude(all_profiles(sk), 'ZCell1 - ZCell0', CUT, 'Cell clearance')
    # PACK / Kelvin wire notches through the bottom frame
    pl_bm = p.zplane('FrB0 - 0.1 mm', 'Below the bottom frame')
    sk = p.sketch(pl_bm, 'Wire notches')
    for s in ('', '-'):
        p.rect(sk, 'NotchX0', 'BoardB', '%s(KSlotY - KWireOD / 2 - NotchClr)' % s, '%s(PackY + PWireOD / 2 + NotchClr)' % s)
    p.extrude(all_profiles(sk), 'FrameT + 0.2 mm', CUT, 'Wire notches')
    # key slots for the rail tongues, through each frame at the board-side edge
    for pl, nm, k0, k1, t in ((pl_bm, 'bottom', 'KeyB0', 'KeyB1', 'FrameT + 0.2 mm'),
                              (p.zplane('ZCell1 + TabT - 0.1 mm', 'Below the top frame'), 'top', 'KeyT0', 'KeyT1',
                               'ZTop - TopT - (ZCell1 + TabT) + 0.2 mm')):
        sk = p.sketch(pl, 'Key slots (%s)' % nm)
        for s in ('', '-'):
            p.rect(sk, 'CellPitch + CellR - KeyDepth - KeyClr', 'RailX0 + 0.01 mm',
                   '%s(%s - KeyClr)' % (s, k0), '%s(%s + KeyClr)' % (s, k1))
        p.extrude(all_profiles(sk), t, CUT, 'Key slots (%s)' % nm)
    # foam ring pockets in the bottom frame's cell side (C1 / C4, the +x pair: only the half away from the board)
    sk = p.sketch(p.zplane('FrB0 + FrameT - FoamPocket', 'Foam pocket floor'), 'Foam pockets')
    trims = []
    for sx, sy in CELL_XY:
        ex, ey = '%sCellPitch' % ('' if sx > 0 else '-'), '%sCellPitch' % ('' if sy > 0 else '-')
        ci = p.circle_s(sk, ex, ey, 'FoamR0')
        co = p.circle_s(sk, ex, ey, 'FoamR1')
        if sx > 0:
            cx, cy = p.ev(ex), p.ev(ey)
            xt = cx - p.ev('FoamTrim')
            for sgn in (1, -1):
                yi = cy + sgn * (p.ev('FoamR0') ** 2 - (cx - xt) ** 2) ** 0.5
                yo = cy + sgn * (p.ev('FoamR1') ** 2 - (cx - xt) ** 2) ** 0.5
                ln = sk.sketchCurves.sketchLines.addByTwoPoints(P3(xt, yi), P3(xt, yo))
                gc = sk.geometricConstraints
                gc.addVertical(ln)
                gc.addCoincident(ln.startSketchPoint, ci)
                gc.addCoincident(ln.endSketchPoint, co)
                sk.sketchDimensions.addDistanceDimension(sk.originPoint, ln.startSketchPoint, HOR, P3(xt, yo + 2)) \
                    .parameter.expression = 'CellPitch - FoamTrim'
            trims.append((cx, cy, xt))

    def pocket(pr):
        c = pr.areaProperties().centroid
        x, y = c.x * 10, c.y * 10
        for cx, cy, xt in trims:                                       # front cells: the piece away from the board
            if abs(y - cy) < p.ev('FoamR1') and abs(x - cx) < p.ev('FoamR1'):
                return pr.profileLoops.count == 1 and x < xt - 0.5
        return pr.profileLoops.count == 2                              # back cells: the whole ring
    p.extrude(all_profiles(sk, pocket), 'FoamPocket + 0.1 mm', CUT, 'Foam pockets')
    # CELL2 sense-wire channel along y = 0 in the bottom frame's cell side, with the solder pocket at its start
    sk = p.sketch(p.zplane('FrB0 + FrameT - ChD', 'Channel floor'), 'Sense channel')
    p.rect(sk, '-(CellPitch + 1.5 mm)', 'CellPitch + CellR + 0.1 mm', '-ChW / 2', 'ChW / 2')
    p.rect(sk, '-(CellPitch + 1.5 mm)', '-(CellPitch - 1.5 mm)', '-ChPocket', 'ChPocket')
    p.extrude(all_profiles(sk), 'ChD + 0.1 mm', CUT, 'Sense channel')
    p.report(9023.9)
    return p


def peg_circles(p, sk, rexpr, jitter=1.0):
    """the four peg-axis circles (y = +-PegY, z = PegZ0 / PegZ1) in a YZ-family sketch (jitter: a second set of
    concentric circles must be drawn off by a different amount, or the solver ties the centres together)"""
    for sy in (1, -1):
        for zk in ('PegZ0', 'PegZ1'):
            y, z = sy * p.ev('PegY'), p.ev(zk)
            c = sk.modelToSketchSpace(P3(p.ev('BoardB'), y, z))
            s0, sy_, sz_ = (sk.modelToSketchSpace(P3(*q)) for q in ((0, 0, 0), (0, 1, 0), (0, 0, 1)))
            y_h = abs(sy_.x - s0.x) > abs(sy_.y - s0.y)                     # world y along the sketch's horizontal?
            dx, dy = 0.031 * jitter, 0.017 * jitter                         # drawn off and dimensioned on (see circle_s)
            ci = sk.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(c.x + dx, c.y + dy, 0), cm(p.ev(rexpr) * 1.01))
            D, o, cp = sk.sketchDimensions, sk.originPoint, ci.centerSketchPoint
            D.addDiameterDimension(ci, adsk.core.Point3D.create(c.x + 0.3, c.y + 0.3, 0)).parameter.expression = '2 * (%s)' % rexpr
            D.addDistanceDimension(o, cp, HOR, adsk.core.Point3D.create(c.x, c.y - 0.4, 0)).parameter.expression = 'PegY' if y_h else zk
            D.addDistanceDimension(o, cp, VER, adsk.core.Point3D.create(c.x + 0.4, c.y, 0)).parameter.expression = zk if y_h else 'PegY'


def rails(des):
    """four clip-on rail blocks (bottom / top, each side) with their key tongues, crush ribs and board peg posts"""
    p = Part(des, 'Rails (parametric)')
    # bottom blocks: the narrow keep strip from the frame up, the full block from BarZ0, both to RailGap0
    sk = p.sketch(p.zplane('FrB0', 'Rail bottom'), 'Bottom keep strips')
    for s in ('', '-'):
        p.rect(sk, 'RailX0', 'BoardB', '%sBarY0' % s, '%sRailReliefY' % s)
    p.extrude(all_profiles(sk), 'RailGap0 - FrB0', NEW, 'Bottom keep strips')
    sk = p.sketch(p.zplane('BarZ0', 'Rail full width'), 'Bottom blocks')
    for s in ('', '-'):
        p.rect(sk, 'RailX0', 'BoardB', '%sBarY0' % s, '%sBarY1' % s)
    p.extrude(all_profiles(sk), 'RailGap0 - BarZ0', JOIN, 'Bottom blocks')
    sk = p.sketch(p.zplane('RailGap1', 'Top blocks start'), 'Top blocks')
    for s in ('', '-'):
        p.rect(sk, 'RailX0', 'BoardB', '%sBarY0' % s, '%sBarY1' % s)
    p.extrude(all_profiles(sk), 'ZTop - TopT - RailGap1', NEW, 'Top blocks')
    # tongues into the carrier's key slots
    for pl, nm, k0, k1, t in ((p.zplane('FrB0', 'Bottom tongues'), 'bottom', 'KeyB0', 'KeyB1', 'FrameT'),
                              (p.zplane('ZCell1 + TabT', 'Top tongues'), 'top', 'KeyT0', 'KeyT1', 'ZTop - TopT - (ZCell1 + TabT)')):
        sk = p.sketch(pl, 'Tongues (%s)' % nm)
        for s in ('', '-'):
            p.rect(sk, 'CellPitch + CellR - KeyDepth', 'RailX0 + 0.01 mm', '%s%s' % (s, k0), '%s%s' % (s, k1))
        p.extrude(all_profiles(sk), t, JOIN, 'Tongues (%s)' % nm)
        # crush ribs on both side faces of each tongue, ramped from the tip (fixed sketch geometry)
        zm = '(%s + (%s) / 2)' % (('FrB0', 'FrameT') if nm == 'bottom' else ('(ZCell1 + TabT)', 'ZTop - TopT - (ZCell1 + TabT)'))
        sk = p.sketch(p.zplane(zm, 'Rib mid (%s)' % nm), 'Crush ribs (%s)' % nm)
        xe, h, lead = p.ev('CellPitch + CellR'), p.ev('RibH'), p.ev('RibLead')
        x0 = xe - p.ev('KeyDepth') + 0.1
        for sgn in (1, -1):
            for yf, d in ((sgn * p.ev(k0), -sgn), (sgn * p.ev(k1), sgn)):
                yb = yf - d * 0.05
                pts = [P3(x0, yb), P3(x0 + lead, yf + d * h), P3(xe, yf + d * h), P3(xe, yb)]
                lines = sk.sketchCurves.sketchLines
                first = prev = lines.addByTwoPoints(pts[0], pts[1])
                for q in pts[2:]:
                    prev = lines.addByTwoPoints(prev.endSketchPoint, q)
                lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
        for cv in sk.sketchCurves:
            cv.isFixed = True
        p.extrude(all_profiles(sk), 'RibW / 2', JOIN, 'Crush ribs (%s)' % nm, symmetric=True)
    # board peg posts, from inside the blocks through the board's peg holes to PostGap under the board-face wall
    sk = p.sketch(p.plane(p.comp.yZConstructionPlane, 'BoardB - 0.5 mm', 'Post roots'), 'Peg posts')
    peg_circles(p, sk, 'PegD / 2')
    p.extrude(all_profiles(sk), 'XIn - PostGap - (BoardB - 0.5 mm)', JOIN, 'Peg posts')
    # relief under the USB-C front housings (they hang below B.Cu in the board notches) in the top blocks
    z0 = 'ZTop - HousD - 0.2 mm - BoardZFloat'
    sk = p.sketch(p.zplane(z0, 'USB relief floor'), 'USB relief')
    for s in ('', '-'):
        p.rect(sk, 'PortX - HousH / 2 - 0.2 mm', 'BoardB + 0.1 mm',
               '%s(PortY - HousW / 2 - 0.25 mm)' % s, '%s(PortY + HousW / 2 + 0.25 mm)' % s)
    p.extrude(all_profiles(sk), 'ZTop - TopT + 1 mm - (%s)' % z0, CUT, 'USB relief')
    names = {(1, 0): 'Rail bottom +y', (-1, 0): 'Rail bottom -y', (1, 1): 'Rail top +y', (-1, 1): 'Rail top -y'}
    for b in p.comp.bRepBodies:
        c = b.boundingBox
        b.name = names[(1 if c.maxPoint.y > 0 else -1, 1 if c.maxPoint.z * 10 > 50 else 0)]
    p.body = p.comp.bRepBodies.item(0)
    print('Rails: %d bodies, %.1f mm3 (mesh model 1137.8)' % (p.comp.bRepBodies.count, sum(b.volume for b in p.comp.bRepBodies) * 1000))
    return p


def sleeves(des):
    p = Part(des, 'Sleeves (parametric)')
    sk = p.sketch(p.plane(p.comp.yZConstructionPlane, 'BoardB + BoardT', 'F.Cu'), 'Sleeves')
    peg_circles(p, sk, 'SleeveR')
    peg_circles(p, sk, 'SleeveBore', jitter=-1.7)
    p.extrude(all_profiles(sk, lambda pr: pr.profileLoops.count == 2), 'SleeveH', NEW, 'Sleeves')
    print('Sleeves: %d bodies, %.1f mm3 (mesh model 36.2)' % (p.comp.bRepBodies.count, sum(b.volume for b in p.comp.bRepBodies) * 1000))
    return p


BUILD = dict(cup=cup, cap=cap, carrier=carrier, rails=rails, sleeves=sleeves)


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    if des.designIntent == adsk.fusion.DesignIntentTypes.PartDesignIntentType:
        des.designIntent = adsk.fusion.DesignIntentTypes.HybridDesignIntentType
    up = des.userParameters
    for n, e, c in PARAMS:
        prm = up.itemByName(n)
        if prm:
            prm.expression, prm.comment = e, c
        else:
            up.add(n, VI(e), 'mm', c)
    for k in PARTS:
        BUILD[k](des)
    bad = []
    for i in range(des.timeline.count):
        it = des.timeline.item(i)
        if it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
            bad.append((it.name, it.errorOrWarningMessage))
    for comp in [o.component for o in des.rootComponent.occurrences if o.component.name.endswith('(parametric)')]:
        for sk in comp.sketches:
            n = sum(1 for cv in sk.sketchCurves if not cv.isFullyConstrained)
            if n and not all(cv.isFixed for cv in sk.sketchCurves):
                bad.append((comp.name + ' / ' + sk.name, '%d curves not fully constrained' % n))
    print('timeline / sketch problems:', bad or 'none')
