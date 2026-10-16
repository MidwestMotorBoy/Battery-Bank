# Reviewer C: round 2 challenge

**What this covers:**
- The two questions the lead assigned (Q1 = B-1, Q2 = A-2), answered first.
- The remaining MAJOR (A-1).
- The MINOR, CONFIG and NOTE items where I have evidence for or against.

**Method:**
- Every figure below was re-derived from the datasheets myself, not taken from the finding:
    - `datasheets/bq25756.pdf` (SLUSEN5A), text in `scratch-c/bq25756.txt`;
    - `scratch-b/pgq04n070.pdf`, figs. rendered in `scratch-b/pgq_p3.png`, which I read;
    - `datasheets/cc2340r5moda.pdf` (SWRS349A), text in `scratch-c/cc2340.txt`;
    - `datasheets/tps62177.pdf`;
    - `datasheets/tps25751.pdf`;
    - `scratch-b/lrb520s-40t1g.txt`.
- The nets come from `nets.txt`.

---

## Q1: B-1 [MAJOR], high-side gate drive at 100 % duty. Verdict: **AGREE, MAJOR** (amended in the details)

### 1. Which FET sits at 100 %, and when (verified)

BQ25756 table 6-1 (p.21–22) uses forward-direction names:

| Mode | HS BUCK FET (Q401) | LS BUCK (Q407) | LS BOOST (Q408) | HS BOOST FET (Q402) |
|---|---|---|---|---|
| BUCK | switching | switching | OFF | **ON** |
| BOOST | **ON** | OFF | switching | switching |

The input-side high-side FET is held on in each direction:

- **Reverse boost** (pack 11.2–16.8 V → VAC 20 V, ratio 1.19–1.79): the battery side is the input. **Q402 is on 100 %** and carries the full battery current. At 100 W from an 11.2 V pack (gauge cut-off 2.8 V/cell) at 95 % efficiency, that is 100 / (11.2 × 0.95) ≈ **9.4 A**, and 10 A at the IBAT_REV = 10 A setting.
- **Forward buck** (for example a 20 V source into a 12–14 V pack): Q402 is on 100 %, at ≤ 5.5 A (ICHG).
- **Forward boost** (a 5 or 9 V source): **Q401** is on 100 %, at ≤ IAC_DPM (≤ 3 A).

The 225 ns forced on-time in §6.3.3.3 concerns the *output-side* HS FET in boost mode. It does not refresh the input-side FET's bootstrap.

### 2. The bootstrap voltage (verified limits, inferred operating point)

- **REGN:** 4.8 / 5.0 / 5.2 V at IREGN = 20 mA (§5.5). In reverse mode REGN runs from BAT once BAT > 3.8 V (§6.3.3.2), so 4.8 V is the floor in the reverse case too.
- **DRV_SUP = REGN minus the drop across R420 (10 Ω):**
    - The average DRV_SUP current is the low-side and refresh gate charge. In boost, Q407 switches plus Q401 as the sync rectifier (its charge comes from BTST1, also recharged from DRV_SUP).
    - From PGQ fig. 6, Qg to 5 V is about 7.5 nC, so the current is about 2 × 7.5 nC × 600 kHz ≈ 9 mA, a 0.09 V drop.
    - B's 0.17 V assumes all four FETs switching (buck-boost). Either way, DRV_SUP ≈ 4.6–4.7 V min.
- **D405 forward drop:** the LRB520S-40 datasheet gives only VF ≤ 0.39 V at 10 mA.
    - The refresh pulse is short and recharges about 0.1 µF × 1.2 V ≈ 120 nC, so the peak current is hundreds of mA. The part is rated IO 200 mA and IFSM 1 A.
    - At that current a small SOD-523 Schottky drops about 0.5–0.7 V (inferred; no VF–IF curve in the sheet).
- **So the gate starts each refresh period at about 4.0–4.2 V, not 4.24 V.** B's figure is slightly optimistic. The difference makes B's case stronger.

### 3. Refresh behaviour (verified)

