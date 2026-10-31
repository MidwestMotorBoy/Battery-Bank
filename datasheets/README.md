# Datasheets

Datasheets and application notes for the parts chosen for Monolith: the P0 production board (`hardware/Production/`, the live board), the dev board (`hardware/DevBoard/`, designed but skipped on 2026-10-18), and parts that have since been replaced. Most were downloaded on 2026-10-11 and 2026-10-14. `sources.csv` lists every file with its source link. These documents are the manufacturers' copyrighted material, included here for reference.

To re-download or refresh them, run from the repo root on a computer with normal internet access:

```
bash tools/fetch_datasheets.sh
```

The script saves each PDF here under the file name in `sources.csv` and skips files already present. At the end it lists any it couldn't fetch, so you can grab those by hand: some sites serve a web page instead of the PDF, and rows whose url isn't a link were added by hand. It also lists any PDF here that `sources.csv` is missing. Three files need hand work if they are ever deleted:

- `bak-n21700cx-65e.pdf` came from Convoy's store, which the script can't reach.
- `aps0730.pdf`: the url is the JLC part page, not the PDF.
- `siz240dt.pdf` is Vishay doc 77182 with the PowerPAIR 3x3S land pattern (doc 78115) appended. The script fetches only 77182.

## Index

Use: **P0** = on the production board schematic, **Dev** = on the dev board schematic only, **History** = on neither schematic (kept because reviews, notes or scripts cite it). Reference designators are P0's unless marked; port 2 of the USB sheet repeats port 1 as 5xx.

### Gauge, protection and cells

| File | Part | Use | Where |
|---|---|---|---|
| `bak-n21700cx-65e.pdf` | BAK N21700CX-65E cell spec (A/00) | P0 | Pack cells (4S1P), adopted 2026-10-23 |
| `bq40z50-r2.pdf` | TI BQ40Z50-R2 | P0, Dev | U101 gauge / protection |
| `bq40z50-r2-trm-sluubk0.pdf` | TI SLUUBK0 (BQ40Z50-R2 TRM) | P0 | U101 data flash and commands |
| `slua660-bq40z50-circuit-design.pdf` | TI SLUA660 | P0 | U101 circuit design and layout |
| `bq2947.pdf` | TI BQ2947 / BQ294700 | P0, Dev | U102 second-level overvoltage protector |
| `tlc-wsfb1514.pdf` | TLC WSFB1514 | P0, Dev | F102 self-control fuse |
| `ao3400a.pdf` | AOS AO3400A | P0, Dev | Q103/Q104 (fuse ignition), Q409/Q509; more on the dev board |
| `bzt52c15.pdf` | BZT52C series | P0, Dev | D103 15 V gate clamp |
| `ncp18xh103f03rb.pdf` | Murata NCP series NTCs | P0, Dev | P0 TH101/TH104/TH401/TH501 are NCP15XH103F03RC (0402), covered by this catalog; dev TH401 is NCP18XH103F03RB |
| `agm404ap1.pdf` | AGM Semi AGM404AP1 | Dev | Dev Q101/Q102 protection FETs. P0 fits BSC007N04LS6 on the same symbol (datasheet not held) |
| `pa2512-1mohm.pdf` | Yageo PA2512 1 mOhm | Dev | Dev RS101 gauge shunt (P0: Ralec LR1206, not held) |
| `bh-21700-b1bj001.pdf` | MYOUNG BH-21700-B1BJ001 | Dev | Dev BT101-BT104 cell holders; `hardware/DevBoard/tools/make_3d_holder.py` |
| `eve-inr21700-58e.pdf` | EVE INR21700-58E | History | Cell before the FEB 21700G and BAK 65E (notes in `docs/archive/`); cell outline in `make_3d_holder.py` |

### USB-C ports and charger

