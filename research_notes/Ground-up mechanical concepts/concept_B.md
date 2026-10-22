# Concept B: "Flashlight": a closed tube with two radially sealed end caps

## 1. Concept in one paragraph

The four cells, two TPU end yokes and the PCB are joined on the bench into a **cassette**, and the **top cap** is screwed to that cassette. The top cap holds the two USB-C receptacles and seals them on the bench. The cassette is charged, discharged and BLE-checked while it is still open. It then slides lengthwise into a **printed rounded-rectangle tube** (MJF PA12, or FDM ASA/PETG for P0) until the top cap's radial O-ring is seated in the tube bore. A **bottom cap** with its own radial O-ring closes the other end and pushes a TPU cushion against the cassette. The last part fitted is an **aluminium heatsink saddle** (JLC sheet metal, 1.5 mm 5052, laser-marked label). It goes into a window in the tube's PCB face, sits on gap filler on the hot parts, and is bonded in with a flexible sealant. The key decision: **the tube is printed, not metal.** A radial O-ring needs a bore with generous corner radii (r ≥ ~2× the cord section). A rectangular aluminium extrusion or a folded JLC shell has inside corners of about 1 mm, plus a seam in the folded case, so neither can take one. A round metal tube that fits 2×2 cells plus a board would be about 76 mm in diameter, roughly 50 % more cross-section. Printing lets me put r = 6 mm corners in the bore, so the BLE window is "free" and only the hot face is metal.

```
 SECTION A-A (across, at mid-length)          SIDE VIEW / EXPLODED (along)
                                                  ┌─────────┐  top cap (PA12) + 2× USB-C
   Al saddle (1.5 mm 5052) ─┐                     │ ▯     ▯ │  radial O-ring 55×2.5
 ┌──────────────────────────▼──┐ ← returns 15 mm  ├─┬─────┬─┤  outer skirt grips tube end
 │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│   wrap 2 edges   │ │     │ │
 │▓ gap filler ▒▒  ▒▒▒  ▒▒     ▓│                  │ │ PCB │ │ ← cassette: yokes+cells+PCB
 │══════════ PCB 43 × 74 ═══════│◄ BLE module      │ │     │ │     (slides in from top)
 │   (2.5 mm air, back parts)    │   edge: plastic  │ │     │ │
 │  ╭───╮ ╭───╮   C1=P1  C4=P2   │   wall only,     │ │     │ │ ┌──────────────┐
 │  │C1 │ │C4 │                  │   saddle return  │ │     │ │ │ printed tube │
 │  ╰───╯ ╰───╯                  │   stops ≥12 mm   │ │     │ │ │ 50×60×90, r6 │
 │  ╭───╮ ╭───╮   C2=P3  C3=P4   │   short of it    │ │     │ │ │ bore corners │
 │  │C2 │ │C3 │                  │                  │ │     │ │ └──────────────┘
 │  ╰───╯ ╰───╯                  │                  ├─┴─────┴─┤  TPU cushion (in yoke)
 └──────────────────────────────┘ printed PA12     │ ○vent   │  bottom cap + O-ring 55×2.5
   outer 50 × 60 mm, wall 2.2      tube, r6 bore   └─────────┘  2 screws per cap, outboard
                                                                of the O-ring (wet side)
```

## 2. Parts list

