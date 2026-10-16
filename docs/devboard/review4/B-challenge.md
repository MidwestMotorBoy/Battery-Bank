# Reviewer B: round 2 challenge

Scope: the lead's questions Q1 (A-1), Q2 (C-1) and Q3 (C-4) in depth, then every other MAJOR (A-2) and the MINOR/CONFIG items that touch my area or that I think are mis-graded.

Every verdict below comes from my own reading of the source, not from the finding's text. Scratch files are in `scratch-b/`:

- `tps62177.txt` and the EC table render `tps62177_sleep.png`;
- `cc2340.txt`;
- `tpd4s201-q1.txt` and `tpd4s201.txt`;
- `smaj22a-ro.pdf` (the fitted LCSC C41376403).

---

## Q1, A-1 [MAJOR]: DIO21 as the CC2340 ROM-bootloader trigger. Verdict: **AMEND → CONFIG (required), with a hardware MINOR**

**Is the trigger pin set by hardware or by the CCFG?**

The trigger pin comes from the boot configuration, not from silicon.

- **TRM SWCU193 §8.5.1.2** (TI web viewer, page GUID-93C18248…): "Configuration of the ROM Bootloader is done between the FCFG and the CCFG. There are defaults that are set in the FCFG that will take effect if a valid CCFG is not present on start-up."
- **SWCU193 bootCfg table** (TI web viewer and the SDK `hapi.h` description; the same fields appear in the Zephyr `ti,cc23x0-ccfg-flash` binding). CCFG `bootCfg.pBldrVtor` selects the behaviour:

    | pBldrVtor | Effect |
    |---|---|
    | `USE_FCFG` (0xFFFFFFF0) | ROM serial bootloader with the FCFG parameters |
    | `FORBID` (0xFFFFFFFC) | bootloader disabled |
    | `UNDEF` (0xFFFFFFFF) | ROM bootloader with the CCFG parameters |
    | a flash address | user bootloader |

    `bldrParam` carries `pinTriggerEnabled`, `pinTriggerDio` and `pinTriggerLevel`.
- **SDK 8.10 CCFG page** (the one A cites, re-read): "Default FCFG bootloader is the standard selection". It enables index 2 (UART DIO22/DIO20) and the pin trigger on DIO21, active low. The page also says that "Default FCFG bootloader, with CCFG settings" lets the user pick custom values, and that "Any bootloader forbidden … will fully disable the bootloader".

**What this means:**

- DIO21 active-low is the **FCFG default**. It applies to a blank or invalid CCFG, and to any CCFG that points at the FCFG (`USE_FCFG`), which is what the SysConfig default selection writes.
- The firmware image always carries its own CCFG. So whether DIO21 is a trigger at all is a build setting the project controls, exactly like an option byte.
- A blank part goes to the bootloader anyway (nothing to boot), so the hardware level on DIO21 doesn't matter there.
- A's failure (reset from S2 → stranded in the ROM bootloader) only happens if the firmware ships with the SDK default selection.
- By the brief's scale that is **CONFIG**: "a firmware … item the hardware depends on". The consequence if missed is serious (the pack loses supervision until a power cycle). So it should be a **required** checklist line, called out at the top of the firmware section.

**The R313 level, redone.**

- **TPS62177 EC table** (rendered, `tps62177_sleep.png`):
    - VH (high-level threshold) is **0.9 V** in the MIN column.
    - VL is 0.3 V MAX.
    - ILKG_SLEEP is **1.4 µA in the TYP column, with no max**.
    - §8.4.4: "a pulldown resistor internally connected to the SLEEP pin".
- **TPS62177 side:**
    - Treating the pull-down as resistive, R ≈ 3.3 V / 1.4 µA = 2.36 MΩ (typ).
    - V = 3.3 × 2.36 / (2.36 + 0.47) = **2.75 V typ**, far above VH 0.9 V.
    - Even if the pull-down were 10× stronger (236 kΩ), V = 1.1 V > 0.9 V. The buck side is robust.
