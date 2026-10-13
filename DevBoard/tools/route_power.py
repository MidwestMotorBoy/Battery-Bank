"""Power-stage copper for both charger ports (run with KiCad 10's python after place_parts.py):
    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/route_power.py

Re-runnable: the UUIDs of everything this script adds are kept in tools/route_power.uuids (KiCad 10's python can't
walk PCB groups), and those items plus the In1/In2 GND planes (GND_PLANE_In1/In2) are deleted and rebuilt on every
run. The items are also grouped per port (route_power_p1/p2) so they select together in the editor. Coordinates are board mm from the board's
top-left corner (same frame as place_parts.py), written for port 1; port 2 is the same copper 37 mm lower.

Per port (hot loops first, [[pcb-layout-principles]]):
  - SW1 / SW2: one compact F.Cu pour each, FET switch pads straight to the inductor pad, nothing else in it;
    the SW test loops hang off the far side of the inductor pads as short stubs.
  - Input bank (AC_SNS_N): F.Cu pour joining Q401's drain pads, the HF cap C430 straddling drain/GND, the 1210 row,
    C423, the polymer C421 and RAC's AC_SNS_N pad; mirrored on B.Cu and stitched with vias.
  - Output bank (BAT_SNS_P): the same for Q402, C438, the 1210s, C432 and RBAT's BAT_SNS_P pad.
  - GND islands under each FET's source pads and the caps' GND pads, stitched straight into the In1 GND plane
    (0.1 mm below F.Cu). Cap GND pads that the bank pour surrounds get a small GND pocket with their own vias.
  - VBAT_SYS from RBAT straight up to the R430 link.
In1 is a solid GND plane over the whole board; In2 is GND fill for now (signals that must cross are added later).
"""
import os
import re
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "MonolithDev.kicad_pcb")
PRO = os.path.join(HERE, "..", "MonolithDev.kicad_pro")
IDS = os.path.join(HERE, "route_power.uuids")
ORIGIN = (50.0, 50.0)
PORT_DY = 37.0
W, H = 196.0, 115.0

pro_backup = open(PRO, encoding="utf-8").read()     # pcbnew saves rewrite the project file: keep the committed one
board = pcbnew.LoadBoard(PCB)
F, B, IN1, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu
mm = pcbnew.FromMM

# ---- clear what an earlier run added -----------------------------------------------------------------------------
old = set(open(IDS).read().split()) if os.path.exists(IDS) else set()
# decide everything before removing anything (removing while walking the board's lists leaves dead wrappers)
groups = [g for g in board.Groups() if g.GetName().startswith("route_power")]
stale = [t for t in board.GetTracks() if t.m_Uuid.AsString() in old]
stale += [z for z in board.Zones() if z.m_Uuid.AsString() in old or z.GetZoneName().startswith(("GND_PLANE_", "KEEPOUT_H"))]
for g in groups:
    board.Remove(g)
for it in stale:
    board.Remove(it)
added = []

def k(x, y):
    return pcbnew.VECTOR2I(mm(x + ORIGIN[0]), mm(y + ORIGIN[1]))


def net(name):
    n = board.FindNet(name)
    assert n is not None, name
    return n


class Port:
    def __init__(self, idx):
        self.idx = idx                                   # "4" or "5"
        self.dy = 0.0 if idx == "4" else PORT_DY
        self.jdy = 0.0 if idx == "4" else -1.0          # J501 sits 36 mm below J401 (USB_Y), not 37
        self.pfx = f"/USB Port {1 if idx == '4' else 2}/"
        self.group = pcbnew.PCB_GROUP(board)
        self.group.SetName(f"route_power_p{1 if idx == '4' else 2}")
        board.Add(self.group)

    def n(self, name):                                   # port-local net; "Net-(D404-K)" style names follow the refs
        if name == "EN_5V1":                              # global label per port
            return net("EN_5V1" if self.idx == "4" else "EN_5V2")
        if name.startswith("Net-("):
            return net(re.sub(r"([A-Z]+)4(\d\d)", lambda m: m.group(1) + self.idx + m.group(2), name))
        return net(name if name == "GND" else self.pfx + name)

    def r(self, ref):                                    # C4xx -> C5xx for port 2
        return ref[0] + self.idx + ref[2:] if ref[1] == "4" else ref

    def pts(self, pts):
        return [(x, y + self.dy) for x, y in pts]

    def zone(self, name, netname, layer, pts, prio=1, clearance=0.2, connection=pcbnew.ZONE_CONNECTION_FULL):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(self.n(netname))
        z.SetZoneName(f"P{1 if self.idx == '4' else 2}_{name}")
        ol = z.Outline()
        ol.NewOutline()
        for x, y in self.pts(pts):
            p = k(x, y)
            ol.Append(p.x, p.y)
        z.SetAssignedPriority(prio)
        z.SetPadConnection(connection)
        z.SetLocalClearance(mm(clearance))
        z.SetMinThickness(mm(0.25))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        board.Add(z)
        self.group.AddItem(z)
        added.append(z.m_Uuid.AsString())
        return z

    def via(self, x, y, netname, d=0.6, drill=0.3):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(k(x, y + self.dy))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(F, B)
        v.SetWidth(mm(d))
        v.SetDrill(mm(drill))
        v.SetNet(self.n(netname))
        board.Add(v)
        self.group.AddItem(v)
        added.append(v.m_Uuid.AsString())
        return v

    def vias(self, netname, pts, **kw):
        for x, y in pts:
            self.via(x, y, netname, **kw)

    def track(self, netname, pts, w, layer=F):
        pts = self.pts(pts)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(k(x0, y0)); t.SetEnd(k(x1, y1))
            t.SetWidth(mm(w)); t.SetLayer(layer)
            t.SetNet(self.n(netname))
            board.Add(t)
            self.group.AddItem(t)
            added.append(t.m_Uuid.AsString())


