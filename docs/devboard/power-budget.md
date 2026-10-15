# Power budget by state (rev A8, 2026-10-14)

Values are datasheet typicals unless marked *est.* Conversions to pack current assume a 14.4 V pack (3.6 V/cell). The TPS62177 runs at about 72–75 % efficiency in sleep mode at these loads (its figs. 11/12, which already include its own quiescent current) and about 88 % in normal mode. The rev A7/A8 numbers were re-derived independently by two reviewers in schematic review 4 (D-3, A's challenge Q2).

| Datasheet | Figures used |
|---|---|
| bq40z50-r2 §7.5 | 336 µA NORMAL, 75 µA SLEEP, 1.6 µA SHUTDOWN |
| bq2947 (U102) | 1–2 µA, every state |
| bq25756 | IQ_BAT 17 µA (ADC off, at 28 V); 0.75 mA reverse-mode IQ |
| tps25751 | 56 µA sleep, 3–6 mA active |
| tpd4s201 (-Q1 §5.7) | VPWR 112 µA typ, 160 µA max, always on |
| tps62177 | 22 µA IQ, 4.8 µA sleep IQ (inside the sleep-mode efficiency curves) |
| tps62933 | 2 µA shutdown, 12 µA IQ |
| HT7550-1 | 2.5 µA typ, 4 µA max (only with JP202 fitted) |
| ina190 | 48 µA |
| m24512 | ≤ 2 µA standby |
| tmp1075 | 10 µA typ / 20 µA max continuous at the default rate; about 2.7 µA at the 220 ms rate; low µA in shutdown/one-shot |
| CC2340R5MODA (SWRS349A §7.9–7.10) | Standby 0.71 µA (RTC on, RAM kept); idle 1.2 mA; TX +8 dBm 10.7 mA; advertising average *est.* ≈ 15 µA at a slow interval |

## Where current is drawn

| Subsystem | Fed from | Measure it at |
|---|---|---|
| Gauge (BQ40Z50-R2) | Cells, via D101 → R105 → BAT | Drop across R105 (100 Ω): 50–340 µA = 5–34 mV |
| U102 (BQ294700) | Cells | Not separately (datasheet value) |
| 3.3 V rail: MCU, both TPS25751 + TPD4S201, TMP1075s, pull-ups | PACK_P → R201 (10 Ω) → TPS62177 | R201, through the INA190 outputs (TP201/TP202) |
| Chargers (2 × BQ25756), 5 V bucks (2 × TPS62933), polymer C432/C532 | PACK_P directly | Not separately (datasheet values) |
| Measurement section (HT7550-1 + 2 × INA190) | PACK_P via JP202 | Off unless the JP202 shunt is fitted |

## Pack current by state

| State | Gauge + U102 | Chargers ×2 | 5 V bucks ×2 | 3.3 V branch (R201) | **Total from the pack** |
|---|---|---|---|---|---|
| **Ship mode (S5)**: gauge SHUTDOWN, FETs off | 1.6 µA + 1–2 µA | 0 (PACK_P cut off) | 0 | 0 | **≈ 3–4 µA**; cell self-discharge dominates |
| **Idle, no cable (S2)**: MCU Standby, BLE advertising, TPS62177 in sleep mode, gauge SLEEP, TMP1075s in shutdown | 75 µA + 1–2 µA | 34 µA | 4 µA | ≈ 118 µA | **≈ 230 µA**: about 2.0 Ah/yr, about 3 %/month |
| Idle, TMP1075s left at their power-up default | | | | ≈ 128 µA | **≈ 240 µA** |
| Idle, everything at datasheet maximum | | | | | **≈ 290 µA** |
| Idle, polymer leakage (C432/C532, FETs on) | | | | | **+ up to 1 mA** at the datasheet limit (500 µA each); far less in practice. Measure at bring-up (review 4 B-4) |
| Idle, gauge not sleeping (`[IN_SYSTEM_SLEEP]` = 0) | 338 µA | 34 µA | 4 µA | ≈ 128 µA | **≈ 500 µA**: about 6 %/month |
| Idle, measurement section on (JP202 and JP201 fitted) | | | | | **+ ≈ 100 µA** |
| **Charging**, one port at 5.5 A | 336 µA | 17 µA idle port; the active one runs from USB | 4 µA | ≈ 3 mA *est.* | Pack **gains about 5.5 A**, minus about 3 mA |
| **Sourcing 100 W** at 20 V (BQ25756 reverse mode) | 336 µA | 0.75 mA | 4 µA | ≈ 3–4 mA *est.* | **6.3 A** at 16.8 V, **7.3 A** at 14.4 V, **8.8 A** at 12.0 V, **9.4 A** at the 2.8 V/cell cut-off |
| Sourcing 5 V 3 A (15 W, TPS62933) | 336 µA | 34 µA | 1 on (12 µA + load) | ≈ 3 mA *est.* | **≈ 1.2 A** at 14.4 V |
| Both ports, 80 W + 20 W | | | | | Same 100 W total: **≈ 7.3 A** nominal, 9.4 A at cut-off |

**Charging, from the USB side:** 5.5 A into a 16 V pack is about 88 W. At about 96 % efficiency that is about 4.6 A from a 20 V source, under the 5.6 A ILIM.

**Storage:** in idle the pack runs flat in months (about 3 %/month plus 1–2 %/month cell self-discharge). For storage the board goes to ship mode, and the gauge's Shutdown Voltage is set to 2700 mV so a forgotten pack stops at a safe cell voltage (review 4 S-1; `bringup-config-checklist.md`).

## 3.3 V rail

| Load | Idle (S2) | Active (cable attached) |
|---|---|---|
| 2 × TPD4S201 (CC/SBU protection, on each LDO_3V3) | **224 µA** (320 µA max). Always on: unpowered, it presents its dead-battery Rd, so the port could only sink | 224 µA |
| 2 × TPS25751 | 112 µA (56 each) | 3–6 mA each active (1 mA idle-attached) |
| 2 × M24512 EEPROM (on each LDO_3V3) | ≤ 4 µA | ≤ 4 µA |
| 3 × TMP1075 (U302–U304; U305/U306 DNP) | ≈ 3 µA in shutdown; 30 µA (60 max) at the power-up default | ≈ 8 µA at the 220 ms rate |
| CC2340R5MODA | ≈ 15 µA *est.* (Standby 0.71 µA plus advertising) | 1.2 mA idle; 10.7 mA TX at +8 dBm |
| Gauge SMBus pull-downs via the 3.3k pull-ups | 6.6 µA | 6.6 µA |
| R313 (220k) while DIO21 holds SLEEP low | 15 µA | 0 (DIO21 high) |
| CHG_INH (DIO24) | 0 (high) | 138 µA while charging (low) |
| Status LED (DIO12, high drive) | 0 (off) | ≈ 3.6 mA if on |
| IRQ_N pull-up (R314 47k) | 0 | 70 µA while any source asserts it |
| **Total at 3.3 V** | **≈ 380 µA** (≈ 410 µA with the TMP1075 default) | **≈ 10–20 mA** |
| **At PACK_LP, through R201** | **≈ 118 µA** (≈ 128 µA) | **≈ 3–6 mA** (R201 drops 30–60 mV) |

## Notes

- **The two TPD4S201s are the largest single block** (about 70 µA at the pack, nearly a third of idle). They keep both ports ready to detect a cable in either role. A lower-Iq CC/SBU protector, or a deeper idle that disarms the ports, is a production-board question, not a dev-board fix.
- **The gauge is the next block (75 µA asleep).** Confirm it sleeps at bring-up: across R105, about 7.5 mV means asleep and about 34 mV means awake.
- **BQ25756 IQ_BAT is specified at 28 V.** At 14.4 V it is likely a little lower.
- **The BLE advertising rate is still the biggest unknown on the MCU side.** At a 100 ms interval the CC2340 average is nearer 100 µA, which adds about 30 µA at the pack.
- **No single point measures total pack drain** (F102 is a fused part, not a jumper). Use R201 (3.3 V branch) plus R105 (gauge), plus about 38 µA for the chargers and bucks from the datasheets. The gauge's own current reading cannot resolve µA (±10 mA offset).
- **Sourcing at the 2.8 V/cell cut-off (9.4 A)** sets the 15 A rating of F102's fuse element and about 1 W per protection FET; the gauge's internal sensor watches them, with U306 as the DNP fallback.