- **CC2340 side:**
    - VIH = 0.8 × VDDS (SWRS349A §7.18.4, `cc2340.txt` l.3083–3086).
    - The divider ratio is VDDS-independent: 2.36/2.83 = **0.834 × VDDS typ**. That passes VIH by only 3.4 % of VDDS (0.11 V at 3.3 V).
    - The pin reads high by spec only while the internal pull-down is at least 1.88 MΩ, i.e. at most about 1.75 µA at 3.3 V, just 25 % above typical. TI gives no max, so the guaranteed margin is zero.
    - A's arithmetic is correct. D-4's "1.4 µA max" is a mis-read (see D-4 below).
- **R313 = 220 kΩ:** 2.36/2.58 = 0.915 × VDDS typ. It still meets VIH with the pull-down up to about 2.2× stronger than typical, at 15 µA instead of 7 µA while S2 holds the pin low.
- The level only matters if DIO21 stays a bootloader trigger. With the CONFIG fix it is just an output, and the level is irrelevant.

**Grade:**

- A-1 → **CONFIG (required)**: CCFG = "Any bootloader forbidden" for production, or "with CCFG settings" with the trigger moved or disabled on the dev board.
- Plus **MINOR**: R313 → 220k as cheap insurance. It is the only hardware part of A-1, and it does not cause the failure on its own.
- A's timing race (RC of about 7 µs against "a few µs") is plausible but inferred. It does not change the grade, because the CCFG removes it entirely.

**Confidence:** verified (TI TRM text on FCFG/CCFG precedence, SDK page, TPS62177 table read from the render). The bootCfg encoding is from TI's TRM table as quoted in the search results; I could not render that page directly.

---

## Q2, C-1 [MINOR]: TPD4S201 VBIAS capacitor rating. Verdict: **DISPUTE the severity → NOTE (+ C-13 DOC stands)**

**What VBIAS can actually reach.** I read three places in the fitted -Q1 datasheet (`tpd4s201-q1.txt`):

- §5.1 abs max (l.350–356): **VBIAS −0.3 to 28 V**; C_CC/C_SBU 28 V.
- §6.3.1, p.11: "The diode clamps used for IEC ESD protection also clamp the ringing voltage during the short-to-VBUS event to limit the peak ringing to **approximately 28 V**."
- §7.2.2.1: VBIAS sits behind a forward-biased "hiding diode" from C_CCx/C_SBUx, in parallel with the central clamp. So VBIAS charges to the clamped C_CC peak minus one diode drop: **≤ about 27–28 V**, not the 40 V unclamped ring.

**Reconciling the three rating statements:**

| Source | Minimum | Recommended |
|---|---|---|
| §5.5 footnote 2 (-Q1; the same text is in the non-Q1 sheet §5.4) | 63 V | 100 V, "to reduce capacitance derating" |
| -Q1 §7.2.2.1 | 50 V | 50 V, from the 40 V unclamped ring |
| Non-Q1 `tpd4s201.pdf` §7.2.2.1 | 28 V | 50 V |

- The non-Q1 sheet says outright: "the internal diode clamps limit the voltage exposed to the C_CCx and C_SBUx pins to around 28V. Therefore, at least a 28V capacitor is required."
- The -Q1 text is the same paragraph with the clamp sentence dropped.
- The footnote's own reason for 63/100 V is capacitance derating, not voltage withstand.
- The binding electrical requirement is the effective capacitance (§5.5 l.555–558): **≥ 0.04 µF**, nominal 0.1 µF. The non-Q1 sheet adds a max of 0.14 µF.

**Our part.**