def grid(x0, y0, x1, y1, pitch):
    out, y = [], y0
    while y <= y1 + 1e-6:
        x = x0
        while x <= x1 + 1e-6:
            out.append((round(x, 3), round(y, 3)))
            x += pitch
        y += pitch
    return out


for idx in ("4", "5"):
    P = Port(idx)
    # ---------------- switch nodes (F.Cu only, minimum area) ----------------
    # SW1: Q401 switch pads (left pad 166.79-168.72 x 30.21-32.81, top pad 168.06-170.16 x 27.83-29.89) to L401 pad 1
    P.zone("SW1", "SW1", F, [(159.4, 28.2), (161.3, 28.2), (161.3, 29.45), (167.95, 29.45), (167.95, 27.75),
                             (170.25, 27.75), (170.25, 30.05), (168.85, 30.05), (168.85, 32.95), (161.3, 32.95),
                             (161.3, 34.8), (159.4, 34.8)], prio=2)
    # SW2: Q402 switch pads (right pad 147.28-149.21 x 30.19-32.79, bottom pad 145.84-147.94 x 33.11-35.17) to L401 pad 2
    P.zone("SW2", "SW2", F, [(156.6, 28.2), (156.6, 34.8), (154.7, 34.8), (154.7, 32.95), (148.05, 32.95),
                             (148.05, 35.25), (145.75, 35.25), (145.75, 33.0), (147.15, 33.0), (147.15, 29.95),
                             (154.7, 29.95), (154.7, 28.2)], prio=2)
    # SW test loops: short stubs straight down off the far side of each inductor pad
    P.track("SW1", [(160.43, 34.6), (160.43, 39.2)], 0.4)
    P.track("SW2", [(155.32, 34.6), (155.32, 39.2)], 0.4)

    # ---------------- input bank: AC_SNS_N ----------------
    ac = [(169.2, 30.3), (171.35, 30.3), (171.35, 30.95), (175.75, 30.95), (175.75, 41.5), (179.1, 41.5),
          (179.1, 43.75), (173.7, 43.75), (173.7, 45.45), (169.4, 45.45), (169.4, 37.85), (169.0, 37.85),
          (169.0, 35.3), (169.2, 35.3)]
    P.zone("AC_F", "AC_SNS_N", F, ac, prio=1)
    P.zone("AC_B", "AC_SNS_N", B, [(164.8, 30.3), (175.75, 30.3), (175.75, 41.5), (179.1, 41.5), (179.1, 45.45),
                                   (164.8, 45.45)], prio=1)
    # GND island: Q401 source pads, C430 / C420 / C421 GND pads, C427 (both pads; its AC pad gets a pocket)
    P.zone("GND_IN", "GND", F, [(166.7, 33.2), (168.75, 33.2), (168.75, 45.45), (162.2, 45.45), (162.2, 34.1),
                                (166.7, 34.1)], prio=1)
    # C427's AC pad sits between two GND pads: AC pocket under it, vias to the B.Cu AC_SNS_N pour
    P.zone("AC_C427", "AC_SNS_N", F, [(165.2, 37.8), (166.55, 37.8), (166.55, 42.0), (165.2, 42.0)], prio=3)
    P.vias("AC_SNS_N", [(165.55, 41.3), (166.2, 41.3)])
    # C424's GND pad sits inside the AC pour: GND pocket below it with its own vias
    P.zone("GND_C424", "GND", F, [(171.45, 37.8), (172.8, 37.8), (172.8, 41.75), (171.45, 41.75)], prio=3)
    P.vias("GND", [(171.8, 41.15), (172.45, 41.15)])
    # C423's GND pad (top, 172.75-175.45 x 29.45-30.6): vias straight above it, joins U401's ground later
    P.zone("GND_C423", "GND", F, [(172.65, 28.3), (175.55, 28.3), (175.55, 30.7), (172.65, 30.7)], prio=3)
    P.vias("GND", [(173.2, 28.85), (174.1, 28.85), (175.0, 28.85)])
    # GND vias: between Q401's source pad and C430, between C430 and C420, then a field in the open part of the island
    P.vias("GND", [(167.35, 35.65), (168.3, 35.65), (167.1, 37.5), (168.0, 37.5)])
    P.vias("GND", grid(162.7, 34.7, 166.3, 37.1, 1.2))
    P.vias("GND", [(163.0, 41.4), (164.2, 41.4), (167.3, 41.4), (168.3, 41.4)])
    # AC_SNS_N stitching to B.Cu: channel between C423 and the 1210 row, and below the row
    P.vias("AC_SNS_N", grid(171.9, 34.3, 175.5, 36.7, 1.2))
    P.vias("AC_SNS_N", [(169.9, 41.4), (174.2, 41.4), (175.4, 41.4), (169.9, 42.7), (171.1, 42.7), (172.3, 42.7),
                        (173.5, 42.7), (174.7, 42.7), (175.9, 42.7)])

    # ---------------- output bank: BAT_SNS_P ----------------
    bat = [(140.1, 17.6), (144.0, 17.6), (144.0, 19.55), (146.8, 19.55), (146.8, 33.3), (140.1, 33.3),
           (140.1, 25.6), (136.3, 25.6), (136.3, 24.05), (140.1, 24.05)]
    P.zone("BAT_F", "BAT_SNS_P", F, bat, prio=1)
    P.zone("BAT_B", "BAT_SNS_P", B, bat, prio=1)
    P.zone("GND_OUT", "GND", F, [(144.3, 17.5), (149.4, 17.5), (149.4, 29.85), (147.05, 29.85), (147.05, 19.45),
                                 (144.3, 19.45)], prio=1)
    # GND pockets for the 1210 GND pads the BAT pour surrounds (C435, C434)
    P.zone("GND_C435", "GND", F, [(143.2, 22.3), (144.55, 22.3), (144.55, 26.1), (143.2, 26.1)], prio=3)
    P.vias("GND", [(143.55, 25.5), (144.2, 25.5)])
    P.zone("GND_C434", "GND", F, [(139.85, 29.0), (143.55, 29.0), (143.55, 30.35), (139.85, 30.35)], prio=3)
    P.vias("GND", [(140.25, 29.35), (140.25, 30.05)])
    # GND vias: Q402 source pad to C438, C438 to C431, field right of C431 and under C432
    P.vias("GND", [(147.7, 27.4), (148.7, 27.4), (148.6, 25.55), (149.0, 26.2)])
    P.vias("GND", grid(147.5, 19.9, 148.9, 21.9, 0.7))
    # BAT_SNS_P stitching to B.Cu
    P.vias("BAT_SNS_P", [(140.6, 26.7), (141.8, 26.7), (143.0, 26.7), (141.2, 27.9), (142.4, 27.9), (143.6, 27.9)])
    P.vias("BAT_SNS_P", grid(140.6, 20.0, 143.0, 21.2, 1.2))
    P.vias("BAT_SNS_P", [(144.4, 20.6)])

    # ---------------- VBAT_SYS: RBAT top pad straight up to the R430 link ----------------
    P.zone("VBAT_SYS", "VBAT_SYS", F, [(136.25, 13.6), (139.8, 13.6), (139.8, 20.9), (136.25, 20.9)], prio=1)

    # ---------------- gate drive (BQ25756 U403 bottom pins, y 24.0-24.6, 0.5 mm pitch) ----------------
    # Pin order 18 SW2 (left column), 19 HG2, 20 BTST2, 21 LG2, 22 PGND, 23 DRV_SUP, 24 REGN, 25 LG1, 26 BTST1, 27 HG1,
    # 28 SW1. The FET pins come in a different order (Q402's gates face away), so every gate drops to an inner layer
    # through a via right under its pin (TI: >= 0.5 mm gate traces, HG beside/over its SW return, LG over the GND plane):
    #   HG1 In2 with its SW1 return stacked under it on B.Cu; LG1 In2 (In1 GND plane above it);
    #   HG2 + SW2 side by side on B.Cu (outer/inner so they never cross); LG2 In2.
    # The bootstrap loops (BTST pin -> C412/C413 -> SW pin) stay on F.Cu with no vias. DRV_SUP and REGN run on F.Cu
    # under C413 to C411 / R420 / C410 left of the IC; the bootstrap diodes D404/D405 (right of C412) are fed through
    # In2 (DRV_SUP) and B.Cu (BTST1/BTST2).
    GV = dict(d=0.5, drill=0.3)                           # gate-area vias (0.1 mm annulus)
    P.via(155.75, 25.15, "HG2", **GV); P.via(156.75, 25.15, "LG2", **GV)
    P.via(159.85, 25.15, "HG1", **GV); P.via(160.85, 24.85, "SW1", **GV)
    P.via(158.95, 28.0, "LG1", **GV); P.via(154.2, 24.6, "SW2", **GV)
    P.via(157.6, 25.95, "DRV_SUP", **GV)
    P.via(157.15, 26.65, "Net-(D405-K)", **GV); P.via(159.6, 27.35, "Net-(D404-K)", **GV)
    # pin escapes and the F.Cu loops
    P.track("HG2", [(155.75, 24.3), (155.75, 25.15)], 0.25)
    P.track("LG2", [(156.75, 24.3), (156.75, 25.15)], 0.25)
    P.track("HG1", [(159.75, 24.3), (159.85, 25.15)], 0.25)
    P.track("LG1", [(158.75, 24.3), (158.75, 25.0)], 0.25)
    P.track("LG1", [(158.75, 25.0), (158.75, 27.75), (158.95, 28.0)], 0.4)
    P.track("SW2", [(155.1, 23.65), (154.5, 23.65), (154.2, 24.0), (154.2, 24.6), (154.72, 25.75)], 0.25)
    P.track("SW1", [(160.25, 24.3), (160.25, 24.55), (160.85, 24.85), (161.28, 25.75)], 0.25)
    P.track("SW1", [(161.1, 26.4), (160.9, 28.5)], 0.6)                          # C412 SW pad to L401
    P.track("Net-(D405-K)", [(156.25, 24.3), (156.25, 25.8)], 0.16)              # BTST2 -> C413
    P.track("Net-(D404-K)", [(159.25, 24.3), (159.25, 25.4), (159.45, 25.8)], 0.16)  # BTST1 -> C412
    P.track("Net-(D405-K)", [(156.6, 26.4), (157.15, 26.65)], 0.3)
    P.track("Net-(D404-K)", [(159.7, 26.6), (159.6, 27.35)], 0.3)
    P.track("GND", [(157.25, 24.3), (157.25, 23.5)], 0.25)                       # PGND to the exposed pad
    P.track("DRV_SUP", [(157.75, 24.3), (157.75, 27.3), (153.2, 27.3), (153.0, 27.0)], 0.3)
    P.track("REGN", [(158.25, 24.3), (158.25, 27.85), (153.3, 27.85), (153.0, 28.15)], 0.25)
    P.track("DRV_SUP", [(151.8, 25.7), (152.6, 26.5)], 0.4)                      # C411 - R420
    P.track("REGN", [(151.8, 27.7), (152.6, 28.3)], 0.4)                         # C410 - R420
    P.vias("GND", [(150.15, 23.0), (150.15, 29.35)])                             # C411 / C410 ground
    # gate lanes
    P.track("HG1", [(159.85, 25.15), (160.3, 25.6), (170.45, 25.6), (170.9, 26.05), (170.9, 27.15)], 0.5, IN2)
    P.track("SW1", [(160.85, 24.85), (161.6, 25.6), (169.0, 25.6), (169.6, 26.2), (169.6, 27.05)], 0.5, B)
    P.track("LG1", [(158.95, 28.0), (159.9, 28.95), (166.2, 28.95), (167.1, 28.05), (167.1, 27.15)], 0.5, IN2)
    P.via(170.9, 27.15, "HG1", **GV); P.via(169.6, 27.05, "SW1", **GV); P.via(167.1, 27.15, "LG1", **GV)
    P.track("HG1", [(170.9, 27.15), (170.9, 28.2)], 0.5)
    P.track("SW1", [(169.6, 27.05), (169.6, 28.0)], 0.5)
    P.track("LG1", [(167.1, 27.15), (167.1, 28.2)], 0.5)
    P.track("HG2", [(155.75, 25.15), (153.4, 27.5), (153.4, 37.2), (145.1, 37.2)], 0.5, B)
    P.track("SW2", [(154.2, 24.6), (152.6, 26.2), (152.6, 36.4), (146.6, 36.4)], 0.5, B)
    P.track("LG2", [(156.75, 25.15), (155.0, 26.9), (155.0, 35.65), (148.9, 35.65)], 0.5, IN2)
    P.via(145.1, 37.2, "HG2", **GV); P.via(146.6, 36.4, "SW2", **GV); P.via(148.9, 35.65, "LG2", **GV)
    P.track("HG2", [(145.1, 37.2), (145.1, 34.6)], 0.5)
    P.track("SW2", [(146.6, 36.4), (146.6, 34.6)], 0.5)
    P.track("LG2", [(148.9, 35.65), (148.9, 34.6)], 0.5)
    # bootstrap diodes: DRV_SUP on In2, BTST nodes on B.Cu
    P.track("DRV_SUP", [(157.6, 25.95), (158.1, 26.45), (161.8, 26.45), (162.35, 27.0), (164.85, 27.0),
                        (165.3, 27.27)], 0.3, IN2)
    P.track("Net-(D405-K)", [(157.15, 26.65), (162.2, 26.65), (162.55, 26.3)], 0.3, B)
    P.track("Net-(D404-K)", [(159.6, 27.35), (161.9, 27.35), (162.55, 28.0), (162.55, 28.25)], 0.3, B)
    P.via(165.3, 27.27, "DRV_SUP", **GV)
    P.via(162.55, 26.3, "Net-(D405-K)", **GV); P.via(162.55, 28.25, "Net-(D404-K)", **GV)
    P.track("Net-(D405-K)", [(162.55, 26.3), (163.1, 26.3)], 0.3)
    P.track("Net-(D404-K)", [(162.55, 28.25), (163.1, 28.25)], 0.3)
    P.track("DRV_SUP", [(164.9, 26.3), (165.3, 26.7), (165.3, 27.27)], 0.3)
    P.track("DRV_SUP", [(164.9, 28.25), (165.3, 27.85), (165.3, 27.27)], 0.3)
    # BQ25756 exposed pad: thermal vias into the GND planes
    P.vias("GND", grid(156.4, 20.8, 159.7, 22.9, 1.05))

    # ---------------- USB-C power path: J401 VBUS -> TPS25751 (U401) VBUS pad -> PPHV pad -> RAC (R424) ----------------
    # PPHV (5.6 A): F.Cu corridor between R425/R426 and the ESD parts, mirrored on B.Cu, via column on the right edge;
    # it feeds RAC's PPHV pad from the right so R425's Kelvin tap lands on the quiet left end of the pad.
    P.zone("PPHV_F", "PPHV", F, [(179.55, 23.5), (180.35, 23.5), (180.35, 25.0), (181.4, 25.0), (181.4, 36.9),
                                 (180.1, 36.9), (180.1, 39.6), (178.2, 39.6), (178.2, 37.4), (179.65, 37.4),
                                 (179.65, 28.3), (179.25, 28.3), (179.25, 26.5), (179.7, 26.5), (179.7, 24.8),
                                 (179.55, 24.8)], prio=2)
    P.zone("PPHV_B", "PPHV", B, [(179.4, 25.2), (181.6, 25.2), (181.6, 39.6), (178.2, 39.6), (178.2, 36.7),
                                 (179.4, 36.7)], prio=2)
    P.vias("PPHV", [(180.85, y) for y in (25.6, 26.6, 27.6, 28.6, 29.8, 31.0, 32.2, 33.4, 34.6, 35.8)])
    P.vias("PPHV", [(178.5, 39.25), (179.2, 39.25)])                      # under RAC's body, between its pads
    P.via(178.45, 26.35, "GND")                                           # C449
    # VBUS (5 A): J401 VBUS pads -> via clusters -> B.Cu pour -> vias beside U401 -> F.Cu band over C406's VBUS pad
    jy = P.jdy                                          # connector-side items follow J401/J501
    P.zone("VBUS_F", "VBUS", F, [(179.9, 21.3), (188.95, 21.3), (188.95, 30.0 + jy), (187.9, 30.0 + jy),
                                 (187.9, 23.3), (179.55, 23.3), (179.55, 22.2), (179.9, 22.2)], prio=2)
    P.zone("VBUS_J", "VBUS", F, [(187.9, 33.3 + jy), (188.95, 33.3 + jy), (188.95, 36.4), (187.9, 36.4)], prio=2)
    P.zone("VBUS_B", "VBUS", B, [(180.3, 21.3), (189.0, 21.3), (189.0, 37.1), (182.0, 37.1), (182.0, 23.3),
                                 (180.3, 23.3)], prio=2)
    P.track("VBUS", [(188.9, 29.6 + jy), (189.6, 29.6 + jy)], 0.5)        # A9/B4
    P.track("VBUS", [(188.9, 34.4 + jy), (189.6, 34.4 + jy)], 0.5)        # A4/B9 (VBUS_J joins the TVS pad)
    P.vias("VBUS", [(188.45, 28.85 + jy), (188.45, 29.65 + jy), (187.75, 29.25 + jy), (188.45, 33.85 + jy),
                    (188.45, 35.35), (188.45, 36.1)])
    P.vias("VBUS", [(180.85, 21.75), (180.85, 22.85), (181.75, 21.75), (181.75, 22.85), (182.65, 21.75)])
    P.via(184.85, 31.87, "VBUS"); P.track("VBUS", [(184.3, 31.87), (184.85, 31.87)], 0.4)   # C450
    P.vias("GND", [(183.75, 24.95), (182.37, 30.9), (186.5, 33.15), (187.3, 33.15)])        # C406, C450, D401
    P.track("VBUS", [(176.8, 21.3), (176.8, 20.9), (180.6, 20.9), (180.6, 21.5)], 0.3)     # U401 pin 32
    # U401 PP5V cap, PD_DRAIN pins onto their exposed pad
    P.track("PP5V", [(175.8, 20.45), (176.0, 21.4)], 0.4)
    P.via(178.4, 19.55, "GND"); P.track("GND", [(177.6, 20.0), (178.4, 19.55)], 0.4)
    P.track("PD_DRAIN", [(177.8, 21.6), (177.8, 22.4)], 0.2)
    P.track("PD_DRAIN", [(177.8, 25.4), (177.8, 24.6)], 0.2)
    # RAC Kelvin taps: ACP (R425) straight down onto the PPHV pad's left end; ACN (R426) under the PPHV pour on In2
    # to the AC_SNS_N pad's outer end
    P.track("PPHV", [(177.35, 35.9), (177.35, 37.8)], 0.25)
    P.track("AC_SNS_N", [(178.94, 35.9), (178.94, 36.75)], 0.25)
    P.via(178.94, 36.75, "AC_SNS_N", **GV)
    P.track("AC_SNS_N", [(178.94, 36.75), (179.95, 37.8), (179.95, 42.8)], 0.25, IN2)
    P.via(179.95, 42.8, "AC_SNS_N", **GV)
    P.track("AC_SNS_N", [(179.95, 42.8), (179.45, 42.8)], 0.25)

    # ---------------- 5 V buck (TPS62933 U404, SOT-583: 1 GND, 2 EN, 3 VIN, 4 GND | 8 FB, 7 SS, 6 BST, 5 SW) ----------------
    # hot loop first: C446 (0.1u) straddles VIN/GND (pins 3/4), the 10u bulk pair beside it; SW straight to C440 and L402
    P.zone("5VIN_F", "5V_IN", F, [(176.2, 47.35), (180.75, 47.35), (180.75, 48.75), (176.2, 48.75)], prio=2)
    P.track("5V_IN", [(180.5, 47.8), (181.4, 46.9)], 0.6)                 # bulk pair -> C446
    P.track("5V_IN", [(163.88, 48.1), (176.3, 48.1)], 0.8)                 # from the R431 link
    P.track("5V_IN", [(181.9, 47.25), (183.1, 47.25)], 0.25)              # C446 -> VIN
    P.track("GND", [(182.0, 48.05), (182.4, 47.75), (183.1, 47.75)], 0.25)  # pin 4 -> C446 GND
    P.vias("GND", [(181.66, 49.25), (177.2, 44.15), (179.64, 44.15), (183.1, 45.3), (180.75, 43.6)])
    P.track("GND", [(183.1, 46.25), (183.1, 45.3)], 0.25)                 # pin 1
    P.track("GND", [(181.58, 43.6), (180.75, 43.6)], 0.3)                 # R432
    P.track("SW_5V", [(184.6, 47.75), (185.9, 47.75)], 0.3)
    P.zone("SW5V_F", "SW_5V", F, [(185.5, 47.3), (186.6, 47.3), (187.05, 46.85), (187.05, 45.0), (189.25, 45.0),
                                  (189.25, 47.0), (187.3, 48.3), (185.5, 48.3)], prio=2)
    # SS and BST share the 0.65 mm gap between the pin column and C440: SS turns up first, BST passes under its corner
    P.track("BST_5V", [(184.6, 47.25), (185.3, 47.25), (185.6, 46.55)], 0.2)
    P.track("SS_5V", [(184.6, 46.75), (185.15, 46.75), (185.15, 43.0), (184.75, 42.55), (184.75, 41.9)], 0.15)
    P.track("EN_5V1", [(183.1, 46.75), (182.45, 46.75), (182.45, 44.5), (182.95, 44.0)], 0.2)
    P.track("Net-(U404-FB)", [(184.6, 46.25), (184.6, 45.3), (183.9, 44.6), (183.9, 42.4), (183.6, 42.0)], 0.2)
    P.track("Net-(U404-FB)", [(181.4, 41.7), (182.6, 41.7)], 0.25)        # R433 - R434
    P.track("Net-(U404-FB)", [(182.27, 38.4), (181.98, 38.9), (181.98, 41.7)], 0.2)   # C447 (DNP feed-forward)
    P.vias("GND", [(184.0, 39.9)])                                        # R434, C439
    # PP5V: L402 -> C441/C442 (F.Cu), regulation sense to the divider top from the output caps, and the 3 A feed up
    # the right edge (In2 + B.Cu between J401's pads and its shell) to C443, TP403 and U401's PP5V pin via C407
    P.zone("PP5V_F", "PP5V", F, [(189.1, 39.4), (192.3, 39.4), (192.3, 43.4), (193.8, 43.4), (193.8, 47.0),
                                 (191.5, 47.0), (191.5, 43.4), (189.1, 43.4)], prio=2)
    P.track("PP5V", [(189.6, 40.2), (189.6, 37.6), (189.25, 37.25), (180.9, 37.25), (180.73, 37.6)], 0.25)
    P.track("PP5V", [(180.7, 38.5), (180.7, 39.4)], 0.25)                 # C447 - R433
    PP5V_RUN = [(173.6, 19.1), (190.9, 19.1), (190.9, 41.6), (189.3, 41.6), (189.3, 21.0), (173.6, 21.0)]
    P.zone("PP5V_IN2", "PP5V", IN2, PP5V_RUN, prio=2)
    P.zone("PP5V_B", "PP5V", B, PP5V_RUN, prio=2)
    P.vias("PP5V", [(189.75, 39.85), (190.55, 39.85), (190.55, 40.75)])          # bottom end, beside the output caps
    P.vias("PP5V", [(180.4, 19.4), (181.6, 19.4)])                        # C443 (under its body)
    P.track("PP5V", [(180.8, 17.6), (180.4, 19.4)], 0.6); P.track("PP5V", [(181.4, 17.6), (181.6, 19.4)], 0.6)
    P.vias("PP5V", [(174.75, 20.45), (174.0, 20.45), (174.4, 19.65)])     # top end, at C407 / pin 34
    P.zone("PP5V_U401", "PP5V", F, [(173.6, 19.2), (176.2, 19.2), (176.2, 21.0), (173.6, 21.0)], prio=2)
    P.via(190.6, 20.9, "PP5V"); P.track("PP5V", [(190.6, 20.9), (191.78, 20.9)], 0.5)      # TP403

