# Power budget by state (rev A5, 2026-10-13)

Values are datasheet typicals unless marked *est.* Conversions to pack current assume a 14.4 V pack (3.6 V/cell) and the TPS62177 at about 80 % efficiency in sleep mode, about 88 % in normal mode.

| Datasheet | Figures used |
|---|---|
| bq40z50-r2 §7.5 | 336 µA NORMAL, 75 µA SLEEP, 1.6 µA SHUTDOWN |
| bq25756 | IQ_BAT 17 µA (ADC off, at 28 V); 0.75 mA reverse-mode IQ |
| tps25751 | 56 µA sleep, 3–6 mA active |
| tps62177 | 22 µA IQ, 4.8 µA sleep IQ |
| tps62933 | 2 µA shutdown, 12 µA IQ |
| tps709 | 1.4 µA |
| ina190 | 48 µA |
| m24512 | ≤ 2 µA standby |
| STM32WB15 | 2.3–4.5 mA run at 64 MHz; RX 4.5 mA, TX 5.2 mA |

## Where current is drawn

| Subsystem | Fed from | Measure it at |
|---|---|---|
| Gauge (BQ40Z50-R2) | Cells, via D101 → R105 → BAT | Drop across R105 (100 Ω): 50–340 µA = 5–34 mV |
| 3.3 V rail: MCU, both TPS25751, SMBus pull-ups | PACK_P → R201 (10 Ω) → TPS62177 | R201, through the INA190 outputs (TP201/TP202) |
| Chargers (2 × BQ25756), 5 V bucks (2 × TPS62933) | PACK_P directly | Not separately (datasheet values) |
| Measurement section (TPS70950 + 2 × INA190) | PACK_P via JP202 | Off unless the JP202 shunt is fitted |

## Pack current by state

| State | Gauge | Chargers ×2 | 5 V bucks ×2 | 3.3 V branch (R201) | **Total from the pack** |
|---|---|---|---|---|---|
| **Shipping**: gauge SHUTDOWN, FETs off | 1.6 µA | 0 (PACK_P cut off) | 0 | 0 | **≈ 2 µA**; cell self-discharge dominates |
| **Idle, no cable** (MCU Stop2, slow BLE, TPS62177 in sleep mode, gauge SLEEP) | 75 µA | 34 µA | 4 µA | ≈ 44 µA | **≈ 157 µA**: about 1.4 Ah/yr, about 2 %/month |
| Idle, gauge not sleeping (`[IN_SYSTEM_SLEEP]` = 0) | 336 µA | 34 µA | 4 µA | ≈ 44 µA | **≈ 420 µA**: about 5 %/month |
| Idle, measurement section on (JP202 and JP201 fitted) | | | | | **+ ≈ 100 µA** |
| **Charging**, one port at 5.5 A | 336 µA | 17 µA idle port; the active one runs from USB | 4 µA | ≈ 3 mA *est.* | Pack **gains about 5.5 A**, minus about 3 mA |
| **Sourcing 100 W** at 20 V (BQ25756 reverse mode) | 336 µA | 0.75 mA | 4 µA | ≈ 3–4 mA *est.* | **6.3 A** at 16.8 V, **7.3 A** at 14.4 V, **8.8 A** at 12.0 V, **9.4 A** at the 2.8 V/cell cut-off |
| Sourcing 5 V 3 A (15 W, TPS62933) | 336 µA | 34 µA | 1 on (12 µA + load) | ≈ 3 mA *est.* | **≈ 1.2 A** at 14.4 V |
| Both ports, 80 W + 20 W | | | | | Same 100 W total: **≈ 7.3 A** nominal, 9.4 A at cut-off |

**Charging, from the USB side:** 5.5 A into a 16 V pack is about 88 W. At about 96 % efficiency that is about 4.6 A from a 20 V source, under the 5.6 A ILIM.

## 3.3 V rail

| Load | Idle (Stop2) | Active (cable attached) |
|---|---|---|
| 2 × TPS25751 | 112 µA (56 each) | 3–6 mA each active (1 mA idle-attached) |
| 2 × M24512 EEPROM (on each LDO_3V3) | ≤ 4 µA | ≤ 4 µA |
| STM32WB1MMC | ≈ 15 µA *est.* (Stop2 about 2 µA plus advertising at about 1 s) | 2.3–4.5 mA run; radio 4.5 / 5.2 mA RX / TX |
| Gauge SMBus pull-downs via the 4.7k pull-ups | 6.6 µA | 6.6 µA |
| CHG_INH (PB8) | 0 (high) | 138 µA while charging (low) |
| NTC dividers (5 × 10k) | 0 | ≈ 825 µA during the ~1 ms sample |
| Status LED | 0 | ≈ 1 mA if on |
| IRQ/BTP pull-ups | 0 | 33 µA per line while asserted |
| **Total at 3.3 V** | **≈ 138 µA** | **≈ 8–15 mA** |
| **At PACK_LP, through R201** | **≈ 44 µA** | **≈ 2–4 mA** (R201 drops 20–40 mV) |

## Notes

- **The gauge is about half the idle budget.** Confirm it sleeps at bring-up: across R105, about 7.5 mV means asleep and about 34 mV means awake.
- **BQ25756 IQ_BAT is specified at 28 V.** At 14.4 V it is likely a little lower.
- **BLE advertising rate is the biggest unknown.** At a 100 ms interval the MCU average is nearer 100 µA, and the idle total rises to about 190 µA.
- **No single point measures total pack drain** now that F101 is placed. Use R201 (3.3 V branch) plus R105 (gauge), plus about 38 µA for the chargers and bucks from the datasheets. The gauge's own current reading cannot resolve µA (±10 mA offset).
- **Sourcing at the 2.8 V/cell cut-off (9.4 A)** sets F101's 15 A rating and about 1 W per protection FET, which TH305 watches.
