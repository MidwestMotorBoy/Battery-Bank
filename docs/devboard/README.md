# Dev board (MonolithDev) record

The dev board was the bench version of the circuit: 196 × 115 mm, about 430 parts, routed and fab-ready at rev A8, but **skipped on 2026-10-18 and never ordered** (confirmed for good on 2026-10-23). The production P0 board was derived from its schematic, so these files are the reviewed reference behind P0, not a description of it. For the current design, read [`docs/spec.md`](../spec.md); for P0's own changes, `hardware/Production/README.md`.

Part numbers, cells, the MCU and the enclosure in these files are the ones of their date (EVE 58E cells, STM32WB before rev A7, TMP1075 sensors before rev A8, potting, the top-cap tube).

**Still useful for P0 and firmware:**

- [`power-budget.md`](power-budget.md): idle current by state (P0 adds about 175 µA for the two TPD6S300s).
- [`mcu-io-power-states.md`](mcu-io-power-states.md): the state of every CC2340 pin in every power state.
- [`bringup-config-checklist.md`](bringup-config-checklist.md): every configuration item from the four reviews. P0's procedure is [`docs/production/p0-bringup-and-training.md`](../production/p0-bringup-and-training.md).
- [`cc2340-pin-budget.md`](cc2340-pin-budget.md) and [`circuit-description.md`](circuit-description.md): why the circuit is the way it is.
- [`launchpad-cc2340-plan.md`](launchpad-cc2340-plan.md): the LaunchPad test plan the firmware follows.

**History:** the four schematic reviews (`schematic-review-*.md`, with the reviewers' working files in `review2/` and `review4/`), the rev 2 change list (`rev2-changes.md`, now fed into P0), the cost-down (`cost-down-2026-10-14.md`) and the capacitor simulations (`cap-reduction-sims-2026-10-17.md`).
