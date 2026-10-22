# Concept D: "Sealed for life" (snap first, then seal with a bonded joint)

## 1. Concept in one paragraph

A single printed PETG **tub** with a closed bottom and an open top. It also has a rectangular **window** in one long face. A one-piece printed TPU **cradle** holds the 2×2 cells, which are spot-welded in place. The cradle also carries the PCB in a side groove. Together these make the **core**, which slides into the tub from the top. Two parts close the box. Both use the same joint: **snap in, then seal with MS-polymer**. (MS-polymer is a moisture-cure sealant that stays elastic and also works as an adhesive.)
- The **aluminium heatsink** is a C-channel from JLC sheet metal. Its flanges are tongues that go into a sealant-filled groove around the window, and they snap under printed barbs.
- The **top cap** carries the two USB-C bores and the breather/test port. It snaps onto the tub rim with a tongue-and-groove joint full of the same sealant.

Because the parts snap, the snaps hold everything while the sealant cures, so **no clamps and no screws** are needed. There are no gaskets either. A printed TPU **over-boot** is the bumper. It also holds the bonded edges against peel, but it is **not** counted as a seal. The pack is leak-tested once through the breather hole, before the vent label goes on, and is then never opened. The MS-polymer joints *can* be cut with a blade if surgery is ever needed.

```
 SECTION across the cells (looking down from the USB end)      LONG SECTION (side view)

        boot (TPU) 2 mm, rim 1.5 mm proud of Al                    USB-C x2 (bores in cap, sealant pocket)
   +--------------------------------------------+                ___||____||___  <- top cap (PETG), snap + MS bead
   |  +--------------------------------------+  |               |  ==tails B+ B- C2==  |  vent/test port
   |  | tub wall 2.0 PETG                    |  |               | [cradle top ribs]    |
   |  |  ( C1 )( C2 )   TPU cradle 1.2 mm    |  |   heatsink -> |#|      ( cells )      |
   |  |  ( C4 )( C3 )                        |  |   window      |#| PCB  ( 70.8  )      |
   |  |  ---------------- PCB 43 mm ------   |  |   (Al C-chan) |#|      (  mm   )      |
   |  |  [L][Q][L][Q]  hot parts             |  |               | |BLE   (       )      |  <- BLE antenna behind
   |  |  ~~~~ gap pad ~~~~                   |  |               | [cradle bottom ribs] |     plastic, no metal
   |  +==]==== Al C-channel 2 mm ====[==+   |  |               |_______tub floor______|
   |   groove+MS   (flanges = tongues)       |  |                 \___ boot end 5 mm __/
   +--------------------------------------------+
```

## 2. Parts list

| # | Part | Material / process | Mass | Made / bought |
|---|---|---|---|---|
| 1 | Tub (closed bottom, open top, heatsink window with sealant groove, snap barbs, 2.0 mm walls) | PETG FDM, 5 perimeters, 100 % infill | 40 g | made |
| 2 | Top cap (2× USB bores with sealant counterbores, Ø6 vent/test port, snap hooks, tongue) | PETG FDM | 8 g | made |
| 3 | Cell cradle: one piece. 2×2 pockets, annular end ribs, PCB groove, weld windows, polarity marks | TPU 95A FDM | 22 g | made |
| 4 | Heatsink: C-channel 46×60 mm face, 4 mm flanges, coated/marked outer face | 5052 Al 2.0 mm, JLC sheet metal | 18 g | made (ordered) |
| 5 | Over-boot: sleeve with a large heatsink window, open USB end, 5 mm end and corner pads | TPU 95A FDM | 35 g | made |
| 6 | Nickel: 3 series links, B+ and B− end strips with 7 A tails, 2 Kelvin tails | pure Ni, 0.2×10 mm (power), 0.15×5 mm (sense) | 8 g | bought strip |
| 7 | Cells, EVE INR21700-58E | – | 280 g | bought |
| 8 | PCB assembly | – | 20 g | bought |
| 9 | Gap pad, 1.5 mm soft (compressed to ~1.0 mm) | silicone thermal pad | 3 g | bought |
| 10 | Adhesive ePTFE vent label (Gore VE/PE class) | – | <1 g | bought |
| 11 | MS-polymer sealant (e.g. a Drei Bond 9160 / Sikaflex-type 1K) | – | 6 g | bought |

That is **5 structural parts** (tub, cap, cradle, heatsink, boot). The rest is cells, the PCB, nickel and consumables.

## 3. Assembly sequence

