# Charge and thermal policy (firmware notes)

How firmware applies the charge ramp and the discharge derate. The thresholds themselves live in [`docs/spec.md`](../spec.md) (Ports, charging and power policy) and are changed there; this file explains the structure, so it doesn't repeat the tables. The pack is four BAK N21700CX-65E cells in 4S1P, 91 Wh typical. The numbers come from the 3-D pack model in `research_notes/Pack thermal BAK 65E/` and must be retuned on P0.

_First written 2026-10-21 for the FEB 21700G cells; rewritten 2026-10-24 for the BAK 65E and the front-cell NTCs on the cans' hot stripe; 2026-10-28, front-cell NTCs moved onto the board. The FEB version is in the git history._

## 1. The cell's limits

BAK's datasheet (A/00, `datasheets/bak-n21700cx-65e.pdf`) gives only the outer limits: charge to 4.20 V at 0–45 °C, up to 12.7 A (2C); discharge at −20–60 °C, up to 19.05 A (3C). It has no temperature-stepped charge table (BAK supplies one on request).

- Until BAK's table arrives, firmware keeps the charge ramp from the FEB table, capped at **4.55 A** (0.7C).
- The app's fast-charge toggle stays for future packs, but firmware always clamps it to the cell's datasheet table.
- Discharge floor: **2.8 V per cell** for life (the datasheet's end voltage is 2.5 V).
- 100 W at an 11.2 V pack is about 9 A, well inside the 19.05 A rating, so the cell's discharge rating no longer limits output below 60 °C. The comfort ramp and the board ramp do.

## 2. Principles

- **Linear ramps, not steps.** Every limit is a straight line from full to reduced across a temperature band, so power never jumps and the pack doesn't oscillate.
- **Ramps stay on or under the cell's table at every temperature.**
- **Act on the hottest sensor.** In the cup the board heats the two front cells. Their NTCs (TS1 on C1, TS4 on C4) are SMD parts on the board in a corner of the gap-filler zone (`research_notes/Pack thermal BAK 65E/smd-ntc.md`). They read 0.6–3.8 K above the hottest can point in the model and never below it, which is why the discharge ramp starts at 44 °C, not 42.
- **Layers:** hardware ceilings (no firmware) → gauge protections and charge algorithm → this firmware policy. Firmware is the smoothest and lowest layer; the others are backstops.
- **Lower the PD offer, don't sag the output.** Discharge limits are applied by re-advertising Source Capabilities so sinks renegotiate cleanly.

## 3. Charging

**Loop (once a second):** `ICHG_REG = min(gauge ChargingCurrent(), ramp(hottest cell), 4.55 A)`, written to each BQ25756 through its TPS25751 (`I2Cr`/`I2Cw`). With both ports sinking, split it so the sum stays under the ramp. The ramp is the charge table in the spec.

**Readback.** R_ICHG is 0 Ω (ICHG pin to PGND, `EN_ICHG_PIN = 0`), so the register is the only charger-level limit. Every second, and before releasing CHG_INH, read back `ICHG_REG`, `EN_ICHG_PIN` and `EN_CHG`. On a mismatch, rewrite the value or inhibit charging.

**Backstops:**
- The TPS25751 configuration loads `ICHG_REG = 3.25 A` at power-up, before the MCU runs.
- CHG_INH is pulled up, so a reset, hang or blank MCU stops charging.
- Gauge JEITA ranges in data flash (spec, Battery management), gauge OCC ≈ 5 A, OTC 45 °C, UTC 0 °C.
- BQ25756 JEITA stays **off**: its NTC is on the FET copper, not the cells.

**Behaviour:**
- **Self-warming in the cold:** the board's heat warms cold cells up through the 0.65 A and 3.25 A bands into the 4.55 A band within tens of minutes. Don't fight it.
- **To explore on P0:** when warm, asking for less input (e.g. a 60 W PDO) may finish as fast with less heat, because the cells stay below the charge ramp.
- **Settings:** max SOC (default 95 %, 60–100 %), a periodic 100 % balancing charge, "charge to 100 % once", trip mode, and an optional "longevity" charge to 4.10 V (about −10 % capacity, noticeably longer cycle life).
- Dual-port charging, pass-through and solar MPPT are listed in the spec.

## 4. Discharge: burst, then a sustainable level

The owner's approach: **don't cap the offer below 100 W; lower where the derate starts instead.** Two numbers matter:

- **Where the ramp starts** sets how long a burst lasts.
- **Where the ramp ends (the sustain power)** sets how warm the cells sit for the rest of the discharge.

The current values (100 W to 44 °C, then a ramp to 40 W at 48 °C, retuned 2026-10-28 for the board NTCs) and the model results are in the spec. A 46 → 50 °C ramp is worth trying on P0.

**Implementation:**
- `P_allow = min(100 W, comfort_ramp(hottest cell), board_ramp(charger TS), low_voltage_limit(V_pack))`. The board ramp is 55 → 70 °C on each charger's TS NTC; the low-voltage limit gives less power as the pack empties, because the cells' resistance rises near empty.
- Re-advertise Source Caps when `P_allow` crosses a 5 W step; go **down** at once, go **up** only after 2 K of cooling and ≥ 10 s (hysteresis, so a laptop isn't renegotiated every second).
- **Port sharing is a user setting.** In USB1 priority (the default), USB2 keeps a guaranteed minimum (10–30 W, default 20 W) and USB1 gets the rest. In Balanced, the port with the larger contract gives way first. The two contracts never add up to more than `P_allow`, even briefly: lower one before raising the other.
- Hardware backstops: IBAT_REV 10 A; gauge OCD1 ≈ 12 A, OCD2 ≈ 14 A, OTD 60 °C.

## 5. Sensors and timing

- **Inputs:** the gauge's `DAStatus2` (TS1–TS4, FET temperature, die), each charger's `TS_ADC` (FET copper, read through the TPS25751), and pack voltage. There are no TMP1075 board sensors on P0.
- **Poll once a second** (planned in `docs/devboard/mcu-io-power-states.md`). The board reacts in about 1 min and the cells in 5–10 min, so 1 s is plenty.
- **Don't poll a charger's ADC while its converter is off.** It powers REGN, and with it the 9 V gate-drive LDO's enable (`research_notes/Loss reduction/summary.md`).
- **9 V gate drive (fitted, default off):** turn it on only for contracts of 45 W or more and with PACK_P at 10 V or more (the LDO's EN may not sit above its input). Configure TPS25751 GPIO6 as an output with initial value high (9 V off). Enable the converter, then `GPsl`; `GPsh` before disabling it, and on charge-done or a fault.

## 6. Open items

1. **BAK's temperature-stepped charge table:** ask BAK, then replace the FEB-derived ramp and revisit the 4.55 A cap.
2. **Measure the 65E's DC resistance** on P0 (10 s pulse at 50 % and 10 % charge) and refit the model's 14 mΩ.
3. **Gauge chemistry ID** for the 65E (likely a GPCCHEM run).
4. **Tune the start temperature and sustain power** on P0 with real loads. Check TS1 / TS4 against thermocouples on the front cans' stripe, and move the discharge ramp if they read more than 1 K differently from the model's offsets.