# ---- pack path (11 A): cells -> RS101 -> Q101/Q102 -> F101 -> PACK_P -> both ports ------------------------------
class Pack(Port):
    def __init__(self):
        super().__init__("4")
        self.group.SetName("route_power_pack")

    def n(self, name):
        return net(name if name in ("GND", "CELL_N", "PACK_P") else "/Cells and Gauge/" + name)


K = Pack()
# cell-to-cell links: the holders all face the same way, so each link runs diagonally under the holders from one
# holder's + pad (left end) to the next holder's - pad (right end): ~8.5 mm bands on F.Cu and B.Cu (~1 mOhm each)
for i, nm in enumerate(("CELL1", "CELL2", "CELL3")):
    d = 28.0 * i
    band = [(8.2, 10.5 + d), (15.7, 10.5 + d), (101.8, 38.5 + d), (101.8, 47.5 + d), (94.3, 47.5 + d), (8.2, 19.5 + d)]
    K.zone("LINK_F_" + nm, nm, F, band, prio=1)
    K.zone("LINK_B_" + nm, nm, B, band, prio=1)
    K.vias(nm, [(11.95, 20.3 + d), (13.5, 20.3 + d), (98.05, 37.7 + d), (96.5, 37.7 + d)] +
           [(x, 15.0 + d + (x - 11.95) * 28.0 / 86.1) for x in (30.0, 45.0, 60.0, 75.0)])
