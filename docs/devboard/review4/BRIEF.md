# Schematic review 4: team brief (rev A7, 2026-10-14)

Four reviewers (A, B, C, D) do a deep review of the MonolithDev dev-board schematic at **rev A7**. Then they challenge each other's findings. The lead (the session that started you) verifies the criticals and writes `../schematic-review-4-2026-10-14.md`.

## The project

- **The product:** Monolith, a 100 W USB-C battery bank. It has 4 × EVE INR21700-58E cells in series (4S1P, up to 16.8 V), two USB-C PD ports, and BLE.
- **The dev board** is a bench version of the electronics. KiCad 10 project in `DevBoard/`. The sheets are:
    - `MonolithDev.kicad_sch`: top sheet and revision log.
    - `gauge.kicad_sch`: Cells and Gauge.
    - `power.kicad_sch`: Sleep Current and 3V3.
    - `mcu.kicad_sch`: MCU and sensors.
    - `usb_port.kicad_sch`: USB Port, instantiated twice; port 1 refs are 4xx and port 2 refs are 5xx.
- **Start here:**
    - `DevBoard/README.md`: the change log, items 1–40. Rev A7 is item 40. Items 37–39 are the cost-down, the discrete charger FETs, and the 6-layer board with the TPD4S201.
    - `docs/devboard/circuit-description.md`: the design intent.
    - `docs/devboard/cc2340-pin-budget.md`: the rev A7 MCU pin plan.
    - `docs/devboard/power-budget.md`, `mcu-io-power-states.md`, `bringup-config-checklist.md`, `rev2-changes.md`, `cost-down-2026-10-14.md`.
- **Previous reviews:**
    - `docs/devboard/schematic-review-2026-10-12.md`, `schematic-review-2-2026-10-12.md`, `schematic-review-3-2026-10-14.md`.
    - Review 2's per-reviewer files are in `docs/devboard/review2/`. They show the format and depth we expect.
    - Items closed there stay closed. Re-raise one only with new evidence, and say that you are doing so.
- **What changed since review 3** (review 3 covered rev A6 up to liquid detection): items 37, 38, 39 and 40 in `DevBoard/README.md`. These have **never been reviewed**, so they get the deepest look. Everything else gets a fresh-eyes pass.

## Inputs in this folder

- `net.xml`: the KiCad netlist, exported from the current schematic.
- `parts.txt`: one line per part (ref, value, DNP, footprint, sheet, MPN, LCSC, Notes property).
- `nets.txt`: one line per net, listing every `ref.pin(pinfunction)` on it.
- `erc.txt`: the current ERC. It has 8 warnings, all known: TPS25751 unused GPIOs tied to GND.
- `DevBoard/MonolithDev_schematic.pdf`: a plot of every sheet. It may be slightly behind the .kicad_sch files; the netlist is the truth.
- `datasheets/`: every datasheet and app note we hold, indexed in `datasheets/sources.csv`.

## Tools on this machine (Windows)

- **Python:** KiCad's python is `"C:/Program Files/KiCad/10.0/bin/python.exe"`. It has pcbnew, PIL, numpy and pymupdf. There is no system python.
- **PDFs:**
    - Text: `import pymupdf; d = pymupdf.open(path); d[i].get_text()`.
    - Figures: render pages to PNG at about 110–150 dpi with `page.get_pixmap(dpi=...)` and look at them with the Read tool. Do this for any figure or table you cite.
- **kicad-cli:** `"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"`.
- **Your own files:**
    - Write scripts and scratch files under your own scratch folder, `docs/devboard/review4/scratch-<letter>/`. Do not write them anywhere else in the repo.
    - Never name a script after a stdlib module (`random.py`, `bisect.py` …).
    - Any script containing a backslash goes through the Write tool, not a bash heredoc.
- **Web:** you may fetch a datasheet we don't hold (manufacturer or distributor site only). Save it in your scratch folder and note the URL.

## Rules

- **Read-only on the design.** Do not edit any `.kicad_sch`, `.kicad_pcb`, `.kicad_sym`, footprint, script or doc outside `docs/devboard/review4/`. Do not commit. You propose fixes; you don't make them.
- **Every claim needs a source:** a datasheet section, table, figure or page; a netlist line; or worked arithmetic.
- **Say how sure you are:** "verified" (you read the page or ran the numbers) or "inferred".
- **No contested premise as fact.** If you rely on something another reviewer owns, ask them (see "Talking to each other").

