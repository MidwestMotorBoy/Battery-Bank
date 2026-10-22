# P0 assembly: one power module, then the tray

How a Monolith P0 goes together, from the mechanical model in `hardware/mechanical/` (side tray). The six steps are shown in `hardware/mechanical/monolith_side_assembly.png`; the connections are in `hardware/mechanical/monolith_side_tabs.png`.

**Status:** a plan, updated 2026-10-21 for the bench-built power module (it replaces the flying leads and the spring-contact sense strip). Nothing has been built yet, so expect it to change at the first fit print.

![Assembly steps](../../hardware/mechanical/monolith_side_assembly.png)

## The idea

The cells, their TPU frame and the board become **one power module, built and tested on the bench**:
- Every connection is a nickel tail through a plated slot in the board, soldered on F.Cu. No wire, no connector, no spring contact.
- The module is programmed, gauge-trained and run at 100 W with the board fully open, before it goes near the tray.
- Nothing is soldered in the tray.

The tray opens on one side only, and the USB-C faces have to pass into the top wall. So the whole module does what the board used to do alone:
1. It drops in through the open side, resting on its ring carrier. The board then sits about 2.1 mm low, so the USB-C faces pass under the top wall.
2. It lifts 2.5 mm, so the USB-C faces enter the top wall and the board's top edge seats on the stops.
3. A PA12 wedge is pushed in under it from the open side. The wedge fills the 2.5 mm under the cells and reaches the board's bottom edge, so it is also the old shim. Its chamfered nose takes up the 0.4 mm preload, and the cover traps it.

## Connections

| Connection | From | Nickel | Slot (KiCad x, y), length along x × 0.6 mm |
|---|---|---|---|
| PACK− | C1 bottom (can) | 0.2 × 7 tab, power finger 4.2 mm | (87.15, 135.18), 4.6 |
| 1N (gauge Kelvin) | same tab, Kelvin finger 1.2 mm | | (91.45, 135.18), 1.6 |
| CELL2 | C2+ / C3− strip, bottom | 0.15 × 3 tail, between the spring rings, kapton wrapped | (100.00, 135.15), 3.4 |
| 4P (gauge Kelvin) | PACK+ tab, Kelvin finger 1.2 mm | | (108.55, 135.18), 1.6 |
| PACK+ | C4 bottom (+ cap) | 0.2 × 7 tab, power finger 4.2 mm | (112.85, 135.18), 4.6 |
| CELL1 | C1+ / C2− strip, top | the strip runs on as a 3 mm tail, down behind the board | (86.10, 69.48), 3.4 |
| CELL3 | C3+ / C4− strip, top | the same, mirrored | (113.90, 69.48), 3.4 |

The positions come from `sb_slots()` in `hardware/mechanical/monolith_shell.py`. They're on the `TAB_SLOTS` and `TAB_SLOT_PADS` layers of `monolith_side_pcb.dxf`.

**Details:**
- **The PACK tabs split near the board.** The power finger takes the current; the Kelvin finger carries none, so it gives the gauge a true sense at the tab. 1N and 4P must stay separate nets on the board, routed to VC0 / SRN side and VC4.
- **Power loss:** about 1 mΩ per PACK tab (12 mm of 0.2 × 4.2 nickel), so about 0.09 W each at 9.4 A.
- **Strain relief:** the bottom tails have a 1 mm kink in the gap behind the board, and the top tails drop 5 mm behind it before turning into their slots. Cells and board are held separately by the tray, so the nickel must flex rather than carry them.
- **Behind B.Cu:** the tails run about 1.1 mm behind B.Cu in the areas on `BCU_TAIL_RUNS`. Only low parts (≤ 0.6 mm) there.

**Board changes needed:**
- Seven plated slots, 0.6 mm wide, 0.4 mm annular ring, at the positions above. Check JLC's minimum plated slot width when ordering.
- Remove the two 18 AWG PACK holes and the five B.Cu spring contacts.
- Route 1N and 4P as Kelvin nets to the gauge.
- Keep-outs: frame bars (`BCU_FRAME_BARS`) and tail runs (`BCU_TAIL_RUNS`).

## Materials and tools

- **Cells:** 4 × EVE INR21700-58E, matched to within 10 mV and checked for internal resistance.
- **Nickel:**
    - 0.15 × 7 mm pure nickel for the three series strips. The top two are cut long, so they run on as the CELL1 / CELL3 tails.
    - 0.15 mm nickel, cut to 3 mm, for the CELL2 tail.
    - 0.2 × 7 mm pure nickel for the PACK tabs, slit at one end into the power and Kelvin fingers.
    - You'll need a spot welder that handles 0.2 mm.
- **Insulation:** kapton tape, fish-paper + rings.
- **Printed parts:**
    - the tray (MJF PA12);
    - the wedge (MJF PA12), with two M2 heat-set inserts in its corner bosses;
    - the TPU cell cage, and the TPU cell frame (ring carrier and top frame);
    - the TPU caps.
