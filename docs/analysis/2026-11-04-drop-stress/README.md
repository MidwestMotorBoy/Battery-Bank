# 1 m drop: contact model, stress in every part (2026-11-04)

The 2026-10-31 study (`../2026-10-31-drop-1m`) treated the bank as two masses with the inside bonded to the cup, so it could
not see the inside parts hitting each other. This one keeps every part that can move as its own body, finds where they
touch on the real master geometry, and runs the impact in 17 orientations from 1 m onto concrete.

## Results (1 m onto concrete, with the 2026-11-05 cup fixes)

The five flat drops are where the model is exact (no rotation needed). Stresses are linear-elastic: past about
48-55 MPa a PA12 part yields or crushes there, so read the numbers as "how far over", not as the stress it sees.
Inside loads move about +-20 % with the contact stiffness, cell stiffness and damping (x0.5 to x2), and a 1.5 m drop
adds about 20 % (`sens.py` -> `out/sensitivity.json`, from the 11-04 geometry).

![face drops](figs/fig_faces.png)

| Part | Worst drop | Demand | Limit | What happens |
|---|---|---|---|---|
| Board | back face, board face | bows 1.0-1.2 mm, surface strain ~8000 ue (99th pct); USB-C tabs ~25 000 ue, ~200 N per receptacle; F.Cu C434 / C531 0.06 mm off the wall | 1000-2000 ue | MLCC cracking, USB-C solder joints. Nothing props the middle of the board; the fix is a mid-board support (not in this round) |
| Rail tongues (bottom pair) | cap end | the front cans still reach them, ~280 N each (was ~460); 307 MPa at the contact, block bodies 136 MPa | 48 MPa | tongue tips crush, the small blocks can crack. The cans sink ~0.5 mm into the bottom frame at the nickel strips before the tongues touch |
| Cup side wall, cradles | narrow side | 178 MPa in the wall near the cap end, cradles 143 MPa (coarse mesh: 1-2 bricks through the wall) | 48 MPa | local yield likely, watch item |
| M2 screws / cup mouth | cap end | in the rebound the core still pushes the cap while the floor has let go, so the cup (~48 g) hangs on the two radial screws: ~1.15 kN (was ~0.74 kN), lumped-shell estimate | ~400 N | the screws load the 1.3 mm of cup mouth below their holes in shear-out; test it on the real cup |
| Cap overtravel posts (5 x r2.5) | cap end | 3.4 kN on the posts, 42 MPa bearing (was 107 on 4 x r1.5) | ~55 MPa | fine now |
| Rail post tips | board face | ~270 N each on the wall, 69 MPa | ~55 MPa (bearing ~85) | tips dent |

Fine: cells (up to 3.0 kN radial and 2700 g against a 13 kN crush test and ~10^4 g for a bare cell), nickel strips
(may yield a little, ductile; the welds sit at about their shear strength, so pull-test them), the O-ring, the gel
filler (13 % stretch), the PA12 post spacers (28 MPa), the cap board feet (88 MPa bearing, 1.3 kN: they dent but
carry), the F.Cu lips, the carrier (frames 45, webs 31 MPa), and the whole port-end drop (everything under 7 MPa).
C421 / C456 / C521 / C556 clear the cans by 1.75-1.9 mm and nothing on B.Cu lands in any flat drop.

The cap-end floor force swings between runs (2.5 kN here, 11 kN on 11-04) because the bottom bumper works right at
its knee: 1.7-1.8 mm of crush, where its force climbs from 2 kN to 90 kN per mm. The cap plate stress (33 MPa here,
53 before) follows it; a 1.5 m drop would bottom it out.

Edges and corners (`out/edges_corners_2026-11-04/`, PC run on the 11-04 geometry, before the inertia relief and the
carrier fixes below): the inside parts there can only move along the drop direction, so a core stopped in one
direction can't slide on in the other, and the cup pivoted on its corner footprint in the FE. Their contact forces
are upper bounds and their stresses are not usable; that needs a 3-DOF version of `dyn.py`.

## Cup-side fixes (2026-11-05)

Logan picked the cup-side fixes from the 11-04 results (`hardware/mechanical/monolith_cup.py`, 402.1 g):

* Rail tongues set back 0.3 mm from the frame faces (`TONGUE_SETBACK`): the cell-to-tongue gap goes 0.40-0.45 to
  0.70-0.75 mm.
* Overtravel posts r1.5 to r2.5 (`OT_R`), plus a fifth post under the front cells (`OT_POSTS`).
* Cradle tops cut to x <= 20.5 under C421 / C556 (`CRADLE_CAP_RELIEF`).
* The 0.5 mm post-tip gap was run as a variant (see below) and is not in the model.

