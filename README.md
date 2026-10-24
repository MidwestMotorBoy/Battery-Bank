# Monolith

An ultralight 93.6 Wh USB-C power bank for backpacking: 4S1P 21700 pack, two bidirectional USB-C PD ports designed for 100 W total, TI CC2340 Bluetooth LE MCU.

<p align="center"><img src="hardware/mechanical/monolith_cup_exploded.png" alt="The Monolith cup: assembled and exploded views with the parts list" width="100%"></p>

## Design overview

The goal is a hiking power bank that is lighter and better behaved than the off-the-shelf ones: under the 100 Wh carry-on limit, able to charge or run 20 V USB-C PD loads, with a proper fuel gauge and a phone app. The pack is four FEB 21700G cells (6.5 Ah, 3.6 V nominal) in 4S1P: 14.4 V, 93.6 Wh nominal, spot-welded with nickel strip and managed by a TI BQ40Z50-R2 gauge/protector with hardware second-level protection (BQ294700 plus a chemical fuse). Each of the two USB-C ports has its own TPS25751 PD controller and BQ25756 bidirectional buck-boost converter, so either port can charge the pack (including from a 5 V solar panel) or source up to 20 V / 5 A, with the pair thermally limited to 100 W; a TPS62933 buck supplies each port's 5 V source rail and a TPS62177 buck supplies the 3.3 V rail. A CC2340R5MODA Bluetooth LE module runs the charge policy, port power sharing and a custom GATT service for an iPhone app. The electronics live on one 43 × 74 mm 6-layer board along one face of the cells, inside an MJF nylon cup closed on five sides and sealed by a bottom cap with one radial O-ring, with TPU bumpers at both ends. There is no metal enclosure: the power stage sheds its heat into the cells through thermal vias and a gap filler.

| | |
|---|---|
| **Energy** | 93.6 Wh nominal (4S1P, 14.4 V, 6.5 Ah, FEB 21700G cells), under the 100 Wh carry-on limit |
| **Ports** | 2 × USB-C, each bidirectional PD 5–20 V up to 5 A; 100 W total as a burst, then a linear thermal derate to a sustained ~40 W ([policy](docs/firmware/charge-and-thermal-policy.md)) |
| **Gauge / protection** | BQ40Z50-R2 (Impedance Track, SMBus), AGM404AP1 CHG/DSG FETs, 1 mΩ shunt; BQ294700 + chemical fuse as the independent second level |
| **MCU** | TI CC2340R5MODA (Cortex-M0+ Bluetooth LE module with integrated antenna) |
| **Board** | 43.2 × 74.35 mm, 6 layers, 1.6 mm, 2 oz outer copper, ENIG, filled and capped vias; JLCPCB assembly |
| **Enclosure** | MJF PA12 cup and bottom cap (one radial O-ring), PA12 cell carrier, TPU 95A bumpers; 59.8 × 51.9 × 97.2 mm, about 400 g (modelled estimate, board populated) |
| **Tools** | KiCad 10 with Python scripts, TI SimpleLink Low Power F3 SDK, Xcode (app, planned) |

## Status

In progress. Nothing has been built, assembled or bench-tested yet; every number above is a design value, not a measurement.

**Done**

