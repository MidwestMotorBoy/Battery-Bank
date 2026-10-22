# Concept A: "Gasketed box"

## 1. Concept

The body is a single **PETG FDM tub**, open on one long face. A **CNC aluminium lid**, which is also the heatsink, closes that face. The lid carries a bought **2.0 mm silicone O-ring** in a machined groove and is screwed down to a **metal-to-plastic hard stop**, so the O-ring squeeze comes from the groove depth and not from screw torque. This lid joint is the only gasketed joint. The two USB-C receptacles seal with their own silicone rings in bores in the top wall, backed by an RTV-filled moat. The BLE antenna radiates through the plastic tub wall, so no window is needed. Breathing is through an adhesive ePTFE vent on the lid. Before the vent goes on, its hole doubles as the leak-test port.

Inside, the cells sit in a **TPU cradle** and float on TPU end pads. The PCB is located by the shell (ledges, top-wall stops and a lug on the lid), so drop loads from the cells never pass through the PCB or the USB-C ports. Nickel tails from the cell strips pass through slots in the PCB, fold flat over the pads and are lap-soldered.

```
CROSS-SECTION (looking down the cell axis)          LONGITUDINAL SECTION
                                                       top end (USB-C)          bottom end
  o        Al lid / heatsink (black anod.)    o        TPU   PETG                PETG  TPU
 [=]==========================================[=]     bumper wall                wall  bumper
 [=] O  ___pedestal___                    O  [=]       ##  |=[USB]=PCB================]| ##
  lobe|  [thermal pad ]   BLE~~ant  |lobe          ## [RTV moat] ^lid lug behind PCB
      |  -L---Q----Q----------------|              ##  |stop|                         | ##
      |==========PCB 1.6============|<-ledge       ##  |pad|==cells 70.8, cradle==|pad| ##
      |  (C1 NL-)   (C4 NR+)        |              ##  | TPU end pads bear on crimp rims| ##
      |  (C2 FL)    (C3 FR)         |                  |________PETG floor____________|
      |__TPU cradle ribs____________|
      |_______PETG floor____________|          O = O-ring in lid groove; o = M2.5 from below,
                                                    tapped into the lid
```

## 2. Parts list

| # | Part | Material / process | Mass | Made/bought |
|---|---|---|---|---|
| 1 | Tub: 2.2 mm walls, all perimeters, no infill. Rim land 5.5 mm wide, ironed. 6 screw lobes (4 at the corners, 2 at mid-long-sides) with gussets. PCB ledges and top-wall stops. Two port bores, each with a 0.8 mm RTV moat | PETG, FDM, printed open face up | 60 g | made |
| 2 | Lid / heatsink: 2.5 mm base and a 4.5 mm rim band. O-ring groove 3.0 w × 1.5 d. Pedestal to the hot parts. 6 × M2.5 tapped holes. PCB-retaining lug. Antenna relief pocket. Vent hole in a 1 mm recess | 6061 Al, JLC CNC, black anodize | 40 g | made |
| 3 | Cell cradle: three bands joined by spines, crush ribs in the bores, a 0.4 mm insulating lip at each **+** end | TPU 95A | 12 g | made |
| 4–5 | End pads, top and bottom (different strip pockets): annular lands on the crimp rims, cap pockets, tail slots, 3 mm gyroid | TPU 95A | 2 × 3.5 g | made |
| 6–7 | End bumpers: press-on, wrap all 8 corners, cover the lid screw heads, USB-C plug cut-outs 13 × 7 mm | TPU 95A | 2 × 8 g | made |
| 8 | 4 × EVE INR21700-58E | — | 280 g | bought |
| 9 | PCB, assembled | — | 15 g | bought (JLC) |
| 10 | Pure nickel strip 0.2 × 8 mm: 3 series links plus 2 PACK straps with tails | Ni | 3 g | bought, cut to length |
| 11 | O-ring, ~78 × 2.0 mm, silicone 60–70A | VMQ | 1 g | bought |
| 12 | 6 × M2.5 × 10 pan-head screws, stainless | steel | 3 g | bought |
| 13 | Thermal pad, 1.0 mm, ≥3 W/m·K, pre-cut 15 × 30 mm | silicone gap pad | 1 g | bought, pre-cut size |
| 14 | Adhesive ePTFE vent, IP67 (Gore VE80205 class or similar) | ePTFE | <0.5 g | bought |
| 15 | Neutral-cure RTV, ~0.2 g; 28 AWG silicone wire, 40 mm (CELL2 sense) | — | — | bought |

