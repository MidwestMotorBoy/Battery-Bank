# Retired mechanical outputs

Generated files for the two enclosures the cup replaced, moved here on 2026-10-24 so `hardware/mechanical/` shows only the current design. None of it is to be built.

- **Top-cap tube** (to 2026-10-18): `monolith_shell.stl`, `monolith_top_cap.stl`, `monolith_end_bumper.stl`, `monolith_fit_ring.stl`, the dummies (`monolith_cell_dummy.stl`, `monolith_top_board_dummy.stl`, `monolith_bottom_pcb_dummy.stl`) and the bottom board outline `monolith_bottom_pcb.dxf`.
- **Side tray with the aluminium cover** (2026-10-18 to 2026-10-21): every `monolith_side_*` file except `monolith_side_pcb.dxf`, which is still the board outline and stays in `hardware/mechanical/`. That includes the cover's STEP, DXF and marking files, the renders, and the FDM home-print kit in `print_kit/`.
- `monolith_layout_compare.png`: the tube against the tray.

The scripts that make these stay in `hardware/mechanical/`, because `monolith_cup.py` and `hardware/Production/tools/make_board.py` import them. Re-running them writes here (`monolith_shell.RETIRED`). The design notes for these layouts are in [`docs/archive/side-tray-mechanical.md`](../../../docs/archive/side-tray-mechanical.md); the current enclosure is in [`docs/mechanical-design.md`](../../../docs/mechanical-design.md).
