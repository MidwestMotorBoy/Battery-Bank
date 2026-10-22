# Critique D: cross-examination of A, B, C and E, and a revised D

All numbers are my own estimates unless a source is quoted. I used these values throughout:
- Al: E = 70 GPa
- Pure Ni yield ≈ 100 MPa, so yield strain ≈ 0.05 %
- TPU 95A compression set: Stratasys FDM TPU 92A measures 44 % at 70 °C (A's source)
- Leak limit: INFICON's IP67 "zero water" level is ≈1×10⁻³ mbar·L/s

---

## A: Gasketed box (CNC lid, O-ring, 6 screws)

**Most serious flaw: the tail bending strain is under-estimated, and it lands on the solder fillet.**

A fixes the PCB to the shell and lets the cells float on about 1 mm of TPU. It then claims that a 5 mm free tail bending through 0.5 mm of travel sees about 0.35 % strain.

That is too low. A tail welded at the cell and lap-soldered flat at the PCB is closer to a **fixed-guided beam**: ε = 3tδ/L² = 3 × 0.2 × 0.5 / 5² = **1.2 %**. Even a pure cantilever gives 0.6 %. Both are 2–3× A's figure, and roughly 20× the yield strain of Ni.

With a Coffin-Manson estimate (ε_f′ ≈ 0.5, c ≈ −0.6), 1.1 % plastic strain gives a life of about **600 cycles**. That is fine for drops. The problem is where the bending moment peaks: at the root of the fold, which is the edge of the lap-solder fillet. Solder fatigues much faster than nickel.

This is a direct result of the "PCB fixed, cells float" architecture. C and my own D avoid it by putting cells and PCB in one carrier. **Test:** 4-wire resistance on each joint across a 26-drop sequence, which A already lists. I would expect cracks at the fillet toe first.

**Second flaw:** the O-ring reaction is about 400 N, and it permanently loads screws threaded through PETG lobes. A admits that PETG creeps at 60 °C (HDT ≈ 70 °C). The hard stop holds the squeeze only while the screws still have more than about 70 N of preload each.

**Idea I'd steal: put the groove in the precision part.** The printed side only has to give one ironed, single-Z land. For D this means the sealant groove geometry, which sets the bond-line thickness, would be better held by the metal part than by the print.

---

## B: Flashlight tube (radial O-rings, bonded saddle)

**Most serious flaw: the production tube material contradicts the evidence the other concepts cite, and the leak test as written cannot pass.**

1. **MJF PA12 is not watertight as-printed.** B calls MJF PA12 at 2.2 mm walls "the production choice: no seam, isotropic". A cites an MDPI study, and E cites Xometry, saying MJF parts are porous and need impregnation. B never addresses this. The parts that would make B's radial seal work (an MJF tube and MJF caps) are the ones least likely to hold 100 mbar without a sealing treatment.
2. **The steps are in the wrong order.** Step 11 vacuum-tests through the vent hole, but the heatsink window is still open until step 12. The note "swap 11 and 12" is the real sequence. Even then, the saddle bead has to cure for 24 h before any test, which is the same cure wait D pays.
3. **The O-ring is over-stretched (smaller point).** A 55 mm ID ring has a 173 mm circumference. The groove root perimeter of a 50 × 60 rounded rectangle with r6 corners is about 185 mm, so the ring is stretched about 7 %. That is above the ~5 % guideline and thins the cross-section by about 3 %, which eats into an already tight ±0.18 mm squeeze budget.

**Idea I'd steal: a bigger heatsink that wraps the edges.** B's saddle is 50 × 86 mm with 15 mm returns, about 79 cm² against D's 28 cm². B also lets the caps stand proud so they are the impact face. I adopt both below.

---

## C: Electrical-first (rigid core, TPU boot clamped by a flat plate)

**Most serious flaw: a flat 2 mm plate on 4 screws cannot hold an even squeeze on a 274 mm TPU bead.**

The bead is a 1.6 mm half-round in 95A at 25–30 % squeeze, so 0.4–0.5 mm of compression. A reasonable line load is 2–3 N/mm per edge.

Treat the plate (51 mm wide, 2 mm thick, I ≈ 34 mm⁴) as simply supported between corner screws about 80 mm apart, with w ≈ 5 N/mm from both edges:

δ = 5wL⁴/384EI ≈ **1.3 mm**

That is about **3× the squeeze**. The middle of each long edge lifts off.

C's own risk list names TPU compression set, and A's source puts that at 44 % at 70 °C. Set would take away part of the squeeze that the plate does deliver. The PA12 carrier flange behind the bead also flexes. A reached the same conclusion with a much stiffer CNC lid and 6 screws (bowing under 0.02 mm), and that is why A has 6 screws.

**Fix for C:** add bent return flanges, more screws, or bond the plate instead.

**Idea I'd steal: take datums from one end, and keep the cells and PCB rigid relative to each other.**
- All cells and the fixed PCB peg locate from the same end.
- Cell length tolerance and CTE are taken by a joggle at the far end.
- In D, the cells and PCB already move together in the TPU cradle. But TPU is soft, so under a 300–500 g end hit the cells can shift relative to the PCB groove by a fraction of a mm. A rigid carrier, or a hard datum at one end, is better.

---

## E: Rigid core with a soft skin (boot is the only seal; plate clamps a bead)

**Most serious flaw: the leak test, as written, tests nothing.**

1. **The vent short-circuits the test.**
   - Step 8 sticks the ePTFE vent on before step 12, which pulls a vacuum over the pack in a jar of water.
   - An ePTFE vent is made to pass air, and the free volume is about 50 cm³. The inside therefore follows the jar pressure within seconds to minutes.
   - The seals see almost no differential pressure, and the vent bubbles steadily right where it is.
   - A leak at the plate bead, a few mm away, would be both unloaded and masked.
   - **Fix:** test through the bare vent hole before fitting the vent, as A, B, C and D all do.
2. **The plate-clamp problem is the same as C's.** The 1.5 mm plate with 3 mm returns has I ≈ 60 mm⁴ by my channel-section estimate. With 4 corner screws over 84 mm and a 1.0 × 0.8 bead at 30 % squeeze (only **0.24 mm** of compression), mid-span deflection comes out around 0.5–0.8 mm.
3. **The screw grommets are TPU too.** The screws clamp through TPU collars, and those collars also take a compression set. Over time the screws lose preload, which is the same loss as at the bead.

**Idea I'd steal: p = T/R.**
- A stretched skin seals round bores and cannot seal flats.
- This is the cleanest statement of why a TPU over-boot cannot be the IP seal. D already rejects that idea, and E gives it a physics basis.
- I'd also take **dispensed gap filler instead of a cut pad**. Putty absorbs the ±0.3 mm print tolerance that sets D's PCB-to-heatsink gap, and there is no pad to place.

---

## Does anything in the others beat D? Yes. Changes to D:

1. **Make the heatsink bigger** (from B).
   - Extend the C-channel to the full PCB face except the 15 mm BLE end, and wrap the flanges about 8 mm round the two long edges outside the bond groove.
   - Area grows from about 28 cm² to about 50 cm², so the continuous dissipation at a 40 K rise goes from about 1.6 W to about 2.8 W.
2. **Widen the bond line** (my own weak point).
   - Change the groove from 3 to 4 mm wide, which gives about 1.25 mm per side.
   - PETG/Al shear strain over the 70 K swing drops from 17–25 % to about **10–13 %**, comfortably inside the MS-polymer movement rating.
3. **Use dispensed gap filler instead of the cut pad** (from E and B).
4. **Take datums from one end** (from C).
   - The cradle gets a rigid PETG datum rib at the USB end, against which the cells and the PCB both register.
   - The far-end sense tails get the joggle.
5. **Enlarge the burst/vent port from Ø6 to Ø10 mm.**
   - A 21700 venting event releases litres of gas per second.
   - Choked flow through 28 mm² is only about 5 L/s.
   - 79 mm² gives margin, and the label still peels off well below the tub's burst pressure.
   - This is my answer to B's "screws as the weak link"; A has no burst path at all.
6. **Make the caps the impact face** (from B). The boot's end pads stay, but the PETG cap rim stands 1 mm proud of the tub, so an end hit loads the snap-bonded joint in compression, not peel.
7. **New honest risk, which the others share:** P0 is the first build (no dev board), and a non-opening pack seals in J301/J302.
   - Gauge training and firmware must be finished at the open-core step.
   - Field updates must go by **BLE OTA**, which the CC2340 supports.
   - Otherwise every firmware fix is a blade-and-rebuild.
   - For P0 specifically, I'd do the first two builds with the joints **unsealed**: snaps only, with the pack dry-tested on the bench, not immersed. Bond only once the electronics are proven. The snap-then-seal design allows this at no cost; a screwed gasket (A) gets it for free.

**What I keep:**
- The bonded, snap-held joints, with no screws, gaskets or clamps.
- One material for the structural seal.
- Cells and PCB riding in one carrier.
- The bare-vent-hole positive-pressure bubble dunk.

I think this is the most robust test procedure of the five, since it makes E's vent mistake impossible.

Revised estimate: about 63 × 54 × 94 mm, about 440 g, about 20 items, still **13 steps** with one 48 h cure.
