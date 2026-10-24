# Reviewer B: challenge round (round 2)

I attacked A-findings.md and C-findings.md and answered the lead's questions 1, 2, 3, 4, 5, 9 and 10.

New sources for this round:
- SLUUBK0B TRM data-flash defaults (`scratchpad/ti_docs/sluubk0b.txt`, §15.9, §15.2.6.1, §15.4.9, §15.10, App. A).
- TPS25751 TRM SLVUCR8B Table 3-19.
- bq40z50-r2 §7.18 and Fig 6-1.
- prosemi_1206FA.txt.
- The real LRC LRB521S-40T1G and LRB520S-40T1G datasheets (downloaded to `B_dl/`).

---

## Lead's questions

### Q1 / A-1 vs A: DOWNGRADE to MINOR (configuration). I retract my round-1 "I'd back a MAJOR".

**What the TPS25751 advertises before the MCU writes anything**
- TRM SLVUCR8B §3.2.17, Table 3-19: the TX_SOURCE_CAPS (0x32) reset value is Number Valid PDOs = 1, PDO1 = 0x2601912C on PP5V.
- Decoded: bits 19:10 = 0x64 → 100 × 50 mV = 5 V; bits 9:0 = 0x12C → 300 × 10 mA = 3 A.
- The register is "Initialized by Application Customization", so after boot it holds whatever the EEPROM bundle says.
- There is no bundle in the repo. docs/firmware/tps25751-eeprom-programming.md describes only the load and update mechanics, and no PDO list exists anywhere.
- With a blank EEPROM, SafeMode waits for a host and nothing is sourced.
- So the per-port wattage with no MCU is purely a bundle decision. Nothing today already limits it.

**Gauge defaults (fresh data flash, SLUUBK0B)**
- §15.9.7 OCD1: −6000 mA, 6 s.
- §15.9.8 OCD2: −8000 mA, 3 s.
- §15.9.9 OCD recovery: 200 mA / 5 s, latch limit 0 (no latch).
- §15.9.10.5 AOLD Threshold = 0xF4: OLDV = 4, OLDD = 0xF.
- §15.2.6.1 AFE Protection Control = 0x70, so RSNS = 0, the "0.5 × AFE Protection Thresholds (default)".
  - App. A Table A-1 (RSNS = 0): setting 0x04 = −19.42 mV, which is **19.4 A** with RS101 = 1 mΩ.
  - Table A-3: delay 0xF = **31 ms**.
- AOLD is one of the "hardware-based protections" (TRM §2.7): an AFE comparator that acts on its own once data flash is loaded.
- ASCD1 0x77: 100 mV → 100 A, 427 µs (Tables A-7 and A-9).

**A's scenarios against those defaults**
- 24 A at 3.0 V/cell and 31 A at the ILIM ceiling are both above 19.4 A, so AOLD opens DSG within about 31 ms.
- 17.6 A at 3.6 V/cell is above OCD2 (8 A), so DSG opens after 3 s.
- With firmware item 4's values (OCD1 10–11 A, OLD 16–20 A, i.e. setting 0x03 16.6 A or 0x04 19.4 A), the result is the same.
- Recovery after 5 s, then a retry. Duty is at most about 3 s on / 5 s off at 17.6 A.

**Effects of that duty cycle**
- Q101/Q102: 17.6² × 8.7 mΩ = 2.7 W for 3 s per cycle. The average is about 1 W, not 5 W continuous.
- F101 at 117 % of rating: the Prosemi table gives "100 % → 4 h min" and "350 % → 5 s max", so it doesn't open in 3 s.
- The cells see 3.1C pulses against the 3C (16.8 A) maximum, 5 % over, for 3 s.
- The 24–31 A cases last at most 31 ms. Nothing reaches the sustained-overload state A describes.

