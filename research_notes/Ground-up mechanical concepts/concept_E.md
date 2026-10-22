# Concept E: rigid core with a soft skin

## 1. Concept in one paragraph

A **one-piece MJF PA12 core** carries all the loads. It holds the four cells in a 2×2 group, and its +x face is a flat deck for the PCB. A **one-piece FDM TPU 95A boot** covers the core like a phone case. The boot is the **only watertight skin**, so the porosity of the PA12 core no longer matters. It is open on one face only: a window over the PCB's hot zone. A flat **JLC 1.5 mm 5052 aluminium plate**, the heatsink, closes that window. Four screws clamp the plate down. The plate squeezes a **bead printed into the boot's window rim**, so the boot is also the gasket. The plate has no other openings except one vent hole.

The USB-C receptacles' own silicone rings seal in bores moulded into the boot's top end, and the PA12 core supports the boot from behind there. The BLE antenna sees TPU only, so it needs no window part. Each end of the boot is a 6 mm graded gyroid crush zone that protects the cell caps.

The cells are joined by spot-welded nickel. **Nickel tails** run through slots in the PCB and are soldered there, each with a Z-loop. The main research finding is this: a stretch-fit lip alone cannot seal a flat face. Contact pressure from a tensioned skin is p = T/R, which is zero on a flat. So the stretch fit locates the boot and seals the round port bores, while the heatsink joint is clamped like a GoPro housing. Section 9 describes E2, a metal-forward variant.

```
 SECTION across the cells (looking down the cell axis)

          boot rim bead (clamped)      Al plate 1.5 (outside wall)
             v                          v
   +--+=====[o]=========================[o]=====+--+   <- screw (TPU collar under head)
   |  |  gap filler ~~~  L1  Q1 ~~~  (BLE end: no plate) |
   |  | ===== PCB 1.6 =====================================|
   |  |  PA12 deck 1.0 (B.Cu pockets)          |  |
   |  |   ( A )   ( D )      A,D on PCB side   |  |  TPU boot 1.8
   |  |   ( B )   ( C )                        |  |  (corner noses 4)
   |  +------------------------------------+  |
   +-------------------------------------------+

 EXPLODED along the cell axis
     [ boot top: 2 port bores, 6 mm gyroid ]   <- boot is ONE part, top+bottom+3 sides
     [ PACK-/PACK+ strips, CELL2 strip in PA12 bridge groove ]
     [ PA12 core: 4 bores + deck ]  <- cells pressed in, core = weld fixture
     [ CELL1 / CELL3 strips ]
     [ boot bottom: 6 mm gyroid ]
     side: PCB -> gap filler -> Al plate + 4 screws
```

## 2. Parts list

| # | Part | Material / process | Mass | Made/bought |
|---|---|---|---|---|
| 1 | Cells ×4 | EVE 21700-58E | 280 g | bought |
| 2 | Core: 4 bores with 3 crush ribs each (0.2 mm interference), PCB deck with B.Cu pockets, CELL2 bridge groove, 4 screw bosses, polarity marks | MJF PA12 (JLC) | 25 g | made |
| 3 | Boot: 1.8 mm solid skin, 100 % infill, black; 6 mm graded gyroid ends; 4 mm corner noses; port bores; window rim with 1.0 × 0.8 mm bead and 4 screw collars | FDM TPU 95A (home) | 45 g | made |
| 4 | Heatsink plate: 52 × 84 × 1.5 mm, 3 mm return flanges on both long edges, Ø3 vent hole, laser-marked labels | JLC sheet metal 5052 | 18 g | made |
| 5 | Nickel strips ×5: CELL1 link, CELL3 link, CELL2 link, PACK− and PACK+ terminals (the PACK± terminals have a power tail and a thin Kelvin tail) | 0.2 × 8 mm pure Ni | 6 g | bought |
| 6 | PCB, populated | FR4 1.6 | 20 g | made (JLC) |
| 7 | Screws ×4, M2.5 × 10 thread-forming for plastics | steel | 1.5 g | bought |
| 8 | Thermal gap filler, dispensed (no pad to cut) | 1-part putty | 3 g | bought |
| 9 | ePTFE adhesive vent, about 8 mm, IP68-rated | bought | 0.3 g | bought |

That is 9 line items and 20 pieces, with 5 unique made parts. Cost is roughly US$25 plus the cells.

## 3. Assembly sequence

