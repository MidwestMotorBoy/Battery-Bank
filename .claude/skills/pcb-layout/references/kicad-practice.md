# KiCad practice and scripting

Contents: 1. Board setup · 2. Net classes · 3. Custom rules (.kicad_dru) · 4. Zones · 5. Net ties and rule areas ·
6. Routing tools · 7. Checking: DRC, parity, renders · 8. Scripting with pcbnew (pitfalls) · 9. Script-based routing
lessons · 10. Hand-off etiquette

Written against KiCad 8–10. Check `Board Setup → Design Rules → Custom Rules → Syntax help` for the exact grammar of
your version.

## 1. Board setup

- Physical stack-up: layer count, thicknesses, copper weights matching the fab's stack (JLC publishes theirs).
- Constraints: minimum clearance, track width, via size/drill, annular ring, hole-to-hole, copper-to-edge, silk
  rules — copy from the fab's capabilities, then add margin.
- Pre-defined track widths and via sizes per net class for quick switching while routing.

## 2. Net classes

Group nets by electrical need and give each class width, clearance and via defaults, e.g.:

| Class | Width | Clearance | Via | Nets |
|---|---|---|---|---|
| HighCurrent | 2.5 mm (or pours) | 0.25 mm | 0.3/0.6 | pack, cells, switch nodes, VBUS, PPHV |
| Power | 0.8 mm | 0.2 mm | 0.3/0.5 | 5 V, 3.3 V rails |
| GateDrive | 0.4 mm | 0.2 mm | 0.3/0.45 | HO/LO, BST |
| Kelvin | 0.2 mm | 0.2 mm | 0.3/0.45 | sense pairs |
| Default | 0.2 mm | 0.15 mm | 0.3/0.45 | everything else |

Assign by name patterns (`*/SW1`, `/Cells and Gauge/CELL*`) so new nets inherit the right class.

## 3. Custom rules (.kicad_dru)

Use custom rules for constraints the board-setup table can't express. Rules live in `<project>.kicad_dru`:

```
(version 1)

# More clearance between high-current copper and small signals (pads keep their footprint spacing)
(rule "HighCurrent to small signals"
	(constraint clearance (min 0.25mm))
	(condition "A.NetClass == 'HighCurrent' && B.NetClass == 'Default' && A.Type != 'Pad' && B.Type != 'Pad'"))

# Component holes on 2 oz outer copper need a bigger ring
(rule "PTH annular ring 2 oz"
	(constraint annular_width (min 0.25mm))
	(condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole' && A.Hole_Size_X >= 0.5mm"))

# Copper-to-edge, except a connector whose land pattern reaches the notch
(rule "Edge margin"
	(constraint edge_clearance (min 0.25mm))
	(condition "A.Parent.Reference != 'J401'"))

# Differential pair geometry
(rule "USB pair"
	(condition "A.inDiffPair('/USB_D*')")
	(constraint diff_pair_gap (opt 0.15mm))
	(constraint track_width (opt 0.2mm)))
```

Notes: one `layer` token per rule (only the last counts); `severity` and `assertion` exist since v7;
`insideCourtyard()` is deprecated in favour of `intersectsCourtyard()`. A `zone_connection` rule did not change the
fill in KiCad 10's python/kicad-cli fills — set the connection on the pad/footprint instead.

## 4. Zones

- One zone outline per net per layer. Priority decides which of overlapping zones fills first; a lower-priority
  zone is cut around a higher one by clearance. Same-net zones with different priorities don't merge (the lower is
  knocked out); same-net same-priority overlaps raise `zones_intersect`.
- Zone settings: clearance, minimum width (removes slivers narrower than this), pad connection (solid / thermal /
  none), thermal gap and spoke width (spoke ≤ pad width; zone min width ≤ spoke width), island removal.
- Full-board plane: draw the outline inset ~0.5 mm from the edge. Give mounting holes a keep-out ring.
- Keep vias inside the zone outline; a via outside the edge makes a narrow neck.
- `connection_width` / minimum-width DRC warnings point only at the zone origin: find the neck by rendering the
  fill or by bisecting (remove footprints, refill, re-run DRC).
- Thermal vias inside exposed pads got thermal-relief rings and pinched planes: set `(zone_connect 2)` (solid) on
  those pads in the footprint.
- Refill zones before DRC (`kicad-cli` DRC refills; scripts must call the filler).

## 5. Net ties and rule areas

- **Net tie** footprints let two nets meet at one defined point (AGND–PGND at a pad, CSA–SW1, gauge VSS–GND at a
  shunt, a copper "link" replacing a 0 Ω). The DRC then flags any other contact.
- **Rule areas** (keep-outs) for antenna regions, mounting holes, board-edge zones; put them in the footprint when
  they belong to a part so they move with it.

## 6. Routing tools

- Interactive router: walkaround/shove modes; set track width per net class; use the differential-pair router for
  pairs and the length tuner for matching.
