# P0 assembly: one power module, then the cup

How a Monolith P0 goes together, from the mechanical model in `hardware/mechanical/` (**the cup**, `monolith_cup.py`; adopted 2026-10-21, it replaces the side tray). Parts and views: `hardware/mechanical/monolith_cup_exploded.png` and `monolith_cup_sections.png`; the connections: `hardware/mechanical/monolith_side_tabs.png` (unchanged).

**Status:** a plan. Nothing has been built yet, so expect it to change at the first fit print. Cells: FEB 21700G 6500 mAh (`docs/project/feb-21700g-datasheet-notes.md`).

![Cup, exploded](../../hardware/mechanical/monolith_cup_exploded.png)

## The idea

The cells, their PA12 carrier and the board become **one rigid power module, built and tested on the bench**:
- Every connection is a nickel tail through a plated slot in the board, soldered on F.Cu. No wire, no connector, no spring contact.
- The board sits on the carrier's pegs, so cells and board move together: the tails only take up cell-length tolerance, not drops.
- The module is programmed, gauge-trained and run at 100 W with everything open, before it goes into the cup.
- Nothing is soldered in the cup.

The cup is closed on five sides, with the two USB-C seal bores in its top wall. The module goes in **from the bottom**, port end first, and is pushed home until the USB-C faces seat in the top wall. A bottom cap seals it with one radial O-ring and is held by two radial M2 screws below the seal. There is no aluminium: the power stage's heat goes into the front cells through thermal vias and a dispensed gap filler, and the carrier's full-length PA12 webs share it with the back pair.

## Connections

| Connection | From | Nickel | Slot (KiCad x, y), length along x × 0.6 mm |
|---|---|---|---|
| PACK− | C1 bottom (can) | 0.2 × 7 tab, power finger 4.2 mm | (86.97, 135.48), 4.6 |
| 1N (gauge Kelvin) | same tab, Kelvin finger 1.2 mm | | (91.28, 135.48), 1.6 |
| CELL2 | C2+ / C3− strip, bottom | 0.15 × 3 tail, along a channel in the carrier's bottom frame, kapton wrapped | (100.00, 135.45), 3.4 |
| 4P (gauge Kelvin) | PACK+ tab, Kelvin finger 1.2 mm | | (108.72, 135.48), 1.6 |
| PACK+ | C4 bottom (+ cap) | 0.2 × 7 tab, power finger 4.2 mm | (113.03, 135.48), 4.6 |
| CELL1 | C1+ / C2− strip, top | the strip runs on as a 3 mm tail, down behind the board | (86.10, 69.48), 3.4 |
| CELL3 | C3+ / C4− strip, top | the same, mirrored | (113.90, 69.48), 3.4 |

The positions come from `sb_slots()` in `hardware/mechanical/monolith_shell.py`; the cup uses the same board, slots and tails. **FEB 21700G (2026-10-21):** the five bottom slots moved 0.30 mm toward the board's bottom edge (the cells sit 0.3 mm lower), and the PACK / Kelvin pairs 0.18 mm outward (wider cell pitch); the CELL1 / CELL3 slots and the board outline are unchanged. They're on the `TAB_SLOTS` and `TAB_SLOT_PADS` layers of `monolith_side_pcb.dxf`.

**Details:**
- **The PACK tabs split near the board.** The power finger takes the current; the Kelvin finger carries none, so it gives the gauge a true sense at the tab. 1N and 4P must stay separate nets on the board, routed to VC0 / SRN side and VC4.
- **Power loss:** about 1 mΩ per PACK tab (12 mm of 0.2 × 4.2 nickel), so about 0.09 W each at 9.4 A.
- **Strain relief:** the bottom tails have a 1 mm kink in the gap behind the board, and the top tails drop 5 mm behind it before turning into their slots. In the cup the board rides on the carrier, so the kinks only absorb tolerance and heat growth.
- **Behind B.Cu:** the tails run about 1.1 mm behind B.Cu in the areas on `BCU_TAIL_RUNS`. Only low parts (≤ 0.6 mm) there.

**Board changes needed:**
- Seven plated slots, 0.6 mm wide, 0.4 mm annular ring, at the positions above. Check JLC's minimum plated slot width when ordering.
- Remove the two 18 AWG PACK holes and the five B.Cu spring contacts.
- Route 1N and 4P as Kelvin nets to the gauge.
- Keep-outs: the carrier rails (`BCU_FRAME_BARS`, now split: no rail at z 25–55 mm), the tail runs (`BCU_TAIL_RUNS`), and the **gap-filler zone** on B.Cu (|y| 7–16 mm, z 27–53 mm: no parts, solid copper, a dense thermal-via array to the power stages on F.Cu).
- Two holes for the carrier's board pegs (Ø2.0 at y ±8.6, z 14 and 68).
- The cover standoffs (H101–H104) and the wedge's screw bosses no longer exist: the standoffs can go.

## Materials and tools

- **Cells:** 4 × FEB 21700G (68E) 6500 mAh, same batch, matched to within 10 mV and to within 1 mΩ on an AC (1 kHz) meter. Measure each cell's diameter: the cup is designed to the 21.85 mm maximum.
- **Nickel:**
    - 0.2 × 10 mm pure nickel for the three series strips (loss cut 4). The top two are cut long, so they run on as the CELL1 / CELL3 tails, trimmed to a 3 mm tongue.
    - 0.15 mm nickel, cut to 3 mm, for the CELL2 tail.
    - 0.2 × 7 mm pure nickel for the PACK tabs, slit at one end into the power and Kelvin fingers (plain nickel, decided 2026-10-24).
    - Source, and how to check it is real nickel: `spot-welding.md`.
