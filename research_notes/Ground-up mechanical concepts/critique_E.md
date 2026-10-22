# Critique E: cross-examination from the "rigid core + TPU boot" author

## A: Gasketed box (PETG tub, CNC lid, O-ring)

**Most serious flaw: the O-ring squeeze depends on a flat printed land, and an FDM PETG rim warps.** A sets squeeze with a hard stop (lid bottoms on the rim). Its own tolerance claim is that ±0.2 mm on the land still gives 15–35 % squeeze. But B quotes 0.1–0.4 mm of FDM flange warp on a part this size, and PETG on an 82 mm open-top tub does warp and curl at the rim corners.

At 0.4 mm of low spot, a 2.0 mm cord designed for 0.5 mm squeeze is left at about 0.1 mm (5 %), which is below every face-seal band A cites (20–30 %). The hard stop makes this worse: the lid bottoms on the *high* spots, so the screws cannot pull a low spot closed. The six screws do pull the compliant lobes up, but the lobes sit outboard of the seal, not under the low spots between them.

Ironing fixes surface texture, not warp. The land should be checked with feeler gauges on a printed tub before the CNC lid is ordered. A softer, thicker cord (2.5 mm) or a printed TPU shim to level the land would buy margin.

A secondary issue under priority #1 (drops): FDM PETG has its weakest direction across layers. A tub printed open face up has every wall's layers stacked perpendicular to the lid, so an edge drop on a long side bends the wall across those layers. The end bumpers only wrap the corners.

**Idea I'd steal:** A's verdict on printed TPU gaskets, with its data. Stratasys' FDM TPU 92A sheet gives 44 % compression set at 70 °C (21 % at 23 °C), against 10–30 % for silicone. That number hits my concept directly (see below).

## B: Flashlight tube with radial O-ring end caps

**Most serious flaw 1: the claim that MJF PA12 at ≥2.2 mm walls needs no sealing is unverified, and the sources I found and A cites point the other way.** MJF porosity is the known weak point for fluid tightness (MDPI 2018 / PMC6120015). Xometry's forum recommends vacuum impregnation, and says penetration varies. B's own production choice is therefore the porous one, while its P0 FDM fallback is the one with sealing guidance. The tube must be leak-coupon-tested, or impregnated.

**Most serious flaw 2: the O-ring bend radius at the corners.** B puts r6 corners on the *bore*, but the O-ring sits in the cap *groove*, whose bottom is about 2 mm further in, so roughly r4. Parker's minimum is 3× the cord section, which is 7.5 mm for a 2.5 mm cord (6× preferred, per the Hackaday summary of the O-Ring Handbook). r4 is about half the minimum: the cord will flatten and twist at all four corners, which is exactly where radial seals leak.

Stretch is also a problem. A 55 mm ID ring has a 173 mm circumference. Laid into a rounded-rectangle groove about 46 × 56 mm with r4 corners, the perimeter is about 197 mm, a stretch of about 14 %. Parker suggests up to about 5 % for static seals. At 14 % the section thins by roughly 7 %, which eats about 0.17 mm of the 0.56 mm nominal squeeze. That is nearly the whole ±0.18 RSS band B budgeted.

The fix is a larger bore radius, which makes the pack bigger, or a printed/moulded rectangular gasket. That lands back on the compression-set problem.

**Ideas I'd steal:**
- **Print sealing bores so layer lines run parallel to the seal line.** My boot's USB bores currently violate this (see below).
- **The top cap belongs to the electronics,** so the USB seal is compressed and checked on the bench before cells are near.

## C: Electrical-first (rigid PA12 carrier, nickel tongues, TPU boot)

C reached nearly the same enclosure as mine independently, so the critique cuts both ways.

