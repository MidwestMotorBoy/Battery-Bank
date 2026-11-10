# Ground-up layout experiment

An experimental, script-built re-layout of the Monolith P0 board.

**Which board is which (since 2026-11-10).** The experiment branch was merged to `master` in PR #66, and Logan
chose to keep it there. `hardware/Production/Monolith.kicad_pcb` on `master` is therefore the ground-up board
(after the second fix pass, commit dd34285). The approved, hand-routed board is the same file at commit
`8dd9eb6` (`git show 8dd9eb6:hardware/Production/Monolith.kicad_pcb`). In the tables below "current board
(master)" still means that hand-routed board, as it was when the comparison ran.

**Not yet redone for the ground-up board:** the order files in `../jlc/` (gerbers, BOM, CPL), the renders and layer
plots in `docs/hardware/`, the board reviews in `docs/reviews/`, the studies in `docs/analysis/` and the board data
in the mechanical model. All of them describe the hand-routed board. The ground-up board has been checked by script
and solver only; nobody has reviewed it in KiCad. Regenerate the order package and review the board before any order.

The schematic, project file, design rules, stack-up, outline, holes, USB-C connectors, wire pads, NTCs, antenna
module, the back-side parts and L401/L501 are unchanged, so the board drops into the same cup. Every other part was
placed again and all copper was drawn again.

The practices and the solver check loop that came out of this work are in the `pcb-layout` skill:
`.claude/skills/pcb-layout/references/solver-verified-layout.md`.

## Second fix pass (2026-11-10, evening)

The board is now the third version. The second pass took the four open items of the first fix pass
(commit ffb0dde): the charger feedback pins, four other signals over 10 mV per edge, the sense pairs, and the two
long tracks in the In4 ground plane. Three were closed and the fourth was tested and left.

| Check | Current board (master) | Ground-up, first version | After fix pass 1 | After fix pass 2 |
|---|---|---|---|---|
| DRC errors / unconnected / parity | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| DRC warnings | 16 | 20 | 23 | 22 (12 narrow connections, 9 silkscreen, 1 text height) |
| Vias / ground vias | 862 / 232 | 875 / 202 | 960 / 219 | 949 / 219 |
| Charger hot loops, four | 0.54 to 0.67 nH | 0.66 to 1.03 nH | 0.50 to 0.56 nH | 0.50 to 0.56 nH |
| Gate-drive loops, sum of eight | 49 nH (3.0 to 8.6) | 72 nH (5.0 to 14.1) | 44 nH (3.3 to 8.0) | 44 nH (3.3 to 8.0) |
| Coupling from all switch nodes into signals | 0.36 pF | 2.43 pF | 0.53 pF | 0.39 pF |
| Signals that take over 10 mV from one edge | 2 | 14 | 8 | 2 |
| Charger feedback pins, step per edge, port 1 / port 2 | under 0.1 / under 0.1 mV | 41 / 204 mV | 24 / 17 mV | 1.2 / under 0.1 mV |
| Area enclosed by the five sense pairs | 46 mm² | 74 mm² | 74 mm² | 29 mm² |
| Kelvin tap error, four charger resistors | within 0.58 % | within 1.18 % | within 1.04 % | within 0.95 % |
| Highest current in one via | 2.6 A, 0 over 3 A | 4.3 A, 8 over 3 A | 2.3 A, 0 over 3 A | 2.3 A, 0 over 3 A |
| Vias under the two gap-filler pads | 141 and 139 | 86 and 77 | 134 and 125 | 133 and 122 |
| PACK_P to the stage, port 1 / port 2 | 1.94 / 1.35 mΩ | 2.64 / 1.59 mΩ | 2.40 / 1.36 mΩ | 2.42 / 1.38 mΩ |
| Ground return, port 1 / port 2 | 1.60 / 1.53 mΩ | 1.91 / 1.80 mΩ | 1.44 / 1.30 mΩ | 1.42 / 1.27 mΩ |
| Copper loss at 100 W, half charge, port 1 / port 2 | 469 / 415 mW | 490 / 416 mW | 435 / 359 mW | 435 / 358 mW |
| Signal track cut into the ground planes | 34 mm | 0 mm | 258 mm | 258 mm |

What was done:

- Feedback pins: R418 moved 0.6 mm and its via 1 mm; R518 moved 5.1 mm towards U503 so the port 2 feedback net runs
  on F only, 8 mm, with no via. These are the only two parts that moved. Cup fit checked again: 0 failed checks.
- EN_5V1, port 1 I2CC_SCL, port 2 SBU_FLT and TS4: each was one via or a short stretch beside switching copper.
- Sense pairs: port 1 input pair as a stack (ACP_F on In2 over ACN_F on In3, 40 to 7.4 mm²), port 2 input pair with
  ACN_F on F following ACP_F on In2 (13 to 0.6 mm²), port 2 input minus tap from the other side of the pad
  (+1.04 to +0.95 %). The port 2 battery pair (10 mm²) and the gauge pair (6.5 mm²) could not be tightened without
  moving parts.
