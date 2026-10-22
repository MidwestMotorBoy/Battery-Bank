# Monolith dev board — schematic design review (rev 1)

_2026-10-12. Three reviewers split the board by sheet, then cross-examined each other: each challenged the other two reviewers' critical and major claims against the datasheets and netlist, and the authors defended or conceded. The lead re-checked the critical finding and arbitrated anything left in dispute. Everything below survived the challenge round. Datasheet sections are the printed section numbers in `datasheets/`._

Scope: `MonolithDev.kicad_sch` (root), `gauge.kicad_sch` (1xx), `power.kicad_sch` (2xx), `mcu.kicad_sch` (3xx), `usb_port.kicad_sch` (4xx and 5xx).
Inputs: netlist and ERC exported with kicad-cli 10.0, `bom.csv`, the datasheets, `circuit-description.md` and the README change list.

Methods used: pin-by-pin datasheet pass, net trace, ERC triage, power tree, worst-case and derating, power-state analysis, fault injection on paper, interface and I2C address check, BOM pass, testability.

## Summary

| Severity | Count |
|---|---|
| Critical | 1 |
| Major | 10 |
| Minor (schematic/BOM) | 22 |
| Firmware / configuration | 11 |
| Open questions | 7 |

The board is not routed yet, so every schematic and footprint fix below is still cheap.

## Status (rev A4, 2026-10-12)

Fixed in the schematic and board unless marked otherwise. Details are in hardware/DevBoard/README.md item 17.

| Item | Status |
|---|---|
| #1 U203 EN tied to PACK_P | **Fixed**: EN floats (internal pull-up). |
| #2 Charge ceiling | **Fixed**: R413/R513 = 9.1k 1 % → 5.5 A per port (revised from 17.8k / 2.8 A so one port can charge at about 1C). Both-port sum, watchdog behaviour and gauge OCC1 are configuration/firmware items (firmware item 14). |
| #3 Discharge-side overload | **F101 raised to 15 A** (1206FA-15A) so 100 W out at the 12 V low end (about 10 A) is within rating. Total-output sharing, gauge OLD and OCD1 are configuration/firmware items (firmware items 3 and 4). |
| #4 Holder contact resistance | Configuration and bring-up: holder mode ≈ 2 A, measure each holder. **Accepted** 2026-10-13: MYOUNG BH-21700-B1BJ001 (C20606791) stays for rev 1 despite its 100 mΩ maximum; high-current tests and learning cycles run on the welded pack (J101). |
| #5 U101 exposed pad | **Fixed**: TI RSM0032A footprint (1.4 mm pad). |
| #6 D± ESD vs GPIO4/5 | **Fixed**: D403/D503 → PESD5V0S2BT. No OVP switch for a D±-to-20 V short. |
| #7 Open or reversed cell | **Fixed in hardware**: R101–R104 1206, J101 DNP. F101 was DNP (hand-fit after checking the cells) until rev A5; now JLC-placed, and the check comes before waking the gauge (protection FETs off until FET_EN), see README item 25. Firmware gating and VIMR/VIMA are configuration items. |
| #8 DSG inrush | **Fixed**: DNP C109 (gate→GND) + D102 (across R111). Fit at bring-up if SCD trips. |
| #9 EV2400 with 3V3 dead | **Fixed**: pull-ups on SMB_PU via R312 0R, plus TP308. Also J104 bench PACK_P header. |
| #10 BTP_INT → PA6 | **Fixed**: Q103 2N7002 buffer; GAUGE_BTP is now active low. |
| #11 U301 MPN | **Fixed**: STM32WB1MMCH6TR, C5456183. Stock still to be checked. |
| m1 Q102 VGS | **Fixed**: DNP D103 15 V clamp. |
| m2, m3, m4, m7, m9, m12, m14, m15, m16, m17, m19, m20 | **Fixed** (values, footprints, parts as listed). |
| m5 SMAJ22A clamp | Not changed: TVS2200 has no LCSC/JLC stock; SMAJ22A meets TPS25751 footnote 4. |
| m6 Edge SMA on 0.8 mm board | **Fixed**: vertical SMAs; later replaced by test loops TP201/TP202 + GND TP208/TP209 (rev A5). |
| m8 TS1 NTC protection | Sheet note: tape the NTC to BT101. |
| m10 J101 + holders | **Fixed**: J101 DNP. |
| m11 TP102 | **Fixed**: "not GND" silkscreen. |
| m13 R430/R530 | Not changed (copper net ties). |
| m18 GPIO11 mapping | Configuration. |
| m21 BOM gaps | **Fixed** for the listed parts. Most generic passives still have no LCSC number. |
| m22 FSW / output C | Not changed: verify at bring-up. |
| Firmware items 1–11 | Open: TPS25751/gauge configuration and STM32 firmware. The DBfg step is now in docs/project/tps25751-eeprom-programming.md. |
| Q3 wake from SHUTDOWN | **Fixed**: SW101 wake button + J104. |
| Missed by the review: BQ25756 bootstrap diodes | **Fixed** 2026-10-12: TI's BQ25756 schematic checklist marks D2/D3 (DRV_SUP → BTST1/BTST2 Schottky) as required; the review accepted the datasheet pin table, which only names the capacitor. D404/D405 per port, LRB521S-40T1G. |
| Missed by the review: ESD caps across the FET pair | **Fixed** 2026-10-12: TI fig. 9-2 C1/C2 (two 0.1 µF in series, CELL_P to PACK_P) were missing; only the PACK+/PACK− pair (C107/C108) was drawn. Added C110/C111. |
| Q1, Q2, Q4–Q7 | Decided (see "Decisions on the open questions"): Q5 fixed (J103 EV2400 order), Q2 → CHG_INH line added, others configuration/documentation. |

