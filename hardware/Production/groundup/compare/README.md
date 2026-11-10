# Ground-up board against the current board: detailed comparison

Run on 2026-11-10. `base` is master's `Monolith.kicad_pcb`, `new` is the ground-up board on this branch. Every tool
reads the board from the `PCB` environment variable and tags its output with `TAG` (`base` or `new`), so both boards
go through the same code. Nothing here is measured.

## Result

| Topic | Current board | Ground-up board | Ahead |
|---|---|---|---|
| Charger hot loops, inductance seen by the FETs | 0.54 to 0.67 nH | 0.66 to 1.03 nH | current |
| Small buck hot loops (5 V port 1, 5 V port 2, 3.3 V) | 0.76 / 0.53 / 1.40 nH | 0.32 / 0.39 / 1.22 nH | ground-up |
| Gate-drive loops, sum of eight | 49 nH (3.0 to 8.6) | 72 nH (5.0 to 14.1) | current |
| Copper loss at 100 W, half charge, port 1 / port 2 | 469 / 415 mW | 490 / 416 mW | level |
| Copper loss at 15 W, port 1 | 48 mW | 37 mW | ground-up |
| Minutes at 100 W before the derate, port 1 | 5.0 | 5.2 | level |
| Hottest FET in a 100 W run, port 1 | 59.4 °C | 60.2 °C (61.7 °C without credit for extra copper cover) | level |
| Kelvin tap error, charger sense resistors | within 0.58 % | within 0.55 %, port 2 input +1.18 % | current |
| Kelvin tap error, gauge shunt | +1.47 % | +1.17 % | ground-up |
| Area enclosed by the five sense pairs | 46 mm² | 74 mm² | current |
| Highest current in one via (9 A battery side, 5 A USB side) | 2.6 A, none over 3 A | 4.3 A, 8 vias over 3 A | current |
| Switch-node copper capacitance, four charger nodes | 72 pF | 70 pF | level |
| Coupling from all switch nodes into listed signal nets | 0.36 pF | 2.4 pF | current |
| Signals that take over 10 mV from one switch-node edge | 2 (both charger TS pins) | 14 | current |

The ground-up board is level on everything that depends on the amount of copper and worse on everything that depends
on where fast edges run. Before it could be built it would need: the high-side gate drives re-routed beside their
switch-node returns (port 2 leg A runs 26 mm round the charger IC), signals moved away from the switch nodes (port 2
charger FB takes 204 mV, I2C up to 153 mV), the 100 nF capacitors and more vias closer to the pack-leg FETs, and more
vias under the gap-filler pads (86 and 77 against 141 and 139), and more vias where PACK_P, CELL_P and the ground
return change layer (3.2 to 4.3 A per via against 1.1 to 2.6 A).

## Files

| Step | Script | Output |
|---|---|---|
| Hot loops (3-D partial inductance, 0.3 mm cells) | `run_hot2.py` | `hot_<tag>.json` |
| Gate loops (0.15 mm cells, ground kept within 2 mm of the loop) | `run_gate3.py`, `gbox.py`, `gmerge.py` | `gate3_<tag>.json` |
| Gate-drive track statistics | `groute.py` | `groute_<tag>.json` |
| Kelvin taps (DC grid solver, 0.05 mm) | `k/kelvin.py` with `RES=0.05` | `k/r05_<tag>/kelvin_<tag>.json` |
| Sense-pair routing and enclosed area | `senspair.py` | `senspair_<tag>.json` |
| Path resistance and 2 mm loss tiles | `k/lossmap.py` | `k/cu_<tag>.json` |
| Loss at each load | `thermal/lossload.py` | `thermal/lossload.json` |
| Thermal runs (on the PC) | `thermal/run_cmp.py`, `thermal/analyze_cmp.py` | `thermal/summary_pc.json` |
| Copper cover and via counts | `custats.py` | `custats_<tag>.json` |
| Per-via current on every power path | `k/viacur.py` | `k/via_<tag>.json` |
| Time and tokens of the work, from the session logs | `worklog.py` | `worklog.json` |
| Field coupling (3-D electrostatic, 0.05 mm) | `coup.py`, `victims.py`, `coup_post.py` | `coup_<tag>.json`, `coup_sum_<tag>.json` |
| Pictures | `figs_cmp.py`, `cmap_fig.py`, `lossfig.py`; `kicad-cli pcb render` for `img/render_*.jpg` | `img/` |
| Page | `build_page.py` with `page_tpl.html`, `page_text.py`, `page_words.py` | one self-contained HTML |

`peec.py`, `loops.py`, `board.py`, `sx.py`, `run_all_defs.py` are the tools of the 2026-11-06 loop study; `k/solve.py`
and `k/run2.py` are the copper solver of the 2026-10-30 review.

## Notes on the method

- Hot loops include every capacitor between the loop's supply net and ground (within 6.1 mm of the IC for the small
  bucks) with its package inductance: 0.3 nH 0402, 0.5 nH 0805, 0.6 nH 1210, 1.5 nH tantalum.
- Gate loops keep ground copper only on the loop's own layer and the plane next to it. `gate3_<tag>_adj.json` holds
  that run for all loops. On the ground-up board this cut the ground return of the port 2 leg A low-side loop (the
  result was meaningless), so that one loop was solved on both boards with both ground planes kept (`BOTH=1`,
  `gate3b_<tag>.json`) and merged in by `gmerge.py`. The both-planes setting reads 5 to 15 % lower on the loops where
  both were run.
- Three ground-up gate loops were too large for memory at 0.15 mm and were solved at 0.175 or 0.2 mm (field `h`).
- Kelvin taps need the 0.05 mm grid. At 0.1 mm the grid bridges the 0.2 mm keep-out rings and reports errors of tens
  of percent that are not real.
- Coupling: the switch node and its bootstrap and high-side gate nets are driven together at 1 V, all other copper
  within 1.5 mm is grounded, and the charge on each net is its coupling capacitance. The step on a victim is
  swing × Cc / (Cc + Cnode), with Cnode = its capacitors + 4 pF per IC pin + 0.1 pF per mm of track + 2 pF. Part
  bodies and magnetic coupling are not in the model.
- Memory: the dense inductance matrix needs about 8 bytes × branches². Above roughly 27 000 branches a run is killed
  in a 14 GB container, and two large loops cannot run side by side.
