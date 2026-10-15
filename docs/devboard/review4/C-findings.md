# Reviewer C: USB-C front end and PD control (usb_port.kicad_sch), round 1

**Scope:**
- Port 1 (4xx refs), checked against port 2 (5xx).
- Straps R1/R2 (port 1) and R3/R4 (port 2).
- U401/U501 TPS25751D, U402/U502 M24512 EEPROM, U405/U505 TPD4S201-Q1 (item 39, never reviewed before).
- Liquid detection: Q403–Q406, R436–R443.
- D401/D501 SMAJ22A and J401/J501 Shou Han TYPE-C 16PCB1.6 IP68.
- PD-level behaviour, connector fault injection, and the TPS25751 ↔ BQ25756 interplay.

**Sources** (all in `datasheets/`; text extracted with PyMuPDF, cited figures rendered to PNG in `scratch-c/`):

| Document | Parts used |
|---|---|
| TPS25751 datasheet, SLVSH93A | §5 (table 5-1), §6.1–6.14, §8.3.2–8.3.11, §8.4.1 (tables 8-2, 8-5, 8-6), §9.2.2.2 (fig. 9-8, table 9-3) |
| TPS25751 TRM, SLVUCR8B | INT_EVENT1/INT_MASK1 §3.2.6–3.2.8, TX source PDO power-path field, Liquid Detection Config 0x98 §3.2.37, 'DBfg' §4.6.2, GPIO events table 5-6 |
| TPS25751EVM guide, SLVUCP9B | Table 1-1, §4.3.1.2, §4.4, figs. 5-4, 5-5, 5-6 |
| TPD4S201-Q1 datasheet, SLVSI17 | All of §4–§7.4, RGR0020C land pattern (p. 27) |
| TPD4S201 datasheet (RUK) | Pinout only |
| M24512 datasheet | §2–§3, package pad note |
| SMAJ series datasheet (Littelfuse) | SMAJ22A row |
| AO3400A, AO3401A, TPS62933, BQ25756 (abs max) | As cited |
| Shou Han TYPE-C 16PCB1.6 IP68 drawing | Pin table, recommended PCB layout |

**Design inputs:**
- `nets.txt`, `parts.txt` and `erc.txt`.
- Footprint pads read from `MonolithDev.kicad_pcb` and `MonolithDev.pretty`.
- The symbol pins read from `usb_port.kicad_sch`.

**Peer answers relied on:**
- B confirmed the TPS62933 limit numbers and their behaviour (C-5).
- B handed me the BQ25756 IAC_DPM/VAC_DPM configuration item (C-11).
- D agreed the TPD4S201 VPWR current figures (C-2) and will fold them into a whole-board budget refresh.

**Summary:** 0 CRITICAL, 0 MAJOR, 8 MINOR, 3 CONFIG, 3 DOC, 5 NOTE.

**After round 2 (final):** 0 CRITICAL, 0 MAJOR, 7 MINOR, 3 CONFIG, 3 DOC, 6 NOTE.
- C-1 is downgraded from MINOR to NOTE (conceded to B; the 100 V part stays as an optional improvement).
- C-4's recommended part is settled: TVS2200DRVR, LCSC C523793.
- C-6 gains a CONFIG line (restore EN_5Vx first after any reset).
- C-7 gains B's ACP/ACN check for the bench short test.
- Details are under "After round 2" at the end.
- Nothing is wired wrongly.
- Port 2 is a verified exact copy of port 1:
  - every 5xx net matches its 4xx net pin for pin;
  - every 5xx part matches its 4xx part in value, footprint, MPN, LCSC and Notes;
  - the only differences are the straps and EN_5V1/EN_5V2.
- The TPD4S201 is wired as TI's EVM fig. 5-5. Three of its datasheet values were not carried over: the 63 V VBIAS rating, the CC-capacitance budget, and the always-on current.

---

### C-1 [MINOR] C451/C551 (TPD4S201 VBIAS) is a 50 V capacitor; the datasheet's ROC footnote asks for at least 63 V, with 100 V recommended

- **Where:** U405.3 / U505.3 VBIAS, net `Net-(U405-VBIAS)`, C451/C551 = CC0603KRX7R9BB104 (0.1 µF 50 V X7R 0603).
- **Evidence:**
  - TPD4S201-Q1 §5.5, footnote (2): "The VBIAS pin requires a minimum 63-VDC rated capacitor. A 100-VDC rated capacitor is recommended to reduce capacitance derating." The effective VBIAS capacitance must be 0.04 µF minimum.
  - Typical application figs. 7-1/7-2 draw C2 = 100 nF **100 V**.
  - The same datasheet contradicts itself in §7.2.2.1: "a minimum of 50VBUS rated capacitor is required … a 50VBUS capacitor is recommended." It explains that VBIAS sees about 40 V of ringing in a 20 V short-to-VBUS.
  - TI's own EVM uses C69 = 0.1 µF **50 V** (SLVUCP9B fig. 5-5).
  - The C451 Notes property argues 50 V from the same 40 V ring. A 40 V ring on a 50 V part leaves 80 % stress, above our 50 % target.
- **Why only MINOR:**
  - The datasheet conflicts with itself, and TI's EVM uses 50 V.
  - Our 50 V X7R still keeps more than 0.04 µF effective at 20–40 V.
- **Proposed fix:**
  - Use a 0.1 µF 100 V X7R 0603 (for example Samsung CL10B104KC8NNNC; check the LCSC number and stock).
  - Same footprint, both ports. It costs cents and satisfies both readings of the datasheet.
  - Update the Notes property (see C-13).
- **Confidence:** verified (read §5.5 footnote 2, §7.2.2.1, figs. 7-1/7-2, EVM fig. 5-5).

### C-2 [MINOR] The TPD4S201 adds about 224 µA typical (320 µA maximum) of always-on 3V3 load; the idle pack drain rises about 35 %

- **Where:** U405.10 / U505.10 VPWR on `/P1_LDO_3V3` and `/USB Port 2/LDO_3V3`. Each of those nets is fed from 3V3 through R401/R501 and the TPS25751 VIN_3V3→LDO_3V3 switch whenever 3V3 is up.
- **Evidence:**
  - TPD4S201-Q1 §5.7 gives IVPWR = 112 µA typ, 160 µA max (3.3 V, −40 to 85 °C). Two ports: 224 µA typ, 320 µA max.
  - The TPD2S300 it replaced drew about 4.2 µA typical per part (review 3, P2). `power-budget.md` still lists "2 × TPD2S300 ≈ 8.5 µA (16 µA max)".
  - Pack current: 0.215 mA × 3.3 V / (14.4 V × 0.8) ≈ +62 µA. Idle goes from about 161 µA to about 220 µA, without D's other rev A7 additions.
  - This cannot be avoided by switching VPWR off. Per TPD4S201 table 6-1, unpowered means the CC FETs are off and the dead-battery Rd is shown, so the port could only ever be a sink.
  - TPD4S201-Q1 §7.3 also requires VPWR to share the PD controller's dead-battery supply, which LDO_3V3 does.