- §5.5 PWM DRIVERS: "VBTST2_REFRESH, Bootstrap refresh comparator threshold voltage, BTST2 falling, VBTST2 − VSW2 when low-side refresh pulse is requested": **2.7 / 3.1 / 3.9 V**. The same values apply to BTST1.
- This is the only refresh mechanism the datasheet describes. I searched the whole text for refresh, bootstrap, BTST, 100 % and duty: there is no periodic or forced refresh, and no maximum on-time for the input-side FET.
- So the guaranteed floor of the high-side gate drive is the comparator threshold: as low as 2.7 V.
- What drains the cap:
    - D405 reverse leakage at VR ≈ VBAT (11–17 V): ≤ 1 µA at 10 V and 25 °C, rising about 30–100× when hot.
    - The HIDRV2 driver bias (not specified).
    - The PGQ IGSS (≤ 100 nA).
- At 50–300 µA, the 0.1 µF C413 droops from about 4.1 V to 3.1 V in about 0.3–2 ms. Refresh therefore happens every few ms. The rate doesn't matter for the conclusion: with a constant drain, the gate sweeps linearly from its start value to the threshold, so the time-weighted distribution of VGS is the same whatever the period.

### 4. The Vgs the FET sees over time, and what the PGQ04N070 does with it

**Datasheet facts:**
- PGQ04N070 p.2: VGS(th) is 1.0 / 1.8 / **2.5 V** (at 250 µA).
- RDS(on) is specified only at 10 V (7 mΩ max) and 4.5 V (10 mΩ max).
- Fig. 6: the Miller plateau at ID = 20 A is about **3.0 V** typical. A typical part needs about 3 V just to carry 20 A in saturation.

**Typical part, read from fig. 4 at ID = 10 A, 25 °C:**

| VGS | VDS at 10 A | RDS(on) |
|---|---|---|
| 4.5 V | 0.07 V | ≈ 7 mΩ (matches the 7.2 mΩ typ) |
| 4.0 V | ≈ 0.10 V | ≈ 10 mΩ |
| 3.5 V | ≈ 0.13 V | ≈ 13 mΩ |
| 3.0 V | ≈ 0.35–0.4 V | ≈ 35–40 mΩ (the curve flattens at 15–17 A: saturation) |

**Typical BQ threshold (3.1 V), typical FET, sweep 4.1 → 3.1 V:**
- The time-averaged RDS(on) is about **14–15 mΩ** at 25 °C: two times the 4.5 V figure. Below about 3.2 V it climbs steeply.
- The hot multiplier is smaller at low VGS (near the zero-temperature-coefficient point), so I take ×1.15–1.36, giving 16–20 mΩ.
- Q402 then dissipates about 9.6² × 0.017 ≈ **1.4–1.8 W**, against B-2's 1.25 W.
- On a PDFN3333 with no published RθJA (40–60 °C/W typical on good copper), that is +60 to +110 °C over ambient, against Tj max **150 °C**. It works, hot, with little margin.

**Maximum-threshold FET (VGS(th) = 2.5 V, +0.7 V on typical):**
- Its overdrive at a given VGS is 0.7 V less. At the typical 3.1 V refresh threshold, the overdrive is 0.6 V instead of 1.3 V.
- First-order (VGS − Vth)² scaling of the typical fig. 4 saturation current (about 15–17 A at 1.2 V overdrive) gives about **4 A**.
- So such a part **leaves the ohmic region at 10 A before the refresh comes**, even with a typical BQ25756.
- With a BQ25756 at the 2.7 V threshold minimum, the overdrive is 0.2 V: essentially off.
- In the last part of every refresh period (roughly VGS 3.3 V → threshold, about 30–45 % of the sweep), Q402 then runs with VDS in volts at about 10 A: tens of watts. It thermally fails within seconds.
- Nothing limits this: IBAT_REV and IAC_DPM regulate average current. The BQ25756 refreshes on the gate voltage, not on VDS.

### Verdict on B-1

- With guaranteed datasheet limits on both parts (VGS(th) max 2.5 V, refresh threshold 2.7–3.9 V), the high-side FET at 100 % duty is not guaranteed to stay ohmic at 9–10 A.
- It works with typical parts (hot), and fails with a high-threshold FET.
- "Works only by luck" under normal 100 W operation: **MAJOR is correct.**