1. Press the four cells into the core, following the polarity marks moulded into it. The crush ribs hold them, and the core is the only fixture.
2. Spot-weld CELL1 (A−/B+) and CELL3 (C−/D+) across the bottom end, and pre-bend their tails up the A and D sides.
3. Flip the pack. Weld the CELL2 strip (B−/C+) with its tail lying in the PA12 bridge groove that runs between the A and D caps. Then weld the PACK− strip on A and the PACK+ strip on D.
4. Check the node voltages with a meter: 0, 3.6, 7.2, 10.8 and 14.4 V.
5. Snap the PCB onto the deck. Thread the 7 tails through the board slots, each with a Z-loop.
6. Solder the tails in BMS-safe order: PACK−, then CELL1, CELL2, CELL3, PACK+, then the two Kelvin tails.
7. Bench test the power-up, charge, discharge and BLE.
8. Stick the vent over the plate hole on its inside face.
9. Dispense gap filler on the inductors and FETs.
10. Fit the boot. Put the top in first so the ports enter their bores, then roll the bottom end over the core past the lip, as with a phone case.
11. Lay the plate in the window and drive the 4 screws in a cross pattern down to the plate's stops.
12. Leak test: put the pack under water in a jar and pull a vacuum with a hand pump. Bubbles from the vent location are expected; bubbles anywhere else mean a leak.

That is **12 steps**. The only fixture is the core. Tools: a capacitive spot welder, a 60 W+ soldering iron with flux, a screwdriver, a syringe and a jar with a hand vacuum pump.

## 4. Cell-to-PCB connection

**Layout.** Cells A and D lie against the PCB, and the series order is A→B→C→D. PACK− is on A's top end and PACK+ on D's top end, so **both 7 A terminals land at the PCB's top edge**, next to the USB-C ports and the power stage. CELL2, the B/C top link on the far side, crosses to the PCB in the moulded PA12 groove, which keeps it 1 mm clear of the A and D caps. CELL1 and CELL3 are bottom links whose tails run up the A and D sides to slots in the PCB's bottom edge.

**Power.** Pure nickel 0.2 × 8 mm measures about 0.9 mΩ over 20 mm, which is about 40 mW at 7 A. Hilumin is not suitable here.

**Sense.** Each tap is a 3 mm tail. The Kelvin pair comes from separate thin tails welded on the same PACK± strips, so the sense current never shares the power tail.

**Joints.** Every cell joint is a spot weld, so the cells never see iron heat. Every board joint is a soldered nickel tail in a slot: a through-board joint, much stronger than SMD pads.

**Vibration and drop.** Cells are fixed radially by the crush ribs and axially by about 0.4 mm of preload from the boot's gyroid ends. The PCB is clamped in the plate stack. Between them, each tail's Z-loop in a deck pocket takes up relative motion of about 0.5 mm, so solder joints are never the load path. Laser-cut nickel shapes can be bought, so there is no hand-cut strip.

## 5. Sealing to IP67

The boot is the envelope, and everything inside it is dry. That leaves **four leak paths**.

| Leak path | Seal |
|---|---|
| Boot wall | FDM TPU is well known for being easy to make watertight. Print 100 % infill, all perimeters (4–5 at 1.8 mm), flow 105–110 % and seams on the outside away from sealing faces. Prusa found that leaks come from seams and infill transitions, not layer bonding [1][2]. **Do not** use MJF TPU (88A) for the boot: MJF parts are porous and need vapour smoothing or impregnation to hold water [3]. |
| Heatsink window | **Clamped, not stretched.** A printed bead (1.0 wide × 0.8 tall) is squeezed about 30 % between the boot rim and the plate, inside the 25–35 % band suppliers recommend [4]. A solid 95A rim would need over 1 kN of clamp force, so the bead must be narrow. The plate's return flanges stiffen its edges between the 4 screws, because corner-only fastening is a documented cause of field leaks [5]. The rim lies on a 2 mm part-free strip around the PCB edge, with the deck behind it. |
| Screw holes | Each screw passes through a **TPU collar** moulded on the rim, which pokes up through an oversized plate hole. The screw head compresses the collar, so the boot is its own grommet. |
| USB-C ×2 | The receptacle's own silicone ring seals radially in an obround bore in the boot. The PA12 core's top wall backs the bore, so the TPU cannot walk off the ring in a drop. Port faces sit 0.5–1 mm below the boot surface: enough to protect them, but shallow enough for plug overmolds. |
| BLE window | None needed. The plate stops short of the BLE board end and the antenna sees only 1.8 mm of TPU. Keep steel screws at least 5 mm away from the antenna. |
| Breathing | An ePTFE vent sits on the plate's inside face. It stops the boot from ballooning at altitude (about 30 kPa at 3000 m) and stops cold-water immersion from pumping water past the seals. In a cell vent event, the TPU boot is also a natural blow-out panel. |