---

## Critical

### 1. U203 TPS70950: EN is tied to IN, which is PACK_P (up to 16.8 V)
- **Refs:** U203 pin 1 (IN) and pin 3 (EN), both on `/Sleep Current and 3V3/LDO_IN`. That net is connected to PACK_P through JP202, with no series resistor.
- **Evidence (tps709):**
  - §6.1 gives VEN absolute maximum 7 V.
  - Table 5-1: "The maximum voltage must remain below 6.5 V".
  - §7.4: "Do not connect EN to VIN. The EN pin is clamped by a 6.5-V Zener diode … excessive current flowing into the Zener clamp will destroy the device."
- **Effect:** the first time JP202 is fitted, U203 is destroyed, and the INA190 supply goes with it.
- **Fix:** leave EN floating; it has an internal 300 nA pull-up and the datasheet allows this. Alternatively, drive it from a divider such as 1 M / 220 k.
- **Verified by:** C (found it), A, B, and the lead (netlist plus datasheet text).

## Major

### 2. Hardware charge-current limit is 9.4–10.2 A per port; the charger falls back to it on watchdog expiry
- **Refs:** R413/R513 (ICHG, 5.11 k), R414/R514 (ILIM_HIZ, 3.65 k), U403/U503.
- **Numbers:**
  - K_ICHG is 48–52 A·kΩ at 5 mΩ (bq25756 §5.5), which gives 9.4–10.2 A.
  - The input limit is 5.3–5.7 A. At 20 V input into a 12 V pack, that is about 8.7 A per port, or about 17 A with both ports.