**Amendments to B-1:**
1. The start voltage is about 4.0–4.2 V: D405 conducts the refresh pulse at hundreds of mA, not at the 10 mA VF test point. This strengthens the finding.
2. Fig. 6's 3.0 V Miller plateau at 20 A is direct datasheet evidence that VGS around 3 V is at the saturation edge for a typical part. Cite it beside fig. 4.
3. The B-2 loss table should carry the B-1 penalty for Q402: about 1.4–1.8 W at 9.6 A hot for a typical part, not 1.25 W.
4. **Fix (a) is the right one.** The comparator floor (2.7 V) is independent of DRV_SUP and of the size of C412/C413, so neither of those helps. The replacement for Q401/Q402 must keep RDS(on) low at **VGS = 2.7 V guaranteed**, which needs VGS(th) max of about 1.5–1.8 V and an RDS(on) spec at 2.5 V. The low sides can stay PGQ04N070.
5. **Fix (c) (ask TI whether there is periodic refresh) should not block the change.** The datasheet describes only the comparator, and any design must work to the datasheet.

**Confidence:**
- Verified: table 6-1, the refresh threshold, REGN, the PGQ limits, figs. 4 and 6.
- Inferred: the D405 VF at the refresh current, the droop rate, and the first-order saturation scaling.

---

## Q2: A-2 [MAJOR], the EV2400 procedure with 3V3 dead. Verdict: **AGREE that the overstress is real; severity AGREE MAJOR** (amended)

### Trace (verified from `nets.txt` and `parts.txt`)

- **3V3 → R312 (0 Ω) → net `/MCU and NTCs/SMB_PU`.** That net holds R304.1, R305.1, R312.2 and TP308.
- **R304 (4.7k) → SCL** = U301.9 DIO6, U302–U306 SCL, U401.9/U501.9 I2Ct_SCL, R115 (100 Ω) to the gauge SMBC, J103.2, TP303.
- **R305 (4.7k) → SDA** = U301.10 DIO8, the TMP1075s, U401.8/U501.8 I2Ct_SDA, R116 to the gauge SMBD, J103.3, TP302.
- **U301 VDDS** = `3V3_MCU` (U301.6/7), joined to 3V3 by R301 (0 Ω).
- **R312 Notes:** "Remove to isolate the SMBus pull-ups from 3V3 (dead 3V3 = 4.7k pull-downs); then feed TP308 for EV2400 work."
- **`bringup-config-checklist.md` §2 step 4:** "With 3V3 down, remove R312 and feed TP308."

### Abs max (verified)

- SWRS349A §7.1: "Voltage on any digital pin: −0.3 to VDDS + 0.3, max 4.1 V."
- No injection-current rating is given, so any clamp current is outside the specification.
- With VDDS = 0 and TP308 = 3.3 V, DIO6 and DIO8 see up to 3.3 V through 4.7k. That is **3 V over the limit**.

### What actually happens (inferred arithmetic)

- **Current path:** each line injects (3.3 − VF − VDDS) / 4.7k into the pin's upper ESD diode, at most about 0.6 mA, about 1.2 mA for the pair.
- **Where it goes:** VDDS is not isolated. Through R301 it is the whole 3V3 rail:
    - TMP1075 ×5 V+;
    - both TPS25751 VIN_3V3, and through their switches LDO_3V3 with the TPD4S201s (112 µA each);
    - R313, R417/R517, R421–R423, R521–R523;
    - the TPS62177 output.
- **Resulting state:** the rail floats up to wherever the load matches the injection, roughly 1.5–2.5 V.
    - That is around the TPS25751 VIN_3V3 UVLO (2.56–2.76 V rising, 2.44–2.64 V falling).
    - The TPS25751s can cycle in and out of boot, and the CC2340 sits in brown-out or a partial boot.
- **Functional consequence A did not list:** several half-powered parts sit on the **same SDA/SCL bus that the EV2400 is talking over**: the TPS25751 I2Ct (pin structure unspecified, my C-10 answer to A), the TMP1075s and the CC2340.
    - A part in an undefined power state can hold or glitch the bus. That puts the gauge data-flash session itself at risk, including a corrupted write during gauge configuration.

### Is it MAJOR, given it's a documented bench procedure?

