# Critique B: the flashlight concept cross-examines A, C, D, E, then defends itself

## A: Gasketed box (PETG tub + CNC aluminium lid with an O-ring face seal)

**Most serious flaw: the lid's clamp force rests on PETG that will creep.**
A's own figure for the silicone O-ring reaction is about 400 N (1.5 N/mm × 255 mm). The six screws must keep at least ~67 N each just to hold the lid on its hard stop. They do this by bearing on PETG lobes under M2.5 pan heads. A pan head's bearing annulus (Ø4.5 head, Ø2.7 hole) is only about 10 mm².
- At a modest 200 N assembly preload, that is about **20 MPa on PETG**.
- PETG's heat-deflection temperature is about 70 °C at 0.45 MPa. A black anodised lid in the sun, or the pack running at 100 W, takes the lobes to 55–60 °C.
- At that stress and temperature, PETG creeps until the preload falls toward the O-ring reaction.
- Once a screw falls below ~67 N, the lid lifts off its stop, and the "squeeze set by groove depth" claim no longer holds.

A lists this as risk 2 but treats it as a torque issue. It is really a **seal-geometry issue**: the hard stop only works while the preload exceeds the O-ring reaction.

Fixes:
- Put a washer under each head so bearing stress stays under ~5 MPa, or
- Move the screws into metal on both sides.

**Second, citation check: MJF PA12.** A rejects MJF PA12 as "porous, needs vacuum impregnation", citing MDPI 2018 (PMC6120015). That paper's title is *"MJF PA12 manufacturing parameters for watertightness"*. It derives orientation and wall-thickness rules for **watertight pressurised parts**, validated on a printed ball valve to ISO 9393. So the citation says MJF can be watertight with the right walls and orientation, not that it always needs impregnation. A over-reads it, and so does E's forum source.

**What I'd steal:** put the precise feature in the metal part (A puts the groove in CNC aluminium), so the printed part only has to provide a plain land. A's specific trick is a land made of a single Z layer, which no layer line crosses.

## C: Electrical-first (rigid core, nickel tongues, TPU boot)

**Most serious flaw: the heat budget is off by about 8×.**
C says the cells stay "near ambient + I²R (~0.5 W total at 7 A)". The 58E's DCIR is about 20–25 mΩ, so:
- One cell: 7² × 0.022 ≈ 1.1 W.
- Four cells: **~4.3 W**. A gives 3–5 W; I gave ~4 W.

At 100 W the cells add as much heat as the converter. C's "cells cool, heatsink is the only problem" story is therefore wrong. A thermal break between the cells and the heatsink also stops the heatsink from helping the cells.

**Second flaw: the only long seal is a printed TPU 95A bead clamped by 4 screws.**
- There is no hard stop, so squeeze depends on torque.
- FDM TPU 92A compression set is **44 % at 70 °C** (Stratasys data cited by A).
- A's plate-bow numbers apply here too: 0.07–0.35 mm mid-span with four corner screws, against a squeeze of ~0.45 mm on the 1.6 mm bead.

After a summer in a car, the bead could be at zero squeeze mid-span.

**What I'd steal:** **datum the cells and the PCB from the same end and make the core rigid.** Then the tongues only absorb cell-length tolerance, not drop motion. This is better than my stress-loop approach (see "My own concept" below).

## D: Sealed for life (snap first, then MS-polymer)

**Checked, and the numbers hold:** Δα of 45 ppm/K × 70 K × 40 mm gives 0.126 mm, which over a 0.5 mm bond line is 25 % shear. That is correct, and as D says, it is **at the sealant's movement limit with zero margin**. Every thermal cycle works the main seal at its rated maximum.

**Most serious flaw: D cannot be reworked, and the next build is the first build.**
- Project memory says the dev board was skipped, so P0 *is* the first build.
- A sealed-for-life P0 means any board fix (even a bodge wire) is a blade-and-reprint job, with a 48 h cure before each retest.