- C451 is CC0603KRX7R9BB104 (Yageo, 0.1 µF 50 V X7R 0603).
- **Voltage stress:** ≤ 28 V / 50 V = **56 %**. VBIAS only reaches this during a short-to-VBUS event; in normal operation it sits near the CC/SBU levels.
- **Capacitance:** a 50 V 0603 X7R 0.1 µF typically keeps about 60–70 % at 25–28 V (inferred; Yageo publishes no curve in our set). That is about 0.06–0.07 µF, above the 0.04 µF minimum.
- TI's own TPS25751EVM fits 0.1 µF **50 V** (SLVUCP9B fig. 5-5 C69, as C read).

**Grade.**

- The hardware meets the voltage TI's own physics paragraph derives, and meets the capacitance limit. The only violation is of a footnote that contradicts both §7.2.2.1 texts and TI's EVM. **NOTE**, not MINOR.
- C's 100 V swap is harmless and costs cents. I'd list it as an optional improvement.
- C-13 (DOC) stands: the Notes property should cite the 28 V clamp and the 0.04 µF minimum, not the 40 V ring.

**Confidence:** verified (all three datasheet passages and the abs max read). The X7R bias retention is inferred.

---

## Q3, C-4 [MINOR]: what the fitted SMAJ22A clamps to in practice. Verdict: **AGREE MINOR, AMEND the evidence**

**The fitted part's datasheet** (LCSC C41376403; Zhuhai Hongjiacheng "R+O" SMAJ series Rev 2.2; `scratch-b/smaj22a-ro.pdf`):

- Row SMAJ22A: VR 22 V, **VBR 24.4–26.9 V at 1 mA**, **VC 35.5 V at IPP 11.3 A (10/1000 µs)**.
- 400 W, VBR temperature coefficient ≤ 0.1 %/°C.
- These are the same as the Littelfuse row. C's "at minimum, confirm VBR" check is satisfied.
- The 35.5 V rating is a **10/1000 µs** figure, not 8/20.

**Clamp at realistic currents.** Using a linear dynamic-resistance model from the worst-case corner:

- Rd ≈ (VC − VBRmax)/IPP = (35.5 − 26.9)/11.3 = **0.76 Ω**. This is pessimistic at low current: a real TVS's knee is softer, so the voltage is lower.
- VBUS stays ≤ 28 V (TPS25751 VBUS/PPHV abs max) only while the TVS current is below:
    - (28 − 26.9)/0.76 ≈ **1.4 A** for a high-VBR part;
    - (28 − 24.4)/0.76 ≈ **4.7 A** for a low-VBR part.
    - Hot, VBR rises 0.1 %/°C, about +1.3 V at 75 °C, which shrinks this further.

**The events, one by one:**

- **Compliant attach.** VBUS starts at vSafe5V. The ring is ≤ 10 V, and the TVS never conducts.
- **IEC 61000-4-2, 8 kV contact.**
    - Charge 150 pF × 8 kV = 1.2 µC into C406 (4.7 µF 50 V, about 2.8 µF effective at 20 V) gives **ΔV ≈ 0.26–0.43 V**. The TVS isn't needed for the energy.
    - The first ~1 ns spike (≈ 30 A, tr 0.8 ns) is set by layout inductance: about 1 nH × 30 A/0.8 ns ≈ 37 V across the cap's ESL plus via. A TVS in SMA, with its own ~1–2 nH, does not stop that either.
    - So ESD performance depends on the C406/C450 placement at the pins, not on the TVS type. This agrees with C's conclusion.
- **Live 20 V hot-plug** (non-compliant always-on source, or a re-plug before the source has discharged).
    - Cable model: ~1 µH, ~0.2 Ω round trip. Into C406 ≈ 2.8 µF effective: Z0 = √(1 µ/2.8 µ) ≈ 0.6 Ω, ζ = 0.2/(2 × 0.6) ≈ 0.17. Unclamped overshoot is exp(−πζ/√(1−ζ²)) ≈ 58 %, so a peak of **≈ 31.6 V**.
    - With the TVS: the cable current near the peak is several amps (20 V/Z0 ≈ 33 A undamped at the zero crossing, decaying). The excess above VBR goes into the TVS, so the TVS current is a few amps for about a µs.
    - From the model above that is about **27–29 V** at VBUS: at the TPS25751 abs max, not safely below it.
    - Estimate only (inferred), but it shows the SMAJ22A protects to about the 28 V line only for low-energy events.
