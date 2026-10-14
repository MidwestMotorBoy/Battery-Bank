# Monolith dev board — rev 2.0 change list

_Started 2026-10-12. Rev 1 (`DevBoard/`) is placed but not routed, ordered or built._

Changes to make in the next revision of the dev board. Add items as rev 1 is routed, built and tested; mark each one done when it is in the rev 2 schematic and layout.

## Requested

### 1. More battery temperature sensors
- **Why:** rev 1 measures cell temperature with a single 10 kΩ 103AT NTC on two wires (J102), taped to one cell at mid-height, on the BQ40Z50-R2's TS1. One sensor can miss a hot cell.
- **Starting point:** the gauge has three more thermistor inputs, TS2–TS4. In rev 1 they are tied to VSS and disabled in data flash. Wiring an NTC to each, with the internal 18 kΩ pull-up as on TS1, gives up to four cell sensors without another IC.
- **To decide:**
  - How many sensors: one per cell (TS1–TS4) or one per holder pair.
  - How they mount: wired NTCs taped to the cells, or SMD NTCs on the board under or beside each holder. Wired sensors read the cell itself; board-mounted ones read the holder area and are easier to assemble.
  - Connectors: one 2-pin header per sensor like J102, or one shared multi-pin header.
  - Firmware: enable TS2–TS4 in gauge data flash and include them in the 20 W thermal throttle and in the broken-sensor rule from `docs/project/monolith-next-actions.md`.
  - Whether the welded-pack connector J101 needs extra pins so the real pack's thermistors can use the same inputs.
- **Status:** **done in rev 1 (rev A4, 2026-10-12)**: one wired 10k NTC per cell (TS1–TS4), each on its own 2-pin header (J102, J105–J107) beside the tap test point of the cell it watches. The welded pack's thermistors plug into the same headers, so J101 needs no extra pins. Firmware still to do: enable TS2–TS4 in data flash and use them in the throttle and broken-sensor rules.

### 1b. Second-level protection (decided 2026-10-13: hardware, BQ294700 + chemical fuse)
- **Why:** the BQ40Z50-R2 is the only per-cell protection. A protection FET failing short, a wrong data-flash setting or a dead gauge leaves per-cell overvoltage unguarded. TI's reference adds a bq294700-class secondary OVP that blows a 3-terminal chemical fuse (the gauge FUSE pin can blow it too; on rev 1 FUSE is tied to VSS).
- **Rev 1 decision (2026-10-12):** no hardware protector. The MCU cross-checks the gauge and can stop both chargers through CHG_INH (PB8 → each BQ25756 CE). That depends on firmware, which certification bodies usually only credit with software evaluation.
- **Decision (2026-10-12):** no hardware second-level protector or chemical fuse, for rev 2 or production. The second layer is software: the STM32 cross-checks the gauge (alive, read-back configuration, cell sum vs gauge stack vs charger VBAT ADC, FET stuck on) and stops charging through CHG_INH (review doc firmware item 12), backed by the charger's stack CV regulation and BAT_OVP, gauge hardware SCD/OLD and F101.
- **Consequences to keep in mind:** that layer only works while the MCU firmware runs, so it needs a hardware watchdog, a fail-safe boot path and test coverage of each check. Certification bodies usually credit software protection only after software evaluation (IEC 60730-1 Annex H / UL 1998 style); plan for that if the product is certified.
- **Reversed (2026-10-13):** hardware second level added in rev 1 after all: BQ294700 (4.35 V/cell OVP) and the gauge FUSE pin blow a TLC WSFB1514 chemical fuse (F102, 4-cell, 15 A) at the cell top; F102 replaces F101 as the pack fuse, TI fig. 9-11. A DNP bench bypass (R127) sits across it. Details: DevBoard/README.md item 33. The software checks above stay as a third layer.
- **Status:** done in the schematic (rev 1, branch hand-review); layout still to do.

## Candidates found during rev 1 layout (confirm before adding)

These came up while placing rev 1 (2026-10-12). Any that are wanted could still go into rev 1 if done before routing and ordering.

### 2. A GND test loop in every probe field
- Rev 1 has one GND test point (TP203, by the sleep-current amps; rev A5 adds TP208/TP209 beside the amp outputs). Each port's probe field and the pack/system field have no ground loop nearby for a scope ground clip.
- Needs schematic changes (new TestPoint symbols on GND). The layout has room: the empty slot in each port's probe field.

### 3. Low-inductance probe points on the switch nodes
- SW1/SW2 test points are wire loops, so a scope ground lead adds inductance and shows ringing that isn't really there.
- Add a signal + GND pad pair spaced for a probe ground spring, or a DNP U.FL/MMCX footprint, at each switch node and at the BQ25756 input/output caps.

## Check after rev 1 bring-up
- **Q402 gate drive:** with the half-bridge package it isn't possible to make both FETs' gate pins face the BQ25756, so HG2/LG2 route around or under Q402. Measure gate ringing on Q402 versus Q401. If it's worse, rearrange the port 2 side of the power stage in rev 2.
- **Hot loops:** measure switch-node ringing and overshoot on both half-bridges and the TPS62933 to confirm the HF cap placement.
