# Loss reduction — shared brief

The Monolith is a 4S1P, 82 Wh USB-C PD power bank (4 × EVE INR21700-58E) with two ports. Each port has a TI BQ25756 4-switch buck-boost charger and a TPS25751 PD controller; a BQ40Z50 gauge runs the pack protection. The owner wants to **cut the electrical losses** before any more thermal or mechanical modelling. You are one of five researchers, each owning one area. **Research and recommend only: do not edit any schematic, board, script or doc in the repo.** Write only your own output file.

## Where things are
- Repo: `C:\Users\Logan\Documents\BatteryBank` (branch `Production`). The local checkout is **behind** `origin/Production`; read the newest design files with `git show d994c3a:<path>`, for example:
  - `git show d994c3a:hardware/Production/README.md` (production design log: parts, trade-offs, the board)
  - `git show d994c3a:hardware/Production/power.kicad_sch`, `usb_port.kicad_sch`, `gauge.kicad_sch` (schematics, text)
  - `git show d994c3a:docs/devboard/circuit-description.md`, `docs/devboard/schematic-review-4-2026-10-14.md`, `docs/devboard/review4/*.md`, `docs/devboard/review2/*.md` (loss and FET reviews)
- Datasheets: `datasheets/` (bq25756.pdf, siz240dt.pdf, aps0730.pdf, agm404ap1.pdf, tps25751.pdf, bq40z50-r2.pdf, eve-inr21700-58e.pdf, pa2010-5mohm.pdf, …). `pdftotext -layout` is installed (Git Bash).
- The current loss model: `research_notes/Ground-up mechanical concepts/model/heat_sources.py`. Read it; to test a change, **copy it to your scratch area** and edit the copy. Run it with the Python at `C:\Users\Logan\AppData\Local\Temp\claude\C--Users-Logan-Documents-BatteryBank\5a6957a1-6049-4783-85aa-a109da28ab92\scratchpad\venv\Scripts\python.exe` (`heat_sources.py nochart` prints the table).
- Parts sourcing: the board is assembled by **JLCPCB**, so LCSC part numbers, stock and price matter (a part JLC doesn't stock must be hand-supplied: say so). You may have JLC search tools (`mcp__kicad__search_jlcpcb_parts`, `mcp__kicad__get_jlcpcb_part`; load them with ToolSearch) and web search. Cite datasheet pages/figures for every resistance, charge or rating you use.

## Current losses (estimates, `heat_sources.py`, nominal 14.4 V pack)
| Source (W) | 30 W out | 100 W out | 100 W, 12 V pack | 88 W charging |
|---|---|---|---|---|
| Cells (4 × ~22 mΩ) | 0.43 | 5.26 | 8.3 | 2.81 |
| Pack path: protection FETs Q101/Q102 (AGM404AP1, 2 × ~5.7 mΩ warm), fuse F101 ~5 mΩ, nickel ~5 mΩ, shunt 1 mΩ, copper | 0.12 | 1.46 | 2.3 | 0.78 |
| Charger FETs, conduction (SiZ240DT, ~13 mΩ at 4.5 V gate) | 0.29 | 1.55 | 2.5 | 0.83 |
| Charger FETs, switching + dead time (600 kHz) | 0.33 | 0.87 | 1.1 | 0.66 |
| Inductor APS0730M2R2F (~12 mΩ DCR + core) | 0.28 | 0.92 | 1.3 | 0.58 |
| Sense resistors RBAT + RAC (5 mΩ each) | 0.08 | 0.42 | 0.6 | 0.26 |
| USB side: TPS25751 PPHV switch ~18 mΩ + USB-C contacts | 0.31 | 0.70 | 0.7 | 0.54 |
| Gate drive, ICs, MCU/BLE | 0.15 | 0.15 | 0.15 | 0.15 |
| **Total** | **2.0** | **11.3** | **17.0** | **6.6** |

## Hard constraints
- **Height:** parts on the board's outer face may be at most **3.2 mm** tall (today's tallest is the 3.1 mm inductor). Every extra mm makes the whole pack thicker; if you propose a taller part, say how much thicker the pack gets and whether it's worth it.
- **Area:** the board is 43.2 × 74.35 mm, double-sided, already crowded. Say whether a change fits the existing footprint or needs more area.
- **Voltages:** USB side up to 20 V (22.5 V OVP, 28 V TVS clamp); pack 10–16.8 V. Keep ≥ 40 V-class FETs on the charger.
- **Gate drive:** BQ25756 drives the charger FETs from REGN (~5 V) unless DRV_SUP is fed separately; BQ40Z50 drives Q101/Q102 with its charge pump. Check the datasheets for what is really available.
- Cost matters (hobby, JLC assembly), weight matters (ultralight), and safety (short-circuit, SOA, inrush) must not get worse.

## What to deliver
Write your findings to your output file (markdown, ~1000–1600 words):
1. **The current part(s)** in your area and what the losses really are (check the model's numbers; correct them if they're wrong).
2. **Candidates:** a table of real parts (MPN, LCSC number, JLC stock/price if you can find it, key specs with datasheet citations, package/footprint fit, height).
3. **Recommendation:** what to change, the loss saved at 30 W / 100 W / 100 W at 12 V / 88 W charging (run the model copy), cost, area and weight changes, and the risks (SOA, ringing, EMI, availability, accuracy, firmware/config changes).
4. **Interactions** with other areas (e.g. a lower switching frequency needs a bigger inductor; a lower-RDS FET has more gate charge).
5. **What you'd measure on the dev board** to confirm it.

Return to me (final message) a ~200-word summary: recommended change(s), watts saved at 100 W and at 30 W, cost/area/height impact, and the main risk.
