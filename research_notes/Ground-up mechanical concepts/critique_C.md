# Critique C: cross-examination by the electrical-first concept

Shared ground first. Four of the five concepts (A, B, D, E, and mine) converged on the same joint: spot-welded pure nickel, with tails through plated PCB slots and soldered there. The real differences are three:
1. Whether cells and PCB move together in a drop.
2. What makes the long seal.
3. How the USB bores seal.

My attacks below are aimed at those three.

## A: Gasketed box (PETG tub, CNC lid, O-ring)

**Most serious flaw: the tails carry the drop motion, and the strain is understated.**
- A fixes the PCB to the shell (ledges, stops, lid lug) but lets the cells "float on about 1 mm of TPU", with 3 mm gyroid end pads.
- So in an end drop, the cells move relative to the board by whatever the pads compress, and the tails must follow.
- A estimates 0.35 % strain for 0.5 mm of travel on 5 mm of free tail. But a tail welded at one end and soldered flat at the other is a fixed-guided beam, where ε = 3tδ/L².
  - At δ = 0.5 mm: 3 × 0.2 × 0.5 / 25 = **1.2 %**.
  - At δ = 1–2 mm, which is plausible with gyroid pads at ~330 g: **2.4–5 %**.
- A rough Coffin–Manson estimate for annealed Ni (εf′ ≈ 0.5, c ≈ −0.6) gives about 100 cycles to cracking at a 4 % range. That is fine for "tens of drops", but it is not the "negligible" A claims.
- The bigger issue is the joint itself: the tail is folded flat and lap-soldered, so each drop loads the fillet in **peel**, the worst mode for solder.

**Second issue: the RTV moat at the USB ports needs neutral-cure silicone to adhere to PETG.** Silicone bonds poorly to PETG without primer, and D says so too. As a backup it is weaker than it looks.

**What I'd steal:**
- **A silicone O-ring instead of a printed TPU bead.** A's sourced data settles it: FDM TPU 92A has 21 % compression set at 23 °C and **44 % at 70 °C** (Stratasys datasheet), while silicone is 10–30 %. A ~25 % squeeze on a printed bead loses about half its interference after a hot summer in a car.
- **The bending calculation for corner-only screws.** A shows a 4-corner lid bowing 0.07–0.35 mm mid-span under ~400 N of O-ring load.
- **The correction to my cell heat figure.** At 7 A, 4 cells × 49 A² × 15–25 mΩ is **3–5 W**, not the ~0.5 W I wrote.

## B: Flashlight tube (radial O-ring end caps)

**Most serious flaw: the radial-squeeze tolerance stack uses a tolerance JLC doesn't quote.**
- B takes MJF tolerance as ±0.3 % (±0.165 mm on 55 mm), which gives a radial ±0.085 mm.
- JLC3DP's capability page lists **±0.3 mm within 100 mm** for PA12 ([JLC3DP](https://jlc3dp.com/capabilities/3d-printing-service)). Its own blog says holes print undersized ([JLC3DP blog](https://jlc3dp.com/blog/mjf-tolerances-and-dimensional-accuracy)).
- Redoing B's RSS with ±0.15 mm per printed part (tube bore and cap groove), ±0.08 mm cord and ±0.1 mm eccentricity gives **±0.25 mm**.
- That puts the squeeze at 0.31–0.81 mm, or **12–32 %**. The low end is below the 15 % floor.
- "Print a test ring and adjust one CAD offset" only removes the systematic part of the error. It does nothing for batch-to-batch scatter or for warp on a thin 90 mm rounded-rectangle tube. The flat walls also bulge, which B itself calculates at 0.8 mm, and the skirt is what has to stop it.
- Secondary issue: the heatsink saddle is held on **only** by an MS-polymer bead, with no mechanical retention. A corner hit on a saddle return loads that bond in peel.

**What I'd steal:**
- **"Print sealing bores so layer lines run parallel to the seal line."** This exposes a flaw in my own concept (below).
- **The proud cap as the impact face,** so drop loads bypass the fasteners.

## D: Sealed for life (snaps + MS-polymer)

