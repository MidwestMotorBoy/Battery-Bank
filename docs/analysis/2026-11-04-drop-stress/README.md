# 1 m drop: contact model, stress in every part (2026-11-04)

The 2026-10-31 study (`../2026-10-31-drop-1m`) treated the bank as two masses with the inside bonded to the cup, so it could
not see the inside parts hitting each other. This one keeps every part that can move as its own body, finds where they
touch on the real master geometry, and runs the impact in 17 orientations from 1 m onto concrete.

## Results (1 m onto concrete)

The five flat drops are where the model is exact (no rotation needed). Stresses are linear-elastic: past about
48-55 MPa a PA12 part yields or crushes there, so read the numbers as "how far over", not as the stress it sees.
Inside loads move about +-20 % with the contact stiffness, cell stiffness and damping (x0.5 to x2), and a 1.5 m drop
adds about 20 % (`sens.py` -> `out/sensitivity.json`).

![face drops](figs/fig_faces.png)

| Part | Worst drop | Demand | Limit | What happens |
|---|---|---|---|---|
| Rail blocks (all four) | cap end, port end, side | front-can rims push the tongues 0.45-1.1 kN; block bodies 100-196 MPa away from the contact | 48 MPa | the tiny blocks can crack; tongues crush |
| Cap overtravel posts (4 x r1.5) | cap end | 2.2-2.9 kN on the posts, ~80-95 MPa bearing | ~55 MPa | tips crush; the front half of the bottom frame also bends onto the cap skirt (1.1 mm gap, ~2.7 kN) |
| Board | board face | bows 1.28 mm, surface strain 8900 ue (99th pct), F.Cu parts 0.03 mm off the wall (C434, C531, L501, C420, C524) | 1000-2000 ue | MLCC cracking, USB-C solder joints (J401 / J501 see ~190-250 N each) |
| C421 / C556 (7343 bulk caps on B.Cu) | back face | the core moves ~1 mm toward the back wall; the caps (0.88 mm off the cradle tops) hit them, ~1.9 kN (rigid estimate, high) | ~50-100 N | the caps or their joints break; cradles 245 MPa there |
| Rail post tips | board face | ~300 N each on the wall | ~55 MPa (bearing ~85) | tips crush |
| Carrier webs | port end, side, board face | the cells squeeze the webs 1.4-1.8 kN | 48 MPa | 134-192 MPa, mostly bearing in the cusps: dents |
| Cup side wall | narrow side | 140 MPa near the cap end (coarse mesh: 1-2 bricks through the wall) | 48 MPa | likely local yield, watch item |

Fine: cells (up to 4.4 kN radial and 4900 g against a 13 kN crush test and ~10^4 g for a bare cell), nickel strips
(may yield a little, ductile; the welds sit at about their shear strength, so pull-test them), the O-ring, the gel
filler (35 % stretch), the PA12 post spacers, the F.Cu lips, the cup walls and cap in the end drops.

Edges and corners (`out/*_<edge|corner>.json` from the PC run, before the inertia relief): the inside parts there
can only move along the drop direction, so a core stopped in one direction can't slide on in the other, and the cup
pivoted on its corner footprint in the FE. Their contact forces are upper bounds (carrier webs up to ~6 kN on the back
wall in a port-end / back edge) and their stresses are not usable yet; that needs a 3-DOF version of `dyn.py`.

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
python facefig.py                         # figs/fig_faces.png (the five flat drops)
python sens.py                            # out/sensitivity.json
```

`run_all.py` builds the contact tables if they are missing (`cache/`, not committed), then per pose: impact with a
rigid structure, the FE compliance, the impact again with the structure's give, the FE stress, the board, and at the
end `checks.py`.

## Limits of the model

* No rotation: edges and corners land with the centre of mass over the contact point, which is the hardest case.
* Linear-elastic PA12: a stress well past 48-55 MPa means the part yields or crushes locally there, not that it sees
  that stress. Thin edges that crush give way and hand the load on; a whole feature past the limit can break.
* The contact stiffness, cell stiffness and damping are estimates; their effect is checked by the sensitivity runs.