1. Check the cells are within ±10 mV of each other. Press them into the cradle in 4S orientation, following the moulded +/− marks.
2. Spot-weld the 5 nickel pieces through the cradle's weld windows. **The cradle is the weld jig.**
   - Top (USB) end: B−, B+ and the C2/C3 link with its CELL2 tail.
   - Bottom end: the CELL1 and CELL3 links.
3. Press the PCB into the cradle groove. The tails go through the PCB slots with an S-bend. Solder the 7 joints: B+, B−, CELL1–3 and 2 Kelvin.
4. Function check on the bench: BMS wake, three cell voltages, USB-C in and out.
5. Slide the core into the tub from the top. The cradle has a 0.3 mm interference fit, so the core is preloaded.
6. Lay the gap pad on the hot parts through the window.
7. Run an MS-polymer bead in the window groove. Press the heatsink in until its flanges click under the barbs.
8. Run a bead in the rim groove and in the two USB counterbores. Press the cap down over the receptacles until it clicks. Wipe off the squeeze-out.
9. Cure for 48 h at room humidity, with the vent hole open.
10. Leak test through the vent hole (see §5).
11. Dry the pack, then apply the vent label.
12. Pull on the boot.
13. Final test and gauge learn cycle over USB/BLE.

**13 steps, 1 cure wait, 0 screws, 0 clamps.**
- Fixtures: the cradle (it is the weld jig) and one printed TPU test-port nozzle.
- Tools: a hobby spot welder, a soldering iron, a sealant gun, a syringe or hand pump with a digital manometer, and a bowl of water.

## 4. Cell-to-PCB connection

**Topology (2×2, alternating cell orientation).**
- **USB end:** B− (C1−) and B+ (C4+) both end here, next to the buck-boost stage, so the 7 A path into the board is about 10 mm long. The C2+/C3− link is also at this end and gives the CELL2 tap.
- **Far end (BLE end):** this end only has the C1/C2 and C3/C4 links, which give CELL1 and CELL3. These carry sense current only.

**Power.**
- Each B± strip is pure Ni 0.2×10 mm, with 3 or more weld pairs on the cell.
- Each tail is about 30 mm long, ≈1 mΩ, which costs about 50 mW at 7 A.
- To lower the loss, a second strip layer can be welded on top.
- The tail goes through a 10.5×0.6 mm PCB slot and is soldered on both sides. A plated slot gives a large joint area.

**Kelvin.** A 5 mm sense tail is welded to the same B± cap, at a separate spot from the power welds. It lands on its own pad, so the gauge never sees the strip's voltage drop.

**Sense taps.** These are 0.15×5 mm tails, each with a fuse resistor on the PCB right at the pad.

**Survival.**
- The cells and the PCB are both held by **the same TPU cradle**, so under shock they move together. The tails only see small differential motion.
- The S-bend in each tail takes up the rest of that motion. The solder fillet takes no bending load.
- Nothing relies on spring contact pressure, so there is no fretting under vibration. That suits a pack that is never opened.
- The cradle's end ribs cover the welds, so no strip edge can reach the can or the tub.

## 5. Sealing to IP67

| Leak path | Seal |
|---|---|
| Heatsink to tub (about 220 mm perimeter) | The C-channel flanges sit in a 3 mm wide × 4 mm deep groove full of MS-polymer, giving ~0.5 mm bond lines. Each flange is sealed on both faces, 8 mm of path. |
| Cap to tub | Tongue-and-groove, MS-polymer filled, sealed on both faces. The snaps hold it during cure. |
| USB-C ×2 | The IP68 receptacle seals its own body. The shell is sealed to the cap by the receptacle's own O-ring/gasket (check from its datasheet whether it seals radially or on a face) and by a ring of MS-polymer in a counterbore. Unplugged ports are IP68 by design. |
| BLE window | None needed. The antenna edge sits at the BLE end, behind 2 mm of plain PETG. The heatsink stops 15 mm short of it. |
| Printed-part porosity | Print the PETG solid: 5 perimeters, 100 % infill, upper end of the nozzle-temperature range, 0.6 mm nozzle, 5 % over-extrusion. FDM still leaves ~micro-voids (one user measured ~20 % mass deficit), so **the leak test is what proves it**. Fix a failing pinhole by wicking thin CA into it and retesting. |
| Pressure and thermal breathing | An adhesive ePTFE vent (Gore PE/VE class, IP67–68 rated) goes over the Ø6 port. The same hole is the **test port**. |