- Teardrops (v8+): add on narrow tracks into pads/vias for mechanical/etch robustness; not on RF lines.
- Stitching vias: place in a grid on fills; they must be on a net (GND) to connect.
- Freerouting (DSN/SES) exists but on dense power boards it routes across power stages and breaks DRC; prefer hand
  routing or a constrained custom router for critical nets.

## 7. Checking: DRC, parity, renders

- `kicad-cli pcb drc --schematic-parity --severity-all -o report.rpt board.kicad_pcb` — run after every stage;
  compare counts by type against the previous run (`scripts/drc_summary.py`).
- **kicad-cli and pcbnew saves rewrite `<project>.kicad_pro`** (key order, defaults, sometimes lost custom rules):
  back it up before and restore after, or the next DRC runs with default rules. If DRC suddenly shows copper-edge,
  clearance or drill errors everywhere, compare the `.kicad_pro` against git first.
- Render PNGs (`scripts/render_board.py`) and look at them; the browser pane can't open local SVGs, PNGs work with
  the image viewer.
- If KiCad has the board open (`~board.kicad_pcb.lck`), tell the user to revert/reload before saving after a
  scripted change, or their save overwrites it.

## 8. Scripting with pcbnew (pitfalls)

- Use KiCad's bundled python (`C:/Program Files/KiCad/10.0/bin/python.exe` on Windows); run scripts with `-I`
  (isolated) and never name a script after a stdlib module (`bisect.py`, `random.py` shadow imports).
- **One board per process**: a second `LoadBoard()` after a save can return a dead wrapper.
- **Mass removal kills wrappers**: removing hundreds of items via pcbnew makes later calls return dead SWIG objects.
  Strip old `(segment …)`/`(via …)`/`(zone …)` blocks from the file as text (balanced-paren scan matching their
  uuid) *before* `LoadBoard`.
- **Groups are write-only from python** in KiCad 10 (`GetItems()` returns bare SwigPyObjects): keep a sidecar file
  of the uuids your script added and delete those on the next run — makes scripts re-runnable.
- **`PCB_VIA.GetWidth()` without a layer argument raises an assert dialog that hangs a headless script**: always
  `GetWidth(pcbnew.F_Cu)`. Find such hangs with `python -X faulthandler` and `faulthandler.dump_traceback_later(30)`.
- `board.GetBoardPolygonOutlines(polyset, False)` needs the bool; `SHAPE_POLY_SET.Collide/Contains/Inflate` work;
  `pad.GetEffectivePolygon(layer, pcbnew.ERROR_INSIDE)` gives the exact pad shape; `zone.GetFilledPolysList(layer)`
  the fill.
- `pcbnew.ExportSpecctraDSN` / `ImportSpecctraSES` work, but SES import replaces every track and via.
- A scratch copy saved under a new name gets default rules (min connection 0): DRC on it is meaningless unless you
  copy the real `.kicad_pro` and `.kicad_dru` beside it.
- Write any script containing backslashes with a file-writing tool, not a shell heredoc (heredocs can halve
  backslashes and corrupt regexes or KiCad text).
- Footprints: changing a symbol's footprint field then reloading the footprint on the board at its old position is
  the clean way to swap packages; check parity afterwards.

## 9. Script-based routing lessons

- Map every pad of an area first (render by net, dump pad boxes), then write zone polygons/tracks with explicit
  coordinates and check clearances before running. One area at a time; DRC and render after each.
- Power as zones (one outline per net per layer), mirrored on the opposite outer layer, stitched. Cap ground pads
  surrounded by another net's pour get a small ground "pocket" zone with their own vias to the plane.
- Placement may need small fixes for routing (turn a sense resistor so current flows straight, move a filter part
  out of the current path): fix placement, not the route.
- Gate drive: keep each gate and its return as a side-by-side pair on F.Cu where possible. If a pair must go
  inner, both run side by side on the same Manhattan layer, in that layer's direction. Stacking on In2/In3 doesn't
  work, because they run at right angles. Keep bootstrap loops on the outer layer without vias. Count lanes and
  check order before coordinates.
- Kelvin taps from the resistor pad's quiet end; route the pair together; never let a router connect a sense line
  to nearby copper of the same net.
- A maze router (A*) on a 0.1 mm grid with obstacles = other-net copper grown by clearance + half width, the
  ground plane layers excluded, and per-layer costs, routes a dense board's small signals far better than
  Freerouting; bucket hole positions for fast via-spacing checks.
- Make such a router obey `routing-discipline.md`:
  - on the inner pair, allow only vertical moves on one layer and horizontal moves on the other, so a turn costs
    a via;
  - cap the path length on F.Cu/B.Cu for signal nets (escapes only);
  - when a via is placed, reserve a GND via site within 1 mm.
  Run `check_routing_rules.py` on the result.

## 10. Hand-off etiquette

- Work on a copy (branch/worktree) when the user is editing the same board in KiCad.
- Commit scripts that generate copper; record decisions (pour plan, stack-up) in project docs.
