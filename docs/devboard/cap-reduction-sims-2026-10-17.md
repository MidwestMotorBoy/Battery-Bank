# Capacitor reduction: simulations (2026-10-17)

For [rev2-changes.md item 1d](rev2-changes.md) (shrink the board, electrolytics first). Script: [`hardware/DevBoard/tools/cap_sims.py`](../../hardware/DevBoard/tools/cap_sims.py) (numpy; writes `cap_sims.json`). Every figure is per port; port 2 is identical. These results pick what to try at bring-up. They don't replace the bring-up measurements.

## What was simulated

| Check | How | Limit used |
|---|---|---|
| Effective capacitance | DC-bias fit per part, then −20 % tolerance and −10 % at 85 °C on MLCCs, −20 % on polymers | BQ25756 §5.3: C<sub>IN</sub> and C<sub>OUT</sub> ≥ 80 µF *after derating*; TPS62933 table 10-2: 5 V at 1.2 MHz, 20 µF typical and 10 µF minimum effective |
| Switching ripple and RMS per capacitor | Ideal CCM current of the 4-switch charger (600 kHz, 2.2 µH) in buck or boost. Each harmonic up to 10 × f<sub>SW</sub> divides between the capacitors (ESR + ESL + derated C), the 0.1 µF HF cap and the external path (USB cable, or pack + wiring). Operating points: forward 5/9/15/20 V at the PD current into a 12–16.8 V pack (ICHG 5.5 A); reverse from a 10–16.8 V pack to 5/9/15 V at 3 A and 20 V at 5 A. | Polymer datasheet ripple ratings; assumed about 2.5 A (1206) and 3 A (1210) for MLCCs |
| Input-filter damping | \|Z<sub>out</sub>\| of source + bank against the charger's negative input resistance V²/P (Middlebrook). USB cable 0.5–1.5 µH at 60 or 150 mΩ. Pack 0.2–0.5 µH at 50 or 85 mΩ. | Margin ≥ 10 dB is comfortable, < 6 dB risks the input oscillating |
| PP5V load step | TI eq. 21 (TPS62933 §10.2.2.8, about 8 cycles to respond), 0.5 → 3 A step, from a 16.8 V pack | ≤ 250 mV undershoot keeps VBUS in range |

## Results

### Charger, USB side (AC_SNS_N)

Area is courtyard area per port. Ripple is the worst case.

| Bank | C<sub>eff</sub> worst at 20 V | ≥ 80 µF | Area | Ripple | Most stressed part | Damping margin |
|---|---|---|---|---|---|---|
| **U0 now: 4 × 22 µF 1210 + 100 µF polymer** | 104 µF | yes | 112 mm² | 162 mV | polymer 65 % | 19.7 dB |
| U1: 4 × 1210, no polymer | 25 µF | **no** | 58 mm² | 162 mV | 1210 43 % | 10.7 dB |
| U2: 2 × 1210 + polymer | 92 µF | yes | 83 mm² | 304 mV | **polymer 123 %** | 18.9 dB |
| U3: 6 × 1210, no polymer | 37 µF | **no** | 88 mm² | 108 mV | 1210 29 % | 14.0 dB |
| U4: 3 × 1210 + polymer | 98 µF | yes | 98 mm² | 212 mV | polymer 85 % | 19.3 dB |

All of the worst cases occur in reverse mode, 20 V 5 A from a 10 V pack, with the converter boosting.

### Charger, battery side (BAT_SNS_P)

| Bank | C<sub>eff</sub> worst at 16.8 V | ≥ 80 µF | Area | Ripple | Most stressed part | Damping margin |
|---|---|---|---|---|---|---|
| **B0 now: 3 × 22 µF 1206 + 100 µF hybrid** | 90 µF | yes | 85 mm² | 102 mV | hybrid 51 % | 20.1 dB |
| B1: 3 × 1206, no hybrid | 10 µF | **no** | 32 mm² | 117 mV | 1206 22 % | **4.6 dB** |
| B2: 2 × 1206 + hybrid | 87 µF | yes | 75 mm² | 122 mV | hybrid 63 % | 19.9 dB |
| B3: 3 × 47 µF 1210, no hybrid | 18 µF | **no** | 44 mm² | 66 mV | 1210 15 % | 9.7 dB |

All of the worst cases occur in forward mode, 9 V into a 16.8 V pack, with the converter boosting.

### 5 V buck (TPS62933)