# CELL_N: BT101's - pad into RS101's CELL_N pad (RS101 turned so that pad faces the cells; TP102 sits in it), plus a
# column between the NTC headers and R101-R104 down to the welded-pack connector J101 (pin 1). One outline per layer
# (overlapping same-net zones don't merge); the B.Cu column stops above the CELL_P_RAW strip so that strip can pass
# under to F101 and J101 pin 5.
K.zone("CELLN_F", "CELL_N", F, [(100.0, 10.5), (116.7, 10.5), (116.7, 17.75), (110.0, 17.75), (110.0, 106.6),
                                (112.6, 106.6), (112.6, 108.6), (108.35, 108.6), (108.35, 17.75), (100.0, 17.75)],
       prio=1)
K.zone("CELLN_B", "CELL_N", B, [(100.0, 10.5), (116.7, 10.5), (116.7, 17.75), (110.2, 17.75), (110.2, 103.5),
                                (107.4, 103.5), (107.4, 17.75), (100.0, 17.75)], prio=1)
K.vias("CELL_N", [(x, y) for x in (102.0, 103.2, 109.2, 110.4, 111.6, 112.8) for y in (11.4, 12.6, 16.8)])
K.vias("CELL_N", [(109.2, y) for y in range(22, 104, 6)])
# RS101 GND side: into the GND planes (pack current returns through them)
K.zone("RS_GND", "GND", F, [(112.4, 22.1), (117.4, 22.1), (117.4, 25.4), (112.4, 25.4)], prio=1)
K.vias("GND", [(x, y) for x in (113.0, 114.0, 115.0, 116.0, 117.0) for y in (24.2, 25.0)] + [(112.85, 22.9), (117.15, 22.9)])
# CELL_P_RAW: BT104's + pad, under BT104's body (below its pads) on F.Cu + B.Cu, under the CELL_N column to F101 and
# along the J101 pins to J101 pin 5
K.zone("PRAW_F", "CELL_P_RAW", F, [(8.2, 103.0), (15.7, 103.0), (15.7, 104.0), (104.2, 104.0), (104.2, 107.5),
                                   (8.2, 107.5)], prio=1)
