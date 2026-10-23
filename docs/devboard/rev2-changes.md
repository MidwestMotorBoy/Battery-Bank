# Monolith dev board — rev 2.0 change list

_Started 2026-10-12. Rev 1 (`hardware/DevBoard/`) is placed but not routed, ordered or built._

**2026-10-18: the dev board will not be built.** These items now feed the production board (`hardware/Production/`); the bring-up checks below move to production P0 (`docs/production/p0-bringup-and-training.md`).

Changes to make in the next revision of the dev board. Add items as rev 1 is routed, built and tested; mark each one done when it is in the rev 2 schematic and layout.

## Requested

### 1. More battery temperature sensors
- **Why:** rev 1 measures cell temperature with a single 10 kΩ 103AT NTC on two wires (J102), taped to one cell at mid-height, on the BQ40Z50-R2's TS1. One sensor can miss a hot cell.
- **Starting point:** the gauge has three more thermistor inputs, TS2–TS4. In rev 1 they are tied to VSS and disabled in data flash. Wiring an NTC to each, with the internal 18 kΩ pull-up as on TS1, gives up to four cell sensors without another IC.
- **To decide:**
  - How many sensors: one per cell (TS1–TS4) or one per holder pair.
  - How they mount: wired NTCs taped to the cells, or SMD NTCs on the board under or beside each holder. Wired sensors read the cell itself; board-mounted ones read the holder area and are easier to assemble.
  - Connectors: one 2-pin header per sensor like J102, or one shared multi-pin header.
  - Firmware: enable TS2–TS4 in gauge data flash and include them in the 20 W thermal throttle and in the broken-sensor rule from `docs/project/monolith-next-actions.md` (since retired; the current thermal policy is in `docs/spec.md`).
  - Whether the welded-pack connector J101 needs extra pins so the real pack's thermistors can use the same inputs.
- **Status:** **done in rev 1 (rev A4, 2026-10-12)**: one wired 10k NTC per cell (TS1–TS4), each on its own 2-pin header (J102, J105–J107) beside the tap test point of the cell it watches. The welded pack's thermistors plug into the same headers, so J101 needs no extra pins. Firmware still to do: enable TS2–TS4 in data flash and use them in the throttle and broken-sensor rules.

### 1b. Second-level protection (decided 2026-10-13: hardware, BQ294700 + chemical fuse)
- **Why:** the BQ40Z50-R2 is the only per-cell protection. A protection FET failing short, a wrong data-flash setting or a dead gauge leaves per-cell overvoltage unguarded. TI's reference adds a bq294700-class secondary OVP that blows a 3-terminal chemical fuse (the gauge FUSE pin can blow it too; on rev 1 FUSE is tied to VSS).
- **Rev 1 decision (2026-10-12):** no hardware protector. The MCU cross-checks the gauge and can stop both chargers through CHG_INH (PB8 → each BQ25756 CE). That depends on firmware, which certification bodies usually only credit with software evaluation.
- **Decision (2026-10-12):** no hardware second-level protector or chemical fuse, for rev 2 or production. The second layer is software: the STM32 cross-checks the gauge (alive, read-back configuration, cell sum vs gauge stack vs charger VBAT ADC, FET stuck on) and stops charging through CHG_INH (review doc firmware item 12), backed by the charger's stack CV regulation and BAT_OVP, gauge hardware SCD/OLD and F101.
- **Consequences to keep in mind:** that layer only works while the MCU firmware runs, so it needs a hardware watchdog, a fail-safe boot path and test coverage of each check. Certification bodies usually credit software protection only after software evaluation (IEC 60730-1 Annex H / UL 1998 style); plan for that if the product is certified.
- **Reversed (2026-10-13):** hardware second level added in rev 1 after all: BQ294700 (4.35 V/cell OVP) and the gauge FUSE pin blow a TLC WSFB1514 chemical fuse (F102, 4-cell, 15 A) at the cell top; F102 replaces F101 as the pack fuse, TI fig. 9-11. A DNP bench bypass (R127) sits across it. Details: hardware/DevBoard/README.md item 33. The software checks above stay as a third layer.
- **Status:** done in the schematic (rev 1, branch hand-review); layout still to do.

### 1c. Production: short D+ to D− directly, drop R440/R540 (requested 2026-10-16)
- **Why:** R440/R540 are 0 Ω links that short D+ to D− at each USB-C port. The short is a passive BC1.2 dedicated-charging-port signature, so legacy devices on adapter cables draw full current. On the dev board the 0 Ω part is only there so it can be left unfitted (D+/D− open) during bring-up.
- **Change for production:** in `usb_port.kicad_sch`, delete R440 and wire D+ to D− as one net (e.g. `DPDN_DCP`); R540 goes with it because both ports come from the same sheet. Move R440's BC1.2 note onto the wire or the connector.
- **What it saves:** one placement per port. On the board, the connector's four interleaved D+/D− pins (B6, A7, A6, B7) all join with one short F.Cu link at the connector: no In2 hop and no via, which frees the crowded strip beside the connector for the CC/SBU links.
- **What it costs:** the open option. Cutting the short link at the connector restores it.
- **Keep on the dev board:** leave R440/R540 in rev 1 until bring-up confirms the DCP short behaves as intended with legacy devices.

