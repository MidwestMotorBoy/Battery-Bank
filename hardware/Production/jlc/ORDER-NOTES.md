# Monolith P0: JLC order files (2026-10-30, from Logan's 22:41 save)

Files
- Monolith_gerbers_JLC.zip: 6 copper layers, mask, paste, silk, Edge.Cuts, PTH + NPTH Excellon (mm), job file. Inner files renamed (no spaces).
- Monolith_BOM_JLC.csv: 76 lines, 261 placed parts (Comment, Designator, Footprint, LCSC Part #, MPN, Qty). Test pads, wire pads and DNP parts (C314, R124, R126) left out.
- Monolith_CPL_JLC.csv: 261 parts, 249 top / 12 bottom (Designator, Mid X, Mid Y, Layer, Rotation).
- Top-only (Logan hand-solders the bottom, 2026-10-30): Monolith_BOM_JLC_top.csv + Monolith_CPL_JLC_top.csv (249 parts); bottom parts to buy and hand-solder: Monolith_bottom_hand_solder.csv.

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