| # | Part | Material / process | Mass | Make/buy |
|---|---|---|---|---|
| 1 | Tube, 50×60×90 mm, 2.2 mm wall, r6 bore corners, window on PCB face, 2 bonding rebates | MJF PA12 (JLC); FDM ASA/PETG for P0 | 39 g | made |
| 2 | Top cap: plug + outer skirt, 2 USB-C apertures, O-ring groove, 2 PCB bosses | MJF PA12 | 11 g | made |
| 3 | Bottom cap: plug + skirt, groove, Ø1.5 mm vent hole in a recess | MJF PA12 | 9 g | made |
| 4 | Heatsink saddle, 50×86 face + 2×15 mm returns, laser-marked label | JLC sheet metal 5052, 1.5 mm, black anodise or bare | 22 g | made |
| 5–6 | Top/bottom yokes: 4 cell pockets with shoulder lands, weld windows, PCB rails, tail channels, 2 mm cushion | TPU 95A (JLC or home) | 2×6 g | made |
| 7 | Cells 4× EVE 58E | bought | 280 g | bought |
| 8 | PCB assembled | JLC PCBA | 25 g | bought |
| 9 | Nickel: 3 series links (pre-formed 21700 2P links) + 2 pack tabs, 0.2×8 mm pure Ni | bought strip | 4 g | bought |
| 10 | 2 × O-ring 55 × 2.5 mm NBR70 (or FKM) | bought | 2 g | bought |
| 11 | 4 × M2.5×6 thread-forming screws (cap retention) + 2 × M2×5 (PCB→top cap) | bought | 2 g | bought |
| 12 | ePTFE adhesive vent (Gore VE80205-class, 2×5 mm) | bought | <0.1 g | bought |
| 13 | Gap filler, dispensed, ~1 mm (e.g. 3 W/m·K putty) | bought | 2 g | bought |
| 14 | MS-polymer / neutral-cure silicone bead (saddle bond) + O-ring grease | bought | 3 g | bought |

That is 6 made part designs, 7 printed or sheet parts, and 14 line items (24 pieces if every screw and cell is counted).

## 3. Assembly sequence

**Electronics sub-assembly**
1. Press both USB-C receptacle gaskets into the top-cap apertures. Screw the PCB to the cap bosses with 2 × M2. The boss height sets gasket compression, so no fixture is needed.
2. Bench-test the PCB + cap from a lab supply on the cell-tap inputs: PD, BLE, firmware flash via J301/J302.

**Cell module.** The yokes act as the weld jig, so no separate fixture is needed.

3. Put the 4 cells into the bottom yoke, polarity per moulded-in marks, and cap them with the top yoke. Check polarity with a meter.
4. Lay the nickel links and pack tabs into the yoke weld windows and spot-weld them (3 links + 2 tabs).
5. Measure all three tap voltages and the pack voltage.

**Cassette**

6. Slide the PCB/top-cap assembly into the yoke rails. The tails go through the plated PCB slots.
7. Solder the tails in BMS order: PACK− first, then CELL1, CELL2, CELL3, then PACK+.
8. Bench-test the full cassette: charge/discharge, gauge learning cycle, BLE range. This is the moment to fix anything.

**Closing**

9. Grease the 2 O-rings and fit them on the caps. Slide the cassette into the tube from the top until the cap skirt bottoms out. Drive 2 screws.
10. Fit the bottom cap (O-ring, cushion contact) and drive 2 screws.
11. **Leak test:** draw −20 kPa through the open vent hole with a hand vacuum pump and a printed nipple. Watch the decay over 2 min. Then apply the vent sticker.
12. Dispense gap filler on the hot parts through the open window and run the sealant bead in the window rebate. Press the saddle on, tape it, and cure for 24 h.
13. Final immersion check: 30 min at 1 m, or a vacuum decay test through a temporary port before the vent goes on (swap steps 11 and 12 to test the whole envelope).

**Count:** 13 steps, of which 2 are tests and 1 is a cure wait. Tools: spot welder, 80 W iron with active flux, screwdriver, multimeter, caulk gun or syringe, and a hand vacuum pump with a printed nipple. **Fixtures: zero dedicated**, because the yokes are the weld jig and the tube is the assembly guide.

## 4. Cell-to-PCB connection

**Layout and series path.** The near-PCB row holds P1 and P2; the far row holds P3 and P4. C1 = P1, C2 = P3, C3 = P4, C4 = P2, with cell orientation alternating.
- **Top end:** link C1+/C2− (tap CELL1) and link C3+/C4− (tap CELL3).
- **Bottom end:** link C2+/C3− (tap CELL2), plus the PACK− tab on C1− and the PACK+ tab on C4+.
- Both power tabs land on the near row at the bottom, so the two 7 A tails are each under 10 mm long. The CELL2 tail runs 22 mm across the bottom yoke in a TPU channel.

