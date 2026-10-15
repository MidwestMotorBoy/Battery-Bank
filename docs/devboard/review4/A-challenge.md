# Reviewer A: round 2 challenge

**Scope:** the lead's assigned questions first (Q1 B-2, Q2 D-3, Q3 D-1), then every MAJOR, and any MINOR or CONFIG I think is wrong or mis-graded.

**Method:**
- Each item is re-derived from the datasheet, not from the reviewer's text.
- Scripts and renders are in `scratch-a/`: `pgq.txt`, `trm.txt`, `tpd4s201.txt`, `tps62177_p16.png`, `tps62177_sleepleak.png`.

**Verdicts:**

| Item | Verdict |
|---|---|
| B-2 | AMEND (grade MINOR confirmed) |
| D-3 | AGREE, with a small AMEND (≈ 240 µA) |
| D-1 | AGREE, AMEND (the consequence is narrower and the Latch Limit = 0 question is sharper) |
| B-1 | AGREE (MAJOR) |
| C-6 | AGREE, AMEND (ride-through depends on how fast firmware restores EN_5Vx) |
| D-4 | AMEND (1.4 µA is typical, not maximum) |
| D-14 brown-out slew | AGREE |
| C-10, D-2 | AGREE (they match A-3) |
| B-3 to B-9, C-1 to C-5, C-7 to C-9, C-11, D-5 to D-11 | No objection (spot-checked where they touch my area) |

---

## Q1. B-2: FET dissipation per position at 100 W

**Topology, from `nets.txt`:**
- **Q401** = HS1: AC_SNS_N to SW1.
- **Q407** = LS1: SW1 to GND.
- **Q402** = HS2: BAT_SNS_P to SW2.
- **Q408** = LS2: SW2 to GND.

**Which FETs switch in which mode.** BQ25756 table 6-1 (p.21–22) and §6.3.3.3:
- In boost mode the HS FET of the input leg is ON and the other leg switches.
- In buck mode the HS FET of the output leg is ON.
- Reverse 12 V → 20 V is boost mode from the battery side. So Q402 is on 100 %, Q407 is the hard-switched low side, Q401 is the synchronous rectifier, and Q408 is off.
- B's position assignment is correct.

**Datasheet inputs** (PGQ04N070 p.2, fig. 3–6 rendered):
- RDS(on) at VGS = 4.5 V: 7.2 mΩ typical, 10 mΩ maximum.
- Fig. 3: ×1.36 at 100 °C, giving 9.8 mΩ typical hot and 13.6 mΩ maximum hot.
- Qgd 2.5 nC; plateau ≈ 3 V (fig. 6).
- RG 3.1 Ω; Coss ≈ 300 pF at 20 V (fig. 5).
- Qrr 15 nC; VSD ≈ 0.8 V.

**BQ25756 inputs (§5.5):**
- Gate drive: 3.4 Ω on, 1.0 Ω off.
- Dead time: 45 ns.
- fSW: 598 kHz (B-12).

**Operating point: reverse 100 W, 12 V pack.**
- I_L = 100 / (0.94 × 12) = 8.87 A.
- D = 1 − 12/20 = 0.40 (≈ 0.43 with losses).
- Ripple 5.5 A p-p (B-13), so I_rms² = 8.87² + 5.5²/12 = 81.2 A².

**My switching estimate** uses the actual edge currents, not the average. The valley is 6.1 A and the peak 11.6 A.
- Turn-on: Ig = (5 − 3) V / (3.4 + 3.1) Ω = 0.31 A. t = 3.5 nC / 0.31 A = 11.4 ns. E = ½ × 20 × 6.1 × 11.4 n = 0.70 µJ.
- Turn-off: Ig = 3 V / 4.1 Ω = 0.73 A. t = 4.8 ns. E = ½ × 20 × 11.6 × 4.8 n = 0.56 µJ.
- At 598 kHz: 0.75 W.
- Coss: ½ × 600 pF × 20² × 598 k = 0.07 W.
- The Qrr of Q401's body diode is dissipated in the FET that turns on, Q407: 15 nC × 20 V × 598 k = 0.18 W.