**Burst-path claim, checked:** choked airflow through the Ø6 port at 1 bar gauge is about 0.0404·A·P₀/√T ≈ 0.013 kg/s, roughly 10 L/s. That is in the range of a 21700 vent event, so "the vent label is the burst point" is plausible. It still needs D's proposed hose test, because the label's blow-off pressure is unknown.

**What I'd steal:** **snap first, then seal.** My bonded heatsink saddle currently needs tape and a 24 h clamp. Printed barbs that catch its returns would hold it during cure and carry peel loads afterwards.

## E: Rigid core + TPU boot

**Most serious flaw: the heatsink seal is a printed bead with almost no compression range.**
- A 1.0 × 0.8 mm bead at 30 % squeeze is **0.24 mm** of compression. That is about one 0.2 mm FDM layer.
- Bead height can only change in layer steps (±0.1 mm). The start/stop seam makes a local high or low spot. The bead sits on soft TPU over a PA12 deck, with four screws spaced along 84 mm.
- So the as-built squeeze plausibly spans **~10–45 %** before compression set.
- After set (44 % at 70 °C), the low end goes to zero.

E's "screw stops, not bead stress" protects against over-squeeze, not under-squeeze.

**Second: the thermal number is optimistic.** E's +21 K uses the whole 190 cm² pack surface at 10 W/m²K. But the aluminium plate is surrounded by TPU, so heat from a 5 W hot spot cannot spread through a TPU skin to the far faces. The plate (~42 cm²) runs much hotter than the pack average. I make the same mistake if I quote only the average, so I quote both.

**What I'd steal:** **p = T/R.** A stretched skin presses with zero force on a flat. This is also a warning for my design. My O-ring, stretched around a rounded-rectangle plug, seats only by squeeze on the four flats, not by tension. So the groove must hold it during insertion, and the 2.7 % stretch only helps at the corners.

## My own concept: what the others beat, and what I'd change

1. **The cells float but the PCB is fixed, so the tails take the drop motion. C and D beat me here.**
   My PCB is screwed to the top cap, while the cells ride a 2 mm TPU cushion. Every end drop flexes the tails by 0.5–1 mm. C and D make cells and PCB move together.
   **Change:**
   - Make the yokes rigid PA12, clamped to the PCB, so the cassette is one rigid body tied to the top cap.
   - Move all drop stroke **outside** the caps, onto press-on TPU end bumpers (A/E style). These also cover the cap screws and the corners.
   - The bottom cap then only applies a small axial preload through a thin TPU pad.
   - Cost: two parts and about 16 g. Gain: the tails see only tolerance, not drops.

2. **My MJF tube is not proven watertight. Neither are the other printed shells.**
   The MDPI paper shows that MJF can be watertight *with* the right walls and orientation, so my claim stands only after a coupon test.
   **Change:** make the first article a 30 mm tube stub with both lands, in MJF *and* in upright FDM PETG. Dunk both at +100 mbar before committing. If MJF weeps, use PETG upright and sand the land.

3. **Wet-bonded saddle with tape and a 24 h clamp. D's version is better.**
   **Change:** add D's printed barbs over the saddle returns, so it is snap-held during cure. I keep a sealant bond rather than a gasket, because a 1–1.5 mm elastic bead absorbs print warp and both A and E show printed face seals are fragile.

4. **Where I still think B wins:**
   - The **radial cap seal** is the only seal in the five concepts whose squeeze is set by XY print dimensions and is **independent of screw preload and plastic creep**. A, C and E all have a creep or bow failure mode on their main seal.
   - The **cap skirt** fixes my own bulge problem (~0.8 mm computed) by geometry.
   - **The top cap belongs to the cassette.** Both USB seals are verified on the bench before any cell is near, which no other concept does.

5. **Thermal: no concept wins on paper.** Every concept, mine included, needs firmware derating above about 40–60 W sustained. My three-sided saddle gives about 2× A/D's plate area, the most of any concept except E's rejected E2.

**Revised position.** B with two changes: a rigid cassette with external TPU bumpers (taken from C and E), and a snap-held bonded saddle (taken from D). The tube material is decided by a stub dunk test. Mass rises to ~425 g and parts to 26 pieces; steps stay at 13.
