# Schematic review 2: rev A4 deep pass (2026-10-12)

Second review of the MonolithDev rev A4 schematic. Three reviewers each took one scope:

- **A:** cells, gauge, protection.
- **B:** both USB ports: the BQ25756 chargers, the TPS25751D PD controllers and the 5 V buck.
- **C:** the MCU, the 3V3 and sleep-current rails, the cross-sheet interfaces, the BOM and testability.

They worked pin by pin against the datasheets in `datasheets/` and messaged each other while they worked. A formal challenge round followed, in which each reviewer re-derived every major finding, and every minor finding that changes hardware, from the other two files. The lead then re-checked the facts the verdicts depend on:

- The BQ25756's 80 µF minimum after derating on CIN and COUT (§5.3).
- The BQ25756 CE high threshold of 1.3 V.
- The BQ40Z50-R2's internal 2 kΩ DSG pull-down (fig. 6-1).
- The D103 15 V Zener from DSG_G to PACK_P.

The first review (`schematic-review-2026-10-12.md`) was not re-opened, except where a fix it made turned out to be wrong.

Raw material is in `review2/`:

- `A-findings.md`, `B-findings.md`, `C-findings.md`: each reviewer's findings, with round-2 amendments marked.
- `A-challenge.md`, `B-challenge.md`, `C-challenge.md`: the challenge round.

## Result

| | Critical | Major | Minor | Note |
|---|---|---|---|---|
| First pass | 0 | 3 | 24 | 28 |
| After the challenge round | **0** | **1** | 24 | 30 |

No critical issues. The one major item is a gauge configuration item, not a wiring error. Every rev A4 change was checked against its datasheet. The netlist shows no wrong connections:

- I2C addresses: 0x0B, 0x20, 0x21, no collisions.
- TPS25751 straps and dead-battery path: correct.
- All 77 STM32WB1MMC pins: correct.
- U101's RSM0032A footprint against TI's land pattern: matches.
- J103 pinout against the EV2400 guide: matches.
- C110/C111 against TI fig. 9-2: correct.
- TPS70950 EN left open: allowed, because the pin has a 300 nA internal pull-up (§7.4).
- TPS62177 pin 4 tied to GND: matches TI's recommendation.

## What the challenge round changed

- **A-1 dropped from MAJOR to MINOR** (B, then C). The claim was that both ports could source 100 W at once with the MCU dead, putting 24–31 A on the pack. Three things defeat it:
  - The gauge's factory defaults already trip it: AOLD at 19.4 A after 31 ms (a hardware comparator), OCD2 at 8 A for 3 s, and OCD1 at 6 A for 6 s.
  - With the MCU dead, EN_5V is low and PP5V = 0, so neither TPS25751 can source at all.
  - Before a configuration bundle loads, the TPS25751 offers only 5 V / 3 A.

  What remains is a running MCU with wrong firmware, which the first review covered as #3. In that case the gauge cycles the outputs on and off; nothing is damaged.
- **A-2 dropped from MAJOR to MINOR** (C). The physics holds: with C109 fitted at 0.1 µF, Q102 turns off in a short far more slowly than its SOA allows. But C109 is DNP, so the fix is the option value and its note.
  - B found it worse than A first said: C109 returns to GND, so in a short Q102's gate-to-source voltage reaches about 28 V.
  - The lead checked that D103 (15 V Zener, DNP) clamps that voltage. D103 must therefore be fitted whenever C109 is.
- **A-3 stayed MAJOR, and C completed the fix.** Keeping Precharge Start at 2.5 V alone is not enough. Charging Voltage Low defaults to 2900 mV, which would also block USB recovery of a pack coming back from a CUV trip.
- **B-5 got worse** (A, then C). The datasheet DC-bias curve for the GMK325BJ226MM gives 5.9–6.8 µF per 22 µF part at 20 V. README item 16 had used 8.5 µF, which is the 15 V figure. The worst-case USB-side bank is 72–75 µF against the 80 µF minimum. A fifth MLCC is not enough to fix it; a 100 µF polymer is.
- **B-3's numbers were corrected.** B's first leakage figures (4–8 mA) came from a search summary. The real LRC curve gives about 0.5 mA at 100 °C for a typical part. A maximum-leakage part can still run away thermally near 90 °C, and D405 is reverse-biased almost all the time, so the swap still stands.
- **A-6's numbers were reconciled.** The end-of-discharge current at 100 W is 11 A. A's earlier 16.8 A was the fuse rating that 11 A needs under Prosemi's rule.
- **C-3 and C-5 dropped to NOTE.**
  - C-3: with realistic damping, JP202 hot-plug ringing peaks at 23–30 V, under the 32 V absolute maximum.
  - C-5: the shrouded FTSH-105-01-L-DV-K is the correct keyed SWD header; only the "pin 7 removed" wording is wrong.