Yes. The documentation is what makes the condition credible rather than hypothetical, and it is not a corner case:
- On every fresh board, the gauge FETs are off (`Manufacturing Status Init` = 0x0000; checklist §2 step 2).
- So PACK_P and 3V3 are dead unless J104 is on.
- Checklist §2 step 4 then tells the user to do exactly this, on every board, before the gauge is configured.

That meets the brief's MAJOR definition: an abs-max violation under a credible condition. What softens it:
- The injection is current-limited to sub-mA by the 4.7k resistors, so permanent damage is unlikely.
- The fix needs no hardware.

**Amendments to A-2:**
1. Add the shared-bus functional risk (above). It argues for the procedural fix even if the CC2340 survives.
2. The preferred procedure (J104 on, so 3V3 is up, keeping R312 fitted) is available. D104 feeds PACK_P from J104 (`Net-(D104-A)` → D104 → PACK_P). Checklist §2 step 3 already lists J104 as a wake source, so the fix is a rewrite of step 4 plus the R312 Notes.
3. Once that rewrite is done, the residual is DOC. The lead can record "MAJOR, procedure fix only, no rework".
4. Extra DOC, outside my scope but found on the way: **R302's Notes are stale.** R302 is the NRST pull-up (`/MCU and NTCs/NRST`: R302.2, U301.14 RSTN), but its Notes say "TPS25751 I2Ct_IRQ is open drain and needs an external pull-up". I leave this to A or D.

**Confidence:**
- Verified: the trace, the abs max, the checklist text.
- Inferred: the rail operating point and the bus behaviour.

---

## A-1 [MAJOR], DIO21 bootloader trigger. Verdict: **AMEND → CONFIG (+ MINOR for the R313 level)**

**Verified:**
- TPS62177 SLEEP has an internal pull-down: ILKG_SLEEP = 1.4 µA at VSLEEP = 3.3 V, about 2.36 MΩ equivalent ("connected to a pull down resistor internally", tps62177 p.3 and EC table).
- The R313 (470k) divider gives 3.3 × 2.36 / (2.36 + 0.47) = **2.75 V**, against CC2340 VIH = 0.8 × VDDS = 2.64 V (cc2340 §7.18). That is 0.11 V of margin, before the internal resistor's tolerance.
- So A's steady-state arithmetic is right.

**Not verified:** that DIO21 is the default FCFG bootloader trigger. A cites the TI SDK web page; the CC2340R5MODA datasheet in `datasheets/` says only that "the ROM also contains a serial (SPI and UART) bootloader" (§8.4). I can neither confirm nor refute the pin offline.

**Why CONFIG rather than MAJOR:**
- A's own analysis says the stranded state is **safe**: pins hi-Z, CHG_INH inhibited, EN_5Vx off.
- The required fix is a SysConfig CCFG setting (bootloader forbidden, or trigger moved or disabled). That is the brief's CONFIG definition: "a firmware … item the hardware depends on".
- On the dev board, recovery exists: SW301 on NRST, and J301.
- The race timing (τ ≈ 6–8 µs against "a few microseconds") is inferred by A.
- With the CCFG fix in place, the hardware is correct as drawn. Without it, the failure is a recoverable hang, not damage.