- **Insulation:** kapton tape for the CELL2 tail. No fish paper: the carrier's frames and webs keep the cans apart and off the board.
- **Printed parts:**
    - the cup and the bottom cap (MJF PA12);
    - the cell carrier (MJF PA12): two frames, spines, split rails, board pegs and the front-back webs;
    - the TPU pad (inside the cap) and the two TPU bumpers.
- **Seal and fixings:** a 2.0 mm silicone O-ring (60A, ~25 % squeeze in the skirt groove), 2 × M2 screws, an ePTFE vent patch.
- **Thermal:** dispensed gap filler, ~3 W/m·K (about 4 g between the board and the two front cells).
- **Other:** conformal coat.
- **Tools:** an AWithZ P20B spot welder with handheld pens (`spot-welding.md`), soldering iron (a chisel tip and plenty of heat, for nickel into a plated slot), a multimeter, the gauge and programming setup (EV2400 on the SMBus pogo pads, XDS110 with Tag-Connect), and a hand pump with a gauge for the leak test.

## Steps

### 1. Cells into the carrier and welded, on the bench
1. **Check the cells.** Measure each cell's voltage, AC resistance and diameter; reject outliers.
2. **Cells into the carrier**, loaded sideways: the front pair (C1, C4) from the board side, the back pair (C2, C3) from the back. The webs hold the front and back pairs apart. Positions per `SB_CELLS` in the model: C1 and C3 + up, C2 and C4 + down.
3. **Qualify the weld first** on two spare cells (`spot-welding.md`), at the settings you'll use.
4. **Weld:**
    - Before the bottom strip goes in, weld the CELL2 tail onto its middle on the bench. That spot sits under the frame, where the pens can't reach once the strip is in.
    - Series strips, slid into the gap between the cell ends and the frame, welded through the frame windows: C1+→C2− top, C2+→C3− bottom, C3+→C4− top. Leave the two top strips long on the board side; they are the CELL1 and CELL3 tails.
    - Lay the CELL2 tail along the channel in the bottom frame. Wrap it in kapton.
    - The PACK− tab on the C1 bottom and the PACK+ tab on the C4 bottom, fingers toward the board side.

### 2. Gap filler and board on, on the bench
1. **Form the tails:** the 1 mm kink in the bottom tails, and the drop and 90° turn in the CELL1 / CELL3 tails, so each ends pointing +x at its slot. A printed bending jig makes them repeatable.
2. **Dispense the gap filler** on the two front cells where the rails stop (|y| 7–16 mm, z 27–53 mm), a little proud, so the board squeezes it.
3. **Board on:** lower it onto the carrier's pegs, threading the seven tails through their slots from B.Cu.
4. **Solder on F.Cu,** PACK− first, then PACK+, then the five sense tails. Trim each tail to about 0.5 mm proud.
    - The BQ40Z50-R2 datasheet (SLUSCS4C §9.2.2.1.3) gives no connection order, only the Kelvin rule for 1N and 4P.
    - The BQ294700 datasheet hasn't been checked yet. Check it before the first build.

### 3. Test the module, on the bench
1. **Check the seven voltages** at the slots against PACK−, then through the gauge.
2. **Program and set up:**
    - Flash the CC2340.
    - Load the BQ40Z50 golden file and run gauge training on the SMBus pogo pads (`p0-bringup-and-training.md`).
    - Load the BQ25756 and TPS25751 configuration.
3. **Function test:** charge and discharge on each port, the 100 W thermal run (thermocouples on a front and a back cell), the gauge readings, and BLE.
4. **Conformal coat**, last. Keep the coat off the antenna end, the pogo pads and the gap-filler zone.

### 4. Module into the cup
1. Port end first, push the module up into the cup from the bottom. The carrier's frames guide it; keep it square so the USB-C seal rings enter their bores together.
2. Push home until the carrier's top frame bears on the top wall and the USB-C faces sit in the top wall.

### 5. Cap
1. O-ring into the skirt groove, lightly greased with silicone grease.
2. TPU pad onto the cap, then push the cap in until the plate lands on the cup rim (hard stop). The pad preloads the core against the top wall.
3. Drive the two M2 screws through the side walls into the skirt bosses (below the O-ring, outside the seal).

### 6. Leak test, vent, bumpers
1. **Leak test** through the bare vent hole: +10–15 kPa, hold 5 min on a gauge, then dunk while pressurised and look for bubbles.
2. Stick the ePTFE vent patch over the hole.
3. Press the TPU bumpers on, top (port well) and bottom.

## Open items
- **Board:** the seven slots, Kelvin routing for 1N / 4P, the `BCU_TAIL_RUNS` keep-outs, the gap-filler zone and thermal vias, the two peg holes, and removing the PACK holes, spring contacts and cover standoffs.
- **Fit:**
    - The O-ring squeeze in an MJF bore: print a coupon of the cup mouth and cap, and dunk-test it.
    - How hard the module pushes home; the USB-C seal rings entering their bores together.
    - Tail lengths and the bending jig.
    - Whether the nickel kinks are enough strain relief in the vibration test. Measure each PACK joint's resistance before and after the vibration and drop tests.
- **Label:** the aluminium cover carried it; for the cup, emboss it in the PA12 or add a small label plate.
- **Service:** the board can't come off the cells without desoldering seven tails, and the cap is screwed. A bad cell means rework at the bench.
- **Connection order:** check the BQ294700 datasheet.
