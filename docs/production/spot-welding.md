# Spot welding the P0 pack

How the cells get welded: the welder, the strip, the recipe, and how to qualify a weld before the real pack. It goes with `p0-assembly.md`, which gives the build order. Decided with Logan on 2026-10-23 and 2026-10-24. Nothing has been welded yet, so the settings below are starting points to confirm on coupons.

## Welder: AWithZ P20B

- **What:** a 14.6 kW supercapacitor welder (about 1600 A peak), mains powered through its 100–240 V adapter, with handheld pens and a foot pedal. It is rated for 0.3 mm pure nickel and 0.15 mm copper.
- **Why:** the 0.2 mm nickel strip in loss cut 4 is beyond the cheap handheld welders. The kWeld plus kCap was dropped: it was out of stock and costly, and the kCap is itself rated to 0.2 mm nickel at most. The P20B needs no LiPo or car battery, and it has the most public test data of the welders compared (esk8.news copper-sandwich thread, Sept 2025 to Feb 2026).
- **Where:** AWithZ's own eBay store (Los Angeles), about $255 on 2026-10-23. The runner-up, the P30C (21.8 kW, $339.99 at diy500amp), has more copper headroom.
- **Pens are required.** The cells are welded inside the PA12 carrier, through the 14 mm weld windows in its end frames, so a fixed top arm can't reach them.

## Strip

| Use | Material | Size | Source (2026-10-23) |
| --- | --- | --- | --- |
| Series strips; the top two keep a 3 mm tongue for the CELL1 / CELL3 wires | Pure nickel, 99.6 % | 0.2 × 10 mm | diy500amp, Pure Nickel Strip Roll, 5 m |
| PACK− / PACK+ pads (the wires are soldered to them on the bench) | Pure nickel | 0.2 × 7 mm, cut from the 10 mm roll (or the 0.2 × 8 roll) | Same listing |
| PACK power leads / Kelvin and sense leads (2026-10-31) | Tinned copper; Zerohal 100G halogen-free polymer / cross-linked ETFE | 18 AWG, TE 100G0111-1.00-0 (1.80 mm OD at most) / 28 AWG, TE 55A0111-28-9 (= M22759/32-28, 0.74 mm OD at most) | DigiKey, cut by the foot; see `ordering/parts-tracker.csv` C03 / C04 |

**Check the nickel is real** before welding anything. Nickel-plated steel looks identical and has 2–3 times the resistance. Four-wire 100 mm of the 0.2 × 10 strip at 5 A from the bench supply: pure nickel reads about 3.5 mΩ (17 mV). Also leave a scrap in salt water overnight: plated steel rusts at the cut edges.

**No copper is welded to a cell.** On the P20B, bare 0.2 mm copper had about a 6 % window between no weld (gear 650) and blowing through the can (gear 690) without flux. With flux it welded, but the copper tore on peel and the flux residue would sit beside the + cap inside a sealed pack. Every weld on a cell is plain nickel, with one recipe.

## Weld qualification (before the real pack)

1. **Coupons.** Two spare 65E cells from the same order, and the same strip roll. Weld both ends: the + cap and the can bottom behave differently.
2. **Find the window.** Start low and step up, with a double pulse and a short preheat. Note the lowest setting that passes the peel test, and the setting where the can blackens, dents or spits. Use a setting about a third of the way up from the lowest pass.
3. **Peel test.** Pull the strip off at 90° with pliers. A pass tears the nickel around the nugget and leaves the nugget on the cell. A fail pops off clean.
4. **Resistance.** Four-wire each test joint at 5 A and write down the mΩ, so the pack's joints can be compared with it.
5. **Real fixture.** A last coupon through a carrier fit print, so the pen angle and pressure match the real job.
6. **Pack welds.** Two pulses per cell end, spaced across the strip. Dress or replace the pen tips when they mushroom. Four-wire every series and PACK joint afterwards, and again after the drop and vibration tests.
7. **Rework.** A failed joint gets new strip on a fresh spot. Never re-weld the same spot more than once.

## Welding inside the carrier

- The cells load sideways into the carrier first. Each strip then slides into the 0.4–0.45 mm gap between the cell ends and the end frame, and is welded through the windows.
- **Sense wires (2026-10-24):** all three cell taps are 28 AWG XL-ETFE wires, soldered to the nickel on the bench before it goes near a cell, so no solder iron touches a cell. CELL2 solders to the middle of the bottom strip (C2+ / C3−), which sits under the frame, not under a window, and its wire lies in the channel in the bottom frame. CELL1 and CELL3 solder under the tongue ends of the top strips, outside the frame. Those joints are 8 mm or more from the nearest weld spot.
- **Before the first weld:** fish-paper rings on the four + ends (C1 and C3 top, C2 and C4 bottom) and the foam preload rings in the bottom frame's pockets (`p0-assembly.md`, step 1). Keep the pens on the + cap inside the ring; a weld through the fish paper chars it.
- Once the first strip is on, the cells are live. Keep the pens from bridging two cells, and cap every loose wire end.
- To confirm on the first carrier fit print: that a 0.2 × 10 mm strip slides into the frame gap, and that the pens sit flat through a 1.6 mm deep, 14 mm window.

The comparison of the PACK tail options (plain nickel, bimetal copper, wire) is drawn to scale in [`docs/archive/pack-tail-options.html`](../archive/pack-tail-options.html) (archived: it predates the decision and still marks option A as recommended). P0 takes option C, the wire tails (2026-10-24): solder the wires to the PACK pads before the pads are welded, and keep every weld spot at least 3 mm from the solder.
