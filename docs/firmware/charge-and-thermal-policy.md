# Charge and thermal policy (firmware notes)

How firmware applies the charge ramp and the discharge derate. The thresholds themselves live in [`docs/spec.md`](../spec.md) (Ports, charging and power policy) and are changed there; this file explains the structure, so it doesn't repeat the tables. The pack is four BAK N21700CX-65E cells in 4S1P, 91 Wh typical. The numbers come from the 3-D pack model in `research_notes/Pack thermal BAK 65E/` and must be retuned on P0.

_First written 2026-10-21 for the FEB 21700G cells; rewritten 2026-10-24 for the BAK 65E and the front-cell NTCs on the cans' hot stripe; 2026-10-28, front-cell NTCs moved onto the board; 2026-11-13, the remaining threshold values moved out to the spec. The FEB version is in the git history._

## 1. The cell's limits

BAK's datasheet (A/00, `datasheets/bak-n21700cx-65e.pdf`) gives only the outer charge and discharge limits (spec, Cells and pack). It has no temperature-stepped charge table (BAK supplies one on request).

- Until BAK's table arrives, firmware keeps the charge ramp from the FEB table, capped at the spec's charge ceiling.
- The app's fast-charge toggle stays for future packs, but firmware always clamps it to the cell's datasheet table.
- Discharge floor: the spec's per-cell floor, which sits above the datasheet's end voltage for cycle life.
- 100 W at an empty pack is well inside the cell's discharge rating, so the cell rating doesn't limit output in the normal temperature range. The comfort ramp and the board ramp do.

## 2. Principles

- **Linear ramps, not steps.** Every limit is a straight line from full to reduced across a temperature band, so power never jumps and the pack doesn't oscillate.
- **Ramps stay on or under the cell's table at every temperature.**
- **Act on the hottest sensor.** In the cup the board heats the two front cells. Their NTCs (TS1 on C1, TS4 on C4) are SMD parts on the board in a corner of the gap-filler zone (`research_notes/Pack thermal BAK 65E/smd-ntc.md`). They read above the hottest can point in the model and never below it (offsets in the spec), which is why the discharge ramp starts 2 K higher than it did with NTCs on the cans.
- **Layers:** hardware ceilings (no firmware) → gauge protections and charge algorithm → this firmware policy. Firmware is the smoothest and lowest layer; the others are backstops.
- **Lower the PD offer, don't sag the output.** Discharge limits are applied by re-advertising Source Capabilities so sinks renegotiate cleanly.

## 3. Charging

**Loop (once a second):** `ICHG_REG = min(gauge ChargingCurrent(), ramp(hottest cell), charge ceiling)`, written to each BQ25756 through its TPS25751 (`I2Cr`/`I2Cw`). With both ports sinking, split it so the sum stays under the ramp. The ramp is the charge table in the spec.

**Readback.** R413/R513 stay 11.8 kΩ (decided 2026-11-07, spec: Decided: the charge-ceiling resistor) with `EN_ICHG_PIN = 0`, so the register is the charger-level limit and a future cell is still a software change. The pin ceiling only applies if a watchdog reset or a power cycle restores `EN_ICHG_PIN = 1` with no host to rewrite it. Every second, and before releasing CHG_INH, read back `ICHG_REG`, `EN_ICHG_PIN` and `EN_CHG`. On a mismatch, rewrite the value or inhibit charging.

**Backstops:**
- The TPS25751 configuration loads a conservative `ICHG_REG` default (the spec's 5–15 °C band current) at power-up, before the MCU runs.
- CHG_INH is pulled up, so a reset, hang or blank MCU stops charging.
- Gauge JEITA ranges, OCC, OTC and UTC in data flash (spec, Battery management and protection).
- BQ25756 JEITA stays **off**: its NTC is on the FET copper, not the cells.

**Behaviour:**
- **Self-warming in the cold:** the board's heat warms cold cells up through the low-current bands of the ramp into the full-current band within tens of minutes. Don't fight it.
- **To explore on P0:** when warm, asking for less input (a lower PDO) may finish as fast with less heat, because the cells stay below the charge ramp.
- **Settings:** max SOC, a periodic 100 % balancing charge, "charge to 100 % once", trip mode, and an optional "longevity" charge to a lower voltage (defaults and ranges in the spec).
- Dual-port charging, pass-through and solar MPPT are listed in the spec.

## 4. Discharge: burst, then a sustainable level

The owner's approach: **don't cap the offer below 100 W; lower where the derate starts instead.** Two numbers matter:

- **Where the ramp starts** sets how long a burst lasts.
- **Where the ramp ends (the sustain power)** sets how warm the cells sit for the rest of the discharge.

The current values (retuned 2026-10-28 for the board NTCs), the model results and the variant worth trying on P0 are in the spec.

**Implementation:**
- `P_allow = min(full power, comfort_ramp(hottest cell), board_ramp(charger TS), low_voltage_limit(V_pack))`. The board ramp acts on each charger's TS NTC; the low-voltage limit gives less power as the pack empties, because the cells' resistance rises near empty.
- Re-advertise Source Caps when `P_allow` crosses a step; go **down** at once, go **up** only after some cooling and a hold time (hysteresis, so a laptop isn't renegotiated every second; step and hysteresis values in the spec).
- **Port sharing is a user setting.** In USB1 priority (the default), USB2 keeps a guaranteed minimum (a setting; range and default in the spec) and USB1 gets the rest. In Balanced, the port with the larger contract gives way first. The two contracts never add up to more than `P_allow`, even briefly: lower one before raising the other.
- Hardware backstops: the BQ25756's IBAT_REV and the gauge's OCD1, OCD2 and OTD (values in the spec).

## 5. Sensors and timing

- **Inputs:** the gauge's `DAStatus2` (TS1–TS4, FET temperature, die), each charger's `TS_ADC` (FET copper, read through the TPS25751), and pack voltage. There are no TMP1075 board sensors on P0.
- **Poll once a second** (planned in `docs/devboard/mcu-io-power-states.md`). The board reacts in about 1 min and the cells in 5–10 min, so 1 s is plenty.
- **Don't poll a charger's ADC while its converter is off.** It powers REGN, and with it the 9 V gate-drive LDO's enable (`research_notes/Loss reduction/summary.md`).
- **9 V gate drive (fitted, default off):** turn it on only for large contracts and with PACK_P above the minimum in the spec (the LDO's EN may not sit above its input; spec, To do: Firmware). Configure TPS25751 GPIO6 as an output with initial value high (9 V off). Enable the converter, then `GPsl`; `GPsh` before disabling it, and on charge-done or a fault.

## 6. Open items

1. **BAK's temperature-stepped charge table:** ask BAK, then replace the FEB-derived ramp and revisit the charge ceiling.
2. **Measure the 65E's DC resistance** on P0 and refit the thermal model (method in the spec, Testing).
3. **Gauge chemistry ID** for the 65E (likely a GPCCHEM run).
4. **Tune the start temperature and sustain power** on P0 with real loads. Check TS1 / TS4 against thermocouples on the front cans' stripe, and move the discharge ramp if they differ from the model's offsets (the rule is in the spec).