**Verdict**
- Real, but the consequence is nuisance trip/retry cycling of both ports plus brief 3C pulses. That is a configuration issue, not unprotected hardware stress. "Nothing in hardware keeps pack current under limits" is wrong: AOLD is hardware.
- **Severity: MINOR.**
- Fix A's way (≤ 50–60 W PDOs and IBAT_REV 10 A in the bundle), or more simply with **per-port bundles**. Each TPS25751 boots its own EEPROM (tps25751 §8.4.1): USB1 bundle 100 W, USB2 bundle 20–30 W. That puts the 80+20 product rule in "hardware" with no MCU, and the worst case becomes 120–130 W ≈ 11–12 A at 12 V.
- Confidence: high on the TRM defaults; medium that the bundle can't re-enable faster recovery.

### Q2 / A-2 vs A: UPHOLD MAJOR, with an amendment that makes it worse
- **Internal 2 kΩ:** bq40z50 Fig 6-1 does show a 2 kΩ between the DSG pump/DSGOFF switch and the DSG pin (text extraction: "DSG Pump … 2 kΩ … DSG … DSGOFF"). Confirmed.
- **What the off switch returns to:** A says VSS. §7.18 specifies "VDSG(OFF) = VDSG − VPACK, −0.4 to 0.4 V, 10 MΩ between PACK and DSG", which says the off state ties DSG to the **PACK pin**, not VSS.
  - On this board the PACK pin reaches PACK_P only through **R113 = 10 kΩ** (nets.txt: Net-(U101-PACK) = R113.2 + U101.27).
  - The turn-off path for C109 is therefore gate → (D102 ∥ R111) → DSG → 2 k → PACK pin → R113 10 k → PACK_P → the short.
  - τ = 12 kΩ × 0.1 µF ≈ **1.2 ms**, against A's 200 µs. A's SOA conclusion (exceeded) is stronger.
  - Confidence that the return is PACK: medium (spec definition plus figure label, no rendered figure).
- **Second effect A missed:** C109 goes to GND, not to Q102's source.
  - In a hard PACK_P short the source collapses to about 0 V while C109 holds the gate at VBAT + 11.5 ≈ 28 V, so VGS ≈ 28 V against the AGM404AP1's ±20 V (agm404ap1 abs max, "VGS ±20").
  - D103 (15 V clamp) is also DNP. If it is fitted, it dumps C109's charge into the short and limits VGS to 15 V, but Q102 stays fully on until the slow discharge ends.
- **D102 orientation:** D102.1 (K) is on U101 DSG and D102.2 (A) on DSG_G, so it conducts gate → DSG pin, which speeds turn-off and bypasses R111. That matches A.
- **Board or option?** It is about a DNP option value. But sheet note 9 and the C109 Notes field instruct the builder to fit 0.1 µF "if SCD trips", and that is a realistic bring-up action whose result can disable discharge protection (Q102 failing short, no second-level protector).
- MAJOR is justified. A's 4.7 nF (τ ≤ 12 k × 5.5 nF = 66 µs even through R113) is the right direction. I would also make D103 fitted whenever C109 is fitted.