- **Stiff over-voltage** (a faulty or EPR source at 28 V+).
    - The TVS would carry amps continuously. PM(AV) is 1 W on an infinite heatsink, and RθJA is 120 °C/W. It fails short ("typical failure mode is short"), which then protects the downstream parts by crowbarring VBUS.
    - The protection here is the PD protocol (C-15), not the TVS.

**Reconciling with my B-6.**

- B-6 used the same 35.5 V rated clamp, but for the charger FETs (40 V) behind the TPS25751 PPHV switch. That surge only reaches PPHV while the sink switch is closed, and the ~100 µF bank behind 5 mΩ absorbs it.
- C-4's exposure is different: the 28 V parts that sit directly on VBUS (TPS25751 VBUS/VBUS_IN, PPHV through a closed switch, TPD4S201 C_CC in a VBUS-to-CC short).
- Both findings stand. They are the same TVS judged against two different abs-max lines.
- For both, the realistic events (vSafe5V attach, ESD) never push the SMAJ22A into its 35.5 V region. Only a live-20 V hot-plug gets near 28 V.

**Grade.** MINOR is right. The TVS2200-class flat clamp TI recommends (TPS25751 §6.1.1 note 4, EVM U2/U3) is the correct production fix. Option 2 (parallel) is fine on the dev board.

**Confidence:**

- Verified: the C41376403 table row; the TPS25751 note as C quotes it.
- Inferred: the Rd model and the hot-plug estimate, which is first-order.

---

## Other items

### A-2 [MAJOR] EV2400 procedure with 3V3 dead overstresses CC2340 SCL/SDA. Verdict: **AGREE (MAJOR by the brief's letter); the fix is procedural**
- **Re-derived:**
    - SWRS349A §7.1 (`cc2340.txt` l.1483–1485): "Voltage on any digital pin −0.3 to VDDS + 0.3, max 4.1 V". The sheet gives no injection-current allowance, so there is nothing to argue from.
    - With 3V3 = 0 and TP308 at 3.3 V: (3.3 − ~0.6)/4.7k ≈ 0.57 mA per line, about 1.15 mA into the clamps.
    - That back-powers VDDS and, through R301 (0R, "MCU 3V3 link"), the whole 3V3 rail with its tens of µA of loads, so the rail sits around 2–2.5 V.
- R312's Notes property literally instructs this ("Remove … then feed TP308 for EV2400 work", `parts.txt` l.136).
- It is a documented procedure that violates abs max, so it is MAJOR under the brief.
- Physical damage at about 1 mA through ESD clamps is unlikely, but the half-powered rail (TPS25751 VIN_3V3 near UVLO) is a real nuisance.
- A's procedural fix (power PACK_P from J104 so 3V3 is up, keep R312) is sufficient; no hardware is needed.

### A-1 timing aside
Covered under Q1.

### C-5 [MINOR] PP5V buck headroom. Verdict: **AGREE**
- The numbers are mine (TPS62933 §8.5 ILS 2.9 A min; ripple 0.63–1.34 A), and C cites the behaviour correctly.
- One addition: on the TPS62933 side the hiccup off time is 10.5 × tSS ≈ 50 ms (§8.5 thiccup_OFF), and it applies only below 65 % UVP. At 3.3–3.6 A, PP5V sags with foldback rather than hiccups.