- Schematic: four reviews of the bench "dev board" schematic (rev A8, about 430 parts), then the production P0 schematic derived from it by script (283 parts) with a netlist check that every surviving pin kept its net. Design notes, reviews and simulations are in `docs/devboard/` and `hardware/Production/README.md`.
- Dev board layout: 196 × 115 mm, 6 layers, routed, DRC clean apart from known footprint-library warnings, JLC fab outputs generated (`hardware/DevBoard/fab/`). It was not ordered: the decision on 2026-10-18 was to skip it and build P0 directly.
- Production board: stack-up, outline and USB-C placement locked to the enclosure model (`hardware/Production/tools/make_board.py` imports the outline from `hardware/mechanical/monolith_shell.py`).
- Mechanical: parametric enclosure model with drop, thermal-expansion, vibration and assembly-clearance checks, STL/STEP/DXF outputs and renders (`docs/mechanical-design.md`). On 2026-10-21 a ground-up study (five concepts, cross-examined) replaced the side tray and its aluminium cover with the heatsink-free cup ([report](reports/Ground-up%20mechanical%20design.md), models in `research_notes/Ground-up mechanical concepts/`).
- Firmware: a command-line build for the LP-EM-CC2340R53 LaunchPad that compiles with no warnings (about 10 KB flash).
- Research: potting versus crush-zone drop protection, with sources (`reports/`).
- Thermal and loss models: part-by-part heat sources, burst and derate simulations for the tray, a CNC-lid hybrid and the cup (`research_notes/Ground-up mechanical concepts/model/`), and a five-area loss-reduction study with a cross-examination ([summary](research_notes/Loss%20reduction/summary.md)).
- Cell choice: FEB 21700G 6500 mAh (93.6 Wh) over the EVE 58E and the Tenpower 60XG, for energy at trail loads ([notes](docs/project/feb-21700g-datasheet-notes.md)); hardware charge cap R413/R513 = 11.8 kΩ.
- Charge and thermal policy for firmware: charge current and discharge power as linear ramps on the hottest cell temperature ([policy](docs/firmware/charge-and-thermal-policy.md)).

**Remaining**

- Place and route the production board (layout in progress; the outline is unchanged by the cup); update it from the P0 schematic; DRC.
- Board changes for the FEB cells and the cup: move the five bottom tab slots, the gap-filler zone with thermal vias, split carrier rails, two peg holes, drop the cover standoffs; update `make_board.py --keepouts` for the cup.
- Decide the P0 loss cuts (protection FETs, 9 V gate drive, inductor and 500 kHz, nickel): about −1.6 W at 100 W ([summary](research_notes/Loss%20reduction/summary.md)).
- Order P0 from JLCPCB, weld the pack, train the gauge (`docs/production/p0-bringup-and-training.md`).
- Firmware beyond the skeleton: gauge and PD-controller drivers, charge policy, power sharing, BLE GATT, MCUboot OTA.
- Fit print of the cup, cap and carrier, and an O-ring dunk coupon; drop and 100 W thermal tests; label ratings.
- iPhone app (SwiftUI + CoreBluetooth).

The current design, open decisions and the working checklist are in [`docs/spec.md`](docs/spec.md), the single source of truth for the project.

## Hardware

The KiCad 10 sources are in `hardware/`, with the production board as the design of record and the dev board kept as the reviewed reference it was derived from.

| Project | Path | What it is |
|---|---|---|
| **Production P0** | [`hardware/Production/`](hardware/Production/) | First board to be built. The dev-board schematic with the bench-only parts removed, JLC extended/0201 passives, SiZ240DT half-bridge FETs, low-profile bulk capacitors, Tag-Connect SWD and gauge-training pads. Generated and checked by the scripts in `tools/`. [README](hardware/Production/README.md) has every change with its reasoning. |
| **Dev board** | [`hardware/DevBoard/`](hardware/DevBoard/) | Bench version with cell holders, test points, jumpers and a sleep-current measurement section. Routed and fab-ready, not ordered. [README](hardware/DevBoard/README.md) is the change log (items 1–50) and board rules. |
| **Mechanical** | [`hardware/mechanical/`](hardware/mechanical/) | Python-generated enclosure (the cup: `monolith_cup.py`; the retired side tray is still there) as STL/STEP/DXF, plus the renders. Notes in [`docs/mechanical-design.md`](docs/mechanical-design.md). |

**Schematics (PDF)**

- [`docs/hardware/monolith-p0-schematic.pdf`](docs/hardware/monolith-p0-schematic.pdf): production P0, 6 sheets (root index, cells and gauge, 3V3 rail, MCU, USB port 1, USB port 2).
- [`docs/hardware/monolithdev-schematic.pdf`](docs/hardware/monolithdev-schematic.pdf): dev board rev A8.

**Board plots (dev board, the routed one; P0 is placed only at the connectors so far)**

| Front (F.Cu, mask, silk) | Back (B.Cu, mask, silk, mirrored) |
|---|---|
| [<img src="docs/hardware/monolithdev-board-front.png" alt="Dev board front plot">](docs/hardware/monolithdev-board-front.png) | [<img src="docs/hardware/monolithdev-board-back.png" alt="Dev board back plot">](docs/hardware/monolithdev-board-back.png) |

**Per port**

