# Layout review checklist

Use at three gates: before routing (placement review), after routing, before ordering. When reviewing someone
else's board, report findings as: severity (must-fix / should-fix / nice-to-have), location (refs/nets/layer),
what's wrong and why (the physics), and the fix.

## A. Before routing (placement)

- [ ] Stack-up and per-layer pour plan written and agreed.
- [ ] Mechanical parts placed and locked; outline, holes, notches, keep-outs, antenna edge correct.
- [ ] Zones follow power/signal flow; noisy and sensitive areas separated; gutters between blocks.
- [ ] Every hot loop: HF cap straddles high-side drain / low-side source; bulk behind; same layer as FETs.
- [ ] Switch-node copper minimal; nothing placed in the FET–inductor gap.
- [ ] Controllers near their FETs, gate-drive pins facing them; programming parts on the quiet side at their pins.
- [ ] Sense resistors oriented for straight current flow; their filters at the IC.
- [ ] Decoupling at every supply pin, smallest nearest.
- [ ] TVS/ESD in-line at connectors; nothing blocking connector pin escapes.
- [ ] Antenna module at the edge with the vendor's keep-out and ground extents.
- [ ] Temperature sensors on the copper they measure.
- [ ] Test points for rails, switch nodes (stub off inductor far side), key signals; ground points beside probes.
- [ ] Repeated blocks identical by translation.
- [ ] Dense ICs (>20 pins or <0.8 mm pitch) have 1.5 mm clear round them (1 mm for small fine-pitch parts), decoupling excepted
      (`check_routing_rules.py`, fan-out section empty).
- [ ] Courtyards clean; DRC + schematic parity clean; placement render reviewed.

## B. After routing

Electrical:
- [ ] DRC: 0 errors; unconnected 0; parity 0; every warning understood.
- [ ] Ground plane(s) continuous under every critical trace (render each plane layer alone; look for slots and
      antipad rows).
- [ ] `check_routing_rules.py` clean: inner layers Manhattan (L3 vertical, L4 horizontal), nothing but GND on
      L2/L5, no via-row slots, no long outer-layer signal runs, every signal via has a GND via within 1 mm.
- [ ] No reference changes on clocks/sense.
- [ ] Hot-loop return in the plane directly under the loop; no traces on the plane layer under power stages.
- [ ] Gate drive paired with its return; no gate trace beside a sense trace.
- [ ] Kelvin pairs from pad ends, tight, no vias/test points, away from SW nodes.
- [ ] Second grounds (gauge VSS, AGND) joined at exactly one point; nothing crosses the gap.
- [ ] High-current paths: width with margin for etch tolerance, no necks, enough vias at each layer change, mirrored
      and stitched where planned.
- [ ] Thermal pads: via arrays, solid connections, paste windowpane.
- [ ] Differential pairs: impedance, matching, symmetric vias, continuous reference.
- [ ] Fills stitched; slivers and islands removed; board-edge stitching where planned.

Manufacturing:
- [ ] Clearances and widths ≥ fab minimums with margin (2 oz outer layers!).
- [ ] Vias: standard sizes; via-in-pad only filled/capped; tented where under parts.
- [ ] Annular rings, hole sizes, copper-to-edge, mask dams on fine pitch.
- [ ] Fiducials, rails if needed; footprints medium density; polarity marks.
- [ ] Silkscreen readable, off pads; pin-1 and connector keys marked.

## C. Before ordering

- [ ] Gerbers and drill viewed; layer order and stack-up match the order form.
- [ ] Position file rotations verified in the fab's viewer; BOM complete; DNP/hand-fit excluded.
- [ ] A last render of every layer and a comparison with the vendor EVM layouts for each power stage.