### C-7 [MINOR] VBUS short while sourcing through PPHV. Verdict: **AGREE, with the BQ25756 half filled in**
- **Re-derived from my side:**
    - In reverse mode the BQ25756 stops on its own. REG0x1E VAC_REV UVP is 80 % of the VAC_REV target (bq25756 p.47). IAC_REV regulates the 5 mΩ RAC current.
    - The 4-switch stage cannot freewheel from the pack: Q402 is the input switch, and its body diode points SW2 → BAT_SNS_P.
    - So the energy the PPHV switch sees is the bank (≈ 130 µF × 20² / 2 ≈ 26 mJ) plus at most a few µs of converter current. It is not a sustained pack-fed short.
- **Discharge time constant:** C × (RPPHV ~20 mΩ + R424 5 mΩ + traces ~10 mΩ) ≈ 130 µF × 35 mΩ ≈ **4.5 µs**.
- **Peak current:**
    - Limited by loop inductance and the MLCC/polymer ESR. Tens to a few hundred amps for single-µs, which is beyond the 10 A/100 µs pulsed rating in amplitude.
    - The I²t is small: 26 mJ split over the switch, R424 and traces.
- C's bring-up test and the E2E question are the right closure.
- **Note for C's test:** ACP−ACN abs max is ±0.3 V (bq25756 §5.1). 100 A × 5 mΩ = 0.5 V would exceed it, but the R425/R426 10 Ω + C414 0.47 µF filter (τ ≈ 9.4 µs) attenuates a µs pulse well below that. The pin current is limited to < 25 mA. Low risk.

### C-15 / C-1 / C-13
See Q2. No further challenge.

### D-4 [CONFIG / MINOR] TPS62177 sleep-mode overload. Verdict: **AMEND the evidence (conclusion stands)**
- D writes "R313 at 470k against the **1.4 µA max** SLEEP pull-down … gives ≥ 2.75 V". The render of the EC table shows 1.4 µA in the **TYP** column, with no maximum (`tps62177_sleep.png`).
- So "≥ 2.75 V" is a typical value, not a bound.
- The buck-side conclusion still holds by a wide margin: VH is 0.9 V min, and even a 10× stronger pull-down gives 1.1 V.
- But the "verified" CC2340-side reading is not. That is the A-1/Q1 margin (0.834 × VDDS typ against VIH 0.8 × VDDS).
- The rest of D-4 (the 15 mA sleep-mode limit, the PG fallback at 87–93 %) agrees with TPS62177 §8.4.4 as I read it.

### D-5 [MINOR] J104 has no overvoltage limit. Verdict: **AGREE; add the port-stage parts**
- From my bank and derating work:
    - C431/C434/C435 and the 5xx MLCCs: 25 V X5R.
    - C432/C532 polymer: 25 V. A polymer with a short and low leakage spec fails short.
    - TPS62933 VIN: 30 V operating / 32 V abs max (§8.1).
    - BQ25756 SRP/SRN/FB: 85 V, not limiting.
- So the first parts to go above about 25 V are on my sheet. That fits D's 25 V threshold.
- D's suggested SMAJ18A after D104: VBR 20.0–22.1 V, VC 29.2 V at 13.7 A (same R+O table, row SMAJ18A). It clamps a current-limited bench supply at about 20–22 V, below the 25 V parts. **AGREE** with the fix.

### D-3 [MINOR + DOC] Idle budget. Verdict: **AGREE**
- My figure for the chargers matches D's "chargers 34" µA: BQ25756 IQ_BAT = 17 µA per port at VAC = 0 with the ADC off (bq25756 §5.5 p.8), and FBG is hi-Z outside the ACUV window (pin 11).
- C432/C532 leakage is correctly carried as a separate spec-max line, applying with the FETs on only.

### Items reviewed with no challenge
- A-3 to A-12, C-2, C-3, C-6, C-8 to C-14, C-16 to C-19, D-1, D-2, D-6 to D-18.
- I read the claims and the cited numbers, and found nothing in them that contradicts my area or the datasheets I hold.
- C-3's 466 pF arithmetic checks: 330 × 1.05 + 120.
- D-6 and A-9 are the same UART back-power mechanism; the brief should merge them.