**Power (7 A).** I use 0.2 × 8 mm pure nickel, about 43 mΩ/m. A 25 mm path adds about 1 mΩ, which is roughly 50 mW at 7 A. Each tail passes through a 1.0 × 8.5 mm plated slot and is soldered on both sides. The slot carries shear, so the solder fillet carries current, not load.

**Sense.** The three taps are tails of the series links themselves. That is one part per node, and there are no wires.

**Kelvin (optional).** One snip along the pack-tab tail gives a 3 mm sense finger that splits from the 5 mm power finger at the weld nugget, so the Kelvin junction sits at the cell. Each finger goes to its own PCB slot.

**Vibration and drop.** The PCB is clamped to the top cap. The cells float in the TPU yokes, which have a 2 mm cushion. In a 1 m end-on drop the cells can therefore move about 0.5–1 mm relative to the PCB. **Every tail has a 1.5 mm U stress loop** between the weld and the slot, formed over a printed comb that is part of the yoke. Tails never bridge a rigid-to-rigid joint without a loop.

**No-spot-welder alternative.** Buy cells with factory-welded solder tabs and solder the links. The tools are then just an iron.

**Risk.** Soldering to nickel close to the can heats the cell. Doing the solder joints on the PCB slots, ≥15 mm from the welds, avoids this.

## 5. Sealing to IP67

| Leak path | Seal | Why it holds |
|---|---|---|
| Top cap ↔ tube | Radial O-ring 55×2.5 NBR on cap plug, r6 bore | Squeeze set by XY geometry, not clamp force |
| Bottom cap ↔ tube | Same | Same |
| USB-C ×2 | Receptacle's own IP68 gasket compressed by cap aperture face; compression set by PCB-to-cap boss height (±0.1 mm printed) | Done and checked on the bench in step 1–2 |
| Saddle ↔ tube window | 1–1.5 mm flexible bead (MS polymer) in a rebate; returns sit in slots, making a labyrinth | Fills printed warp up to ~1 mm; elastic for Al/PA12 CTE mismatch (~0.25 mm shear over 80 mm at ΔT 40 K) |
| Cap retention screws | Placed **outboard** of the O-ring, on the wet side | Not a leak path at all |
| BLE window | None needed: the whole side wall is PA12 | No joint |
| Breathing | ePTFE adhesive vent inside bottom cap recess | Equalises the ~200 mbar thermal/altitude swings Gore cites for small enclosures, which would otherwise load the seals |

**Radial vs face seal, quantified.** A 2.5 mm cord wants 15–30 % squeeze, which is 0.38–0.75 mm (nominal 0.56 ± 0.19).

*Radial seal.* The radial gap stack is: tube bore ±0.085 (MJF ±0.3 % on 55 mm, halved), cap groove ±0.085, cord section ±0.08, and cap eccentricity ±0.1. The RSS is ±0.18 mm, which fits the band. Printing one test ring and adjusting a single groove offset in CAD closes the remainder. The O-ring's reaction is hoop load, internal to the cap/tube pair; **the screws carry no sealing load, so plastic creep doesn't relax the seal.**

*Face seal on the same 50×60 flange.* FDM flange warp of 0.1–0.4 mm adds directly to the squeeze error. On top of that, the seal needs roughly 0.3–0.6 N/mm × 190 mm ≈ 60–115 N of permanent screw load into printed bosses, which creeps.

**Catch I found by calculation.** The O-ring pushes the tube's flat 55 mm end walls outward. Treating a 10 mm wide strip of 2.2 mm PA12 as a fixed-fixed beam under ~0.5 N/mm gives an estimated bulge of **~0.8 mm**, which is more than the whole squeeze. That is why both caps have an **outer skirt** that sandwiches the tube end: the skirt holds the wall at the land, protects the end edges, and carries the retention screws. Do not drop the skirt to save mass.