**Most serious flaw: the PETG snaps carry a constant load at heatsink temperature, and the sealant is already at its movement limit.**
- The 1.5 mm gap pad is compressed to 1.0 mm (33 %). Over roughly 400 mm² of parts, a soft pad pushes back with about 70–140 kPa, which is **~30–55 N** acting outward on the heatsink at all times.
- PETG barbs carry that load, right next to a plate that D lets reach 55 °C before derating. PETG's HDT at 0.45 MPa is only about 70 °C, so the barbs will creep.
- As they relax, the load moves into the MS-polymer in tension and peel.
- D's own CTE numbers already put the bead at 17–25 % shear strain against a ±20–25 % movement rating. The sealant has no margin left to also carry structural load.
- Smaller issue: 1K MS-polymer cures from its exposed edge (~2–3 mm per 24 h). In a 4 mm deep tongue-and-groove joint whose inner side faces dry, sealed air, the 48 h cure is optimistic. A leak test at 48 h may pass on uncured sealant that later shrinks.
- The "cells and PCB move together because they share a TPU cradle" claim is weak. A 95A TPU cradle lets the 280 g of cells move relative to a PCB held in a groove of the same soft part.

**What I'd steal:**
- **Return flanges on the heatsink** (D's C-channel, also used by B and E) to stiffen the plate between screws. This is free in JLC sheet metal.
- **A positive-pressure bubble dunk,** so water can't get in during the test.
- **Make the vent the designed burst point,** pointing away from the hand.

## E: Rigid core + TPU boot (my closest twin)

**Most serious flaw: the drop load path loads the tails.**
- E routes end-on cell inertia into the boot's 4 mm gyroid ("the core's end rims do not carry cell inertia; the boot ends do").
- The cells are held in the PA12 core only by crush ribs with 0.2 mm of interference. The friction from that is on the order of tens of newtons per cell, against E's own ~170 N impact per cell.
- So in an end drop, the cells slide in their bores and compress the gyroid by up to its stroke. Meanwhile the core and PCB, which have far less mass behind them, decelerate differently.
- The differential motion is therefore mm-scale, against a 0.5 mm Z-loop budget, and every cycle can ratchet the cells.
- My concept differs here on purpose: the cells bear on the carrier's own end frames, and the posts transfer the load. That makes **cells + carrier + PCB one rigid body**, and the tails see only cell-length tolerance.

**Second issue: the thermal estimate contradicts the design.**
- E's +21 K figure spreads 5 W over the whole 190 cm² pack surface.
- But the only way heat reaches the faces away from the plate is *through the cells*. E's own PA12 deck is there to stop exactly that.
- Either the cells are the heat spreader, and get hot, or the plate alone does it (≈0.04–0.05 W/K, as A, D and I compute).

**What I'd steal:**
- **p = T/R:** a stretch fit seals round bores but never a flat. This validates the clamped rim.
- **Black, preferably polyether TPU,** for UV and hydrolysis.
- **TPU screw collars** as built-in grommets.

## Defend or fix my own concept

**What I keep:**
- **The rigid-core rule.** The cells' axial load goes through carrier end-frame posts, so cells and PCB decelerate together. A, D and E each leave the tails exposed to the cushion stroke in some form; this is the main reason to choose C's internals.
- **Cells and PCB located from the same end.** No other concept addresses cell-length tolerance and carrier CTE explicitly.
- **Power tongues at the end opposite the USB.** D and E put PACK± at the USB end, next to the power stage. Mine keeps the 10 mm slots out of the end where two USB-C receptacles already crowd a 43 mm edge. This choice should follow the real PCB's power-stage placement, so it is a call to make, not a principle.

**What the others beat, and what I changed (concept_C.md updated):**
1. **Seal:** the integral printed TPU bead is replaced by a **bought 1.5 mm silicone O-ring in a groove printed in the boot rim**. PA12 hard-stop bosses on the carrier flange poke through the rim to set the squeeze at ~25 %. Credit to A's compression-set data. This adds 1 part.
2. **Thermal:** I corrected the cell self-heating to **3–5 W at 7 A** and added a cell-side derate. Credit to A.
3. **Plate stiffness (to add):** 3 mm return flanges on the JLC heatsink, or 6 screws. A's bowing calculation shows that a 2 mm flat plate on 4 corner screws can bow by about as much as the whole 0.37 mm squeeze. Credit to A, D and E.
4. **USB bores (new weak point I hadn't seen):**
   - My boot prints open-face up, which makes the port bores horizontal. Every layer line then runs *along* the bore, a potential leak path under the receptacle ring (point from A and B).
   - TPU 95A conforms better than PETG, but I won't rely on it. Add a 1 mm counterbore around each port filled with MS-polymer as a second barrier (D's detail), and test it with the pressurised bubble dunk.
   - Printing the boot upright instead would fix the bores but put layer lines across the O-ring groove, which is worse.

**Revised position:** C's *internals* (rigid core, end-frame load path, datum rule, tongue-as-tap) are the strongest electrical and drop design on the table. E's and my boot are the same enclosure idea, and with A's O-ring and stiffened plate, that boot becomes credible for IP67. My recommendation is **C's core inside E/C's boot**, sealed with A's O-ring and hard-stop principle.
