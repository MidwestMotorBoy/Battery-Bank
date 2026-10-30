# Archive

Notes that no longer describe the design, kept so the history of each decision can still be read. Nothing here is current: [`docs/spec.md`](../spec.md) is the single source of truth. Earlier versions of files that were rewritten in place (for example the FEB-era charge and thermal policy) are in the git history instead.

| File | What it was | Retired | Replaced by |
| --- | --- | --- | --- |
| [`eve-58e-datasheet-notes.md`](eve-58e-datasheet-notes.md) | Notes on the EVE INR21700-58E, the first cell (82 Wh pack) | 2026-10-21 | FEB 21700G, then the BAK N21700CX-65E (spec, Cells and pack) |
| [`feb-21700g-datasheet-notes.md`](feb-21700g-datasheet-notes.md) | Notes on the FEB 21700G (93.6 Wh pack) and its temperature table | 2026-10-23 | BAK N21700CX-65E (spec, Cells and pack). Firmware keeps this table's charge ramp until BAK sends its own |
| [`side-tray-mechanical.md`](side-tray-mechanical.md) | The side tray with its aluminium cover, the top-cap tube before it, and the scripts that render them | 2026-10-21 | The cup ([`docs/mechanical-design.md`](../mechanical-design.md)) |
| [`pack-tail-options.html`](pack-tail-options.html) | To-scale comparison of three PACK tail options (plain nickel, bimetal copper, wire), drawn before the decision: it still marks option A as recommended and shows a 20 AWG power wire | 2026-10-24 | Option C, 18 AWG wire tails (spec, Decisions; [`docs/production/p0-assembly.md`](../production/p0-assembly.md)). Moved here from `docs/production/` on 2026-10-29 |
| [`project-status-2026-10-17/`](project-status-2026-10-17/) | HTML status deck from 2026-10-17: EVE 58E cells, 82 Wh, printed tube, STM32WB → CC2340 | 2026-10-24 | The repo README and the spec |

Already removed before this archive existed: `docs/project/monolith-next-actions.md` (retired 2026-10-23 for the spec; see the spec's Contradictions table).
