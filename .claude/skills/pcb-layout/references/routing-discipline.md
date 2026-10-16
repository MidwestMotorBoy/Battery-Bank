# Routing discipline: layer directions, fan-out first, untouchable planes

These rules come from the user's review of an earlier pour plan. They are the house rules for routing on this
project, and they are a good default on any multilayer board. `scripts/check_routing_rules.py` checks all of
them on a KiCad board. Run it after every routing stage, alongside DRC.

Layer names below use L-numbers for a 6-layer board. The KiCad equivalents are L1 = F.Cu, L2 = In1, L3 = In2,
L4 = In3, L5 = In4, L6 = B.Cu. On other layer counts, apply the same roles. Planes are the layers next to the
outer layers, and each pair of buried signal layers between them is a Manhattan pair.

## Contents
1. Inner signal layers are a Manhattan pair · 2. Outer layers are free-angle but local · 3. Fan out
fine-pitch parts first · 4. The ground planes are untouchable · 5. Reference changes · 6. Scripted routing ·
7. Checklist

## 1. Inner signal layers are a Manhattan pair

- **L3 (In2) is vertical-preferred and L4 (In3) is horizontal-preferred.** Every segment on L3 runs along Y and
  every segment on L4 runs along X. There are no diagonals and no "just this once" jogs.
- **Change direction only by a via to the paired layer.** A net that must turn goes L3 vertical, then a via,
  then L4 horizontal. It never turns within one layer.
- Why:
  - Two buried signal layers with no plane between them couple broadside. Crossing at 90° keeps that coupling
    to a point at each crossing instead of a long parallel run.
  - Fixed directions keep the routing channels open. Each layer's tracks pack in parallel lanes, so the next
    net always has a lane, and the board stays routable to the end.
  - The result is predictable and easy to review by eye or by script.
- Plan lanes at the start: count how many nets must cross each region on each axis, and leave channels at
  placement for them.
- The direction rule covers traces only. A local copper pour on L3/L4 (GND fill, a small rail island) isn't a
  route. Pours still keep off the planes, as section 4 says.

## 2. Outer layers are free-angle but local

- L1 and L6 (F.Cu, B.Cu) allow any angle; use 45° or arcs, never acute angles. Use them for:
  - component escapes and fan-out stubs;
  - short local connections inside a block (a few mm, pad to pad, part to its via);
  - decoupling: cap to pin, cap to via;
  - power pours, hot loops, gate-drive pairs and Kelvin pairs, which belong at the parts.
- **Don't run long signals on the outer layers.** Anything that leaves its block drops to L3/L4 through a via
  near the part and travels in Manhattan style.
- Why: the 2 oz outer layers need wider minimum gaps, so traces there waste area. They also carry the power
  pours, sit nearest to probes, fingers and ESD, and radiate more than buried layers.
- `check_routing_rules.py` flags outer-layer signal runs longer than `--outer-max` (default 15 mm) for review.
  Power, gate-drive and Kelvin nets that must stay at their parts are exceptions, and you can whitelist them.

## 3. Fan out fine-pitch parts first

- **Keep at least 3 mm clear around any IC with more than 20 pins, or with a pin pitch under 0.8 mm.** The clear
  area is measured from the IC's courtyard. No other part's courtyard enters it, so every pin has room to
  escape and drop a via.
- **Exception: decoupling caps** go as close to their pins as DRC allows, inside the 3 mm area. The checker
  treats a cap that shares a supply/ground net with the IC as decoupling.
- **Fan out these ICs before routing any other nets.** Give each signal pin a short escape and a via, staggered,
  so each pin can reach L3/L4. Then route the rest of the board. If fan-out comes later, the vias of other nets
  fill the space, and the dense part becomes unroutable.
- This extends `placement.md` §7 (escape channels): the rule sets the channel at 3 mm all round.

## 4. The ground planes are untouchable

- **L2 and L5 (In1, In4) are solid GND planes.** They carry no traces, no splits, no other-net islands and no
  rows of vias.
- A second ground (battery-gauge VSS, AGND, chassis) **does not go on a plane layer**. Pour it as local fill on
  the outer layer under its parts, plus fill on the signal layers if needed. Keep L2/L5 solid system GND under
  it, and join the second ground only at its single point (shunt pad or net tie). The gauge's small currents
  don't need a plane of their own. What matters is that pack current never flows in the gauge's copper.
- **Vias through the planes:**
  - Through vias necessarily pierce L2/L5. Each one leaves an antipad, so arrange them so the plane stays whole.
  - Never put vias in a straight row whose antipads merge into a slot. Stagger high-current via arrays, and keep
    at least a 0.3 mm copper web between neighbouring antipads.
  - Keep via fields out from under critical traces on the adjacent layers.
  - Render each plane layer alone after placing any via array.
- **Don't route a signal across a gap in its adjacent plane.** That includes accidental gaps (antipad slots,
  cut-outs and keep-outs).

## 5. Reference changes

- A signal that changes layer usually changes reference plane. L1 and L3 reference L2; L4 and L6 reference L5.
- **Every such layer change gets a GND via within 1 mm of the signal via.** That via carries the return current
  between the planes. The checker reports signal vias with no GND via within 1 mm.
- L3 ↔ L4 swaps (a direction change) also change reference plane, from L2 to L5. They need the GND via too.

## 6. Scripted routing

- A script router must generate axis-aligned segments per layer: only vertical on L3, only horizontal on L4.
  At a turn it places a via, then continues on the other layer.
- On the outer layers, keep the router to short escapes. Cap the outer-layer path length for signal nets, and
  give each one a via down to the Manhattan pair near its pad.
- Put the plane layers out of bounds for the router. Never pass them as routing layers.
- At every L3 ↔ L4 via and every outer ↔ inner via, place or reuse a GND via within 1 mm. Reserve the spot when
  the via is placed, before neighbouring tracks take the space.
- Order: fan out the fine-pitch ICs (section 3) → power and critical nets (SKILL.md order) → Manhattan routing
  of the rest → fills and stitching.

## 7. Checklist

- [ ] No segment on L3 that isn't vertical; none on L4 that isn't horizontal.
- [ ] No tracks and no non-GND zones on L2/L5; no via rows that slot them.
- [ ] No long signal runs on L1/L6 (all flagged ones reviewed).
- [ ] Every signal layer change has a GND via within 1 mm.
- [ ] Every IC with more than 20 pins or a pitch under 0.8 mm has 3 mm clear around it (decoupling excepted),
      and was fanned out first.
