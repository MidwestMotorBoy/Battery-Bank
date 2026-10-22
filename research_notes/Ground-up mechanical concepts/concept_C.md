# Concept C — "Electrical-first": nickel tongues through the board, rigid core in a TPU boot

## 1. Concept in one paragraph

Start with the joint, not the box. The four cells (2×2) sit in a **one-piece PA12 carrier**. The carrier's two end frames also act as the welding jig, the insulator rings, and the load path in a drop. **Formed pure-nickel busbars** are spot-welded to the cells. Each busbar has a **Z-joggled tongue** that drops 4 mm down the side of the stack and passes through a **plated slot in the PCB**, where it is soldered like a through-hole pin. Each series link is also its own sense tap. PACK+ and PACK− each get a wide power tongue plus a narrow Kelvin tongue. That makes **seven slots and zero wires**. Cells, carrier, nickel and PCB become one rigid **"core"**, so cells and board cannot move relative to each other. The tongues therefore only absorb cell-length tolerance, not drop motion. The core is tested on the bench, then tilted USB-end-first into a **home-printed TPU 95A boot** (5 sides). The aluminium heatsink closes the 6th side. Four screws clamp the boot rim between the heatsink and a carrier flange. A bought 1.5 mm silicone O-ring sits in a groove printed into that rim, and PA12 hard stops poke through the rim to set the squeeze. The enclosure has one seal line, two port bores and one vent. *(Revised after cross-examination: the integral printed TPU bead was replaced by the O-ring, see critique_C.md.)*

```
 SECTION across cells (looking down the cell axis)        LONG SECTION (bottom end shown)
                                                          
   TPU boot 2-2.5 mm, ribbed inside                         heatsink  ===========[vent]====
  .-------------------------------.                         th.pad    ##   ##
  | .---------------------------. |                         PCB       ======|=|=====|=|====  <- tongues soldered
  | |  ( FL )        ( FR )      | |  far row                          ...  | |     | |        on the outer face
  | |  ( NL )        ( NR )      | |  near row              carrier  |  .--' |     | '--.
  | |___________________________| |  <- PA12 carrier wall           |  |  Z-joggle    |
  | ===========PCB============= | |  1.6 mm FR4                cell =|  |   flexure  |
  | ##  ##   hot parts   ##     | |  thermal pad                 ===+==+=nickel busbar=+==  (recessed 0.5 mm
  |=====heatsink 2 mm Al=========|=|  outside wall                end-frame post |   post        below posts)
  '-^-screw-------------------^-'                              TPU boot end wall + crush ribs
    O-ring in boot-rim groove, clamped heatsink -> carrier flange (PA12 hard stops)

 Series ring (2x2, alternating):  NL(+top) -> FL -> FR -> NR(+bottom)
   top end:    L1 = NL-FL (CELL1 tap)      L3 = FR-NR (CELL3 tap)      both reach PCB directly
   bottom end: PACK- on NL, PACK+ on NR, L2 = FL-FR (CELL2 tap) runs over a 0.8 mm PA12 bridge rib
   7 slots: PACK+ (P,K), PACK- (P,K) and CELL2 at the bottom; CELL1, CELL3 (narrow) at the top beside the USB-Cs
```

Power enters the board at the bottom end, away from the crowded USB-C end. The top-end tongues carry only sense current, so they are 3 mm wide and fit between the ports.

Note: the repo's 2026-10-21 commit ("nickel tails through plated slots", 7 fingers) reached the same joint independently. This concept adds the rigid-core/soft-boot enclosure, the datum and flexure rules, the bridge rib, and the vent hole used as a leak-test port.

## 2. Parts list

| # | Part | Material / process | Mass | Made/bought |
|---|---|---|---|---|
| 1 | Cells ×4 | EVE INR21700-58E | 280 g | bought |
| 2 | Carrier (end frames, bridge rib, PCB pegs, flange, 4 insert bosses) | MJF PA12 (JLC) or home PETG | 12 g | made |
| 3 | Busbars ×5: L1, L2, L3, PACK+, PACK− | 0.15 mm pure-Ni strip (10 mm), bent and dimpled in a printed die | 2 g | strip bought, formed |
| 4 | Sense/Kelvin tongues ×5 | 0.15 mm Ni strip (4 mm), welded Ni-to-Ni onto 3 links + 2 PACK tabs | <1 g | formed |
| 5 | PCB | 1.6 mm FR4 with 7 plated slots | 20 g populated | made (JLC) |
| 6 | Thermal pad | 1 mm silicone gap pad, pre-cut die-cut size | 3 g | bought |
| 7 | Heatsink / wall | Al 5052 2 mm, JLC laser cut, vent hole + 4 screw holes, laser-marked labels | 21 g | made (JLC) |
| 8 | Boot (5 sides, rim O-ring groove, port bores, crush ribs, corner voids) | FDM TPU 95A, 100 % infill | 45 g | made |
| 8a | O-ring, ~1.5 mm silicone, ~240 mm loop | VMQ | 1 g | bought |
| 9 | Heat-set inserts M2.5 ×4 | brass | 2 g | bought |
| 10 | Screws M2.5×8 ×4 | stainless | 2 g | bought |
| 11 | Adhesive ePTFE vent (≈8 mm, IP67/68 class) | bought | 0.3 g | bought |
| 12 | Bending die (fixture, reused) | PETG/PLA | — | made |

