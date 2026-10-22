# A rigid core in a printed tub, closed by an O-ring heatsink lid

This report is a clean-sheet look at how the Monolith's four cells, board and heatsink should be held together and sealed. Five agents each designed a pack a different way:

- **A:** a gasketed box;
- **B:** a flashlight tube with end caps;
- **C:** a design driven by the cell-to-board connection;
- **D:** a bonded, sealed-for-life pack;
- **E:** a rigid core inside a TPU boot.

Each agent then cross-examined the other four and revised its own concept. They ended up much closer together than they started. The recommended design takes the inside of C and the shell of A, and borrows details from B, D and E:

- **Core:** a rigid PA12 core holds the cells and the PCB as one unit. Nickel links spot-welded to the cells pass through plated slots in the board and are soldered there.
- **Tub:** the core sits on TPU end pads in an MJF PA12 tub that is open on the board face.
- **Lid:** a CNC aluminium heatsink closes the tub. A bought silicone O-ring sits in a groove in the lid and seats against a hard stop.
- **Outside:** TPU bumpers on the ends take the drops.

The pack has three water paths: one O-ring joint, two USB-C port seals and a vent.

The constraints came from the brief (`research_notes/Ground-up mechanical concepts/brief.md`):

- **Cells:** 4 × EVE INR21700-58E in 4S1P.
- **Board:** about 43 × 74 mm, 1.6 mm thick, lying lengthwise beside the cells, with the two IP68 USB-C ports out of the top end.
- **Heatsink:** a metal heatsink pressed against the board is one of the outside walls.
- **Durability:** 1 m drops onto rock and mild vibration; IP67 if possible.
- **Assembly:** simple assembly matters more than serviceability.
- **Materials:** 3D-printed parts and metal only. No hand-cut foam, mica or fish paper.

The full concepts and critiques are in `research_notes/Ground-up mechanical concepts/`. The numbers below are the agents' own estimates, checked against each other in the cross-examination, unless a source is given. None of them has been measured on this pack.

## What the five concepts were, and what broke

| | Concept | Size (mm) | Mass | Steps | The flaw the others found |
|---|---|---|---|---|---|
| A | PETG tub; a CNC Al lid with an O-ring, screwed down | 56 × 60 × 90 | ~440 g | 13 | The cells float while the board is fixed to the shell, so the solder tails bend about 1.2 % per 0.5 mm of travel (A first claimed 0.35 %). The PETG screw lobes creep under ~400 N of O-ring load. The metal lid sits over the BLE antenna. |
| B | Printed tube; radial O-ring end caps; heatsink bonded into a window | 50 × 60 × 93 | ~425 g | 13 | The squeeze budget assumed ±0.3 % print tolerance, but JLC quotes ±0.3 mm. Redone, squeeze is 12–32 %, below the 15 % floor at the low end. B also has the most seal length: two O-rings plus a ~270 mm bonded joint. |
| C | Nickel tongues through PCB slots; rigid core; TPU boot | 86 × 51 × 56 | ~390 g | 14 | Its printed TPU rim bead sat under a 2 mm plate on 4 screws. The plate bows ~1.3–1.5 mm against ~0.45 mm of squeeze. C also put cell self-heating at 0.5 W instead of 3–5 W. |
| D | Snap together, then seal with MS-polymer; no screws | 63 × 54 × 94 | ~440 g | 13 | The Al/PETG expansion mismatch puts the sealant at 17–25 % shear strain against a ±20–25 % rating, with no margin. The bead may cure slowly at the root of a deep groove. A bad first build has to be cut open. |
| E | PA12 core inside a stretch-fit FDM TPU boot | 57 × 51 × 92 | ~410 g | 12 | Its printed bead squeeze is ~0.24 mm, about one print layer, under a bowing 1.5 mm plate. In E's first version the vent went on before the leak test, so the test couldn't detect anything. |

No concept survived unchanged. Three of the failures are general lessons that shaped the recommendation:

1. **Printed TPU can't be the main seal.** FDM TPU 92A takes a compression set of 21 % at 23 °C and **44 % at 70 °C** ([Stratasys FDM TPU 92A](https://WWW.STRATASYS.COM/contentassets/a194ef2599e447b6bbc6f5402437c890/mds_fdm_tpu92a_0124a.pdf)). Silicone takes typically 10–30 % ([Polymax](https://www.polymax.co.uk/blog/compression-set/)). The flat plates the concepts proposed also bowed more than the whole squeeze between their screws. A, C and E all ended up with a bought silicone O-ring.
2. **A stretched skin seals curves, not flats.** A tensioned membrane presses on a surface with p = T/R, which is zero on a flat face (E). A TPU boot can seal round port bores. The heatsink joint still has to be clamped, as GoPro housings do.
3. **Whatever moves in a drop must not span a solder joint.** If the board is fixed to the shell and the cells float, the tails take the drop. If the cells and board move as one core, the tails only take cell-length tolerance (C). All five concepts adopted this rule in the cross-examination.

