# Monolith P0: JLC order notes

**Order package for the script-built board, made 2026-11-14** from `../Monolith.kicad_pcb` on `master` (board and
schematic last changed in commit `dd34285`, PR #66; Logan chose this board as the design on 2026-11-13). Gerbers, drill,
position file, BOM and CPL all come from that one save, by [`make_package.sh`](make_package.sh). The package of the
earlier hand-routed board is history in [`../retired/jlc-hand-routed/`](../retired/jlc-hand-routed/ORDER-NOTES.md): do
not mix its files with these.

**Two things before you upload:**
1. **No person has reviewed this board in KiCad yet.** It is DRC clean and was checked by script and solver. If the
   review changes anything (or the cleaned-up board in open PR #68 is merged), rerun `make_package.sh`: it remakes every
   file from the new save in about a minute.
2. **Silkscreen on the board, left as it is (board edits are Logan's):**
   - The title text "Monolith Bat Bank / REV 1.0 / 10/30/26" (F.SilkS, left-justified at x 121.5, y 136.5) spans
     x 121.5 to 135.9 mm, but the board's right edge is at x 121.625. It is all off the board, so JLC will drop it or
     ask about it. Move it inboard (or delete it) and set the date.
   - "T3" and "T3R" overlap at J119/J120 (x 104.6 to 106.8, y 132.9 to 135.4), and "T3R" runs onto C115 pad 2.
   - B.SilkS "GEL 30 2.3 g" at both gap-filler zones: the dose is 1.9 g per zone now.
   - "P+" runs onto R126 pad 2; U301's pin-1 circle runs onto C315 pad 2; the U404 reference touches L402's outline;
     "T2R" is under the minimum text height. JLC clips silk off pads, so these only look untidy.

## Files

| File | What it is |
|---|---|
| `Monolith_gerbers_JLC.zip` | **Upload this to the PCB quote.** 6 copper layers, mask, paste, silk, Edge.Cuts, PTH and NPTH Excellon (mm), job file. Inner-layer files renamed with no spaces (`Monolith-In1_Cu.g1` ...). |
| `Monolith_BOM_JLC_top.csv` + `Monolith_CPL_JLC_top.csv` | **Upload these to the assembly step.** Top side only: 249 parts, 75 BOM lines. |
| `Monolith_BOM_JLC_top_simple.csv` | The same top BOM in JLC's four columns (Comment, Designator, Footprint, JLCPCB Part #), if the full one won't parse. |
| `Monolith_bottom_hand_solder.csv` | The 12 bottom parts Logan fits by hand (tracker L01-L03). |
| `Monolith_BOM_JLC.csv` + `Monolith_CPL_JLC.csv` | Both sides, 261 parts (249 top, 12 bottom), 76 BOM lines, for a both-sides quote. |
| `kicad-pos.csv` | kicad-cli's raw position file, the input to the CPL. |
| `make_package.sh`, `make_jlc_files.py` | Remake all of the above from the board (Docker, `kicad/kicad:10.0`). |

The BOM and CPL are built from the board's footprints: test pads, wire pads, holes, Tag-Connect pads and the DNP parts
(C314, R124, R126) are left out. The part list, values, footprints and LCSC codes are the same as the hand-routed
board's BOM, line for line. What changed is where the parts sit: 237 of the 261 parts moved and 154 turned.

## Hand-made fixes, now applied by the script

These live only in the order files, not in the board, so `make_jlc_files.py` adds them every time:
- **R412/R512 49.9k 1 % 0201:** LCSC C7343965. That code is Stackpole RMCF0201FT49K9
  ([LCSC](https://www.lcsc.com/product-detail/C7343965.html)), so the BOM now says that MPN. The old BOM paired it
  with the schematic's MPN, UNI-ROYAL 0201WMF4992TEE, which is a different part. The schematic still has no LCSC code
  for these two.
- **Rotation offsets** from Logan's JLC preview of 2026-10-30, added to each part's rotation (CPL rotation is CCW
  positive, so 90 deg CW = -90): -90 for U402/U502, U403/U503, U405/U505, U406/U506, Q101/Q102, U204; 180 for Q103,
  Q104, U404/U504, Q409/Q509. They depend on the footprint, not the layout, so they carry over.
- **F102 body shift:** JLC drew the body 0.65 mm toward pads 1/2. F102 is at 180 deg again, so Mid X is +0.65 mm, as before.

Still **check every part in JLC's placement preview**, because the positions and rotations are new: the QFNs, FETs, diodes, USB-C and fuse first.

## Before checkout

- [ ] **TVS2200 pin 1 (D401 / D501, Maxinmicro C55616459):** confirm in the preview that the pin-1 mark sits on pad 1, the GND side. At 180 deg the GND pins and EP land on VBUS: a VBUS-GND short on both ports. On this board both are at 0 deg (D501 was at 180 on the hand-routed board), so the two should now look the same in the preview.
- [ ] **L402/L502:** pick C49248023 (ABC EHE05023R3MFB) on that BOM line by hand if JLC doesn't match it (it didn't stick last time).
- [x] SiZ240DT (Q401/Q402/Q501/Q502) and TPS25751DREFR (U401/U501): pre-ordered at JLC by Logan (2026-11-07). Make sure the order draws on that stock.
- [ ] **Remarks:** fill and cap all 0.3 mm holes, including the **24** component holes inside the U401/U501 (8 each) and U405/U505 (4 each) exposed pads (a separate ComponentDrill tool in `Monolith-PTH.drl`, not vias; the board also has 949 vias, all 0.3 / 0.45 mm). Edge rails / fiducials on the two long sides only; no tabs on the USB-C edge (J401/J501 overhang it by 2.5 mm) or the bottom wire row. Solder the J401/J501 shell legs if possible (no paste aperture; Logan hand-solders them otherwise).
- R413/R513 stay 11.8k (Logan, 2026-11-07). U102 stays BQ294700 (4.35 V; gauge COV goes to 4.25 V).
- The 12 bottom parts stay hand-soldered (Logan, 2026-11-07); preheat the board for the 1210 MLCCs (p0-assembly step 0.0).

## Checks on this save (2026-11-14, KiCad 10.0.8)

- DRC with zones refilled: **0 errors, 0 unconnected, 0 schematic parity issues**. 22 warnings, the same as on
  2026-11-10: 12 narrow connections (thin pour necks at U401/U405/U505 ground pins, one PACK_P plane neck, width steps
  on CHG_G and port 1 ACN_F; `../groundup/README.md`), 9 silkscreen and 1 text height (listed above).
- ERC: **0 errors**, 17 known warnings (14 pin-to-pin, 3 off-grid ends).
- Fab rules in the board: 0.15 / 0.15 mm track and clearance, 0.3 mm via on a 0.45 mm pad, hole to hole 0.2 mm, and
  0.45 mm where either hole is a pad hole of 0.5 mm or more (`../Monolith.kicad_dru`). Drill sizes in the file: 0.3
  (vias and EP holes), 0.5 (USB-C shell slots), 0.8, 1.15, 1.5 mm plated; 0.99 and 2.2 x 2.6 mm unplated.
- Board outline 43.25 x 74.43 mm, the same as the hand-routed board.

## PCB options

- 6 layers, 43.25 x 74.43 mm, 1.6 mm, ENIG
- Outer copper 2 oz, inner 0.5 oz (matches the 2 oz DRC rules: 0.15/0.15, 0.3 mm vias)
- Via covering: epoxy filled and capped, so thermal vias in pads don't wick solder
- Any stackup is fine; no impedance control needed

## Assembly

- Top-side assembly only; bottom 12 parts hand-soldered (C208-C213, C421, C456, C521, C556, TH101, TH104). Paste: high temp SAC305.
- No LCSC part, consign or use global sourcing: L401/L501 Coilcraft XGL7030-332MEC, U301 TI CC2340R5MODAN0MHAR. These three lines have no LCSC code in the BOM on purpose.
- C421/C456/C521/C556 (KEMET T593V686M035APE070) are bottom-side, hand-soldered, bought from DigiKey or Mouser (tracker L02).
