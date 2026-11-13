# Reviews

Design reviews of the P0 board and its enclosure, newest first. Each folder has a README with the findings, a fix checklist and the figures. Every board review here is of the **hand-routed board** (the board file at commit `8dd9eb6`). The ground-up re-layout that has been on `master` since 2026-11-10 (PR #66) has been checked by script and solver only (`hardware/Production/groundup/`) and has no review here.

- [`2026-11-03-rail-retention/`](2026-11-03-rail-retention/README.md): rail block retention. Five options for the tongue joint that would snap in a drop; the cup now carries the drop loads (edge lands, F.Cu lips, front-can cradles, PA12 post spacers).
- [`2026-10-31-mouth-band/`](2026-10-31-mouth-band/README.md): cup mouth, cap collar against a thicker mouth band. The 2.4 mm mouth band was adopted.
- [`2026-10-30-routed-board/`](2026-10-30-routed-board/README.md): the routed board. DRC, copper resistance of every power path, current-sense taps, thermal impact of the routed copper. Also summarises the earlier placement and first routed reviews.

## Review history

Most board reviews after the first routed review were written as private pages for Logan and are not in the repo. This table records what each one covered and what came of it, from the project notes and the commit history. Times are UTC on the day given.

| Date | What was reviewed | Outcome | In the repo |
|---|---|---|---|
| 2026-11-10 | Ground-up re-layout against the hand-routed board (hot loops, gate loops, coupling, copper loss, Kelvin taps, thermal) | Script and solver comparison only, no human review; Logan kept the board on `master` (PR #66). A cleanup pass after his critiques waits in open PR #68 | `hardware/Production/groundup/compare/README.md` |
| 2026-11-07 | Whole project before ordering (bring-up traps, retention, gauge and charger configuration, consistency) | No wiring error. Logan's answers: R413/R513 stay 11.8k, keep BQ294700 with COV 4.25 V, UART_TX to J301 pin 6, silk labels at the wire holes, no coupons (PR #64). Open at checkout: the D401/D501 pin-1 check in JLC's preview. The dev-board configuration checklist conflicts with P0 | `hardware/Production/jlc/ORDER-NOTES.md`, `docs/spec.md` |
| 2026-11-06 | Switch-node, hot-loop and gate-loop inductance of the routed board (Logan's 2026-11-04 save) | No must-fix; optional fixes listed | `docs/analysis/2026-11-06-loop-area/` |
| 2026-11-03 | Rail block retention (five options) | Options 2 and 5 built (PR #61) | [`2026-11-03-rail-retention/`](2026-11-03-rail-retention/README.md) |
| 2026-10-31 | Cup mouth collar against a mouth band | 2.4 mm mouth band adopted | [`2026-10-31-mouth-band/`](2026-10-31-mouth-band/README.md) |
| 2026-10-30, 22:01 | Final review of the 21:58 save, blockers only | ERC 0 errors, netlist matches the board pad for pad, DRC 0 errors. One blocker: L502 at the cup's corner fillet, fixed by a 2.0 mm inductor on L402/L502. Approved by Logan (PR #44) | `hardware/Production/README.md` (*Routed and approved*, *Part swaps after approval*) |
| 2026-10-30, 18:08 to 21:58 | Rev 7 detailed review (Kelvin and I2C coupling, per-port 100 W thermal, power stage, gauge, RF), then rev 8 to rev 12 | Port 2 sense read 1.08x at rev 7 and +7.2 % on SRP at rev 8; closed at rev 9 to rev 12 (all sense taps within 0.7 %, DRC 0 errors). U301 antenna keep-out extended to every layer. BQ40Z50 FET Options 0x24 went into `docs/production/p0-bringup-and-training.md` (PR #43). Left open: C118 to GND (offered, not answered), CELL1 via 0.37 mm from J302's hole | |
| 2026-10-30, 14:29 to 17:04 | Rev 3, rev 4 and rev 5 of the routed board | Port 1 PACK_P path, port 2 ACN tap, VPWR capacitors, F102 heater return (195 to 2.7 mΩ) and the BAT_SNS_P overlap fixed; J1–J4 renamed J117–J120; JLC hole-to-hole rules set (186 warnings to 4) | |
| 2026-10-30, 04:02 | First routed board review (rev 2) | Fix list closed in the later revisions above | [`2026-10-30-routed-board/`](2026-10-30-routed-board/README.md) |