| Drop | Item | 11-04 | 11-05 |
|---|---|---|---|
| cap end | overtravel posts | 2.7 kN, 107 MPa | 3.4 kN, 42 MPa |
| cap end | cells on the bottom tongues | 920 N, tongues 517 MPa, blocks 196 MPa | 555 N, 307 MPa, 136 MPa |
| cap end | cap board feet | 960 N, 48 MPa | 1345 N, 9 MPa (99.9th pct away from the contact) |
| port end | cells on the top tongues | 2.2 kN, blocks 101 MPa | none, blocks 3 MPa (a model error, below) |
| back face | C421 / C556 on the cradles | 1.9 kN, cradles 245 MPa | none, cradles 38 MPa |
| back face | board strain | 4300 ue | 8100 ue (the caps no longer prop the board mid-span) |
| board face | board strain, post tips | 8900 ue, 312 N | 7800 ue, 269 N |
| narrow side | cup wall, cradles, rail blocks | 140, 111, 143 MPa | 178, 143, 104 MPa |

Three model errors were found and fixed on the way. The 11-04 numbers above are as they were reported, so part of each
change is the model, not the cup:

* **Carrier top frame missing.** At the 1.0 mm cloud mesh the 0.95 mm top frame had no bricks at all, so in a port-end
  drop the core sank 1 mm onto the top tongues. The carrier is now meshed at 0.5 mm or finer (`fe_core.H_CARRIER`). The
  PC run at 0.75 mm had the frame, but the next error gave the same result there.
* **Carrier give.** The carrier's give where it bears on the cup was a unit load spread over the whole contact patch,
  held at the cells' patches. Where the frame lies flat on a wall, that bends the parts of the frame the cells don't
  back, which the real contact never loads, so a frame flat on the top wall came out ~100 N/mm. Now both sides are
  rigid flats: the cells' patches are held, and the cup's patch is pushed in by a set displacement (`fe_core.compliance`).
  That is a stiffness upper bound, which is what a contact that puts its pressure where the part is stiff gives.
* **C421 / C456 / C521 / C556 height.** KiCad's 3D model is the 2.8 mm AVX 7343-30. The BOM part is the KEMET T593V
  (7343-20, 2.0 mm), so `monolith_parts.real_board()` now trims them to 2.0 mm. Their gap to the cradle tops was 1.68
  mm, not 0.88, before the trim (2.7 mm after it), so most of the 11-04 back-face cap strike came from the model.

The board plate model (`board_dyn.py`) also gained the B.Cu side: every B.Cu part within 3 mm of a can or a cradle top
(`cache/board_bcu.json`) is a one-sided stop, with the cans moving with the core. None land in the flat drops.

**Post-tip gap 0.5 (variant, not adopted).** Opening the rail post tips to 0.5 mm under the board-face wall means the
post spacers go to 0.5 too (they must stop at or below the tips). In the board-face drop that takes the tips from
269 to 223 N each (69 to 57 MPa) but lets the board travel further: it bows 1.82 mm (was 1.20), strain 9300 ue (was
7800), and L201, C531 and L501 reach the wall (L201 by 0.18 mm). The tips are the smaller problem, so the gaps stay at
0.3 / 0.4.

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
* **Structure** (`fem.py`, `fe_shell.py`, `fe_core.py`): voxel bricks (H for the cup + cap, at most 0.5 mm for the
  carrier, H / 2 for the rail blocks), AMG-preconditioned CG. The 11-05 runs use H 1.0.
  * The cup + cap stands on the floor at the bumper footprint. On a flat landing every bumper within 1 mm of the first
    touch carries too (the cap-end bumper sits 0.55 mm proud of the port-end one on the board face, and the model has
    no rotation). The rest of the outer skin can reach the floor through the label (one-sided stops, active set).
  * The compliance of each contact patch is the secant at the contact's peak, with all the shell's loads applied
    together, and it goes back into the impact as that contact's series spring. The impact is then run again.
  * The carrier's give where it bears on the cup: the cells' patches held and the cup's patch pushed in, both as rigid
    flats (`fe_core.compliance`).
  * Stress: every contact force on its patch at the peak instants, plus the part's own inertia. The carrier and rail
    blocks are free bodies, held by weak surface springs for the moment that the no-rotation model leaves over.
* **Board** (`board_dyn.py`): a Morley plate (60 modes) driven by the cup's motion, on one-sided supports (spacers 0.4,
  lips 0.5, USB-C housings 0.17-0.20, rail posts moving with the core, and the B.Cu parts nearest the cans and cradle
  tops). Strain envelope and part clearances.
* **Checks** (`checks.py`): every part against its limit. PA12 48 MPa tensile, ~55 MPa compressive; board strain
  1000 ue warn, 2000 ue bad; nickel strip ~240 N; a P20B weld ~250 N in shear; M2 pull-out ~200 N per screw.

## Run

```
python run_all.py --nproc N --h 0.75      # all 17 poses; ~2 GB per worker at H 0.75, ~3-4 GB at H 0.5
python run_all.py --nproc 4 --h 1.0 side board back bottom top   # the five flat drops (~50 min on 4 cores)
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