## Methods

Use the methods ranked in our review practice, adapted to your scope:

1. **Pin-by-pin datasheet pass** for every IC in scope. For every pin: is it connected, at the correct level, inside abs-max, and are unused pins handled per the datasheet? Re-check the symbol's pinout against the datasheet *and* the footprint pad numbering, even for "known" parts.
2. **Net-by-net trace** from `nets.txt`. Look for:
    - single-pin nets;
    - nets with no source or two drivers;
    - nets crossing voltage domains;
    - open-drain nets without a pull-up, or with a pull-up to the wrong rail;
    - pull-ups that back-power an unpowered part.
3. **ERC triage:** confirm the 8 known warnings are still the only ones and still benign.
4. **Power tree:** for every rail, check:
    - its source and load budget;
    - UVLO, sequencing and inrush;
    - input/output caps per the regulator datasheet, with MLCC DC-bias derating.
5. **Worst case and derating:**
    - stress ratio = applied / rated; aim for about 50 % on voltage for MLCCs and FETs;
    - include tolerance, temperature, hot-plug and inductive transients;
    - check FET Vgs against what the driver actually applies.
6. **State analysis:**
    - power-up, reset, brown-out, ship mode, power-off and back-powering;
    - every strap pin's sampled value;
    - what every MCU-driven net does while the MCU is in reset or unprogrammed. CC2340 pins are hi-Z in reset.
7. **Fault injection on paper:**
    - short each output;
    - reverse or overvoltage each input;
    - unplug each connector mid-operation;
    - insert cells in any order.
8. **Interface check** at every connector and voltage-domain boundary: levels, ESD, pull states when unplugged, connector pinout.
9. **BOM pass:**
    - every part has an MPN and LCSC number, with correct voltage, power, tolerance and dielectric ratings;
    - the package matches the footprint;
    - check DNP intent;
    - check the `Notes` property is still true (stale notes count as findings).
10. **Testability and bring-up:** test points per rail, isolation jumpers, DNP options and the programming header.
11. **Firmware-facing check:** pin map, I2C addresses, interrupt and wake sources, configuration items the hardware depends on.

## Severity

- **CRITICAL:** the board will not work, will damage itself or the cells, or is unsafe as drawn.
- **MAJOR:** works only by luck, violates a datasheet requirement or abs-max under a credible condition, or needs a rework wire.
- **MINOR:** a hardware improvement or a marginal design value.
- **CONFIG:** a firmware, EEPROM, data-flash or procedure item the hardware depends on.
- **DOC:** a wrong or stale note, symbol text, README line or Notes property.
- **NOTE:** checked and correct, worth recording.

## Output (round 1)

Write `docs/devboard/review4/<letter>-findings.md`, in the format of `docs/devboard/review2/A-findings.md`:

- **Header:** your scope, your sources, and a summary count.
- **Then one block per finding:**
    - `### A-1 [SEVERITY] one-line claim`
    - **Where:** refs, nets and pins.
    - **Evidence:** with sources.
    - **Proposed fix.**
    - **Confidence.**
- **At the end:** a "Checked and correct" list of what you verified, so the lead can see coverage.

## Talking to each other

- **Live questions:** the lead will give you your peers' session ids. While you work, message a peer with `SendMessage` when your finding depends on their area. Examples:
    - "does the BQ25756 ever drive VBAT above 17 V?"
    - "what pull-up does IRQ_N have on the gauge side?"
- **Answering:** keep questions short, answer peers' questions promptly, and record any answer you rely on in your findings.
- **Round 2 (challenge):** after round 1 the lead will ask you to read the others' findings files. Attack every CRITICAL and MAJOR claim, and any MINOR you think is wrong, by independent re-derivation from the datasheet, not by restating it. Write `<letter>-challenge.md`, with each item marked AGREE, AMEND or DISPUTE plus your evidence.
- **Round 3 (defend):** the lead will ask you to answer the challenges against your own findings (concede, amend or defend). Append the result to your findings file under "After round 2".