K.zone("PRAW_F101", "CELL_P_RAW", F, [(110.6, 96.5), (116.6, 96.5), (116.6, 103.8), (110.6, 103.8)], prio=1)
K.zone("PRAW_B", "CELL_P_RAW", B, [(8.2, 103.0), (15.7, 103.0), (15.7, 104.0), (110.6, 104.0), (110.6, 96.5),
                                   (116.6, 96.5), (116.6, 102.0), (134.8, 102.0), (134.8, 109.3), (131.8, 109.3),
                                   (131.8, 106.2), (110.6, 106.2), (110.6, 107.5), (8.2, 107.5)], prio=1)
K.vias("CELL_P_RAW", [(x, 104.6) for x in (9.0, 10.2, 11.4, 12.6, 13.8, 15.0)] +
       [(x, 105.8) for x in (9.6, 10.8, 12.0, 13.2, 14.4)] + [(x, 105.75) for x in range(28, 101, 8)] +
       [(x, y) for x in (111.2, 112.4, 113.6, 114.8, 116.0) for y in (99.4, 100.6, 101.8, 103.0)])
K.track("CELL_P_RAW", [(116.3, 97.4), (118.1, 97.4)], 0.5)              # TP108 second pad
# CELL_P: F101 up between the pack probe columns on F.Cu, under the gauge on B.Cu, into Q101's source pins from the left
K.zone("CELLP_F", "CELL_P", F, [(112.95, 95.4), (115.05, 95.4), (115.05, 92.2), (118.0, 92.2), (118.0, 58.8),
                                (115.0, 58.8), (115.0, 91.0), (112.95, 91.0)], prio=1)