- **C-1 was confirmed by both peers, but its margin is thin.** With R417 at 100 k, CE sits at about 1.51 V against a 1.3 V threshold, and any value below about 82 k fails.
- **New items surfaced in the challenge round:**
  - OCD2 must be raised to 12–13 A for 1–2 s, or it trips a single 100 W port at low pack voltage.
  - Two charger-only configurations, after power-on or a watchdog reset, can charge at about 2C.
  - Once a port is sourcing, it keeps draining the pack to 2.5 V total; only gauge CUV stops it.
  - SW101 cannot wake anything while F101 is out. (Moot since rev A5: F101 is JLC-placed.)
  - Each port has its own EEPROM, so per-port bundles are possible.

## MAJOR

**A-3: Disabling gauge precharge would let a reversed or dead cell be charged.**

The first review's firmware item 4 sets Precharge Start Voltage to 0. This board has no precharge FET, and PCHG_COMM = 0. With the default 2.5 V threshold, the gauge holds the CHG FET off whenever any single cell is below 2.5 V (TRM §4.9, a per-cell test). That is the only block that doesn't depend on the MCU against the BQ25756 charging a cell that is reversed in a holder or over-discharged. The BQ25756 sees only the whole stack, and EVE prohibits reverse charging.

**Fix (configuration only):**
- Precharge Start Voltage = 2500 mV.
- Charging Voltage Low ≤ 2500 mV.
- PCHG_COMM = 0.
- Also consider enabling the SUV permanent fail (2.2 V for 5 s).
- Keep SOCD disabled, or raise it above 100 W discharge current.
- Correct the conflicting text in circuit-description §2.

## MINOR: hardware changes (proposed)