**Notes on the parts:**
- **No heat-set inserts:** the screws go up through the PETG lobes into threads tapped in the aluminium lid. The plastic only sees bearing load under the screw head.
- **No PCB screws:** the board is captured between the ledges, the stops, the lid lug and the thermal pad.

## 3. Assembly sequence

1. Push the 4 cells into the cradle, **−** end first. The lip at each **+** end fixes polarity. Check every cell orientation with a meter.
2. On the bench, solder the 28 AWG CELL2 wire to the CELL2 link strip at the spot that will sit over C3's negative base.
3. Bend the tails on the PACK and column strips in a **printed bending jig** (the only fixture).
4. Spot-weld the 5 strips, using the cradle as the weld jig.
5. Press on the two TPU end pads, with the tails through their slots.
6. Drop the cell module into the tub.
7. Lower the PCB onto the ledges with the tails through its slots. Slide it about 2.5 mm toward the top wall until the receptacles enter their bores and the board edge hits the stops.
8. Fold the 4 tails flat over their pads and solder them. Solder the CELL2 wire.
9. Bench power-up, lid off: cell voltages, BLE, USB-C both ways.
10. Fill both port moats with RTV from outside and wipe flush. Let it cure.
11. On the lid: put the thermal pad on the pedestal. Fit the O-ring with a smear of silicone grease; 2 % stretch holds it in the groove when the lid is inverted. Place the lid; its lug drops in behind the PCB's bottom edge. Drive the 6 screws until the lid bottoms on the rim.
12. Leak test through the vent hole (§9), then stick the vent on.
13. Press on the two TPU bumpers.

That is **13 steps**. Tools: spot welder, 80 W+ iron, multimeter, screwdriver, and a hand pump with a gauge. One printed fixture.

## 4. Cell-to-PCB connection

**Cell layout and strip plan:**
- The 2×2 group has a near row (NL, NR) against the PCB and a far row (FL, FR).
- Top end: C1 (NL) **−** = PACK−, C4 (NR) **+** = PACK+, C2+/C3− link across the far row = CELL2.
- Bottom end: link NL→FL (C1+/C2− = CELL1) and link FR→NR (C3+/C4− = CELL3).
- Both power nodes are in the near row, so the 7 A tails are straight, wide and short (8 mm wide, about 5 mm free length).
- The two bottom links already run toward the PCB, so CELL1 and CELL3 are just extensions of those strips.

**The one crossing:** CELL2 is the only node that would have to cross a can rim at a different potential. It carries only sense and balance current, so it uses a wire instead of a nickel tail.

**Joint design:**
- Each tail passes through a slot in the PCB. The slot is 0.6 mm wide and 3.5 mm long axially, to allow for the slide.
- The tail folds 90° flat onto a 6 × 8 mm pad and is lap-soldered. This makes a large, inspectable fillet; it does not rely on a fillet inside the slot.
- **Kelvin sensing:** each PACK pad is split into force and sense copper on the board. The sense trace leaves the corner of the pad furthest from the board current. This leaves the ~0.3 mΩ tail inside the measured span, which is about 2 mV at 7 A. That is acceptable for the gauge.
- **Power losses:** 0.2 × 8 mm nickel is about 0.45 mΩ per 10 mm, so all the links and tails together dissipate under 0.25 W at 7 A.

**Vibration and drop:**
- The PCB is fixed to the shell and the cells float on about 1 mm of TPU. Relative motion is taken by the tails bending out of plane, which is their thin direction.
- With about 5 mm of free length and 0.5 mm of relative travel, bending strain is about 0.35 %. That is plastic, but low-cycle: tens of drops are fine.
- Vibration amplitude in a TPU-preloaded module is in microns, so fatigue is negligible.
- No solder joint is made on a cell can, and the CELL2 wire is soldered to the strip before welding.
- **No-welder option:** cells with factory-welded solder tabs would remove the spot welder altogether. 58E availability with tabs is unverified.

## 5. Sealing to IP67