- TPS25751D USB-C PD controller, configured from its own M24512 EEPROM (patch-bundle programming notes in `docs/project/tps25751-eeprom-programming.md`).
- BQ25756 bidirectional buck-boost at 600 kHz, 2.2 µH inductor, 5 mΩ sense resistors, two SiZ240DT 40 V half-bridges (dev board: four PGQ04N070 singles); gate resistors fitted as 0 Ω links with DNP RC snubbers so ringing can be fixed without a respin.
- TPS62933 5 V buck for the port's 5 V source rail; TPD6S300 CC protection (24 V short-to-VBUS, IEC ESD); TVS2200 flat clamp on VBUS.
- Shou Han IP68 right-angle USB-C receptacle, 5 A / 20 V.

**Pack and supervision**

- BQ40Z50-R2 with four cell NTCs, cell balancing and JEITA; 1 mΩ shunt; BQ294700 per-cell OVP that fires the WSFB1514 chemical fuse independently of the gauge.
- One wire-ORed interrupt line (both PD controllers, gauge BTP) into the MCU; CHG_INH pulled up so a reset, hang or unprogrammed MCU stops charging.
- Idle current budgeted by state in `docs/devboard/power-budget.md` (dev board rev A8 estimate about 230 µA; P0's TPD6S300 CC protectors add about 175 µA on top, per `hardware/Production/README.md`), with a gauge ship mode for storage.

Datasheets and app notes the design was checked against are in `datasheets/` (indexed in `datasheets/sources.csv`).

## Firmware

`firmware/` targets the CC2340R5MODA with TI's SimpleLink Low Power F3 SDK. Until a board exists it runs on the LP-EM-CC2340R53 LaunchPad, which has the same silicon and memory.

- **Toolchain:** TI Arm Clang, SysConfig and `gmake` from Code Composer Studio 21, the LPF3 SDK 9.23, and UniFlash/DSLite with an XDS110 probe. Everything is driven from a `Makefile` in the style of TI's SDK examples; CCS itself is only used for debugging. Install steps and version pins are in [`firmware/README.md`](firmware/README.md).
- **Structure:** `boards/<board>.syscfg` holds the pin map and CCFG per target (LaunchPad now, dev board/P0 next); SysConfig generates the driver configuration and linker includes into `build/<board>/syscfg/`; `app/` is the application. NoRTOS for bring-up, moving to FreeRTOS when the BLE stack comes in.
- **State:** the skeleton builds (banner and reset reason on the XDS110 UART, heartbeat LED, a button standing in for the IRQ line) and has not been run on hardware yet.
- **Planned:** SMBus gauge driver, TPS25751 4CC commands and EEPROM patch loading, the charge and thermal policy in [`docs/firmware/charge-and-thermal-policy.md`](docs/firmware/charge-and-thermal-policy.md), port power sharing, settings in flash, BLE GATT service, MCUboot signed OTA.

## Repo layout

```
.
├── README.md
├── LICENSE
├── hardware/
│   ├── Production/        KiCad 10 project "Monolith" (P0): schematic, board, library, generator scripts
│   ├── DevBoard/          KiCad 10 project "MonolithDev": schematic, routed board, library, fab/, tools/, 3dmodels/
│   └── mechanical/        Enclosure models (Python → STL/STEP/DXF) and renders
├── firmware/              CC2340 firmware: Makefile, boards/*.syscfg, app/, tools.mak.example
├── docs/
│   ├── hardware/          Schematic PDFs and board plots exported from KiCad
│   ├── devboard/          Circuit description, schematic reviews 1–4, power budget, pin budget, bring-up checklist, simulations
│   ├── production/        P0 assembly (the cup) and the bring-up and gauge-training procedure
│   ├── firmware/          Charge and thermal policy
│   ├── project/           Next actions, cell datasheet notes (FEB 21700G, EVE 58E), TPS25751 EEPROM programming
│   ├── mechanical-design.md
│   └── project-status/    HTML status deck
├── datasheets/            Manufacturer datasheets and app notes (sources.csv lists where each came from)
├── reports/               Research reports (potting and drop protection; ground-up mechanical design)
├── research_notes/        Sources and working notes: potting, the ground-up concepts and their models, loss reduction
└── tools/                 fetch_datasheets.sh
```
