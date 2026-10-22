# Critique from A ("gasketed box") of B, C, D and E, plus self-review

The numbers are my own back-of-envelope checks. I use a beam model for plate bow between screws: δ = 5wL⁴/384EI. Values: Al E = 69 GPa; TPU 95A E ≈ 25 MPa (a typical filament value, so take it as order-of-magnitude).

---

## B: Flashlight tube

**Most serious flaw: B has the most seal joints of the five, and its "free" BLE window costs a fourth, bonded seal.**

The seal count is:
- two radial O-rings,
- an MS-polymer bond around the saddle window, about 270 mm of wet joint with a 24 h cure that can't be reworked,
- two USB-C seals,
- the vent.

So B ends up with 4 long seals against A's 1, which defeats the point of choosing radial O-rings to get rid of a face seal.

The window also cuts out most of the tube face that B itself calculates is too flexible: B's own number is a 0.8 mm bulge of a 2.2 mm PA12 flat under O-ring pressure, which is why it needs skirts. With the window, that face becomes a frame around the opening, and the same O-ring hoop load bears on it.

B's tolerance analysis (RSS ±0.18 mm against a ±0.19 mm squeeze band) also has no margin. It quietly relies on "print one test ring and adjust" for every print batch.

**Steal:** the electronics own the top cap, so USB-C seals are made and checked on the bench before any cell is near. **Also the MJF PA12 choice: B was right and I was wrong** (see self-review).

---

## C: Electrical-first, rigid core in a TPU boot

**Most serious flaw: the only long seal (an integral TPU bead clamped by 4 screws through a flat 2 mm plate) can't hold squeeze between the screws.**