| Leak path | Seal | Rationale |
|---|---|---|
| Lid to tub (the only gasketed joint) | 2.0 mm silicone O-ring in a CNC face groove 1.5 d × 3.0 w | **25 % squeeze** (inside the 20–30 % face-seal band, [Marco Rubber](https://www.marcorubber.com/downloads/Marco-O-Ring-Gland-General-Design-Considerations.pdf)); **~70 % gland fill** (60–85 % target, [Harkesh](https://harkesh.com/tools/groove-calculator)) |
| Groove shape | Corner radius ≥ 7 mm (3.5 × CS); ring stretched 1–3 % onto the groove inner wall | External (immersion) pressure pushes the ring onto the inner wall it already seats on |
| Printed side of the joint | One flat, ironed land | The tub is printed open face up, so the land is the last single-Z layer: planar by construction, and no layer lines cross the seal |
| Squeeze tolerance | ±0.2 mm on the land still gives 15–35 % squeeze | Why a 2.0 mm cross-section was chosen over 1.5 mm |
| Screw pattern | 6 screws: 4 corners + 2 mid-long-side lobes, all outside the seal line | Mid-span bowing is the classic failure ([Engineers Edge](https://engineersedge.com/general_engineering/gasket_cover_compression.htm)). O-ring load ≈ 1.5 N/mm × 255 mm ≈ 400 N. With 4 corner screws the lid bows 0.07–0.35 mm mid-span; with 6 it is under 0.02 mm. The PETG long walls are deep beams (2.2 × 55 mm) and do not bow |
| USB-C ×2 | Receptacle's own silicone ring (10.25 × 4.45 mm, 1 mm long) in a stadium bore of about 10.05 × 4.25 mm. Outer moat filled with neutral-cure RTV | A horizontal bore printed open face up has layer lines running *along* the bore, which are leak paths across a 0.1 mm squeeze. So the ring is the dam and the RTV is the seal. The RTV is inspectable from outside and the joint never needs to open |
| BLE | None: the antenna faces the PETG side wall | The lid has a 3 mm relief pocket over the antenna to push metal back to about 9 mm |
| Breathing | Adhesive ePTFE vent (IP67 rated, e.g. [Gore VE80205](https://gore.com/node/4951)) on smooth anodized Al in a recess | Without a vent, going from sea level to 4000 m gives +38 kPa inside, about 160 N on the lid. A −10→60 °C swing gives about ±25 kPa |
| Printed-wall porosity | All-perimeter walls ≥ 2 mm, 0.15 mm layers, hot nozzle, seam on the outside corner. Insert-free bosses never break through a wall | [Prusa's tests](https://blog.prusa3d.com/watertight-3d-printing-pt1-vases-cups-and-other-open-models_48949/): leaks come from seams and infill/perimeter transitions, and material stops mattering at about 6 perimeters (2–3 mm) |

**Why not a printed TPU gasket?**
- **Compression set:** FDM TPU 92A measures 21 % at 23 °C and **44 % at 70 °C** ([Stratasys FDM TPU 92A](https://WWW.STRATASYS.COM/contentassets/a194ef2599e447b6bbc6f5402437c890/mds_fdm_tpu92a_0124a.pdf)), and SLS TPU 90A measures 60 % at 70 °C ([EPFL](https://epfl.ch/schools/sti/ateliers/wp-content/uploads/2024/09/TPU_90A-SLS-EN.pdf)). Silicone is typically 10–30 % ([Polymax](https://www.polymax.co.uk/blog/compression-set/)).
- **Closure force:** 95A is roughly 10× stiffer than 60A silicone, so closure force goes up the same way.
- **Seams:** a printed gasket has seams and start/stop blobs. Hobby builders explicitly report "no formal IP rating" ([example](https://www.printables.com/model/1505724-outdoor-enclosure-for-govee-light-controller-tpu-g)).
- **Verdict:** a printed TPU gasket is fine for IP54. For IP67, a $0.20 O-ring is the right call.

**Other tub processes:**
- **MJF PA12** is porous and needs vacuum impregnation ([MDPI 2018](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6120015/)).
- **SLA** would be non-porous and give better bores, but it is brittle in drops.

## 6. Drop and vibration

**Benchmark:** a bare cell must pass 3 × 1 m drops onto concrete without fire under IEC 62133-2 cl. 7.3.3 ([In Compliance](https://incompliancemag.com/achieving-compliance-to-small-format-battery-pack-standards/)). The pack's job is to do better than a bare cell, especially at the **+** cap.

- **End-on, top:** cells → top TPU end-pad lands on the crimp rims (cap pocketed; the CID is never loaded) → PETG wall → TPU bumper.
  - At 4.4 m/s, stopping over about 3 mm of bumper plus pad travel gives about 330 g.
  - The PCB bears on its own stops. The receptacles never take the cell mass.
- **End-on, bottom:** the same path. The lid lug only stops the PCB from moving backward.
- **Lid face down:** cells → near-side cradle ribs → *underside of the PCB ledges* → walls → rim → lid.
  - There is a 1.5 mm gap from the cradle to the back of the PCB, which is more than the TPU can compress, so the PCB never takes cell load.
- **Floor or side:** cradle crush ribs, about 1 mm, against the walls.
- **Corners:** the 8 corners sit inside TPU bumpers. The lid edges are radiused, and the corner screw heads are buried in the bumper. A corner hit cannot shear the lid relative to the tub, because the screws and the hard-stop land carry it.
- **Vibration:** the module is preloaded about 0.3 mm by oversize TPU, and the PCB is preloaded by the thermal pad. There are no unsupported masses.

## 7. Thermal

**Heat path:** FETs and inductors → (thermal vias and part tops) → 1 mm pad, about 0.6 K/W over 450 mm² → pedestal → 2.5 mm Al plate, which spreads well → black-anodized outer face (ε ≈ 0.85).

**Lid on its own:**
- About 50 cm² at h ≈ 11 W/m²K, or about 18 K/W.
- 5 W steady would be +90 K, so **100 W is thermally a transient mode**.
- Lid plus board heat capacity is about 45 J/K. At 2 W losses (a 45 W load) it settles near +35 K.

**Cells:** the cells generate their own heat, about 3–5 W at 7 A (DCIR about 25 mΩ × 4). They are kept *thermally decoupled* from the lid by the PCB and an air gap, so lid heat doesn't age them.

**Firmware requirements:**
- Derate on the on-board temperature sensor.
- Hold the lid at **≤48 °C** (the touch limit for metal).
- Optionally, 1.5 mm milled fins on the lid would add about 40 % effective area for about 4 g.

## 8. Estimates

- **Body:** 52 (w, 56 at the lobes) × 59 (h) × 82 (l) mm.
- **With bumpers:** about 56 × 60 × 90 mm, roughly 300 cm³.
- **Mass:** about 440 g. Cells 280, tub 60, lid 40, TPU 35, PCB 15, other 10.
- **Parts:** 7 made + 4 cells + PCB + 5 strips + O-ring + 6 screws + pad + vent + wire = **27 pieces, 13 assembly steps**.
- **Materials:** PETG, TPU, aluminium, nickel, silicone (O-ring, RTV, pad), plus steel screws and the ePTFE vent. That is **5 core materials**.
- **Cost:** CNC lid about $15–25. Everything else is under $10, excluding the cells and PCB.

## 9. Risks and tests

1. **USB-C bore seal on a printed bore:** this is the weakest seal.
   - Test: print a coupon with bores in 0.05 mm steps and pressure-test each.
   - Fallback: rely on the RTV moat alone.
2. **Rim land flatness and PETG creep:** creep under 400 N at 60 °C slowly relaxes screw preload. Because the lid is on a hard stop, the squeeze is set by the groove, but the screws can lose preload.
   - Test: 70 °C soak for 48 h, then re-check torque and repeat the leak test.
3. **BLE under a metal lid:** a parallel plate about 9 mm away will detune the module.
   - Test: RSSI with the lid off vs on, at 5 and 10 m.
4. **Thermal:** a 100 W run is limited by the lid's heat capacity and needs derating.
   - Test: thermocouple on the lid at 45 W and at 100 W.
5. **Tail fatigue** after repeated end drops.
   - Test: 10 × 1 m drops per face, with a 4-wire resistance check of each joint before and after.
6. **Thermal runaway:** a gasketed box has no designed burst path. The PETG tub would fail first. This is the same as most consumer banks, but it is not elegant.
7. **Leak test procedure:**
   - Seal a printed TPU nozzle over the vent hole and hold +10 kPa (≈1 m of water) for 5 min.
   - Repeat with the pack submerged to locate bubbles.
   - Then fit the vent and do a 1 m / 30 min immersion, weighing the pack before and after.

## 10. Ideas others could borrow

- **Hard-stop gland with the groove in the CNC part:** the printed part only has to provide one ironed, single-Z land.
- **Screws from below into a tapped aluminium lid:** no heat-set inserts, and the plastic sees only compression.
- **Shell-located PCB with floating cells:** the PCB is captured by ledges, stops and a lid lug, with zero PCB screws. The cell mass never loads the USB-C ports or the board.
- **The vent hole as the leak-test port** before the vent is stuck on.
- **Strip plan that puts both 7 A nodes in the near row,** so only one sense line (CELL2) needs a wire.
- **Slot-and-fold lap joints** whose oversize slots also absorb the PCB's port-engaging slide.
- **A polarity lip on the + end of each TPU cradle bore,** which also acts as the insulator ring under the strip.
