# Ordering: Monolith P0 build

Everything to buy for the first Monolith packs, one line per thing to order, with where to get it and where the order stands. Quantities are for **5 packs** plus a few spares unless the line says otherwise.

- **[`parts-tracker.csv`](parts-tracker.csv)** is the tracking sheet and the source of truth. It opens in Excel, Numbers or Google Sheets, and GitHub shows it as a table.
- **The tables below** are a copy of it with clickable links, rebuilt by `python ordering/update_readme.py`. Edit the CSV, then run the script (or ask Claude to).

What goes in each pack, and why, lives in [`docs/production/p0-assembly.md`](../docs/production/p0-assembly.md) and the parts list doc (https://claude.ai/artifact/H3ockxT3mDWvfV9bMjEbps). This folder only tracks buying.

## How to use the sheet

| Column | What goes in it |
|---|---|
| ID | Fixed line number: B board, L hand-solder parts, C cells and pack, H housing, K consumables, T tools. Add new lines at the end of their group with the next free number. |
| Per pack / Qty to buy | What one pack uses, and what to order for 5 packs with spares. |
| Vendor / Link | Where to buy. Some links are vendor searches; swap in the exact listing once you've bought it, so a reorder is one click. |
| Unit cost / Total | USD, filled in when known. The price date is in the notes. |
| Status | `To order`, `Decide` (a choice is still open), `Hold` (waiting on something, see notes), `Check` (you may already have it), `Ordered`, `Received`, `Have`, `Dropped`. |
| Order date / Order # / Received | Fill in as orders go out and arrive (dates as YYYY-MM-DD). |

**Excel:** keep it as CSV when you save (File > Save As > "CSV UTF-8"). Excel may offer to convert the file or reformat dates and long numbers like order numbers; say no, or prefix an order number with an apostrophe.

## Order plan

1. **Now, the board (JLCPCB).** Upload the files in [`hardware/Production/jlc/`](../hardware/Production/jlc/) (top-side assembly only, see `ORDER-NOTES.md`). Sort out B02–B07 in the same order, or JLC leaves those parts off: TPS25751 (U401/U501), SiZ240DT (Q401/Q402/Q501/Q502) through global sourcing (D401/D501 are now the in-stock Maxinmicro TVS2200DRVR, C55616459); Coilcraft XGL7030-332MEC (L401/L501) and the CC2340 module (U301) consigned or global-sourced; and C49248023 picked by hand on the L402/L502 line.
2. **Now, LCSC.** The 12 bottom-side parts for hand-soldering, plus R124/R126 (left off at JLC on purpose, fitted after the pack voltages check): L01–L04.
3. **Now, the fit coupons (H01)**, so the full housing order isn't held up. They test the USB-C bores, O-ring squeeze, cap screws and rail clips.
4. **Now, the long-lead small stuff:** gap filler (C07), stickers (H12), vent patches (H10), O-rings, screws, grease, foam and punches, nickel strip, wire, fish-paper rings.
5. **After the coupons pass:** cup, cap, carrier and rail blocks in one JLC3DP order (one powder batch), and the TPU parts. The print files are on master since PR #50 (1.6 mm walls, vent pocket, one-piece bumpers).
6. **Hold: cells (C01).** Wait until BAK confirms the datasheet and the temperature-stepped charge profile, then buy 24 from one batch.

## Still open

- **Cells:** waiting on BAK's reply (C01).
- **Back-cell NTCs:** confirm the Semitec 103AT type against the BQ40Z50 thermistor table (C06).
- **Foam thickness:** 1.6 or 1 mm, picked by measuring the cell gap once cells are in the carrier (C08/C09).
- **Screw length:** the model uses M2 × 5 (`SCREW_L` in `monolith_cup.py`); the parts list doc still says × 6.
- **Tools marked `Check`:** mark them `Have` or `To order`.

## Tracker

<!-- tracker:start -->

_Generated from `parts-tracker.csv` by `update_readme.py`; edit the CSV, not this table._

**Status:** To order 28 · Decide 2 · Hold 7 · Check 5 · Have 1  
**Known prices:** $526.93 listed so far (most lines have no price yet), $0.00 ordered.

### Board

| ID | Item | Qty | Vendor | Cost (USD) | Status | Ordered | Notes |
|---|---|---|---|---|---|---|---|
| B01 | P0 board: PCB + top-side assembly<br><sub>6 layers, 43.25 x 74.43 x 1.6 mm, ENIG, 2 oz outer / 0.5 oz inner, epoxy-filled capped vias, SAC305 paste</sub> | 5 boards | [JLCPCB](https://cart.jlcpcb.com/quote) |  | **To order** |  | Upload from hardware/Production/jlc/: Monolith_gerbers_JLC.zip, Monolith_BOM_JLC_top.csv, Monolith_CPL_JLC_top.csv (top side only; 249 parts). Rotations and F102 offset already checked in JLC preview (ORDER-NOTES.md). PCBA minimum is 2: assemble 2 first or all 5. Lines B02-B07 must be resolved in the same order or JLC leaves those parts off. |
| B02 | TPS25751DREFR (U401, U501)<br><sub>USB-C PD controller, WQFN-38</sub> | 10 | [JLC global sourcing](https://www.lcsc.com/product-detail/C30169739.html) |  | **To order** |  | LCSC C30169739 out of stock on 2026-10-30; critical part, no substitute. |
| B03 | SiZ240DT-T1-GE3 (Q401, Q402, Q501, Q502)<br><sub>Vishay dual N-FET, PowerPAIR 3x3S</sub> | 20 | [JLC global sourcing](https://www.lcsc.com/product-detail/C3289403.html) |  | **To order** |  | LCSC C3289403 had only 2 in stock on 2026-10-30; need 4 per board. |
| B04 | TVS2200DRVR (D401, D501)<br><sub>Wuxi Maxinmicro 22 V flat-clamp TVS, DFN-6 2x2 (pin-compatible with TI TVS2200)</sub> | 10 | [JLC parts library](https://www.lcsc.com/product-detail/C55616459.html) | 1.35 | **To order** |  | Switched 2026-10-31 from TI C523793 (short at JLC) to Maxinmicro C55616459 (LCSC stock 3000, extended part). In the JLC BOM now; check the pin-1 rotation of D401/D501 in the JLC preview. |
| B05 | Coilcraft XGL7030-332MEC (L401, L501)<br><sub>3.3 uH, 7 x 7 x 3 mm</sub> | 12 | [DigiKey / Coilcraft, consigned to JLC](https://www.digikey.com/en/products/result?keywords=XGL7030-332MEC) |  | **To order** |  | No LCSC part. Consign (ship to JLC) or let JLC global sourcing buy it from DigiKey/Mouser. 10 + 2 spare. |
| B06 | TI CC2340R5MODAN0MHAR (U301)<br><sub>BLE module, 7 x 10 mm</sub> | 6 | [DigiKey / TI, consigned to JLC](https://www.digikey.com/en/products/result?keywords=CC2340R5MODAN0MHAR) |  | **To order** |  | No LCSC part (ORDER-NOTES.md). Consign or global sourcing, same as B05. 5 + 1 spare. |
| B07 | ABC EHE05023R3MFB (L402, L502)<br><sub>3.3 uH, 5.5 x 5.2 x 2.0 mm</sub> | 10 | [JLC parts library](https://www.lcsc.com/product-detail/C49248023.html) |  | **To order** |  | In the JLC BOM, but the selection did not stick last time: pick C49248023 on that line by hand. |

### Hand-solder (LCSC)

| ID | Item | Qty | Vendor | Cost (USD) | Status | Ordered | Notes |
|---|---|---|---|---|---|---|---|
| L01 | 22 uF 35 V 1210 (C208-C213, bottom side)<br><sub>Taiyo Yuden GMK325BJ226MM-P</sub> | 35 | [LCSC](https://www.lcsc.com/product-detail/C778721.html) |  | **To order** |  | From Monolith_bottom_hand_solder.csv. 30 + spares. |
| L02 | 68 uF 35 V polymer tantalum (C421, C456, C521, C556, bottom side)<br><sub>KEMET T593V686M035APE070, EIA-7343-20 (V case, 2.0 mm), on the 7343 D land pattern</sub> | 22 | [Mouser](https://www.mouser.com/c/?q=T593V686M035APE070) | 53.68 | **To order** |  | Logan 2026-10-31, replaces CCTC CA55-D035M476T (LCSC C2761440). Mouser 94 in stock, $2.44 at 10+ (2026-10-31); 52-week factory lead, next 1,000 due 2026-12-21, so buy now. Not at LCSC. From Monolith_bottom_hand_solder.csv. 20 + 2 spare. |
| L03 | 10k B3435 NTC 0402 (TH101, TH104, bottom side)<br><sub>Murata NCP15XH103F03RC</sub> | 20 | [LCSC](https://www.lcsc.com/product-detail/C77131.html) |  | **To order** |  | Front-cell NTCs (TS1/TS4). 0402s get lost: buy double. |
| L04 | 5.1k 0402 (R124, R126)<br><sub>UNI-ROYAL 0402WGF5101TCE</sub> | 20 | [LCSC](https://www.lcsc.com/product-detail/C25905.html) |  | **To order** |  | DNP at JLC on purpose: fitted by hand after the seven pack voltages read right (p0-assembly step 3.1). |

### Cells and interconnect

| ID | Item | Qty | Vendor | Cost (USD) | Status | Ordered | Notes |
|---|---|---|---|---|---|---|---|
| C01 | BAK N21700CX-65E cells<br><sub>21700, 6500 mAh, 3.5 V; one batch, matched to 10 mV and 1 mOhm</sub> | 24 | [Liion Wholesale / diy500amp / United Lithium / 18650 Battery Store](https://diy500amp.com/products/bak-65e-21700-6500mah-25a-battery-high-capacity-energy-cell) | 9.75 ea | Hold |  | HOLD until BAK confirms the datasheet and temperature-stepped charge profile. 20 for 5 packs + 2 weld-qualification + 2 spare. Price is diy500amp 2026-10-23 (sold out then); Liion Wholesale listed 9.25. |
| C02 | Pure nickel strip, 0.2 x 10 mm, 5 m roll<br><sub>99.6 % Ni; series strips and PACK pads (cut to 7 mm)</sub> | 1 roll | [diy500amp](https://diy500amp.com/products/pure-nickel-strip-roll-for-battery-spot-welding) | 15.99 | **To order** |  | Check it is real nickel: 100 mm reads ~3.5 mOhm 4-wire (spot-welding.md). |
| C03 | 18 AWG wire, TE 100G0111-1.00-0 (PACK leads)<br><sub>Zerohal 100G (VG 95218-20 Type E), 1.00 mm2 19/0.25 tinned Cu, 1.69-1.80 mm OD, 125 C, black</sub> | 1 reel (100 m) | [element14 / Farnell (RS AU back-ordered)](https://my.element14.com/raychem-te-connectivity/100g0111-1-00-9/single-wire/dp/3236605) |  | **Decide** |  | Logan 2026-10-31. Only sold as 100 m reels: ~US$180 (RS AU, AU$279, back-ordered to 2027-01-07) to ~US$245 (element14 MY, white -9, 30 in stock); RS UK no longer stocks it. Link is the white -9 listing; -0 is black. Fits the 1.8 mm notches exactly (no hole change). Cheaper fallback with more margin: TE 55A0111-18 / M22759/32-18 (19/30, 1.47-1.57 mm OD, 150 C XL-ETFE), 10 ft cuts ~$11 at wirecare.com. Old pick M22759/11-18 (Skycraft 50 ft) also still fits. research_notes/pack-wire-te-2026-10-31.md |
| C04 | 28 AWG XL-ETFE wire, TE 55A0111-28-9 (sense + Kelvin leads)<br><sub>Raychem Spec 55 (= M22759/32-28), 7/36 tinned Cu, 0.64-0.74 mm OD, 150 C, white</sub> | 1 reel (100 m) | [Farnell UK / element14](https://uk.farnell.com/raychem-te-connectivity/55a0111-28-9/single-wire/dp/3236641) |  | **To order** |  | Logan 2026-10-31. GBP 71.35 per 100 m reel ex VAT at Farnell UK, 27 in stock (2026-10-31). Any M22759/32-28 (same wire, any maker) is a drop-in if a shorter cut turns up. Not M22759/11-28 (0.79-0.89 mm OD, too fat for the CELL2 channel). |
| C05 | Fish-paper insulator rings, 21700, adhesive<br><sub>0.2 mm; about 20 mm OD, 10-10.5 mm ID</sub> | 1 pack (330) | [Amazon (MatchWhiz)](https://www.amazon.com/MatchWhiz-Insulator-Highland-Electrical-Insulation/dp/B0CQJMXZSV) |  | **To order** |  | Check the listing photo for size; hole must clear the measured BAK + cap (< ~10 mm). |
| C06 | Back-cell NTCs (TS2, TS3)<br><sub>10 kOhm NTC, Semitec 103AT type, insulated leads</sub> | 12 | [DigiKey](https://azcus.digikey.com/en/products/detail/semitec-usa-corp/103AT-2/16579059) |  | **Decide** |  | Confirm 103AT matches the BQ40Z50 thermistor table before buying (parts list doc, Still to choose). |
| C07 | Gap filler: Parker Chomerics THERM-A-GAP GEL 30, 10 cc<br><sub>65-00-GEL30-0010; ~4.5 g per pack (3.1 g/cc)</sub> | 2 | [Newark](https://www.newark.com/search?st=65-00-GEL30-0010) | 104.42 | **To order** |  | Logan chose to stay on GEL 30 (2026-10-31). 30 cc is quote-only. Two syringes cover 5 packs plus rework. |
| C08 | Silicone foam sheet 1.6 mm, PSA (preload rings)<br><sub>USA Sealing ZUSA-FRS-HTPSA-125, FR closed-cell, 1/16 in x 12 x 12 in</sub> | 1 sheet | [Amazon (USA Sealing)](https://www.amazon.com/USA-Sealing-Retardant-Silicone-Adhesive/dp/B07CRV3NPF) |  | **To order** |  | Buy both sheets (cheap); pick 1.6 or 1 mm after measuring the cell gap (~30 % squeeze). |
| C09 | Silicone foam sheet 1 mm, PSA (preload rings)<br><sub>Generic 250 x 250 mm closed-cell silicone, 1MM option</sub> | 1 sheet | [Amazon](https://www.amazon.com/250X250MM-Adhesive-Silicone-Thickness-Silicon/dp/B0F93B4RX6) |  | **To order** |  | Firmness not listed: a punched ring should squeeze to 70 % by finger. |

### Housing

| ID | Item | Qty | Vendor | Cost (USD) | Status | Ordered | Notes |
|---|---|---|---|---|---|---|---|
| H01 | Fit coupons (print first)<br><sub>A seal-bore ladder, B1 cup mouth, B2 cap, C1 carrier, C2 rails: MJF PA12; C3 sleeves: TPU 95A</sub> | 1 set | [JLC3DP (TPU at home OK)](https://jlc3dp.com/3d-printing-quote) |  | **To order** |  | Files: hardware/mechanical/coupons/*.stl. Test the USB-C bores, O-ring squeeze, cap screws and rail clips before ordering H02-H05. |
| H02 | Cup<br><sub>MJF PA12 (black dye optional); 1.6 mm side walls, 2.0 board face, 1.85 top, 2.4 mouth</sub> | 5 | [JLC3DP](https://jlc3dp.com/3d-printing-quote) |  | Hold |  | hardware/mechanical/monolith_cup_cup.stl (PR #50 geometry, merged 2026-10-31). Hold until coupons pass. Order H02-H05 together for one powder batch. |
| H03 | Bottom cap<br><sub>MJF PA12</sub> | 5 | [JLC3DP](https://jlc3dp.com/3d-printing-quote) |  | Hold |  | hardware/mechanical/monolith_cup_cap.stl. Hold until coupons pass. |
| H04 | Cell carrier<br><sub>MJF PA12</sub> | 5 | [JLC3DP](https://jlc3dp.com/3d-printing-quote) |  | Hold |  | hardware/mechanical/monolith_cup_carrier.stl. Hold until coupons pass. |
| H05 | Board rail blocks (clip-on, with peg posts)<br><sub>MJF PA12</sub> | 20 | [JLC3DP](https://jlc3dp.com/3d-printing-quote) |  | Hold |  | hardware/mechanical/monolith_cup_rails.stl. Hold until coupons pass. |
| H06 | TPU parts: cap pad, 4 post sleeves, top + bottom bumpers<br><sub>TPU 95A FDM; bumpers one print each face-down, 5 walls, 4 top/bottom, 30 % gyroid; pad 10 % gyroid</sub> | 5 sets | [Home FDM or JLC3DP](https://jlc3dp.com/help/article/tpu) |  | Hold |  | monolith_cup_pad.stl, _sleeve.stl, _bumpt.stl, _bumpb.stl. Print after the coupons; the vent grille is part of the bottom bumper. |
| H07 | O-ring, 58 x 54 x 2 mm NBR, 10 pcs<br><sub>uxcell; 3.3 % stretch, ~24 % squeeze</sub> | 1 pack (10) | [Amazon (uxcell)](https://www.amazon.com/s?k=uxcell+58mm+x+54mm+x+2mm+nitrile+o-ring) |  | **To order** |  | Picked 2026-10-25. Not the 58 x 54.4 x 1.8 variant. Fallback: USA Sealing ZUSAS70FDA2X55 silicone (Zoro 11.39 / 10). |
| H08 | Cap screws M2 x 5 pan head, thread-forming for plastic<br><sub>18-8 stainless (A2), PT style</sub> | 20 | [McMaster-Carr](https://www.mcmaster.com/99461A914/) |  | **To order** |  | Length 5 mm per the model (SCREW_L in monolith_cup.py, 2.4 mm mouth since 2026-10-31); the parts list doc still says x 6. |
| H09 | O-ring grease<br><sub>Krytox GPL 205 (PFPE/PTFE; no silicone-oil grease)</sub> | 1 tube | [Silmid / any Krytox dealer](https://www.silmid.com/es/lubricants/greases/krytox-gpl-205-ptfe-thickened-grease-56gm-2oz-tube-nsf-registeredh1-food-compliant) |  | **To order** |  |  |
| H10 | Vent patch, 12 mm adhesive ePTFE (VOSAREA car-lamp vent, 100 sheets)<br><sub>Over the 3 mm cap hole, under the bottom bumper; fitted after the leak test</sub> | 1 pack (100) | [Amazon (VOSAREA)](https://www.amazon.com/s?k=VOSAREA+car+light+anti+fog+breathable+membrane) | 13.49 | **To order** |  | No IP rating: dunk-test the first pack. Paste the exact listing URL here once bought. |
| H11 | Vent fallback: Gore VE80308 (Takachi 8-pack)<br><sub>7.6 mm, IP67; same hole and pocket</sub> | 1 pack (8) | [Takachi](https://takachi-enclosure.com/products/VE8) |  | Hold |  | Only if the VOSAREA patch fails the dunk test. |
| H12 | Wrap label (vinyl sticker)<br><sub>Custom 7.91 x 2.87 in (201.0 x 72.85 mm), matte, custom cutline included</sub> | 25-30 | [StickerApp](https://stickerapp.com) |  | **To order** |  | Upload hardware/label/out/monolith_label_bl_stickerapp.pdf (re-exported for the 1.6 mm walls in PR #50). Measure thickness: the model clears ~0.17 mm. |

### Consumables

| ID | Item | Qty | Vendor | Cost (USD) | Status | Ordered | Notes |
|---|---|---|---|---|---|---|---|
| K01 | Conformal coat<br><sub>MG Chemicals 419D acrylic (solvent-removable)</sub> | 1 can | [Any (DigiKey, Amazon)](https://mgchemicals.com/downloads/tds/tds-419d-a.pdf) |  | **To order** |  | Mask the antenna end, Tag-Connect pads, gap-filler zone and USB-C rings. |
| K02 | Kapton tape<br><sub>Polyimide</sub> | 1 roll | Any |  | Check |  | Probably already on the bench. |
| K03 | Dispensing tips 14-16 ga tapered<br><sub>For GEL 30</sub> | 1 pack | Any |  | **To order** |  |  |
| K04 | Leak-detection fluid<br><sub>Or soapy water</sub> | 1 | Any |  | Check |  | Vacuum-jar bubble test, p0-assembly step 6. |

### Tools

| ID | Item | Qty | Vendor | Cost (USD) | Status | Ordered | Notes |
|---|---|---|---|---|---|---|---|
| T01 | AWithZ P20B spot welder with handheld pens<br><sub>14.6 kW, 1600 A</sub> | 1 | [AWithZ eBay store / diy500amp](https://www.ebay.com/str/awithz) | 255.00 | Check |  | About 255 on 2026-10-23. Mark Have if already bought. |
| T02 | Hollow punch 15 mm<br><sub>uxcell single punch</sub> | 1 | [Amazon (uxcell)](https://www.amazon.com/uxcell-Leather-Gasket-Strap-Hollow/dp/B01N4OJ2H6) |  | **To order** |  | Foam ring ID. |
| T03 | Hollow punch 20 mm<br><sub>uxcell single punch</sub> | 1 | [Amazon (uxcell)](https://www.amazon.com/uxcell-Leather-Gasket-Strap-Hollow/dp/B01MT9JVZ1) |  | **To order** |  | Foam ring OD (pocket is 21.4). |
| T04 | Vacuum jar + hand pump with gauge<br><sub>Readable to -50 kPa; food-vacuum or resin-degassing pot</sub> | 1 | [Best Buy Auto Equipment (Mityvac MV8255) / any](https://bestbuyautoequipment.com/Mityvac-MV8255-p/mitmv8255-03.htm) | 83.00 | **To order** |  | Pump suggestion; any pump with a gauge works. |
| T05 | 0.01 g scale<br><sub>For dosing ~2.3 g of gel per zone</sub> | 1 | Any |  | Check |  |  |
| T06 | Tag-Connect TC2030-IDC-NL (+ TC2030-CLIP)<br><sub>One cable for J301 SWD and J302 gauge</sub> | 1 | [DigiKey](https://www.digikey.com/en/products/result?keywords=TC2030-IDC-NL) |  | Check |  | p0-bringup-and-training.md lists it as part of the bring-up kit. |
| T07 | EV2400 (clone) and XDS110 (LP-MSPM0G3519 LaunchPad)<br><sub>Gauge setup and CC2340 flashing</sub> | 1 each | Have |  | Have |  | Already in the bring-up kit. |

<!-- tracker:end -->