- **Sheet stock:**
    - 0.2 mm fish paper: the sheet on the board side, four + end rings;
    - 1 mm EVA, only for the two USB-C hold-downs.
- **Cover and fixings:** the anodized cover and 2 × M2 thread-forming screws with a nylon patch.
- **Other:**
    - a 0.5 mm gap pad;
    - an ePTFE vent patch;
    - neutral-cure silicone;
    - conformal coat.
- **Tools:** soldering iron (a chisel tip and plenty of heat, for nickel into a plated slot), a multimeter, and the gauge and programming setup (EV2400 on the SMBus pogo pads, XDS110 with Tag-Connect).

## Steps

### 1. Cells welded, on the bench
1. **Check the cells.** Measure each cell's voltage and internal resistance, and reject outliers.
2. **Cells into the cage**, standing on the ring carrier (rings up), in their positions (`SB_CELLS` in the model: C1 and C3 + up, C2 and C4 + down). The webs keep them 1.4 mm apart. Fish-paper rings on the four + ends.
3. **Weld:**
    - Series strips, over the cage: C1+→C2− top, C2+→C3− bottom, C3+→C4− top. Leave the two top strips long on the board side; they are the CELL1 and CELL3 tails.
    - The CELL2 tail onto the middle of the bottom strip, along the channel between the spring rings. Wrap it in kapton: it passes under the C1 and C4 rims.
    - The PACK− tab on the C1 bottom and the PACK+ tab on the C4 bottom, fingers toward the board side.

### 2. Frame and board on, on the bench
1. Top frame over the cells: plate on the top ends, bars down the board side.
2. Fish-paper sheet on the cells' board-side face. The tails pass over and under it.
3. **Form the tails:** the 1 mm kink in the bottom tails, and the drop and 90° turn in the CELL1 / CELL3 tails, so each ends pointing +x at its slot. A printed bending jig makes them repeatable.
4. **Board on:** lower it onto the frame bars, threading the seven tails through their slots from B.Cu.
5. **Solder on F.Cu,** PACK− first, then PACK+, then the five sense tails. Trim each tail to about 0.5 mm proud.
    - The BQ40Z50-R2 datasheet (SLUSCS4C §9.2.2.1.3) gives no connection order, only the Kelvin rule for 1N and 4P.
    - The BQ294700 datasheet hasn't been checked yet. Check it before the first build.
6. Tape the module together at the bottom −x corners, so the ring carrier stays put.

### 3. Test the module, on the bench
1. **Check the seven voltages** at the slots against PACK−, then through the gauge.
2. **Program and set up:**
    - Flash the CC2340.
    - Load the BQ40Z50 golden file and run gauge training on the SMBus pogo pads (`p0-bringup-and-training.md`).
    - Load the BQ25756 and TPS25751 configuration.
3. **Function test:** charge and discharge on each port, the 100 W thermal run, the gauge readings, and BLE.
4. **Conformal coat and staking**, last. Keep the coat off the antenna end and the pogo pads.

### 4. Module into the tray
Slide it in through the open side, resting on its ring carrier. The board sits about 2.1 mm low, so the USB-C faces pass under the top wall. The crush ribs bear on the cell wraps as it goes in.

### 5. Lift and wedge
1. Lift the module 2.5 mm, for example with a flat spudger under the board's bottom edge, until the USB-C faces sit in the top wall and the board's top edge bears on the stops.
2. Hold it there and push the wedge in under it from the open side, nose first. The nose lifts the ring carrier the last 0.4 mm, which preloads the cell stack.
3. It clicks home over the ridge on the tray floor. Its two corner bosses now sit beside the board's notches, ready for the cover screws.

### 6. Close
1. Gap pad on the tall parts, kept clear of the vent.
2. ePTFE vent patch inside the cover.
3. Silicone bead along the cover joint.
4. USB-C hold-downs (2 × 1 mm EVA).
5. **Cover:** tuck it under the top lip, then drive the 2 M2 screws into the wedge's inserts. The four cover standoffs sit 0.2 mm under it.
6. Snap the TPU caps on.

## Open items
- **Board:** the seven slots, Kelvin routing for 1N / 4P, the `BCU_TAIL_RUNS` keep-outs, and removing the PACK holes and spring contacts.
- **Fit:**
    - How hard the wedge is to push in against the preload. If it's too stiff, lengthen the nose.
    - Tail lengths and the bending jig.
    - Whether the nickel kinks are enough strain relief in the vibration test. Measure each PACK joint's resistance before and after the vibration and drop tests.
- **Service:** the board can't come off the cells without desoldering seven tails. That's normal for a power bank, but a bad cell means rework at the bench.
- **Connection order:** check the BQ294700 datasheet.