**Printed porosity**
- MJF PA12 at ≥2.2 mm walls is the production choice: no seam, isotropic.
- FDM tube for P0:
  - Print it **upright** so layer lines run around the bore, parallel to the seal line. Lying down, every layer line would be an axial leak channel under the O-ring.
  - Use 4–5 perimeters at 100 % infill and about 103 % flow.
  - Put the Z-seam on the window side, sand the two 8 mm lands lightly, and grease them.
  - Optionally brush thin epoxy on the inside.
- A printed TPU radial ring is possible, but TPU 95A has much worse compression set than NBR and a start/stop seam. Use it only for a first fit check. The two bought O-rings cost cents.

## 6. Drop & vibration

- **End-on, either end.** The caps stand ~1.5 mm proud of the tube, so the cap is the first contact. The load path is ground → cap → TPU cushion (2 mm) → yoke **shoulder lands on the can rim**. A relief clears the + cap/CID button and the weld nuggets.
  - At 1 m (4.4 m/s), 2 mm of stroke gives about 500 g, which is ~1.4 kN for 280 g of cells. Spread over 4 × 160 mm² of rim, that is ~2 MPa, comfortable for TPU and the can.
  - Because the cap is the impact face, the retention screws only see the tube's own inertia (~0.08 kg × 500 g ≈ 400 N across 2 screws), not the cassette's.
  - The PCB is tied to the top cap. The USB receptacles bear on cap shoulders, not on their gaskets.
- **Side or face.** Cells are held radially only by the TPU yokes at their ends and touch the tube wall through about 0.4 mm of clearance. A side hit dents PA12 locally, which spreads the load along the can's length.
  - On the heatsink face, the aluminium saddle plus 1 mm of gap filler and 2.5 mm of air protect the PCB. The saddle also stiffens the window.
- **Corner.** The saddle returns wrap the two long edges on the PCB side. Cap skirts cover all eight end corners in PA12, the toughest of the allowed printed materials. A TPU over-boot on the caps is an optional add-on if testing shows cracking.
- **Vibration.** The cassette is preloaded axially between the cushion and the top cap shoulder, and the tails have stress loops. Nothing rattles.

## 7. Thermal

**PCB to saddle.** About 400 mm² of contact on the FETs and inductors through 1 mm of 3 W/m·K filler gives ~0.8 K/W, or **~4 K at 5 W**. A 1.5 mm aluminium plate spreads the heat with a few more kelvin.

**Saddle to air** (50×86 face + returns ≈ 0.0079 m², h ≈ 11 W/m²K with anodised black ε≈0.85):
- That is ~0.09 W/K. The plate's thermal time constant is only ~7 min, so **a continuous 100 W output (5 W loss) would heat the saddle to ~+45–50 K**. That is too hot to touch.
- The PA12 walls are thin enough not to be the bottleneck (2.2 mm / 0.2 W/m·K = 0.011 m²K/W vs 0.09 for the air film). The real limit is spreading heat away from the plate, not the plastic.
- A full metal tube would roughly double the effective area. That is the honest cost of the printed tube.

**Mitigation.** The firmware derates on the TMP1075 sensors, holding saddle ≤ 48 °C and cells ≤ 45 °C while charging. Typical trail loads of 20–30 W (~1.5 W loss) settle around +12–15 K. Cells generate ~4 W of their own heat at 7 A; their 330 J/K thermal mass and the 2.5 mm air gap to the PCB keep them coupled loosely to the saddle.

## 8. Estimates

