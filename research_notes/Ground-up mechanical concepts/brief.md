# Ground-up mechanical concept — shared brief

This is a THOUGHT EXPERIMENT: a clean-sheet mechanical design for a hobby trail battery bank. You may read the existing design for facts (repo `C:\Users\Logan\Documents\BatteryBank`, `mechanical/monolith_shell.py`, `README.md`, `Production/README.md`, `reports/`), but do NOT copy it by default and do NOT edit any repo file. Write only to your output file named below.

## Fixed facts
- 4 × EVE INR21700-58E cylindrical cells (21.5 mm Ø × 70.8 mm, ~70 g each), wired **4S1P** (14.4 V nominal, 82 Wh). The BMS needs PACK+, PACK−, and three mid-tap sense lines (CELL1–3); a Kelvin pair on the stack ends is nice to have. Pack current up to ~7 A (100 W).
- One PCB, 1.6 mm FR4, ~43 × 74 mm, runs **lengthwise parallel to the cells** along one side of the cell group. Two USB-C ports (IP68-rated board-mount receptacles, TYPE-C 16PCB1.6 IP68, LCSC C55629729) stick out of the **top end**. A BLE module sits on one board edge and needs a non-metal window for its antenna.
- A **metal heatsink** (aluminium) presses against the PCB's hot parts (buck-boost inductors/FETs, up to ~5 W of loss at 100 W) and **is one of the pack's outside walls**.
- Cell layout is the designer's choice (2×2 is the obvious one; 1×4 flat or other are allowed if justified).

## Requirements, in priority order
1. **Survive the trail:** mild vibration; 1 m drops onto rock/concrete on any face, edge or corner. Cylindrical cells are most vulnerable end-on (the CID / + cap) and to can denting.
2. **Watertight, target IP67** (1 m immersion, 30 min). Explain where every seal is, including the USB-C ports, the heatsink-to-body joint, the BLE window, and pressure/thermal breathing.
3. **Simple assembly** matters MORE than serviceability. Serviceability is low priority — glued/welded/non-opening is acceptable. Count assembly steps and fixtures.
4. **How the cells connect to the PCB**, both power (7 A) and the sense taps. This is a known hard problem — give it real attention. Nickel strip, spot welding, soldering, sheet-metal busbars, spring contacts, etc. are all fair game; say what tools it needs.
5. **Limit material types.** Allowed: anything 3D-printable (FDM at home: PLA/PETG/ASA/TPU; or JLC's print service: MJF PA12, SLA resins, TPU, etc.) and **metal** (JLC custom sheet metal — laser cut/bent aluminium or steel with silkscreen/laser-marked labels; nickel strip; CNC). **Not allowed:** hand-cut foam, mica, fish paper, or any sheet stock the builder must cut by hand. Small off-the-shelf hardware (screws, heat-set inserts, O-rings, a breather vent, thermal paste/pad, sealant, wire) is OK if you justify and list it — fewer is better, and prefer a printed TPU part where it can do the job.
6. Low cost, light weight, compact (hobby project, ultralight backpacking product).

## What to deliver
Research where it helps (web search for real products, IP67 enclosure design rules, printed-TPU gasket data, sealing of printed parts, drop-test practice for 21700 packs, etc.) — cite sources briefly. Then write your concept to your output file (markdown, ~1200–2000 words), with these sections:
1. **Concept in one paragraph** + an ASCII sketch (section and/or exploded view).
2. **Parts list**: every part, its material/process, rough mass, and whether bought or made.
3. **Assembly sequence**: numbered steps, tools/fixtures, and the count.
4. **Cell-to-PCB connection**: power and sense, how it's made, how it survives vibration/drop.
5. **Sealing to IP67**: each leak path and its seal; how printed-part porosity is handled; pressure equalisation.
6. **Drop & vibration**: load paths for end-on, side, and corner hits.
7. **Thermal**: heat path PCB → heatsink → air; keeping cell temp down.
8. **Estimates**: outer dimensions, total mass, part count, material types count.
9. **Risks / weak points**, honestly, and how you'd test them.
10. **Best ideas others could borrow** from this concept even if it isn't chosen.

Return to me (your final message) a ~250-word summary: the concept, its 3 strongest points, its 3 weakest points, and estimated size/mass/part count/assembly-step count.
