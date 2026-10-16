# Reviewer D: round 2 challenge

Every verdict below is re-derived from the datasheets. Sources are the same as in D-findings.md, plus:
- `scratch-b/pgq04n070.pdf` (JinYu V2.0). I read its p.2 table and rendered pages 3 and 4 (figs. 4 and 8).
- `bq25756.pdf` (SLUSEN5A): §5.5 PWM drivers, §6.3.3.3, Table 6-1.
- `tps25751.pdf` §6.12, §6.7.
- `tps62177.pdf` EC table, rendered to `scratch-d/png/tps62177_ec.png`.
- `cc2340r5moda.pdf` §7.17.2, §8.11.
- The TI SDK 8.10 CCFG page (fetched): "Default FCFG bootloader … Pin Trigger enabled for DIO 21, active low on reset", and "the standard selection".

Verdict summary:
- **Q1, B-1:** AGREE, stays MAJOR. AMEND the reasoning: it bites even with a typical FET if the BQ25756 refreshes near its 2.7 V minimum.
- **Q2, A-1:** AMEND to CONFIG (blocking) + MINOR hardware margin. The board is safe in the stuck state.
- **Q3:** C-2 AGREE (MINOR). C-6 AGREE (MINOR), with a hold-up number.
- **Other items:**
    - A-2 AGREE (MAJOR) with an addition.
    - A-3/A-4/A-5/A-6/A-7/A-9 AGREE.
    - B-2/B-4 AGREE. C-4 AGREE. C-7 AGREE.

---

## Q1. B-1 [MAJOR]: can the PGQ04N070 high side drop out of full enhancement at 100 % duty?

**Verdict: AGREE (MAJOR). AMEND the evidence:** the failure does not need a maximum-threshold FET.

**1. Which FET is held on (verified).**
- BQ25756 Table 6-1: in BOOST mode the "HS BUCK FET" (the input-leg high side) is ON continuously. In BUCK mode the "HS BOOST FET" is ON.
- In reverse mode the battery leg is the input leg. 20 V out of an 11–16.8 V pack is always boost, so Q402 (battery-side HS, HG2) carries the whole battery current with no off-time.
- §6.3.3.3: the only forced pulse in boost mode is the output-side high side, "forced to turn on for 225 ns in each switching cycle". That is Q401, not Q402. So nothing periodically recharges BTST2.
- The same holds for forward buck charging (Q402 ON, ≤ 5.8 A) and forward boost from 5–9 V (Q401 ON).
- **This is the product's headline mode** (100 W out at 20 V), not a corner case.

**2. The gate floor is the refresh comparator (verified).**
- §5.5: VBTST2_REFRESH = 2.7 / 3.1 / 3.9 V, "BTST falling, VBTST − VSW when low-side refresh pulse is requested".
- While Q402 is on, VGS(Q402) = VBTST2 − VSW2 (HIDRV2 is tied to BTST2), less the 0 Ω R446.
- So VGS saw-tooths between the post-refresh level and the comparator threshold. B gets about 4.24 V for the top (REGN 4.8 V min − R420 drop − D405 VF), and I accept that arithmetic.
- The droop *rate* is set by unspecified BTST quiescent current plus D405 leakage. It changes how often the refresh happens, not the floor: a larger C413 stretches the period but keeps the same fraction of time near the floor.

**3. What the PGQ04N070 does at that floor (typical part, read from the rendered curves).**
- **Fig. 4** (output characteristics, 25 °C, typical), at ID = 12.6 A:
    - VGS 4.5 V: about 7 mΩ, so VDS ≈ 0.09 V and **P ≈ 1.1 W**.
    - VGS 4.0 V: VDS ≈ 0.11 V, P ≈ 1.4 W.
    - VGS 3.5 V: VDS ≈ 0.2 V, P ≈ 2.5 W.
    - **VGS 3.0 V:** the curve is already bending over (≈ 11 A at 0.5 V, ≈ 13.5 A at 1.0 V, ≈ 17 A at 2 V). 12.6 A needs **VDS ≈ 0.8 V**, so **P ≈ 10 W**.