| File | Part | Use | Where |
|---|---|---|---|
| `tps25751.pdf` | TI TPS25751 | P0, Dev | U401/U501 USB PD controller |
| `tps25751-trm-slvucr8.pdf` | TI SLVUCR8 (TPS25751 TRM) | P0 | PD host interface, 4CC commands |
| `slvafl1-eeprom-update.pdf` | TI SLVAFL1 | P0 | TPS25751 EEPROM update over I2C |
| `slvafv8-ec-patch-load.pdf` | TI SLVAFV8 | P0 | TPS25751 patch load from a host |
| `tps25751evm-slvucp9.pdf` | TI SLVUCP9 (TPS25751 EVM) | P0 | Reference schematic |
| `m24512.pdf` | ST M24512-DF | P0, Dev | U402/U502 PD controller EEPROM |
| `bq25756.pdf` | TI BQ25756 | P0, Dev | U403/U503 buck-boost charger |
| `bq25756evm-sluuct7.pdf` | TI SLUUCT7 (BQ25756 EVM) | P0 | Reference schematic |
| `siz240dt.pdf` | Vishay SiZ240DT + PowerPAIR 3x3S land pattern | P0 | Q401/Q402/Q501/Q502 charger half-bridges |
| `aps0730.pdf` | Coilank APS-F series | P0, Dev | APS0530M3R3H: L402/L502 5 V buck inductor. APS0730M2R2F: L401/L501 land pattern and A/B alternate (fitted: Coilcraft XGL7030-332MEC, not held) |
| `tps62933.pdf` | TI TPS62933 | P0, Dev | U404/U504 5 V PP5V buck |
| `tpd6s300.pdf` | TI TPD6S300 | P0 | U405/U505 CC/SBU port protector |
| `tvs2200.pdf` | TI TVS2200 | P0, Dev | D401/D501 VBUS flat-clamp TVS (reference part; P0 fits the Maxinmicro clone below) |
| `maxinmicro-tvs2200drvr.pdf` | Wuxi Maxinmicro TVSXX00DRVR family (V1.0, Chinese/English) | P0 | D401/D501 as fitted since 2026-10-31 (LCSC C55616459), pin-compatible with the TI part |
| `lrb520s-40t1g.pdf` | LRC LRB520S-40T1G | P0, Dev | D404/D405/D410/D411 (and 5xx) |
| `usb-c-16pcb1.6-ip68.pdf` | Shou Han TYPE-C 16PCB1.6 IP68 | P0, Dev | J401/J501 USB-C (1.6 mm board) |
| `gmk325bj226mm.pdf` | Taiyo Yuden GMK325BJ226MM-P | P0, Dev | 22 uF 35 V 1210 caps (C208-C213, C420 and others) |
| `cl31-4u7-50v-c406.pdf` | CCTC 1206B475K500NT (general MLCC series spec) | P0, Dev | C406/C506 charger input cap. The file name says CL31, but the sheet is CCTC's |
| `pa2010-5mohm.pdf` | Yageo PA series (0100-2010) | P0, Dev | P0 R424/R524 PA0805FRE470R005L; dev R424/R427 PA2010 sense resistors |
| `tpd4s201-q1.pdf` | TI TPD4S201-Q1 | Dev | Dev U405/U505 port protector (RGR package) |
| `smaj22a.pdf` | Littelfuse SMAJ series | Dev | Dev D105 SMAJ18A. SMAJ22A on D401/D501 was replaced by the TVS2200 (rev A8) |
| `bat54ws.pdf` | BAT54WS | Dev | Dev D101/D406-D409. P0 D101 is a Nexperia BAT54L (not held) |
| `ao3401a.pdf` | AOS AO3401A | Dev | Dev Q403/Q404 liquid-detect pull-ups |
| `usb-c-16pcb0.8-ip68.pdf` | Shou Han TYPE-C 16PCB0.8 IP68 | History | Connector for the old 0.8 mm board; its drawing is the source of `hardware/DevBoard/tools/make_3d_usbc.py` and the drawing_extract outlines |
| `tpd4s201.pdf` | TI TPD4S201 (RUK, non-Q1) | History | Non-Q1 variant; dev review 4 (B-challenge) compares it with the -Q1, which the dev board fitted |
| `tpd2s300.pdf` | TI TPD2S300 | History | Port protector before the TPD4S201 (2026-10-14) |
| `esd2can24.pdf` | TI ESD2CAN24-Q1 | History | CC ESD D402/D502, removed 2026-10-14 |
| `iauc45n04s6l063h.pdf` | Infineon IAUC45N04S6L063H | History | Charger half-bridge before the PGQ04N070 (2026-10-14) |
| `xal7030.pdf` | Coilcraft XAL7030 | History | Charger inductor before 2026-10-14 |
| `tmk325abj476mm.pdf` | Taiyo Yuden TMK325ABJ476MM-P | History | 47 uF 25 V battery-side caps, replaced by 22 uF CL31A226 in the 2026-10-14 cost-down |
| `yageo-rt-0805.pdf` | Yageo RT0805 thin film | History | 0.1 % resistors (dev review 4 R433/R533); on neither schematic now (P0 uses Panasonic ERA2AEB, not held) |