K.zone("CELLP_B", "CELL_P", B, [(112.95, 95.5), (118.0, 95.5), (118.0, 58.8), (127.0, 58.8), (127.0, 26.0),
                                (115.0, 26.0), (115.0, 58.8), (112.95, 58.8)], prio=1)
K.zone("CELLP_Q101", "CELL_P", F, [(117.8, 25.9), (128.6, 25.9), (128.6, 25.1), (130.6, 25.1), (130.6, 27.0),
                                   (117.8, 27.0)], prio=1)
K.vias("CELL_P", [(x, 26.55) for x in (118.0, 119.0, 120.0, 121.0, 122.0, 123.0, 124.0)] +
       [(116.5, y) for y in (59.4, 60.6, 66.0, 72.0, 78.0, 84.0, 90.0)] + [(113.5, 91.8), (114.5, 91.8), (113.5, 92.9)])
K.track("CELL_P", [(114.5, 62.0), (115.3, 62.0)], 0.5)                  # TP101
K.track("CELL_P", [(128.6, 26.8), (128.6, 27.7)], 0.5)                  # C110
# FET_MID: Q101 and Q102 face the same way, so their drain pads join on B.Cu through a 3x3 via grid in each pad
K.zone("FETMID_B", "FET_MID", B, [(127.6, 21.6), (131.9, 21.6), (131.9, 33.0), (127.6, 33.0)], prio=1)
K.vias("FET_MID", [(x, y + o) for o in (0.0, 8.0) for x in (129.2, 130.0, 130.8) for y in (22.65, 23.35, 24.05)], **GV)
# PACK_P: Q102 source pins -> F.Cu strip -> B.Cu bus beside the port-1 output banks, to R430 (port 1), R530 (port 2),
# R431/R531 (5 V bucks) and the bench-supply diode
K.zone("PACKP_Q102", "PACK_P", F, [(128.6, 33.1), (130.6, 33.1), (130.6, 34.2), (136.0, 34.2), (136.0, 35.25),
                                   (128.6, 35.25)], prio=1)