- **Outer size:** 50 × 60 × 93 mm (tube 90 + proud caps), about 280 cm³.
- **Mass:** ≈ 410 g. Cells 280, PCB 25, tube 39, caps 20, saddle 22, yokes 12, the rest ~12.
- **Parts:** 14 line items / 24 pieces; 6 custom designs.
- **Material types:** 4 made (PA12, TPU, 5052 Al, Ni) plus bought NBR, sealant, filler and ePTFE.
- **Assembly:** 13 steps, 0 dedicated fixtures.

## 9. Risks / weak points, and the test for each

1. **Thermal ceiling at 100 W sustained.** Test a powered cassette in the closed tube at 100 W, with thermocouples on the saddle, the FETs and C1/C4.
2. **Tube end bulge and seal squeeze across print batches.** Print bore and land coupons and measure them. Do 30 min / 1 m immersion and −20 kPa decay tests on 3 builds, before and after 10 thermal cycles from −10 to 50 °C.
3. **Saddle bond is permanent and wet**, with 24 h cure and no rework. Test peel and leak after 10 drops. The P0 alternative is a printed TPU face gasket under 6 screws into heat-set inserts, which is reopenable.
4. **USB-C gasket compression depends on printed boss height.** Use a feeler or immersion test per port. The datasheet compression range needs confirming.
5. **CELL2 tail is 22 mm long.** Vibration test (sine sweep or a "car dashboard" run) plus inspecting the solder joints with a microscope.
6. **Cell vent event.** A sealed tube is a pressure vessel. The bottom cap's 2 thread-forming screws should be the **intended weak link**, letting go at a few bar before the walls split. Proof-test an empty tube with a hand pump and gauge.
7. **The PCB is sealed in for good**, apart from removing the caps. Debug and gauge training must be finished at step 8.

## 10. Best ideas others could borrow

- **Radial seals with an outer clamping skirt.** Squeeze is set by printed XY geometry, there is no sustained screw load on printed parts, and the skirt stops the free tube end from bulging under O-ring pressure (a ~0.8 mm effect if you skip it).
- **Top cap belongs to the electronics.** USB-C gaskets are compressed by boss geometry and verified on the bench before any cell is near.
- **The yoke is the weld jig.** Cell holders with weld windows and shoulder lands remove the separate fixture and protect the CID in the same part.
- **Leak-test through the vent hole before the vent sticker goes on.** It costs nothing and gives a quantitative pass/fail.
- **Retention screws on the wet side of the O-ring** are never a leak path.
- **Print sealing bores upright** so layer lines run parallel to the seal line, and put the Z-seam where it's cut away or off the land.
- **Make the impact face the cap** (proud caps), so drop loads don't pass through the cap retention.

### Sources
- Gore small adhesive vent VE80205 and the ~200 mbar pressure-swing figure: [In Compliance](https://incompliancemag.com/new-protective-vent-improves-reliability-of-small-electronic-devices/), [Gore vent FAQ](https://www.gore.com/resources/faq-gore-protective-vents), [Gore adhesive vents](https://www.gore.com/products/venting/adhesive-vents)
- O-ring squeeze and clearance (Parker ORD 5700-derived tables): [Apple Rubber static table](https://www.applerubber.com/src/pdf/table-a-static.pdf), [All Seals glands](https://allsealsinc.com/pdfs/Dynamic-oring-glands.pdf), [Global O-Ring calculator](https://www.globaloring.com/groove-design-calculator/)
- Printed waterproof enclosures (perimeters, 100 % infill, PETG/ASA, TPU seal leaks, test before use): [Zbotic](https://zbotic.in/3d-printing-electronics-housings-water-and-dustproof-cases/), [MakerWorld waterproof box](https://makerworld.com/en/models/454290)
- 5052 bend radius and flange minimums for the saddle: [Fictiv sheet metal](https://blog.fictiv.com/specifications/sheet-metal), [Protocase bend radii](https://www.protocase.com/resources/Protocase-Bend-Radii-Bend-Sizes.pdf)
- Numbers I estimated rather than sourced: bulge, thermal, drop g-load, and MJF tolerance (±0.3 % is JLC's typical claim, to verify).