**Cold, UV and age.** TPU's Tg is about −30 to −50 °C, and Prusament claims 95A keeps its impact strength down to −50 °C [6][7]. It stiffens 2–3× near −20 °C, but a screw-clamped bead keeps its contact. Common filaments are aromatic TPU, which yellows and surface-degrades in UV. Stabilisers only delay this; aliphatic grades resist it [8][9]. So print **black** (carbon black is the cheapest UV screen) and treat the boot as a replaceable wear part. TPU's compression set is worse than silicone's, so the design relies on screw stops, not bead stress. The stretch-fit port bores lean on the silicone rings for their elasticity. If you can find a polyether TPU, prefer it to polyester, because polyester TPU hydrolyses in warm, wet conditions.

**Stretch seals in general.** Otterbox-style silicone skins with port plugs are sold as dust covers, not waterproofing [10]. Real IP67 action-cam housings use a rigid shell plus a clamped gasket. This concept follows that split.

## 6. Drop and vibration

- **End-on drop:** an empty 1 m drop is about 3.9 J for the whole pack and 2.75 J for the cells. Over a 4 mm gyroid stroke that is about 690 N, roughly 250 g, or about 170 N per cell. The gyroid is relieved over the cap centres so the load goes onto the crimp rims. The core's end rims do not carry cell inertia; the boot ends do.
- **Side drop:** the load goes through 1.8 mm of TPU, the 1 mm PA12 bore wall, and the can over its whole length. The boot stands 1 mm proud of the plate, so flat drops on the heatsink face land on the TPU rim. Components keep 0.5 mm of gap-filler clearance to the plate.
- **Corner drop:** hollow 4 mm TPU corner noses, the phone-case air-cushion trick, plus the rigid PA12 core corner behind them. This is the stiffest path.
- **Vibration:** crush ribs, axial preload and Z-loop tails. No mass hangs on a solder joint.

## 7. Thermal

The heat path is: FETs and inductors → about 0.5 mm of gap filler → the 1.5 mm Al plate (about 42 cm² exposed, with laser-marked or black surface for emissivity) → air. The plate spreads heat sideways into the rest of the pack.

Natural convection plus radiation is about 10 W/m²K. Over the whole pack surface (about 190 cm²) that is about 0.19 W/K. Heat capacity is about 330 J/K, so the time constant is about 30 min. A 100 W session (about 50 min, 5 W of loss) therefore gives about **+21 K**. That reaches about 50 °C cells at 30 °C ambient, above the 45 °C charge limit, so the firmware must derate. That is true of any shell this size.

A 1.8 mm TPU boot adds only about 10 % to each face's thermal resistance (2.7 vs 27 K/W). The skin is therefore not an insulation penalty. The PA12 deck (1 mm, plus B.Cu pockets) sits between the PCB and cells A and D and keeps them from hot-spotting.

## 8. Estimates

- **Size:** about 57 × 51 × 92 mm, about 270 cm³. That is the 46.6 mm core plus 7.8 mm for the deck, PCB, parts, filler and plate on x, plus the boot.
- **Mass:** about **400 g**, of which 120 g is not cells.
- **Parts:** 20 pieces, 5 unique made parts, 12 assembly steps, 1 fixture (the core).
- **Material types:** PA12, TPU, Al and Ni, plus bought steel screws, gap filler and the vent.

## 9. Variant E2: metal forward

Two JLC 1.0 mm aluminium U-channels nest into a box tube, with the heatsink half on the PCB side. The ends close with TPU end caps that act as bumpers and gaskets. A TPU liner must insulate the cans from the metal.

- **Better:** the whole shell is a heatsink, so there are no hot spots. It resists cuts and rock scrapes.
- **Worse:** two 160 mm overlap seams need sealant, which more than doubles the seal length. The BLE antenna needs a cut-out plus a TPU patch, a fifth seal. It adds about 25 g and a liner part, and the aluminium dents permanently on rock.
- **Verdict:** use E2 only if sustained 100 W matters more than IP67 margin.