K.track("PACK_P", [(130.55, 35.2), (130.55, 35.6)], 0.5)                # C107
K.zone("PACKP_B", "PACK_P", B, [(131.6, 13.4), (136.0, 13.4), (136.0, 46.9), (157.5, 46.9), (157.5, 49.3),
                                (136.0, 49.3), (136.0, 83.6), (157.5, 83.6), (157.5, 86.2), (133.5, 86.2),
                                (133.5, 54.8), (131.6, 54.8), (131.6, 36.2), (128.6, 36.2), (128.6, 33.6),
                                (132.2, 33.6), (132.2, 21.0), (131.6, 21.0)], prio=1)
K.vias("PACK_P", [(x, 34.75) for x in (129.0, 129.8, 130.6, 132.8, 133.6, 134.4, 135.2)])
for oy in (0.0, 37.0):                                                  # R430 / R530 PACK_P pads
    K.zone("PACKP_R30_%d" % oy, "PACK_P", F, [(131.7, 13.6 + oy), (135.7, 13.6 + oy), (135.7, 17.7 + oy),
                                              (131.7, 17.7 + oy)], prio=1)
    K.vias("PACK_P", [(132.1, 14.2 + oy), (132.1, 15.2 + oy), (132.1, 16.2 + oy), (133.0, 17.15 + oy),
                      (133.8, 17.15 + oy), (134.6, 17.15 + oy)])