- **Fig. 8** (transfer at VDS = 5 V):
    - At 25 °C, ID = 10 A needs VGS ≈ 2.75 V and 20 A needs about 3.0 V.
    - At 125 °C the curve shifts about −0.35 V. A hot part at VGS = 3.0 V behaves roughly like a cold part at 3.35 V less the mobility loss: about 0.3 V VDS and **≈ 4 W**.
- **Time-averaged over a linear sawtooth** from 4.24 V down to the typical 3.1 V refresh: P ≈ 1.1–1.4 W for the first two thirds of the period, rising steeply to about 8 W at the bottom. The average is **≈ 3 W cold, ≈ 2–2.5 W hot**, at 12.6 A.
    - At the 10 A IBAT_REV point it is about 2 W (P scales a little faster than I² because VDS bends).
    - B-2's 1.36–2.16 W assumes 4.5 V drive. The real figure is roughly 1.5–2× that.
- **With the BQ25756 refreshing at its 2.7 V minimum, even a typical PGQ04N070 cannot carry 12.6 A.**
    - Fig. 8 typical at VGS 2.7 V gives about 8–9 A *at VDS = 5 V*. Below the needed current the FET leaves the ohmic region.
    - The current path is drain → source (VBAT → SW2). The body diode (anode SW2) is reverse-biased, so nothing bypasses the channel.
    - The loop keeps demanding current, SW2 falls and VDS climbs toward VBAT.
- **With a maximum-threshold part** (VGS(th) 2.5 V max against 1.8 V typ, p.2), shift fig. 8 by +0.7 V. At VGS 3.0 V it passes about 1 A.
- **What happens next (inferred):** D405 only recharges C413 when SW2 drops to about DRV_SUP − VF − VC413 ≈ 1 V. So the stage self-refreshes only after the FET has already dropped most of VBAT across itself. The result is a relaxation oscillation with 10–100 W pulses in Q402. Fig. 9 SOA (Tc = 25 °C) allows only about 3 A at 10 V for DC/10 ms.
- I see no mechanism in the datasheet that keeps the gate above the comparator floor.

**4. Answer to the coordinator's number:** at VGS = 3.0 V and 12.6 A, a typical PGQ04N070 dissipates **≈ 10 W at 25 °C (≈ 4 W hot)** while the gate sits there. That is against a 4.46 °C/W RθJC and no published RθJA, so tens of °C per ms of dwell. With a maximum-threshold part, or a 2.7 V-refresh controller, it cannot carry the current at all.

**5. Grade and fix.**
- MAJOR holds: the board "works only by luck" (Vth and refresh-threshold lottery) in its main 100 W mode.
- B's fix (a) is right: a high side with VGS(th) max ≤ 2.0 V and RDS(on) specified at 2.5 V.
- I'd add an interim CONFIG: until the FET is changed, set **IBAT_REV ≈ 5 A**. At 5 A, fig. 4 at VGS 3.0 V gives about 0.15 V and about 0.75 W. That caps reverse output near 60 W at 12 V. Bring-up check (b) as B wrote.

**Confidence:** fig. 4 and fig. 8 readings and Table 6-1/§5.5 are verified. The oscillation mode and the hot-part estimate are inferred.

---

## Q2. A-1 [MAJOR]: stuck in the ROM bootloader after a reset from S2. What is the board state, and does it change the grade?

**Verdict: AMEND. The board is safe. Grade it CONFIG (blocking: must be done before first flash) + a MINOR hardware margin (R313).** The trigger risk is wider than A states (every power-on, not only resets from S2), but the cure is one CCFG setting.

**1. The premise is verified.** The SDK 8.10 page says the default and "standard" selection is "Default FCFG bootloader … Pin Trigger enabled for DIO 21, active low on reset". DIO21 is 3V3_SLEEP. A firmware build with default SysConfig therefore ships with the trigger armed.