- **Proposed fix:**
  - No hardware change: accept the cost.
  - Update `power-budget.md` (D is folding this into the rev A7 budget refresh).
  - Re-measure the R201 idle current at bring-up.
  - For production, compare with a lower-Iq protector (for example a TPD8S300-class part) if idle drain matters.
- **Confidence:** verified (datasheet value). The pack figure is arithmetic. D agrees.

### C-3 [MINOR] CC capacitance: 330 pF plus the TPD4S201's 40–120 pF reaches 466 pF against the TPS25751's 480 pF maximum; TI's EVM uses 220 pF with this protector

- **Where:** C401/C402 (C501/C502) 330 pF C0G on CC1/CC2, with U405 CON_CC in parallel.
- **Evidence:**
  - TPS25751 §6.4 CCCy: 200 pF min, 400 pF nom, 480 pF max. Footnote 3: "Capacitance includes all external capacitance to the Type-C receptacle."
  - TPD4S201-Q1 §5.7: CON_CC is 40/74/120 pF, seen from CCx or C_CCx.
  - Worst case: 330 × 1.05 + 120 = 466.5 pF. That leaves about 13 pF for the connector contact, about 10 mm of trace on each side, and the TPS25751's own pin.
  - Best case: 313.5 + 40 = 353.5 pF, which is fine.
  - TPS25751EVM fig. 5-4 has C26/C27 = **220 pF 50 V** on 751_CC1/CC2, behind the same TPD4S201. 220 pF gives 249–351 pF, centred in the 200–480 pF window. It also sits inside the PD cReceiver range of 200–600 pF (TPD4S201-Q1 table 7-2).
  - The 330 pF value dates from before any protector sat on CC (circuit-description §7.1, "TPS25751 datasheet").
- **Proposed fix:** C401/C402/C501/C502 → 220 pF 50 V C0G 0402 (for example CL05C221JB5NNNC), the same footprint.
- **Confidence:** verified (both tables and the EVM schematic read). Whether 466 pF actually breaks BMC is inferred; it is only a margin issue.

### C-4 [MINOR] D401/D501 SMAJ22A clamps at 35.5 V at its rated current, above the 28 V abs-max of everything on VBUS; TI recommends a flat-clamp TVS2200

- **Where:** D401 (D501) K on `/USB Port 1/VBUS`, A on GND, at J401.
- **Evidence:**
  - **SMAJ22A** (Littelfuse table): VR 22.0 V, VBR 24.40–26.90 V at 1 mA, VC 35.5 V at IPP 11.3 A (10/1000 µs).
  - **Abs-max on the VBUS net:**
    - TPS25751 VBUS_IN, VBUS and PPHV: 28 V (§6.1.1, §6.1.2).
    - TPD4S201 C_CC/C_SBU: 28 V (in a VBUS-to-CC/SBU short).
    - BQ25756 VAC: 85 V (it is not limiting).
  - **TPS25751 §6.1.1 note 4:** "A TVS with a break down voltage falling between the Recommended max and the Abs max value is recommended such as TVS2200."
    - The SMAJ22A's VBR of 24.4–26.9 V does fall inside the 22–28 V window, so its standoff is correct.
    - Only its clamp slope is the issue.
  - **TI's EVM** uses a TVS2200DRVR on VBUS (SLVUCP9B table 1-1, U2/U3; fig. 5-4).
  - **In practice:**
    - ESD: an 8 kV contact discharge (about 1.2 µC) into C406 (4.7 µF) raises VBUS by only about 0.3 V, so ESD is fine without the TVS.
    - Hot-plug ringing: small energy, clamped near VBR.
    - The exposure is a surge or a stiff over-voltage source. A battery bank never sees mains surges, which is why this is MINOR.
  - **Datasheet mismatch:** the BOM fits LCSC C41376403 "JLC preferred SMAJ22A", while the datasheet we hold and `circuit-description.md` cite C148220 (Littelfuse). The fitted part's datasheet has not been checked.