### Q3 / A-3 vs A: UPHOLD MAJOR (configuration). A better fix than A's exists.
- TRM §4.9: PRECHARGE is entered if "Min cell voltage1..4 < Precharge Start Voltage". "Setting Precharge Start Voltage and Charging Voltage Low = 0 mV disables the precharge function."
- §15.4.9.1: the Precharge Start Voltage minimum is 0 (it can't be negative).
- A reversed cell sits below the VC ADC range (−0.2 V, §7.10). CellVoltage() is reported unsigned in mV, so it reads about 0 mV at best. 0 < 0 is false, so with firmware item 4 (0 mV) the gauge does **not** block charging. With the default 2500 mV it does: CHG is off because PCHG_COMM = 0 selects the non-existent precharge FET.
- CUV opens only DSG. So A's mechanism holds, and first-review firmware item 4 directly conflicts with EVE §12.2.4.
- **Alternative fix A didn't list:**
  - Enable the SUV permanent fail. §15.10.1 defaults are 2200 mV, 5 s. PF checks are all disabled by default (§15.2.5.1 Enabled PF A = 0x00) until ManufacturingStatus()[PF] is set.
  - A reversed or dead cell (< 2.2 V) then latches all FETs off (§3.1 action 1). That keeps USB revival of a merely low pack (2.2–2.5 V/cell) possible.
  - Caution if PF is enabled: §15.10.4 SOCD defaults to −10 A / 5 s. Only SOCD's own bit enables it, but anyone flipping "enable all PF" would permanently fail the pack at 100 W from a low pack (≈ 10.7 A). Keep SOCD off or set it ≥ 16 A.
- Severity: MAJOR. This is a safety-relevant configuration decision on a holder board where reversal is realistic.

### Q4 / A-4, A-5 vs A: both UPHOLD MINOR
**How the pack connects with F101 DNP:**
- F101 is the only link from CELL_P_RAW (BT104 +, J101.5, R104) to CELL_P. J101 is DNP too.
- As assembled, the cells reach only the VC filter network. CELL_P, the FETs, and through D101/R105 the gauge BAT are all unpowered.
- The board runs only from J104 (bench supply on PACK_P), with Q102/Q101 body diodes back-feeding FET_MID and VCC through R106.
- BAT is genuinely unpowered in a real, documented state: "check each cell, then hand-fit F101".

**A-4:** a test point on CELL_P_RAW is needed to check BT104 (CELL_P_RAW − CELL3) without probing an F101 pad. Correct, cheap.

**A-5:** TI Fig 9-1 has D1 on the 4P side. Moving D101's anode to CELL_P_RAW costs nothing.
- One caution: with the anode on CELL_P_RAW, the gauge stays powered even when F101 is removed. That is what TI intends, but it defeats the first review's Q7 method ("measure total drain across the F101 pads"), because the gauge current would then bypass the meter. A already notes this.

### Q5 / A-6 vs A: UPHOLD MINOR, with the design-case numbers corrected
- **The 16.8 A figure** is not the design case. It is about 2 × 100 W at 12–13 V, which is the A-1 fault and is now bounded by AOLD/OCD (Q1).
- **Design case** (100 W total, firmware item 3): pack power ≈ 100 / 0.93 + about 1 W overhead ≈ 108.5 W.
  - At 3.0 V/cell loaded (12.0 V): 9.0 A.
  - At 2.75 V/cell (11.0 V): 9.9 A.
  - At 2.5 V/cell (10.0 V, EVE cut-off): 10.9 A.
  - So "about 11 A" is right only if 100 W is allowed down to the 2.5 V cut-off.
- **Prosemi rule** (prosemi_1206FA.txt p.2: In = Imax / (0.70 × Ktemp), Ktemp ≈ 0.95 at 50 °C):
  - Imax 9.0 A → In ≥ 13.5 A: 15 A OK.
  - Imax 10.9 A → In ≥ 16.4 A: 15 A is under.
- So 15 A is right only with a firmware or gauge power taper below about 3.0 V/cell. Otherwise use 1206FA-20A.
- The fix choice belongs to the power-policy owner. MINOR is right.

### Q9 / C-1 and B-17 vs C: UPHOLD MINOR, R417/R517 = 100 k
- **Noise immunity:** CE's input path is 100 k to PGND plus 1 k to PB8.
  - When PB8 is driven (normal run) the node is held at 1 k impedance, the same as today.
  - Only in Standby, Shutdown or reset is CE at about 50–100 k. In that state the charger is either supposed to be inhibited (APC pull-up) or free to charge (MCU off), so a glitch there toggles between two legal states for microseconds. The DNP 1 nF (τ = 100 µs) closes it.
- **Leakage:** IOUT_BIAS 1 µA max (bq25756 §5.5) × 100 k = 0.1 V < VIL 0.4 V. STM32 PB8 leakage (FT_f, about ±150 nA) adds ≤ 15 mV.
- **Fail-open intent preserved:** with the MCU unpowered, PB8 has no pull-up and CE ≈ 0.1 V. Charging is allowed, so USB still revives a dead pack.
- **Polarity swap rejected:** an inverted design (pull-up, MCU drives low to allow charging) would break fail-open. An unprogrammed or dead MCU would block charging, and the MCU itself is powered from the pack. That reintroduces the dead-pack lock-out decision Q2 avoided.
  - **Corrected after reading A-challenge Q9:** with the pull-up on 3V3, a fully dead pack does start charging, because 3V3 is down and the TPS62177 discharge holds it at 0 V.
  - But 3V3 comes up from PACK_P within milliseconds of the charger lifting the bank above about 3.5–4 V, even with the gauge FETs off.
  - From then on, charging continues only if firmware drives PB8 low. So the swap makes all charging firmware-dependent, which is fail-safe for an unprogrammed MCU.
  - That is a legitimate design-intent choice. I withdraw "rejected" and leave the decision to the lead. For rev 1 as built, 100 k is the minimal fix.
- **Extra pull-up rejected:** it fights the same requirement.
- Firmware alternative with no part change: inhibit only from Stop2, never Standby. C-1 says so too.
- Verdict: 100 k plus a DNP 1 nF is the best balance.

### Q10 / C-3 vs C: DOWNGRADE to NOTE (amended; first written as UPHOLD MINOR). Mechanism credible, 30 V is an upper bound, fix harmless
- **The ringing mechanism** is standard. Hot-plugging a source with low-ESR capacitance onto a bare MLCC through a few cm of trace gives an under-damped series RLC.
- **C's figures:** ζ = R / (2·√(L/C)). With L 50–100 nH and C204 ≈ 0.6–0.7 µF effective, Z0 = 0.27–0.41 Ω. For ζ ≥ 0.5 (≤ 16 % overshoot) R would need ≥ 0.27–0.41 Ω. Realistic R is 30–80 mΩ (two shunt contacts about 10–20 mΩ each, trace, ESR), so ζ ≈ 0.04–0.15 and overshoot is 62–88 %. 16.8 V × 1.6–1.9 = 27–32 V. C's 30 V is in range.
- **What may reduce it:**
  1. The source has to be a low-impedance capacitor near JP202. If the nearest PACK_P capacitance is only C107/C108 (0.1 µF in series = 0.05 µF) and the big banks sit 5–10 cm away at the chargers, both the effective L and the charge-sharing loss grow. The peak could be well below 30 V or similar; layout decides.
  2. Shunt contact make is often bouncy and resistive (tens of mΩ to Ω during wipe), which damps the first peak.
- **Against:** the TPS709 abs max is 32 V (§6.1), and the margin is ≤ 2 V on a credible estimate.
- The proposed 100 Ω (or even 10 Ω, ζ > 10) costs nothing: about 0.1 mA load, 10 mV drop.
- MINOR is right. A scope check at bring-up would settle it.
- **Amended after reading A's analysis:** A shows there is no local bulk near JP202. C206 sits behind R201 and C201 is DNP, so the source is the charger banks 5–10 cm away. Contact plus polymer ESR gives ζ ≈ 0.12–0.29 and a 23–28 V peak, below the 30 V recommended maximum.
- That matches my item 1 above. I accept NOTE (keep the 100 Ω as a free tweak), and split with A on whether it is MINOR or NOTE: lean NOTE.

---

## Remaining A and C items (MAJOR, or MINOR with a hardware change)

### A-7 vs A: UPHOLD MINOR
- AGM404AP1 RDS(on) 6.0 mΩ max at VGS 10 V (agm404ap1 table). The DSG drive is VBAT + 11.5 V, so VGS ≈ 11.5 V is valid.
- 11² × 6.0 m × 1.45 ≈ 1.05 W each.
- PA7 is spare (J303.2 only, nets.txt), and ADC-capable per C's DS13258 check. The fix is fine.

### A-8 vs A: UPHOLD MINOR (documentation plus optional series-R footprint)
- §7.1: TS abs max VREG + 0.3 V.
- A shorted lead to a 12.6 V can, through the NTC body, gives about 1 mA into the TS clamp.

### A-9 vs A: UPHOLD MINOR
- A reversed J104 lead: PACK_P is clamped through each BQ25756 battery-side leg. The LS2 body diode (GND → SW2) and the HS2 body diode (SW2 → BAT_SNS_P) give 2 VF ≈ −1.4 V. Each TPS62933's internal FETs give the same.
- Polymer reverse voltage at −1.4 V is beyond the usual ≤ 1 V allowance.
- A keyed connector is the cheapest fix.

### A-10 vs A: UPHOLD MINOR (marginal, not failing)
- BTP_INT VOH is ≥ 3.5 V at 0 µA and ≥ 1.8 V at −10 µA.
- Linear interpolation against the R117 470 k load: V = 3.5 − 0.17 µA⁻¹ × V/0.47 MΩ → V ≈ 2.57 V.
- That is above the 2N7002 Vth max of 2.5 V (at 250 µA), and Q103 needs only about 33 µA, which takes slightly less VGS. Works, with little margin. BSS138 or R117 = 1 MΩ are fine fixes.

### A-11 vs A: UPHOLD MINOR. The Kelvin-at-pack-connector argument is TI's (§9.2.2.1.3).

### A-12 vs A: UPHOLD MINOR (layout guidance)
- IPC-2221 external: 2.5 mm × 70 µm = 271 mil² → 0.048 × 20^0.44 × 271^0.725 = 0.048 × 3.74 × 58.0 = **10.4 A** at ΔT 20 °C. Re-derived; A is correct.

### C-2 vs C: UPHOLD MINOR (cosmetic). 0.3–0.5 mA in an InGaN LED is plausible; a 330 Ω change is free.

### C-4 vs C: UPHOLD MINOR
- Confirmed in nets.txt: GND has exactly one TP (TP203).
- I endorse a GND point in each port's probe field and a CE_N TP. CE_N is where B-17 and C-1 will be verified.

### C-5 vs C: UPHOLD MINOR. I can't verify the Samtec option code independently; the documentation mismatch is real either way.

### C-6 vs C: UPHOLD MINOR (BOM hygiene, high impact at order time)
- I spot-checked parts.txt: R417, R432, R1–R4, R401/R501 and R420–R429 have an empty LCSC field.

### C-7 vs C: UPHOLD MINOR
- tps25751 §6.1.1: I2Ct pins −0.3 to 4 V.
- Silk text is a free fix.

---

## Missed by everyone

### M-B1 [MINOR, config] Gauge OCD2 default (−8 A / 3 s) trips a single 100 W port at a low pack, and firmware item 4 doesn't list it
- SLUUBK0B §15.9.8: OCD2 Threshold −8000 mA, Delay 3 s.
- First-review firmware item 4 sets OCD1 10–11 A and OLD 16–20 A but never mentions OCD2.
- At 100 W from 12 V the pack current is 9.0 A (Q5), above 8 A. Single-port 100 W would drop after 3 s at about 3.0 V/cell, then retry every 5 s (OCD recovery).
- Fix: add "OCD2 ≥ OCD1 (e.g. 12–13 A / 1–2 s)" to firmware item 4.
- Same check for **SOCD** (§15.10.4, −10 A / 5 s, PF): keep its PF enable bit off, or raise it to ≥ 16 A, before anyone enables PF (see Q3).

### M-B2 [NOTE] TPS25751 power-on source caps = 5 V / 3 A only, until the bundle loads
- TRM Table 3-19 reset value.
- If a bundle fails its integrity check, the device stays in PTCH/SafeMode and doesn't source at all. It never falls back to an unsafe default. Good, and worth recording for A-1.

### M-B3 [NOTE] Per-port bundles are possible and simplify the power-sharing rule
- Each TPS25751 has its own EEPROM (U402/U502, both at 0x50 on separate I2Cc buses).
- So the two ports may carry different bundles, e.g. USB1 100 W and USB2 30 W.
- docs/firmware/tps25751-eeprom-programming.md assumes one Low Region binary for both. Note the option there.
