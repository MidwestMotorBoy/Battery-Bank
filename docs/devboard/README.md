# Dev board (MonolithDev) record

The dev board was the bench version of the circuit: 196 × 115 mm, about 430 parts, routed and fab-ready at rev A8, but **skipped on 2026-10-18 and never ordered** (confirmed for good on 2026-10-23). The production P0 board was derived from its schematic, so these files are the reviewed reference behind P0, not a description of it. For the current design, read [`docs/spec.md`](../spec.md); for P0's own changes, [`hardware/Production/README.md`](../../hardware/Production/README.md). The KiCad project and its change log are in [`hardware/DevBoard/`](../../hardware/DevBoard/README.md); the schematic PDF and board renders are in [`docs/hardware/`](../hardware/).

These are dated notes. They are kept as written: part numbers, cells, the MCU and the enclosure are the ones of their date (EVE 58E cells, STM32WB before rev A7, TMP1075 sensors before rev A8, PGQ04N070 charger FETs and XAL7030 inductors, potting, the top-cap tube). Where a note and `docs/spec.md` disagree, the spec wins.

## Still applies to P0 and firmware

| File | What it is | Use on P0 |
|---|---|---|
| [`power-budget.md`](power-budget.md) | Idle current by power state (rev A8) | Baseline for P0's idle current; P0 adds about 175 µA for the two TPD6S300s (`docs/spec.md`). |
| [`mcu-io-power-states.md`](mcu-io-power-states.md) | State of every CC2340 pin in every power state | P0 keeps the dev board pin map minus the LED and UART; firmware follows it. |
| [`cc2340-pin-budget.md`](cc2340-pin-budget.md) | CC2340R5MODA pin plan and the reasons for it | Cited by P0's `mcu.kicad_sch` and `tools/tidy_production.py`. |
| [`bringup-config-checklist.md`](bringup-config-checklist.md) | Every configuration item from the four reviews, in bring-up order | The configuration items carry over; P0's procedure is [`docs/production/p0-bringup-and-training.md`](../production/p0-bringup-and-training.md). |
| [`launchpad-cc2340-plan.md`](launchpad-cc2340-plan.md) | LP-EM-CC2340R53 LaunchPad test plan | The plan the firmware follows until P0 exists (`firmware/README.md`). |
| [`cap-reduction-sims-2026-10-17.md`](cap-reduction-sims-2026-10-17.md) | Charger and PP5V capacitor-bank simulations | P0's PP5V bulk capacitance follows its result (cited in `hardware/Production/README.md` and `tools/make_production.py`). |
| [`rev2-changes.md`](rev2-changes.md) | The rev 2 change list | Fed into P0 on 2026-10-18; P0's changes are logged in `hardware/Production/README.md`. |
| [`circuit-description.md`](circuit-description.md) | Plain-English design intent (draft 5, 2026-10-11) | Background on why the circuit is the way it is; values have moved on since. |

## History only

| File | What it is |
|---|---|
| [`schematic-review-2026-10-12.md`](schematic-review-2026-10-12.md) | Review 1, rev 1 schematic |
| [`schematic-review-2-2026-10-12.md`](schematic-review-2-2026-10-12.md) | Review 2, rev A4 deep pass. Per-reviewer findings and challenges in [`review2/`](review2/) |
| [`schematic-review-3-2026-10-14.md`](schematic-review-3-2026-10-14.md) | Review 3, rev A6 hand-review branch |
| [`schematic-review-4-2026-10-14.md`](schematic-review-4-2026-10-14.md) | Review 4, rev A7 team review. Brief, per-reviewer findings and challenges in [`review4/`](review4/) |
| [`cost-down-2026-10-14.md`](cost-down-2026-10-14.md) | JLC cost-down candidates for the dev board BOM |
| [`j301-swd-pinout.png`](j301-swd-pinout.png) | Pinout of the dev board's 10-pin 1.27 mm SWD header. P0's J301 is a TC2030-NL instead (`docs/production/p0-bringup-and-training.md`). |

The `schematic-review-*.md` files are the lead's verified summaries; the `review2/` and `review4/` files are the raw material they cite as sources, so both are kept.

**Review 4 inputs.** `review4/net.xml` is the KiCad netlist exported for the review on 2026-10-14; `review4/dump_netlist.py` turned it into `parts.txt` (one line per part) and `nets.txt` (one line per net), and `erc.txt` is the ERC of the same day. The findings cite these files by name and line, so they describe the rev A7 schematic, not the current one. The reviewers' `scratch-*/` folders (fetched datasheets, scripts, page renders) were never committed. Review 2's netlist dumps were not committed either, so its findings' references to `nets.txt`, `parts.txt` and `erc.rpt` point at the rev A4 schematic in git history.