- **Bead force.** A 1.6 mm half-round 95A bead at 25–30 % squeeze needs roughly 3–9 N/mm, about 0.75–2.2 kN around a ~250 mm path.
- **Plate bow.** A flat 2 mm plate (I ≈ 30 mm⁴ across about 45 mm) between corner screws 80 mm apart, loaded on both edges at even 3 N/mm, bows about 1.5 mm. The whole squeeze is about 0.45 mm.
- **Insert load.** Four heat-set inserts in PA12 would carry 200–550 N each.
- **Compression set.** TPU 92A sets 44 % at 70 °C ([Stratasys FDM TPU 92A](https://WWW.STRATASYS.COM/contentassets/a194ef2599e447b6bbc6f5402437c890/mds_fdm_tpu92a_0124a.pdf)), so whatever squeeze is left after one hot car is gone.

**Smaller error:** C says the cells generate "~0.5 W total at 7 A". With a 58E DCIR of about 20–25 mΩ, I²R is 49 × 0.022 ≈ 1.1 W per cell, about 4–5 W for the pack. That is about 8× higher. C's conclusion that the cells stay near ambient doesn't hold during a 100 W session.

**Steal:** the **rigid core**. Cells, carrier and PCB are one unit, so the drop stroke happens outside the electrical joints and the tails only absorb tolerance. Also **datum the cells and the PCB from the same end.** This beats A's choice (see self-review).

---

## D: Sealed for life (snap, then bond)

**Most serious flaw: the cure of 1K moisture-cure MS-polymer in a confined 4 mm-deep groove.**

- The groove is closed by a snapped-in aluminium flange on one side and PETG on the other. Moisture can only enter through a ~0.5 mm bond-line slit.
- D quotes a cure rate of 2–3 mm per 24 h, but that is for an open bead. Through a slit it could take weeks at the groove root.
- A 48 h leak test can pass on a skin-cured bead that is still paste behind it. The test proves nothing about the end state.

**Strain margin.** D's own strain figure (17–25 % shear against a ±20–25 % movement rating) means every sunny day uses up the full joint capability. That is a fatigue problem for a sealed-for-life pack.

**Flange length (unverified).** A 4 mm flange on 2 mm 5052 is at or below typical minimum flange rules of about 3t + R ≈ 6–8 mm. Check JLC's limit.

**Steal:** D's **quantified leak test**. A +100 mbar positive-pressure bubble dunk (water can't get in), decay used only as a gross check because of the temperature sensitivity D quantifies (about 3.4 mbar per K). Also **make the vent the designed burst point.**

---

## E: Rigid core, soft skin

**Most serious flaw: the heatsink seal is the same physics problem as C, but worse.**

- **Squeeze.** A 1.0 × 0.8 mm TPU bead at 30 % squeeze gives only **0.24 mm of squeeze**.
- **Plate bow.** It is clamped by 4 screws through a 1.5 mm plate with 3 mm returns, so I is about 15 mm⁴ per edge. Over an ~80 mm span, even 1 N/mm of bead load bows the plate about 0.5 mm, twice the squeeze.
- **Compression set.** The 44 % at 70 °C figure takes away a further ~0.1 mm.

E itself cites corner-only fastening as a documented field-leak cause, then uses 4 screws.

**Fit risk.** "Roll the boot on like a phone case" with a 1.8 mm, 100 %-infill 95A skin is unproven. Phone cases are about 1 mm thick and much softer. Expect the boot to tear at the port bores or not seat.

**Steal:** **p = T/R**: never trust a stretch fit on a flat face. Clamp flats, and stretch-seal only round bores. That one line is the clearest argument in the set.

---

## Self-review: what beats A, and what I change

### 1. I got MJF porosity wrong. I'm switching the tub to MJF PA12

Concept A cited the MDPI 2018 study as "MJF PA12 is porous and needs impregnation". Having now read it, the study says the opposite for normal walls:
- untreated MJF PA12 vessels at **≥0.7 mm wall held more than 0.4 MPa** with no measurable leak, in both build orientations;
- the valve body held 4.2 MPa for 1 h;
- only walls of 0.4–0.5 mm leaked.

([PMC6120015](https://pmc.ncbi.nlm.nih.gov/articles/PMC6120015/))

What changes:
- **The tub becomes MJF PA12**, 2.0 mm walls, from JLC.
- **USB-C bores.** MJF has no axial layer channels, so the bores become a real radial seal. The RTV moat is demoted to an optional backup.
- **Rim land.** It still needs work: MJF is around Ra 6 µm against roughly 1.6–3.2 µm wanted for a static face seal, and flatness is about ±0.3 %. **Lap the rim on 400-grit paper on glass (1 min).** This fixes both. The hard-stop gland already tolerates ±0.2 mm.
- **Drop and cold.** PA12 is also tougher than PETG in drops and in the cold.

### 2. Rigid core instead of floating cells (from C and E)

My own tail numbers were inconsistent. I specified 0.2 mm nickel with about 5 mm free length. At 0.5 mm of relative travel that is ε ≈ 3tδ/L² ≈ **1.2 %**, not the 0.35 % I wrote. That is plastic and fatigue-limited after a modest number of drops.

The fix:
- **Make the cradle MJF PA12 and screw the PCB to it,** so cells and board move together. The tails become C-style closed plated slots with no slide oversize, soldered both sides.
- **The core floats on the two TPU end pads.**
- **The USB-C receptacles slide axially in their bores.** The silicone ring is 1 mm long. The MJF bore becomes 3.5 mm long, so the ring stays sealed over ±1.2 mm of core travel.
- **Travel limit.** TPU-faced PCB edge stops cap the travel at 1.0 mm.
- **Assembly.** The bottom TPU pad goes in last as the wedge that takes up the 2.5 mm port-engagement slide.
- **What it removes.** The lid lug is no longer needed. Soldering moves to the bench, and the core can be bench-tested before it goes into the tub (B's and C's sequencing).

### 3. Leak test

I'm adopting D's +100 mbar bubble dunk, done through the vent hole before the vent goes on.

### 4. What I defend

- **One gasketed joint.** A bought silicone O-ring in a CNC groove with a hard stop.
- **Six screws threaded into the aluminium lid,** with the plastic in compression only.

C and E show why: their 4-screw, thin-plate, printed-bead seals bow about 2–10× more than their whole squeeze. B and D replace the face seal with two O-rings plus a bond, or with bonds that can't be checked. A's lid-joint maths is the only one in the set with margin: 25 % squeeze, ±0.2 mm tolerance, bow under 0.02 mm.

### 5. What I concede

**BLE is A's real weak spot.** B, D and E all leave plastic over the antenna. A's lid covers the whole open face, and a printed roof over the antenna is geometrically impossible with the port-engaging slide. I checked the tilt-in clearance: it needs much more than the 2.5 mm of length slack.

A roof at the bottom end doesn't work either: the slide moves the board away from it. So the mitigation stays a 3 mm lid relief pocket plus a range test. Any fixed plastic roof over the antenna would also block lowering the core into the tub, so **A has no clean fallback** if the range test fails. That is a genuine point against A's architecture, and in its favour for B, D and E.