- EN_5V2 (78 mm) and SDA (56 mm) stay on In4. Their path is free on In3 for 60 and 45 mm (`lfree.py`), the rest is
  where nine east-west In3 tracks cross the centre column, and there is no legal via site between y 101 and 107
  (U506, C531 on F, C211 on B). The only complete signal-layer route runs through the port 1 charger stage and the
  2 mm gap that joins the two halves of the In2 PACK_P plane. An east-edge In4 route would be about 70 mm per net
  with a 14 to 17 mm east-west slot across the port 1 input return. In4 is unchanged: 258 mm, 28 crossing nets (the
  new one is port 1 ACN_F on In3, which also lies over the CHG_INT and PPHV tracks for 3.3 mm).

Two side effects, both found by the solvers in `compare/` and not by DRC, the open-connection check or the plane
check:

- A new ACN_F via at (106.05, 107.3) sat in a 0.85 mm neck of the B.Cu PACK_P bus. Port 1 PACK_P went from 2.6 to
  4.5 mΩ on the 0.05 mm grid; the 0.1 mm grid bridged the cut-out. Repaired in `hand3/s12.json` (no via, ACN_F stays
  on In3).
- The new EN_5V1 hop on In2 at U404 closed the last gap in the In2 PACK_P plane between U404's input vias and the
  vias of its bulk capacitor C444. The net stayed in one piece through other layers, so nothing flagged it; the
  hot-loop solver showed C444's loop going from 1.45 nH to not connected inside the solver box. Repaired in
  `hand3/s13.json` (hop on B.Cu); C444 is now at 0.95 nH and port 1 PACK_P at 2.42 mΩ.

Rules that follow: check new vias as well as new tracks against pour necks (`ml.py` and `vsite.py` treat plane pours
as free space); after every edit near power copper run `RES=0.05 python compare/k/pk.py` and the hot-loop solver and
compare the per-capacitor list with the run before; `piecepic.py` draws the pieces of a plane in different colours.
Do not start two `dk.sh` commands at the same time: the first to finish stops the Docker daemon of the other.

Hand specs and helpers of this pass are in `hand3/`: `s1` to `s6b` for the signals, `p1in_*` and `mk_pair.py` for
the port 1 input pair, `s9` to `s13` for the pairs and the two repairs, each applied with `step.sh`. Some steps in
between were one-off commands, so `hand3/` is a record and not a one-command rebuild; the board file is the
reference. New tools: `lfree.py` (where a track could change layer unchanged, and what blocks it), `piecepic.py`,
`netpath.py`, `zoomf.py`, `pathfill.py`, `seglib.py`, `cyd.py`, `ml.py --corridor`.
DRC report: `results/drc_groundup_fix2.json`. Picture: `results/layers_fix2.png`.

## First fix pass (2026-11-10, afternoon)

The first version (commit 6aaa778) lost the detailed comparison on everything that depends on where fast edges run.
A targeted fix pass reworked the gate drives, the 100 nF capacitors and vias at the pack-leg FETs, the layer-change
and gap-filler vias, and the slow signals that ran beside switching copper. That second version is commit ffb0dde. Same placement except four 0402 capacitors (C430, C438, C530, C538), so the cup fit is unchanged.

| Check | Current board (master) | Ground-up, first version | Ground-up, after the fix pass |
|---|---|---|---|
| DRC errors / unconnected / parity | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| DRC warnings | 16 | 20 | 23 (13 narrow connections, 9 silkscreen, 1 text height) |
| Vias / ground vias | 862 / 232 | 875 / 202 | 960 / 219 |
| Charger hot loops | 0.54 to 0.67 nH | 0.66 to 1.03 nH | 0.50 to 0.56 nH |
| Gate-drive loops, sum of eight | 49 nH | 72 nH | 44 nH |
| Coupling from switch nodes into signals | 0.36 pF | 2.43 pF | 0.53 pF |
| Signals over 10 mV per switch-node edge | 2 | 14 | 8 |
| Highest current in one via | 2.6 A | 4.3 A | 2.3 A |
| Vias under the two gap-filler pads | 141 and 139 | 86 and 77 | 134 and 125 |
| PACK_P to the stage, port 1 / port 2 | 1.94 / 1.35 mΩ | 2.64 / 1.59 mΩ | 2.40 / 1.36 mΩ |
| Ground return, port 1 / port 2 | 1.60 / 1.53 mΩ | 1.91 / 1.80 mΩ | 1.44 / 1.30 mΩ |
| Copper loss at 100 W, half charge, port 1 / port 2 | 469 / 415 mW | 490 / 416 mW | 435 / 359 mW |
| Minutes at 100 W before the derate, port 1 | 5.0 | 5.2 | 5.3 |
| Signal track cut into the ground planes | 34 mm | 0 mm | 258 mm |

