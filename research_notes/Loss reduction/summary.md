# Loss reduction — combined findings (2026-10-21)

Five researchers (A charger FETs, B frequency + inductor, C pack path, D cells + interconnect, E USB side, fixed losses, system), then a cross-examination round. Full reports: `A_charger_fets.md` … `E_usb_fixed_system.md`, each with a cross-examination section. All numbers are estimates from datasheets and the `heat_sources.py` model, not measurements.

## Recommended for P0 (keeping the EVE 58E cells)

| # | Change | 30 W | 100 W | 100 W, near-empty | 88 W charging | Cost / area / height | Gate on P0 |
|---|---|---|---|---|---|---|---|
| 1 | **Protection FETs Q101/Q102 → XNRUSEMI XRS120N04D (C50314144)**, 2.8 mΩ max at 10 V vs 6.0; same footprint | 0.03 | 0.45 | ~1.3 | 0.18 | +$0.14; none; −0.1 mm | Kelvin RDS(on); scope the SCD turn-off at the gauge's slowest gate fall |
| 2 | **9 V gate drive (DRV_SUP) from a TPS7A4101 LDO** per port; enable = REGN AND a per-port enable | 0 | 0.38–0.43 | ~1.0 | 0.22 | ~$1–2, 20–25 mm² per port; none | needs a per-port enable signal (no spare MCU pins: see below) |
| 3 | **Inductor → Coilcraft XGL7030-332MEC + 500 kHz (R412 40.2 k → 49.9 k)**; same footprint, 3.1 mm | 0.16 | 0.49 | ~0.85 | 0.26 | +$1.6 each, hand-supplied; none | inductor temperature, ripple, loop stability |
| 4 | **Nickel:** series strips 0.2 × 10 mm Ni; PACK tails 0.2 mm Cu with a Ni weld pad | 0.02 | 0.26 | 0.47 | 0.14 | a few grams | 4-wire joint resistance; weld quality on the thicker strip |
| | **Total** | **~0.2** | **~1.6** | **~3.6** | **~0.8** | | |

The board's share of the 100 W heat falls from ~5.5 W to ~4.2 W (≈ −24 %); the pack total from ~11.4 W to ~9.8 W.

**Config/firmware, no parts:** EN_PFM = 1 while sourcing (0.3–0.45 W per port at light/no load); route the 5 V PDO through the BQ25756 (TPS25751 reg 0x32, PDO 1 = PP_EXT; ~0.4 W at 15 W, needs a TI or bench check that the charger integration supports it); keep the default 20 V-first charging priority.

## Not recommended for P0
- **Molicel P60B (now P60C)** cells: the biggest lever on paper (−2.5 W at 100 W) but not buyable, its 12.8 mΩ is unverified, and it raises the short-circuit current to ~300–365 A, which forces BSZ018N04LS6 protection FETs, a ≤ 30 µs SCD delay and a fuse rethink. Design the cage to accept it for a later trial.
- **Splitting charger leg B** (BSZ018N04LS6 on the 100 %-on high side): a further −0.44 W at 100 W, but +0.2 W when charging from 9 V adapters, a leg re-layout, and only ~200 at JLC. Keep it as the fallback if P0 is heat-limited at 100 W.
- **TPS25751S with external CSD87501L path:** −0.30 W at 100 W, but TI hasn't confirmed charger integration in source mode and the FET is only 30 V under a 28 V clamp.
- **Lower sense resistors** (RAC/RBAT 2–3 mΩ): the TPS25751 writes limits scaled for 5 mΩ; TI fixes RBAT at 5 mΩ. **Lower shunt** (0.5 mΩ): worse gauge offset for 0.035 W. **Lower-resistance fuse:** ≤ 0.06 W, not at JLC.
- **Lower frequency alone** (300–400 kHz in a 3.1 mm body): the larger L brings more DCR and saturation; it loses. **Taller inductors:** 0.2–0.5 W more for a 1.8–2.9 mm thicker pack.

## Model corrections found
- F101 was deleted in rev A6; the remaining fuse F102 (TLC WSFB1514) is 1–3 mΩ, not 5.
- Nickel path ≈ 8.5 mΩ, not 5. Inductor ≈ 15 mΩ warm, not 12. Gate drive under-counted by ~0.1 W at 20 V.
- Near empty, the 58E's resistance is ~1.5× higher: 100 W from a ~10.3 A pack costs ~23.6 W, not 17. Firmware should throttle at low pack voltage.
- "9 V 3.3 A" isn't a legal PDO (9 V tops out at 27 W). The 5 V path (TPS62933 + 36 mΩ PP5V switch) loses ~1.3–1.8 W at 15 W and isn't modelled.
- Short-circuit current must use the cells' AC impedance over the 0.1–1 ms trip window: ~200 A with the 58E (XRS120N04D is fine), ~300–365 A with the P60B.

## Open issue: the DRV_SUP enable
TI (bq25756 §6.3.3.2, p.21): DRV_SUP must be off whenever the converter is disabled. REGN alone isn't enough, because the ADC powers REGN with the converter off (§6.3.7). Each port needs its own enable, and `docs/devboard/cc2340-pin-budget.md` says the CC2340 has no spare pins. **Resolved (2026-10-21): use each port's own TPS25751 GPIO, commanded over I2C, ANDed with REGN.** From the TPS25751 datasheet and TRM (SLVUCR8B):
- GPIO4, GPIO5 and GPIO6 are push-pull digital I/O (GPIO_VOH ≥ 2.9 V at 2 mA). Today they're tied to GND as unused; GPIO6 is the cleanest to free (GPIO4/5 double as USB D+/D− and liquid-detect pins).
- **No event matches "converter running".** `enablesource_port1` (73) is high only while sourcing a *high-power* contract (PDO > 1); `attachedassink` (75) is high while attached to a source, including after charge termination or a fault pause with the converter stopped. ORing them leaves both gaps.
- **'GPsh' / 'GPsl'** (TRM §4.6.5–4.6.6) set a GPIO high or low by I2C task, on a GPIO configured in AppConfig as "Output Enabled without Event" with an Initial Value. The MCU already talks to each TPS25751 over I2C, so this costs no MCU pins.
- **BQ25756 §6.3.3.2:** REGN is on only when VAC is OK with forward charge enabled, or in reverse mode with EN_REV = 1 (plus the ADC case in §6.3.7). So REGN is a good hardware proxy for "converter enabled".

**Circuit, per port** (one 2N7002-class N-FET, two resistors):
- TPS7A4101 EN pulled up to REGN through 100 kΩ, so the LDO can only run while REGN is up.
- N-FET drain on EN, source to GND, gate on TPS25751 GPIO6, with a 100 kΩ gate pull-up to the TPS25751's LDO_3V3. GPIO6 is configured active-low: Initial Value = high (LDO off at reset and while the GPIO is Hi-Z).
- Keep A's Schottky from REGN to DRV_SUP, so the converter still starts and runs on ~5 V gate drive whenever the LDO is off (dead battery, 5 V contracts).

**Firmware order:** enable the converter → 'GPsl' (LDO on). Before disabling a converter, or on its charge-done / fault interrupt → 'GPsh' (LDO off). Never poll the ADC on an idle port (E's rule). The REGN AND covers the case where firmware hangs with the converter off and the ADC idle.

**Residual gap:** autonomous charge termination keeps REGN up, so DRV_SUP stays biased until firmware sees charge-done and sends 'GPsh' (milliseconds to ~1 s). TI gives no timing for the rule; confirm on E2E or accept it and test on P0.