for oy in (0.0, 37.0):                                                  # R431 / R531 (5 V buck inputs)
    K.via(156.25, 48.1 + oy, "PACK_P"); K.track("PACK_P", [(156.25, 48.1 + oy), (157.2, 48.1 + oy)], 0.8)
K.track("PACK_P", [(119.9, 57.3), (119.9, 59.5), (134.8, 59.5)], 1.0)   # D104 (bench supply) -> bus
K.track("PACK_P", [(119.9, 59.5), (120.65, 60.25), (120.65, 61.7)], 0.5)   # TP106
K.via(134.8, 59.5, "PACK_P")

# ---- In1 solid GND plane, In2 GND fill (whole board; fill clips to the outline and the antenna keep-out) ---------
for lay, name in ((IN1, "GND_PLANE_In1"), (IN2, "GND_PLANE_In2")):
    z = pcbnew.ZONE(board)
    z.SetLayer(lay); z.SetNet(net("GND")); z.SetZoneName(name)
    ol = z.Outline(); ol.NewOutline()
    for x, y in ((0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)):   # inset: no edge slivers
        p = k(x, y)
        ol.Append(p.x, p.y)
    z.SetAssignedPriority(0)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetLocalClearance(mm(0.2))
    z.SetMinThickness(mm(0.25))
    board.Add(z)

# ---- M3 mounting holes: 6.4 mm copper keep-out on every layer (clear of the screw head and washer, and no
# sliver between the hole's two clearance circles in the planes) -------------------------------------------------
import math
for fp in board.GetFootprints():
    if not fp.GetReference().startswith("H"):
        continue
    c = fp.GetPosition()
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetZoneName("KEEPOUT_" + fp.GetReference())
    ls = pcbnew.LSET()
    for lay in (F, IN1, IN2, B):
        ls.AddLayer(lay)
    z.SetLayerSet(ls)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ol = z.Outline(); ol.NewOutline()
    for i in range(32):
        a = 2 * math.pi * i / 32
        ol.Append(int(c.x + mm(3.2) * math.cos(a)), int(c.y + mm(3.2) * math.sin(a)))
    board.Add(z)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(PCB)
open(IDS, "w", newline="\n").write("\n".join(added) + "\n")
open(PRO, "w", encoding="utf-8", newline="\n").write(pro_backup)
print("zones", len(board.Zones()), "tracks+vias", len(board.GetTracks()))