### 1d. Shrink the board: find capacitors to remove, electrolytics first (requested 2026-10-17)
- **Why:** the board is too big. The bulk capacitors, the electrolytics above all, take the most area per part, so they come out first if bring-up shows they aren't needed.
- **Candidates, per port (port 2 = 5xx):**

  | Capacitors | Net | What they are |
  |---|---|---|
  | C421 (electrolytic) + C420/C423/C424/C427 (22 µF 1210) | AC_SNS_N/PPHV | charger input bank |
  | C432 (hybrid polymer) + C431/C434/C435 (22 µF 1206) | BAT_SNS_P | charger output bank |
  | C443 (electrolytic) + C441/C442 (22 µF 1206) | PP5V | 5 V buck output |
  | C444/C445 (10 µF 1206) | 5V_IN | 5 V buck input |

- **Limits to respect:**
  - **PP5V:** must keep enough bulk for USB PD's 120 µF source requirement (cSrcBulkShared; README item 44 counts about 136 µF now). An electrolytic can only come out if MLCCs make up that capacitance once DC-bias derating at 5 V is counted.
  - **Charger banks:** each must keep enough capacitance for the BQ25756's ripple and loop stability, and its MLCCs must stay within their ripple-current rating once the polymer is gone.
  - **PPHV:** the bulk also sets the inrush the TPS25751 soft-start limits (README note 9).
- **How to test (at bring-up, after the hot-loop and tuning-link checks):** at full load in each direction (forward charge and reverse 100 W), record these with the full banks fitted, then remove capacitors one at a time and repeat:
  - ripple on each rail;
  - the load-step transient;
  - charger stability;
  - MLCC temperature;
  - VBUS behaviour on attach and on a PD contract change.

  Electrolytics come off first, then MLCCs from the back row. Keep the smallest set that passes with margin, then design rev 2 for that set (also try fewer larger-value MLCCs, or one size up instead of a polymer).
- **Simulation results (2026-10-17, [cap-reduction-sims-2026-10-17.md](cap-reduction-sims-2026-10-17.md)):**
  - **Charger polymers C421/C432:** stay. They are the smallest way to meet the 80 µF rule.
  - **First try:**
    - C443/C543 → one 22 µF 1206. Blocked by the TPS25751's 120 µF cSrcBulkShared note until that is confirmed not to apply to a dedicated supply.
    - C435/C535 removed.
  - **Then, only if the polymer stays cool:** C427/C527 removed.
- **Then:** use the area saved to tighten the layout in rev 2, alongside the other cuts (dev-only test loops, measurement links, tuning links per the bring-up item below).

## Candidates found during rev 1 layout (confirm before adding)

These came up while placing rev 1 (2026-10-12). Any that are wanted could still go into rev 1 if done before routing and ordering.

### 2. A GND test loop in every probe field
- Rev 1 has one GND test point (TP203, by the sleep-current amps; rev A5 adds TP208/TP209 beside the amp outputs). Each port's probe field and the pack/system field have no ground loop nearby for a scope ground clip.
- Needs schematic changes (new TestPoint symbols on GND). The layout has room: the empty slot in each port's probe field.

### 3. Low-inductance probe points on the switch nodes
- SW1/SW2 test points are wire loops, so a scope ground lead adds inductance and shows ringing that isn't really there.
- Add a signal + GND pad pair spaced for a probe ground spring, or a DNP U.FL/MMCX footprint, at each switch node and at the BQ25756 input/output caps.

## Check after rev 1 bring-up
- **Q402 gate drive:** *(resolved in rev 1 by the 2026-10-14 cost-down: the legs are now discrete PGQ04N070 FETs, so every gate can face the BQ25756.)* With the half-bridge package it wasn't possible to make both FETs' gate pins face the BQ25756, so HG2/LG2 routed around or under Q402. Measure gate ringing on Q402 versus Q401. If it's worse, rearrange the port 2 side of the power stage in rev 2.
- **Hot loops:** measure switch-node ringing and overshoot on both half-bridges and the TPS62933 to confirm the HF cap placement.
- **Gate/bootstrap tuning links (decided 2026-10-16: keep for dev, revisit at bring-up):**
  - The links: R444–R447 (gate) and R448/R449 (BTST, high-side turn-on only), plus their 5xx copies. All are 0 Ω, and the R450/C454 and R451/C455 snubbers are DNP.
  - During the hot-loop measurements, fit the smallest value or snubber that tames any ringing.
  - Then, for production, replace every link still at 0 Ω with copper, as in item 1c.
