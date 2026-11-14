# Monolith P0: JLC order notes

**There is no order package for the board yet (2026-11-13).** On 2026-11-13 Logan chose the script-built board as the
design: `../Monolith.kicad_pcb` on `master` (commit `dd34285`, PR #66, see [`../groundup/README.md`](../groundup/README.md)).
The gerbers, BOM and CPL that used to be in this folder were made from the hand-routed board (the same file at commit
`8dd9eb6`). They moved to [`../retired/jlc-hand-routed/`](../retired/jlc-hand-routed/ORDER-NOTES.md) and must not be
used with today's board: its parts sit in different places.

## To make the order package for the script-built board

1. **Review the board in KiCad first.** It is DRC clean (0 errors, 0 unconnected) and was checked by script and solver,
   but no person has reviewed it. If the cleaned-up version in open PR #68 is merged, make the package from that board.
2. **Make gerbers, drill, BOM and CPL together from one save** and keep them together in this folder
   (`.claude/skills/jlc-fab-files/SKILL.md` has the steps). A gerber zip from one save with a CPL from another is the
   mistake to avoid.
3. **Carry the hand-made fixes across.** They existed only in the old BOM and CPL files, not in the board:
   - R412/R512 49.9k 1 % 0201: LCSC C7343965 (Stackpole RMCF0201FT49K9), added in the JLC BOM only, not yet in the schematic.
   - Test pads, wire pads and the DNP parts (C314, R124, R126) are left out of the BOM and CPL.
   - Top-side assembly only: a top BOM and CPL, and a hand-solder list for the 12 bottom parts
     (C208-C213, C421, C456, C521, C556, TH101, TH104).
   - Rotation fixes from Logan's JLC preview of 2026-10-30, as offsets to each part's rotation in the CPL (CW = -90, file
     rotation is CCW-positive): 90 deg CW for U402/U502, U403/U503, U405/U505, U406/U506, Q101/Q102, U204; 180 deg for
     Q103, Q104, U404/U504, Q409/Q509. On the hand-routed board F102 also needed its body moved 0.65 mm toward pads 1/2.
     The footprints are the same, so the same fixes are expected, but most parts have a new position and rotation: check
     every one again in JLC's placement preview.
4. **Run the checks on that save:** DRC, ERC (0 errors and 17 known warnings on 2026-11-13) and schematic-to-board parity.

## Before checkout (2026-11-07 pre-order review, Logan's answers)

- [ ] **TVS2200 pin 1 (D401 / D501, Maxinmicro C55616459):** confirm in JLC's placement preview that the pin-1 mark sits on pad 1, the GND side. At 180 deg the GND pins and EP land on VBUS, a VBUS-GND short on both ports.
- [x] SiZ240DT (Q401/Q402/Q501/Q502) and TPS25751DREFR (U401/U501): pre-ordered at JLC by Logan (2026-11-07).
- [ ] Remarks: fill and cap all 0.3 mm holes, including the component holes inside the U401/U501 and U405/U505 exposed pads (24 on the hand-routed board, a separate ComponentDrill tool, not vias; count them again on the new save). Edge rails / fiducials added by JLC on the two long sides only; no tabs on the USB-C edge (J401/J501 overhang it by 2.5 mm) or the bottom wire row. Solder the J401/J501 shell legs if possible (no paste aperture; Logan hand-solders them otherwise).
- R413/R513 stay 11.8k (Logan, 2026-11-07). U102 stays BQ294700 (4.35 V; gauge COV goes to 4.25 V).
- The 12 bottom parts stay hand-soldered (Logan, 2026-11-07); preheat the board for the 1210 MLCCs (p0-assembly step 0.0).

## PCB options

- 6 layers, 43.25 x 74.43 mm, 1.6 mm, ENIG
- Outer copper 2 oz, inner 0.5 oz (matches the 2 oz DRC rules: 0.15/0.15, 0.3 mm vias)
- Via covering: epoxy filled and capped, so thermal vias in pads don't wick solder
- Any stackup is fine; no impedance control needed

## Assembly

- Top-side assembly only; bottom 12 parts hand-soldered (C208-C213, C421, C456, C521, C556, TH101, TH104). Paste: high temp SAC305.
- No LCSC part, consign or use global sourcing: L401/L501 Coilcraft XGL7030-332MEC, U301 TI CC2340R5MODAN0MHAR
- Check every part's rotation and pin 1 in JLC's placement preview, mainly the QFNs, diodes, USB-C, FETs and the bottom side
