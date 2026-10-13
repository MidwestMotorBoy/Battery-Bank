# Reviewer A — Cells and Gauge (gauge.kicad_sch) — first pass

Scope: BT101–BT104, J101, cell taps/VC filters, U101 BQ40Z50-R2 pin-by-pin + RSM0032A footprint, RS101 + SRP/SRN filter,
Q101/Q102 drive and SOA, C107/C108/C110/C111, F101, Q103 BTP buffer, SW101, J104, TS1–TS4, PBI/VCC/BAT, SMBus/J103,
PACK_P distribution, pack-level fault analysis.
Sources: bq40z50-r2.pdf (SLUSCS4C; section numbers are the printed ones; figures rendered from the PDF with PyMuPDF),
SLUUBK0B TRM (scratchpad/ti_docs/sluubk0b.txt), agm404ap1.pdf (figures rendered), prosemi_1206FA.pdf (rendered),
eve-inr21700-58e.pdf, pa2512-1mohm.pdf, SLUU446D, nets.txt / parts.txt.

Summary: 0 CRITICAL, 3 MAJOR, 9 MINOR, 8 NOTE.
After round 2: 0 CRITICAL, 1 MAJOR (A-3), 11 MINOR (A-1 and A-2 downgraded), 8 NOTE. A-3, A-6 and A-10 amended.

---

