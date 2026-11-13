# Monolith P0: JLC order files (2026-10-30, from Logan's 22:41 save)

> **These files are for the hand-routed board, not for the board now on master (2026-11-10).** Since PR #66,
> `../Monolith.kicad_pcb` is the ground-up re-layout (`../groundup/README.md`). Every file in this folder was made from
> the hand-routed board (the same file at commit `8dd9eb6`) and is a matching set for that board. Do not mix the two:
> gerbers made from today's board with the CPL in this folder would place almost every part in the wrong spot. To order the
> ground-up board, regenerate gerbers, drill, BOM and CPL together, carry the hand-made BOM fixes below across, and check
> rotations in JLC's preview again. The ground-up board has not been reviewed in KiCad.

## Before checkout (2026-11-07 pre-order review, Logan's answers)

- [x] **Regenerate the gerber zip** after the two board edits approved on 2026-11-07: silk labels at the pack / NTC wire holes, and the new UART_TX trace (U301 pad 16 DIO18 to J301 pad 6). Done 2026-11-08 (PR #65, commit `36dad0c`): `Monolith_gerbers_JLC.zip` was regenerated from the save with the 14 F.SilkS hole labels, the UART_TX route and the two F.Cu corner GND fills (DRC 0 errors, 0 unconnected, 16 warnings). BOM and CPL files were not touched: no part or position changed, and they carry the hand-made fixes below. Do not regenerate them from the board: its footprint fields have the new TVS, bulk caps and inductor since the 2026-11-08 save, but not R412/R512's LCSC code, and the CPL rotation fixes exist only in these files.
- [ ] **TVS2200 pin 1 (D401 / D501, Maxinmicro C55616459):** confirm in JLC's placement preview that the pin-1 mark sits on pad 1, the GND side. The TVS swap (10-31) came after the 10-30 rotation check; at 180 deg the GND pins and EP land on VBUS, a VBUS-GND short on both ports.
- [x] SiZ240DT (Q401/Q402/Q501/Q502) and TPS25751DREFR (U401/U501): pre-ordered at JLC by Logan (2026-11-07).
- [ ] Remarks: fill and cap all 0.3 mm holes, including the 24 component holes inside the U401/U501 and U405/U505 exposed pads (separate ComponentDrill tool, not vias). Edge rails / fiducials added by JLC on the two long sides only; no tabs on the USB-C edge (J401/J501 overhang it by 2.5 mm) or the bottom wire row. Solder the J401/J501 shell legs if possible (no paste aperture; Logan hand-solders them otherwise).
- R413/R513 stay 11.8k (Logan, 2026-11-07). U102 stays BQ294700 (4.35 V; gauge COV goes to 4.25 V).
- The 12 bottom parts stay hand-soldered (Logan, 2026-11-07); preheat the board for the 1210 MLCCs (p0-assembly step 0.0).

Files
- Monolith_gerbers_JLC.zip: 6 copper layers, mask, paste, silk, Edge.Cuts, PTH + NPTH Excellon (mm), job file. Inner files renamed (no spaces). Regenerated 2026-11-08 (see above); this is the file to upload.
- kicad-pos.csv: the raw kicad-cli position file of the 2026-10-30 save, the input the CPL files were made from (part positions have not changed on the hand-routed board since). The loose `gerbers/` folder from the same save was removed on 2026-11-13: it was older than the zip (no 2026-11-08 silk labels, UART_TX route or corner fills) and had no drill files.
- Monolith_BOM_JLC.csv: 76 lines, 261 placed parts (Comment, Designator, Footprint, LCSC Part #, MPN, Qty). Test pads, wire pads and DNP parts (C314, R124, R126) left out.
- Monolith_CPL_JLC.csv: 261 parts, 249 top / 12 bottom (Designator, Mid X, Mid Y, Layer, Rotation).
- Top-only (Logan hand-solders the bottom, 2026-10-30): Monolith_BOM_JLC_top.csv + Monolith_CPL_JLC_top.csv (249 parts); bottom parts to buy and hand-solder: Monolith_bottom_hand_solder.csv.
- Monolith_BOM_JLC_top_simple.csv: the same 249 top parts in a four-column form (Comment, Designator, Footprint, JLCPCB Part #), without MPNs or Qty.

PCB options
- 6 layers, 43.25 x 74.43 mm, 1.6 mm, ENIG
- Outer copper 2 oz, inner 0.5 oz (matches the 2 oz DRC rules: 0.15/0.15, 0.3 mm vias)
- Via covering: epoxy filled and capped, so thermal vias in pads don't wick solder
- Any stackup is fine; no impedance control needed

Assembly
- Top-side assembly only; bottom 12 parts hand-soldered (C208-C213, C421, C456, C521, C556, TH101, TH104). Paste: high temp SAC305.
- No LCSC part, consign or use global sourcing: L401/L501 Coilcraft XGL7030-332MEC, U301 TI CC2340R5MODAN0MHAR
- R412/R512 49.9k 1% 0201: LCSC C7343965 (Stackpole RMCF0201FT49K9, ~400 in stock on 10-30), added in the JLC BOM only, not yet in the schematic
- Check every part's rotation and pin 1 in JLC's placement preview, mainly the QFNs, diodes, USB-C, FETs and the bottom side

Checks on this save: DRC 0 errors / 0 unconnected (warnings only: library path in the copy, silk, CELL1/J302 hole 0.37 mm); ERC 0 errors (17 known warnings); schematic and board match pin for pin; Kelvin taps unchanged (port 1 +0.7 / +0.4 %, port 2 +0.3 / 0.0 %).

Rotation fixes from Logan's JLC preview (23:10Z), applied to both CPL files (CW = -90, file rotation is CCW-positive):
- 90 deg CW: U402/U502, U403/U503, U405/U505, U406/U506, Q101/Q102, U204
- 180 deg: Q103 (23:20Z), Q104, U404/U504, Q409/Q509
- F102 Mid X +0.65 mm (23:34Z): JLC's body drew 0.65 mm toward pads 1/2.