**Why MS-polymer and not epoxy.**
- The CTE mismatch is Al 23 vs PETG ~68 ppm/K.
- Over a 70 K swing (−20 to +50 °C), that is about 0.13 mm of relative movement at each end of an 80 mm joint.
- A rigid epoxy line would crack. A 0.5–0.75 mm elastic MS line sees roughly 17–25 % shear strain, which is at the limit of the typical ±20–25 % movement rating.
- The bond lines are therefore deliberately thick, and the snaps carry the mechanical load so the sealant only seals.
- Use **PETG, not ASA**: ASA's ~95 ppm/K pushes the strain past the limit.
- Silicone is more elastic but bonds poorly to PETG without a primer.
- MS-polymer bonds to aluminium and to most plastics without primer. PETG-specific data is thin, so **test coupons first**.

**Leak test for a pack that never opens.**
- The free air volume is ≈ 60 cm³: about 190 cm³ inside minus ~103 cm³ of cells and ~25 cm³ of cradle and PCB.
- Push the printed nozzle into the vent port and pressurise to **+100 mbar**. That is about the hydrostatic pressure at 1 m, and stays under the 100–200 mbar that INFICON says IP67 seals tolerate.
- **(a) Pressure decay:** let the pack equalise for 30 min, then hold 5 min. A limit of 1×10⁻³ mbar·L/s, which is INFICON's "zero water" equivalent for IP67, allows only a **5 mbar drop**.
  - Temperature is the weak point: 1 K of drift is about 3.4 mbar.
  - Run the test in a closed box with the pack at room temperature, and use decay only as a gross pass/fail.
- **(b) Bubble dunk at the same +100 mbar:** this is the real test.
  - The inside is at higher pressure, so water cannot get in.
  - Each joint shows its own leak, so you know where to fix it.
- Then dry the pack and stick on the vent.

## 6. Drop and vibration

- **End-on (worst case for the CID/+ cap):**
  - Load goes boot end pad (5 mm) → PETG floor or cap → cradle end ribs → cell.
  - The ribs are **annular**: they bear only on the can's crimp shoulder, about 2 mm in from the edge. The middle of the + cap / CID is relieved.
  - The 4 mm ribbed TPU crush zone at each end gives the cells stopping distance.
  - The PCB rides in the cradle, so it decelerates with the cells and the tails are not loaded.
- **Side (heatsink face):**
  - The boot rim stands 1.5 mm proud of the Al, so a flat drop lands on TPU.
  - A rock point hitting the Al loads the 2 mm plate, then the soft gap pad, then the inductors. Keep a 0.5 mm free gap so a dent does not crush parts.
  - Peel at the bond edge is resisted by the snaps and by the boot rim lying over the flange edges.
- **Side (plain faces):** boot → 2 mm PETG → 1.2 mm TPU cradle skin → can. The can is spread over its whole length, so denting risk is low.
- **Corner:** 5 mm TPU boot corner pads, then the PETG corner (radius ≥3 mm). The snap barbs sit away from the corners.
- **Vibration:** the core is preloaded by interference, there is no free play, and every tail has an S-bend. The TPU cradle also gives some damping.

## 7. Thermal

**Heat path.** FETs and inductors → 1 mm compressed gap pad (≈3–6 W/m·K) → 2 mm Al spreader → air. The outer face is powder-coated or printed, giving ε ≈ 0.9 instead of ~0.05 for bare Al.

**Honest numbers.**
- The exposed face is ~46×60 mm ≈ 0.0028 m².
- With convection plus radiation at h ≈ 14 W/m²K, that gives ~0.04 W/K, so the face alone sheds only **~1.6 W at a 40 K rise**.
- **100 W continuous is a transient rating.**
  - The pack has ~300 J/K of thermal mass. At 5 W of loss, the internals warm about 1 K/min.
  - A full 82 Wh discharge at 100 W takes ~45 min.
  - So the firmware must derate on the heatsink-zone TMP1075 sensor, for example taper above 55 °C.

**Keeping the cells cool.** The PCB back faces the cells across a 2 mm air gap plus the 1.2 mm TPU skin, which insulates them. Heat goes outward to the Al. Do not cover the heatsink with the boot.

## 8. Estimates

| | |
|---|---|
| Shell outer | ~59 × 50 × 85 mm |
| With boot | **~63 × 54 × 93 mm (0.32 L)** |
| Total mass | **≈ 430 g** (cells 280) |
| Part count | 5 structural + 7 nickel + 4 cells + PCB + 3 consumables ≈ **20 items** |
| Material types | **4 made**: PETG, TPU, Al, Ni. **3 consumable**: MS-polymer, gap pad, ePTFE vent |
| Assembly | **13 steps**, 1 × 48 h cure, 0 screws, 0 clamps |