Path B (fewer parts): order the five busbars with their tongues as **one-piece laser-cut/etched pure-nickel or Hilumin parts** from a custom nickel-tab supplier. That removes part 4 and step 6. JLC's sheet-metal line lists Al 5052, stainless, cold-rolled and galvanised steel. I found no nickel or nickel-plated grade and no thin gauges ([JLCCNC](https://jlccnc.com/blog/sheet-metel-online)). A JLC busbar would be ≥0.5 mm steel, which a hobby welder cannot join to a can, so **JLC sheet metal is used only for the heatsink**.

## 3. Assembly sequence

1. Press 4 heat-set inserts into the carrier (soldering iron).
2. Cut Ni strip to length and form all busbars and tongues in the printed die. The die sets the Z-joggle and a 0.5 mm weld-pad dimple.
3. Insert cells into the carrier from the open back, following the moulded polarity arrows. Snap fingers hold the far row. All cells datum against the **bottom** end frame. Check each cell voltage.
4. Drop the busbars into the end-frame recesses. The recesses locate them, so no extra jig is needed.
5. Spot-weld all pads, both ends (2 pulses × 2 spots per pad).
6. Weld the 5 narrow tongues onto their links/tabs (Ni-to-Ni, away from the cells). *(Path B: skip.)*
7. Lower the PCB onto the carrier's round and slotted pegs. All 7 tongues enter their slots together, guided by the joggle compliance.
8. Solder 7 tongues from the outer face. Use an 80–100 W iron, ≤5 s per joint; the joint is ≥12 mm from any weld.
9. Bench-test the core (BMS boot, gauge, charge/discharge). No wires to disturb.
10. Place the thermal pad on the hot parts.
11. Tilt the core USB-first into the boot until the receptacles pop into their bores, then rotate it down.
12. Lay on the heatsink and drive 4 screws through heatsink → boot rim → carrier flange, in a cross pattern.
13. Leak test through the bare vent hole (§5).
14. Stick the adhesive ePTFE vent over the 2 mm hole on the heatsink's outer face (degrease first). It is applied last because the hole is needed for step 13.

**14 steps, 1 printed fixture** (bending die). Tools: capacitor spot welder, 80 W iron, multimeter, screwdriver, syringe + gauge for the leak test.

## 4. Cell-to-PCB connection

**Power path:** cell → 10 mm × 0.15 mm Ni link (≈1 mΩ) → PACK tab → 10 mm power tongue (≈0.7 mΩ) → plated slot → 2 oz pour. The total nickel in the path is ~5 mΩ, about 0.25 W at 7 A, spread over 5 pieces. The power slots are 10.5 × 0.6 mm, plated, and stitched with vias to both pours. Solder fills a 0.2 mm gap per side and leaves a fillet on both faces.

**Sense:** every link's tongue *is* the CELLn tap, so no separate sense harness can fail. The Kelvin pair is pure geometry: the narrow PACK± Kelvin tongue leaves the tab on the cell side of the power tongue, so the gauge sees no tongue IR drop.

**Tolerance and motion rules:**
- *Datum at one end.* All cells push against the bottom frame, so bottom-end tongues land exactly. Cell-length tolerance (±0.2–0.3 mm) appears only at the top end, where the 4 mm vertical leg of the Z-joggle flexes.
- *One fixed PCB peg, near the datum end.* The top peg is slotted. Carrier PA12 expands ~100 ppm/K, but the cells (steel, ~12 ppm/K) and FR4 (~14 ppm/K) expand almost equally. Locating both from the same end leaves ~0.01 mm thermal mismatch at the tongues; the plastic floats.
- *Rigid core.* The PCB is clamped to the carrier by the heatsink stack, so a drop moves the whole core in the boot. The tongues never see the 3 mm boot stroke.
- *Welds out of the load path.* Busbars sit 0.5–1 mm below the end-frame posts, so nothing presses on a weld.

