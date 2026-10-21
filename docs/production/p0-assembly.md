# P0 assembly: framed cell module, tray, board

How a Monolith P0 goes together, from the mechanical model in `mechanical/` (side tray). The six steps are shown in `mechanical/monolith_side_assembly.png`.

**Status:** a plan, updated 2026-10-21 for the TPU cell frame and the spring-contact sense strip. Nothing has been built yet, so expect it to change at the first fit print.

![Assembly steps](../../mechanical/monolith_side_assembly.png)

## The idea

The tray opens on one side only, and the board has to make two moves:
1. It drops in through the open side.
2. It slides 2.5 mm toward the top, so the USB-C faces pass into the top wall.

The cells can't make that slide. So the cell module is built and tested on the bench, inside a printed TPU frame, and goes in first. The board then joins it in two ways:
- **Power (PACK− and PACK+):** two 18 AWG leads, threaded through plated holes and soldered on F.Cu. They're the only joints made inside the tray.
- **Sense (CELL1, CELL2, CELL3, plus the gauge's Kelvin taps 1N and 4P):** wired on the bench to a small ENIG sense strip on the frame. Five gold spring contacts on the board's B.Cu land on it as the board drops in, and wipe 2.5 mm along its pads as the board slides up. No connector to tear, and no soldering.

| Connection | From | How it reaches the board | Board feature (KiCad, mm) |
|---|---|---|---|
| PACK− | tab on the C1 bottom | 18 AWG lead, looped for the slide | plated hole (86.0, 134.6), 1.6 mm drill, 3.4 mm pad |
| PACK+ | tab on the C4 bottom | 18 AWG lead, looped for the slide | plated hole (114.0, 134.6) |
| 1N | PACK− tab | 28 AWG lead to the sense strip | spring contact (96, 123.5) |
| CELL1 | C1+ / C2− strip, top | 28 AWG lead down the groove | spring contact (98, 123.5) |
| CELL2 | C2+ / C3− strip, bottom | 28 AWG lead between the spring rings | spring contact (100, 123.5) |
| CELL3 | C3+ / C4− strip, top | 28 AWG lead down the groove | spring contact (102, 123.5) |
| 4P | PACK+ tab | 28 AWG lead to the sense strip | spring contact (104, 123.5) |

The positions come from `SB_LEAD_HOLES`, `SB_CONTACTS` and `SB_CONTACT_Z` in `mechanical/monolith_shell.py`. They're on the `TAB_PADS` and `BCU_SENSE_CONTACTS` layers of `monolith_side_pcb.dxf`.

The contacts work at about 2.8 mm, from B.Cu to the strip pads. Each pad is 6 mm long to cover the slide plus tolerance.

**Board changes needed:**
- PACK± become plated holes for 18 AWG.
- Add five SMT spring contacts on B.Cu: gold, about 2.4–3.2 mm free height, working at 2.8 mm. The part is still to be chosen.
- The gauge's VC0 / VC4 Kelvin sense comes from the 1N / 4P contacts, not from the PACK pads.

## Materials and tools

- **Cells:** 4 × EVE INR21700-58E, matched to within 10 mV and checked for internal resistance.
- **Nickel:** 0.15 × 7 mm, for the three series strips and the two PACK tabs. You'll need a spot welder.
- **Wire:**
    - 18 AWG silicone, red and black, about 30 mm each.
    - 28 AWG silicone in five colours.
- **Sense strip:** 0.6 mm ENIG PCB, about 9.2 × 9 mm, with five pads (JLCPCB).
- **Printed parts:**
    - the tray (MJF PA12);
    - the TPU cell frame: bottom holder and top frame;
    - the TPU caps and the TPU board shim.
- **Sheet stock:**
    - 0.2 mm mica, for the cross;
    - 0.2 mm fish paper: liner, the sheet on the board side, four + end rings.
    - 1 mm EVA is now used only for the two USB-C hold-downs.
- **Cover and fixings:** the anodized cover and 2 × M2 thread-forming screws with a nylon patch.
- **Other:**
    - a 0.5 mm gap pad;
    - an ePTFE vent patch;
    - neutral-cure silicone;
    - conformal coat, applied to the board beforehand.
- **Tools:** soldering iron, a multimeter, and the gauge and programming setup (EV2400 on the SMBus pogo pads, XDS110 with Tag-Connect).

## Steps

### 1. Cell module in its frame, on the bench
1. **Check the cells.** Measure each cell's voltage and internal resistance, and reject outliers.
2. **Make the PACK leads first.** Solder each 18 AWG lead to the end of its nickel tab before the tab is welded to a cell, so no soldering heat reaches a can.
3. **Weld the module:**
    - Mica cross: the y = 0 sheet stops 17 mm out, leaving room for the sense web.
    - The series strips: C1+→C2− top, C2+→C3− bottom, C3+→C4− top.
    - The PACK− tab on the C1 bottom and the PACK+ tab on the C4 bottom.
    - The cell order and + ends are `SB_CELLS` in the model.
4. **Insulation:** fish-paper rings on the four + ends, and the liner round the −x and ±y faces.
5. **Frame:**
    - Slide the module into the TPU top frame: plate on the top ends, bars down the board side, web in the groove between C1 and C4.
    - Press the sense strip into the web pocket, pads facing out.
6. **Sense leads:** solder the five 28 AWG leads to the strip's back pads, then to their nickel.
    - CELL1 and CELL3 run in the top-plate slots and down the groove.
    - CELL2, 1N and 4P go under the cells: they run in the channel between the spring rings, then up the groove.
7. **Check on the bench:** every pad on the strip reads the right voltage against PACK−, and no can shorts to any lead.

### 2. Prepare the tray
Drop the TPU bottom holder into the floor zone, spring rings up. The rings are open over the C2 and C4 + caps. Check that the crush ribs are clean and the port holes are reamed to size.

### 3. Framed module in
1. Slide the framed module in through the open side. The crush ribs squeeze the liner, and the spring rings take up the length.
2. Lay the fish-paper sheet on the cells' board-side face. Its window goes around the sense strip.
3. Lead the two PACK leads down into the gap below the board zone, out through the open side.

### 4. Board in
1. Hold the board 2.5 mm below its final position and thread the two PACK leads through their holes from the B.Cu side.
2. Lower the board onto the frame bars. The spring contacts land on the lower half of the strip pads.
3. **Slide it up 2.5 mm** until the USB-C faces sit in the top wall and the board's top edge bears on the stops. The contacts wipe up the pads, and the PACK leads take the slide in their loops.

### 5. Shim, solder, program, test
1. Fit the TPU shim under the board's bottom edge.
2. **Solder the two PACK leads on F.Cu,** PACK− first, then PACK+, and trim them.
    - The BQ40Z50-R2 datasheet (SLUSCS4C §9.2.2.1.3) gives no connection order, only the Kelvin rule for 1N and 4P.
    - The BQ294700 datasheet hasn't been checked yet. Check it before the first build.
3. **Check the five sense voltages** through the gauge, or at test points.
4. **Program and set up:**
    - Flash the CC2340.
    - Load the BQ40Z50 golden file and run gauge training on the SMBus pogo pads (`p0-bringup-and-training.md`).
    - Load the BQ25756 and TPS25751 configuration.
5. **Function test while it's open:** charge and discharge on each port, the gauge readings, and BLE.

### 6. Close
1. Gap pad on the tall parts, kept clear of the vent.
2. ePTFE vent patch inside the cover.
3. Silicone bead along the cover joint.
4. USB-C hold-downs (2 × 1 mm EVA).
5. **Cover:** tuck it under the top lip, then drive the 2 M2 screws. The four cover standoffs sit 0.2 mm under it.
6. Snap the TPU caps on.

## Open items
- **Board:** PACK± as 18 AWG holes, five B.Cu spring contacts (choose the part), the frame-bar keep-outs, and Kelvin sense from the contacts.
- **Sense strip:** draw it (0.6 mm, ENIG, five pads 1.4 × 6 mm at 2 mm pitch, plus back-side wire pads).
- **Fit:**
    - Contact force, and how much the TPU bars creep. The contacts' working height depends on the bars.
    - Lead lengths, and threading the PACK leads.
- **Connection order:** check the BQ294700 datasheet.