**Reverse 100 W from 12 V, per position:**

| Position | Terms | Max RDS, hot (13.6 mΩ) | Typical RDS, hot (9.8 mΩ) | B |
|---|---|---|---|---|
| Q402 HS2, 100 % on | I_rms² × R | **1.10 W** | 0.80 W | 1.07 W |
| Q407 LS1, hard-switched | 0.4 × I_rms² × R + Psw + Coss + Qrr | 0.44 + 0.75 + 0.07 + 0.18 = **1.44 W** | 1.32 W | 1.36 W |
| Q401 HS1, synchronous rectifier | 0.6 × I_rms² × R + VSD × I × 2 tDT × f | 0.66 + 0.38 = **1.04 W** | 0.86 W | 1.20 W (B puts Qrr here) |
| Q408 LS2 | off | 0 | 0 | 0 |
| **Stage** | | **3.6 W** | 3.0 W | 3.6 W |

**Pack at 11.2 V (2.8 V/cell, 9.6 A):** conduction scales by about (9.6/8.87)² = 1.17, which gives Q402 1.29 W and Q407 ≈ 1.60 W. That matches B's 1.25 / 1.55.

**Forward charging:**

| Case | Q401 HS1 | Q407 LS1 | Q402 HS2 | Q408 LS2 | Stage |
|---|---|---|---|---|---|
| Buck 20 → 12 V, 5.5 A (D 0.6, ripple 3.65 A) | 0.26 W conduction + 0.46 W switching + 0.07 W Coss + 0.18 W Qrr = 0.97 W | 0.17 W + 0.24 W dead time = 0.41 W | 0.43 W (on 100 %) | off | 1.8 W |
| 20 → 16.8 V (B's row) | 0.94 W | 0.50 W | 0.45 W | off | 1.9 W |

- I agree with B's 20 → 16.8 V row.
- In the true buck-boost region (VAC ≈ VBAT, for example 15 V PDO at 3 A into a 15 V pack), all four FETs switch but I_L ≈ 3 A, so each position is ≤ 0.5 W.
- **Reverse boost from a low pack is the worst case.** Forward operation never reaches the reverse numbers.

**Verdict: AMEND.**
- 1.1–1.6 W is right as a **maximum-RDS, hot** bracket for the three active positions at 100 W, 12 → 11.2 V pack.
- Typical parts sit at 0.8–1.3 W.
- The per-position split shifts slightly: Q407 is about 0.1 W higher and Q401 about 0.15 W lower than B's figures, because the Qrr loss lands in the FET that turns on, and the turn-on and turn-off edges carry the valley and peak currents. The stage total is unchanged at 3.6 W.
- B's "about 0.5 W per FET, shared across two packages" correction stands. The two FETs of a leg conduct alternately and never share current.
- These numbers exclude B-1's gate-sag penalty on Q402.

**Grade: MINOR is right.**
- **Junction temperature.** Tj ≈ T_copper + P × (RθJC 4.46 °C/W + about 5 °C/W pad-to-copper spreading, inferred) ≈ T_copper + 14 °C for 1.44 W.
- **What bounds the copper.** The copper is bounded by the BQ25756 TS hard stop on TH401 (94.5 °C at POR, 81 °C with TS_T5 = 00b; B-8). That gives Tj ≤ about 110 °C, against the 150 °C limit, provided TH401 sits on the Q402/Q407 copper.
- **Why not MAJOR.** Hardware already bounds it, so it is not "works only by luck". It would become MAJOR only if layout puts TH401 away from the two hottest positions. Add that placement condition to B's fix.

---

## Q2. D-3: the rev A7 idle budget

I re-derived each 3V3 load line from the datasheets.

| Load | Source | Typical | Note |
|---|---|---|---|
| 2 × TPS25751 | IVIN_3V3,Sleep = 56 µA ("VVBUS = 0 V, VVIN_3V3 = 3.3 V", tps25751 §6.7) | 112 µA | verified |
| 2 × TPD4S201 VPWR | IVPWR 112 µA typical, 160 µA maximum (the maximum is quoted at VPWR = 4.5 V; tpd4s201 §5.7) | 224 µA | verified. VPWR is on each P_LDO_3V3, which in Sleep comes from VIN_3V3 |
| 3 × TMP1075, default rate (R1R0 = 00) | IQ 10 µA typical, 20 µA maximum (§6.5) | 30 µA | about 1 µA if firmware uses shutdown (A-4) |
| CC2340 | Standby 0.71 µA plus advertising | about 15 µA | estimate; it depends on the advertising interval |
| Gauge SMBC/SMBD 1 MΩ pull-downs | 3.3 V / 1 MΩ × 2 | 6.6 µA | D's citation |
| R313 while DIO21 holds sleep mode | 3.3 V / 470k | 7.0 µA | verified |
| 2 × M24512 standby | | ≤ 4 µA | |
| **3V3 total** | | **≈ 400 µA** | D's figure confirmed |

**Loads I checked and found zero in idle:**
- The STAT1/STAT2/PG 10k pull-ups: open drain, high-Z with no VAC.
- The CE pull-ups: CHG_INH is driven high, so no current.
- R432/R532: EN_5Vx low.
- The I2C/I2Cc pull-ups: buses idle high.
- R314: IRQ_N idle high.
- R208: PG high.
- The TMP1075 address straps.
- The BQ25756 FB divider: FBG is hi-Z outside the VAC window (B-12).

**Pack side:**
- **D's conversion** used 80 % efficiency plus a separate 4.8 µA IQ.
- **The datasheet efficiency at this load.** TPS62177 fig. 11/12 (sleep mode, rendered p.16; the curves are for 5 V out):
    - About 75–80 % at 0.4 mA from 12 V.
    - At 14 V: about 63 % at 100 µA and about 85 % at 1 mA.
    - Interpolated to 0.4 mA at 14.4 V: about 72–75 %. For 3.3 V out it is slightly lower.
- **The curves already include IQ,** so adding 4.8 µA again double-counts it.
- **3V3 branch:** 400 µA × 3.3 / (0.73 × 14.4) ≈ 126 µA (D had 119 µA).
- **Total:** gauge 75 + U102 1.5 + chargers 34 + bucks 4 + 126 ≈ **240 µA typical** (D: 235 µA).
- **With TMP1075 shutdown (A-4/D-3 firmware):** about 230 µA.

**Verdict: AGREE, AMEND to "about 230–245 µA typical".**
- The figure is driven by the TPD4S201 (C-2) and the TPS25751 sleep current. Those two are 336 µA of the 400 µA at 3V3.
- MINOR + DOC is the right grade.
- The worst case (TPD4S201 160 µA maximum, TMP1075 20 µA maximum) is about 525 µA at 3V3, or about 290 µA at the pack.

---

## Q3. D-1: [NR], latch recovery with PRES tied to VSS

**Verified in the TRM (SLUUBK0B, `scratch-a/trm.txt`):**
1. **The default is removable.** DA Configuration bit 2, "NR: Use PRES in system detection … 0 = Use PRES, REMOVABLE mode (default)" (TRM data-flash table, the line beginning "NR (Bit 2)"). D is right.
2. **Recovery depends on [NR].** TRM §2.7 says: "The recovery condition for removable pack ([NR] = 0) is based on the transition on the PRES pin, while the recovery condition for embedded pack ([NR] = 1) is based on the Reset time."
    - Every latch table repeats this: COVL, OCDL, AOLDL, ASCCL and ASCDL each have "Latch Reset ([NR] = 0): … Low-high-low transition on PRES pin".
    - PRES (U101.16) is on CELL_N in `nets.txt`, so it can never transition. D is right.
3. **The latch enables default on.** Enabled Protections A, default 0xFF, includes AOLDL (bit 7). Enabled Protections B, default 0xFF, includes ASCDL and ASCCL.
4. **Every Latch Limit defaults to 0.** This is my new evidence. COV, OCD, AOLD, ASCC and ASCD Latch Limit are all "Min 0, Max 255, Default 0" (TRM §15.9.x, e.g. "Overload latch counter trip threshold … 0").
    - The Latch Trip condition is written as "counter ≥ Latch Limit".
    - Read literally, a limit of 0 means the **first** trip latches. Read as "0 = disabled", it never latches.
    - The TRM states neither, and I found no text saying 0 disables the latch. This is the open point D flagged, and it decides whether the default is harmless or latches on the first short.

**The consequence, re-derived (AMEND: narrower than "latch itself dead"):**
- **Discharge latches (AOLDL, ASCDL, OCDL)** set XDSG only. DSG opens, so PACK_P (and therefore 3V3 and the MCU) collapses.
    - The CHG FET stays on. A USB charger can raise PACK_P (the BQ25756 forward path, CE low because 3V3 is dead).
    - Then 3V3 comes back and the MCU can send MAC 0x0041 DeviceReset (TRM §14.1.35) to clear the latch.
    - So the pack is **dead until USB is plugged in and firmware issues DeviceReset**, not dead for good. Without that firmware step, it discharges nothing even with USB present.
- **Charge latches (COVL, ASCCL)** set XCHG only. DSG stays on and the board stays alive. The MCU can reset the gauge itself.
- **J104 or the EV2400** also recover it on the bench, as D says.

**Verdict: AGREE (CONFIG), AMEND the consequence and the evidence.**
- The fix stands: prefer [NR] = 1, so latches clear after their Reset time.
- Also add to the checklist:
    - Set every Latch Limit explicitly (non-zero, e.g. TI's EVM values) rather than relying on the undocumented meaning of 0.
    - Firmware sends DeviceReset when it boots and finds SafetyStatus()[xxxL] set.
- **Grade.** CONFIG is right, because the hardware is fine and the fix is data flash. If bring-up shows Latch Limit = 0 means "latch on the first trip", D-1 is the most user-visible failure on the board: a single bench short kills discharge until USB is attached. Test this deliberately at bring-up with J104 current-limited.

---

## Other items

### B-1 [MAJOR]: high-side gate sags to the bootstrap-refresh threshold. AGREE
- **Re-derived from BQ25756 §5.5** (scratch-b/bq25756.txt lines 1540–1610):
    - VBTST2_REFRESH is 2.7 / 3.1 / 3.9 V. It is "BTST falling, VBTST − VSW when low-side refresh pulse is requested".
    - Nowhere does the datasheet describe a periodic refresh. §6.3.3.3 forces only a 225 ns minimum HS on-time per cycle in boost, and that applies to the switching leg, not the 100 % leg.
- **The droop current is real.**
    - In reverse boost, BTST2 sits at about VBAT + 4.2 V and D405's anode is at REGN, so D405 is reverse-biased by about 11 V.
    - A Schottky leaks about 1–3 µA cold at that bias and roughly 30–100× more at 100 °C. Driver bias comes on top.
    - So the 0.1 µF bootstrap cap reaches the refresh threshold in milliseconds, as B says.
- **Effect at the gate voltages the refresh allows** (PGQ04N070 fig. 4, rendered):
    - At VGS = 3 V the typical part carries about 13 A at 0.5 V VDS. At 10 A that is roughly 30–45 mΩ, about 3–4 W at the bottom of the sawtooth.
    - At 3.5 V it is about 10 mΩ.
    - With VGS(th) up to 2.5 V, a maximum-threshold part at a 2.7 V refresh is barely on.
- **Grade.** "Violates a datasheet requirement under a credible condition" fits: RDS(on) is unspecified below 4.5 V and the operating point is normal 100 W reverse. MAJOR is right.
- **Fix.** Fix (a), a logic-level high side, is the right one. A bigger bootstrap cap only lengthens the period; it doesn't raise the minimum.
- **AMEND (minor).** The IAUC45 had the same sawtooth. Its 2.0 V maximum threshold makes the bottom of the sawtooth survivable rather than safe. So "no regression" is not quite true: this is a regression in margin, not new behaviour.

### C-6 [MINOR]: PP5V collapses on MCU reset. AGREE, AMEND
- **My state analysis agrees.** In reset the CC2340 pins are hi-Z (SWRS349A; TRM SWCU193 §8.5, input buffers disabled). R432 turns U404 off (0.7 µA × 100k = 0.07 V, below the 1.1 V disable threshold, tps62933 EC).
- **New: ride-through time.**
    - PP5V holds about 250 µF effective (B-15).
    - Rp needs PP5V > 4.75 V (C's §6.12). The headroom from 5.08 V is 0.33 V.
    - The PP5V load in that window is Rp (about 0.33 mA) plus VCONN to an e-marker (a few mA, up to tens of mA).
    - Hold-up is 250 µF × 0.33 V / I: about 80 ms at 1 mA, about 8 ms at 10 mA.
    - A CC2340 WDT or pin reset reaches application code in about 1–10 ms (ROM boot plus SDK init, inferred).
- **So the outcome depends on firmware,** not just hardware.
- **Add a CONFIG line:** "Restore EN_5V1/EN_5V2 from retained state (or set them high) as the first act after reset, before BLE stack init."
    - The CC2340 keeps no GPIO state across a reset. The firmware must hold the needed EN state in retention RAM, or derive it from TPS25751 status. The first option is faster.
- **Keep C's bring-up test.** Measure the drop time with the e-marked cable.

### D-4 [CONFIG/MINOR]: TPS62177 sleep-mode overload. AMEND one number
- D quotes "R313 at 470k against the **1.4 µA max** SLEEP pull-down … gives ≥ 2.75 V".
- The datasheet row (tps62177 EC table p.5, rendered in `scratch-a/tps62177_sleepleak.png`) has 1.4 µA in the **typical** column, with no maximum.
- So 2.75 V is the typical level, not a minimum. The TPS62177 side (VH 0.9 V) is still met with huge margin. The CC2340 side, where DIO21 is also the ROM bootloader trigger, is my A-1.
- The rest of D-4 is agreed: LED off, ≤ +4 dBm, leave sleep mode on IRQ_N.

### D-14 brown-out falling slew (flagged to A). AGREE
- SWRS349A §7.3: falling slew ≤ 1 mV/µs.
- D's 1.9 mV/µs at a 38 mA peak exceeds the limit only at the start of the collapse, which is far above the 1.67 V BOD. Near the BOD the slew is about 0.7 mV/µs.
- A CUV or DSG-open brown-out normally happens in S2 or low load, not at the 38 mA peak.
- The limit exists so the BOD can act. Inferred acceptable. If bring-up shows bad resets, TI's own remedy for high-impedance sources is a 10 µF VDDS capacitor (§7.3 footnote 3). C301 could become 10 µF in rev 2.0.

### C-10 and D-2. AGREE
- Both are consistent with my A-3, which is the wire-OR and edge-wake consequence.
- C's INT_EVENT1 reset value 0x08 and D's BTP_POL default are taken as their verified sources. I didn't re-derive them; they are outside my datasheets.

### D-6 and D-7. AGREE
- Both are duplicates already cross-referenced: D-6 = A-9, D-7 = A-6.
- On D-7: XL = 1 alone isn't sufficient. The bus rise time (A-6) caps it at 100 kHz with 4.7k pull-ups.

### Spot checks with no objection
- **C-2 (TPD4S201 224 µA):** confirmed against tpd4s201 §5.7, IVPWR 112 / 160 µA.
- **B-12 CE levels:** 3.3 × 1k/48k = 0.07 V. Matches mine.
- **B-15 EN pull-down arithmetic:** matches my state analysis.
- **D-9 Notes table:** it overlaps my A-11. D's extra rows (Q103, R117, TP107, gauge note 8, power note 6) are correct against `nets.txt`.