**Keep as MINOR:** R313 → 220k (A's optional item 3). It raises the level to about 3.0 V and restores VIH margin for anything else that reads DIO21.

**For the product, not this board:** with no reset button and no J301, the same configuration miss would strand a sealed unit. Carry the CCFG item into the production checklist.

---

## Other items with evidence from my area

### B-14 [NOTE], "Never configured (blank EEPROM): the BQ25756 starts in default mode and charges". Verdict: **AMEND**

- **Verified:** TPS25751 table 8-6 (SafeMode, which both ports are strapped to): "The device does not enable the sink path. USB PD is disabled until configuration is loaded."
- §8.4.1: "If no EEPROM is detected, then the device waits for an external host to load a configuration."
- With a blank or absent EEPROM, the PPHV switch never closes. The BQ25756 never sees VAC from USB, so it cannot start charging from USB in default mode, whatever CE says.
- The risk B lists (IAC_DPM at maximum, 5.8 A against a 3 A PDO) arises only with a **configured** bundle that omits Q12/Q13, which is my C-11.
- Reword the B-14 bullet: "Blank EEPROM: the TPS25751 (SafeMode) never closes PPHV, so no USB charging. With a configured bundle but no Q12/Q13, IAC_DPM stays at the pin ceiling (C-11)."

### B-6 [MINOR], FET and inductor voltage margin. Verdict: **AGREE**, with an addition

- B's table uses the SMAJ22A VC of 35.5 V. The same clamp is above the TPS25751 VBUS_IN/PPHV abs-max of **28 V** (§6.1.1/6.1.2) before it ever reaches the FETs. That is my C-4: TI recommends a flat-clamp TVS2200.
- So a TVS2200 would improve both B-6 (35.5 → about 28 V peak on PPHV) and C-4. Suggest the lead merges the fix decision.
- B's point stands that the surge reaches the bank only with the sink switch closed.

### B-2 [MINOR], FET loss budget. Verdict: **AGREE**, amended by Q1

- Add the B-1 low-VGS penalty to Q402's row: 1.4–1.8 W at 9.6 A hot for a typical part.
- This makes the IBAT_REV = 10 A and TS settings load-bearing, as B says.

### B-7 [MINOR], TPS62933 headroom. Joint item, owned by me (C-5). B's numbers are mine. Not re-argued.

### D-3 [MINOR + DOC], rev A7 idle budget. Verdict: **AGREE**

- D uses my TPD4S201 figures (112 µA typ, 160 µA max each, TPD4S201-Q1 §5.7).
- D's 235–245 µA pack idle includes them plus the TMP1075s and R313. I re-added D's terms: 220 µA (my C-2 alone) + about 30 µA of TMP1075 at 3.3 V (about 9 µA at the pack) + R313's 7 µA (about 2 µA at the pack) ≈ 231 µA. That is consistent.

### D-4 [CONFIG / MINOR], TPS62177 sleep-mode overload on a PD attach. Verdict: **AGREE**

- What I gave D:
    - The TPS25751 has no documented misbehaviour between the 2.44–2.64 V UVLO and the 3.0 V operating minimum, and no switchover to the VBUS LDO once booted (§8.3.2; the dead-battery state latches until DBfg).
    - The liquid-detect pull-up reading droops with the rail (my C-9).
- The attach load (3–6 mA active sink, §6.7) arrives within ms of CC attach, before the MCU can react. So "exit sleep on IRQ" only works if the TPS62177's own sleep-to-normal transition (PG-triggered, D's §8.4.4) is fast enough. **Keeping normal mode whenever a cable could be attached is the safer config.**

### No objection, not re-derived in depth

- A: A-3 to A-12. Outside my datasheets, except A-3's IRQ latching, which matches my C-10 (TRM §3.2.6).
- B: B-3, B-4, B-5, B-8 to B-13, B-15 to B-17.
- D: D-1, D-2, D-5 to D-18.
- I would expect no disputes from my side on these.

---

## Verdict summary

| Item | Severity claimed | Verdict | Short reason |
|---|---|---|---|
| B-1 | MAJOR | **AGREE (MAJOR)**, amended | Refresh floor 2.7–3.9 V with no forced refresh; PGQ Vth max 2.5 V leaves the FET at about 4 A saturation at 10 A; works only with typical parts. Start voltage about 4.0–4.2 V. Fix (a). |
| A-2 | MAJOR | **AGREE (MAJOR)**, amended | Abs max VDDS + 0.3 V violated on the standard fresh-board path; adds a shared-bus functional risk. Procedure-only fix; residual is DOC once the checklist is rewritten. |
| A-1 | MAJOR | **AMEND → CONFIG** (+ MINOR R313) | Safe, recoverable hang fixed by a CCFG setting; DIO21 default not verifiable offline; VIH margin 0.11 V verified. |
| B-14 | NOTE | **AMEND** | Blank EEPROM plus SafeMode means PPHV never closes, so there is no default-mode USB charging. |
| B-6 | MINOR | AGREE (+ link to C-4) | The TVS clamp is above the TPS25751's 28 V before the FETs. |
| B-2 | MINOR | AGREE, amended | Add the B-1 penalty to Q402. |
| D-3 | MINOR + DOC | AGREE | Consistent with C-2. |
| D-4 | CONFIG / MINOR | AGREE | Keep normal mode while a cable can attach. |