### Power rails, MCU and misc

| File | Part | Use | Where |
|---|---|---|---|
| `tps62177.pdf` | TI TPS62177 | P0, Dev | U204 3.3 V always-on buck |
| `cc2340r5moda.pdf` | TI CC2340R5MODA | P0, Dev | U301 BLE module |
| `rh-s2761-46r-testloop.pdf` | RH-S2761-46R test loop | P0, Dev | GND and switch-node test loops (TP109, TP405, TP406, TP412) |
| `ina190.pdf` | TI INA190 | Dev | Dev U201/U202 sleep-current amplifiers |
| `ss34.pdf` | SS34 | Dev | Dev D104 |
| `1n4148ws.pdf` | 1N4148WS | Dev | Dev D102 |
| `ts-1187a-switch.pdf` | XKB TS-1187A | Dev | Dev SW101/SW301 tactile switches |
| `tps709.pdf` | TI TPS709 | History | Dev amplifier LDO before the HT7550 (2026-10-14) |
| `srp5030t.pdf` | Bourns SRP5030T | History | 5 V buck inductor before the APS0530 (2026-10-14) |
| `srn4018ta.pdf` | Bourns SRN4018TA | History | 3.3 V buck inductor before the FNR4030 (2026-10-14) |
| `tmp1075.pdf` | TI TMP1075 | History | Dev rev A7 board temperature sensors, removed in rev A8 |
| `stm32wb1mmc.pdf` | ST STM32WB1MMC | History | BLE module before the CC2340R5MODA (rev A7) |
| `stm32wb15cc.pdf` | ST STM32WB15CC | History | The MCU inside the STM32WB1MMC |
| `bss138.pdf` | BSS138 | History | Dev Q103 level shift, replaced by the AO3400A in the 2026-10-14 cost-down |

### P0 parts with no datasheet here

BSC007N04LS6 (Q101/Q102, LCSC C534274), Coilcraft XGL7030-332MEC (L401/L501), Changjiang FNR4030S100MT (L201), TI TPS7A4101 (U406/U506, SBVS183B), Nexperia BAT54L (D101), Ralec LR1206-21R001F4 (RS101), MA120610FR005MZ (R427/R527), CCTC CA55-D035M476T (C421/C456), Panasonic ERA2AEB (R418/R419). Superseded parts with no datasheet here: JinYu PGQ04N070 and SXN SMMS1040 (dev charger stage), Holtek HT7550-1 (dev), and the FEB 21700G cell (see `docs/archive/feb-21700g-datasheet-notes.md`).

## History

- 2026-10-11: first set, for the dev board.
- 2026-10-14 (schematic review 3): the second-level protection and liquid-detection parts (BQ2947, WSFB1514, TPD2S300), the BQ40Z50-R2 technical reference manual and SLUA660, the BQ25756 and TPS25751 EVM guides (reference schematics), and the discretes (FETs, diodes, NTC, switch, test loop, C406). ST AN5290 and AN5165 (st.com refuses scripted downloads) and the Everlight 19-217 LED datasheet were never fetched. Both became moot when the STM32WB and that LED were replaced.
- 2026-10-14 to 10-18: TPD4S201 / -Q1, 1.6 mm USB-C, CC2340R5MODA, TMP1075, TVS2200, then the P0 parts APS0730, SiZ240DT and TPD6S300.
- 2026-10-23: the BAK N21700CX-65E product specification (A/00, 2025-04-10), the pack cell adopted on 10-23. It was added by hand from Convoy's store.
