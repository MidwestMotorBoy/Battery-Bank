# 1 m drop: contact model, stress in every part (2026-11-04)

The 2026-10-31 study (`../2026-10-31-drop-1m`) treated the bank as two masses with the inside bonded to the cup, so it could
not see the inside parts hitting each other. This one keeps every part that can move as its own body, finds where they
touch on the real master geometry, and runs the impact in 17 orientations from 1 m onto concrete.

Results and the ranked list of weak parts: see `out/checks.json` and the figures in `figs/` (written by the run on the PC).

## Model

* **Bodies** (`bodies.py`): the shell (cup, cap, bumpers, label, screws, O-ring, pad, vent: 64 g), the four cells (each
  with its share of nickel, tails, insulators, foam and gel: about 75 g), the carrier (9.1 g), the four rail blocks
  (0.25-0.32 g each) and the board (22.6 g with spacers and half the gel). Built from `hardware/mechanical/monolith_cup.py`
  on master, with the crush ribs and bore ribs left off (they are meant to give).
* **Gaps** (`gapcheck.py` -> `out/gaps.json`): the first-touch gap of every pair along +-x, +-y, +-z. They match the
  design gaps (cradles 0.15, post tips 0.3, spacers 0.4, lips 0.5, lands 0.12, feet 0.2, OT posts 0.3).
* **Contact law** (`contacts.py`, `tables.py`): force = K_W x the overlap volume of the two solids (manifold3d booleans),
  K_W = E / 2.5 mm = 680 N/mm^3 for PA12. Tables of overlap against travel for every pair and both senses, per pose.
* **Impact** (`dyn.py`): one degree of freedom per body along the drop direction (no rotation), 4.43 m/s at touch-down,
  explicit time steps of 0.05 us. The floor pushes the shell through the bumpers (the 10-31 gyroid / TPU law). Each
  contact has a series spring: the cell (8 kN/mm radial, 30 kN/mm axial), the USB-C receptacle (3 kN/mm), and the
  structure's own give from the FE below. Damping 10 % of critical per contact, bumper hysteresis 0.35.
* **Structure** (`fem.py`, `fe_shell.py`, `fe_core.py`): voxel bricks (H 0.75 mm for the cup + cap and carrier, H / 2
  for the rail blocks), AMG-preconditioned CG.
  * The cup + cap stands on the floor at the bumper footprint. On a flat landing every bumper within 1 mm of the first
    touch carries too (the cap-end bumper sits 0.55 mm proud of the port-end one on the board face, and the model has
    no rotation). The rest of the outer skin can reach the floor through the label (one-sided stops, active set).
  * The compliance of each contact patch is the secant at the contact's peak, with all the shell's loads applied
    together, and it goes back into the impact as that contact's series spring. The impact is then run again.
  * Stress: every contact force on its patch at the peak instants, plus the part's own inertia. The carrier and rail
    blocks are free bodies, held by weak surface springs for the moment that the no-rotation model leaves over.
* **Board** (`board_dyn.py`): a Morley plate (60 modes) driven by the cup's motion, on one-sided supports (spacers 0.4,
  lips 0.5, USB-C housings 0.17-0.20, rail posts moving with the core). Strain envelope and part clearances.
* **Checks** (`checks.py`): every part against its limit. PA12 48 MPa tensile, ~55 MPa compressive; board strain
  1000 ue warn, 2000 ue bad; nickel strip ~240 N; a P20B weld ~250 N in shear; M2 pull-out ~200 N per screw.

## Run

```
python run_all.py --nproc N --h 0.75      # all 17 poses; ~2 GB per worker at H 0.75, ~3-4 GB at H 0.5
python figs.py                            # figs/*.png
```

`run_all.py` builds the contact tables if they are missing (`cache/`, not committed), then per pose: impact with a
rigid structure, the FE compliance, the impact again with the structure's give, the FE stress, the board, and at the
end `checks.py`.

## Limits of the model

* No rotation: edges and corners land with the centre of mass over the contact point, which is the hardest case.
* Linear-elastic PA12: a stress well past 48-55 MPa means the part yields or crushes locally there, not that it sees
  that stress. Thin edges that crush give way and hand the load on; a whole feature past the limit can break.
* The contact stiffness, cell stiffness and damping are estimates; their effect is checked by the sensitivity runs.