## 10. Risks and tests

1. **Bead clamp force and plate bowing between screws.** Measure with pressure-indicating film or a lipstick witness, then vacuum-dunk.
2. **The boot must not leak** (print tuning, seam placement). Before assembly, print a test cup with the same settings and run a 24 h water hold plus a vacuum test.
3. **The fit must survive temperature extremes and set:** the boot's stretch fit over the ports and its fit as a whole at −20 °C, and long-term set. Run freezer then hot-car cycling (−20/+60 °C ×20), then re-test.
4. **The PCB needs a 2 mm part-free edge strip** for the rim. Check it against the current layout before committing.
5. **Thermal limit at 100 W.** Log the TMP1075 readings over a full 100 W charge.
6. **End-drop gyroid tuning.** Do instrumented drops (a phone accelerometer taped to a dummy pack), then measure the cell's OCV and check the caps.
7. **UV yellowing and hardening.** Accept it, and reprint the boot (about 2 h, about $2).

## 11. Ideas others could borrow

- **A skin that owns the water, with a core that owns the loads.** This lets a porous MJF PA12 core and printed parts go unsealed.
- **p = T/R:** never trust a stretch fit on a flat face. Clamp flats, and stretch-seal only round bores.
- **Gasket bead and screw grommets printed into the boot,** so no O-rings are bought.
- **A–D cell order** that puts both 7 A terminals at the PCB's port end, with the far tap carried over in a moulded insulating bridge groove.
- **The core as the welding fixture,** with polarity marks moulded in.
- **Vacuum-jar bubble test,** with the vent as the expected bubble source.
- **The TPU boot as the BLE window and the vent-event blow-out panel.**

Sources:
[1] [Snapmaker – watertight prints](https://www.snapmaker.com/blog/3d-printing-watertight/)
[2] [Prusa – watertight 3D printing](https://blog.prusa3d.com/watertight-3d-printing-pt1-vases-cups-and-other-open-models_48949/)
[3] [Xometry forum – MJF electronic casing / TPU sealing](https://xometry.pro/en/topic/best-process-to-3d-print-electronic-card-casing)
[4] [Rogers – enclosure seal compression 25–35 %](https://rogerscorp.com/blog/2025/the-mechanics-of-enclosure-seal-design-gap-spacing-cfd-and-compressibility); [Stockwell – submerged gaskets](https://www.stockwell.com/submerged-gaskets/)
[5] [Modus Advanced – IP67 enclosure field-leak case study](https://www.modusadvanced.com/hubfs/Modus_Case_Study_Final.pdf)
[6] [Prusament TPU 95A listing (−50 °C claim)](https://www.3djake.com/prusa/prusament-tpu-95a-jet-black)
[7] [PMC8347130 TPU property table (Tg −42 °C, brittle point ≤ −68 °C)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8347130/table/polymers-13-02467-t002)
[8] [Covestro – aromatic TPU yellowing](https://solutions.covestro.com/en/highlights/articles/theme/product-technology/optical-properties)
[9] [Adhesives Magazine – aliphatic vs aromatic PU](https://adhesivesmag.com/articles/91695-options-for-polyurethane-chemistry)
[10] [Otterbox Defender (silicone skin, port plugs for dust)](https://www.officer.com/command-hq/technology/computers-software/handheld-computers/product/10307614/otter-products-llc-defender-series-for-tablets-ipad-2-and-blackberry-playbook)
Sheet-metal bend and flange rules: [Fictiv](https://blog.fictiv.com/specifications/sheet-metal). Check JLC's own limits.

## Revisions after cross-examination (see critique_E.md)
- Rim seal: bought 1.5 mm silicone cord in a groove in the boot rim, squeeze set by the plate stops. The printed bead is the P0/IP54 option only, because FDM TPU 92A takes 44 % compression set at 70 °C (Stratasys MDS).
- USB bores: an MS-polymer-filled moat around each port, because the window-up print leaves layer lines along the bore axis.
- Thermal corrected: plate-only path ≈ 0.042 W/K, so about 1–1.7 W steady within a 48 °C touch limit (τ ≈ 16 min) and 100 W is burst only. Added 12 mm plate returns lying outside the boot sides as fins (+50 % area, +7 g).
- Vent moved to the plate's outside face and applied last. The leak test is now +100 mbar through the bare vent hole while dunked; it replaces the vacuum jar, which pulls water in on release.
- Cells datum toward the PCB-fixed end (from C).
