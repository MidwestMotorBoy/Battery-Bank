# Thermal comparison inputs

Pack thermal model (`pack3d.py`, `smd.py`, `ntc.py`, `cu.py`, copied from the 2026-11-05 inner-copper study) with a
runner that takes each board's heat-source positions, routed-copper loss tiles and copper cover.

- `cu_base.json`, `cu_new.json`: per-port copper resistance and 2 mm loss tiles from the DC grid solver
  (`../lossmap.py`) for master's board and the ground-up board.
- `run_cmp.py <boards> <cases> [hours]`: boards `base`, `new`, `new_k38` (ground-up without credit for its extra
  copper cover). Results go to `results/<board>/<case>_cmp.npz`.
- `analyze_cmp.py`: prints one `RESULT {json}` line per run and writes `results/summary.json`.

Needs numpy, scipy and pyamg (the venv of the thermal model on the PC has them).
