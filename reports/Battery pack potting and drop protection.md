# Cushion the cell ends, don't pot the cells

The short answer for the Monolith is to **leave the cell cavity unpotted.** Drop resistance should come from compliant end stops and crushable corners. The board should get a selective conformal coat plus staking, not a full pour. If the cells need any compound at all, use a thin, soft, thermally conductive layer between their outer faces and the shell, with low-density foam only at the cell ends. Drop protection and thermal performance pull in different directions only if one material is asked to do both jobs. Battery foams, the obvious "drop-proof" potting, have a thermal conductivity of **0.05–0.075 W/m·K**, which is barely better than still air. Conductive potting that does cool the cells weighs **1.6–3.1 g/cm³**, so filling the 2×2 cell voids would add about **45–85 g to a 333 g product**. The physics also shows that potting is the wrong tool for drops. The documented drop failure in cylindrical cells is **contact loss in the CID region after an axial (end-on) impact**, and stroke at the ends is what fixes that, not fill around the cans. The research supports this direction well. Two things the research did not settle are left for the validation plan: absolute peak-g and temperature numbers for this pack, and any 58E-specific data. Many numbers below are the researchers' own first-principles estimates and are marked as such.

## Two jobs, two materials: why one compound cannot do both

The available compounds fall into three density bands, and within those bands, conductivity goes up with density. **Every product found above 1 W/m·K is 1.6 g/cm³ or denser.** **Every product at or below 0.3 g/cm³ has k ≤ 0.075 W/m·K** ([H.B. Fuller EV Protect 4006 TDS](https://res.cloudinary.com/iwh/image/upload/q_auto,g_center/assets/1/26/HB-Fuller_EVProtect4006_TDS-0626.pdf); [Graco profile of DOWSIL EF-6525](https://graco.com/us/en/in-plant-manufacturing/material-profiles/foam/dow-dowsil-ef-6525.html); [Henkel TGF 1000](https://www.henkel-adhesives.com/uk/en/product/thermal-gap-fillers/bergquist_gap_fillertgf1000.html); [Parker SC-320](https://www.parker.com/content/dam/Parker-com/Literature/Assembly---Protection-Solutions-Division/Technical-Datasheets-(TDS)/Datasheet---CoolThermSC-320(Chinese)_DS3724C.pdf)). The only middle option found is Permabond's ET5442 epoxy foam. It is 0.89 g/cm³ with a foam k of 0.3 W/m·K, but it is 60 Shore D and effectively permanent ([Permabond ET5442 TDS](https://www.permabond.com/wp-content/uploads/2023/10/ET5442_TDS.pdf)).

| Family / example | Density (g/cm³) | k (W/m·K) | Hardness | Small-batch form | Mass if filling the ~27 cm³ cell voids* |
|---|---|---|---|---|---|
| PU battery foam: [EV Protect 4006](https://res.cloudinary.com/iwh/image/upload/q_auto,g_center/assets/1/26/HB-Fuller_EVProtect4006_TDS-0626.pdf) | 0.16–0.19 | 0.05 | 35–45 Shore A | 20.9 kg pail minimum, machine mix | 4–5 g |
| Silicone foam: [DOWSIL EF-6525](https://graco.com/us/en/in-plant-manufacturing/material-profiles/foam/dow-dowsil-ef-6525.html) | 0.3 | 0.075 | 30 Shore 00 | not confirmed | 8 g |
| Epoxy foam: [Permabond ET5442](https://www.permabond.com/wp-content/uploads/2023/10/ET5442_TDS.pdf) | 0.89 | 0.3 (skin >1) | 60 Shore D | dual cartridge | 24 g |
| Silicone gel: [Wacker SilGel 612](https://www.wacker.com/h/de-ke/medias/WACKER-SilGel-612-AB-en-2025.03.14.pdf), [SYLGARD 527](https://www.farnell.com/datasheets/2040055.pdf) | 0.95–0.97 | ~0.2 (typical) | penetration 150–300 | 2 kg kits | 26 g |
| Unfilled silicone: [SYLGARD 184](https://www.dow.com/en-us/pdp.sylgard-184-silicone-elastomer-kit.01064291z) | 1.03 | 0.27 | 43 Shore A | small kits | 28 g |
| Gap filler: [Bergquist TGF 1000](https://www.henkel-adhesives.com/uk/en/product/thermal-gap-fillers/bergquist_gap_fillertgf1000.html) | 1.6 | 1.0 | 30 Shore 00 | cartridge | 43 g |
| Conductive epoxy: [MG 832TC](https://www.mouser.com/datasheet/3/293/1/tds_832tc_2parts.pdf) | 1.7 | 0.7 | 81 Shore D | 450 mL kit | 46 g |
| High-k gap filler: [TGF 3600](https://conro.com/downloads/Manuals/BERGQUIST-TGF-3600-TDS.pdf), [SC-320](https://www.parker.com/content/dam/Parker-com/Literature/Assembly---Protection-Solutions-Division/Technical-Datasheets-(TDS)/Datasheet---CoolThermSC-320(Chinese)_DS3724C.pdf) | 3.0–3.1 | 3.2–3.6 | ~35 Shore 00 | cartridge / bulk | 81–84 g |

*The researchers' geometry estimate: a 2×2 bounding box minus the cells is (4 − π)·d² × 70.8 mm ≈ 27–29 cm³. The central interstice alone is only about 7 cm³.

The heat side of the problem is serious. No published DCIR or still-air heating data exists for the EVE 58E. A BudgetLightForum user found almost nothing independent ([BLF thread](https://budgetlightforum.com/t/eve-21700-40pl-70-amp-cell/225506)). The researchers therefore bracketed it. They took the Molicel P45B's **15 mΩ** DC impedance as a floor ([Molicel P45B datasheet](https://www.imrbatteries.com/content/molicel_p45b.pdf)) and 25–40 mΩ as a plausible range for an energy cell. That gives **about 0.7–2 W per cell at 7 A, or roughly 4–6 W for the pack as a planning figure**. This is an estimate, and it should be replaced by an HPPC pulse measurement. With no heat leaving, 4–6 W into the cells' ~280 J/K over a 50-minute discharge gives a **43–64 K rise**. From 25 °C that approaches or passes the 60 °C discharge limit that vendors list for the 58E ([NKON 58E listing](https://www.nkon.nl/en/eve-inr21700-58e-5700mah-16-8a.html)). A sealed 100 W pack therefore needs a deliberate conduction path from the cells. Internal air is not enough.

The researchers' conduction estimate shows what any fill actually buys. Their equivalent film coefficient is h_eq = k/t:

- Still air across a 3 mm gap: about **9 W/m²K**.
- Silicone foam across 3 mm: about **17 W/m²K**.
- Unfilled silicone across 3 mm: about **67 W/m²K**.
- A 1 W/m·K filler across 3 mm: about **330 W/m²K**.

The printed wall (PLA/PETG, 2 mm) is about 75–100 W/m²K, so it is not the bottleneck. The bottleneck is natural convection and radiation outside the shell, at roughly 8–12 W/m²K. For 8–10 W total that means **a 20–30 K shell-to-ambient rise that no internal potting can beat**. Only a larger or metal outer surface, or airflow, lowers that floor.

Simulation work agrees in direction but shows a modest size. A silicone-encapsulated LFP 32700 pack ran **2.57 °C cooler at 1C and 3.84 °C cooler at 2C** than an air-filled one ([SAE 2024-28-0224](https://saemobilus.sae.org/papers/thermal-performance-encapsulated-lfp-battery-packs-encapsulants-2024-28-0224)). The conclusion is that potting helps the cells only when it bridges them to a heat-rejecting wall and has k above about 0.1 W/m·K. Foam wrapped around cells makes them slightly worse. Potting that couples the board's hot inductors (about 1.6 W each, worst case) to the cells is actively harmful.

## The drop threat is axial, and the answer is stroke

The compliance bar is low. **IEC 62133-2 requires three 1.0 m drops onto concrete with no fire or explosion** ([EverExceed](https://www.everexceed.com/overview-of-lithium-battery-safety-testing-iec-62133_n426); [Samsung 40T datasheet](https://www.dnkpower.com/wp-content/uploads/2019/02/SAMSUNG-INR21700-40T-Datasheet.pdf)). **UN 38.3 T4 requires a 150 g, 6 ms half-sine** with no leak or vent and OCV at least 90 % afterwards ([Lenovo UN38.3 summary](https://static.lenovo.com/ww/docs/regulatory/msds/SB10W51939_UN38.3.pdf)). Neither test requires the product to keep working. A pack with an open CID or a cracked MLCC still passes. Backpackers expect more. CleverHiker's reviewers drop power banks from about 2.4 m ([CleverHiker NB10000 Gen4](https://www.cleverhiker.com/backpacking/nitecore-nb-10000-gen4-power-bank-review/)), though Backpacking Light cites unpublished tests in which the same product did poorly ([Backpacking Light](https://backpackinglight.com/nitecore-nb10000-portable-battery-charger-review)). A functional target of 26 drops from 1.22–1.5 m is a product decision, not a compliance requirement.

The failure mode points to the ends. A 2021 *Journal of Energy Storage* study found modern cylindrical cells shrug off shocks beyond automotive standards. In axial drops, several cell types **failed ohmically, with no thermal event, through contact loss in the CID region** ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2352152X21009105); [TUM full text](https://mediatum.ub.tum.de/doc/1639525/1639525.pdf)). The researchers worked from the abstract, because the full text was blocked. Three factors make this worse:

- Full SOC makes cells stiffer and lowers their strain to short ([Scientific Reports 2016](https://www.nature.com/articles/srep21829)).
- Dynamic loading shorts 18650s at smaller displacement than quasi-static loading ([Engineering Failure Analysis](https://www.sciencedirect.com/science/article/abs/pii/S1350630723005423)).
- Ageing to 80 % capacity reduces the work needed to cause a major internal short in 21700s ([ResearchGate, snippet only](https://www.researchgate.net/figure/Disassembled-cylindrical-21700-cell-Inner-parts-consist-of-anode-cathode-and_fig3_366607930)).

Design for an end-of-life cell at 100 % SOC. In the Monolith the cell axes run along the 83 mm length, so **an end-first drop loads all four CIDs at once.**

The stroke arithmetic, the researchers' own first-principles calculation, sets the envelope. A 1.5 m drop of 333 g carries **4.9 J at 5.42 m/s**:

| Peak deceleration target | Ideal constant-force stroke | Linear-spring stroke | Real foam thickness (~65 % usable strain) |
|---|---|---|---|
| 100 g | 15 mm | 30 mm | ~23 mm+ |
| 200 g | 7.5 mm | 15 mm | ~11.5–17 mm |
| 500 g | 3 mm | 6 mm | ~5–7 mm |

For context, a UN 38.3 T4 pulse equals a velocity change of about 5.6 m/s over about 17 mm of stopping distance. Each 58E has therefore already survived something like a 1.6 m drop onto a 17 mm cushion. With the **5–8 mm of end stroke** this envelope can realistically spare, peak g will land around 300–500 g or worse. The cells' margin beyond 150 g is undocumented. This is the single most important number to measure, not estimate.

Mass is not the constraint. Volume is. The absorber volume for 200 g on the end face is about 33 cm³, which is **about 6 g of PORON XRD** (SG 0.14–0.24) ([PORON XRD datasheet](https://www.algeos.com.au/pdfs/PORONXRDDataSheet.pdf)) or about 10 g of 25 %-density printed TPU. **Sorbothane would cost about 39 g** for the same volume at SG 1.27–1.32 ([Sorbothane SDS](https://www.sorbothane.com/wp-content/uploads/110-sorbothane-safety-data-sheet.pdf)), so drop it. Rogers' ">90 % absorbed" claims have no stated test conditions ([Rogers](https://www.rogerscorp.com/applications/impact-absorption)).

Corners need a different element. At 200 g the peak force is about 650 N. Spread over a whole end face that is about 0.25 MPa, but on a ~300 mm² corner it is about 2.2 MPa, which bottoms out soft foam instantly. Corners need a dense TPU lattice or a solid TPU nose that grows its contact area as it crushes. Uniform dense gyroids give an undesirable initial stress spike ([Springer, gyroid metamaterials](https://link.springer.com/article/10.1007/s12239-024-00136-1)). Printed TPU gyroids at about 30 % density show the useful plateau at 10–30 % strain ([PMC TPU gyroid study](https://pmc.ncbi.nlm.nih.gov/articles/PMC13186003/)). Grade the lattice soft at the face and denser behind.

Thermally, end foam costs almost nothing. By the cell's geometry, the two end faces of a 21700 are only about **13 % of its surface area** (about 6.9 cm² against about 47 cm² of sidewall; this is this report's own arithmetic). Insulating them barely changes the heat path that matters.

The shell matters too. FDM impact strength is lowest when the impact loads the layer interfaces, and **PC and PETG are the most sensitive to layer thickness** ([Pamukkale Univ. study](https://gcris.pau.edu.tr/handle/11499/46272)). Short-carbon-fibre nylon is weak in impact parallel to the layers ([Preprints.org](https://www.preprints.org/manuscript/202409.2382)). For the one-piece tray, print so that end and corner loads run along the extrusion paths, and prefer tough unfilled PETG, PA12 or PC over PA-CF. That preference is the researchers' inference and has not been confirmed by comparative data.

## The board needs coating and staking, not a 25 g pour

"Potted board" in the production plan should be narrowed. Potting does stop board flex, and flex is the main way MLCCs crack in a drop. Bending loads the ceramic through the solder fillets ([DigiKey TechForum](https://forum.digikey.com/t/ceramic-capacitor-failure-design-solutions-mitigating-board-flex-cracking/26195)).

The production board is **1.6 mm** thick, which weakens the case for potting further. These are this report's own beam-theory estimates, not measured:

- **Stiffness.** Bending stiffness scales with thickness cubed, so a 1.6 mm board is about 8× stiffer than a 0.8 mm one. Under the same inertial drop load it deflects about 8× less.
  - The flex-cracking risk that potting would remove is already small. Supporting the board at its edges and at the two screw pillars removes most of what is left.
- **Weight.** The board itself weighs about 9–10 g over the side board's ~32 cm². It is stiff enough that the compound would add mass without adding much stiffness.
- **What thickness doesn't fix:**
  - **Bending at fixed points.** For a given curvature, the surface strain is twice that of a 0.8 mm board. Wherever the board is forced to bend (a screw boss pulled down unevenly, a pillar slightly proud of the others, depanelization), MLCCs crack more easily. Keep large MLCCs at least 3–5 mm from screw points and break-off tabs, and orient them so their long axis runs parallel to the expected bend line.
  - **Heavy parts.** Their own inertia still loads their joints however stiff the board is. The 7×7 mm inductors and the USB-C receptacles still need staking or bosses.
  - **Thermal-cycling fatigue.** A thicker board is less compliant, so QFN/WSON joints fatigue sooner in thermal cycling.

A stiff compound adds to that stress:

- Cure shrinkage cracks MLCCs, so Murata says to "select a resin with low curing contraction" and to buffer with a silicone under-coat ([Murata FAQ](https://www.murata.com/en-global/support/faqs/capacitor/ceramiccapacitor/mnt/0024)).
- Encapsulant that wicks under a QFN or WSON and then expands puts the joints in tension and shortens fatigue life ([DfR / SMTnet](https://smtnet.com/library/files/upload/tensile-stress.pdf)).
- Low-Tg PU or silicone is the norm on SMT boards because high-Tg compounds break joints as they shrink ([Wikipedia, Potting](https://en.wikipedia.org/wiki/Potting_(electronics))).

The safe ranking runs from silicone gel, to soft silicone, to soft PU, to flexibilised epoxy, with rigid epoxy last. Also, by the researchers' estimate, a 5 mm pour over a 40 cm² board weighs **20–40 g**, against **0.1–0.6 g** for a conformal coat or parylene ([SCS coating thickness comparison](https://scscoatings.com/newsroom/blog/conformal-coatings-thickness-comparing-parylene-with-liquid-coatings/)).

IP68 does not require potting. It is an enclosure property, provided by the tray, the cover seal and the receptacles' own gaskets. Potting behind an IP68 USB-C receptacle is only needed to hold it mechanically, and printed bosses and through-hole shell tabs do that job better. If compound is used near a receptacle, the sequence is:

1. Run a thixotropic bead to dam the receptacle and let it cure.
2. Fill below the rear face only.
3. Cap the mating cavity during the pour.

A Type-C patent notes that edge glue fails because thermal expansion opens gaps at the housing ([Justia 20240039205](https://patents.justia.com/patent/20240039205)).

Thermally, potting the board helps only where it connects hot parts to the aluminium cover. Bulk fill at about 0.3 W/m·K mainly adds thermal mass and pushes inductor heat toward the cells. Keep the gap pad, or a 1–2 W/m·K dispensable gap filler, between the inductors and FETs and the cover. Keep the Kapton or fish-paper side of the board facing the cells as an air-backed thermal break.

The BLE antenna rules out potting near the module. A plain ABS wall was reported to pull a 2.4 GHz antenna down by about **100 MHz** ([RF Cafe forum](https://rfcafe.com/forums/antennas/Questions-about-covering-an-antenna-with-plastic.htm)). A practical rule is 5–8 mm of clearance from dielectric ([AISLER community](https://community.aisler.net/t/co-design-of-pcb-antennas-and-3d-printed-enclosures-practical-rf-insights/5518)). Full encapsulation at Dk 2.7–4 would shift a compact antenna by hundreds of MHz, past the 83.5 MHz-wide band. That figure is the researchers' first-order estimate. Potting over the antenna would probably also void the module's certified condition. TI's integration guide ([ZHDA212](https://www.ti.com.cn/cn/lit/pdf/zhda212)) was not read for its keep-out, so check it. The module end should stay in air, dammed off.

Process traps decide which chemistry to use:

- **Platinum-cure silicones** are inhibited by sulfur, amines, urethanes, organotin and plasticisers ([Wacker SilGel 612 TDS](https://www.wacker.com/h/de-ke/medias/WACKER-SilGel-612-AB-en-2025.03.14.pdf)), and by solder flux ([NuSil](https://nusil.avantorsciences.com/assetsvc/asset/en_US/id/46394520/contents)). Smooth-On calls PLA and PETG prints "a very frequent modern cause" ([Smooth-On](https://support.smooth-on.com/knowledgebase.php?article=46)). That covers the tray, the cell wrap and no-clean residue, so any Pt gel needs a cleaned board and a patch test on the real tray material.
- **Acetoxy RTV** releases acetic acid and must never go near the electronics. Use alkoxy-cure or addition-cure silicone ([Intertronics](https://intertronics.co.uk/2018/08/adhere-academy-are-rtv-silicone-sealants-corrosive/)).
- **PU** foams with CO₂ when it picks up moisture ([Chase/HumiSeal](https://blog.chasecorp.com/humiseal/5-simple-steps-to-eliminate-bubbles-in-potting-encapsulants)).

Whatever is applied, **BQ40Z50 golden-file programming, gauge training through J302, CC2340 flashing and the functional test must finish first**. The alternative is to leave the SMBus pogo pads and the Tag-Connect footprint as masked, open wells. Removability law is not a blocker. A law-firm reading of the July 2026 Commission guidance says power banks fall outside Article 11 ([HLC](https://www.hlc.com/en/publications/avoiding-the-redesign-the-eus-latest-position-on-battery-removability)), though that is secondary and the guidance itself was not read. Even so, a gel or uncoated cell area keeps the pack separable for recycling and failure analysis.

## Runaway propagation and venting set two hard limits

Two safety rules constrain any fill. First, **the positive-cap vent must stay free.** The only cell-maker guidance found is second-hand A123 text: cells must be mounted so they do not interfere with the vent function ([All About Circuits](https://forum.allaboutcircuits.com/threads/considerations-for-lithium-battery-venting-in-product-design.193758/post-1821826)). Potting over the cap risks raising the burst pressure until the can fails at the sidewall instead. NASA calls sidewall breach a high risk for modern high-energy cells ([NASA NTRS 20180004170](https://ntrs.nasa.gov/api/citations/20180004170/downloads/20180004170.pdf)). This fits the end-foam plan only if the positive-end foam is a ring or a dished pad that leaves the cap and its vent path into a plenum open. The single ePTFE breather is sized for pressure equalisation, not runaway gas. The researchers infer that the tray needs a designed weak point aimed away from the user.

Second, **touching cells with no heat-dissipation path "nearly assures propagation"**, and even **4 mm of air spacing** let neighbours get damaged in NASA's tests ([NASA NTRS 20160010200](https://ntrs.nasa.gov/api/citations/20160010200/downloads/20160010200.pdf); [NASA NTRS 20170001655](https://ntrs.nasa.gov/api/citations/20170001655/downloads/20170001655.pdf)). Whether foam helps is contested:

- Aspen Aerogels says PU and silicone foams "cannot withstand thermal runaway" ([Charged EVs](https://chargedevs.com/features/thermal-runaway-in-ev-battery-packs-designing-a-mitigation-strategy/)). Aspen is a vendor.
- Warwick found some interstitial foams contained sidewall rupture and stopped propagation in 21700 modules, with lower-density foams doing better ([Warwick WRAP 190638](https://wrap.warwick.ac.uk/id/eprint/190638)). The numbers were not extracted.

No source tested a small sealed 4-cell pack. For an 82 Wh consumer bank, a realistic and light step is a thin mica, ceramifying silicone or aerogel separator in the cross-shaped gap between cells. That keeps the cell-to-cell path insulating while the outer faces couple to the shell. It is the researchers' reconciliation of the cooling and propagation goals, not a tested design. Do not use paraffin PCM, despite its striking cooling results: the 64.4 °C to 40.4 °C reduction came in a module study ([Behi et al. 2022](https://doaj.org/article/fc51d87754d749988f6f17755f4aa228)), and paraffin adds fuel and saturates after one discharge.

## Recommended approach, ranked options and validation plan

**Recommended approach.** Do not pot the cells. Do not do a full board pour. Build drop resistance from geometry, and add thermal compound only where a heat path exists:

1. At each end, fit **6–10 mm** of graded TPU lattice or PORON XRD between the cell ends and the outer face. Add **1–2 mm PORON** directly on each cell end so no CID cap ever meets a rigid boss, and keep the positive cap's vent path open.
2. Fit dense, progressively crushing TPU noses at the corners.
3. Keep **1–3 mm** of compliance between the cell sidewalls and the walls. Where a wall rejects heat, make that layer a soft gap filler such as TGF 1000 (1.0 W/m·K, 30 Shore 00) rather than foam.
4. Cushion the board block against the tray rather than bonding it rigidly to an impact face.
5. On the board, apply a selective silicone or urethane-acrylic conformal coat. Stake the inductors, the module body and the large MLCCs with soft silicone. Hold the USB-C receptacles with printed bosses. Keep the gap pad to the cover. Leave the antenna end in air. On the 1.6 mm board, keep large MLCCs 3–5 mm from the screw pillars. Make the pillars coplanar so tightening the screws doesn't bend the board.

The added mass is roughly **10–25 g**. That is an estimate; most of it is the gap filler, and the cushioning is under 10 g.

| Rank | Option | Drop benefit | Thermal effect on cells | Mass | Verdict |
|---|---|---|---|---|---|
| 1 | End stops (TPU lattice / PORON) + cell-end pads + TPU corners | High: addresses the axial CID failure | Negligible (ends ≈ 13 % of area) | ~6–15 g | Do it |
| 2 | Conformal coat + soft staking + receptacle bosses on board | High for MLCCs, inductors, USB-C | None; keep gap pad to cover | <1–3 g | Do it; replaces "potted board" |
| 3 | Thin soft gap filler between outer cell faces and a heat-rejecting wall | Moderate (holds cells, damps) | Positive if it reaches a real sink | ~5–15 g partial | Do it if the 100 W test shows cells near 55 °C |
| 4 | Mica / ceramifying sheet in the inter-cell cross | None | Neutral in normal use | ~2–5 g (est.) | Recommended for propagation; not tested at this scale |
| 5 | Silicone gel (SilGel 612 / SYLGARD 527) pour on the board, antenna dammed | Moderate | Slight harm if it couples to the cells | ~20–30 g | Only if coating fails salt-fog or condensation tests |
| 6 | Low-density foam (EF-6525, EV Protect, FlexFoam) around the cells | Moderate | **Negative**: insulates | 4–8 g | Avoid (end pads aside) |
| 7 | Filled conductive potting of all cell voids (TGF 3600, SC-320, 832TC) | Moderate | Positive | **45–85 g** | Reject: mass, rework, vent risk |
| 8 | Rigid epoxy or epoxy foam (832TC, ET5442) on board or cells | Mixed | Mixed | 24–46 g | Reject: MLCC/QFN stress, permanent |

**Validation test plan.**

1. **Instrumented dummy drop.** Build the tray with four dummy cells at the 58E's ~71 g each, for example machined aluminium or steel-filled printed slugs. Mount a ≥2,000 g-range accelerometer on one dummy cell and another on the shell. Drop onto concrete from 1.0 m and 1.5 m, covering both ends, all faces and four corners (26 drops, as in the MIL-STD-810-style sequence ([TDK-Lambda report](https://www.emea.lambda.tdk.com/ch/KB/Vega-Mil-810E-Shock-Summary-Report.pdf))). Record the peak g and pulse width at the cell against the 150 g / 6 ms benchmark. Iterate the lattice grading until end drops land as close to that as the envelope allows.
2. **Live-cell functional drop.** Use real cells at 100 % SOC and the coated board. Before and after the same sequence, log OCV, DCIR and impedance per cell; a resistance rise is the CID-contact signature. Also log gauge readings, PD negotiation, both chargers and BLE RSSI. Inspect MLCCs and receptacle joints, cross-sectioning a sample.
3. **100 W thermal run.** Start at full charge at 25 °C and 35 °C and discharge at 100 W to cutoff. Place thermocouples at mid-height on each cell, on the inductors, on the cover and on the shell. Compare air, end-foam only, and side gap-filler configurations. Repeat for a 5.5 A charge and for back-to-back cycles. Pass if cells stay ≥5 K below 60 °C on discharge and below 45 °C on charge, and if each gauge NTC tracks its can within a few K. Measure 58E DCIR by HPPC at 7 A first, to replace the 4–6 W estimate.
4. **RF and process checks.** Measure BLE S11 or RSSI with the board bare, coated and installed. Run cure patch tests of any silicone on the actual tray filament, cell wrap and a fluxed scrap board. Confirm that programming and gauge training complete before coating, or through the masked pad wells.

## Conclusion

The project's working assumption, that a potted board and some foam around the cells make the pack tougher, is half right. Compliance comes from the ends: what protects the cells in a drop is stroke at the CID end, which costs a few grams of lattice or PORON, while any compound around the cans changes the thermal picture far more than the mechanical one. That means the drop design and the thermal design can be optimised almost independently: soft, light and thick at the ends; thin, conductive and wall-coupled along the sides; air at the antenna and the vent. The real unknowns are peak g at the cell with only 5–8 mm of stroke, and the 58E's actual heat at 7 A. Both are cheap to measure with a dummy-mass drop rig and one instrumented 100 W discharge. Those two tests should come before any compound is bought in quantity.