## The recommended design

```
 CROSS-SECTION (down the cell axis)                LONG SECTION
                                                     top (USB-C)                  bottom
    o  CNC Al lid / heatsink, black anodized  o      TPU  PA12                   PA12  TPU
   [=]=====================================[=]     bump wall                     wall  bump
   [=] O   [gap filler]     |antenna: no lid|      ##  |=[USB]=====PCB==========|=|  | ##
   lobe|  ======PCB 1.6=======  (plastic)  |lobe   ##  [moat]  tongues soldered ^ ^  | ##
       |   |  |  slots   |  |              |       ##  |pad|== cells in PA12 carrier ==|pad| ##
       |  .-PA12 carrier, end frames------.|       ##  | TPU end pads on the crimp rims |  ##
       |  | (FL)          (FR) |           |           |____________PA12 floor_________|
       |  | (NL)          (NR) |           |
       |  '------------------- '           |       O = silicone O-ring in the lid groove
       |_________MJF PA12 tub______________|       o = M2.5 screws from below, through
                                                       metal compression limiters into the lid
```

### The core: cells and board as one part (from C)

**Carrier:** a one-piece MJF PA12 carrier holds the 2×2 cells. It does four jobs:

- Its end frames are the spot-welding jig.
- The 0.5 mm PA12 lip under each + end replaces the fish-paper rings.
- It is the drop load path.
- It carries the board on two pegs.

**Cell datum:** all four cells push against the bottom end frame, so cell-length tolerance (±0.2–0.3 mm) shows up only at the top end. One PCB peg is round, near the datum end; the other is slotted. Steel cans (~12 ppm/K) and FR4 (~14 ppm/K) expand almost alike, so locating both from the same end leaves ~0.01 mm of thermal mismatch at the joints. The PA12 (~100 ppm/K) is left to float.

**Interconnect:** pure-nickel busbars (0.15 mm, the gauge a hobby capacitor welder handles) are spot-welded to the cans. Each busbar has a Z-joggled tongue that drops down the side of the stack and through a plated slot in the board. The tongue is soldered there, ≥12 mm of nickel away from the can.

**Sense taps:** each series link is also its own sense tap. PACK+ and PACK− each split into a wide power tongue and a narrow Kelvin tongue. That makes **seven slots and no sense wires**. It is the same joint the repo adopted on 2026-10-21 ("nickel tails through plated slots"). This exercise reached it again on its own, and adds the datum and peg rules.

**Busbar supply:** JLC sheet metal can't make the busbars. It lists no nickel or nickel-plated grades and no thin gauges ([JLCCNC](https://jlccnc.com/blog/sheet-metel-online)). A ≥0.5 mm steel or copper bar can't be welded to a can with hobby equipment. The nickel is either strip formed in a printed die, or one-piece etched parts from a nickel-tab vendor. If no welder is available, cells with factory-welded solder tags would work with the same board.

**Which end carries the power:** C puts PACK± at the bottom, away from the crowded USB-C end, with only the narrow CELL1/CELL3 tongues between the ports. A, D and E put both 7 A nodes at the USB end for the shortest path to the converter. This is a board-layout choice and should follow the current Production placement.

**Bench test:** the core is a complete, testable power module before it ever sees the tub. It can be programmed, gauge-trained and run at 100 W on the bench. This matches the bench-built module in the current design.

### The shell: one O-ring joint (from A, revised)

**Tub:** MJF PA12 from JLC, open on the board face, 2.2 mm walls. A first proposed FDM PETG, then switched after the cross-examination: PETG lobes creep under the O-ring load at 55–60 °C, and its walls are weakest across the layers in an edge drop.