- **Proposed fix:**
  - Option 1: fit TVS2200DRVR (SON-6 2 × 2) at J401/J501, as the EVM does.
  - Option 2: keep the SMAJ22A and add the TVS2200 in parallel.
  - At minimum, fetch the C41376403 datasheet and confirm VBR min ≥ 24.4 V (above PD's 21 V maximum and the ACOV 22.5 V stop) and VBR max ≤ 28 V.
- **Confidence:**
  - Verified: the SMAJ22A row, the TPS25751 note, the EVM BOM.
  - Inferred: the ESD arithmetic, and that the JLC part matches Littelfuse.

### C-5 [MINOR] PP5V buck headroom: the TPS62933 valley limit allows only about 3.2–3.5 A out, against the TPS25751's 3 A VBUS plus VCONN (ILIM5V setting 3 clamps at 3.04–3.58 A)

- **Where:** U404/U504 → `/USB Port 1/PP5V` → U401.34 PP5V (PP_5V to VBUS, and PP_CABLE to CC as VCONN).
- **Evidence:**
  - TPS25751 §6.3.1: VBUS 3 A plus CC 315 mA, both from PP5V. §6.8: ILIM5V setting 3 is 3.04–3.58 A.
  - TPS62933: ILS_LIMIT (valley) is 2.9 A min; IHS_LIMIT is 4.2 A min.
  - Ripple with L402 3.3 µH at 1.0–1.35 MHz: 0.63–1.34 A p-p (B's arithmetic).
  - So Iout(max) ≈ 2.9 + ΔI/2 = **3.2–3.5 A**. A 3 A sink plus an active cable's 0.3 A VCONN (3.3 A) sits at the edge.
  - A sink pulling up to the TPS25751 clamp hits the buck's limit first.
  - B: the valley limit acts cycle by cycle with frequency foldback, so PP5V sags rather than hiccups. Hiccup only follows below 65 % UVP for 256 µs.
  - The likely outcome is the TPS25751 hitting PP5V UVLO (3.8–4.2 V falling, §6.11) and entering ErrorRecovery. That is safe, but it means the port cannot really deliver 5 V 3 A plus VCONN.
- **Proposed fix:**
  - Accept it on the dev board and measure it at bring-up: 3 A resistive load plus a VCONN load on CC.
  - Optional: ILIM5V setting 2 (2.3–2.7 A) always clamps first, but it caps the 5 V PDO at about 2.25 A. Advertise 5 V 2 A or 2.4 A if VCONN is ever needed at 5 V.
  - Production: a TPS62933 sibling or a 4 A buck would remove the edge.
- **Confidence:** verified datasheet limits. The ripple arithmetic is agreed with B. The behaviour sequence is inferred.

### C-6 [MINOR] "PPHV sourcing at 9–20 V does not depend on the MCU" is doubtful: the attach (vSafe5V), the Rp current source and VCONN all come from PP5V, and the MCU gates PP5V (EN_5Vx, pull-down R432)

- **Where:** EN_5V1 → U404 EN (R432 100k to GND), PP5V → U401.34; `mcu-io-power-states.md` line 71.
- **Evidence:**
  - **Rp:** TPS25751 §6.12 specifies IRp1.5 and IRp3.0 only for 4.75 V < VPP5V < 5.5 V, and VOC_5 is "VPP5V > 3.802 V". The Rp current sources are supplied from PP5V.
  - **VCONN:** comes from PP5V through PP_CABLE (§8.3.3.1), and §8.3.3.1.8 disables it on PP5V UVLO.
  - **vSafe5V:** a new attach always starts at vSafe5V. By default PDO1 uses PP5V (TRM TX source caps, "Power Path for PDO 1: 0h = PP5V, 2h = PP_EXT").
  - **On an MCU reset during a 20 V contract** (CC2340 pins go hi-Z in reset, so R432 turns the buck off):
    - PP5V decays.
    - The Rp advertisement and VCONN to an e-marked 5 A cable collapse.
    - The partner may see a detach or a cable reset. The contract can be lost even though BQ25756 reverse mode continues.
  - TI does not document this sequence, so the consequences are inferred.
- **Proposed fix:**
  - Bring-up test: hold a 20 V 5 A contract (e-marked cable) and force an MCU reset or pull EN_5V1 low. Watch CC, VCONN and VBUS.
  - If the contract drops, choose one:
    - (a) Accept it, and correct line 71 to match the 5 V case already accepted there.
    - (b) Configure PDO1 on PP_EXT (PPHV via the BQ25756 at 5 V) so attach does not need PP5V. Rp and VCONN still do.
    - (c) Hold EN_5Vx on with a weak pull-up instead of a pull-down. That conflicts with open item 7 in the same file (idle budget), so it is a trade.
- **Confidence:**
  - Inferred: the consequence.
  - Verified: the PP5V conditions on Rp and VCONN in the datasheet tables.

### C-7 [MINOR] VBUS shorted to GND while sourcing at 20 V through PPHV: the integrated PPHV switch has no current clamp, and the protection is only the VBUS-UVLO turn-off plus the BQ25756's own reverse-mode protection

- **Where:** U401 PPHV (20) ↔ VBUS_IN (23), PPHV bank (C409, C449, and through R424 the AC_SNS_N bank: C420/C423/C424/C427 4 × 22 µF 35 V plus the C421 100 µF polymer, about 130 µF effective at 20 V).
- **Evidence:**
  - TPS25751 §8.3.3.2 lists the PPHV path protections as OVP, RCP and VBUS UVLO. Unlike PP_5V (§8.3.3.1.1, ILIM5V clamp in 1.15 µs), there is no current limit.
  - VBUS UVLO (3.5–3.8 V falling) disables GATE_VBUS "within tPPHV_RCP", but this datasheet revision gives no number for tPPHV_RCP.
  - §6.1.2 PPHV path: 7 A continuous, **10 A pulsed (≤ 100 µs, ≤ 1 %)**. RPPHV is about 16–26 mΩ over temperature (fig. 6-5). SOA is in fig. 6-6.
  - A receptacle short lets about 130 µF at 20 V (26 mJ) plus the BQ25756's reverse output into the switch. Only RPPHV, the 5 mΩ R424 and the traces limit it, so the peak can exceed 10 A for tens of µs.
  - TI's EVM uses the same topology (TPS25751D PPHV ↔ BQ25756), so this is TI's accepted architecture.
  - The same applies to a VBUS short while sinking, where the bank back-discharges until RCP or UVLO opens.
  - B owns the BQ25756 reverse-mode short behaviour (IBAT_REV, reverse-mode OCP).
- **Proposed fix:**
  - No schematic change.
  - At bring-up, short VBUS at the receptacle through a current probe while sourcing 20 V. Record peak current and duration, and the TPS25751 and BQ25756 status.
  - Confirm with TI E2E that the PPHV switch survives a hard short with a 130 µF PPHV-side bank.
  - Keep sheet note 9's soft-start setting.
- **Confidence:** inferred. The datasheet gives no response time; the ratings are verified.

### C-8 [MINOR] Testability: no test pads on CC1/CC2, SBU_FLT, the SBU sense nodes or the liquid-detect gate nets

- **Where:** nets `/USB Port 1/CC1`, `CC2`, `C_CC1`, `C_CC2`, `SBU1_SNS`, `SBU2_SNS`, `SBU_FLT`, `LIQ_PU`, `LIQ_PD` (and port 2).
- **Evidence:**
  - `nets.txt`: none of these nets has a TP. The port has TPs only on VBUS, PPHV, PP5V, LDO_3V3, REGN, SW1/2, STAT1/2, PG, CE_N and I2CC.
  - TI's EVM brings out C_CC1/C_CC2/C_SBU1/C_SBU2 (SLVUCP9B table 4-1, TP13–TP16) and GPIO4/5/6/7 plus TPD_FLT (table 4-5).
  - Our bring-up tasks need these points:
    - PD BMC sniffing;
    - the review 3 C4 "confirm with a scope that LIQ_PU goes low";
    - checking FLT during the short tests in C-7.
  - Project practice (`dev-board-practices`) is probe points on every debug-relevant signal.
- **Proposed fix:** add 1 mm pads (or the Harwin loop on CC) on CC1, CC2 (controller side), SBU_FLT, SBU1_SNS, SBU2_SNS, LIQ_PU and LIQ_PD, on both ports. Place them so they don't add stubs on CC: a pad right on the trace.
- **Confidence:** verified (netlist).

### C-9 [CONFIG] Liquid-detect thresholds must allow for TPD4S201 SBU leakage, GPIO leakage and LDO_3V3 sag; the Application Customization Tool defaults may assume the EVM's 249 kΩ pull-up

- **Where:** Liquid Detection Configuration register 0x98 (TRM §3.2.37); R436/R437 100k, R438/R439 1M; U405 SBU path.
- **Evidence:**
  - **Leakage, pull-up phase:**
    - TPD4S201-Q1 §5.7 IC_SBU_LEAK: up to 3.2 µA at 3.6 V, the same if the SBUx side is biased.
    - TPS25751 GPIO_ILKG: ±1 µA.
    - Through Rup = 100 kΩ, the "dry, pull-up on" reading can droop by up to (3.2 + 1) µA × 100 k ≈ 0.42 V at 85 °C.
    - With TI's EVM Rup = 249 kΩ (SLVUCP9B fig. 5-6: R106/R107 249k), the droop would be about 1 V.
  - **Rail sag:** the pull-up rail is LDO_3V3. During a cable attach with the TPS62177 in sleep mode, 3V3 can sag to about 2.87–3.07 V (D's analysis). That moves the dry reading down by up to about 10 %.
  - **Tool defaults:** they come from the EVM, which fits 249k. `bringup-config-checklist.md` §3 says "Start from the tool's default thresholds (Rup 100 kΩ / Rdown 1 MΩ as the datasheet's table 9-3)", which assumes the defaults match our 100k. That is not shown anywhere.
- **Proposed setting:**
  - Compute the 0x98 high/low thresholds (14 mV/LSB) for 100k/1M with ≥ 0.5 V margin below the 2.87 V worst-case dry reading.
  - Check the tool's defaults against that before flashing.
  - Keep review 3 C5's wet test (salt water SBU–GND and SBU–VBUS).
- **Confidence:** verified leakage specs. The tool-default concern is inferred.

### C-10 [CONFIG] I2Ct interrupt and addresses: IRQ_N is a latched level whose mask comes from the EEPROM; the MCU must read and clear both controllers at start-up

- **Where:** U401.10 / U501.10 I2Ct_IRQ on IRQ_N; I2Ct at 0x20 (U401) and 0x21 (U501).
- **Evidence:**
  - **Addresses:** port 1 has ADCIN1 = LDO_3V3 (decoded 7) and ADCIN2 = GND (0). That is SafeMode, index #1 = 0x20. Port 2 has (0,0): SafeMode, index #2 = 0x21. Sources: TPS25751 tables 8-2, 8-5, 8-6; TI's EVM truth table in fig. 5-4 agrees. The two addresses differ and are available during BOOT and APP. No TMP1075 (0x48–0x4C) or gauge (0x0B) conflict.
  - **Latching:** TRM §3.2.6 says "If any bit in this register is 1, then the IRQ pin is pulled low. Only the interrupt events enabled in INT_MASK1 will be asserted."
  - **Reset values:** INT_EVENT1 resets to 0x08 (PlugInsertOrRemoval set). INT_MASK1 resets to 0, and its bytes 1–10 "must be configured through the Application Customization Tool".
  - So whether IRQ_N is low after boot depends on the bundle.
  - Answered to A, who owns the wire-OR.
- **Proposed setting:**
  - MCU init reads INT_EVENT1 at 0x20 and 0x21 and writes INT_CLEAR1 (0x18).
  - Unmask PlugInsertOrRemoval, LiquidDetection [60] and any fault events in each bundle.
  - Do a 9-clock bus clear before the first transaction, because SDA/SCL sat at 0 V while 3V3 was down (A's area).
- **Confidence:** verified (TRM and datasheet tables).

### C-11 [CONFIG] TPS25751 bundle questions Q12/Q13 (BQ25756 IAC_DPM and VAC_DPM tracking the contract) are not on the bring-up checklist

- **Where:** U402/U502 bundles → U403/U503 registers 0x06 (IAC_DPM) and 0x08 (VAC_DPM) over I2Cc.
- **Evidence:**
  - SLVUCP9B §4.3.1.2 steps 5–6: Q12 sets IAC_DPM to the negotiated contract current plus a chosen margin ("negotiates a PD contract at 3A, then the INDPM is set to 3.15A"). Q13 sets VAC_DPM below the contract voltage.
  - Without it, the only input limit is ILIM_HIZ (R414 3.6k): a 5.3–5.8 A ceiling (B). A boost-mode charge from a 9 V 3 A PDO would then overload the source until the source's OCP trips.
  - `bringup-config-checklist.md` §3 lists VFB_REG, ICHG_REG and others, but not Q12/Q13. B agreed this item is mine.
- **Proposed setting:** add to §3: "Q12 INDPM margin 0–5 % (IAC_DPM tracks the contract current); Q13 VINDPM 5 % below the contract voltage." Verify by reading reg 0x06/0x08 back over J402 after a 9 V 3 A contract.
- **Confidence:** verified (EVM guide). That the tool writes these on every new contract is TI's description, not tested.

### C-12 [DOC] R441/R541 Notes still say "TPD2S300 FLT pull-up"

- **Where:** R441/R541 Notes property.
- **Evidence:**
  - `parts.txt`: "TPD2S300 FLT pull-up (open drain, 1.7-300k to 2.7-5.5 V) …".
  - The part is now the TPD4S201. Its limits are the same: FLT pull-up 1.7–300 kΩ, rail 2.7–5.5 V (TPD4S201-Q1 §5.5). So the value of 100k to LDO_3V3 stays correct. TI's EVM uses 10k (R117).
- **Proposed fix:** "TPD4S201 FLT pull-up (open drain; 1.7–300 kΩ to 2.7–5.5 V). FLT → GPIO3 = Fault_Input_Event (33): CC or SBU OVP (and an ESD-triggered OVP) forces Type-C error recovery, as on TI's TPS25751EVM."
- **Confidence:** verified.

### C-13 [DOC] C451/C551 Notes justify 50 V from the 40 V ring, but don't mention the datasheet's 63 V minimum

- **Where:** C451/C551 Notes property.
- **Evidence:** see C-1. If C-1 is not adopted, the note should still record the conflict and the EVM precedent, so nobody "corrects" it blindly.
- **Proposed fix:** update with C-1, or note: "TPD4S201-Q1 §5.5 fn 2 says ≥ 63 V (100 V rec.); §7.2.2.1 and TI's EVM C69 use 50 V".
- **Confidence:** verified.

### C-14 [DOC] Stale or incorrect lines in `circuit-description.md` §7 and `power-budget.md` for USB-port parts

- **Where and fixes:**
  - `circuit-description.md` §7.1, line 141: "TPD2S300 (U405/U505) … the TPD2S300 FLT on GPIO3" → TPD4S201 (item 39). CC also now passes through U405: "CC1/CC2 → TPS25751 CC1/CC2" (line 140) should read "→ U405 C_CCx/CCx → TPS25751 CC1/CC2".
  - Line 142: the SMAJ22A is cited as "(C148220)". The BOM fits C41376403 ("JLC preferred"). Make them agree and hold the fitted part's datasheet (C-4).
  - Line 143: the ESD bullet is three revisions braided into one sentence. It says "rev A6, 2026-10-14: … TPD4S201", but the TPD4S201 is item 39 (rev A7 period). Rewrite: "CC and SBU: TPD4S201 (IEC ±8 kV contact, ±35 V surge, 28 V short-to-VBUS); D±: none (shorted together by R440)."
  - Line 148: "Add unpopulated divider footprints on each ADCIN so other strap options can be tried." There are none: R1–R4 are single 0 Ω parts on the root sheet. Either add the 0603 divider pairs or delete the sentence. To change a strap you need to know that R1 ties ADCIN1 to LDO_3V3: moving it to GND gives decoded 0, and SafeMode #2 then collides with port 2's 0x21.
  - Line 150: "I2Cc … pull-ups to LDO_3V3" is correct (R402/R403 3.3k, R404 10k). The brief's guess "R421–R423" is wrong: those are the STAT1/STAT2/PG pull-ups to 3V3.
  - §7.3 last bullet: "CE pulled low (charge enabled)" is stale since rev A5 (R417 pull-up to 3V3 plus CHG_INH, sheet note 11).
  - `power-budget.md` 3.3 V table: the "2 × TPD2S300" row → 2 × TPD4S201 at 224 µA typ / 320 µA max (C-2).
  - `mcu-io-power-states.md` line 71: see C-6.
- **Confidence:** verified (file lines read).

### C-15 [NOTE] EPR 28/48 V source and other over-voltage cases: protected by protocol, not by hardware; the hardware survives only up to about 28 V

- **The "25 V parts":**
  - Nothing rated 25 V sits on VBUS or PPHV. Checked from `parts.txt`:

    | Net | Parts | Rating |
    |---|---|---|
    | VBUS | C406, C450 | 50 V |
    | PPHV | C409, C449 | 50 V |
    | AC_SNS_N | C420/C423/C424/C427 MLCCs, C421 polymer | 35 V |

  - The 25 V items in this scope are datasheet limits:
    - TPS25751 CC1/CC2 abs-max is 26 V. They sit behind U405, whose CC OVP trips at 5.6–6.2 V.
    - TPS25751's recommended CVBUS rating is 25 V; we fit 50 V.
    - The battery-side 25 V caps (C431–C435) cannot see VBUS without a converter fault (B).
- **EPR:**
  - An EPR source applies 28/36/48 V only after EPR Mode entry, which needs an EPR-capable sink and cable. The TPS25751 is SPR only (§9.2.1.1: PPS 5–21 V; TPD4S201 "20V SPR"), so a compliant EPR charger stays at ≤ 20 V.
  - **Faulty source at 28 V:**
    - The SMAJ22A (VBR ≤ 26.9 V) conducts a few amps. Its dynamic resistance is about (35.5 − 26)/11.3 ≈ 0.85 Ω, so roughly 2–3 A, about 70 W.
    - It fails, most likely short, which then trips the source's OCP.
    - Meanwhile VBUS is held at about 27–28 V: exactly the TPS25751 and TPD4S201 abs-max.
    - TPS25751 OVP opens PPHV (VOVP4RCP is configurable up to 24 V, §6.11), so the BQ25756 (85 V) is isolated.
  - **At 48 V:** the TPS25751 VBUS pins exceed abs-max until the TVS fails short. Expect U401 damage.
  - A TVS2200 (C-4) would not change this. Only a series OVP FET would, and that is not worth adding for a protocol-violating source.
- **Reverse-polarity cable** (VBUS negative, non-compliant DIY cable):
  - D401 forward-conducts at about 0.8–1.5 V. That exceeds the TPS25751 VBUS −0.3 V abs-min and the TPD4S201 C_x −0.3 V abs-min.
  - The parts are sacrificial; no design action.
- **CC, SBU or DP/DN shorted to VBUS at 20 V:**
  - CC and SBU: the TPD4S201 tolerates 21.5 V hot-plug (VSTBUS) and 28 V DC. Its OVP opens in 70–80 ns, with a system-side clamp of ≤ 7 V. FLT goes low and GPIO3 forces error recovery, which removes VBUS.
  - Margin: PD 20 V +5 % = 21 V against 21.5 V.
  - DP/DN connect only to each other (R440), so VBUS on them is harmless.
- **Confidence:** verified ratings; inferred TVS behaviour beyond its table.

### C-16 [NOTE] Dead-battery and no-battery boot sequence is correct for a DRP with the TPD4S201

- **Sequence** (3V3 down, USB source attached):
  1. U405 is unpowered, so its RD_DB (4.1–6.1 kΩ) is on C_CC via RPD_Gx = C_CCx (table 6-1, "Unpowered, dead battery support"). The source applies vSafe5V.
  2. U401 runs from the VBUS LDO (§8.3.2). LDO_3V3 rises and powers U405 VPWR and U402 together.
     - This is the shared supply that TPD4S201-Q1 §6.3.4/§7.3 says is "critical".
     - The TPS25751 shows its own dead-battery Rd clamp while VIN_3V3 = 0 (§8.3.4.4, VCLAMP §6.12).
  3. U405 turns its FETs on within 3.5 ms, then removes RD_DB (tON_FET_DB ≤ 9.5 ms).
     - During the overlap the source sees the TPS25751 clamp in parallel with 5.1 kΩ: about 1.2–1.7 V at IRp3.0. That is above vRa, so it still reads as Rd.
     - The source's tCCDebounce (100–200 ms) also covers the overlap.
  4. SafeMode keeps the sink path off until the EEPROM bundle loads (table 8-6). The bundle then negotiates and closes PPHV, with the SS setting 0 inrush at about 0.06 A (sheet note 9).
  5. The BQ25756 runs from VAC. CE reads low because R417 pulls up to a dead 3V3, so charging is allowed. The TPS25751 configures the charger over I2Cc.
- **3V3 load in dead-battery mode:** on LDO_3V3 the worst case is about 4.6 mA. That is EEPROM read about 2 mA, two 3.3k pull-ups at 1 mA each when low, R404 0.33 mA, and U405 0.16 mA. The VLDO_3V3 spec covers ≤ 18 mA (§6.6).
  - Note: the TPS25751S table §6.3.2 lists a 5 mA limit for the VBUS-LDO case. The D-variant table does not, but we are close to it if it applies. Inferred, and not a problem with the duty cycle.
- **Back-power:** none found.
  - The VIN_3V3 switch is open in dead-battery mode.
  - The I2Ct pins are pulled to 0 V by the dead 3V3 pull-ups. That is reverse bias to LDO_3V3.
- **Once 3V3 is back:** the MCU must send 'DBfg' (TRM §4.6.2). This is already in `bringup-config-checklist.md` §3.
- **Both EEPROMs:** they boot independently, each on its own I2Cc bus at 0x50 (§8.4.1: "each device is connected to a unique EEPROM"). M24512 = 64 KB ≥ the 36 KB minimum (§8.3.11). The ID page answers at 0x58, and the BQ25756 at 0x6B: no collision.
- **Confidence:** verified datasheet behaviour; the parallel-Rd voltage is inferred arithmetic.

### C-17 [NOTE] TPD4S201 FLT also fires on CC OVP and on an ESD-induced OVP, so an ESD gun hit on CC/SBU will drop VBUS through error recovery

- **Evidence:**
  - TPD4S201-Q1 table 6-1: the "IEC ESD generated over voltage condition" row has FLT low and the FETs off.
  - GPIO3 = Fault_Input_Event (33) puts the port into Type-C error recovery (TRM table 5-6).
  - This is TI's intended behaviour (§7.2.2.3, "forcing a detach … is recommended") and review 3's H1 carried over correctly.
  - Record it so that ESD qualification doesn't log a re-attach as a failure.
  - FLT is High-Z below VPWR UVLO, so there is no false fault at power-up (table 6-1).

### C-18 [NOTE] TPD4S201 datasheet artefacts

- **Evidence:**
  - §5.1 lists a "VBUS" pin (abs-max 28 V), and §5.5 lists "VBUS 0–21.5 V" and "VBUS_LV capacitance 0.1 µF".
  - Neither the RGR (Q1) nor the RUK package has a VBUS pin (pin tables, both datasheets). Pins 16, 17, 19 and 20 are NC ("may be left floating or grounded") and are correctly unconnected.
  - The RUK (EVM) and RGR pinouts are identical, so the EVM fig. 5-5 wiring transfers one to one.
  - The fitted MPN TPD4S201TRGRRQ1 appears in the Q1 orderable addendum. The datasheet's own figures name it TPD4S201QRGRR.

### C-19 [NOTE] Brief items checked with no finding: the USB 2.0 data and VBUS-discharge items

- **USB 2.0 data:** not used. DP (A6/B6) and DN (A7/B7) are each tied across the two rows and joined by R440 0 Ω (DCP).
- **D± ESD:** review 3 closed it ("nothing to damage"). I found no new evidence.
- **vSafe0V:**
  - IDSCH is 4–15 mA at 22 V (§6.11). It acts on VBUS only (about 5 µF: C406 plus C450), because the PPHV switch is open when unattached.
  - 20 V → 0.8 V takes about 5 µF × 19.2 V / 4 mA ≈ 24 ms, well inside the 650 ms tSafe0V.
  - The PPHV-side bank stays charged behind the open switch. That is the TPS25751/BQ25756 firmware's responsibility (RCP blocks it).
- **100 W over two ports:** decided in review 2 (A-1, closed). Per-port bundles: USB1 up to 100 W, USB2 20–30 W, and the MCU lowers USB1 on USB2's attach. Not re-raised.
- **Sink and source range 5/9/15/20 V:**
  - Source: PDO1 on PP5V; 9–20 V on PPHV (TRM PDO power-path field "2h = PP_EXT"; datasheet §9.2.2.1 PPS via PPHV with the BQ25756).
  - Sink: 5–21 V on PPHV into VAC, with ACUV 4.1 V and ACOV 22.5 V (±1.5 %), above PD's 21 V.
  - The hardware supports both.

---

## Checked and correct

**U401/U501 TPS25751D: pin by pin** (table 5-1, all 38 pins plus 2 EPs)
- **Symbol and footprint:**
  - Pins 20, 23, 32 and 34 are single symbol pins on merged footprint pads.
  - Pad 20 spans PPHV pins 20–22 (0.65 × 1.175 mm). Pad 23 spans VBUS_IN 23–25. Pad 32 spans VBUS 32/33 (at −0.2 mm, 0.65 mm wide, over pins at 0.0/−0.4). Pad 34 spans PP5V 34/35.
  - Checked against the pad coordinates in `TI_WQFN-38-2EP_REF0038A_…_2oz.kicad_mod`.
  - GND [11, 12, 14, 31, 39] and DRAIN [15, 30] use stacked pins. EP 39 is GND; EP 40 is PD_DRAIN, isolated.
- **Power pins:**
  - VBUS (32) and VBUS_IN (23) both go to connector VBUS.
  - PPHV → BQ25756 VAC and R424.
  - PP5V ← TPS62933 at 5.08 V (inside 4.9–5.5 V).
  - VIN_3V3 ← 3V3 via R401 0R.
  - LDO_3V3 and LDO_1V5 have caps only (LDO_1V5 has no external load, as required).
- **Caps** (§6.4, with DC bias):

  | Pin | Parts | Effective | Window |
  |---|---|---|---|
  | VIN_3V3 | C403 10 µF X5R 0805 | about 7–8 µF | 5–10 µF |
  | LDO_3V3 | C404 + C408 + C452 | about 9.5 µF | 5–25 µF |
  | LDO_1V5 | C405 10 µF X5R 0603 | ≤ 11 µF | 4.5–12 µF |
  | VBUS | C406 4.7 µF 50 V + C450 10 nF | about 2.5–4 µF at 20 V | 1–10 µF |
  | PP5V | C407 10 µF at the pin + C441/C442 + C443 220 µF polymer | — | ≥ 120 µF, 10 µF at the pin |

- **Ratings against our plan:**
  - VBUS_IN/PPHV: recommended max 22 V, abs 28 V; our 20 V +5 % = 21 V.
  - PPHV path: 7 A continuous, about 20 mΩ, so 0.5 W at 5 A.
  - PP_5V: 3 A.
- **Straps:** ADCIN1/2 per table 8-6; SafeMode on both. The ADCIN tie-to-rail and tie-to-GND options are allowed by table 8-2.
- **I/O:**
  - I2Ct SDA/SCL go to the MCU bus (A's pull-ups to 3V3; I2Ct abs-max 4 V).
  - I2Ct_IRQ → IRQ_N, open drain.
  - I2Cc SDA/SCL: R402/R403 3.3k to LDO_3V3, as table 8-4 asks.
  - I2Cc_IRQ ← BQ25756 INT with R404 10k to LDO_3V3 ("do not tie to GND", satisfied).
- **GPIOs:**
  - GPIO0, 1, 2 and 11 are tied to GND ("tie to ground when unused").
  - GPIO3 ← U405 FLT.
  - GPIO4/5 ← SBU1/2_SNS (LD1/LD2).
  - GPIO6 → LIQ_PU (R442 100k to LDO_3V3).
  - GPIO7 → LIQ_PD (R443 100k to GND).
  - All inside the GPIO 6 V abs-max; FLT pulls up to 3.3 V.
- **ERC:** exactly 8 warnings: GPIO0, 1, 2 and 11 on U401 and U501, pin-to-pin bidirectional against power output on the GND tie. Benign.

**U402/U502 M24512-DFMC6TG**
- Pin 1 E0, pin 2 E1, pin 3 E2 all to GND → 0x50 (TPS25751 requires 0x50).
- Pin 4 VSS plus the EP pad 4 to GND (datasheet: the centre pad goes to VSS or is left floating).
- SDA/SCL on I2Cc. WC (pin 7) to GND, so writes are enabled for FLwd updates.
- VCC from LDO_3V3, inside 1.7–5.5 V. C408 is nearby.
- 64 KB ≥ the 36 KB minimum.

**U405/U505 TPD4S201-Q1 (item 39): pin by pin against table 4-1**

| Pin | Name | Connected to |
|---|---|---|
| 1 | C_SBU1 | J401 A8 SBU1 |
| 2 | C_SBU2 | J401 B8 SBU2 |
| 3 | VBIAS | C451 (C-1) |
| 4 | C_CC1 | J401 A5 |
| 5 | C_CC2 | J401 B5 |
| 6 | RPD_G2 | C_CC2 |
| 7 | RPD_G1 | C_CC1 (dead-battery option, as EVM fig. 5-5 R113/R115) |
| 8, 13, 18 | GND | GND |
| 9 | FLT | SBU_FLT (R441 100k to LDO_3V3) |
| 10 | VPWR | LDO_3V3 with C452 1 µF X5R (about 0.9 µF at 3.3 V; range 0.3–1 µF) |
| 11 | CC2 | U401 CC2 |
| 12 | CC1 | U401 CC1 |
| 14 | SBU2 | SBU2_SNS |
| 15 | SBU1 | SBU1_SNS |
| 16, 17, 19, 20 | NC | Unconnected |
| 21 | EP | GND |

- **Ranges:** SBU operating 0–4.3 V against our 3.3 V maximum. SBU OVP is 4.0–4.41 V and CC OVP 5.6–6.2 V, so VCONN of 5.5 V maximum passes. The CC FETs carry 600 mA at TJ ≤ 105 °C against 315 mA of VCONN, with RON 0.42 Ω, a 0.13 V drop.
- **Footprint:** matches the RGR0020C land pattern (p. 27): 0.6 × 0.24 mm pads at ±1.65 mm, 0.5 mm pitch, 2.05 mm EP, vias at ±0.775 mm. Pin 1 is top-left with counter-clockwise numbering.
- **Review 3 H1 carry-over:** FLT → GPIO3 = Fault_Input_Event (33) (TRM table 5-6: "When set low by the system, Port1 enters the Type-C Error Recovery State"). The pull-up is inside the 1.7–300 kΩ / 2.7–5.5 V window. Carried over correctly.

**Liquid detection (Q403–Q406, R436–R443)**
- Topology matches TPS25751 fig. 9-8 and EVM fig. 5-6:
  - PFET source on LDO_3V3, drain through 100k (R436/R437) to SBUx_SNS;
  - NFET source on GND, drain through 1M (R438/R439) to SBUx_SNS;
  - shared gates.
- Values match table 9-3 (100k / 1M; the EVM uses 249k, see C-9).
- AO3401A Vgs(th) −0.5 to −1.3 V and AO3400A 0.65 to 1.45 V, both fully on with 3.3 V GPIO drive.
- Review 3 H2 gate pulls are present: R442 (LIQ_PU to LDO_3V3, holds the PFETs off) and R443 (LIQ_PD to GND, holds the NFETs off), both 100k as EVM R105/R110.

**J401/J501 connector**

| Pins | Function | Net |
|---|---|---|
| A1/B12, B1/A12, SH | GND | GND |
| A4/B9, B4/A9 | VBUS | VBUS |
| A5 | CC1 | C_CC1 |
| B5 | CC2 | C_CC2 |
| A6, B6 | DP1, DP2 | DP |
| A7, B7 | DN1, DN2 | DN |
| A8 | SBU1 | SBU1 |
| B8 | SBU2 | SBU2 |

- The assignments match the Shou Han pin table.
- Footprint pad order left to right is A1/B12, A4/B9, B8, A5, B7, A6, A7, B6, A8, B5, B4/A9, B1/A12, at 0.5 mm narrow pitch and ±2.4 / ±3.2 mm wide pads. This matches the drawing's recommended layout (6.40 / 4.80 / 3.50 mm spans).
- The connector is rated 20 V / 5 A, enough for our plan with no margin. Contact resistance is 40 mΩ per pin.

**D401/D501:** cathode (pin 1) on VBUS, anode to GND; KiCad D_SMA pad 1 is the cathode. VR 22 V ≥ 21 V; VBR within 22–28 V (C-4 covers the clamp).

**Port 2 = port 1:** checked by script (`scratch-c/cmp.py` and a `parts.txt` diff).
- 0 net differences except /P1_ADCINx, /P2_ADCINx, the LDO_3V3 net name (/P1_LDO_3V3 carries R1) and EN_5V1/EN_5V2.
- 0 part differences in value, footprint, MPN, LCSC or Notes.
- U401 and U501 PCB pads carry the same nets in the same positions.

**TPS25751 ↔ BQ25756 control before the MCU boots**
- **Charging:** the TPS25751 bundle owns the charger registers over I2Cc. CE is pulled up to 3V3 by R417, so with 3V3 up and the MCU in reset or hi-Z, charging is inhibited; with 3V3 down (dead pack), charging is allowed.
- **Reverse mode:** CE does not gate it (BQ25756: "charging is enabled when EN_CHG bit is 1 and CE pin is LOW"), so sourcing is under TPS25751 control only. This matches sheet note 11.
- **Bundle items that matter:** DIS_CE_PIN = 0, plus C-11.

**Fault injection, VBUS short to GND while sourcing 5 V:** the PP_5V current clamp acts in 1.15 µs, then the switch turns off after tILIM 5.1 ms (§6.8). Correct. The 20 V case is C-7.

---

## Round 1 summary (5 lines)

1. Counts: 0 CRITICAL, 0 MAJOR, 8 MINOR, 3 CONFIG, 3 DOC, 5 NOTE. Port 2 is a verified exact copy of port 1, and the two I2Ct addresses differ (0x20 and 0x21, SafeMode).
2. Top item, C-1: the TPD4S201 VBIAS cap C451/C551 is rated 50 V, while the datasheet's ROC footnote asks for at least 63 V (100 V recommended). The datasheet contradicts itself and TI's EVM uses 50 V. Fix: a 100 V 0603.
3. Top item, C-3: the CC capacitance (330 pF plus up to 120 pF in the TPD4S201) reaches 466 pF against the TPS25751's 480 pF maximum. TI's EVM uses 220 pF with this protector, so C401/C402 should go to 220 pF.
4. Top item, C-2: the TPD4S201 draws 112–160 µA per port at all times (it was about 4 µA for the TPD2S300). Pack idle drain rises from about 161 to about 220 µA, and power-budget.md is stale.
5. Also: the SMAJ22A clamp sits above the 28 V abs-max at rated surge (TI recommends a TVS2200, C-4). The PP5V buck has only about 3.2–3.5 A of headroom (C-5). Sourcing at 20 V still depends on the MCU-gated PP5V (C-6). VBUS-short behaviour on PPHV needs a bench test (C-7). Test pads are missing (C-8).

---

## After round 2

**Challenges answered.**
- A, B and D each challenged C-1, C-4, C-5, C-6 and C-7 (A-challenge.md, B-challenge.md, D-challenge.md).
- Nobody disputed C-2, C-3, C-8 to C-14 or C-15 to C-19. A, B and D agree with C-2, and B and D spot-checked C-3 (B confirmed the 466 pF arithmetic).

### C-1, VBIAS cap rating: **CONCEDE. MINOR → NOTE.** C-13 (DOC) stands, amended

- B's evidence is right. I re-checked it in the non-Q1 datasheet (`scratch-c/tpd4s201.txt` l.1414–1417): "the internal diode clamps limit the voltage exposed to the C_CCx and C_SBUx pins to around 28V. Therefore, at least a 28V capacitor is required."
    - The -Q1 §6.3.1 text says the same: "limit the peak ringing to approximately 28V".
    - VBIAS sits behind a forward "hiding diode", so it sees at most about 28 V, not the 40 V unclamped ring.
- The 63 V / 100 V footnote gives capacitance derating as its reason. The binding requirement is the effective capacitance: ≥ 0.04 µF.
- A 50 V X7R 0603 at ≤ 28 V (56 % stress) keeps more than 0.04 µF, and TI's EVM fits 50 V.
- **Final:** NOTE. The 100 V X7R swap stays as an optional, cents-level improvement.
- **C-13 amended text for the Notes property:** "TPD4S201 VBIAS: ≥ 0.04 µF effective; the internal clamps hold VBIAS to about 28 V in a short to VBUS (non-Q1 §7.2.2.1). 50 V X7R as TI's EVM C69. The -Q1 §5.5 footnote's 63/100 V is for derating."

### C-4, VBUS TVS: **DEFEND MINOR, with B's amended evidence. Part settled: TVS2200DRVR**

**Accepted from B:**
- The fitted R+O SMAJ22A (C41376403, `scratch-b/smaj22a-ro.pdf`) has the same row as Littelfuse: VR 22 V, VBR 24.4–26.9 V, VC 35.5 V at 11.3 A. That rating is **10/1000 µs**, not 8/20.
- Its dynamic resistance is about 0.76 Ω, so VBUS stays ≤ 28 V only below about 1.4 A (high-VBR part) to 4.7 A (low-VBR part).
- ESD is absorbed by C406/C450, so it does not depend on the TVS type.
- A live 20 V hot-plug clamps at roughly **27–29 V**: at the TPS25751 VBUS/PPHV 28 V abs max, not safely below it.
- So the exposure is real but limited to non-compliant events. MINOR is right (D agrees).

**SMAJ18A against TVS2200 for VBUS:**
- **SMAJ18A** (B/D's suggestion for J104 in D-5) **is unsuitable on VBUS.**
    - Its row (`smaj22a.txt` l.386–394): VR 18.0 V, **VBR 20.0–22.1 V**, VC 29.2 V.
    - A legal PD 20 V contract may sit at 21 V (+5 %), and PPS goes to 21 V. A low-VBR unit would then conduct in normal operation, roughly (21 − 20) / ~0.7 Ω ≈ 1 A on a 1 W part, and fail.
    - It also sits below our ACOV 22.5 V stop. It stays fine for J104 (PACK_P ≤ 16.8 V; D-5).
- **TVS2200DRVR**, the part TI names in TPS25751 §6.1.1 note 4 and fits on the TPS25751EVM (U2/U3):
    - 22 V standoff;
    - flat clamp, 28.4 V max at 40 A 8/20 µs (TI product page);
    - VBR about 24.6–25.9 V (distributor listings disagree; take the TI datasheet at layout time).
    - It stays below or at the 28 V abs max where the SMAJ22A reaches 35.5 V.
- **Sourcing** (fetched 2026-10-14, inferred from listings; I did not download the TI datasheet):
    - LCSC **C523793**, about 5.5k in stock (LCSC listing via web search).
    - JLCPCB part page `jlcpcb.com/partdetail/TexasInstruments-TVS2200DRVR/C523793`: "SMT Assembly, Economic and Standard", library type **Extended**.
    - The local JLC database in the KiCad MCP is not populated, so I could not cross-check it there.
- **Final recommendation:**
    - Fit TVS2200DRVR (WSON-6 2 × 2 mm; a new footprint, pads 1–3 to VBUS and 4–6 plus EP to GND per the TI land pattern, to be checked against the datasheet) at J401/J501. Extended part, about $0.20.
    - Dev-board option: keep the D401 SMAJ22A footprint as DNP or fitted in parallel. It adds energy capability for a stiff over-voltage source, and the TVS2200 sets the clamp level.
    - Download the TI datasheet into `datasheets/` before layout.
- **Grade:** MINOR.

### C-5, PP5V buck headroom: **unchanged, MINOR**

- B agrees, and adds that the hiccup off time is 10.5 × tSS ≈ 50 ms, and hiccup happens only below 65 % UVP. My text already says PP5V sags with foldback rather than hiccups.

### C-6, sourcing depends on the MCU (EN_5Vx): **ACCEPT A's and D's amendments. Stays MINOR, plus a CONFIG line**

**D's stronger statement is right.**
- Unattached Rp runs from LDO_3V3 (TPS25751 §6.12, VOC_3.3), so attach *detection* survives EN_5Vx low.
- But IRp1.5/IRp3.0 and VOC_5 need PP5V, and vSafe5V comes from PP5V. So **every new source attach** needs the MCU to raise EN_5Vx within the Type-C VBUS turn-on window, not only the 5 V contract.
- This links to `mcu-io-power-states.md` open item 7.

**Hold-up through an MCU reset under an existing contract:**
- PP5V bulk is about 245–250 µF (C443 220 µF polymer plus C441/C442/C407).
- Load with the buck off is Rp about 0.33 mA, R433/R434 40 µA, and VCONN to an e-marker.

| Total load | Time from 5.08 V to the 4.75 V IRp floor (A, D) |
|---|---|
| 1 mA | about 80 ms |
| 5 mA | about 16 ms |
| 10 mA | about 8 ms |

- The CC2340 reboots in 0.35–0.45 ms (SWRS349A §7.17.2, per D).
- So a 20 V contract *can* ride through a WDT reset, if firmware restores EN_5Vx in its first few ms. It cannot from a ROM-bootloader hang (A-1) or an unprogrammed part.

**New CONFIG line** (for `bringup-config-checklist.md` §4):
- "First action after any reset, before BLE/stack init: restore EN_5V1/EN_5V2. Take the state from retention RAM, or set high if the TPS25751 STATUS shows an attached source role or VBUS present. The CC2340 keeps no GPIO state across reset."

**Bring-up test** as in C-6, plus measuring the PP5V droop time with the e-marked 5 A cable.

- **Final:** MINOR, plus the CONFIG line above.
- **DOC:** `mcu-io-power-states.md` line 71 should say "a 9–20 V contract survives an MCU reset only if firmware restores EN_5Vx within about 10–80 ms; a new attach always needs the MCU".

### C-7, VBUS short while sourcing at 20 V: **unchanged, MINOR, with B's half added**

- B confirms the BQ25756 side:
    - Reverse-mode UVP (VAC < 80 % of VAC_REV, REG0x1E) stops the converter.
    - Q402's body diode blocks a pack-fed freewheel.
    - So the PPHV switch sees the bank's about 26 mJ, with τ ≈ 130 µF × 35 mΩ ≈ 4.5 µs, plus a few µs of converter current. The peak amplitude exceeds the switch's 10 A pulsed rating, but the I²t is small.
- **Add to the bench test:** ACP−ACN abs max is ±0.3 V (bq25756 §5.1). 100 A × 5 mΩ = 0.5 V at R424, but the R425/R426 10 Ω + C414 0.47 µF filter (τ ≈ 9.4 µs) attenuates a µs pulse. Measure ACP−ACN at the IC pins during the short.

### Final severities, Reviewer C

| Item | Final |
|---|---|
| C-1 | NOTE (was MINOR) |
| C-2 | MINOR |
| C-3 | MINOR |
| C-4 | MINOR (fit TVS2200DRVR, C523793) |
| C-5 | MINOR |
| C-6 | MINOR, plus a CONFIG line |
| C-7 | MINOR |
| C-8 | MINOR |
| C-9, C-10, C-11 | CONFIG |
| C-12, C-13 (amended), C-14 | DOC |
| C-15 to C-19 | NOTE |

**Totals:** 0 CRITICAL, 0 MAJOR, 7 MINOR, 3 CONFIG, 3 DOC, 6 NOTE.