- **Limits it exceeds:**
  - EVE 58E maximum charge current of 5.6 A.
  - F101 (8 A).
  - The holders: 100 mΩ contact resistance (see #4), no current rating.
  - The gauge's hardware trips with RS101 = 1 mΩ: SCC 22 A and OLD 8.3 A (bq40z50 §7.31). That leaves 5.6–22 A of charge current caught only by firmware OCC, which takes seconds.
- **Watchdog fallback:**
  - ICHG_REG is "Reset by: REG_RESET, WATCHDOG" (Table 6-10), and the watchdog defaults to 40 s.
  - If the TPS25751 stops servicing the charger, the limit returns to the pin setting.
  - VFB_REG does not reset on watchdog, so charge voltage is unaffected.
- **Fix:**
  - Raise R413/R513. About 17.8 k gives 2.8 A, which suits both ports charging and the holder current limit in #4. About 8.87–10 k gives 5.6–5.0 A for single-port, welded-pack-only use.
  - Configuration:
    - Set EN_CHG_BIT_RESET_BEHAVIOR = 0 (REG0x15 bit 3) so a watchdog expiry stops charging.
    - Set gauge OCC1 to 5.6 A or less with a short delay.
- **Rejected during challenge:** changing RS101 to 2–3 mΩ.
  - TI §9.2.2.1.4 says to use "the smallest value possible".
  - At 3 mΩ, an 85–170 A short puts 0.26–0.51 V on SRP/SRN, beyond the ±0.3 V absolute maximum.
  - RS101 stays at 1 mΩ.

### 3. USB sourcing can overload F101 on the discharge side
This is the discharge-side counterpart of #2.
- **Refs:** U403/U503 in reverse mode, TPS25751 source PDOs, F101, Q101/Q102.
- **Why:**
  - In reverse mode, the only hardware limit is ILIM_HIZ on the USB side: 5.5 A, about 110 W per port.
  - IBAT_REV is set by register only. It resets to 20 A and has 5 A steps (REG0x62).
- **Numbers:** two ports at 100 W from a 12 V pack draw about 17.5 A. One port draws about 8.8 A.
- **Limits it exceeds:** F101 (about 6 A continuous after derating), OLD (8.3 A minimum), and the holders.
- **Fix (configuration):**
  - Cap the total source PDOs at about 60–80 W.
  - Set IBAT_REV to 5 A on each port.
  - Set gauge OCD1 to about 6 A or less.
  - If 100 W sourcing is a goal, F101 and the holders need re-rating.

### 4. Holder contact resistance is up to 100 mΩ per holder
- **Evidence:** bh-21700-b1bj001.pdf note 2a, "CONTACT RESISTANCE: 100 MILLIOHMS MAX".
- **Effect:**
  - Worst case for the 4S stack is 0.4 Ω: 2 V drop and 10 W at 5 A, dissipated right at the cell terminals. The cells' surface limit is 60 °C.
  - The resistance sits at the spring-to-cell contact, behind the PCB tap, so the Kelvin taps can't exclude it. Each VC reading is off by up to ±I × 0.1 V per cell.
  - At 3 A charge, that is up to +0.3 V per cell: false COV near the end of constant-current charging.
  - At 3 A discharge, it is up to −0.3 V per cell: early CUV.
  - Impedance-track learning is distorted.
- **Fix:**
  - Limit holder-mode current to about 2 A, through the ICHG setting (#2), source PDOs (#3) and gauge thresholds.
  - Measure each holder's contact resistance at bring-up.
  - Run high-current tests and gauge learning cycles on the welded pack through J101 only.

### 5. U101 (BQ40Z50-R2) footprint exposed pad is 2.8 mm; the package pad is 1.4 mm
- **Refs:** U101, footprint `Package_DFN_QFN:VQFN-32-1EP_4x4mm_P0.4mm_EP2.8x2.8mm`. The footprint description cites tps25750.pdf, so it was made for a different TI part.
- **Evidence (bq40z50-r2.pdf, RSM0032A):**
  - The outline gives the thermal pad as "1.4 ±0.05". The "2X 2.8" dimension is the lead span (7 × 0.4).
  - The land pattern pad is "(1.4)".
  - The stencil is "(1.3)" with "86 % printed coverage" (1.3² / 1.4² = 0.86).
- **Effect:**
  - On the board, the footprint pad is 2.8 mm with four 1.13 mm paste windows, about 2.6 times TI's paste area.
  - That leaves 0.20 mm of copper (and about 0.24 mm of paste) between the pad and the lead tips.
  - The likely result is solder bridges from VSS to VC1–VC4, SRP/SRN or BAT.
- **Fix:** make a project footprint from TI's land pattern: 32 lands of 0.6 × 0.2 mm on a 3.8 mm span, a 1.4 mm pad and a 1.3 mm paste window.
- **Before redrawing:** all three reviewers worked from the PDF text, because no renderer was available. Spend a minute confirming on the drawing page itself; the text strongly supports 1.4 mm.

### 6. The D+/D− ESD part does not protect TPS25751 GPIO4/GPIO5
- **Refs:** D403/D503 (ESD2CAN24) on DP/DN, which go to U401/U501 pins 26/27. BC1.2 is intended (circuit-description §7.1).
- **Evidence:**
  - The GPIOx absolute maximum is 6.0 V (tps25751 §6.1.1).
  - The ESD2CAN24 breaks down at 25.5–35.5 V and clamps at 35 V at 16 A TLP.
  - So it neither clamps an ESD strike low enough for the GPIOs nor survives a D± short to 20 V VBUS. It is the right part for CC, which is rated to 26 V.
- **Fix:**
  - Use a ≤ 6 V low-capacitance ESD array on D± (TPD2E2U06 class).
  - For surviving a short to 20 V, add an OVP switch (TPD2S300 class).
  - If BC1.2 is dropped, tie GPIO4/5 to GND instead.

### 7. An open, missing or reversed cell drives current through the VC filter resistors and U101; and F101 can't be fitted after checking the cells
- **Refs:** BT101–BT104, R101–R104 (0603, 100 Ω), U101 VC1–VC4/VSS, F101.
- **Missing BT101:**
  - The load returns through VSS, U101's VSS-to-VC1 clamp and R101.
  - That is up to about 100 mA: about 1 W in an 0603 resistor, and twice U101's 50 mA ISS absolute maximum (§7.1).
- **Missing BT102–BT104:** the path is through two 100 Ω resistors, so at most about 55 mA, about 0.3 W per resistor.
- **Duration:** both cases last until the gauge's undervoltage trip (CUV) opens DSG, which is seconds.
- **Reversed BT101:**
  - 36 mA flows continuously, putting 0.13 W in R101.
  - The VC ADC range (−0.2 to 5 V) can't see a reversed cell.
  - USB charging would then reverse-charge it, which EVE §12.2.4 prohibits.
- **Procedure conflict:** the sheet note says "Check each cell at TP103–TP105 before fitting F101". But F101 is JLC-assembled (dnp no, LCSC C21261118), so the loads connect the moment the cells go in.
- **Fix:**
  - Make F101 removable (fuse clip or blade holder), or add a jumper or switch in series with CELL_P_RAW.
  - Use 1206 resistors for R101–R104.
  - Firmware: refuse EN_5Vx and charging unless all four cells read 2.5–4.25 V.
  - Enable the gauge's VIMR/VIMA cell-imbalance permanent-fail checks.

### 8. No inrush limit when DSG turns on into about 280 µF on PACK_P
- **Refs:** Q102, R111, and PACK_P capacitance: C431–C437 and C531–C537 (14 × 47 µF 25 V at review time; since the polymer change, 6 × 47 µF MLCC plus C432/C532 100 µF polymer, still about 290 µF effective) plus C444/C445/C544/C545.
- **Why:**
  - Q102 is a source follower.
  - Its gate slews at the DSG pump current (about 40–95 µA, derived from the §7.18 rise-time spec) divided by Cgd: about 0.5–5 V/µs.
  - That is far faster than the bank can follow, so only the loop resistance limits the current.
- **Numbers:** peak about 110–170 A, τ about 35–50 µs, about 50 mJ per turn-on.
- **Effects:**
  - Well above the 22 A SCD threshold, so expect nuisance trips.
  - Stresses F101's I²t and Q102. The 184 A pulsed rating is not exceeded.
- **Fix:**
  - Add DNP footprints for a gate-to-drain capacitor (DSG_G to FET_MID, 4.7–10 nF with about 1 k in series) or a gate-to-GND capacitor (about 100 nF, which gives about 1 V/ms and about 0.3 A).
  - Add a diode across R111 so turn-off stays fast, then check SCD turn-off time with the capacitor fitted.
- **Rejected during challenge:** a gate-to-source capacitor. In a source follower it is bootstrapped and only adds delay.

### 9. The EV2400 can't talk to the gauge whenever 3V3 is down, which is exactly when it's needed
- **Refs:** R304/R305 (4.7 k to 3V3), J103, SDA/SCL.
- **Why:**
  - 3V3 comes from PACK_P, which sits after the protection FETs. With the FETs off (fresh gauge, CUV/OCD trip, SHUTDOWN), 3V3 is dead.
  - When off, the TPS62177 actively pulls its output down through 175 Ω (tps62177 §8.3.2). R304/R305 then act as 4.7 k pull-downs.
  - The gauge needs VIH ≥ 1.3 V (§7.11), which only works if the EV2400's own pull-up is ≤ 7.2 kΩ. That value is unverified.
- **Fix:**
  - Feed the R304/R305 pull-ups through a 0 Ω or jumper (or an "aux 3V3" header), so they can be disconnected for EV2400 work.
  - Add a way to power PACK_P from a bench supply or a wake button (see Q3).

### 10. BTP_INT can push PA6 above its rating (major, pending a bring-up measurement)
- **Refs:** U101 pin 15 (BTP_INT), R114 (100 k to 3V3), U301 PA6, net GAUGE_BTP.
- **BTP_INT output (bq40z50 §7.12):** VOH is ≥ 3.5 V with no maximum. The high side is a weak 10–20 µA source; the low side is driven hard (0.4 V at 1.5 mA).
- **PA6 limits:** PA6 is FT_a, with an absolute maximum of VDD + 4.0 V, which is 4.0 V when unpowered. Positive injection is not allowed (DS13258 Tables 17/18).
- **Effect:** with about 15 µA into R114, PA6 sits at about 4.8 V.
- **Sleep current:** if BTP idles low, R114 draws 33 µA, which also corrupts the R_MEAS sleep measurement.
- **Fix:** buffer with a 2N7002 (gate to BTP_INT with about 1 M to VSS, drain to PA6 with the pull-up) and invert the polarity in firmware. At minimum, measure the open-circuit VOH at bring-up.

### 11. U301 (STM32WB1MMC) has no MPN or LCSC number
- **Why:** JLC won't place it, and the LGA-77 with 0.3 mm lands can't practically be hand-soldered.
- **Fix:** MPN STM32WB1MMCH6TR (DS14096 Table 5). Confirm stock or plan consigned parts.

---

## Minor (schematic, footprint, BOM)

| # | Refs | Issue | Fix |
|---|---|---|---|
| m1 | Q102 | During a hard PACK_P short, DSG = VBAT + 10.5–12 V takes VGS toward 28.8 V, against ±20 V. Pump-limited, lasts until SCD trips (SCD1 delay can be up to 915 µs). | DNP 15–18 V Zener gate-to-source, and keep the SCD1 delay short. |
| m2 | C105 (PBI) | 2.2 µF 25 V 0603 X5R keeps only about 0.7–1 µF at 16.8 V; TI asks for 2.2 µF (§7.3). | 2.2 µF 50 V X7R 0805/1206, or 4.7 µF. |
| m3 | C205 (U203 out) | 2.2 µF 10 V 0603 gives about 1.1–1.4 µF effective at 5 V, against ≥ 1.5 µF (tps709 §8.1.1). C202/C203 sit at the amplifiers and don't count. | 4.7 µF 10 V 0603. |
| m4 | R433/R434, U404 (both ports) | PP5V = 4.90–5.10 V (FB 784–816 mV), against the TPS25751 PP5V minimum of 4.9 V. R433 is 105 k > 100 k, and there is no feed-forward cap (tps62933 §10.2.2.10). | R433 = 107 k (5.08 V); DNP CFF across R433/R533 (TI example 10 pF). |
| m5 | D401/D501 | SMAJ22A reaches about 28 V at about 3 A (0.76–0.98 Ω dynamic resistance), the TPS25751's 28 V absolute maximum. Triggers: a non-compliant hot 20 V source, unplugging under load, ESD. | TVS2200 (flat clamp, as in TI's reference). |
| m6 | J201/J202 | Amphenol 132289 edge-launch SMA: KiCad's 3D model shows a leg gap of about 1.73 mm, which suits a 1.6 mm board; this board is 0.8 mm. | Check the Amphenol drawing; pick a 0.8 mm edge-launch or a vertical SMA. |
| m7 | U401/U501 pin 10 | IRQ1/IRQ2 have no pull-up (TPS25751 Table 5-1 requires one). PA0/PA2 are analog after reset. | 100 k to 3V3. |
| m8 | J102 → TS1 | TS1 absolute maximum is about 2.1 V, with no series R or ESD. The NTC is taped to a cell can, which is that cell's negative terminal (up to about 10.8 V above VSS on BT104). | Mount on BT101 (can = VSS) and note it, or add 1 k in series plus a clamp. |
| m9 | R101–R104 | See #7: 0603 is under-rated for fault currents. | 1206. |
| m10 | J101 + holders | Both can be populated, which puts cells in parallel tap-to-tap through sense traces (about 10 A at a 0.5 V mismatch). | Ship J101 unfitted, or add an interlock or jumper. |
| m11 | TP102 | CELL_N looks like ground. A scope ground clip here, together with a GND-referenced SMA/USB, shorts RS101. | Silkscreen "CELL_N — not GND". |
| m12 | J303 | NTC_EN, EN_5V1 and EN_5V2 are push-pull MCU nets brought straight out, so overriding them causes contention. | 1 k in series in each line. |
| m13 | R430/R530 | Permanent net-tie copper: the charger's battery side can't be isolated from PACK_P, though the circuit description (§8) asked for that. | Solder-jumper gap or two 2512 0 Ω. |
| m14 | 3V3_SLEEP / PB4 | PB4 floats when the MCU is unpowered, so the TPS62177 pull-down selects sleep mode (15 mA max). No test point. | Test point on 3V3_SLEEP plus a DNP 100 k to 3V3. |
| m15 | J301/J302 | SWD 2×5 1.27 mm has pin 7 present, so keyed cables won't fit. UART order TX/RX/GND. No reset button. BOOT0 is a fixed 10 k pull-down with no pad. | Keyed/shrouded header (FTSH-105-…-K), silkscreen TX direction, reset tactile switch, BOOT0 pad. |
| m16 | U204 pin 4 | TPS62177 NC pin is open; TI recommends AGND. | Tie to GND. |
| m17 | J201/J202, U205/U206 | INA190 maximum capacitive load is 1 nF and there is no short-circuit spec. A 50 Ω scope input or a shorted SMA overloads it. | Fit R204/R205 = 49.9 Ω; note "1 MΩ input". |
| m18 | U401/U501 GPIO0–3, 6, 7, 11 | Tied to GND per Table 5-1 (this is all 14 ERC violations, all false positives). GPIO11 is output-only, so a config that maps an event to it would drive it into GND. | Confirm every "GPIO x Mapped Event" = 0; optionally 100 k pull-downs plus pads. |
| m19 | R431/R531 | 1206 0 Ω carrying up to about 1.7 A; typical rating is 2 A. | 2512 0 Ω or a 3 A jumper part. |
| m20 | C409/C509 | 1 µF 35 V 0603 on VAC drops to about 0.4 µF at 20 V; TI asks for 1 µF. | 1 µF 50 V 0805. |
| m21 | BOM | No MPN: R201 (10 Ω 0.5 W 1206), TH301–TH304, TH401, TH501 (B value matters), D301, JP202. No voltage rating: C106, C202, C203, C301–C304, C308–C311, C408, C508. C401/C402/C501/C502 have "50V C0G" only in the hidden Notes field. 0.1 µF spread over 5 BOM lines. A programmatic check of capacitor voltage against net maximum found no under-rated capacitor. | Fill in MPN/LCSC and ratings; consolidate. |
| m22 | Power stage (both ports) | BQ25756 runs at about 600 kHz (top of range) with 2.2 µH (minimum; −20 % → 1.76 µH): ripple up to 4.7 A, peak about 12.2 A against Isat 18 A, which is OK. TPS62933 output C is about 255 µF against TI's typical 20 µF; no maximum is stated, so it is unverified rather than out of range. | Consider R412 = 50 k (500 kHz); load-step and start-up checks at bring-up. |

## Firmware and configuration (no schematic change)

Consolidated, with review 2 corrections, in `bringup-config-checklist.md`.

1. **Charger setup in the TPS25751 config:**
   - VFB_REG = 0x0F (1.534 V → 16.80 V). The power-on default gives 16.84 V, up to 16.96 V worst case; the documented "1.527 V" isn't on the 2 mV grid and ignores the FBG resistance.
   - Also set ICHG_REG, IPRECHG, ITERM (power-on value is 2.0 A), the watchdog, and EN_CHG_BIT_RESET_BEHAVIOR = 0.
2. **Charger temperature input (JEITA):** with the rev A4 network (1.8k/5.6k) the "cool" threshold on the FET NTC is about 18.8 °C (was 16 °C), so charge current drops to 20 % below that by default. Set EN_JEITA = 0, or TS_T2/JEITA_ISETC accordingly. In charge mode an open NTC is caught as cold (only 0.75 % margin); in reverse mode it is not detected.
3. **Source power sharing (see #3; F101 is 15 A since rev A4):** keep the total pack current at or below about 10–11 A, i.e. the product rule of 100 W total out (USB1 up to 100 W alone, 80 W + 20 W with both ports). IBAT_REV only steps 20/15/10/5 A, so it is a coarse backstop (10 A per port); the real limit is the source PDOs the TPS25751 offers. The MCU lowers USB1's offer when USB2 attaches (attach interrupt), mirroring the charge-current rule in item 14. In holder mode cap the total much lower (#4).
4. **Gauge data flash before the first charge:**
   - 4S and the EVE chemistry.
   - Enable all four cell thermistors TS1–TS4 (rev A4 adds J105–J107) and use the maximum for the temperature protections.
   - Thresholds: COV ≤ 4.25 V, CUV, OCC1 about 6 A, OCD1 about 10–11 A for the welded pack (100 W at the 12 V low end) and about 2–3 A in holder mode, OLD about 16–20 A (its 8.3 A minimum would cut 100 W at low pack voltage), a short SCD1 delay. F101 (15 A) is the backstop above these.
   - VIMR/VIMA enabled, and a sleep-current threshold above the ±10 mA coulomb-counter offset.
   - Then send FET enable.
   - Factory defaults found in the TRM (SLUUBK0B): `DA Configuration` = 0x12 (**3S**), `Manufacturing Status Init` = 0x0000 (**FET_EN off**, so a fresh board does not power from its cells; first power comes from USB or the J104 bench header).
   - **Precharge (SUPERSEDED by review 2 A-3: keep Precharge Start Voltage = 2500 mV, set Charging Voltage Low ≤ 2500 mV; see `bringup-config-checklist.md`):** `FET Options[PCHG_COMM]` defaults to 0 = external precharge FET, which this board does not have. Set `Precharge Start Voltage` = `Charging Voltage Low` = 0 mV to disable the gauge precharge (the BQ25756 already precharges at 0.56 A below about 3.0 V/cell) and leave `PCHG_COMM` = 0 so the gauge 0-V charging circuit stays off (decision Q4).
   - Keep `OCD:Recovery Delay` / `OCC:Recovery Delay` short: after an OCD trip DSG stays off until charge current is seen for that delay, and the charge current meanwhile flows through Q102's body diode (decision Q1).
5. **Dead-battery flag:** after any start where VBUS arrives before 3V3, the MCU must clear the TPS25751 dead-battery flag (DBfg, tps25751 §8.3.2). Until then, LDO_3V3 (EEPROM and I2Cc pull-ups) runs from VBUS. Add this to `docs/project/tps25751-eeprom-programming.md`.
6. **Gating EN_5Vx and charging:** refuse both unless the gauge reports four valid cells and both FETs on.
7. **TPS62177 sleep mode:** never enter it with a cable attached. It supplies only 15 mA, and the two TPS25751s alone draw 3–6 mA each.
8. **PB4:** set it push-pull before using sleep mode (README item 9).
9. **EV2400 mode:** release the I2C peripheral (or hold the MCU in reset) while bqStudio is connected, because there are two masters on SDA/SCL.
10. **PA6 (BTP):** it is not a WKUP pin, so the gauge can wake the MCU from Stop but not from Standby or Shutdown. Never enable PA6's internal pull resistors.
11. **NTC readings:** wait at least 5 ms after raising NTC_EN (τ = 0.5 ms). PA8's drive drop costs about 0.5–0.8 °C near 100 °C. Jumpering J303 PA7 to NTC_EN lets firmware measure the excitation directly.
12. **CHG_INH (PB8, rev A4; polarity reversed in rev A5, see review 2 D1):** drive **low** to allow charging, high (or release) to stop both chargers at their CE pins. Before rev A5 it was: drive high to stop both chargers. Assert it when the gauge stops answering for about 2 s; when its read-back configuration is wrong (cell count, COV/CUV/OCC); when the gauge stack voltage, the sum of its cells and the chargers' VBAT ADC (read through the TPS25751 with I2Cr) disagree by more than about 300 mV; when any cell is outside 2.5-4.25 V; or when the gauge reports CHG off but charge current still flows (FET stuck on). Drive it low only while a port is charging and these checks pass; drive it high otherwise. Since rev A5, low costs 138 µA (two 47k CE pull-ups), so idle must be high. See `mcu-io-power-states.md`. (Rev A5: input or reset stops charging; a dead pack still recovers from USB because 3V3 is down.) The TPS25751 configuration must keep `DIS_CE_PIN` = 0.
13. **Body-diode limit (decision Q1):** while the gauge reports XDSG = 1 and charge current flows, hold the chargers at the precharge level (ICHG_REG via I2Cw) until DSG is back on.
14. **Charge-current sharing (ICHG pin = 5.5 A per port):** TPS25751 configuration starts each BQ25756 at ICHG_REG = 2.8 A, EN_ICHG_PIN = 1, EN_CHG_BIT_RESET_BEHAVIOR = 0, IPRECHG ≈ 0.5 A, ITERM = 0.25 A. When only one port is charging, the MCU raises it (I2Cw) to the full rate: 5.5 A for the welded pack; in holder mode limited by the measured holder contact resistance (#4). On the other port's attach interrupt (IRQ1/IRQ2), the MCU drops the first port back to 2.8 A before the new contract closes PPHV. Gauge OCC1 about 6 A with a short delay. The cell maximum is 1C (5.6 A, "not for cycle life"); the project target is 0.5C, so the full rate belongs in a "fast charge" mode.

## Open questions

_Decided 2026-10-12; see "Decisions on the open questions" below._

1. **Body-diode heating:** does the gauge turn the off FET back on when current flows in its body-diode direction (SLUUBK0, not in the repo)?
   - CUV recovery at precharge is about 1.5 W in Q102 per port (about a 90 °C rise).
   - A latched DSG during a fast charge is 4–5 W.
2. **Second-level protection:** there is no second-level protector or chemical fuse (TI's reference uses bq2947x). Acceptable for the dev board? For production?
3. **Wake from SHUTDOWN:** the gauge needs PACK > 2.05–2.45 V to wake. Today the only sources are USB or clipping a supply onto TP106. Add a wake button (CELL_P → about 1 k → PACK_P) or a PACK_P supply header?
4. **USB with no cells:** the BQ25756 has no battery-absent detection, so PACK_P is held at about 16.8 V. The gauge runs through Q102's body diode; if it turns CHG on, VC4 sees about 17 V with VC1–VC3 floating. Forbid this in the bring-up procedure, or inhibit it in config?
5. **J103 pin order:** does SCL/SDA/GND match the EV2400 cable? Its documentation isn't in the repo.
6. **Charger PG:** should it go to a TPS25751 GPIO, as in TI figs 9-3/9-6? Today it goes to a test point only.
7. **Sleep-current measurement:** R_MEAS sees only the 3V3 branch. The PACK_P-side loads (2 × BQ25756 IQ_BAT, 2 × TPS62933 shutdown, the gauge) are not included. Document this, or measure the total at the pack.

### Decisions on the open questions (2026-10-12)

| # | Decision |
|---|---|
| Q1 | The BQ40Z50-R2 has no body-diode protection (TRM SLUUBK0B). Configuration + firmware: short OCD/OCC recovery delays, chargers held at precharge level while XDSG = 1 (firmware item 13). Measure Q102 temperature at bring-up. No hardware change. |
| Q2 | Rev 1: no hardware second-level protector. Instead the MCU cross-checks the gauge (alive, configuration, cell sum vs gauge stack vs charger VBAT ADC, FET stuck on) and can stop both chargers through the new CHG_INH line (PB8 → 1 k → each BQ25756 CE). This is firmware-dependent; decided 2026-10-12: no hardware secondary OVP or chemical fuse for production either; software is the second layer (rev2-changes.md 1b). |
| Q3 | Fixed: SW101 wake button and J104 bench PACK_P header. |
| Q4 | Rule + configuration: fit cells before USB (silkscreen and sheet note); gauge precharge and 0-V charging disabled (firmware item 4). |
| Q5 | Fixed: J103 is now 4-pin in the EV2400 SMBus order (SLUU446D): 1 VSS, 2 SCL, 3 SDA, 4 VOUT unused. The old 3-pin order would have shorted SCL to ground on a straight cable. EV2400 pull-ups are 20 k to 3.3 V, so with 3V3 down R312 must be removed (see #9). |
| Q6 | No change: the TPS25751 GPIO event table (TRM SLVUCR8B Table 5-6) has no input event for a charger PG line; the TPS25751 manages the BQ25756 over I2Cc and its INT line. PG stays on its test point. |
| Q7 | Documented: R_MEAS covers the 3V3 branch only. (Rev A5: the gauge BAT feed now comes from before F101, so this reading excludes the gauge's own supply current.) For the total pack drain, measure across the (DNP) F101 pads with a meter before fitting the fuse. (Rev A5: F101 is JLC-placed, so this method is gone; use the gauge's current reading.) |

## Verified correct (coverage)

- **TPS25751D:** every pin matches Table 5-1, and the fused lead pads match the REF0038A footprint.
  - Address straps decode to 0x20 (port 1) and 0x21 (port 2).
  - Capacitors meet Table 6.4 after derating.
  - The I2Cc side (EEPROM, pull-ups) runs from LDO_3V3, so EEPROM boot works with 3V3 dead.
- **BQ25756:** all 36 pins match Table 4-1.
  - ACP/ACN and SRP/SRN polarity and filters are correct, CE is low, BTST caps are 0.1 µF, DRV_SUP is fed through 10 Ω.
  - ACOV is 22.46 V, ACUV 4.10 V, VINDPM 4.51 V.
  - Sense resistors are 5 mΩ.
  - With CHG open mid-charge, PACK_P stays below about 18 V (BAT_OVP at 104 %).
- **Half-bridge FETs (IAUC45N04S6L063H):** pinout and land pattern verified from the datasheet images. Voltage stress is 56 % (Q401) and 42 % (Q402).
- **TPS62933:** RT, EN default off, BST, input caps and valley current limit are correct.
- **USB-C connector:** pad order matches the ShouHan drawing; rated 20 V / 5 A.
- **Ports:** port 1 and port 2 are identical. A script compared all 105 parts; the only shared nets are GND, PACK_P, 3V3, SDA and SCL. The ERC "U401/U501 GPIO11" error is not a merged net.
- **BQ40Z50-R2:** all 33 pins match Table 6-1, and unused pins are handled per the datasheet.
  - Cell stack order and VC taps are correct, and VC4 is taken before F101.
  - VSS = CELL_N on the SRP side, with correct polarity.
  - Q101/Q102 are common-drain with the body diodes the right way round; pinout verified from the image.
  - BAT, VCC and PACK networks match TI's reference.
  - Balancing current is 10.5 mA.
  - F101 interrupt rating (300 A) is above the prospective short-circuit current (85–170 A).
- **Holder:** polarity verified from the drawing (pad 1 = +).
- **STM32WB1MMC:** all 77 pins match DS14096, and decoupling matches ST's reference.
  - Peripheral functions: I2C1 on PB6/PB7, USART1 on PA9/PA10, SWD, ADC inputs on the NTC pins, WKUP on the IRQ pins, and no EXTI collisions.
  - No back-power path into any MCU pin, apart from #10.
- **TPS62177, INA190 and power tree:** TPS62177 VIN range, EN, FB and L/C are correct, and INA190 pinout and ranges are correct.
  - 3V3 worst case is about 30 mA against a 500 mA rating.
  - STAT/PG/EN_5V levels are all within limits.
- **I2C addresses:** main bus 0x0B / 0x20 / 0x21; private buses BQ25756 0x6B and EEPROM 0x50. No collisions.
- **Netlist and ERC:** no single-pin nets, no undriven nets, no power net with two sources, and every global label appears on at least two sheets. All 14 ERC violations are false positives (unused GPIOs tied to GND per the datasheet).

## What the challenge round changed

| Round-1 claim | Outcome |
|---|---|
| Inrush fix: gate-to-source cap on Q102 (B) | Rejected; it is bootstrapped in a source follower. Replaced by a gate-to-drain or gate-to-GND cap. |
| Inrush peak 80–300 A (B) | Narrowed to 110–170 A, limited by loop resistance (A). |
| Raise RS101 to 2–3 mΩ (B) | Rejected: 3 mΩ exceeds SRP/SRN ±0.3 V during a short, and TI says use the smallest value. Fix moved to R413/R513. |
| Missing cell: "1 W load → 0.1 A, about 1 W per resistor" everywhere (B) | Corrected to ≤ 55 mA / 0.3 W for BT102–BT104. The BT101 case (about 100 mA / 1 W) was defended and upheld. |
| BTP_INT idles at mid-rail (C) | Withdrawn: VOL is 0.4 V at 1.5 mA, an active driver. |
| JEITA cool threshold 17 °C; open NTC undetected (A) | Corrected to 16.0 °C. An open NTC is caught in charge mode and missed only in reverse mode. |
| SMAJ22A overshoot on hot-plug (A) | Hot-plug case dropped (USB-C attaches at vSafe5V). The other triggers remain; still minor. |
| TPS62933 output C "out of range" (A) | Reworded to "unverified" (no maximum is stated). A missing CFF was found as a result. |
| Edge SMA for 1.6 mm board, from memory (C) | Backed with KiCad 3D-model geometry; drawing check still needed. |
| CC caps unrated (C) | Narrowed: the rating is in Notes and missing only from the BOM. |
| New in the challenge round | Discharge-side overload (#3), holder contact resistance (#4), DBfg firmware step, R430/R530 can't be opened, Q102 VGS during a short, PP5V CFF. |
