# Protection FETs Q101/Q102: options for the BAK 65E short circuit

**Decision (2026-10-23):** Logan picked the BSC007N04LS6 for Q101/Q102. `docs/spec.md` carries it.

Written 2026-10-23. Stock and prices are LCSC's pages on that day (JLC pulls extended parts from LCSC; all of these are extended parts). Datasheet figures are from the makers' datasheets. The SOA and transient-thermal curves are graphs that could not be read from this session, so the temperature rises below come from a model, described at the end, and one graph check per part remains (see "Still to check").

## The problem

- Dead short at PACK_P with four 65E cells: about **375–400 A** (cells at the datasheet's ≤ 8 mΩ AC, about 40 mΩ for the rest of the loop). Lower-resistance FETs raise it slightly.
- The gauge clears it: tDETECT (a few µs at this overdrive, 15 µs assumed) plus the SCD1 delay (61 µs today), then the gate discharges through the 5.1 kΩ series resistor (TI's value; about 6 kΩ with the pin).
- Two stresses per FET:
  1. **Fully on** until the gate falls to the Miller plateau: I² × R for about 100–170 µs, in both Q101 and Q102.
  2. **Linear turn-off**, Q102 (DSG) only: while VDS climbs from 0 to 16.8 V, the loop resistance limits the current, so power peaks at about 1.8 kW (8.4 V, 210 A) and averages about 1.2 kW. The Miller time is Qgd divided by about 0.75 mA of gate current. Q101 just conducts through its body diode.
- Bigger dies help (1) and hurt (2), because their larger Qg and Qgd make the gauge's weak gate drive slower.

## Candidates (40 V, LCSC stock on 10-23)

| Part | Package | RDS(on) max at 10 V | Qg / Qgd | Pulse rating | LCSC stock | Price at 10+ |
| --- | --- | --- | --- | --- | --- | --- |
| Infineon BSZ018N04LS6 (current spec) | TSDSON-8 FL 3.3 × 3.3 | 1.8 mΩ | 31 / 3.8 nC | 633 A | **93** | $1.52 |
| **Infineon BSC007N04LS6** (C534274) | TDSON-8 FL 5 × 6 | **0.70 mΩ** | 94 / **11.2 nC** | 1524 A, EAS 674 mJ | 1,471 | $1.25 |
| **Toshiba TPHR8504PL,LQ** (C22388172) | SOP Advance 5 × 6 | 0.85 mΩ | 103 / 25 nC | **500 A for 100 µs**, EAS 336 mJ | **29,273** | **$0.79** |
| onsemi NTMFS5C410NLT1G (C348540) | SO-8FL 5 × 6 | 0.82 mΩ | 143 / 22 nC | 900 A for 10 µs | 3,954–11,028 (page disagrees) | $1.01 |
| TI CSD18510Q5B (C2876544) | VSON 5 × 6 | 0.96 mΩ | 118 / 21 nC | — | 813 | $1.20 |
| Infineon BSC014N04LS (C2760081) | TDSON-8 FL 5 × 6 | 1.4 mΩ | 61 / 9.8 nC | 820 A | 6,834 | from $0.40 |
| HUAYI HYG015N04LS1C2 (C2874970) | PDFN 5 × 6 | 1.7 mΩ | 59 / 8.5 nC | 600 A | 16,302 | $0.49 |

All are ±20 V gate, 175 °C (CSD18510Q5B is 150 °C). Also checked and dropped: NVMFS5C404NL (out of stock), TPH1R204PL (63 in stock), HYG011N04LS1C2 (298), BSC014N04LSI (750, $1.67), BSC010N04LS (9,232 in stock but 150 °C Tj).

## Results (per FET, SCD1 delay 61 µs, the 5.1 kΩ gate resistor kept)

| Part | Short current | Fully on: power × time | ΔTj fully on | Q102 linear turn-off | ΔTj in turn-off | Both FETs at 100 W |
| --- | --- | --- | --- | --- | --- | --- |
| BSZ018N04LS6 | 376 A | 331 W × 95 µs | ~65 K | 5 µs, 6 mJ | ~50 K | 0.23 W |
| **BSC007N04LS6** | 402 A | 147 W × 135 µs | **~14 K** | **15 µs, 17 mJ** | **~35 K** | **0.09 W** |
| TPHR8504PL | 398 A | 175 W × 127 µs | ~20 K | 33 µs, 38 mJ | ~60 K | 0.10 W |
| NTMFS5C410NL | 399 A | 169 W × 166 µs | ~23 K | 29 µs, 34 mJ | ~57 K | 0.09 W |
| CSD18510Q5B | 395 A | 195 W × 139 µs | ~27 K | 28 µs, 32 mJ | ~64 K | 0.11 W |
| BSC014N04LS | 385 A | 270 W × 111 µs | ~38 K | 13 µs, 15 mJ | ~53 K | 0.16 W |
| HYG015N04LS1C2 | 378 A | 316 W × 109 µs | ~64 K | 11 µs, 13 mJ | ~71 K | 0.20 W |

100 W loss uses 7.5 A of pack current (105 W from 14 V) and typical RDS(on) × 1.25 for warm parts; at 12 V the losses are 1.36× higher.

## Levers

- **A turn-off speed-up on Q102 only.** A PNP (MMBT3906, JLC basic) with its emitter on the gate and collector to PACK_P through Rc, with its base at the 5.1 kΩ node and a 1N4148WS bypass diode for turn-on. The gauge pin still sees TI's 5.1 kΩ. Sizing Rc for about a 6 µs Miller time (Rc ≈ 0.9 kΩ for the TPHR8504PL, 2.0 kΩ for the BSC007N04LS6) cuts the turn-off energy to about 7 mJ for every part. That brings the TPHR8504PL down to about 15 K + 26 K, and the BSC007N04LS6 to about 11 K + 22 K. At about 60 A/µs and an assumed 150 nH loop, the overshoot is about 9 V, so the peak is about 26 V and nothing avalanches. Do not make it faster than about 3 µs, or the loop inductance drives the FET into avalanche.
- **SCD1 delay 61 µs → 0 µs.** This removes 61 µs of full current, which roughly halves the fully-on heating for every part. tDETECT still filters short spikes. The risk is a nuisance trip, which the P0 test has to rule out. It is worth trying on P0, but no candidate needs it.
- **Paralleling.** Not worth it. A single 5 × 6 part beats two 3.3 × 3.3 parts on resistance, area and mass. In the linear turn-off, the FET with the lowest threshold takes most of the current, so sharing is poor exactly where it matters. Four BSZ018s also cannot be bought (93 in stock).

## Recommendation

**Infineon BSC007N04LS6 for Q101 and Q102, with the gate circuit unchanged.**
- It has the lowest RDS(on) on the list: about −0.14 W at 100 W against the BSZ018.
- It has the smallest Qgd of the sub-1 mΩ parts, so it is the only one that turns off in about 15 µs through TI's 5.1 kΩ without extra parts.
- Its short-circuit temperature rise is about half the BSZ018's.
- It is the same OptiMOS 6 family as the BSZ018, so it is fully characterised.
- 1,471 in stock is plenty for a few packs; at about $2.50 per board it costs about $0.50 less than the BSZ018.

**Runner-up: Toshiba TPHR8504PL with the Q102 PNP speed-up.** It has the deepest stock (29k), is the cheapest, and its datasheet explicitly rates 500 A for 100 µs. Without the speed-up, its 25 nC Qgd leaves about 33 µs in the linear region at about 1.2 kW. That is plausible, but it is the kind of stress where trench FETs fail below their Zth prediction, so pair it with the speed-up.

Package change: a 5 × 6 power-SO8 footprint (S 1–3, G 4, D 5–8 + tab) replaces the 3.3 × 3.3. It adds about 22 mm² and about 0.1 g per FET. The common drain makes Q101/Q102 a natural shared tab pour.

## Still to check

- Read Diagram 3 (SOA) of the chosen part: the point 8.4 V / 210 A must sit under the 10 µs line, and should sit near or under the 100 µs line. For the TPHR8504PL, this is Fig. 8.16.
- Read Diagram 4 (Zth) to replace the model figures.
- P0 controlled short test with a current probe on DSG gate, VDS and current, at 61 µs and then 0 µs.

## Model

The temperature rises are scaled from the BSZ018N04LS6's Zth (Infineon Diagram 4: about 0.2 K/W at 100 µs and 0.4 K/W at 250 µs, read earlier in this project). They scale ∝ √t below 100 µs and by die area relative to the BSZ018, estimated from RDS(on) max (older OptiMOS +20 %). RDS(on) hot = max × 1.3. The gate starts at about 13.5 V, the plateau is about 4.5 V at 400 A, and the gate path is about 6 kΩ. The linear-mode energy is VB² / (6 R) × t_Miller. Model script: `model.py` next to this file.