**2. The level margin is worse than "typical", and applies at every boot (verified, new).**
- TPS62177 EC table (rendered): **ILKG_SLEEP = 1.4 µA is a *typical* value with no max**. VH = 0.9 V.
- The pull-down is therefore unbounded on the strong side. R313 470k gives 2.75 V *typical*, against CC2340 VIH = 0.8 × VDDS = 2.64 V.
- A part whose pull-down is about 30 % stronger reads below VIH on *every* power-on. That is not only after an S2 reset.
- Erratum for my own D-4: I wrote "1.4 µA max". It is typical. I'll correct it in round 3.

**3. Timing of the S2-reset case (verified, new).**
- §7.17.2: Reset/Shutdown → Active is **350–450 µs**, "includes device ROM bootcode execution time". R313 recharges the pin with τ ≈ 7 µs (A's figure).
- So if the pad is released at reset, it is long settled before the ROM samples it. The pure RC race is unlikely.
- The live risks are the steady-state VIH margin above, and an I/O latch that survives the reset.
- §8.11: "In Shutdown mode … the I/Os are latched". Wake from Shutdown is a reset through the ROM. If firmware ever enters Shutdown with DIO21 low, the trigger is asserted *deterministically* at the next boot.
- Firmware rule: drive DIO21 high before Shutdown and before any deliberate reset.

**4. Board state while the MCU sits in the ROM bootloader.** All DIOs are inputs unless the ROM selects them. Per A's N-3, index 2 has UART RX DIO22 (not bonded) and TX DIO20, which is only enabled after a host accesses it.

| Net | State | Effect |
|---|---|---|
| CHG_INH (DIO24) | hi-Z (SPI CLK input in index 2) | R417/R517 47k hold CE high, so **both chargers inhibited** |
| EN_5V1/EN_5V2 (DIO3/DIO4) | hi-Z | R432/R532 100k against the TPS62933 Ip 0.7 µA gives 0.07 V < 1.1 V, so **PP5V off**. Attach detection still works from LDO_3V3 (TPS25751 §6.12 VOC_3.3, "unattached", VLDO_3V3 > 2.302 V). But vSafe5V needs PP5V, so **no new source contract** (see C-6) |
| 3V3_SLEEP (DIO21) | hi-Z | R313 → about 2.75 V > VH 0.9 V, so the **TPS62177 is in normal mode**. The rail is fine, and the 15 mA sleep limit doesn't apply |
| LED (DIO12) | hi-Z (SPI POCI input) | off |
| IRQ_N (DIO11) | input | sources latch low unserviced (A-3); harmless |

- **Cells:** protected independently by U101 (COV/CUV/OCD/SCD) and U102/F102. Neither depends on the MCU.
- **Drain while stuck (inferred):**
    - CC2340 in ROM polling at about 2–3 mA (§7.9 active about 2.6 mA at 48 MHz), plus the 3V3 idle of D-3 (about 0.4 mA) and TMP1075s at their default rate (30 µA).
    - That is about 3 mA at 3.3 V, or 0.8–0.9 mA at the pack, plus the gauge.
    - A full 5.8 Ah pack runs to CUV in about 6–7 months. CUV then opens DSG, PACK_P collapses and 3V3 power-cycles, which re-boots the MCU.
    - The WDT is not running in ROM (it is enabled by application firmware), so there is no faster self-recovery.
- **Safe?** Yes. No charging, no 5 V sourcing, cells protected. It fails in the "no function" direction, not the unsafe one.
- **Recovery:**
    - On the dev board: press SW301 (the reset re-samples DIO21 while R313 holds it, so this works when the level margin is OK), or use J301.
    - In the product: no button, and USB attach doesn't reset the MCU. It stays dead to BLE and PD supervision until CUV or service.

**5. Grade.**
- The hardware needs no rework wire: one CCFG choice removes the hazard entirely ("Any bootloader forbidden" for production, or the trigger moved to DIO3 active-high as A proposes). And the stuck state is safe.
- So by the BRIEF scale this is **CONFIG**, mandatory and blocking, on the checklist before the first flash.
- I'd *add* a **MINOR** for the hardware margin: R313 → 100k gives 3.3 × 2.36/(2.36 + 0.1) = 3.17 V typical. With a pull-down twice as strong as typical it is still 3.04 V, above VIH. It costs 33 µA in S2 instead of 7 µA. If the CCFG fix is done, A's 220k is enough.
- If the lead prefers to keep MAJOR because the default build is armed, I wouldn't dispute it hard. The deciding fact is that the board is safe in that state.

**Confidence:** pin states verified from the netlist and datasheets. The SDK default and the ILKG typ-only are verified. The ROM sampling instant and the latch behaviour across a WDT reset are not documented, so inferred.

---

## Q3. C-2 and C-6 from the power-tree side

### C-2 [MINOR] TPD4S201 always-on 3V3 load: AGREE (MINOR)
- **Re-derived:**
    - TPD4S201-Q1 §5.7: IVPWR 112 µA typ, 160 µA max, on each LDO_3V3.
    - TPS25751 §6.6: LDO_3V3 = VIN_3V3 through RLDO_3V3 1.4 Ω whenever 3V3 is up (not dead-battery). So the current is drawn from the TPS62177 rail.
    - At 14.4 V, the sleep-mode efficiency I assumed (80 %) gives **+62 µA at the pack**, which matches C.
- **Power-tree consequences checked:**
    - (a) **Ship mode and FETs-off are unaffected:** 3V3 is off, so VPWR is unpowered there.
    - (b) **Dead-battery start still works:** VPWR then comes from the TPS25751's VBUS LDO, which is what TPD4S201 §7.3 asks for.
    - (c) **15 mA sleep-mode margin:** 0.32 mA max is negligible.
    - (d) **Share of the idle budget:** together with the TPS25751 sleep current it is 336 µA of the about 400 µA 3V3 idle (D-3). That is the largest single block in the idle budget.
- MINOR is right: within ratings, a cost decision. My D-3 rolls it into the rev A7 budget.

### C-6 [MINOR] Sourcing depends on the MCU via EN_5Vx: AGREE (MINOR), with numbers
- **Power-tree re-derivation:**
    - PP5V is produced only by U404/U504 TPS62933, gated by EN_5Vx. R432/R532 pull down, so the buck is off in MCU reset, unprogrammed, bootloader (Q2) and brown-out.
    - TPS25751 §6.12: the *unattached* Rp works from LDO_3V3 (VOC_3.3, VLDO_3V3 > 2.302 V), so attach detection survives EN low.
    - But IRp1.5/IRp3.0 are specified only for 4.75 V < VPP5V < 5.5 V, and VOC_5 (attached) needs VPP5V > 3.802 V. vSafe5V comes from PP5V.
    - So **every new source attach** needs the MCU to raise EN_5Vx within the Type-C tVBUSON window, not just the 5 V contract. That is a stronger statement than C's.
- **Hold-up during an MCU reset under an existing 20 V contract (inferred arithmetic):**
    - PP5V bulk: C443 220 µF polymer plus C441/C442 22 µF + C407 10 µF (about 25 µF effective at 5 V) ≈ 245 µF.
    - Load with the buck off: R433/R434 divider 5.08 V/127k = 40 µA, Rp 330 µA, and VCONN for an e-marker. Take about 5 mA total.
    - dV/dt ≈ 5 mA/245 µF ≈ 20 V/s. PP5V falls from 5.08 V to the 4.75 V IRp floor in **≈ 16 ms**, and to the 3.8 V VOC_5 limit in about 64 ms.
    - The CC2340 reboots in 0.35–0.45 ms (§7.17.2). If firmware drives EN_5Vx high in its first few ms, before the BLE stack, the TPS62933 soft start (C439 33 nF) restores PP5V and a 20 V contract can ride through a WDT reset.
    - If the MCU is stuck in the ROM (Q2) or unprogrammed, it can't.
- **Proposed addition to C's fix:** a firmware rule. "Restore EN_5Vx from the attach state as the first action after any reset: read the TPS25751 status, or default EN_5Vx high when VBUS is present." Plus C's bring-up test.
- MINOR is the right grade. A test-and-firmware item, no hardware fault.

---

## Other MAJORs

### A-2 [MAJOR] EV2400 / TP308 with 3V3 dead puts 3.3 V on unpowered CC2340 SDA/SCL: AGREE (MAJOR), with an addition
- **Re-derived:**
    - CC2340 §7.1 limits DIO pins to VDDS + 0.3 V. With VDDS = 0, 3.3 V through 4.7k injects about 0.6 mA per line. This is a documented procedure, so the condition is credible, and it meets the BRIEF's MAJOR definition (abs max under a credible condition).
    - Both the procedure and the R312 Notes direct it.
- **Addition, answering A's open question:**
    - The review 1 decision Q5 (`schematic-review-2026-10-12.md`) records that **"EV2400 pull-ups are 20 k to 3.3 V"**.
    - So even with R312 removed and TP308 left unfed, a connected EV2400 alone injects (3.3 − 0.6)/20k ≈ 0.13 mA per line into the dead CC2340 (inferred from that record; not re-measured).
    - The only clean procedure is A's: gauge work with 3V3 up (J104 powering PACK_P), and the CC2340 held in reset through J301 nRESET or idle on the bus.

### B-1: see Q1. A-1: see Q2.

---

## MINOR / CONFIG items

| Item | Verdict | Re-derivation |
|---|---|---|
| A-3 [CONFIG] latched level sources on edge wake | AGREE | Independently matches my D-2 (BTP latched until BTPDischargeSet/ChargeSet, TRM). The TPS25751 INT_EVENT1 reset value 0x08 is C's. The firmware rule "never Standby with DIO11 low" is necessary. |
| A-4 [CONFIG] TMP1075 SD against ALERT | AGREE | My D-3 budget used the same §6.5 numbers: 10/20 µA default, 2.7 µA at R = 11, 0.37/3.5 µA in SD. |
| A-5 [MINOR] R314 leakage margin | AGREE | AO3400A IDSS 1 µA/25 °C and 5 µA/55 °C at 30 V (ao3400a p.2). VIH 2.64 V leaves 6.6 µA at 100k. 47k is a sound change. |
| A-6 [MINOR] SMBus rise time | AGREE | The gauge forces 100 kHz anyway ([XL] = 0, TRM SBS Configuration). 3.3k keeps the gauge VOL inside 0.4 V at 1 mA (DS 7.11: 0.4 V at 1.5 mA). |
| A-7 [MINOR] J303 1–2 shunt | AGREE | Q103 AO3400A is about 48 mΩ at VGS 2.5 V, so a shunt shorts 3V3 through it. The TPS62177 current limit is 1.0 A typ / 1.2 A max (EC table). Q103 sees about 1 A × VDS, fine short-term. The TMP1075 ALERT at 3 mA spec would be overstressed. |
| A-9 [MINOR] J302 back-power | AGREE (duplicate of my D-6; A primary) | |
| B-2 [MINOR] FET loss budget | AGREE, and Q1 adds about 1.5–2× for the refresh sag on Q402 | |
| B-4 [MINOR] polymer leakage | AGREE | It only matters with FETs on. In ship mode PACK_P is isolated. Carried in D-3. |
| C-4 [MINOR] SMAJ22A clamp 35.5 V | AGREE | 35.5 V at 11.3 A Ipp (LCSC R+O listing). At cable-ring energies the clamp sits nearer VBR (24.4–27 V), so MINOR is right, not MAJOR. |
| C-7 [MINOR] VBUS short at 20 V through PPHV | AGREE | 130 µF × 20 V gives 26 mJ, plus the reverse-mode output. TI uses the same topology on the EVM, so MINOR with a bring-up test. |

No DISPUTE on any item I read.
