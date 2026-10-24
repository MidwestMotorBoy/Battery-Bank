# Gap filler options (2026-10-24)

The job: about 1.46 cc between the B.Cu via zone and the two front cells (|y| 7–16 mm, z 27–53 mm), with a bond line of 2.75 mm at the can tangent and about 3.8 mm at the edges. The pack is built at home, sealed in the IP67 cup with no potting, and has the cells fitted when the filler goes in, so there is no oven (BAK 65E max 60 °C). Interactive comparison: <https://claude.ai/artifact/K8jvRVs7B9i3sVL1AdEWej>.

**Decision (Logan, 2026-10-24): Parker Chomerics THERM-A-GAP GEL 30 for P0 and the gift packs.**

## What conductivity buys (`fill.py`, `renders/fill.json`)

| Filler k | Hottest part, 100 W | Hottest part, charging | 100 W burst |
| --- | --- | --- | --- |
| none | 62.6 °C | 59.6 °C | 2.0 min |
| 1.5 W/m·K | 60.0 °C | 55.3 °C | 5.2 min |
| 3 W/m·K | 58.5 °C | 53.2 °C | 6.2 min |
| 6 W/m·K | 55.7 °C | 51.8 °C | 5.8 min |

Past 3 W/m·K more board heat goes into C4, so the cell NTC ends the burst sooner. Datasheet values are measured by different methods (ASTM D5470, Hot Disk, laser flash) and aren't directly comparable, so handling, cure and rework decide.

## Options

Mass is for 1.46 cc. Prices are single-unit listings seen in October 2026.

| Product | k (method) | Density, mass | Cure | Rework | Dispensing | Insulation | Shelf life | Price | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Parker GEL 30, 65-00-GEL30-0010 (10 cc) | 3.5 | 3.1, 4.5 g | none (pre-cured, one part) | peels off | hand-push syringe, stiff (20 g/min at 90 psi) | 8 kV/mm, 10¹⁴ Ω·cm, V-0 | 18 months | Farnell €51.20, also Newark, DigiKey | **pick** |
| Bergquist TGF 3600, GF3500S35-07-60-50CC | 3.6 (D5470) | 3.0, 4.4 g | 15 h at 25 °C, 60 min pot life | lifts out (Shore 00 35) | 50 cc 1:1 gun and static mixers; batch builds | 275 V/mil, 10¹⁰ Ω·cm, V-0 | 5 months | DigiKey $51.86 | runner-up |
| Laird Tflex CR350S (50 cc duo) | 3.6 (Hot Disk) | 3.15, 4.6 g | 2 h at 70 °C + 0.5 h at 100 °C only | easy | as TGF 3600 | 7 kV/mm, 2.9×10¹⁴ Ω·cm | 9 months | Mouser | out: oven cure |
| Bergquist Liqui Form TLF LF3500 (30 cc min) | 3.5 (D5470) | 3.1, 4.5 g | none | not stated | cartridge gun | 10 kV/mm, 10¹³ Ω·cm | 104 days | no small-qty price | skip |
| Laird Tputty 607MF (30 cc min) | 6.2 (Hot Disk) | 3.42, 5.0 g | none | easy | syringe, 105 g/min | 6 kV/mm, 10¹⁴ Ω·cm | 9 months | DigiKey 180 cc $132 | skip: heavier, higher k doesn't help |
| MG Chemicals 8327GL6 (25 mL) | 6.0 (laser flash) | 2.3, 3.4 g | non-curing paste, silicone-free | wipes off | spatula or syringe, 7,000 Pa·s | 3.2 kV/mm, 10⁹ Ω·cm, V-0 | 2 years | Farnell UK £31.59 | lightest; 3 and 5 W/m·K siblings discontinued |
| Thermal Grizzly TG Putty Pro (30 g) | not published | not published | none | easy | by hand; rated 0.2–3.0 mm gaps | "non-conductive" | not stated | $47.85 | skip: no data |

Insulation doesn't decide it: the cans are sleeved, the pack tops out at 16.8 V, and even 10⁹ Ω·cm across the zone is about 60 MΩ. Parker GEL 8010 (2.7 g/cc, 3.0 W/m·K) saves 0.6 g but outgasses about nine times as much (1.33 % TML), which isn't welcome in a sealed cup.

## Using GEL 30

- Tare the module on a 0.01 g scale and lay about 2.3 g per zone, a little proud, through a 14–16 gauge tapered tip (or no tip).
- Seat the board. Nothing cures, so the module can go straight into the cup.
- Lift the board on the first dummy and check the gel wetted both the copper and the cans.
- To rework, peel it off, wipe with IPA, and use fresh gel.
- Two syringes cover P0, the dummy, and about five gift packs.

## Sources

- THERM-A-GAP gels datasheet: <https://cdn.components.ru/media/PDF/3757824.pdf>; Farnell: <https://ie.farnell.com/chomerics/65-00-gel30-0010/dispensable-gel-10cc-syringe-silicone/dp/3934801>
- TGF 3600 TDS: <https://conro.com/downloads/Manuals/BERGQUIST-TGF-3600-TDS.pdf>
- Tflex CR350S: <https://www.mouser.com/datasheet/3/94/1/THR_DS_Tflex_CR350S_08142024.pdf>
- TLF LF3500: <https://datasheets.tdx.henkel.com/BERGQUIST-LIQUI-FORM-TLF-LF3500-en_GL.pdf>
- Tputty 607MF: <https://www.mouser.lt/datasheet/3/94/1/THR_DS_Tputty_607MF.pdf>
- 8327GL6: <https://www.mouser.lt/datasheet/3/293/1/tds_8327GL6.pdf>
- TG Putty: <https://www.thermal-grizzly.com/media/05/b4/a2/1734342273/TG_Datasheet_Putty_EN_TGU20241212.pdf>