**Why not the alternatives:**

| Method | Verdict |
|---|---|
| Nickel strip + spot welder (chosen) | Ni-to-Ni weld on the nickel-plated steel can is what the process is made for ([kWeld thread](https://endless-sphere.com/sphere/threads/spot-welding-copper-strips-to-18650-battery-cells.84680/page-3)). Hobbyists typically own a capacitor welder (kWeld, Malectrics, Glitter 801D class) that handles 0.15–0.2 mm pure Ni. Cheap handheld units manage ~0.1–0.15 mm, which is why 0.15 mm is specified. |
| JLC sheet-metal busbars (Cu/Al/steel) | Too thick and not nickel. Copper is among the worst materials to resistance-weld (electrode pick-up), and hobby welders struggle with it ([ES thread](https://endless-sphere.com/sphere/threads/resistance-soldering-bus-strips-to-18650-cells.88965/page-2)). Industry joins Al/Cu busbars to 21700s by laser wobble welding ([Warwick 2024](https://wrap.warwick.ac.uk/id/eprint/188181)), which is not hobby equipment. |
| Soldering directly to cells | The iron dwells seconds at ~350 °C on the terminal, which degrades the cell or can vent it ([Oscar Liang](https://oscarliang.com/solder-li-ion-battery-18650/)). The evidence is mixed, but it is not recommendable. The concept *does* solder, but at the PCB, ≥12 mm of 0.15 mm nickel away from the can, which is the accepted "solder to the strip, not the cell" practice. |
| Spring/pressure contacts | Vibration causes micro-motion and fretting oxide, so resistance climbs. They need high force and Au/Ni-plated BeCu ([patent US11699870](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11699870)). A 280 g cell mass in a 1 m drop momentarily unloads any spring, and 7 A through a fretting contact is a heat source. Rejected. |
| PCB as end plate | Impossible with the lengthwise board. A second end board just moves the wire problem to a board-to-board joint. |

**No-welder fallback:** buy 58E cells with factory-welded solder tags and solder the tongue to the tag. This keeps the same PCB.

## 5. Sealing to IP67

| Leak path | Seal |
|---|---|
| Boot ↔ heatsink (the only long seam) | A 1.5 mm silicone O-ring in a groove printed into the boot rim, squeezed ~25 % by the 2 mm Al plate. Four PA12 hard-stop bosses on the carrier flange poke through the rim and set the squeeze, so it doesn't depend on screw torque or TPU creep. Printed TPU has 21 % compression set at 23 °C and 44 % at 70 °C ([Stratasys TPU 92A](https://WWW.STRATASYS.COM/contentassets/a194ef2599e447b6bbc6f5402437c890/mds_fdm_tpu92a_0124a.pdf)), so the TPU only forms the groove; the O-ring is the seal. The 4 screws pass **outboard** of the bead, so their holes are outside the wet line. The boot wall stands 1 mm proud of the heatsink face to protect its edges. |
| USB-C ×2 | The IP68 receptacle seals itself to the PCB internally. Its shell gasket seals radially in a TPU bore (bore per datasheet, −0.1 mm). The carrier's top frame backs the bore so it can't walk. Verify the gasket style against the C55629729 drawing. *Revised:* the bores print horizontal, so layer lines run along them. As a second barrier, add a 1 mm counterbore around each port filled with MS-polymer. *Also revised:* the heatsink gets 3 mm bent return flanges so the plate doesn't bow between the 4 screws. |
| BLE window | None needed: the boot is TPU. The heatsink is cut back 8–10 mm over the module's antenna edge, and the boot rim widens to fill the gap. |
| Breathing | 82 Wh in ~0.1 L of air. Going from sea level to 4000 m is ~40 kPa of ΔP, which would peel the seal. An adhesive ePTFE vent sits over a 2 mm hole in the heatsink; adhesive bonds reliably to aluminium, poorly to TPU. In a cell vent event, the boot seam is the designed burst path. |
| Printed porosity | Boot printed at 100 % infill, 3+ perimeters, ~105 % flow, slow speed. TPU's layer fusion is good: hobby IPX7-style TPU containers passed 1 h submersions ([Fabbaloo](https://www.fabbaloo.com/?p=229876)). Backup: brush the inside with PU, which beat other coatings in a 1 bar FDM test ([3Druck](https://3druck.com/en/diy/waterproof-fdm-prints-comparison-test-of-different-waterproofing-methods-42157951/)). The PA12 carrier is inside the seal, so MJF porosity doesn't matter. |
| Leak test | Before the vent goes on, pressurise through the vent hole to 15 kPa (≈1.5 m of water), submerge, and watch for bubbles. Then apply the vent. |

## 6. Drop & vibration

At 1 m the impact speed is 4.4 m/s. The boot's internal crush ribs give ~3 mm of stroke, which means ≈330 g average and ~600 g peak on a 0.35 kg core.

- **End-on:** cell can → shoulder/rim → 0.5 mm PA12 insulator ring in the end frame → frame web → 5 posts (4 corners + centre valley) → boot end ribs. Peak ~460 N per cell over the ~210 mm² crimp shoulder ≈ 2 MPa, trivial for the can. The + button/CID and the welds sit in windows and recesses and are **never** in the load path.
- **Side/face:** cells → carrier walls → boot side ribs. On the heatsink face, the plate spreads the load into the PCB stack. The boot lip stands proud so the plate edge doesn't take the first hit.
- **Corner:** 4 mm TPU corners with internal voids act as soft crumple zones. The core has no sharp corners.
- **Vibration:** the only cantilevered metal is the 4 mm tongue legs, which weigh about a gram. Every heavy part is clamped.

## 7. Thermal

Heat path: hot parts → 1 mm gap pad → 2 mm Al outer wall → air. The plate alone is ~35 cm²; at ~15 W/m²K (convection + radiation) that is ≈0.05 W/K. **Steady state it sheds only ~1–1.5 W within a 48 °C touch limit**, which covers ~45–60 W continuous output. At 100 W (5 W loss), the heatsink + PCB + cell thermal mass buys roughly 10–20 min before firmware must derate on the heatsink NTC/TMP1075. The PCB's cell-side face is cool (no hot parts there) and separated from the cells by the PA12 wall, a deliberate thermal break. **Correction:** at 7 A the cells self-heat **3–5 W** (4 × 49 A² × ~15–25 mΩ DCIR). That is as much as the converter loss, and it has no metal path out. 100 W is therefore limited by cell temperature as much as by the heatsink, and the firmware must also derate on a cell-side TMP1075. This is an honest limit, not a solved problem.

## 8. Estimates

- Outer ≈ **86 × 51 × 56 mm** (≈245 cm³)
- Mass ≈ **390 g** (cells 280 g)
- Parts: **29** (Path A) / **24** (Path B), including the O-ring
- Assembly: **14 steps**, 1 fixture
- Material types: **4** structural (PA12, TPU, Al, Ni), plus FR4, silicone pad and hardware

## 9. Risks / weak points and tests

1. **The heatsink is thermally weak** for 100 W continuous. Test with a 100 W PD load and thermocouples; set the firmware derate curve from the data.
2. **The tilt-in of the USB ports through the TPU bores** may tear or slacken the bores. Print 3 boots and do 5 insertions each, then leak-test each. Fallback: slotted bores closed by the carrier collar.
3. **Weld pad reaching the + button through a 0.5 mm ring.** The 0.5 mm die dimple must be proven. Weld 10 sample pads on dead cells and peel-test them.
4. **Soft groove walls in printed TPU.** The hard stops must hold the O-ring squeeze at 25 ± 7 %. Check with a lipstick witness, then leak-test after 30 days at 45 °C and again after 20 thermal cycles.
5. **Solder-joint fatigue** at the slots under thermal cycling. Do −10/+50 °C × 100 cycles, monitoring CELLn and PACK resistance. Then drop 26 times (every face, edge and corner) per the 1 m spec and re-measure.
6. **Hand-bent nickel variance** (Path A). The die must be good. Path B removes this risk.
7. **No service:** a bad cell means rebuilding the core. Accepted per the priorities.

## 10. Best ideas to borrow

- **Every series link is its sense tap**, and the **Kelvin pair is two tongues on one tab**. No harness at all.
- **Datum the cells and the PCB from the same end** and let the plastic float. This removes tolerance and CTE from the solder joints.
- **Rigid core, soft boot.** The drop stroke happens outside the electrical joints.
- **The carrier end frame is the weld jig, the insulator ring and the drop load path** in one printed part, replacing fish paper.
- **Load-bearing posts stand taller than the busbars**, so no impact ever lands on a weld or a CID.
- **The vent hole doubles as the leak-test port.**
- **Bring power in at the end opposite the USB ports**. The tongues at the crowded end carry only µA and can be narrow.