**Most serious flaw: "the 4 screws pass outboard of the bead, so their holes are outside the wet line" is wrong for a through-clamped rim.** The screw path is heatsink hole → boot rim hole → **carrier flange**, and the carrier is *inside* the boot. Water entering at the screw head runs down the shank, bypasses the bead (which only seals the rim's top face to the plate), and arrives at the rim underside and the PA12 flange.

The joint then depends on the PA12 flange around a heat-set insert being watertight. That is an MJF part with a pressed brass insert and a melt zone, which is precisely the porous path C said was "inside the seal, so porosity doesn't matter." I caught the same trap while designing E and solved it with TPU collars that seal under each screw head. C needs either those collars, a second bead on the rim underside inboard of the screws, or blind fasteners.

Two smaller points:
- C's 0.15 mm Ni with a 10 mm × 0.15 mm power tongue: its own figures give about 0.25 W in the nickel. That is OK, but 0.2 mm is better if the welder can do it.
- The tilt-in-through-bores risk is shared with E.

**Ideas I'd steal:**
- **Datum the cells and the PCB from the same end and let the plastic float.** The CTE argument (steel ≈ FR4 ≈ 12–14 ppm/K vs PA12 ≈ 100) is sound and costs nothing. In E, the axial preload from the boot ends should push the cells toward the PCB's fixed end.
- **The vent hole as the pressure-test port, vent applied last on the outside face.** C notes adhesive bonds well to Al and poorly to TPU.

## D: Sealed for life (PETG tub, snap + MS-polymer bonds)

**Most serious flaw: the bonded joint runs at its strain limit by D's own numbers, at the temperature where the sealant is weakest.** D calculates 17–25 % shear strain in the MS line against a ±20–25 % movement rating, i.e. zero margin. The worst case is −20 °C: PETG (68 ppm/K) shrinks about 3× more than Al, and MS polymers stiffen and lose elongation when cold, while movement ratings are quoted at room temperature.

Adhesion of MS polymer to PETG is also untested; D's own source only says surface prep matters. Every IP67 seam in D, including cap to tub, is this joint. There is no fallback except cutting it open, and a 48 h cure is needed before even the first leak test. It must pass cold-cycled lap-shear coupons before anything else is built.

**Idea I'd steal:** **a positive-pressure bubble dunk.** With the inside at +100 mbar, water cannot get in during the test, and each leak shows where it is. My vacuum-jar test is worse: on releasing the vacuum, any leak *sucks water in*. Also D's INFICON figures: a 100 mbar test, and a seal-damage threshold of 100–200 mbar.

## Where the others beat my concept, and what I change

1. **Printed TPU bead compression set (from A).** With 44 % set at 70 °C, my 0.8 mm bead at 30 % squeeze (0.24 mm) keeps only about 0.13 mm after a hot-car soak. That is thin against 1.5 mm plate bowing between 4 screws. **Change:** the boot rim gets a groove for a **bought 1.5 mm silicone O-ring cord** (or a moulded rectangular ring). The plate's screw stops set its squeeze. The printed bead remains the P0 / IP54 option. This adds 1 bought part and keeps the boot as the envelope.

2. **USB bore layer lines (from B and A).** My boot prints window-up. That keeps the rim sealing face a clean top surface, but it puts the USB bores horizontal, with layer lines running along the bore axis: leak channels under the receptacle ring's ~0.1 mm squeeze. Printing the other way would push the problem onto the rim seal instead. **Change:** keep window-up, and add a 0.8 mm moat around each port on the boot's outer face, filled with MS polymer (bonds primerless to most plastics; TPU adhesion to be coupon-tested). The ring is the dam and the moat is the seal (A's arrangement).

3. **Thermal: I was optimistic.** I spread 5 W over the whole 190 cm² pack (0.19 W/K, +21 K). But my heat path is plate → air, with the PA12 deck as a deliberate thermal break. The honest figure is plate-only: about 42 cm² × 10 W/m²K ≈ 0.042 W/K, so **about 1–1.7 W steady within a 48 °C touch limit**. The plate plus PCB is about 40 J/K, giving a time constant τ ≈ 16 min, so 100 W is a burst mode, as A, B, C and D all say. **Change:** add 12 mm returns on both long edges of the plate that lie *outside* the boot side walls as passive fins (they don't seal, so no new leak path). That is about +20 cm², about +50 % area, for about 7 g. The firmware derate is unchanged.

4. **Leak test (from D and C).** Move the vent to the plate's **outside** face and apply it last. Test first at +100 mbar through the bare hole while dunked.

5. **Datum (from C).** Push all cells toward the top/PCB-fixed end so CTE stays out of the tails.

**What I'd defend:**
- **The boot as the single envelope** beats A's and D's printed PETG tubs on drop toughness and gives the BLE window for free.
- **TPU collars under the screws** beat C's screws "outboard of the bead."
- **Clamping instead of bonding** stays testable and reopenable without cure time, which beats D.
- **No radial seal in a printed rounded-rectangle bore** avoids B's corner-radius and stretch problem.

**Net effect:** +1 bought O-ring cord, +1 sealant moat step, the vent moved to the outside, and plate fins. Mass is about 410 g and assembly is 13 steps.