What it cost: 258 mm of 0.15 to 0.2 mm signal track on In4 in six nets (EN_5V2 78.0, SDA 55.5, port 1 TS 44.9,
port 1 PPHV sense 36.7, port 1 CHG_INT 35.5, port 2 TS 7.0), mostly down the centre column between the two power
stages and only 8.9 mm of it within 3 mm of a board edge. 27 nets on In3 and B cross one of those slots (2 on the
current board). In1 has no track. `in4fig.py` and `in4cross.py` produce the picture and the crossing list.

Still behind the current board after this first pass (see the second pass above for what changed): six signals
besides the charger TS pins took over 10 mV per edge (EN_5V1 28,
port 1 I2CC_SCL 26, port 2 SBU_FLT 25, port 1 FB 24, TS4 23, port 2 FB 17 mV), the five sense pairs enclose 74 mm²
against 46 mm², the port 2 input sense tap reads +1.04 %, port 1 PACK_P is 2.40 against 1.94 mΩ, and three more vias
sit in 0402 pads. Weaknesses 1, 2 and 3 in the list below are reduced, not gone; the others are unchanged.

How the fix pass was built (all from the first version, `new/c11`): `build_e.sh` (lift, gate drives by
`hand2/gate.py`, capacitor moves, stage vias by `hand2/stagev.py`, layer-change vias by `viapick.py`), then the
router with `--avoid` (other nets pay to run near switching copper), then hand specs `hand2/*.json` applied one at a
time with `step.sh` (hand edit, full-rule DRC, plane-island check and copper dump in one go). `ml.py` searches a
legal link with exact clearances, `vsite.py` tests a via site, `gp.py` plans an In4 hop, `nearsw.py` lists victims
near switching copper, `at.py` and `zoom.py` show what is at a point. `dk.sh` starts a Docker daemon for one
command only.

Two lessons from this pass:

- The first fix board passed DRC, the open-connection check and the plane check with two real faults in it: three
  hand-drawn tracks cut the port 1 PACK_P bus (2.6 to 27.8 mΩ) and four added vias touched the battery sense taps
  (+2.2 and +2.7 %). Only the copper and Kelvin solvers in `compare/` showed them. Run those after every change in
  a power stage, not at the end.
- When the coupling solver flags a signal, run it again with `WHERE=<net suffix>`: it prints where on the victim
  the charge lands. Every hot spot here was a via beside switching copper, and moving that via 0.3 to 1 mm fixed it.

Pictures: `results/layers_fix.png` (F, In2, In3, In4, B). DRC report: `results/drc_groundup_fix.json`.

## Result of the first version (2026-11-10, commit 6aaa778)

| Check | Ground-up board | Current board (master) |
|---|---|---|
| KiCad DRC with the project rules | 0 errors, 0 unconnected, parity 0 | 0 errors, 0 unconnected, parity 0 |
| DRC warnings | 20 (10 narrow connections, 9 silkscreen, 1 text height) | 16 (15 silkscreen, 1 text height) |
| Cup fit, `board_checks()` in `monolith_cup.py` | 26 of 26 pass | 26 of 26 pass |
| Tracks / vias / track length | 5099 / 875 / 3733 mm | 2007 / 862 / 2609 mm |
| Summed copper loss of the 16 solver cases | 1.04 W | 0.99 W |

Copper resistance, same solver and cases as the 2026-10-30 review (`docs/reviews/2026-10-30-routed-board/tools/run2.py`),
port 1 / port 2 in milliohm:

| Path | Ground-up | Current |
|---|---|---|
| PACK_P, Q102 to battery sense resistor | 2.64 / 1.59 | 1.94 / 1.35 |
| CELL_P, fuse to Q101 | 1.48 | 1.30 |
| CELL_P_RAW, J112 to fuse | 0.16 | 0.25 |
| CELL_N, J108 to shunt | 0.20 | 0.32 |
| VBUS, connector to TPS25751 | 1.97 / 1.84 | 1.22 / 1.11 |
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

A detailed comparison (hot loops, gate loops, loss at each load, thermals, Kelvin taps, switch-node coupling) is in
`compare/README.md`.

## Known weaknesses of the first version

1. The In2 PACK_P plane and the In3 3V3 plane were cut into pieces by signal routes and are held together
   by link tracks (0.5 mm for the regulator feeds, 0.2 to 0.3 mm for 3V3). The In2 plane no longer shares
   current with the B.Cu PACK_P bus, which is why PACK_P is worse than on the current board.
2. The shunt's ground end (RS101 pad 2) has three vias, about 3 A each at 9 A. Signals routed under the pad
   leave no room for more. Ground resistance to the buck FETs is about 20 % higher than on the current board.
3. Inner layers are not Manhattan. The router was allowed any direction on In2 and In3, and most signal vias
   have no ground via beside them. The loop, coupling and thermal comparison in `compare/` shows the cost:
   gate loops 49 % more inductance, charger hot loops 20 to 60 % more, and 14 signals that take over 10 mV from
   a switch-node edge against 2 on the current board.
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
