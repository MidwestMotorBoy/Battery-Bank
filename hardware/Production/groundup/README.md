# Ground-up layout experiment

An experimental, script-built re-layout of the Monolith P0 board. It exists only on the branch
`claude/project-thread-ploune`. `master` still holds the approved, hand-routed board, and nothing here
should be merged without a review.

On this branch `hardware/Production/Monolith.kicad_pcb` is the ground-up board. The schematic, project
file, design rules, stack-up, outline, holes, USB-C connectors, wire pads, NTCs, antenna module, the
back-side parts and L401/L501 are unchanged, so the board drops into the same cup. Every other part was
placed again and all copper was drawn again. `jlc/` still holds the fab files of master's board.

## Result (2026-11-10)

| Check | Ground-up board | Current board (master) |
|---|---|---|
| KiCad DRC with the project rules | 0 errors, 0 unconnected, parity 0 | 0 errors, 0 unconnected, parity 0 |
| DRC warnings | 20 (10 narrow connections, 9 silkscreen, 1 text height) | 16 (15 silkscreen, 1 text height) |
| Cup fit, `board_checks()` in `monolith_cup.py` | 26 of 26 pass | 26 of 26 pass |
| Tracks / vias / track length | 5099 / 875 / 3733 mm | 2007 / 862 / 2609 mm |
| Summed copper loss of the 16 solver cases | 1.03 W | 0.99 W |

Copper resistance, same solver and cases as the 2026-10-30 review (`docs/reviews/2026-10-30-routed-board/tools/run2.py`),
port 1 / port 2 in milliohm:

| Path | Ground-up | Current |
|---|---|---|
| PACK_P, Q102 to battery sense resistor | 2.64 / 1.59 | 1.94 / 1.35 |
| CELL_P, fuse to Q101 | 1.42 | 1.30 |
| CELL_P_RAW, J112 to fuse | 0.16 | 0.25 |
| CELL_N, J108 to shunt | 0.20 | 0.32 |
| VBUS, connector to TPS25751 | 1.96 / 1.84 | 1.22 / 1.11 |
| AC_SNS_N, sense resistor to Q401/Q501 | 0.96 / 0.85 | 2.88 / 2.65 |
| BAT_SNS_P, sense resistor to Q402/Q502 | 0.58 / 0.58 | 0.62 / 0.53 |
| PPHV, TPS25751 to sense resistor | 0.18 / 0.17 | 0.37 / 0.33 |
| GND, shunt to Q401/Q501 source | 1.91 / 1.80 | 1.60 / 1.53 |

So the experiment is level with the hand-routed board on loss, not better. Before signal routing the same
pours measured about 0.72 W. The difference went into plane fragmentation, see the first two caveats.

Routing discipline (`crr.py`, the checker from the pcb-layout skill), ground-up / current:
off-direction segments on In2 and In3 1478 / 366, tracks on the GND plane layers 0 / 16, non-GND zones on
the GND plane layers 0 / 3, via rows that slot a plane 65 / 52, signal vias with no GND via within 1 mm
301 / 43, outer-layer signal runs over 15 mm 12 / 1, parts inside the fan-out ring of dense ICs 94 / 134.

Pictures: `results/layers.png` (four routing layers), `results/render_top.png`.

## Known weaknesses

1. The In2 PACK_P plane and the In3 3V3 plane were cut into pieces by signal routes and are held together
   by link tracks (0.5 mm for the regulator feeds, 0.2 to 0.3 mm for 3V3). The In2 plane no longer shares
   current with the B.Cu PACK_P bus, which is why PACK_P is worse than on the current board.
2. The shunt's ground end (RS101 pad 2) has three vias, about 3 A each at 9 A. Signals routed under the pad
   leave no room for more. Ground resistance to the buck FETs is about 20 % higher than on the current board.
3. Inner layers are not Manhattan. The router was allowed any direction on In2 and In3, and most signal vias
   have no ground via beside them. No loop-area, EMC or thermal review has been done on this board.
4. Vias sit in pads at C409.1 (PPHV), U301.5, C549.2, RS101.2 and several ground pads.
5. Kelvin pairs were auto-routed and are not tightly paired. Port 1 FSW is 0.15 mm wide.
6. C449 and C549 are about 4 mm from the TPS25751 PPHV pins.
7. Port 1 REGN and HIDRV1 stay 0.2 mm wide on In2 around x 104 to 111, y 102 to 106, because wider tracks
   split the PACK_P plane there.
8. Two ground vias pass through the VBUS pours and the PACK_P bus (C507.2 and C416.2).
9. Silkscreen: 14 reference designators are hidden where no free spot was found.
10. The 10 narrow-connection warnings are thin pour necks at the U401/U405/U505 ground pins, one PACK_P plane
    neck, and width steps on CHG_G and port 1 ACN_F.

## How it was built

All scripts run with KiCad 10's Python inside the `kicad/kicad:10.0` Docker image (`kc` is the wrapper).

1. Placement: `place*.py`, `placelib.py`, `run.py` write `placement.json`; `apply_place.py` moves the parts.
   `mechcheck.py` re-poses the per-part meshes of `hardware/mechanical/board/monolith_board.npz` and runs
   `board_checks()`, so the cup fit is tested without a STEP export.
2. Old copper is stripped (`strip.py`), power pours, vias and Kelvin taps are drawn by `cu.py`, `copper.py`
   and `add_copper.py`.
3. Signals: `router.py`, an A* router on a 0.05 mm grid over F, In2, In3 and B (`route1n.sh`). It knows the
   0.25 mm high-current spacing rule, fine-pitch escapes and ground stitching (`--stitch`).
4. Plane connectivity: `isl.py` finds copper groups that are cut off from the main body of GND, 3V3 and
   PACK_P. KiCad only reports those as a zone-to-zone airwire. `isloop.sh` routes a link for each.
5. Hand fixes: `hand/*.json` applied with `handadd.py` (fixed copper ids in `hand/keepu.txt`), `lift.py`,
   `cpnet.py`, `movefp.py`. Helpers for tight spots: `viascan.py`, `viaok.py`, `placescan.py`, `zoom.py`.
6. Finishing: `dedupe.py`, `widen.sh` (power and gate-drive tracks toward their class width, backed off where
   DRC objects), `wreset.py`, `pinfix.py` (gauge pins), `silk.py`, then `drc.sh` in a clean project copy.

Things that cost time and are worth knowing before touching this again:

- DRC only applies `Monolith.kicad_dru` when the board file is called `Monolith.kicad_pcb` and sits beside
  its project file. pcbnew's Python only loads net classes when `<board>.kicad_pro` sits beside the board.
- Any new inner-layer route can split a plane. Run `isl.py` after every routing change.
- A track widened across a via of another net makes pcbnew re-net that via on the next load. `widen.py`
  now records the nets and puts them back.
- Removing a "dangling" track can remove a live route that has a short stub. Trim the stub instead.
- Ground vias have to exist before signal routing. Adding them afterwards displaces routes.
