# Pack wires: TE 100G0111-1.00-0 and 55A0111-28-9 (2026-10-31)

Logan asked whether two TE wires can replace the PACK and sense wire picks from 2026-10-24 (M22759/11-18 and M16878/6 Type ET). Both fit the existing Ø1.5 / Ø0.8 mm plated holes, the carrier notches (sized for 1.8 / 0.75 mm OD plus 0.2 mm each side) and the B.Cu keep-outs, so nothing on the board or in the model changes.

TE's own drawing pages can't be fetched from the cloud, so the figures come from TE's datasheets and drawings as mirrored by Farnell, element14 and RS (links at the end).

## 18 AWG PACK leads

| | TE 100G0111-1.00-0 (new) | M22759/11-18 (old) | TE 55A0111-18 / M22759/32-18 (fallback) |
| --- | --- | --- | --- |
| Standard | Zerohal 100G, VG 95218-20 Type E (German defence), EN 50306-2 | US mil-spec | Raychem Spec 55 / US mil-spec |
| Conductor | 1.00 mm², 19 × 0.25 mm tinned copper, 1.17–1.26 mm | 19/30 silver-plated copper, ~1.22 mm | 19/30 tinned copper, ~1.22 mm |
| Insulation | Halogen-free polymer blend, dual wall, 0.20 mm min | PTFE, ~0.25 mm | Radiation cross-linked ETFE, ~0.15 mm |
| OD | 1.69–1.80 mm | 1.68–1.78 mm (AWC) | 1.47–1.57 mm |
| Fit in the 1.8 mm notch / keep-outs | Exactly at the limit, same margins the model uses | 0.02 mm under | 0.23 mm under |
| Max conductor resistance | 20.0 Ω/km at 20 °C | ~20.9 Ω/km | ~21–22 Ω/km |
| 25 mm at 9.4 A | 0.50 mΩ, 44 mW | 0.52 mΩ, 46 mW | ~0.55 mΩ, 49 mW |
| Temperature | −55 to 125 °C (20,000 h) | −65 to 200 °C | −65 to 150 °C |
| Mass | 10.7 g/m, ~0.5 g for both leads | ~11 g/m | ~9 g/m |
| Voltage | 750 / 1300 V AC | 600 V | 600 V |
| Buying | 100 m reels only, ~US$180–245; RS UK has dropped it, RS AU back-ordered to 2027-01-07 | 50 ft lots (Skycraft) | 10 ft cuts, ~US$11 (wirecare.com) |

- **Electrical:** the 1.00 mm² conductor is a touch bigger than 18 AWG (0.82 mm²), so it is marginally better. At the 6.5–9.4 A this pack runs, any of the three is about 0.5 mΩ per lead and under 50 mW. The difference is a few milliwatts.
- **Temperature:** the cans top out at 48 °C and the board near the holes at about 60 °C at 100 W, so 125 °C is plenty.
- **Soldering:** the 100G insulation is a polymer blend, not a fluoropolymer, and the datasheet says nothing about solder-iron resistance (it gives under 0.5 % shrink at 150 °C). Strip about 3 mm, tin quickly, keep the iron off the jacket, and try one scrap joint into a Ø1.5 hole on a spare board before the real build. Tinned copper wets as easily as silver-plated.
- **Flex:** 19 strands of 0.25 mm, the same as 19/30. No difference.
- **Colour:** the last digit is the Mil-Std-681 colour, so -0 is black and -2 red. A red PACK+ would mean a second 100 m reel.

## 28 AWG sense and Kelvin leads

| | TE 55A0111-28-9 (new) | M16878/6 Type ET (old) |
| --- | --- | --- |
| Conductor | 7/36 tinned copper | BCE 19/40 or BCB 7/36 |
| Insulation | Radiation cross-linked ETFE, ~0.15 mm | PTFE |
| OD | 0.64–0.74 mm (0.027 ± 0.002 in; it's M22759/32-28) | 0.64–0.74 mm |
| Temperature | −65 to 150 °C | −65 to 200 °C |
| Buying | £71.35 per 100 m reel at Farnell UK, 27 in stock | IEWC 500 ft minimum |

It's a drop-in: same OD, so the CELL2 channel (1.0 × 0.95 mm) and the Ø0.8 mm holes are unchanged. XL-ETFE is the usual aerospace wire for hand soldering and doesn't melt back at iron temperatures. The sense leads carry only balancing current and the Kelvin leads none, so resistance doesn't matter.

## Sources

- [RS UK, 100G0111-1.00-0](https://uk.rs-online.com/web/p/harsh-environment-wire/1365952): 19/0.25, 0.2 mm wall, 1.69–1.80 mm OD, 125 °C, 750 V, no longer stocked
- [element14, 100G0111-1.00-9](https://my.element14.com/raychem-te-connectivity/100g0111-1-00-9/single-wire/dp/3236605), with the TE drawing (farnell.com/cad/1772931.pdf: 1.17–1.26 mm conductor, 1.69 / 1.75 / 1.80 mm OD, 10.70 kg/km, 20.00 Ω/km) and datasheet (farnell.com/datasheets/2861826.pdf: part-number key, dual wall)
- [RS AU, 100G0111-1.00-6](https://au.rs-online.com/web/p/hook-up-wire/2441403): AU$278.67 per 100 m, back-ordered
- [Farnell UK, 55A0111-28-9](https://uk.farnell.com/raychem-te-connectivity/55a0111-28-9/single-wire/dp/3236641) and [TE datasheet, 55A0111-28-0](https://www.te.com.cn/chn-zh/product-2183123001.datasheet.pdf)
- [NASA NEPP, M22759/32 sizes](https://nepp.nasa.gov/npsl/Wire/22759/22759_32.htm), [TE datasheet, 55A0111-18-6](https://www.te.com.cn/chn-zh/product-216051-000.datasheet.pdf), [wirecare, M22759/32-18 10 ft cuts](https://www.wirecare.com/products/tefzel-mil-spec-hookup-wire-18-awg-red)