## 9. Risks and weak points

1. **No way back in without cutting.**
   - A dead cell or a board fault after closing means slicing the cap and heatsink beads with a thin blade or wire. That works because MS-polymer stays elastic.
   - Then slide the core out, and either desolder 7 tails or grind the welds to swap a cell.
   - The PETG parts are probably reusable after scraping the grooves. Plan on reprinting them (about 3 h).
   - Realistically, a failed P0 pack becomes a rebuild, not a repair.
   - **Mitigation:** do a full functional and charge-cycle test at step 4, *before* closing.
2. **A venting cell in a sealed box.**
   - A 21700 thermal event releases litres of gas, and the ePTFE vent cannot pass that flow.
   - Make the Ø6 vent port the **intended weak point**: the vent label blows off at well under the shell's burst pressure, and the port points away from the user's hand (USB end, side).
   - Test it: pressurise a sacrificial tub with a hose and confirm that the label fails first.
3. **Sealant adhesion on PETG and the CTE strain margin.**
   - Make lap-shear and peel coupons, then thermal-cycle them 20× from −20 to +60 °C and pull them apart.
   - If they fail, abrade and flame-treat the PETG, or move to a wider groove.
4. **FDM porosity.** The bubble dunk catches it. Expect some first-print rework.
5. **Leak-test drift.** Pressure decay on 60 cm³ is temperature-limited, so rely on the bubble dunk.
6. **USB seal stack.** If the receptacle seals on its face, cap-to-board tolerance controls the compression. The sealant counterbore covers this, but check with a dunk.
7. **Cure time and humidity.** 1K MS-polymer cures ~2–3 mm per 24 h, and the groove is 4 mm deep. Wait the full 48 h before the leak test.
8. **The heatsink is undersized for sustained 100 W.** Treat 100 W as a burst rating. Bench-test to steady state with thermocouples on the heatsink and on a cell.

## 10. Ideas other concepts could borrow

- **Snap first, then seal:** snaps carry the load and hold parts during cure, and the elastic sealant only seals. This removes clamps, screws and gaskets.
- **The C-channel heatsink flanges as tongues** in a sealant-filled groove. You get two sealed faces and a long leak path for free, plus a stiffer plate.
- **The breather hole doubles as the leak-test port.** Test before the vent label goes on, using a positive-pressure bubble dunk (water cannot get in).
- **The TPU cradle is the weld jig, the PCB carrier and the crush zone in one part.** Cells and PCB move together, so the tails stay unloaded.
- **Put B+ and B− at the USB/power end.** With an even series count and alternating orientation, both stack ends land on the same end of the cell group.
- **Annular end ribs** that load the crimp shoulder and keep force off the CID.
- **Make the vent the designed burst point.**
- **MS-polymer joints can be cut and redone,** which gives "sealed for life" an escape hatch.

**Rejected:**
- Print-pause embedding of the heatsink: PETG does not bond to Al, which leaves a leak path, and it would heat the parts.
- Printing the shell around the cells: hours at 70–80 °C bed temperature next to Li-ion cells.
- Solvent-welding PETG: it needs DCM.
- Using the TPU boot as the IP seal: a stretch-fit printed TPU sleeve is not a reliable seal.

### Sources
- INFICON, *Leak testing for ingress protection class IP67* (He-equivalent limits 1–2×10⁻³ mbar·L/s, 100 mbar test, seal damage above 100–200 mbar): https://www.inficon.com/media/5417/download/Leak%20testing%20for%20ingress%20protection%20class%20IP67%20miaq00en-04%20%282505%29.pdf
- Bonnen, pressure-decay leak-rate approximation: https://www.bonnenbatteries.com/waterproof-and-sealing-test-methods-for-commercial-and-industrial-energy-storage-battery-pack/
- MS-polymer substrate and primerless adhesion guide: https://www.allfasteners.com.au/ms-polymer-adhesive-sealant-guide
- Adhesive bonding of printed PLA/PETG/ABS/ASA (choice of adhesive and surface prep matter): https://link.springer.com/article/10.1007/s40194-025-02048-9
- FDM porosity (~20 % mass deficit, still leaks at high wall counts): https://forum.bambulab.com/t/printing-a-solid-air-tight-and-water-tight-print/189426
- Gore pressure vents datasheet (PE series IP67/68, adhesive −40 to 100 °C): https://www.gore.com/system/files/2024-08/GORE-Pressure-Vents-Datasheet-US-AUG24.pdf