| # | Item | Change | Source |
|---|---|---|---|
| H1 (superseded by D1) | CHG_INH is lost while the MCU is in Standby, Shutdown or reset: PB8's 25–55 k pull-up against the 10 k CE pull-down gives at most 0.54 V on CE | R417/R517 10k → **100k** 1 %, plus a DNP 1 nF from CE to PGND; or reverse the polarity (decision D1) | C-1, B-17 |
| H2 | USB-side bulk is 72–75 µF worst case against the BQ25756's 80 µF minimum after derating | C421/C521 68 µF → **100 µF 35 V polymer** (about 98 µF worst case) | B-5 |
| H3 | The bootstrap Schottkys LRB521S-40 are high-leakage parts; a maximum-leakage part can run away thermally near 90 °C, and D405 is reverse-biased almost all the time | D404/D405/D504/D505 → **LRB520S-40T1G** (C132124, same SOD-523, 9–20× lower leakage) | B-3 |
| H4 | C109 (DNP) at 0.1 µF breaks Q102's short-circuit SOA, and its note tells builders to fit it | DNP value → **4.7 nF**; note: "fit D103 whenever C109 is fitted" | A-2 |
| H5 (D3: kept 15 A) | F101 15 A fails Prosemi's sizing rule at 11 A (100 W at a 2.5 V/cell cut-off) | **1206FA-20A**, or keep 15 A with the cut-off at 2.8 V/cell or higher (decision D3) | A-6 |
| H6 | Q103 2N7002: BTP_INT drive is guaranteed only about 2.57 V against a 2.5 V maximum Vth | Q103 → **BSS138** (or another part with Vth max ≤ 1.5 V) | A-10 |
| H7 | No test point before the fuse, so BT104 can't be checked as the sheet note asks; BAT is fed after F101 (TI feeds it before) | Add **TP on CELL_P_RAW**; consider moving R105 to CELL_P_RAW (but that breaks the "measure drain across the F101 pads" method) | A-4, A-5 |
| H8 | Protection FETs dissipate about 1 W each at 100 W, but nothing senses their temperature | Add **TH305** beside Q101/Q102 on spare PA7 (ADC), same 10k/100 nF divider from NTC_EN | A-7 (C's proposal) |
| H9 | One GND test point on the whole board; 5V_AMP, LDO_3V3, CE_N and LDO_IN have no test points | Add GND loops beside each switch-node probe field and test points on those nets | C-4 |
| H10 | TPS25751 PPHV pins have no local decoupling and VBUS has no 10 nF at the connector (TI layout example) | Add **0.1 µF on PPHV** and **10 nF on VBUS** at J401/J501 | B-6 |
| H11 | J104 bench input is an unkeyed header; a reversed lead drives PACK_P negative (TI §9.2.2.3.3) | Keyed 2-pin connector, or a series Schottky or reverse-polarity FET | A-9 |
| H12 | D301 green LED: InGaN part with Vf 3.3 V, driven from 3.3 V through 1 k, gets about 0.5 mA | R306 → **330 Ω**, or a 570 nm green part | C-2 |
| H13 (D2: kept 9.1k) | ICHG pin ceiling reaches 5.83 A worst case against EVE's 5.6 A; this only applies after a watchdog reset or a bundle fault | R413/R513 9.1k → **9.53k** (5.57 A worst case); decision D2, because this lowers single-port charging slightly | B-4 |
| H14 | J101 welded-pack connector has no Kelvin sense for 1N/4P | Rev 2 (welded-pack learning accuracy) | A-11 |
| H15 | The TS2–TS4 NTCs sit on cell cans at 4.2–12.6 V, against TS pins rated 2.1 V | Insulated sensors plus Kapton; update sheet note 10; optional series resistor | A-8 |

Other minor items, not hardware:
- **A-12:** the pack path needs copper pours, not the 2.5 mm net class (a layout item).
- **C-6:** 107 placed parts still have no LCSC number.
- **C-7:** mark "3.3 V max" at TP308.
- **A-1, B-1, B-2, B-7:** configuration items, listed below.

## Configuration and firmware items

These add to the first review's firmware list, items 1–14.

1. **A-3 gauge precharge:** see the MAJOR section above.
2. **A-1:** each TPS25751 EEPROM bundle defaults to safe source PDOs of 60 W or less. Better: build per-port bundles (USB1 100 W, USB2 20–30 W), so the 80 + 20 W product rule holds without the MCU (M-B3).
3. **OCD2** to about 12–13 A for 1–2 s. Otherwise the default 8 A for 3 s trips a single 100 W port at low pack voltage (M-B1).
4. **BQ25756 IBAT_REV** to 5–10 A; the default is 20 A (B-7).
5. **BQ25756 TS_T5 = 00b** (about 81 °C) and **BHOT = 00b**, so the FET-area MLCCs stay within their 85 °C rating (B-2).
6. **BQ25756 EN_PFM = 0**, because ITERM is 0.25 A (B-11).
7. **Watchdog:** confirm the TPS25751 services the BQ25756 watchdog. If it doesn't, sourcing drops every 40 s and ICHG_REG resets to its 20 A power-on value (B-11, B-4).
8. **Gauge sleep:** with IN_SYSTEM_SLEEP = 1, the gauge never sleeps, because 3V3 holds SMBus high (336 µA). If sleep is enabled, the CHG FET opens in sleep (A N-1, C-8).
9. **Gauge [BCAST] = 0** (C-16).
10. **SCD delays:** short enough to clear a hard short before F101 melts, about 0.5 ms at 185 A (A N-2).
11. **CUV:** enabled with a short delay. Once a port is sourcing, it runs the pack down to 2.5 V total (A M-2).
12. ~~**CHG_INH:** use Stop2, not Standby, while inhibiting, and re-assert after every reset (C-1).~~ Superseded by D1 and item 17.
13. **Port-to-itself cable loop:** detect it and stop (B-12).
14. **Bring-up:** capture the J402 I2C bus to find out whether the bundle rewrites ICHG_REG on every attach (M-3).

## Documentation fixes

- **README item 16:** the USB-side bulk figure used the 15 V DC-bias value (X-1).
- **J301:** "pin 7 removed" should say "keyed shroud" (C-5).
- **Port sheet text:** "5.00 V" should be 5.08 V, and "ILIM 5.5 A" should be 5.6 A (B-11).
- **NTC B-constants:** the 3380 vs 3435 labels are inconsistent (C-12).
- **R201:** the description says 0.5 W, but the part is 1/4 W (C-13).
- **JP201/JP202:** the shunts are missing from the BOM (C-15).
- **D401:** drawn with the bidirectional TVS symbol, but the SMAJ22A is unidirectional; assembly polarity is correct (B-13).
- **Circuit description §2:** its PCHG_COMM text conflicts with A-3.
- **SW101:** hold it for 0.5 s to wake the gauge, and note that it does nothing while F101 is out (N-6, X-4).

## Decisions (2026-10-13)

| | Decision | Done |
|---|---|---|
| D1 | **Reverse CHG_INH** (fails safe), with an MCU watchdog | R417/R517 → 47k pull-up to 3V3 (C25819). The MCU drives PB8 low to allow charging. 47k rather than 10k: the CE low level is 0.07 V instead of 0.30 V, against a VIL max of 0.4 V. Replaces H1. Sheet notes, README item 23, circuit description and first-review firmware item 12 updated. |
| Watchdog | **Internal IWDG in hardware mode**, no external IC | Option byte IWDG_SW = 0, so the IWDG starts at every reset and firmware cannot disable it. It runs from the 32 kHz LSI and keeps running in Stop and Standby (STM32WB15 DS §3.18.4). See firmware item 15. |
| D2 | **Keep R413/R513 = 9.1k** (5.5 A nominal, maximum single-port charging) | No change. H13 not done. The worst case of 5.83 A is accepted; it applies only after a BQ25756 watchdog reset or a bundle fault (firmware item 7). |
| D3 | **Keep F101 15 A**; the gauge cut-off under load stays at 2.8 V/cell or higher | Recorded in F101's notes. See firmware item 16. H5 not done. |

Firmware and configuration items added by these decisions:

15. **IWDG:**
    - Option bytes: IWDG_SW = 0 (hardware start). IWDG_STOP = 1 and IWDG_STDBY = 1 keep it counting in Stop and Standby, so a low-power loop must wake to refresh it. Alternatively, set them to 0 to freeze it there, but then a hang inside Stop is not caught.
    - Timeout depends on the state (`mcu-io-power-states.md` rule 4): about 2 s while charging or sourcing, refreshed only from the ≤ 1 s supervision loop after the gauge and charger checks pass; about 16 s in idle Stop2, refreshed by an RTC wake-up about every 8 s. Never refresh it from a free-running timer interrupt.
    - Set DBGMCU to freeze the IWDG while the debugger halts the core.
    - Count resets in an RTC backup register and report them, so a reset loop is visible.
16. **Gauge cut-off for F101 = 15 A:** set the gauge's undervoltage/terminate thresholds so the pack never delivers 100 W below 2.8 V/cell under load (9.8 A, about 14.7 A of fuse rating needed). Use CUV and terminate voltage, or have the MCU step the PDOs down below about 3.0 V/cell.
17. **CHG_INH:**
    - Drive PB8 push-pull low only while charging is allowed, and high in idle and while only sourcing. Low costs 138 µA (two 47k pull-ups), almost the whole 150 µA idle budget.
    - Use Stop0–2 for low-power waits; GPIO state is held there. Standby and Shutdown are not used at all (BLE needs Stop2).
    - The full pin-by-state plan is in `mcu-io-power-states.md`.
    - After every reset, run the checks (firmware item 12) before driving PB8 low.
## Hardware changes made (rev A5, 2026-10-13)

| Item | Done |
|---|---|
| H2 USB-side bulk | C421/C521 → 100 µF 35 V polymer (C5246554), same 6.3 mm footprint; about 99 µF worst case. ESR 48 mΩ, 1.5 A rms rating against about 1 A rms worst case (MLCCs carry about 80 %) |
| H3 bootstrap diodes | LRB520S-40T1G (C132124) |
| H4 C109 | DNP value 4.7 nF; note: fit D103 with it |
| H6 Q103 | BSS138 (onsemi, C52895) |
| H7 BAT feed | **Follows TI fig. 9-12:** D101 from CELL_P_RAW (cell top, before F101). TP108 added on CELL_P_RAW |
| H9 test points | GND loops TP412/TP512/TP109/TP309; pads on CE_N, LDO_3V3, LDO_IN, 5V_AMP |
| H10 PPHV/VBUS caps | C449/C549 0.1 µF PPHV; C450/C550 10 nF VBUS |
| H12 LED | R306 330 Ω |
| C-6 LCSC | Every resistor and capacitor now has a JLC number |
| Open-item pass | H11 J104: D104 SS34 series diode. H15: insulated-NTC sheet note. B-13 D401 symbol. C-5 J301 wording. C-12 B-constant notes. C-13 R201 text. C-15 shunt notes. Header LCSC numbers. Antenna keep-out rule area. Configuration checklist (`bringup-config-checklist.md`) |
| H8 FET temperature | TH305 between Q101/Q102 on PA7 (ADC1_IN2), divider R320/C312 (README item 28) |
| Not done | H14 J101 Kelvin (rev 2); LCSC numbers for headers (test loops are now SMD RH-S2761-46R, C55121754: README item 26). U301 hand-soldered (out of stock at LCSC, user decision) |

## Decisions that were asked (kept for the record)

- **D1, CHG_INH polarity.** The choice is between:
  - (a) Keep "MCU off = charging allowed" and fix it with 100 k (H1). The margin is about 0.2 V.
  - (b) Reverse it: a pull-up on CE to 3V3, and the MCU pulls low to allow charging. A dead pack still revives from USB, because 3V3 is down when CE is first sampled. After that, charging needs running firmware, so an unprogrammed or hung MCU blocks charging.
- **D2, ICHG ceiling.** The choice is between:
  - Keep 9.1k, a 5.5 A nominal pin ceiling. You asked for this to maximise single-port charging. Worst case is 5.83 A, 4 % over EVE's 1C, and only after a watchdog or bundle fault.
  - Change to 9.53k: 5.25 A nominal, 5.57 A worst case.
- **D3, F101 rating.** The choice is between:
  - 20 A, which meets Prosemi's rule at a 2.5 V/cell cut-off.
  - 15 A, which is acceptable if the gauge cut-off under load stays at 2.8 V/cell or higher, or output power tapers at low charge.
