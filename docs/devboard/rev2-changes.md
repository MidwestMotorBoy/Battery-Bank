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
- **Status:** open.

### 1b. Second-level protection for production (decision open)
- **Why:** the BQ40Z50-R2 is the only per-cell protection. A protection FET failing short, a wrong data-flash setting or a dead gauge leaves per-cell overvoltage unguarded. TI's reference adds a bq294700-class secondary OVP that blows a 3-terminal chemical fuse (the gauge FUSE pin can blow it too; on rev 1 FUSE is tied to VSS).
- **Rev 1 decision (2026-10-12):** no hardware protector. The MCU cross-checks the gauge and can stop both chargers through CHG_INH (PB8 → each BQ25756 CE). That depends on firmware, which certification bodies usually only credit with software evaluation.
- **To decide:** whether production needs the hardware secondary OVP + chemical fuse (depends on the certification path: IEC 62133-2 / IEC 62368-1 / UL 2056). If so, prototype it on rev 2 (fuse heater behind a DNP link until the setup is checked).
- **Status:** open.

## Candidates found during rev 1 layout (confirm before adding)

These came up while placing rev 1 (2026-10-12). Any that are wanted could still go into rev 1 if done before routing and ordering.

### 2. A GND test loop in every probe field
- Rev 1 has one GND test point (TP203, by the SMA connectors). Each port's probe field and the pack/system field have no ground loop nearby for a scope ground clip.
- Needs schematic changes (new TestPoint symbols on GND). The layout has room: the empty slot in each port's probe field.

### 3. Low-inductance probe points on the switch nodes
- SW1/SW2 test points are wire loops, so a scope ground lead adds inductance and shows ringing that isn't really there.
- Add a signal + GND pad pair spaced for a probe ground spring, or a DNP U.FL/MMCX footprint, at each switch node and at the BQ25756 input/output caps.

## Check after rev 1 bring-up
- **Q402 gate drive:** with the half-bridge package it isn't possible to make both FETs' gate pins face the BQ25756, so HG2/LG2 route around or under Q402. Measure gate ringing on Q402 versus Q401. If it's worse, rearrange the port 2 side of the power stage in rev 2.
- **Hot loops:** measure switch-node ringing and overshoot on both half-bridges and the TPS62933 to confirm the HF cap placement.