| Bank | C<sub>eff</sub> at 5.16 V | Area | Ripple | Est. undershoot, 0.5 → 3 A |
|---|---|---|---|---|
| **P0 now: C407 + 2 × 22 µF 1206 + 100 µF polymer** | 103 µF | 79 mm² | 3 mV | ~60 mV |
| P1: C407 + 2 × 1206, no polymer | 23 µF | 25 mm² | 3 mV | ~270 mV |
| P3: C407 + 3 × 1206, no polymer | 33 µF | 36 mm² | 2 mV | ~190 mV |
| P2: C407 + 1 × 1206 | 13 µF | 15 mm² | 6 mV | ~490 mV |
| **I0 now: input, 2 × 10 µF 50 V 1206** | 5.7 µF at 16.8 V | 21 mm² | 90 mV | — (0.68 A each) |
| I1: input, 1 × 10 µF | 2.9 µF | 11 mm² | 184 mV | — (1.38 A) |

## What this says

1. **The charger polymers stay.** The BQ25756's own limit is ≥ 80 µF after derating on each side, and the polymers supply 70–90 % of it. Without them the banks are 10–25 µF. Making up 80 µF from MLCCs alone takes about 13 × 1210 on the USB side (about 190 mm², against 112 mm² now). So the polymers are the *smallest* way to meet the rule, not the largest. On the battery side the hybrid is also what damps the pack leads: without it the margin falls to 4.6 dB.
2. **Small MLCC trims inside the 80 µF rule:**
   - **B2: drop one 1206 on the battery side** (C435/C535). It still has 87 µF, the hybrid runs at 63 % of its rating, and ripple goes 102 → 122 mV. Saves about 10 mm² per port. Low risk.
   - **U4: drop one 1210 on the USB side** (C427/C527). It still has 98 µF, but the polymer reaches 85 % of its rating in the worst reverse case (20 V 5 A from a 10 V pack). Saves about 15 mm² per port. Only if bring-up shows the polymer stays cool, or if firmware derates reverse power at low pack voltage.
   - U2 (two 1210s gone) overloads the polymer (123 %). No.
3. **The biggest win is the PP5V polymer C443/C543.** Swapping it for one more 22 µF 1206 (P3) still gives 33 µF, which is above TI's 20 µF typical. The estimated step undershoot of about 190 mV is within the 250 mV budget. That saves about 43 mm² per port. It also brings the TPS62933 back near TI's tested range: the present 103 µF is 5× typical, which the datasheet warns can hurt start-up and loop stability (review 4 already flagged this).
   - **Blocker:** the TPS25751 datasheet's capacitor table lists 120 µF on PP5V, citing USB PD *cSrcBulkShared*. That name suggests it applies to a supply shared between ports. Each port here has its own TPS62933, which would fall under the much smaller dedicated-supply value. This is unverified: confirm in the USB PD spec, or with TI, before relying on it.
   - **Checked 2026-10-17: the dedicated-supply value applies.**
     - USB PD Rev 3.0 v1.2 (quoted in Microchip AN3265, table 5-3) defines cSrcBulk as the "source bulk capacitance when a port is powered from a dedicated supply", minimum 10 µF. cSrcBulkShared (120 µF) is its shared-supply counterpart.
     - The TPS25751 table cites cSrcBulkShared with no condition, because the usual design is one 5 V rail feeding several ports. Its own hard floor is the footnote: at least 10 µF directly at PP5V (C407 here).
     - Each Monolith port's PP5V comes from its own TPS62933 and feeds only that port's VBUS and VCONN, so cSrcBulk ≥ 10 µF applies. P3 has about 33 µF effective.
     - Still to measure at bring-up: the PP5V 0.5 → 3 A load step with C443 removed (estimated about 190 mV against a 250 mV budget).
     - Caveats: the PD spec table was read through Microchip's quote, not the spec itself. TI's EVM (single port) fits 220 µF on PP5V anyway, which is conservative rather than required. If Fast Role Swap is ever enabled, revisit this, because FRS relies on the bulk capacitance to hold VBUS.
4. **Keep both 5V_IN caps.** With one, ripple doubles to about 180 mV and that cap carries about 1.4 A, more than half its assumed rating, against TI's 10 µF typical.
5. **Not covered here:** the charger inductor L401/L501 has a 132 mm² courtyard, more than any capacitor bank. The BQ25756 tops out at about 600 kHz, so a smaller inductor would trade against higher ripple current and peak current. It would need its own study.

**Potential saving:** P3 + B2 come to about 53 mm² per port, about 1 cm² for the board. Adding U4 makes it about 1.4 cm².

## Assumptions to check at bring-up

- **DC bias:** curve fits to the few points in the earlier reviews. The real curves come from the vendors' tools (Taiyo Yuden, Samsung).
- **MLCC ripple ratings:** assumed. Check the parts' temperature at the worst-case points above.
- **Cable and pack paths:** estimates. Lower inductance or resistance changes the damping figures. The low-resistance cases are already included.
- **The ripple model:** ideal CCM, with no buck-boost transition region, light-load modes or dead time. The load step is TI's estimate, not a loop model; measure the PP5V step with and without C443.