**Lid:**
- CNC 6061 aluminium, black anodized, about $15–25 from JLC CNC.
- A face-seal groove 3.0 mm wide × 1.5 mm deep holds a bought 2.0 mm silicone (VMQ) O-ring. That gives **25 % squeeze** and ~70 % gland fill, inside the 20–30 % face-seal band ([Marco Rubber](https://www.marcorubber.com/downloads/Marco-O-Ring-Gland-General-Design-Considerations.pdf)).
- Groove corners need a radius ≥ 7 mm.
- The lid lands **metal-on-plastic on a hard stop**, so the groove depth sets the squeeze, not screw torque.
- A 2.0 mm cord rather than 1.5 mm keeps 15–35 % squeeze across ±0.2 mm of rim error.

**The groove belongs in the precise part.** The tub only has to supply one flat land. Because the tub prints open face up, that land is a single layer.

**Screws:**
- Six M2.5 screws: four at the corners and two at the middle of the long sides, all outside the seal line.
- O-ring load is about 1.5 N/mm × 255 mm ≈ 400 N. With four corner screws the lid bows 0.07–0.35 mm mid-span; with six it bows under 0.02 mm.
- The screws go up through tub lobes into **threads tapped in the aluminium**, so there are no heat-set inserts.
- **New in this synthesis:** a pressed metal compression limiter (a brass or steel sleeve) in each lobe. The screw then clamps metal to metal, and PA12 creep can't relax the preload that keeps the lid on its stop. The cross-examination flagged this creep (B on A), but no concept fixed it.

**BLE:** the lid outline is cut back 8–10 mm over the module's antenna edge (from E), so the antenna sees only PA12. A's original lid covered the antenna at about 9 mm, and that concept had no clean fallback.

**USB-C ports:**
- The IP68 receptacle (C55629729) seals itself to the board. Its shell ring seals radially in a bore in the tub's top wall.
- Horizontal printed bores have layer lines running along the seal (A, B, C), so each port also gets an outside moat filled with neutral-cure RTV or MS-polymer as a second barrier.
- The carrier's top frame backs the receptacles, so a plug strike doesn't load the bore.

**Vent:** an adhesive ePTFE vent (IP67 class, e.g. [Gore VE80205](https://gore.com/node/4951)) on the anodized lid, in a recess. Without one, a trip from sea level to 4000 m gives about +38 kPa inside, roughly 160 N on the lid. A −10 → 60 °C swing gives about ±25 kPa.

**Burst path:** D argues for enlarging the vent hole to about Ø10 mm so it doubles as the burst path if a cell vents. The earlier rejection of enclosure venting still stands for shipping products. That makes this a judgement call to revisit, not a requirement.

**Bead vs O-ring:** the current design's 0.3 mm silicone-bead cover joint is the one big change. The cross-examination makes a clear case that a squeeze set by a hard stop in a precise groove is the joint with real margin.

### Drop protection (A, B, E)

- **Inside the tub:** the core sits on printed TPU end pads, a 3 mm gyroid. The pads bear on the can crimp rims and leave the + caps in pockets, so the CID never takes load. This follows the earlier potting and drop report.
- **Outside:** printed TPU end bumpers stand proud of the faces and corners and cover the corner screw heads, so drops land on them, not on the lid edge or the seal.
- **End-on:** at 4.4 m/s over ~3 mm of stroke, the average is about 330 g. The peak per cell is ~460 N over the ~210 mm² crimp shoulder, about 2 MPa, which the can takes easily.
- **Lid face down:** the load runs cells → carrier → PCB stack → thermal filler → lid. The bumper lip stands proud of the lid, so the plate edge doesn't take the first hit.
- **Watch:** the core moves about 1 mm on its pads in a drop while the lid is fixed to the tub, so the thermal interface shears. Use a soft filler, not a hard pad.

### Thermal: 100 W is a burst rating

All five concepts agreed on this, and I checked it independently:

| | Value |
|---|---|
| Heatsink face | ~35–50 cm² |
| Combined convection + radiation | ~15 W/m²K |
| Lid conductance | ~0.05–0.075 W/K |
| Heat shed at a 40 K rise | **~1–2 W** |
| Converter loss at 100 W | ~5 W |
| Cell self-heating at ~7.4 A | 4 × 7.4² × ~22 mΩ ≈ 4.8 W |

The ~22 mΩ is an estimate: no measured DCIR exists for the 58E. The cells' heat has no metal path out.

**Consequences for the firmware:**
- 100 W is limited by thermal mass, about 10–20 minutes, and needs a derate on both a board sensor and a cell-side TMP1075.
- About 45–60 W can run continuously.
- The lid should be held at ≤ 48 °C, the touch limit for metal.

**Options:**
- Milled fins on the lid would add about 40 % effective area for ~4 g.
- The board-to-lid interface should be a dispensed gap filler, or a pad bought pre-cut to size. Nothing hand-cut.

The 100 W thermal run planned in the earlier report sets the actual derate curve.

### Leak test (from D)

Before the vent goes on, its bare hole is the test port:

1. Seal a printed TPU nozzle over the hole.
2. Pressurise to **+10–15 kPa**, about 1–1.5 m of water, and hold for 5 min on a gauge (pressure decay).
3. Submerge the pack still pressurised and look for bubbles. Positive pressure means water can't get in during the test.
4. Fit the vent.
5. Do a 1 m / 30 min immersion, weighing the pack before and after.

Testing *after* the vent is fitted proves nothing: the inside equalises through the vent, so the seals see no pressure.

## Parts and assembly

| Part | Material / process | Made / bought |
|---|---|---|
| Carrier: end frames, + lips, PCB pegs | MJF PA12 | made (JLC) |
| Tub: rim land, lobes, port bores, moats | MJF PA12 | made (JLC) |
| Lid / heatsink: groove, tapped holes, vent recess, antenna cut-back, laser-marked label | CNC 6061, black anodized | made (JLC) |
| End pads ×2, end bumpers ×2 | TPU 95A | made (FDM) |
| Nickel busbars and tongues | 0.15 mm pure Ni | strip bought and formed, or one-piece etched |
| PCB with 7 plated slots | FR4 1.6 mm | made (JLC) |
| O-ring ~2.0 mm, ~78 mm ID | silicone | bought |
| M2.5 screws ×6, compression limiters ×6 | stainless, brass | bought |
| Gap filler, ePTFE vent, RTV or MS-polymer | — | bought |
| Bending die (fixture) | PLA/PETG | made |

**Materials:** PA12, TPU, aluminium and nickel are the made materials. The bought parts are silicone, small hardware and the vent. There are about 25 pieces, roughly 56 × 60 × 90 mm with bumpers, and about 430 g.

**Assembly (about 13 steps):**

1. Form the busbars in the printed die.
2. Load the cells into the carrier against the bottom datum, and meter each cell.
3. Spot-weld the busbars.
4. Lower the PCB onto the pegs, with all seven tongues into their slots.
5. Solder the seven tongues from the board's outer face.
6. Bench-test the core: program, gauge training, 100 W run.
7. Press in the compression limiters, then fit the TPU end pads and drop the core into the tub. Slide it so the ports enter their bores.
8. Fill the port moats from outside and let them cure.
9. Dispense the gap filler and fit the O-ring.
10. Fit the lid and drive the six screws until it seats on the hard stop.
11. Run the pressure-decay and bubble test through the vent hole.
12. Stick on the vent.
13. Press on the bumpers.

**Tools:** a spot welder, an 80 W+ iron, a meter, a screwdriver and a hand pump with a gauge.

**Firmware:** D's caveat applies here too. Once the lid is closed, J301/J302 are sealed in. Either firmware updates go over BLE, or the first P0 builds stay unsealed (lid on, no O-ring) until the electronics are proven. D recommended exactly that.

## Unresolved, and the tests that settle it

1. **Is untreated MJF PA12 watertight?** The concepts disagreed, and this is the one factual dispute left open.
   - A and B read MDPI 2018: untreated MJF PA12 vessels with walls ≥ 0.7 mm held > 0.4 MPa with no leak, in both build orientations ([PMC6120015](https://pmc.ncbi.nlm.nih.gov/articles/PMC6120015/)).
   - D and E cite the same paper and vendor forums for the opposite.
   - **Test:** order a closed PA12 coupon box with this wall and rim, pressurise it to 15 kPa and dunk it. If it weeps, the fallback is vacuum impregnation, or an FDM PETG tub with compression limiters.
2. **USB-C bore seal:** print a coupon with bores in 0.05 mm steps, with and without the moat, and pressure-test each.
3. **O-ring joint margin:** soak the closed tub at 70 °C for 48 h, then repeat the leak test and check screw torque.
4. **Tail fatigue:** 10 × 1 m drops per face on a dummy-mass core, with a four-wire resistance check of every tongue joint before and after.
5. **BLE range:** RSSI at 5 and 10 m with the lid off and on.
6. **Thermal:** a 100 W run with thermocouples on the lid and a cell, to set the derate.

## What changes versus the current design

The current design (tray, aluminium cover, bench-built power module, nickel tails through slots, wedge) is already close to this. The exercise mainly confirms its architecture. The changes it suggests are:

- **Cover joint:** a 0.3 mm silicone bead becomes a silicone O-ring in a CNC groove with a hard stop. The cover becomes CNC rather than flat sheet.
- **Cover screws:** add compression limiters, or thread the screws into the aluminium, so the plastic doesn't creep under the screws.
- **Fish paper:** the board-side sheet and + rings are replaced by printed PA12 lips on the carrier.
- **Leak test:** add the vent-hole pressure test to the assembly procedure.
- **Thermal derate:** treat 100 W as a burst rating in the firmware and the README.