### A-1 [MINOR, was MAJOR; AMENDED in round 2] Both ports can source 100 W at once with the MCU dead; nothing in hardware keeps pack current under F101/cell/FET limits
- **Where:** PACK_P → R430/R530 → both BQ25756 battery sides (reverse mode), F101, Q101/Q102, RS101, the cells. TPS25751 EEPROM bundles (U402/U502).
- **Evidence:**
  - The 100 W total rule (first review #3, firmware item 3: 80 + 20 W) is enforced only by the MCU lowering USB1's PDO when USB2 attaches.
  - Reviewer B confirmed: each TPS25751 boots its own EEPROM independently (tps25751 §8.4.1), and the planned bundle is the same on both ports.
  - The only per-port hardware cap is ILIM_HIZ (3.6 k → 5.3–5.8 A on the USB side, bq25756 Table 7-6, Fig 7-18), about 106–117 W per port.
  - IBAT_REV is register-only (POR 20 A). CE/CHG_INH does not stop reverse mode (bq25756 §6.3.6 enable conditions do not include CE).
- **Worst-case math (welded pack):**
  - Path resistance R ≈ 4 × 25 mΩ cell DC + 2 × 8.7 mΩ FETs hot (6.0 mΩ max × 1.45 at ~100 °C, AGM Fig 4) + 5 mΩ F101 hot + 1 mΩ RS101 + traces ≈ 0.13 Ω.
  - 2 × 100 W at 94 % gives 213 W from the pack. Solve I·(V_ocv − 0.13·I) = 213:
    - 3.6 V/cell (14.4 V): I = 17.6 A.
    - 3.0 V/cell (12.0 V): I = 24 A.
  - At B's hardware ceiling (2 × 5.8 A × 20 V / 0.93 = 249 W) and 12 V, the pack is near its maximum-power point: I ≈ 31 A.
  - Against the limits:
    - EVE maximum discharge is 16.8 A (eve §3.6).
    - F101 1206FA-15A: Prosemi rule In = Imax/(0.70·Ktemp) gives about 10 A continuous at 50 °C. 24 A is 160 % of rating, and its opening time is not specified (only 350 % → ≤ 5 s).
    - Q101/Q102: 24² × 8.7 mΩ = 5.0 W each, against RθJA 60 °C/W. That is thermal runaway within tens of seconds.
  - So only the gauge's data flash (OCD1/OLD) protects the pack. Default OCD1 is 6 A (Table 9-1), so a fresh gauge trips. A gauge configured per firmware item 4 (OCD1 10–11 A) also trips, then recovers and trips again; both ports drop repeatedly.
- **Proposed fix:**
  - Move the #3 limit out of MCU firmware and into the EEPROM bundle. Default source PDOs must be safe for both ports with no MCU: ≤ 50–60 W per port (≤ 3 A at 20 V), so the pack sees ≤ ~10–11 A at 12 V.
  - Set IBAT_REV = 10 A (or 5 A) in the bundle.
  - The MCU raises one port to 100 W only while the other is unattached.
  - Keep gauge OCD1 ≈ 11 A and OLD 16–20 A as the backstop.
  - B has a companion item (CHG_INH covers charging only; sourcing has no hardware stop).
- **Confidence:** high on the arithmetic and that the guard lives only in firmware; medium on the cell DC resistance (25 mΩ assumed against the 18 mΩ AC spec).
- **AMENDED in round 2: DOWNGRADED to MINOR** (conceded to B, re-checked in SLUUBK0B).
  - Fresh-gauge defaults already bound the overload:
    - AFE Protection Control default 0x70 → RSNS = 0, half thresholds (§15.2.6.1).
    - AOLD:Threshold default 0xF4 → OLDV 4 = −19.42 mV (Table A-1), which is 19.4 A at 1 mΩ (≈ 16–22 A with the §7.31 ±2.5 mV offset / ±5 % scale). OLDD 0xF ≈ 31 ms (§7.32 tOLD 1–31 ms). This is an AFE hardware comparator, independent of firmware.
    - OCD1 −6 A/6 s and OCD2 −8 A/3 s (§15.9.7–8).
  - Outcome by case:
    - 24–31 A case (3.0 V/cell, or the ILIM_HIZ ceiling): AOLD trips in ≈ 31 ms.
    - 17.6 A case (3.6 V/cell): OCD2 trips in 3 s.
    - Firmware item 4's planned settings (OCD1 10–11 A, OLD 16–20 A) also trip.
  - So there is no sustained F101/FET/cell overload. What remains:
    - With the MCU dead and two 100 W sinks attached, both ports drop and retry-cycle. That is a function failure.
    - There are ms-to-s pulses of 1.6–2.8C.
  - The EEPROM-default fix (≤ 50–60 W per port, IBAT_REV 10 A) stands as the remedy.
  - **Also from C:** with the MCU truly dead, EN_5Vx is low and PP5V = 0, so a TPS25751 can't source a contract at all (B-14). The realistic trigger is therefore MCU alive but firmware wrong or not yet written, which is first review #3. MINOR is confirmed.
  - **New config point (from B):** firmware item 4 omits OCD2. Its default −8 A/3 s trips a single 100 W port at a low pack (9–11 A, A-6 amendment). Set OCD2 ≈ 12–13 A / 1–2 s, consistent with OCD1 10–11 A and OLD 16–20 A.

### A-2 [MINOR, was MAJOR; AMENDED in round 2] The DNP inrush fix C109 = 0.1 µF (gate→GND) would make Q102's short-circuit turn-off slow enough to exceed its SOA
- **Where:** C109 (DSG_G→GND, DNP 0.1 µF), D102 (DNP, bypasses R111), R111 5.1k, Q102 AGM404AP1, U101 DSG (pin 28). Sheet note 9 says to fit C109 + D102 if inrush trips SCD.
- **Evidence:**
  - bq40z50 Fig 6-1 (CHG/DSG drive): DSG is pulled down through an internal 2 kΩ and the DSGOFF switch to VSS, with a zener from PACK. D102 bypasses only R111, so the internal 2 kΩ stays in series.
  - §7.18 tF: 4.7 nF + 5.1 kΩ falls to 1 V in 40 µs typ / **300 µs max**. The max is about 3.7 × the typ, so the internal pull-down can be about 20 kΩ worst case.
  - AGM404AP1 Fig 14 SOA (Tc = 25 °C): about 550 W at 100 µs and about 160 W at 1 ms (read from the 100 µs/1 ms lines: 184 A × 3 V, 13 A × 40 V, 4 A × 40 V). Ciss 842 pF, Qgd 2.6 nC.
- **Worst-case math (hard PACK_P short, welded pack, 16.8 V):**
  - Prospective current I_sc = 16.8 V / (4 × 18 mΩ AC + 9 + 3.9 + 1 + ~5 mΩ) ≈ 185 A. With DC cell resistance it is ≥ 100 A.
  - Gate charge: the gate is at VBAT + 11.5 ≈ 28 V. C109 to GND adds 0.1 µF × 28 V = 2.8 µC to remove.
  - Time constant: τ = 2 kΩ × 0.101 µF = 200 µs typical, about 2 ms at the tF-max pull-down.
  - Fully enhanced phase (gate 28 → ~7 V, where gfs = 20 S passes 100 A): τ·ln(4) ≈ 280 µs. That is benign at I²R ≈ 60–200 W.
  - Linear phase (7 → 2 V): τ·ln(3.5) ≈ 250 µs typical, 2.5 ms worst. Peak power is about V·I_sc/4 = 16.8 × 100…185 / 4 = 420–780 W.
  - Against SOA: 250 µs allows about 330 W (log interpolation 550 W @ 100 µs → 160 W @ 1 ms); 2.5 ms allows about 100 W. **Exceeded by 1.3–2.4× typical and about 5× worst case.** Add the SCD delay (≤ 915 µs + ≤ 160 µs tDETECT) at full current before any of this.
  - Q102 failing short removes discharge protection. There is no second-level protector (decision Q2).
- **Without C109** (as built): τ = 7.1 kΩ × ~1.5 nF ≈ 10 µs, and the Miller plateau ≈ 2.6 nC / 1 mA ≈ 3 µs. Fine.
- **Proposed fix:** change the DNP value to **4.7 nF** (3.3–10 nF range) and keep D102.
  - Turn-on: the pump current derived from §7.18 tR (4.7 nF, 4.0 V in 200–500 µs → 38–94 µA) gives 38–94 µA / 5.5 nF = 7–17 V/ms, so the inrush into 290 µF is 2–5 A. That is below the 8.3 A minimum OLD setting and far below SCD.
  - Turn-off: τ = 2 k × 5.5 nF = 11 µs typ, ≤ 0.12 ms worst. Linear phase ≤ 0.15 ms, where ~450 W is allowed.
  - My inrush estimate for the welded pack at full charge is about 185 A peak (τ ≈ 26 µs), which is at Q102's 184 A IDM. Consider fitting the 4.7 nF from the start rather than only "if SCD trips".
  - Update sheet note 9 and the C109 Notes field (they say 0.1 µF, ~1 V/ms).
- **Confidence:** medium-high. The DSG pull-down path is read from Fig 6-1; the worst-case pull-down is scaled from tF max, not specified directly.
- **AMENDED in round 2: severity DOWNGRADED to MINOR** (conceded to C; the physics was upheld by C).
  - C109 is DNP, so the board as built is fine.
  - My own N-2 shows the inrush likely does not trip SCD1 (it is above 100 A for only about 16 µs, against a ≥ 61 µs delay + 160 µs tDETECT), so fitting C109 is unlikely to be needed.
  - The finding is the option value and sheet note: change it to 4.7 nF.
  - C's fit of tF gives an internal pull-down of about 1 kΩ typ and about 15 kΩ max. With 0.1 µF that is τ ≈ 0.1–1.5 ms, so the conclusion (SOA exceeded at ≥ typical) is unchanged.

### A-3 [MAJOR] Disabling the gauge precharge (firmware item 4) removes the only non-MCU block on charging a reversed or over-discharged cell
- **Where:** U101 data flash (Precharge Start Voltage, Charging Voltage Low, FET Options[PCHG_COMM]), U101 pin 30 PCHG (NC, no precharge FET), Q101 (CHG), CHG_INH (PB8 → R435/R535 → CE; low = charge when the MCU is off), BT101–BT104 holders.
- **Evidence:**
  - TRM SLUUBK0B §4.9: the gauge enters PRECHARGE if the minimum cell is below Precharge Start Voltage (default 2500 mV, §15.4.9.1). With PCHG_COMM = 0 (default) it uses the external precharge FET.
  - This board has no precharge FET. So, as delivered, the CHG FET stays off while any cell is below 2.5 V. Q101's body diode (anode CELL_P) blocks charge current, so the pack cannot be charged at all.
  - Firmware item 4 sets Precharge Start Voltage = Charging Voltage Low = 0 mV ("disables the precharge function", same section), which removes that block.
  - CUV opens only DSG. Charging stays allowed in CUV.
  - Doc conflict: circuit-description §2 says "set data flash so precharge uses the CHG FET" (PCHG_COMM = 1); the review says PCHG_COMM = 0 with thresholds at 0.
- **Fault scenario:**
  - The holders accept a cell backwards (circuit-description §1).
  - The stack then reads 3 × 3.6 − 3.6 = 7.2 V. The BQ25756 sees VBAT below its LOWV threshold (whole-stack, ≈ 12 V) and precharges at about 0.56 A.
  - The reversed cell reads ≤ −0.2 V (below the ADC range, §7.10) and is driven further into reverse at 0.56 A until the charger safety timer runs out: hours, about 1 Ah.
  - EVE §12.2.4: "Inverse charging shall be strictly prohibited". EVE §12.3.3: the charger should "detect voltage of cell box and determine recharging procedures".
  - CHG_INH only helps if the MCU is programmed and running. On this dev board it often won't be.
  - VIMR/VIMA PF may catch it eventually, but VIMR needs a rest period (and the reversed cell sits outside the ADC range).
- **Proposed fix (configuration, no hardware change):**
  - Keep PCHG_COMM = 0 (PCHG pin NC) and Precharge Start Voltage at about 2.5 V (default). Then any cell below 2.5 V, including a reversed or dead one, holds the CHG FET off.
  - Recovering an over-discharged cell becomes a deliberate bench step (EV2400 or a cell charger).
  - Make circuit-description §2 and firmware item 4 agree.
  - The trade-off is that a long-stored pack with a cell below 2.5 V will not revive from USB. That is EVE's intent.
- **Confidence:** medium-high on the TRM behaviour; medium on the exact BQ25756 precharge entry voltage (whichever it is, the charger is stack-level and cannot see one bad cell).
- **AMENDED in round 2 (fix completed, from C; MAJOR upheld by C):**
  - §4.9 condition 2 also enters PRECHARGE (CHG off with PCHG_COMM = 0) when the max cell is below Charging Voltage Low − hysteresis while not charging. Charging Voltage Low defaults to 2900 mV (§15.4.9.2).
  - With only Precharge Start kept at 2500 mV, a pack recovering from CUV (all cells 2.5–2.9 V) would also be blocked from USB.
  - Corrected configuration:
    - Precharge Start Voltage = 2500 mV (per-cell minimum, condition 1).
    - Charging Voltage Low ≤ 2500 mV (or 0, which disables only condition 2).
    - PCHG_COMM = 0.

### A-4 [MINOR] No test point on CELL_P_RAW, so BT104 can't be checked before F101 is fitted as the sheet note requires
- **Where:** sheet text "check each cell at TP102-TP105, then hand-fit F101". TP101 is on CELL_P (after F101) and floats until F101 is fitted. CELL_P_RAW = {BT104.1, F101.1, J101.5, R104.1}.
- **Evidence:** nets.txt. TP102–TP105 = CELL_N, CELL1, CELL2, CELL3: five nodes are needed for four cells, and only four are on test points before the fuse.
- **Fix:** move TP101 to CELL_P_RAW, or add a TP there; F101 pad 1 is a poor probe point. Reword the note to "TP102–TP105 and TP_CELL_P_RAW".
- **Confidence:** high.

### A-5 [MINOR] BAT is fed after F101; TI feeds it from the cell top (4P) before the fuse
- **Where:** D101 anode on CELL_P (after F101) → R105 → BAT (pin 32). VC4 (R104) is on CELL_P_RAW (before F101).
- **Evidence:**
  - bq40z50 Fig 9-1 (rendered): D1 (30 V) anode is on the J2 pin 1 / 4P line, the same node as R20 → VC4, upstream of F1. §9.2.2.3.1 says D1 isolates BAT from short-circuit dips; it was never meant to sit behind the fuse.
  - Effects on this board:
    1. In the assembled state (F101 DNP) and whenever F101 opens, U101 has VC1–VC4 driven by the cells but BAT unpowered. It is dead unless a charger back-feeds VCC through Q102's body diode. No reference design or test condition puts the device in that state.
    2. After F101 opens, the gauge can't log the event or report.
    3. EV2400 could read all four cell voltages before F101 is fitted, which is exactly the check the sheet asks for, if BAT were powered.
- **Fix:**
  - Move D101's anode to CELL_P_RAW.
  - If the Q7 "measure total drain across F101" method is to be kept, measure the gauge separately across R105: 100 Ω gives 5–34 mV at 52–336 µA (§7.5).
- **Confidence:** medium. The topology difference is certain; the harm of the BAT-off/VC-on state is unquantified.

### A-6 [MINOR] F101 15 A is under-rated by Prosemi's own sizing rule at the end of a 100 W discharge
- **Where:** F101 1206FA-15A. The Notes field says "~10 A continuous, 75 % derating".
- **Evidence:**
  - prosemi_1206FA p.2: "In = Imax / (0.70 × Ktemp)" (0.70, not 0.75). The derating curve gives Ktemp ≈ 0.95 at 50 °C and ≈ 0.93 at 60 °C.
  - p.1: 15 A = 3.9 mΩ, I²t 16.3 A²s; 20 A = 1.8 mΩ, I²t 48 A²s; same 24 Vdc/300 A interrupt rating.
- **Math:**
  - Pack current at 100 W out, 94 % efficiency, path R 0.13 Ω: 9.0 A at 3.0 V/cell loaded, 10.9 A at 2.5 V/cell (EVE cut-off), plus ~0.3 A overhead.
  - Required In = 11.2 / (0.70 × 0.95) = 16.8 A, which is more than 15 A.
  - Dissipation: 11² × 3.9 mΩ = 0.47 W (cold) in a 1206.
- **Fix:** 1206FA-20A (C-number to look up) gives 0.22 W at 11 A. It still clears a hard short as a backstop: 48 A²s at 185 A takes 1.4 ms, which leaves the gauge's SCD to act first (see N-2). Alternatively, firmware tapers output power below about 3.2 V/cell. Correct the Notes field.
- **Confidence:** high (manufacturer formula).
- **AMENDED in round 2:** clarifying the two numbers in my summaries.
  - The end-of-discharge pack current is **≈ 11 A**: single port at 100 W, 94 % efficiency, +0.3 W overhead = 106.7 W, at 2.5 V/cell loaded, with 0.03 Ω board path → 106.7/(10 − 0.32) = 11.0 A.
  - **16.5–16.8 A is the required fuse rating** In = 11.0/(0.70 × 0.95), not a current.
  - The verdict depends on the gauge CUV setting:

    | Loaded cut-off | Pack current | Required In | 15 A part |
    |---|---|---|---|
    | 2.5 V/cell | 11.0 A | 16.5 A | Under-rated |
    | 2.8 V/cell | 9.8 A | 14.7 A | OK |
    | 3.0 V/cell | 9.1 A | 13.7 A | OK |

  - Fix restated: the 20 A part, OR keep 15 A and set CUV (loaded) ≥ 2.8 V/cell, OR taper power below 3.0 V/cell.
  - Two ports at 100 W each is A-1's fault case, not this sizing case.

### A-7 [MINOR] Protection FETs dissipate about 1 W each at 100 W, but nothing measures their temperature
- **Where:** Q101/Q102. TS1–TS4 are now all on cells (rev A4). TH301/TH302 sit at Q402/Q502, TH303 between the connectors, TH304 in port 1's probe field (README placement). TI fig 9-1 puts RT1 "close to Q2 and Q3".
- **Math:**
  - 11 A² × 6.0 mΩ × 1.45 (hot) = 1.05 W each, 2.1 W in about 1 cm² (RθJA 60 °C/W each, Table 2). Expect Tj ≈ 105–125 °C at 45 °C ambient.
  - In the A-1 fault: 5 W each.
- **Fix:**
  - Agreed with C: add TH305 (NCP18XH103F03RB) beside Q101/Q102 on spare PA7 (ADC1_IN2). Use the same 10 k-to-NTC_EN divider + 100 nF as R308–R311 / C308–C311.
  - Keep TH304 at the heatsink-pad position (circuit-description §6). Fallback: move TH304. Also enable the gauge internal temperature sensor for OTD with U101 placed next to the FETs.
  - Add "protection FET temperature" to the MCU cross-check list.
  - Give FET_MID/CELL_P/PACK_P copper on both outer layers.
- **Confidence:** medium (RθJA depends on layout).

### A-8 [MINOR] TS2–TS4 NTCs ride on cell cans at 4.2–12.6 V; TS pins are rated 2.1 V and only tape and sleeve separate them
- **Where:** J105/J106/J107 → TS2–TS4 (U101 pins 11–13); NTC return on CELL_N. The cans of BT102/BT103/BT104 are CELL1/CELL2/CELL3.
- **Evidence:** §7.1 TS abs max VREG + 0.3 = 2.1 V. This is a new condition in rev A4: the first review's m8 fix put only J102 on BT101 (can = VSS).
- **Math:**
  - A lead touching a can injects into the TS ESD clamp and the internal 1.8 V LDO, which can't sink current. Through the NTC body (10 k at 25 °C) that is (12.6 − 2.1)/10 k ≈ 1 mA; through a bare lead, current is limited only by wiring.
  - The likely result is a dead U101, the only hardware protector (decision Q2).
- **Context:** TI's own 4S reference has the same VSS-referenced NTCs in a pack, so this is standard practice when the insulation is permanent. Open holders with re-taped sensors are the weak point, especially near the bare can bottom.
- **Fix:**
  - Specify insulated NTCs (insulated body + PTFE/Kapton jacket) and a Kapton layer under each sensor, at mid-body away from the cell ends. Put this in sheet note 10, which today mentions only J102/BT101.
  - Optional: a 0R/1 k series footprint in each TS line, with the bqStudio thermistor coefficients recomputed for the added 1 k.
- **Confidence:** medium (probability-driven).

### A-9 [MINOR] J104 bench input is an unkeyed 2.54 mm header; a reversed lead drives PACK_P negative, which TI explicitly warns about
- **Where:** J104 (1 PACK_P, 2 GND), Q102, U101 PACK (R113 10 k), both BQ25756 battery sides, both TPS62933 VIN, C432/C532 polymer.
- **Evidence:**
  - bq40z50 §9.2.2.3.3: Q4 protects the DSG FET "in the event of a reverse-connected charger … Q3 can be driven into its linear region and suffer severe damage if the PACK+ input becomes slightly negative". There is no Q4 here (circuit-description §2: "no external charger connects to the pack terminals"), but J104 is exactly such a connection.
  - PACK abs min is −0.3 V (§7.1).
- **Math:**
  - PACK_P is clamped at about −1.4 to −2 V by each charger's battery-side LS + HS body diodes and each TPS62933's internal body diodes. Those carry the bench supply's current limit, split four ways.
  - The PACK pin sees about −1.4 V through 10 k (≈ 80 µA).
  - Q102: the gate is held near the PACK pin, so VGS ≈ 0.8 V against a 1.2 V Vth(min), with little margin when hot (Fig 6).
  - The polymer caps sit at −1.4 V or more, beyond the usual ≤ 0.5–1 V reverse allowance.
- **Fix:** a keyed 2-pin connector (JST-XH/PH) with +/− silkscreen, or a series Schottky. TI's Q4 circuit could also be added to DSG_G.
- **Confidence:** medium.

### A-10 [MINOR; AMENDED in round 2] Q103 2N7002 gate drive is only about 2.6 V worst case, against its 2.5 V max Vth
- **Where:** BTP_INT (U101.15) → Q103 gate, R117 470 k to CELL_N; drain on GAUGE_BTP with R114 100 k to 3V3 (needs ~33 µA).
- **Evidence:** §7.12 VOH ≥ 3.5 V at 0 µA and ≥ 1.8 V at −10 µA (VBAT > 5.5 V). R117's note assumes a 10–20 µA source, which gives 4.7–9.4 V; that is typical (PRES text, §9.2.2.2.3), not guaranteed. 2N7002 Vth is 1.0–2.5 V at 250 µA.
- **Fix:** a low-Vth part (BSS138 0.8–1.5 V, or DMG1012T) or R117 = 1 MΩ. VGS stays ≤ PBI ≈ 16.8 V, under ±20 V. Configure BTP active-high so the idle level is low and Q103 is off: no R114 current and no 10–20 µA from the pack.
- **Confidence:** medium.
- **AMENDED in round 2 (from C):** the guaranteed level is better than 1.8 V.
  - A Thevenin fit of the two §7.12 points (Voc ≥ 3.5 V; R_out ≤ (3.5 − 1.8)/10 µA = 170 k) into R117 = 470 k gives VG ≥ 3.5 × 470/640 = 2.57 V.
  - That assumes a linear source between the spec points, against Vth(max) 2.5 V at 250 µA. The gate drive is marginal rather than failing.
  - MINOR stands; the BSS138 swap is cheap.

### A-11 [MINOR] The welded-pack connector J101 has no Kelvin sense for 1N/4P, which distorts the learning cycle the welded pack exists for
- **Where:** J101 pin 1 (CELL_N: power + VSS + SRP sense + VC1 cap), pin 5 (CELL_P_RAW: power + VC4 sense).
- **Evidence:** bq40z50 §9.2.2.1.3: Kelvin at 4P and 1N "is equally important". Lead + terminal resistance (≈ 3–8 mΩ each) is added to cell 1 and cell 4 voltages at I × R.
- **Math:**
  - At a 1C learning discharge (5.6 A) × 5 mΩ = 28 mV on cells 1 and 4, against a cell impedance of ~18–30 mΩ: a 15–25 % error in those cells' Ra tables.
  - Also, MKDS 1,5 is rated about 13.5 A against 11 A continuous here.
- **Fix:** a 7-way J101 with separate 1N and 4P sense wires to the R101 bottom / R104 nets (CELL_N sense to the VSS star, 4P to R104), the power pins sized for 15 A.
- **Confidence:** medium.

### A-12 [MINOR] The HighCurrent net class (2.5 mm) is about 10 A on 2 oz; the pack path needs pours
- **Where:** README net classes. Nets: CELL_P_RAW, CELL_P, FET_MID, PACK_P, CELL1–3, CELL_N, GND, VBAT_SYS.
- **Math:** IPC-2221 external: 2.5 mm × 70 µm = 271 mil², I = 0.048 · ΔT^0.44 · A^0.725 = 10.4 A at ΔT = 20 °C (7.7 A at 10 °C). The design point is 11 A continuous, with 20 A+ in the A-1 fault.
- **Fix:** ≥ 5 mm or poured on both outer layers with stitching; same for the holder interconnects.
- **Confidence:** high.

---

### N-1 [NOTE] The gauge never sleeps (always in NORMAL, 336 µA); if sleep is enabled, the CHG FET turns off in sleep
- **Evidence:** TRM §5.3.1 sleep-entry table: SMBus must be low for Bus Timeout unless [IN_SYSTEM_SLEEP] = 1. Here 3V3 is always on and R304/R305 hold the bus high. Same table: "Turn off CHG FET … if FET Options[SLEEPCHG] = 0". §7.5: 336 µA vs 52–75 µA, about 2.9 Ah/yr (shared with C for the sleep budget).
- **Fix:** IN_SYSTEM_SLEEP = 1 with a Bus Timeout, and SLEEPCHG = 1. Otherwise USB charging can't start until the MCU wakes the gauge: Q101's body diode blocks current, so the wake comparator never trips.

### N-2 [NOTE] Keep SCD delays short enough that U101 clears a hard short before F101 melts
- **Evidence:** §7.32: tSCD1 0–915 µs (61 µs steps), tSCD2 0–458 µs, plus tDETECT up to 160 µs. F101 15 A melting I²t is 16.3 A²s typ.
- **Math:** at 185 A that is 0.48 ms (and less at the minimum I²t).
- **Fix:** SCD1 + tDETECT ≤ ~250 µs. With RS101 = 1 mΩ an SCD1 of about 100 mV (100 A) and ≥ 61 µs delay should ride through the turn-on inrush (τ ≈ 26 µs; drops below 100 A after ≈ 16 µs). With C109 = 4.7 nF (A-2) the question disappears.

### N-3 [NOTE] Keep [BCAST] = 0 (raised by C)
- With BCAST set, the gauge acts as an SMBus master and broadcasts to 0x08/0x09 on the shared bus.

### N-4 [NOTE] Holder contact opening mid-discharge, and reversed BT102–BT104 (same mechanism as first-review #7, now upper cells)
- **Contact opens mid-discharge:** the only path across the gap is R10x → VCx/VCx+1 internal clamp → R10x+1 (200 Ω). Up to 6–8 V across it gives ≤ 40 mA, 0.16 W in a 1206 (0.25 W). Fine until CUV (delay default 2 s) opens DSG.
- **Reversed BT102–BT104:** about (3.6 − 0.7)/200 Ω = 14.5 mA continuous through the VC(n)/VC(n+1) internal diode. This violates VCn ≥ VC(n−1) − 0.3 V (§7.1) and slowly discharges the reversed cell. A-3 covers the charging side.

### N-5 [NOTE] Documentation
- Sheet note 10 covers only J102/BT101; J105–J107 need the same warning (A-8).
- circuit-description §2 says "PACK 10 kΩ input resistor is internal". It is R113, external, as README item 2 says.
- circuit-description §2 vs firmware item 4 conflict on PCHG_COMM (A-3).
- F101 Notes use "75 % derating" (A-6).
- C109 Notes say 0.1 µF / ~1 V/ms (A-2).

### N-6 [NOTE] SW101 wake timing and current
- PACK_P bulk ≈ 290 µF through R118 4.7 k: τ = 1.36 s.
- Time to VSHUTDOWN+ max 2.45 V (§7.3): 0.31 s at 12 V and 0.38 s at 10 V. The button must be held about 0.5 s (more if the TPS62177 starts drawing below 2.45 V).
- Current into a shorted PACK_P is 3.6 mA (60 mW). OK.

### N-7 [NOTE] BTP drain while asserted
- When BTP_INT is high, its 10–20 µA comes from PBI/BAT into R117, plus 33 µA from 3V3 through R114 (Q103 on).

### N-8 [NOTE] Verified correct (no finding)
- **U101 pins:** all 33 match Table 6-1, and the symbol numbers match the netlist.
- **Unused pins:**
  - PRES, DISP, FUSE, PTC, PTCEN to VSS (Table 6-1 / §9.2.2.3.6).
  - LEDCNTLA–C NC (allowed).
  - NC 7/14/29 open (allowed).
  - PCHG NC (allowed).
- **RSM0032A footprint:** checked against the rendered land pattern (p.53) and outline (p.52): 32 × 0.6 × 0.2 lands at (3.8) centres, 0.4 pitch, pins 1–8 down the left (pin 1 top), 9–16 bottom L→R, 17–24 right B→T, 25–32 top R→L, pad 33 1.4 mm with a 1.3 mm paste window (86 % coverage).
- **VC filters:** 100 Ω / 0.1 µF differential, as in Table 6-1. VC4 tap before F101. Balancing current about 3.6 V / (200 + 200 Ω) ≈ 9–10 mA.
- **SRP/SRN:** SRP from CELL_N (VSS side), SRN from GND, 100 Ω + 0.1 µF (§9.2.2.2.1). Within ±0.3 V abs max up to 300 A.
- **RS101:** PA2512FKE7W0R001E is TCR code E = ±50 ppm (PA datasheet ordering code), meeting TI's ≤ 50 ppm. Dissipation 0.12 W at 11 A, 0.58 W at 24 A, against 2 W.
- **Gate drive:** CHG/DSG 5.1 k series and 10 M gate-source, as in §9.2.2.3.3. Q101 is CHG on the cell side (body diode blocks charge) and Q102 is DSG on the pack side; directions are correct.
- **D103:** orientation K→DSG_G, A→PACK_P. Its 14.2 V min Vz against a normal max VGS of about 12.2 V (VDSG(ON) ≤ 12 V + 0.2 V path drop) leaves 2 V of margin.
- **C110/C111:** match fig 9-2 C1/C2, cell side after the fuse to PACK+; 50 V holds 16.8 V if one shorts. C107/C108 match §9.2.2.1.5.
- **Supply pins:** VCC via R106 100 Ω from FET_MID (TI R13). PACK via R113 10 k (TI R15). PBI 2.2 µF 50 V 0805.
- **SMBus:** 100 Ω series (TI R24/R25). J103 order matches SLUU446D §2.6 (1.1 VSS, 1.2 SCL, 1.3 SDA, 1.4 VOUT).
- **F101 interrupt rating:** 300 A at 24 Vdc, above the 185 A prospective current.
- **R430/R530 link:** about 0.25 mΩ (3 × 3 mm, 2 oz), 30 mW at 11 A.
- **Diode footprints:** D101/D102/D103 SOD pad 1 = K matches the symbols.
- **AGM footprint:** pads match the datasheet (S 1–3, G 4, D 5–8 + tab).
